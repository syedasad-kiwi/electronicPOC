import streamlit as st
import google.generativeai as genai
import feedparser
from typing import Dict, List, Optional, Generator
import os
from dataclasses import dataclass
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import content_types
from datetime import datetime
import html
import re
import json
from models.response_models import NewsItem, NewsResponse

# Page configuration
st.set_page_config(
    page_title="IoT News Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .news-item {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .news-title {
        color: #1f77b4;
        font-weight: bold;
    }
    .news-date {
        color: #666;
        font-size: 0.8rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background-color: #e6f3ff;
    }
    .bot-message {
        background-color: #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)

# Configure Gemini
# Load environment variables from .env file if running locally
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Load API key from environment variable or Streamlit secrets
try:
    # First try to get from Streamlit secrets
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # If running locally, try to get from environment variable
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        st.error("No Gemini API key found. Please set the GEMINI_API_KEY environment variable or Streamlit secret.")
        st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

class IoTNewsBot:
    def __init__(self):
        self.feed_urls = [
            "https://www.iotinsider.com/feed/",
            "https://www.electronicspecifier.com/?format=rss",
            "https://www.student-circuit.com/feed/"
        ]
        self.history: List[Dict] = []
        self.model = model

    def clean_html(self, raw_html: str) -> str:
        """Remove HTML tags and clean up text."""
        # First, remove script and style elements
        raw_html = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL)
        raw_html = re.sub(r'<style.*?</style>', '', raw_html, flags=re.DOTALL)
        
        # Remove HTML tags but preserve line breaks
        cleanr = re.compile('<br\s*/?>', re.IGNORECASE)
        raw_html = cleanr.sub('\n', raw_html)
        cleanr = re.compile('<.*?>')
        text = cleanr.sub('', raw_html)
        
        # Clean up whitespace while preserving structure
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return html.unescape(text.strip())

    def fetch_news(self) -> tuple[List[Dict], str]:
        """Fetch the latest IoT news from multiple RSS feeds."""
        all_posts = []
        all_formatted_posts = []
        
        for feed_url in self.feed_urls:
            try:
                st.write(f"Fetching from: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                if hasattr(feed, 'bozo_exception') and feed.bozo:
                    st.warning(f"Feed warning for {feed_url}: {feed.bozo_exception}")
                    continue
                
                if not feed.entries:
                    st.warning(f"No entries found in feed: {feed_url}")
                    continue
                
                # Get source name from feed
                source_name = feed.feed.get('title', feed_url.split('/')[2])
                
                for entry in feed.entries[:5]:  # Get latest 5 entries from each feed
                    try:
                        # Get full content if available, otherwise use description
                        if hasattr(entry, 'content') and entry.content:
                            content = entry.content[0]['value']
                        else:
                            content = entry.get('description', entry.get('summary', ''))
                        
                        clean_content = self.clean_html(content)
                        
                        # Format date - handle different date formats
                        try:
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                            elif hasattr(entry, 'published'):
                                # Try different date formats
                                for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z"]:
                                    try:
                                        pub_date = datetime.strptime(entry.published, fmt)
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    pub_date = datetime.now()
                            else:
                                pub_date = datetime.now()
                            
                            formatted_date = pub_date.strftime("%B %d, %Y")
                        except Exception:
                            formatted_date = "Recent"
                        
                        # Get categories/tags if available
                        categories = entry.get('tags', [])
                        tags = [tag.get('term', '') for tag in categories if tag.get('term')]
                        
                        # Get author information
                        authors = entry.get('authors', [])
                        author_names = [author.get('name', '') for author in authors if author.get('name')]
                        
                        post_data = {
                            "title": entry.title,
                            "description": clean_content,
                            "link": entry.link,
                            "date": formatted_date,
                            "tags": tags,
                            "authors": author_names,
                            "source": source_name
                        }
                        all_posts.append(post_data)
                        
                        # Format for context with more detailed information
                        all_formatted_posts.append(f"""Title: {entry.title}
Date: {formatted_date}
Source: {source_name}
{'Authors: ' + ', '.join(author_names) if author_names else ''}
Full Content: {clean_content}
Topics: {', '.join(tags) if tags else 'N/A'}
Source URL: {entry.link}
---""")
                    except Exception as e:
                        st.warning(f"Error processing entry from {feed_url}: {str(e)}")
                        continue
                        
            except Exception as e:
                st.warning(f"Error fetching from {feed_url}: {str(e)}")
                continue
        
        if not all_posts:
            st.error("No valid entries could be processed from any feed")
            return [], ""
        
        # Sort posts by date (most recent first)
        try:
            all_posts.sort(key=lambda x: datetime.strptime(x['date'], "%B %d, %Y") if x['date'] != "Recent" else datetime.now(), reverse=True)
        except:
            pass  # If sorting fails, keep original order
        
        return all_posts, "\n".join(all_formatted_posts)

    def process_query(self, query: str) -> Generator[str, None, None]:
        """Process user query using Gemini and yield response chunks."""
        _, context = self.fetch_news()
        
        prompt = f"""You are an IoT News Assistant. Your task is to answer questions based on the provided news articles.
        When answering:
        
        1. Provide a natural, conversational response directly addressing the user's query
        2. Format your answer as a cohesive paragraph or bullet points as appropriate
        3. Include specific details from articles (dates, numbers, quotes)
        4. Always include the source article title AND URL at the end of each information point
        5. Do not use formulaic headers or repetitive structures
        
        For direct questions (like "who is X?"), provide a single, clear answer.
        For summary requests, organize the information in a readable format with appropriate bullet points.
        
        IMPORTANT: Always include both the article title and URL at the end of your responses, 
        like this: "Source: Article Title (https://www.example.com/article-url)"
        
        Only include relevant information from the articles. If information is not found, say so clearly.
        
        Current news context:
        {context}
        
        User query: {query}"""
        
        try:
            response = self.model.generate_content(
                prompt,
                stream=True,
                generation_config={
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'top_k': 40
                }
            )
            
            # Stream response chunks
            for chunk in response:
                if chunk.text:
                    cleaned_text = chunk.text
                    # Remove any unwanted section headers like "People in the News"
                    cleaned_text = re.sub(r'^#+ .+$', '', cleaned_text, flags=re.MULTILINE)
                    # Format bullet points
                    cleaned_text = re.sub(r'^\* ', '- ', cleaned_text, flags=re.MULTILINE)
                    cleaned_text = re.sub(r'^-([^\s])', r'- \1', cleaned_text, flags=re.MULTILINE)
                    # Format quotes
                    cleaned_text = re.sub(r'>"([^"]+)"', r'"\1"', cleaned_text)
                    # Remove "Key Point:" prefix if present at the beginning of responses
                    cleaned_text = re.sub(r'^Key Point:', '', cleaned_text)
                    cleaned_text = re.sub(r'^- Key Point:', '- ', cleaned_text, flags=re.MULTILINE)
                    cleaned_text = re.sub(r'^- \*\*Key Point\*\*:', '- ', cleaned_text, flags=re.MULTILINE)
                    
                    # Ensure URLs are properly formatted as links
                    cleaned_text = re.sub(r'Source: ([^(]+) \(([^)]+)\)', r'Source: [\1](\2)', cleaned_text)
                    yield cleaned_text
        except Exception as e:
            yield f"I apologize, but I encountered an error while processing your query: {str(e)}"

def display_news_sidebar(news_items: List[Dict]):
    """Display news items in the sidebar."""
    st.sidebar.title("📰 Latest IoT News")
    
    # Add refresh button
    if st.sidebar.button("🔄 Refresh News"):
        st.rerun()
    
    st.sidebar.markdown("---")
    
    for item in news_items:
        with st.sidebar.container():
            st.markdown(f"""
            <div class="news-item">
                <div class="news-title">{item['title']}</div>
                <div class="news-date">📅 {item['date']}</div>
                <div style="margin-top: 0.5rem;">{item['description'][:200]}...</div>
                <a href="{item['link']}" target="_blank">🔗 Read full article</a>
            </div>
            """, unsafe_allow_html=True)

def init_streamlit(news_items: List[Dict]):
    """Initialize Streamlit UI components."""
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.image("https://img.icons8.com/color/96/000000/robot.png", width=80)
    
    with col2:
        st.title("IoT News Assistant")
        st.markdown("""
        Welcome to your AI-powered IoT News Assistant! 👋
        I can help you understand the latest IoT news and trends. Try asking about specific technologies,
        companies, or get summaries of recent developments.
        """)
    
    st.markdown("---")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
    
    # Display the news sidebar
    display_news_sidebar(news_items)
    
    # Add a subtle footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
        Powered by KiwiTech AI <br>
        <small>Ask me about specific details from the articles!</small>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return st.chat_input("🤔 What would you like to know about IoT?")

def main():
    try:
        # Initialize bot
        bot = IoTNewsBot()
        
        # Fetch news first
        with st.spinner("Fetching latest IoT news..."):
            news_items, _ = bot.fetch_news()
            if news_items:
                st.success("News feed updated successfully!")
            else:
                st.error("Unable to fetch news. Please try again later.")
                return
        
        # Initialize UI with news items
        user_input = init_streamlit(news_items)
        
        # Process user input
        if user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_input)
            
            # Get bot response
            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                full_response = []
                
                # Show thinking indicator
                with st.spinner("Analyzing IoT news..."):
                    response_iterator = bot.process_query(user_input)
                    # Stream the response chunks
                    for chunk in response_iterator:
                        if chunk:
                            full_response.append(chunk)
                            # Display intermediate response with proper markdown rendering
                            formatted_response = ''.join(full_response).strip()
                            # Ensure response is not treated as code block
                            if not formatted_response.startswith('```'):
                                message_placeholder.markdown(formatted_response, unsafe_allow_html=True)
                            else:
                                # If it's a code block, remove the markers and format as regular text
                                cleaned_response = re.sub(r'```.*?\n|```', '', formatted_response)
                                message_placeholder.markdown(cleaned_response, unsafe_allow_html=True)
                    
                    # Add complete response to chat history
                    if full_response:
                        complete_response = ''.join(full_response).strip()
                        st.session_state.messages.append({"role": "assistant", "content": complete_response})
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try refreshing the page or check your internet connection.")

if __name__ == "__main__":
    main()

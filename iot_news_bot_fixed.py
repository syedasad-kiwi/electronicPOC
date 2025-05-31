import streamlit as st
import streamlit as st # Ensure streamlit is imported if used in async context
import google.generativeai as genai
import feedparser
from typing import Dict, List, Optional, Generator, AsyncGenerator
import os
import asyncio # Added for async operations
from dataclasses import dataclass
# from google.generativeai.generative_models import GenerativeModel # Will be replaced by ADK
# from google.generativeai.types import content_types # May not be needed with ADK
from google_adk.agent import Agent
from google_adk.llm import Gemini
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
    /* Define color palette */
    :root {
        --primary-color: #005f73; /* Deep teal/blue */
        --secondary-color: #f8f9fa; /* Light gray */
        --text-color: #212529; /* Dark gray/black */
        --accent-color-bot: #e0f7fa; /* Light cyan for bot messages */
        --accent-color-user: #cfe2f3; /* Light blue for user messages */
        --border-color: #dee2e6; /* For borders and lines */
        --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    body {
        font-family: var(--font-family);
        color: var(--text-color);
    }

    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        background-color: var(--secondary-color); /* Apply background to whole app */
    }

    /* Sidebar news items */
    .news-item {
        padding: 1.2rem;
        border-radius: 8px;
        background-color: #ffffff; /* White background for news items */
        margin-bottom: 1rem;
        border-left: 5px solid var(--primary-color);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: box-shadow 0.3s ease;
    }
    .news-item:hover {
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    .news-title {
        color: var(--primary-color);
        font-weight: bold;
        font-size: 1.1rem; /* Slightly larger title */
        margin-bottom: 0.3rem;
    }
    .news-date {
        color: #555; /* Darker gray for date */
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .news-item a {
        color: var(--primary-color);
        text-decoration: none;
        font-weight: 500;
    }
    .news-item a:hover {
        text-decoration: underline;
    }

    /* Chat messages */
    .chat-message {
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem; /* Increased margin */
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .user-message {
        background-color: var(--accent-color-user);
        border-left: 5px solid #007bff; /* Standard blue for user */
    }
    .bot-message {
        background-color: var(--accent-color-bot);
        border-left: 5px solid var(--primary-color);
    }

    /* Styling for source links in bot messages */
    .bot-message a {
        color: #004c5a; /* Darker shade of primary for links */
        text-decoration: underline;
        font-size: 0.9rem; /* Slightly smaller for source links */
    }
    .bot-message a:hover {
        color: #007bff; /* A brighter blue on hover for links */
    }

    /* Footer styling */
    .footer {
        text-align: center;
        padding: 1rem;
        font-size: 0.85rem;
        color: #6c757d; /* Muted color */
    }

    /* General styling for Streamlit buttons to make feedback buttons less obtrusive */
    /* This might affect other buttons, so care is needed. */
    /* For feedback buttons, we rely on them being in small columns and the disabled state. */
    /* The following is an attempt to style the feedback buttons more specifically if possible */
    /* This selector targets buttons inside the specific column structure of feedback */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stButton"] button {
        /*padding: 0.2rem 0.5rem !important; */ /* Smaller padding - might be too aggressive */
        font-size: 0.9rem !important; /* Slightly smaller font */
        /* margin: 0 0.1rem !important; */ /* Minimal margin */
    }

    /* Styling for disabled feedback buttons */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stButton"] button:disabled {
        background-color: #d4edda !important;
        color: #155724 !important;
        border-color: #c3e6cb !important;
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
# model = genai.GenerativeModel('gemini-2.0-flash') # ADK Agent will manage its own model

# Define the ADK Agent
# This agent is responsible for analyzing the news context against a user query.
# It uses the Google ADK's Agent base class and leverages the Gemini LLM
# via the `google_adk.llm.Gemini` wrapper. Its primary method `call`
# takes the news context and user query, constructs a prompt, and interacts
# with the LLM to generate a text-based response.
class NewsAnalysisAgent(Agent):
    def __init__(self, model_name="gemini-1.5-flash"): # Using a recent model
        super().__init__()
        self.llm = Gemini(model_name=model_name)

    async def call(self, context: str, query: str) -> Dict[str, any]:
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
            # ADK's generate_content is suitable for non-streaming text generation
            # For simplicity, using generate_text which is often available for direct text output
            # Depending on the ADK version, this might be self.llm.generate_content(prompt).text
            response_content = await self.llm.generate_text(prompt=prompt)
            return {"text": response_content}
        except Exception as e:
            # Log error or handle more gracefully
            return {"text": f"Error in NewsAnalysisAgent: {str(e)}"}


class IoTNewsBot:
    def __init__(self):
        self.feed_urls = [
            "https://www.iotinsider.com/feed/",
            "https://www.electronicspecifier.com/?format=rss",
            "https://www.student-circuit.com/feed/"
        ]
        self.history: List[Dict] = []
        # Instantiate the ADK agent that will handle query processing.
        self.news_agent = NewsAnalysisAgent(model_name='gemini-1.5-flash')
        self.current_news_items: List[NewsItem] = []
        self.current_news_context: str = ""

    def clean_html(self, raw_html: str) -> str:
        """Remove HTML tags and clean up text."""
        # First, remove script and style elements
        raw_html = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL)
        raw_html = re.sub(r'<style.*?</style>', '', raw_html, flags=re.DOTALL)
        
        # Remove HTML tags but preserve line breaks
        cleanr = re.compile(r'<br\s*/?>', re.IGNORECASE) # Use raw string for regex
        raw_html = cleanr.sub('\n', raw_html)
        cleanr = re.compile('<.*?>')
        text = cleanr.sub('', raw_html)
        
        # Clean up whitespace while preserving structure
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return html.unescape(text.strip())

    def fetch_news(self) -> None:
        """Fetch the latest IoT news and store it in instance attributes."""
        all_posts: List[NewsItem] = []
        all_formatted_posts = []
        self.current_news_items = [] # Clear previous items
        self.current_news_context = "" # Clear previous context
        
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
                        # Append NewsItem instance
                        all_posts.append(NewsItem(**post_data))
                        
                        # Format for context with more detailed information - using post_data dict for convenience
                        all_formatted_posts.append(f"""Title: {post_data['title']}
Date: {post_data['date']}
Source: {post_data['source']}
{'Authors: ' + ', '.join(post_data['authors']) if post_data['authors'] else ''}
Full Content: {post_data['description']}
Topics: {', '.join(post_data['tags']) if post_data['tags'] else 'N/A'}
Source URL: {post_data['link']}
---""")
                    except Exception as e:
                        st.warning(f"Error processing entry from {feed_url}: {str(e)}")
                        continue
                        
            except Exception as e:
                st.warning(f"Error fetching from {feed_url}: {str(e)}")
                continue
        
        if not all_posts:
            st.error("No valid entries could be processed from any feed")
            # No return value needed, but internal state remains empty
            return
        
        # Sort posts by date (most recent first)
        try:
            # Now all_posts contains NewsItem objects, so access date attribute
            all_posts.sort(key=lambda x: datetime.strptime(x.date, "%B %d, %Y") if x.date != "Recent" else datetime.now(), reverse=True)
        except Exception as e: # Catch potential errors during sort
            st.warning(f"Could not sort news items by date: {e}")
            # Keep original order if sorting fails
        
        self.current_news_items = all_posts
        self.current_news_context = "\n".join(all_formatted_posts)
        # No explicit return

    async def process_query(self, query: str) -> AsyncGenerator[str, None]:
        """Process user query using ADK Agent and yield response using stored news context."""
        if not self.current_news_context:
            yield "News has not been fetched yet or no news is available. Please refresh the news feed."
            return

        try:
            # Invoke the ADK agent to process the query against the current news context.
            agent_response = await self.news_agent.call(context=self.current_news_context, query=query)
            response_text = agent_response.get("text", "No response text found.")

            # For now, yield the entire response as a single chunk.
            # Streaming from ADK agent's `generate_content` would require more changes.
            # Basic cleaning similar to before, can be expanded
            cleaned_text = response_text
            cleaned_text = re.sub(r'^#+ .+$', '', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^\* ', '- ', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^-([^\s])', r'- \1', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'>"([^"]+)"', r'"\1"', cleaned_text)
            cleaned_text = re.sub(r'^Key Point:', '', cleaned_text)
            cleaned_text = re.sub(r'^- Key Point:', '- ', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^- \*\*Key Point\*\*:', '- ', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'Source: ([^(]+) \(([^)]+)\)', r'Source: [\1](\2)', cleaned_text)
            
            yield cleaned_text
        except Exception as e:
            st.error(f"Error processing query with NewsAnalysisAgent: {str(e)}")
            yield f"I apologize, but I encountered an error while processing your query with the ADK agent: {str(e)}"

def display_news_sidebar(news_items: List[NewsItem]):
    """Display news items in the sidebar."""
    st.sidebar.title("📰 Latest IoT News")
    
    # Add refresh button
    if st.sidebar.button("🔄 Refresh News"):
        st.session_state.refresh_news_request = True
        st.rerun()
    
    st.sidebar.markdown("---")
    
    for item in news_items:
        # Use a generic news icon (e.g., emoji)
        icon = "📰" # Newspaper emoji as a generic icon
        # Could add more logic here for source-specific icons if desired
        # e.g., if 'iotinsider' in item['source'].lower(): icon = "💡"

        with st.sidebar.container():
            st.markdown(f"""
            <div class="news-item">
                <div class="news-title">{icon} {item.title}</div>
                <div class="news-date">📅 {item.date} | Source: {item.source}</div>
                <div style="margin-top: 0.5rem;">{item.description[:180]}...</div>
                <a href="{item.link}" target="_blank">🔗 Read full article</a>
            </div>
            """, unsafe_allow_html=True)

def init_streamlit(news_items: List[NewsItem]):
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
    if "feedback" not in st.session_state: # For feedback
        st.session_state.feedback = {}
    
    # Display chat history
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"], unsafe_allow_html=True) # Allow HTML for potential markdown links

            if message["role"] == "assistant":
                message_id = f"msg_{i}" # Create a unique ID for feedback keys

                # Check if feedback has been given for this message
                feedback_given = st.session_state.feedback.get(message_id)

                cols = st.columns([1, 1, 8]) # Adjust column ratios as needed
                with cols[0]:
                    if st.button("👍", key=f"up_{message_id}", help="Positive feedback",
                                 disabled=feedback_given is not None,
                                 use_container_width=True): # Apply custom class here if needed via markdown
                        st.session_state.feedback[message_id] = "positive"
                        st.rerun() # Rerun to update button state
                with cols[1]:
                    if st.button("👎", key=f"down_{message_id}", help="Negative feedback",
                                 disabled=feedback_given is not None,
                                 use_container_width=True):
                        st.session_state.feedback[message_id] = "negative"
                        st.rerun() # Rerun to update button state

                if feedback_given:
                    with cols[2]:
                        st.caption(f"Feedback: {feedback_given}",)


    # Display the news sidebar
    display_news_sidebar(news_items)
    
    # Add a subtle footer
    st.markdown("---")
    st.markdown(
        """
        <div class="footer">
        Powered by KiwiTech AI (ADK Enhanced) <br>
        <small>Ask me about specific details from the articles!</small>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return st.chat_input("🤔 What would you like to know about IoT?")

async def get_bot_response(bot: IoTNewsBot, user_input: str) -> str:
    """Helper async function to get full response from the bot."""
    full_response_chunks = []
    # process_query is now an async generator
    async for chunk in bot.process_query(user_input):
        if chunk:
            full_response_chunks.append(chunk)
    return "".join(full_response_chunks)

def main():
    try:
        # Initialize bot
        if "iot_news_bot" not in st.session_state:
            st.session_state.iot_news_bot = IoTNewsBot()
        bot = st.session_state.iot_news_bot

        # Determine if news needs to be fetched
        refresh_requested = st.session_state.get('refresh_news_request', False)
        if 'first_load' not in st.session_state:
            st.session_state.first_load = True

        if st.session_state.first_load or refresh_requested:
            with st.spinner("Fetching latest IoT news..."):
                bot.fetch_news() # Populates bot.current_news_items and bot.current_news_context
                if bot.current_news_items: # Check if fetch was successful
                    st.success("News feed updated successfully!")
                # Error messages are now handled within fetch_news using st.error
                # We can add a check here if critical failure needs to halt execution
                elif not bot.current_news_items and st.session_state.first_load: # Critical fail on first load
                     st.error("Unable to fetch news for the first time. Please check console or try again later.")
                     return # Stop execution if first load fails critically
                elif refresh_requested and not bot.current_news_items:
                    st.warning("Failed to refresh news. Existing news (if any) will be used.")


            st.session_state.refresh_news_request = False # Reset flag
            st.session_state.first_load = False
        
        news_items_for_sidebar = bot.current_news_items
        
        # Initialize UI with news items
        user_input = init_streamlit(news_items_for_sidebar)
        
        # Process user input
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_input)
            
            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                with st.spinner("Analyzing IoT news with ADK Agent..."):
                    # Run the async function to get the bot's response
                    # For Streamlit, which runs in its own thread, directly calling asyncio.run
                    # might lead to "RuntimeError: asyncio.run() cannot be called from a running event loop".
                    # A common pattern is to use st.experimental_singleton or st.cache_data for async calls,
                    # or run it in a way that Streamlit handles.
                    # For simplicity, as process_query yields a single string now,
                    # we can adapt the calling pattern.

                    # This is a simplified way to run an async gen and get its first (and only) result.
                    # In a more complex scenario with true async streaming to UI, this would need st.write_stream or similar.
                    
                    # We need to run the async generator.
                    # Using asyncio.run() here if not in an existing loop.
                    # If Streamlit runs its own loop, this might need adjustment.
                    # Let's try a direct run for this specific case, as we expect one item.

                    complete_response = asyncio.run(get_bot_response(bot, user_input))

                    if complete_response:
                        message_placeholder.markdown(complete_response, unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": complete_response})
                    else:
                        message_placeholder.markdown("Sorry, I couldn't generate a response.", unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't generate a response."})
                
    except Exception as e:
        st.error(f"An error occurred in main: {str(e)}")
        # More detailed error for debugging if needed
        # import traceback
        # st.error(f"Traceback: {traceback.format_exc()}")
        st.info("Please try refreshing the page or check your internet connection.")

if __name__ == "__main__":
    # To run main() which now might involve async operations initiated by asyncio.run()
    # This setup should be okay as main() itself is not async, but calls asyncio.run().
    main()

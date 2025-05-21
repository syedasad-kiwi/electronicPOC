import streamlit as st
import google.generativeai as genai
import feedparser
from google.adk import Agent
from google.adk.tool import Tool
from google.adk.model import LLMModel
from typing import Dict, List
import os

# Configure Gemini
GEMINI_API_KEY = 'AIzaSyClhXJtXsGuAmvRHghpB68lMnw9YIyxFL4'
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

class IoTNewsBot(Agent):
    def __init__(self):
        super().__init__()
        self.feed_url = "https://www.iotinsider.com/feed/"
        self.history: List[Dict] = []
    
    def fetch_news(self) -> str:
        """Fetch the latest IoT news from the RSS feed."""
        feed = feedparser.parse(self.feed_url)
        latest_posts = []
        
        for entry in feed.entries[:5]:  # Get latest 5 entries
            latest_posts.append(f"Title: {entry.title}\nSummary: {entry.description}\n")
        
        return "\n".join(latest_posts)
    
    def process_query(self, query: str) -> str:
        """Process user query using Gemini."""
        context = self.fetch_news()
        
        prompt = f"""Based on the following IoT news context:
        {context}
        
        User query: {query}
        
        Please provide a relevant, concise response."""
        
        response = model.generate_content(prompt)
        return response.text

def init_streamlit():
    """Initialize Streamlit UI components."""
    st.title("IoT News Assistant")
    st.write("Ask me anything about the latest IoT news!")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    return st.chat_input("What would you like to know about IoT?")

def main():
    # Initialize bot and UI
    bot = IoTNewsBot()
    user_input = init_streamlit()
    
    # Process user input
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get bot response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            response = bot.process_query(user_input)
            
            # Stream the response
            message_placeholder.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()

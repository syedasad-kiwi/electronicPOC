# IoT News Assistant

An AI-powered chatbot that provides insights and answers questions about the latest IoT news.

## Features

- Fetches the latest IoT news from multiple sources including [IoT Insider](https://www.iotinsider.com/), Electronics Specifier, and Student Circuit.
- Answers questions about IoT news using a Google ADK Agent powered by the Gemini LLM.
- Enhanced user interface with a modern look, improved news display in the sidebar, and a user feedback mechanism for responses.
- Provides clear, consolidated responses (ADK integration currently uses non-streaming responses).
- Displays news articles in a sidebar for easy reference, with a manual refresh option.
- Responsive and user-friendly interface.

## Technology Stack

- **Streamlit**: For the web interface.
- **Google Agent Development Kit (ADK)**: For building and orchestrating AI agent logic.
- **Google Gemini API**: The underlying Large Language Model used by the ADK agent.
- **Feedparser**: For RSS feed processing.
- **Pydantic**: For data modeling (e.g., `NewsItem`).
- **Python**: Core programming language.

## Architecture Overview

The application has been refactored to use a Google ADK agent (`NewsAnalysisAgent`) for processing user queries and interacting with the Gemini LLM. This agent encapsulates the logic for understanding queries based on fetched news context.

**Future Vision: Multi-Layered Agent System**

The long-term architectural goal is to evolve this into a multi-layered agent system using ADK for more specialized processing. The conceptualized layers include:
  - **Layer 1: News Aggregation & Normalization Agent (`NewsAggregatorAgent`):** Responsible for robustly fetching, cleaning, de-duplicating, and structuring news from various sources into `NewsItem` objects.
  - **Layer 2: Query Understanding Agent (`QueryUnderstandingAgent`):** An LLM-based agent to perform nuanced analysis of user queries, identifying intent and key entities.
  - **Layer 3: Information Retrieval & Synthesis Agent (`ResponseSynthesisAgent`):** An LLM-based agent to generate comprehensive answers based on the structured query and news data, including accurate source citation.

This layered approach, orchestrated by a top-level ADK agent (e.g., `SequentialAgent`), aims to improve modularity, maintainability, and the quality of information processing. The current single agent is the first step towards this more sophisticated architecture.


## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file in the root directory based on `sample.env`
   - Add your Gemini API key to the `.env` file:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     ```
4. Run the application:
   ```
   streamlit run iot_news_bot_fixed.py
   ```

## Usage

- Ask questions about IoT news and trends
- Get summaries of recent developments
- Find specific information about IoT companies, technologies, and projects

## Deploy on Streamlit Cloud

This application can be deployed on Streamlit Cloud for public access.

1. Push your code to GitHub
2. Go to [Streamlit Community Cloud](https://streamlit.io/cloud)
3. Sign in and connect your GitHub account
4. Deploy your application by selecting this repository
5. Add your Gemini API key as a secret in the Streamlit Cloud dashboard:
   - In your app's settings, go to the "Secrets" section
   - Add the following:
     ```
     GEMINI_API_KEY = "your_gemini_api_key_here"
     ```

## License

MIT
# IoT News Assistant

An AI-powered chatbot that provides insights and answers questions about the latest IoT news.

## Features

- Fetches the latest IoT news from [IoT Insider](https://www.iotinsider.com/)
- Answers questions about IoT news using Gemini AI
- Provides real-time streaming responses
- Displays news articles in a sidebar for easy reference
- Responsive and user-friendly interface

## Technology Stack

- **Streamlit**: For the web interface
- **Google Generative AI (Gemini)**: For natural language processing
- **Feedparser**: For RSS feed processing
- **Python**: Core programming language

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
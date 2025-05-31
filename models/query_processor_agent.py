from google_adk import Agent
from google_adk.tools import GoogleSearchTool, RSSFeedParser

class QueryProcessorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="QueryProcessorAgent",
            model="gemini-2.0-flash",
            tools=[GoogleSearchTool(), RSSFeedParser()],
            instruction="You are an IoT news assistant. Answer user queries by combining information from RSS feeds and Google Search."
        )

    def process_query(self, query):
        response = self.run(query)
        return response

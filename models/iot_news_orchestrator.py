from google_adk import CustomAgent
from models.sequential_agent import NewsProcessingPipeline
from models.parallel_agent import DataFetcherAgent

class IoTNewsOrchestrator(CustomAgent):
    def __init__(self):
        super().__init__(
            name="IoTNewsOrchestrator",
            sub_agents=[
                DataFetcherAgent(),
                NewsProcessingPipeline()
            ]
        )

    def combine_results(self, rss_results, search_results):
        # Logic to combine RSS and Google Search results
        return {
            "rss": rss_results,
            "search": search_results
        }

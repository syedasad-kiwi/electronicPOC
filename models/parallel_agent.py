from google_adk import ParallelAgent

class DataFetcherAgent(ParallelAgent):
    def __init__(self):
        super().__init__(
            name="DataFetcherAgent",
            sub_agents=[
                # Add RSS Feed Fetcher and Google Search Fetcher here
            ]
        )

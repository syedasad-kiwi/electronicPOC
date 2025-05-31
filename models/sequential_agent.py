from google_adk import SequentialAgent
from models.query_processor_agent import QueryProcessorAgent

class NewsProcessingPipeline(SequentialAgent):
    def __init__(self):
        super().__init__(
            name="NewsProcessingPipeline",
            sub_agents=[
                QueryProcessorAgent(),
                # Add RSS Feed Fetcher and Google Search Fetcher here
            ]
        )

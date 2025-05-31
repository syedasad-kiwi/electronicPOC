# IoT News Bot: Multi-Layered Agent System Conceptual Model

This document outlines a conceptual model for a multi-layered agent system to enhance the IoT News Bot, leveraging the Google ADK (Agent Development Kit).

## 1. Overall Architecture

The system will be orchestrated by a top-level `OrchestratorAgent`, likely a `google_adk.agent.SequentialAgent`. This agent will manage the flow of execution through various specialized agents, ensuring a structured approach to processing user requests and generating news-informed responses.

The process is initiated when a user submits a query. This query is captured and placed into the shared `session.state`, making it accessible to the first agent in the sequence. Each subsequent agent processes data from `session.state` and stores its output back into `session.state` for the next agent in the chain.

**Workflow:**

1.  User submits a query.
2.  `OrchestratorAgent` starts.
3.  `NewsAggregatorAgent` fetches and processes news.
4.  `QueryUnderstandingAgent` parses the user's query.
5.  `ResponseSynthesisAgent` generates the final answer.
6.  The `OrchestratorAgent` returns the final answer to the user interface.

## 2. Layer 1: News Aggregation & Normalization Agent (`NewsAggregatorAgent`)

*   **Purpose:** This agent is responsible for fetching raw news data from multiple configured RSS feeds, cleaning the HTML content, extracting relevant metadata (title, link, date, content), and structuring it into a standardized format.
*   **Type:** A custom `google_adk.agent.Agent` that internally orchestrates multiple steps, potentially using a `SequentialAgent` or `ParallelAgent` for efficiency.
*   **Internal Structure (Conceptual):**
    *   **Feed Fetching (Parallel):** A `google_adk.agent.ParallelAgent` could be used to fetch data from all RSS feed URLs concurrently. Each fetching task within this parallel agent would be a `google_adk.tools.FunctionTool` that wraps the existing `feedparser` logic for a single feed. This tool would handle the actual HTTP request and initial parsing of one feed.
        *   **Input (to each FunctionTool):** A single RSS feed URL.
        *   **Output (from each FunctionTool):** A list of raw entry data from that feed.
    *   **Data Cleaning & Normalization (Sequential):** After parallel fetching, a sequential step (or another `FunctionTool`) would take the aggregated raw entries. This step would:
        *   Clean HTML from content.
        *   Normalize date formats.
        *   Extract authors, tags, and other relevant metadata.
        *   De-duplicate articles if possible (e.g., based on URL or title similarity).
        *   Transform the data into a list of standardized `NewsItem` objects (Pydantic models or dataclasses).
*   **Inputs:**
    *   A list of RSS feed URLs (e.g., from configuration or `session.state["feed_urls"]`).
*   **Outputs:**
    *   A structured list of `NewsItem` objects, stored in `session.state["processed_news_items"]`.
    *   Optionally, a summary or status of the aggregation (e.g., number of articles fetched), stored in `session.state["news_aggregation_status"]`.
*   **ADK Primitives Used (Examples):**
    *   `google_adk.agent.Agent` (for the main wrapper)
    *   `google_adk.agent.SequentialAgent` (for internal step-by-step processing if complex)
    *   `google_adk.agent.ParallelAgent` (for concurrent feed fetching)
    *   `google_adk.tools.FunctionTool` (to wrap existing Python functions for fetching and cleaning)
    *   `session.state` (for storing inputs and outputs)

## 3. Layer 2: Query Understanding Agent (`QueryUnderstandingAgent`)

*   **Purpose:** This agent analyzes the user's raw query to understand its intent (e.g., asking for a summary of a topic, details about a specific product, comparison between technologies) and to extract key entities (like "IoT security", "NXP", "Zigbee vs. LoRaWAN"). This structured understanding helps the next layer to retrieve and synthesize information more effectively.
*   **Type:** `google_adk.agents.LlmAgent`, utilizing a Gemini model for its natural language understanding capabilities.
*   **Inputs:**
    *   The user's raw query: `session.state["user_query"]`.
    *   (Optional) A concise summary or list of titles from `session.state["processed_news_items"]` to provide context to the LLM, helping it better align extracted entities with the available news.
*   **Prompt Engineering:** The prompt for this `LlmAgent` would instruct the model to:
    *   Identify the primary intent (e.g., "summarize", "define", "compare", "specific_detail").
    *   Extract key entities, classifying them (e.g., technology, company, product, standard).
    *   Return the output in a structured format (e.g., JSON).
*   **Outputs:**
    *   A dictionary or a Pydantic model containing the parsed query information. Example:
        ```json
        {
          "intent": "summarize_topic",
          "entities": [
            {"type": "technology", "name": "IoT security"},
            {"type": "concept", "name": "latest trends"}
          ],
          "original_query": "Can you give me a summary of the latest trends in IoT security?"
        }
        ```
    *   This output will be stored in `session.state["parsed_query_info"]`.
*   **ADK Primitives Used:**
    *   `google_adk.agents.LlmAgent`
    *   `session.state`

## 4. Layer 3: Information Retrieval & Synthesis Agent (`ResponseSynthesisAgent`)

*   **Purpose:** This agent takes the structured understanding of the user's query (from Layer 2) and the comprehensive list of processed news articles (from Layer 1) to generate a relevant, coherent, and well-supported answer.
*   **Type:** `google_adk.agents.LlmAgent`, powered by a Gemini model. This agent will perform the core reasoning and content generation.
*   **Inputs:**
    *   Parsed query information: `session.state["parsed_query_info"]`.
    *   The full list of processed news items: `session.state["processed_news_items"]`.
*   **Prompt Engineering:** This is the most critical LLM interaction. The prompt will instruct the agent to:
    *   Address the user's `original_query` based on the `intent` and `entities` from `parsed_query_info`.
    *   Synthesize information from multiple articles in `processed_news_items` if necessary.
    *   Prioritize information most relevant to the query.
    *   Provide specific details, dates, and quotes when appropriate.
    *   **Crucially, cite sources for each piece of information provided**, including the article title and URL (similar to the current bot's functionality but driven by structured input).
    *   If information is not found, clearly state that.
    *   Format the response conversationally and clearly (e.g., using paragraphs or bullet points as appropriate).
*   **Outputs:**
    *   The final textual response to be presented to the user. This will be the ultimate output of the `OrchestratorAgent`.
*   **ADK Primitives Used:**
    *   `google_adk.agents.LlmAgent`
    *   `session.state` (for inputs)

## 5. Data Flow

Data flows through the system primarily via the shared `session.state` dictionary, which is accessible to all agents orchestrated by the top-level agent.

1.  **User Query:** The initial user query is placed into `session.state["user_query"]` (or a similar key) by the application framework (e.g., Streamlit).
2.  **News Aggregation:**
    *   `NewsAggregatorAgent` reads feed URLs (e.g., `session.state["feed_urls"]`).
    *   It writes its output to `session.state["processed_news_items"]`.
3.  **Query Understanding:**
    *   `QueryUnderstandingAgent` reads `session.state["user_query"]` and potentially `session.state["processed_news_items"]` (for context).
    *   It writes its output to `session.state["parsed_query_info"]`.
4.  **Response Synthesis:**
    *   `ResponseSynthesisAgent` reads `session.state["parsed_query_info"]` and `session.state["processed_news_items"]`.
    *   Its output (the final textual answer) becomes the result of the `OrchestratorAgent`'s execution.

This use of `session.state` allows for a decoupled yet connected system where agents can operate on shared data without direct dependencies on each other's internal implementations, beyond the agreed-upon data structures.

## 6. Error Handling and Orchestration Notes

*   **Sequential Execution:** The top-level `SequentialAgent` (`OrchestratorAgent`) ensures that the layers are executed in the intended order: News Aggregation -> Query Understanding -> Response Synthesis. If one agent in the sequence fails, the sequence may terminate or handle the error according to its configuration.
*   **Error Handling within Agents:**
    *   **`NewsAggregatorAgent`:** Robust error handling is vital here. If some RSS feeds fail, the agent should ideally continue with the feeds that were successful, log errors, and report the partial success. It should not halt the entire process unless no news can be fetched at all. `FunctionTool`s can raise exceptions, which the calling agent can catch.
    *   **`QueryUnderstandingAgent`:** If the LLM fails to parse the query or returns an unexpected format, this agent might default to a "general understanding" or pass through the raw query with a flag indicating parsing issues.
    *   **`ResponseSynthesisAgent`:** If this agent fails to generate a response, the system should provide a graceful fallback message to the user.
*   **Timeouts:** Agents, especially those involving LLM calls or external HTTP requests, should have appropriate timeouts configured.
*   **Validation:** Pydantic models or similar data validation techniques should be used for the data passed between agents via `session.state` to ensure data integrity and catch errors early.

This multi-layered approach aims to create a more robust, maintainable, and intelligent IoT News Bot, where each agent focuses on a specific task, improving the overall quality of the responses.

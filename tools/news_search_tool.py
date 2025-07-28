import os
from dotenv import load_dotenv
from crewai_tools import BaseTool
from algoliasearch.search_client import SearchClient

load_dotenv()

class NewsSearchTool(BaseTool):
    name: str = "Financial News Search Tool"
    description: str = (
        "Searches for financial news articles about a specific stock ticker. "
        "Use this to find recent news, sentiment, or reports on a company."
    )
    
    def _run(self, ticker: str, query: str = "") -> str:
        try:
            client = SearchClient.create(
                os.getenv("ALGOLIA_APP_ID"),
                os.getenv("ALGOLIA_SEARCH_API_KEY")
            )
            index = client.init_index(os.getenv("ALGOLIA_INDEX_NAME"))
            
            search_params = {
                'filters': f'ticker:"{ticker.upper()}"',
                'hitsPerPage': 5
            }
            
            search_query = query if query else ticker
            results = index.search(search_query, search_params)
            
            if not results.get("hits"):
                return f"No news found for ticker {ticker} with query '{query}'."

            summaries = [
                f"Title: {hit.get('title')}\nDescription: {hit.get('description', 'N/A')}"
                for hit in results.get("hits", [])
            ]
            return "\n---\n".join(summaries)
        
        except Exception as e:
            return f"Error while searching for news: {e}"
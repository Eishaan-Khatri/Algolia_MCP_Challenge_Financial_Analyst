import os
from dotenv import load_dotenv
from newsapi import NewsApiClient
from algoliasearch.search_client import SearchClient

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ALGOLIA_APP_ID = os.getenv("ALGOLIA_APP_ID")
ALGOLIA_ADMIN_API_KEY = os.getenv("ALGOLIA_ADMIN_API_KEY")
ALGOLIA_INDEX_NAME = os.getenv("ALGOLIA_INDEX_NAME")

# --- Initialize Clients ---
try:
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)
    algolia_client = SearchClient.create(ALGOLIA_APP_ID, ALGOLIA_ADMIN_API_KEY)
    index = algolia_client.init_index(ALGOLIA_INDEX_NAME)
    print("Successfully initialized NewsAPI and Algolia clients.")
except Exception as e:
    print(f"Error initializing clients: {e}")
    exit()

def fetch_and_index_news(ticker: str, company_name: str):
    """Fetches news for a given company and indexes it in Algolia."""
    print(f"Fetching news for {company_name} ({ticker})...")
    
    try:
        all_articles = newsapi.get_everything(q=company_name, language='en', sort_by='relevancy', page_size=20)
    except Exception as e:
        print(f"Error fetching news from NewsAPI: {e}")
        return

    articles_to_index = []
    for article in all_articles.get('articles', []):
        if not article.get('title') or not article.get('url'):
            continue # Skip articles without a title or URL
        record = {
            'ticker': ticker,
            'company_name': company_name,
            'title': article['title'],
            'description': article.get('description', ''),
            'url': article['url'],
            'source': article.get('source', {}).get('name'),
            'publishedAt': article.get('publishedAt'),
            'objectID': article['url'] 
        }
        articles_to_index.append(record)
        
    if not articles_to_index:
        print(f"No valid articles found for {company_name}.")
        return

    try:
        index.save_objects(articles_to_index, {'autoGenerateObjectIDIfNotExist': True})
        print(f"Successfully indexed {len(articles_to_index)} articles for {ticker}.")
        
        index.set_settings({
            'searchableAttributes': ['title', 'description', 'company_name'],
            'attributesForFaceting': ['filterOnly(ticker)', 'source']
        })
        print("Algolia index settings configured.")

    except Exception as e:
        print(f"Error indexing data in Algolia: {e}")

if __name__ == "__main__":
    stocks_to_track = { "TSLA": "Tesla", "AAPL": "Apple", "NVDA": "Nvidia", "MSFT": "Microsoft", "GOOGL": "Alphabet" }
    for ticker, name in stocks_to_track.items():
        fetch_and_index_news(ticker, name)
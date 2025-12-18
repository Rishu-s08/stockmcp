import asyncio
import os
from typing import TypedDict

import requests
from dotenv import load_dotenv

from mcp_define import mcp


load_dotenv()
NEWSAPI_API_KEY = os.getenv("NEWS_API_KEY")


class NewsArticle(TypedDict):
    title: str
    description: str


# @mcp.tool()
async def fetch_news(query: str) -> list[NewsArticle]:
    """this tool Fetch the news articles for a query from NewsAPI (sorted by recency)."""
    if not NEWSAPI_API_KEY:
        raise ValueError("NEWSAPI_API_KEY is not set in the environment.")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWSAPI_API_KEY,
        "language": "en",
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "ok":
        # include code/message to diagnose why we hit the "else" path
        raise ValueError(f"NewsAPI error for {query}: {data}")

    articles = data.get("articles") or []
    return [
        NewsArticle(
            title=article.get("title") or "",
            description=article.get("description") or "",
        )
        for article in articles
    ]



import os
import logging
import aiohttp
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def web_search(query: str) -> str:
    """
    Search the web for real-time information using Tavily API.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not found in environment variables."
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "smart",
        "include_answer": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    return f"Error: Tavily API returned status {response.status}"
                data = await response.json()
                
                results = data.get("results", [])
                if not results:
                    return "No results found."
                
                formatted_results = [f"Answer: {data.get('answer', 'N/A')}\n"]
                for r in results[:3]:
                    formatted_results.append(f"- Title: {r.get('title')}\n  URL: {r.get('url')}\n  Content: {r.get('content')[:300]}...")
                
                return "\n".join(formatted_results)
    except Exception as e:
        logger.error(f"Error in web_search: {e}")
        return f"Error performing web search: {str(e)}"

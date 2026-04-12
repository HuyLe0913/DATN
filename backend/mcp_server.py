from fastmcp import FastMCP
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("mcp_server")

@mcp.tool()
async def search_financial_reports(query: str):
    """Search for financial reports using Weaviate vector search."""
    backend_url = os.getenv("BACKEND_API_URL", "http://app:8000")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # The backend API uses POST for /ask/vector
        response = await client.post(f"{backend_url}/ask/vector", params={"query": query})
        return response.json()

@mcp.tool()
async def query_knowledge_graph(query: str):
    """Query the Neo4j knowledge graph using natural language."""
    backend_url = os.getenv("BACKEND_API_URL", "http://app:8000")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # The backend API uses POST for /ask/graph
        response = await client.post(f"{backend_url}/ask/graph", params={"query": query})
        return response.json()

if __name__ == "__main__":
    import uvicorn
    print("Starting MCP Server with transport='sse'...")
    mcp.run(transport="sse")

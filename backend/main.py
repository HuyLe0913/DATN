from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import tempfile

from backend.services.ingestion import process_md_content, run_ingestion
from backend.services.retrieval import search_hybrid, retrieve_enriched_context, SearchResult
from backend.services.ocr import process_pdf_ocr
from backend.services.s3_utils import upload_file
from backend.services.llm_utils import get_llm
from backend.database import init_postgres, init_weaviate

from fastmcp import FastMCP

app = FastAPI(title="Financial RAG API", version="1.0.0")
mcp = FastMCP("finance")


class AskResponse(BaseModel):
    answer: str
    context: str

class VectorResponse(BaseModel):
    results: List[SearchResult]

class GraphResponse(BaseModel):
    classification: dict
    graph_results: List[dict]
    cypher: str

@app.on_event("startup")
def startup_event():
    try:
        init_postgres()
        init_weaviate()
        print("Databases initialized.")
        print("Registered Routes:")
        for route in app.routes:
            print(f"  {route.path} -> {type(route)}")
    except Exception as e:
        print(f"Database initialization failed: {e}")

@app.on_event("shutdown")
def shutdown_event():
    from backend.database import close_weaviate_client
    close_weaviate_client()
    print("Databases connections closed.")

@app.post("/ingest/file", summary="Upload và nạp dữ liệu từ một file .md lẻ")
async def ingest_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .md")
    try:
        content = await file.read()
        md_content = content.decode("utf-8")
        process_md_content.delay(md_content, file.filename)
        return {"message": f"File {file.filename} queued for ingestion."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/folder", summary="Nạp dữ liệu hàng loạt từ thư mục mẫu /data")
async def ingest_folder(data_dir: str = "/data"):
    try:
        run_ingestion.delay(data_dir)
        return {"message": "Bulk ingestion queued. Follow worker logs for progress."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/pdf", summary="Upload file PDF để chạy OCR và nạp dữ liệu tự động")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .pdf")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        s3_key = upload_file(tmp_path, "pdfs", file.filename)
        os.unlink(tmp_path)
        process_pdf_ocr.delay(s3_key)
        return {"message": f"PDF {file.filename} uploaded and OCR task started.", "s3_key": s3_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/vector", response_model=VectorResponse, summary="Tìm kiếm vector đơn thuần")
async def ask_vector(
    query: str,
    symbol: Optional[str] = None,
    year: Optional[int] = None,
    quarter: Optional[str] = None
):
    try:
        results = await search_hybrid(query, symbol=symbol, year=year, quarter=quarter)
        return VectorResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/graph", response_model=GraphResponse, summary="Truy vấn đồ thị đơn thuần")
async def ask_graph(
    query: str,
    symbol: Optional[str] = None
):
    try:
        from backend.services.retrieval import retrieve_graph_context
        graph_data = await retrieve_graph_context(query, symbol=symbol)
        return GraphResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- MCP Tools Implementation ---

@mcp.tool()
async def search_financial_reports(query: str, symbol: Optional[str] = None, year: Optional[int] = None):
    """
    Search for financial report content using hybrid vector search.
    :param query: The natural language question or search term.
    :param symbol: Ticker symbol (e.g., 'VPB').
    :param year: Fiscal year (e.g., 2024).
    """
    results = await search_hybrid(query, symbol=symbol, year=year)
    return "\n---\n".join([f"Source: {r.filename}\nContent: {r.content}" for r in results])

@mcp.tool()
async def query_knowledge_graph(query: str, symbol: str):
    """
    Query the knowledge graph for structured financial data and relationships.
    :param query: Natural language query for graph analysis.
    :param symbol: Ticker symbol (e.g., 'VRE').
    """
    from backend.services.retrieval import retrieve_graph_context
    graph_data = await retrieve_graph_context(query, symbol=symbol)
    return {
        "classification": graph_data.get("classification"),
        "results": graph_data.get("graph_results"),
        "cypher": graph_data.get("cypher")
    }

# Mount MCP ASGI app

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="debug")

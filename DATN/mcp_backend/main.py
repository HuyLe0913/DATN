from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import tempfile

from mcp_backend.services.ingestion import process_md_content, run_ingestion
from mcp_backend.services.retrieval import search_hybrid, retrieve_enriched_context, SearchResult
from mcp_backend.services.ocr import process_pdf_ocr
from mcp_backend.services.s3_utils import upload_file
from mcp_backend.services.llm_utils import get_llm
from mcp_backend.database import init_postgres, init_weaviate

from fastmcp import FastMCP

app = FastAPI(title="Financial RAG API", version="1.0.0")


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
    from mcp_backend.database import close_weaviate_client
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


class VectorResponseItem(BaseModel):
    text: str
    file_name: str
    header_path: str
    score: float
    # Metadata tối giản để Agent kiểm chiếu
    symbol: Optional[str] = None
    year: Optional[int] = None
    quarter: Optional[str] = None

class VectorResponse(BaseModel):
    results: List[VectorResponseItem]

@app.post("/ask/vector", response_model=VectorResponse, summary="Tìm kiếm báo cáo tài chính (Vector)")
async def search_financial_reports(
    query: str = Query(..., description="Nội dung cần tìm kiếm"),
    symbol: Optional[str] = Query(None, description="Mã cổ phiếu"),
    year: Optional[int] = Query(None, description="Năm báo cáo"),
    quarter: Optional[str] = Query(None, description="Quý báo cáo (1, 2, 3, 4)"),
    limit: int = Query(5, description="Số lượng kết quả trả về")
):
    try:
        results = await search_hybrid(
            query=query, 
            symbol=symbol, 
            year=year, 
            quarter=quarter,
            limit=limit
        )
        
        lean_results = [
            VectorResponseItem(
                text=r.text,
                file_name=r.file_name,
                header_path=r.header_path,
                score=round(r.score, 4),
                symbol=r.symbol,
                year=r.year,
                quarter=r.quarter
            ) for r in results
        ]
        
        return VectorResponse(results=lean_results)
    except Exception as e:
        print(f"Error in search_financial_reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/graph", response_model=GraphResponse, summary="Truy vấn dữ liệu từ Knowledge Graph")
async def query_knowledge_graph(
    query: str,
    symbol: Optional[str] = None
):
    try:
        from mcp_backend.services.retrieval import retrieve_graph_context
        graph_data = await retrieve_graph_context(query, symbol=symbol)
        return GraphResponse(**graph_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

mcp = FastMCP.from_fastapi(app, name="Financial-Agent")
mcp_app = mcp.http_app(path="/", transport="streamable-http")
app.router.lifespan_context = mcp_app.lifespan
app.mount("/mcp", mcp_app)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="debug")

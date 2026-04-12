from __future__ import annotations
import os
import glob
import json
from typing import List
from dotenv import load_dotenv
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from celery import shared_task
from backend.services.s3_utils import get_file_content

load_dotenv()

from backend.services.llm_utils import get_llm, get_embeddings
import re
import unicodedata

def extract_metadata_from_filename(filename: str):
    """
    Tách Symbol, Year, Quarter từ tên file.
    Hỗ trợ nhiều định dạng:
    - ACB_Baocaotaichinh_Q1_2024_Hopnhat.md
    - 20240426 - ACB - BCTC Quy I 2024.md
    """
    # Loại bỏ phần mở rộng
    name_without_ext = os.path.splitext(filename)[0]
    
    # 1. Clean name: remove initial date (8 digits) and separators
    name_clean = re.sub(r"^\d{8}[_\s-]*", "", name_without_ext).strip()
    
    # 2. Pattern chuẩn: SYMBOL_Baocaotaichinh_QUARTER_YEAR
    match = re.search(r"([A-Z0-9]+)_Baocaotaichinh_Q([1-4])_(\d{4})", name_clean, re.IGNORECASE)
    if match:
        return {
            "symbol": match.group(1).upper(),
            "quarter": match.group(2), # Trả về '1', '2', '3', '4'
            "year": int(match.group(3))
        }
    
    # 3. Pattern linh hoạt hơn (tìm Year, Symbol, Quarter riêng lẻ)
    # Tìm Year: 4 chữ số 20xx
    year_match = re.search(r"\b(20\d{2})\b", name_clean)
    year = int(year_match.group(1)) if year_match else None
    
    # Tìm Symbol: 3-5 chữ cái hoa đứng riêng
    name_no_year = name_clean
    if year_match:
        name_no_year = name_clean.replace(year_match.group(1), "")
    
    symbol_match = re.search(r"\b([A-Z]{3,5})\b", name_no_year)
    symbol = symbol_match.group(1).upper() if symbol_match else None
    
    # Tìm Quarter: Q1-Q4 hoặc Quy I-IV hoặc Quy 1-4
    quarter = None
    q_match = re.search(r"\bQ([1-4])\b", name_clean, re.IGNORECASE)
    if q_match:
        quarter = q_match.group(1)
    else:
        # Thử tìm chữ "Quy I/II/III/IV/1/2/3/4"
        q_text_match = re.search(r"Quy\s+([1-4]|I{1,3}|IV)", name_clean, re.IGNORECASE)
        if q_text_match:
            qv = q_text_match.group(1).upper()
            mapping = {"I": "1", "II": "2", "III": "3", "IV": "4", "1": "1", "2": "2", "3": "3", "4": "4"}
            quarter = mapping.get(qv, qv)

    return {"symbol": symbol, "year": year, "quarter": quarter}

def enrich_context(chunk_content: str, file_name: str, header_path: str) -> str:
    """
    Sử dụng LLM để tạo tóm tắt ngữ cảnh cho mảnh văn bản.
    """
    prompt = f"""
    Hãy viết một câu tóm tắt ngữ cảnh ngắn gọn (dưới 30 từ) cho đoạn văn bản sau đây trích từ báo cáo tài chính.
    Tên file: {file_name}
    Vị trí (Headers): {header_path}
    
    Đoạn văn bản:
    {chunk_content[:1000]}... (trích đoạn)
    
    Yêu cầu đầu ra: Chỉ trả về câu tóm tắt ngữ cảnh. Ví dụ: 'Đoạn văn này giải trình về doanh thu trong báo cáo tài chính năm 2023 của công ty [X]'.
    """
    llm = get_llm()
    response = llm.invoke(prompt)
    content = response.content
    if isinstance(content, list):
        # Join parts if it's a list
        context = " ".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content]).strip()
    else:
        context = str(content).strip()
    return context # Trả về bản tóm tắt nguyên bản

@shared_task(name="process_md_content")
def process_md_content(md_content: str, file_name: str, skip_graph: bool = False):
    from backend.database import SessionLocal, get_weaviate_client, close_weaviate_client
    from backend.models import FinancialChunkORM
    import weaviate.classes as wvc
    """
    Xử lý nội dung Markdown: Chunking, Embedding và lưu trữ.
    """

    # Normalize input text to NFC to ensure consistent accent encoding
    md_content = unicodedata.normalize('NFC', md_content)

    # Markdown Chunking
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    chunks = markdown_splitter.split_text(md_content)

    db_session = SessionLocal()
    weaviate_client = get_weaviate_client()
    collection = weaviate_client.collections.get("FinancialReport")

    # Extract global metadata from filename
    metadata = extract_metadata_from_filename(file_name)
    symbol = metadata.get("symbol")
    year = metadata.get("year")
    quarter = metadata.get("quarter")

    pg_chunks = []
    
    try:
        print(f"Starting to process {len(chunks)} chunks for {file_name} (Symbol: {symbol}, Year: {year}, Q: {quarter})...")
        
        # Weaviate Batch Context Manager
        with collection.batch.dynamic() as batch:
            for i, chunk in enumerate(chunks):
                # Extract header path
                headers = [chunk.metadata.get(h, "") for _, h in headers_to_split_on]
                header_path = " > ".join([h for h in headers if h])
                
                raw_content = chunk.page_content

                # 1. Enrichment (Skipped)
                summary = "" 
                enriched_content = raw_content 
                
                # 2. Generate Embedding
                print(f"  Embedding chunk {i+1}/{len(chunks)}...")
                embeddings = get_embeddings()
                vector = embeddings.embed_query(enriched_content)
                
                # 3. Add to Postgres list
                pg_chunks.append(FinancialChunkORM(
                    file_name=file_name,
                    symbol=symbol,
                    year=year,
                    quarter=quarter,
                    header_path=header_path,
                    raw_content=raw_content,
                    chunk_text=raw_content,
                    enriched_text=enriched_content
                ))
                
                # 4. Add to Weaviate batch
                batch.add_object(
                    properties={
                        "text": enriched_content,
                        "summary": summary,
                        "content": raw_content,
                        "symbol": symbol,
                        "year": int(year) if year else None,
                        "quarter": quarter,
                        "file_name": file_name,
                        "header_path": header_path
                    },
                    vector=vector 
                )

                # 5. Intermittent Commit (Every 20 chunks)
                if len(pg_chunks) >= 20:
                    print(f"  Persisting batch of {len(pg_chunks)} chunks...")
                    db_session.add_all(pg_chunks)
                    db_session.commit()
                    pg_chunks = [] # Clear list
        
        # 6. Final Bulk Commit for remaining
        if pg_chunks:
            print(f"  Persisting final {len(pg_chunks)} chunks for {file_name}...")
            db_session.add_all(pg_chunks)
            db_session.commit()

        # 7. Batch Graph Extraction (Only if not skipped)
        if not skip_graph:
            chunk_texts = [c.page_content for c in chunks]
            batch_size = 20
            for i in range(0, len(chunk_texts), batch_size):
                batch_data = chunk_texts[i:i+batch_size]
                extract_graph_batch_task.apply_async(args=[batch_data, symbol, file_name], queue="graph-queue")
        
        print(f"Successfully processed {file_name}: {len(chunks)} chunks saved.")
    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        db_session.rollback()
    finally:
        db_session.close()
        close_weaviate_client()

@shared_task(
    name="extract_graph_batch_task", 
    bind=True, 
    autoretry_for=(Exception,), 
    retry_backoff=True, 
    max_retries=10
)
def extract_graph_batch_task(self, texts: List[str], symbol: str, file_name: str):
    """
    Task Celery để trích xuất đồ thị từ một BỘ các đoạn văn bản (Batch).
    Giúp tận dụng context window lớn và giảm số lượng API calls.
    """
    from backend.services.graph_service import graph_service, Node, Edge
    
    # Combine texts with clear separators
    combined_text = "\n\n--- DOCUMENT CHUNK ---\n\n".join(texts)
    
    print(f"Executing batch graph extraction for {file_name} (Symbol: {symbol}, Chunks: {len(texts)})...")
    extraction = graph_service.extract_graph_from_text(combined_text, symbol)
    
    if extraction:
        # Tự động gán nguồn dữ liệu (Document node)
        doc_node = Node(id=file_name, label="Document", properties={"file_name": file_name})
        if not any(n.id == file_name for n in extraction.nodes):
            extraction.nodes.append(doc_node)
            
        # Gán quan hệ FROM_SOURCE cho tất cả các node được trích xuất
        for node in extraction.nodes:
            if node.id != file_name:
                extraction.edges.append(Edge(source=node.id, target=file_name, type="FROM_SOURCE"))
        
        # Lưu vào Neo4j
        graph_service.save_graph(extraction)
        print(f"Batch graph extraction saved for {file_name} ({len(extraction.nodes)} nodes created)")
    else:
        print(f"Batch graph extraction yielded no data for {file_name}")

@shared_task(
    name="extract_graph_task", 
    bind=True, 
    autoretry_for=(Exception,), 
    retry_backoff=True, 
    max_retries=3
)
def extract_graph_task(self, text: str, symbol: str, file_name: str):
    """
    Old single-chunk task, redirected to batch task with a list of 1.
    """
    return extract_graph_batch_task.delay([text], symbol, file_name)

@shared_task(name="run_ingestion")
def run_ingestion(data_dir: str = "/data"):
    # Find files recursively
    md_files = glob.glob(os.path.join(data_dir, "**", "*.md"), recursive=True)
    if not md_files:
        print(f"No .md files found in {data_dir}")
        return
    
    print(f"Found {len(md_files)} files to process in {data_dir}.")
    for i, file_path in enumerate(md_files):
        file_name = os.path.basename(file_path)
        print(f"[{i+1}/{len(md_files)}] Processing file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            process_md_content.delay(md_content, file_name)
    print("Ingestion run completed.")

@shared_task(name="ingest_from_s3")
def ingest_from_s3(md_s3_key: str):
    print(f"Starting ingestion from S3: {md_s3_key}...")
    content = get_file_content("markdowns", md_s3_key)
    process_md_content(content, md_s3_key)
    print(f"Ingestion from S3 completed for {md_s3_key}")

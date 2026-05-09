import os
from typing import List, Optional
from pydantic import BaseModel
import weaviate.classes as wvc
from dotenv import load_dotenv
from mcp_backend.database import get_weaviate_client
from mcp_backend.services.llm_utils import get_embeddings, get_llm
import asyncio
import json

load_dotenv()

class SearchResult(BaseModel):
    text: str
    summary: Optional[str]
    content: Optional[str]
    symbol: Optional[str]
    year: Optional[int]
    quarter: Optional[str]
    file_name: str
    header_path: str
    score: Optional[float]

async def search_hybrid(query: str, symbol: str = None, year: int = None, quarter: str = None, limit: int = 3) -> List[SearchResult]:
    embeddings = get_embeddings()
    client = get_weaviate_client()
    # Use await for embedding
    query_vector = await embeddings.aembed_query(query)
    
    collection = client.collections.get("FinancialReport")
    
    filters = []
    if symbol:
        filters.append(wvc.query.Filter.by_property("symbol").equal(symbol.upper()))
    if year:
        filters.append(wvc.query.Filter.by_property("year").equal(int(year)))
    if quarter:
        # Normalize Q1-Q4 to 1-4
        norm_q = quarter.upper().replace("Q", "")
        filters.append(wvc.query.Filter.by_property("quarter").equal(norm_q))
    
    where_filter = None
    if filters:
        where_filter = wvc.query.Filter.all_of(filters) if len(filters) > 1 else filters[0]
 
    try:
        # Tối ưu limit và alpha để cân bằng giữa keyword và ngữ cảnh
        response = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=0.3, # Keyword-heavy but maintains semantic relationships
            limit=30,  # Tăng pool ban đầu để rerank chuyên sâu hơn
            filters=where_filter,
            return_metadata=wvc.query.MetadataQuery(score=True)
        )
        
        results = []
        seen_texts = set()
        
        # Phân tích query để xác định mục tiêu
        q_lower = query.lower()
        financial_keywords = ["triệu", "vnd", "tỉ", "tỷ", "đồng", "báo cáo", "kết quả", "cân đối", "tài sản", "lợi nhuận"]
        is_financial_query = any(k in q_lower for k in financial_keywords)
        is_main_report_query = any(k in q_lower for k in ["bảng cân đối", "kết quả kinh doanh", "lưu chuyển tiền tệ"])

        for obj in response.objects:
            text = obj.properties.get("text", "")
            header = obj.properties.get("header_path", "")
            
            # 1. Khử trùng nâng cao (Dựa trên 100 ký tự đầu của text)
            text_sum = text[:100].strip()
            if text_sum in seen_texts:
                continue
            seen_texts.add(text_sum)
            
            score = obj.metadata.score if obj.metadata.score else 0.0
            
            # 2. Cấu trúc Bảng số liệu (Table Density)
            # Ưu tiên các chunk có cấu trúc bảng rõ ràng
            table_markers = text.count("|")
            if table_markers > 12:
                score += 0.4 # Bảng lớn, dữ liệu tập trung
            elif table_markers > 5:
                score += 0.2
                
            # 3. Định danh Báo cáo (Form Patterns)
            # Các báo cáo chuẩn thường có mã "Mẫu B01", "Mẫu B02"...
            import re
            if re.search(r"Mẫu B0[1-9]", text) or re.search(r"Mẫu B0[1-9]", header):
                score += 0.4 # Đây gần như chắc chắn là trang chủ của báo cáo chính
                
            # 4. Tín hiệu "Chính xác & Hợp nhất"
            if "đã kiểm toán" in text.lower() or "đã kiểm toán" in header.lower():
                score += 0.15
            if "hợp nhất" in text.lower() or "hợp nhất" in header.lower():
                score += 0.1
                
            # 5. Phân tách Báo cáo chính vs. Thuyết minh (Notes)
            # Nếu tìm báo cáo chính, hãy hạ điểm Thuyết minh để tránh noise
            if is_main_report_query and "thuyết minh" in header.lower():
                score -= 0.2 # Thuyết minh thường chứa chi tiết, không phải bảng tổng hợp
                
            # 6. Khớp tiêu đề trực tiếp
            if q_lower in header.lower():
                 score += 0.2
            elif any(word in header.lower() for word in q_lower.split() if len(word) > 4):
                 score += 0.05

            # 7. Khử nhiễu Quản trị/Thù lao (Noise Filtering)
            # Nếu đang tìm số liệu tài chính mà gặp phần Thù lao/HĐQT thì trừ điểm nặng
            irrelevant_keywords = ["hội đồng quản trị", "ban kiểm soát", "ban điều hành", "thù lao", "tiền lương", "quản trị công ty"]
            if is_financial_query and any(k in header.lower() or (k in text.lower()[:500]) for k in irrelevant_keywords):
                score -= 0.6 

            results.append(SearchResult(
                text=text,
                summary=obj.properties.get("summary", ""),
                # Truncate content to 25k chars as a safety measure for context window
                content=obj.properties.get("content", "")[:25000],
                symbol=obj.properties.get("symbol", ""),
                year=obj.properties.get("year", 0),
                quarter=obj.properties.get("quarter", ""),
                file_name=obj.properties.get("file_name", ""),
                header_path=header,
                score=round(score, 4)
            ))
            
        # Rerank và trả về kết quả
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
        
    except Exception as e:
        print(f"Weaviate Query Error: {e}")
        return []

async def classify_query(query: str) -> dict:
    llm = get_llm()
    prompt = f"""
    Phân tích câu hỏi tài chính sau và trích xuất thông tin theo định dạng JSON:
    Câu hỏi: '{query}'

    Yêu cầu JSON:
    {{
        "intent": "FINANCIAL" (con số, BCTC) | "EVENT" (tin tức, sự kiện) | "GENERAL" (chung chung),
        "entities": ["Mã CK", "Tên cty", "Ngành"],
        "time_period": "Q1 2024", "Năm 2023", v.v.,
        "rel_type": "EXPLAINS" (nguyên nhân) | "CONTRIBUTES_TO" (thành phần) | "MENTIONS" (đề cập)
    }}
    Chỉ trả về JSON.
    """
    try:
        response = await llm.ainvoke(prompt)
        res = response.content
        if "```json" in res: res = res.split("```json")[1].split("```")[0].strip()
        return json.loads(res)
    except:
        return {"intent": "GENERAL", "entities": [], "time_period": None, "rel_type": "MENTIONS"}

def generate_cypher_query(classification: dict) -> str:
    intent = classification.get("intent")
    entities = classification.get("entities", [])
    period = classification.get("time_period")
    rel = classification.get("rel_type", "MENTIONS")
    
    entity_str = entities[0] if entities else "ACB"
    
    if intent == "FINANCIAL":
        # Tìm con số và các thành phần đóng góp
        cypher = f"""
        MATCH (item:FinancialItem)-[:BELONGS_TO]->(c:Company {{id: '{entity_str}'}})
        OPTIONAL MATCH (item)-[:IN_PERIOD]->(p:Period)
        OPTIONAL MATCH (sub:FinancialItem)-[:CONTRIBUTES_TO]->(item)
        RETURN item.id as Item, item.content as Value, p.id as Period, sub.id as SubItem
        LIMIT 10
        """
    elif intent == "EVENT":
        # Tìm sự kiện và giải thích cho biến động
        cypher = f"""
        MATCH (e:EconomicEvent)
        WHERE e.id CONTAINS '{entity_str}' OR e.content CONTAINS '{entity_str}'
        OPTIONAL MATCH (e)-[:EXPLAINS]->(item:FinancialItem)
        RETURN e.id as Event, e.content as Description, item.id as ImpactedItem
        LIMIT 10
        """
    else:
        # Mặc định: Tìm kiếm node liên quan bất kỳ
        cypher = f"MATCH (n) WHERE n.id CONTAINS '{entity_str}' OR n.content CONTAINS '{entity_str}' RETURN n LIMIT 10"
    
    return cypher

async def retrieve_graph_context(query: str, symbol: Optional[str] = None) -> dict:
    """
    Chỉ thực hiện trích xuất tri thức từ Graph (Neo4j).
    Tập trung vào sự kiện và các mối quan hệ phức tạp.
    """
    # 1. Classify intent
    classification = await classify_query(query)
    
    if symbol and symbol not in classification['entities']:
        classification['entities'].insert(0, symbol)
        
    # 2. Generate & Execute Cypher
    from mcp_backend.services.graph_service import graph_service
    cypher = generate_cypher_query(classification)
    
    # Execute query (minimal data as requested)
    graph_results = graph_service.execute_read_query(cypher)
    
    return {
        "classification": classification,
        "graph_results": graph_results,
        "cypher": cypher
    }

async def retrieve_enriched_context(query: str, symbol: str = None, year: int = None, quarter: str = None) -> str:
    # RUN IN PARALLEL: Vector Search + Graph Logic
    vector_task = search_hybrid(query, symbol, year, quarter, limit=5)
    graph_task = retrieve_graph_context(query, symbol)
    
    vector_results, graph_data = await asyncio.gather(vector_task, graph_task)
    
    # Process results
    vector_context = "\n".join([f"[File: {r.file_name}] {r.content}" for r in vector_results])
    graph_context = "\n".join([str(r) for r in graph_data["graph_results"]])
    classification = graph_data["classification"]
    
    return f"""
    NGỮ CẢNH VĂN BẢN (VECTOR SEARCH):
    {vector_context}

    PHÂN TÍCH ĐỒ THỊ (GRAPH LOGIC):
    Intent: {classification['intent']} | Target: {classification['entities']}
    Dữ liệu đồ thị:
    {graph_context}
    """
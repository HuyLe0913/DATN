import os
from typing import List, Optional
from pydantic import BaseModel
import weaviate.classes as wvc
from dotenv import load_dotenv
from backend.database import get_weaviate_client
from backend.services.llm_utils import get_embeddings, get_llm
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

async def search_hybrid(query: str, symbol: str = None, year: int = None, quarter: str = None, limit: int = 5) -> List[SearchResult]:
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
        # Weaviate v4 query is sync but we can run it in executor or just keep it sync as it's fast
        # but the embedding part was the real bottleneck.
        response = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=0.5,
            limit=limit,
            filters=where_filter,
            return_metadata=wvc.query.MetadataQuery(score=True)
        )
        
        results = [
            SearchResult(
                text=obj.properties.get("text", ""),
                summary=obj.properties.get("summary", ""),
                content=obj.properties.get("content", ""),
                symbol=obj.properties.get("symbol", ""),
                year=obj.properties.get("year", 0),
                quarter=obj.properties.get("quarter", ""),
                file_name=obj.properties.get("file_name", ""),
                header_path=obj.properties.get("header_path", ""),
                score=obj.metadata.score if obj.metadata.score else 0.0
            ) for obj in response.objects
        ]
        return results
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
    from backend.services.graph_service import graph_service
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
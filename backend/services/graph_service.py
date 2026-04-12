from typing import List, Optional
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from backend.services.llm_utils import get_llm
import json

load_dotenv()

NEO4J_URL = os.getenv("NEO4J_URL", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

class Node(BaseModel):
    id: str = Field(description="Unique identifier for the node (e.g., Symbol, Item name, Event summary)")
    label: str = Field(description="Label: Company, FinancialItem, Period, EconomicEvent, Person, Document")
    content: Optional[str] = Field(None, description="Detailed text or value of the node")
    properties: dict = Field(default_factory=dict)

class Edge(BaseModel):
    source: str
    target: str
    type: str # BELONGS_TO, IN_PERIOD, CONTRIBUTES_TO, EXPLAINS, MENTIONS, MANAGES, FROM_SOURCE
    properties: dict = Field(default_factory=dict)

class GraphExtraction(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class GraphService:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def extract_graph_from_text(self, text: str, symbol: str = None) -> Optional[GraphExtraction]:
        llm = get_llm()
        
        prompt = f"""
        Nhiệm vụ của bạn là trích xuất thông tin tài chính sâu từ văn bản (đặc biệt là các BẢNG Markdown) thành cấu trúc Đồ thị (Graph).
        
        1. DANH SÁCH THỰC THỂ (NODES):
        - Company: id là mã chứng khoán (ví dụ: {symbol or 'Mã CK'}), content là tên đầy đủ và ngành.
        - FinancialItem: id là tên khoản mục (ví dụ: 'Doanh thu thuần', 'Tổng tài sản'). 
          QUAN TRỌNG: content PHẢI là giá trị con số kèm đơn vị (ví dụ: '12,345 tỷ VNĐ').
        - Period: id là nhãn thời gian (ví dụ: 'Q1 2024' hoặc 'Năm 2023').
        - EconomicEvent: id là tóm tắt sự kiện, content là mô tả chi tiết nguyên nhân/ảnh hưởng.

        2. DANH SÁCH QUAN HỆ (EDGES):
        - BELONGS_TO: (FinancialItem) -> (Company)
        - IN_PERIOD: (FinancialItem) -> (Period)
        - EXPLAINS: (EconomicEvent) -> (FinancialItem)
        - MENTIONS: (EconomicEvent) -> (Company)

        VĂN BẢN CẦN TRÍCH XUẤT (CHÚ Ý CÁC BẢNG):
        {text}

        YÊU CẦU: Trả về kết quả dưới dạng JSON duy nhất. 
        Hãy trích xuất tât cả các con số tài chính quan trọng thành các nodes để Agent có thể tra cứu chính xác.
        {{
            "nodes": [ {{"id": "...", "label": "...", "content": "...", "properties": {{...}}}} ],
            "edges": [ {{"source": "...", "target": "...", "type": "...", "properties": {{...}}}} ]
        }}
        """
        
        try:
            response = llm.invoke(prompt)
            content = response.content
            if isinstance(content, list):
                content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            return GraphExtraction(**data)
        except Exception as e:
            print(f"Error extracting graph: {e}")
            return None

    def save_graph(self, extraction: GraphExtraction):
        if not self.driver:
            return

        with self.driver.session() as session:
            for node in extraction.nodes:
                cypher = f"MERGE (n:{node.label} {{id: $id}}) SET n.content = $content, n += $props"
                session.run(cypher, id=node.id, content=node.content or "", props=node.properties)
            
            for edge in extraction.edges:
                cypher = f"""
                MATCH (s {{id: $source}})
                MATCH (t {{id: $target}})
                MERGE (s)-[r:{edge.type}]->(t)
                SET r += $props
                """
                session.run(cypher, source=edge.source, target=edge.target, props=edge.properties)

    def execute_read_query(self, cypher: str, params: dict = None) -> List[dict]:
        """
        Thực thi một câu lệnh Cypher đọc và trả về danh sách các bản ghi (dict).
        """
        if not self.driver: return []
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, **(params or {}))
                return [record.data() for record in result]
        except Exception as e:
            print(f"Cypher Error (Read): {e}")
            return []

    def execute_write_query(self, cypher: str, params: dict = None):
        """
        Thực thi một câu lệnh Cypher ghi.
        """
        if not self.driver: return
        
        try:
            with self.driver.session() as session:
                session.run(cypher, **(params or {}))
        except Exception as e:
            print(f"Cypher Error (Write): {e}")

    def query_graph_context(self, keywords: List[str], limit: int = 10) -> str:
        """
        Tìm kiếm các node liên quan bằng Cypher động và trả về chuỗi ngữ cảnh.
        """
        if not self.driver: return ""
        
        context_parts = []
        with self.driver.session() as session:
            for kw in keywords:
                cypher = """
                MATCH (n)
                WHERE n.id CONTAINS $kw OR n.content CONTAINS $kw
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m LIMIT $limit
                """
                result = session.run(cypher, kw=kw, limit=limit)
                for record in result:
                    node = record["n"]
                    if node:
                        context_parts.append(f"Entity: {node['id']} ({list(node.labels)[0]}) - Details: {node.get('content', '')}")
                    
                    rel = record["r"]
                    target = record["m"]
                    if rel and target:
                        context_parts.append(f"Relation: {node['id']} -[{rel.type}]-> {target['id']}")
        
        return "\n".join(list(set(context_parts)))

graph_service = GraphService()

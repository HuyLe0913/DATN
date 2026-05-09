from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FinancialChunkORM(Base):
    __tablename__ = "financial_chunks"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    symbol = Column(String, index=True)
    year = Column(Integer, index=True)
    quarter = Column(String, index=True)
    header_path = Column(String) # e.g., "H1 > H2 > H3"
    raw_content = Column(Text)
    chunk_text = Column(Text) # The same as raw_content, but maybe processed
    enriched_text = Column(Text) # Summary + Raw

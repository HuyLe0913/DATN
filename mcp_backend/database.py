import os
import weaviate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mcp_backend.models import Base
from dotenv import load_dotenv

load_dotenv()

# --- PostgreSQL Configuration ---
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@postgres-db:5432/ews_rag")

import time
print(f"Connecting to PostgreSQL: {POSTGRES_URL}")

def get_engine_with_retry(url, retries=20, delay=5):
    for i in range(retries):
        try:
            # Try to resolve hostname manually for debug
            import socket
            hostname = url.split("@")[1].split(":")[0]
            ip = socket.gethostbyname(hostname)
            print(f"Resolved {hostname} to {ip}")
            
            engine = create_engine(url)
            # Test connection
            with engine.connect() as conn:
                print("Database connection successful!")
            return engine
        except Exception as e:
            print(f"Connection attempt {i+1} failed: {e}")
            if i < retries - 1:
                time.sleep(delay)
    raise Exception("Could not connect to database after several retries.")

engine = get_engine_with_retry(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_postgres():
    print("Initializing PostgreSQL tables...")
    Base.metadata.create_all(bind=engine)
    print("PostgreSQL tables initialized.")

# --- Weaviate Configuration ---
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")

_weaviate_client = None

def get_weaviate_client():
    global _weaviate_client
    if _weaviate_client is None:
        print(f"Opening persistent connection to Weaviate: {WEAVIATE_URL}")
        _weaviate_client = weaviate.connect_to_local(
            host="weaviate",
            port=8080,
            grpc_port=50051,
        )
    return _weaviate_client

def close_weaviate_client():
    global _weaviate_client
    if _weaviate_client is not None:
        _weaviate_client.close()
        _weaviate_client = None

def init_weaviate():
    print("Initializing Weaviate collection...")
    client = get_weaviate_client()
    try:
        # For development: Check if we need to recreate the collection
        # if client.collections.exists("FinancialReport"):
        #     client.collections.delete("FinancialReport")
            
        if not client.collections.exists("FinancialReport"):
            client.collections.create(
                name="FinancialReport",
                properties=[
                    weaviate.classes.config.Property(name="text", data_type=weaviate.classes.config.DataType.TEXT), # Combined for search
                    weaviate.classes.config.Property(name="summary", data_type=weaviate.classes.config.DataType.TEXT),
                    weaviate.classes.config.Property(name="content", data_type=weaviate.classes.config.DataType.TEXT),
                    weaviate.classes.config.Property(name="symbol", data_type=weaviate.classes.config.DataType.TEXT),
                    weaviate.classes.config.Property(name="year", data_type=weaviate.classes.config.DataType.INT),
                    weaviate.classes.config.Property(name="quarter", data_type=weaviate.classes.config.DataType.TEXT),
                    weaviate.classes.config.Property(name="file_name", data_type=weaviate.classes.config.DataType.TEXT),
                    weaviate.classes.config.Property(name="header_path", data_type=weaviate.classes.config.DataType.TEXT),
                ],
                vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none()
            )
            print("Weaviate collection 'FinancialReport' created.")
        else:
            print("Weaviate collection 'FinancialReport' already exists.")
    finally:
        close_weaviate_client()
    print("Weaviate initialization done.")

if __name__ == "__main__":
    init_postgres()
    print("PostgreSQL initialized.")
    # Weaviate initialization might fail if not in Docker network, 
    # but we will call it from the app container.

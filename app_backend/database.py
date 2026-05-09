import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Cấu hình URL kết nối PostgreSQL (Async)
# Mặc định trỏ vào service 'db' trong docker-compose
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@db:5432/financial_agent"
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with async_session() as session:
        yield session

async def init_db():
    from models import Base
    async with engine.begin() as conn:
        # Trong thực tế nên dùng Alembic, nhưng ở đây khởi tạo nhanh bằng create_all
        await conn.run_sync(Base.metadata.create_all)

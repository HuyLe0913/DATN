from __future__ import annotations
import os
from celery import Celery

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery_app = Celery(
    "financial_rag",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["mcp_backend.services.ingestion", "mcp_backend.services.ocr"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

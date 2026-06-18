# Financial Investment Agent - DATN

Hệ thống AI Agent hỗ trợ phân tích báo cáo tài chính, gồm pipeline ingestion/RAG, chat backend và giao diện web.

## Kiến trúc dự án

- `agent_core/`: Agent orchestration, tools integration, CLI và API stream cho hội thoại.
- `mcp_backend/`: Dịch vụ ingestion/retrieval, MCP endpoint, Celery tasks cho OCR + graph/vector.
- `app_backend/`: Chat/session backend (FastAPI + SQLAlchemy async), lưu lịch sử hội thoại.
- `frontend/`: Ứng dụng Next.js chat UI.
- `data/`: Dữ liệu vào/ra cho pipeline xử lý báo cáo.
- `docker-compose.yml`: Orchestration toàn bộ services (Redis, MinIO, Weaviate, Neo4j, Postgres, workers, APIs, frontend).

## Luồng xử lý chat

1. Frontend gọi `POST /api/chat`.
2. `app_backend` lưu user message theo `chatId`.
3. `app_backend` gọi `agent_core` qua `AGENT_URL`.
4. `agent_core` stream phản hồi (`THOUGHT`/`FINAL`) về frontend.

## Chạy nhanh bằng Docker (khuyến nghị)

1. Tạo file `.env` từ mẫu:

```bash
cp .env.example .env
```

2. Điền các API key bắt buộc trong `.env`:

- `OPENROUTER_API_KEY`
- `MISTRAL_API_KEY`
- (tuỳ chọn) `TAVILY_API_KEY`

3. Khởi động toàn bộ stack:

```bash
docker-compose up --build
```

4. Truy cập:

- Frontend: `http://localhost:3000`
- App backend (chat sessions): `http://localhost:8000`
- MCP/RAG backend: `http://localhost:8001`
- Agent core API: `http://localhost:8002`

## Chạy riêng Agent Core (CLI)

```bash
cd agent_core
pip install -r requirements.txt
python main.py
```

Biến môi trường tối thiểu cho `agent_core`:

```bash
OPENROUTER_API_KEY=your_key_here
AGENT_MODEL_NAME=openrouter/google/gemini-2.0-flash-lite:free
```

## Ghi chú kỹ thuật

- Endpoint chat frontend chuẩn là `frontend/app/api/chat/route.ts`.
- `frontend/app/api/agent-v3/route.ts` giữ lại để tương thích ngược và đã forward sang route chuẩn.
- `app_backend` đọc URL agent từ biến môi trường `AGENT_URL`.

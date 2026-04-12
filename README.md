# Financial Investment Agent - DATN

Hệ thống Agent thông minh hỗ trợ phân tích đầu tư tài chính.

## Cấu trúc dự án
- `agent_core/`: Bộ khung Agent lõi, Orchestrator và Tools.
- `backend/`: API và Xử lý hậu cần (FastAPI, Celery).
- `data/`: Dữ liệu báo cáo tài chính (raw & processed).
- `notebooks/`: Các file nghiên cứu và cào dữ liệu.

## Hướng dẫn chạy Agent Core (CLI)

### 1. Cài đặt môi trường
Đảm bảo bạn đã cài đặt Python 3.9+ và các thư viện cần thiết:
```bash
cd agent_core
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Tạo file `.env` bên trong folder `agent_core/` (hoặc chỉnh sửa file có sẵn):
```bash
OPENROUTER_API_KEY=your_key_here
MODEL_NAME=openrouter/google/gemini-2.5-flash-lite
```

### 3. Chạy Agent
Chạy file giao diện dòng lệnh interactive:
```bash
python main.py
```

## Chạy toàn bộ hệ thống (Docker)
Để khởi chạy API, Database và các Worker:
```bash
docker-compose up --build
```
Log của các worker sẽ hiển thị quá trình xử lý báo cáo tài chính từ thư mục `data/`.
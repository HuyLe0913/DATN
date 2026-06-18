FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Chạy API server của agent trên port 8002
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8002"]

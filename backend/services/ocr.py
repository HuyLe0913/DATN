import os
import tempfile
from celery import shared_task
from backend.services.s3_utils import download_file, upload_file

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

@shared_task(name="process_pdf_ocr", queue="ocr-queue")
def process_pdf_ocr(pdf_s3_key: str):
    from mistralai.client import Mistral
    from backend.services.ingestion import ingest_from_s3
    print(f"Starting OCR for {pdf_s3_key} using Mistral...")
    
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Download PDF from MinIO
        pdf_path = os.path.join(tmpdir, "input.pdf")
        download_file("pdfs", pdf_s3_key, pdf_path)
        
        # 2. Upload PDF to Mistral
        print("Uploading PDF to Mistral...")
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            mistral_file = client.files.upload(
                file={
                    "file_name": os.path.basename(pdf_s3_key),
                    "content": pdf_data,
                },
                purpose="ocr"
            )
        
        file_id = mistral_file.id
        print(f"File uploaded to Mistral with ID: {file_id}")
        
        # 3. Call Mistral OCR using file ID
        print(f"Starting Mistral OCR processing for file_id: {file_id}...")
        import requests
        
        ocr_url = "https://api.mistral.ai/v1/ocr"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        # Fixed schema: type='file', and key is 'file_id'
        payload = {
            "model": "mistral-ocr-latest",
            "document": {"type": "file", "file_id": file_id}
        }
        
        try:
            response = requests.post(ocr_url, json=payload, headers=headers)
            response.raise_for_status()
            ocr_response = response.json()
        except requests.exceptions.HTTPError as e:
            print(f"API Error Response: {e.response.text}")
            raise
        
        # 4. Clean up file from Mistral
        try:
            client.files.delete(file_id=file_id)
            print(f"Deleted temporary file {file_id} from Mistral.")
        except Exception as e:
            print(f"Warning: Failed to delete Mistral file {file_id}: {e}")
        
        # 5. Extract Markdown from OCR Result
        print("Extracting Markdown...")
        full_markdown = ""
        for page in ocr_response.get("pages", []):
            full_markdown += page.get("markdown", "") + "\n\n"
        
        if not full_markdown:
            full_markdown = f"OCR Result Placeholder (Empty response)\n{str(ocr_response)}"
        
        markdown_content = full_markdown
        
        # 5. Save Markdown to MinIO
        md_file_name = pdf_s3_key.replace(".pdf", ".md")
        md_path = os.path.join(tmpdir, md_file_name)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        upload_file(md_path, "markdowns", md_file_name)
        print(f"OCR completed. Markdown saved to markdowns/{md_file_name}")
        
        # 6. Trigger Ingestion (S3 based)
        ingest_from_s3.delay(md_file_name)

    return md_file_name

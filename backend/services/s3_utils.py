import os
import boto3
from botocore.client import Config

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

def upload_file(file_path, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)
    s3_client.upload_file(file_path, bucket, object_name)
    return object_name

def download_file(bucket, object_name, file_path):
    s3_client.download_file(bucket, object_name, file_path)
    return file_path

def get_file_content(bucket, object_name):
    response = s3_client.get_object(Bucket=bucket, Key=object_name)
    return response["Body"].read().decode("utf-8")

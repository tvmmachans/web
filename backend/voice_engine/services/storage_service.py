import os
import boto3
from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
import logging
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.use_minio = os.getenv("USE_MINIO", "true").lower() == "true"

        if self.use_minio:
            self.minio_client = Minio(
                os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                secure=False,
            )
            self.bucket_name = os.getenv("MINIO_BUCKET", "voice-engine")
            self._ensure_bucket_exists()
        else:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
            self.bucket_name = os.getenv("S3_BUCKET", "voice-engine-bucket")

    def _ensure_bucket_exists(self):
        """Ensure MinIO bucket exists"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")

    async def upload_audio(
        self, file_data: bytes, filename: str, content_type: str = "audio/wav"
    ) -> str:
        """Upload audio file and return URL"""
        try:
            file_id = str(uuid.uuid4())
            key = f"audio/{file_id}/{filename}"

            if self.use_minio:
                # Upload to MinIO
                from io import BytesIO

                data = BytesIO(file_data)
                self.minio_client.put_object(
                    self.bucket_name,
                    key,
                    data,
                    len(file_data),
                    content_type=content_type,
                )
                url = f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{self.bucket_name}/{key}"
            else:
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_data,
                    ContentType=content_type,
                )
                url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"

            logger.info(f"Uploaded audio file: {key}")
            return url

        except Exception as e:
            logger.error(f"Audio upload failed: {e}")
            raise

    async def upload_video(
        self, file_data: bytes, filename: str, content_type: str = "video/mp4"
    ) -> str:
        """Upload video file and return URL"""
        try:
            file_id = str(uuid.uuid4())
            key = f"video/{file_id}/{filename}"

            if self.use_minio:
                from io import BytesIO

                data = BytesIO(file_data)
                self.minio_client.put_object(
                    self.bucket_name,
                    key,
                    data,
                    len(file_data),
                    content_type=content_type,
                )
                url = f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{self.bucket_name}/{key}"
            else:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_data,
                    ContentType=content_type,
                )
                url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"

            logger.info(f"Uploaded video file: {key}")
            return url

        except Exception as e:
            logger.error(f"Video upload failed: {e}")
            raise

    async def download_file(self, file_url: str) -> bytes:
        """Download file from storage"""
        try:
            if self.use_minio:
                # Extract key from MinIO URL
                key = file_url.split(f"/{self.bucket_name}/")[1]
                response = self.minio_client.get_object(self.bucket_name, key)
                return response.read()
            else:
                # Extract key from S3 URL
                key = file_url.split(f"{self.bucket_name}.s3.amazonaws.com/")[1]
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                return response["Body"].read()

        except Exception as e:
            logger.error(f"File download failed: {e}")
            raise

    async def delete_file(self, file_url: str):
        """Delete file from storage"""
        try:
            if self.use_minio:
                key = file_url.split(f"/{self.bucket_name}/")[1]
                self.minio_client.remove_object(self.bucket_name, key)
            else:
                key = file_url.split(f"{self.bucket_name}.s3.amazonaws.com/")[1]
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)

            logger.info(f"Deleted file: {file_url}")

        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            raise

    async def get_presigned_url(self, file_url: str, expiration: int = 3600) -> str:
        """Generate presigned URL for temporary access"""
        try:
            if self.use_minio:
                key = file_url.split(f"/{self.bucket_name}/")[1]
                url = self.minio_client.presigned_get_object(
                    self.bucket_name, key, expires=expiration
                )
                return url
            else:
                key = file_url.split(f"{self.bucket_name}.s3.amazonaws.com/")[1]
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": key},
                    ExpiresIn=expiration,
                )
                return url

        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            raise


# Global storage service instance
storage_service = StorageService()

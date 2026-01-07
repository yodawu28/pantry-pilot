import uuid
from io import BytesIO
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException
from app.config import settings

class MinioService:
    """Service for MinIO object store"""

    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )

        self.bucket = settings.minio_bucket
        self._ensure_bucket()


    async def upload_file(self, file: UploadFile) -> str:
        """Upload file to MinIO"""
        self._validate_file_upload(file)

        # Generate unique filename
        file_ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
        object_name = f"{uuid.uuid4()}.{file_ext}"

        try:
            # Read file content
            contents = await file.read()

            # upload to MinIO
            self.client.put_object(
                self.bucket,
                object_name,
                data=BytesIO(contents),
                length=len(contents),
                content_type=file.content_type or "application/octet-stream",
            )
            
            return f"minio://{self.bucket}/{object_name}"
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate URL: {str(e)}")



    def _ensure_bucket(self):
        """Create bucket if not exists"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"✅ Created MinIO bucket: {self.bucket}")
        except S3Error as e:
            print(f"⚠️  MinIO bucket check failed: {e}")

    def _validate_file_upload(self, file: UploadFile):
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed ")
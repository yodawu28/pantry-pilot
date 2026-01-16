import io
import base64
from minio import Minio, S3Error
from app.config import settings
from shared.types import ImageData
from PIL import Image

class MinioClient:
    """MinIO client wrapper"""

    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )

    def get_object_bytes(self, object_name: str) -> bytes:
        """Fetch object from MinIO."""
        try:
            response = self.client.get_object(settings.minio_bucket, object_name=object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise RuntimeError(f"Failed to fetch from MinIO: {e}")

async def get_image_from_storage(image_path: str) -> ImageData:
    """
    MCP Tool: Fetch image from MinIO storage.
    
    Args:
        image_path: MinIO path (format: "minio://bucket/object_name")
    Returns:
        ImageData with image bytes and metadata
    """

    # Parsed path
    if not image_path.startswith(settings.storage_minio_prefix):
        raise ValueError(f"Invalid MinIO path: {image_path}")
    
    parts = image_path.replace(settings.storage_minio_prefix, "").split("/", 1)

    if len(parts) != 2:
        raise ValueError(f"Invalid MinIO path format: {image_path}")


    bucket_name, object_name = parts

    # Fetch from MinIO
    client = MinioClient()
    image_bytes = client.get_object_bytes(object_name=object_name)

    # Get image metadata
    image = Image.open(io.BytesIO(image_bytes))
    content_type = f"image/{image.format.lower()}" if image.format else "image/jpeg"

    # Base64 encode for JSON serialization
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    return ImageData(
        image_base64=image_base64,
        content_type=content_type,
        size_bytes=len(image_bytes),
        width=image.width,
        height=image.height
    )
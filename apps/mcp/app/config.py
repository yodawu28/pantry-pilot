
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP server settings"""
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")

    # Server
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001


    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "receipts"
    minio_secure: bool = False

    # Database (for context)
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/pantry_pilot"

    # Tool settings
    extraction_timeout_seconds: int = 30
    confidence_threshold: float = 0.7
    max_image_size_mb: int = 10

    storage_minio_prefix: str = "minio://"


settings = Settings()

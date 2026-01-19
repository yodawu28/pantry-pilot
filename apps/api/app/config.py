from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pantry_pilot"

    # Agent URL
    agent_url: str = "http://localhost:8002"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "receipts"
    minio_secure: bool = False

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Redis Queue
    redis_host: str = "localhost"
    redis_port: int = 6379

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()

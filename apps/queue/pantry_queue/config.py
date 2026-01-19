"""Queue Service Configuration"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Queue service settings from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    # Queue settings
    queue_name: str = "pantry-pilot"
    default_timeout: int = 600  # 10 minutes
    result_ttl: int = 3600  # 1 hour
    failure_ttl: int = 86400  # 24 hours

    # Agent service (use localhost for local dev, agent for Docker)
    agent_url: str = "http://localhost:8002"

    # Database (use localhost for local dev, postgres for Docker)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pantry_pilot"

    # Worker settings
    worker_name: str | None = None
    burst_mode: bool = False  # For testing


settings = Settings()

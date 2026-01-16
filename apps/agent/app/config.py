from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars
    )

    # Server
    agent_host: str = "0.0.0.0"
    agent_port: int = 8002

    # MCP Server
    mcp_url: str = "http://localhost:8001"

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"  # gpt-4o, gpt-4-turbo, gpt-4-vision-preview
    openai_temperature: float = 0.0
    openai_max_tokens: int = 4096

    # Vision/OCR
    vision_enabled: bool = True
    image_preprocessing: bool = True
    max_image_size: int = 2048

    # Agent behavior
    confidence_threshold: float = 0.7
    max_retries: int = 2
    timeout_seconds: int = 30

    # Format
    image_format: list[str] = ["JPEG", "PNG", "WEBP"]


settings = Settings()
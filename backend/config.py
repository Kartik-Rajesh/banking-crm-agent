"""Application configuration and environment settings."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    groq_api_key: str = ""
    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    database_url: str = "sqlite:///./banking_crm.db"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    log_level: str = "INFO"
    app_name: str = "Banking CRM Agent"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

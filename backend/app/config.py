"""
Configuration management for QueryDawg backend.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # API Configuration
    api_key: str = os.getenv("API_KEY", "dev-querydawg-api-key-2024")
    environment: str = os.getenv("ENVIRONMENT", "development")

    # LLM Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")  # For metadata API
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Database URL for direct PostgreSQL connection (Spider databases + metadata)
    database_url: str = os.getenv("DATABASE_URL", "")

    # Database Configuration (for Spider databases - local for now)
    spider_db_path: Path = Path(os.getenv("SPIDER_DATA_PATH", "data/spider/database"))

    # CORS Configuration
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures we only create one Settings instance.
    """
    return Settings()

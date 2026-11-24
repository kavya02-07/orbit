"""
Orbit Backend — Application Configuration
Loads settings from .env using pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Security
    secret_key: str = "changeme-generate-a-real-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = "sqlite:///./orbit.db"

    # Storage
    faiss_index_path: str = "./data/faiss_index"
    upload_dir: str = "./data/uploads"

    # Models
    embedding_model: str = "all-MiniLM-L6-v2"
    gemini_model: str = "gemini-1.5-flash"
    gemini_api_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Retrieval
    retrieval_top_k: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()

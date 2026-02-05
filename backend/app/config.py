from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "coderev-ai"
    app_env: str = "development"
    secret_key: str = "super-secret-key-change-in-production"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://coderev:coderev_secret@localhost:5432/coderev_ai"
    sync_database_url: str = "postgresql://coderev:coderev_secret@localhost:5432/coderev_ai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # GitHub OAuth
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"
    github_webhook_secret: str = "webhook-secret"

    # Anthropic
    anthropic_api_key: str = ""

    # JWT
    jwt_secret_key: str = "jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

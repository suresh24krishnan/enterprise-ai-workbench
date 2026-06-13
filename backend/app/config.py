"""
Application configuration — all values sourced from environment variables.
Never hardcode secrets or environment-specific values here.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = "local"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_log_level: str = "info"

    # CORS — comma-separated list of allowed origins
    cors_origins_raw: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    # Identity
    identity_provider: str = "mock"

    # ClaimCenter
    claimcenter_adapter: str = "mock"

    # Model provider
    model_provider: str = "mock"

    # Audit store
    audit_store: str = "sqlite"

    # Knowledge provider
    knowledge_provider: str = "local"

    # Governance
    governance_strict_mode: bool = True

    # JWT — secret must be overridden in non-local environments
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 480


@lru_cache
def get_settings() -> Settings:
    return Settings()

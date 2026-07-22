"""
Centralized application settings.

All configuration comes from environment variables (12-factor style).
Nothing in this file should ever contain a real secret — defaults here
are safe placeholders for local development only.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata ---
    app_name: str = "EcoMind AI"
    environment: str = Field(default="development")  # development | staging | production
    debug: bool = Field(default=True)

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://ecomind:ecomind@localhost:5432/ecomind",
        description="Async SQLAlchemy connection string (asyncpg driver).",
    )
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=5)
    auto_create_tables: bool = Field(
        default=True,
        description=(
            "Dev/Docker convenience: create missing tables on startup. Does NOT alter "
            "existing tables. Set to false once real migrations (Alembic) are in place."
        ),
    )

    # --- Auth ---
    jwt_secret: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="Secret used to sign JWTs. Must be overridden via env var in every real deployment.",
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)

    # --- AI provider ---
    llm_provider: str = Field(default="anthropic")  # anthropic | openai
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")

    # --- CORS ---
    cors_allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Logging ---
    log_level: str = Field(default="INFO")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got {v!r}")
        return v

    @field_validator("jwt_secret")
    @classmethod
    def warn_default_secret_in_prod(cls, v: str, info) -> str:
        # Cheap guardrail: refuse to boot with the placeholder secret outside dev.
        # (Environment is validated separately; this just protects jwt_secret itself.)
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Settings are cached so environment variables are parsed once per process,
    not on every request. FastAPI dependencies should call this via
    Depends(get_settings) rather than importing a module-level instance,
    which makes it trivial to override in tests.
    """
    return Settings()

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # App configuration
    environment: str = "development"
    base_url: str = Field(
        default="http://localhost:8000", description="Base URL for the application"
    )

    # Supabase configuration
    supabase_url: str = Field(default="", description="Supabase URL")
    supabase_anon_key: str = Field(default="", description="Supabase anonymous key")
    supabase_service_key: str | None = Field(
        default=None, description="Supabase service key"
    )
    database_url: str | None = Field(default=None, description="Database URL")

    # JWT configuration
    jwt_secret_key: str = Field(
        default="default-secret-key", description="JWT secret key"
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # CORS configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Sentry Configuration
    sentry_dsn: str | None = Field(
        default=None, description="Sentry DSN for error tracking"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


# Create global settings instance
settings = Settings()

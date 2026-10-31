from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    app_name: str = "MealMate India API"
    environment: str = "development"
    supabase_url: str = Field(
        default="",
        validation_alias="SUPABASE_URL",
    )
    supabase_anon_key: str = Field(
        default="",
        validation_alias="SUPABASE_ANON_KEY",
    )
    admin_bootstrap_email: str = Field(
        default="",
        validation_alias="ADMIN_BOOTSTRAP_EMAIL",
    )
    cors_origins: str = Field(
        default="",
        validation_alias="CORS_ORIGINS",
    )
    database_url: str = Field(
        default="postgresql+psycopg://localhost:5432/mealmate",
        validation_alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MEALMATE_",
        extra="ignore",
    )

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        """Accept only comma-separated, exact HTTP(S) origins."""
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        for origin in origins:
            parsed = urlparse(origin)
            try:
                has_valid_port = parsed.port is not None or parsed.netloc
            except ValueError as exc:
                raise ValueError("CORS_ORIGINS contains an invalid origin") from exc
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or not has_valid_port
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.params
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("CORS_ORIGINS must contain exact HTTP(S) origins")
        return ",".join(origins)

    def get_cors_origins(self) -> list[str]:
        """Return allowed origins, with local defaults only in development."""
        configured = [origin for origin in self.cors_origins.split(",") if origin]
        if self.environment.lower() in {"development", "dev", "local"}:
            return list(dict.fromkeys([*configured, "http://localhost:5173", "http://127.0.0.1:5173"]))
        if not configured:
            raise ValueError("CORS_ORIGINS must be configured outside development")
        return configured


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings object for the application process."""
    return Settings()

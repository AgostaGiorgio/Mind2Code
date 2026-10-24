from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    database_url: str = Field(..., description="PostgreSQL async connection URI (postgresql+asyncpg://...)")

    log_level: str = Field(default="INFO", description="Python logging level")

    enable_progress_polling: bool = Field(
        default=True,
        description="Poll PostgreSQL for externally written progress updates and broadcast them over SSE",
    )
    poll_interval_seconds: float = Field(
        default=2.0,
        gt=0,
        description="Seconds between PostgreSQL progress polls",
    )

    n8n_finalize_webhook_url: str | None = Field(
        default=None,
        description="n8n webhook URL invoked to start a project finalization",
    )
    finalize_webhook_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        description="Timeout for the n8n finalize webhook call",
    )

    app_url: str = "http://localhost:8000"
    orbit_api_url: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @classmethod
    def load_from_yaml(cls, yaml_path: str = "config.yaml") -> "AppConfig":
        with open(yaml_path, "r") as file:
            yaml_data = yaml.safe_load(file)
            if not yaml_data:
                yaml_data = {}
        return cls(**yaml_data)


app_config = AppConfig.load_from_yaml()

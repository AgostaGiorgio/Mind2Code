from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    postgresql_user: str = Field(..., description="PostgreSQL user")
    postgresql_password: str = Field(..., description="PostgreSQL password")
    postgresql_host: str = Field(..., description="PostgreSQL host")
    postgresql_port: str = Field(..., description="PostgreSQL port")
    postgresql_database: str = Field(..., description="PostgreSQL database name")

    @property
    def postgresql_connection_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgresql_user}:{self.postgresql_password}@"
            f"{self.postgresql_host}:{self.postgresql_port}/{self.postgresql_database}"
        )

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
    n8n_project_title_webhook_url: str | None = Field(
        default=None,
        description="n8n webhook URL that extracts the project title from the user input",
    )
    n8n_requirements_webhook_url: str | None = Field(
        default=None,
        description="n8n webhook URL that starts requirements generation for a project",
    )
    n8n_code_webhook_url: str | None = Field(
        default=None,
        description="n8n webhook URL that starts the code phase",
    )
    n8n_test_webhook_url: str | None = Field(
        default=None,
        description="n8n webhook URL that starts the test phase",
    )
    n8n_review_webhook_url: str | None = Field(
        default=None,
        description="n8n webhook URL that starts the review phase",
    )
    n8n_retrospective_webhook_url: str | None = Field(
        default=None,
        description="n8n webhook URL that starts the retrospective phase",
    )
    n8n_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        description="Timeout shared by every n8n webhook call",
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

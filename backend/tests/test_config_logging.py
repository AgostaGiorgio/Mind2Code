"""Config, DI container and logging helper tests (T-2, T-11)."""

import logging

import pytest
from dependency_injector import providers

from src.config.app_config import AppConfig
from src.config.logger import configure_logging
from src.di import Container
from src.main import APP_VERSION, app, container


PG = {
    "postgresql_user": "u",
    "postgresql_password": "p",
    "postgresql_host": "h",
    "postgresql_port": "5432",
    "postgresql_database": "db",
}


def test_cors_origins_parsed_from_comma_string():
    config = AppConfig(**PG, cors_origins="http://a, http://b ")
    assert config.cors_origins == ["http://a", "http://b"]


def test_cors_origins_accepts_list():
    config = AppConfig(**PG, cors_origins=["http://a"])
    assert config.cors_origins == ["http://a"]


def test_postgresql_connection_uri_from_parts():
    config = AppConfig(**PG)
    assert config.postgresql_connection_uri == "postgresql+asyncpg://u:p@h:5432/db"


def test_load_from_yaml(tmp_path):
    yaml_file = tmp_path / "cfg.yaml"
    yaml_file.write_text(
        "postgresql_user: u\n"
        "postgresql_password: p\n"
        "postgresql_host: h\n"
        "postgresql_port: '5432'\n"
        "postgresql_database: db\n"
    )
    config = AppConfig.load_from_yaml(str(yaml_file))
    assert config.postgresql_connection_uri == "postgresql+asyncpg://u:p@h:5432/db"


def test_load_from_empty_yaml(tmp_path):
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("")
    config = AppConfig.load_from_yaml(str(yaml_file))
    # Falls back to the environment (.env) for the required POSTGRESQL_* fields.
    assert config.postgresql_connection_uri.startswith("postgresql+asyncpg://")


def test_container_wires_providers():
    c = Container()
    assert isinstance(c.project_service, providers.Factory)
    service = c.project_service()
    from src.services.projects import ProjectService

    assert isinstance(service, ProjectService)
    assert c.event_broker() is c.event_broker()  # singleton


def test_app_version_and_routes_registered():
    assert APP_VERSION
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/api/v1/projects" in paths
    assert "/api/v1/events" in paths
    assert "/api/v1/projects/{project_id}/progress" in paths


def test_container_override_project_repository():
    c = Container()
    sentinel = object()
    c.project_repository.override(providers.Object(sentinel))
    assert c.project_repository() is sentinel
    c.project_repository.reset_override()


def test_postgres_client_session_context_manager():
    import asyncio

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.clients.postgres_client import PostgresClient

    client = PostgresClient("postgresql+asyncpg://u:p@localhost:5432/db")

    async def use_session():
        async with client.async_session() as session:
            return isinstance(session, AsyncSession)

    assert asyncio.run(use_session()) is True


def test_progress_validator_direct_call():
    from src.db.models.project import ProgressUpdateRequest

    with pytest.raises(ValueError):
        ProgressUpdateRequest._validate_percentage(200)


def test_configure_logging_sets_json_handler():
    configure_logging("DEBUG")
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1
    handler = root.handlers[0]
    assert handler.formatter is not None

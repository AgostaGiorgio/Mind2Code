from dependency_injector import containers, providers

from src.clients.n8n_client import N8NClient
from src.clients.postgres_client import PostgresClient
from src.config.app_config import app_config
from src.repositories.projects import ProjectRepository
from src.services.progress_poller import ProgressPoller
from src.services.projects import ProjectService
from src.sse.broker import EventBroker


class Container(containers.DeclarativeContainer):
    postgres_client = providers.Singleton(
        PostgresClient, db_url=app_config.postgresql_connection_uri
    )

    event_broker = providers.Singleton(EventBroker)

    n8n_client = providers.Singleton(
        N8NClient,
        finalize_url=app_config.n8n_finalize_webhook_url,
        project_title_url=app_config.n8n_project_title_webhook_url,
        requirements_url=app_config.n8n_requirements_webhook_url,
        code_url=app_config.n8n_code_webhook_url,
        test_url=app_config.n8n_test_webhook_url,
        review_url=app_config.n8n_review_webhook_url,
        retrospective_url=app_config.n8n_retrospective_webhook_url,
        timeout_seconds=app_config.n8n_timeout_seconds,
    )

    project_repository = providers.Factory(
        ProjectRepository, postgres_client=postgres_client
    )

    project_service = providers.Factory(
        ProjectService,
        project_repository=project_repository,
        event_broker=event_broker,
        n8n_client=n8n_client,
    )

    progress_poller = providers.Factory(
        ProgressPoller,
        project_repository=project_repository,
        event_broker=event_broker,
        interval_seconds=app_config.poll_interval_seconds,
    )

from dependency_injector import containers, providers

from src.clients.finalize_webhook import FinalizeWebhookClient
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

    finalize_webhook = providers.Singleton(
        FinalizeWebhookClient,
        url=app_config.n8n_finalize_webhook_url,
        timeout_seconds=app_config.finalize_webhook_timeout_seconds,
    )

    project_repository = providers.Factory(
        ProjectRepository, postgres_client=postgres_client
    )

    project_service = providers.Factory(
        ProjectService,
        project_repository=project_repository,
        event_broker=event_broker,
        finalize_webhook=finalize_webhook,
    )

    progress_poller = providers.Factory(
        ProgressPoller,
        project_repository=project_repository,
        event_broker=event_broker,
        interval_seconds=app_config.poll_interval_seconds,
    )

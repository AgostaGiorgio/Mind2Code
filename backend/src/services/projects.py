import logging
from enum import Enum

from src.clients.finalize_webhook import FinalizeWebhookClient
from src.db.models.project import (
    ProgressEvent,
    ProgressUpdateRequest,
    Project,
    ProjectDetail,
    ProjectNameUpdateRequest,
)
from src.repositories.projects import ProjectRepository
from src.sse.broker import EventBroker

logger = logging.getLogger(__name__)


class FinalizeResult(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    WEBHOOK_FAILED = "webhook_failed"
    NOT_CONFIGURED = "not_configured"


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        event_broker: EventBroker,
        finalize_webhook: FinalizeWebhookClient,
    ):
        self.__project_repository = project_repository
        self.__event_broker = event_broker
        self.__finalize_webhook = finalize_webhook

    async def list_projects(self) -> list[Project]:
        logger.debug("Fetching projects...")
        return await self.__project_repository.list_projects()

    async def get_project_detail(self, execution_id: int) -> ProjectDetail | None:
        logger.debug(f"Fetching project detail for execution_id {execution_id}...")
        return await self.__project_repository.get_project_detail(execution_id)

    async def rename_project(
        self, execution_id: int, payload: ProjectNameUpdateRequest
    ) -> ProjectDetail | None:
        logger.debug(f"Renaming project {execution_id} to '{payload.name}'...")
        return await self.__project_repository.update_name(execution_id, payload.name)

    async def finalize_project(self, execution_id: int) -> FinalizeResult:
        logger.debug(f"Requesting finalization for execution_id {execution_id}...")

        # Atomically claim the request: only a fully complete, not-yet-finalized
        # project can be finalized.
        requested = await self.__project_repository.request_finalization(execution_id)
        if requested is None:
            existing = await self.__project_repository.get_project_detail(execution_id)
            return FinalizeResult.CONFLICT if existing else FinalizeResult.NOT_FOUND

        if not self.__finalize_webhook.configured:
            await self.__project_repository.reset_finalization(
                execution_id, "finalization is not configured"
            )
            return FinalizeResult.NOT_CONFIGURED

        triggered = await self.__finalize_webhook.trigger(execution_id)
        if not triggered:
            await self.__project_repository.reset_finalization(
                execution_id, "could not reach the finalization workflow"
            )
            return FinalizeResult.WEBHOOK_FAILED

        logger.info(f"Finalization started for execution_id {execution_id}.")
        return FinalizeResult.OK

    async def update_progress(
        self, execution_id: int, payload: ProgressUpdateRequest
    ) -> Project | None:
        logger.debug(f"Updating progress for execution_id {execution_id} to {payload.completion_percentage}%...")
        updated = await self.__project_repository.update_completion(
            execution_id, payload.completion_percentage
        )
        if updated is None:
            return None

        event = ProgressEvent(
            execution_id=updated.execution_id,
            completion_percentage=updated.completion_percentage,
        )
        await self.__event_broker.publish_progress(event)
        logger.info(
            f"Progress updated and broadcast for execution_id {execution_id}.",
            extra={"event": event.model_dump(by_alias=True)},
        )
        return updated

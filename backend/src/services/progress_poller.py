import asyncio
import logging
from datetime import datetime, timezone

from src.db.models.project import FinalizationEvent, ProgressEvent
from src.repositories.projects import ProjectRepository
from src.sse.broker import EventBroker

logger = logging.getLogger(__name__)


class ProgressPoller:
    """Background poller that bridges PostgreSQL changes to the SSE broker.

    Completion updates may be written directly to PostgreSQL by an external
    service instead of going through the HTTP API. This task periodically reads
    the rows whose ``updated_at`` moved past a watermark and republishes them as
    :class:`ProgressEvent` on the in-process :class:`EventBroker`, so connected
    SSE clients still receive live updates.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        event_broker: EventBroker,
        interval_seconds: float = 2.0,
    ):
        self.__project_repository = project_repository
        self.__event_broker = event_broker
        self.__interval_seconds = interval_seconds
        self.__watermark: datetime | None = None
        self.__task: asyncio.Task | None = None

    async def start(self) -> None:
        if self.__task is not None:
            return

        # Start from the newest row so we do not replay the whole history on boot;
        # a client that connects afterwards reloads the list via GET /api/v1/projects.
        self.__watermark = await self.__project_repository.get_latest_updated_at()
        if self.__watermark is None:
            self.__watermark = datetime.now(timezone.utc)
        self.__task = asyncio.create_task(self.__run())
        logger.info(
            f"Progress poller started (interval={self.__interval_seconds}s, "
            f"watermark={self.__watermark})."
        )

    async def stop(self) -> None:
        if self.__task is None:
            return
        self.__task.cancel()
        try:
            await self.__task
        except asyncio.CancelledError:
            pass
        self.__task = None
        logger.info("Progress poller stopped.")

    async def __run(self) -> None:
        while True:
            await asyncio.sleep(self.__interval_seconds)
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - a background loop must survive a bad tick
                logger.error("Progress poller tick failed.", exc_info=True)

    async def poll_once(self) -> None:
        since = self.__watermark
        if since is None:
            return

        projects = await self.__project_repository.list_updated_since(since)
        if not projects:
            return

        for project in projects:
            await self.__event_broker.publish_progress(
                ProgressEvent(
                    project_id=project.id,
                    completion_percentage=project.completion_percentage,
                    status=project.status,
                )
            )
            await self.__event_broker.publish_finalization(
                FinalizationEvent(
                    project_id=project.id,
                    finalization_percentage=project.finalization_percentage,
                    final_repo_url=project.final_repo_url,
                    finalize_error=project.finalize_error,
                )
            )

        self.__watermark = max(project.updated_at for project in projects)
        logger.debug(
            f"Progress poller published {len(projects)} event(s) up to {self.__watermark}.",
            extra={"watermark": self.__watermark.isoformat()},
        )

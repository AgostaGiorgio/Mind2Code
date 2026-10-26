import asyncio
import logging
from typing import Set
from uuid import UUID

from src.db.models.project import FinalizationEvent, ProgressEvent

logger = logging.getLogger(__name__)


class EventBroker:
    """In-process SSE fan-out broker.

    Subscribers receive an :class:`asyncio.Queue` of ``(event_name, payload)``
    tuples and are removed on disconnect. Consecutive duplicate values for the
    same ``(event_name, project_id)`` are collapsed.
    """

    def __init__(self, max_queue_size: int = 256):
        self.__max_queue_size = max_queue_size
        self.__subscribers: Set[asyncio.Queue] = set()
        self.__last_values: dict[tuple[str, UUID], object] = {}

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=self.__max_queue_size)
        self.__subscribers.add(queue)
        logger.debug(f"New SSE subscriber. Total subscribers: {len(self.__subscribers)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self.__subscribers.discard(queue)
        logger.debug(f"SSE subscriber removed. Total subscribers: {len(self.__subscribers)}")

    async def publish_progress(self, event: ProgressEvent) -> None:
        await self.__publish(
            "progress",
            event.project_id,
            event.completion_percentage,
            event.model_dump_json(by_alias=True),
        )

    async def publish_finalization(self, event: FinalizationEvent) -> None:
        await self.__publish(
            "finalization",
            event.project_id,
            event.finalization_percentage,
            event.model_dump_json(by_alias=True),
        )

    async def __publish(self, name: str, project_id: UUID, value: object, payload: str) -> None:
        key = (name, project_id)
        # Collapse duplicates: the API path can publish immediately while the DB
        # poller may observe the very same row change a moment later.
        if self.__last_values.get(key) == value:
            logger.debug(
                f"Skipping duplicate {name} event for project {project_id}."
            )
            return
        self.__last_values[key] = value

        if not self.__subscribers:
            return

        message = (name, payload)
        dead: list[asyncio.Queue] = []
        for queue in self.__subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead.append(queue)

        for queue in dead:
            self.unsubscribe(queue)

        logger.debug(
            f"Broadcast {name} event for project {project_id} "
            f"to {len(self.__subscribers)} subscriber(s)."
        )

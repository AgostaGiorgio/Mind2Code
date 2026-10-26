"""Progress poller tests: external Postgres writes -> SSE broker.

Covers the new ingestion path where an external service updates rows directly
in PostgreSQL and the backend still broadcasts a ``progress`` event.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.services.progress_poller import ProgressPoller
from src.sse.broker import EventBroker
from tests.conftest import FakeProjectRepository, make_project

PROJECT_ID = UUID("11111111-1111-4111-8111-111111111111")


def _repo_with(completion=40, updated_at=None):
    project = make_project(
        PROJECT_ID, "Alpha", completion=completion, updated_at=updated_at
    )
    return FakeProjectRepository([project]), project


def test_start_does_not_replay_backlog_on_boot():
    async def scenario():
        repo, _ = _repo_with(completion=40)
        broker = EventBroker()
        q = broker.subscribe()
        poller = ProgressPoller(repo, broker, interval_seconds=60)

        await poller.start()
        await poller.poll_once()
        await poller.stop()

        assert q.empty()

    asyncio.run(scenario())


def test_poll_publishes_externally_updated_rows():
    async def scenario():
        old = datetime.now(timezone.utc) - timedelta(minutes=5)
        repo, _ = _repo_with(completion=40, updated_at=old)
        broker = EventBroker()
        poller = ProgressPoller(repo, broker, interval_seconds=60)
        await poller.start()

        q = broker.subscribe()
        # Simulate an external writer updating the row directly in PostgreSQL.
        repo.projects[PROJECT_ID] = repo.projects[PROJECT_ID].model_copy(
            update={
                "completion_percentage": 75,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        await poller.poll_once()
        await poller.stop()

        assert q.get_nowait() == (
            "progress",
            f'{{"projectId":"{PROJECT_ID}","completionPercentage":75}}',
        )
        name, payload = q.get_nowait()
        assert name == "finalization"
        assert '"finalizationPercentage":0' in payload

    asyncio.run(scenario())


def test_poll_advances_watermark_without_republishing():
    async def scenario():
        old = datetime.now(timezone.utc) - timedelta(minutes=5)
        repo, project = _repo_with(completion=40, updated_at=old)
        broker = EventBroker()
        poller = ProgressPoller(repo, broker, interval_seconds=60)
        await poller.start()

        repo.projects[PROJECT_ID] = project.model_copy(
            update={
                "completion_percentage": 75,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        await poller.poll_once()

        # Second tick sees nothing new.
        q = broker.subscribe()
        await poller.poll_once()
        await poller.stop()

        assert q.empty()

    asyncio.run(scenario())

"""SSE event broker unit tests (T-7, FR-8, FR-16)."""

import asyncio
from uuid import UUID

from src.db.models.project import FinalizationEvent, ProgressEvent, ProjectStatus
from src.sse.broker import EventBroker

PROJECT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_PROJECT_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_progress_delivered_to_all_subscribers():
    broker = EventBroker()
    q1 = broker.subscribe()
    q2 = broker.subscribe()

    event = ProgressEvent(project_id=PROJECT_ID, completion_percentage=75)
    asyncio.run(broker.publish_progress(event))

    expected = (
        "progress",
        f'{{"projectId":"{PROJECT_ID}","completionPercentage":75,"status":null}}',
    )
    assert q1.get_nowait() == expected
    assert q2.get_nowait() == expected


def test_finalization_event_delivered():
    broker = EventBroker()
    q = broker.subscribe()

    asyncio.run(
        broker.publish_finalization(
            FinalizationEvent(project_id=PROJECT_ID, finalization_percentage=40)
        )
    )

    name, payload = q.get_nowait()
    assert name == "finalization"
    assert f'"projectId":"{PROJECT_ID}"' in payload
    assert '"finalizationPercentage":40' in payload


def test_unsubscribe_stops_delivery():
    broker = EventBroker()
    q1 = broker.subscribe()
    q2 = broker.subscribe()
    broker.unsubscribe(q2)

    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=50)
        )
    )

    assert not q1.empty()
    assert q2.empty()


def test_publish_without_subscribers_is_noop():
    broker = EventBroker()
    # Should not raise and should return immediately.
    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=1)
        )
    )


def test_full_queue_is_dropped_as_dead_subscriber():
    broker = EventBroker(max_queue_size=1)
    queue = broker.subscribe()

    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=10)
        )
    )
    # Second publish overflows the single-slot queue -> subscriber is dropped.
    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=20)
        )
    )

    assert queue.qsize() == 1
    assert queue.get_nowait() == (
        "progress",
        f'{{"projectId":"{PROJECT_ID}","completionPercentage":10,"status":null}}',
    )


def test_unsubscribe_unknown_queue_is_safe():
    broker = EventBroker()
    broker.unsubscribe(asyncio.Queue())  # must not raise


def test_duplicate_value_is_not_republished():
    broker = EventBroker()
    q = broker.subscribe()

    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=75)
        )
    )
    # The DB poller can observe the same change the API already published.
    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=75)
        )
    )
    assert q.qsize() == 1

    # A real change is still delivered.
    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=80)
        )
    )
    assert q.qsize() == 2


def test_same_value_for_different_project_ids_is_published():
    broker = EventBroker()
    q = broker.subscribe()

    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=75)
        )
    )
    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=OTHER_PROJECT_ID, completion_percentage=75)
        )
    )
    assert q.qsize() == 2


def test_same_completion_with_different_status_is_published():
    broker = EventBroker()
    q = broker.subscribe()

    asyncio.run(
        broker.publish_progress(
            ProgressEvent(
                project_id=PROJECT_ID,
                completion_percentage=40,
                status=ProjectStatus.CODE_RUNNING,
            )
        )
    )
    asyncio.run(
        broker.publish_progress(
            ProgressEvent(
                project_id=PROJECT_ID,
                completion_percentage=40,
                status=ProjectStatus.CODE_DONE,
            )
        )
    )

    assert q.qsize() == 2


def test_progress_and_finalization_are_deduped_independently():
    broker = EventBroker()
    q = broker.subscribe()

    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=100)
        )
    )
    asyncio.run(
        broker.publish_finalization(
            FinalizationEvent(project_id=PROJECT_ID, finalization_percentage=1)
        )
    )
    # Same completion value again -> dropped; the finalization value is untouched.
    asyncio.run(
        broker.publish_progress(
            ProgressEvent(project_id=PROJECT_ID, completion_percentage=100)
        )
    )

    assert q.qsize() == 2

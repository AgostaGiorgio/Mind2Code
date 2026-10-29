"""SSE endpoint tests (T-9).

Covers
------
US-3 / FR-8, FR-9 : streaming content type + progress event framing.
US-5 / FR-20      : periodic heartbeat keep-alive (timeout shrunk via shim).

The SSE endpoint is a streaming response that deliberately never ends, so these
tests drive the route's generator directly instead of through a streaming HTTP
client (which would block until the heartbeats eventually complete).
"""

import asyncio
from uuid import UUID

import pytest

from src.db.models.project import FinalizationEvent, ProgressEvent
from src.routers import router as router_module
from src.sse.broker import EventBroker

PROJECT_ID = UUID("11111111-1111-4111-8111-111111111111")


class FakeRequest:
    def __init__(self, disconnect_after: int | None = None):
        self.calls = 0
        self._disconnect_after = disconnect_after

    async def is_disconnected(self) -> bool:
        self.calls += 1
        if self._disconnect_after is None:
            return False
        return self.calls > self._disconnect_after


class PrefilledBroker(EventBroker):
    """Broker whose next subscription already contains one event."""

    def __init__(self, name: str, payload: str):
        super().__init__()
        self._message = (name, payload)

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        queue.put_nowait(self._message)
        self._EventBroker__subscribers.add(queue)
        return queue


class _FastAsyncio:
    """Shim replacing the module-level ``asyncio`` so the heartbeat fires fast."""

    TimeoutError = asyncio.TimeoutError
    QueueFull = asyncio.QueueFull

    def __init__(self, timeout: float):
        self._timeout = timeout

    async def wait_for(self, coro, timeout=None):
        return await asyncio.wait_for(coro, timeout=self._timeout)


def _response(broker, request):
    return asyncio.run(_call_route(broker, request))


async def _call_route(broker, request):
    # @inject wrapper: supply the broker explicitly so the container is bypassed.
    return await router_module.events_stream(request, event_broker=broker)


def test_sse_stream_headers_and_progress_framing(monkeypatch):
    monkeypatch.setattr(router_module, "asyncio", _FastAsyncio(0.05))
    payload = ProgressEvent(
        project_id=PROJECT_ID, completion_percentage=75
    ).model_dump_json(by_alias=True)
    broker = PrefilledBroker("progress", payload)
    response = _response(broker, FakeRequest())

    assert response.media_type == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"

    async def first_chunk():
        chunk = await response.body_iterator.__anext__()
        await response.body_iterator.aclose()
        return chunk

    chunk = asyncio.run(first_chunk())
    assert chunk == f"event: progress\ndata: {payload}\n\n"
    assert broker._EventBroker__subscribers == set()  # cleaned up on close


def test_sse_frames_finalization_event(monkeypatch):
    monkeypatch.setattr(router_module, "asyncio", _FastAsyncio(0.05))
    payload = FinalizationEvent(
        project_id=PROJECT_ID,
        finalization_percentage=60,
        final_repo_url=None,
        finalize_error=None,
    ).model_dump_json(by_alias=True)
    broker = PrefilledBroker("finalization", payload)
    response = _response(broker, FakeRequest())

    async def first_chunk():
        chunk = await response.body_iterator.__anext__()
        await response.body_iterator.aclose()
        return chunk

    assert asyncio.run(first_chunk()) == f"event: finalization\ndata: {payload}\n\n"


def test_sse_emits_heartbeat_when_idle(monkeypatch):
    monkeypatch.setattr(router_module, "asyncio", _FastAsyncio(0.05))
    broker = EventBroker()
    response = _response(broker, FakeRequest())

    async def first_chunk():
        chunk = await response.body_iterator.__anext__()
        await response.body_iterator.aclose()
        return chunk

    assert asyncio.run(first_chunk()) == ": heartbeat\n\n"
    assert broker._EventBroker__subscribers == set()


def test_sse_stops_and_unsubscribes_when_client_disconnects(monkeypatch):
    monkeypatch.setattr(router_module, "asyncio", _FastAsyncio(0.05))
    broker = EventBroker()
    response = _response(broker, FakeRequest(disconnect_after=1))

    async def drain():
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(drain())
    assert chunks == [": heartbeat\n\n"]
    assert broker._EventBroker__subscribers == set()

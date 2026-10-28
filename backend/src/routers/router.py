import asyncio
import logging
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from src.db.models.project import (
    ProgressUpdateRequest,
    Project,
    ProjectCreateRequest,
    ProjectDetail,
    ProjectNameUpdateRequest,
    RetryPhase,
)
from src.di import Container
from src.services.projects import (
    CreateProjectStatus,
    FinalizeResult,
    ProjectService,
    RetryPhaseResult,
)
from src.sse.broker import EventBroker

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/projects", tags=["projects"])


@api_router.get("", response_model=list[Project], status_code=200)
@inject
async def get_projects(
    project_service: ProjectService = Depends(Provide[Container.project_service]),
) -> list[Project]:
    return await project_service.list_projects()


@api_router.post("", response_model=ProjectDetail, status_code=201)
@inject
async def create_project(
    payload: ProjectCreateRequest,
    project_service: ProjectService = Depends(Provide[Container.project_service]),
) -> ProjectDetail:
    outcome = await project_service.create_project(payload)

    if outcome.status is CreateProjectStatus.CREATED and outcome.project is not None:
        return outcome.project
    if outcome.status is CreateProjectStatus.NOT_CONFIGURED:
        raise HTTPException(
            status_code=503, detail="Project creation workflow is not configured."
        )
    if outcome.status is CreateProjectStatus.TITLE_EXTRACTION_FAILED:
        raise HTTPException(
            status_code=502, detail="Could not extract the project title."
        )
    raise HTTPException(status_code=500, detail="Could not create the project.")


@api_router.get("/{project_id}", response_model=ProjectDetail, status_code=200)
@inject
async def get_project_detail(
    project_id: UUID,
    project_service: ProjectService = Depends(Provide[Container.project_service]),
) -> ProjectDetail:
    project = await project_service.get_project_detail(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@api_router.patch("/{project_id}", response_model=ProjectDetail, status_code=200)
@inject
async def rename_project(
    project_id: UUID,
    payload: ProjectNameUpdateRequest,
    project_service: ProjectService = Depends(Provide[Container.project_service]),
) -> ProjectDetail:
    updated = await project_service.rename_project(project_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return updated


@api_router.post("/{project_id}/finalize", status_code=204)
@inject
async def finalize_project(
    project_id: UUID,
    project_service: ProjectService = Depends(Provide[Container.project_service]),
) -> Response:
    result = await project_service.finalize_project(project_id)

    if result is FinalizeResult.OK:
        return Response(status_code=204)
    if result is FinalizeResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Project not found.")
    if result is FinalizeResult.CONFLICT:
        raise HTTPException(
            status_code=409, detail="Project is not eligible for finalization."
        )
    raise HTTPException(status_code=503, detail="Could not start the finalization workflow.")


@api_router.post("/{project_id}/progress", response_model=Project, status_code=200)
@inject
async def update_progress(
    project_id: UUID,
    payload: ProgressUpdateRequest,
    project_service: ProjectService = Depends(Provide[Container.project_service]),
) -> Project:
    updated = await project_service.update_progress(project_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return updated


# Generic phase retry, e.g. POST /projects/{id}/CODE. It is declared after the
# specific action routes so /finalize and /progress keep winning the match.
@api_router.post("/{project_id}/{phase}", response_model=ProjectDetail, status_code=200)
@inject
async def retry_phase(
    project_id: UUID,
    phase: RetryPhase,
    project_service: ProjectService = Depends(Provide[Container.project_service]),
) -> ProjectDetail:
    outcome = await project_service.retry_phase(project_id, phase)

    if outcome.result is RetryPhaseResult.OK and outcome.project is not None:
        return outcome.project
    if outcome.result is RetryPhaseResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Project not found.")
    if outcome.result is RetryPhaseResult.CONFLICT:
        raise HTTPException(
            status_code=409,
            detail="This phase cannot be started in the current project state.",
        )
    if outcome.result is RetryPhaseResult.NOT_CONFIGURED:
        raise HTTPException(
            status_code=503, detail="Phase retry workflow is not configured."
        )
    raise HTTPException(
        status_code=502, detail="Could not start the phase retry workflow."
    )


events_router = APIRouter(tags=["events"])


@events_router.get("/events")
@inject
async def events_stream(
    request: Request,
    event_broker: EventBroker = Depends(Provide[Container.event_broker]),
) -> StreamingResponse:
    async def event_generator():
        queue = event_broker.subscribe()
        logger.debug("SSE client connected.")
        try:
            while not await request.is_disconnected():
                try:
                    name, payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                else:
                    yield f"event: {name}\ndata: {payload}\n\n"
        finally:
            event_broker.unsubscribe(queue)
            logger.debug("SSE client disconnected.")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

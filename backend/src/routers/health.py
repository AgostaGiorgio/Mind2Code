from fastapi import APIRouter

health_router = APIRouter(tags=["health"])


@health_router.get("/health", status_code=200)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

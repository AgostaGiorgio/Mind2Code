import logging
from contextlib import asynccontextmanager
from pathlib import Path

import tomli
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.app_config import app_config
from src.config.logger import configure_logging
from src.di import Container
from src.routers import health, router

logger = logging.getLogger(__name__)

_pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
APP_VERSION = tomli.loads(_pyproject.read_text())["tool"]["poetry"]["version"]

container = Container()
container.wire(modules=[router, health])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up.")

    poller = None
    if app_config.enable_progress_polling:
        poller = container.progress_poller()
        await poller.start()

    yield

    if poller is not None:
        await poller.stop()
    logger.info("Application shutting down.")


app = FastAPI(title="Mind2Code API", version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_origins,
    allow_credentials=app_config.cors_allow_credentials,
    allow_methods=app_config.cors_allow_methods,
    allow_headers=app_config.cors_allow_headers,
)

app.include_router(health.health_router)
app.include_router(router.api_router, prefix="/api/v1")
app.include_router(router.events_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

import logging
from datetime import datetime
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.clients.postgres_client import PostgresClient
from src.db.models.project import Project, ProjectDetail
from src.repositories import queries as q

logger = logging.getLogger(__name__)


class ProjectRepository:
    def __init__(self, postgres_client: PostgresClient):
        self.__postgres_client = postgres_client

    async def list_projects(self) -> list[Project]:
        async with self.__postgres_client.async_session() as session:
            try:
                result = await session.execute(q.LIST_PROJECTS)
                rows = result.mappings().all()
                logger.debug(f"Fetched {len(rows)} projects from the database.")
                return [Project(**row) for row in rows]
            except (SQLAlchemyError, ValidationError) as e:
                logger.error(f"Error fetching projects: {e}", exc_info=True)
                return []

    async def get_project_detail(self, project_id: UUID) -> ProjectDetail | None:
        async with self.__postgres_client.async_session() as session:
            try:
                result = await session.execute(
                    q.GET_PROJECT_DETAIL, {"project_id": project_id}
                )
                row = result.mappings().first()
                logger.debug(f"Fetched project detail for '{project_id}'.")
                return ProjectDetail(**row) if row else None
            except (SQLAlchemyError, ValidationError) as e:
                logger.error(
                    f"Error fetching project detail for '{project_id}': {e}", exc_info=True
                )
                return None

    async def create_project(
        self, name: str, user_input: str, auto: bool
    ) -> ProjectDetail | None:
        async with self.__postgres_client.async_session() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        q.CREATE_PROJECT,
                        {
                            "name": name,
                            "github_url": "",
                            "user_input": user_input,
                            "auto": auto,
                        },
                    )
                    row = result.mappings().first()
                    if row is None:
                        logger.error("Project creation returned no row.")
                        return None
                    logger.info(f"Project '{row['id']}' created.")
                    return ProjectDetail(**row)
            except (SQLAlchemyError, ValidationError) as e:
                logger.error(f"Error creating project: {e}", exc_info=True)
                return None

    async def update_name(self, project_id: UUID, name: str) -> ProjectDetail | None:
        async with self.__postgres_client.async_session() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        q.UPDATE_NAME, {"project_id": project_id, "name": name}
                    )
                    row = result.mappings().first()
                    if row is None:
                        logger.warning(f"Project with id '{project_id}' not found.")
                        return None
                    logger.debug(f"Project '{project_id}' renamed to '{name}'.")
                    return ProjectDetail(**row)
            except (SQLAlchemyError, ValidationError) as e:
                logger.error(
                    f"Error renaming project '{project_id}': {e}", exc_info=True
                )
                return None

    async def request_finalization(self, project_id: UUID) -> Project | None:
        async with self.__postgres_client.async_session() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        q.REQUEST_FINALIZATION, {"project_id": project_id}
                    )
                    row = result.mappings().first()
                    if row is None:
                        logger.warning(
                            f"Finalization not eligible for project '{project_id}'."
                        )
                        return None
                    logger.info(f"Finalization requested for project '{project_id}'.")
                    return Project(**row)
            except (SQLAlchemyError, ValidationError) as e:
                logger.error(
                    f"Error requesting finalization for '{project_id}': {e}", exc_info=True
                )
                return None

    async def reset_finalization(self, project_id: UUID, finalize_error: str) -> None:
        async with self.__postgres_client.async_session() as session:
            try:
                async with session.begin():
                    await session.execute(
                        q.RESET_FINALIZATION,
                        {"project_id": project_id, "finalize_error": finalize_error},
                    )
                    logger.warning(
                        f"Finalization reset for project '{project_id}': {finalize_error}"
                    )
            except SQLAlchemyError as e:
                logger.error(
                    f"Error resetting finalization for '{project_id}': {e}", exc_info=True
                )

    async def get_latest_updated_at(self) -> datetime | None:
        async with self.__postgres_client.async_session() as session:
            try:
                result = await session.execute(q.GET_LATEST_UPDATED_AT)
                row = result.mappings().first()
                return row["latest_updated_at"] if row else None
            except SQLAlchemyError as e:
                logger.error(f"Error fetching latest updated_at: {e}", exc_info=True)
                return None

    async def list_updated_since(self, since: datetime) -> list[Project]:
        async with self.__postgres_client.async_session() as session:
            try:
                result = await session.execute(
                    q.LIST_PROJECTS_UPDATED_SINCE, {"since": since}
                )
                rows = result.mappings().all()
                logger.debug(f"Fetched {len(rows)} projects updated since {since}.")
                return [Project(**row) for row in rows]
            except (SQLAlchemyError, ValidationError) as e:
                logger.error(f"Error fetching projects updated since {since}: {e}", exc_info=True)
                return []

    async def update_completion(self, project_id: UUID, completion_percentage: int) -> Project | None:
        async with self.__postgres_client.async_session() as session:
            try:
                async with session.begin():
                    result = await session.execute(
                        q.UPDATE_COMPLETION,
                        {
                            "project_id": project_id,
                            "completion_percentage": completion_percentage,
                        },
                    )
                    row = result.mappings().first()
                    if row is None:
                        logger.warning(f"Project with id '{project_id}' not found.")
                        return None
                    logger.debug(f"Project '{project_id}' completion updated to {completion_percentage}%.")
                    return Project(**row)
            except (SQLAlchemyError, ValidationError) as e:
                logger.error(
                    f"Error updating completion for project '{project_id}': {e}", exc_info=True
                )
                return None

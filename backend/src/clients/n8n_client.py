import logging

import httpx

logger = logging.getLogger(__name__)

_MAX_TITLE_LENGTH = 200


class N8NClient:
    """HTTP client for the n8n workflows used by Mind2Code.

    A single client groups every webhook the backend calls: finalization,
    project-title extraction and requirements generation.
    """

    def __init__(
        self,
        project_title_url: str | None,
        requirements_url: str | None,
        finalize_url: str | None,
        timeout_seconds: float = 30.0,
    ):
        self.__project_title_url = project_title_url
        self.__requirements_url = requirements_url
        self.__finalize_url = finalize_url
        self.__timeout = timeout_seconds

    @property
    def finalize_configured(self) -> bool:
        return bool(self.__finalize_url)

    @property
    def project_title_configured(self) -> bool:
        return bool(self.__project_title_url)

    @property
    def requirements_configured(self) -> bool:
        return bool(self.__requirements_url)

    async def trigger_finalization(self, project_id: str) -> bool:
        """Start the release workflow. The DB UUID of the project is sent."""
        if not self.__finalize_url:
            return False

        response = await self.__post(
            self.__finalize_url,
            {"project_id": project_id},
        )
        if response is None:
            return False

        logger.info(f"Finalize webhook triggered for project {project_id}.")
        return True

    async def extract_project_title(self, user_input: str) -> str | None:
        """Ask n8n to derive a project title from the user input."""
        if not self.__project_title_url:
            return None

        response = await self.__post(
            self.__project_title_url,
            {"user_input": user_input},
        )
        if response is None:
            return None

        try:
            payload = response.json()
        except ValueError as e:
            logger.error(
                f"Project title webhook returned invalid JSON: {e}", exc_info=True
            )
            return None

        title = payload.get("project_title") if isinstance(payload, dict) else None
        if not isinstance(title, str) or not title.strip():
            logger.error("Project title webhook returned no usable 'project_title'.")
            return None

        logger.info("Project title extracted via the n8n webhook.")
        return title.strip()[:_MAX_TITLE_LENGTH]

    async def trigger_requirements(self, project_id: str) -> bool:
        """Start the requirements-generation workflow for a DB project id."""
        if not self.__requirements_url:
            return False

        response = await self.__post(
            self.__requirements_url,
            {"project_id": project_id},
        )
        if response is None:
            return False

        logger.info(f"Requirements webhook triggered for project {project_id}.")
        return True

    async def __post(
        self, url: str, payload: dict[str, object]
    ) -> httpx.Response | None:
        try:
            async with httpx.AsyncClient(timeout=self.__timeout) as client:
                response = await client.post(url, json=payload)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"n8n webhook call failed ({url}): {e}", exc_info=True)
            return None

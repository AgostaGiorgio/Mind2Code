import logging

import httpx

logger = logging.getLogger(__name__)

_MAX_TITLE_LENGTH = 200


class N8NClient:
    """HTTP client for the n8n workflows used by Mind2Code.

    A single client groups every webhook the backend calls: project-title
    extraction and the per-phase workflows.
    """

    def __init__(
        self,
        project_title_url: str | None,
        requirements_url: str | None,
        code_url: str | None,
        test_url: str | None,
        review_url: str | None,
        retrospective_url: str | None,
        timeout_seconds: float = 30.0,
    ):
        self.__project_title_url = project_title_url
        self.__phase_urls = {
            "REQUIREMENTS": requirements_url,
            "CODE": code_url,
            "TEST": test_url,
            "REVIEW": review_url,
            "RETROSPECTIVE": retrospective_url,
        }
        self.__timeout = timeout_seconds

    @property
    def project_title_configured(self) -> bool:
        return bool(self.__project_title_url)

    @property
    def requirements_configured(self) -> bool:
        return bool(self.__phase_urls["REQUIREMENTS"])

    def phase_configured(self, phase: str) -> bool:
        return bool(self.__phase_urls.get(phase))

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
        return await self.trigger_phase("REQUIREMENTS", project_id)

    async def trigger_phase(self, phase: str, project_id: str) -> bool:
        """Start the workflow that owns a specific pipeline phase."""
        url = self.__phase_urls.get(phase)
        if not url:
            return False

        response = await self.__post(url, {"project_id": project_id})
        if response is None:
            return False

        logger.info(f"{phase} webhook triggered for project {project_id}.")
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

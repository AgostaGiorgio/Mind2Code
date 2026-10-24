import logging

import httpx

logger = logging.getLogger(__name__)


class FinalizeWebhookClient:
    """Triggers the external (n8n) finalization workflow over HTTP.

    The request only carries the execution id; all the git/GitHub work happens
    in n8n, which reports progress back by writing to PostgreSQL.
    """

    def __init__(self, url: str | None, timeout_seconds: float = 10.0):
        self.__url = url
        self.__timeout = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.__url)

    async def trigger(self, execution_id: int) -> bool:
        if not self.__url:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.__timeout) as client:
                response = await client.post(self.__url, json={"executionId": execution_id})
            response.raise_for_status()
            logger.info(f"Finalize webhook triggered for execution_id {execution_id}.")
            return True
        except httpx.HTTPError as e:
            logger.error(
                f"Finalize webhook call failed for execution_id {execution_id}: {e}",
                exc_info=True,
            )
            return False

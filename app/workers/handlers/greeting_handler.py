"""Sample handler demonstrating the job handler pattern."""

import logging
from typing import Any

from app.repositories.greeting import GreetingRepository
from app.repositories.job import Job

logger = logging.getLogger(__name__)


class GreetingHandler:
    """Processes greeting jobs by looking up greetings from the repository."""

    def __init__(self, greeting_repository: GreetingRepository) -> None:
        self.greeting_repository = greeting_repository

    async def handle(self, job: Job) -> dict[str, Any]:
        """Handle a greeting job.

        Args:
            job: The claimed job to process

        Returns:
            Result dict with status and greeting_id
        """
        greeting_id: str = job.payload.get("greeting_id", "")
        logger.info(f"Processing greeting job {job.id} for greeting {greeting_id}")

        greeting = await self.greeting_repository.get_by_id(greeting_id)

        if greeting is None:
            logger.warning(f"Greeting {greeting_id} not found for job {job.id}")
            return {"status": "not_found", "greeting_id": greeting_id}

        logger.info(f"Processed greeting {greeting_id}: {greeting.get('message', '')}")
        return {"status": "processed", "greeting_id": greeting_id}

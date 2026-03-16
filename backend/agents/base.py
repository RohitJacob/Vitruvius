"""Base class for all LLM-backed agents with retry and logging."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2.0


class BaseLLMAgent(ABC):
    """Provides retry logic and a uniform interface for pipeline agents."""

    name: str = "base"
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY

    def __init__(
        self,
        *,
        vision_model: str = "",
        text_model: str = "",
    ):
        self.vision_model = vision_model or None
        self.text_model = text_model or None

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await self.execute(*args, **kwargs)
            except Exception as exc:
                last_err = exc
                logger.warning(
                    "%s attempt %d/%d failed: %s",
                    self.name,
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
        raise RuntimeError(
            f"{self.name} failed after {self.max_retries} attempts: {last_err}"
        ) from last_err

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any: ...

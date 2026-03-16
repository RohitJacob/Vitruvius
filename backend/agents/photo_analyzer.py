"""Stage 1: Analyze each uploaded photo individually using a vision model."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from agents.base import BaseLLMAgent
from config import get_settings
from models.schemas import PhotoAnalysis, PhotoMeta
from services import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert architectural inspector analyzing site visit photographs. "
    "For each photo, identify construction defects, safety issues, code violations, "
    "material degradation, water damage, structural concerns, or any other noteworthy "
    "observations an architect would document in a site visit report."
)

USER_PROMPT = """\
Analyze this site visit photograph. Respond with ONLY valid JSON (no markdown):
{
  "description": "Brief description of what is shown in the photo",
  "issues": ["issue 1", "issue 2"],
  "severity": "low|medium|high|critical",
  "location_hint": "Where this appears to be (e.g. exterior wall, roof, basement)",
  "tags": ["tag1", "tag2"]
}
"""


class PhotoAnalyzerAgent(BaseLLMAgent):
    name = "photo_analyzer"

    async def execute(
        self,
        photos: dict[str, PhotoMeta],
        *,
        on_progress: Callable[[float], Any] | None = None,
    ) -> dict[str, PhotoAnalysis]:
        settings = get_settings()
        sem = asyncio.Semaphore(settings.max_concurrent_llm_calls)
        results: dict[str, PhotoAnalysis] = {}
        total = len(photos)
        done = 0

        async def _analyze_one(photo: PhotoMeta) -> None:
            nonlocal done
            async with sem:
                logger.info("  Analyzing photo %d/%d: %s (%dKB)",
                            done + 1, total, photo.filename, len(photo.b64_data) * 3 // 4 // 1024)
                try:
                    data = await llm_client.chat_json_with_images(
                        USER_PROMPT,
                        [(photo.b64_data, photo.mime_type)],
                        system=SYSTEM_PROMPT,
                        model=self.vision_model,
                    )
                    results[photo.id] = PhotoAnalysis(photo_id=photo.id, **data)
                    logger.info("  Photo done: %s → %s", photo.filename, data.get("severity", "?"))
                except Exception:
                    logger.exception("Failed to analyze photo %s", photo.id)
                    results[photo.id] = PhotoAnalysis(
                        photo_id=photo.id,
                        description="Analysis failed – please review manually",
                        severity="medium",
                    )
                finally:
                    done += 1
                    if on_progress and total > 0:
                        await _maybe_await(on_progress(done / total))

        tasks = [_analyze_one(p) for p in photos.values()]
        await asyncio.gather(*tasks)
        return results


async def _maybe_await(val: Any) -> None:
    if asyncio.iscoroutine(val):
        await val

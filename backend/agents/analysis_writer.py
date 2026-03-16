"""Stage 3: Write professional findings for each photo group."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Callable

from agents.base import BaseLLMAgent
from config import get_settings
from models.schemas import Finding, PhotoAnalysis, PhotoGroup, PhotoMeta
from services import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior architect writing a professional site visit inspection report. "
    "Write clear, technical findings suitable for a formal report to a client or "
    "building owner. Be specific and actionable."
)

USER_PROMPT_TEMPLATE = """\
Based on the following group of site visit photos and their individual analyses,
write a professional finding for an inspection report.

Group: {label}
Individual analyses:
{analyses_text}

The photos are attached. Write a finding with these fields.
Respond with ONLY valid JSON (no markdown):
{{
  "observation": "What was observed — be specific and factual",
  "potential_cause": "Likely cause of the issue",
  "recommendation": "Recommended action / remediation",
  "severity": "low|medium|high|critical"
}}
"""


class AnalysisWriterAgent(BaseLLMAgent):
    name = "analysis_writer"

    async def execute(
        self,
        groups: list[PhotoGroup],
        analyses: dict[str, PhotoAnalysis],
        photos: dict[str, PhotoMeta],
        *,
        on_progress: Callable[[float], Any] | None = None,
    ) -> dict[str, Finding]:
        settings = get_settings()
        sem = asyncio.Semaphore(settings.max_concurrent_llm_calls)
        findings: dict[str, Finding] = {}
        total = len(groups)
        done = 0

        async def _write_one(group: PhotoGroup) -> None:
            nonlocal done
            async with sem:
                logger.info("  Writing finding %d/%d: %s (%d key photos)",
                            done + 1, total, group.label, len(group.key_photo_ids))
                try:
                    analyses_text = "\n".join(
                        f"- [{a.photo_id[:8]}] {a.description} "
                        f"(severity: {a.severity}, issues: {', '.join(a.issues)})"
                        for pid in group.photo_ids
                        if (a := analyses.get(pid))
                    )

                    images = [
                        (photos[pid].b64_data, photos[pid].mime_type)
                        for pid in group.key_photo_ids
                        if pid in photos
                    ]

                    prompt = USER_PROMPT_TEMPLATE.format(
                        label=group.label,
                        analyses_text=analyses_text,
                    )

                    data = await llm_client.chat_json_with_images(
                        prompt,
                        images,
                        system=SYSTEM_PROMPT,
                        model=self.vision_model,
                    )

                    finding_id = str(uuid.uuid4())
                    findings[finding_id] = Finding(
                        id=finding_id,
                        group_id=group.id,
                        **data,
                    )
                except Exception:
                    logger.exception("Failed to write analysis for group %s", group.id)
                    finding_id = str(uuid.uuid4())
                    findings[finding_id] = Finding(
                        id=finding_id,
                        group_id=group.id,
                        observation="Analysis generation failed – please write manually",
                        severity="medium",
                    )
                finally:
                    done += 1
                    if on_progress and total > 0:
                        await _maybe_await(on_progress(done / total))

        tasks = [_write_one(g) for g in groups]
        await asyncio.gather(*tasks)
        return findings


async def _maybe_await(val: Any) -> None:
    if asyncio.iscoroutine(val):
        await val

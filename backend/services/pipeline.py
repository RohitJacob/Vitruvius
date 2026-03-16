"""Orchestrator: runs the agentic pipeline stages and updates session status in-place."""

from __future__ import annotations

import asyncio
import logging
import time

from agents.photo_analyzer import PhotoAnalyzerAgent
from agents.photo_grouper import PhotoGrouperAgent
from agents.analysis_writer import AnalysisWriterAgent
from agents.template_analyzer import TemplateAnalyzerAgent
from models.schemas import PipelineStage, PipelineStatus, Session

logger = logging.getLogger(__name__)

STAGE_WEIGHTS = {
    "analyzing_photos": (0.0, 0.40),
    "grouping":         (0.40, 0.55),
    "writing_analyses": (0.55, 0.95),
    "analyzing_template": (0.95, 1.0),
}


def _overall(stage: str, local_pct: float) -> float:
    """Convert a per-stage 0-1 progress to an overall 0-1 progress."""
    start, end = STAGE_WEIGHTS.get(stage, (0.0, 1.0))
    return start + local_pct * (end - start)


class AnalysisPipeline:
    """Runs all agent stages, updating session.status in real-time."""

    def __init__(self, session: Session):
        self.session = session

    def _update(self, stage: PipelineStage, local_pct: float, message: str) -> None:
        overall = _overall(stage.value, local_pct)
        self.session.status = PipelineStatus(
            stage=stage,
            progress=overall,
            message=message,
        )

    async def run(self) -> None:
        s = self.session
        vm = s.vision_model or None
        tm = s.text_model or None
        pipeline_t0 = time.perf_counter()

        logger.info("Pipeline START  session=%s  photos=%d  template=%s",
                     s.id[:8], len(s.photos), bool(s.template_bytes))

        try:
            await self._run_stages(s, vm, tm, pipeline_t0)
        except Exception as exc:
            logger.exception("Pipeline error for session %s", s.id[:8])
            s.status = PipelineStatus(
                stage=PipelineStage.ERROR,
                error=str(exc),
                message="Pipeline failed",
            )

    async def _run_stages(self, s: Session, vm, tm, pipeline_t0: float) -> None:
        # -- Stage 1: Analyze individual photos --
        self._update(PipelineStage.ANALYZING_PHOTOS, 0.0, "Analyzing individual photos…")

        photo_analyzer = PhotoAnalyzerAgent(vision_model=vm, text_model=tm)

        async def _photo_progress(pct: float) -> None:
            n = int(pct * len(s.photos))
            self._update(PipelineStage.ANALYZING_PHOTOS, pct,
                         f"Analyzed {n}/{len(s.photos)} photos")

        template_task: asyncio.Task | None = None
        if s.template_bytes:
            logger.info("  Template analysis started in background")
            template_analyzer = TemplateAnalyzerAgent(vision_model=vm, text_model=tm)
            template_task = asyncio.create_task(
                template_analyzer.run(s.template_bytes, s.template_mime, s.template_filename)
            )

        t0 = time.perf_counter()
        s.photo_analyses = await photo_analyzer.run(
            s.photos, on_progress=_photo_progress
        )
        logger.info("  Stage 1 DONE  %.1fs  analyzed=%d photos", time.perf_counter() - t0, len(s.photo_analyses))

        # -- Stage 2: Group photos --
        self._update(PipelineStage.GROUPING, 0.0, "Grouping related photos…")

        t0 = time.perf_counter()
        grouper = PhotoGrouperAgent(vision_model=vm, text_model=tm)
        s.groups = await grouper.run(s.photo_analyses)
        logger.info("  Stage 2 DONE  %.1fs  groups=%d", time.perf_counter() - t0, len(s.groups))
        for g in s.groups:
            logger.info("    Group: %s (%d photos, %d key)", g.label, len(g.photo_ids), len(g.key_photo_ids))

        self._update(PipelineStage.GROUPING, 1.0, f"Found {len(s.groups)} groups")

        # -- Stage 3: Write analyses --
        self._update(PipelineStage.WRITING_ANALYSES, 0.0, "Writing findings…")

        writer = AnalysisWriterAgent(vision_model=vm, text_model=tm)

        async def _write_progress(pct: float) -> None:
            n = int(pct * len(s.groups))
            self._update(PipelineStage.WRITING_ANALYSES, pct,
                         f"Written {n}/{len(s.groups)} findings")

        t0 = time.perf_counter()
        s.findings = await writer.run(
            s.groups, s.photo_analyses, s.photos, on_progress=_write_progress
        )
        logger.info("  Stage 3 DONE  %.1fs  findings=%d", time.perf_counter() - t0, len(s.findings))

        # -- Collect template analysis result --
        if template_task:
            self._update(PipelineStage.ANALYZING_TEMPLATE, 0.5, "Waiting for template analysis…")
            try:
                s.template_schema = await template_task
                logger.info("  Stage 4 DONE  template analyzed")
            except Exception:
                logger.exception("Template analysis failed")

        # -- Done --
        total = time.perf_counter() - pipeline_t0
        logger.info("Pipeline DONE  session=%s  %.1fs total", s.id[:8], total)

        s.status = PipelineStatus(
            stage=PipelineStage.READY_FOR_REVIEW,
            progress=1.0,
            message=f"Analysis complete ({total:.0f}s)",
        )

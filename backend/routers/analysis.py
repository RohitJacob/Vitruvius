"""Analysis endpoints: kick off pipeline, stream progress, get results."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import AnalysisResults, PipelineStage, PipelineStatus
from services.pipeline import AnalysisPipeline
from services.session_manager import session_manager

logger = logging.getLogger(__name__)
router = APIRouter()

RUNNING_STAGES = {
    PipelineStage.ANALYZING_PHOTOS,
    PipelineStage.GROUPING,
    PipelineStage.WRITING_ANALYSES,
    PipelineStage.ANALYZING_TEMPLATE,
}

TERMINAL_STAGES = {
    PipelineStage.READY_FOR_REVIEW,
    PipelineStage.DONE,
    PipelineStage.ERROR,
}


@router.post("/sessions/{session_id}/analyze")
async def start_analysis(session_id: str):
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    if session.status.stage not in RUNNING_STAGES:
        pipeline = AnalysisPipeline(session)
        asyncio.create_task(pipeline.run())
        await asyncio.sleep(0.05)

    return StreamingResponse(
        _poll_progress(session_id),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


async def _poll_progress(session_id: str):
    """Poll session status every 300ms and emit SSE on any change."""
    last_snapshot = ""
    while True:
        session = session_manager.get(session_id)
        if not session:
            yield f"data: {json.dumps({'stage': 'error', 'error': 'Session expired'})}\n\n"
            return

        evt = {
            "stage": session.status.stage.value,
            "progress": round(session.status.progress, 3),
            "message": session.status.message,
            "error": session.status.error,
        }

        snapshot = f"{evt['stage']}:{evt['progress']}:{evt['message']}"
        if snapshot != last_snapshot:
            yield f"data: {json.dumps(evt)}\n\n"
            last_snapshot = snapshot

        if session.status.stage in TERMINAL_STAGES:
            return

        await asyncio.sleep(0.3)


def _sse_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


@router.get("/sessions/{session_id}/status")
async def get_status(session_id: str):
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "session_id": session_id,
        "stage": session.status.stage.value,
        "progress": session.status.progress,
        "message": session.status.message,
        "error": session.status.error,
    }


@router.get("/sessions/{session_id}/results", response_model=AnalysisResults)
async def get_results(session_id: str):
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    photos_b64 = {pid: pmeta.b64_data for pid, pmeta in session.photos.items()}

    return AnalysisResults(
        groups=session.groups,
        findings=session.findings,
        photo_analyses=session.photo_analyses,
        template_schema=session.template_schema,
        photos=photos_b64,
    )


@router.get("/sessions/{session_id}/photos/{photo_id}")
async def get_photo(session_id: str, photo_id: str):
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    photo = session.photos.get(photo_id)
    if not photo:
        raise HTTPException(404, "Photo not found")
    return {
        "id": photo.id,
        "filename": photo.filename,
        "mime_type": photo.mime_type,
        "b64_data": photo.b64_data,
    }

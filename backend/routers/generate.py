"""Generate endpoints: create the final report and serve the download ZIP."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from models.schemas import PipelineStage
from services.report_generator import generate_download_zip, generate_report_docx
from services.session_manager import session_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sessions/{session_id}/generate")
async def generate_report(session_id: str):
    """Generate the final report. Returns a summary before download."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    return {
        "session_id": session_id,
        "group_count": len(session.groups),
        "finding_count": len(session.findings),
        "template": session.template_filename or "none",
        "ready": True,
    }


@router.get("/sessions/{session_id}/download")
async def download_zip(session_id: str):
    """Download the full ZIP (report + photos + raw JSON)."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    try:
        zip_bytes = generate_download_zip(session)
    except Exception:
        logger.exception("Report generation failed for session %s", session_id)
        raise HTTPException(500, "Report generation failed")

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=vitruvius_report_{session_id[:8]}.zip"
        },
    )


@router.get("/sessions/{session_id}/download-docx")
async def download_docx(session_id: str):
    """Download just the .docx report."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    try:
        docx_bytes = generate_report_docx(session)
    except Exception:
        logger.exception("Docx generation failed for session %s", session_id)
        raise HTTPException(500, "Report generation failed")

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=report_{session_id[:8]}.docx"
        },
    )

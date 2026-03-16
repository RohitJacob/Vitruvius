"""Upload endpoints: receive photos + template, create a session."""

from __future__ import annotations

import base64
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from models.schemas import PhotoMeta, SessionSummary, PipelineStage
from services.session_manager import session_manager

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
}
ALLOWED_TEMPLATE_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/pdf",
}


@router.post("/upload", response_model=SessionSummary)
async def upload_files(
    photos: list[UploadFile] = File(...),
    template: Optional[UploadFile] = File(None),
    vision_model: str = Form(""),
    text_model: str = Form(""),
):
    session = session_manager.create()
    logger.info("Upload session=%s  photos=%d  template=%s",
                session.id[:8], len(photos), template.filename if template else "none")

    if vision_model:
        session.vision_model = vision_model
    if text_model:
        session.text_model = text_model

    for photo_file in photos:
        content_type = photo_file.content_type or "image/jpeg"
        if content_type not in ALLOWED_IMAGE_TYPES:
            logger.warning("Skipping non-image file: %s (%s)", photo_file.filename, content_type)
            continue

        raw = await photo_file.read()
        b64 = base64.b64encode(raw).decode()
        meta = PhotoMeta(
            filename=photo_file.filename or "unnamed.jpg",
            mime_type=content_type,
            b64_data=b64,
        )
        session.photos[meta.id] = meta

    if not session.photos:
        session_manager.delete(session.id)
        raise HTTPException(400, "No valid image files uploaded")

    if template:
        tmpl_type = template.content_type or ""
        if tmpl_type not in ALLOWED_TEMPLATE_TYPES:
            raise HTTPException(400, f"Unsupported template type: {tmpl_type}")
        session.template_bytes = await template.read()
        session.template_filename = template.filename or "template"
        session.template_mime = tmpl_type

    return SessionSummary(
        session_id=session.id,
        stage=session.status.stage,
        photo_count=len(session.photos),
        group_count=0,
        template_filename=session.template_filename,
    )

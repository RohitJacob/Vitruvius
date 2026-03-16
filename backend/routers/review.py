"""Review endpoints: edit findings, move photos, re-analyze groups."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException

from agents.analysis_writer import AnalysisWriterAgent
from models.schemas import (
    Finding,
    MovePhotoRequest,
    NewGroupFromPhotoRequest,
    PhotoGroup,
    ReAnalyzeRequest,
    UpdateFindingRequest,
)
from services.session_manager import session_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.patch("/sessions/{session_id}/findings/{finding_id}")
async def update_finding(
    session_id: str,
    finding_id: str,
    body: UpdateFindingRequest,
):
    """Directly edit a finding's text fields."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    finding = session.findings.get(finding_id)
    if not finding:
        raise HTTPException(404, "Finding not found")

    if body.observation is not None:
        finding.observation = body.observation
    if body.potential_cause is not None:
        finding.potential_cause = body.potential_cause
    if body.recommendation is not None:
        finding.recommendation = body.recommendation
    if body.severity is not None:
        finding.severity = body.severity

    return finding


@router.post("/sessions/{session_id}/move-photo")
async def move_photo(session_id: str, body: MovePhotoRequest):
    """Move a photo from one group to another (or create a new group)."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    source = next((g for g in session.groups if g.id == body.source_group_id), None)
    if not source or body.photo_id not in source.photo_ids:
        raise HTTPException(404, "Photo not found in source group")

    source.photo_ids.remove(body.photo_id)
    if body.photo_id in source.key_photo_ids:
        source.key_photo_ids.remove(body.photo_id)

    if body.target_group_id:
        target = next((g for g in session.groups if g.id == body.target_group_id), None)
        if not target:
            raise HTTPException(404, "Target group not found")
        target.photo_ids.append(body.photo_id)
    else:
        new_group = PhotoGroup(
            id=str(uuid.uuid4()),
            label="New Group",
            photo_ids=[body.photo_id],
            key_photo_ids=[body.photo_id],
        )
        session.groups.append(new_group)

        new_finding = Finding(
            id=str(uuid.uuid4()),
            group_id=new_group.id,
            observation="Moved from another group – please review",
            severity="medium",
        )
        session.findings[new_finding.id] = new_finding

    # Clean up empty groups
    session.groups = [g for g in session.groups if g.photo_ids]

    return {"groups": [g.model_dump() for g in session.groups]}


@router.post("/sessions/{session_id}/re-analyze")
async def re_analyze_group(session_id: str, body: ReAnalyzeRequest):
    """Re-run the analysis writer for a specific group with optional hint."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    group = next((g for g in session.groups if g.id == body.group_id), None)
    if not group:
        raise HTTPException(404, "Group not found")

    writer = AnalysisWriterAgent(
        vision_model=session.vision_model or None,
        text_model=session.text_model or None,
    )

    # Remove old finding for this group
    old_finding_ids = [
        fid for fid, f in session.findings.items() if f.group_id == group.id
    ]
    for fid in old_finding_ids:
        del session.findings[fid]

    new_findings = await writer.run(
        [group],
        session.photo_analyses,
        session.photos,
    )
    session.findings.update(new_findings)

    return {
        "findings": {k: v.model_dump() for k, v in new_findings.items()},
    }


@router.post("/sessions/{session_id}/new-group")
async def create_new_group(session_id: str, body: NewGroupFromPhotoRequest):
    """Pull a photo out into a new group and optionally trigger analysis."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    source = next((g for g in session.groups if g.id == body.source_group_id), None)
    if not source or body.photo_id not in source.photo_ids:
        raise HTTPException(404, "Photo not found in source group")

    source.photo_ids.remove(body.photo_id)
    if body.photo_id in source.key_photo_ids:
        source.key_photo_ids.remove(body.photo_id)

    new_group = PhotoGroup(
        id=str(uuid.uuid4()),
        label=body.label or "New Group",
        photo_ids=[body.photo_id],
        key_photo_ids=[body.photo_id],
    )
    session.groups.append(new_group)

    writer = AnalysisWriterAgent(
        vision_model=session.vision_model or None,
        text_model=session.text_model or None,
    )
    new_findings = await writer.run(
        [new_group],
        session.photo_analyses,
        session.photos,
    )
    session.findings.update(new_findings)

    session.groups = [g for g in session.groups if g.photo_ids]

    return {
        "group": new_group.model_dump(),
        "findings": {k: v.model_dump() for k, v in new_findings.items()},
    }


@router.put("/sessions/{session_id}/groups/{group_id}")
async def update_group(session_id: str, group_id: str, body: dict):
    """Update group metadata (label, key_photo_ids)."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    group = next((g for g in session.groups if g.id == group_id), None)
    if not group:
        raise HTTPException(404, "Group not found")

    if "label" in body:
        group.label = body["label"]
    if "key_photo_ids" in body:
        group.key_photo_ids = body["key_photo_ids"]

    return group.model_dump()


@router.delete("/sessions/{session_id}/groups/{group_id}")
async def delete_group(session_id: str, group_id: str):
    """Remove a group and its findings."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    session.groups = [g for g in session.groups if g.id != group_id]
    finding_ids_to_remove = [
        fid for fid, f in session.findings.items() if f.group_id == group_id
    ]
    for fid in finding_ids_to_remove:
        del session.findings[fid]

    return {"ok": True}

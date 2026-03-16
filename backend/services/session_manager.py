"""In-memory session store with TTL-based auto-cleanup."""

from __future__ import annotations

import asyncio
import logging
import time

from models.schemas import Session

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, ttl_seconds: int = 3600):
        self._sessions: dict[str, Session] = {}
        self._ttl = ttl_seconds
        self._cleanup_task: asyncio.Task | None = None

    def create(self) -> Session:
        session = Session()
        self._sessions[session.id] = session
        logger.info("Created session %s", session.id)
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        logger.info("Deleted session %s", session_id)

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [
            sid
            for sid, s in self._sessions.items()
            if now - s.created_at > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.info("Expired session %s", sid)

    async def _run_cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(60)
            self._cleanup_expired()

    def start_cleanup_task(self) -> None:
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._run_cleanup_loop())

    def stop_cleanup_task(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


session_manager = SessionManager()

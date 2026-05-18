import logging
import shutil
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_registry: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


class SessionService:
    def __init__(self, generated_agents_dir: str | None = None):
        self._base_dir = Path(generated_agents_dir or settings.generated_agents_dir)

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        session_dir = self._base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        with _lock:
            _registry[session_id] = {
                "session_id": session_id,
                "created_at": datetime.utcnow(),
                "stage": "idle",
                "chat_ws": None,
                "status_ws": None,
                "preview_ws": None,
                "framework": None,
                "preview_running": False,
            }
        logger.info("Session created: %s", session_id)
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with _lock:
            return _registry.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        with _lock:
            return session_id in _registry

    def set_chat_ws(self, session_id: str, ws: Any) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["chat_ws"] = ws

    def clear_chat_ws(self, session_id: str) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["chat_ws"] = None

    def set_status_ws(self, session_id: str, ws: Any) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["status_ws"] = ws

    def clear_status_ws(self, session_id: str) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["status_ws"] = None

    def set_preview_ws(self, session_id: str, ws: Any) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["preview_ws"] = ws

    def clear_preview_ws(self, session_id: str) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["preview_ws"] = None

    def set_framework(self, session_id: str, framework: str) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["framework"] = framework

    def set_preview_running(self, session_id: str, running: bool) -> None:
        with _lock:
            if session_id in _registry:
                _registry[session_id]["preview_running"] = running

    def is_preview_running(self, session_id: str) -> bool:
        with _lock:
            session = _registry.get(session_id)
            return bool(session and session.get("preview_running"))

    def get_session_dir(self, session_id: str) -> Path:
        return self._base_dir / session_id

    def cleanup_old_sessions(self, max_age_hours: int | None = None) -> int:
        age_hours = max_age_hours if max_age_hours is not None else settings.session_max_age_hours
        cutoff = time.time() - (age_hours * 3600)
        deleted = 0

        if not self._base_dir.exists():
            return 0

        for entry in self._base_dir.iterdir():
            if not entry.is_dir():
                continue
            try:
                mtime = entry.stat().st_mtime
                if mtime < cutoff:
                    shutil.rmtree(entry)
                    with _lock:
                        _registry.pop(entry.name, None)
                    deleted += 1
                    logger.info("Cleaned up old session dir: %s", entry.name)
            except OSError as e:
                logger.warning("Failed to clean session dir %s: %s", entry.name, e)

        return deleted

"""
session_manager.py — User session management for FlowBot.

Responsibilities:
- Track active sessions and their metadata.
- Handle session timeouts and recovery.
- Provide a single source of truth for session state.

Future Changes:
- Persist sessions to DB for multi-instance deployments.
- Add session-scoped variables for personalization.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.logger import logger


class SessionManager:
    """
    Manages user sessions, including timeout and recovery.
    """

    # ---------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------
    def __init__(self, timeout_minutes: int = 30):
        self.timeout = timedelta(minutes=timeout_minutes)
        self.sessions: Dict[str, Dict[str, Any]] = {}

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------
    def get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        """
        Returns an existing session or creates a new one.
        """
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "user_name": None,
                "last_topic": None
            }
            logger.info(f"[Session Created] user_id={user_id}")
        return self.sessions[user_id]

    def refresh_session(self, user_id: str):
        """
        Updates the last_active timestamp for a session.
        """
        if user_id in self.sessions:
            self.sessions[user_id]["last_active"] = datetime.utcnow()
            logger.debug(f"[Session Refreshed] user_id={user_id}")

    def is_session_expired(self, user_id: str) -> bool:
        """
        Checks if a session has expired.
        """
        if user_id not in self.sessions:
            return True
        last_active = self.sessions[user_id]["last_active"]
        expired = datetime.utcnow() - last_active > self.timeout
        if expired:
            logger.info(f"[Session Expired] user_id={user_id}")
        return expired
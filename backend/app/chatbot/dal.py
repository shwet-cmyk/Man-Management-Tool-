from __future__ import annotations

from collections import defaultdict
from datetime import datetime, UTC
from uuid import uuid4


class ChatbotDAL:
    """DAL scaffold with in-memory storage for demo/runtime-only behavior."""

    def __init__(self) -> None:
        self._store: dict[str, list[dict]] = defaultdict(list)

    def create_session_id(self) -> str:
        return str(uuid4())

    def append_message(self, session_id: str, role: str, content: str) -> dict:
        row = {
            'id': str(uuid4()),
            'role': role,
            'content': content,
            'created_at': datetime.now(UTC).isoformat(),
        }
        self._store[session_id].append(row)
        return row

    def list_messages(self, session_id: str) -> list[dict]:
        return list(self._store.get(session_id, []))

"""Session listing and history, read directly from the SDK's own tables."""

import os
import sqlite3
import uuid
from contextlib import closing

from agents import SQLiteSession

DB_PATH = os.getenv("SPENDLITE_SESSIONS_DB", "./sessions.db")

LIST_SQL = """
SELECT s.session_id, s.created_at, s.updated_at,
       (SELECT json_extract(m.message_data, '$.content')
          FROM agent_messages m
         WHERE m.session_id = s.session_id
           AND json_extract(m.message_data, '$.role') = 'user'
         ORDER BY m.id LIMIT 1) AS title
  FROM agent_sessions s
 ORDER BY s.updated_at DESC
"""


def new_session_id() -> str:
    return f"web-{uuid.uuid4().hex[:12]}"


def open_session(session_id: str) -> SQLiteSession:
    return SQLiteSession(session_id, DB_PATH)


def list_sessions() -> list[dict]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(LIST_SQL).fetchall()
        except sqlite3.OperationalError:
            return []  # the SDK creates its tables on first write
    return [
        {
            "id": row["session_id"],
            "title": (row["title"] or "New chat")[:60],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


async def get_history(session_id: str) -> list[dict]:
    items = await open_session(session_id).get_items()
    history: list[dict] = []
    for item in items:
        role = item.get("role")
        if role == "user" and isinstance(item.get("content"), str):
            history.append({"role": "user", "content": item["content"]})
        elif role == "assistant":
            blocks = item.get("content") or []
            text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
            if text:
                history.append({"role": "assistant", "content": text})
    return history

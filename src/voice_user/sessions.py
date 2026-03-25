"""Session CRUD operations."""

import json
import sqlite3
from datetime import datetime, timezone

from uuid_utils import uuid7

from .types import SessionRecord


def _row_to_session(row: tuple) -> SessionRecord:
    return SessionRecord(
        id=row[0],
        user_id=row[1],
        session_type=row[2],
        started_at=row[3],
        ended_at=row[4],
        duration_s=row[5],
        metrics=json.loads(row[6]) if isinstance(row[6], str) else row[6],
    )


def create_session(
    conn: sqlite3.Connection,
    user_id: str,
    session_type: str,
    metrics: dict | None = None,
) -> SessionRecord:
    """Create a new session. Does not commit."""
    session_id = str(uuid7())
    now = datetime.now(timezone.utc).isoformat()
    m = json.dumps(metrics or {})
    conn.execute(
        "INSERT INTO sessions (id, user_id, session_type, started_at, metrics) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, user_id, session_type, now, m),
    )
    return SessionRecord(
        id=session_id, user_id=user_id, session_type=session_type,
        started_at=now, ended_at=None, duration_s=None,
        metrics=metrics or {},
    )


def end_session(
    conn: sqlite3.Connection,
    session_id: str,
    duration_s: float,
    metrics: dict | None = None,
) -> SessionRecord:
    """Mark a session as ended. Does not commit."""
    now = datetime.now(timezone.utc).isoformat()
    if metrics is not None:
        conn.execute(
            "UPDATE sessions SET ended_at = ?, duration_s = ?, metrics = ? WHERE id = ?",
            (now, duration_s, json.dumps(metrics), session_id),
        )
    else:
        conn.execute(
            "UPDATE sessions SET ended_at = ?, duration_s = ? WHERE id = ?",
            (now, duration_s, session_id),
        )
    return get_session(conn, session_id)  # type: ignore[return-value]


def get_session(conn: sqlite3.Connection, session_id: str) -> SessionRecord | None:
    """Fetch a session by ID."""
    row = conn.execute(
        "SELECT id, user_id, session_type, started_at, ended_at, duration_s, metrics "
        "FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_session(row)


def list_sessions(
    conn: sqlite3.Connection,
    user_id: str,
    session_type: str | None = None,
    limit: int = 50,
) -> list[SessionRecord]:
    """List sessions for a user, optionally filtered by type."""
    if session_type is not None:
        rows = conn.execute(
            "SELECT id, user_id, session_type, started_at, ended_at, duration_s, metrics "
            "FROM sessions WHERE user_id = ? AND session_type = ? "
            "ORDER BY started_at DESC LIMIT ?",
            (user_id, session_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, user_id, session_type, started_at, ended_at, duration_s, metrics "
            "FROM sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [_row_to_session(r) for r in rows]


def update_session(
    conn: sqlite3.Connection, session_id: str, **fields
) -> SessionRecord:
    """Update session fields. Does not commit."""
    allowed = {"session_type", "ended_at", "duration_s", "metrics"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_session(conn, session_id)  # type: ignore[return-value]

    parts = []
    values = []
    for key, val in updates.items():
        parts.append(f"{key} = ?")
        values.append(json.dumps(val) if key == "metrics" else val)
    values.append(session_id)

    conn.execute(
        f"UPDATE sessions SET {', '.join(parts)} WHERE id = ?", values
    )
    return get_session(conn, session_id)  # type: ignore[return-value]

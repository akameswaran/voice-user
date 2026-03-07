"""User CRUD operations."""

import json
import sqlite3
from datetime import datetime, timezone

from uuid_utils import uuid7

from .types import UserRecord


def _row_to_user(row: tuple) -> UserRecord:
    return UserRecord(
        id=row[0],
        name=row[1],
        created_at=row[2],
        preferences=json.loads(row[3]) if isinstance(row[3], str) else row[3],
    )


def create_user(
    conn: sqlite3.Connection, name: str, preferences: dict | None = None
) -> UserRecord:
    """Create a new user. Does not commit -- caller manages transaction."""
    user_id = str(uuid7())
    now = datetime.now(timezone.utc).isoformat()
    prefs = json.dumps(preferences or {})
    conn.execute(
        "INSERT INTO users (id, name, created_at, preferences) VALUES (?, ?, ?, ?)",
        (user_id, name, now, prefs),
    )
    return UserRecord(
        id=user_id, name=name, created_at=now,
        preferences=preferences or {},
    )


def get_user(conn: sqlite3.Connection, user_id: str) -> UserRecord | None:
    """Fetch a user by ID. Returns None if not found."""
    row = conn.execute(
        "SELECT id, name, created_at, preferences FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_user(row)


def list_users(conn: sqlite3.Connection) -> list[UserRecord]:
    """List all users ordered by creation time."""
    rows = conn.execute(
        "SELECT id, name, created_at, preferences FROM users ORDER BY created_at"
    ).fetchall()
    return [_row_to_user(r) for r in rows]


def update_user(
    conn: sqlite3.Connection, user_id: str, **fields
) -> UserRecord:
    """Update user fields (name, preferences). Does not commit."""
    allowed = {"name", "preferences"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        user = get_user(conn, user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        return user

    parts = []
    values = []
    for key, val in updates.items():
        parts.append(f"{key} = ?")
        values.append(json.dumps(val) if key == "preferences" else val)
    values.append(user_id)

    cursor = conn.execute(
        f"UPDATE users SET {', '.join(parts)} WHERE id = ?", values
    )
    if cursor.rowcount == 0:
        raise ValueError(f"User {user_id} not found")

    return get_user(conn, user_id)  # type: ignore[return-value]

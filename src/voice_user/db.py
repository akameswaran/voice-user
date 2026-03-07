"""Database initialization and migration for voice-user."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_MIGRATION_1_SQL = """
CREATE TABLE users (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    preferences JSON DEFAULT '{}' CHECK (json_valid(preferences))
);

CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    session_type TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    duration_s  REAL,
    metrics     JSON DEFAULT '{}' CHECK (json_valid(metrics)),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE recordings (
    id          TEXT PRIMARY KEY,
    session_id  TEXT,
    user_id     TEXT NOT NULL,
    filename    TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    duration_s  REAL,
    sample_rate INTEGER,
    metadata    JSON DEFAULT '{}' CHECK (json_valid(metadata)),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_user ON sessions(user_id, started_at);
CREATE INDEX idx_recordings_session ON recordings(session_id);
CREATE INDEX idx_recordings_user_time ON recordings(user_id, recorded_at);
"""


def _apply_migration_1(conn: sqlite3.Connection) -> None:
    conn.executescript(_MIGRATION_1_SQL)


_MIGRATIONS = [
    (1, _apply_migration_1),
]


def _get_current_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] if row[0] is not None else 0
    except sqlite3.OperationalError:
        return 0


def _configure_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_size_limit=67108864")


def init_db(db_path: Path) -> sqlite3.Connection:
    """Create or open a database, enable WAL + foreign keys, run pending migrations."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    _configure_connection(conn)

    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "  version INTEGER NOT NULL,"
        "  applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )

    current = _get_current_version(conn)
    for version, migrate_fn in _MIGRATIONS:
        if version > current:
            migrate_fn(conn)
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (version, now),
            )
            conn.commit()

    return conn


def get_db(db_path: Path) -> sqlite3.Connection:
    """Get a configured connection to an existing database."""
    conn = sqlite3.connect(str(db_path))
    _configure_connection(conn)
    return conn

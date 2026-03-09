"""Analysis storage — multiple analysis results per recording."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import TypedDict

from uuid_utils import uuid7


class AnalysisRecord(TypedDict):
    id: str
    recording_id: str
    analyzer: str
    version: str | None
    created_at: str
    results: dict


def _row_to_analysis(row: tuple) -> AnalysisRecord:
    results = row[5]
    if isinstance(results, str):
        results = json.loads(results)
    return AnalysisRecord(
        id=row[0],
        recording_id=row[1],
        analyzer=row[2],
        version=row[3],
        created_at=row[4],
        results=results,
    )


def save_analysis(
    conn: sqlite3.Connection,
    recording_id: str,
    analyzer: str,
    results: dict,
    version: str | None = None,
) -> AnalysisRecord:
    """Save an analysis result for a recording. Does NOT commit."""
    aid = str(uuid7())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO analyses (id, recording_id, analyzer, version, created_at, results)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (aid, recording_id, analyzer, version, now, json.dumps(results)),
    )
    return AnalysisRecord(
        id=aid,
        recording_id=recording_id,
        analyzer=analyzer,
        version=version,
        created_at=now,
        results=results,
    )


def get_latest_analysis(
    conn: sqlite3.Connection,
    recording_id: str,
    analyzer: str,
) -> AnalysisRecord | None:
    """Get the most recent analysis of a given type for a recording."""
    row = conn.execute(
        """SELECT id, recording_id, analyzer, version, created_at, results
           FROM analyses
           WHERE recording_id = ? AND analyzer = ?
           ORDER BY created_at DESC LIMIT 1""",
        (recording_id, analyzer),
    ).fetchone()
    return _row_to_analysis(row) if row else None


def list_analyses(
    conn: sqlite3.Connection,
    recording_id: str,
    analyzer: str | None = None,
) -> list[AnalysisRecord]:
    """List analyses for a recording, optionally filtered by analyzer type."""
    if analyzer:
        rows = conn.execute(
            """SELECT id, recording_id, analyzer, version, created_at, results
               FROM analyses
               WHERE recording_id = ? AND analyzer = ?
               ORDER BY created_at""",
            (recording_id, analyzer),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT id, recording_id, analyzer, version, created_at, results
               FROM analyses
               WHERE recording_id = ?
               ORDER BY created_at""",
            (recording_id,),
        ).fetchall()
    return [_row_to_analysis(r) for r in rows]


def delete_analyses(
    conn: sqlite3.Connection,
    recording_id: str,
    analyzer: str | None = None,
) -> None:
    """Delete analyses for a recording. If analyzer given, only that type. Does NOT commit."""
    if analyzer:
        conn.execute(
            "DELETE FROM analyses WHERE recording_id = ? AND analyzer = ?",
            (recording_id, analyzer),
        )
    else:
        conn.execute(
            "DELETE FROM analyses WHERE recording_id = ?",
            (recording_id,),
        )

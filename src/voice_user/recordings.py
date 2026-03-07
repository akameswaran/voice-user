"""Recording storage: WAV file I/O + database metadata."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
from uuid_utils import uuid7

from .types import RecordingRecord


def _row_to_recording(row: tuple) -> RecordingRecord:
    return RecordingRecord(
        id=row[0],
        session_id=row[1],
        user_id=row[2],
        filename=row[3],
        recorded_at=row[4],
        duration_s=row[5],
        sample_rate=row[6],
        metadata=json.loads(row[7]) if isinstance(row[7], str) else row[7],
    )


def write_audio_file(
    recordings_dir: Path, user_id: str, audio_data: np.ndarray, sr: int
) -> str:
    """Write audio to a WAV file on disk. Returns path relative to recordings_dir."""
    user_dir = recordings_dir / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{uuid7()}_{ts}.wav"
    rel_path = f"{user_id}/{filename}"
    sf.write(str(recordings_dir / rel_path), audio_data, sr)
    return rel_path


def register_recording(
    conn: sqlite3.Connection,
    user_id: str,
    filename: str,
    recorded_at: str,
    session_id: str | None = None,
    duration_s: float | None = None,
    sample_rate: int | None = None,
    metadata: dict | None = None,
) -> RecordingRecord:
    """Insert a DB row for an already-written file. Does not commit."""
    rec_id = str(uuid7())
    m = json.dumps(metadata or {})
    conn.execute(
        "INSERT INTO recordings "
        "(id, session_id, user_id, filename, recorded_at, duration_s, sample_rate, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (rec_id, session_id, user_id, filename, recorded_at, duration_s, sample_rate, m),
    )
    return RecordingRecord(
        id=rec_id, session_id=session_id, user_id=user_id,
        filename=filename, recorded_at=recorded_at,
        duration_s=duration_s, sample_rate=sample_rate,
        metadata=metadata or {},
    )


def save_recording(
    conn: sqlite3.Connection,
    user_id: str,
    audio_data: np.ndarray,
    sr: int,
    recordings_dir: Path,
    session_id: str | None = None,
    metadata: dict | None = None,
) -> RecordingRecord:
    """Write WAV to disk + insert DB row. Cleans up file on DB failure."""
    rel_path = write_audio_file(recordings_dir, user_id, audio_data, sr)
    full_path = recordings_dir / rel_path
    now = datetime.now(timezone.utc).isoformat()
    duration = len(audio_data) / sr
    try:
        return register_recording(
            conn, user_id, filename=rel_path, recorded_at=now,
            session_id=session_id, duration_s=duration,
            sample_rate=sr, metadata=metadata,
        )
    except Exception:
        full_path.unlink(missing_ok=True)
        raise


def get_recording(
    conn: sqlite3.Connection, recording_id: str
) -> RecordingRecord | None:
    """Fetch a recording by ID."""
    row = conn.execute(
        "SELECT id, session_id, user_id, filename, recorded_at, "
        "duration_s, sample_rate, metadata FROM recordings WHERE id = ?",
        (recording_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_recording(row)


def list_recordings(
    conn: sqlite3.Connection,
    session_id: str | None = None,
    user_id: str | None = None,
) -> list[RecordingRecord]:
    """List recordings filtered by session and/or user."""
    conditions = []
    params: list = []
    if session_id is not None:
        conditions.append("session_id = ?")
        params.append(session_id)
    if user_id is not None:
        conditions.append("user_id = ?")
        params.append(user_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = conn.execute(
        f"SELECT id, session_id, user_id, filename, recorded_at, "
        f"duration_s, sample_rate, metadata FROM recordings {where} "
        f"ORDER BY recorded_at",
        params,
    ).fetchall()
    return [_row_to_recording(r) for r in rows]


def delete_recording(
    conn: sqlite3.Connection, recording_id: str, recordings_dir: Path
) -> bool:
    """Delete DB row first, then file. Returns False if not found."""
    rec = get_recording(conn, recording_id)
    if rec is None:
        return False
    conn.execute("DELETE FROM recordings WHERE id = ?", (recording_id,))
    file_path = recordings_dir / rec["filename"]
    file_path.unlink(missing_ok=True)
    return True

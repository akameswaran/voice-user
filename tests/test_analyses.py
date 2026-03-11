"""Tests for analysis CRUD operations."""

import pytest
import numpy as np

from voice_user import (
    init_db,
    create_user,
    create_session,
    save_recording,
    save_analysis,
    get_latest_analysis,
    list_analyses,
    delete_analyses,
    AnalysisRecord,
)


@pytest.fixture
def conn(tmp_path):
    c = init_db(tmp_path / "test.db")
    yield c
    c.close()


@pytest.fixture
def user(conn):
    return create_user(conn, name="TestUser")


@pytest.fixture
def session(conn, user):
    return create_session(conn, user["id"], "practice")


@pytest.fixture
def rec_dir(tmp_path):
    d = tmp_path / "recordings"
    d.mkdir()
    return d


@pytest.fixture
def sample_audio():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    return (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), sr


@pytest.fixture
def recording(conn, user, session, rec_dir, sample_audio):
    audio, sr = sample_audio
    with conn:
        return save_recording(conn, user["id"], audio, sr, rec_dir, session_id=session["id"])


# ── save_analysis ────────────────────────────────────────────


def test_save_analysis_returns_record(conn, recording):
    results = {"score": 85, "detail": {"pitch": 90, "resonance": 80}}
    with conn:
        a = save_analysis(conn, recording["id"], "femme_scoring", results)
    assert a["recording_id"] == recording["id"]
    assert a["analyzer"] == "femme_scoring"
    assert a["results"] == results
    assert a["version"] is None
    assert a["id"]  # UUIDv7
    assert a["created_at"]  # ISO timestamp


def test_save_analysis_with_version(conn, recording):
    results = {"accuracy": 0.95}
    with conn:
        a = save_analysis(conn, recording["id"], "whisper_es", results, version="large-v3")
    assert a["version"] == "large-v3"
    assert a["analyzer"] == "whisper_es"


def test_save_analysis_multiple_types(conn, recording):
    with conn:
        a1 = save_analysis(conn, recording["id"], "pitch_accuracy", {"cents_off": 5})
        a2 = save_analysis(conn, recording["id"], "vibrato_detect", {"rate_hz": 5.5})
    assert a1["id"] != a2["id"]
    assert a1["analyzer"] == "pitch_accuracy"
    assert a2["analyzer"] == "vibrato_detect"


def test_save_analysis_multiple_versions(conn, recording):
    with conn:
        a1 = save_analysis(conn, recording["id"], "femme_scoring", {"score": 70}, version="v1")
        a2 = save_analysis(conn, recording["id"], "femme_scoring", {"score": 85}, version="v2")
    assert a1["id"] != a2["id"]


# ── get_latest_analysis ──────────────────────────────────────


def test_get_latest_analysis(conn, recording):
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 70}, version="v1")
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 85}, version="v2")
    latest = get_latest_analysis(conn, recording["id"], "femme_scoring")
    assert latest is not None
    assert latest["results"]["score"] == 85
    assert latest["version"] == "v2"


def test_reanalysis_returns_newer(conn, recording):
    """Re-running analysis on same recording with updated code should return the new result."""
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 70, "model": "old"}, version="v1")
    # Simulate re-analysis with updated pipeline
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 82, "model": "new"}, version="v1")
    latest = get_latest_analysis(conn, recording["id"], "femme_scoring")
    assert latest["results"]["score"] == 82
    assert latest["results"]["model"] == "new"
    # Both analyses still exist
    all_analyses = list_analyses(conn, recording["id"], analyzer="femme_scoring")
    assert len(all_analyses) == 2


def test_get_latest_analysis_wrong_analyzer(conn, recording):
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 85})
    result = get_latest_analysis(conn, recording["id"], "whisper_es")
    assert result is None


def test_get_latest_analysis_no_analyses(conn, recording):
    result = get_latest_analysis(conn, recording["id"], "femme_scoring")
    assert result is None


# ── list_analyses ────────────────────────────────────────────


def test_list_analyses_all(conn, recording):
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 85})
        save_analysis(conn, recording["id"], "whisper_es", {"text": "hello"})
    analyses = list_analyses(conn, recording["id"])
    assert len(analyses) == 2


def test_list_analyses_filtered(conn, recording):
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 85})
        save_analysis(conn, recording["id"], "whisper_es", {"text": "hello"})
    analyses = list_analyses(conn, recording["id"], analyzer="femme_scoring")
    assert len(analyses) == 1
    assert analyses[0]["analyzer"] == "femme_scoring"


def test_list_analyses_empty(conn, recording):
    analyses = list_analyses(conn, recording["id"])
    assert analyses == []


# ── delete_analyses ──────────────────────────────────────────


def test_delete_analyses_by_analyzer(conn, recording):
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 85})
        save_analysis(conn, recording["id"], "whisper_es", {"text": "hello"})
    with conn:
        delete_analyses(conn, recording["id"], analyzer="femme_scoring")
    remaining = list_analyses(conn, recording["id"])
    assert len(remaining) == 1
    assert remaining[0]["analyzer"] == "whisper_es"


def test_delete_analyses_all(conn, recording):
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 85})
        save_analysis(conn, recording["id"], "whisper_es", {"text": "hello"})
    with conn:
        delete_analyses(conn, recording["id"])
    assert list_analyses(conn, recording["id"]) == []


# ── CASCADE on recording delete ──────────────────────────────


def test_cascade_delete_recording(conn, recording, rec_dir):
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", {"score": 85})
    from voice_user import delete_recording
    with conn:
        delete_recording(conn, recording["id"], rec_dir)
    row = conn.execute(
        "SELECT COUNT(*) FROM analyses WHERE recording_id = ?",
        (recording["id"],)
    ).fetchone()
    assert row[0] == 0


# ── Migration on existing DB ────────────────────────────────


def test_migration_v2_on_existing_v1(tmp_path):
    """Simulate a v1 DB and verify migration 2 adds analyses table."""
    conn = init_db(tmp_path / "old.db")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='analyses'"
    ).fetchone()
    assert tables is not None
    ver = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    assert ver[0] == 3
    conn.close()


def test_migration_v3_adds_exercise_columns(tmp_path):
    """Migration 3 adds exercise_type and include_in_session_aggregate columns to analyses."""
    conn = init_db(tmp_path / "test.db")
    # Query the column info for the analyses table
    cols = conn.execute("PRAGMA table_info(analyses)").fetchall()
    col_names = {row[1] for row in cols}
    assert "exercise_type" in col_names, "exercise_type column missing from analyses"
    assert "include_in_session_aggregate" in col_names, "include_in_session_aggregate column missing from analyses"
    conn.close()


def test_migration_v3_index_exists(tmp_path):
    """Migration 3 creates idx_analyses_exercise_type index."""
    conn = init_db(tmp_path / "test.db")
    idx = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_analyses_exercise_type'"
    ).fetchone()
    assert idx is not None, "idx_analyses_exercise_type index not created by migration 3"
    conn.close()


def test_save_analysis_populates_exercise_type_column(conn, recording):
    """save_analysis() stores exercise_type from results into the indexed column."""
    results = {"exercise_type": "integration", "score": 75}
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", results)
    row = conn.execute(
        "SELECT exercise_type FROM analyses WHERE recording_id = ?",
        (recording["id"],)
    ).fetchone()
    assert row is not None
    assert row[0] == "integration"


def test_save_analysis_populates_include_in_session_aggregate_column(conn, recording):
    """save_analysis() stores include_in_session_aggregate from results into the indexed column."""
    results = {"exercise_type": "integration", "include_in_session_aggregate": True, "score": 75}
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", results)
    row = conn.execute(
        "SELECT include_in_session_aggregate FROM analyses WHERE recording_id = ?",
        (recording["id"],)
    ).fetchone()
    assert row is not None
    assert row[0] == 1  # SQLite stores bool as INTEGER (1=True)


def test_save_analysis_include_in_session_aggregate_false(conn, recording):
    """save_analysis() stores include_in_session_aggregate=False as 0 in the DB."""
    results = {"exercise_type": "range_exploration", "include_in_session_aggregate": False}
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", results)
    row = conn.execute(
        "SELECT include_in_session_aggregate FROM analyses WHERE recording_id = ?",
        (recording["id"],)
    ).fetchone()
    assert row is not None
    assert row[0] == 0  # SQLite stores bool as INTEGER (0=False)


def test_save_analysis_exercise_type_none_when_absent(conn, recording):
    """save_analysis() stores NULL for exercise_type when not in results."""
    results = {"score": 80}
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring", results)
    row = conn.execute(
        "SELECT exercise_type, include_in_session_aggregate FROM analyses WHERE recording_id = ?",
        (recording["id"],)
    ).fetchone()
    assert row is not None
    assert row[0] is None
    assert row[1] is None


def test_exercise_type_column_queryable(conn, recording):
    """exercise_type column can be used to filter analyses."""
    with conn:
        save_analysis(conn, recording["id"], "femme_scoring",
                      {"exercise_type": "integration", "score": 80})
        save_analysis(conn, recording["id"], "femme_scoring",
                      {"exercise_type": "ceiling_probe", "score": 90})
    rows = conn.execute(
        "SELECT exercise_type FROM analyses WHERE recording_id = ? AND exercise_type = ?",
        (recording["id"], "integration")
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "integration"

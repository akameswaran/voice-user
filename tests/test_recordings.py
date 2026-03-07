import numpy as np
import pytest

from voice_user.db import init_db
from voice_user.users import create_user
from voice_user.sessions import create_session
from voice_user.recordings import (
    write_audio_file, register_recording, save_recording,
    get_recording, list_recordings, delete_recording,
)


@pytest.fixture
def conn(tmp_path):
    c = init_db(tmp_path / "test.db")
    yield c
    c.close()


@pytest.fixture
def user(conn):
    return create_user(conn, name="Alice")


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
    """1 second of 440 Hz sine wave at 16kHz."""
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    return (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), sr


def test_write_audio_file(rec_dir, user, sample_audio):
    audio, sr = sample_audio
    rel_path = write_audio_file(rec_dir, user["id"], audio, sr)
    full_path = rec_dir / rel_path
    assert full_path.exists()
    assert full_path.suffix == ".wav"
    assert user["id"] in str(rel_path)


def test_write_audio_file_creates_user_dir(rec_dir, user, sample_audio):
    audio, sr = sample_audio
    write_audio_file(rec_dir, user["id"], audio, sr)
    user_dir = rec_dir / user["id"]
    assert user_dir.is_dir()


def test_register_recording(conn, user):
    rec = register_recording(
        conn, user["id"], filename="test/file.wav",
        recorded_at="2026-03-07T00:00:00+00:00",
        duration_s=1.0, sample_rate=16000,
    )
    assert rec["user_id"] == user["id"]
    assert rec["filename"] == "test/file.wav"
    assert rec["session_id"] is None


def test_register_recording_with_session(conn, user, session):
    rec = register_recording(
        conn, user["id"], filename="test/file.wav",
        recorded_at="2026-03-07T00:00:00+00:00",
        session_id=session["id"],
    )
    assert rec["session_id"] == session["id"]


def test_register_recording_with_metadata(conn, user):
    rec = register_recording(
        conn, user["id"], filename="test/file.wav",
        recorded_at="2026-03-07T00:00:00+00:00",
        metadata={"prompt": "Say hello"},
    )
    assert rec["metadata"] == {"prompt": "Say hello"}


def test_save_recording(conn, user, rec_dir, sample_audio):
    audio, sr = sample_audio
    rec = save_recording(conn, user["id"], audio, sr, rec_dir)
    assert rec["user_id"] == user["id"]
    assert rec["sample_rate"] == sr
    assert rec["duration_s"] == pytest.approx(1.0, abs=0.01)
    full_path = rec_dir / rec["filename"]
    assert full_path.exists()


def test_save_recording_with_session(conn, user, session, rec_dir, sample_audio):
    audio, sr = sample_audio
    rec = save_recording(
        conn, user["id"], audio, sr, rec_dir, session_id=session["id"]
    )
    assert rec["session_id"] == session["id"]


def test_get_recording(conn, user, rec_dir, sample_audio):
    audio, sr = sample_audio
    saved = save_recording(conn, user["id"], audio, sr, rec_dir)
    fetched = get_recording(conn, saved["id"])
    assert fetched is not None
    assert fetched["id"] == saved["id"]


def test_get_recording_not_found(conn):
    assert get_recording(conn, "nonexistent") is None


def test_list_recordings_by_user(conn, user, rec_dir, sample_audio):
    audio, sr = sample_audio
    save_recording(conn, user["id"], audio, sr, rec_dir)
    save_recording(conn, user["id"], audio, sr, rec_dir)
    recs = list_recordings(conn, user_id=user["id"])
    assert len(recs) == 2


def test_list_recordings_by_session(conn, user, session, rec_dir, sample_audio):
    audio, sr = sample_audio
    save_recording(conn, user["id"], audio, sr, rec_dir, session_id=session["id"])
    save_recording(conn, user["id"], audio, sr, rec_dir)  # standalone
    recs = list_recordings(conn, session_id=session["id"])
    assert len(recs) == 1


def test_delete_recording(conn, user, rec_dir, sample_audio):
    audio, sr = sample_audio
    rec = save_recording(conn, user["id"], audio, sr, rec_dir)
    file_path = rec_dir / rec["filename"]
    assert file_path.exists()
    result = delete_recording(conn, rec["id"], rec_dir)
    assert result is True
    assert not file_path.exists()
    assert get_recording(conn, rec["id"]) is None


def test_delete_recording_not_found(conn, rec_dir):
    result = delete_recording(conn, "nonexistent", rec_dir)
    assert result is False


def test_cascade_delete_user_deletes_recordings(conn, user, rec_dir, sample_audio):
    audio, sr = sample_audio
    save_recording(conn, user["id"], audio, sr, rec_dir)
    conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    recs = list_recordings(conn, user_id=user["id"])
    assert recs == []


def test_session_delete_sets_recording_null(conn, user, session, rec_dir, sample_audio):
    audio, sr = sample_audio
    rec = save_recording(
        conn, user["id"], audio, sr, rec_dir, session_id=session["id"]
    )
    conn.execute("DELETE FROM sessions WHERE id = ?", (session["id"],))
    fetched = get_recording(conn, rec["id"])
    assert fetched is not None
    assert fetched["session_id"] is None

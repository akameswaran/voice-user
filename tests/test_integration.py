"""End-to-end integration test simulating a coaching app session."""

import numpy as np

from voice_user import (
    init_db, create_user, list_users,
    create_session, end_session, list_sessions,
    save_recording, list_recordings, delete_recording,
)


def test_full_coaching_workflow(tmp_path):
    """Simulate: create user, start session, record audio, end session, query history."""
    db_path = tmp_path / "data" / "test.db"
    rec_dir = tmp_path / "data" / "recordings"
    conn = init_db(db_path)

    # Create two users
    with conn:
        alice = create_user(conn, name="Alice")
        bob = create_user(conn, name="Bob")

    assert len(list_users(conn)) == 2

    # Alice does a practice session
    with conn:
        session = create_session(conn, alice["id"], session_type="practice")

    # Record some audio during the session
    audio = np.zeros(16000, dtype=np.float32)  # 1s silence
    with conn:
        rec1 = save_recording(
            conn, alice["id"], audio, 16000, rec_dir,
            session_id=session["id"], metadata={"prompt": "hello"},
        )
        rec2 = save_recording(
            conn, alice["id"], audio, 16000, rec_dir,
            session_id=session["id"], metadata={"prompt": "goodbye"},
        )

    # End the session with metrics
    with conn:
        ended = end_session(
            conn, session["id"], duration_s=45.0,
            metrics={"score": 82, "pitch": 95, "resonance": 70},
        )

    assert ended["duration_s"] == 45.0
    assert ended["metrics"]["score"] == 82

    # Query Alice's history
    sessions = list_sessions(conn, alice["id"])
    assert len(sessions) == 1

    recs = list_recordings(conn, session_id=session["id"])
    assert len(recs) == 2

    # Bob has no sessions
    assert list_sessions(conn, bob["id"]) == []

    # Delete one recording
    with conn:
        delete_recording(conn, rec1["id"], rec_dir)

    assert len(list_recordings(conn, session_id=session["id"])) == 1

    conn.close()


def test_multi_user_isolation(tmp_path):
    """Verify users only see their own sessions and recordings."""
    conn = init_db(tmp_path / "test.db")
    rec_dir = tmp_path / "recordings"

    with conn:
        alice = create_user(conn, name="Alice")
        bob = create_user(conn, name="Bob")

    audio = np.zeros(8000, dtype=np.float32)

    with conn:
        s_alice = create_session(conn, alice["id"], "practice")
        save_recording(conn, alice["id"], audio, 16000, rec_dir, session_id=s_alice["id"])

        s_bob = create_session(conn, bob["id"], "practice")
        save_recording(conn, bob["id"], audio, 16000, rec_dir, session_id=s_bob["id"])

    assert len(list_sessions(conn, alice["id"])) == 1
    assert len(list_sessions(conn, bob["id"])) == 1
    assert len(list_recordings(conn, user_id=alice["id"])) == 1
    assert len(list_recordings(conn, user_id=bob["id"])) == 1

    conn.close()

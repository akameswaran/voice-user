import pytest

from voice_user.db import init_db
from voice_user.users import create_user
from voice_user.sessions import (
    create_session, end_session, get_session, list_sessions, update_session,
)


@pytest.fixture
def conn(tmp_path):
    c = init_db(tmp_path / "test.db")
    yield c
    c.close()


@pytest.fixture
def user(conn):
    return create_user(conn, name="Alice")


def test_create_session(conn, user):
    s = create_session(conn, user["id"], session_type="workshop")
    assert s["user_id"] == user["id"]
    assert s["session_type"] == "workshop"
    assert s["ended_at"] is None
    assert s["duration_s"] is None
    assert s["metrics"] == {}


def test_create_session_with_metrics(conn, user):
    s = create_session(conn, user["id"], "practice", metrics={"score": 85})
    assert s["metrics"] == {"score": 85}


def test_end_session(conn, user):
    s = create_session(conn, user["id"], "workshop")
    ended = end_session(conn, s["id"], duration_s=120.5, metrics={"passed": True})
    assert ended["ended_at"] is not None
    assert ended["duration_s"] == 120.5
    assert ended["metrics"] == {"passed": True}


def test_end_session_preserves_existing_metrics(conn, user):
    s = create_session(conn, user["id"], "workshop", metrics={"start_score": 50})
    ended = end_session(conn, s["id"], duration_s=60.0, metrics={"end_score": 80})
    assert ended["metrics"] == {"end_score": 80}


def test_get_session(conn, user):
    created = create_session(conn, user["id"], "workshop")
    fetched = get_session(conn, created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]


def test_get_session_not_found(conn):
    assert get_session(conn, "nonexistent") is None


def test_list_sessions(conn, user):
    create_session(conn, user["id"], "workshop")
    create_session(conn, user["id"], "evaluation")
    sessions = list_sessions(conn, user["id"])
    assert len(sessions) == 2


def test_list_sessions_filter_by_type(conn, user):
    create_session(conn, user["id"], "workshop")
    create_session(conn, user["id"], "evaluation")
    create_session(conn, user["id"], "workshop")
    sessions = list_sessions(conn, user["id"], session_type="workshop")
    assert len(sessions) == 2
    assert all(s["session_type"] == "workshop" for s in sessions)


def test_list_sessions_limit(conn, user):
    for i in range(5):
        create_session(conn, user["id"], "practice")
    sessions = list_sessions(conn, user["id"], limit=3)
    assert len(sessions) == 3


def test_list_sessions_ordered_by_started_at(conn, user):
    s1 = create_session(conn, user["id"], "workshop")
    s2 = create_session(conn, user["id"], "evaluation")
    sessions = list_sessions(conn, user["id"])
    assert sessions[0]["id"] == s1["id"]
    assert sessions[1]["id"] == s2["id"]


def test_update_session(conn, user):
    s = create_session(conn, user["id"], "workshop")
    updated = update_session(conn, s["id"], metrics={"progress": 50})
    assert updated["metrics"] == {"progress": 50}


def test_cascade_delete_user_deletes_sessions(conn, user):
    create_session(conn, user["id"], "workshop")
    conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    sessions = list_sessions(conn, user["id"])
    assert sessions == []

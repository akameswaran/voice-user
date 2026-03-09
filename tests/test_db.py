import sqlite3

import pytest

from voice_user.db import init_db, get_db


def test_init_db_creates_file(tmp_path):
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    assert db_path.exists()
    conn.close()


def test_init_db_enables_wal(tmp_path):
    conn = init_db(tmp_path / "test.db")
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()


def test_init_db_enables_foreign_keys(tmp_path):
    conn = init_db(tmp_path / "test.db")
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1
    conn.close()


def test_init_db_creates_schema_version_table(tmp_path):
    conn = init_db(tmp_path / "test.db")
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchall()
    assert len(rows) == 1
    conn.close()


def test_init_db_creates_users_table(tmp_path):
    conn = init_db(tmp_path / "test.db")
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchall()
    assert len(rows) == 1
    conn.close()


def test_init_db_creates_sessions_table(tmp_path):
    conn = init_db(tmp_path / "test.db")
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
    ).fetchall()
    assert len(rows) == 1
    conn.close()


def test_init_db_creates_recordings_table(tmp_path):
    conn = init_db(tmp_path / "test.db")
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='recordings'"
    ).fetchall()
    assert len(rows) == 1
    conn.close()


def test_init_db_sets_version(tmp_path):
    conn = init_db(tmp_path / "test.db")
    version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version == 2
    conn.close()


def test_init_db_idempotent(tmp_path):
    db_path = tmp_path / "test.db"
    conn1 = init_db(db_path)
    conn1.close()
    conn2 = init_db(db_path)
    version = conn2.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version == 2
    count = conn2.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    assert count == 2
    conn2.close()


def test_get_db_returns_connection(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = get_db(db_path)
    assert isinstance(conn, sqlite3.Connection)
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1
    conn.close()


def test_json_check_constraint(tmp_path):
    conn = init_db(tmp_path / "test.db")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO users (id, name, created_at, preferences) VALUES (?, ?, ?, ?)",
            ("test-id", "Test", "2026-01-01T00:00:00+00:00", "not-valid-json"),
        )
    conn.close()


def test_init_db_creates_parent_dirs(tmp_path):
    db_path = tmp_path / "nested" / "deep" / "test.db"
    conn = init_db(db_path)
    assert db_path.exists()
    conn.close()

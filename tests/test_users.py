import pytest

from voice_user.db import init_db
from voice_user.users import create_user, get_user, list_users, update_user


@pytest.fixture
def conn(tmp_path):
    c = init_db(tmp_path / "test.db")
    yield c
    c.close()


def test_create_user(conn):
    user = create_user(conn, name="Alice")
    assert user["name"] == "Alice"
    assert "id" in user
    assert "created_at" in user
    assert user["preferences"] == {}


def test_create_user_with_preferences(conn):
    user = create_user(conn, name="Bob", preferences={"theme": "dark"})
    assert user["preferences"] == {"theme": "dark"}


def test_get_user(conn):
    created = create_user(conn, name="Alice")
    fetched = get_user(conn, created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["name"] == "Alice"


def test_get_user_not_found(conn):
    assert get_user(conn, "nonexistent") is None


def test_list_users_empty(conn):
    assert list_users(conn) == []


def test_list_users(conn):
    create_user(conn, name="Alice")
    create_user(conn, name="Bob")
    users = list_users(conn)
    assert len(users) == 2
    names = {u["name"] for u in users}
    assert names == {"Alice", "Bob"}


def test_update_user_name(conn):
    user = create_user(conn, name="Alice")
    updated = update_user(conn, user["id"], name="Alicia")
    assert updated["name"] == "Alicia"
    fetched = get_user(conn, user["id"])
    assert fetched["name"] == "Alicia"


def test_update_user_preferences(conn):
    user = create_user(conn, name="Alice")
    updated = update_user(conn, user["id"], preferences={"lang": "es"})
    assert updated["preferences"] == {"lang": "es"}


def test_update_user_not_found(conn):
    with pytest.raises(ValueError, match="not found"):
        update_user(conn, "nonexistent", name="Ghost")


def test_create_user_unique_ids(conn):
    u1 = create_user(conn, name="Alice")
    u2 = create_user(conn, name="Alice")
    assert u1["id"] != u2["id"]

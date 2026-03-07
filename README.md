# voice-user

Shared user management, session tracking, and recording storage for voice coaching apps.

## Install (as editable dependency)

```toml
[tool.uv.sources]
voice-user = { path = "../voice-user", editable = true }
```

## Usage

```python
from voice_user import init_db, create_user, create_session

conn = init_db(Path("data/app.db"))

with conn:
    user = create_user(conn, name="Alice")
    session = create_session(conn, user["id"], session_type="practice")
```

"""Shared user/profile/storage for voice coaching apps."""

from .db import init_db, get_db
from .users import create_user, get_user, list_users, update_user
from .sessions import create_session, end_session, get_session, list_sessions, update_session
from .recordings import (
    write_audio_file, register_recording, save_recording,
    get_recording, list_recordings, delete_recording,
)
from .types import UserRecord, SessionRecord, RecordingRecord
from .analyses import (
    AnalysisRecord,
    save_analysis,
    get_latest_analysis,
    list_analyses,
    delete_analyses,
)

__all__ = [
    "init_db", "get_db",
    "create_user", "get_user", "list_users", "update_user",
    "create_session", "end_session", "get_session", "list_sessions", "update_session",
    "write_audio_file", "register_recording", "save_recording",
    "get_recording", "list_recordings", "delete_recording",
    "UserRecord", "SessionRecord", "RecordingRecord",
    "AnalysisRecord", "save_analysis", "get_latest_analysis",
    "list_analyses", "delete_analyses",
]

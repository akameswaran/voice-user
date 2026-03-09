"""Return type definitions for voice-user API."""

from typing import TypedDict


class UserRecord(TypedDict):
    id: str
    name: str
    created_at: str
    preferences: dict


class SessionRecord(TypedDict):
    id: str
    user_id: str
    session_type: str
    started_at: str
    ended_at: str | None
    duration_s: float | None
    metrics: dict


class RecordingRecord(TypedDict):
    id: str
    session_id: str | None
    user_id: str
    filename: str
    recorded_at: str
    duration_s: float | None
    sample_rate: int | None
    metadata: dict


class AnalysisRecord(TypedDict):
    id: str
    recording_id: str
    analyzer: str
    version: str | None
    created_at: str
    results: dict

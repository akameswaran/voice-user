def test_public_api_imports():
    from voice_user import (
        init_db, get_db,
        create_user, get_user, list_users, update_user,
        create_session, end_session, get_session, list_sessions, update_session,
        write_audio_file, register_recording, save_recording,
        get_recording, list_recordings, delete_recording,
        UserRecord, SessionRecord, RecordingRecord,
        AnalysisRecord, save_analysis, get_latest_analysis,
        list_analyses, delete_analyses,
    )
    assert callable(init_db)
    assert callable(create_user)
    assert callable(save_recording)
    assert callable(save_analysis)
    assert callable(get_latest_analysis)
    assert callable(list_analyses)
    assert callable(delete_analyses)

"""Tests for pending file processing."""

import json
from pathlib import Path


def test_get_pending_dir_creates_directory(tmp_path, monkeypatch):
    """get_pending_dir creates directory if it doesn't exist."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    from session_log.pending import get_pending_dir

    result = get_pending_dir()

    assert result == tmp_path / ".claude" / "session-log" / "pending"
    assert result.exists()


def test_write_pending_metadata_creates_file(tmp_path):
    """write_pending_metadata creates JSON file with correct structure."""
    from session_log.pending import write_pending_metadata

    metadata = {
        "filename": "2026-01-12_10-00-00_test.md",
        "date": "2026-01-12T10:00:00+00:00",
        "project": "test-project",
        "summary_path": "/path/to/summary.md",
    }
    embedding_data = {
        "content": "# Summary content",
        "metadata": {"project": "test-project"},
    }

    success, error = write_pending_metadata(
        filename="2026-01-12_10-00-00_test.md",
        metadata=metadata,
        embedding_data=embedding_data,
        pending_dir=tmp_path,
    )

    assert success is True
    assert error is None

    pending_file = tmp_path / "2026-01-12_10-00-00_test.md.json"
    assert pending_file.exists()

    data = json.loads(pending_file.read_text())
    assert data["version"] == 1
    assert "created_at" in data
    assert data["metadata"] == metadata
    assert data["embedding"] == embedding_data


def test_process_pending_sessions_indexes_and_embeds(tmp_path, monkeypatch):
    """process_pending_sessions indexes in SQLite and embeds in ChromaDB."""
    from session_log.pending import write_pending_metadata, process_pending_sessions

    # Create a pending file
    metadata = {
        "filename": "test-session.md",
        "date": "2026-01-12T10:00:00+00:00",
        "project": "test",
        "summary_path": str(tmp_path / "summary.md"),
    }
    embedding_data = {
        "content": "Test content",
        "metadata": {"project": "test"},
    }
    write_pending_metadata("test-session.md", metadata, embedding_data, tmp_path)

    # Mock the index and embed functions
    indexed_calls = []
    embedded_calls = []

    def mock_index(meta, db_path=None):
        indexed_calls.append(meta)
        return True, None

    def mock_embed(session_id, content, metadata=None, db_path=None):
        embedded_calls.append((session_id, content))
        return True, None

    monkeypatch.setattr("session_log.pending.index_session", mock_index)
    monkeypatch.setattr("session_log.pending.embed_session", mock_embed)

    stats = process_pending_sessions(pending_dir=tmp_path)

    assert stats["processed"] == 1
    assert stats["indexed"] == 1
    assert stats["embedded"] == 1
    assert stats["deleted"] == 1
    assert len(indexed_calls) == 1
    assert len(embedded_calls) == 1
    assert not (tmp_path / "test-session.md.json").exists()  # Deleted after success

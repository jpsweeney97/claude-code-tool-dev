"""Tests for pending processing integration in tool handlers."""

import json


def test_handle_tool_processes_pending_on_first_call(tmp_path, monkeypatch):
    """handle_tool processes pending sessions on first call."""
    from tool_handlers import handle_tool, _reset_pending_flag

    # Reset the global flag for testing
    _reset_pending_flag()

    # Create pending directory with a file
    pending_dir = tmp_path / "pending"
    pending_dir.mkdir()

    pending_file = pending_dir / "test-session.md.json"
    pending_file.write_text(
        json.dumps(
            {
                "version": 1,
                "created_at": "2026-01-12T10:00:00+00:00",
                "metadata": {
                    "filename": "test-session.md",
                    "date": "2026-01-12T10:00:00+00:00",
                    "project": "test",
                    "summary_path": str(tmp_path / "summary.md"),
                },
                "embedding": {
                    "content": "Test content",
                    "metadata": {"project": "test"},
                },
            }
        )
    )

    processed_calls = []

    def mock_process(pending_dir=None, db_path=None, chroma_path=None):
        processed_calls.append(True)
        return {"processed": 1, "indexed": 1, "embedded": 1, "deleted": 1}

    monkeypatch.setattr("tool_handlers.process_pending_sessions", mock_process)

    # First call should process pending
    handle_tool("list_sessions", {})
    assert len(processed_calls) == 1

    # Second call should NOT process pending
    handle_tool("list_sessions", {})
    assert len(processed_calls) == 1  # Still 1, not 2

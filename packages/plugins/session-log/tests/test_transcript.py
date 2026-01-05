"""Tests for transcript parser."""


import pytest


@pytest.fixture
def sample_transcript(tmp_path):
    """Create a sample transcript file."""
    transcript = tmp_path / "transcript.jsonl"
    content = '''{"type":"user","message":{"content":"Help me fix the auth bug"}}
{"type":"assistant","message":{"content":[{"type":"thinking","thinking":"Let me look"},{"type":"tool_use","name":"Read","input":{"file_path":"src/auth.py"}},{"type":"text","text":"Found the issue."}]}}
{"type":"user","message":{"content":"Fix it"}}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"src/auth.py","old_string":"bug","new_string":"fix"}},{"type":"text","text":"Fixed!"}]}}
'''
    transcript.write_text(content)
    return transcript


def test_parse_transcript_extracts_tool_calls(sample_transcript):
    """Parser extracts tool calls from transcript."""
    from session_log.transcript import parse_transcript

    result = parse_transcript(sample_transcript)

    assert len(result.tool_calls) == 2
    assert result.tool_calls[0]["name"] == "Read"
    assert result.tool_calls[1]["name"] == "Edit"


def test_parse_transcript_extracts_files_touched(sample_transcript):
    """Parser extracts unique files touched."""
    from session_log.transcript import parse_transcript

    result = parse_transcript(sample_transcript)

    assert "src/auth.py" in result.files_touched


def test_parse_transcript_counts_messages(sample_transcript):
    """Parser counts user and assistant messages."""
    from session_log.transcript import parse_transcript

    result = parse_transcript(sample_transcript)

    assert result.user_message_count == 2
    assert result.assistant_message_count == 2


def test_parse_transcript_extracts_text_content(sample_transcript):
    """Parser extracts text content from assistant messages."""
    from session_log.transcript import parse_transcript

    result = parse_transcript(sample_transcript)

    assert "Found the issue" in result.assistant_text
    assert "Fixed!" in result.assistant_text


def test_parse_transcript_handles_malformed_json(tmp_path):
    """Test that malformed JSON lines are skipped with warning."""
    import sys
    from io import StringIO

    from session_log.transcript import parse_transcript

    transcript = tmp_path / "test.jsonl"
    transcript.write_text(
        '{"type": "user", "message": {}}\n'
        "not valid json\n"
        '{"type": "assistant", "message": {"content": []}}\n'
    )

    # Capture stderr
    old_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        result = parse_transcript(transcript)
        stderr_output = sys.stderr.getvalue()
    finally:
        sys.stderr = old_stderr

    # Should process valid lines
    assert result.user_message_count == 1
    assert result.assistant_message_count == 1

    # Should warn about invalid line
    assert "malformed JSON" in stderr_output.lower() or "line 2" in stderr_output


def test_parse_transcript_handles_empty_lines(tmp_path):
    """Test that empty lines are skipped silently."""
    from session_log.transcript import parse_transcript

    transcript = tmp_path / "test.jsonl"
    transcript.write_text(
        '{"type": "user", "message": {}}\n'
        "\n"
        "   \n"
        '{"type": "user", "message": {}}\n'
    )

    result = parse_transcript(transcript)
    assert result.user_message_count == 2


def test_bash_command_extraction(tmp_path):
    """Test that Bash commands are extracted from tool calls."""
    import json

    from session_log.transcript import parse_transcript

    transcript = tmp_path / "test.jsonl"

    entries = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls -la"}},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "git status"}},
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/test.py"}},
        ]}},
    ]

    transcript.write_text("\n".join(json.dumps(e) for e in entries))

    result = parse_transcript(transcript)

    assert result.commands_run == ["ls -la", "git status"]
    assert len(result.tool_calls) == 3


def test_bash_command_with_missing_command_field(tmp_path):
    """Test that Bash tool calls without command field are handled."""
    import json

    from session_log.transcript import parse_transcript

    transcript = tmp_path / "test.jsonl"

    entries = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {}},  # No command
        ]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "echo test"}},
        ]}},
    ]

    transcript.write_text("\n".join(json.dumps(e) for e in entries))

    result = parse_transcript(transcript)

    # Should only include the one with a command
    assert result.commands_run == ["echo test"]

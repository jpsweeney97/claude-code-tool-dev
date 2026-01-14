# Session-Log Lightweight Hooks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make session-log hooks stdlib-only by deferring ChromaDB embedding to the MCP server, reducing hook execution time from ~500ms to <100ms.

**Architecture:** Hooks write a "pending" JSON file with all data needed for indexing. MCP server processes pending files on first tool call, performing SQLite indexing and ChromaDB embedding. This separates fast capture from slow indexing.

**Tech Stack:** Python 3.12 stdlib (json, subprocess, datetime, pathlib, dataclasses), SQLite3, ChromaDB (deferred to MCP server only)

---

## Task 1: Create Pending File Module

**Files:**
- Create: `packages/plugins/session-log/session_log/pending.py`
- Create: `packages/plugins/session-log/tests/test_pending.py`

### Step 1.1: Write test for get_pending_dir

```python
# tests/test_pending.py
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
```

### Step 1.2: Run test to verify it fails

Run: `cd packages/plugins/session-log && uv run pytest tests/test_pending.py::test_get_pending_dir_creates_directory -v`
Expected: FAIL with "No module named 'session_log.pending'"

### Step 1.3: Write minimal implementation

```python
# session_log/pending.py
"""Process pending session files for deferred indexing."""

from pathlib import Path


def get_pending_dir() -> Path:
    """Get directory for pending session files."""
    pending_dir = Path.home() / ".claude" / "session-log" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    return pending_dir
```

### Step 1.4: Run test to verify it passes

Run: `cd packages/plugins/session-log && uv run pytest tests/test_pending.py::test_get_pending_dir_creates_directory -v`
Expected: PASS

### Step 1.5: Write test for write_pending_metadata

Add to `tests/test_pending.py`:

```python
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
```

### Step 1.6: Run test to verify it fails

Run: `cd packages/plugins/session-log && uv run pytest tests/test_pending.py::test_write_pending_metadata_creates_file -v`
Expected: FAIL with "cannot import name 'write_pending_metadata'"

### Step 1.7: Write implementation for write_pending_metadata

Add to `session_log/pending.py`:

```python
import json
from datetime import datetime, timezone


def write_pending_metadata(
    filename: str,
    metadata: dict,
    embedding_data: dict,
    pending_dir: Path | None = None,
) -> tuple[bool, str | None]:
    """Write pending metadata for deferred indexing.

    Args:
        filename: The session filename (used as pending file basename).
        metadata: SQLite metadata dict.
        embedding_data: Dict with 'content' and 'metadata' for ChromaDB.
        pending_dir: Optional override for pending directory (for testing).

    Returns:
        Tuple of (success, error_message).
    """
    if pending_dir is None:
        pending_dir = get_pending_dir()

    pending_file = pending_dir / f"{filename}.json"

    pending_data = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
        "embedding": embedding_data,
    }

    try:
        pending_file.write_text(json.dumps(pending_data, indent=2))
        return True, None
    except OSError as e:
        return False, f"Failed to write pending file: {e}"
```

### Step 1.8: Run test to verify it passes

Run: `cd packages/plugins/session-log && uv run pytest tests/test_pending.py -v`
Expected: PASS (2 tests)

### Step 1.9: Write test for process_pending_sessions

Add to `tests/test_pending.py`:

```python
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
```

### Step 1.10: Run test to verify it fails

Run: `cd packages/plugins/session-log && uv run pytest tests/test_pending.py::test_process_pending_sessions_indexes_and_embeds -v`
Expected: FAIL with "cannot import name 'process_pending_sessions'"

### Step 1.11: Write implementation for process_pending_sessions

Add to `session_log/pending.py`:

```python
import sys

from .storage import index_session
from .search import embed_session


def process_pending_sessions(
    pending_dir: Path | None = None,
    db_path: Path | None = None,
    chroma_path: Path | None = None,
) -> dict:
    """Process all pending session files.

    For each pending file:
    1. Index in SQLite
    2. Embed in ChromaDB
    3. Delete pending file if both succeed

    Args:
        pending_dir: Optional override for pending directory (for testing).
        db_path: Optional override for SQLite path (for testing).
        chroma_path: Optional override for ChromaDB path (for testing).

    Returns:
        Dict with counts: processed, indexed, embedded, failed, deleted.
    """
    if pending_dir is None:
        pending_dir = get_pending_dir()

    if not pending_dir.exists():
        return {"processed": 0, "indexed": 0, "embedded": 0, "failed": 0, "deleted": 0}

    stats = {"processed": 0, "indexed": 0, "embedded": 0, "failed": 0, "deleted": 0}

    for pending_file in pending_dir.glob("*.json"):
        stats["processed"] += 1

        try:
            data = json.loads(pending_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Skipping malformed pending file {pending_file.name}: {e}", file=sys.stderr)
            pending_file.unlink(missing_ok=True)
            stats["failed"] += 1
            continue

        version = data.get("version", 1)
        if version != 1:
            print(f"Warning: Unknown pending file version {version}, skipping", file=sys.stderr)
            stats["failed"] += 1
            continue

        metadata = data.get("metadata", {})
        embedding = data.get("embedding", {})

        # Index in SQLite
        indexed, index_error = index_session(metadata, db_path=db_path)
        if indexed:
            stats["indexed"] += 1
        else:
            print(f"Warning: Failed to index {pending_file.name}: {index_error}", file=sys.stderr)

        # Embed in ChromaDB
        embedded, embed_error = embed_session(
            session_id=metadata.get("filename", pending_file.stem),
            content=embedding.get("content", ""),
            metadata=embedding.get("metadata"),
            db_path=chroma_path,
        )
        if embedded:
            stats["embedded"] += 1
        else:
            print(f"Warning: Failed to embed {pending_file.name}: {embed_error}", file=sys.stderr)

        # Delete only if both succeeded
        if indexed and embedded:
            pending_file.unlink(missing_ok=True)
            stats["deleted"] += 1

    return stats
```

### Step 1.12: Run all pending tests

Run: `cd packages/plugins/session-log && uv run pytest tests/test_pending.py -v`
Expected: PASS (3 tests)

### Step 1.13: Commit Task 1

```bash
cd packages/plugins/session-log
git add session_log/pending.py tests/test_pending.py
git commit -m "feat(session-log): add pending file module for deferred indexing"
```

---

## Task 2: Create Standalone SessionEnd Hook

**Files:**
- Create: `packages/plugins/session-log/scripts/session_end_standalone.py`
- Create: `packages/plugins/session-log/tests/test_session_end_standalone.py`

### Step 2.1: Write test for inlined TranscriptData and parse_transcript

```python
# tests/test_session_end_standalone.py
"""Tests for standalone session_end hook (stdlib-only)."""

import json
from pathlib import Path


def test_parse_transcript_extracts_files(tmp_path):
    """Inlined parse_transcript extracts files from tool calls."""
    # Import from standalone script (not package)
    import sys
    scripts_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))

    from session_end_standalone import parse_transcript, TranscriptData

    transcript = tmp_path / "test.jsonl"
    transcript.write_text(json.dumps({
        "type": "assistant",
        "message": {
            "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": "/path/to/file.py"}},
                {"type": "tool_use", "name": "Bash", "input": {"command": "pytest"}},
            ]
        }
    }) + "\n")

    result = parse_transcript(transcript)

    assert isinstance(result, TranscriptData)
    assert "/path/to/file.py" in result.files_touched
    assert "pytest" in result.commands_run
    assert result.assistant_message_count == 1
```

### Step 2.2: Run test to verify it fails

Run: `cd packages/plugins/session-log && uv run pytest tests/test_session_end_standalone.py::test_parse_transcript_extracts_files -v`
Expected: FAIL with "No module named 'session_end_standalone'"

### Step 2.3: Write session_end_standalone.py with inlined transcript parsing

```python
#!/usr/bin/env python3
"""Lightweight SessionEnd hook - stdlib only, no external dependencies.

This script captures session data and writes a pending file for deferred
indexing. It does NOT import chromadb or the session_log package.
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ============================================================================
# TRANSCRIPT PARSING (inlined from session_log/transcript.py)
# ============================================================================

@dataclass
class TranscriptData:
    """Parsed data from a session transcript."""
    tool_calls: list = field(default_factory=list)
    files_touched: set = field(default_factory=set)
    user_message_count: int = 0
    assistant_message_count: int = 0
    assistant_text: str = ""
    commands_run: list = field(default_factory=list)


def extract_files_from_tool(name: str, input_data: dict) -> set:
    """Extract file paths from tool input."""
    files = set()
    if name in ("Read", "Write", "Edit"):
        if path := input_data.get("file_path"):
            files.add(path)
    return files


def parse_transcript(path: Path) -> TranscriptData:
    """Parse a transcript JSONL file and extract session data."""
    result = TranscriptData()
    text_parts = []

    with open(path) as f:
        for line_num, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON at line {line_num}: {e}", file=sys.stderr)
                continue

            msg_type = entry.get("type")
            message = entry.get("message", {})

            if msg_type == "user":
                result.user_message_count += 1
            elif msg_type == "assistant":
                result.assistant_message_count += 1
                content = message.get("content", [])

                if isinstance(content, list):
                    for block in content:
                        block_type = block.get("type")

                        if block_type == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})

                            result.tool_calls.append({"name": tool_name, "input": tool_input})
                            result.files_touched.update(extract_files_from_tool(tool_name, tool_input))

                            if tool_name == "Bash":
                                if cmd := tool_input.get("command"):
                                    result.commands_run.append(cmd)

                        elif block_type == "text":
                            if text := block.get("text"):
                                text_parts.append(text)

    result.assistant_text = "\n".join(text_parts)
    return result


# ============================================================================
# SUMMARY GENERATION (inlined from session_log/summarizer.py)
# ============================================================================

def generate_title(transcript_data: TranscriptData, branch: str | None) -> str:
    """Generate a session title from content."""
    if branch and branch not in ("main", "master"):
        parts = branch.split("/")[-1].replace("-", " ").replace("_", " ")
        return parts.title()

    if transcript_data.files_touched:
        first_file = sorted(transcript_data.files_touched)[0]
        return Path(first_file).stem.replace("_", " ").title()

    return "Session"


def generate_slug(title: str) -> str:
    """Generate a filename slug from title."""
    return title.lower().replace(" ", "-")[:30]


def calculate_duration_minutes(start_time: str, end_time: datetime) -> int:
    """Calculate session duration in minutes."""
    start = datetime.fromisoformat(start_time)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    delta = end_time - start
    return max(1, int(delta.total_seconds() / 60))


def generate_summary(
    transcript_data: TranscriptData,
    session_state: dict,
    commit_end: str | None = None,
    commits_made: int = 0,
    end_time: datetime | None = None,
) -> str:
    """Generate a session summary markdown document."""
    if end_time is None:
        end_time = datetime.now(timezone.utc)

    start_time = session_state.get("start_time", end_time.isoformat())
    branch = session_state.get("branch")
    project = Path(session_state.get("cwd", ".")).name

    title = generate_title(transcript_data, branch)
    duration = calculate_duration_minutes(start_time, end_time)

    frontmatter_lines = [
        "---",
        f"date: {start_time}",
        f"duration_minutes: {duration}",
        f"project: {project}",
    ]

    if branch:
        frontmatter_lines.append(f"branch: {branch}")
    if session_state.get("commit_start"):
        frontmatter_lines.append(f"commit_start: {session_state['commit_start']}")
    if commit_end:
        frontmatter_lines.append(f"commit_end: {commit_end}")
    if commits_made:
        frontmatter_lines.append(f"commits_made: {commits_made}")

    frontmatter_lines.extend([
        f"files_touched: {len(transcript_data.files_touched)}",
        f"commands_run: {len(transcript_data.commands_run)}",
        "---",
    ])

    content_lines = [
        "",
        f"# Session: {title}",
        "",
        "## Accomplished",
        "",
        "- Session summary pending analysis",
        "",
        "## Files",
        "",
    ]

    if transcript_data.files_touched:
        files = sorted(transcript_data.files_touched)
        if len(files) <= 5:
            content_lines.append(", ".join(files))
        else:
            content_lines.append(", ".join(files[:5]) + f" (+{len(files) - 5})")
    else:
        content_lines.append("No files modified")

    content_lines.append("")

    return "\n".join(frontmatter_lines + content_lines)


def get_summary_filename(session_state: dict, title: str) -> str:
    """Generate the summary filename."""
    start_time = session_state.get("start_time", datetime.now(timezone.utc).isoformat())
    try:
        dt = datetime.fromisoformat(start_time)
    except ValueError:
        dt = datetime.now(timezone.utc)
    date_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
    slug = generate_slug(title)
    return f"{date_str}_{slug}.md"


# ============================================================================
# PENDING FILE MANAGEMENT
# ============================================================================

def get_pending_dir() -> Path:
    """Get directory for pending session files."""
    pending_dir = Path.home() / ".claude" / "session-log" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    return pending_dir


def write_pending_metadata(
    filename: str,
    metadata: dict,
    embedding_data: dict,
    pending_dir: Path | None = None,
) -> tuple[bool, str | None]:
    """Write pending metadata for deferred indexing."""
    if pending_dir is None:
        pending_dir = get_pending_dir()

    pending_file = pending_dir / f"{filename}.json"

    pending_data = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
        "embedding": embedding_data,
    }

    try:
        pending_file.write_text(json.dumps(pending_data, indent=2))
        return True, None
    except OSError as e:
        return False, f"Failed to write pending file: {e}"


# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def get_state_dir() -> Path:
    """Get directory for session state files."""
    return Path.home() / ".claude" / "session-log" / "state"


def load_session_state(session_id: str, state_dir: Path | None = None) -> dict | None:
    """Load session state from SessionStart hook."""
    if state_dir is None:
        state_dir = get_state_dir()

    state_file = state_dir / f"session_{session_id}.json"
    if not state_file.exists():
        return None

    try:
        return json.loads(state_file.read_text())
    except json.JSONDecodeError as e:
        print(f"Warning: Malformed session state file: {e}", file=sys.stderr)
        return None


def delete_state_file(session_id: str, state_dir: Path | None = None) -> None:
    """Delete session state file after successful processing."""
    if state_dir is None:
        state_dir = get_state_dir()

    state_file = state_dir / f"session_{session_id}.json"
    try:
        if state_file.exists():
            state_file.unlink()
    except OSError as e:
        print(f"Warning: Failed to delete state file: {e}", file=sys.stderr)


def get_git_info(cwd: str) -> tuple[str | None, int]:
    """Get current HEAD commit and count of new commits."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit_hash = commit.stdout.strip() if commit.returncode == 0 else None
        return commit_hash, 0
    except subprocess.TimeoutExpired:
        print("Warning: Git command timed out", file=sys.stderr)
        return None, 0
    except FileNotFoundError:
        return None, 0


def ensure_sessions_dir(cwd: str) -> Path:
    """Ensure .claude/sessions/ directory exists."""
    sessions_dir = Path(cwd) / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


# ============================================================================
# MAIN HOOK HANDLER
# ============================================================================

def handle_session_end(
    input_data: dict,
    state_dir: Path | None = None,
    pending_dir: Path | None = None,
) -> dict:
    """Handle SessionEnd event - lightweight version.

    Only writes summary file and pending metadata.
    SQLite indexing and ChromaDB embedding deferred to MCP server.
    """
    session_id = input_data.get("session_id")
    if not session_id:
        return {"success": False, "reason": "No session_id in input data"}

    session_state = load_session_state(session_id, state_dir)
    if session_state is None:
        return {"success": False, "reason": f"No session state found for session {session_id}"}

    transcript_path = input_data.get("transcript_path")
    if not transcript_path or not Path(transcript_path).exists():
        return {"success": False, "reason": "Transcript not found"}

    cwd = input_data.get("cwd", session_state.get("cwd", "."))

    # Parse transcript
    transcript_data = parse_transcript(Path(transcript_path))

    # Skip empty sessions
    if transcript_data.user_message_count < 2:
        delete_state_file(session_id, state_dir)
        return {"success": True, "reason": "Session too short, skipping"}

    # Get git info
    commit_end, commits_made = get_git_info(cwd)
    end_time = datetime.now(timezone.utc)

    # Generate summary
    summary = generate_summary(
        transcript_data=transcript_data,
        session_state=session_state,
        commit_end=commit_end,
        commits_made=commits_made,
        end_time=end_time,
    )

    # Write summary file
    title = generate_title(transcript_data, session_state.get("branch"))
    filename = get_summary_filename(session_state, title)

    sessions_dir = ensure_sessions_dir(cwd)
    summary_path = sessions_dir / filename

    try:
        summary_path.write_text(summary)
    except OSError as e:
        print(f"Warning: Failed to write summary: {e}", file=sys.stderr)
        return {"success": False, "reason": f"Failed to write summary: {e}"}

    # Build metadata for deferred indexing
    metadata = {
        "filename": filename,
        "date": session_state.get("start_time"),
        "project": Path(cwd).name,
        "branch": session_state.get("branch"),
        "duration_minutes": calculate_duration_minutes(
            session_state.get("start_time", end_time.isoformat()),
            end_time,
        ),
        "commits_made": commits_made,
        "files_touched": len(transcript_data.files_touched),
        "commands_run": len(transcript_data.commands_run),
        "title": title,
        "summary_path": str(summary_path),
    }

    embedding_data = {
        "content": summary,
        "metadata": {
            "project": Path(cwd).name,
            "branch": session_state.get("branch"),
            "date": session_state.get("start_time"),
        },
    }

    # Write pending file for deferred indexing
    pending_written, pending_error = write_pending_metadata(
        filename=filename,
        metadata=metadata,
        embedding_data=embedding_data,
        pending_dir=pending_dir,
    )

    if not pending_written:
        print(f"Warning: Failed to write pending metadata: {pending_error}", file=sys.stderr)

    # Clean up state file
    delete_state_file(session_id, state_dir)

    return {
        "success": True,
        "summary_path": str(summary_path),
        "pending_written": pending_written,
    }


def main():
    """Entry point for hook."""
    try:
        input_data = json.load(sys.stdin)
        result = handle_session_end(input_data)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(f"SessionEnd hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Step 2.4: Run test to verify it passes

Run: `cd packages/plugins/session-log && uv run pytest tests/test_session_end_standalone.py::test_parse_transcript_extracts_files -v`
Expected: PASS

### Step 2.5: Write test to verify no heavy imports

Add to `tests/test_session_end_standalone.py`:

```python
def test_no_heavy_imports():
    """Standalone script has no chromadb or session_log imports."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    script_path = scripts_dir / "session_end_standalone.py"

    content = script_path.read_text()

    assert "import chromadb" not in content
    assert "from chromadb" not in content
    assert "from session_log" not in content
    assert "import session_log" not in content
```

### Step 2.6: Run test to verify it passes

Run: `cd packages/plugins/session-log && uv run pytest tests/test_session_end_standalone.py::test_no_heavy_imports -v`
Expected: PASS

### Step 2.7: Write integration test for handle_session_end

Add to `tests/test_session_end_standalone.py`:

```python
def test_handle_session_end_writes_summary_and_pending(tmp_path):
    """handle_session_end writes summary file and pending metadata."""
    import sys
    scripts_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))

    from session_end_standalone import handle_session_end

    # Create state dir and file
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "session_test-123.json"
    state_file.write_text(json.dumps({
        "session_id": "test-123",
        "start_time": "2026-01-12T10:00:00+00:00",
        "cwd": str(tmp_path / "project"),
        "branch": "feat/test",
    }))

    # Create project dir
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create transcript
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        json.dumps({"type": "user", "message": {"content": "hello"}}) + "\n" +
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}) + "\n" +
        json.dumps({"type": "user", "message": {"content": "bye"}}) + "\n" +
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "goodbye"}]}}) + "\n"
    )

    pending_dir = tmp_path / "pending"
    pending_dir.mkdir()

    result = handle_session_end(
        input_data={
            "session_id": "test-123",
            "transcript_path": str(transcript),
            "cwd": str(project_dir),
        },
        state_dir=state_dir,
        pending_dir=pending_dir,
    )

    assert result["success"] is True
    assert "summary_path" in result
    assert result["pending_written"] is True

    # Verify summary file exists
    summary_path = Path(result["summary_path"])
    assert summary_path.exists()
    assert "# Session:" in summary_path.read_text()

    # Verify pending file exists
    pending_files = list(pending_dir.glob("*.json"))
    assert len(pending_files) == 1

    # Verify state file deleted
    assert not state_file.exists()
```

### Step 2.8: Run all standalone tests

Run: `cd packages/plugins/session-log && uv run pytest tests/test_session_end_standalone.py -v`
Expected: PASS (3 tests)

### Step 2.9: Commit Task 2

```bash
cd packages/plugins/session-log
git add scripts/session_end_standalone.py tests/test_session_end_standalone.py
git commit -m "feat(session-log): add standalone session_end hook (stdlib-only)"
```

---

## Task 3: Integrate Pending Processing into MCP Server

**Files:**
- Modify: `packages/plugins/session-log/tool_handlers.py`
- Create: `packages/plugins/session-log/tests/test_tool_handlers_pending.py`

### Step 3.1: Write test for pending processing on tool call

```python
# tests/test_tool_handlers_pending.py
"""Tests for pending processing integration in tool handlers."""

import json
from pathlib import Path


def test_handle_tool_processes_pending_on_first_call(tmp_path, monkeypatch):
    """handle_tool processes pending sessions on first call."""
    from tool_handlers import handle_tool, _reset_pending_flag

    # Reset the global flag for testing
    _reset_pending_flag()

    # Create pending directory with a file
    pending_dir = tmp_path / "pending"
    pending_dir.mkdir()

    pending_file = pending_dir / "test-session.md.json"
    pending_file.write_text(json.dumps({
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
    }))

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
```

### Step 3.2: Run test to verify it fails

Run: `cd packages/plugins/session-log && uv run pytest tests/test_tool_handlers_pending.py -v`
Expected: FAIL with "cannot import name '_reset_pending_flag'"

### Step 3.3: Modify tool_handlers.py to process pending

```python
# Add at top of tool_handlers.py after existing imports:
from session_log.pending import process_pending_sessions

# Add global flag after imports:
_pending_processed = False


def _reset_pending_flag():
    """Reset pending processed flag (for testing only)."""
    global _pending_processed
    _pending_processed = False


# Modify handle_tool function:
def handle_tool(name: str, arguments: dict) -> list[ToolResult]:
    """Route tool call to appropriate handler."""
    global _pending_processed

    # Process any pending sessions on first tool call
    if not _pending_processed:
        try:
            stats = process_pending_sessions()
            if stats.get("processed", 0) > 0:
                import sys
                print(f"Processed {stats['processed']} pending sessions "
                      f"(indexed: {stats.get('indexed', 0)}, "
                      f"embedded: {stats.get('embedded', 0)})", file=sys.stderr)
        except Exception as e:
            import sys
            print(f"Warning: Failed to process pending sessions: {e}", file=sys.stderr)
        _pending_processed = True

    if name == "list_sessions":
        return handle_list_sessions(arguments)
    elif name == "get_session":
        return handle_get_session(arguments)
    elif name == "search_sessions":
        return handle_search_sessions(arguments)
    return [ToolResult(type="text", text=f"Unknown tool: {name}")]
```

### Step 3.4: Run test to verify it passes

Run: `cd packages/plugins/session-log && uv run pytest tests/test_tool_handlers_pending.py -v`
Expected: PASS

### Step 3.5: Commit Task 3

```bash
cd packages/plugins/session-log
git add tool_handlers.py tests/test_tool_handlers_pending.py
git commit -m "feat(session-log): process pending sessions on first MCP tool call"
```

---

## Task 4: Update hooks.json to Use Standalone Script

**Files:**
- Modify: `packages/plugins/session-log/hooks/hooks.json`

### Step 4.1: Update hooks.json

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_start.py"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_end_standalone.py"
          }
        ]
      }
    ]
  }
}
```

### Step 4.2: Commit Task 4

```bash
cd packages/plugins/session-log
git add hooks/hooks.json
git commit -m "feat(session-log): switch to stdlib-only hooks (no uv run)"
```

---

## Task 5: Integration Testing and Verification

### Step 5.1: Run all tests

Run: `cd packages/plugins/session-log && uv run pytest tests/ -v`
Expected: All tests PASS

### Step 5.2: Reinstall plugin

Run: `claude plugin marketplace update tool-dev && claude plugin install session-log@tool-dev`
Expected: Successfully installed

### Step 5.3: Test hook execution time

Run: `time echo '{"session_id": "test", "cwd": "/tmp"}' | python3 ~/.claude/plugins/cache/tool-dev/session-log/*/scripts/session_start.py`
Expected: Completes in <100ms (no venv creation)

### Step 5.4: Commit all changes

```bash
cd packages/plugins/session-log
git add -A
git commit -m "feat(session-log): complete lightweight hooks refactor

- Add pending.py module for deferred indexing
- Create session_end_standalone.py with inlined stdlib-only code
- Integrate pending processing into MCP server tool handlers
- Switch hooks.json to use python3 directly (no uv run)

Hooks now execute in <100ms. SQLite indexing and ChromaDB embedding
are deferred to the MCP server's first tool call."
```

---

## Verification Checklist

- [ ] `uv run pytest tests/` passes all tests
- [ ] `session_end_standalone.py` contains no chromadb/session_log imports
- [ ] Hook execution completes in <100ms
- [ ] MCP server processes pending files on first tool call
- [ ] End-to-end: session end → pending file → MCP query → session appears

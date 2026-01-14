# Layered Capture Design: Audit Fixes

**Target:** `docs/designs/layered-capture-design.md`
**Audit Date:** 2026-01-06
**Status:** P1 + P2 fixes complete (P3 deferred)

---

## P1 — Critical Path (Block Implementation)

### 1.1 Define Missing Serialization Methods

**Location:** Data Model section (lines 92-389)

**Problem:** `from_json()` and `to_dict()` are called but never defined.

**Fix:** Add to `LayerOneContext` dataclass:

```python
def to_dict(self) -> dict:
    return {
        "session_id": self.session_id,
        "project_path": self.project_path,
        "started_at": self.started_at.isoformat(),
        "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        "git_start": {
            "branch": self.git_start.branch,
            "commit": self.git_start.commit,
            "uncommitted_files": self.git_start.uncommitted_files,
        },
        "git_end": {
            "branch": self.git_end.branch,
            "commit": self.git_end.commit,
            "uncommitted_files": self.git_end.uncommitted_files,
        } if self.git_end else None,
        "tasks": [
            {
                "content": t.content,
                "status": t.status.value,
                "active_form": t.active_form,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in self.tasks
        ],
        "files_modified": list(self.files_modified),
        "files_read": list(self.files_read),
        "last_checkpoint": self.last_checkpoint.isoformat(),
    }

@classmethod
def from_json(cls, json_str: str) -> "LayerOneContext":
    data = json.loads(json_str)
    return cls(
        session_id=data["session_id"],
        project_path=data["project_path"],
        started_at=datetime.fromisoformat(data["started_at"]),
        ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
        git_start=GitState(
            branch=data["git_start"]["branch"],
            commit=data["git_start"]["commit"],
            uncommitted_files=data["git_start"].get("uncommitted_files", []),
        ),
        git_end=GitState(
            branch=data["git_end"]["branch"],
            commit=data["git_end"]["commit"],
            uncommitted_files=data["git_end"].get("uncommitted_files", []),
        ) if data.get("git_end") else None,
        tasks=[
            Task(
                content=t["content"],
                status=TaskStatus(t["status"]),
                active_form=t["active_form"],
                created_at=datetime.fromisoformat(t["created_at"]),
                completed_at=datetime.fromisoformat(t["completed_at"]) if t.get("completed_at") else None,
            )
            for t in data.get("tasks", [])
        ],
        files_modified=set(data.get("files_modified", [])),
        files_read=set(data.get("files_read", [])),
        last_checkpoint=datetime.fromisoformat(data["last_checkpoint"]),
    )
```

**Done when:** Both methods exist and handle all fields including nested objects.

---

### 1.2 Define Missing Persistence Functions

**Location:** SessionStart Hook section (lines 395-499)

**Problem:** `save_live_context()`, `save_handoff()`, `cleanup_live_context()`, `load_previous_handoff()` are called but never defined.

**Fix:** Add implementations after the hook code:

```python
CONTEXT_DIR = Path.home() / ".claude" / "layered-context"
HANDOFF_DIR = CONTEXT_DIR / "handoffs"

def get_project_hash(project_path: str) -> str:
    """Generate stable hash for project identity."""
    return hashlib.sha256(project_path.encode()).hexdigest()[:12]

def save_live_context(context: LayerOneContext) -> None:
    """Save active session context."""
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    path = CONTEXT_DIR / f"live_{context.session_id}.json"
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(context.to_dict(), indent=2))
    tmp_path.replace(path)

def cleanup_live_context(session_id: str) -> None:
    """Remove live context file after session ends."""
    path = CONTEXT_DIR / f"live_{session_id}.json"
    path.unlink(missing_ok=True)

def save_handoff(context: LayerOneContext) -> None:
    """Save completed session as handoff for future resumption."""
    project_hash = get_project_hash(context.project_path)
    branch = context.git_end.branch if context.git_end else context.git_start.branch or "unknown"

    handoff_dir = HANDOFF_DIR / f"{project_hash}_{branch}"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    # Save timestamped handoff
    timestamp = context.ended_at or context.last_checkpoint
    filename = timestamp.strftime("%Y-%m-%d_%H-%M") + ".json"
    path = handoff_dir / filename
    path.write_text(json.dumps(context.to_dict(), indent=2))

    # Update current.json pointer
    current_path = handoff_dir / "current.json"
    current_path.write_text(json.dumps(context.to_dict(), indent=2))

def load_previous_handoff(project_path: str, branch: str | None) -> LayerOneContext | None:
    """Load most recent handoff for this project/branch."""
    project_hash = get_project_hash(project_path)

    # Try branch-specific first
    if branch:
        handoff_dir = HANDOFF_DIR / f"{project_hash}_{branch}"
        current_path = handoff_dir / "current.json"
        if current_path.exists():
            try:
                return LayerOneContext.from_json(current_path.read_text())
            except Exception:
                pass

    # Fall back to any branch for this project
    for handoff_dir in HANDOFF_DIR.glob(f"{project_hash}_*"):
        current_path = handoff_dir / "current.json"
        if current_path.exists():
            try:
                return LayerOneContext.from_json(current_path.read_text())
            except Exception:
                continue

    return None
```

**Done when:** All four functions are defined with implementations.

---

### 1.3 Fix `is_success()` to be Tool-Aware

**Location:** PostToolUse Hook section (lines 592-598)

**Problem:** Current logic assumes all tools return `{"error": ...}` or `{"success": ...}`. Actual tool results vary by tool type.

**Current code:**
```python
def is_success(result: dict) -> bool:
    if "error" in result:
        return False
    if "success" in result:
        return result["success"]
    return True  # Assume success if no error
```

**Replace with:**
```python
def is_success(tool_name: str, result: Any) -> bool:
    """Check if tool execution succeeded. Tool-aware implementation."""
    if result is None:
        return False

    # Handle string results (Write/Edit return content or error message)
    if isinstance(result, str):
        error_indicators = ["error", "failed", "permission denied", "not found"]
        return not any(ind in result.lower() for ind in error_indicators)

    # Handle dict results
    if isinstance(result, dict):
        # Bash returns exit_code
        if tool_name == "Bash":
            return result.get("exit_code", 1) == 0

        # Explicit error field
        if "error" in result:
            return False

        # Explicit success field
        if "success" in result:
            return result["success"]

    # Default: assume success if we got here
    return True
```

**Also update call sites** (lines 556, 576) to pass `tool_name`:
```python
if file_path and is_success(tool_name, tool_result):
```

**Done when:** `is_success()` takes `tool_name` parameter and handles Bash exit_code + string error detection.

---

### 1.4 Revise Layer 2 Adoption Expectations

**Location:** Success Metrics section (lines 1127-1137)

**Problem:** Target of 60% → 80% is unrealistic. Claude is request-response, not self-directed.

**Change:**
```markdown
| **L2 adoption** | 60% → 80% | % sessions where Claude updates context.md |
```

**To:**
```markdown
| **L2 adoption** | 10% → 30% | % sessions where Claude updates context.md (without hook-assisted reminders) |
```

**Also add note after the table:**
```markdown
**Note:** Layer 2 adoption depends on Claude proactively following CLAUDE.md instructions. Without hook-assisted reminders, expect low adoption. Layer 1 provides the reliable floor; Layer 2 is enrichment.
```

**Done when:** Metric reflects realistic expectations and note explains why.

---

## P2 — Before v1

### 2.1 Remove "Before Ending" Trigger

**Location:** Layer 2 Protocol section (lines 627-632)

**Problem:** No mechanism exists to detect session end. Sessions end abruptly.

**Change the "When to Update" list from:**
```markdown
1. **Completing a major task** — After marking a TodoWrite item complete
2. **Making a decision** — When choosing between alternatives
3. **Discovering a gotcha** — Constraints, surprises, things to remember
4. **Before ending** — If you sense the session is wrapping up
```

**To:**
```markdown
1. **Completing a major task** — After marking a TodoWrite item complete
2. **Making a decision** — When choosing between alternatives
3. **Discovering a gotcha** — Constraints, surprises, things to remember
```

**Done when:** "Before ending" trigger is removed from protocol.

---

### 2.2 Cut Layer 3 from v1 Scope

**Location:** Layer 3: Deep Resume section (lines 690-746)

**Action:** Add a notice at the top of the Layer 3 section:

```markdown
> **v1 Scope:** Layer 3 is deferred. Implement after Layer 1 + Layer 2 are proven in production. The episodic-memory plugin dependency and unproven need make this a v2 feature.
```

**Also update Migration Path table** (lines 1110-1124):
- Change Phase 7 (`/deep-resume` command) to show "v2" instead of "1" day
- Add note: "Phases 1-6 constitute v1. Phase 7+ are v2."

**Done when:** Layer 3 is clearly marked as out of v1 scope.

---

### 2.3 Remove File Locking (Atomic Writes Sufficient)

**Location:** File Locking section (lines 983-1079)

**Action:** Replace the `file_lock` context manager and `save_live_context_safe` with a note:

```markdown
## File Safety

Atomic writes (`.tmp` + rename) prevent corruption. File locking is not needed for v1.

```python
def save_atomic(path: Path, content: str) -> None:
    """Write atomically to prevent corruption."""
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(content)
    tmp_path.replace(path)  # Atomic on POSIX
```

**Note:** If concurrent session corruption is reported in production, revisit `fcntl` locking.
```

**Done when:** File locking section is simplified to atomic writes only.

---

### 2.4 Simplify Checkpoint System

**Location:** File Locking section (lines 1030-1078)

**Action:** Keep `save_checkpoint()` and `load_checkpoint()` but remove `cleanup_checkpoint()` and `handle_orphan()` complexity. Simplify to:

```python
def save_checkpoint(context: LayerOneContext) -> None:
    """Save periodic checkpoint for crash recovery."""
    CHECKPOINT_DIR = CONTEXT_DIR / "checkpoints"
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    path = CHECKPOINT_DIR / f"checkpoint_{context.session_id}.json"
    save_atomic(path, json.dumps(context.to_dict(), indent=2))

def load_checkpoint(session_id: str) -> LayerOneContext | None:
    """Load checkpoint if it exists."""
    path = CONTEXT_DIR / "checkpoints" / f"checkpoint_{session_id}.json"
    if not path.exists():
        return None
    try:
        return LayerOneContext.from_json(path.read_text())
    except Exception:
        return None
```

**Done when:** Checkpoint system is 20 lines, not 50.

---

## P3 — Hardening

### 3.1 Add Schema Versioning

**Location:** Data Model section, in `to_dict()` method

**Add to output:**
```python
def to_dict(self) -> dict:
    return {
        "schema_version": 1,  # Add this line
        "session_id": self.session_id,
        ...
    }
```

**Add to `from_json()`:**
```python
@classmethod
def from_json(cls, json_str: str) -> "LayerOneContext":
    data = json.loads(json_str)
    version = data.get("schema_version", 1)
    if version > 1:
        raise ValueError(f"Unsupported schema version: {version}")
    ...
```

**Done when:** All JSON includes `schema_version` and loading validates it.

---

### 3.2 Add Error Handling to Hook Entry Points

**Location:** SessionStart Hook `main()` (lines 418-468) and PostToolUse Hook `main()` (lines 522-589)

**Wrap both with:**
```python
def main():
    try:
        # existing code
    except Exception as e:
        import sys
        print(f"Hook error (non-blocking): {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on hook failure
```

**Done when:** Both hooks have top-level try/except that logs but doesn't block.

---

### 3.3 Add Logging for Silent Failures

**Location:** `find_orphaned_contexts()` (lines 471-482)

**Change:**
```python
except Exception:
    # Corrupted file - delete it
    f.unlink()
```

**To:**
```python
except Exception as e:
    # Corrupted file - log and delete
    print(f"Removing corrupted context file {f}: {e}", file=sys.stderr)
    f.unlink()
```

**Done when:** Corrupted file deletion is logged to stderr.

---

## Verification Checklist

After all fixes, verify:

- [x] `LayerOneContext.to_dict()` exists and handles all fields
- [x] `LayerOneContext.from_json()` exists and reconstructs all fields
- [x] `save_live_context()`, `save_handoff()`, `cleanup_live_context()`, `load_previous_handoff()` all defined
- [x] `is_success()` takes `tool_name` and handles Bash exit codes
- [x] Layer 2 adoption metric shows 10-30%, not 60-80%
- [x] "Before ending" trigger removed from Layer 2 protocol
- [x] Layer 3 marked as v2/deferred
- [x] File locking section simplified to atomic writes
- [ ] `schema_version` in JSON output (P3 - deferred)
- [ ] Hooks have top-level error handling (P3 - deferred)

---

## Re-audit Trigger

Re-run three-lens audit after completing P1 + P2 items to verify no new issues introduced.

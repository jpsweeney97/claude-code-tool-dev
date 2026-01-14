# Layered Capture: Audit Fixes

Amendments to `layered-capture-design.md` addressing 5 HIGH-priority findings from audit cycle 1.

**Date:** 2026-01-06
**Status:** Integrated (2026-01-06)
**Addresses:** F5, F7, F8, F9, F15

---

## Summary

| Finding | Issue | Fix |
|---------|-------|-----|
| F5/F7 | `format_layer_two_only()` undefined | Add L2-only injection handler |
| F8 | `fcntl.flock()` POSIX-only | Graceful fallback on Windows |
| F9 | Git failures return empty strings | Use `Optional[str]`, handle None |
| F15 | Checkpoint saved but never loaded | Add `load_checkpoint()` for crash recovery |

---

## F5/F7: L2-Only Handler

**Problem:** SessionStart crashes when only `.claude/context.md` exists (no L1 handoff).

**Solution:** Add `format_layer_two_only()` to handle this edge case:

```python
def format_layer_two_only(l2: LayerTwoContext, current_git: GitState) -> str:
    """
    Format injection when only Layer 2 exists (no L1 handoff).

    This is unusual — happens when:
    - User manually created .claude/context.md before first session
    - L1 handoff was deleted but L2 remains
    """
    sections = []

    # Header with warning
    header = f"[Resuming: {l2.goal or 'Previous context'}]"
    if current_git.branch:
        header += f"\nBranch: {current_git.branch}"
    sections.append(header)

    # Warning about missing L1
    sections.append("⚠️ Task progress unavailable (no session history found)")

    # L2 content: decisions, learnings, blocking
    if l2.decisions:
        lines = ["Decisions:"]
        for d in l2.decisions[:3]:
            line = f"  • {d.choice}"
            if d.reasoning:
                line += f": {d.reasoning[:55]}"
            lines.append(line)
        sections.append("\n".join(lines))

    if l2.blocking:
        sections.append("Blocking:\n  • " + "\n  • ".join(b[:50] for b in l2.blocking[:2]))

    if l2.learnings:
        lines = ["Learnings:"]
        for learn in l2.learnings[:2]:
            lines.append(f"  • {learn.content[:50]}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
```

**Integration:** Update SessionStart hook line 441-442:

```python
else:
    # Only Layer 2 exists (unusual but handle it)
    injection = format_layer_two_only(previous_l2, current_git)
```

---

## F8: Cross-Platform File Locking

**Problem:** `fcntl.flock()` raises `ImportError` on Windows.

**Solution:** Try fcntl, fallback to no-op. Atomic writes still prevent corruption.

```python
from contextlib import contextmanager
import sys

@contextmanager
def file_lock(path: Path):
    """
    Acquire exclusive lock on file.

    On POSIX (macOS, Linux): Uses fcntl for real locking.
    On Windows: No-op (atomic writes still protect against corruption).
    """
    lock_path = path.with_suffix(".lock")
    lock_file = open(lock_path, "w")

    try:
        # Try fcntl-based locking (POSIX only)
        try:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            has_lock = True
        except (ImportError, OSError):
            # Windows or other platform — proceed without lock
            # Atomic writes still prevent corruption
            has_lock = False

        yield

    finally:
        if has_lock:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
```

**Rationale:** Atomic writes (`.tmp` + `rename`) prevent corruption. Locking primarily prevents race conditions in concurrent sessions — rare enough that skipping on Windows is acceptable.

---

## F9: Git Error Handling

**Problem:** Git command failures silently return empty strings, creating corrupt `GitState`.

**Solution:** Use `Optional[str]` for fields, return `None` on failure:

```python
@dataclass
class GitState:
    """Git state snapshot. Fields are None if git unavailable or not a repo."""
    branch: str | None
    commit: str | None
    uncommitted_files: list[str] = field(default_factory=list)

    @classmethod
    def capture(cls) -> "GitState":
        """Capture current git state. Returns None fields if git fails."""
        import subprocess

        def run(cmd: list[str]) -> str | None:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd="."
                )
                if result.returncode != 0:
                    return None
                return result.stdout.strip() or None
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                return None

        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        commit_full = run(["git", "rev-parse", "HEAD"])
        commit = commit_full[:12] if commit_full else None

        # Only get status if we confirmed it's a git repo
        uncommitted = []
        if branch is not None:
            status = run(["git", "status", "--porcelain"])
            if status:
                uncommitted = [line[3:] for line in status.split("\n") if line]

        return cls(branch=branch, commit=commit, uncommitted_files=uncommitted)

    @property
    def is_available(self) -> bool:
        """True if git info was captured successfully."""
        return self.branch is not None
```

**Caller updates:** Minimal — `format_injection` already checks `if ctx.git_state.commit`.

---

## F15: Checkpoint Loading for Crash Recovery

**Problem:** `save_checkpoint()` is called but `load_checkpoint()` doesn't exist. Crash recovery incomplete.

**Solution:** Add checkpoint loading and integrate into orphan recovery:

```python
CHECKPOINT_DIR = CONTEXT_DIR / "checkpoints"

def save_checkpoint(context: LayerOneContext) -> None:
    """Save periodic checkpoint for crash recovery."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    path = CHECKPOINT_DIR / f"checkpoint_{context.session_id}.json"
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(context.to_dict(), default=str))
    tmp_path.replace(path)


def load_checkpoint(session_id: str) -> LayerOneContext | None:
    """Load checkpoint if it exists."""
    path = CHECKPOINT_DIR / f"checkpoint_{session_id}.json"
    if not path.exists():
        return None
    try:
        return LayerOneContext.from_json(path.read_text())
    except Exception:
        return None


def cleanup_checkpoint(session_id: str) -> None:
    """Remove checkpoint after successful handoff."""
    path = CHECKPOINT_DIR / f"checkpoint_{session_id}.json"
    path.unlink(missing_ok=True)


def handle_orphan(orphan: LayerOneContext) -> None:
    """
    Recover context from crashed session.

    Strategy: If orphan has no ended_at, try to load checkpoint
    which may have more recent data than the live context file.
    """
    if orphan.ended_at is None:
        # Crash before clean shutdown — try checkpoint
        checkpoint = load_checkpoint(orphan.session_id)
        if checkpoint and checkpoint.last_checkpoint > orphan.last_checkpoint:
            # Checkpoint is newer — use it
            orphan = checkpoint

        # Mark as ended at last known good state
        orphan.ended_at = orphan.last_checkpoint
        orphan.git_end = orphan.git_start  # Best we can do

    save_handoff(orphan)
    cleanup_live_context(orphan.session_id)
    cleanup_checkpoint(orphan.session_id)
```

**Storage layout update:**

```
~/.claude/
├── layered-context/
│   ├── live_{session_id}.json
│   ├── checkpoints/                    # NEW
│   │   └── checkpoint_{session_id}.json
│   └── handoffs/
│       └── {project_hash}_{branch}/
│           └── ...
```

---

## Implementation Notes

- **F5/F7:** Single function addition + one-line integration
- **F8:** Replace existing `file_lock` function
- **F9:** Modify `GitState` dataclass and `capture()` method
- **F15:** Add checkpoint directory + 3 functions + update `handle_orphan()`

**No architectural changes required.** All fixes are additive or replacement-in-place.

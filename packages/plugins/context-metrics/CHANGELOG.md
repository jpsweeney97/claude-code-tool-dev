# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Context window auto-detection from JSONL `message.model` field — prefix-matches `claude-opus-4-6` and `claude-sonnet-4-6` to 1M window.
- Strengthened test coverage for validation paths and edge cases.

### Fixed

- Sidecar stderr now redirected to `~/.claude/.context-metrics-sidecar.log` instead of inheriting parent stderr.
- Delivered semantics — hook response state only advances after successful client delivery; disconnects preserve trigger state for re-evaluation.
- Signal handler deadlock in sidecar shutdown — `server.shutdown()` now runs on a daemon thread to avoid blocking `serve_forever()`.
- PR review fixes: removed `sys.path` manipulation, added type validation for usage fields, corrected message counting logic.
- Missing `/sessions/compaction` endpoint and URL-encoded query parameters for session registration.
- Inaccurate comments and stale amendment references in docstrings.

## [0.1.0] - 2026-02-28

### Added

- Plugin scaffold with JSONL test fixtures.
- Config reader (`config.py`) with `~/.claude/context-metrics.local.md` YAML frontmatter support and context window auto-detection from observed occupancy.
- JSONL tail-reader (`jsonl_reader.py`) with 4-condition positive-only selector, backward EOF scan, and message deduplication by ID.
- Session registry (`session_registry.py`) with lease-based expiry (600s timeout) and thread-safe concurrent access.
- Trigger engine (`trigger_engine.py`) with 5 trigger types (compaction, token delta, percentage delta, boundary crossing, heartbeat) and OR-based evaluation.
- Summary line formatter (`formatter.py`) with 3 output formats: full, minimal, and compaction.
- Sidecar HTTP server (`server.py`) on `127.0.0.1:7432` — shared across all concurrent sessions.
- Hook scripts: `start_sidecar.py` (SessionStart), `stop_sidecar.py` (SessionEnd), `context_summary.py` (UserPromptSubmit + SessionStart compact).
- `hooks.json` wiring for all hook events.
- `/context-dashboard` skill for on-demand detailed metrics.
- Integration tests for end-to-end hook and server behavior.

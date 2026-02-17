# Context Injection — D5 Session 29 Findings

**Source:** Two codex-dialogue consultations (evaluative, budget 1) run as P0-1 tests during D5 Session 29.
**Date:** 2026-02-17
**Branch:** `feature/context-injection-agent-integration` at `3010574`

## Finding 1: Entity Extraction Edge Cases

**Module:** `packages/context-injection/context_injection/entities.py`
**Consultation topic:** Edge case handling in path parsing regexes

### High Priority

**Port/config patterns produce false-positive `file_loc` matches**
- `192.168.1.1:443` and `server.port.value:5432` both match `_FILE_LOC_COLON_RE`.
- The regex requires only `name.ext:digits`, which these satisfy.
- These patterns appear in natural language discussion of server configurations.
- Downstream path resolver marks them `not_tracked`, but they consume entity slots and could trigger unnecessary scout operations.
- **Suggested fix:** Require at least one `/` or known extension before the `:digits` anchor, or add a negative lookahead for IP-like patterns.

### Medium Priority

**Inconsistent traversal filtering between extractors**
- `_extract_file_paths` filters `..` segments, but `_FILE_LOC_COLON_RE` matches `../../deep/file.py:3`.
- Downstream `path_decisions` catches these (deny_reason: "directory traversal not allowed"), providing defense-in-depth.
- The inconsistency means traversal paths consume entity IDs and processing unnecessarily.
- **Suggested fix:** Add the same `".." in parts` segment check to `_extract_file_locs`.

**Hidden directory handling partially broken**
- `./.hidden/file.py` extracts as `hidden/file.py` (drops both `./` and the leading dot from `.hidden`).
- `src/.hidden/file.py` extracts correctly.
- `.hidden/file.py` extracts as `hidden/file.py` (drops leading dot).
- Root cause: `[\w]` after `\.{1,2}/` in `_FILE_PATH_RE` requires a word character, so leading dots are not captured.
- **Suggested fix:** Use `[\w.]` instead of `[\w]` after `\.{1,2}/` to support dot-prefixed segments.

### Low Priority

**Paths with spaces produce split partial matches**
- `./my dir/file.py` produces two matches: `./my` and `dir/file.py`.
- Inherent to `\w`-based character classes which exclude spaces.
- Low severity: LLM-generated claims rarely contain spaced paths. Partial matches fail downstream path resolution.

**Bare extensionless filenames produce no entity**
- `Makefile`, `Dockerfile`, `README`, `LICENSE` all produce zero matches.
- By design: `_FILE_NAME_RE` requires a known extension, `_FILE_PATH_RE` requires a `/` separator.
- Coverage gap, not a bug. Adding a well-known-names list would be a new feature.

**Dotfiles produce no entity**
- `.env`, `.gitignore` produce zero matches.
- These are commonly referenced in developer discussions, so this may be a meaningful coverage gap.

**Absolute paths lose leading slash**
- `/etc/config.yaml` matches as `etc/config.yaml`.
- Arguably correct: entity extraction operates on repo-relative paths, and absolute system paths are out of scope.

**Empty path components accepted**
- `src//file.py` and `src///file.py` both match.
- Downstream normalization collapses these. Practical impact is cosmetic.

## Finding 2: Checkpoint Serialization Security Gaps

**Module:** `packages/context-injection/context_injection/checkpoint.py`
**Consultation topic:** Checkpoint serialization format correctness and security

### High Priority

**Restore path forgery after server restart**
- When `has_real_state == False` (server restarted), the restore path at line 199 accepts any checkpoint that passes structural integrity checks.
- An adversarial agent can craft a self-consistent checkpoint: envelope `checkpoint_id = X`, payload `last_checkpoint_id = X`, payload `conversation_id = target`, correct `size` — all 4 guards pass.
- Impact: poisoned `evidence_history` could manipulate dedupe/budget, fake `entries` could skew `compute_action`, manufactured `claim_registry` could alter ledger validation.
- **Threat model note:** The agent is Claude Code itself, so the practical threat is defense-in-depth rather than active exploitation.
- **Suggested fix:** HMAC-sign checkpoints. Infrastructure already exists (`generate_token`/`verify_token` in `state.py`). Estimated ~4 lines in serialize/deserialize.

### Medium Priority

**Inbound restore path does not enforce MAX_CHECKPOINT_PAYLOAD_BYTES**
- `deserialize_checkpoint()` at line 101 does not check payload size against the 16KB cap.
- The cap is only enforced during serialization (line 81).
- An oversized checkpoint would be accepted on restore, potentially forcing heavy parse and memory allocation.
- **Suggested fix:** Add `len(payload.encode("utf-8")) > MAX_CHECKPOINT_PAYLOAD_BYTES` check in `deserialize_checkpoint`.

**Checkpoint replay allows state rollback**
- A valid old checkpoint for the same conversation can be replayed after server restart.
- Server has no in-memory state to distinguish current from old.
- Violates the checkpoint chain's forward-only intent.
- **Suggested fix:** Would be addressed by HMAC signing with a timestamp or sequence number in the signed data.

### Low Priority

**Outer checkpoint_string size is unbounded**
- Inner payload cap is 16KB, but outer `checkpoint_string` (JSON-escaped envelope) has no cap.
- Worst case with escape-dense payload: ~32KB. Real payloads (natural language) typically add 5-15% overhead.
- **Suggested fix:** Add `MAX_CHECKPOINT_STRING_BYTES` constant (e.g., 32KB) as a transport safety net.

**Compaction preserves evidence_history but trims entries**
- `compact_ledger` trims entries to most recent 8 but does not touch `evidence_history`.
- Evidence records reference turns by number; trimmed turns may cause stale dedupe blocking.
- Currently unreachable: `MAX_CONVERSATION_TURNS=15 < MAX_ENTRIES_BEFORE_COMPACT=16` (DD-2 invariant).
- **Suggested fix:** Defer until DD-2 invariant is relaxed. If relaxed, window `evidence_history` to match retained entry range.

## Confirmed Correct

- Double-encoded JSON via Pydantic handles escaping correctly (unicode, control characters, backslashes, quotes).
- Size field integrity check is deterministic between serialize/deserialize paths.
- Ordered extraction pipeline (URL -> file_loc -> file_path -> file_name -> symbols -> errors) with span tracking prevents overlapping extractions.
- `_canon()` normalization and confidence assignment logic are correct.
- Traversal filtering in `_extract_file_paths` using `".." in parts` segment check (not substring) correctly allows filenames with consecutive dots.

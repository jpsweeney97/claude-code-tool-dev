# Dialogue First-Turn Fast Path Hardening

Design for hardening `_next_turn_sequence()` in `DialogueController` to distinguish "genuinely empty TurnStore" from "metadata unreadable or structurally suspect." Unifies the local-metadata consistency invariant across `_next_turn_sequence()`, `recover_startup()`, and `read()`.

## Origin

Ticket T-20260410-02. Source: PR #101 review finding — the first-turn fast path treats `TurnStore.get_all()` returning an empty mapping as definitive proof that no turns have completed, which is correct on the verified happy path but not robust against replay corruption, path mismatches, or partial metadata state.

## Package

All changes target `packages/plugins/codex-collaboration/`.

## Problem

`_next_turn_sequence()` at `dialogue.py:725-753` currently has two branches:

```python
local_turns = self._turn_store.get_all(handle.collaboration_id)
if not local_turns:
    return 1  # Fast path: no local metadata → first turn

thread_data = runtime.session.read_thread(handle.codex_thread_id)
# ... count completed turns from remote
return completed_count + 1
```

The fast path trusts `not local_turns` (empty dict) as proof of zero completed turns. But `TurnStore.get_all()` discards `ReplayDiagnostics` from `replay_jsonl()`. If the JSONL store has mid-file corruption, schema violations, or trailing truncation, `get_all()` returns `{}` even though records existed but were unreadable. The fast path cannot distinguish "genuinely empty" from "corrupt."

Additionally, when local metadata IS present, the current code doesn't validate that it's consistent with the remote completed turn count. `read()` at `dialogue.py:853` already enforces a strict left-join (missing metadata per completed turn = integrity failure), but `_next_turn_sequence()` doesn't check the same invariant. This means `reply()` can dispatch a turn on a handle that `read()` would later reject.

A parallel gap exists in `recover_startup()` at `dialogue.py:535`, which only checks `len(metadata) < completed_count` — this misses gaps (`{1, 3}` with `completed_count=3` has `len=2 < 3`, catches it; but `{1, 3}` with `completed_count=2` has `len=2 == 2`, passes the check despite `read()` expecting keys `{1, 2}`).

## Design

### 1. `TurnStore.get_all_checked()` — new method

```python
def get_all_checked(self, collaboration_id: str) -> tuple[dict[int, int], ReplayDiagnostics]:
```

Single-pass replay returning both filtered metadata and diagnostics. Calls `replay_jsonl` once, filters results by `collaboration_id`, returns `(filtered_dict, diagnostics)`.

**File-global diagnostics contract:** The turn store is a session-wide JSONL file, so diagnostics are file-global, not collaboration-scoped. A corrupt line from an unrelated collaboration will appear in the diagnostics. This is a deliberate fail-closed tradeoff — the caller cannot distinguish per-collaboration corruption from file-wide corruption, and should treat any diagnostic as reason to distrust an otherwise-empty result for this collaboration. This contract must be documented in the method's docstring.

Existing `get_all()`, `get()`, and `check_health()` are unchanged. No impact on other callers.

### 2. Shared local-metadata consistency check

New module-level function in `dialogue.py`:

```python
def _local_metadata_consistent(local_turns: dict[int, int], completed_count: int) -> bool:
    """True iff local turn metadata keys are exactly {1, 2, ..., completed_count}."""
    if completed_count == 0:
        return not local_turns
    return set(local_turns.keys()) == set(range(1, completed_count + 1))
```

Encodes the invariant that `read()` already enforces via its strict left-join. Used by both `_next_turn_sequence()` and `recover_startup()`.

### 3. `_next_turn_sequence()` — three-phase trust policy

**Phase 1 — local-only fast path:**

```
if local_turns == {} and diagnostics are empty:
    return 1
```

The only state where we bypass `read_thread()`. The file either doesn't exist or exists with zero diagnostics and no records for this collaboration.

**Phase 2 — remote read:**

All other states require `read_thread()`. On failure, raise with causal chain (`from exc`) and context about why we needed the remote:

- Empty local + diagnostics present: error includes diagnostic labels (e.g., `diagnostics=mid_file_corruption, trailing_truncation`), not just counts. Wording: `"session turn metadata file has replay diagnostics (diagnostics=...), and remote thread read failed."`
- Non-empty local: error includes local key state. Wording: `"cannot validate local turn metadata (sequences=...) against remote, remote thread read failed."`

Both include `collaboration_id` and are raised `from exc` to preserve causal chain.

**Phase 3 — remote/local consistency (uniform for all non-fast-path states):**

After successful `read_thread()`, compute `completed_count`. Then apply `_local_metadata_consistent(local_turns, completed_count)`.

If false:
1. Mark handle `"unknown"` via `self._lineage_store.update_status(collaboration_id, "unknown")` — consistent with `recover_startup()`'s quarantine pattern.
2. Raise deterministic integrity error before dispatch.

If true:
- `return completed_count + 1`

This covers all inconsistency shapes uniformly:

| Local state | Remote state | Consistent? | Example |
|---|---|---|---|
| `{}` | 0 completed | Yes | Clean first turn via remote |
| `{}` | 2 completed | No | Missing metadata (corrupt/lost) |
| `{1}` | 2 completed | No | Partial tail |
| `{2}` | 2 completed | No | Gap (missing turn 1) |
| `{1, 2, 3}` | 2 completed | No | Extra local |
| `{1, 3}` | 3 completed | No | Gap |
| `{1, 2}` | 2 completed | Yes | Normal subsequent turn |

### 4. Error message shapes

**Remote read failure (empty local + diagnostics):**
```
Turn sequence derivation failed: session turn metadata file has replay
diagnostics (diagnostics=mid_file_corruption, schema_violation), and
remote thread read failed.
Got: collaboration_id='collab-sess-1', <exc repr>
```
Raised `from exc`.

**Remote read failure (non-empty local):**
```
Turn sequence derivation failed: cannot validate local turn metadata
(sequences=[1, 2]) against remote, remote thread read failed.
Got: collaboration_id='collab-sess-1', <exc repr>
```
Raised `from exc`.

**Local/remote inconsistency (integrity failure):**
```
Turn sequence derivation failed: local turn metadata inconsistent with
remote. Expected sequences [1, 2, 3], got [1, 3].
Got: collaboration_id='collab-sess-1', completed_count=3,
actual_sequences=[1, 3]
```
No `from` — this is a local integrity failure, not a remote exception. Handle marked `"unknown"` before raise.

### 5. `recover_startup()` — same invariant

Replace `dialogue.py:535`:

```python
# Before:
if len(metadata) < completed_count:

# After:
if not _local_metadata_consistent(metadata, completed_count):
```

Same consequence (mark `"unknown"`, continue). Now catches gaps (`{1, 3}` with `completed_count=2`) and extra-local keys (`{1, 2, 3}` with `completed_count=2`) in addition to the original "fewer than expected" case.

## Test Plan

### `test_turn_store.py` — `get_all_checked()` unit tests

| Test | Setup | Assertion |
|------|-------|-----------|
| Clean store with matching records | Write 2 turns for collab-1 | Returns `{1: size, 2: size}` + empty diagnostics |
| Corrupt JSONL with matching records | Write valid turn, then corrupt line, then valid turn | Returns partial results + non-empty diagnostics |
| Empty store (no file exists) | Fresh tmp_path | Returns `{}` + empty diagnostics |

### `test_dialogue.py` — `_next_turn_sequence()` behavioral tests

| Test | Setup | Assertion |
|------|-------|-----------|
| **Existing** happy path | Empty store, clean | `turn_sequence == 1`, `read_thread_calls == 0` |
| **Existing** second reply | One completed turn | `turn_sequence == 2`, `read_thread_calls == 1` |
| Empty + diagnostics + remote 0 completed | Corrupt JSONL, remote returns 0 completed | `turn_sequence == 1` (consistent: `_local_metadata_consistent({}, 0) == True`) |
| Empty + diagnostics + remote 2 completed | Corrupt JSONL, remote returns 2 completed | Integrity error — `_local_metadata_consistent({}, 2) == False`. Handle marked `"unknown"` |
| Empty + diagnostics + remote fails | Corrupt JSONL, `read_thread` raises | Error contains "session turn metadata file has replay diagnostics" + diagnostic labels |
| Gap `{2}` + remote 2 completed | Pre-populate turn 2 only | Integrity error mentioning "Expected [1, 2], got [2]". Handle marked `"unknown"` |
| Partial tail `{1}` + remote 2 completed | Pre-populate turn 1 only | Integrity error mentioning "Expected [1, 2], got [1]". Handle marked `"unknown"` |
| Extra local `{1, 2, 3}` + remote 2 completed | Pre-populate turns 1-3 | Integrity error mentioning "Expected [1, 2], got [1, 2, 3]". Handle marked `"unknown"` |
| Non-empty + remote fails | Turn 1 metadata, `read_thread` raises | Error contains "cannot validate local turn metadata" + `sequences=[1]` |

### `test_dialogue.py` — `recover_startup()` consistency

| Test | Setup | Assertion |
|------|-------|-----------|
| Gapped metadata in recovery | Handle with `{1, 3}` metadata, remote 3 completed | Handle marked `"unknown"` |

## Files Touched

| File | Changes |
|------|---------|
| `server/turn_store.py` | Add `get_all_checked()` (~12 lines with docstring) |
| `server/dialogue.py` | Add `_local_metadata_consistent()` (~5 lines); rewrite `_next_turn_sequence()` (~40 lines); update `recover_startup()` line 535 (~1 line) |
| `tests/test_dialogue.py` | ~9 new tests |
| `tests/test_turn_store.py` | ~3 new tests |

## Unchanged

- `get_all()`, `get()`, `check_health()` — unchanged, no callers affected
- `read()` at `dialogue.py:834` — already has strict integrity check via left-join; this design makes `_next_turn_sequence()` and `recover_startup()` consistent with it
- The happy path (turn 1, clean store) — still returns 1 without `read_thread`

## Risks

**File-global diagnostic blast radius:** A corrupt line from collaboration A can disable the fast path for collaboration B in the same session. This is fail-closed by design — correctness over performance. The double-check cost is one `read_thread()` call, which is the normal path for non-first turns anyway. If this causes user-visible latency in multi-dialogue sessions with store corruption, the mitigation is per-collaboration JSONL files (a larger TurnStore refactor, out of scope).

**`recover_startup()` behavior change:** The updated check is strictly more conservative — it quarantines handles that the old `len(metadata) < completed_count` check would have allowed through. This is the correct direction (aligning with `read()`'s invariant), but existing dialogues with gap states will now be quarantined on session restart instead of being reactivated. The quarantine is non-destructive (handle becomes `"unknown"`, eligible for reattach after repair).

## Decision Log

| # | Decision | Driver | Alternatives rejected |
|---|----------|--------|----------------------|
| 1 | Approach B (`get_all_checked`) over A (`check_health` secondary call) or C (change `_replay` everywhere) | Single-pass, additive API, no existing caller changes | A: double replay, splits one logical read; C: breaks all callers |
| 2 | Any diagnostic (including trailing truncation) distrusts fast path | A truncated line could be the missing metadata for this exact collaboration | `has_warnings` only — too lenient for "prove no turns completed" |
| 3 | Post-read_thread consistency check, not just local contiguity | Partial tail (`{1}` vs remote 2) is contiguous but inconsistent; `read()` would reject it | Contiguity-only — leaves gap between reply and read invariants |
| 4 | Raise integrity error on non-empty inconsistency, don't silently fall through | Dispatching on broken state makes it worse; `read()` would reject later anyway | Fall through to remote — silent self-healing of bad state |
| 5 | Mark handle `"unknown"` before raising on inconsistency | Aligns with `recover_startup()` quarantine pattern | Leave handle status unchanged — inconsistent with existing quarantine behavior |
| 6 | Shared `_local_metadata_consistent()` for both `_next_turn_sequence` and `recover_startup` | Same invariant enforced by `read()`; one function, two enforcement sites | Inline checks — drift risk between the two sites |
| 7 | File-global diagnostics (not per-collaboration) | JSONL is session-wide; per-collaboration filtering would require parsing corrupt records | Per-collaboration diagnostics — impossible for unparseable lines |

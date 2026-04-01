---
date: 2026-04-01
time: "12:58"
created_at: "2026-04-01T16:58:31Z"
session_id: 563ea3fd-6db8-4e43-a0b3-373b71dc3eea
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-01_12-25_persistence-hardening-task-4-journal-migration.md
project: claude-code-tool-dev
branch: main
commit: 6bbd38cb
title: "persistence hardening Tasks 5-6 and branch merges"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/profiles.py
  - packages/plugins/codex-collaboration/tests/test_profiles.py
  - packages/plugins/codex-collaboration/server/models.py
  - packages/plugins/codex-collaboration/tests/test_models_r2.py
---

# persistence hardening Tasks 5-6 and branch merges

## Goal

Complete the persistence hardening and type narrowing plan by: (1) merging Branch 1 (`fix/persistence-replay-hardening`, Tasks 0-4) to main, (2) executing Tasks 5-6 on Branch 2 (`fix/type-narrowing`), (3) merging Branch 2 to main.

**Trigger:** Session 6 completed Task 4 and left Branch 1 review-clean and ready to merge. Tasks 5-6 were the remaining items in the plan at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`.

**Stakes:** Tasks 5-6 are lower-stakes than Tasks 0-4 — type narrowing catches typos and removes `Any` holes, but doesn't affect crash resilience. The real stakes were in getting Branch 1 merged cleanly (10 implementation commits, 3 JSONL store migrations).

**Success criteria:** (1) Both branches merged to main. (2) All 6 plan tasks complete. (3) Full suite passing. (4) No regressions.

**Connection to project arc:** Seventh and final session in the persistence hardening chain: design (1) → plan (2) → review rounds 1-3 (3) → review round 4 + merge (4) → execute Tasks 0-3 (5) → execute Task 4 (6) → **merge Branch 1 + execute Tasks 5-6 + merge Branch 2** (7). The plan is now fully executed and landed on main.

## Session Narrative

Session began by loading the Task 4 handoff (`2026-04-01_12-25_persistence-hardening-task-4-journal-migration.md`). The user confirmed readiness to proceed with the handoff's first next step: merging Branch 1 to main.

**Branch 1 merge — ruff formatting artifacts:** `git status` revealed 28 unstaged modified files across the codex-collaboration plugin. These were not mentioned in the handoff as uncommitted work. Inspection of sample diffs (`models.py`, `runtime.py`) showed they were purely cosmetic ruff formatting changes — line wrapping, parenthesization — produced by `ruff format .` runs during Task 4 execution that reformatted the whole directory beyond the Task 4 files.

The user resolved the formatting artifacts before the session continued, using a worktree-only reverse apply of the unstaged plugin diff to restore the committed state without touching the index.

**HEAD vs. reviewed commit:** The user noted that HEAD (`88028f70`) was not the reviewed Task 4 commit (`2266ccab`). Two handoff archive commits separated them (`d731c165` for save, `88028f70` for archive). The user asked whether to keep or remove these commits before merging. I recommended keeping them — archived handoffs are project documentation that belongs on main, and all prior sessions followed the same pattern. User approved.

**Branch 1 merge execution:** User requested `--ff-only` to enforce the fast-forward assumption. Merge succeeded cleanly: `bb2df9dd..88028f70`, 14 commits, 2,460 insertions, 13 files. Branch deleted with `-d`.

**Branch 2 creation and Task 5 execution (TDD):** Created `fix/type-narrowing` from main. Read the plan for Tasks 5-6 (lines 1691-2062) and all four target files (`profiles.py` at 136 lines, `test_profiles.py` at 88 lines, `models.py` at 244 lines, `test_models_r2.py` at 161 lines) — all small enough to read in one pass.

Task 5 (F4 — Literal types for ResolvedProfile) followed strict TDD:
1. Wrote 14 failing tests: 10 in `TestTypeNarrowing` (posture/effort/turn_budget rejection + acceptance) and 4 in `TestYamlIngressValidation` (YAML ingress path with `_REFERENCES_DIR` monkeypatch). Added `Path` and `yaml` imports to the test file.
2. Verified all 10 rejection tests failed as expected (no validation existed). The 4 "accepted" tests passed immediately — valid values already work without validation.
3. Implemented in three edits to `profiles.py`: (a) added `Literal` and `get_args` to typing imports, (b) added the four type aliases and two frozensets after `ProfileValidationError`, narrowed `ResolvedProfile` fields and `resolve_profile()` parameter types, (c) inserted the three-check validation block between the resolution logic and the pre-existing policy widening gate.
4. Added `# type: ignore[arg-type]` comments to test calls that deliberately pass invalid literal values (Pyright correctly flags these at edit time — the type system is working).
5. All 25 profile tests passed (11 existing + 14 new). Full suite: 427 passing. Lint clean on target files.
6. Discarded ruff formatting artifacts from 27 non-target files (same pattern as Tasks 1-4 — `ruff format` reformats the whole directory). Used `git diff --name-only | grep -v` to restore non-target files.
7. Committed as `ad7fe6d0`.

**Task 6 execution (TDD):** Task 6 (F6 — Concrete session type) was simpler — one test, two edits:
1. Wrote 1 failing test: `test_advisory_runtime_state_session_not_any` inspecting `__dataclass_fields__["session"].type` as a string token. The test asserts two things: the annotation is not `"Any"`, and it contains `"AppServerRuntimeSession"`. This is a raw string comparison, not `get_type_hints()` — the latter would trigger the circular import that `TYPE_CHECKING` is designed to avoid.
2. Also updated imports: replaced unused `HandleStatus` with `AdvisoryRuntimeState`.
3. Verified it failed: `AssertionError: session field is still typed as Any`.
4. Implemented in two edits to `models.py`: (a) added `TYPE_CHECKING` import and guard block importing `AppServerRuntimeSession`, (b) changed `session: Any` to `session: AppServerRuntimeSession`. The `from __future__ import annotations` at line 3 (already present) ensures the annotation stays as a string at runtime.
5. Ruff wanted to reformat `models.py` (the `codex_thread_id` comment wrapping) — applied formatting, then discarded artifacts from non-target files.
6. All 10 model tests passed (9 existing + 1 new). Full suite: 428 passing.
7. Committed as `b25e8bf3`.

**User review of Tasks 5-6:** User ran the full plugin suite (`430 passed in 2.41s`), verified ruff clean on touched files, and found one P3 finding — empty-string explicit overrides (`explicit_posture=""`, `explicit_effort=""`) silently fell back to defaults via `or` semantics instead of reaching the new validation gate. The `or` pattern (`explicit_posture or profile.get(...)`) treats any falsey value as "not provided," creating a bypass path around the new F4 validation. The user also noted that no static type checker config (pyright/mypy) is checked into the repo.

**Fix implementation:** Changed all five override selection lines in `profiles.py:107-131` from `or` semantics to `if x is not None` semantics. The `turn_budget` field already used `is not None` (it was the only field with correct semantics in the original code). Added 2 tests (`test_empty_string_posture_rejected`, `test_empty_string_effort_rejected`) confirming empty strings reach validation. Full suite: 430 passing. Committed as `6bbd38cb`.

**Branch 2 merge and re-review:** User's re-review found no findings. Confirmed the `is not None` fix closes the gap, verified the targeted tests passed (37 passed), full suite passed (430 passed in 2.10s), and ruff clean. Merged `fix/type-narrowing` to main with `--ff-only` (3 commits, `88028f70..6bbd38cb`). Branch deleted with `-d`.

## Decisions

### Keep handoff archive commits on Branch 1 before merging

**Choice:** Merge Branch 1 with both handoff archive commits (`d731c165`, `88028f70`) included, rather than stripping them.

**Driver:** Archived handoffs are project documentation that belongs on main. All prior sessions (1-5) followed the same pattern — handoff save/archive commits traveled with the feature branch. Stripping would require interactive rebase plus re-committing the handoff separately on main after merge.

**Alternatives considered:**
- **Strip via `git reset --soft HEAD~2`** — would orphan this session's archived handoff from the branch history. Rejected because it fights the established workflow and adds steps for cosmetic cleanliness on a branch about to be deleted.
- **Cherry-pick to main separately** — would separate the handoff from its associated implementation commits. Rejected as unnecessary fragmentation.

**Trade-offs accepted:** Branch has 14 commits instead of 12, slightly noisier history. Accepted because the handoff commits are small and self-documenting.

**Confidence:** High (E2) — verified all prior sessions followed the same pattern by checking the branch commit log which showed `docs(handoff):` commits on every branch.

**Reversibility:** N/A — merge already completed.

**Change trigger:** None — this is a workflow convention, not a technical decision.

### Use --ff-only for branch merges

**Choice:** Use `git merge --ff-only` instead of plain `git merge` for both branch merges.

**Driver:** User requested: "use `--ff-only` so Git enforces the fast-forward assumption instead of silently creating a merge commit if the branch moved." This enforces the invariant that main hasn't diverged — if it had, the merge would fail loudly rather than silently creating a merge commit.

**Alternatives considered:**
- **Plain `git merge`** — would silently create a merge commit if main had diverged. Rejected because it hides the divergence.

**Trade-offs accepted:** If main had diverged, the merge would fail and require a rebase first. Accepted because this is the desired behavior — divergence should be surfaced, not hidden.

**Confidence:** High (E2) — both merges succeeded as fast-forwards, confirming the assumption.

**Reversibility:** N/A — merges completed.

**Change trigger:** None — this is a safety practice.

### Switch explicit override selection from `or` to `is not None`

**Choice:** Changed all five override selection lines in `resolve_profile()` from `or` semantics to `if x is not None` semantics.

**Driver:** User's P3 review finding: empty-string explicit overrides (`explicit_posture=""`) silently fell back to defaults via `or` semantics, bypassing the new F4 validation gate. The `or` pattern treats any falsey value (including `""`, `0`, `False`) as "not provided."

**Alternatives considered:**
- **Keep `or` semantics and add empty-string rejection as a separate check** — would leave the inconsistency between `None` (not provided) and `""` (provided but falsey). Rejected because the root cause is the `or` semantics, not a missing validation rule.
- **Only fix posture and effort (the two string fields with validation)** — would leave the other fields (`sandbox`, `approval_policy`) with inconsistent semantics. Rejected for consistency.

**Trade-offs accepted:** `turn_budget` already used `is not None` semantics (it was the original code's only `is not None` field). No regression risk — `None` is the only sentinel value used by callers.

**Confidence:** High (E2) — verified that all callers pass `None` for "not provided" (no caller passes empty strings intentionally). Added 2 tests confirming empty strings now reach validation.

**Reversibility:** High — single-line changes.

**Change trigger:** None — this closes a bypass gap.

## Changes

### Modified files

| File | Purpose |
|------|---------|
| `server/profiles.py` | Added `Posture`, `Effort`, `SandboxPolicy`, `ApprovalPolicy` Literal type aliases; narrowed `ResolvedProfile` and `resolve_profile()` types; added runtime validation block; switched override selection to `is not None` semantics |
| `tests/test_profiles.py` | Added `TestTypeNarrowing` (12 tests) and `TestYamlIngressValidation` (4 tests); added `Path` and `yaml` imports |
| `server/models.py` | Added `TYPE_CHECKING` guard importing `AppServerRuntimeSession`; changed `session: Any` to `session: AppServerRuntimeSession` |
| `tests/test_models_r2.py` | Added `test_advisory_runtime_state_session_not_any`; replaced `HandleStatus` import with `AdvisoryRuntimeState` |

### Commit log (Branch 2: fix/type-narrowing)

| Commit | Message | Tests |
|--------|---------|-------|
| `ad7fe6d0` | fix: narrow ResolvedProfile fields to Literal types (F4) | 427 |
| `b25e8bf3` | fix: narrow AdvisoryRuntimeState.session to AppServerRuntimeSession (F6) | 428 |
| `6bbd38cb` | fix: use is-not-None semantics for explicit override selection (F4) | 430 |

### Full plan commit log (all tasks)

| Commit | Message | Task | Tests |
|--------|---------|------|-------|
| `bf2641af` | docs: update design spec with review findings | — | — |
| `311fea3f` | feat: shared JSONL replay helper with corruption classification | 1 | 384 |
| `5f7edbde` | test: cover UnknownOperation trailing-classification and partial final line | 1 | 384 |
| `7cb2685f` | fix: migrate TurnStore to shared replay helper (I2) | 2 | 389 |
| `538c726a` | fix: migrate LineageStore to shared replay helper (I4) | 3 | 401 |
| `a33e98d0` | fix: migrate Journal to shared replay helper (I5) | 4A | 411 |
| `7bba1da4` | fix: correct test docstring for turn_sequence enforcement scope | 4A | 411 |
| `16394b8e` | test: controller-level corruption tests for journal and TurnStore | 4B | 413 |
| `d3de26eb` | style: document completed-phase relaxation, fix E402 import order | 4 | 413 |
| `2266ccab` | fix: strengthen controller fallback test, remove unused import | 4 | 413 |
| `ad7fe6d0` | fix: narrow ResolvedProfile fields to Literal types (F4) | 5 | 427 |
| `b25e8bf3` | fix: narrow AdvisoryRuntimeState.session to AppServerRuntimeSession (F6) | 6 | 428 |
| `6bbd38cb` | fix: use is-not-None semantics for explicit override selection (F4) | 5 fix | 430 |

## Codebase Knowledge

### Literal Type Pattern in profiles.py

`profiles.py:21-28` defines the type aliases and frozensets:

```python
Posture = Literal["collaborative", "adversarial", "exploratory", "evaluative", "comparative"]
Effort = Literal["minimal", "low", "medium", "high", "xhigh"]
SandboxPolicy = Literal["read-only"]
ApprovalPolicy = Literal["never"]

_VALID_POSTURES: frozenset[str] = frozenset(get_args(Posture))
_VALID_EFFORTS: frozenset[str] = frozenset(get_args(Effort))
```

The `get_args()` pattern serves dual purpose: static type checking for code callers (Pyright flags `"adversrial"` as incompatible with `Posture`) and runtime validation via frozenset membership for YAML-loaded strings. Same pattern as `lineage_store.py` for `HandleStatus`/`CapabilityProfile`.

### Override Selection Pattern

`profiles.py:107-131` — all five override selections now use `is not None`:

```python
posture = (
    explicit_posture
    if explicit_posture is not None
    else profile.get("posture", _DEFAULT_POSTURE)
)
```

Previously, `posture`, `effort`, `sandbox`, and `approval_policy` used `or` semantics. Only `turn_budget` already used `is not None` (because `0` is falsey but semantically meaningful for integers). The fix aligned all five fields.

### Validation Gate Order

`profiles.py:133-148` — validation runs in this order:
1. Type narrowing: posture ∈ `_VALID_POSTURES`, effort ∈ `_VALID_EFFORTS`, `type(turn_budget) is int and turn_budget > 0`
2. Policy widening: `sandbox != "read-only"` or `approval_policy != "never"` rejected

Type narrowing validation was added by Task 5. The policy widening gate was pre-existing. The `type(x) is int` check for turn_budget rejects bools (`isinstance(True, int)` returns `True` in Python because bool subclasses int).

### TYPE_CHECKING Guard Pattern in models.py

`models.py:7-10`:

```python
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .runtime import AppServerRuntimeSession
```

Combined with `from __future__ import annotations` (already present at line 3), this avoids the `models → runtime → models` circular import. At runtime, `session: AppServerRuntimeSession` is stored as the string `"AppServerRuntimeSession"` (PEP 563 lazy evaluation). Type checkers resolve it via the `TYPE_CHECKING` import.

The test at `test_models_r2.py:164-174` verifies via raw annotation string inspection (`__dataclass_fields__["session"].type`), NOT `get_type_hints()` (which would trigger the circular import).

### YAML Ingress Path

`profiles.py:40-64` — `load_profiles()` reads `consultation-profiles.yaml` and optionally merges `consultation-profiles.local.yaml`. The `_REFERENCES_DIR` module-level variable points to the `references/` directory. Tests monkeypatch this to `tmp_path` to exercise the full YAML ingress path including file read, YAML parsing, key mapping (`reasoning_effort` → `effort`), local override merge, and validation.

Key contract: YAML uses `reasoning_effort` (not `effort`) as the field key. This mapping happens at `profiles.py:111`: `profile.get("reasoning_effort")`. The `TestYamlIngressValidation` tests exercise this mapping explicitly — `test_yaml_bad_effort_rejected` writes `reasoning_effort: "turbo"` to YAML and verifies the validation catches it after mapping.

The local override merge path (`profiles.py:55-62`) uses `{**base, **override}` — a full key-level override, not a deep merge. This means a local override with `posture: "adversrial"` replaces the base profile's posture entirely. `test_local_override_bad_posture_rejected` exercises this path: base has valid `"collaborative"`, local override introduces the typo `"adversrial"`, merged result is rejected.

### ResolvedProfile Dataclass Structure

`profiles.py:33-39` — the narrowed dataclass:

```python
@dataclass(frozen=True)
class ResolvedProfile:
    posture: Posture          # was str
    turn_budget: int          # unchanged
    effort: Effort | None     # was str | None
    sandbox: SandboxPolicy    # was str
    approval_policy: ApprovalPolicy  # was str
```

`frozen=True` ensures immutability — resolved profiles are value objects, not mutable state. The `Posture` and `Effort` fields carry the Literal constraint at the type level, which Pyright enforces at call sites. At runtime, the validation block (`profiles.py:133-148`) enforces the same constraint via frozenset membership for values arriving from YAML (which are always `str`, not `Literal`).

### Test Coverage Summary

| Test Class | File | Count | Purpose |
|------------|------|-------|---------|
| `TestTypeNarrowing` | `test_profiles.py` | 12 | Rejection + acceptance for posture, effort, turn_budget |
| `TestYamlIngressValidation` | `test_profiles.py` | 4 | YAML ingress path including local override merge |
| `test_advisory_runtime_state_session_not_any` | `test_models_r2.py` | 1 | Annotation string token check for F6 |

### Dependency Graph (Complete — All Plan Work)

```
replay.py (shared helper — no dependencies)
  ↑ imported by:
  ├── turn_store.py (uses replay_jsonl, SchemaViolation)
  ├── lineage_store.py (uses replay_jsonl, SchemaViolation, UnknownOperation)
  └── journal.py (uses replay_jsonl, SchemaViolation, ReplayDiagnostics)

models.py (HandleStatus, CapabilityProfile Literal types; OperationJournalEntry dataclass)
  ↑ imported by:
  ├── lineage_store.py (get_args for literal validation frozensets)
  ├── journal.py (OperationJournalEntry for explicit construction)
  ├── dialogue.py (controller logic, filtering, recovery)
  └── runtime.py (AppServerRuntimeSession — imported by models.py under TYPE_CHECKING)

profiles.py (Posture, Effort, SandboxPolicy, ApprovalPolicy Literal types; ResolvedProfile)
  ↑ imported by:
  ├── dialogue.py (resolve_profile for consultation start)
  └── mcp_server.py (profile parameter handling)
```

## Context

### Mental Model

This session was **completion and integration** — landing completed work on main and executing the two simplest remaining tasks. Unlike sessions 5-6 which were execution-heavy with complex store migrations, this session was primarily git workflow (merge Branch 1, create Branch 2, merge Branch 2) with two straightforward TDD implementations in between.

The type narrowing tasks (5-6) are a different category from the persistence hardening tasks (0-4). Tasks 0-4 were defense-in-depth: replacing crash-on-malformed with diagnose-and-continue at the persistence layer. Tasks 5-6 are type safety: replacing `str` and `Any` with `Literal` types that catch typos at both compile time (Pyright) and runtime (frozenset validation). The two categories are complementary — Tasks 0-4 handle what happens when bad data reaches the store, Tasks 5-6 prevent bad data from being created in the first place.

### Project State

- **Branch:** `main` at `6bbd38cb`
- **Tests:** 430 passing (359 baseline + 71 new across all 6 tasks)
- **Plan progress:** All 6 tasks complete, plan fully executed
- **Both branches merged:** `fix/persistence-replay-hardening` (Tasks 0-4) and `fix/type-narrowing` (Tasks 5-6)
- **Ruff formatting artifacts:** Present in working directory during ruff runs but consistently discarded before commits. The plugin's formatting style differs from ruff's defaults on ~28 files — a pre-existing condition, not introduced by this work.

### Test Count Summary (Full Plan)

| Task | New Tests | Running Total |
|------|-----------|---------------|
| Task 1 (replay helper) | 25 | 384 |
| Task 2 (TurnStore) | 5 | 389 |
| Task 3 (LineageStore) | 12 | 401 |
| Task 4 (Journal + controller) | 12 | 413 |
| Task 5 (Literal types) | 14+2 | 430 |
| Task 6 (Concrete session type) | 1 | 428* |
| **Total new** | **71** | **430** |

*Task 6 committed before the Task 5 review fix (which added 2 tests), so its running total shows 428.

## Learnings

### `or` semantics in override resolution create validation bypass paths

**Mechanism:** Python's `or` operator returns the first truthy value. For string overrides like `explicit_posture or profile.get("posture", default)`, an empty string `""` is falsey and falls through to the default/profile value. When runtime validation only runs on the resolved value, the empty string never reaches validation — it's silently replaced by a valid default.

**Evidence:** `resolve_profile(explicit_posture="")` returned the default `"collaborative"` posture instead of raising `ProfileValidationError`. The `or` pattern was pre-existing (not introduced by Task 5), but the validation added by Task 5 exposed the gap — before validation existed, the bypass was invisible.

**Implication:** When adding runtime validation to an existing resolution chain, audit the resolution semantics for falsey-value bypass paths. `is not None` is the correct sentinel check when `None` means "not provided."

**Watch for:** Any `x or default` pattern where `x` could be `""`, `0`, `False`, or `[]` and where the intent is "use `x` if the caller provided it."

### Ruff formatting artifacts are a recurring issue in this plugin

**Mechanism:** Running `ruff format .` in the codex-collaboration plugin directory reformats ~28 files with cosmetic changes (line wrapping, parenthesization). These changes are not bugs — they reflect a divergence between the plugin's existing style and ruff's defaults. The artifacts appear after every `ruff format` run and must be discarded before committing.

**Evidence:** Observed in Tasks 1-4 (documented in prior handoffs) and again in this session. The user resolved it this session by reverse-applying the unstaged diff.

**Implication:** When committing in this plugin, always use `git diff --name-only` to verify only intended files are modified, and discard formatting artifacts from non-target files before staging. Alternatively, run `ruff format` only on specific files: `ruff format server/profiles.py tests/test_profiles.py`.

**Watch for:** `git status` showing many modified files after a ruff run — these are formatting artifacts, not implementation changes.

### Plan's test counts don't match actual (cumulative across all tasks)

**Mechanism:** The plan specified test counts per task that didn't always match actual. Plan said 67 new tests total; actual is 71 (plan's count was written before review-driven additions). The discrepancies accumulated across Tasks 1-5 from review findings adding extra tests, plan miscounting existing tests, and behavioral changes that replaced crash-expected tests with filter-expected tests.

**Evidence:** Plan Task 5: 14 tests → actual 14 (matches). But plan cumulative total doesn't account for the 2 empty-string tests added during review. Overall plan said 67 → actual 71.

**Implication:** For future plans with test counts, treat plan counts as estimates, not exact targets. The TDD cycle with review naturally produces more tests than the plan specifies (review findings, edge case discovery).

## Next Steps

### 1. AC6 analytics emission (deferred)

**Dependencies:** None — all persistence hardening work is complete.

**What to read first:** Ticket T-20260330-03 for scope. Plan's delivery.md at line 255 for packet 2b context.

**Approach:** Scope the ticket against the landed code on main. Open a fresh `fix/*` branch.

**Acceptance criteria:** Per ticket.

## In Progress

Clean stopping point. All 6 plan tasks are committed on main. No work in flight. No uncommitted files. Both feature branches deleted.

## Open Questions

### Ruff formatting divergence in codex-collaboration plugin

The plugin has ~28 files where ruff's formatting differs from the existing code style. This causes formatting artifacts after every `ruff format .` run. The divergence is pre-existing and not introduced by the persistence hardening work. Options: (1) accept it and always format only specific files, (2) run a one-time `ruff format .` and commit the result as a separate formatting commit. Neither is urgent — the current workaround (discard artifacts before commit) works.

### Static type checker not configured

The user's review noted: "I did not run a separate static type checker pass; this repo/package does not appear to have an obvious pyright/mypy config checked in." The Literal type aliases added in Task 5 would benefit from static type checking to catch misuses at import sites. Currently only runtime validation and Pyright's inline diagnostics (in the editor) catch type errors.

## Risks

### Pre-existing ruff formatting divergence may cause accidental commits

If someone runs `ruff format .` in the plugin directory and stages all changes without inspecting, the ~28 formatting changes would be committed alongside implementation work. Mitigated by: reviewing `git diff --name-only` before staging, and the existing pattern of formatting only target files.

## References

| What | Where |
|------|-------|
| Implementation plan (final) | `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` |
| Design spec | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` |
| Profiles (Literal types, F4) | `packages/plugins/codex-collaboration/server/profiles.py` |
| Models (TYPE_CHECKING, F6) | `packages/plugins/codex-collaboration/server/models.py` |
| Profile tests | `packages/plugins/codex-collaboration/tests/test_profiles.py` |
| Model tests | `packages/plugins/codex-collaboration/tests/test_models_r2.py` |
| Shared replay helper | `packages/plugins/codex-collaboration/server/replay.py` |
| Recovery coordinator | `packages/plugins/codex-collaboration/server/dialogue.py:369-601` |
| Prior handoff (Task 4) | `docs/handoffs/archive/2026-04-01_12-25_persistence-hardening-task-4-journal-migration.md` |
| Prior handoff (Tasks 0-3) | `docs/handoffs/archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md` |
| AC6 analytics ticket | T-20260330-03 |

## Gotchas

### Empty-string explicit overrides bypass `or`-based resolution

`resolve_profile(explicit_posture="")` with `or` semantics silently returns the default posture. The `or` pattern treats any falsey value as "not provided." Fixed by switching to `is not None` semantics, but this is a general Python gotcha — any `x or default` pattern is vulnerable to falsey-value bypass when the caller might provide `""`, `0`, `False`, or `[]`.

### `type(x) is int` rejects bools but `isinstance(x, int)` doesn't

Python's `bool` is a subclass of `int`, so `isinstance(True, int)` returns `True`. The `turn_budget` validation uses `type(x) is int` (strict identity check) to correctly reject `True`/`False` as valid turn budgets. This pattern is used consistently across all JSONL store callbacks (replay helper) and the profile validation.

### Ruff formatting artifacts require per-file formatting in this plugin

Running `ruff format .` in `packages/plugins/codex-collaboration/` reformats ~28 files. Always format specific files (`ruff format server/profiles.py`) rather than the whole directory when working in this plugin. Or inspect `git diff --name-only` before staging.

### `from __future__ import annotations` makes all annotations strings at runtime

`models.py` uses PEP 563 lazy annotations. The `session: AppServerRuntimeSession` field is stored as the string `"AppServerRuntimeSession"` at runtime, not resolved to the actual class. Tests must inspect `__dataclass_fields__["session"].type` as a string, NOT use `get_type_hints()` (which would import the class and trigger the circular dependency).

## User Preferences

**Execute-then-review workflow:** Consistent across all 7 sessions. The user reviews each task's output before proceeding. This session: user reviewed Tasks 5-6 together (since both were on the same branch), found one P3 finding, and approved the fix in a second review pass.

**Review format:** Structured with `::code-comment` annotations including priority, confidence, file, line range. Findings section lists each issue with file links. Verdict is implicit in the review structure (no explicit ship/block label this session, but the "no findings" second review clearly signals approval).

**Merge safety:** User explicitly requested `--ff-only` for branch merges — prefers failing loudly over silently creating merge commits. This is a safety practice: enforces the assumption that main hasn't diverged.

**Branch naming:** User specified `fix/*` for Branch 2 instead of `chore/*` (which the handoff had suggested). The user's explicit instruction takes precedence over the handoff's suggestion.

**Phase-boundary handoffs:** Consistent across all 7 sessions. Each session ends with a handoff save. This is the final session in the chain — no further sessions expected unless AC6 analytics work begins.

## Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1 | 2026-03-31 | Design spec | `archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| 2 | 2026-03-31 | Implementation plan | `archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| 3 | 2026-03-31 | Review rounds 1-3 | `archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| 4 | 2026-04-01 | Review round 4 + merge | `archive/2026-04-01_00-00_plan-revision-round-4-persistence-hardening.md` |
| 5 | 2026-04-01 | Execute Tasks 0-3 | `archive/2026-04-01_01-33_persistence-hardening-execution-tasks-0-3.md` |
| 6 | 2026-04-01 | Execute Task 4 | `archive/2026-04-01_12-25_persistence-hardening-task-4-journal-migration.md` |
| **7** | **2026-04-01** | **Merge + Tasks 5-6** | **This handoff** |

# PR #23 Deferred Findings — Design

**Date:** 2026-02-21
**Status:** Reviewed (7 amendments applied from evaluative Codex dialogue)
**Branch:** TBD (off `main` at `71a88ab`)
**Origin:** PR #23 (cross-model plugin review) — 2 review rounds, 33 total findings. 7 deferred items remain.

## Problem

PR #23 addressed 25 of 33 findings across 2 review rounds. 7 items were deferred:

| ID | Type | Summary |
|----|------|---------|
| I3 | Silent fallback | `mode` defaults to `"server_assisted"` when agent epilogue is missing — no signal to analytics consumers |
| S5 | Missing sentinel | No closing `<!-- /pipeline-data -->` sentinel; extraction termination is implicit |
| S4 | Narrow exception | `read_file()` catches `FileNotFoundError` only; `PermissionError` propagates unhandled |
| I7 | Missing test | No conformance test validates scope-breach behavior across documents |
| — | Test gap | `check_agent_governance_count` FileNotFoundError branch untested |
| — | Test gap | `check_event_types_in_contract` §13-missing branch untested |
| — | Test gap | Error accumulation (multiple simultaneous failures) untested |

An 8th item (S3: allowed-tools completeness) was investigated and found to be a non-issue — both skills list exactly the tools they use.

## Design Decisions

### D1: `mode_source` observability field (I3)

**Decision:** Add `mode_source` as a reserved nullable enum (`"epilogue"` | `"fallback"`) to `dialogue_outcome` events. Do not add to `consultation_outcome` events.

**Rationale:** The builder's `.get("mode", "server_assisted")` default is correct behavior — `server_assisted` is the expected mode in most cases. The problem is that when the agent fails to emit an epilogue, the default activates silently. `mode_source` makes the default's activation visible without changing the default itself.

**Schema impact:** Reserved nullable field, no version bump. Follows the `episode_id` precedent (line 413 of `emit_analytics.py`). Not added to `_DIALOGUE_REQUIRED` — this is diagnostic telemetry, not contractual semantics.

**Enum validation:** Add `_VALID_MODE_SOURCES = {"epilogue", "fallback"}` constant. `validate()` enforces: for `dialogue_outcome` events, `mode_source` must be `None` or a member of `_VALID_MODE_SOURCES`. For `consultation_outcome` events, `mode_source` must be absent or `None` — non-None values are rejected. This is an injection-protection guard: `build_consultation_outcome` never sets the field, so the check prevents manual injection of semantically incorrect values.

**Absent-vs-null policy:** `mode_source` is absent from `consultation_outcome` event dicts (not set to `None`). In `dialogue_outcome` event dicts, it is always present — `None` when pipeline omits it, `"epilogue"` or `"fallback"` when set.

**Values:**
- `"epilogue"` — `mode` was parsed from the agent's `<!-- pipeline-data -->` JSON epilogue
- `"fallback"` — epilogue was missing, unparseable, missing `mode` key, or had invalid mode value
- `null` — `consultation_outcome` event (field not applicable)

**Codex consultation:** Codex initially proposed a 0.4.0 resolver rule, then conceded that reserved nullable is correct for diagnostic telemetry (T2 of dialogue, concession).

### D2: S5 reframed as extraction termination clarification (S5-lite)

**Decision:** Defer the closing sentinel (`<!-- /pipeline-data -->`). Instead, clarify SKILL.md's parsing instructions: "Parse JSON from the fenced code block immediately after `<!-- pipeline-data -->`. Stop at the first closing code fence. If the epilogue is missing or unparseable, set `mode` to `"server_assisted"` and `mode_source` to `"fallback"`."

**Rationale:** `emit_analytics.py` receives pre-parsed pipeline data — it never sees the sentinel. The sentinel format is SKILL.md's concern only. The current single sentinel works; adding a closing one is complexity for minimal gain when extraction termination is properly documented.

**Codex consultation:** Both sides agreed in T2-T3 that the current sentinel is sufficient. The closing sentinel is deferred, not rejected — it can be added later if parsing ambiguity is observed.

### D3: Widen to `OSError` (S4)

**Decision:** Replace `read_file()`'s `path.exists()` + `FileNotFoundError` pattern with direct `try/except OSError` on `path.read_text()`. Include exception class in error messages: `f"cannot read {path} ({type(e).__name__}): {e}"`. Update all 4 `except FileNotFoundError` blocks in `validate()` to `except OSError`. Also widen `check_agent_governance_count`'s `except FileNotFoundError` at line 109 and the 3 unconditional governance calls at lines 257-271 to `except OSError`.

**Downstream catch widening (regression prevention):** Before this change, `read_file()` always raises `FileNotFoundError` (via the explicit `path.exists()` guard), so the narrow catches downstream are accidentally correct. After widening `read_file()` to `OSError`, all downstream catches must also widen — otherwise `PermissionError` and other `OSError` subtypes propagate unhandled, aborting the validator's error accumulation behavior. This affects 5 total catch sites: 4 in `validate()` (lines 206, 211, 216, 221) and 1 in `check_agent_governance_count` (line 109).

**Rationale:** `OSError` is the common base for `FileNotFoundError`, `PermissionError`, and other filesystem errors (`IsADirectoryError`, `UnicodeDecodeError` via OS-level encoding issues). Catching the base class handles all filesystem failure modes. The `path.exists()` guard also has a TOCTOU race (file could be deleted between check and read).

**Test approach:** Monkeypatch `Path.read_text` to raise `PermissionError` — deterministic, no actual filesystem permission changes needed.

### D4: Cross-component scope-breach conformance test (I7)

**Decision:** Parse the existing `### Valid termination reasons` subsection in consultation-contract.md §13 (line 332), which already lists the canonical values in backtick-delimited format. No contract modification needed.

New test imports `_VALID_TERMINATION_REASONS` from `emit_analytics`, extracts backtick-delimited values from §13's existing subsection with `re.findall(r"`([^`]+)`", body)`, and compares as sets. Also verifies §6 references `termination_reason: scope_breach`.

**Rationale:** §13 already contains a `### Valid termination reasons` subsection with the exact 5 values (`convergence`, `budget`, `error`, `scope_breach`, `complete`). Adding a second representation would create drift risk. The existing subsection is already canonical and parseable.

**Codex consultation (collaborative):** Evolved from shallow substring check (T1) through cross-component invariant (T3) to structured canonical line (T5-T6). **Codex consultation (evaluative):** Revised in T3 — both sides agreed the contract already has the canonical line and should not be modified.

## Architecture

### Two parallel streams with zero file overlap

| Stream | Findings | Files Owned |
|--------|----------|-------------|
| **A** (analytics + docs) | I3, S5-lite | `emit_analytics.py`, `test_emit_analytics.py`, `dialogue/SKILL.md` |
| **B** (validator + tests) | S4, I7, 3 test gaps | `validate_consultation_contract.py`, `test_consultation_contract_sync.py` |

`codex-dialogue.md` is reserved for Stream A but requires no changes (the agent's epilogue format is already correct; S5-lite changes SKILL.md's parsing instructions, not the agent's output format). `consultation-contract.md` was originally in Stream B for a D4 contract edit, but D4 was revised to parse the existing content — no contract changes needed.

### Stream A changes

**`emit_analytics.py`:**
- Add `_VALID_MODE_SOURCES = {"epilogue", "fallback"}` constant
- `build_dialogue_outcome`: add `"mode_source": pipeline.get("mode_source")` (nullable, no default)
- `validate()`: for `dialogue_outcome`, check `mode_source` is `None` or in `_VALID_MODE_SOURCES`; for `consultation_outcome`, reject non-None `mode_source` if present
- No changes to `_DIALOGUE_REQUIRED`, `_CONSULTATION_REQUIRED`, or `_resolve_schema_version`

**`test_emit_analytics.py`:**
- Update `test_all_fields_present` (line 421): add `mode_source` to the expected key set
- Update pipeline-key coverage tests if they assert exact field counts
- Test `mode_source` propagation in `dialogue_outcome` (both `"epilogue"` and `"fallback"`)
- Test `mode_source` invalid value rejected on `dialogue_outcome`
- Test `mode_source` rejected (validation error) on `consultation_outcome` when non-None
- Test `mode_source` None on `dialogue_outcome` passes (nullable)

**`dialogue/SKILL.md`:**
- Add `mode_source` row to Step 7a pipeline field table
- Rewrite `mode` row to clarify extraction termination: "Parse JSON from the fenced code block immediately after `<!-- pipeline-data -->`. Stop at the first closing code fence. If the epilogue is missing or unparseable, set `mode` to `"server_assisted"` and `mode_source` to `"fallback"`."
- D2 parser tests: the instruction-only S5-lite mitigation should be paired with tests in `test_emit_analytics.py` verifying the "stop at first closing fence" parsing rule. Without tests, formatting drift could silently break epilogue extraction.

### Stream B changes

**`validate_consultation_contract.py`:**
- Rewrite `read_file()`: remove `path.exists()`, wrap `path.read_text()` in `try/except OSError`
- Update 4 `except FileNotFoundError` blocks in `validate()` to `except OSError`
- Widen `check_agent_governance_count` `except FileNotFoundError` (line 109) to `except OSError`
- Add `check_scope_breach_conformance()` function (called from `validate()` for runtime enforcement, not test-only)

**`consultation-contract.md`:**
- No changes — §13 already has `### Valid termination reasons` with the canonical values

**`test_consultation_contract_sync.py`:**
- `test_agent_governance_missing_file`: non-existent agent path → verify error message
- `test_event_types_missing_section`: contract text without `## 13.` → verify "section not found" error
- `test_multiple_simultaneous_errors`: input triggering 2+ check functions → verify all errors accumulated
- `test_read_file_permission_error`: monkeypatch `Path.read_text` raising `PermissionError` → verify `OSError` caught
- `test_scope_breach_conformance`: import `_VALID_TERMINATION_REASONS` from `emit_analytics`, parse §13's existing `### Valid termination reasons` subsection with `re.findall(r"`([^`]+)`", body)`, compare as sets
- `test_scope_breach_in_section_6`: verify §6 references `termination_reason: scope_breach`

## Verification

All commands run from the repo root (`/Users/jp/Projects/active/claude-code-tool-dev`). Test files are at repo root `tests/`, not inside the plugin directory. The plugin's `scripts/` are at `packages/plugins/cross-model/scripts/`.

### Stream A

| Check | Command | Expected |
|-------|---------|----------|
| Unit tests | `uv run pytest tests/test_emit_analytics.py -x -q` | All pass (existing + new) |
| Fixture replay | `uv run pytest tests/test_emit_analytics.py -k TestReplayConformance -x -q` | 15 pass (fixtures unchanged) |
| Ruff | `uv run ruff check packages/plugins/cross-model/scripts/emit_analytics.py tests/test_emit_analytics.py` | Clean |

### Stream B

| Check | Command | Expected |
|-------|---------|----------|
| Unit tests | `uv run pytest tests/test_consultation_contract_sync.py -x -q` | All pass (existing + new) |
| Conformance validator | `uv run scripts/validate_consultation_contract.py` | PASS |
| Ruff | `uv run ruff check scripts/validate_consultation_contract.py tests/test_consultation_contract_sync.py` | Clean |

### Integration

| Check | Command | Expected |
|-------|---------|----------|
| Full suite | `uv run pytest tests/ -x -q` | All existing + new tests pass |

## Risks

### Instruction-based epilogue emission remains non-deterministic

`mode_source: "fallback"` makes the problem visible but doesn't prevent it. The agent may still fail to emit the epilogue, and `mode` will still default to `"server_assisted"`. The improvement is observability — analytics consumers can now filter for `mode_source == "fallback"` to identify events where the mode value is inferred.

### I7 test imports from emit_analytics

The scope-breach conformance test in Stream B imports `_VALID_TERMINATION_REASONS` from `emit_analytics.py` (owned by Stream A). This is a read-only import — Stream B does not modify `emit_analytics.py`. The import creates a logical dependency but not a file-level conflict.

### Existing plan overlap

Two untracked plan docs exist in `docs/plans/` that touch some of the same files:
- `2026-02-21-p0-system-polish.md` — touches `emit_analytics.py`, `test_emit_analytics.py`
- `2026-02-20-e-tuning-review-fixes.md` — touches `test_emit_analytics.py`

These plans are for different work items. File-level merge contention is possible but limited to Stream A files. Stream B has no overlap with existing plans.

## References

| What | Where |
|------|-------|
| PR #23 (merged) | `https://github.com/jpsweeney97/claude-code-tool-dev/pull/23` |
| emit_analytics.py | `packages/plugins/cross-model/scripts/emit_analytics.py` |
| Conformance validator | `scripts/validate_consultation_contract.py` |
| Validator tests | `tests/test_consultation_contract_sync.py` |
| Analytics tests | `tests/test_emit_analytics.py` |
| Dialogue SKILL.md | `packages/plugins/cross-model/skills/dialogue/SKILL.md` |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` |
| Codex dialogue (collaborative) | Thread `019c8395-5b30-7fd2-ac9d-c0f789db43c8` — 6 turns, converged |
| Codex dialogue (evaluative) | Thread `019c83bc-707d-7182-acc3-e5e957eee822` — 6 turns, converged |
| Codex consultation (I3 quick) | Thread `019c838d-a4dc-7d20-952c-d45df428848d` — 1 turn |

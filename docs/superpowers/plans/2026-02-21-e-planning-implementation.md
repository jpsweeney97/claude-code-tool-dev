# E-PLANNING Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `--plan` flag to `/dialogue` that triggers a Step 0 question-shaping pre-step, improving gatherer output quality for architectural and planning questions.

**Architecture:** Step 0 runs Claude-locally before the existing 7-step pipeline. It performs field-scoped decomposition with independent validation and fallback — each output field (`planning_question`, `assumptions`, `key_terms`, `shape_confidence`, `ambiguities`) is validated independently, and invalid fields fall back to baseline behavior without discarding valid siblings. Step 0 is considered successful (`question_shaped=true`) when ≥1 routing field (`planning_question`, `assumptions`, `key_terms`) is accepted from decomposition output; fallback is recovery, not acceptance. When 0 routing fields are accepted, `question_shaped=false` records decomposition failure with deterministic companion values. A simplified debug gate (artifact signals + intent×failure lexeme combos with architecture phrase suppression) skips Step 0 entirely for debugging questions (`question_shaped=null`, all companions null). Analytics uses a tri-state `question_shaped` (null/true/false) to distinguish "not attempted" from "attempted and failed." A unified `_resolve_schema_version()` helper centralizes version determination across all feature flags.

**Tech Stack:** Python 3 (emit_analytics.py, tests), Markdown (SKILL.md, agent docs, contract, profiles YAML)

**Reference:** `docs/plans/2026-02-19-cross-model-plugin-enhancements.md` §3 (E-PLANNING spec). Design decisions from two Codex dialogues: exploratory (thread `019c7e82-d230-7b53-b17c-e189cb11a895`) and collaborative (thread `019c7e96-f46e-79a2-8e5f-e861dd91cc75`).

**Branch:** Create `feature/e-planning` from `main`.

**Test command:** `uv run pytest tests/test_emit_analytics.py -v` (run from repo root)

**Dependencies between tasks:**
- Task 1 (emit_analytics.py plumbing): independent
- Task 2 (emit_analytics.py validation): depends on Task 1 (uses new constants and resolver)
- Task 3 (analytics tests): depends on Tasks 1+2 (tests the new code)
- Task 4 (consultation-contract.md): independent (parallel with Task 1)
- Task 5 (consultation-profiles.yaml): depends on Task 4 (references contract changes)
- Task 6 (SKILL.md Step 0 + fallback): depends on Tasks 3+4+5 (references tested analytics, contract, profile)
- Task 7 (codex-dialogue agent): depends on Tasks 4+6 (reads contract + delegation changes)
- Task 8 (spec-lock tests): depends on Tasks 4+5+6+7 (cross-references all modified files)
- Task 9 (enhancements spec update): depends on Task 6 (documents debug gate spec deviation)
- Task 10 (final verification): depends on all tasks

---

## Task List

### Task 1: emit_analytics.py — Planning Field Plumbing
- **Modify:** `packages/plugins/cross-model/scripts/emit_analytics.py`
- Add `_VALID_SHAPE_CONFIDENCE` enum set
- Add `assumptions_generated_count`, `ambiguity_count` to `_COUNT_FIELDS`
- Add `_resolve_schema_version()` helper
- Replace hard-coded `None` planning fields with `pipeline.get()` calls
- Replace inline 0.2.0 auto-bump with `_resolve_schema_version()` call
- **Why first:** All other tasks reference these constants and the resolver

### Task 2: emit_analytics.py — Planning Field Validation
- **Modify:** `packages/plugins/cross-model/scripts/emit_analytics.py`
- Add tri-state invariant: `question_shaped is not None` → remaining planning fields must be non-None
- Add `shape_confidence` enum validation (when non-None)
- Add `question_shaped` bool type check (when non-None)
- Replace provenance-only cross-field invariant with unified `_resolve_schema_version()` check
- **Why second:** Uses constants from Task 1; must exist before tests in Task 3

### Task 3: Analytics Tests — 26 New Tests
- **Modify:** `tests/test_emit_analytics.py`
- Add `SAMPLE_PIPELINE` planning field defaults (explicit None)
- Add `_pipeline_with_planning()` helper
- 8 build tests: schema bump, tri-state routing, field propagation, type rejection
- 9 validate tests: tri-state invariant, shape_confidence enum, question_shaped bool, cross-field, error precedence
- 3 reverse invariant tests: stray companion rejection when question_shaped=None
- 2 E2E tests: planning end-to-end, planning+provenance combined
- 4 hardening tests: edge cases (bool pipeline values, string pipeline values, etc.)
- **Why third:** Verifies Tasks 1+2 before downstream files reference them

### Task 4: Consultation Contract — Delegation Envelope Update
- **Modify:** `packages/plugins/cross-model/references/consultation-contract.md`
- Add `reasoning_effort` field to §6 delegation envelope table
- Add `delegated-precedence` resolution note to §8 policy resolver
- **Why parallel with T1:** Independent document; no code dependencies

### Task 5: Planning Profile
- **Modify:** `packages/plugins/cross-model/references/consultation-profiles.yaml`
- Add `planning` profile: `posture: evaluative`, `turn_budget: 8`, `reasoning_effort: xhigh`
- **Why after T4:** References contract delegation envelope for reasoning_effort propagation

### Task 6: SKILL.md — Step 0, Debug Gate, Fallback, Analytics
- **Modify:** `packages/plugins/cross-model/skills/dialogue/SKILL.md`
- Add `--plan` flag to argument table and argument-hint frontmatter
- Add Step 0 section: template, debug gate, field-scoped fallback, tri-state semantics
- Add conditional in Step 1: skip extraction when Step 0 provides assumptions
- Update Step 2: use Step 0 `key_terms` when available
- Update Step 5: add `reasoning_effort` to delegation envelope
- Update Step 7: add planning pipeline fields to emission table
- Update line 36: profile resolution includes `reasoning_effort`
- **Why after T3+T4+T5:** Largest change; references tested analytics, contract, and profile

### Task 7: codex-dialogue Agent — reasoning_effort Propagation
- **Modify:** `packages/plugins/cross-model/agents/codex-dialogue.md`
- Add `reasoning_effort` to Phase 1 parse table
- Add propagation instruction: read from envelope, pass as `config.model_reasoning_effort`
- **Why after T4+T6:** Reads contract changes and delegation envelope from SKILL.md

### Task 8: Spec-Lock Tests — 8 Cross-Reference Tests
- **Create:** `tests/test_e_planning_spec_sync.py`
- Tests that verify cross-file consistency: flag table completeness, profile field coverage, delegation envelope fields, schema version constants, debug gate pattern list, planning field names
- **Why after T4-T7:** Cross-references all modified files

### Task 9: Enhancements Spec Update — Debug Gate Deviation
- **Modify:** `docs/plans/2026-02-19-cross-model-plugin-enhancements.md`
- Update §3.3 to document debug gate skip behavior (replacing best-effort)
- Add amendment note explaining the design change and rationale
- **Why after T6:** Documents the spec deviation introduced in Task 6

### Task 10: Final Verification
- Run full test suite, lint, verify counts
- **Why last:** Confirms everything works together

---

*Phase 3 detailed steps follow below.*

---

## Task 1: emit_analytics.py — Planning Field Plumbing

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:38-91` (constants), `:290-370` (builder)

**Step 1: Add `_VALID_SHAPE_CONFIDENCE` enum set**

After `_VALID_SEED_CONFIDENCE` (line 41), add:

```python
_VALID_SHAPE_CONFIDENCE = {"high", "medium", "low"}
```

**Step 2: Add planning count fields to `_COUNT_FIELDS`**

Add `"assumptions_generated_count"` and `"ambiguity_count"` to the `_COUNT_FIELDS` set (after `"provenance_unknown_count"` at line 90):

```python
    "assumptions_generated_count",
    "ambiguity_count",
```

**Step 3: Add `_resolve_schema_version()` helper**

After the `_is_non_negative_int` function (line 67), add:

```python
def _resolve_schema_version(event: dict) -> str:
    """Determine schema version from feature-flag fields.

    Precedence: planning (0.3.0) > provenance (0.2.0) > base (0.1.0).
    Used in both build (auto-set) and validate (exact equality check).
    """
    if event.get("question_shaped") is not None:
        return "0.3.0"
    if _is_non_negative_int(event.get("provenance_unknown_count")):
        return "0.2.0"
    return _SCHEMA_VERSION
```

**Step 4: Replace hard-coded planning fields with `pipeline.get()` calls**

In `build_dialogue_outcome`, replace lines 355-359:

```python
        # Planning (nullable)
        "question_shaped": None,
        "shape_confidence": None,
        "assumptions_generated_count": None,
        "ambiguity_count": None,
```

with:

```python
        # Planning (nullable — populated when --plan is used)
        "question_shaped": pipeline.get("question_shaped"),
        "shape_confidence": pipeline.get("shape_confidence"),
        "assumptions_generated_count": pipeline.get("assumptions_generated_count"),
        "ambiguity_count": pipeline.get("ambiguity_count"),
```

**Step 5: Replace inline auto-bump with unified resolver**

Replace lines 366-368:

```python
    # Schema version auto-bump (§4.4): valid provenance count → 0.2.0
    if _is_non_negative_int(event.get("provenance_unknown_count")):
        event["schema_version"] = "0.2.0"
```

with:

```python
    # Schema version auto-bump (§4.4): unified resolver
    event["schema_version"] = _resolve_schema_version(event)
```

**Step 6: Verify no syntax errors**

Run: `python3 -m py_compile packages/plugins/cross-model/scripts/emit_analytics.py`
Expected: No output (clean import)

**Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py
git commit -m "feat(analytics): add planning field plumbing and unified schema resolver

- Add _VALID_SHAPE_CONFIDENCE enum set
- Add assumptions_generated_count, ambiguity_count to _COUNT_FIELDS
- Add _resolve_schema_version() helper (0.3.0 > 0.2.0 > 0.1.0)
- Replace hard-coded None planning fields with pipeline.get() calls
- Replace inline 0.2.0 auto-bump with unified resolver"
```

---

## Task 2: emit_analytics.py — Planning Field Validation

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:440-505` (validate function)

**Step 1: Add tri-state invariant after mode check**

After the mode validation block (line 448), add the tri-state invariant:

```python
    # Tri-state planning invariant: question_shaped drives field requirements
    qs = event.get("question_shaped")
    if qs is not None:
        if not isinstance(qs, bool):
            raise ValueError(
                f"question_shaped must be bool or None, got {type(qs).__name__}"
            )
        # Forward: when question_shaped is set (true or false), remaining planning
        # fields must be non-None (failure telemetry is preserved even on false)
        for pf in ("shape_confidence", "assumptions_generated_count", "ambiguity_count"):
            if event.get(pf) is None:
                raise ValueError(
                    f"{pf} is required when question_shaped is set (got None)"
                )
    else:
        # Reverse: when question_shaped is None (--plan not used or debug gate
        # skip), all companion fields must also be None
        for pf in ("shape_confidence", "assumptions_generated_count", "ambiguity_count"):
            if event.get(pf) is not None:
                raise ValueError(
                    f"{pf} must be None when question_shaped is None "
                    f"(got {event.get(pf)!r})"
                )

    # Independent enum validation for nullable shape_confidence;
    # validate whenever non-null regardless of question_shaped branch
    sc = event.get("shape_confidence")
    if sc is not None and sc not in _VALID_SHAPE_CONFIDENCE:
        raise ValueError(f"invalid shape_confidence: {sc!r}")
```

**Step 2: Replace provenance-only cross-field invariant with unified resolver check**

Replace lines 456-462:

```python
    # Cross-field: provenance count requires schema 0.2.0
    prov = event.get("provenance_unknown_count")
    if _is_non_negative_int(prov) and event.get("schema_version") != "0.2.0":
        raise ValueError(
            f"provenance_unknown_count is set ({prov}) but schema_version "
            f"is {event.get('schema_version')!r}, expected '0.2.0'"
        )
```

with:

```python
    # Cross-field: schema_version must match feature-flag state
    expected_version = _resolve_schema_version(event)
    actual_version = event.get("schema_version")
    if actual_version != expected_version:
        raise ValueError(
            f"schema_version mismatch: expected {expected_version!r} "
            f"(from feature flags), got {actual_version!r}"
        )
```

**Step 3: Verify no syntax errors**

Run: `python3 -m py_compile packages/plugins/cross-model/scripts/emit_analytics.py`
Expected: No output (clean import)

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py
git commit -m "feat(analytics): add planning field validation and unified schema check

- Add tri-state invariant: question_shaped non-None requires remaining planning fields
- Add shape_confidence enum validation
- Add question_shaped bool type check
- Replace provenance-only cross-field invariant with unified _resolve_schema_version check"
```

---

## Task 3: Analytics Tests — 26 New Tests

**Files:**
- Modify: `tests/test_emit_analytics.py:83-107` (SAMPLE_PIPELINE), new test classes

**Step 1: Add explicit None planning fields to SAMPLE_PIPELINE**

In `SAMPLE_PIPELINE` (line 83), add after the `"scope_roots_fingerprint": None` line:

```python
    # Planning fields (None = --plan not used)
    "question_shaped": None,
    "shape_confidence": None,
    "assumptions_generated_count": None,
    "ambiguity_count": None,
```

**Step 2: Add `_pipeline_with_planning()` helper**

After `_consultation_input` (around line 123), add:

```python
def _pipeline_with_planning(
    question_shaped: bool = True,
    shape_confidence: str = "high",
    assumptions_generated_count: int = 3,
    ambiguity_count: int = 1,
    **overrides,
) -> dict:
    return {
        **SAMPLE_PIPELINE,
        "question_shaped": question_shaped,
        "shape_confidence": shape_confidence,
        "assumptions_generated_count": assumptions_generated_count,
        "ambiguity_count": ambiguity_count,
        **overrides,
    }
```

**Step 3: Write 8 build tests in TestBuildDialogueOutcome**

Add after the existing provenance tests (after `test_provenance_unknown_count_float_pipeline_no_schema_bump`):

```python
    # --- Planning field build tests ---

    def test_schema_version_bumps_with_planning(self) -> None:
        """schema_version auto-bumps to 0.3.0 when question_shaped is non-None."""
        pipeline = _pipeline_with_planning()
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.3.0"

    def test_schema_version_bumps_with_planning_false(self) -> None:
        """schema_version 0.3.0 even when question_shaped=False (failure telemetry)."""
        pipeline = _pipeline_with_planning(question_shaped=False)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.3.0"

    def test_planning_fields_propagated_from_pipeline(self) -> None:
        """All 4 planning fields propagate from pipeline input."""
        pipeline = _pipeline_with_planning(
            question_shaped=True,
            shape_confidence="medium",
            assumptions_generated_count=5,
            ambiguity_count=2,
        )
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["question_shaped"] is True
        assert event["shape_confidence"] == "medium"
        assert event["assumptions_generated_count"] == 5
        assert event["ambiguity_count"] == 2

    def test_planning_none_when_absent(self) -> None:
        """Planning fields default to None when not in pipeline."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["question_shaped"] is None
        assert event["shape_confidence"] is None
        assert event["assumptions_generated_count"] is None
        assert event["ambiguity_count"] is None

    def test_planning_precedence_over_provenance(self) -> None:
        """schema_version 0.3.0 takes precedence when both planning and provenance active."""
        pipeline = _pipeline_with_planning(provenance_unknown_count=3)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.3.0"

    def test_planning_nonbool_question_shaped_still_bumps(self) -> None:
        """Non-bool question_shaped triggers 0.3.0 (resolver checks `is not None`, validation catches type)."""
        pipeline = {**SAMPLE_PIPELINE, "question_shaped": "yes"}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # String "yes" is not None, so resolver returns 0.3.0
        assert event["schema_version"] == "0.3.0"

    def test_planning_question_shaped_false_all_fields_present(self) -> None:
        """question_shaped=False still propagates all planning fields."""
        pipeline = _pipeline_with_planning(
            question_shaped=False,
            shape_confidence="low",
            assumptions_generated_count=0,
            ambiguity_count=0,
        )
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["question_shaped"] is False
        assert event["shape_confidence"] == "low"

    def test_resolve_schema_version_base(self) -> None:
        """_resolve_schema_version returns 0.1.0 with no feature flags."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert MODULE._resolve_schema_version(event) == "0.1.0"
```

**Step 4: Update existing provenance cross-field test**

The existing `test_provenance_schema_version_cross_field_invariant` (around line 767) asserts `match="provenance_unknown_count is set"` which will no longer match after Task 2's unified resolver change (new error is `"schema_version mismatch"`). Update the match string:

```python
    def test_provenance_schema_version_cross_field_invariant(self) -> None:
        """provenance_unknown_count requires schema_version 0.2.0."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["schema_version"] = "0.1.0"
        with pytest.raises(ValueError, match="schema_version mismatch"):
            MODULE.validate(event, "dialogue_outcome")
```

**Step 5: Write 8 new validate tests in TestValidate**

Add after the existing cross-field invariant tests:

```python
    # --- Planning field validation tests ---

    def test_planning_tri_state_missing_shape_confidence(self) -> None:
        """question_shaped=True requires shape_confidence."""
        pipeline = _pipeline_with_planning(shape_confidence=None)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="shape_confidence is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_tri_state_missing_assumptions_count(self) -> None:
        """question_shaped=True requires assumptions_generated_count."""
        pipeline = _pipeline_with_planning(assumptions_generated_count=None)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="assumptions_generated_count is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_tri_state_missing_ambiguity_count(self) -> None:
        """question_shaped=True requires ambiguity_count."""
        pipeline = _pipeline_with_planning(ambiguity_count=None)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="ambiguity_count is required"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_invalid_shape_confidence(self) -> None:
        """shape_confidence must be in valid set."""
        pipeline = _pipeline_with_planning(shape_confidence="very_high")
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="invalid shape_confidence"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_question_shaped_wrong_type(self) -> None:
        """question_shaped must be bool when non-None."""
        pipeline = {**SAMPLE_PIPELINE, "question_shaped": "yes", "shape_confidence": "high", "assumptions_generated_count": 3, "ambiguity_count": 1}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        with pytest.raises(ValueError, match="question_shaped must be bool"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_schema_version_cross_field_invariant(self) -> None:
        """Planning active requires schema_version 0.3.0."""
        pipeline = _pipeline_with_planning()
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["schema_version"] = "0.2.0"  # Mutate to wrong version
        with pytest.raises(ValueError, match="schema_version mismatch"):
            MODULE.validate(event, "dialogue_outcome")

    def test_provenance_schema_version_still_validated(self) -> None:
        """Provenance without planning still requires 0.2.0."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["schema_version"] = "0.1.0"  # Mutate to wrong version
        with pytest.raises(ValueError, match="schema_version mismatch"):
            MODULE.validate(event, "dialogue_outcome")

    def test_planning_valid_event_passes(self) -> None:
        """Fully valid planning event passes validation."""
        pipeline = _pipeline_with_planning()
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        MODULE.validate(event, "dialogue_outcome")  # Should not raise

    # --- Reverse invariant tests ---

    def test_reverse_invariant_stray_shape_confidence(self) -> None:
        """question_shaped=None with stray shape_confidence rejects."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["shape_confidence"] = "high"  # Stray companion
        with pytest.raises(ValueError, match="shape_confidence must be None when question_shaped is None"):
            MODULE.validate(event, "dialogue_outcome")

    def test_reverse_invariant_stray_assumptions_count(self) -> None:
        """question_shaped=None with stray assumptions_generated_count rejects."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["assumptions_generated_count"] = 3  # Stray companion
        with pytest.raises(ValueError, match="assumptions_generated_count must be None when question_shaped is None"):
            MODULE.validate(event, "dialogue_outcome")

    def test_reverse_invariant_stray_ambiguity_count(self) -> None:
        """question_shaped=None with stray ambiguity_count rejects."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["ambiguity_count"] = 1  # Stray companion
        with pytest.raises(ValueError, match="ambiguity_count must be None when question_shaped is None"):
            MODULE.validate(event, "dialogue_outcome")

    # --- Error precedence test ---

    def test_planning_nonbool_no_companions_type_error_first(self) -> None:
        """Non-bool question_shaped without companions: type error takes precedence."""
        pipeline = {**SAMPLE_PIPELINE, "question_shaped": "yes"}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # isinstance check fires before companion-field forward check
        with pytest.raises(ValueError, match="question_shaped must be bool"):
            MODULE.validate(event, "dialogue_outcome")
```

**Step 6: Write 2 E2E tests in TestMain**

Add after `test_dialogue_provenance_end_to_end`:

```python
    def test_dialogue_planning_end_to_end(self, tmp_path, monkeypatch) -> None:
        """E2E: planning fields trigger schema_version 0.3.0 in log."""
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        pipeline = _pipeline_with_planning()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_dialogue_input(pipeline=pipeline)))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0

        event = json.loads(log_path.read_text().strip())
        assert event["schema_version"] == "0.3.0"
        assert event["question_shaped"] is True
        assert event["shape_confidence"] == "high"

    def test_dialogue_planning_and_provenance_end_to_end(
        self, tmp_path, monkeypatch
    ) -> None:
        """E2E: planning takes precedence over provenance for schema_version."""
        log_path = tmp_path / "events.jsonl"
        monkeypatch.setattr(MODULE, "_LOG_PATH", log_path)

        pipeline = _pipeline_with_planning(provenance_unknown_count=5)
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_dialogue_input(pipeline=pipeline)))
        monkeypatch.setattr("sys.argv", ["emit_analytics.py", str(input_file)])

        exit_code = MODULE.main()
        assert exit_code == 0

        event = json.loads(log_path.read_text().strip())
        assert event["schema_version"] == "0.3.0"
        assert event["provenance_unknown_count"] == 5
```

**Step 7: Write 4 hardening tests**

Add to TestBuildDialogueOutcome:

```python
    def test_planning_bool_shape_confidence_passes_through(self) -> None:
        """Bool shape_confidence from pipeline passes through (validation catches)."""
        pipeline = _pipeline_with_planning(shape_confidence=True)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["shape_confidence"] is True  # Builder is permissive

    def test_planning_negative_assumptions_count_passes_through(self) -> None:
        """Negative assumptions_generated_count passes through (validation catches)."""
        pipeline = _pipeline_with_planning(assumptions_generated_count=-1)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["assumptions_generated_count"] == -1  # Builder is permissive

    def test_planning_float_ambiguity_count_passes_through(self) -> None:
        """Float ambiguity_count passes through (validation catches)."""
        pipeline = _pipeline_with_planning(ambiguity_count=1.5)
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["ambiguity_count"] == 1.5  # Builder is permissive

    def test_planning_string_count_passes_through(self) -> None:
        """String assumptions_generated_count passes through (validation catches)."""
        pipeline = _pipeline_with_planning(assumptions_generated_count="3")
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["assumptions_generated_count"] == "3"  # Builder is permissive
```

**Step 8: Run full test suite**

Run: `uv run pytest tests/test_emit_analytics.py -v`
Expected: 137 tests pass (111 existing + 26 new; 1 existing test updated in Step 4)

**Step 9: Commit**

```bash
git add tests/test_emit_analytics.py
git commit -m "test(analytics): add 26 planning field tests

- 8 build tests: schema bump, tri-state routing, field propagation, type passthrough
- 9 validate tests: tri-state invariant, shape_confidence enum, question_shaped bool, cross-field, error precedence
- 3 reverse invariant tests: stray companion rejection when question_shaped=None
- 2 E2E tests: planning end-to-end, planning+provenance combined
- 4 hardening tests: bool/negative/float/string passthrough"
```

---

## Task 4: Consultation Contract — Delegation Envelope Update

**Files:**
- Modify: `packages/plugins/cross-model/references/consultation-contract.md:106-124` (§6), `:188-200` (§8)

**Step 1: Add `reasoning_effort` to §6 delegation envelope table**

In the table at line 110, add a new row after `seed_confidence`:

```markdown
| `reasoning_effort` | No | Resolved from profile or flag. Values: `minimal`, `low`, `medium`, `high`, `xhigh`. When omitted, use §8 default (`xhigh`). |
```

**Step 2: Add delegated-precedence note to §8 policy resolver**

After the `model_reasoning_effort` default row (line 196), add:

```markdown

**Delegated precedence:** When the delegation envelope (§6) includes `reasoning_effort`, the agent uses it directly — no re-resolution of profile files. The delegating skill is responsible for resolution order (explicit flag > profile > §8 default). The agent's §8 resolver is the fallback when the delegation envelope omits the field.
```

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/references/consultation-contract.md
git commit -m "docs(contract): add reasoning_effort to delegation envelope

- Add reasoning_effort field to §6 delegation envelope table
- Add delegated-precedence note to §8 policy resolver"
```

---

## Task 5: Planning Profile

**Files:**
- Modify: `packages/plugins/cross-model/references/consultation-profiles.yaml:68` (after code-review profile)

**Step 1: Add `planning` profile**

After the `code-review` profile (line 68), add:

```yaml

  planning:
    description: >
      Plan review and architectural design. Evaluative posture with proactive
      question shaping. Use when reviewing plans, making architectural decisions,
      or exploring design trade-offs. Pairs with --plan flag for Step 0 question
      decomposition.
    sandbox: read-only
    approval_policy: never
    reasoning_effort: xhigh
    posture: evaluative
    turn_budget: 8
```

**Step 2: Commit**

```bash
git add packages/plugins/cross-model/references/consultation-profiles.yaml
git commit -m "feat(profiles): add planning consultation profile

- posture: evaluative, turn_budget: 8, reasoning_effort: xhigh
- Pairs with --plan flag for Step 0 question decomposition"
```

---

## Task 6: SKILL.md — Step 0, Debug Gate, Fallback, Analytics

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md`

This is the largest task. Changes are organized by section.

**Step 1: Update frontmatter argument-hint**

Replace line 4:
```
argument-hint: '"question" [-p posture] [-n turns] [--profile name]'
```
with:
```
argument-hint: '"question" [-p posture] [-n turns] [--profile name] [--plan]'
```

**Step 2: Add `--plan` to argument table**

After the `--profile` row in the Arguments table (around line 30), add:

```markdown
| `--plan` | — | boolean | false |
```

**Step 3: Update profile resolution text (line 36)**

Replace:
```
**Profile resolution:** Profiles set `posture` and `turn_budget` only. Execution controls (`sandbox`, `approval_policy`, `reasoning_effort`) use consultation contract defaults.
```
with:
```
**Profile resolution:** Profiles set `posture`, `turn_budget`, and `reasoning_effort`. Execution controls (`sandbox`, `approval_policy`) use consultation contract defaults.
```

**Note:** This is a behavior change, not just documentation. Existing profiles define `reasoning_effort` values (e.g., `quick-check: medium`, `exploratory: high`) that were previously ignored because the old text excluded `reasoning_effort` from profile resolution. After this change: `quick-check` goes from `xhigh` (contract default) to `medium`, `exploratory` and `code-review` go from `xhigh` to `high`. This resolves a pre-existing inconsistency between SKILL.md and `profiles.yaml`.

**Step 4: Add validation rule for `--plan`**

After validation rule 4 (line 42), add:
```markdown
5. If `--plan` is present without a question/problem statement, ask the user: "What problem would you like to plan?"
```

**Step 5: Add Step 0 section before Step 1**

Before `### Step 1: Extract assumptions` (line 48), add the full Step 0 section:

```markdown
### Step 0: Question shaping (when `--plan` is set)

Skip this step if `--plan` is not set. Proceed directly to Step 1.

**Debug gate:** Before decomposition, check if the question is a debugging question. If ANY of these artifact signals appear in the question (case-insensitive): `traceback`, `stack trace`, `exception`, `panic`, `segfault` — OR if an intent signal (`how do I fix`, `how do we fix`, `debug`, `root cause`, `why does`) appears together with an unsuppressed failure lexeme (`fail`, `failing`, `failed`, `failure`, `error`, `bug`, `crash`, `broken`) — then skip Step 0 entirely. Set all planning pipeline fields to null. Proceed to Step 1 with the raw question.

Architecture phrase suppressions (these phrases suppress adjacent failure lexemes): `error handling`, `failure mode`, `failure modes`, `fault tolerance`, `error budget`, `recovery strategy`, `retry policy`, `crash-only design`.

Example: "How should we design error handling for the API?" → NOT a debugging question (failure lexeme "error" is suppressed by "error handling"). "Why does the API error on startup?" → IS a debugging question (intent "why does" + unsuppressed "error").

**Decomposition:** Run Claude-locally (no Codex). Decompose the user's problem statement using this template:

```
Given this problem statement: "{raw_input}"

Decompose into:
1. A focused, answerable question (one sentence)
2. 2-5 testable assumptions (things that could be true or false about the codebase)
3. 3-8 search terms (function names, module names, file patterns, concepts)
4. Your confidence that this decomposition captures the user's intent (high/medium/low)
5. 0-3 ambiguities that could change the decomposition

Format:
planning_question: ...
assumptions:
- A1: "..."
- A2: "..."
key_terms: [term1, term2, ...]
shape_confidence: high|medium|low
ambiguities:
- ...
```

**Validation:** Parse the decomposition output. For each field, apply tolerant normalization:
- Key aliases: accept `question` as alias for `planning_question`, `confidence` for `shape_confidence`
- List parsing: accept both YAML list and comma-separated formats for `assumptions`, `key_terms`, `ambiguities`
- Assumption ID repair: if IDs are missing (e.g., bare strings), assign A1, A2, ... sequentially
- Dedup: remove duplicate assumptions (normalized text match)
- Cap: maximum 5 assumptions, 8 key_terms, 3 ambiguities

After normalization, validate each routing field independently:
- `planning_question`: must be a non-empty string. If invalid → fallback to raw question.
- `assumptions`: must be a non-empty list of strings. If invalid → Step 1 extracts from `planning_question`.
- `key_terms`: must be a non-empty list of strings. If invalid → Step 2 Gatherer A derives normally.
- `shape_confidence`: must be `"high"`, `"medium"`, or `"low"`. If invalid → default to `"low"`.
- `ambiguities`: must be a list of strings. If invalid → empty list.

**Tri-state `question_shaped`:**
- `null`: `--plan` was not set (all planning pipeline fields are null)
- `true`: `--plan` was set AND ≥ 1 routing field (`planning_question`, `assumptions`, `key_terms`) was accepted after validation
- `false`: `--plan` was set AND 0 routing fields were accepted (complete decomposition failure)

**shape_confidence downgrade:** For each routing field that falls back:
- `assumptions` fallback: downgrade `shape_confidence` one level (high→medium, medium→low)
- `key_terms` fallback: downgrade `shape_confidence` one level
- Minimum is `low` (no further downgrade)

**UX output:** Always show `planning_question` and `shape_confidence` to the user. Show full detail (assumptions, key_terms, ambiguities) only when:
- `shape_confidence` is `medium` or `low`, OR
- Any routing field triggered fallback

If `shape_confidence` is `low`, emit a note: "Question decomposition has low confidence. Consider clarifying: {ambiguities}."

**Pipeline state:** Initialize all planning pipeline fields before Step 0:
- `question_shaped`: null
- `shape_confidence`: null
- `assumptions_generated_count`: null
- `ambiguity_count`: null

**Atomic Step 0 finalization:** After Step 0 completes, set all planning pipeline fields atomically. There are exactly two post-decomposition terminal states (the debug gate skip is a separate pre-decomposition path that leaves all fields at null):

**Success** (`question_shaped=true`, ≥1 routing field accepted):
- `question_shaped`: true
- `shape_confidence`: resolved value after downgrades
- `assumptions_generated_count`: number of assumptions in Step 0 raw output (before fallback)
- `ambiguity_count`: number of ambiguities in Step 0 output

**Failure** (`question_shaped=false`, 0 routing fields accepted OR unrecoverable decomposition error):
- `question_shaped`: false
- `shape_confidence`: "low"
- `assumptions_generated_count`: parsed raw count if available, else 0
- `ambiguity_count`: parsed raw count if available, else 0

This atomic finalization prevents stale-companion states where `pipeline.get()` reads partially-set fields after a mid-Step-0 exception. The debug gate skip is a separate path — it leaves all fields at their initialized null values (not false).
```

**Step 6: Update Step 1 with conditional skip**

Replace the Step 1 header and first paragraph:

```markdown
### Step 1: Resolve assumptions

**If Step 0 provided valid assumptions:** Use them directly. Skip extraction.

**Otherwise (no `--plan`, or Step 0 assumptions fell back):** From the question (which may be `planning_question` from Step 0 or the raw question), identify testable assumptions and assign IDs:
```

The rest of Step 1 remains unchanged.

**Step 7: Update Step 2 key_terms integration**

In the Gatherer A prompt template, add a note:

```markdown
When `--plan` is set and Step 0 provided valid `key_terms`, use those as `{extracted_terms}`. Otherwise, derive terms from the question as usual.
```

**Step 8: Update Step 5 delegation envelope**

Add `reasoning_effort` to the delegation template:

```markdown
    reasoning_effort: {resolved from profile or contract default}
```

And add a note:

```markdown
**`reasoning_effort` resolution:** profile value > consultation contract §8 default (`xhigh`). When `--plan` is used without `--profile`, reasoning_effort falls through to the contract default (`xhigh`). Pass the resolved value in the envelope — the `codex-dialogue` agent uses it directly without re-resolving profiles. (A `-t` flag for explicit override is deferred — profile propagation covers the immediate need.)
```

**Step 9: Update Step 7 pipeline fields table**

Add to the Pipeline fields table:

```markdown
| `question_shaped` | Step 0 | bool or null |
| `shape_confidence` | Step 0 | string or null |
| `assumptions_generated_count` | Step 0 | int or null |
| `ambiguity_count` | Step 0 | int or null |
```

**Step 10: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(dialogue): add --plan flag with Step 0 question shaping

- Add --plan flag to argument table and frontmatter
- Add Step 0: debug gate, template decomposition, field-scoped fallback
- Tri-state question_shaped semantics (null/true/false)
- Deterministic shape_confidence downgrade per fallback
- Conditional Step 0 UX (detail on medium/low only)
- Update Step 1 to conditional 'resolve assumptions'
- Update Step 2 for key_terms integration
- Update Step 5 for reasoning_effort delegation
- Update Step 7 for planning pipeline fields
- Update profile resolution to include reasoning_effort"
```

---

## Task 7: codex-dialogue Agent — reasoning_effort Propagation

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:34-44` (parse table), `:93-100` (Phase 2 setup)

**Step 1: Add `reasoning_effort` to parse table**

In the Phase 1 parse table (line 36), add a new row:

```markdown
| `reasoning_effort` | No | Resolved reasoning effort for Codex calls. Values: `minimal`, `low`, `medium`, `high`, `xhigh`. When omitted, use consultation contract §8 default (`xhigh`). Passed from delegation envelope. |
```

**Step 2: Add propagation instruction to Phase 2**

After the existing `config` parameter description (around line 97), add:

```markdown
If the delegation envelope includes `reasoning_effort`, use it as `config.model_reasoning_effort`. Otherwise, use the consultation contract §8 default (`xhigh`). Do not re-resolve profile files — the delegating skill has already resolved precedence.
```

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "feat(codex-dialogue): add reasoning_effort propagation from delegation envelope

- Add reasoning_effort to Phase 1 parse table
- Add propagation instruction: envelope value > contract default"
```

---

## Task 8: Spec-Lock Tests — 8 Cross-Reference Tests

**Files:**
- Create: `tests/test_e_planning_spec_sync.py`

**Step 1: Write spec-lock tests**

```python
"""Spec-lock tests for E-PLANNING cross-file consistency.

These tests verify that cross-file references remain consistent across
the E-PLANNING implementation files. They read the actual source files
and check for structural invariants.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent / "packages" / "plugins" / "cross-model"
SKILL_PATH = PLUGIN_ROOT / "skills" / "dialogue" / "SKILL.md"
PROFILES_PATH = PLUGIN_ROOT / "references" / "consultation-profiles.yaml"
CONTRACT_PATH = PLUGIN_ROOT / "references" / "consultation-contract.md"
AGENT_PATH = PLUGIN_ROOT / "agents" / "codex-dialogue.md"
ANALYTICS_PATH = PLUGIN_ROOT / "scripts" / "emit_analytics.py"


class TestEPlanningSpecSync:
    """Cross-file consistency checks for E-PLANNING."""

    def test_plan_flag_in_skill_argument_table(self) -> None:
        """SKILL.md argument table includes --plan flag."""
        content = SKILL_PATH.read_text()
        assert re.search(r"\|\s*`--plan`\s*\|", content), (
            "SKILL.md argument table missing --plan flag"
        )

    def test_plan_flag_in_argument_hint(self) -> None:
        """SKILL.md frontmatter argument-hint includes --plan."""
        content = SKILL_PATH.read_text()
        assert "--plan" in content.split("---")[1], (
            "SKILL.md argument-hint missing --plan"
        )

    def test_planning_profile_exists(self) -> None:
        """consultation-profiles.yaml has a planning profile."""
        content = PROFILES_PATH.read_text()
        assert re.search(r"^\s+planning:", content, re.MULTILINE), (
            "consultation-profiles.yaml missing planning profile"
        )

    def test_planning_profile_posture(self) -> None:
        """Planning profile uses evaluative posture."""
        content = PROFILES_PATH.read_text()
        # Anchor to planning block: find "planning:" then check posture
        # within the same indented block (before the next top-level key)
        planning_match = re.search(
            r"^\s+planning:\s*\n((?:\s{4,}.*\n)*)",
            content,
            re.MULTILINE,
        )
        assert planning_match, "consultation-profiles.yaml missing planning profile block"
        block = planning_match.group(1)
        posture_match = re.search(r"posture:\s*(\w+)", block)
        assert posture_match and posture_match.group(1) == "evaluative", (
            "Planning profile posture should be evaluative"
        )

    def test_reasoning_effort_in_delegation_envelope(self) -> None:
        """Consultation contract §6 delegation envelope includes reasoning_effort."""
        content = CONTRACT_PATH.read_text()
        # Scope to §6 section — reasoning_effort already exists in §8 defaults,
        # so a whole-file check would pass before Task 4 adds it to §6
        section_6_match = re.search(
            r"(##\s*§?6\b.*?)(?=##\s*§?7\b|\Z)", content, re.DOTALL
        )
        assert section_6_match, "consultation-contract.md missing §6 section"
        assert "reasoning_effort" in section_6_match.group(1), (
            "consultation-contract.md §6 delegation envelope missing reasoning_effort"
        )

    def test_reasoning_effort_in_agent_parse_table(self) -> None:
        """codex-dialogue agent Phase 1 parse table includes reasoning_effort."""
        content = AGENT_PATH.read_text()
        # Scope to parse table row — the file may mention reasoning_effort
        # elsewhere (e.g., model_reasoning_effort), so check for a table row
        parse_table_match = re.search(
            r"\|[^\n]*`reasoning_effort`[^\n]*\|", content
        )
        assert parse_table_match, (
            "codex-dialogue.md Phase 1 parse table missing reasoning_effort row"
        )

    def test_valid_shape_confidence_in_analytics(self) -> None:
        """emit_analytics.py defines _VALID_SHAPE_CONFIDENCE."""
        content = ANALYTICS_PATH.read_text()
        assert "_VALID_SHAPE_CONFIDENCE" in content, (
            "emit_analytics.py missing _VALID_SHAPE_CONFIDENCE"
        )

    def test_resolve_schema_version_in_analytics(self) -> None:
        """emit_analytics.py defines _resolve_schema_version."""
        content = ANALYTICS_PATH.read_text()
        assert "_resolve_schema_version" in content, (
            "emit_analytics.py missing _resolve_schema_version"
        )
```

**Step 2: Run spec-lock tests**

Run: `uv run pytest tests/test_e_planning_spec_sync.py -v`
Expected: 8 tests pass

**Step 3: Commit**

```bash
git add tests/test_e_planning_spec_sync.py
git commit -m "test(e-planning): add 8 spec-lock cross-reference tests

- Flag table completeness (--plan in argument table and hint)
- Profile field coverage (planning profile exists, evaluative posture)
- Delegation envelope fields (reasoning_effort in contract and agent)
- Schema version constants (_VALID_SHAPE_CONFIDENCE, _resolve_schema_version)"
```

---

## Task 9: Enhancements Spec Update — Debug Gate Deviation

**Files:**
- Modify: `docs/plans/2026-02-19-cross-model-plugin-enhancements.md:156` (§3.3 debug gate)

**Step 1: Update §3.3 debug gate description**

Replace the existing debug gate text (line 156):

```
**Scope:** `--plan` is for architectural, design, and planning questions — not debugging. Debugging questions ("why does X fail?") produce root-cause hypotheses, not architectural assumptions; the template structure is not designed for them. If a debugging question is detected (heuristic: question contains "fail", "error", "bug", "crash", "broken"), run Step 0 best-effort and force `shape_confidence: low` with guidance: "This looks like a debugging question. Consider running without `--plan` for better results."
```

with:

```
**Scope:** `--plan` is for architectural, design, and planning questions — not debugging. Debugging questions ("why does X fail?") produce root-cause hypotheses, not architectural assumptions; the template structure is not designed for them.

**Debug gate (amended 2026-02-21):** If a debugging question is detected, skip Step 0 entirely — do not run best-effort. Set all planning pipeline fields to null (`question_shaped: null`). Proceed directly to Step 1 with the raw question.

Detection uses a two-tier heuristic:
- **Artifact signals** (any match skips): `traceback`, `stack trace`, `exception`, `panic`, `segfault`
- **Intent+failure combos** (both required): an intent term (`how do I/we fix`, `debug`, `root cause`, `why does`) combined with an unsuppressed failure lexeme (`fail`, `failing`, `failed`, `failure`, `error`, `bug`, `crash`, `broken`)

**Architecture phrase suppressions** prevent false positives on planning questions about error handling: `error handling`, `failure mode(s)`, `fault tolerance`, `error budget`, `recovery strategy`, `retry policy`, `crash-only design`.

_Design rationale: Skip produces a clean null analytics signal (--plan was not effectively used), whereas best-effort produces a noisy question_shaped=false signal that conflates debugging detection with decomposition failure. The non-blocking pipeline means misclassification is recoverable — if the gate incorrectly skips Step 0, the dialogue still runs normally. Original design was best-effort with forced `shape_confidence: low`; changed to skip after cross-model design review (threads 019c7e82, 019c7e96)._
```

**Step 2: Commit**

```bash
git add docs/plans/2026-02-19-cross-model-plugin-enhancements.md
git commit -m "docs(spec): amend §3.3 debug gate from best-effort to skip

- Skip Step 0 entirely for debugging questions (cleaner analytics signal)
- Two-tier detection: artifact signals + intent×failure lexeme combos
- Architecture phrase suppressions prevent false positives
- Rationale: cross-model design review threads 019c7e82, 019c7e96"
```

---

## Task 10: Final Verification

**Step 1: Run full analytics test suite**

Run: `uv run pytest tests/test_emit_analytics.py -v`
Expected: 137 tests pass (111 existing + 26 new)

**Step 2: Run spec-lock tests**

Run: `uv run pytest tests/test_e_planning_spec_sync.py -v`
Expected: 8 tests pass

**Step 3: Run all tests together**

Run: `uv run pytest tests/test_emit_analytics.py tests/test_e_planning_spec_sync.py -v`
Expected: 145 tests pass (137 analytics + 8 spec-lock)

**Step 4: Run lint**

Run: `uv run ruff check packages/plugins/cross-model/scripts/ tests/`
Expected: No errors

**Step 5: Verify file change count**

Modified files (7):
- `packages/plugins/cross-model/scripts/emit_analytics.py`
- `tests/test_emit_analytics.py`
- `packages/plugins/cross-model/references/consultation-contract.md`
- `packages/plugins/cross-model/references/consultation-profiles.yaml`
- `packages/plugins/cross-model/skills/dialogue/SKILL.md`
- `packages/plugins/cross-model/agents/codex-dialogue.md`
- `docs/plans/2026-02-19-cross-model-plugin-enhancements.md`

New files (1):
- `tests/test_e_planning_spec_sync.py`

---

## Final Verification

Run: `uv run pytest tests/test_emit_analytics.py tests/test_e_planning_spec_sync.py -v`
Expected: All tests pass (145 total: 137 analytics [111 existing + 26 new] + 8 spec-lock)

Run: `uv run ruff check packages/plugins/cross-model/scripts/ tests/`
Expected: No errors

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `scripts/emit_analytics.py` | Modified | Planning field plumbing, `_resolve_schema_version()`, tri-state validation |
| `tests/test_emit_analytics.py` | Modified | 26 new tests (build, validate, E2E, hardening, reverse invariant, error precedence) |
| `tests/test_e_planning_spec_sync.py` | New | 8 spec-lock cross-reference tests |
| `references/consultation-contract.md` | Modified | `reasoning_effort` in §6 delegation envelope |
| `references/consultation-profiles.yaml` | Modified | `planning` profile |
| `skills/dialogue/SKILL.md` | Modified | `--plan` flag, Step 0, debug gate, field-scoped fallback, reasoning_effort propagation |
| `agents/codex-dialogue.md` | Modified | `reasoning_effort` in parse table and config propagation |
| `docs/plans/...enhancements.md` | Modified | §3.3 debug gate amendment (best-effort → skip) |

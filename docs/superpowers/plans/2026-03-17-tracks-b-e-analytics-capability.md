# Tracks B + E: Analytics Coverage & Capability Completeness

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 4 new analytics sections to `compute_stats.py` (planning effectiveness, provenance health, parse diagnostics, consultation quality), add thread discovery CLI, integrate reviewer analytics, and fix the pre-existing contract sync test failure.

**Architecture:** All new sections follow the existing `_compute_*` pattern: a template dict defines the output shape, a function computes values from period-filtered events, and `_SECTION_MATRIX` controls which sections appear for each `--type`. Track E #8 (thread discovery) adds a `--threads` CLI flag. Track E #9 (reviewer analytics) adds a `consultation_source` discriminator field to `consultation_outcome` events and wires event emission into `codex-reviewer.md`.

**Tech Stack:** Python (compute_stats.py, event_schema.py, emit_analytics.py), Markdown (agent files), pytest

**Prerequisites:**
- Tracks A, C, D complete (all merged to main)
- `feature/learning-injection` branch merged
- 629 cross-model package tests passing
- `test_termination_reasons_match_contract` fails pre-existing (fixed in Task 1)

---

### Task 1: Fix `test_termination_reasons_match_contract`

**Files:**
- Modify: `tests/test_consultation_contract_sync.py:414-448`

**Context:** The test imports `_VALID_TERMINATION_REASONS` from `emit_analytics.py` via `importlib.util.spec_from_file_location`. This fails because `emit_analytics.py` uses `if __package__:` guards with sibling imports (`event_log`, `event_schema`) — when loaded outside the package, the `else` branch hits `ModuleNotFoundError`.

**Fix:** Import from `event_schema.py` instead — it's a leaf module with no sibling imports (only `from __future__ import annotations` and `import types`), so importlib loads it cleanly. `VALID_TERMINATION_REASONS` is defined there (line 145) and re-imported by `emit_analytics.py`.

- [ ] **Step 1: Replace the importlib target**

Replace the full `test_termination_reasons_match_contract` function (lines 414-448):

```python
def test_termination_reasons_match_contract() -> None:
    """§13's Valid termination reasons must match event_schema.VALID_TERMINATION_REASONS."""
    import re as re_mod
    import importlib.util as ilu

    # Import from event_schema (leaf module, no sibling imports — importlib-safe)
    schema_path = REPO_ROOT / "packages/plugins/cross-model/scripts/event_schema.py"
    spec = ilu.spec_from_file_location("event_schema", schema_path)
    assert spec is not None and spec.loader is not None
    schema_mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(schema_mod)
    code_reasons = schema_mod.VALID_TERMINATION_REASONS

    # Parse §13's "### Valid termination reasons" subsection
    contract_text = CONTRACT_PATH.read_text()
    section_13 = MODULE.extract_section_text(contract_text, "## 13.")
    assert section_13 is not None, "§13 not found in contract"

    # Find the subsection body after "### Valid termination reasons"
    sub_start = section_13.find("### Valid termination reasons")
    assert sub_start != -1, "§13 missing '### Valid termination reasons' subsection"

    # Extract text until next ### or end
    sub_text = section_13[sub_start:]
    next_sub = sub_text.find("\n### ", len("### Valid termination reasons"))
    if next_sub != -1:
        sub_text = sub_text[:next_sub]

    # Extract backtick-delimited values
    contract_reasons = set(re_mod.findall(r"`([^`]+)`", sub_text))

    assert contract_reasons == code_reasons, (
        f"termination reason mismatch: contract has {sorted(contract_reasons)}, "
        f"code has {sorted(code_reasons)}"
    )
```

Key changes: `emit_analytics` → `event_schema`, `emit_mod._VALID_TERMINATION_REASONS` → `schema_mod.VALID_TERMINATION_REASONS` (public constant, no underscore prefix).

- [ ] **Step 2: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_consultation_contract_sync.py::test_termination_reasons_match_contract -v
```
Expected: PASS

- [ ] **Step 3: Run full contract sync suite**

Run:
```bash
uv run pytest tests/test_consultation_contract_sync.py -v
```
Expected: 30 passed, 0 failed (was 29 passed, 1 failed)

- [ ] **Step 4: Commit**

```bash
git add tests/test_consultation_contract_sync.py
git commit -m "fix: import termination reasons from event_schema instead of emit_analytics

The test loaded emit_analytics via importlib, which fails because
emit_analytics has sibling imports guarded by if __package__:.
event_schema is a leaf module with no sibling imports — importlib
loads it cleanly. VALID_TERMINATION_REASONS is defined there."
```

---

### Task 2: Planning Effectiveness Metrics (Track B, Finding #2)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/compute_stats.py` (add template + function)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats.py` (add tests)

**Context:** Planning fields (`question_shaped`, `shape_confidence`, `assumptions_generated_count`, `ambiguity_count`) are stored in both `dialogue_outcome` and `consultation_outcome` events (schema 0.3.0 — `event_schema.py:37-46` resolution). `emit_analytics.py:457-460` populates them from the pipeline. No `_compute_*` section consumes them.

The tri-state invariant: when `question_shaped` is set (bool), all companion fields (`shape_confidence`, `assumptions_generated_count`, `ambiguity_count`) are required non-None. When `question_shaped` is None, all companions must also be None. Validated in `emit_analytics.py:578-608`.

- [ ] **Step 1: Write the failing test for `_compute_planning`**

Add to `test_compute_stats.py`:

```python
def _make_dialogue_event(**overrides: object) -> dict:
    """Minimal dialogue_outcome event for planning tests."""
    base: dict = {
        "event": "dialogue_outcome",
        "schema_version": "0.3.0",
        "consultation_id": "test-plan-001",
        "ts": "2026-03-17T10:00:00Z",
        "posture": "collaborative",
        "turn_count": 4,
        "turn_budget": 10,
        "converged": True,
        "convergence_reason_code": "all_resolved",
        "termination_reason": "convergence",
        "resolved_count": 3,
        "unresolved_count": 0,
        "emerged_count": 1,
        "seed_confidence": "normal",
        "mode": "server_assisted",
    }
    base.update(overrides)
    return base


def _make_consultation_event(**overrides: object) -> dict:
    """Minimal consultation_outcome event for planning tests."""
    base: dict = {
        "event": "consultation_outcome",
        "schema_version": "0.3.0",
        "consultation_id": "test-consult-001",
        "thread_id": None,
        "ts": "2026-03-17T10:00:00Z",
        "posture": "collaborative",
        "turn_count": 1,
        "turn_budget": 1,
        "termination_reason": "complete",
        "mode": "server_assisted",
    }
    base.update(overrides)
    return base


class TestComputePlanning:
    """Tests for _compute_planning section."""

    def test_no_planned_events(self) -> None:
        """Events without question_shaped return zero counts."""
        events = [_make_dialogue_event(), _make_consultation_event()]
        result = compute_stats._compute_planning(events, events[:1])
        assert result["plan_mode_total"] == 0
        assert result["no_plan_total"] == 2
        assert result["plan_mode_rate"] is None  # 0/0 undefined

    def test_planned_dialogue(self) -> None:
        """Dialogue with question_shaped=True counted in plan_mode."""
        planned = _make_dialogue_event(
            question_shaped=True,
            shape_confidence="high",
            assumptions_generated_count=3,
            ambiguity_count=1,
        )
        unplanned = _make_dialogue_event(consultation_id="test-002")
        result = compute_stats._compute_planning([planned, unplanned], [])
        assert result["plan_mode_dialogue_count"] == 1
        assert result["plan_mode_total"] == 1
        assert result["no_plan_total"] == 1

    def test_planned_consultation(self) -> None:
        """Consultation with question_shaped=True counted."""
        planned = _make_consultation_event(
            question_shaped=True,
            shape_confidence="medium",
            assumptions_generated_count=2,
            ambiguity_count=0,
        )
        result = compute_stats._compute_planning([], [planned])
        assert result["plan_mode_consultation_count"] == 1
        assert result["plan_mode_total"] == 1

    def test_shape_confidence_distribution(self) -> None:
        """shape_confidence_counts tallied across planned events."""
        events = [
            _make_dialogue_event(
                consultation_id=f"d-{i}",
                question_shaped=True,
                shape_confidence=conf,
                assumptions_generated_count=1,
                ambiguity_count=0,
            )
            for i, conf in enumerate(["high", "high", "medium", "low"])
        ]
        result = compute_stats._compute_planning(events, [])
        assert result["shape_confidence_counts"] == {"high": 2, "medium": 1, "low": 1}

    def test_avg_assumptions_and_ambiguity(self) -> None:
        """Averages computed across planned events only."""
        events = [
            _make_dialogue_event(
                consultation_id="d-1",
                question_shaped=True,
                shape_confidence="high",
                assumptions_generated_count=4,
                ambiguity_count=2,
            ),
            _make_dialogue_event(
                consultation_id="d-2",
                question_shaped=True,
                shape_confidence="high",
                assumptions_generated_count=6,
                ambiguity_count=0,
            ),
            _make_dialogue_event(consultation_id="d-3"),  # no plan
        ]
        result = compute_stats._compute_planning(events, [])
        assert result["avg_assumptions_generated"] == 5.0
        assert result["avg_ambiguity_count"] == 1.0

    def test_convergence_comparison(self) -> None:
        """Plan vs no-plan convergence rates for dialogues."""
        planned_converged = _make_dialogue_event(
            consultation_id="d-1",
            question_shaped=True, shape_confidence="high",
            assumptions_generated_count=2, ambiguity_count=0,
            converged=True,
        )
        planned_not = _make_dialogue_event(
            consultation_id="d-2",
            question_shaped=True, shape_confidence="medium",
            assumptions_generated_count=1, ambiguity_count=1,
            converged=False,
        )
        unplanned_converged = _make_dialogue_event(
            consultation_id="d-3", converged=True,
        )
        result = compute_stats._compute_planning(
            [planned_converged, planned_not, unplanned_converged], []
        )
        assert result["plan_convergence_rate"] == 0.5  # 1/2
        assert result["no_plan_convergence_rate"] == 1.0  # 1/1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestComputePlanning -v
```
Expected: FAIL — `_compute_planning` not found

- [ ] **Step 3: Add `_PLANNING_TEMPLATE` and `_compute_planning`**

Add the template after `_DELEGATION_TEMPLATE` (~line 119) in `compute_stats.py`:

```python
_PLANNING_TEMPLATE: dict = {
    "plan_mode_dialogue_count": 0,
    "plan_mode_consultation_count": 0,
    "plan_mode_total": 0,
    "no_plan_total": 0,
    "plan_mode_rate": None,
    "shape_confidence_counts": {},
    "avg_assumptions_generated": None,
    "avg_ambiguity_count": None,
    "plan_convergence_rate": None,
    "no_plan_convergence_rate": None,
}
```

Add the function after `_compute_delegation` (~line 355):

```python
def _compute_planning(
    dialogue_outcomes: list[dict],
    consultation_outcomes: list[dict],
) -> dict:
    """Compute planning effectiveness metrics.

    Consumes events where question_shaped is set (schema 0.3.0+).
    Compares convergence rates for planned vs unplanned dialogues.
    """
    result = copy.deepcopy(_PLANNING_TEMPLATE)

    all_events = dialogue_outcomes + consultation_outcomes
    planned: list[dict] = []
    unplanned: list[dict] = []

    for event in all_events:
        if event.get("question_shaped") is not None:
            planned.append(event)
        else:
            unplanned.append(event)

    plan_dialogues = [e for e in planned if e.get("event") == "dialogue_outcome"]
    plan_consultations = [e for e in planned if e.get("event") == "consultation_outcome"]

    result["plan_mode_dialogue_count"] = len(plan_dialogues)
    result["plan_mode_consultation_count"] = len(plan_consultations)
    result["plan_mode_total"] = len(planned)
    result["no_plan_total"] = len(unplanned)

    total = len(planned) + len(unplanned)
    if total > 0:
        result["plan_mode_rate"] = len(planned) / total

    # shape_confidence distribution across planned events
    conf_counts: dict[str, int] = {}
    for event in planned:
        conf = event.get("shape_confidence")
        if isinstance(conf, str):
            conf_counts[conf] = conf_counts.get(conf, 0) + 1
    result["shape_confidence_counts"] = conf_counts

    # Averages across planned events
    assumptions_vals = [
        event["assumptions_generated_count"]
        for event in planned
        if isinstance(event.get("assumptions_generated_count"), int)
    ]
    if assumptions_vals:
        result["avg_assumptions_generated"] = sum(assumptions_vals) / len(assumptions_vals)

    ambiguity_vals = [
        event["ambiguity_count"]
        for event in planned
        if isinstance(event.get("ambiguity_count"), int)
    ]
    if ambiguity_vals:
        result["avg_ambiguity_count"] = sum(ambiguity_vals) / len(ambiguity_vals)

    # Convergence comparison (dialogues only — consultations don't have converged field)
    planned_dialogues_with_conv = [
        e for e in plan_dialogues if isinstance(e.get("converged"), bool)
    ]
    unplanned_dialogues = [e for e in unplanned if e.get("event") == "dialogue_outcome"]
    unplanned_with_conv = [
        e for e in unplanned_dialogues if isinstance(e.get("converged"), bool)
    ]

    if planned_dialogues_with_conv:
        result["plan_convergence_rate"] = (
            sum(1 for e in planned_dialogues_with_conv if e["converged"])
            / len(planned_dialogues_with_conv)
        )
    if unplanned_with_conv:
        result["no_plan_convergence_rate"] = (
            sum(1 for e in unplanned_with_conv if e["converged"])
            / len(unplanned_with_conv)
        )

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestComputePlanning -v
```
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/compute_stats.py packages/plugins/cross-model/tests/test_compute_stats.py
git commit -m "feat: add planning effectiveness metrics (Track B, finding #2)

_compute_planning section: plan_mode counts/rate, shape_confidence
distribution, avg assumptions/ambiguity, plan vs no-plan convergence
rate comparison. Consumes schema 0.3.0 question_shaped events."
```

---

### Task 3: Provenance Health Metrics (Track B, Finding #3)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/compute_stats.py` (add template + function)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats.py` (add tests)

**Context:** `provenance_unknown_count` is set in `dialogue_outcome` events by the dialogue pipeline's Step 3h-bis provenance validation. It's non-negative int or `None` (when Step 3c fires — zero-output fallback). Schema version bumps to 0.2.0 when present (`event_schema.py:44`). `stats_common.safe_nonneg_int()` extracts it safely.

The 3-tier recovery in `codex-dialogue` (exact → component-boundary suffix → basename) runs in Step 4 of the agent's turn loop. `provenance_unknown_count` measures how many citations weren't matched by any tier — a degradation signal for gatherer quality.

- [ ] **Step 1: Write the failing tests**

Add to `test_compute_stats.py`:

```python
class TestComputeProvenance:
    """Tests for _compute_provenance section."""

    def test_no_provenance_events(self) -> None:
        """Events without provenance_unknown_count return defaults."""
        events = [_make_dialogue_event()]
        result = compute_stats._compute_provenance(events)
        assert result["provenance_observed_events"] == 0
        assert result["avg_provenance_unknown"] is None

    def test_zero_unknown_count(self) -> None:
        """provenance_unknown_count=0 means all citations matched."""
        events = [_make_dialogue_event(provenance_unknown_count=0)]
        result = compute_stats._compute_provenance(events)
        assert result["zero_unknown_count"] == 1
        assert result["provenance_observed_events"] == 1
        assert result["avg_provenance_unknown"] == 0.0

    def test_high_unknown_threshold(self) -> None:
        """provenance_unknown_count > 3 counted as high."""
        events = [
            _make_dialogue_event(consultation_id="d-1", provenance_unknown_count=5),
            _make_dialogue_event(consultation_id="d-2", provenance_unknown_count=2),
            _make_dialogue_event(consultation_id="d-3", provenance_unknown_count=0),
        ]
        result = compute_stats._compute_provenance(events)
        assert result["high_unknown_count"] == 1
        assert result["zero_unknown_count"] == 1
        assert result["avg_provenance_unknown"] == pytest.approx(7 / 3)

    def test_null_excluded_from_observed(self) -> None:
        """None provenance_unknown_count (3c path) excluded from observed."""
        events = [
            _make_dialogue_event(consultation_id="d-1", provenance_unknown_count=2),
            _make_dialogue_event(consultation_id="d-2"),  # None — 3c path
        ]
        result = compute_stats._compute_provenance(events)
        assert result["provenance_observed_events"] == 1
        assert result["provenance_missing_events"] == 1
        assert result["avg_provenance_unknown"] == 2.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestComputeProvenance -v
```
Expected: FAIL — `_compute_provenance` not found

- [ ] **Step 3: Add `_PROVENANCE_TEMPLATE` and `_compute_provenance`**

Template (after `_PLANNING_TEMPLATE`):

```python
_PROVENANCE_TEMPLATE: dict = {
    "avg_provenance_unknown": None,
    "zero_unknown_count": 0,
    "high_unknown_count": 0,
    "provenance_observed_events": 0,
    "provenance_missing_events": 0,
}
```

Function (after `_compute_planning`):

```python
def _compute_provenance(dialogue_outcomes: list[dict]) -> dict:
    """Compute provenance health metrics from dialogue outcomes.

    provenance_unknown_count tracks how many citations in the briefing
    weren't matched by the 3-tier recovery in codex-dialogue Step 4.
    None means Step 3c fired (zero-output fallback, provenance never ran).
    """
    result = copy.deepcopy(_PROVENANCE_TEMPLATE)

    observed: list[int] = []
    missing = 0

    for event in dialogue_outcomes:
        val = stats_common.safe_nonneg_int(event, "provenance_unknown_count")
        if val is not None:
            observed.append(val)
        else:
            missing += 1

    result["provenance_observed_events"] = len(observed)
    result["provenance_missing_events"] = missing

    if observed:
        result["avg_provenance_unknown"] = sum(observed) / len(observed)
        result["zero_unknown_count"] = sum(1 for v in observed if v == 0)
        result["high_unknown_count"] = sum(1 for v in observed if v > 3)

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestComputeProvenance -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/compute_stats.py packages/plugins/cross-model/tests/test_compute_stats.py
git commit -m "feat: add provenance health metrics (Track B, finding #3)

_compute_provenance section: avg unknown count, zero/high thresholds,
observed/missing event counts. Consumes provenance_unknown_count from
dialogue_outcome events (null = Step 3c path, excluded from avg)."
```

---

### Task 4: Parse Diagnostics Metrics (Track B, Finding #6)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/compute_stats.py` (add template + function)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats.py` (add tests)

**Context:** `parse_truncated` (unclosed fence block detected) and `parse_degraded` (epilogue parse failed, markdown regex fallback used) are booleans in `dialogue_outcome` events, set by `emit_analytics.py:468` and `:363`. When `parse_degraded=True`, the convergence code came from regex fallback (lower precision). These fields have no stats section.

- [ ] **Step 1: Write the failing tests**

Add to `test_compute_stats.py`:

```python
class TestComputeParseDiagnostics:
    """Tests for _compute_parse_diagnostics section."""

    def test_all_clean(self) -> None:
        events = [
            _make_dialogue_event(parse_truncated=False, parse_degraded=False),
            _make_dialogue_event(
                consultation_id="d-2",
                parse_truncated=False, parse_degraded=False,
            ),
        ]
        result = compute_stats._compute_parse_diagnostics(events)
        assert result["clean_count"] == 2
        assert result["truncated_count"] == 0
        assert result["degraded_count"] == 0
        assert result["observed_events"] == 2

    def test_truncated_and_degraded(self) -> None:
        events = [
            _make_dialogue_event(parse_truncated=True, parse_degraded=False),
            _make_dialogue_event(
                consultation_id="d-2",
                parse_truncated=False, parse_degraded=True,
            ),
            _make_dialogue_event(
                consultation_id="d-3",
                parse_truncated=True, parse_degraded=True,
            ),
        ]
        result = compute_stats._compute_parse_diagnostics(events)
        assert result["truncated_count"] == 2
        assert result["degraded_count"] == 2
        assert result["clean_count"] == 0  # none had both False

    def test_missing_fields_excluded(self) -> None:
        """Events without parse fields don't count as observed."""
        events = [
            _make_dialogue_event(parse_truncated=True, parse_degraded=False),
            _make_dialogue_event(consultation_id="d-2"),  # no parse fields
        ]
        result = compute_stats._compute_parse_diagnostics(events)
        assert result["observed_events"] == 1
        assert result["truncated_count"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestComputeParseDiagnostics -v
```
Expected: FAIL — `_compute_parse_diagnostics` not found

- [ ] **Step 3: Add `_PARSE_DIAGNOSTICS_TEMPLATE` and `_compute_parse_diagnostics`**

Template:

```python
_PARSE_DIAGNOSTICS_TEMPLATE: dict = {
    "truncated_count": 0,
    "degraded_count": 0,
    "clean_count": 0,
    "observed_events": 0,
}
```

Function:

```python
def _compute_parse_diagnostics(dialogue_outcomes: list[dict]) -> dict:
    """Compute parse diagnostics from dialogue outcomes.

    parse_truncated: True when an unclosed fence block is detected in synthesis.
    parse_degraded: True when epilogue parse failed and markdown regex fallback
    was used (lower precision for converged detection).
    """
    result = copy.deepcopy(_PARSE_DIAGNOSTICS_TEMPLATE)

    for event in dialogue_outcomes:
        truncated = event.get("parse_truncated")
        degraded = event.get("parse_degraded")

        # Only count events where at least one field is present as bool
        if not isinstance(truncated, bool) and not isinstance(degraded, bool):
            continue

        result["observed_events"] += 1
        t = truncated is True
        d = degraded is True

        if t:
            result["truncated_count"] += 1
        if d:
            result["degraded_count"] += 1
        if not t and not d:
            result["clean_count"] += 1

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestComputeParseDiagnostics -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/compute_stats.py packages/plugins/cross-model/tests/test_compute_stats.py
git commit -m "feat: add parse diagnostics metrics (Track B, finding #6)

_compute_parse_diagnostics section: truncated/degraded/clean counts.
Users can now detect when analytics data is degraded (epilogue parse
failed, regex fallback used with lower convergence precision)."
```

---

### Task 5: Wire Track B Sections into Section Matrix

**Files:**
- Modify: `packages/plugins/cross-model/scripts/compute_stats.py:362-368` (section matrix), `:407` (type literal), `:494-546` (compute function), `:576` (CLI choices)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats.py` (add integration tests)

**Context:** Three new sections need wiring: `planning`, `provenance`, `parse_diagnostics`. Add them to the matrix, the compute orchestrator, the output envelope, and the CLI.

- [ ] **Step 1: Write the failing integration test**

Add to `test_compute_stats.py`:

```python
class TestTrackBSectionWiring:
    """Integration tests for Track B section matrix wiring."""

    def test_all_includes_new_sections(self) -> None:
        """--type all includes planning, provenance, parse_diagnostics."""
        events = [_make_dialogue_event(
            question_shaped=True, shape_confidence="high",
            assumptions_generated_count=3, ambiguity_count=1,
            provenance_unknown_count=0,
            parse_truncated=False, parse_degraded=False,
        )]
        result = compute_stats.compute(events, 0, 0, "all")
        assert "planning" in result
        assert result["planning"]["plan_mode_total"] == 1
        assert "provenance" in result
        assert result["provenance"]["provenance_observed_events"] == 1
        assert "parse_diagnostics" in result
        assert result["parse_diagnostics"]["observed_events"] == 1

    def test_dialogue_type_includes_new_sections(self) -> None:
        """--type dialogue includes planning, provenance, parse_diagnostics."""
        result = compute_stats.compute([], 0, 0, "dialogue")
        assert "planning" in result
        assert "provenance" in result
        assert "parse_diagnostics" in result

    def test_consultation_type_includes_planning(self) -> None:
        """--type consultation includes planning but not provenance/parse."""
        result = compute_stats.compute([], 0, 0, "consultation")
        assert "planning" in result
        assert result["provenance"]["provenance_observed_events"] == 0  # zeroed
        assert result["parse_diagnostics"]["observed_events"] == 0  # zeroed

    def test_security_type_excludes_new_sections(self) -> None:
        """--type security excludes all new sections."""
        result = compute_stats.compute([], 0, 0, "security")
        assert result["planning"]["plan_mode_total"] == 0  # template default
        assert result["provenance"]["provenance_observed_events"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestTrackBSectionWiring -v
```
Expected: FAIL — `planning` key not in result

- [ ] **Step 3: Update `_SECTION_MATRIX`**

Replace `_SECTION_MATRIX` (lines 362-368):

```python
_SECTION_MATRIX: dict[str, dict[str, bool]] = {
    "all":          {"usage": True,  "dialogue": True,  "context": True,  "security": True,  "delegation": True,  "planning": True,  "provenance": True,  "parse_diagnostics": True},
    "dialogue":     {"usage": True,  "dialogue": True,  "context": True,  "security": False, "delegation": False, "planning": True,  "provenance": True,  "parse_diagnostics": True},
    "consultation": {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": False, "planning": True,  "provenance": False, "parse_diagnostics": False},
    "security":     {"usage": False, "dialogue": False, "context": False, "security": True,  "delegation": False, "planning": False, "provenance": False, "parse_diagnostics": False},
    "delegation":   {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": True,  "planning": False, "provenance": False, "parse_diagnostics": False},
}
```

Rationale: `planning` available under `dialogue` (most useful for plan-mode users), `consultation` (consultations also store planning fields), and `all`. Provenance and parse diagnostics are dialogue-only (consultation_outcome events don't have these fields).

- [ ] **Step 4: Update `compute()` to call new functions and include in envelope**

Add to the section-inclusion block (after the delegation section, ~line 525):

```python
    if matrix.get("planning"):
        planning_section = _compute_planning(dialogue_outcomes, consultation_outcomes)
    else:
        planning_section = copy.deepcopy(_PLANNING_TEMPLATE)

    if matrix.get("provenance"):
        provenance_section = _compute_provenance(dialogue_outcomes)
    else:
        provenance_section = copy.deepcopy(_PROVENANCE_TEMPLATE)

    if matrix.get("parse_diagnostics"):
        parse_diagnostics_section = _compute_parse_diagnostics(dialogue_outcomes)
    else:
        parse_diagnostics_section = copy.deepcopy(_PARSE_DIAGNOSTICS_TEMPLATE)
```

Add to the return dict (after `"delegation": delegation_section`):

```python
        "planning": planning_section,
        "provenance": provenance_section,
        "parse_diagnostics": parse_diagnostics_section,
```

- [ ] **Step 5: Run tests**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py -v
```
Expected: All tests pass (existing + new integration tests)

- [ ] **Step 6: Run full cross-model test suite to check for regressions**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/ -q
```
Expected: 629+ passed, 0 failed (legacy tests that assert on output shape may need fixture updates if they check exact keys)

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/compute_stats.py packages/plugins/cross-model/tests/test_compute_stats.py
git commit -m "feat: wire Track B sections into section matrix and output

planning, provenance, parse_diagnostics added to _SECTION_MATRIX.
planning included in dialogue+consultation+all types. provenance
and parse_diagnostics in dialogue+all only (dialogue-specific fields)."
```

---

### Task 6: Consultation Quality Metrics (Track E, Finding #7)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/compute_stats.py` (add template + function + matrix + wiring)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats.py` (add tests)

**Context:** `consultation_outcome` events (from `/codex` single-turn consultations) are the most-generated but least-measured event type. Currently `--type consultation` returns only the `usage` section. Track D added `thread_id` (string, nullable) to consultation_outcome — thread continuation means the same `thread_id` appears in multiple events within the period.

Available fields in `consultation_outcome`: `thread_id`, `turn_count`, `turn_budget`, `termination_reason`, `mode`, `posture`, plus planning fields from Task 2.

- [ ] **Step 1: Write the failing tests**

Add to `test_compute_stats.py`:

```python
class TestComputeConsultation:
    """Tests for _compute_consultation section (Track E #7)."""

    def test_empty(self) -> None:
        result = compute_stats._compute_consultation([])
        assert result["complete_count"] == 0
        assert result["thread_continuation_rate"] is None

    def test_basic_counts(self) -> None:
        events = [
            _make_consultation_event(termination_reason="complete"),
            _make_consultation_event(
                consultation_id="c-2",
                termination_reason="complete",
            ),
        ]
        result = compute_stats._compute_consultation(events)
        assert result["complete_count"] == 2

    def test_termination_distribution(self) -> None:
        events = [
            _make_consultation_event(termination_reason="complete"),
            _make_consultation_event(
                consultation_id="c-2", termination_reason="error",
            ),
        ]
        result = compute_stats._compute_consultation(events)
        assert result["termination_counts"] == {"complete": 1, "error": 1}

    def test_thread_continuation(self) -> None:
        """Thread continuation: same thread_id in 2+ events."""
        events = [
            _make_consultation_event(thread_id="thread-A"),
            _make_consultation_event(
                consultation_id="c-2", thread_id="thread-A",
            ),
            _make_consultation_event(
                consultation_id="c-3", thread_id="thread-B",
            ),
            _make_consultation_event(
                consultation_id="c-4", thread_id=None,
            ),
        ]
        result = compute_stats._compute_consultation(events)
        # 2 events have thread-A (continuation), 1 has thread-B (single), 1 is None
        # Continuation count: events with a continued thread_id = 2
        assert result["thread_continuation_count"] == 2
        # Rate: continued / events with non-null thread_id = 2/3
        assert result["thread_continuation_rate"] == pytest.approx(2 / 3)

    def test_posture_distribution(self) -> None:
        events = [
            _make_consultation_event(posture="adversarial"),
            _make_consultation_event(
                consultation_id="c-2", posture="collaborative",
            ),
            _make_consultation_event(
                consultation_id="c-3", posture="collaborative",
            ),
        ]
        result = compute_stats._compute_consultation(events)
        assert result["posture_counts"] == {"adversarial": 1, "collaborative": 2}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestComputeConsultation -v
```
Expected: FAIL

- [ ] **Step 3: Add `_CONSULTATION_TEMPLATE` and `_compute_consultation`**

Template:

```python
_CONSULTATION_TEMPLATE: dict = {
    "complete_count": 0,
    "termination_counts": {},
    "posture_counts": {},
    "thread_continuation_count": 0,
    "thread_continuation_rate": None,
}
```

Function:

```python
def _compute_consultation(consultation_outcomes: list[dict]) -> dict:
    """Compute single-turn consultation quality metrics.

    Thread continuation: a thread_id appearing in 2+ events indicates
    the user resumed a prior conversation. Rate is measured over events
    with non-null thread_id.
    """
    result = copy.deepcopy(_CONSULTATION_TEMPLATE)

    if not consultation_outcomes:
        return result

    # Termination distribution
    termination_counts: dict[str, int] = {}
    posture_counts: dict[str, int] = {}

    for event in consultation_outcomes:
        reason = event.get("termination_reason")
        if isinstance(reason, str):
            termination_counts[reason] = termination_counts.get(reason, 0) + 1
        if reason == "complete":
            result["complete_count"] += 1

        posture = event.get("posture")
        if isinstance(posture, str):
            posture_counts[posture] = posture_counts.get(posture, 0) + 1

    result["termination_counts"] = termination_counts
    result["posture_counts"] = posture_counts

    # Thread continuation
    thread_ids: dict[str, int] = {}
    for event in consultation_outcomes:
        tid = event.get("thread_id")
        if isinstance(tid, str):
            thread_ids[tid] = thread_ids.get(tid, 0) + 1

    continued_threads = {tid for tid, count in thread_ids.items() if count >= 2}
    events_with_tid = sum(thread_ids.values())
    continuation_events = sum(
        count for tid, count in thread_ids.items() if tid in continued_threads
    )

    result["thread_continuation_count"] = continuation_events
    if events_with_tid > 0:
        result["thread_continuation_rate"] = continuation_events / events_with_tid

    return result
```

- [ ] **Step 4: Wire into section matrix and compute()**

Update `_SECTION_MATRIX` — add `"consultation"` section column:

```python
_SECTION_MATRIX: dict[str, dict[str, bool]] = {
    "all":          {"usage": True,  "dialogue": True,  "context": True,  "security": True,  "delegation": True,  "planning": True,  "provenance": True,  "parse_diagnostics": True,  "consultation": True},
    "dialogue":     {"usage": True,  "dialogue": True,  "context": True,  "security": False, "delegation": False, "planning": True,  "provenance": True,  "parse_diagnostics": True,  "consultation": False},
    "consultation": {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": False, "planning": True,  "provenance": False, "parse_diagnostics": False, "consultation": True},
    "security":     {"usage": False, "dialogue": False, "context": False, "security": True,  "delegation": False, "planning": False, "provenance": False, "parse_diagnostics": False, "consultation": False},
    "delegation":   {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": True,  "planning": False, "provenance": False, "parse_diagnostics": False, "consultation": False},
}
```

Add to `compute()` section-inclusion block:

```python
    if matrix.get("consultation"):
        consultation_section = _compute_consultation(consultation_outcomes)
    else:
        consultation_section = copy.deepcopy(_CONSULTATION_TEMPLATE)
```

Add to return dict:

```python
        "consultation": consultation_section,
```

- [ ] **Step 5: Run all tests**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py -v
```
Expected: All pass

- [ ] **Step 6: Run full suite for regressions**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/ -q
```
Expected: 629+ passed, 0 failed

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/compute_stats.py packages/plugins/cross-model/tests/test_compute_stats.py
git commit -m "feat: add consultation quality metrics (Track E, finding #7)

_compute_consultation section: termination/posture distributions,
thread continuation rate. Now --type consultation shows meaningful
metrics beyond just usage counts."
```

---

### Task 7: Thread Discovery CLI (Track E, Finding #8)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/compute_stats.py` (add `_list_threads` function + CLI flag)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats.py` (add tests)

**Context:** `thread_id` is stored in `consultation_outcome` (Track D, string or null), `dialogue_outcome` (via pipeline), and `delegation_outcome` (required field). Users can't discover past thread IDs to resume consultations. This task adds `--threads` to list them.

- [ ] **Step 1: Write the failing tests**

Add to `test_compute_stats.py`:

```python
class TestListThreads:
    """Tests for _list_threads function."""

    def test_empty(self) -> None:
        result = compute_stats._list_threads([])
        assert result == []

    def test_groups_by_thread_id(self) -> None:
        events = [
            _make_consultation_event(
                thread_id="tid-A", ts="2026-03-17T10:00:00Z",
            ),
            _make_consultation_event(
                consultation_id="c-2",
                thread_id="tid-A", ts="2026-03-17T11:00:00Z",
            ),
            _make_dialogue_event(
                thread_id="tid-B", ts="2026-03-17T09:00:00Z",
            ),
        ]
        result = compute_stats._list_threads(events)
        assert len(result) == 2
        # Sorted by last_ts descending
        assert result[0]["thread_id"] == "tid-A"
        assert result[0]["event_count"] == 2
        assert result[0]["last_ts"] == "2026-03-17T11:00:00Z"
        assert result[1]["thread_id"] == "tid-B"
        assert result[1]["event_count"] == 1

    def test_null_thread_id_excluded(self) -> None:
        events = [
            _make_consultation_event(thread_id=None),
            _make_consultation_event(
                consultation_id="c-2", thread_id="tid-A",
            ),
        ]
        result = compute_stats._list_threads(events)
        assert len(result) == 1
        assert result[0]["thread_id"] == "tid-A"

    def test_event_types_collected(self) -> None:
        events = [
            _make_consultation_event(thread_id="tid-A"),
            _make_dialogue_event(thread_id="tid-A"),
        ]
        result = compute_stats._list_threads(events)
        assert set(result[0]["event_types"]) == {"consultation_outcome", "dialogue_outcome"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestListThreads -v
```
Expected: FAIL

- [ ] **Step 3: Add `_list_threads` function**

```python
def _list_threads(events: list[dict]) -> list[dict]:
    """List unique thread_ids across all structured events.

    Returns list of dicts sorted by last_ts descending:
    [{"thread_id": str, "event_count": int, "last_ts": str, "event_types": list[str]}]
    """
    threads: dict[str, dict] = {}

    for event in events:
        tid = event.get("thread_id")
        if not isinstance(tid, str):
            continue

        if tid not in threads:
            threads[tid] = {
                "thread_id": tid,
                "event_count": 0,
                "last_ts": "",
                "event_types": set(),
            }

        threads[tid]["event_count"] += 1
        ts = event.get("ts", "")
        if isinstance(ts, str) and ts > threads[tid]["last_ts"]:
            threads[tid]["last_ts"] = ts

        et = event.get("event", "")
        if isinstance(et, str):
            threads[tid]["event_types"].add(et)

    # Convert sets to sorted lists for JSON serialization
    result = []
    for info in threads.values():
        info["event_types"] = sorted(info["event_types"])
        result.append(info)

    # Sort by last_ts descending
    result.sort(key=lambda t: t["last_ts"], reverse=True)
    return result
```

- [ ] **Step 4: Add `--threads` flag to CLI**

In the `main()` function, add the argument after `--json`:

```python
    parser.add_argument(
        "--threads",
        action="store_true",
        default=False,
        help="List unique thread IDs instead of computing stats",
    )
```

Add the branch after `period_days` parsing, before the existing `try/except`:

```python
    if args.threads:
        try:
            events, _skipped = read_events.read_all(Path(args.path))
            period_days_val = stats_common.parse_period_days(args.period)
            if period_days_val > 0:
                now = datetime.now(timezone.utc)
                events = stats_common.filter_by_period(events, period_days_val, now).events
            result = _list_threads(events)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"thread listing failed: {exc}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))
        return
```

Note: requires importing `datetime` and `timezone` at the top of `main()` or ensuring they're already available. Check — `compute_stats.py` already imports `from datetime import datetime, timedelta, timezone` at the module level (used by `compute()`).

- [ ] **Step 5: Run tests**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestListThreads -v
```
Expected: 4 passed

- [ ] **Step 6: Manual CLI verification**

Run:
```bash
python3 packages/plugins/cross-model/scripts/compute_stats.py --threads --period all
```
Expected: JSON array of thread objects (may be empty if no events on this machine). Verify the output is valid JSON.

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/compute_stats.py packages/plugins/cross-model/tests/test_compute_stats.py
git commit -m "feat: add --threads CLI for thread discovery (Track E, finding #8)

_list_threads aggregates thread_ids across all event types with
count, last timestamp, and event type set. Supports --period
filtering. Enables users to discover past consultation threads
for resumption via codex-reply."
```

---

### Task 8: Reviewer Analytics Integration (Track E, Finding #9)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/event_schema.py:73-81` (add `consultation_source` to consultation_outcome)
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py` (add `consultation_source` field population)
- Modify: `packages/plugins/cross-model/agents/codex-reviewer.md` (add analytics emission step)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats.py` (add discriminator tests)
- Modify: `packages/plugins/cross-model/tests/test_compute_stats_legacy.py` (update consultation fixtures)

**Context:** `codex-reviewer.md` runs Codex consultations but emits no analytics events — it's invisible to stats. The agent has Bash + Read + Glob + Grep + MCP tools (no Write tool). To emit analytics, the agent must create a temp JSON file and call `emit_analytics.py`. Since it has Bash, it can use `echo` + heredoc to create the file.

The discriminator field `consultation_source` distinguishes interactive `/codex` consultations from automated reviewer consultations. This enables `_compute_consultation` to report reviewer usage separately.

**Decision point:** Adding `consultation_source` to `consultation_outcome` required fields means ALL consultation events must populate it. Existing events won't have it → validation fails. Two options:

**(A) Required field** — add to required set, emit_analytics always sets it. Existing events fail validation → excluded from stats (graceful degradation).
**(B) Optional field** — don't add to required set, just populate when available. No backward-compat issue.

**Recommended: (B) Optional field.** This avoids invalidating historical events. `_compute_consultation` checks for the field when present.

- [ ] **Step 1: Write the failing test for consultation_source handling**

Add to `test_compute_stats.py`:

```python
class TestConsultationSource:
    """Tests for consultation_source discriminator."""

    def test_source_distribution(self) -> None:
        events = [
            _make_consultation_event(consultation_source="codex"),
            _make_consultation_event(
                consultation_id="c-2", consultation_source="codex",
            ),
            _make_consultation_event(
                consultation_id="c-3", consultation_source="reviewer",
            ),
            _make_consultation_event(consultation_id="c-4"),  # no source (legacy)
        ]
        result = compute_stats._compute_consultation(events)
        assert result["source_counts"] == {
            "codex": 2, "reviewer": 1, "unknown": 1,
        }
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py::TestConsultationSource -v
```
Expected: FAIL — `source_counts` not in result

- [ ] **Step 3: Add `source_counts` to `_CONSULTATION_TEMPLATE` and `_compute_consultation`**

Add to template:

```python
    "source_counts": {},
```

Add to `_compute_consultation` function, inside the event loop:

```python
        source = event.get("consultation_source")
        source_key = source if isinstance(source, str) else "unknown"
        source_counts[source_key] = source_counts.get(source_key, 0) + 1
```

Initialize `source_counts: dict[str, int] = {}` before the loop, assign to `result["source_counts"]` after.

- [ ] **Step 4: Add `VALID_CONSULTATION_SOURCES` to `event_schema.py`**

Add after `VALID_TERMINATION_REASONS` (~line 147):

```python
VALID_CONSULTATION_SOURCES: frozenset[str] = frozenset({
    "codex",
    "dialogue",
    "reviewer",
})
"""Discriminator for consultation_outcome origin. Optional field — not
in required set to preserve backward compatibility with historical events."""
```

- [ ] **Step 5: Update `emit_analytics.py` to populate `consultation_source`**

In `build_consultation_outcome` (~line 494), add after `termination_reason`:

```python
        "consultation_source": pipeline.get("consultation_source", "codex"),
```

Default is `"codex"` — the `/codex` skill path. `/dialogue` sets it to `"dialogue"` and `codex-reviewer` to `"reviewer"`.

- [ ] **Step 6: Update `codex-reviewer.md` to emit analytics**

Add a Step 5 to the agent after synthesis (after the existing Step 4):

```markdown
## Step 5: Emit Analytics

After completing the review, emit a consultation_outcome event for analytics visibility:

```bash
TMPFILE=$(mktemp /tmp/codex-review-analytics-XXXXXX.json)
cat > "$TMPFILE" <<'ANALYTICS_EOF'
{
  "event_type": "consultation_outcome",
  "pipeline": {
    "posture": "{posture used}",
    "turn_count": {turn_count},
    "turn_budget": {turn_count},
    "thread_id": "{thread_id from codex-reply response, or null}",
    "termination_reason": "complete",
    "mode": "server_assisted",
    "consultation_source": "reviewer"
  }
}
ANALYTICS_EOF
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/emit_analytics.py" "$TMPFILE" 2>/dev/null || true
rm -f "$TMPFILE"
```

**Fail-soft:** The `|| true` ensures analytics failure doesn't block the review output. The `2>/dev/null` suppresses error output. If `emit_analytics.py` fails, the review still completes — analytics emission is observability, not correctness.

Do NOT emit analytics if the consultation was aborted (MCP tool unavailable, user cancelled).
```

Also add `Write` is NOT needed — the heredoc approach uses only Bash.

- [ ] **Step 7: Update consultation fixtures in `_legacy` tests**

In `test_compute_stats_legacy.py`, update `_make_consultation` factory to include `consultation_source`:

```python
        "consultation_source": "codex",
```

This ensures legacy tests don't break when the field is added. Check if any assertions compare exact event dicts — if so, add the field there too.

- [ ] **Step 8: Run tests**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/test_compute_stats.py -v
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/ -q
```
Expected: All pass

- [ ] **Step 9: Commit**

```bash
git add packages/plugins/cross-model/scripts/event_schema.py packages/plugins/cross-model/scripts/emit_analytics.py packages/plugins/cross-model/scripts/compute_stats.py packages/plugins/cross-model/agents/codex-reviewer.md packages/plugins/cross-model/tests/test_compute_stats.py packages/plugins/cross-model/tests/test_compute_stats_legacy.py
git commit -m "feat: add reviewer analytics integration (Track E, finding #9)

Add consultation_source discriminator (optional field, backward
compatible). codex-reviewer emits consultation_outcome events via
Bash heredoc. _compute_consultation reports source_counts distribution.
VALID_CONSULTATION_SOURCES enum in event_schema."
```

---

### Task 9: Full Verification and PR

**Files:** None (verification only)

- [ ] **Step 1: Run full cross-model package tests**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/ -v --tb=short
```
Expected: 629+ tests pass, 0 failures

- [ ] **Step 2: Run contract sync tests**

Run:
```bash
uv run pytest tests/test_consultation_contract_sync.py -v
```
Expected: 30 passed, 0 failed (the pre-existing failure is now fixed by Task 1)

- [ ] **Step 3: Run retrieval script to verify no regressions**

Run:
```bash
python3 packages/plugins/cross-model/scripts/retrieve_learnings.py --query "planning effectiveness" --max-entries 3
python3 packages/plugins/cross-model/scripts/compute_stats.py --period all --type all 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('Sections:', list(d.keys()))"
```
Expected: Retrieval returns entries. Stats output includes all new sections: `planning`, `provenance`, `parse_diagnostics`, `consultation`.

- [ ] **Step 4: Verify branch state**

Run:
```bash
git log --oneline HEAD --not main
```
Expected: 8 commits (Tasks 1-8)

- [ ] **Step 5: Create PR**

```bash
git push -u origin <branch-name>
gh pr create --title "feat: analytics coverage + capability completeness (Tracks B+E)" --body "$(cat <<'EOF'
## Summary

- Fix pre-existing `test_termination_reasons_match_contract` failure (import from leaf module)
- **Track B:** 3 new analytics sections — planning effectiveness (#2), provenance health (#3), parse diagnostics (#6)
- **Track E #7:** Consultation quality metrics with thread continuation rate
- **Track E #8:** `--threads` CLI for thread discovery
- **Track E #9:** Reviewer analytics integration with `consultation_source` discriminator

## Track B: Analytics Coverage

| Section | Key Metrics | Source Events |
|---------|-------------|---------------|
| `planning` | plan_mode rate, shape_confidence distribution, convergence comparison | dialogue + consultation |
| `provenance` | avg unknown count, zero/high thresholds | dialogue |
| `parse_diagnostics` | truncated/degraded/clean counts | dialogue |

## Track E: Capability Completeness

| Finding | Feature | Key Metrics |
|---------|---------|-------------|
| #7 | `consultation` section | termination/posture distribution, thread continuation rate |
| #8 | `--threads` CLI flag | Thread listing with event counts and types |
| #9 | Reviewer analytics | `consultation_source` discriminator, source_counts |

## Test plan

- [ ] 629+ cross-model package tests pass
- [ ] 30/30 contract sync tests pass (was 29/30 — pre-existing fix included)
- [ ] New sections appear in `--type all` output
- [ ] `--threads` returns valid JSON
- [ ] Legacy tests updated with new fixtures

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

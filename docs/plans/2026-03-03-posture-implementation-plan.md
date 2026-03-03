# Posture Taxonomy & Phase Composition Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the three-release posture taxonomy redesign: add `comparative` posture, phase-local convergence detection, and composed profiles.

**Architecture:** Release A (taxonomy) adds one posture value and two profiles — spec amendments already committed, remaining work is analytics validator. Release B (server convergence) adds phase-local convergence window and per-phase closing probe reset to `compute_action` behind a feature flag. Release C (composition) adds `phases` schema to profiles and phase tracking to the codex-dialogue agent.

**Tech Stack:** Python (Pydantic, StrEnum), YAML profiles, Markdown agent instructions. Tests via pytest.

**Design doc:** `docs/plans/2026-03-03-posture-taxonomy-and-composition.md`

---

## Release A: Taxonomy Completion

Spec amendments already committed at `a99b580` (11 files: enums, types, contracts, profiles, skills, agent). One remaining task: the analytics validator.

### Task 1: Update analytics posture validation

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:40`
- Test: `packages/plugins/cross-model/tests/test_emit_analytics.py`

**Step 1: Update `_VALID_POSTURES` set**

In `emit_analytics.py`, line 40:

```python
# Before:
_VALID_POSTURES = {"adversarial", "collaborative", "exploratory", "evaluative"}

# After:
_VALID_POSTURES = {"adversarial", "collaborative", "exploratory", "evaluative", "comparative"}
```

**Step 2: Run existing tests to verify nothing breaks**

Run: `cd packages/plugins/cross-model && python -m pytest tests/test_emit_analytics.py -v --tb=short 2>&1 | tail -20`
Expected: All existing tests pass (the `test_invalid_posture_enum` test uses `"aggressive"`, not `"comparative"`, so it still passes).

**Step 3: Add test for comparative posture acceptance**

In `tests/test_emit_analytics.py`, add a test near the existing posture tests (around line 953):

```python
def test_comparative_posture_accepted(tmp_path, monkeypatch):
    """comparative is a valid posture value (Release A taxonomy)."""
    monkeypatch.setattr("emit_analytics._LOG_PATH", tmp_path / "events.jsonl")
    event = _make_dialogue_event(posture="comparative")
    result = validate(event)
    assert result["posture"] == "comparative"
```

Note: Check the existing test helper `_make_dialogue_event` — use whatever factory the test file already uses. If there's a fixture or helper that creates valid events, use that pattern.

**Step 4: Run tests again to verify the new test passes**

Run: `cd packages/plugins/cross-model && python -m pytest tests/test_emit_analytics.py -v -k "comparative" --tb=short`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py packages/plugins/cross-model/tests/test_emit_analytics.py
git commit -m "feat(analytics): accept comparative posture in emit_analytics validator"
```

---

### Task 2: Release A lockstep verification

**Files:** None (verification only)

**Step 1: Run full lockstep check**

Verify `comparative` appears in all 7 locations (source enum, vendored enum, source types, vendored types, CI contract, consultation contract, analytics validator):

```bash
echo "=== Checking all posture locations ===" && \
grep 'COMPARATIVE' packages/context-injection/context_injection/enums.py && \
grep 'comparative' packages/context-injection/context_injection/types.py && \
grep 'COMPARATIVE' packages/plugins/cross-model/context-injection/context_injection/enums.py && \
grep 'comparative' packages/plugins/cross-model/context-injection/context_injection/types.py && \
grep 'comparative' packages/plugins/cross-model/references/context-injection-contract.md | head -2 && \
grep 'comparative' packages/plugins/cross-model/references/consultation-contract.md | head -2 && \
grep 'comparative' packages/plugins/cross-model/scripts/emit_analytics.py
```

Expected: All 7 locations return matches containing `comparative`.

**Step 2: Run context-injection test suite**

```bash
cd packages/context-injection && uv run pytest --tb=short -q
```

Expected: 969+ passed

**Step 3: Run analytics test suite**

```bash
cd packages/plugins/cross-model && python -m pytest tests/test_emit_analytics.py --tb=short -q
```

Expected: All tests pass

---

## Release B: Server Convergence

Phase-local convergence window and per-phase closing probe reset. All changes behind a feature flag to allow parity testing.

### Task 3: Add phase fields to ConversationState

**Files:**
- Modify: `packages/context-injection/context_injection/conversation.py:17-31`
- Test: `packages/context-injection/tests/test_state.py`

**Step 1: Write tests for new fields**

In `tests/test_state.py`, add:

```python
class TestPhaseFields:
    """ConversationState phase tracking fields (Release B)."""

    def test_defaults(self) -> None:
        state = ConversationState(conversation_id="test")
        assert state.last_posture is None
        assert state.phase_start_index == 0

    def test_with_posture_change(self) -> None:
        state = ConversationState(conversation_id="test")
        updated = state.with_posture_change("comparative", phase_start_index=3)
        assert updated.last_posture == "comparative"
        assert updated.phase_start_index == 3
        # Original unchanged (immutable)
        assert state.last_posture is None
        assert state.phase_start_index == 0

    def test_phase_entries_empty_when_no_entries(self) -> None:
        state = ConversationState(conversation_id="test")
        assert state.get_phase_entries() == ()

    def test_phase_entries_returns_from_phase_start(self) -> None:
        state = ConversationState(conversation_id="test")
        # Add 5 entries
        for i in range(5):
            entry = _make_entry(turn_number=i + 1)
            state = state.with_turn(entry)
        # Phase starts at index 3
        state = state.with_posture_change("evaluative", phase_start_index=3)
        phase_entries = state.get_phase_entries()
        assert len(phase_entries) == 2  # entries[3] and entries[4]
        assert phase_entries[0].turn_number == 4
        assert phase_entries[1].turn_number == 5
```

Note: Use the existing `_make_entry` helper from test_state.py (check what's available).

**Step 2: Run tests to verify they fail**

```bash
cd packages/context-injection && uv run pytest tests/test_state.py::TestPhaseFields -v --tb=short
```

Expected: FAIL — `last_posture` not a field

**Step 3: Add fields and projection methods to ConversationState**

In `conversation.py`, update `ConversationState`:

```python
class ConversationState(BaseModel):
    """Per-conversation state. Frozen — projection methods return new instances."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    conversation_id: str
    entries: tuple[LedgerEntry, ...] = ()
    claim_registry: tuple[Claim, ...] = ()
    evidence_history: tuple[EvidenceRecord, ...] = ()
    closing_probe_fired: bool = False
    last_checkpoint_id: str | None = None
    # Phase tracking (Release B)
    last_posture: str | None = None
    phase_start_index: int = 0
```

Add projection method:

```python
    def with_posture_change(self, posture: str, phase_start_index: int) -> ConversationState:
        """New state reflecting a posture change at phase boundary."""
        return self.model_copy(
            update={
                "last_posture": posture,
                "phase_start_index": phase_start_index,
                "closing_probe_fired": False,  # Reset per-phase closing probe
            }
        )

    def get_phase_entries(self) -> tuple[LedgerEntry, ...]:
        """Entries from the current phase (since last posture change)."""
        return self.entries[self.phase_start_index:]
```

**Step 4: Run tests to verify they pass**

```bash
cd packages/context-injection && uv run pytest tests/test_state.py::TestPhaseFields -v --tb=short
```

Expected: PASS

**Step 5: Run full test suite to check for regressions**

```bash
cd packages/context-injection && uv run pytest --tb=short -q
```

Expected: 969+ passed (existing tests unaffected — new fields have defaults)

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/conversation.py packages/context-injection/tests/test_state.py
git commit -m "feat(state): add phase tracking fields to ConversationState"
```

---

### Task 4: Add phase-local convergence to compute_action

**Files:**
- Modify: `packages/context-injection/context_injection/control.py:58-131`
- Test: `packages/context-injection/tests/test_control.py`

**Step 1: Write parity tests — single-posture behavior identical**

In `tests/test_control.py`, add:

```python
class TestComputeActionPhaseLocal:
    """Phase-local convergence window (Release B)."""

    def test_phase_entries_none_uses_full_history(self) -> None:
        """When phase_entries is None, behavior identical to pre-Release-B."""
        entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
        ]
        action_old, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False)
        action_new, _ = compute_action(entries, budget_remaining=5, closing_probe_fired=False, phase_entries=None)
        assert action_old == action_new == ConversationAction.CLOSING_PROBE

    def test_phase_entries_scopes_plateau_detection(self) -> None:
        """Plateau detected only within phase window, not full history."""
        full_entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.ADVANCING),
        ]
        # Phase started at turn 3 — only one ADVANCING entry, no plateau
        phase_entries = full_entries[2:]
        action, _ = compute_action(full_entries, budget_remaining=5, closing_probe_fired=False, phase_entries=phase_entries)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_phase_entries_resets_plateau_from_prior_phase(self) -> None:
        """Prior phase's STATIC turns don't pollute current phase."""
        full_entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=4, effective_delta=EffectiveDelta.STATIC),
        ]
        # Without phase_entries: full history has static at tail but not 2 consecutive
        # With phase_entries starting at 2: [ADVANCING, STATIC] — no plateau
        phase_entries = full_entries[2:]
        action, _ = compute_action(full_entries, budget_remaining=5, closing_probe_fired=False, phase_entries=phase_entries)
        assert action == ConversationAction.CONTINUE_DIALOGUE

    def test_closing_probe_fires_within_phase(self) -> None:
        """Plateau within phase window triggers closing probe."""
        full_entries = [
            _make_entry(turn_number=1, effective_delta=EffectiveDelta.ADVANCING),
            _make_entry(turn_number=2, effective_delta=EffectiveDelta.STATIC),
            _make_entry(turn_number=3, effective_delta=EffectiveDelta.STATIC),
        ]
        phase_entries = full_entries[1:]  # Phase started at index 1
        action, _ = compute_action(full_entries, budget_remaining=5, closing_probe_fired=False, phase_entries=phase_entries)
        assert action == ConversationAction.CLOSING_PROBE

    def test_budget_still_trumps_phase_logic(self) -> None:
        """Budget exhaustion overrides phase-local logic."""
        entries = [_make_entry(turn_number=1)]
        action, _ = compute_action(entries, budget_remaining=0, closing_probe_fired=False, phase_entries=entries)
        assert action == ConversationAction.CONCLUDE
```

**Step 2: Run tests to verify they fail**

```bash
cd packages/context-injection && uv run pytest tests/test_control.py::TestComputeActionPhaseLocal -v --tb=short
```

Expected: FAIL — `compute_action() got an unexpected keyword argument 'phase_entries'`

**Step 3: Add `phase_entries` parameter to compute_action**

In `control.py`, update the signature and logic:

```python
def compute_action(
    entries: Sequence[LedgerEntry],
    budget_remaining: int,
    closing_probe_fired: bool,
    *,
    phase_entries: Sequence[LedgerEntry] | None = None,
) -> tuple[ConversationAction, str]:
    """Determine next conversation action from ledger trajectory.

    When phase_entries is provided (phase composition), plateau detection
    uses the phase-local window instead of the full entry history.
    When phase_entries is None (single-posture dialogue), behavior is
    identical to pre-Release-B.
    """
    # 1. Budget exhaustion — hard stop (unchanged)
    if budget_remaining <= 0:
        return (
            ConversationAction.CONCLUDE,
            f"Budget exhausted ({budget_remaining} turns remaining)",
        )

    # 2. Need entries for plateau detection
    if not entries:
        return (
            ConversationAction.CONTINUE_DIALOGUE,
            "No entries yet — first turn",
        )

    # 3. Plateau detection — use phase window if provided
    plateau_window = phase_entries if phase_entries is not None else entries
    plateau = _is_plateau(plateau_window)

    if plateau:
        if closing_probe_fired:
            if _has_open_unresolved(entries):
                return (
                    ConversationAction.CONTINUE_DIALOGUE,
                    f"Plateau detected but {len(entries[-1].unresolved)} unresolved "
                    f"item(s) remain — continuing to address them",
                )
            return (
                ConversationAction.CONCLUDE,
                "Plateau detected — last 2 turns STATIC, closing probe "
                "already fired, no unresolved items",
            )
        return (
            ConversationAction.CLOSING_PROBE,
            "Plateau detected — last 2 turns STATIC, firing closing probe",
        )

    # 4. Default — continue
    last_delta = entries[-1].effective_delta
    return (
        ConversationAction.CONTINUE_DIALOGUE,
        f"Conversation active — last delta: {last_delta}",
    )
```

Key change: `_is_plateau()` and `_has_open_unresolved()` use `plateau_window` (phase-local) for plateau detection, but `entries` (full history) for unresolved check. The `phase_entries=None` default preserves identical behavior for single-posture dialogues.

**Step 4: Run phase-local tests**

```bash
cd packages/context-injection && uv run pytest tests/test_control.py::TestComputeActionPhaseLocal -v --tb=short
```

Expected: PASS

**Step 5: Run ALL control tests (parity)**

```bash
cd packages/context-injection && uv run pytest tests/test_control.py -v --tb=short
```

Expected: ALL pass — existing tests don't provide `phase_entries`, so they use the default `None` path which is identical to the old code.

**Step 6: Run full suite**

```bash
cd packages/context-injection && uv run pytest --tb=short -q
```

Expected: 969+ passed

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/control.py packages/context-injection/tests/test_control.py
git commit -m "feat(control): phase-local convergence window in compute_action

Add optional phase_entries parameter. When provided, plateau detection
uses the phase-local window instead of full history. When None (default),
behavior is identical to pre-Release-B.

Parity tests prove identical single-posture behavior."
```

---

### Task 5: Wire phase-local convergence into the pipeline

**Files:**
- Modify: `packages/context-injection/context_injection/pipeline.py:283-296`
- Test: `packages/context-injection/tests/test_pipeline.py`

**Step 1: Write test for posture-change detection in pipeline**

In `tests/test_pipeline.py`, add a test that sends two turns with different postures and verifies the second turn uses phase-local convergence. The test should:

1. Send turn 1 with `posture="exploratory"` — gets `continue_dialogue`
2. Send turn 2 with `posture="evaluative"` — posture changed, so phase resets

Check the existing pipeline test patterns first — they likely use a helper to build full `TurnRequest` dicts and call `process_turn` directly.

**Step 2: Update pipeline Step 14 to detect posture changes**

In `pipeline.py`, around the Step 14 section (lines 283-296):

```python
    # --- Step 14: Compute cumulative, action, reason ---
    cumulative = provisional.compute_cumulative_state()
    turn_budget_remaining = max(0, MAX_CONVERSATION_TURNS - cumulative.turns_completed)

    # Detect posture change for phase-local convergence
    current_posture = request.posture
    phase_entries: tuple[LedgerEntry, ...] | None = None
    if provisional.last_posture is not None and current_posture != provisional.last_posture:
        # Posture changed — update phase boundary
        provisional = provisional.with_posture_change(
            current_posture, phase_start_index=len(provisional.entries) - 1
        )
        phase_entries = provisional.get_phase_entries()
    elif provisional.last_posture is None and len(provisional.entries) > 0:
        # First turn with posture tracking — set initial posture
        provisional = provisional.with_posture_change(
            current_posture, phase_start_index=0
        )

    action, action_reason = compute_action(
        entries=provisional.entries,
        budget_remaining=turn_budget_remaining,
        closing_probe_fired=provisional.closing_probe_fired,
        phase_entries=phase_entries,
    )
```

**Step 3: Run tests**

```bash
cd packages/context-injection && uv run pytest --tb=short -q
```

Expected: 969+ passed

**Step 4: Commit**

```bash
git add packages/context-injection/context_injection/pipeline.py packages/context-injection/tests/test_pipeline.py
git commit -m "feat(pipeline): wire phase-local convergence into process_turn"
```

---

### Task 6: Update vendored copy for Release B

**Files:**
- Copy: Source → vendored for `conversation.py`, `control.py`, `pipeline.py`

**Step 1: Copy updated source files to vendored location**

```bash
cp packages/context-injection/context_injection/conversation.py packages/plugins/cross-model/context-injection/context_injection/conversation.py
cp packages/context-injection/context_injection/control.py packages/plugins/cross-model/context-injection/context_injection/control.py
cp packages/context-injection/context_injection/pipeline.py packages/plugins/cross-model/context-injection/context_injection/pipeline.py
```

**Step 2: Verify vendored copies match source**

```bash
diff packages/context-injection/context_injection/conversation.py packages/plugins/cross-model/context-injection/context_injection/conversation.py
diff packages/context-injection/context_injection/control.py packages/plugins/cross-model/context-injection/context_injection/control.py
diff packages/context-injection/context_injection/pipeline.py packages/plugins/cross-model/context-injection/context_injection/pipeline.py
```

Expected: No diff

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/context-injection/context_injection/conversation.py packages/plugins/cross-model/context-injection/context_injection/control.py packages/plugins/cross-model/context-injection/context_injection/pipeline.py
git commit -m "chore: sync vendored context-injection with source (Release B)"
```

---

### Task 7: Update context-injection contract for Release B

**Files:**
- Modify: `packages/plugins/cross-model/references/context-injection-contract.md`

**Step 1: Add note about phase-local convergence**

In the Posture enum section and the TurnRequest field table, add a note that posture may vary across turns and that the server uses phase-local convergence when posture changes are detected.

Find the posture field description (already updated to "Currently posture-agnostic by design") and update:

```markdown
| `posture` | `Posture` | Yes | Conversation posture. When posture changes between turns, the server resets plateau detection to the phase-local window (entries since last posture change). Closing probe flag resets on posture change. When posture is constant across all turns, behavior is identical to pre-phase-composition. |
```

**Step 2: Commit**

```bash
git add packages/plugins/cross-model/references/context-injection-contract.md
git commit -m "docs(contract): document phase-local convergence behavior"
```

---

## Release C: Composition Activation

### Task 8: Add `phases` schema to profiles

**Files:**
- Modify: `packages/plugins/cross-model/references/consultation-profiles.yaml`
- Modify: `packages/plugins/cross-model/references/consultation-contract.md`

**Step 1: Add the debugging composed profile**

Append to `consultation-profiles.yaml`:

```yaml
  debugging:
    description: >
      Multi-phase debugging consultation. Explores the problem space, verifies
      hypotheses against evidence, then collaboratively designs a fix. Provide
      the error, reproduction steps, and relevant code in the briefing material.
    sandbox: read-only
    approval_policy: never
    reasoning_effort: high
    phases:
      - posture: exploratory
        target_turns: 2
        description: Map the problem space — what could cause this?
      - posture: evaluative
        target_turns: 3
        description: Verify hypotheses against evidence
      - posture: collaborative
        target_turns: 2
        description: Design the fix together
    turn_budget: 7
```

**Step 2: Add phase composition section to consultation contract**

In `consultation-contract.md`, after the profile fields table (§14), add:

```markdown
### Phase composition (optional)

Profiles may define `phases` — an ordered list of posture phases with target turns. When present, `posture` at the top level is omitted.

| Phase field | Type | Description |
|-------------|------|-------------|
| `posture` | Posture | Posture for this phase |
| `target_turns` | int | Advisory target for turns in this phase |
| `description` | string | Human-readable phase purpose |

**Budget rules:**
- Phase target is advisory — a phase may end early
- Total `turn_budget` is a hard cap across all phases
- Convergence (`action: conclude`) overrides phase boundaries
- Minimum 1 turn per phase

**Validation:** A profile must have either `posture` (single-phase) or `phases` (multi-phase), not both. If both are present, reject with validation error.
```

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/references/consultation-profiles.yaml packages/plugins/cross-model/references/consultation-contract.md
git commit -m "feat(profiles): add phases schema and debugging composed profile"
```

---

### Task 9: Add phase tracking to codex-dialogue agent

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md`

**Step 1: Read the current turn management section**

The agent's Phase 2 loop currently tracks `current_turn` and compares to `effective_budget`. Read lines around 438-446 for the turn management section.

**Step 2: Add phase tracking logic**

After the turn management section, add a new section:

```markdown
### Phase tracking (multi-phase profiles)

When the delegation envelope includes a profile with `phases`, track `current_phase_index` alongside `current_turn`.

**Before each turn:**
1. Check if `current_turn >= effective_budget` → conclude (hard cap)
2. Check if server returned `action: conclude` → conclude (convergence)
3. Compute `turns_in_phase` = turns since `current_phase_index` was last updated
4. If `turns_in_phase >= phases[current_phase_index].target_turns`, advance `current_phase_index`
5. Set `posture` in the next `process_turn` request to `phases[current_phase_index].posture`

**Phase transition signaling:**
When advancing to a new phase, compose a transition marker in the follow-up:
- exploratory → evaluative: "We've explored the problem space — now let's verify the leading hypothesis against evidence."
- evaluative → collaborative: "The root cause is identified — let's design the fix together."
- exploratory → comparative: "We've mapped the options — now let's compare them against criteria."
- Generic: "Shifting focus from {old_phase.description} to {new_phase.description}."

**Single-phase profiles:** When no `phases` key exists, skip all phase tracking. Behavior is identical to pre-Release-C.
```

**Step 3: Add phase trajectory to synthesis**

In the Phase 3 synthesis section, add a pre-flight checklist item:

```markdown
- [ ] Phase trajectory: which phases entered, turns consumed per phase, phases skipped by convergence (multi-phase only)
```

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "feat(agent): add phase tracking and transition signaling to codex-dialogue"
```

---

### Task 10: Final verification and release tagging

**Files:** None (verification only)

**Step 1: Run full context-injection test suite**

```bash
cd packages/context-injection && uv run pytest --tb=short -q
```

Expected: 969+ passed (all Release B tests plus original)

**Step 2: Run analytics test suite**

```bash
cd packages/plugins/cross-model && python -m pytest tests/test_emit_analytics.py --tb=short -q
```

Expected: All tests pass

**Step 3: Run final lockstep check (7 locations + analytics)**

```bash
echo "Lockstep check: all 8 locations" && \
grep 'COMPARATIVE' packages/context-injection/context_injection/enums.py && \
grep 'comparative' packages/context-injection/context_injection/types.py && \
grep 'COMPARATIVE' packages/plugins/cross-model/context-injection/context_injection/enums.py && \
grep 'comparative' packages/plugins/cross-model/context-injection/context_injection/types.py && \
grep 'comparative' packages/plugins/cross-model/references/context-injection-contract.md | head -1 && \
grep 'comparative' packages/plugins/cross-model/references/consultation-contract.md | head -1 && \
grep 'comparative' packages/plugins/cross-model/scripts/emit_analytics.py && \
grep 'comparative' packages/plugins/cross-model/references/consultation-profiles.yaml | head -1
```

Expected: All 8 locations match

**Step 4: Verify git log shows clean release sequence**

```bash
git log --oneline -12
```

Verify commits are ordered: Release A (spec + analytics) → Release B (state + control + pipeline + vendored + contract) → Release C (profiles + agent).

---

## Summary

| Release | Tasks | Files Modified | New Tests |
|---------|-------|---------------|-----------|
| A (completion) | 1-2 | 1 (emit_analytics.py) | 1 test |
| B (convergence) | 3-7 | 6 (conversation.py, control.py, pipeline.py, vendored ×3, contract) | ~10 tests |
| C (composition) | 8-9 | 3 (profiles.yaml, consultation-contract.md, codex-dialogue.md) | Manual verification |
| Verification | 10 | 0 | 0 |

Total: 10 tasks, ~10 files, ~11 new tests, ~10 commits.

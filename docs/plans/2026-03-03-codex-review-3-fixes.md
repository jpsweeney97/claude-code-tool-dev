# Codex Review #3 Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all findings from Codex review #3 — 2 doc fixes, agent spec fix, phase delegation wiring, and 6 test coverage gaps — before merging `feature/cross-model-plugin` to `main`.

**Architecture:** Three categories of work: (1) doc/spec fixes (F1, F2), (2) phase delegation wiring (F3) across the `/dialogue` SKILL.md and `codex-dialogue.md` agent, (3) test hardening (P1–P6). All work happens in the existing worktree at `.worktrees/cross-model-plugin/` on branch `feature/cross-model-plugin`.

**Tech Stack:** Python (Pydantic, pytest), Markdown (agent specs, contract docs, skill files)

**Worktree:** `.worktrees/cross-model-plugin/` on `feature/cross-model-plugin` (12 existing commits)

**Test commands:**
- Context-injection: `cd packages/context-injection && uv run pytest`
- Analytics: `cd packages/plugins/cross-model && uv run pytest tests/`
- Single test: `cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestPipelinePhaseLocal::test_name -v`

---

## Task 1: Fix contract one-shot policy description (F1)

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/plugins/cross-model/references/context-injection-contract.md:736`
- Modify: `.worktrees/cross-model-plugin/packages/context-injection/context_injection/control.py:72-77`
- Modify (vendored): `.worktrees/cross-model-plugin/packages/plugins/cross-model/context-injection/context_injection/control.py:72-77`

**Step 1: Update contract line 736**

Replace the current one-shot policy description:

```
**One-shot policy:** A closing probe fires at most once per conversation. If the conversation resumes after a closing probe (plateau broken by ADVANCING/SHIFTING), a second plateau skips the probe and proceeds directly to `conclude`.
```

With:

```
**Closing probe policy:** A closing probe fires at most once *per phase*. When posture changes (phase boundary), `closing_probe_fired` resets — the new phase gets its own probe opportunity. Within a single phase, if the conversation resumes after a closing probe (plateau broken by ADVANCING/SHIFTING), a second plateau skips the probe and proceeds directly to `conclude`. In single-posture conversations (no phase changes), this is equivalent to once-per-conversation.
```

**Step 2: Update compute_action docstring at control.py:72-77**

Replace:

```python
    Design decision — one-shot closing probe policy:
        A closing probe fires at most once per conversation. If the conversation
        advances after a closing probe (plateau broken by ADVANCING/SHIFTING),
        a second plateau will skip the probe and proceed directly to CONCLUDE.
        Rationale: repeated probes add latency without new information — if the
        first probe did not surface actionable material, a second will not either.
```

With:

```python
    Design decision — closing probe policy (once per phase):
        A closing probe fires at most once per phase. When posture changes
        (phase boundary), closing_probe_fired resets — the new phase gets its
        own probe opportunity. Within a single phase, if the conversation
        advances after a closing probe (plateau broken by ADVANCING/SHIFTING),
        a second plateau skips the probe and proceeds directly to CONCLUDE.
        In single-posture conversations, this is equivalent to once per
        conversation.
```

**Step 3: Sync vendored control.py**

```bash
cp packages/context-injection/context_injection/control.py packages/plugins/cross-model/context-injection/context_injection/control.py
```

Verify: `diff packages/context-injection/context_injection/control.py packages/plugins/cross-model/context-injection/context_injection/control.py`

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/references/context-injection-contract.md \
       packages/context-injection/context_injection/control.py \
       packages/plugins/cross-model/context-injection/context_injection/control.py
git commit -m "docs(contract): fix closing probe policy — once per phase, not per conversation"
```

---

## Task 2: Fix agent phase transition timing (F2)

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/plugins/cross-model/agents/codex-dialogue.md:455-473`

**Step 1: Replace phase tracking section**

Replace lines 455-473 (the current "Phase tracking (multi-phase profiles)" section) with:

```markdown
### Phase tracking (multi-phase profiles)

When the delegation envelope includes `phases` (a list of phase objects with `posture`, `target_turns`, `description`), track phase progression alongside the turn loop.

**Additional state:**

| State | Initial value | Purpose |
|-------|--------------|---------|
| `current_phase_index` | `0` | Index into `phases` array |
| `phase_turns_completed` | `0` | Turns completed in the current phase |

**Phase advancement (after Step 3, before Step 5 follow-up):**

After each successful `process_turn` response (Step 3), before composing the follow-up (Step 5):

1. Increment `phase_turns_completed`
2. If `phase_turns_completed >= phases[current_phase_index].target_turns` AND `current_phase_index < len(phases) - 1`:
   - Advance: `current_phase_index += 1`, `phase_turns_completed = 0`
   - Compose a transition marker in the follow-up (see below)
3. Set `posture` for the next `process_turn` call to `phases[current_phase_index].posture`

**Hard cap precedence:** Budget exhaustion (`current_turn >= effective_budget`) and server `conclude` always take precedence over phase advancement. Check both before evaluating phase advancement.

**Last phase exhaustion:** When `phase_turns_completed >= target_turns` on the *last* phase (`current_phase_index == len(phases) - 1`), do not advance — remain in the last phase. The server's convergence detection or budget cap terminates the conversation.

**Phase transition signaling:**
When advancing to a new phase, compose a transition marker in the follow-up:
- exploratory -> evaluative: "We've explored the problem space — now let's verify the leading hypothesis against evidence."
- evaluative -> collaborative: "The root cause is identified — let's design the fix together."
- exploratory -> comparative: "We've mapped the options — now let's compare them against criteria."
- Generic: "Shifting focus from {old_phase.description} to {new_phase.description}."

**Single-phase profiles:** When no `phases` key exists in the delegation envelope, skip all phase tracking. Behavior is identical to pre-Release-C.
```

**Step 2: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "fix(agent): explicit phase_turns_completed counter for unambiguous transition timing"
```

---

## Task 3: Wire phase delegation in /dialogue SKILL.md (F3)

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/plugins/cross-model/skills/dialogue/SKILL.md:66-68` (flag table)
- Modify: `.worktrees/cross-model-plugin/packages/plugins/cross-model/skills/dialogue/SKILL.md:310-325` (Step 5 delegation template)

**Step 1: Update argument parsing — profile resolution**

In the flag table near line 66, update the description for `--profile`:

Current:
```
| `--profile` | — | Named preset from [`consultation-profiles.yaml`](../../references/consultation-profiles.yaml) | none |
```

No change needed here — profiles already resolve all fields. The resolution order already says "explicit flags > profile values > defaults."

**Step 2: Update Step 5 delegation template**

Replace lines 310-325 (the Task template):

```
Task(
  subagent_type: "cross-model:codex-dialogue",
  description: "Run Codex dialogue on question",
  prompt: """
    Goal: {user's question}
    Posture: {resolved posture}
    Budget: {resolved turn count}
    seed_confidence: {normal or low}
    reasoning_effort: {resolved from profile or contract default}
    scope_envelope: {scope from §3 preflight — allowed roots and source classes}

    {assembled briefing with sentinel}
  """
)
```

With:

```
Task(
  subagent_type: "cross-model:codex-dialogue",
  description: "Run Codex dialogue on question",
  prompt: """
    Goal: {user's question}
    Posture: {resolved posture — omit if phases is set}
    Phases: {resolved phases array from profile — omit if single-posture}
    Budget: {resolved turn count}
    seed_confidence: {normal or low}
    reasoning_effort: {resolved from profile or contract default}
    scope_envelope: {scope from §3 preflight — allowed roots and source classes}

    {assembled briefing with sentinel}
  """
)
```

**Step 3: Add phase delegation documentation after the template**

After the existing `reasoning_effort` resolution paragraph (line 327), add:

```markdown
**Phase delegation:** When the resolved profile contains `phases` (multi-phase profile), pass the `phases` array in the delegation envelope and omit `Posture`. The `codex-dialogue` agent reads `phases` to drive phase progression. When the profile has a single `posture` (no `phases` key), pass `Posture` and omit `Phases`. The agent detects which field is present and behaves accordingly.

**Phase validation at delegation time:** Before delegating a multi-phase profile, verify:
1. `phases` is a non-empty list
2. Each phase has `posture`, `target_turns` (int >= 1), and `description` (string)
3. Adjacent phases have distinct postures (same-posture consecutive phases silently merge at the server)
4. Sum of `target_turns` across phases does not exceed `turn_budget`

If validation fails, report the error to the user and do not delegate.
```

**Step 4: Update the codex-dialogue agent to parse phases from delegation envelope**

In `.worktrees/cross-model-plugin/packages/plugins/cross-model/agents/codex-dialogue.md`, update the "Parse the prompt" table (around line 36-45) to add `Phases`:

Add after the `Posture` row:

```markdown
| Phases | No | Ordered list of phase objects (`{posture, target_turns, description}`). Mutually exclusive with `Posture`. When present, the agent drives phase transitions per the "Phase tracking" section. |
```

**Step 5: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md \
       packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "feat(dialogue): wire phase delegation — pass phases array to codex-dialogue agent"
```

---

## Task 4: Test P1 — Pipeline closing probe -> phase change -> second probe (highest priority)

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/context-injection/tests/test_pipeline.py`

**Step 1: Write the failing test**

Add to `TestPipelinePhaseLocal`:

```python
def test_closing_probe_fires_again_after_phase_change(self) -> None:
    """Full once-per-phase path: probe fires in phase 1, phase changes,
    probe fires again in phase 2.
    """
    ctx = _make_ctx(git_files=set())
    # T1: exploratory STATIC
    r1 = _make_turn_request(
        conversation_id="conv_reprobe",
        turn_number=1,
        posture="exploratory",
        delta="static",
        claims=_static_claims(1),
    )
    res1 = process_turn(r1, ctx)
    assert res1.status == "success"

    # T2: exploratory STATIC -> plateau -> CLOSING_PROBE
    r2 = _make_turn_request(
        conversation_id="conv_reprobe",
        turn_number=2,
        posture="exploratory",
        delta="static",
        claims=_static_claims(2),
        state_checkpoint=res1.state_checkpoint,
        checkpoint_id=res1.checkpoint_id,
    )
    res2 = process_turn(r2, ctx)
    assert res2.action == ConversationAction.CLOSING_PROBE

    # T3: evaluative ADVANCING -> new phase, probe reset
    r3 = _make_turn_request(
        conversation_id="conv_reprobe",
        turn_number=3,
        posture="evaluative",
        delta="advancing",
        state_checkpoint=res2.state_checkpoint,
        checkpoint_id=res2.checkpoint_id,
    )
    res3 = process_turn(r3, ctx)
    assert res3.action == ConversationAction.CONTINUE_DIALOGUE

    # T4: evaluative STATIC
    r4 = _make_turn_request(
        conversation_id="conv_reprobe",
        turn_number=4,
        posture="evaluative",
        delta="static",
        claims=_static_claims(4),
        state_checkpoint=res3.state_checkpoint,
        checkpoint_id=res3.checkpoint_id,
    )
    res4 = process_turn(r4, ctx)
    assert res4.status == "success"

    # T5: evaluative STATIC -> plateau in phase 2 -> CLOSING_PROBE again
    r5 = _make_turn_request(
        conversation_id="conv_reprobe",
        turn_number=5,
        posture="evaluative",
        delta="static",
        claims=_static_claims(5),
        state_checkpoint=res4.state_checkpoint,
        checkpoint_id=res4.checkpoint_id,
    )
    res5 = process_turn(r5, ctx)
    assert res5.action == ConversationAction.CLOSING_PROBE
```

**Step 2: Run test to verify it passes**

```bash
cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestPipelinePhaseLocal::test_closing_probe_fires_again_after_phase_change -v
```

Expected: PASS (the implementation already supports this — the test is a coverage gap, not a code gap).

**Step 3: Commit**

```bash
git add packages/context-injection/tests/test_pipeline.py
git commit -m "test(pipeline): P1 — closing probe fires again after phase change"
```

---

## Task 5: Test P2 — A->B->A posture flip

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/context-injection/tests/test_pipeline.py`

**Step 1: Write the test**

Add to `TestPipelinePhaseLocal`:

```python
def test_posture_flip_a_b_a_resets_phase_window(self) -> None:
    """A->B->A posture flip: return to a prior posture creates a new phase,
    not a resumption of the original phase.
    """
    ctx = _make_ctx(git_files=set())
    # T1: exploratory STATIC
    r1 = _make_turn_request(
        conversation_id="conv_flip",
        turn_number=1,
        posture="exploratory",
        delta="static",
        claims=_static_claims(1),
    )
    res1 = process_turn(r1, ctx)
    assert res1.status == "success"

    # T2: evaluative STATIC -> new phase (1 entry), no plateau
    r2 = _make_turn_request(
        conversation_id="conv_flip",
        turn_number=2,
        posture="evaluative",
        delta="static",
        claims=_static_claims(2),
        state_checkpoint=res1.state_checkpoint,
        checkpoint_id=res1.checkpoint_id,
    )
    res2 = process_turn(r2, ctx)
    assert res2.action == ConversationAction.CONTINUE_DIALOGUE

    # T3: exploratory STATIC -> new phase again (1 entry), no plateau
    # This is the key assertion: returning to exploratory does NOT resume
    # the prior exploratory phase (which had 1 STATIC). It starts fresh.
    r3 = _make_turn_request(
        conversation_id="conv_flip",
        turn_number=3,
        posture="exploratory",
        delta="static",
        claims=_static_claims(3),
        state_checkpoint=res2.state_checkpoint,
        checkpoint_id=res2.checkpoint_id,
    )
    res3 = process_turn(r3, ctx)
    assert res3.action == ConversationAction.CONTINUE_DIALOGUE

    # T4: exploratory STATIC -> now 2 STATIC in this phase -> CLOSING_PROBE
    r4 = _make_turn_request(
        conversation_id="conv_flip",
        turn_number=4,
        posture="exploratory",
        delta="static",
        claims=_static_claims(4),
        state_checkpoint=res3.state_checkpoint,
        checkpoint_id=res3.checkpoint_id,
    )
    res4 = process_turn(r4, ctx)
    assert res4.action == ConversationAction.CLOSING_PROBE
```

**Step 2: Run test**

```bash
cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestPipelinePhaseLocal::test_posture_flip_a_b_a_resets_phase_window -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add packages/context-injection/tests/test_pipeline.py
git commit -m "test(pipeline): P2 — A->B->A posture flip creates fresh phase"
```

---

## Task 6: Test P3 — STATIC posture-change turn + next STATIC fires probe

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/context-injection/tests/test_pipeline.py`

**Step 1: Write the test**

Add to `TestPipelinePhaseLocal`:

```python
def test_static_at_phase_boundary_counts_toward_plateau(self) -> None:
    """The posture-change turn itself is STATIC, then the next turn is also
    STATIC. This should fire the closing probe because the boundary entry
    is included in the new phase window.
    """
    ctx = _make_ctx(git_files=set())
    # T1: exploratory ADVANCING
    r1 = _make_turn_request(
        conversation_id="conv_boundary_static",
        turn_number=1,
        posture="exploratory",
        delta="advancing",
    )
    res1 = process_turn(r1, ctx)
    assert res1.status == "success"

    # T2: evaluative STATIC -> posture change, new phase with 1 STATIC entry
    r2 = _make_turn_request(
        conversation_id="conv_boundary_static",
        turn_number=2,
        posture="evaluative",
        delta="static",
        claims=_static_claims(2),
        state_checkpoint=res1.state_checkpoint,
        checkpoint_id=res1.checkpoint_id,
    )
    res2 = process_turn(r2, ctx)
    # Only 1 entry in new phase — no plateau yet
    assert res2.action == ConversationAction.CONTINUE_DIALOGUE

    # T3: evaluative STATIC -> 2 STATIC in phase -> CLOSING_PROBE
    r3 = _make_turn_request(
        conversation_id="conv_boundary_static",
        turn_number=3,
        posture="evaluative",
        delta="static",
        claims=_static_claims(3),
        state_checkpoint=res2.state_checkpoint,
        checkpoint_id=res2.checkpoint_id,
    )
    res3 = process_turn(r3, ctx)
    assert res3.action == ConversationAction.CLOSING_PROBE
```

**Step 2: Run test**

```bash
cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestPipelinePhaseLocal::test_static_at_phase_boundary_counts_toward_plateau -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add packages/context-injection/tests/test_pipeline.py
git commit -m "test(pipeline): P3 — STATIC boundary entry counts toward phase-local plateau"
```

---

## Task 7: Test P4 — get_phase_entries at exact boundary index

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/context-injection/tests/test_conversation.py`

**Step 1: Write the test**

Add to `TestPhaseFields`:

```python
def test_phase_entries_at_boundary_index(self) -> None:
    """When phase_start_index = len(entries) - 1 (the exact index produced
    by a posture change), get_phase_entries returns exactly one entry.
    """
    state = ConversationState(conversation_id="test")
    for i in range(4):
        state = state.with_turn(_make_entry(turn_number=i + 1))
    # Simulate posture change: phase starts at last entry
    state = state.with_posture_change(
        "evaluative", phase_start_index=len(state.entries) - 1
    )
    phase_entries = state.get_phase_entries()
    assert len(phase_entries) == 1
    assert phase_entries[0].turn_number == 4
```

**Step 2: Run test**

```bash
cd packages/context-injection && uv run pytest tests/test_conversation.py::TestPhaseFields::test_phase_entries_at_boundary_index -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add packages/context-injection/tests/test_conversation.py
git commit -m "test(conversation): P4 — get_phase_entries at exact boundary index"
```

---

## Task 8: Test P5 — Checkpoint round-trip preserves phase fields

**Files:**
- Modify: `.worktrees/cross-model-plugin/packages/context-injection/tests/test_pipeline.py`

**Step 1: Write the test**

Add a new test class after `TestPipelinePhaseLocal`:

```python
class TestCheckpointPhaseFields:
    """Checkpoint round-trip preserves phase tracking fields (P5)."""

    def test_checkpoint_preserves_phase_fields(self) -> None:
        """Phase fields survive checkpoint serialize -> deserialize round-trip."""
        ctx = _make_ctx(git_files=set())
        # T1: exploratory
        r1 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=1,
            posture="exploratory",
            delta="advancing",
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: evaluative -> posture change creates phase fields
        r2 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=2,
            posture="evaluative",
            delta="advancing",
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.status == "success"

        # Verify phase fields survived the round-trip by checking
        # that T3 with same posture does NOT reset the phase
        # (if fields were lost, T3 would be treated as first turn)
        r3 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=3,
            posture="evaluative",
            delta="static",
            claims=_static_claims(3),
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.status == "success"

        # T4: evaluative STATIC -> 2 STATIC in phase -> CLOSING_PROBE
        # This proves phase_start_index survived: if it was reset to 0,
        # the phase window would include T1 (ADVANCING) and no plateau.
        r4 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=4,
            posture="evaluative",
            delta="static",
            claims=_static_claims(4),
            state_checkpoint=res3.state_checkpoint,
            checkpoint_id=res3.checkpoint_id,
        )
        res4 = process_turn(r4, ctx)
        assert res4.action == ConversationAction.CLOSING_PROBE
```

**Step 2: Run test**

```bash
cd packages/context-injection && uv run pytest tests/test_pipeline.py::TestCheckpointPhaseFields::test_checkpoint_preserves_phase_fields -v
```

Expected: PASS (Pydantic's `model_dump_json`/`model_validate_json` round-trips all fields, including the new ones).

**Step 3: Commit**

```bash
git add packages/context-injection/tests/test_pipeline.py
git commit -m "test(pipeline): P5 — checkpoint round-trip preserves phase fields"
```

---

## Task 9: Tests P1-P5 vendored sync + full suite verification

**Step 1: Run the full context-injection test suite**

```bash
cd packages/context-injection && uv run pytest -q
```

Expected: 993 passed (986 baseline + 7 new: P1 + P2 + P3 + P4 + P5, where P1 is 1 test, P2 is 1, P3 is 1, P4 is 1, P5 is 1, plus the existing 2 tests = 7 new total). Actual count may differ slightly — verify all pass, no failures.

**Step 2: Run analytics suite**

```bash
cd packages/plugins/cross-model && uv run pytest tests/ -q
```

Expected: 3 passed.

**Step 3: Commit verification**

No commit needed — this is a verification step.

---

## Task 10: Commit doc/spec/delegation changes and run final verification

**Step 1: Verify vendored copies still match**

```bash
diff packages/context-injection/context_injection/control.py packages/plugins/cross-model/context-injection/context_injection/control.py
diff packages/context-injection/context_injection/conversation.py packages/plugins/cross-model/context-injection/context_injection/conversation.py
diff packages/context-injection/context_injection/pipeline.py packages/plugins/cross-model/context-injection/context_injection/pipeline.py
```

Expected: No differences (only control.py was modified in Task 1, and it was synced).

**Step 2: Review commit log**

```bash
git log --oneline -20
```

Verify clean commit sequence with Tasks 1-8 as separate commits after the 12 existing implementation commits.

---

## Summary

| Task | Finding | Type | Files |
|------|---------|------|-------|
| 1 | F1: Contract/docstring one-shot → once-per-phase | Doc fix | contract, control.py (source + vendored) |
| 2 | F2: Agent phase transition timing ambiguity | Spec fix | codex-dialogue.md |
| 3 | F3: Wire phase delegation in /dialogue | Feature | dialogue/SKILL.md, codex-dialogue.md |
| 4 | P1: Probe → phase change → second probe | Test | test_pipeline.py |
| 5 | P2: A→B→A posture flip | Test | test_pipeline.py |
| 6 | P3: STATIC boundary + next STATIC | Test | test_pipeline.py |
| 7 | P4: get_phase_entries exact boundary | Test | test_conversation.py |
| 8 | P5: Checkpoint round-trip phase fields | Test | test_pipeline.py |
| 9 | Verification: full suite run | Verify | — |
| 10 | Final: vendored sync + commit log | Verify | — |

**Note on P6 (profile validation rules):** Deferred. Profile validation enforcement requires changes to the `/dialogue` skill's profile resolution logic — a larger scope that belongs in a follow-up after the current branch merges. The adjacent-distinct-postures rule is documented in the consultation contract §14 and the debugging profile already satisfies it; enforcement codifies what's already constrained by design.

**Dependencies:**
- Task 1 (doc fix) and Tasks 4-8 (tests) are independent — can be parallelized
- Task 2 (agent timing) must complete before Task 3 (delegation wiring), since Task 3 references the phase tracking section
- Task 9 depends on Tasks 1, 4-8
- Task 10 depends on all prior tasks

**Estimated new test count:** 5 tests (P1: 1, P2: 1, P3: 1, P4: 1, P5: 1)

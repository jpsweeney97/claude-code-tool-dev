# Dialogue Analytics Error Fixes — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 recurring errors in the `/dialogue` skill's analytics pipeline — 3 caused by Claude improvisation (instruction gaps) and 1 genuine code bug (byte-blind compaction).

**Architecture:** Two root causes, two fix types. Root Cause A (Errors 1, 2, 3): SKILL.md and agent template instructions are passive where they need active prohibitions — Claude substitutes its own behavior. Root Cause B (Error 4): checkpoint compaction uses entry count as a proxy for byte size, which breaks with large claims. Fixes apply defense-in-depth: harden instructions AND add code-level validation/fallbacks.

**Tech Stack:** Python 3 (emit_analytics.py, checkpoint.py), Markdown (SKILL.md, codex-dialogue.md), pytest

---

## Chunk 1: Error 2 — convergence_reason_code Validation

Fixes the `invalid convergence_reason_code: 'convergence'` error by validating epilogue values before use and enumerating valid values in the agent template.

### Task 1: Test — invalid epilogue code falls through to map_convergence

**Files:**
- Modify: `packages/plugins/cross-model/tests/test_emit_analytics.py`

- [ ] **Step 1: Write the failing test**

Add after the `test_parse_synthesis_both_fail` test (around line 227):

```python
def test_build_dialogue_outcome_invalid_epilogue_convergence_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid convergence_reason_code in epilogue is replaced by computed value."""
    # Epilogue has "convergence" (valid for termination_reason, NOT convergence_reason_code)
    synthesis = (
        "### Conversation Summary\n"
        "- **Converged:** Yes\n"
        "- **Turns:** 3\n"
        "\n"
        "```json\n"
        "<!-- pipeline-data -->\n"
        "{\n"
        '  "mode": "server_assisted",\n'
        '  "thread_id": "thread-1",\n'
        '  "turn_count": 3,\n'
        '  "converged": true,\n'
        '  "convergence_reason_code": "convergence",\n'
        '  "termination_reason": "convergence",\n'
        '  "scout_count": 1,\n'
        '  "resolved_count": 2,\n'
        '  "unresolved_count": 0,\n'
        '  "emerged_count": 1,\n'
        '  "scope_breach_count": 0\n'
        "}\n"
        "```\n"
    )
    result = build_dialogue_outcome(
        {
            "pipeline": {"posture": "evaluative", "turn_budget": 8},
            "synthesis_text": synthesis,
            "scope_breach": False,
        }
    )
    captured = capsys.readouterr()
    # Should have warned and fallen through to map_convergence
    assert "invalid epilogue convergence_reason_code" in captured.err
    # converged=True + unresolved=0 → all_resolved
    assert result["convergence_reason_code"] == "all_resolved"
    assert result["termination_reason"] == "convergence"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py::test_build_dialogue_outcome_invalid_epilogue_convergence_code -v`
Expected: FAIL — currently the invalid epilogue value passes through to validation, which raises ValueError

### Task 2: Implement — validate epilogue enum values in build_dialogue_outcome

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:428-470`

- [ ] **Step 3: Add epilogue validation before event construction**

In `build_dialogue_outcome`, after `map_convergence` (line 450) and before the event dict (line 452), add validation for both epilogue enum fields:

```python
    # Validate epilogue enum values — invalid values fall through to computed defaults.
    # The agent template may produce values from the wrong enum (e.g. "convergence"
    # is valid for termination_reason but not convergence_reason_code).
    epilogue_code = parsed.get("convergence_reason_code")
    if epilogue_code is not None and epilogue_code not in _VALID_CONVERGENCE_CODES:
        print(
            f"invalid epilogue convergence_reason_code {epilogue_code!r}, "
            f"using computed value {code!r}",
            file=sys.stderr,
        )
        epilogue_code = None

    epilogue_reason = parsed.get("termination_reason")
    if epilogue_reason is not None and epilogue_reason not in _VALID_TERMINATION_REASONS:
        print(
            f"invalid epilogue termination_reason {epilogue_reason!r}, "
            f"using computed value {reason!r}",
            file=sys.stderr,
        )
        epilogue_reason = None
```

Then update line 469-470 to use the validated variables:

```python
        "convergence_reason_code": epilogue_code or code,
        "termination_reason": epilogue_reason or reason,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py::test_build_dialogue_outcome_invalid_epilogue_convergence_code -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to verify no regressions**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py -v`
Expected: All tests pass

### Task 3: Harden agent template — enumerate valid convergence_reason_code values

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:655`

- [ ] **Step 6: Update field description to enumerate valid values**

Change line 655 from:
```
| `convergence_reason_code` | string or null | Code from synthesis checkpoint |
```
To:
```
| `convergence_reason_code` | string or null | One of: `"all_resolved"`, `"natural_convergence"`, `"budget_exhausted"`, `"error"`, `"scope_breach"`. Set to `null` if dialogue did not converge. Do NOT use `termination_reason` values here — the two fields have different enums. |
```

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py \
       packages/plugins/cross-model/tests/test_emit_analytics.py \
       packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "fix(cross-model): validate epilogue convergence_reason_code before use

Invalid epilogue values (e.g. 'convergence' from wrong enum) now fall
through to the computed map_convergence() result instead of propagating
to validation. Agent template updated to enumerate valid values."
```

---

## Chunk 2: Errors 1 & 3 — SKILL.md Instruction Hardening

Fixes Claude improvisation on the analytics flow by adding explicit prohibitions per the project's "Prohibit, don't omit" writing principle.

### Task 4: Harden Step 7a — synthesis_text and file creation instructions

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:365-417`

- [ ] **Step 8: Add prohibitions to the synthesis_text field description**

At line 372, change the `synthesis_text` row from:
```
| `synthesis_text` | string | Full raw output from the `codex-dialogue` agent's Task tool return value |
```
To:
```
| `synthesis_text` | string | The `codex-dialogue` agent's Task tool return value, copied verbatim. Do NOT use your Step 6 paraphrase, summary, or commentary. Do NOT summarize, truncate, or reformat the agent output. The emitter script parses structured markers (`<!-- pipeline-data -->`, `RESOLVED:`, `**Converged:**`) that only exist in the raw output. |
```

- [ ] **Step 9: Add prohibitions to the file creation instruction**

At line 367, change:
```
Use the Write tool to create `/tmp/claude_analytics_{random_suffix}.json` containing the input JSON for the emitter script. The file has four top-level fields:
```
To:
```
Use the Write tool to create `/tmp/claude_analytics_{random_suffix}.json` containing the input JSON for the emitter script. Use a short random alphanumeric suffix (e.g., `a7x9b2`). Do NOT use descriptive names. Do NOT use Bash, sed, echo, cat <<EOF, heredocs, or any shell command to create or modify this file — use the Write tool only. The file has four top-level fields:
```

- [ ] **Step 10: Add file creation prohibitions to the /codex SKILL.md**

The `/codex` SKILL.md uses a different analytics structure (`consultation_outcome` with pipeline-only fields, no `synthesis_text`). Only the file creation instruction applies. At `packages/plugins/cross-model/skills/codex/SKILL.md` around line 238, find the equivalent "Use the Write tool to create" instruction and add the same file creation prohibitions from Step 9 (random suffix, no sed/bash/heredocs). Do NOT add `synthesis_text` prohibitions — they don't apply to `/codex`.

- [ ] **Step 11: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md \
       packages/plugins/cross-model/skills/codex/SKILL.md
git commit -m "fix(cross-model): harden analytics instructions with explicit prohibitions

Add 'Prohibit, don't omit' style directives to Step 7a:
- synthesis_text must be raw Task return value, not summary
- File creation must use Write tool, not sed/bash
- Suffix must be random, not descriptive"
```

---

## Chunk 3: Error 4 — Byte-Aware Checkpoint Compaction

Fixes the "Checkpoint payload exceeds 16384 bytes" error by adding byte-aware compaction that runs before the hard cap check.

### Task 5: Test — compact_to_budget reduces payload under limit

**Files:**
- Modify: `packages/plugins/cross-model/context-injection/tests/test_checkpoint.py`

- [ ] **Step 12: Write the failing test for compact_to_budget**

Add a new test class after `TestCompactLedger`:

```python
class TestCompactToBudget:
    """compact_to_budget: iteratively trim entries until payload fits."""

    def test_reduces_under_limit(self) -> None:
        """State exceeding byte budget is trimmed to fit."""
        from context_injection.checkpoint import (
            MAX_CHECKPOINT_PAYLOAD_BYTES,
            compact_to_budget,
        )
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        counters = LedgerEntryCounters(
            new_claims=3, revised=0, conceded=0, unresolved_closed=0,
        )
        # Build 12 entries with moderate-sized claims that collectively exceed 16KB
        entries: list[LedgerEntry] = []
        for i in range(12):
            claims = [
                Claim(text=f"Claim {j} of turn {i}: {'analysis ' * 20}", status="new", turn=i + 1)
                for j in range(3)
            ]
            entries.append(
                LedgerEntry(
                    position=f"Position for turn {i}: {'context ' * 30}",
                    claims=claims,
                    delta="advancing",
                    tags=[],
                    unresolved=[],
                    counters=counters,
                    quality=QualityLabel.SUBSTANTIVE,
                    effective_delta=EffectiveDelta.ADVANCING,
                    turn_number=i + 1,
                )
            )

        state = ConversationState(conversation_id="conv-1")
        for entry in entries:
            state = state.with_turn(entry)

        # Verify it exceeds the cap before compaction
        payload_size = len(state.model_dump_json().encode("utf-8"))
        assert payload_size > MAX_CHECKPOINT_PAYLOAD_BYTES

        # Compact to budget
        compacted = compact_to_budget(state, MAX_CHECKPOINT_PAYLOAD_BYTES)
        compacted_size = len(compacted.model_dump_json().encode("utf-8"))
        assert compacted_size <= MAX_CHECKPOINT_PAYLOAD_BYTES
        assert len(compacted.entries) >= 1
        # Claim registry rebuilt from remaining entries
        expected_claims = sum(len(e.claims) for e in compacted.entries)
        assert len(compacted.claim_registry) == expected_claims

    def test_preserves_state_under_limit(self) -> None:
        """State already under budget is returned unchanged."""
        from context_injection.checkpoint import (
            MAX_CHECKPOINT_PAYLOAD_BYTES,
            compact_to_budget,
        )

        state = ConversationState(conversation_id="conv-1")
        result = compact_to_budget(state, MAX_CHECKPOINT_PAYLOAD_BYTES)
        assert result is state

    def test_single_oversized_entry_raises(self) -> None:
        """Single entry exceeding budget cannot be compacted — returns as-is."""
        from context_injection.checkpoint import compact_to_budget
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        counters = LedgerEntryCounters(
            new_claims=100, revised=0, conceded=0, unresolved_closed=0,
        )
        claims = [
            Claim(text=f"Very long claim {'x' * 200} {i}", status="new", turn=1)
            for i in range(100)
        ]
        entry = LedgerEntry(
            position="x" * 500,
            claims=claims,
            delta="advancing",
            tags=[],
            unresolved=[],
            counters=counters,
            quality=QualityLabel.SUBSTANTIVE,
            effective_delta=EffectiveDelta.ADVANCING,
            turn_number=1,
        )
        state = ConversationState(conversation_id="conv-1").with_turn(entry)
        # Can't compact below 1 entry — returns state as-is (caller raises)
        result = compact_to_budget(state, 1024)
        assert len(result.entries) == 1
```

- [ ] **Step 13: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_checkpoint.py::TestCompactToBudget -v`
Expected: FAIL — `compact_to_budget` doesn't exist yet

### Task 6: Implement — compact_to_budget function

**Files:**
- Modify: `packages/plugins/cross-model/context-injection/context_injection/checkpoint.py`

- [ ] **Step 14: Add compact_to_budget after compact_ledger (after line 283)**

```python
def compact_to_budget(
    state: ConversationState,
    max_bytes: int,
    min_entries: int = 1,
) -> ConversationState:
    """Iteratively remove oldest entries until serialized payload fits under max_bytes.

    Keeps at least min_entries entries. Rebuilds claim_registry from
    remaining entries after each removal. Returns state unchanged if
    already under budget. Returns state with min_entries if compaction
    cannot reach the target (caller is responsible for the error).
    """
    payload_size = len(state.model_dump_json().encode("utf-8"))
    if payload_size <= max_bytes:
        return state

    while len(state.entries) > min_entries:
        trimmed = state.entries[1:]
        claims = tuple(c for e in trimmed for c in e.claims)
        state = state.model_copy(
            update={
                "entries": trimmed,
                "claim_registry": claims,
            }
        )
        payload_size = len(state.model_dump_json().encode("utf-8"))
        if payload_size <= max_bytes:
            return state

    return state
```

- [ ] **Step 15: Run compact_to_budget tests to verify they pass**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_checkpoint.py::TestCompactToBudget -v`
Expected: PASS

### Task 7: Test — serialize_checkpoint auto-compacts instead of raising

**Files:**
- Modify: `packages/plugins/cross-model/context-injection/tests/test_checkpoint.py`

- [ ] **Step 16: Write the failing test for auto-compaction in serialize_checkpoint**

Add to the `TestSerializeCheckpoint` class:

```python
    def test_auto_compacts_when_over_budget(self) -> None:
        """serialize_checkpoint compacts instead of raising when payload exceeds limit."""
        from context_injection.checkpoint import MAX_CHECKPOINT_PAYLOAD_BYTES
        from context_injection.enums import EffectiveDelta, QualityLabel
        from context_injection.ledger import LedgerEntry, LedgerEntryCounters
        from context_injection.types import Claim

        counters = LedgerEntryCounters(
            new_claims=3, revised=0, conceded=0, unresolved_closed=0,
        )
        entries: list[LedgerEntry] = []
        for i in range(12):
            claims = [
                Claim(text=f"Claim {j} of turn {i}: {'analysis ' * 20}", status="new", turn=i + 1)
                for j in range(3)
            ]
            entries.append(
                LedgerEntry(
                    position=f"Position for turn {i}: {'context ' * 30}",
                    claims=claims,
                    delta="advancing",
                    tags=[],
                    unresolved=[],
                    counters=counters,
                    quality=QualityLabel.SUBSTANTIVE,
                    effective_delta=EffectiveDelta.ADVANCING,
                    turn_number=i + 1,
                )
            )
        state = ConversationState(conversation_id="conv-1")
        for entry in entries:
            state = state.with_turn(entry)

        # Should NOT raise — should auto-compact
        result = serialize_checkpoint(state)
        assert result.checkpoint_string  # Got a valid checkpoint
        payload_size = len(result.checkpoint_string.encode("utf-8"))
        # The payload field is already a JSON string (double-encoded).
        # Check its byte size directly — do NOT re-dump, that would add quoting.
        inner = json.loads(result.checkpoint_string)
        assert len(inner["payload"].encode("utf-8")) <= MAX_CHECKPOINT_PAYLOAD_BYTES
```

- [ ] **Step 17: Run test to verify it fails**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_checkpoint.py::TestSerializeCheckpoint::test_auto_compacts_when_over_budget -v`
Expected: FAIL — currently raises ValueError

### Task 8: Implement — auto-compact in serialize_checkpoint + fix error type

**Files:**
- Modify: `packages/plugins/cross-model/context-injection/context_injection/checkpoint.py:67-85`

- [ ] **Step 18: Update serialize_checkpoint to auto-compact before raising**

Replace lines 78-85 (after `payload = state_for_payload.model_dump_json()`):

```python
    payload = state_for_payload.model_dump_json()
    payload_size = len(payload.encode("utf-8"))

    if payload_size > MAX_CHECKPOINT_PAYLOAD_BYTES:
        compacted = compact_to_budget(state_for_payload, MAX_CHECKPOINT_PAYLOAD_BYTES)
        payload = compacted.model_dump_json()
        payload_size = len(payload.encode("utf-8"))
        if payload_size > MAX_CHECKPOINT_PAYLOAD_BYTES:
            raise CheckpointError(
                "checkpoint_too_large",
                f"Checkpoint payload exceeds {MAX_CHECKPOINT_PAYLOAD_BYTES} bytes "
                f"after compaction: got {payload_size} bytes.",
            )
        state_for_payload = compacted
```

Also update the docstring at line 73 to reflect the new behavior:

```python
    """Serialize state to checkpoint. Returns SerializedCheckpoint.

    parent_id is derived from state.last_checkpoint_id (not a parameter).
    New checkpoint_id is embedded into state BEFORE serializing the payload,
    so the returned state already has last_checkpoint_id updated (CC-3 fix).
    Auto-compacts if payload exceeds MAX_CHECKPOINT_PAYLOAD_BYTES.
    Raises CheckpointError if compaction cannot bring payload under limit.
    """
```

- [ ] **Step 19: Update the existing test_exceeds_size_cap_raises**

The existing test at line 91 expects `ValueError`. Update to expect `CheckpointError` with code `"checkpoint_too_large"` — this test uses 100 claims of 200+ chars in a single entry, which can't be compacted below 1 entry. **Preserve the full test body (lines 92-117)** — only change the assertion at lines 118-119:

```python
    def test_exceeds_size_cap_raises(self) -> None:
        ...
        state = ConversationState(conversation_id="conv-1").with_turn(entry)
        with pytest.raises(CheckpointError) as exc_info:
            serialize_checkpoint(state)
        assert exc_info.value.code == "checkpoint_too_large"
```

- [ ] **Step 20: Update the DD-2 invariant comment**

At lines 261-264, change:

```python
    """Reduce state size by keeping only recent entries.

    Unreachable under DD-2 invariant (MAX_CONVERSATION_TURNS <
    MAX_ENTRIES_BEFORE_COMPACT). The pipeline's pre-append turn cap guard
    rejects turns before entry count can reach the compaction threshold.
    Retained as a safety net if the invariant is relaxed in the future.
```

To:

```python
    """Reduce state size by keeping only recent entries.

    Entry-count trigger is unreachable under DD-2 invariant
    (MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT). However,
    DD-2 does NOT guarantee byte-size compliance — conversations with
    large claims can exceed MAX_CHECKPOINT_PAYLOAD_BYTES with fewer
    entries than the compaction threshold. Use compact_to_budget() for
    byte-aware compaction. This function is retained as a safety net
    if the DD-2 invariant is relaxed in the future.
```

- [ ] **Step 21: Run all checkpoint tests**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_checkpoint.py -v`
Expected: All tests pass

- [ ] **Step 22: Run full context-injection test suite**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest -v`
Expected: All tests pass (991 tests)

- [ ] **Step 23: Commit**

```bash
git add packages/plugins/cross-model/context-injection/context_injection/checkpoint.py \
       packages/plugins/cross-model/context-injection/tests/test_checkpoint.py
git commit -m "fix(context-injection): byte-aware checkpoint compaction

compact_to_budget() iteratively trims oldest entries until the
serialized payload fits under MAX_CHECKPOINT_PAYLOAD_BYTES.
serialize_checkpoint() auto-compacts before raising.

Error type changed from ValueError to CheckpointError (code:
checkpoint_too_large) so pipeline.py:81 catches it properly.
DD-2 invariant comment updated to clarify it prevents entry-count
compaction but not byte-size overflow."
```

---

## Chunk 4: Error 1 Defense-in-Depth — Graceful Degradation

Changes `build_dialogue_outcome` to degrade gracefully on `parse_failed` instead of raising ValueError. The event proceeds with default counts and `convergence_reason_code: "error"`, still capturing valuable pipeline metrics.

### Task 9: Test — parse_failed produces degraded event

**Files:**
- Modify: `packages/plugins/cross-model/tests/test_emit_analytics.py`

- [ ] **Step 24: Update existing test and add degraded event test**

The existing `test_parse_synthesis_both_fail` at line 216-226 expects ValueError. Replace the ValueError assertion with a degraded-event assertion:

```python
def test_parse_synthesis_both_fail(capsys: pytest.CaptureFixture[str]) -> None:
    synthesis = "Plain text without epilogue or recognizable markdown headings."

    parsed = parse_synthesis(synthesis)
    captured = capsys.readouterr()

    assert "epilogue missing or malformed, falling back to markdown parsing" in captured.err
    assert parsed["turn_count"] == 0
    assert parsed["converged"] is False
    assert parsed["thread_id"] is None
    assert parsed["scout_count"] == 0
    assert parsed["parse_failed"] is True

    # Should degrade gracefully instead of raising
    result = build_dialogue_outcome(
        {
            "pipeline": {"posture": "evaluative", "turn_budget": 4},
            "synthesis_text": synthesis,
            "scope_breach": False,
        }
    )
    assert result["convergence_reason_code"] == "error"
    assert result["termination_reason"] == "error"
    assert result["parse_degraded"] is True
```

- [ ] **Step 25: Run test to verify it fails**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py::test_parse_synthesis_both_fail -v`
Expected: FAIL — currently raises ValueError

### Task 10: Implement — graceful degradation on parse_failed

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:434-438`

- [ ] **Step 26: Replace ValueError with warning + degraded flag**

Change lines 434-438 from:

```python
    parsed = parse_synthesis(synthesis_text)
    if parsed.get("parse_failed"):
        raise ValueError(
            "synthesis parse failed: epilogue and markdown parsing yielded no usable data"
        )
```

To:

```python
    parsed = parse_synthesis(synthesis_text)
    parse_degraded = parsed.get("parse_failed", False)
    if parse_degraded:
        print(
            "synthesis parse failed: epilogue and markdown parsing yielded no usable data; "
            "emitting degraded event with defaults",
            file=sys.stderr,
        )
```

Then, before `map_convergence` (around line 444), short-circuit convergence when degraded to avoid depending on `map_convergence` producing correct results for degenerate zero-turn inputs:

```python
    if parse_degraded:
        code, reason = ("error", "error")
    else:
        code, reason = map_convergence(
            converged=parsed["converged"],
            unresolved_count=parsed["unresolved_count"],
            turn_count=parsed["turn_count"],
            turn_budget=turn_budget,
            scope_breach=scope_breach,
        )
```

Then add `parse_degraded` to the event dict (after `"emerged_count"` around line 473):

```python
        "parse_degraded": parse_degraded,
```

- [ ] **Step 27: Run test to verify it passes**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py::test_parse_synthesis_both_fail -v`
Expected: PASS

- [ ] **Step 28: Run full emit_analytics test suite**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py -v`
Expected: All tests pass

- [ ] **Step 29: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py \
       packages/plugins/cross-model/tests/test_emit_analytics.py
git commit -m "fix(cross-model): degrade gracefully on synthesis parse failure

build_dialogue_outcome no longer raises ValueError when both epilogue
and markdown parsers fail. Instead, emits a degraded event with
default counts and convergence_reason_code='error'. Pipeline metrics
(posture, gatherer stats, etc.) are still captured.

Added parse_degraded bool field to distinguish degraded events from
genuine error outcomes."
```

---

## Verification

After all chunks are implemented:

- [ ] **Step 30: Run cross-model test suite**

Run: `cd packages/plugins/cross-model && uv run pytest -v`
Expected: All tests pass

- [ ] **Step 31: Run context-injection test suite**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest -v`
Expected: All 991 tests pass

- [ ] **Step 32: Lint check**

Run: `cd packages/plugins/cross-model && uv run ruff check scripts/ tests/`
Run: `cd packages/plugins/cross-model/context-injection && uv run ruff check context_injection/ tests/`
Expected: Clean

- [ ] **Step 33: Final commit — update CLAUDE.md gotchas if needed**

If the `checkpoint_too_large` error code is new, add it to any error code documentation. Review whether the CLAUDE.md gotcha about "Hook failure polarity" needs updating for the new CheckpointError behavior.

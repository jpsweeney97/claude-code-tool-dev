# T-C: Turn-Level Event Emission

```yaml
id: T-C
date: 2026-02-27
status: open
priority: medium
branch: feature/turn-level-events
blocked_by: [T-F]
blocks: [T-D]
related: [T-A, T-B, T-D, T-F]
effort: M (2-3 sessions)
```

## Summary

Emit a `turn_completed` event after each Codex turn in a dialogue. Currently, analytics events are only emitted at dialogue completion (Step 7 of `/dialogue`). This means all intermediate state — per-turn claim evolution, delta trajectories, scout decisions, convergence signals — is lost. Turn-level events create a time-series view of dialogue progression.

**Value:** Enables per-turn diagnostics, convergence trajectory analysis, and mid-dialogue failure recovery. This is the single biggest structural gap in the analytics system.

## Rationale

Current dialogue_outcome events capture the *end state* (45 fields). But the *path* to that state is invisible:
- Which turns advanced vs stalled?
- When were scouts most productive?
- How did claim counts evolve turn-by-turn?
- At what point did convergence signals appear?

These questions can only be answered with per-turn telemetry.

## Design

### New Event Type: `turn_completed`

```json
{
  "schema_version": "0.1.0",
  "event": "turn_completed",
  "ts": "2026-02-27T12:00:05Z",
  "session_id": "uuid",
  "consultation_id": "uuid",
  "turn_number": 3,
  "turn_budget": 8,
  "posture": "adversarial",
  "delta": "advancing",
  "claims": {
    "new": 2,
    "reinforced": 1,
    "revised": 0,
    "conceded": 0,
    "total": 5
  },
  "unresolved_count": 1,
  "scout_executed": true,
  "scout_action": "read",
  "scout_outcome": "success",
  "action": "continue_dialogue",
  "action_reason": "Conversation active — last delta: advancing"
}
```

### Data Sources

The `codex-dialogue` agent already has all this data available at each turn:

| Field | Source |
|-------|--------|
| `turn_number` | Agent's turn counter |
| `delta` | Extracted from Codex response (Step 2 of 7-step loop) |
| `claims.*` | From `validated_entry.counters` in TurnPacket (Step 3) |
| `unresolved_count` | From current turn's unresolved list |
| `scout_executed` | Whether Step 5-6 ran |
| `scout_action` / `scout_outcome` | From ScoutResult (Step 6) |
| `action` / `action_reason` | From TurnPacket's `action` field (Step 3) |

### Emission Mechanism

**Two options for where to emit:**

#### Option A: Agent-side emission (recommended)
The `codex-dialogue` agent emits directly at the end of each turn's 7-step loop, before composing the follow-up prompt (Step 6→7 boundary).

**Pros:** Agent has all the data; no additional MCP calls needed.
**Cons:** Adds instructions to an already-large spec (740 lines).

Implementation: Add a Step 7b to the 7-step loop:
```
7b. Emit turn event
Write turn data to /tmp/claude_turn_{consultation_id}_{turn_number}.json
Call emit_analytics.py (extended for turn_completed type)
Best-effort: failure does not halt dialogue.
```

#### Option B: Server-side emission
The context injection MCP server emits a turn event as part of `process_turn` (Call 1).

**Pros:** Server has structured data (entities, template candidates, path decisions, budget).
**Cons:** Server doesn't know about scout outcomes (those happen in Call 2). Server doesn't know about Codex response content. Would need a separate "turn finalize" call.

**Recommendation:** Option A. The agent has the complete picture. Server enrichment can come later (T-D).

### Changes to `emit_analytics.py`

Add `turn_completed` event builder and validation:

```python
_TURN_COMPLETED_REQUIRED = {
    "schema_version",
    "event",
    "ts",
    "consultation_id",
    "turn_number",
    "turn_budget",
    "delta",
    "action",
}
```

Validation rules:
- `turn_number` >= 1
- `delta` in `{advancing, shifting, static}`
- `action` in `{continue_dialogue, closing_probe, conclude}`
- `claims` object has all required count fields when present
- `scout_executed` is bool

### Changes to `read_events.py`

Add `turn_completed` to `_REQUIRED_FIELDS` and `_KNOWN_UNSTRUCTURED` (or the structured set).

### Changes to `codex-dialogue.md`

Add a 4-line instruction block after Step 7 of the per-turn loop:

```markdown
**7b. Emit turn event (best-effort)**
Write `/tmp/claude_turn_{consultation_id}_{turn_number}.json` with:
`{"event_type":"turn_completed","consultation_id":"...","turn_number":N,"delta":"...","claims":{...},"scout_executed":bool,"action":"..."}`
Run: `python3 "{plugin_root}/scripts/emit_analytics.py" /tmp/claude_turn_....json`
Failure does not halt dialogue. Proceed to follow-up composition.
```

### Correlation

Turn events correlate with the final `dialogue_outcome` via `consultation_id`. Analysis can reconstruct the full trajectory:
```
consultation_id=abc → [turn_1, turn_2, turn_3, ..., dialogue_outcome]
```

## Files to Modify

| File | Action | Change |
|------|--------|--------|
| `packages/plugins/cross-model/scripts/emit_analytics.py` | Modify | Add `turn_completed` builder + validation |
| `packages/plugins/cross-model/scripts/read_events.py` | Modify | Add required-field schema |
| `packages/plugins/cross-model/agents/codex-dialogue.md` | Modify | Add Step 7b turn event emission |

## Acceptance Criteria

1. One `turn_completed` event emitted per Codex turn in a dialogue
2. Events correlate with final `dialogue_outcome` via `consultation_id`
3. `turn_number` values are sequential (1, 2, 3, ...)
4. Scout execution data is accurate (matches actual scout execution)
5. Emission failures do not halt or delay the dialogue
6. `read_events.py --validate` passes for all new events

## Risks

- **Agent spec bloat:** Adding per-turn emission to the 740-line `codex-dialogue.md` spec. Mitigate by keeping the instruction block minimal (4 lines) and referencing the emission contract rather than duplicating it.
- **Performance:** One additional `emit_analytics.py` call per turn (~100ms). Acceptable for multi-turn dialogues where Codex response time dominates (5-30s per turn).
- **Partial emission:** If the dialogue fails mid-stream, some turn events will exist without a closing `dialogue_outcome`. This is actually valuable — those turn events are the only record of what happened before the failure.

## Future Extensions (out of scope)

- Combine with T-D's pipeline metrics to add entity counts, template match rates, etc. to turn events
- Time-series visualization in T-A's `/codex stats`
- Turn-level comparison across dialogues (same question, different postures)

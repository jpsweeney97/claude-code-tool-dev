# T-F: Failure Event Emission

```yaml
id: T-F
date: 2026-02-27
status: open
priority: high
branch: feature/failure-events
blocked_by: []
blocks: [T-C]
related: [T-A, T-C]
effort: S (1 session)
```

## Summary

Add failure event emission to the analytics pipeline. Currently, mid-dialogue failures (Codex timeouts, scope breaches, MCP errors) produce only `logger.warning()` calls to stderr — they never reach the event log. This creates a blind spot: we know when things succeed but not when or how they fail.

**Value:** Closes the biggest safety gap in the analytics system. Silent failures are the hardest bugs to find. Failure events make them visible, debuggable, and trackable over time.

## Rationale

Current failure visibility:

| Failure | Current Signal | Visible To |
|---------|---------------|------------|
| Credential block | `block` event in log | Yes (codex_guard.py) |
| Broad-tier shadow | `shadow` event in log | Yes (codex_guard.py) |
| Mid-dialogue Codex timeout | Agent error handling | No — lost |
| Context injection MCP error | `logger.warning()` to stderr | No — lost |
| Scope breach termination | `termination_reason: scope_breach` in dialogue_outcome | Partial — only if dialogue completes |
| Scout execution failure | `logger.info()` to stderr | No — lost |
| Checkpoint error | `logger.warning()` to stderr | No — lost |
| Gatherer timeout/failure | Skill-level retry | No — lost |
| Parse truncation | `parse_truncated: true` in dialogue_outcome | Partial — only if dialogue completes |

**Key gap:** If a dialogue fails before Step 7 (analytics emission), no event is logged at all. The failure is invisible.

## Design

### New Event Types

#### 1. `dialogue_failed`
Emitted when a dialogue terminates abnormally before completion.

```json
{
  "schema_version": "0.1.0",
  "event": "dialogue_failed",
  "ts": "2026-02-27T12:00:00Z",
  "session_id": "uuid",
  "consultation_id": "uuid",
  "failure_stage": "turn_3",
  "failure_type": "codex_timeout",
  "error_message": "Codex MCP tool call timed out after 120s",
  "partial_state": {
    "turns_completed": 2,
    "posture": "adversarial",
    "mode": "server_assisted",
    "converged": false,
    "resolved_count": 1,
    "scout_count": 1
  }
}
```

**failure_type enum:**
- `codex_timeout` — Codex MCP tool call timed out
- `codex_error` — Codex returned an error response
- `mcp_error` — Context injection MCP tool failed
- `scope_breach` — 3 scope breaches triggered termination (currently logged in dialogue_outcome but worth a dedicated failure event for mid-stream visibility)
- `agent_error` — Unhandled error in dialogue agent
- `parse_error` — Synthesis parsing failed completely

#### 2. `scout_failed`
Emitted per-scout when execution fails.

```json
{
  "schema_version": "0.1.0",
  "event": "scout_failed",
  "ts": "2026-02-27T12:00:00Z",
  "session_id": "uuid",
  "consultation_id": "uuid",
  "turn_number": 3,
  "scout_type": "read",
  "failure_status": "denied",
  "target_display": "src/config.py",
  "error_message": "Path denied: matches denylist pattern .env"
}
```

**Note:** The context injection server already returns `ScoutResultFailure` with `status` (not_found, denied, binary, decode_error, timeout) and `error_message`. This event captures those failures in the event log for longitudinal analysis.

#### 3. `gatherer_failed`
Emitted when a context gatherer (code or falsifier) fails or times out during `/dialogue` Step 2.

```json
{
  "schema_version": "0.1.0",
  "event": "gatherer_failed",
  "ts": "2026-02-27T12:00:00Z",
  "session_id": "uuid",
  "gatherer": "code",
  "failure_type": "timeout",
  "retry_attempted": true,
  "retry_succeeded": false
}
```

### Emission Mechanism

#### For `dialogue_failed`
The `/dialogue` skill (SKILL.md) must emit this event in its failure recovery paths. Currently, failures are handled but not logged:

**Integration point:** After Step 5 (delegation) fails, before presenting error to user:
1. Write `/tmp/claude_analytics_fail_{random}.json` with the failure event
2. Call `emit_analytics.py` (requires extending the script to accept `dialogue_failed` event type)

#### For `scout_failed`
Two options:

**Option A (preferred):** The `codex-dialogue` agent spec already handles `ScoutResultFailure`. Add an instruction to emit a lightweight failure event via Bash when a scout fails. The agent writes the event JSON directly:
```bash
echo '{"event":"scout_failed",...}' >> ~/.claude/.codex-events.jsonl
```
Simple, no new script needed. Risk: malformed JSON on agent error. Mitigation: wrap in a try/fail pattern or use a tiny emitter helper.

**Option B:** Extend `emit_analytics.py` to accept `scout_failed` events. Cleaner validation but higher friction per-scout.

**Recommendation:** Option A for MVP, migrate to Option B if validation errors appear.

#### For `gatherer_failed`
The `/dialogue` skill already handles gatherer failures in Step 2 (retry logic). Add event emission after retry exhaustion:
1. Write event JSON
2. Call `emit_analytics.py` (extended for new type)

### Changes to `emit_analytics.py`

Add to the event type dispatch:
- `dialogue_failed`: New builder + validation (fewer required fields than `dialogue_outcome`)
- `gatherer_failed`: New builder + validation
- `scout_failed`: New builder + validation (or skip if using Option A direct-write)

### Changes to `read_events.py`

Add to `_REQUIRED_FIELDS`:
- `dialogue_failed`: `{event, ts, failure_stage, failure_type, error_message}`
- `scout_failed`: `{event, ts, scout_type, failure_status, error_message}`
- `gatherer_failed`: `{event, ts, gatherer, failure_type}`

## Files to Modify

| File | Action | Change |
|------|--------|--------|
| `packages/plugins/cross-model/scripts/emit_analytics.py` | Modify | Add `dialogue_failed`, `gatherer_failed` builders + validation |
| `packages/plugins/cross-model/scripts/read_events.py` | Modify | Add required-field schemas for new event types |
| `packages/plugins/cross-model/skills/dialogue/SKILL.md` | Modify | Add failure event emission in error recovery paths (Steps 2, 5) |
| `packages/plugins/cross-model/agents/codex-dialogue.md` | Modify | Add scout failure event emission (if Option A) |

## Acceptance Criteria

1. `dialogue_failed` events captured for all failure paths in `/dialogue`
2. `scout_failed` events captured for every `ScoutResultFailure` response
3. `gatherer_failed` events captured for timeout and retry-exhaustion cases
4. All new events pass `read_events.py --validate`
5. Existing `dialogue_outcome` emission unaffected
6. Failures in failure-event emission do not block user-visible output (best-effort)

## Risks

- **Agent spec complexity:** Adding emission instructions to `codex-dialogue.md` (already 740 lines) increases cognitive load. Keep instructions minimal — 2-3 lines per emission point.
- **Event log growth:** Failure events are typically rare. If a systemic issue causes many failures, log growth is actually the desired signal.
- **Double-counting:** A dialogue that fails and then retries could emit `dialogue_failed` + `dialogue_outcome`. Use `consultation_id` to correlate; add `retry_of` field if retry linkage needed later.

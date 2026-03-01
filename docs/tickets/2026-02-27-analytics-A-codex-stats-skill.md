# T-A: /codex stats — Analytics Presentation Skill

```yaml
id: T-A
date: 2026-02-27
status: open
priority: high
branch: feature/codex-stats-skill
blocked_by: []
blocks: [T-B]
related: [T-B, T-C, T-D, T-E, T-F]
effort: S (1-2 sessions)
```

## Summary

Create a user-invocable `/codex stats` skill that reads `~/.claude/.codex-events.jsonl` and presents analytics about cross-model consultation usage. This is the presentation layer for analytics data that already exists but has no user-facing surface.

**Value:** Validates what metrics users actually care about before investing in derived metrics (T-B) or new instrumentation (T-C through T-E). Acts as the feedback loop that shapes all downstream analytics work.

## Rationale

The plugin currently logs 5 event types (`consultation`, `block`, `shadow`, `dialogue_outcome`, `consultation_outcome`) with up to 45 fields per event. Two scripts exist for emission (`emit_analytics.py`) and reading (`read_events.py`), but there is no user-facing presentation. Users have no way to see how often they consult, whether dialogues converge, or whether the credential guard blocks dispatches.

## Design

### Skill Structure

Create `packages/plugins/cross-model/skills/stats/SKILL.md` as a user-invocable skill.

### Arguments

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `--period` | `7d`, `30d`, `all` | `30d` | Time window for aggregation |
| `--type` | `dialogue`, `consultation`, `security`, `all` | `all` | Which event category to report |

### Output Sections

#### 1. Usage Overview
- Total consultations (single-turn) and dialogues (multi-turn)
- Count by posture (adversarial, collaborative, exploratory, evaluative)
- Date range covered, events per day average

#### 2. Dialogue Quality (when `--type dialogue` or `all`)
- Convergence rate: `converged=true / total_dialogues`
- Average turns to convergence
- Convergence reason distribution (`all_resolved`, `natural_convergence`, `budget_exhausted`, `error`, `scope_breach`)
- Termination reason distribution
- Mode distribution (`server_assisted` vs `manual_legacy`)
- Average resolved/unresolved/emerged counts

#### 3. Context Quality (when `--type dialogue` or `all`)
- Seed confidence distribution (`normal` vs `low`)
- Low seed confidence reason breakdown
- Average citations, unique files, shared citation paths
- Gatherer retry rate

#### 4. Security (when `--type security` or `all`)
- Credential blocks (strict + contextual tiers)
- Shadow detections (broad tier)
- Block rate: `blocks / (blocks + consultations)`

### Implementation Approach

The skill should:
1. Use Bash to invoke `read_events.py` to load events
2. Filter by time window using `ts` field (ISO 8601)
3. Compute aggregations inline (no new Python script needed for MVP)
4. Present as formatted markdown with inline code blocks for numbers

**Alternative (preferred if complexity warrants):** Create a `compute_stats.py` script in `scripts/` that reads events, computes aggregations, and outputs a JSON summary. The skill invokes it and formats the output. This is cleaner for testing and reuse by T-B.

### Event Schema Reference

The skill must handle all 3 schema versions (0.1.0, 0.2.0, 0.3.0) and degrade gracefully when fields are absent:
- 0.1.0 events lack `provenance_unknown_count`
- 0.1.0/0.2.0 events lack planning fields (`question_shaped`, etc.)
- `consultation` events (from codex_guard.py PostToolUse) have only 7 fields

### Reader API

`read_events.py` exposes library functions:
- `read_all(path) -> (events, skipped_count)`
- `read_by_type(path, event_type) -> (events, skipped_count)`
- `classify(event) -> str`
- `validate_event(event) -> list[str]`

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `packages/plugins/cross-model/skills/stats/SKILL.md` | Create | Skill definition |
| `packages/plugins/cross-model/scripts/compute_stats.py` | Create (if chosen) | Stats computation module |
| `packages/plugins/cross-model/plugin.json` | Modify | Register new skill |

## Acceptance Criteria

1. `/codex stats` produces readable output with all 4 sections
2. `--period` filtering works correctly across timezone boundaries
3. Handles empty event log gracefully (no events yet)
4. Handles mixed schema versions without errors
5. Handles malformed events (skips with count, like `read_events.py`)
6. Output is concise enough to be useful, detailed enough to be actionable

## Risks

- **Empty event log:** First-time users will see empty output. Skill should say "No events recorded yet. Run /codex or /dialogue to start generating analytics."
- **Large event logs:** No pagination in MVP. If performance becomes an issue, add `--last N` flag.
- **Schema version drift:** Skill must handle old events. Use `.get()` with defaults for all optional fields.

## Open Questions

1. Should the skill produce a summary comment with recommendations (e.g., "Your convergence rate is 45% — consider using adversarial posture for technical questions")?
2. Should there be a `--json` flag for machine-readable output?

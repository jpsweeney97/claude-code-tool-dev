# E-ANALYTICS Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add consultation analytics to the cross-model plugin — `dialogue_outcome` events for `/dialogue` and `consultation_outcome` events for `/codex`, both appended to `~/.claude/.codex-events.jsonl`.

**Architecture:** The `/dialogue` skill gains a new Step 7 that parses the `codex-dialogue` agent's synthesis output, assembles a 30+ field event record, and appends it to the shared JSONL event log. The `/codex` skill gains a parallel but simpler emission step. The `codex-dialogue` agent is updated to output the actual Codex thread ID (not a boolean). The `codex_guard.py` hook is fixed to check `structuredContent.threadId` in addition to the top-level field, aligning it with the agent's extraction logic.

**Tech Stack:** Markdown instruction documents (skills, agents), JSONL event log, Python (guard fix), Bash `echo >>` for append.

**Reference:** `docs/plans/2026-02-19-cross-model-plugin-enhancements.md` §4 (authoritative spec)

**Branch:** Create `feature/e-analytics` from `main`.

**Test command:**
- Guard tests: `cd packages/plugins/cross-model && uv run pytest ../../tests/test_codex_guard.py -v`
- Integration tests: behavioral — run `/dialogue` and `/codex`, verify JSONL output with `jq`

**Dependencies between tasks:**
- Task 1: independent (agent output format fix)
- Task 2: independent (guard thread_id check fix — separate file)
- Task 3: depends on Task 1 (extraction contract references new thread_id format)
- Task 4: independent of Tasks 1-3 (codex skill is separate)
- Task 5: depends on Tasks 3-4 (documents final event schemas)
- Task 6: depends on Tasks 1-5 (marketplace update + dialogue integration test)
- Task 7: depends on Tasks 4-6 (codex integration test)

---

## Task 1: Update codex-dialogue agent — thread_id output

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:510`

**Step 1: Edit the Continuation section output format**

In `packages/plugins/cross-model/agents/codex-dialogue.md`, find the Continuation section (line 510) and change:

```markdown
- **Thread ID present:** yes/no
```

to:

```markdown
- **Thread ID:** {persisted threadId value} | none
```

**Step 2: Verify no other references to "Thread ID present" in the agent**

Run: `rg "Thread ID present" packages/plugins/cross-model/agents/codex-dialogue.md`
Expected: 0 matches (the only occurrence was just changed)

**Step 3: Check the Example section references the new format**

Read the Example/Continuation section near line 529+ of `codex-dialogue.md`. If the example shows "Thread ID present: yes", update it to show an actual thread ID value (e.g., `Thread ID: thread_abc123`).

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "feat(codex-dialogue): output actual thread ID value instead of boolean

The Continuation section now outputs the persisted threadId string
(or 'none') instead of 'Thread ID present: yes/no'. This enables
the analytics extraction contract (spec §4.5a) to capture the actual
thread ID for cross-session linkage."
```

---

## Task 2: Fix codex_guard.py thread_id check

**Files:**
- Modify: `packages/plugins/cross-model/scripts/codex_guard.py:217-220`
- Test: `tests/test_codex_guard.py`

**Step 1: Write failing tests**

In `tests/test_codex_guard.py`, add tests for the `structuredContent.threadId` path. Find the `TestPost` class (around line 155) and add after the existing post tests:

```python
def test_post_thread_id_from_structured_content(self, tmp_path, monkeypatch) -> None:
    """thread_id_present is True when threadId is in structuredContent."""
    monkeypatch.setattr(MODULE, "_LOG_PATH", tmp_path / "events.jsonl")
    data = _post()
    data["tool_response"] = {
        "content": "response text",
        "structuredContent": {"threadId": "thread_abc123"},
    }
    MODULE.handle_post(data)
    log = json.loads((tmp_path / "events.jsonl").read_text().strip())
    assert log["thread_id_present"] is True

def test_post_thread_id_from_top_level_response(self, tmp_path, monkeypatch) -> None:
    """thread_id_present is True when threadId is at top level of tool_response."""
    monkeypatch.setattr(MODULE, "_LOG_PATH", tmp_path / "events.jsonl")
    data = _post()
    data["tool_response"] = {
        "content": "response text",
        "threadId": "thread_abc123",
    }
    MODULE.handle_post(data)
    log = json.loads((tmp_path / "events.jsonl").read_text().strip())
    assert log["thread_id_present"] is True

def test_post_thread_id_absent(self, tmp_path, monkeypatch) -> None:
    """thread_id_present is False when no threadId anywhere."""
    monkeypatch.setattr(MODULE, "_LOG_PATH", tmp_path / "events.jsonl")
    data = _post()
    MODULE.handle_post(data)
    log = json.loads((tmp_path / "events.jsonl").read_text().strip())
    assert log["thread_id_present"] is False
```

**Step 2: Run tests to verify the structuredContent test fails**

Run: `uv run pytest tests/test_codex_guard.py::TestPost::test_post_thread_id_from_structured_content -v`
Expected: FAIL — `assert log["thread_id_present"] is True` fails because the guard doesn't check `structuredContent.threadId` yet.

**Step 3: Fix the guard's thread_id_present computation**

In `packages/plugins/cross-model/scripts/codex_guard.py`, replace lines 217-220:

```python
    thread_id_present = bool(
        (isinstance(tool_input, dict) and tool_input.get("threadId"))
        or (isinstance(tool_response, dict) and tool_response.get("threadId"))
    )
```

with:

```python
    thread_id_present = bool(
        (isinstance(tool_input, dict) and tool_input.get("threadId"))
        or (isinstance(tool_response, dict) and tool_response.get("threadId"))
        or (
            isinstance(tool_response, dict)
            and isinstance(tool_response.get("structuredContent"), dict)
            and tool_response["structuredContent"].get("threadId")
        )
    )
```

**Step 4: Run all guard tests to verify fix**

Run: `uv run pytest tests/test_codex_guard.py -v`
Expected: ALL PASS (existing tests + 3 new tests)

**Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/codex_guard.py tests/test_codex_guard.py
git commit -m "fix(codex-guard): check structuredContent.threadId for thread_id_present

The guard only checked tool_response.get('threadId') (top-level) but the
Codex MCP server may return the thread ID in structuredContent.threadId
(the agent's primary source per consultation contract §10). This caused
thread_id_present to be false even when the agent had the ID.

Now checks 3 sources in order: tool_input.threadId (codex-reply),
tool_response.threadId (top-level), tool_response.structuredContent.threadId."
```

---

## Task 3: Add Step 7 (analytics emission) to dialogue SKILL.md

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:188` (after Step 6)

**Step 1: Add Step 7 section after Step 6**

In `packages/plugins/cross-model/skills/dialogue/SKILL.md`, after Step 6 "Present synthesis" (line 188) and before the "## Constants" section (line 190), insert:

```markdown
### Step 7: Emit analytics

After presenting synthesis to the user, emit a `dialogue_outcome` event to the shared event log. Analytics is best-effort — failures do not block the user from seeing the synthesis.

**7a. Parse synthesis output**

Extract structured fields from the `codex-dialogue` agent's Task tool return value:

| Field | Source | Extraction |
|-------|--------|------------|
| `resolved_count` | Synthesis Checkpoint | Count lines starting with `RESOLVED:` |
| `unresolved_count` | Synthesis Checkpoint | Count lines starting with `UNRESOLVED:` |
| `emerged_count` | Synthesis Checkpoint | Count lines starting with `EMERGED:` |
| `converged` | Summary "Converged:" field | `true` if value starts with "yes" (case-insensitive) |
| `turn_count` | Summary "Turns:" field | First integer in "Turns: {N} of {budget}" |
| `thread_id` | Continuation "Thread ID:" field | String after "Thread ID:" trimmed. If "none", use `null`. |
| `scout_count` | Continuation "Evidence:" field | First integer found, or 0 if "none" |

If any field cannot be parsed, use default: 0 for counts, `null` for strings, `false` for booleans.

**7b. Determine convergence reason**

| Condition | `convergence_reason_code` | `termination_reason` |
|-----------|--------------------------|---------------------|
| `converged` is true and `unresolved_count` is 0 | `all_resolved` | `convergence` |
| `converged` is true and `unresolved_count` > 0 | `natural_convergence` | `convergence` |
| `converged` is false and `turn_count` >= budget | `budget_exhausted` | `budget` |
| `converged` is false and `turn_count` < budget | `error` | `error` |

**7c. Assemble event**

Construct the JSON event object. Fields come from three sources:
- **Pipeline state** (available from earlier steps): `posture`, `turn_budget`, `profile_name`, `seed_confidence`, `low_seed_confidence_reasons`, `assumption_count`, `no_assumptions_fallback`, `gatherer_a_lines`, `gatherer_b_lines`, `gatherer_a_retry`, `gatherer_b_retry`, `citations_total`, `unique_files_total`, `gatherer_a_unique_paths`, `gatherer_b_unique_paths`, `shared_citation_paths`, `counter_count`, `confirm_count`, `open_count`, `claim_count`, `source_classes`, `scope_root_count`, `scope_roots_fingerprint`
- **Parsed from synthesis** (Step 7a): `resolved_count`, `unresolved_count`, `emerged_count`, `converged`, `turn_count`, `thread_id`, `scout_count`
- **Computed** (Step 7b + generated): `convergence_reason_code`, `termination_reason`, `consultation_id` (UUID v4), `ts` (ISO 8601 UTC), `session_id` (from environment)

```jsonc
{
  "schema_version": "0.1.0",
  "consultation_id": "{generated UUID v4}",
  "thread_id": "{parsed or null}",
  "session_id": "{Claude Code session ID}",
  "event": "dialogue_outcome",
  "ts": "{ISO 8601 UTC timestamp}",
  "posture": "{resolved posture}",
  "turn_count": 0,
  "turn_budget": 0,
  "profile_name": null,
  "mode": "server_assisted",
  "converged": false,
  "convergence_reason_code": "all_resolved",
  "termination_reason": "convergence",
  "resolved_count": 0,
  "unresolved_count": 0,
  "emerged_count": 0,
  "seed_confidence": "normal",
  "low_seed_confidence_reasons": [],
  "assumption_count": 0,
  "no_assumptions_fallback": false,
  "gatherer_a_lines": 0,
  "gatherer_b_lines": 0,
  "gatherer_a_retry": false,
  "gatherer_b_retry": false,
  "citations_total": 0,
  "unique_files_total": 0,
  "gatherer_a_unique_paths": 0,
  "gatherer_b_unique_paths": 0,
  "shared_citation_paths": 0,
  "counter_count": 0,
  "confirm_count": 0,
  "open_count": 0,
  "claim_count": 0,
  "scout_count": 0,
  "source_classes": [],
  "scope_root_count": 0,
  "scope_roots_fingerprint": null,
  "question_shaped": null,
  "shape_confidence": null,
  "assumptions_generated_count": null,
  "ambiguity_count": null,
  "provenance_unknown_count": null,
  "episode_id": null
}
```

**7d. Append to event log**

Append the JSON event as a single line to `~/.claude/.codex-events.jsonl`:

```bash
echo '{...event JSON...}' >> ~/.claude/.codex-events.jsonl
```

If the append fails (file permission error, disk full), log a warning to the user: "Analytics emission failed: {error}. This does not affect the consultation results." Do not retry.
```

**Step 2: Update the Constants table**

Add to the Constants table (after the existing entries):

```markdown
| Analytics schema version | 0.1.0 | Event schema version |
| Analytics event log | `~/.claude/.codex-events.jsonl` | Shared with codex_guard.py |
```

**Step 3: Verify the pipeline step count in any overview text**

Check if the SKILL.md mentions "6 steps" or "Steps 1-6" anywhere outside the step definitions. If so, update to "7 steps" / "Steps 1-7".

Run: `rg "6 step|Steps 1-6|step 6" packages/plugins/cross-model/skills/dialogue/SKILL.md -i`
Update any matches.

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(dialogue): add Step 7 analytics emission for dialogue_outcome events

Adds a new pipeline step after synthesis presentation that:
1. Parses codex-dialogue output for structured fields (counts, thread_id)
2. Determines convergence reason from parsed state
3. Assembles 30+ field dialogue_outcome event
4. Appends to ~/.claude/.codex-events.jsonl (best-effort, non-blocking)

Schema version 0.1.0. Provenance and planning fields nullable for forward
compatibility with E-TUNING and E-PLANNING enhancements."
```

---

## Task 4: Add analytics emission to codex SKILL.md

**Files:**
- Modify: `packages/plugins/cross-model/skills/codex/SKILL.md:202` (Diagnostics section)

**Step 1: Add analytics emission after Diagnostics**

In `packages/plugins/cross-model/skills/codex/SKILL.md`, find the Diagnostics section (line 202). After the existing diagnostics content (line 213 "Do not log prompt bodies..."), add a new section:

```markdown
### Analytics Emission

After capturing diagnostics, emit a `consultation_outcome` event to the shared event log. Analytics is best-effort — failures do not block the consultation response.

Construct and append a single JSON line to `~/.claude/.codex-events.jsonl`:

```jsonc
{
  "schema_version": "0.1.0",
  "consultation_id": "{generated UUID v4}",
  "thread_id": "{threadId from Codex response, or null}",
  "session_id": "{Claude Code session ID}",
  "event": "consultation_outcome",
  "ts": "{ISO 8601 UTC timestamp}",
  "posture": "{resolved posture from briefing}",
  "turn_count": 1,
  "turn_budget": 1,
  "profile_name": null,
  "mode": "server_assisted",
  "converged": null,
  "termination_reason": "complete"
}
```

For multi-turn `/codex` consultations (continued with `codex-reply`), increment `turn_count` for each round-trip. `turn_budget` remains 1 (standalone consultations have no pre-set budget).

Append using:
```bash
echo '{...event JSON...}' >> ~/.claude/.codex-events.jsonl
```

If the append fails, log a warning. Do not retry.
```

**Step 2: Update the Diagnostics section to reference analytics**

At line 179, the existing text says "After relaying, capture diagnostics for this consultation (see Diagnostics section...)". After this line, add:

```markdown
After diagnostics, emit a `consultation_outcome` analytics event (see [Analytics Emission](#analytics-emission) section).
```

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/skills/codex/SKILL.md
git commit -m "feat(codex): add consultation_outcome analytics emission

Standalone /codex consultations now emit consultation_outcome events to
~/.claude/.codex-events.jsonl with reduced schema (no gatherer metrics,
no seed_confidence). Provides unified analytics stream for all cross-model
consultations alongside dialogue_outcome events from /dialogue."
```

---

## Task 5: Update README.md event table

**Files:**
- Modify: `packages/plugins/cross-model/README.md:68-72`

**Step 1: Add new event types to the table**

In `packages/plugins/cross-model/README.md`, find the event log table (line 68). After the `consultation` row (line 72), add two new rows:

```markdown
| `dialogue_outcome` | `/dialogue` Step 7 | `schema_version`, `consultation_id`, `thread_id`, `session_id`, `event`, `ts`, `posture`, `turn_count`, `turn_budget`, `profile_name`, `mode`, `converged`, `convergence_reason_code`, `termination_reason`, `resolved_count`, `unresolved_count`, `emerged_count`, `seed_confidence`, `low_seed_confidence_reasons`, `assumption_count`, `no_assumptions_fallback`, gatherer metrics, scope envelope, nullable planning/provenance fields |
| `consultation_outcome` | `/codex` post-diagnostics | `schema_version`, `consultation_id`, `thread_id`, `session_id`, `event`, `ts`, `posture`, `turn_count`, `turn_budget`, `profile_name`, `mode`, `converged`, `termination_reason` |
```

**Step 2: Add schema version note**

Below the table, add:

```markdown
`dialogue_outcome` and `consultation_outcome` events use `schema_version` for forward compatibility. See `docs/plans/2026-02-19-cross-model-plugin-enhancements.md` §4.4 for version semantics.
```

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/README.md
git commit -m "docs: add dialogue_outcome and consultation_outcome to event log table"
```

---

## Task 6: Marketplace update + dialogue integration test

**Files:** No file changes — runtime verification.

**Step 1: Update marketplace and reinstall plugin**

```bash
claude plugin marketplace update cross-model
claude plugin install cross-model@cross-model
```

Verify the installed SHA matches the branch tip:
```bash
git rev-parse HEAD
```
Compare with the `gitCommitSha` in `~/.claude/plugins/installed_plugins.json`.

**Step 2: Note the current JSONL event count**

```bash
wc -l ~/.claude/.codex-events.jsonl
```

Record the line count as the baseline.

**Step 3: Run a `/dialogue` invocation**

In a new Claude Code session (or this one after restart), run:
```
/dialogue -p evaluative -n 4 "Is the analytics emission in the /dialogue skill well-designed?"
```

This is both a real review and an integration test.

**Step 4: Verify `dialogue_outcome` event emitted**

```bash
jq 'select(.event == "dialogue_outcome")' ~/.claude/.codex-events.jsonl | tail -1
```

**Verify these fields are present and valid:**
- `schema_version` = `"0.1.0"`
- `consultation_id` is a UUID string
- `event` = `"dialogue_outcome"`
- `ts` is ISO 8601 format
- `posture` = `"evaluative"`
- `turn_count` > 0
- `turn_budget` = 4
- `resolved_count` + `unresolved_count` + `emerged_count` > 0
- `seed_confidence` is `"normal"` or `"low"`
- `gatherer_a_lines` > 0
- `thread_id` is a string (not a boolean, not "yes/no")

**Step 5: Verify JSONL file integrity**

```bash
jq empty ~/.claude/.codex-events.jsonl
```

Expected: exits 0 (all lines are valid JSON). If this fails, there's a formatting issue in the emitted event.

---

## Task 7: Codex integration test

**Files:** No file changes — runtime verification.

**Step 1: Run a `/codex` invocation**

```
/codex "What is the purpose of the seed_confidence field in the dialogue pipeline?"
```

**Step 2: Verify `consultation_outcome` event emitted**

```bash
jq 'select(.event == "consultation_outcome")' ~/.claude/.codex-events.jsonl | tail -1
```

**Verify these fields are present and valid:**
- `schema_version` = `"0.1.0"`
- `consultation_id` is a UUID string
- `event` = `"consultation_outcome"`
- `ts` is ISO 8601 format
- `turn_count` >= 1
- `turn_budget` = 1
- `termination_reason` = `"complete"`
- `thread_id` is a string or null (not a boolean)

**Step 3: Verify existing events unchanged**

```bash
jq 'select(.event == "consultation")' ~/.claude/.codex-events.jsonl | tail -1
```

Expected: Existing `consultation` events (from `codex_guard.py`) still have the same schema. The new `consultation_outcome` events coexist alongside them.

**Step 4: Final JSONL integrity check**

```bash
wc -l ~/.claude/.codex-events.jsonl
jq empty ~/.claude/.codex-events.jsonl
```

Expected: Line count increased by at least 2 (one `dialogue_outcome` + one `consultation_outcome`), all lines valid JSON.

---

## Final Verification

After all tasks:

1. Run: `jq 'select(.event == "dialogue_outcome")' ~/.claude/.codex-events.jsonl`
   Expected: At least 1 record with all required fields (schema_version, consultation_id, event, ts, posture, turn_count, etc.)

2. Run: `jq 'select(.event == "consultation_outcome")' ~/.claude/.codex-events.jsonl`
   Expected: At least 1 record with reduced schema fields

3. Verify existing events still work: `jq 'select(.event == "consultation")' ~/.claude/.codex-events.jsonl`
   Expected: Existing records unchanged

4. Run guard tests: `uv run pytest tests/test_codex_guard.py -v`
   Expected: ALL PASS (existing + 3 new tests)

## Summary of Deliverables

| File | New/Modified | What This Plan Adds |
|------|-------------|---------------------|
| `agents/codex-dialogue.md` | Modified | Thread ID value output (was boolean) |
| `scripts/codex_guard.py` | Modified | `structuredContent.threadId` check added to `thread_id_present` |
| `tests/test_codex_guard.py` | Modified | 3 new tests for thread_id_present extraction |
| `skills/dialogue/SKILL.md` | Modified | Step 7: analytics emission with extraction contract |
| `skills/codex/SKILL.md` | Modified | Analytics emission step for standalone consultations |
| `README.md` | Modified | Two new event types in event log table |

All paths relative to `packages/plugins/cross-model/` except `tests/test_codex_guard.py` (repo root).

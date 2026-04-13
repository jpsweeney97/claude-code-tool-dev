---
name: shakedown-b1
description: Run the B1 pre-benchmark integration shakedown. Writes containment seed, spawns the shakedown-dialogue agent, captures artifacts. Use when the user invokes /shakedown-b1 or asks to run a shakedown.
user-invocable: true
allowed-tools: Bash, Read, Write, Agent, mcp__plugin_codex-collaboration_codex-collaboration__codex.status
---

# Shakedown B1

Operator-facing harness that orchestrates the pre-benchmark integration shakedown lifecycle: preflight, seed, spawn, capture.

## Procedure

### 1. Determine repo root

```bash
git rev-parse --show-toplevel
```

If this fails, report "not in a git repository" and stop.

### 2. Preflight: runtime health

Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.status` with `repo_root` from step 1.

- If `auth_status` is `"missing"`: report auth remediation and stop.
- If `errors` is non-empty: report errors and stop.

### 3. Read session ID

Read the file at `${CLAUDE_PLUGIN_DATA}/session_id` (written by `publish_session_id.py` at session start).

- If the file does not exist or is empty: report "session_id not published — check SessionStart hook" and stop.

### 4. Stale cleanup

Run via Bash:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/clean_stale_shakedown.py"
```

This removes seed, scope, active-run, and completion-marker files older than 24 hours from prior runs. Runs before seed creation to prevent stale containment state from a crashed prior run.

- If the script fails: report the error and stop.

### 5. Single-active-run check

Read `${CLAUDE_PLUGIN_DATA}/shakedown/active-run-<session_id>`. If it exists:

1. Read the `run_id` it contains.
2. Check for BOTH `scope-<run_id>.json` and `seed-<run_id>.json`.
3. If either file exists, a prior shakedown is still active. Report: "A shakedown run is already active in this session (run_id: `<run_id>`, state: seed|scope). Wait for it to complete or manually remove the state files." Stop.

### 6. Generate run_id

Generate a UUID4.

### 7. Write seed file and active-run pointer

Create `${CLAUDE_PLUGIN_DATA}/shakedown/` directory if needed.

Write `active-run-<session_id>` containing the `run_id` (plain text).

Write `seed-<run_id>.json`:

```json
{
  "session_id": "<session_id>",
  "run_id": "<run_id>",
  "file_anchors": [
    "<repo_root>/docs/superpowers/specs/codex-collaboration/contracts.md",
    "<repo_root>/docs/superpowers/specs/codex-collaboration/delivery.md",
    "<repo_root>/packages/plugins/codex-collaboration/server/mcp_server.py"
  ],
  "scope_directories": [
    "<repo_root>/docs/superpowers/specs/codex-collaboration/",
    "<repo_root>/packages/plugins/codex-collaboration/server/"
  ],
  "created_at": "<ISO timestamp>"
}
```

`scope_directories` are deduplicated parent directories of the `file_anchors`. All three scouting tools use the same scope boundary: a file is in scope if it is a file anchor or within a scope directory.

### 8. Write initial metadata

Write `${CLAUDE_PLUGIN_DATA}/shakedown/metadata-<run_id>.json` immediately after seed creation. This ensures metadata exists on all exit paths, including failures:

```json
{
  "run_id": "<run_id>",
  "session_id": "<session_id>",
  "task_id": "B1",
  "classification": "pre_benchmark_integration_shakedown",
  "commit_sha": "<output of git rev-parse HEAD>",
  "timestamp": "<ISO timestamp>",
  "file_anchors": ["<...>"],
  "scope_directories": ["<...>"],
  "result": null
}
```

`result` starts as `null` and is overwritten on failure or completion (step 11).

### 9. Spawn agent

Use the Agent tool:

```
Agent(
  subagent_type="shakedown-dialogue",
  prompt="""You are running a pre-benchmark integration shakedown on task B1.

**Task:** Conduct a structured dialogue with Codex about the codex-collaboration
package, then scout Codex's factual claims against the source code.

**Opening question for Codex:** "Describe the architecture of the
codex-collaboration server: its major components, their responsibilities,
and how they interact during a dialogue session."

**Repository root:** <repo_root>
**Scope directories:** <scope_directories as JSON array>

Your Read, Grep, and Glob calls are constrained to the scope directories
by the containment guard. You can access any file within those directories.

**Begin by calling `codex.dialogue.start` with repo_root to create a dialogue
handle. Then send the opening question above as the `objective` parameter on
your first `codex.dialogue.reply` call using the returned collaboration_id.**
After receiving Codex's first reply, follow the dialogue-codex skill procedure."""
)
```

Required template fields: task framing, opening Codex question, `repo_root`, `scope_directories`, two-step dialogue initiation (`start` creates handle, first `reply` sends the question).

### 10. Verify transcript capture

After the Agent tool returns, check for completion markers:

1. Check `${CLAUDE_PLUGIN_DATA}/shakedown/transcript-<run_id>.done`
2. If `.done` exists: transcript is at `transcript-<run_id>.jsonl`. Proceed.
3. If `.error` exists: read its contents, update metadata `result` to `"transcript_error"`, report the error, and stop.
4. If neither exists: wait 1 second, check again. If still absent: update metadata `result` to `"transcript_capture_failure"`, report "Transcript capture did not complete — SubagentStop hook may have failed silently", and stop.

If the Agent tool itself fails (spawn error, unexpected termination): update metadata `result` to `"agent_spawn_failure"`, report the error, and stop.

### 11. Capture remaining artifacts

**Inspection template:** Write to `${CLAUDE_PLUGIN_DATA}/shakedown/inspection-<run_id>.md` with a 14-item checklist:

```markdown
# Shakedown Inspection: <run_id>

## Per-Turn Checks (items 1-7)
- [ ] 1. Exactly one state block per turn with correct sentinel
- [ ] 2. All 13 top-level fields present, correct types
- [ ] 3. First emitted state block has `turn: 2`
- [ ] 4. Subsequent `turn` values are strictly increasing
- [ ] 5. Counter arithmetic consistent (sum of statuses = total_claims)
- [ ] 6. effective_delta is per-turn (not cumulative)
- [ ] 7. Scouting turns have >=1 definition + >=1 falsification query
- [ ] 8. Non-scouting turns have correct empty-field values

## Terminal Checks (items 9-11)
- [ ] 9. Terminal turn has epilogue with all 3 fields
- [ ] 10. converged derivation matches ledger state
- [ ] 11. effective_delta_overall is cumulative across all turns

## Containment Checks (items 12-14)
- [ ] 12. All Read/Grep/Glob calls within scope directories
- [ ] 13. No Bash/Write/Edit/Agent tool calls
- [ ] 14. No prohibited artifact names emitted
```

Update metadata `result` to `"artifacts_staged"` after all artifacts are written. This is NOT adjudication — the harness stages lifecycle artifacts; the operator performs inspection and determines the final result (`pass` / `fail` / `inconclusive`) separately.

### 12. Report

Present to the operator:
- Run ID
- Transcript location (`transcript-<run_id>.jsonl`)
- Metadata location (`metadata-<run_id>.json`)
- Inspection template location (`inspection-<run_id>.md`)
- Summary: how many turns, whether `converged`, final counter snapshot

Then: "Artifacts staged. Apply the 14-item inspection checklist to the transcript to determine the run result."

## Failure Handling

| Condition | Behavior |
|-----------|----------|
| `codex.status` unavailable | Report: plugin may not be installed. Stop |
| `session_id` missing | Report: SessionStart hook may not have fired. Stop |
| Stale cleanup fails | Report error. Stop |
| Active run detected | Report run_id and state. Stop |
| Agent spawn fails | Update metadata `result` to `"agent_spawn_failure"`. Report error. Stop |
| Transcript `.error` exists | Update metadata `result` to `"transcript_error"`. Report error. Stop |
| Transcript markers missing | Update metadata `result` to `"transcript_capture_failure"`. Report. Stop |

## Scope

This skill handles lifecycle orchestration: preflight, seed, spawn, transcript capture, artifact staging. It does NOT perform inspection or adjudication. The operator applies the 14-item inspection checklist to the transcript and determines the run result (`pass` / `fail` / `inconclusive`) as a separate step.

## Verification Gate

Lifecycle staging succeeds when:
- Seed created in `${CLAUDE_PLUGIN_DATA}/shakedown/`
- SubagentStart fires (seed promoted to scope)
- Agent runs contained (Read/Grep/Glob within scope)
- SubagentStop fires (scope removed, transcript written)
- Metadata (`result: "artifacts_staged"`), transcript, and inspection template all written

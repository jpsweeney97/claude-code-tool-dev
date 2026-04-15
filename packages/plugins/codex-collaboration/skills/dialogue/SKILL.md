---
name: dialogue
description: Run a production Codex dialogue against the codebase. Spawns the dialogue-orchestrator agent and surfaces the production synthesis artifact. Use when the user invokes /dialogue or asks to start a Codex dialogue about code.
user-invocable: true
allowed-tools: Bash, Read, Write, Agent
---

# /dialogue

Production dialogue harness. Runs preflight cleanup, writes containment seed, spawns the dialogue-orchestrator agent, and surfaces the production synthesis artifact.

**Invocation:** `/dialogue <objective>` — the entire argument string after `/dialogue` is the objective. No flags, no optional positional arguments.

## Procedure

### 1. Capture objective

The full argument string after `/dialogue` is the objective. No flag tokenization — capture verbatim.

If the objective is empty or whitespace-only, ask the user: "What would you like to discuss with Codex?" and stop.

### 2. Determine repo root

```bash
git rev-parse --show-toplevel
```

If this fails, report "not in a git repository" and stop.

### 3. Read session ID

Read the file at `${CLAUDE_PLUGIN_DATA}/session_id` (written by `publish_session_id.py` at session start).

- If the file does not exist or is empty: report "session_id not published — check SessionStart hook" and stop.

### 4. Stale cleanup

Run via Bash:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/clean_stale_shakedown.py"
```

Removes seed, scope, active-run, and completion-marker files older than 24 hours from prior runs. Runs before seed creation to prevent stale containment state from a crashed prior run from tripping the live-run check in step 5.

- If the script fails: report the error and stop.

### 5. Single-active-run check

Read `${CLAUDE_PLUGIN_DATA}/shakedown/active-run-<session_id>`. If it exists:

1. Read the `run_id` it contains.
2. Check for BOTH `scope-<run_id>.json` and `seed-<run_id>.json`.
3. If either file exists, a prior contained run is still active. Report: "A contained run is already active in this session (run_id: `<run_id>`, state: seed|scope). Wait for it to complete or manually remove the state files." Stop.

### 6. Write seed and active-run pointer

Generate a UUID4 `run_id`.

Create `${CLAUDE_PLUGIN_DATA}/shakedown/` directory if needed.

Write `active-run-<session_id>` containing `run_id` (plain text).

Write `seed-<run_id>.json`:

```json
{
  "session_id": "<session_id>",
  "run_id": "<run_id>",
  "file_anchors": [],
  "scope_directories": ["<repo_root>"],
  "created_at": "<ISO timestamp>"
}
```

`file_anchors` is empty for v1. `scope_directories` is repo root only — coarse containment per plan §5.1.

### 7. Dispatch orchestrator

Use the Agent tool:

```
Agent(
  subagent_type="dialogue-orchestrator",
  prompt="""<objective>

Repository root: <repo_root>
Scope directories: ["<repo_root>"]"""
)
```

The orchestrator performs inline scouting, starts the Codex dialogue, runs the per-turn verification loop, and returns the production synthesis artifact.

### 8. Surface synthesis

Extract the production synthesis artifact from the orchestrator's output by locating the `<PRODUCTION_SYNTHESIS>` sentinel and parsing the JSON inside it.

**If the artifact is present**, surface it in this exact order:

**Summary line:**

```
**<termination_code>** | converged: <converged> | turns: <turn_count>/<turn_budget> | mode: <mode> | mode_source: <mode_source>
```

**Synthesis:**

Display `final_synthesis` as prose.

**Claims:**

| Claim | Status | Citation |
|---|---|---|
| \<text\> | \<final_status\> | \<representative_citation\> |

One row per `final_claims[]` entry.

**Citations:**

- `<path>:<line_range>` — \<snippet\>

One line per `synthesis_citations[]` entry.

**Ledger Summary:**

Display `ledger_summary`.

**Canonical Artifact:**

```json
<full production synthesis artifact JSON, pretty-printed>
```

The Markdown sections above are a **view** of this canonical artifact. The JSON is the **source of truth**. Every Markdown field is a transparent projection of the corresponding JSON field — do NOT compute any field differently between the two renderings.

Do NOT wrap the JSON appendix in `<details>` tags or depend on collapsible rendering behavior. Plain fenced JSON is the portable default.

**If the `<PRODUCTION_SYNTHESIS>` sentinel is missing or its JSON is unparseable**, report: "Orchestrator did not return a production synthesis artifact. Raw output:" followed by the orchestrator's returned message verbatim.

## Failure Handling

| Condition | Behavior |
|-----------|----------|
| Empty objective | Ask user for objective. Stop |
| Not in git repository | Report. Stop |
| `session_id` missing | Report: SessionStart hook may not have fired. Stop |
| Stale cleanup fails | Report error. Stop |
| Active run detected | Report run_id and state. Stop |
| Agent spawn/run fails | Report raw orchestrator output. Stop |
| Synthesis artifact unparseable | Report raw output. Stop |

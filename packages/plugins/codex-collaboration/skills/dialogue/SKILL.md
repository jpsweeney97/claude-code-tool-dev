---
name: dialogue
description: Run a production Codex dialogue against the codebase. Spawns pre-dialogue gatherer agents, assembles a briefing, then spawns the dialogue-orchestrator agent and surfaces the production synthesis artifact. Use when the user invokes /dialogue or asks to start a Codex dialogue about code.
user-invocable: true
allowed-tools: Bash, Read, Write, Agent
---

# /dialogue

Production dialogue harness. Dispatches pre-dialogue gatherer agents, assembles a deterministic briefing, writes containment seed, spawns the dialogue-orchestrator agent, and surfaces the production synthesis artifact.

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

### 5. Single-active-run check (revised)

Generate a UUID4 `run_id`. This single value is carried through the entire lifecycle (active-run pointer, seed, orchestrator dispatch, cleanup).

Read `${CLAUDE_PLUGIN_DATA}/shakedown/active-run-<session_id>`. If the file does not exist, proceed to step 5-lock.

If the file exists, read the `run_id` it contains and perform a two-tier liveness inspection:

| State | Detection | Action |
|---|---|---|
| Live run | `seed-<run_id>.json` or `scope-<run_id>.json` exists | Block: "A dialogue is already in progress in this session (run_id: `<run_id>`). Wait for it to complete or manually remove the state files." Stop. |
| Abandoned pointer | No seed/scope for the pointer's `run_id` | Delete the stale pointer via Bash (`trash <path>`), log "Cleaned up abandoned active-run pointer", proceed to step 5-lock. |

**Rationale:** Within a single Claude Code session, the skill runs sequentially. The only scenario where this session's active-run pointer exists at step 5 is a prior invocation that crashed before its finally block could clean up. The seed/scope check is sufficient because the pointer is session-scoped and the skill is sequential. No mtime-based age check is needed.

### 5-lock. Write active-run pointer

Create `${CLAUDE_PLUGIN_DATA}/shakedown/` directory if needed.

Write `active-run-<session_id>` containing the `run_id` from step 5 (plain text, unchanged format). This acquires the session lock before any long-running work. The gatherer pipeline runs under this lock.

**All subsequent steps (5a through 8) execute under a try/finally guard.** The finally block deletes `active-run-<session_id>` to release the lock on every exit path — success, failure, or error. See §Lock Lifecycle below.

### 5a. Extract assumptions

From the objective, identify testable assumptions and assign sequential IDs (A1, A2, ...). Cap at 5. Apply tautology filter: reject assumptions that restate or negate the objective itself. When in doubt, keep the assumption.

If no testable assumptions exist (e.g., "How does X work?"), pass an empty list to the falsifier. The falsifier's no-assumptions fallback activates.

Extract 3-8 key terms from the objective for the code explorer.

### 5b. Dispatch gatherers (parallel)

Launch both gatherers in parallel via the Agent tool:

```
Agent(
  subagent_type="context-gatherer-code",
  prompt="Objective: {objective}\n\nKey terms: {comma-separated terms}"
)

Agent(
  subagent_type="context-gatherer-falsifier",
  prompt="Objective: {objective}\n\nAssumptions:\n- A1: {text}\n- A2: {text}\n..."
)
```

If assumptions list is empty, the falsifier prompt reads: `Assumptions:\n(none)`

Both gatherers are read-only (Glob, Grep, Read only) and run outside containment. They do NOT interact with the Codex API.

**Execution bounds.** Each gatherer agent has `maxTurns: 20` in its definition, which caps the number of tool calls per gatherer. This is the primary mechanism for bounding gatherer execution — the Agent tool does not support wall-clock timeouts. If a gatherer exhausts its turn budget without emitting output, the assembly pipeline treats it as a low-output gatherer (step 2 retry, then step 3 fallback).

**Failure during gathering.** If either Agent call returns an error (e.g., agent spawn failure), treat the failed gatherer's output as empty and continue to step 5c. The assembly pipeline's retry and fallback steps handle missing or insufficient output. Do NOT stop the procedure on gatherer failure — the orchestrator can operate without a briefing (v1 behavior).

### 5c. Assemble briefing (deterministic pipeline)

Run the 10-step deterministic assembly pipeline on gatherer outputs. No LLM participates in assembly — it is parse-and-compose only. Treat the code explorer as Gatherer A and the falsifier as Gatherer B.

| Step | Name | Operation |
|---|---|---|
| 1 | Parse | Extract tagged lines from each gatherer's output; ignore untagged text |
| 2 | Retry | If a gatherer produced <4 parseable lines, re-launch once with a format-reinforcing prompt (see below); parse retry output; merge with original (retry-wins on duplicate key: same tag type + normalized citation) |

**Retry prompts** (step 2). The retry prompt is gatherer-specific to respect each agent's provenance domain:
- **Code explorer retry:** "Emit prefix-tagged lines per the tag grammar. Each CLAIM needs `@ path:line` and `[SRC:code]`."
- **Falsifier retry:** "Emit prefix-tagged lines per the tag grammar. Each CLAIM needs `@ path:line` and `[SRC:docs]`. Each COUNTER needs `@ path:line`, `AID:<id>`, and `TYPE:<type>`."
| 3 | Fallback | If total parseable lines across both gatherers is 0 after retries, produce the fallback briefing (see below); skip steps 4-10 |
| 4 | Discard | Remove CLAIM/COUNTER/CONFIRM missing `@ path:line`; remove COUNTER/CONFIRM missing `AID:`; remove COUNTER missing `TYPE:`; remove empty-content lines |
| 5 | Cap | If >3 COUNTER lines remain, keep first 3 by appearance order |
| 6 | Sanitize | Scan remaining content for credential patterns (AWS keys, PEM blocks, JWT tokens, GitHub PATs). Remove any line containing a match. |
| 7 | Dedup | Same tag type + normalized citation across gatherers → keep Gatherer A's version. Different tag types at same citation are both retained. Normalize key: strip leading `./`, lowercase path, collapse `//` |
| 8 | Provenance | For each CLAIM line missing `[SRC:code]` or `[SRC:docs]`, assign `[SRC:unknown]` and increment `provenance_unknown_count`. Does not drop lines. |
| 9 | Group | Deterministic order (Gatherer A items first within each section): Context (OPEN + COUNTER + CONFIRM), Material (CLAIM), Question (objective verbatim) |
| 10 | Health check | Count citations and unique files; compute `briefing_quality` (see below) |

**Briefing quality** (step 10):

| Field | Type | Computation |
|---|---|---|
| `total_citations` | int | Count of lines with `@ path:line` |
| `unique_files` | int | Count of distinct file paths cited |
| `provenance_unknown` | int | From step 8 |
| `warnings` | list | Reason codes (see below) |

Warning codes:
- `thin_citations` — `total_citations` < 8
- `few_files` — `unique_files` < 5
- `provenance_violations` — `provenance_unknown` >= 2

Warnings inform the orchestrator but do NOT block the dialogue.

**Assembled briefing format:**

```
<!-- dialogue-orchestrated-briefing -->
<!-- briefing-meta: {"total_citations": <N>, "unique_files": <N>, "provenance_unknown": <N>, "warnings": [<codes>]} -->

## Seed Evidence

This section is an external briefing assembled from pre-dialogue gatherer
agents. It is seed evidence, not verified ledger state. Use it to
reprioritize Phase 1 targets (focus on gaps and OPEN items), but do NOT
suppress Phase 1 reads based on gatherer CLAIMs. Seed-derived facts
referenced in the synthesis must carry `citation_tier: "seed"`.

### Context

{OPEN items}
{COUNTER items}
{CONFIRM items}

### Material

{CLAIM items}

## Objective

{user's objective, verbatim}
```

**Fallback briefing** (step 3, when total parseable lines = 0):

```
<!-- dialogue-orchestrated-briefing -->
<!-- briefing-meta: {"total_citations": 0, "unique_files": 0, "provenance_unknown": 0, "warnings": ["zero_output"]} -->

## Seed Evidence

This section is an external briefing assembled from pre-dialogue gatherer
agents. It is seed evidence, not verified ledger state. Use it to
reprioritize Phase 1 targets, but do NOT suppress Phase 1 reads based on
gatherer CLAIMs. Seed-derived facts referenced in the synthesis must
carry `citation_tier: "seed"`.

(Context gathering produced insufficient results. Rely on inline scouting
and per-turn verification for evidence.)

## Objective

{user's objective, verbatim}
```

### 5d. Briefing-quality log

Log a brief quality summary for the user:
- Number of findings from each gatherer (e.g., "Code explorer: 18 lines, Falsifier: 12 lines")
- Warning codes, if any
- "Briefing assembled. Launching orchestrator."

This is informational, not blocking.

### 6. Write containment seed

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

`file_anchors` is empty. `scope_directories` is repo root only — coarse containment.

The active-run pointer already exists (from step 5-lock). The seed is written just before orchestrator dispatch so the SubagentStart hook can materialize scope.

### 7. Dispatch orchestrator (modified)

Prepend the assembled briefing to the original dispatch prompt. The original v1 dispatch prompt (objective, repo root, scope) is preserved unchanged after the briefing:

```
Agent(
  subagent_type="dialogue-orchestrator",
  prompt="""{assembled_briefing}

{objective}

Repository root: <repo_root>
Scope directories: ["<repo_root>"]"""
)
```

The objective appears twice: once inside the briefing's `## Objective` section (for the assembler's record) and once as the top-level field after the briefing (for the orchestrator to use directly as the canonical objective in Phase 2). The orchestrator MUST use the top-level objective — the one after the briefing block — as the value it sends to `codex.dialogue.reply` in Phase 2. The briefing's `## Objective` section exists for structural completeness; the top-level field is the operative input.

The briefing is delimited by the `<!-- dialogue-orchestrated-briefing -->` sentinel. The orchestrator detects the sentinel to know that pre-dialogue gathering occurred. If the sentinel is absent (e.g., this code path was not reached), the orchestrator proceeds with Phase 1 inline scouting as its sole pre-dialogue exploration — identical to v1 behavior.

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
| \<text\> | \<final_status\> | \<representative_citation or —\> |

One row per `final_claims[]` entry. If `representative_citation` is `null`, render `—` (em-dash) in the Citation column. This signals "claim was registered but not independently verified against a specific file during the dialogue."

**Citations:**

- `<path>:<line_range>` — \<snippet\> `[<citation_tier>]`

One line per `synthesis_citations[]` entry. Append the `citation_tier` value (`seed` or `dialogue`) in brackets.

**Ledger Summary:**

Display `ledger_summary`.

**Canonical Artifact:**

```json
<full production synthesis artifact JSON, pretty-printed>
```

The Markdown sections above are a **view** of this canonical artifact. The JSON is the **source of truth**. Every Markdown field is a transparent projection of the corresponding JSON field — do NOT compute any field differently between the two renderings.

Do NOT wrap the JSON appendix in `<details>` tags or depend on collapsible rendering behavior. Plain fenced JSON is the portable default.

**If the `<PRODUCTION_SYNTHESIS>` sentinel is missing or its JSON is unparseable**, report: "Orchestrator did not return a production synthesis artifact. Raw output:" followed by the orchestrator's returned message verbatim.

## Lock Lifecycle

The `/dialogue` skill is the release owner for the `active-run-<session_id>` lock.

**Acquire:** Step 5-lock writes `active-run-<session_id>` with plain-text `run_id`.

**Release pattern:** Steps 5a through 8 execute under a try/finally guard:

```
run_id = uuid4()                          # step 5
write active-run-<session_id>             # step 5-lock: acquire
  content: run_id (plain text)
try:
    extract assumptions                   # step 5a
    dispatch gatherers                    # step 5b
    assemble briefing                     # step 5c
    log quality                           # step 5d
    write seed-<run_id>.json              # step 6
    dispatch orchestrator                 # step 7
    surface synthesis                     # step 8
finally:
    delete active-run-<session_id>        # release
```

**Release (success):** After step 8 completes, remove `active-run-<session_id>` via `trash`. This allows the user to run another `/dialogue` in the same session.

**Release (failure):** If any step between 5a and 8 fails — gatherer exhaustion, assembly error, seed write failure, orchestrator crash — remove `active-run-<session_id>` via `trash` before reporting the error to the user.

**Crash recovery:** If the skill cannot run its finally block (context exhaustion, user kill), the pointer persists. The next `/dialogue` in the same session encounters it in step 5 and applies the two-tier liveness check: no seed/scope → delete pointer and proceed; seed/scope present → block (24h stale sweep handles this rare edge case). A new session gets a new `session_id` and is unaffected.

## Failure Handling

| Condition | Behavior |
|-----------|----------|
| Empty objective | Ask user for objective. Stop |
| Not in git repository | Report. Stop |
| `session_id` missing | Report: SessionStart hook may not have fired. Stop |
| Stale cleanup fails | Report error. Stop |
| Active run detected (live) | Report run_id and state. Stop |
| Active run detected (abandoned) | Clean up pointer, proceed |
| Gatherer exhausts maxTurns | Treat partial output as low-output; assembly retry and fallback handle it. Continue |
| Gatherer spawn failure | Treat as empty output; assembly fallback handles it. Continue |
| Assembly produces zero output | Fallback briefing used. Continue |
| Seed write fails | Report error. Stop (finally releases lock) |
| Agent spawn/run fails | Report raw orchestrator output. Stop (finally releases lock) |
| Synthesis artifact unparseable | Report raw output. Stop (finally releases lock) |

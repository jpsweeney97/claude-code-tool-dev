---
name: dialogue
description: "Multi-turn Codex consultation with proactive context gathering. Launches parallel codebase explorers, assembles a structured briefing, and delegates to codex-dialogue. Use when you need a thorough, evidence-backed consultation, deep codebase analysis before asking Codex, or when the user says 'deep review', 'explore and discuss', or 'thorough consultation'. For quick single-turn questions, use /codex."
argument-hint: '"question" [-p posture] [-n turns] [--profile name] [--plan]'
user-invocable: true
allowed-tools: mcp__plugin_cross-model_codex__codex, mcp__plugin_cross-model_codex__codex-reply, mcp__plugin_cross-model_context-injection__process_turn, mcp__plugin_cross-model_context-injection__execute_scout
---

# Dialogue — Orchestrated Codex Consultation

Launch a multi-turn Codex dialogue with proactive context gathering. Two parallel agents explore the codebase before the dialogue starts, assembling a structured briefing that gives Codex richer initial context.

**For quick single-turn questions:** Use `/codex` instead.

## Preconditions

Before proceeding, verify MCP tools are available:
- `mcp__plugin_cross-model_codex__codex` and `mcp__plugin_cross-model_codex__codex-reply`
- `mcp__plugin_cross-model_context-injection__process_turn` and `mcp__plugin_cross-model_context-injection__execute_scout`

If any tool is unavailable, report which tools are missing and stop. Do not attempt to run the pipeline without all 4 tools.

## Arguments

Parse flags from `$ARGUMENTS`:

| Flag | Short | Values | Default |
|------|-------|--------|---------|
| `--posture` | `-p` | `adversarial`, `collaborative`, `exploratory`, `evaluative` | `collaborative` |
| `--turns` | `-n` | 1-15 | 8 |
| `--profile` | — | Named preset from [`consultation-profiles.yaml`](../../references/consultation-profiles.yaml) | none |
| `--plan` | — | boolean | false |

Everything after flags is the **question** (required).

**Resolution order:** explicit flags > profile values > defaults.

**Profile resolution:** Profiles set `posture`, `turn_budget`, and `reasoning_effort`. Execution controls (`sandbox`, `approval_policy`) use consultation contract defaults.

**Validation:**
1. Reject unknown flags.
2. Reject invalid enum values for `--posture`.
3. Reject `--turns` outside 1-15.
4. If question is empty after flag extraction, ask the user: "What would you like to discuss with Codex?"
5. If `--plan` is present without a question/problem statement, ask the user: "What problem would you like to plan?"

Error format: `argument parsing failed: {reason}. Got: {input!r:.100}`

## Pipeline

### Step 0: Question shaping (when `--plan` is set)

Skip this step if `--plan` is not set. Proceed directly to Step 1.

**Debug gate:** Before decomposition, check if the question is a debugging question. If ANY of these artifact signals appear in the question (case-insensitive): `traceback`, `stack trace`, `exception`, `panic`, `segfault` — OR if an intent signal (`how do I fix`, `how do we fix`, `debug`, `root cause`, `why does`) appears together with an unsuppressed failure lexeme (`fail`, `failing`, `failed`, `failure`, `error`, `bug`, `crash`, `broken`) — then skip Step 0 entirely. Set all planning pipeline fields to null. Proceed to Step 1 with the raw question.

Architecture phrase suppressions (a suppression phrase suppresses a failure lexeme only when the lexeme appears as a substring of the suppression phrase, and that suppression phrase appears in the question): `error handling`, `failure mode`, `failure modes`, `fault tolerance`, `error budget`, `recovery strategy`, `retry policy`, `crash-only design`.

Example: "How should we design error handling for the API?" → NOT a debugging question (failure lexeme "error" is suppressed by "error handling"). "Why does the API error on startup?" → IS a debugging question (intent "why does" + unsuppressed "error"). "Why does the retry fail on large payloads?" → IS a debugging question (intent "why does" + failure lexeme "fail"; the suppression phrase "retry policy" is NOT present in the question, so "fail" is not suppressed).

**Decomposition failure:** If the decomposition call produces no output, empty output, or unparseable output (the response does not contain at least one of `planning_question`, `assumptions`, or `key_terms` as recognizable fields), treat it as a complete decomposition failure. Set `question_shaped=false` and proceed to the Failure terminal state below. Do not retry the decomposition call.

Example: The decomposition call times out or returns "I cannot process this request" — neither contains any routing fields, so `question_shaped=false` and the pipeline falls through to Failure.

**Decomposition:** Run Claude-locally (no Codex). Decompose the user's problem statement using this template:

````
Given this problem statement: "{raw_input}"

Decompose into:
1. A focused, answerable question (one sentence)
2. 2-5 testable assumptions (things that could be true or false about the codebase)
3. 3-8 search terms (function names, module names, file patterns, concepts)
4. Your confidence that this decomposition captures the user's intent (high/medium/low)
5. 0-3 ambiguities that could change the decomposition

Format:
planning_question: ...
assumptions:
- A1: "..."
- A2: "..."
key_terms: [term1, term2, ...]
shape_confidence: high|medium|low
ambiguities:
- ...
````

**Validation:** Parse the decomposition output. For each field, apply tolerant normalization:
- Key aliases: accept `question` as alias for `planning_question`, `confidence` for `shape_confidence`
- List parsing: accept both YAML list and comma-separated formats for `assumptions`, `key_terms`, `ambiguities`
- Assumption ID repair: if IDs are missing (e.g., bare strings), assign A1, A2, ... sequentially
- Dedup: remove duplicate assumptions (normalized text match)
- Tautology filter: reject assumptions that are restatements or negations of the question itself. An assumption must be a testable proposition about the codebase, not a reframing of the question. When in doubt, keep the assumption — false negatives (keeping a tautology) are less harmful than false positives (rejecting a valid assumption that overlaps with the question). Example: question "Is X over-engineered?" → reject "X is over-engineered" (restatement) or "X is not over-engineered" (negation); accept "X has more abstraction layers than its callers require" (testable). If rejected, decrement `assumptions_generated_count` accordingly.
- Cap: maximum 5 assumptions, 8 key_terms, 3 ambiguities

After normalization, validate each routing field independently:
- `planning_question`: must be a non-empty string. If invalid → fallback to raw question.
- `assumptions`: must be a non-empty list of strings. If invalid → Step 1 resolves from `planning_question`.
- `key_terms`: must be a non-empty list of strings. If invalid → Step 2 Gatherer A derives normally.
- `shape_confidence`: must be `"high"`, `"medium"`, or `"low"`. If invalid → default to `"low"`.
- `ambiguities`: must be a list of strings. If invalid → empty list.

**Tri-state `question_shaped`:**
- `null`: `--plan` was not set (all planning pipeline fields are null)
- `true`: `--plan` was set AND ≥ 1 routing field (`planning_question`, `assumptions`, `key_terms`) was accepted after validation
- `false`: `--plan` was set AND 0 routing fields were accepted (complete decomposition failure)

**shape_confidence downgrade:** For each routing field that falls back:
- `assumptions` fallback: downgrade `shape_confidence` one level (high→medium, medium→low)
- `key_terms` fallback: downgrade `shape_confidence` one level
- Minimum is `low` (no further downgrade)

**UX output:** Always show `planning_question` and `shape_confidence` to the user. Show full detail (assumptions, key_terms, ambiguities) only when:
- `shape_confidence` is `medium` or `low`, OR
- Any routing field triggered fallback

If `shape_confidence` is `low`, emit a note: "Question decomposition has low confidence. Consider clarifying: {ambiguities}."

**Pipeline state:** Initialize all planning pipeline fields before Step 0:
- `question_shaped`: null
- `shape_confidence`: null
- `assumptions_generated_count`: null
- `ambiguity_count`: null

**Atomic Step 0 finalization:** After Step 0 completes, set all planning pipeline fields atomically. There are exactly two post-decomposition terminal states (the debug gate skip is a separate pre-decomposition path that leaves all fields at null):

**Success** (`question_shaped=true`, ≥1 routing field accepted):
- `question_shaped`: true
- `shape_confidence`: resolved value after downgrades
- `assumptions_generated_count`: number of assumptions in Step 0 raw output (before fallback)
- `ambiguity_count`: number of ambiguities in Step 0 output

**Failure** (`question_shaped=false`, 0 routing fields accepted OR unrecoverable decomposition error):
- `question_shaped`: false
- `shape_confidence`: "low"
- `assumptions_generated_count`: parsed raw count if available, else 0
- `ambiguity_count`: parsed raw count if available, else 0

This atomic finalization prevents stale-companion states where `pipeline.get()` reads partially-set fields after a mid-Step-0 exception. The debug gate skip is a separate path — it leaves all fields at their initialized null values (not false).

### Step 1: Resolve assumptions

**If Step 0 provided valid assumptions:** Use them directly. Skip extraction.

**Otherwise (no `--plan`, or Step 0 assumptions fell back):** From the question (which may be `planning_question` from Step 0 or the raw question), identify testable assumptions and assign IDs:

- Read the question and list statements that could be true or false about the codebase.
- Assign sequential IDs: A1, A2, A3, ...
- If no testable assumptions exist (e.g., "How does X work?"), pass an empty list.

**Example:**

Question: "Is our redaction pipeline over-engineered? It seems like the format-specific layer is redundant given the generic layer catches everything."

Assumptions:
- `A1: "The generic redaction layer catches everything the format-specific layer catches"`
- `A2: "The format-specific layer is redundant"`

### Step 2: Launch context gatherers

Launch both agents **in parallel** via the Task tool with a 120-second timeout each:

**Gatherer A (code explorer):**
```
Task(
  subagent_type: "cross-model:context-gatherer-code",
  description: "Gather code context for dialogue",
  prompt: "Question: {question}\n\nKey terms: {extracted_terms}",
  timeout: 120000
)
```

When `--plan` is set and Step 0 provided valid `key_terms`, use those as `{extracted_terms}`. Otherwise, derive terms from the question as usual.

**Gatherer B (falsifier):**
```
Task(
  subagent_type: "cross-model:context-gatherer-falsifier",
  description: "Test assumptions against codebase",
  prompt: "Question: {question}\n\nAssumptions:\n- A1: {assumption_1}\n- A2: {assumption_2}\n...",
  timeout: 120000
)
```

**Timeout handling:** If a gatherer times out (120s), treat as 0 parseable lines. Proceed to the low-output retry in Step 3.

**Learning retrieval (§17):** Before briefing assembly, attempt to read learning cards per consultation contract §17. Fail-soft: missing store does not block consultation.

### Step 3: Assemble briefing

Perform **deterministic, non-LLM assembly** of gatherer outputs. Reference: `references/tag-grammar.md` for full grammar and edge cases.

**Step ID crosswalk** (SKILL.md ↔ tag-grammar.md assembly processing order):

| SKILL.md | tag-grammar.md | Operation |
|----------|---------------|-----------|
| 3a | 1 | Parse |
| 3b | 2 | Retry |
| 3c | 3 | Zero-output fallback |
| 3d | 4 | Discard |
| 3e | 5 | Cap |
| 3f | 6 | Sanitize |
| 3g | 7 | Dedup |
| 3h-bis | 8 | Validate provenance |
| 3h | 9 | Group |

**Processing order:**

**3a. Parse:** Scan each gatherer's output for lines starting with `CLAIM:`, `COUNTER:`, `CONFIRM:`, or `OPEN:`. Ignore all other lines.

**3b. Low-output retry:** After parsing, if a gatherer produced fewer than 4 parseable tagged lines, re-launch that gatherer once with a prompt reinforcing the output format: "Emit findings as prefix-tagged lines per the output format. Each CLAIM must include `@ path:line` citation and `[SRC:code]` or `[SRC:docs]` provenance tag. Each COUNTER must include `@ path:line` citation, `AID:<id>`, and `TYPE:<type>`." Parse the retry output (3a) and merge with the original lines. Two lines are duplicates when they share the same tag type AND the same normalized citation (`path:line`). All other line pairs are non-duplicates. Non-duplicate lines are combined (both kept). For duplicate claim keys (same tag type + normalized citation): retry-wins — prefer the SRC-tagged version from retry output over the untagged original. Tie-break: if both original and retry have valid SRC tags (`code` or `docs`), keep the retry version. (This both-tagged tie-break fills a gap in the spec, which does not address the case where both versions carry valid SRC tags.) If still below 4 after retry, proceed with available output.

**Content conflict tracking:** When the retry-wins rule resolves a duplicate (same tag type + normalized citation, different content text), increment `content_conflict_count` (pipeline-local diagnostic counter, initialized to `0`). This counter is not emitted to analytics in the current schema — it exists for pipeline observability only.

**3c. Zero-output fallback:** If total parseable lines across both gatherers is 0 after retries:

```
<!-- dialogue-orchestrated-briefing -->
## Context
(Context gathering produced insufficient results. Rely on mid-dialogue scouting for evidence.)

## Material
(none)

## Question
{user's question, verbatim}
```

Set `seed_confidence` to `low` with `low_seed_confidence_reasons: ["zero_output"]`. Set `provenance_unknown_count` to `null` (3h-bis is skipped, so provenance validation never ran). Skip steps 3d through 3h (including 3h-bis), Step 4, and Step 4b.

**3c as terminal exception:** Step 3c is a terminal early-exit that bypasses the normal pipeline entirely. Step 4b is the "sole authority" for `seed_confidence` within its jurisdiction (the normal path where Steps 3d through 3h-bis, 4, and 4b all run). When 3c fires, it sets both `seed_confidence` and `low_seed_confidence_reasons` directly because the composition step (4b) is skipped. The `zero_output` row in Step 4b's reason table documents the reason's semantics, not its runtime origin — in the 3c path, the reason is set by 3c itself, not collected by 4b.

**3d. Discard:** Remove:
- `CLAIM`, `COUNTER`, or `CONFIRM` lines missing `@ path:line` citation
- `COUNTER` or `CONFIRM` lines missing `AID:` field
- `COUNTER` lines missing `TYPE:` field
- Lines where the tag is present but no content follows the colon

**3e. Cap:** If more than 3 `COUNTER` lines remain after discard, keep the first 3 (by order of appearance). This ensures valid counters are not displaced by invalid ones that were discarded.

**3f. Sanitize:** Run the consultation contract pre-dispatch credential check (§7) on all remaining line content. If a line contains a credential pattern (AWS key, PEM, JWT, GitHub PAT, etc.), remove that line. This is defense-in-depth — the dialogue agent's own sanitizer is the final gate.

**3g. Dedup:** If both gatherers emit lines with the same tag type citing the same file and line number, keep Gatherer A's version. Different tag types at the same citation are kept (e.g., Gatherer A's `CLAIM` and Gatherer B's `CONFIRM` at the same `path:line` are both retained — they serve different purposes). Normalize the citation key before comparing: strip leading `./`, lowercase the path, collapse `//` to `/`.

**3h-bis. Validate provenance:** For each `CLAIM` line in the final retained set, check for `[SRC:code]` or `[SRC:docs]`. If a CLAIM line lacks a provenance tag:
- Assign `[SRC:unknown]`. Emitters never produce `unknown`; its presence means the gatherer did not follow its output format.
- Increment `provenance_unknown_count`.

3h-bis produces `provenance_unknown_count` as a metric only. It does **not** set `seed_confidence` — that happens in Step 4b.

Do **not** implement path inference (guessing SRC from the citation path). This is an explicit prohibition — `[SRC:unknown]` preserves data and marks uncertainty for downstream recovery via scouting.

`[SRC:unknown]` lines are preserved in the assembled briefing — not stripped before delegation.

**Pipeline state:** Initialize `provenance_unknown_count` as a pipeline variable with these semantics:
- `null` — Step 3c fired (3h-bis never ran). Signals to `emit_analytics.py` that provenance validation was skipped; schema stays at `0.1.0`.
- `0` — 3h-bis ran and all CLAIMs have valid SRC tags. Signals provenance validation ran successfully; schema bumps to `0.2.0`.
- Positive `int` — count of CLAIMs where `[SRC:unknown]` was assigned. If `>= 2`, Step 4b adds `provenance_violations` to `low_seed_confidence_reasons`.

Store this value for use by Step 4b (reason evaluation) and Step 7 (analytics emission).

**3h. Group:** Assemble into three sections with deterministic ordering (Gatherer A items first, then Gatherer B within each section):

```
<!-- dialogue-orchestrated-briefing -->
## Context
{OPEN items}
{COUNTER items}
{CONFIRM items}

## Material
{CLAIM items}

## Question
{user's question, verbatim}
```

The sentinel `<!-- dialogue-orchestrated-briefing -->` must appear in the briefing. The `codex-dialogue` agent uses it to detect an external briefing.

### Step 4: Health check

Count citations and unique files in the assembled briefing. Step 4 computes metrics only — it does **not** set `seed_confidence`. That happens in Step 4b.

| Metric | Threshold | Reason code on failure |
|--------|-----------|----------------------|
| Total lines with `@ path:line` | >= 8 | `thin_citations` |
| Unique file paths cited | >= 5 | `few_files` |

Store triggered reason codes for Step 4b.

### Step 4b: Compose seed_confidence

Collect reasons from all pipeline stages into `low_seed_confidence_reasons`:

| Reason | Source | Trigger |
|--------|--------|---------|
| `zero_output` | Step 3c (terminal) | Total parseable lines = 0 after retries. Set directly by 3c — 4b is skipped. |
| `thin_citations` | Step 4 | Total lines with `@ path:line` < 8 |
| `few_files` | Step 4 | Unique file paths cited < 5 |
| `provenance_violations` | Step 3h-bis | `provenance_unknown_count` >= 2 |

`seed_confidence` = `low` if `low_seed_confidence_reasons` is non-empty; `normal` otherwise. Step 4b is the sole authority for `seed_confidence` in the normal pipeline path (Steps 3d through 4b all run). Exception: Step 3c is a terminal early-exit that sets `seed_confidence` directly and skips 4b entirely (see Step 3c above). No short-circuit masking between reasons — all triggered reasons are collected.

`seed_confidence: low` does **not** block the dialogue. It tells the dialogue agent to prioritize early scouting to compensate for thin initial context.

### Step 5: Delegate to codex-dialogue

Launch the `codex-dialogue` agent via the Task tool:

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

**`reasoning_effort` resolution:** profile value > consultation contract §8 default (`xhigh`). When `--plan` is used without `--profile`, reasoning_effort falls through to the contract default (`xhigh`). Pass the resolved value in the envelope — the `codex-dialogue` agent uses it directly without re-resolving profiles. (A `-t` flag for explicit override is deferred — profile propagation covers the immediate need.)

**`scope_envelope` construction:** Before delegation, run the consultation contract §3 preflight to determine allowed roots and source classes. Pass the resulting scope envelope to `codex-dialogue`. The scope is immutable once set — on scope breach, the dialogue agent terminates and produces a synthesis with `termination_reason: scope_breach` in the pipeline-data epilogue (see contract §6).

**Scope validation (§3):** Before delegation, verify these 5 conditions against the scope envelope. If any would be violated, do not delegate — inform the user and request updated consent:

1. No root path outside the original allowed set
2. No source class outside the original allowed set
3. Estimated outbound bytes within session budget
4. No path adjacent to known secret files (`auth.json`, `.env`, `*.pem`)
5. No sandbox mode escalation from `read-only` to higher privilege

Mid-dialogue scope breaches are handled differently: the agent terminates and produces a synthesis with `termination_reason: scope_breach` (see §6). Re-consent gating (§10) is deferred.

The agent detects the sentinel, skips briefing assembly, and runs the multi-turn conversation.

### Step 6: Present synthesis

Relay the `codex-dialogue` agent's synthesis to the user. Include:
1. The narrative synthesis (convergence, concessions, emergent ideas, open questions)
2. The Synthesis Checkpoint block (RESOLVED/UNRESOLVED/EMERGED)
3. Your own assessment of the dialogue outcomes

### Step 7: Emit analytics

After presenting synthesis to the user, emit a `dialogue_outcome` event via the analytics emitter script. Analytics is best-effort — failures do not block the user from seeing the synthesis.

**7a. Write input file**

Use the Write tool to create `/tmp/claude_analytics_{random_suffix}.json` containing the input JSON for the emitter script. The file has four top-level fields:

| Field | Type | Source |
|-------|------|--------|
| `event_type` | `"dialogue_outcome"` | Literal |
| `synthesis_text` | string | Full raw output from the `codex-dialogue` agent's Task tool return value |
| `scope_breach` | bool | Determined during Step 5-6 delegation. `true` if the codex-dialogue agent's `<!-- pipeline-data -->` epilogue contains `termination_reason: scope_breach` or `scope_breach_count > 0`. `false` otherwise. Derived from epilogue fields — not from output shape (the agent always returns a synthesis, even on scope breach). If the epilogue is missing or unparseable, default to `false` and log a warning. |
| `pipeline` | object | Pipeline state accumulated during Steps 1-6 (see field table below) |

Pipeline fields to include:

| Pipeline Field | Source Step | Type |
|----------------|-----------|------|
| `posture` | Args | string |
| `turn_budget` | Args | int |
| `profile_name` | Args | string or null |
| `seed_confidence` | Step 4b | `"normal"` or `"low"` |
| `low_seed_confidence_reasons` | Step 4b | list of enum: `thin_citations`, `few_files`, `zero_output`, `provenance_violations` |
| `assumption_count` | Step 1 | int |
| `no_assumptions_fallback` | Step 1 | bool |
| `gatherer_a_lines` | Step 3 | int |
| `gatherer_b_lines` | Step 3 | int |
| `gatherer_a_retry` | Step 3 | bool |
| `gatherer_b_retry` | Step 3 | bool |
| `citations_total` | Step 4 | int |
| `unique_files_total` | Step 4 | int |
| `gatherer_a_unique_paths` | Step 3 | int |
| `gatherer_b_unique_paths` | Step 3 | int |
| `shared_citation_paths` | Step 3 | int |
| `counter_count` | Step 3 | int |
| `confirm_count` | Step 3 | int |
| `open_count` | Step 3 | int |
| `claim_count` | Step 3 | int |
| `provenance_unknown_count` | Step 3h-bis | int or null |
| `source_classes` | Step 5 | list of strings |
| `scope_root_count` | Step 5 | int |
| `scope_roots_fingerprint` | Step 5 | string or null |
| `question_shaped` | Step 0 | bool or null |
| `shape_confidence` | Step 0 | string or null |
| `assumptions_generated_count` | Step 0 | int or null |
| `ambiguity_count` | Step 0 | int or null |
| `mode` | Step 5 agent return | `"server_assisted"` or `"manual_legacy"`. Parse from the agent's `<!-- pipeline-data -->` JSON epilogue block. Extract the JSON object from the fenced block following the sentinel. If the epilogue is missing, fall back to `"server_assisted"` and log a warning. |

**7b. Run emitter**

The emitter script is at `scripts/emit_analytics.py` within this plugin. Construct the path from this skill's base directory (shown in the header): replace the trailing `skills/dialogue` with `scripts/emit_analytics.py`.

```bash
python3 "{plugin_root}/scripts/emit_analytics.py" /tmp/claude_analytics_{random_suffix}.json
```

**7c. Check result**

The script prints a JSON status line to stdout:
- `{"status": "ok"}` — event appended successfully
- `{"status": "degraded", "reason": "..."}` — input valid, but log write failed
- `{"status": "error", "reason": "..."}` — bad input or validation failure

On `error` or `degraded`, warn the user: `"Analytics emission failed: {reason}. This does not affect the consultation results."` Do not retry.

## Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| Gatherer count | 2 | Fixed for v1 |
| Gatherer timeout | 120s | Prevents pipeline stall |
| Gatherer output cap | 40 tagged lines each | Noise prevention |
| Low parseable threshold | 4 tagged lines | Triggers reformat retry |
| COUNTER cap | 3 | Falsifier noise prevention |
| Health check: min citations | 8 | Coverage proxy |
| Health check: min unique files | 5 | Breadth proxy |
| Reformat retry budget | 1 per gatherer | One retry, then proceed |
| Analytics emitter | `scripts/emit_analytics.py` | Relative to plugin root |
| Analytics event log | `~/.claude/.codex-events.jsonl` | Shared with codex_guard.py |

## Failure Modes

| Failure | Recovery |
|---------|----------|
| Gatherer timeout (120s) | Treat as 0 lines, retry once, proceed with available output |
| Both gatherers return 0 lines | Minimal briefing + `seed_confidence: low` |
| Sanitizer removes all content | Minimal briefing + `seed_confidence: low` |
| codex-dialogue fails to start | Report error to user, suggest `/codex` for direct consultation |
| codex-dialogue errors mid-conversation | Agent synthesizes from available `turn_history` (built-in fallback) |
| MCP tools unavailable | Report missing tools and stop |
| Analytics emitter returns error | Warn user with reason from script output. Do not retry. |
| Analytics emitter returns degraded | Warn user. Event was valid but log write failed. Do not retry. |
| Analytics emitter script not found | Warn user: "Analytics emitter not found." Skip emission. |

## Example

**User:** `/dialogue -p adversarial "Is our redaction pipeline over-engineered? The format-specific layer seems redundant."`

**Step 1 — Resolve assumptions:**
- `A1: "The generic redaction layer catches everything the format-specific layer catches"`
- `A2: "The format-specific layer is redundant"`

**Step 2 — Launch gatherers (parallel):**
- Gatherer A explores `redact.py`, `redact_formats.py`, `paths.py`, test files → emits 18 `CLAIM` lines + 2 `OPEN`
- Gatherer B tests A1 and A2 against codebase → emits 1 `CONFIRM`, 2 `COUNTER`, 1 `OPEN`

**Step 3 — Assemble briefing:**
```
<!-- dialogue-orchestrated-briefing -->
## Context
OPEN: Whether format-specific redaction adds value given generic runs unconditionally
OPEN: Whether test fixture coverage reflects production workload distribution AID:A2
COUNTER: Format-specific layer has zero matches in 847/969 test cases @ test_redact.py:203 AID:A2 TYPE:interface mismatch
COUNTER: Generic redaction catches all patterns format-specific targets @ redact.py:78 AID:A2 TYPE:control-flow mismatch
CONFIRM: Denylist covers OWASP secret categories (AWS, PEM, JWT, GitHub PAT) @ paths.py:22 AID:A1

## Material
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45 [SRC:code]
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11 [SRC:code]
...16 more CLAIM lines (each with [SRC:code] or [SRC:docs])...

## Question
Is our redaction pipeline over-engineered? The format-specific layer seems redundant.
```

**Step 4 — Health check:** 20 citations, 8 unique files → no reason codes triggered.

**Step 4b — Compose seed_confidence:** `low_seed_confidence_reasons` is empty → `seed_confidence: normal`

**Step 5 — Delegate:** Launch `codex-dialogue` with adversarial posture, budget 8, assembled briefing. Agent detects sentinel, skips its own briefing assembly, runs multi-turn conversation.

**Step 6 — Present synthesis:** Relay narrative + Synthesis Checkpoint to user.

**Step 7 — Emit analytics:** Parse synthesis output → 7 RESOLVED, 0 UNRESOLVED, 3 EMERGED, converged=true, 5 turns. convergence_reason=`all_resolved`. Append `dialogue_outcome` event to `~/.claude/.codex-events.jsonl`.

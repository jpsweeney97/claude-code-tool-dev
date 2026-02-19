---
name: dialogue
description: "Multi-turn Codex consultation with proactive context gathering. Launches parallel codebase explorers, assembles a structured briefing, and delegates to codex-dialogue. Use when you need a thorough, evidence-backed consultation, deep codebase analysis before asking Codex, or when the user says 'deep review', 'explore and discuss', or 'thorough consultation'. For quick single-turn questions, use /codex."
argument-hint: '"question" [-p posture] [-n turns] [--profile name]'
user-invocable: true
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

Everything after flags is the **question** (required).

**Resolution order:** explicit flags > profile values > defaults.

**Profile resolution:** Profiles set `posture` and `turn_budget` only. Execution controls (`sandbox`, `approval_policy`, `reasoning_effort`) use consultation contract defaults.

**Validation:**
1. Reject unknown flags.
2. Reject invalid enum values for `--posture`.
3. Reject `--turns` outside 1-15.
4. If question is empty after flag extraction, ask the user: "What would you like to discuss with Codex?"

Error format: `argument parsing failed: {reason}. Got: {input!r:.100}`

## Pipeline

### Step 1: Extract assumptions

From the user's question, identify testable assumptions and assign IDs:

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

### Step 3: Assemble briefing

Perform **deterministic, non-LLM assembly** of gatherer outputs. Reference: `references/tag-grammar.md` for full grammar and edge cases.

**Processing order:**

**3a. Parse:** Scan each gatherer's output for lines starting with `CLAIM:`, `COUNTER:`, `CONFIRM:`, or `OPEN:`. Ignore all other lines.

**3b. Low-output retry:** After parsing, if a gatherer produced fewer than 4 parseable tagged lines, re-launch that gatherer once with a prompt reinforcing the output format: "Emit findings as prefix-tagged lines per the output format. Each CLAIM must include `@ path:line` citation. Each COUNTER must include `@ path:line` citation, `AID:<id>`, and `TYPE:<type>`." Parse the retry output (3a) and combine with the original lines. If still below 4 after retry, proceed with available output.

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

Set `seed_confidence` to `low`. Skip steps 3d-3h.

**3d. Discard:** Remove:
- `CLAIM`, `COUNTER`, or `CONFIRM` lines missing `@ path:line` citation
- `COUNTER` or `CONFIRM` lines missing `AID:` field
- `COUNTER` lines missing `TYPE:` field
- Lines where the tag is present but no content follows the colon

**3e. Cap:** If more than 3 `COUNTER` lines remain after discard, keep the first 3 (by order of appearance). This ensures valid counters are not displaced by invalid ones that were discarded.

**3f. Sanitize:** Run the consultation contract pre-dispatch credential check (§7) on all remaining line content. If a line contains a credential pattern (AWS key, PEM, JWT, GitHub PAT, etc.), remove that line. This is defense-in-depth — the dialogue agent's own sanitizer is the final gate.

**3g. Dedup:** If both gatherers emit lines with the same tag type citing the same file and line number, keep Gatherer A's version. Different tag types at the same citation are kept (e.g., Gatherer A's `CLAIM` and Gatherer B's `CONFIRM` at the same `path:line` are both retained — they serve different purposes). Normalize the citation key before comparing: strip leading `./`, lowercase the path, collapse `//` to `/`.

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

Count citations and unique files in the assembled briefing:

| Metric | Threshold | On failure |
|--------|-----------|-----------|
| Total lines with `@ path:line` | >= 8 | Set `seed_confidence` to `low` |
| Unique file paths cited | >= 5 | Set `seed_confidence` to `low` |

If either threshold fails, `seed_confidence` is `low`. Both must pass for `normal`.

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
    scope_envelope: {scope from §3 preflight — allowed roots and source classes}

    {assembled briefing with sentinel}
  """
)
```

**`scope_envelope` construction:** Before delegation, run the consultation contract §3 preflight to determine allowed roots and source classes. Pass the resulting scope envelope to `codex-dialogue`. The scope is immutable once set — on scope breach, the dialogue agent stops and returns a resume capsule per contract §6.

The agent detects the sentinel, skips briefing assembly, and runs the multi-turn conversation.

### Step 6: Present synthesis

Relay the `codex-dialogue` agent's synthesis to the user. Include:
1. The narrative synthesis (convergence, concessions, emergent ideas, open questions)
2. The Synthesis Checkpoint block (RESOLVED/UNRESOLVED/EMERGED)
3. Your own assessment of the dialogue outcomes

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

## Failure Modes

| Failure | Recovery |
|---------|----------|
| Gatherer timeout (120s) | Treat as 0 lines, retry once, proceed with available output |
| Both gatherers return 0 lines | Minimal briefing + `seed_confidence: low` |
| Sanitizer removes all content | Minimal briefing + `seed_confidence: low` |
| codex-dialogue fails to start | Report error to user, suggest `/codex` for direct consultation |
| codex-dialogue errors mid-conversation | Agent synthesizes from available `turn_history` (built-in fallback) |
| MCP tools unavailable | Report missing tools and stop |

## Example

**User:** `/dialogue -p adversarial "Is our redaction pipeline over-engineered? The format-specific layer seems redundant."`

**Step 1 — Extract assumptions:**
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
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11
...16 more CLAIM lines...

## Question
Is our redaction pipeline over-engineered? The format-specific layer seems redundant.
```

**Step 4 — Health check:** 20 citations, 8 unique files → `seed_confidence: normal`

**Step 5 — Delegate:** Launch `codex-dialogue` with adversarial posture, budget 8, assembled briefing. Agent detects sentinel, skips its own briefing assembly, runs multi-turn conversation.

**Step 6 — Present synthesis:** Relay narrative + Synthesis Checkpoint to user.

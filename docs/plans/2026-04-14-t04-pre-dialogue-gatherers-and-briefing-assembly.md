---
title: "T-04 Pre-Dialogue Gatherers and Briefing Assembly"
date: 2026-04-14
status: Draft
supersession_ticket: T-20260330-04
prior_authority:
  - docs/plans/2026-04-13-t04-v1-production-dialogue-scoping-plan.md
  - docs/plans/2026-04-14-t04-v1-first-live-dialogue-report.md
semantic_source:
  - packages/plugins/cross-model/agents/context-gatherer-code.md
  - packages/plugins/cross-model/agents/context-gatherer-falsifier.md
  - packages/plugins/cross-model/skills/dialogue/SKILL.md
  - packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md
---

# T-04 Pre-Dialogue Gatherers and Briefing Assembly

## 1. Goal and Scope

This plan defines the **second production slice** under T-04. It adds
pre-dialogue context-gathering agents and deterministic briefing assembly
to the codex-collaboration `/dialogue` surface, advancing T-04 acceptance
criteria 3 and 4 from `T-20260330-04`.

The first production slice (v1, merged as PR #106 at `c3c11fa4`) delivered
the `/dialogue` skill, `dialogue-orchestrator` agent, per-turn verification
contract, and hook-matcher extension. That slice uses inline scouting only:
the orchestrator itself executes Read/Grep/Glob calls during Phase 1 and
the per-turn verification loop. This slice adds a pre-dialogue exploration
layer that runs before the orchestrator spawns.

### 1.1 This Plan Is

- A design for two gatherer agents (code explorer and falsifier) adapted
  from cross-model semantic sources into codex-collaboration-owned
  contracts.
- A deterministic assembly pipeline that composes gatherer output into a
  structured briefing block.
- A briefing injection contract that passes the assembled briefing to the
  orchestrator via the Agent prompt.
- A production synthesis artifact extension (`citation_tier`) that gives
  seed evidence a typed home.
- A verification plan for the gatherer-through-synthesis integration.

### 1.2 This Plan Is NOT

- T-04 closure. Benchmark execution, the benchmark-readiness T4-BR-07
  prerequisite gate, the context-injection retirement decision, and
  reference unification remain.
- A redesign of the orchestrator's core loop. Phases 1–5 of the
  orchestrator are unchanged except for briefing detection and
  `citation_tier` emission.
- An analytics or telemetry design. The assembly pipeline produces
  quality metadata for the orchestrator, not for external analytics.
- A port of cross-model's `--plan` question-shaping machinery.
  Assumption extraction is basic and inline for this slice.
- Scored benchmark execution. That is gated by T4-BR-07 items 1–8
  (`docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md`).

### 1.3 Acceptance Criteria (this slice)

| # | Criterion | Source |
|---|-----------|--------|
| 1 | `context-gatherer-code` agent exists in `packages/plugins/codex-collaboration/agents/` | T-04 AC-3 |
| 2 | `context-gatherer-falsifier` agent exists in `packages/plugins/codex-collaboration/agents/` | T-04 AC-3 |
| 3 | Gatherers use standard Claude-side tools (`Glob`, `Grep`, `Read`) | T-04 AC-3, benchmark candidate definition |
| 4 | `/dialogue` skill dispatches gatherers in parallel before orchestrator spawn | This plan |
| 5 | Deterministic assembly pipeline produces a briefing from gatherer output | T-04 AC-4 |
| 6 | Orchestrator receives and uses the briefing as pre-gathered context | This plan |
| 7 | Production synthesis artifact includes `citation_tier` on `synthesis_citations[]` | This plan |
| 8 | Existing 566-test suite passes unchanged | Regression guard |
| 9 | At least one end-to-end `/dialogue` run completes with gatherers active | Verification |

### 1.4 Relationship to Benchmark

The benchmark candidate is "Claude-side scouting with `Glob`, `Grep`, and
`Read`" (`docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`,
line 50). The benchmark does not specify whether scouting is inline (the
orchestrator) or pre-dialogue (gatherers). Both use Claude-side tools.
Gatherers are required by the T-04 ticket's acceptance criteria, not by the
benchmark itself.

Scored benchmark runs remain blocked by T4-BR-07 prerequisites. This plan
does not address those prerequisites.

## 2. Decisions

All decisions in this section are locked. They were reached through design
discussion and confirmed before this plan was drafted.

### D1. Invocation Model: Pre-Dialogue Gatherers

Gatherers run before the Codex dialogue starts, dispatched by the
`/dialogue` skill. This follows the cross-model pattern where two parallel
agents explore the codebase before the first Codex turn. Their output is
assembled into a briefing that enriches the orchestrator's initial context.

**Alternatives considered:**
- Per-turn gatherer dispatch (orchestrator dispatches gatherers during each
  turn's scouting phase). Rejected: requires `Agent` in the orchestrator's
  tools list, containment changes for subagent scope propagation, and
  restructures the orchestration contract.
- Hybrid (pre-dialogue + per-turn dispatch). Rejected: unnecessary
  complexity for this slice. The orchestrator's inline scouting already
  provides per-turn depth.

### D2. Assembly Location: The `/dialogue` Skill

The `/dialogue` skill owns gatherer dispatch, assumption extraction,
deterministic assembly, health checking, and briefing injection. The
orchestrator receives the assembled briefing — it does not participate in
gathering or assembly.

**Rationale:** Keeps the orchestrator focused on the dialogue loop. Avoids
giving it the `Agent` tool. The skill is the integration surface; the
orchestrator is the execution engine.

### D3. Containment: Gatherers Outside Containment

Gatherers run before containment is established. The containment seed is
written by the `/dialogue` skill in step 6 (v1 procedure), and the scope
is materialized by `SubagentStart` when the orchestrator spawns. Gatherers
dispatch before step 6.

**Why this is safe:** Gatherers are read-only (`Glob`, `Grep`, `Read`
only). They cannot modify files or dispatch subagents. The containment
system restricts the orchestrator (which runs the Codex dialogue and
handles external-model communication), not pre-dialogue exploration.

### D4. Inline Scouting Survives

The orchestrator's Phase 1 (inline initial scouting, 5-call budget)
survives alongside gatherers. They are complementary:

| Layer | Timing | Purpose | Budget |
|---|---|---|---|
| Gatherers | Pre-dialogue | Breadth — wide codebase exploration | ~30 tagged lines each |
| Phase 1 | Pre-Codex-turn | Depth — targeted reads informed by the objective | 5 Read/Grep/Glob calls |
| Per-turn scouting | During dialogue | Verification — scout specific claims from Codex | Per-turn budget |

Phase 1's budget is unchanged. The orchestrator may use the briefing to
reprioritize Phase 1 targets (e.g., focus on gaps the gatherers flagged
as OPEN, or on objective-critical surfaces the gatherers did not reach).
The briefing must NOT suppress Phase 1 reads — seed evidence is
unverified, and Phase 1 is the only bounded inline validation pass
before the Codex dialogue. A gatherer CLAIM about a file does not exempt
that file from Phase 1 sampling.

### D5. Tag Grammar: Reuse Format, Own the Reference

Reuse the cross-model tag grammar format (`CLAIM:`, `COUNTER:`, `CONFIRM:`,
`OPEN:` with `@ path:line` citations, `AID:`, `TYPE:`, `SRC:`). The
grammar is the load-bearing interface between gatherers and the assembler —
it must be deterministic and machine-parseable.

Create a codex-collaboration-owned frozen copy at
`packages/plugins/codex-collaboration/references/tag-grammar.md`. This is
NOT a live dependency on the cross-model file. The candidate system needs
its own contract surface that evolves independently.

**Semantic source:** `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md`

### D6. Assembly Pipeline: Core Without Analytics Coupling

Port the core assembly pipeline from cross-model. Drop analytics coupling,
learning retrieval, and `seed_confidence` plumbing. Keep provenance
validation. Full pipeline specified in §4.

### D7. Briefing Quality Visible to Orchestrator

The assembly pipeline produces quality metadata (citation counts, file
diversity, provenance warnings). This metadata is embedded in the briefing
as a machine-readable block and is visible to the orchestrator. The
orchestrator can adjust Phase 1 behavior based on briefing quality (e.g.,
scout harder if the briefing is thin).

### D8. Assumption Extraction: Basic Inline

No `--plan` flag machinery. The `/dialogue` skill extracts testable
assumptions from the objective inline, capped at 5, with a tautology
filter. The falsifier receives the assumption list; the code explorer
receives the objective and key terms.

### D9. Briefing Injection: Prompt with Sentinel and Framing

The assembled briefing is passed in the orchestrator's Agent prompt,
delimited by the `<!-- dialogue-orchestrated-briefing -->` sentinel. The
prompt includes explicit semantic framing:

- This is seed evidence from pre-dialogue gatherers.
- It is NOT verified ledger state.
- Use it to guide Phase 1 target selection.
- Seed-derived facts in the synthesis must carry `citation_tier: "seed"`.

### D10. Seed Evidence: `citation_tier` on `synthesis_citations[]`

Add `citation_tier: "seed" | "dialogue"` to each entry in
`synthesis_citations[]`. The ledger counters and `ledger_summary` remain
dialogue-tier only. The distinction is always recoverable from the artifact.

**Alternatives considered:**
- Separate `seed_evidence[]` field. Rejected: parallel array duplicates
  the citation shape, consumers look in two places.
- `seed_context_summary` + `seed_citations[]`. Rejected: prose summary
  can drift from actual citations.

## 3. Gatherer Agent Contracts

Two agents, dispatched in parallel by the `/dialogue` skill. Both are
read-only, run on Sonnet, and emit prefix-tagged lines.

### 3.1 Code Explorer (`context-gatherer-code`)

**Purpose:** Question-driven codebase exploration. Finds code relevant to
the user's objective and emits factual observations.

**Model:** Sonnet
**Tools:** `Glob`, `Grep`, `Read`

**Input:**
- `objective` — the user's `/dialogue` objective (required)
- `key_terms` — extracted search terms (optional; derives its own if absent)
- `scope_envelope` — optional `{allowed_roots: string[]}`. When set,
  confine all Glob/Grep/Read operations to paths under `allowed_roots`.
  When unset (normal production), explore the full repository. Reserved
  for benchmark-scored runs where T4-BR-07 requires formalized scope
  configuration for compared runs.

**Output:** Prefix-tagged lines following the tag grammar (§3.3).

| Tag | When | Citation | SRC |
|---|---|---|---|
| `CLAIM` | Factual observation about the codebase | Required | Required (`code`) |
| `OPEN` | Unresolved question or ambiguity | Optional | No |

**Domain:** Code, tests, configuration. Does NOT explore `docs/decisions/`,
`docs/plans/`, `docs/learnings/`, or git history — those are the
falsifier's domain.

**Constraints:**
- 40-line output cap
- 8-file read cap
- No narrative — tagged lines only; untagged text ignored by assembler
- Read-only — no file modification
- If `scope_envelope` is set, every Glob/Grep/Read must target a path
  under one of the `allowed_roots`. Paths outside are skipped, not errored.

**Failure mode:** If no relevant files found, emit 1–2 `OPEN` items
describing the search and why nothing matched. Never emit zero lines.

**Semantic source:** `packages/plugins/cross-model/agents/context-gatherer-code.md`

### 3.2 Falsifier (`context-gatherer-falsifier`)

**Purpose:** Repo-first assumption tester. Explores the codebase
independently to test whether stated assumptions hold.

**Model:** Sonnet
**Tools:** `Glob`, `Grep`, `Read`

**Input:**
- `objective` — the user's `/dialogue` objective (required)
- `assumptions` — list of testable assumptions with IDs (e.g.,
  `A1: "The denylist covers all secret types"`). May be empty.
- `scope_envelope` — optional `{allowed_roots: string[]}`. Same semantics
  as the code explorer (§3.1). When set, confine exploration to paths
  under `allowed_roots`. When unset, explore the full repository.

**Output:** Prefix-tagged lines following the tag grammar (§3.3).

| Tag | When | Citation | AID | TYPE |
|---|---|---|---|---|
| `COUNTER` | Evidence contradicting an assumption | Required | Required | Required |
| `CONFIRM` | Evidence supporting an assumption | Required | Required | No |
| `OPEN` | Unresolved question or ambiguity | Optional | Optional | No |
| `CLAIM` | Factual observation (no-assumptions fallback only) | Required | No | No |

**Domain:** Decision documents, plans, learnings, architectural files,
AND code (repo-first means broad exploration). When assumptions list is
empty, scopes to rationale surfaces only (`docs/decisions/`, `docs/plans/`,
`CLAUDE.md`, `README.md`).

**Constraints:**
- 40-line output cap
- 3 `COUNTER` cap — if more than 3 contradictions found, keep the 3 with
  strongest evidence
- No narrative — tagged lines only
- Read-only

**Failure mode:** If no relevant evidence found, emit 1–2 `OPEN` items.
If all assumptions confirmed, emit `CONFIRM` for each — the falsifier is
not required to find contradictions.

**TYPE whitelist** (COUNTER only):
- `interface mismatch`
- `control-flow mismatch`
- `data-shape mismatch`
- `ownership/boundary mismatch`
- `docs-vs-code drift`

**Semantic source:** `packages/plugins/cross-model/agents/context-gatherer-falsifier.md`

### 3.3 Tag Grammar

The tag grammar is the machine-parseable contract between gatherers and
the assembly pipeline. It is documented in a codex-collaboration-owned
reference at `packages/plugins/codex-collaboration/references/tag-grammar.md`.

**Line format:**

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>] [SRC:<source>]
```

**Tags:** `CLAIM`, `COUNTER`, `CONFIRM`, `OPEN`
**AID:** Assumption ID reference (e.g., `AID:A1`)
**TYPE:** Contradiction type from the whitelist (COUNTER only)
**SRC:** Provenance — `code`, `docs`. Assembler-assigned only: `unknown`

Full parse rules, discard rules, and edge cases are in the reference
document. The reference is semantically derived from
`packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md`
but is independently owned and versioned.

## 4. Deterministic Assembly Pipeline

The `/dialogue` skill assembles gatherer output using a deterministic,
non-LLM pipeline. No language model participates in assembly — it is
parse-and-compose only.

### 4.1 Pipeline Steps

| Step | Name | Operation |
|---|---|---|
| 1 | Parse | Extract tagged lines from each gatherer's output; ignore untagged |
| 2 | Retry | If a gatherer produced <4 parseable lines, re-launch once with format-reinforcing prompt; parse retry output; merge with original (retry-wins on duplicate key: same tag type + normalized citation) |
| 3 | Fallback | If total parseable lines across both gatherers is 0 after retries, produce minimal briefing; skip steps 4–10 |
| 4 | Discard | Remove CLAIM/COUNTER/CONFIRM missing `@ path:line`; remove COUNTER/CONFIRM missing `AID:`; remove COUNTER missing `TYPE:`; remove empty-content lines |
| 5 | Cap | If >3 COUNTER lines remain, keep first 3 by appearance order |
| 6 | Sanitize | Run credential-pattern check on remaining content; remove lines containing credential patterns (AWS keys, PEM, JWT, GitHub PAT, etc.) |
| 7 | Dedup | Same tag type + normalized citation across gatherers → keep Gatherer A's version; different tag types at same citation are both retained; normalize key: strip leading `./`, lowercase path, collapse `//` |
| 8 | Provenance | For each CLAIM line missing `[SRC:code]` or `[SRC:docs]`, assign `[SRC:unknown]` and increment `provenance_unknown_count` |
| 9 | Group | Deterministic order (Gatherer A items first within each section): Context (OPEN + COUNTER + CONFIRM), Material (CLAIM), Question (objective verbatim) |
| 10 | Health check | Count citations and unique files; compute briefing quality |

### 4.2 Briefing Quality

Step 10 produces a `briefing_quality` object:

| Field | Type | Computation |
|---|---|---|
| `total_citations` | int | Count of lines with `@ path:line` |
| `unique_files` | int | Count of distinct file paths cited |
| `provenance_unknown` | int | From step 8 |
| `warnings` | list | Reason codes, see below |

**Warning codes:**

| Code | Trigger |
|---|---|
| `thin_citations` | `total_citations` < 8 |
| `few_files` | `unique_files` < 5 |
| `provenance_violations` | `provenance_unknown` >= 2 |

Warnings inform the orchestrator but do NOT block the dialogue. A thin
briefing means the orchestrator should lean harder on Phase 1 inline
scouting.

### 4.3 Fallback Briefing (step 3)

When total parseable lines = 0 after retries:

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

## 5. Briefing Format

### 5.1 Structure

The assembled briefing is delimited by the
`<!-- dialogue-orchestrated-briefing -->` sentinel. Immediately after the
sentinel, a machine-readable metadata block carries the briefing quality
object.

```
<!-- dialogue-orchestrated-briefing -->
<!-- briefing-meta: {"total_citations": 15, "unique_files": 7, "provenance_unknown": 0, "warnings": []} -->

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

### 5.2 Semantic Framing

The briefing header includes explicit instructions for the orchestrator:

1. This is seed evidence from pre-dialogue gatherers.
2. It is NOT verified ledger state — do not register these as Codex claims.
3. Use it to reprioritize Phase 1 targets (focus on gaps and OPEN items).
   Do NOT use it to suppress Phase 1 reads — a gatherer CLAIM about a
   file does not exempt that file from Phase 1 sampling.
4. Any seed-derived facts referenced in `final_synthesis` must carry
   `citation_tier: "seed"` in `synthesis_citations[]`.

### 5.3 Sentinel Detection

The orchestrator detects the briefing by the presence of
`<!-- dialogue-orchestrated-briefing -->` in its Agent prompt. If the
sentinel is absent (e.g., gatherers were skipped), the orchestrator
proceeds with Phase 1 inline scouting as its sole pre-dialogue
exploration — identical to v1 behavior.

## 6. Orchestrator Integration

### 6.1 Changes to the Orchestrator

The orchestrator body changes are minimal:

| Change | What | Why |
|---|---|---|
| Briefing detection | Parse `<!-- briefing-meta: {...} -->` from prompt | Know the briefing quality |
| Phase 1 adjustment | Use briefing quality to inform scouting targets | Avoid redundant exploration |
| `citation_tier` emission | Add `citation_tier` to `synthesis_citations[]` entries | Typed provenance in the artifact |

### 6.2 Non-Goals for the Core Loop

These are explicitly unchanged:

- Phase 3 per-turn verification loop (claim extraction, ledger,
  scouting, state emission)
- Termination conditions and codes
- `<SHAKEDOWN_TURN_STATE>` emission schema (13 fields)
- Ledger counters and `ledger_summary`
- `DIALOGUE_TURN_BUDGET` (10)
- Prohibited actions (no Bash, Write, Edit, Agent)
- Containment guard enforcement

The orchestrator gains a richer input (the briefing) and a one-field
schema extension (`citation_tier`). Its behavioral contract is otherwise
unchanged.

## 7. Production Artifact Delta

### 7.1 `synthesis_citations[]` Extension

Current schema (`dialogue-orchestrator.md`, line 303):

```json
{"path": "string", "line_range": "string", "snippet": "string"}
```

Extended schema:

```json
{
  "path": "string",
  "line_range": "string",
  "snippet": "string",
  "citation_tier": "seed" | "dialogue"
}
```

| Value | Meaning |
|---|---|
| `"seed"` | Citation derived from pre-dialogue gatherer evidence |
| `"dialogue"` | Citation derived from per-turn verification (Codex claim scouting) |

**Backward compatibility:** If `citation_tier` is absent, the consumer
should treat it as `"dialogue"` (v1 artifacts predate this field).

### 7.2 `final_claims[].representative_citation` Constraint

`final_claims` entries carry a `representative_citation` that the
`/dialogue` skill renders in the claims table. This citation must be
dialogue-tier only — it must come from per-turn verification scouting,
not from the pre-dialogue briefing.

**Rule:** The orchestrator must NOT use a seed-sourced citation as the
`representative_citation` for a `final_claims` entry. If the only
evidence for a claim came from seed exploration (gatherer CLAIMs), the
`representative_citation` should be `null` rather than a seed citation.
This prevents unverified seed evidence from appearing as the support
for a dialogue-tier claim in the user-facing claims table.

**Rationale:** `final_claims` tracks Codex claims and their verification
status. A `representative_citation` is the strongest evidence the
orchestrator found during per-turn scouting. Allowing seed citations
here would blur the "seed, not ledger" boundary — the claims table
would show unverified gatherer output as if it were dialogue-verified
evidence.

**Schema change:** `representative_citation` becomes nullable. When the
field is `null`, the `/dialogue` skill renders `—` (em-dash) in the
Citation column of the user-facing claims table. This signals "claim
was registered but not independently verified against a specific file
during the dialogue." The `final_status` field still indicates the
claim's verification outcome — `null` citation means the claim was
assessed through dialogue context rather than direct file evidence.

### 7.3 Other Fields

| Field | Status |
|---|---|
| `final_claims` | Schema changed: `representative_citation` is now nullable (§7.2). Claim tracking logic unchanged — still Codex-claim-only. |
| `ledger_summary` | Unchanged — dialogue-tier counters only |
| `final_synthesis` | Unchanged in structure — may reference seed evidence in prose |
| `termination_code` | Unchanged |
| `converged` | Unchanged — based on Codex-claim verification, not seed evidence |

Seed evidence does NOT inflate `final_claims` counts, `supported` /
`contradicted` tallies, or convergence determination. Those remain
Codex-claim-only metrics. The `citation_tier` field on
`synthesis_citations[]` provides the audit trail for which facts came
from which exploration layer. The `representative_citation` constraint
on `final_claims` prevents tier blurring in the user-facing claims
table.

## 8. Skill Procedure Changes

The v1 `/dialogue` skill procedure has 8 steps: capture objective →
repo root → session ID → stale cleanup → single-run check → seed write →
dispatch orchestrator → surface synthesis. The gatherer integration
restructures steps 5–7 to split the active-run lock from the
containment seed and insert the gatherer pipeline between them.

### 8.1 Lock/Seed Split

In v1, the active-run pointer and the containment seed are written
together in step 6. They serve different purposes:

| File | Content | Purpose | Lifecycle |
|---|---|---|---|
| `active-run-<session_id>` | Plain-text `run_id` | Session lock — prevents double `/dialogue` in the same session | Written at step 5-lock, deleted in finally block |
| `seed-<run_id>.json` | Scope configuration | Containment bootstrap — SubagentStart materializes scope | Written at step 6, consumed by SubagentStart |

**Lock scope is session-local.** The containment architecture is fully
session-scoped: `active_run_path()` returns `shakedown_dir /
f"active-run-{session_id}"`, `read_active_run_id()` does exact
per-session lookup, and all run artifacts (seed, scope, transcript)
are keyed by `run_id` which is unique per invocation. Two sessions
running dialogues concurrently have completely disjoint file sets.
Step 5 checks only for `active-run-<this_session_id>`, not for
`active-run-*`.

This slice splits the lock from the seed. The active-run pointer moves
to immediately after the single-run check (step 5), closing the TOCTOU
window before the gatherer pipeline runs. The seed remains where it was,
written just before orchestrator dispatch.

**Why this is safe:** The SubagentStart hook matcher
(`shakedown-dialogue|dialogue-orchestrator`) does not match gatherer
agent names (`context-gatherer-code`, `context-gatherer-falsifier`).
SubagentStart will not fire for gatherers. If it hypothetically did, it
would find the active-run but no seed, hit the "no seed" early return
in `containment_lifecycle.py` (lines 80–82), and exit silently.

### 8.2 Run ID Generation

Generate one `run_id` (UUID4) at the start of the procedure, before
step 5. This single value is carried through the entire lifecycle:

| Consumer | How `run_id` is used |
|---|---|
| `active-run-<session_id>` | Written as plain-text file content (unchanged format) |
| `seed-<run_id>.json` | Filename includes `run_id` |
| `containment_lifecycle.py` | Reads `run_id` from active-run via `read_active_run_id()` to locate seed/scope |
| Orchestrator dispatch | Passed in prompt for traceability |
| Cleanup (finally block) | Used to delete `active-run-<session_id>` |

The active-run pointer format is unchanged from v1: the filename is
`active-run-<session_id>` and the content is the plain-text `run_id`.
This preserves compatibility with `server/containment.py`'s
`read_active_run_id()` which reads the file with `.read_text().strip()`.
The liveness check (step 5) reads the `run_id` from the file content to
locate seed/scope files — no format change, no new fields.

### 8.3 Revised Procedure (steps 5–7)

**Step 5. Single-run check** (revised from v1)

Check for `active-run-<this_session_id>` (session-scoped, not global).
If the file does not exist, proceed to step 5-lock.

If the file exists, read the `run_id` from its content and perform a
two-tier liveness inspection:

| State | Detection | Action |
|---|---|---|
| Live run | `seed-<run_id>.json` or `scope-<run_id>.json` exists | Block: "a dialogue is already in progress" |
| Abandoned pointer | No seed/scope for the pointer's `run_id` | Delete the stale pointer, proceed |

**Rationale:** Within a single Claude Code session, the skill runs
sequentially — you cannot invoke `/dialogue` while a previous
invocation is still running. The only scenario where this session's
active-run pointer exists at step 5 is a prior invocation that crashed
(context exhaustion, user kill) before its finally block could clean
up. In that case, the seed was either never written (crash during
gathering) or already consumed and scope already cleaned (crash after
orchestrator completed). Either way, no seed or scope file exists, and
the pointer is safely deletable.

The seed/scope check is sufficient because the pointer is session-scoped
and the skill is sequential. No mtime-based age check is needed — there
is no concurrent-gathering scenario within a single session.

**Step 5-lock. Write active-run pointer** (moved from v1 step 6)

Write `active-run-<session_id>` with plain-text `run_id` as content
(unchanged format from v1). This acquires the lock before any
long-running work. The gatherer pipeline (up to 120 seconds per
gatherer) runs under this lock.

**Step 5a. Extract assumptions**

From the objective, identify testable assumptions and assign sequential
IDs (A1, A2, ...). Cap at 5. Apply tautology filter: reject assumptions
that restate or negate the objective itself. When in doubt, keep the
assumption.

If no testable assumptions exist (e.g., "How does X work?"), pass an
empty list to the falsifier. The falsifier's no-assumptions fallback
activates.

Extract 3–8 key terms from the objective for the code explorer.

**Step 5b. Dispatch gatherers (parallel)**

Launch both gatherers in parallel via the Agent tool:

```
Agent(
  subagent_type: context-gatherer-code
  prompt: "Objective: {objective}\n\nKey terms: {terms}"
)

Agent(
  subagent_type: context-gatherer-falsifier
  prompt: "Objective: {objective}\n\nAssumptions:\n- A1: ...\n- A2: ..."
)
```

Timeout: 120 seconds each.

**Step 5c. Assemble briefing**

Run the deterministic assembly pipeline (§4) on gatherer outputs.
Produce the briefing block (§5) with sentinel, metadata, semantic
framing, and grouped findings.

**Step 5d. Briefing-quality log**

Log a brief quality summary for the user:

- Number of findings from each gatherer
- Warning codes (if any)
- "Briefing assembled. Launching orchestrator."

This is informational, not blocking.

**Step 6. Write containment seed** (v1 step 6, minus the active-run write)

Write `seed-<run_id>.json` with scope configuration. The active-run
pointer already exists (from step 5-lock).

**Step 7. Dispatch orchestrator** (modified from v1 step 7)

The v1 dispatch passes the objective to the orchestrator. The modified
dispatch prepends the assembled briefing to the prompt:

```
Agent(
  subagent_type: dialogue-orchestrator
  prompt: "{assembled_briefing}\n\n{original_dispatch_prompt}"
)
```

The original dispatch prompt (objective, seed reference, etc.) is
unchanged. The briefing is prepended so the orchestrator sees it first.

### 8.4 Lock Lifecycle

The `/dialogue` skill is the release owner for the `active-run-<session_id>`
lock. It acquires the lock in step 5-lock and must release it on every
exit path. The seed/scope liveness check in step 5 is the recovery
mechanism for crash-abandoned pointers.

**Acquire:** Step 5-lock writes `active-run-<session_id>` with
plain-text `run_id` as content.

**Release (success):** After step 8 (surface synthesis) completes, delete
`active-run-<session_id>`. This allows the user to run another
`/dialogue` in the same session.

**Release (failure):** If any step between 5-lock and 8 fails — gatherer
timeout, assembly error, seed write failure, orchestrator crash — delete
`active-run-<session_id>` before reporting the error to the user.

**Implementation pattern:** Steps 5a through 8 execute under a
try/finally guard:

```
run_id = uuid4()
write active-run-<session_id>        # step 5-lock: acquire
  content: run_id (plain text)
try:
    extract assumptions              # step 5a
    dispatch gatherers               # step 5b
    assemble briefing                # step 5c
    log quality                      # step 5d
    write seed-<run_id>.json         # step 6
    dispatch orchestrator            # step 7
    surface synthesis                # step 8
finally:
    delete active-run-<session_id>   # release
```

**Crash recovery:** If the skill cannot run its finally block (context
exhaustion, user kill, process crash), the active-run pointer persists.
The next `/dialogue` invocation in the same session (if the session
survives, e.g., context compression) will encounter it in step 5 and
apply the seed/scope liveness check:

- If no seed or scope file exists (the common crash case: crash during
  gathering or after orchestrator completed) → the pointer is treated
  as abandoned, deleted, and the new invocation proceeds immediately.
- If a seed or scope file exists (rare: crash mid-containment) → the
  pointer is treated as a live run and blocks. The SessionStart stale
  sweep (24h) handles this edge case.

If the session does not survive (process kill), a new session gets a
new `session_id` and checks only its own pointer — the stale pointer
from the old session does not block the new one. The SessionStart
stale sweep eventually cleans up the orphaned pointer.

**Recovery latency:** Immediate for same-session retry (seed/scope
absent → clean up and proceed). Zero impact on new sessions (different
session_id). The 24-hour stale sweep is only relevant for orphaned
pointers with seed/scope still present — a rare edge case.

**Interaction with containment lifecycle:** The `active-run-<session_id>`
file is read by `containment_lifecycle.py` during SubagentStart to find
the `run_id` and locate the seed. SubagentStart fires only for the
orchestrator (hook matcher: `shakedown-dialogue|dialogue-orchestrator`),
not for gatherers. The orchestrator's full lifecycle (SubagentStart →
run → SubagentStop) happens within the try block, so the active-run
file exists throughout the orchestrator's lifetime. Deleting it in the
finally block is safe because SubagentStop has already completed by
the time the orchestrator Agent call returns to the skill.

**Change from v1:** In v1, the active-run pointer persisted indefinitely
after success (documented in the v1 live-run report: "active-run-e60a3e2e
— present (expected; not cleaned by SubagentStop, per design)"). This
slice changes the design: the skill explicitly cleans up on both success
and failure. Crash-abandoned pointers are recovered by the seed/scope
liveness check in step 5 — if no seed or scope exists for the pointer's
`run_id`, the pointer is treated as abandoned and deleted immediately.
The 24-hour stale sweep remains as a deep backstop for the rare case
where a crash leaves both a pointer and a seed/scope file.

## 9. File Inventory

### 9.1 New Files

| File | Type | Purpose |
|---|---|---|
| `packages/plugins/codex-collaboration/agents/context-gatherer-code.md` | Agent | Code explorer gatherer |
| `packages/plugins/codex-collaboration/agents/context-gatherer-falsifier.md` | Agent | Falsifier gatherer |
| `packages/plugins/codex-collaboration/references/tag-grammar.md` | Reference | Frozen tag grammar (owned copy) |

### 9.2 Modified Files

| File | Change | Scope |
|---|---|---|
| `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` | Add steps 5a–5d, modify dispatch | Skill grows by ~80–100 lines |
| `packages/plugins/codex-collaboration/agents/dialogue-orchestrator.md` | Add briefing detection, `citation_tier` emission | ~10 lines of change |

### 9.3 Unchanged Files

| File | Why unchanged |
|---|---|
| `packages/plugins/codex-collaboration/hooks/hooks.json` | Gatherers are not containment-managed agents; no hook-matcher change needed |
| `packages/plugins/codex-collaboration/scripts/containment_lifecycle.py` | Gatherers run outside containment |
| `packages/plugins/codex-collaboration/scripts/containment_guard.py` | Guard enforces on orchestrator only |
| `packages/plugins/codex-collaboration/references/dialogue-turn-contract.md` | Per-turn contract unchanged |

## 10. Verification Plan

### 10.1 Unit-Level

| Check | Method |
|---|---|
| Tag grammar parse rules | Test tagged-line parsing against edge cases from §3.3 reference |
| Assembly discard rules | Test malformed lines are correctly removed |
| Assembly dedup rules | Test cross-gatherer dedup with normalized citation keys |
| Provenance assignment | Test `[SRC:unknown]` assignment and counting |
| Health check thresholds | Test warning code generation |
| Tautology filter | Test assumption rejection for restatements and negations |
| Liveness check (step 5) | Test two tiers: seed/scope present → block; no seed/scope → clean up and proceed |

### 10.2 Integration-Level

| Check | Method |
|---|---|
| Gatherer output format | Dispatch each gatherer on a known codebase; verify output parses cleanly |
| Assembly pipeline end-to-end | Feed gatherer output through full pipeline; verify briefing structure |
| Briefing injection | Verify orchestrator receives and parses the sentinel and metadata |
| `citation_tier` emission | Verify production synthesis contains tier-marked citations |

### 10.3 End-to-End

| Check | Method |
|---|---|
| Full `/dialogue` with gatherers | Invoke `/dialogue <objective>` and verify: gatherers dispatch, briefing assembles, orchestrator receives briefing, synthesis includes seed-tier citations |
| Regression: `/dialogue` without gatherers | If gatherers fail or time out, verify the orchestrator proceeds with v1 behavior (inline scouting only) |
| Regression: existing test suite | `uv run --package codex-collaboration pytest` passes unchanged |

### 10.4 Rubric Alignment

The 14-item inspection rubric from the shakedown system applies to the
orchestrator's per-turn behavior, which is unchanged. Gatherers and
assembly are pre-orchestrator — they are not subject to the per-turn
rubric. A separate rubric for gatherer quality (output format compliance,
domain adherence, cap compliance) should be defined during implementation.

## 11. Deferred Work

| Item | Reason | Trigger |
|---|---|---|
| `--plan` question-shaping machinery | Complexity disproportionate to v2 value | User feedback requests richer assumption extraction |
| Analytics coupling (`emit_analytics.py`) | Orthogonal to gatherer correctness | Analytics design for codex-collaboration |
| Learning retrieval injection | Orthogonal; codex-collaboration may have its own learnings system | Learnings system design |
| Multi-agent scope transport | Not needed — gatherers run outside containment | Future agents that need containment-managed gathering |
| Shakedown-to-production reference unification | Separate T-04 closure item (v1 plan §2.2 item 4) | After gatherer slice is stable |
| Concurrent shakedown + production runs | v1 plan §2.3 — shared-namespace constraint | Post-v1 containment redesign |
| Automated gatherer-quality rubric | Per §10.4 — should exist but is not blocking | Implementation phase |
| Credential sanitization pattern list | Reuse cross-model's §7 patterns initially; own the list if patterns diverge | Pattern divergence observed |

## 12. References

| Resource | Location | Purpose |
|---|---|---|
| Supersession ticket | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | Acceptance authority |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Evaluation authority |
| v1 scoping plan | `docs/plans/2026-04-13-t04-v1-production-dialogue-scoping-plan.md` | Prior slice design |
| v1 verification report | `docs/plans/2026-04-14-t04-v1-first-live-dialogue-report.md` | E2E verification precedent |
| Benchmark readiness | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md` | T4-BR-07 prerequisite gate |
| Cross-model code explorer | `packages/plugins/cross-model/agents/context-gatherer-code.md` | Semantic source |
| Cross-model falsifier | `packages/plugins/cross-model/agents/context-gatherer-falsifier.md` | Semantic source |
| Cross-model `/dialogue` skill | `packages/plugins/cross-model/skills/dialogue/SKILL.md` | Assembly pipeline semantic source |
| Cross-model tag grammar | `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md` | Tag grammar semantic source |
| Orchestrator agent | `packages/plugins/codex-collaboration/agents/dialogue-orchestrator.md` | Integration target |
| `/dialogue` skill | `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` | Integration target |

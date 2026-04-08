# T7: Executable Slice Definition

**Date:** 2026-04-07
**Plan:** [2026-04-01-t04-benchmark-first-design-plan.md](2026-04-01-t04-benchmark-first-design-plan.md)
**Done-when:** There is an agreed smallest buildable slice that can execute one dialogue and expose the fields the dry-run must inspect ([plan.md:43](2026-04-01-t04-benchmark-first-design-plan.md#L43)).
**Status:** `Defined` — T8 implements.

## Authorities

| Authority | What it governs | Reference |
|-----------|----------------|-----------|
| T7/T8 plan boundary | T7 defines the slice; T8 implements and runs it | [plan.md:42-46](2026-04-01-t04-benchmark-first-design-plan.md#L42) |
| Risk I mitigation | Pre-benchmark dry-run validates layers 4-6 loop integration | [risk-analysis.md:231](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md#L231) |
| T6-deferred items | `scope_envelope` harness wiring + B8 anchor-adequacy decision rule | [composition-review.md:193](../reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md#L193) |
| T4 scouting contract | Behavioral loop, containment, evidence recording | [scouting-behavior.md](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md), [state-model.md](t04-t4-scouting-position-and-evidence-provenance/state-model.md), [containment.md](t04-t4-scouting-position-and-evidence-provenance/containment.md) |

## Slice Summary

T7 defines the **minimum runnable packet for one pre-benchmark integration shakedown on B1**.

- One real dialogue, outside benchmark execution.
- Purpose: validate loop integration, containment-path exercise, and observable state projection before benchmark-facing harness work.
- Selected task: `B1`.
- Not a benchmark run class. Not governed by T4-BR-08. Not scored. Not evidentiary for benchmark policy.

T7 does not implement the packet. T8 implements it.

## Two-Layer Architecture

### Layer 1: Infrastructure Reuse

The existing R1/R2 implementation provides the mechanical dialogue surface. All of the following exist and are tested (460 tests as of 2026-04-07):

| Component | What it provides |
|-----------|-----------------|
| `codex.dialogue.start` / `.reply` / `.read` | MCP tool surface for dialogue lifecycle |
| Advisory runtime bootstrap | Codex App Server connection, auth, version check, thread management |
| Lineage store | Session-partitioned handle persistence (append-only JSONL) |
| Operation journal | Crash-recovery entries, journal-before-dispatch, trim on completion |
| Context assembly | Assembler, profile filter, redactor, trimmer, budget enforcement |
| Turn store | Committed turn persistence and replay |

This layer is **mechanical plumbing only**. It does not implement the T4 scouting contract's behavioral loop.

### Layer 2: Behavioral Layer (Must Be Added)

The T4 scouting contract defines the behavioral dialogue surface. None of the following exist in the codex-collaboration implementation:

- `effective_delta`, `ledger_summary`, `compute_action`, `scope_envelope`, `allowed_roots`, `claim_provenance_index`, `ClassificationTrace`: zero matches in `packages/plugins/codex-collaboration/server/`.
- `dialogue-codex` skill: does not exist. Only `codex-status` and `consult-codex` skills are implemented.
- Containment enforcement: no implementation.

This layer is what the shakedown validates. T7 defines it. T8 builds it.

## B1-Load-Bearing Behavioral Subset

The full T4 scouting contract spans 12 spec files. For the B1 shakedown, this subset is load-bearing:

### Per-Turn Loop Shape

Extract → register → compute counters/`effective_delta` → control decision → scout → update verification state → compose follow-up → send ([T4-SB-01](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#t4-sb-01), steps 1-7).

### Claim Registration

- New/revised handling with within-turn ordering ([T4-SM-01](t04-t4-scouting-position-and-evidence-provenance/state-model.md#t4-sm-01), [T4-SM-02](t04-t4-scouting-position-and-evidence-provenance/state-model.md#t4-sm-02)).
- Initial scoutable vs. `not_scoutable` classification for claims that appear in B1.
- Basic operational classification only — the full audit-side decomposition review ([scouting-behavior.md:226](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#L226)) is deferred.

### Verification-State Updates

- Status derivation from evidence dispositions ([T4-SM-06](t04-t4-scouting-position-and-evidence-provenance/state-model.md#t4-sm-06), status derivation rule at [state-model.md:346](t04-t4-scouting-position-and-evidence-provenance/state-model.md#L346)).
- Normative verification states: `unverified` | `supported` | `contradicted` | `conflicted` | `ambiguous` | `not_scoutable`.
- For the B1 shakedown, the most common transitions will be `unverified` → `supported` (claim verified by scouting) and `unverified` → `not_scoutable` (claim not mechanically verifiable). `contradicted`, `conflicted`, and `ambiguous` are possible but less likely given B1's evaluative character.

### Scout Target Selection and Query Coverage

- Target priority: unverified (attempts=0) → conflicted → ambiguous ([T4-SB-03](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#t4-sb-03)).
- At most one scout target per round.
- Mandatory definition + falsification query coverage, 2-5 tool calls per round ([T4-SB-04](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#t4-sb-04)).

### Evidence Recording

- Evidence-record creation with citations from scouting output ([T4-SM-06](t04-t4-scouting-position-and-evidence-provenance/state-model.md#t4-sm-06)).
- Evidence-block re-emission after each completed round (atomic commit, [state-model.md:503](t04-t4-scouting-position-and-evidence-provenance/state-model.md#L503)).

### Synthesis Epilogue

Population sufficient for manual inspection of loop outputs. Required fields from [risk-analysis.md:231](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md#L231):

- `effective_delta`
- Ledger summary
- `converged` derivation
- All epilogue required fields

### Deferred From the First Shakedown

| Surface | Why deferred |
|---------|-------------|
| B8 decomposition and anchor-adequacy logic | B8 excluded — conditional on enforcement gaps ([composition-review.md:123](../reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md#L123)) |
| Benchmark artifact set (`manifest.json`, `runs.json`, `adjudication.json`, `summary.md`) | Reserved for benchmark execution |
| `claim_provenance_index` emission, `[ref:]` surfaces | Scored-run harness work ([T4-BR-04](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-04)) |
| Methodology findings and `methodology_finding_threshold` | Scored-run harness work ([T4-BR-09](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-09) rows 1-2) |
| Omission-audit proof surface | Scored-run harness work ([T4-BR-07](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-07) item 8) |
| Transcript parser and mechanical diff engine | Scored-run harness work ([T4-BR-02](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-02)) |
| Narrative-claim inventory and ledger completeness checker | Scored-run harness work ([T4-BR-06](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-06)) |
| `allowed_roots` equivalence, `max_evidence`, scored-run scope formalization | Scored-run comparability ([T4-BR-09](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-09) row 5) |
| T5 `agent_local` migration | External prerequisite for scored runs, T5-owned ([T5 decision](2026-04-02-t04-t5-mode-strategy.md), [T4-BR-01](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-01)) |
| Full audit-side `not_scoutable` decomposition review | Adjudication machinery, not needed for operational classification ([scouting-behavior.md:226](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#L226)) |
| Post-execution canonical-path filtering ([T4-CT-01](t04-t4-scouting-position-and-evidence-provenance/containment.md#t4-ct-01)) | Claude Code `PostToolUse` cannot modify native tool output; pre-execution confinement + manual inspection is sufficient for the shakedown |

## Containment

Containment for the shakedown is **pre-execution confinement via PreToolUse hooks** on the native `Read` / `Grep` / `Glob` tools.

T4 specifies two containment layers: pre-execution confinement ([T4-CT-02](t04-t4-scouting-position-and-evidence-provenance/containment.md#t4-ct-02)) and post-execution canonical-path filtering ([T4-CT-01](t04-t4-scouting-position-and-evidence-provenance/containment.md#t4-ct-01)). For the shakedown, only pre-execution confinement is implemented. Post-execution filtering is deferred to scored-run work because Claude Code's `PostToolUse` hook cannot modify native tool output — `updatedMCPToolOutput` applies to MCP tools only.

### Why Pre-Execution Only Is Sufficient for the Shakedown

- Pre-execution confinement prevents out-of-scope tool calls entirely: `Read` is denied, `Grep`/`Glob` `path` parameters are rewritten to `scope_root` within `allowed_roots`. If input is correctly constrained, output is inherently within scope.
- Post-execution filtering is defense-in-depth for edge cases (e.g., symlinks resolving outside scope, Grep matching content in included-but-unexpected files). These edge cases are detectable by manual per-turn inspection (checklist item 11) for the shakedown.
- Scored runs require automated post-execution filtering because manual inspection does not scale to 8-task corpus runs. That mechanism is later T7/T8 work.

### Why PreToolUse Hooks

- T4 requires confinement as a **harness function** applied before tool execution ([containment.md:37](t04-t4-scouting-position-and-evidence-provenance/containment.md#L37)).
- The codex-collaboration trust model names Claude-side PreToolUse as the authoritative enforcement point ([foundations.md:124](../superpowers/specs/codex-collaboration/foundations.md#L124)).
- The plugin already has hook infrastructure: [hooks.json](../../packages/plugins/codex-collaboration/hooks/hooks.json) and [codex_guard.py](../../packages/plugins/codex-collaboration/scripts/codex_guard.py).
- Wrapper MCP tools rejected: they would distort the candidate tool surface away from the benchmark's intended `Glob` / `Grep` / `Read` path ([benchmark.md:93-94](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md#L93)).

### Enforcement Specification

The PreToolUse hook uses `updatedInput` to rewrite tool parameters and `permissionDecision: "deny"` to block out-of-scope calls.

| Tool | Mechanism | T4 source |
|------|-----------|-----------|
| `Read` | Check `file_path` against `allowed_roots`. Out-of-scope → `permissionDecision: "deny"` (tool does not execute) | [T4-CT-02](t04-t4-scouting-position-and-evidence-provenance/containment.md#t4-ct-02) |
| `Grep` | Rewrite `path` to `scope_root` within `allowed_roots` via `updatedInput`. Results inherently under scope root | [T4-CT-02](t04-t4-scouting-position-and-evidence-provenance/containment.md#t4-ct-02) |
| `Glob` | Rewrite `path` to `scope_root` within `allowed_roots` via `updatedInput`. Results inherently under scope root | [T4-CT-02](t04-t4-scouting-position-and-evidence-provenance/containment.md#t4-ct-02) |

**Deferred:** Post-execution canonical-path filtering ([T4-CT-01](t04-t4-scouting-position-and-evidence-provenance/containment.md#t4-ct-01)) is required for scored runs but not for the manually-inspected shakedown. The inspector verifies containment correctness via checklist items 10-12.

### Scope Envelope for B1

B1 primary evidence anchors define `allowed_roots`:

- `docs/superpowers/specs/codex-collaboration/contracts.md`
- `docs/superpowers/specs/codex-collaboration/delivery.md`
- `packages/plugins/codex-collaboration/server/mcp_server.py`

The shakedown harness reads B1's corpus metadata and populates non-empty `allowed_roots` in the consultation configuration before the dialogue starts.

### Hook State Transport

The PreToolUse hook needs access to the active `allowed_roots` but Claude Code's hook input only provides `session_id`, `tool_name`, `tool_input`, `tool_use_id`, `cwd`, and `transcript_path`. There is no mechanism to pass arbitrary dialogue-specific state to hook processes.

**Required mechanism:** session-bound scope file, created and removed by subagent lifecycle hooks.

**Lifecycle contract:**

1. Before spawning the shakedown subagent, the harness writes a **seed file** at `${CLAUDE_PLUGIN_DATA}/shakedown/seed-<session_id>.json` containing `allowed_roots` and the owning `session_id`. The seed file does not contain `agent_id` (unknown until spawn).
2. A `SubagentStart` hook, matched on the shakedown agent's `agent_type`, fires when the subagent is spawned — before the subagent executes any tool calls. The hook reads `agent_id` from its input (`hooks#common-input-fields`), reads the seed file, and writes the **scope file** at `${CLAUDE_PLUGIN_DATA}/shakedown/scope-<session_id>.json` with the full activation record (including `agent_id`). It then removes the seed file.
3. The PreToolUse hook reads `session_id` and `agent_id` from the hook input, looks for a matching scope file, and enforces containment only when **all three conditions** hold: (a) a scope file exists for the current `session_id`, (b) the hook input includes an `agent_id`, and (c) that `agent_id` matches the scope file's `agent_id`. Calls on the main thread (no `agent_id` in hook input) always pass through, even if the scope file exists.
4. If no matching scope file exists, or the `agent_id` does not match, the hook passes through (containment inactive).
5. A `SubagentStop` hook, matched on the same `agent_type`, fires when the subagent finishes and removes the scope file.

**Expected ordering (inference, not explicit doc guarantee):** The Claude Code lifecycle diagram (`hooks#hook-lifecycle`) shows `SubagentStart` → agentic loop (with `PreToolUse` before each tool call) → `SubagentStop`. The `SubagentStart` docs say it fires "when a subagent is spawned" and can "inject context into the subagent," implying completion before the subagent acts. `PreToolUse` fires "before a tool call executes." The inference is that `SubagentStart` completes before the subagent's first `PreToolUse`, so the scope file is present when the first guarded call fires. The docs do not explicitly state this sequencing. **T8 must validate this ordering as its first implementation step** — a minimal test that writes a marker file from `SubagentStart` and checks for it from the subagent's first `PreToolUse`. If the ordering does not hold, the fallback is a brief poll in the `PreToolUse` hook (wait for scope file with a short timeout), and if the file still does not appear, **deny the call** (`permissionDecision: "deny"`) rather than passing through — containment must fail closed.

**Why `SubagentStart`/`SubagentStop` and not the parent harness:** The parent harness does not have access to the subagent's `agent_id` before spawning it — `agent_id` is generated by Claude Code at spawn time and first appears in the `SubagentStart` hook input. Attempting to write the scope file with `agent_id` from the parent would require guessing or a round-trip that the API does not support.

**Scope file format:**
```json
{
  "session_id": "<owning session>",
  "run_id": "<UUID4 — unique to this shakedown run>",
  "agent_id": "<agent_id of the shakedown subagent, written by SubagentStart>",
  "allowed_roots": ["docs/superpowers/specs/codex-collaboration/contracts.md", "..."],
  "created_at": "<ISO timestamp>"
}
```

**Seed file format (transient, removed by SubagentStart):**
```json
{
  "session_id": "<owning session>",
  "run_id": "<UUID4>",
  "allowed_roots": ["docs/superpowers/specs/codex-collaboration/contracts.md", "..."],
  "created_at": "<ISO timestamp>"
}
```

This follows the same plugin-data pattern as the lineage store (`${CLAUDE_PLUGIN_DATA}/lineage/`). The `agent_id` binding ensures the hook only constrains tool calls from the shakedown subagent, not the operator's own tool usage in the same session. The `run_id` provides an additional discriminator that survives session resume (see Stale Scope File Recovery).

### Hook Scoping and Session Isolation

The containment hook activates **only when a scope file exists for the current `session_id` AND the calling `agent_id` matches the scope file's `agent_id`**. This prevents:

- **Same-session operator usage:** Main-thread tool calls (no `agent_id` in hook input) always pass through, even while a scope file exists. The operator can Read/Grep/Glob freely during the same session.
- **Other subagent usage:** Subagents with a different `agent_id` than the shakedown agent are not constrained.
- **Cross-session contamination:** Different sessions have different `session_id` values and will not match the scope file.

The hook reads `session_id` and `agent_id` from the hook input (provided by Claude Code on every PreToolUse invocation — `agent_id` present only for subagent calls per `hooks#common-input-fields`), constructs the expected scope file path (`scope-<session_id>.json`), and passes through immediately if the file does not exist or the `agent_id` does not match.

**Why `agent_id` and not just `session_id`:** Claude Code's hook input provides `session_id` on every call but does not provide a dialogue-run-scoped identifier. `agent_id` is the finest-grained discriminator available for distinguishing shakedown subagent calls from main-thread or other-subagent calls within the same session.

### Stale Scope File Recovery

If a shakedown aborts before `SubagentStop` removes the scope file:

- **New session:** A new session has a different `session_id` and will not match the stale file — containment is not accidentally activated.
- **Resumed session (`--resume`):** Claude Code's resume flow reuses the original `session_id` (`hooks#json-output-2` documents the `resume` source). The `session_id` alone would match the stale file. However, containment requires both `session_id` match AND `agent_id` match. A resumed session spawns new subagents with new `agent_id` values, so the stale file's `agent_id` will not match — containment is not reactivated. If the operator explicitly relaunches the shakedown, the `SubagentStart` hook detects the existing scope file for the same `session_id`, removes it, and writes a fresh one with the new `agent_id`.
- **Stale seed files:** If the harness crashes between writing the seed file and spawning the subagent, the seed file remains but never becomes a scope file. The `SubagentStart` hook should also clean up stale seed files (age > 24 hours) for the current `session_id`. Seed files do not activate containment (PreToolUse looks for scope files only).
- **Startup cleanup:** The shakedown harness should check for and remove stale scope and seed files (age > 24 hours) at startup, following the same pattern as the handoff plugin's session-state cleanup. This cleanup should run on both fresh sessions and resume flows.
- **Manual cleanup:** An operator can remove stale files: `trash ${CLAUDE_PLUGIN_DATA}/shakedown/scope-*.json ${CLAUDE_PLUGIN_DATA}/shakedown/seed-*.json`.

### Hook Registration

Three hook registrations are required in `hooks.json`:

| Hook event | Matcher | Script | Purpose |
|------------|---------|--------|---------|
| `SubagentStart` | Shakedown agent type name | `containment_lifecycle.py` | Reads seed file + `agent_id` from hook input, writes scope file, removes seed file |
| `SubagentStop` | Same agent type name | `containment_lifecycle.py` | Removes scope file |
| `PreToolUse` | `Read\|Grep\|Glob` | `containment_guard.py` | Reads scope file, enforces `allowed_roots` via `updatedInput` / `permissionDecision` |

The `PreToolUse` matcher targets native `Read`, `Grep`, and `Glob` (not the codex-collaboration MCP prefix used by `codex_guard.py`). The existing `codex_guard.py` pattern demonstrates the stdin-JSON / exit-code / `updatedInput` protocol; both containment scripts use the same protocol.

The `SubagentStart` and `SubagentStop` matchers use the shakedown agent's custom agent type name (e.g., `"shakedown-dialogue"`). This ensures the lifecycle hooks fire only for the shakedown subagent, not for unrelated subagents like `Explore` or `Plan`.

## Dialogue Skill

The shakedown dialogue runs inside a **dedicated subagent** dispatched by the shakedown harness. This is a structural requirement, not an optimization: the containment hook uses the subagent's `agent_id` (from `hooks#common-input-fields`) to distinguish shakedown tool calls from the operator's same-session tool usage. The `agent_id` is captured by the `SubagentStart` lifecycle hook at spawn time and written into the scope file before the subagent's first tool call executes (see Hook State Transport).

A new `dialogue-codex` skill must instruct Claude to execute 6 concrete behaviors for the B1 shakedown:

1. **Extract factual claims** from each Codex reply.
2. **Register/update local claim state** before the next follow-up — new claims registered, revised claims updated, `not_scoutable` classification applied where the scoutable criteria ([scouting-behavior.md:215-221](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#L215)) are not met.
3. **Choose at most one scout target** per round using T4 priority order ([T4-SB-03](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#t4-sb-03)): unverified (attempts=0) → conflicted → ambiguous.
4. **Execute at least one definition and one falsification query** when scouting occurs, within the 2-5 tool call range ([T4-SB-04](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md#t4-sb-04)).
5. **Emit structured per-turn state** after each completed round: an evidence block (target claim, file path, line range, disposition, citations) and a verification-state summary (all tracked claims with current status). This is the inspector's primary observable surface — without it, the per-turn checklist cannot be executed. The format must be stable across turns (same field names, same structure) so the inspector can compare rounds.
6. **Produce a follow-up that visibly uses current ledger/evidence state** and concludes with inspectable epilogue fields on the terminal turn.

This is the B1-subset of the skill. It is not the full scored-run T4 consumer surface.

### Minimum Per-Turn Emission Schema

Behavior 5 requires a stable, inspectable format. The minimum required fields per round:

**Evidence block** (emitted after each scouting round):

| Field | Type | Description |
|-------|------|-------------|
| `target_claim` | string | The claim being scouted |
| `target_claim_id` | int | The claim's ledger ID |
| `scope_root` | string | The `allowed_roots` entry used for this round |
| `queries` | list | Each query: `{type: "definition"|"falsification"|"supplementary", tool: "Read"|"Grep"|"Glob", target: "<path or pattern>"}` |
| `disposition` | string | `"supports"` / `"contradicts"` / `"ambiguous"` / `"conflicted"` |
| `citations` | list | Each citation: `{path: "<file>", lines: "<range>", snippet: "<text>"}` |

**Verification-state summary** (emitted after each round, including non-scouting turns):

| Field | Type | Description |
|-------|------|-------------|
| `turn` | int | Current turn number |
| `claims` | list | Each claim: `{id: int, text: "<claim>", status: "<verification status>", scout_attempts: int}` |
| `counters` | object | `{total_claims: int, supported: int, contradicted: int, not_scoutable: int, unverified: int, evidence_count: int}` |
| `effective_delta` | object | Counter changes since last turn (on terminal turn, overall delta) |

This schema is the minimum for the shakedown inspector. Scored-run work may extend it with `claim_provenance_index`, `ClassificationTrace`, and other T4 surfaces.

## Loop State Architecture

Loop state is **Claude-side working state** carried in the dialogue and surfaced in the transcript.

- Server-side state for the shakedown remains limited to existing dialogue infrastructure artifacts (lineage store, journal, turn store).
- Behavioral loop state (claim ledger, verification states, counter values, evidence records) lives in Claude's structured working context during the dialogue.
- Evidence blocks are re-emitted after each completed scouting round ([state-model.md:503](t04-t4-scouting-position-and-evidence-provenance/state-model.md#L503)), giving the inspector a per-turn observable surface in the transcript.
- The dialogue skill's behavior 5 (emit structured per-turn state) ensures this surface exists in a stable, inspectable format. Without it, the per-turn checklist cannot be executed.
- The inspector reads loop state from the transcript: per-turn evidence blocks, verification-state summaries, follow-up text, and terminal epilogue.

## Inspection Protocol

Inspection granularity is **per-turn**, consistent with the risk analysis: "each turn's extraction" and "each ledger summary" ([risk-analysis.md:231-234](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md#L231)).

### Per-Turn Checklist

| # | Inspection item |
|---|----------------|
| 1 | Extracted claims and their registration outcome |
| 2 | Current verification-state summary |
| 3 | Selected scout target and why it won priority |
| 4 | Executed query set — at least one definition and one falsification query when scouting occurs |
| 5 | Resulting evidence record and updated verification status |
| 6 | Whether the next follow-up visibly uses that state |

### Terminal-Turn Checklist

| # | Inspection item |
|---|----------------|
| 7 | `effective_delta` matches recomputation from loop counters |
| 8 | Final convergence decision matches structured control logic |
| 9 | Synthesis epilogue is complete and internally consistent |

### Containment Checklist (All Turns)

| # | Inspection item |
|---|----------------|
| 10 | `scope_envelope` is present and `allowed_roots` is non-empty |
| 11 | All scouting tool calls stayed within B1-derived `allowed_roots` |
| 12 | No out-of-scope results in tool output (verified by path inspection; post-execution filtering is deferred to scored-run work) |

## Acceptance Criteria

### Ready-to-Run Preconditions

The shakedown is ready to run only when all of the following exist:

1. The `dialogue-codex` skill is implemented with all 6 behaviors and can be invoked through the existing dialogue infrastructure.
2. Containment hooks are registered: `SubagentStart`/`SubagentStop` lifecycle hooks (matched on shakedown agent type) for scope file create/remove, and `PreToolUse` guard for `Read`/`Grep`/`Glob` with `allowed_roots` enforcement.
3. B1 anchor-to-scope wiring writes a seed file with non-empty `allowed_roots` to `${CLAUDE_PLUGIN_DATA}/shakedown/seed-<session_id>.json` before spawning the subagent; the `SubagentStart` hook promotes it to a scope file with `agent_id`.
4. Transcript capture writes post-containment output to a stable shakedown path.
5. Shakedown metadata record writes commit SHA, timestamp, task ID `B1`, and classification `pre_benchmark_integration_shakedown`.

### Shakedown Result Model

The shakedown produces exactly one of three outcomes: `pass`, `fail`, or `inconclusive`.

**Evaluation order:** Check validity first, then correctness.

**Step 1 — Validity check (inconclusive gate):**

If more than half of B1's extracted claims are classified `not_scoutable`, the result is **inconclusive**. The loop mostly exercised the classification path, not the scouting path. Classification may be correct, but insufficient scouting-path exercise means the shakedown cannot validate loop integration. Stop here — do not evaluate pass/fail.

Action on inconclusive: re-evaluate whether B1 generates enough scoutable claims to validate the loop. If not, select an additional corpus task for a second shakedown run.

**Step 2 — Correctness check (pass/fail):**

The shakedown **passes** if manual per-turn inspection confirms all 12 checklist items hold.

The shakedown **fails** if any checklist item does not hold. On failure, route the failure back to the specific gate or control surface it invalidates:

| Failure class | Route to |
|---------------|----------|
| Claim extraction incorrect | Dialogue skill (behavior 1) |
| Ledger state wrong or ignored | Dialogue skill (behaviors 2, 6) |
| Scout target selection wrong | Dialogue skill (behavior 3), T4-SB-03 |
| Query coverage insufficient | Dialogue skill (behavior 4), T4-SB-04 |
| Per-turn state not emitted or unstable format | Dialogue skill (behavior 5) |
| Convergence decision wrong | T1 control contract |
| Containment violated | PreToolUse hook implementation |
| Epilogue incomplete | Dialogue skill (behavior 6) |

## Shakedown Artifacts

Use shakedown-specific artifacts, not benchmark artifact names.

| Artifact | Contents |
|----------|---------|
| Raw transcript | Post-containment dialogue transcript |
| Shakedown metadata | Commit SHA, timestamp, task ID `B1`, classification `pre_benchmark_integration_shakedown` |
| Inspection notes | Per-turn checklist results tied to the single run |

Do NOT emit `manifest.json`, `runs.json`, `adjudication.json`, or `summary.md` for this packet. Those names are reserved for benchmark execution.

## Ownership Boundary

| Owner | Responsibility |
|-------|---------------|
| T7 (this document) | Defines the behavioral layer, acceptance criteria, containment mechanism, inspection protocol, and boundary table |
| T8 | Implements the behavioral layer, runs the shakedown, produces inspection notes |

## What the Shakedown Proves

A passing B1 shakedown proves that the existing dialogue infrastructure plus the new B1 behavioral layer can run one contained dialogue end-to-end and keep usable local loop state.

It does **not** prove:

- Benchmark readiness
- Scored-run validity
- B8 adequacy
- Full T4 coverage
- Benchmark artifact correctness
- T5 mode migration correctness
- Resilience under error conditions

## T8 Handoff

T8 receives this definition and implements the minimum runnable packet.

**First validation (before other implementation):** Confirm that `SubagentStart` hooks complete before the subagent's first `PreToolUse`. Write a minimal test: a `SubagentStart` hook creates a marker file, and the subagent's first `PreToolUse` checks for it. If the ordering does not hold, implement a short-timeout poll in the `PreToolUse` hook that denies the call if the scope file never appears (fail closed). This validates the inferred lifecycle ordering that the containment design depends on (see Hook State Transport).

**Implementation items:**

1. `dialogue-codex` skill with 6 concrete behaviors (including per-turn state emission), running inside a dedicated subagent (custom agent type for hook matching)
2. Loop mechanics producing inspectable state
3. Containment hooks: `SubagentStart`/`SubagentStop` lifecycle hooks (scope file create/remove) + `PreToolUse` guard for `Read`/`Grep`/`Glob` (activation requires `session_id` + `agent_id` match)
4. B1 anchor-to-scope wiring (harness writes seed file with `allowed_roots`, `SubagentStart` promotes to scope file with `agent_id`, `SubagentStop` removes)
5. Transcript capture (post-containment)
6. Shakedown metadata record
7. Per-turn inspection notes

After the shakedown passes, T8 expands toward benchmark execution:

| Expansion | Source |
|-----------|--------|
| Benchmark artifact set | [benchmark.md:182-195](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md#L182) |
| Transcript parser and diff engine | [T4-BR-02](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-02) |
| Narrative-claim inventory and completeness | [T4-BR-06](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-06) |
| Methodology findings and threshold | [T4-BR-09](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-09) rows 1-2 |
| Omission-audit proof | [T4-BR-07](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-07) item 8 |
| T5 `agent_local` migration | [T4-BR-01](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#t4-br-01) (external prerequisite) |
| B8 and remaining corpus tasks | After enforcement gaps closed ([composition-review.md:123](../reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md#L123)) |

## Boundary Table

| Surface | Current state | Required for shakedown | Deferred / external |
|---------|--------------|----------------------|-------------------|
| Dialogue infrastructure (`start/reply/read`, lineage, journal, runtime) | Exists (460 tests) | Reuse | — |
| `dialogue-codex` skill | Missing | Yes — T7 defines, T8 implements | — |
| T4 behavioral loop (claim extraction, registration, ledger, counters, convergence) | Missing | Yes — T7 defines, T8 implements | — |
| PreToolUse containment hooks (`Read`/`Grep`/`Glob` against `allowed_roots`) | Missing | Yes — T7 defines, T8 implements | — |
| B1 anchor-to-scope wiring | Missing | Yes — T7 defines, T8 implements | Scored-run scope formalization is later T7 work |
| Transcript capture (post-containment) | Missing | Yes — T7 defines, T8 implements | Parseable transcript spec, parser, diff are later work |
| Shakedown metadata + inspection notes | Missing | Yes — T7 defines, T8 implements | Benchmark artifact contract is later work |
| Benchmark artifact set | Missing | No | Required only for benchmark execution |
| Scored-run harness (inventory, completeness, methodology, proof) | Missing | No | Required only for scored runs |
| T5 `agent_local` migration | Missing | No | External prerequisite for scored runs (T5-owned) |
| B8 anchor-adequacy decision rule | Missing | No | Later T7 scored-run work |

## References

| What | Where |
|------|-------|
| T-04 benchmark-first design plan | [2026-04-01-t04-benchmark-first-design-plan.md](2026-04-01-t04-benchmark-first-design-plan.md) |
| Convergence-loop risk analysis | [2026-04-01-t04-convergence-loop-risk-analysis.md](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md) |
| T6 composition review | [2026-04-04-t04-t6-benchmark-first-design-composition-review.md](../reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md) |
| T4 scouting behavior | [scouting-behavior.md](t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md) |
| T4 state model | [state-model.md](t04-t4-scouting-position-and-evidence-provenance/state-model.md) |
| T4 containment | [containment.md](t04-t4-scouting-position-and-evidence-provenance/containment.md) |
| T4 benchmark readiness | [benchmark-readiness.md](t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md) |
| Benchmark contract | [dialogue-supersession-benchmark.md](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) |
| T5 mode strategy | [2026-04-02-t04-t5-mode-strategy.md](2026-04-02-t04-t5-mode-strategy.md) |
| Codex-collaboration delivery | [delivery.md](../superpowers/specs/codex-collaboration/delivery.md) |
| Codex-collaboration foundations | [foundations.md](../superpowers/specs/codex-collaboration/foundations.md) |
| T7 corpus constraint ticket | [T-20260403-01](../tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md) |

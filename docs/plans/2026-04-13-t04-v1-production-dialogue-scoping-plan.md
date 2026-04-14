---
title: "T-04 v1 Production Dialogue Scoping Plan"
date: 2026-04-13
status: Approved
supersession_ticket: T-20260330-04
prior_authority:
  - docs/plans/2026-04-02-t04-t1-structured-termination-contract.md
  - docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md
  - docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
  - docs/plans/2026-04-07-t7-executable-slice-definition.md
  - docs/plans/2026-04-07-t8-minimum-runnable-shakedown-packet.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md
---

# T-04 v1 Production Dialogue Scoping Plan

## 1. Purpose and Non-Purposes

This plan defines a **first production slice** under T-04 that lets a user
invoke `/dialogue <objective>` against codex-collaboration's existing runtime.
It is deliberately thin and re-minimized around what the current containment
transport actually supports: a single contained subagent per session, a
parent-written active-run pointer plus seed, a `SubagentStart`-materialized
scope, and a `SubagentStop`-captured transcript. The slice adds no new
transport machinery.

**This plan is:**

- A first-production-slice plan, not a T-04 closure plan (see §2 split).
- A concrete ownership table naming four new v1 surfaces and their
  dependencies on existing lifecycle, guard, and runtime code.
- An explicit run model obeying the seed-to-scope lifecycle in
  `packages/plugins/codex-collaboration/scripts/containment_lifecycle.py`.
- A required hook-matcher extension that wires lifecycle enforcement onto
  the new production agent.
- A two-artifact emission contract: a user-facing production synthesis
  and an internal verification transcript using the exact emission shape
  the current `dialogue-codex` skill already produces.
- A named v1 consumer path that proves cross-model migrations are not in
  scope.

**This plan is NOT:**

- T-04 closure. Pre-dialogue gatherer agents, deterministic briefing
  assembly, and multi-agent scope transport are explicit remaining T-04
  work, not v1 (§2.2).
- A literal port of cross-model surfaces. Cross-model `dialogue/SKILL.md`,
  `codex-dialogue.md`, and the context-gatherer agents are semantic
  sources only.
- A redesign of T1–T6 semantics. Those are adopted as-is via a
  production-local extraction of the current `dialogue-codex` skill's
  per-turn contract (§4, §9.3).
- A plan for scored benchmark execution or analytics. Those are owned by
  downstream tickets (T-20260330-05/06/07) or gated by T4-BR-07
  prerequisites.

## 2. Scope

### 2.1 v1 Acceptance (this slice)

1. User invokes `/dialogue <objective>` and receives a production synthesis
   artifact on termination.
2. Exactly one contained subagent — `dialogue-orchestrator` — is spawned
   per dialogue run. Its `Read`/`Grep`/`Glob` calls are enforced by the
   existing containment guard.
3. The orchestrator performs a brief inline initial scouting phase before
   the first `codex.dialogue.reply`, entirely within its own agent body.
4. The per-turn loop honors every accepted T1–T6 semantic via a
   production-local extracted reference doc (§4, §9.3).
5. Terminalization emits two artifacts:
   - Production synthesis artifact (user-facing, structured JSON).
   - Verification transcript in the exact emission shape the current
     `dialogue-codex` skill already produces (internal, JSONL).
6. The 14-item inspection rubric passes against the verification
   transcript for at least one representative objective.
7. The existing 566-test shakedown suite continues to pass unchanged.

### 2.2 Remaining T-04 Acceptance (explicitly not v1)

The T-04 ticket names gatherers and deterministic briefing assembly in its
scope and acceptance bar
(`docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`).
v1 does not close T-04. The remaining closure acceptance is:

1. Production `context-gatherer-code` and `context-gatherer-falsifier`
   agents adapted from cross-model semantic sources.
2. Deterministic briefing assembly composing gatherer output into a
   structured pre-dialogue briefing block.
3. Multi-agent scope-transport design sufficient to contain gatherers
   alongside the orchestrator (phased scope rewrites within one run, or
   multi-run aggregation semantics).
4. Shakedown-to-production reference unification: `dialogue-codex` factored
   to a thin adapter over the production-local extracted reference doc,
   making the reference true shared authority.
5. Whatever further items the ticket's closure bar names that are not in
   §2.1.

### 2.3 Explicitly Out of v1

| Out of scope | Why |
|---|---|
| Pre-dialogue gatherer agents | §2.2 remaining T-04 acceptance |
| Deterministic briefing assembly | §2.2 remaining T-04 acceptance |
| Multi-agent scope-transport extension | §2.2 remaining T-04 acceptance |
| Shakedown-to-production reference unification | §2.2 remaining T-04 acceptance |
| Concurrent shakedown + production runs in one session | Shared-namespace single-active-run constraint (§5.2) defers dual-run to post-v1 |
| `<data_dir>/shakedown/` directory rename | Post-v1 cleanup; acknowledged infrastructure debt |
| Containment-guard operator-message wording ("shakedown scope") | Same — naming drift, not a behavioral defect |
| Scored benchmark execution | Gated by T4-BR-07 prerequisite items 1–8 |
| Cross-model `dialogue/SKILL.md` parser migration | Deferred until a cross-model consumer ingests v1's synthesis artifact (§7.2) |
| Cross-model `codex-dialogue.md` changes | T5 §6 deliberate non-migration |
| Analytics dashboard / cutover | Owned by T-20260330-06/07 |
| Secrets redaction for allowed-scope content | T4-CT-05 declared external blocker; v1 inherits benchmark-corpus-safe assumption with explicit documentation |

## 3. User-Facing `/dialogue` Contract

### 3.1 Invocation

```
/dialogue <objective>
```

- `<objective>` — free-form prose. The user's dialogue prompt.
- Optional trailing flags for profile selection and explicit paths are
  implementation detail, not contract points.

### 3.2 Production Synthesis Artifact (user-facing)

Terminalization produces a single structured JSON artifact:

| Field | Source | Contract |
|---|---|---|
| `objective` | Echoed from invocation | — |
| `mode` | Orchestrator | Always `"agent_local"` (T5) |
| `mode_source` | Orchestrator | Always `null` (T5 §3.5) |
| `termination_code` | Orchestrator | One of the `TerminationCode` enum values (Risk B) |
| `converged` | Orchestrator | Mechanical projection of `termination_code` |
| `turn_count` / `turn_budget` | Orchestrator | Actual turns consumed and budget declared |
| `final_claims[]` | Orchestrator | `{text, final_status, representative_citation}`. No audit trail, no `minimum_fallback`, no `scout_attempts` |
| `synthesis_citations[]` | Orchestrator | `{path, line_range, snippet}` — evidence the user can verify the answer against |
| `final_synthesis` | Orchestrator | Narrative answer |
| `ledger_summary` | Orchestrator | Terminal human-readable summary (single emission at termination) |

The production artifact contains no verification telemetry. Per-turn
`effective_delta` lives in the verification transcript (§3.3); raw per-scout
evidence records are reconstructable from transcript fields (§3.3), not
separately emitted. `minimum_fallback` accounting and scope-breach counts
are orchestrator-internal state — they do NOT appear in the user-facing
artifact and, per §3.3's no-new-fields commitment, they do NOT appear in
the verification transcript either. Scope-breach outcomes surface via
`termination_code = "scope_breach"` in this production artifact (T1 enum)
and via `converged = false` plus `ledger_summary` prose in the transcript
epilogue (§3.3); `minimum_fallback` branches are verified by source review
per `dialogue-codex/SKILL.md:120` ("transcript-indistinguishable from an
omitted fallback").

### 3.3 Verification Transcript (internal)

Captured via the existing `SubagentStop` lifecycle at
`<data_dir>/shakedown/transcript-<run_id>.jsonl`. Shape is **exactly** what
the current `dialogue-codex` skill already emits per
`packages/plugins/codex-collaboration/skills/dialogue-codex/SKILL.md:252–268`:

- Per-turn state blocks with these 13 fields: `turn`, `scouted`,
  `target_claim_id`, `target_claim`, `scope_root`, `queries`,
  `disposition`, `citations`, `claims`, `counters`, `effective_delta`,
  `terminal`, `epilogue`.
- First emitted state block is `turn: 2` (first post-reply verification
  turn); `turn: 1` is the opening send and does not emit a state block.
- Terminal state block carries an `epilogue` object with `ledger_summary`,
  `converged`, `effective_delta_overall`.

v1 adds **no new emission fields** to this shape. The Risk-J structured
per-scout evidence record is reconstructable from the emitted fields
(`turn` + `target_claim` + `scope_root` + `queries` + `citations` +
`disposition`) during rubric inspection; it is not a separately emitted
field.

**Explicitly NOT in the transcript.** The current `dialogue-codex`
emission shape carries no `scope_breach_count` counter and excludes
`minimum_fallback` claims from `claims` and `counters` per
`dialogue-codex/SKILL.md:111-120`. The no-new-fields commitment holds
in v1: scope-breach outcomes surface via orchestrator logs plus
`converged = false` and `ledger_summary` prose in the terminal epilogue;
zero-claim / `minimum_fallback` branches are verified by source review,
not transcript inspection. `termination_code` itself is a production-
synthesis field (§3.2), not a transcript field — the transcript epilogue
projects it to `converged: bool`.

### 3.4 Dialogue Run Lifecycle (user-facing view)

1. User invokes `/dialogue <objective>`.
2. `/dialogue` skill writes parent-owned state (active-run pointer + seed)
   and dispatches the orchestrator.
3. Claude Code spawns the orchestrator; `SubagentStart` hook materializes
   the scope file (§6).
4. Orchestrator performs inline initial scouting, then opens the Codex
   dialogue via `codex.dialogue.start` (handle only) and sends the
   objective via the first `codex.dialogue.reply`.
5. Orchestrator runs the per-turn loop until a `TerminationCode` is
   produced.
6. `SubagentStop` hook copies the orchestrator's transcript to
   `transcript-<run_id>.jsonl`.
7. Orchestrator returns the production synthesis artifact to the
   `/dialogue` skill; skill surfaces it to the user.

## 4. Ownership Table

| Surface | Path | Status | Owns | Depends on |
|---|---|---|---|---|
| `/dialogue` user skill | `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` | **NEW** | Invocation parsing, preflight stale-state cleanup, shared-namespace single-run check, parent-owned active-run + seed write, orchestrator dispatch, production synthesis surfacing | Orchestrator agent, containment lifecycle hooks, `scripts/clean_stale_shakedown.py` |
| `dialogue-orchestrator` agent | `packages/plugins/codex-collaboration/agents/dialogue-orchestrator.md` | **NEW** | Inline initial scouting, per-turn loop execution, production-synthesis emission. Cites the production-local turn-semantics reference | Turn-semantics reference doc, `codex.dialogue.*` runtime, existing containment guard |
| Turn-semantics reference doc | `packages/plugins/codex-collaboration/references/dialogue-turn-contract.md` | **NEW** (extracted from current `dialogue-codex` body at v1 start) | Production-local authoritative turn contract (target selection, claim classification, status derivation, disposition enum, emission shape, terminalization, budget semantics) | — |
| Hook matchers (`SubagentStart`, `SubagentStop`) | `packages/plugins/codex-collaboration/hooks/hooks.json` | **EXISTING — EXTEND** | Lifecycle enforcement for `dialogue-orchestrator` in addition to `shakedown-dialogue` | Existing `containment_lifecycle.py` |
| `dialogue-codex` skill | `packages/plugins/codex-collaboration/skills/dialogue-codex/SKILL.md` | **EXISTING — UNTOUCHED** | Shakedown per-turn contract. Byte-for-byte unchanged in v1. Remains redundant with the extracted reference; unification is remaining-T-04 work (§2.2) | — |
| `shakedown-b1` skill / `shakedown-dialogue` agent | `packages/plugins/codex-collaboration/skills/shakedown-b1/`, `agents/shakedown-dialogue.md` | **EXISTING — UNTOUCHED** | Shakedown user flow | — |
| Containment transport (lifecycle + guard + server helpers) | `packages/plugins/codex-collaboration/scripts/containment_lifecycle.py`, `scripts/containment_guard.py`, `server/containment.py` | **EXISTING — UNTOUCHED** | Active-run / seed / scope / transcript lifecycle, PreToolUse guard for Read/Grep/Glob | — |
| `codex.dialogue.start/reply/read` | `packages/plugins/codex-collaboration/server/dialogue.py`, `server/mcp_server.py` | **EXISTING — UNTOUCHED** | Codex thread persistence, transport | — |

**Ownership invariants:**

- `dialogue-codex` skill body is byte-for-byte unchanged in v1.
  `shakedown-b1` and `shakedown-dialogue` are byte-for-byte unchanged in v1.
  The 566-test shakedown suite must continue to pass unchanged.
- The extracted reference doc is **production-local authority** in v1, not
  shared authority. Shakedown continues to rely on its own skill body.
  Shared-authority unification is explicit remaining-T-04 work (§2.2).
- Existing containment scripts and server code are unchanged. The only
  containment-adjacent edit is `hooks.json` matcher extension (§7.1).

## 5. Containment Model for v1

### 5.1 Decision

v1 uses coarse repo-root `allowed_roots` for `/dialogue`:

```
seed = {
  "session_id": <session_id>,
  "run_id": <run_id>,
  "file_anchors": [],
  "scope_directories": [<repo_root>],
  "created_at": <ISO timestamp>,
}
```

`scope_directories = [<repo_root>]` ensures the containment guard allows
`Read`/`Grep`/`Glob` anywhere under the repo root while still enforcing
the anti-narrowing invariant and scope-breach counter
(T4-CT-01, T4-CT-02).

### 5.2 Shared-Namespace Constraint

v1 writes production artifacts into the existing `<data_dir>/shakedown/`
directory alongside shakedown artifacts. The directory name is now
infrastructure debt; post-v1 cleanup renames it (§7.2).

**Consequence: one active contained run per session.** The transport is
keyed by a single `active-run-<session_id>` pointer
(`server/containment.py:36`); a session can have at most one active
contained run at any moment. Concurrent shakedown and production runs in
the same session are **not supported** in v1.

If the user invokes `/dialogue` while a shakedown run is active (or vice
versa), the second invocation MUST fail fast with an operator-visible
message pointing at the live run's state. Both entry points
(`/dialogue` skill and shakedown-b1 skill) must implement this check.
§9.4 captures this as a named risk.

### 5.3 Declared Safety Dependency (Inherited)

T4-CT-05 declares an external blocker: within `allowed_roots`, files may
contain secrets, and T4's direct tools have no redaction equivalent to
the helper-era `redactions_applied`. v1 inherits this assumption
explicitly — the production `/dialogue` surface is safe for
benchmark-corpus-like repos (curated, secret-free) but not for general
repos that may contain credentials in tracked files. A v1 release note
must state this limitation.

### 5.4 Anti-Narrowing Invariant

The orchestrator MUST NOT select a narrower `scope_root` to exclude files
that might contradict a claim under investigation. Invariant verbatim
from T4-CT-02.

## 6. Run Model

### 6.1 Seed-to-Scope Lifecycle (obeys current transport)

`containment_lifecycle.py` makes `SubagentStart` the scope-file creator.
The parent cannot know the child's `agent_id` before spawn, so it MUST
NOT write scope. v1 obeys this lifecycle literally.

| Step | Actor | Action |
|---|---|---|
| 1 | `/dialogue` skill (parent) | Run preflight stale-state cleanup by invoking `scripts/clean_stale_shakedown.py` (the same sweep `shakedown-b1` runs at its step 4, prior to its own live-run check). Then check for live `active-run-<session_id>`; if present, fail fast per §5.2. Generate `run_id`. `write_text_file(active_run_path(session_id), run_id)`. `write_json_file(seed_file_path(run_id), seed)` with `scope_directories=[<repo_root>]` and `file_anchors=[]`. **Do not write scope file.** The preflight sweep is load-bearing: a crashed prior run's `active-run-<session_id>` + `scope-<run_id>.json` would otherwise trip the live-run check before any post-spawn cleanup can fire (`containment_lifecycle.py:73` runs inside `_handle_subagent_start`, which is unreachable when the parent fails fast pre-spawn). |
| 2 | `/dialogue` skill | Dispatch `dialogue-orchestrator` subagent. |
| 3 | `SubagentStart` hook (existing, matcher extended per §7.1) | Runs `_handle_subagent_start`: reads pointer, reads seed, calls `build_scope_from_seed(seed, agent_id)` with hook-provided `agent_id`, writes `scope-<run_id>.json`, unlinks seed. Behavior unchanged. |
| 4 | `dialogue-orchestrator` agent | Inline initial scouting (§6.2); then `codex.dialogue.start(repo_root)` (handle creation, no state block); then first `codex.dialogue.reply(collaboration_id, objective)` (turn 1 send, no state block); then per-turn loop emitting state blocks from `turn: 2` onward per the reference doc. |
| 5 | `SubagentStop` hook (existing, matcher extended per §7.1) | Runs `_handle_subagent_stop`: copies transcript to `transcript-<run_id>.jsonl`, writes `.done` marker, unlinks `scope-<run_id>.json`. The `active-run-<session_id>` pointer is left in place and overwritten on the next invocation or pruned by the 24h age sweep. Behavior unchanged. |
| 6 | `/dialogue` skill | Receives the production synthesis artifact from the orchestrator's final message; surfaces it to the user. |

### 6.2 Inline Initial Scouting

Before `codex.dialogue.start`, the orchestrator performs a bounded
scouting pass against the user's objective. Purpose: pre-seed context so
the first Codex reply is not cold. Scope:

- At most **N tool calls** (initial target N=3; exact budget pinned at
  authoring time and named in the orchestrator's agent body).
- Targets `<objective>` plus any optional explicit paths.
- Produces a short prose context block the orchestrator prepends to the
  first `reply`'s `objective` parameter.
- Does **not** produce a separate briefing artifact, does **not** emit a
  state block, does **not** grow into a gatherer subsystem.

If inline scouting expands beyond the initial budget or starts producing
structured briefing artifacts, that is the signal to split it into a
gatherer agent — which is remaining T-04 work (§2.2), not v1 scope creep.
§9.2 captures this as a named risk.

### 6.3 Per-Turn Loop (inside the reference doc)

The per-turn loop is defined normatively in the extracted turn-semantics
reference doc (§4). The orchestrator cites the reference and executes it
verbatim. Every accepted T1–T6 semantic is present:

- TerminationCode enum projection (Risk B)
- `minimum_fallback` provenance tagging and exclusion rules (T2; Risk A)
- Deterministic referential continuity (T3; Risk C)
- Structured per-scout evidence in the state block (Risk J;
  reconstructable from the emitted fields)
- `agent_local` mode emission (T5)
- Cross-turn unresolved diff / `unresolved_closed` (Risk K)
- Scope-breach termination separate from convergence (Risk G; the
  orchestrator-internal breach count reaching the Risk-G threshold
  produces `termination_code = "scope_breach"`, `converged = false`;
  the count itself is NOT an emitted field — only the termination code
  in the production synthesis (§3.2) and `converged` + `ledger_summary`
  prose in the transcript epilogue are observable per §3.3)
- Canonical ledger block survival under compression (Risk F)

## 7. Migration Table

### 7.1 Required for v1

| Surface | Change | Rationale |
|---|---|---|
| `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` | Create (new) | v1 user surface |
| `packages/plugins/codex-collaboration/agents/dialogue-orchestrator.md` | Create (new) | v1 orchestrator |
| `packages/plugins/codex-collaboration/references/dialogue-turn-contract.md` | Create (extracted from current `dialogue-codex` body) | Production-local authoritative turn contract |
| `packages/plugins/codex-collaboration/hooks/hooks.json` — `SubagentStart` and `SubagentStop` matchers | Extend to match `dialogue-orchestrator` in addition to `shakedown-dialogue` | **Critical.** Without this, seed-to-scope materialization and transcript capture never fire for production runs |

**Hook matcher extension detail.** Current `hooks.json:15, 26` matches
only `"shakedown-dialogue"`. The v1 edit changes both matchers to match
`"shakedown-dialogue|dialogue-orchestrator"` (or adds two entries with
the same script — either form works). If this edit is omitted, the
orchestrator's `Read`/`Grep`/`Glob` calls pass through uncontained
because no scope file is ever materialized, and no transcript is ever
captured — a silent defeat of the entire containment story. §8.3
includes an explicit verification check for hook firing.

### 7.2 Deferred to later compatibility work

| Surface | Change | Deferral trigger |
|---|---|---|
| `packages/plugins/cross-model/scripts/event_schema.py` (`VALID_MODES`) | Add `agent_local` | First cross-model consumer ingests a v1 artifact |
| `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Document `agent_local` | Same |
| `packages/plugins/cross-model/skills/dialogue/SKILL.md` (epilogue parser) | Accept `agent_local` without fallback rewrite | Same — v1 synthesis is not routed through cross-model's parser |
| Cross-model analytics-builder / validator tests | Propagation coverage for `agent_local` | Pairs with the enum change |
| Cross-model HANDBOOK / README | Operator-facing doc updates | Pairs with parser migration |
| `dialogue-codex` skill factored to reference-doc adapter | Factor shakedown skill body to adapter over the production-local reference; reference becomes shared authority | Remaining-T-04 work (§2.2) |
| `<data_dir>/shakedown/` directory rename | Rename to neutral (e.g., `runs/`) or introduce a parallel `dialogue/` namespace | Dual-run support or operator-naming confusion |
| `containment_guard.py:180` operator-message wording | Change "outside the shakedown scope" to neutral phrasing | Same — naming drift |
| Secrets redaction | Post-v1 redaction at PreToolUse or at synthesis emission | T4-CT-05 declared external blocker |
| Pre-dialogue gatherer agents + briefing assembly + multi-agent scope transport | Create production-local gatherer agents; design multi-agent scope transport; ship deterministic briefing assembly | Remaining-T-04 closure (§2.2) |

**Deferral-trigger honesty.** v1 names the concrete consumer path:

- Production synthesis artifact consumer: the invoking user only. No
  cross-model surface receives or validates this artifact.
- Verification transcript consumer: the 14-item rubric (prose
  inspection), nothing else. `event_schema.VALID_MODES` and the
  cross-model epilogue parser are not in the rubric's consumption path.

Cross-model migration becomes binding the first time a cross-model
surface (analytics, adjudicator, validator) is wired into either pipeline.

## 8. Verification Path

### 8.1 What v1 reuses from T8

| T8 asset | Reuse | How |
|---|---|---|
| Containment guard (`scripts/containment_guard.py`) | Yes — as-is | Guards orchestrator's `Read`/`Grep`/`Glob` |
| Containment lifecycle (`scripts/containment_lifecycle.py`) | Yes — hook matchers extended | Materializes scope on `SubagentStart`; captures transcript on `SubagentStop` |
| Transcript JSONL capture | Yes — as-is | Produces v1 verification transcript at `shakedown/transcript-<run_id>.jsonl` |
| `dialogue-codex` skill content | Extracted at v1 start into the production-local reference doc | Production-local authority; shakedown skill untouched |
| 14-item inspection rubric (in `shakedown-b1/SKILL.md`) | Yes — as a prose inspection tool | Applied to v1 verification transcript |
| `shakedown-b1` skill | **No** | Not the production user flow |
| `shakedown-dialogue` agent | **No** | Not the production contained agent |

### 8.2 End-to-End Verification

A representative `/dialogue <objective>` invocation must:

1. Dispatch the orchestrator with a valid active-run + seed on disk and
   no pre-existing scope file.
2. `SubagentStart` materializes `scope-<run_id>.json` with
   `agent_id` equal to the orchestrator's hook-provided `agent_id`.
3. Containment guard allows on-scope Read/Grep/Glob and denies off-scope;
   breach count is surfaced in the terminal epilogue.
4. Orchestrator completes the loop and emits:
   - Production synthesis artifact to the `/dialogue` skill.
   - Per-turn state blocks captured by `SubagentStop` into
     `transcript-<run_id>.jsonl`.
5. 14-item rubric passes against the transcript.
6. 566-test shakedown suite still passes unchanged.

### 8.3 Verification Checks

| Check | Source | Expected |
|---|---|---|
| `SubagentStart` and `SubagentStop` hooks fire for `dialogue-orchestrator` (matcher extension in place) | `hooks.json` after §7.1 edit | Pass — absence here silently defeats containment |
| Transcript state-block fields match current `dialogue-codex` emission shape exactly (13 fields, no additions) | `dialogue-codex/SKILL.md:252–268` | Pass |
| First emitted state block is `turn: 2`; subsequent strictly increasing | T-20260410-01 closed contract | Pass |
| 14-item rubric | `shakedown-b1/SKILL.md` (rubric only; shakedown flow not invoked) | All 14 items pass |
| Production synthesis contains `mode="agent_local"`, `mode_source=null` | T5 §3.5 | Pass |
| Termination yielded a `TerminationCode`; `converged` is its mechanical projection | Risk B | Pass |
| Containment denied any out-of-scope tool invocation; breaches surface via orchestrator logs, `termination_code = "scope_breach"` in the production artifact (§3.2), and `converged = false` + `ledger_summary` prose in the transcript epilogue — not via a structured counter per §3.3 | T4-CT-01 / T4-CT-02 | Pass |
| No code path invoked `shakedown-b1` or `shakedown-dialogue` | Boundary invariant | Pass |
| 566-test shakedown suite | Existing suite | Pass unchanged |

### 8.4 Shakedown/Production Boundary Invariants

- `dialogue-codex` skill body is byte-for-byte unchanged in v1.
- `shakedown-b1` skill and `shakedown-dialogue` agent are byte-for-byte
  unchanged in v1.
- No production surface loads shakedown skills or invokes the shakedown
  agent.
- 14-item rubric is reused as a **test rubric**, not as a production
  user flow. Production user flow is `/dialogue`.
- T8 smoke log (`t8-t4-live-smoke-log.md`) remains the shakedown
  verification record. v1 verification produces a separate artifact.
- The user-invocable `/dialogue` skill's `allowed-tools` does NOT
  include any `codex.dialogue.*` MCP tools — the `dialogue-orchestrator`
  agent owns those calls. This preserves
  `test_bootstrap.py::test_no_user_invocable_dialogue_skill_exists`
  unchanged in v1: the test asserts no user-invocable skill's
  `allowed-tools` references dialogue MCP tools, and a production
  `/dialogue` skill that only dispatches the orchestrator via the
  `Agent` tool satisfies that boundary mechanically. Post-v1 cleanup
  may rename the test to match its actual assertion.

## 9. v1-Specific Risks

### 9.1 Hook-matcher extension silently omitted

**Mechanism.** Implementation session adds `/dialogue` skill and
`dialogue-orchestrator` agent without extending the `SubagentStart` /
`SubagentStop` matchers in `hooks.json`. Containment lifecycle never
activates for production runs. Orchestrator's `Read`/`Grep`/`Glob`
calls pass through uncontained; no transcript is captured; verification
rubric cannot run.

**Mitigation.** §7.1 names the matcher extension as **critical** with
explicit before/after. §8.3 includes an explicit hook-firing check.
§11 acceptance criteria gates on the matcher being in place.

### 9.2 Inline initial scouting grows into a briefing subsystem

**Mechanism.** Bounded inline scouting (§6.2) is a pragmatic quality
compromise for v1's no-gatherer slice. If it expands — additional tool
calls, structured briefing blocks, dedicated pre-dialogue phases — v1
silently re-discovers the briefing-assembly layer deferred to remaining
T-04.

**Mitigation.** §6.2 caps the budget at small N, forbids separate
briefing artifacts, and names growth past the cap as the trigger to
split into a gatherer agent (remaining T-04 work).

### 9.3 Production-local reference drifts from `dialogue-codex`

**Mechanism.** Reference doc is extracted from `dialogue-codex` at v1
start. If either surface is edited during v1 without mirroring the
other, they silently diverge. Shakedown and production would then run
against semantically different per-turn contracts.

**Mitigation.** v1 commits to zero behavioral edits to per-turn
semantics in either `dialogue-codex` or the reference doc. Any hotfix
or clarification must land in both surfaces in the same commit —
explicit review-time discipline. Remaining-T-04 closure eliminates the
risk by factoring `dialogue-codex` to a thin adapter over the reference.

### 9.4 Shared-namespace single-run constraint surprises users

**Mechanism.** §5.2 constrains a session to one active contained run.
A user who starts a shakedown run then invokes `/dialogue` (or vice
versa) sees the second invocation fail.

**Mitigation.** Both entry points run the `clean_stale_shakedown.py`
preflight sweep (24h age threshold) before the live-run check, consistent
with `shakedown-b1` step 4. If a stale run younger than 24h blocks the
check, the operator-visible message points at the live run's state for
manual remediation. §11 acceptance gates on both the preflight sweep
and the check existing.

### 9.5 Secrets leak through coarse `allowed_roots`

**Mechanism.** Repo-root containment allows orchestrator `Read`/`Grep`/
`Glob` anywhere in the repo. If the repo contains credentials, they may
reach the orchestrator and potentially surface in the production
synthesis artifact.

**Mitigation.** §5.3 inherits T4-CT-05 explicitly. v1 release note
documents the benchmark-corpus-safe assumption. Post-v1 packet owns
resolving this (redaction at PreToolUse or at synthesis emission).

### 9.6 Operator-visible naming drift in containment messages

**Mechanism.** `containment_guard.py:180` denies with "Requested Read
path is outside the shakedown scope." For production denials, "shakedown"
is misleading.

**Mitigation.** Acceptable for v1; §7.2 names the wording fix as
post-v1 cleanup. v1 release note documents the drift so operators are
not confused.

## 10. v1 Open Questions

Do not block plan approval; authoring-time decisions for the
implementation session that follows.

1. Exact inline-scouting tool budget for §6.2 (initial target: N=3).
2. Exact `/dialogue` flag vocabulary — profile selection, initial
   explicit paths, budget override.
3. Production synthesis serialization — Markdown wrapper around the JSON
   vs raw JSON surfaced in the user's chat.
4. Recovery semantics on orchestrator crash (low-impact; v1 targets
   happy path).

## 11. Acceptance Criteria for Plan Approval

- [ ] §1 frames v1 as a first production slice under T-04, not closure.
- [ ] §2 splits v1 acceptance from remaining T-04 acceptance explicitly.
- [ ] §4 ownership table names the four new v1 surfaces: `/dialogue`
      skill, `dialogue-orchestrator` agent, turn-semantics reference doc,
      `hooks.json` matcher extension.
- [ ] §5 states the shared-namespace single-active-run constraint plainly.
- [ ] §6 run model obeys the current seed-to-scope lifecycle — parent
      writes active-run + seed; `SubagentStart` writes scope.
- [ ] §6.1 step 1 names preflight stale-state cleanup
      (`clean_stale_shakedown.py`) before the shared-namespace
      live-run check.
- [ ] §7.1 names the `hooks.json` matcher extension as **critical**
      required v1 change with explicit before/after.
- [ ] §8.1 reuses existing containment lifecycle and the 14-item rubric
      without invoking shakedown skills or modifying shakedown artifacts.
- [ ] §8.3 includes explicit checks for hook firing and for transcript
      fields matching the current emission shape (no additions).
- [ ] §8.4 preserves shakedown/production boundary invariants: no edits
      to `dialogue-codex`, `shakedown-b1`, or `shakedown-dialogue`.
- [ ] §8.4 names the bootstrap-test boundary invariant: `/dialogue`
      skill's `allowed-tools` excludes `codex.dialogue.*` MCP tools, so
      `test_bootstrap.py::test_no_user_invocable_dialogue_skill_exists`
      passes unchanged.
- [ ] §7.2 deferral triggers name concrete consumers, not vague
      "someday" conditions.
- [ ] v1 release note commits to documenting the T4-CT-05 secrets
      inheritance (§5.3) and the "shakedown scope" operator-message
      wording (§9.6).

## 12. Next Step (after plan approval)

Implementation order:

1. Author the production-local turn-semantics reference doc by extracting
   per-turn contract content from the current `dialogue-codex` skill.
2. Author `dialogue-orchestrator` agent body citing the reference doc,
   with inline initial scouting phase and production synthesis emission.
3. Author `/dialogue` user skill: invocation parsing, parent-owned
   active-run + seed write, shared-namespace single-run check,
   orchestrator dispatch, synthesis surfacing.
4. Extend `hooks.json` `SubagentStart` and `SubagentStop` matchers to
   match `dialogue-orchestrator`. Run existing lifecycle tests to
   confirm they still pass.
5. First end-to-end verification per §8.2 on a representative objective.
6. 14-item rubric inspection against the resulting verification
   transcript.
7. Confirm 566-test shakedown suite still passes unchanged.

## 13. References

**Supersession ticket:**
- `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`

**Accepted prior authority (contracts adopted as-is):**
- T1: `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md`
- T2: `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md`
- T3: `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md`
- T4: `docs/plans/t04-t4-scouting-position-and-evidence-provenance/` (10-file modular spec)
- T5: `docs/plans/2026-04-02-t04-t5-mode-strategy.md`
- T6: closed (composition review at `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md`)
- T7: `docs/plans/2026-04-07-t7-executable-slice-definition.md`
- T8: `docs/plans/2026-04-07-t8-minimum-runnable-shakedown-packet.md`

**Risk analysis:**
- `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md`

**Closed ticket (turn semantics):**
- `docs/tickets/2026-04-10-dialogue-codex-turn-semantics-clarification.md`

**Semantic sources (cross-model — not ported, consulted only):**
- `packages/plugins/cross-model/skills/dialogue/SKILL.md`
- `packages/plugins/cross-model/agents/codex-dialogue.md`
- `packages/plugins/cross-model/agents/context-gatherer-code.md`
- `packages/plugins/cross-model/agents/context-gatherer-falsifier.md`

**Runtime and containment surface (existing, relied on unchanged):**
- `packages/plugins/codex-collaboration/server/dialogue.py`
- `packages/plugins/codex-collaboration/server/mcp_server.py`
- `packages/plugins/codex-collaboration/server/containment.py`
- `packages/plugins/codex-collaboration/scripts/containment_lifecycle.py`
- `packages/plugins/codex-collaboration/scripts/containment_guard.py`
- `packages/plugins/codex-collaboration/hooks/hooks.json` (matchers extended in v1)

**Shakedown surface (must remain untouched in v1):**
- `packages/plugins/codex-collaboration/skills/shakedown-b1/SKILL.md`
- `packages/plugins/codex-collaboration/skills/dialogue-codex/SKILL.md`
- `packages/plugins/codex-collaboration/agents/shakedown-dialogue.md`

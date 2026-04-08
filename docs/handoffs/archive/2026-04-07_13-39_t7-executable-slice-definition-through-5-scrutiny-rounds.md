---
date: 2026-04-07
time: "13:39"
created_at: "2026-04-07T17:39:52Z"
session_id: 6b13fcd8-79b8-409c-b4fb-1c74c8c0a2da
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-07_12-13_branch-triage-and-repo-cleanup-to-exact-mirror.md
project: claude-code-tool-dev
branch: feature/t7-slice-definition
commit: 2390725f
title: T7 executable slice definition through 5 scrutiny rounds
type: handoff
files:
  - docs/plans/2026-04-07-t7-executable-slice-definition.md
  - docs/plans/2026-04-01-t04-benchmark-first-design-plan.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - docs/superpowers/specs/codex-collaboration/delivery.md
---

# Handoff: T7 executable slice definition through 5 scrutiny rounds

## Goal

Define the minimum runnable packet for the T7 pre-benchmark integration
shakedown — the "agreed smallest buildable slice that can execute one
dialogue and expose the fields the dry-run must inspect"
([plan.md:43](../plans/2026-04-01-t04-benchmark-first-design-plan.md#L43)).

**Trigger:** The prior session completed the git-hygiene arc (PRs #96,
#97). All T6 prerequisites were met, `main` was exact mirror of
`origin/main` at `7011e73b`, and T7 was the next item in the plan's
critical path (`T2 -> T3 -> T6 -> T7 -> T8`).

**Stakes:** T7 defines what T8 implements. A weak T7 definition means T8
either builds too much (full T4 for a shakedown) or too little (misses
load-bearing surfaces and the shakedown is uninformative). The definition
must be precise enough for T8 to implement without independently
re-deriving the T4-to-B1 boundary.

**Success criteria:**
- Agreed smallest buildable slice defined
- Component list with clear ownership (T7 defines, T8 implements)
- Interface contracts between infrastructure reuse and new behavioral layer
- Build sequence derivable from the definition
- Acceptance criteria with failure routing

**Connection to project arc:** T7 is Phase 4 of the T-04 benchmark-first
design plan. T6 (composition check) closed on 2026-04-06. T7 feeds
directly into T8 (implement and run the dry-run). The benchmark itself
(dialogue supersession) determines whether codex-collaboration's dialogue
workflow can retire cross-model's context-injection subsystem.

## Session Narrative

### Phase 1: Handoff load and initial context gathering

Session opened with `/load`, archiving the prior git-hygiene handoff. The
user directed: "Continue with T7. Start by reading the relevant files."

Read the four referenced files from the prior handoff's next steps:
- `plan.md:42-43` — T7 done-when ("agreed smallest buildable slice")
- `benchmark-readiness.md:167-255` — T4-BR-07 eight-item prerequisite
  gate and T4-BR-08 non-scoring run classification
- `composition-review.md:192-196` — two items deferred to T7
  (`scope_envelope` wiring and B8 anchor-adequacy decision rule)

Also read the codex-collaboration delivery spec, benchmark contract
(8 tasks, 4 pass-rule metrics), and the codex-collaboration spec.yaml
for the full authority model. Checked the existing implementation:
20 server modules, 460 tests, R1/R2 milestones partially delivered.

### Phase 2: Initial framing (rejected by scrutiny)

Produced an initial T7 summary with a four-part question. Framed T7 as
a "design/analysis task, not an implementation task" that should "produce
a document." Proposed deriving inspection fields from benchmark metrics
and adjudication rules.

User copied the response and returned with a detailed scrutiny containing
6 findings:

1. **Critical:** T7 is not document-only — plan says "post-minimal-
   implementation gate" and leaves room for implementation
   ([plan.md:10](../plans/2026-04-01-t04-benchmark-first-design-plan.md#L10),
   [:76](../plans/2026-04-01-t04-benchmark-first-design-plan.md#L76))
2. **Critical:** Scope collapsed to "8 prerequisites + 2 deferred items"
   — missed transcript fidelity, provenance-index consumers, synthesis-
   format updates, narrative-claim inventory, and 10 BR-09 amendments
3. **High:** Inspection fields anchored to benchmark metrics, not
   loop-integration invariants (risk analysis says inspect
   `effective_delta`, ledger summary, `converged`, epilogue per-turn)
4. **High:** Too casual about deferring BR-07 prerequisites under BR-08
5. **High:** Understated `scope_envelope` comparability gap
6. **High:** "What already exists" overweighted runtime, underweighted
   harness/artifact gap

All findings were accepted. The first scrutiny established: T7 must be
a "minimum runnable packet" not a "document," inspection targets loop-
integration invariants not benchmark metrics, and the boundary must
separate what exists from what each run class needs.

### Phase 3: Corrected framing and two contract choices

Produced a corrected framing with:
- Four-column boundary table (already implemented / shakedown / scored
  runs / external)
- Two inspection layers (loop-integration invariants first, benchmark
  artifacts second)
- B8 excluded from first dry-run
- T5 `agent_local` deferred

User returned two corrections:
1. T5 dependency still misframed — if the run is BR-08(a) benchmark
   execution, T5 `agent_local` is required
2. Artifact set too small if run stays inside benchmark execution

User presented a binary choice: either keep BR-08(a) and require T5 +
full artifacts, or move outside benchmark execution and use lighter
artifacts. User also answered: T7 should define only, T8 implements.

### Phase 4: Two decisions and user acceptance

Made two decisions:
1. **Pre-benchmark integration shakedown** (not BR-08(a)) — governed by
   risk analysis Risk I, not benchmark-readiness contract. The risk
   analysis says "before the benchmark" (line 231).
2. **T5 migration deferred** — `agent_local` vs `server_assisted` doesn't
   affect loop mechanics. T5 is for scored runs.

User accepted both decisions and noted: "These two decisions are coupled"
— moving outside benchmark execution is what makes T5 deferral defensible.

User then produced the first complete T7 slice definition and invoked
`/scrutinize` on it.

### Phase 5: Scrutiny round 2 (Major revision → infrastructure/behavior gap)

Scrutiny found 2 Critical failures:

1. The scouting loop does not exist in the codex-collaboration
   implementation. Zero matches for `effective_delta`, `ledger_summary`,
   `compute_action`, `scope_envelope`, `allowed_roots` in `server/`.
   Only `codex-status` and `consult-codex` skills exist — no
   `dialogue-codex` skill.
2. Minimum packet understated by 3 major components (dialogue skill,
   loop mechanics, convergence detection)

Root cause: conflation of dialogue infrastructure (R1/R2, exists) with
dialogue behavior (T4 scouting contract, doesn't exist).

User confirmed the gap by independently verifying zero matches in the
codebase. Produced a revised definition with explicit two-layer split.

### Phase 6: Scrutiny round 3 (Minor revision)

User's revised definition correctly separated infrastructure from
behavior but the behavioral layer was thinly specified:
- Dialogue skill was one sentence
- T4-to-B1 subset unspecified
- Containment mechanism ambiguous
- Loop state architecture unspecified

User tightened the definition with:
- B1-load-bearing behavioral subset with T4 line-level citations
- Containment as harness-side (citing containment.md:35, :78)
- Dialogue skill as 5 concrete behaviors
- Per-turn inspection granularity
- Explicit proof boundary ("does not prove benchmark readiness")

### Phase 7: Scrutiny round 4 (Defensible)

Scrutiny found the tightened definition defensible with 2 residual items:
1. Containment mechanism for host tools unresolved (hooks vs wrappers)
2. Loop state persistence implicit

User resolved both:
- **PreToolUse hooks** on native Read/Grep/Glob — trust model names
  PreToolUse as authoritative enforcement point
  ([foundations.md:124](../superpowers/specs/codex-collaboration/foundations.md#L124)),
  existing hook infrastructure in `hooks.json` and `codex_guard.py`,
  wrapper tools rejected because they'd distort benchmark tool surface
- **Claude-side working state** in dialogue transcript — T4's evidence
  blocks re-emitted per-turn ([state-model.md:503](../plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md#L503))

### Phase 8: Document compilation and scrutiny round 5

Compiled the full T7 definition artifact to
`docs/plans/2026-04-07-t7-executable-slice-definition.md` on branch
`feature/t7-slice-definition`. 341 lines.

User scrutinized the artifact. Found 1 Critical + 2 High:
1. **Critical:** Verification-state vocabulary wrong (`verified / false`
   instead of T4's normative `unverified | supported | contradicted |
   conflicted | ambiguous | not_scoutable`) and wrong citation (T4-SM-05
   instead of T4-SM-06)
2. **High:** Hook state transport undefined — PreToolUse input doesn't
   include `allowed_roots`, no bridge from scope wiring to hook
3. **High:** Transcript inspection assumes visible per-turn state that
   the skill contract didn't require emitting

Applied all 5 fixes: corrected verification states, added session-scoped
scope file mechanism, added per-turn emission as behavior 5 (now 6
behaviors), added `not_scoutable` threshold for shakedown validity.

### Phase 9: Scrutiny round 6 and final fixes

User scrutinized the revised document. Found 1 Critical + 2 High:
1. **Critical:** PreToolUse alone cannot do post-execution filtering or
   guarantee post-containment transcript capture. Claude Code docs
   confirm PostToolUse cannot modify native tool output
   (`updatedMCPToolOutput` is MCP-only).
2. **High:** Scope file at `${CLAUDE_PLUGIN_DATA}/shakedown/scope.json`
   is plugin-global, not session-scoped. Stale file from crashed
   shakedown would constrain future sessions.
3. **High:** Outcome model contradicts itself — binary pass/fail section
   plus later "inconclusive" override.

Applied all 5 fixes:
- Narrowed containment to pre-execution only (PreToolUse `updatedInput`
  for Grep/Glob path rewrite, `permissionDecision: "deny"` for Read).
  Post-execution filtering explicitly deferred to scored-run work.
- Session-bound scope file: `scope-<session_id>.json` with hook-side
  `session_id` validation
- Stale scope recovery: session binding prevents accidental activation,
  24-hour cleanup at startup
- Outcome model rewritten as `pass | fail | inconclusive` with validity
  check (inconclusive) before correctness check (pass/fail)
- Minimum per-turn emission schema: evidence block (7 fields) and
  verification-state summary (4 fields)

Final document is 405 lines. User will review the revised document and
share their review in the next session.

## Decisions

### Decision 1: Pre-benchmark integration shakedown, not BR-08(a)

**Choice:** The first dry-run dialogue is outside benchmark execution.
Not BR-08(a). Not scored. Not evidentiary for benchmark policy.

**Driver:** The risk analysis says "before the benchmark, run one dry-run
dialogue" ([risk-analysis.md:231](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md#L231)).
The purpose is loop-integration validation (Risk I mitigation), not
benchmark scoring.

**Alternatives considered:**
- **BR-08(a) exploratory shakedown** — classifying within benchmark
  execution. Rejected because it inherits T5 `agent_local` requirement
  (silent downgrade to `server_assisted` prohibited during benchmark
  execution,
  [benchmark-readiness.md:22](../plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md#L22))
  and full artifact set (`manifest.json`, `runs.json`,
  `adjudication.json`, `summary.md`,
  [benchmark.md:184](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md#L184)).
  Overhead doesn't serve the integration-validation purpose.

**Trade-offs accepted:** The shakedown cannot inform benchmark policy,
threshold setting, or calibration. Its results are strictly non-evidentiary.
This is acceptable because the purpose is loop-integration validation,
not benchmark scoring.

**Confidence:** High (E2) — verified the risk analysis says "before the
benchmark" and the plan separates T7 (define) from T8 (implement).
Both decisions are coupled: moving outside benchmark execution makes T5
deferral defensible.

**Reversibility:** High — the shakedown classification is metadata, not
implementation. The same code can be reclassified as BR-08(a) later if
T5 and artifacts are added.

**What would change this decision:** If the first dry-run's results need
to inform benchmark policy (threshold setting, calibration). Currently
they do not — the shakedown validates loop mechanics only.

### Decision 2: T5 `agent_local` deferred to scored runs

**Choice:** T5 mode migration is an external prerequisite for scored runs,
not part of the minimum runnable packet.

**Driver:** The shakedown validates loop mechanics (`effective_delta`,
ledger summary, convergence, epilogue). `agent_local` vs `server_assisted`
is a metadata surface that doesn't affect loop behavior.

**Alternatives considered:**
- **Include T5 in minimum packet** — would block the shakedown on 5 T5
  migration surfaces (enum, docs, parser, skill, tests). Rejected because
  mode doesn't affect loop-integration invariants.

**Trade-offs accepted:** The shakedown runs without `agent_local`. For
scored runs, T5 must land first (silent downgrade prohibited during
benchmark execution).

**Confidence:** High (E2) — coupled with Decision 1. Pre-benchmark
classification removes the benchmark-execution rules that would require
`agent_local`.

**Reversibility:** High — T5 surfaces are additive. Adding them to the
packet doesn't require changing existing components.

**What would change this decision:** If mode affects loop behavior (it
doesn't — mode describes orchestration ownership, not evidence mechanics,
[T5:28](../plans/2026-04-02-t04-t5-mode-strategy.md#L28)).

### Decision 3: T7 defines, T8 implements

**Choice:** T7 produces the slice definition. T8 implements it and runs
the shakedown.

**Driver:** User stated: "T7 should define only, not define-plus-
implement, at least from the current state. The plan separates T7 and T8
on purpose." Two unresolved contract choices (run classification, T5
dependency) needed resolution before implementation could proceed.

**Alternatives considered:**
- **T7 defines and implements** — plan.md:76 allows "T7 plus the
  minimal executable slice work if the slice is small enough." Rejected
  because the contract choices needed resolution first.

**Trade-offs accepted:** Adds one session boundary between definition
and implementation. Worth it because the definition went through 5
scrutiny rounds — implementing on unstable semantics would have hardened
mistakes into code.

**Confidence:** High (E2) — the 5 scrutiny rounds validated this: each
round found definitional errors that would have become implementation
bugs.

**Reversibility:** N/A — T7 is complete. T8 starts from the definition.

**What would change this decision:** Nothing — T7 is defined. The
question is moot.

### Decision 4: PreToolUse hooks for containment (not wrapper MCP tools)

**Choice:** Containment enforced via PreToolUse hooks on native
`Read` / `Grep` / `Glob` tools.

**Driver:** T4 requires confinement as a harness function
([containment.md:37](../plans/t04-t4-scouting-position-and-evidence-provenance/containment.md#L37)).
The codex-collaboration trust model names PreToolUse as the authoritative
enforcement point
([foundations.md:124](../superpowers/specs/codex-collaboration/foundations.md#L124)).
The plugin already has hook infrastructure (`hooks.json`, `codex_guard.py`).

**Alternatives considered:**
- **Wrapper MCP tools** (`scope.read`, `scope.grep`, `scope.glob`) —
  would keep containment in the server. Rejected because it distorts the
  candidate tool surface away from the benchmark's intended
  `Glob` / `Grep` / `Read` path
  ([benchmark.md:93-94](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md#L93)).
- **Prompt-only containment** — skill tells Claude to stay within roots.
  Rejected because T4 is explicit that confinement is a harness function,
  not a prompt instruction.

**Trade-offs accepted:** PreToolUse can only do pre-execution confinement.
Post-execution canonical-path filtering (T4-CT-01) requires a mechanism
Claude Code's PostToolUse cannot provide for native tools
(`updatedMCPToolOutput` is MCP-only). Post-execution filtering deferred
to scored-run work. Manual inspection covers this for the shakedown.

**Confidence:** High (E2) — verified against Claude Code hook documentation
that PreToolUse supports `updatedInput` (for Grep/Glob path rewrite) and
`permissionDecision: "deny"` (for Read denial). Verified PostToolUse
cannot modify native tool output.

**Reversibility:** Medium — hook infrastructure is separate from the
dialogue skill. Changing containment mechanism doesn't require skill
changes, but transcript format might differ.

**What would change this decision:** If PostToolUse gains native tool
output modification capability. Currently it does not (2026-04-07).

### Decision 5: Pre-execution containment only for the shakedown

**Choice:** Post-execution canonical-path filtering (T4-CT-01) deferred
to scored-run work. Shakedown uses pre-execution confinement only.

**Driver:** Claude Code's PostToolUse hook cannot modify native tool
output — `updatedMCPToolOutput` applies to MCP tools only. Pre-execution
confinement via `updatedInput` constrains Grep/Glob `path` parameters,
and `permissionDecision: "deny"` blocks out-of-scope Read calls. If input
is correctly constrained, output is inherently within scope.

**Alternatives considered:**
- **Full T4 containment (pre + post)** — requires a mechanism Claude Code
  doesn't provide for native tools. Building a custom post-execution
  filter layer would add significant implementation complexity for edge
  cases (symlinks, unexpected Grep matches) that are detectable by manual
  inspection.

**Trade-offs accepted:** Edge cases (symlinks resolving outside scope,
Grep matching content in included-but-unexpected files) are not
automatically filtered. Manual per-turn inspection (checklist item 12)
catches these. Not scalable to 8-task corpus runs — post-execution
filtering is required for scored runs.

**Confidence:** High (E2) — verified PostToolUse limitations in official
Claude Code docs. Pre-execution + manual inspection is sufficient for
a single-task human-inspected shakedown.

**Reversibility:** High — post-execution filtering is additive. Building
it later doesn't change the pre-execution layer.

**What would change this decision:** Scored-run requirements (which need
automated post-execution filtering).

### Decision 6: Session-bound scope file for hook state transport

**Choice:** PreToolUse hooks read containment state from a session-bound
file at `${CLAUDE_PLUGIN_DATA}/shakedown/scope-<session_id>.json`.

**Driver:** Claude Code's hook input includes `session_id`, `tool_name`,
`tool_input` but no mechanism for passing arbitrary dialogue-specific
state. A side-channel file is required.

**Alternatives considered:**
- **Plugin-global scope file** (single `scope.json`) — simpler but not
  session-scoped. A crashed shakedown would leave containment active for
  future sessions. Rejected after scrutiny found this was "not actually
  session-scoped."
- **Environment variable** — would require setting at session start.
  Doesn't survive across hook invocations reliably.

**Trade-offs accepted:** File I/O on every PreToolUse invocation. Minimal
overhead — file is small JSON, reads are fast.

**Confidence:** High (E2) — follows the same `${CLAUDE_PLUGIN_DATA}`
pattern as lineage store. Session binding via `session_id` in filename
prevents cross-session contamination.

**Reversibility:** High — scope file mechanism is internal to the
containment hook. Changing it doesn't affect other components.

**What would change this decision:** If Claude Code adds a mechanism for
passing custom state to hooks (e.g., hook-scoped context or environment
injection).

### Decision 7: Three-valued outcome model (pass / fail / inconclusive)

**Choice:** Shakedown result is `pass | fail | inconclusive`, with
validity check (inconclusive) running before correctness check (pass/fail).

**Driver:** Scrutiny found that a binary pass/fail model contradicts
the later `not_scoutable` threshold — a run can satisfy all 12 checklist
items and still be uninformative if >50% of claims are `not_scoutable`.

**Alternatives considered:**
- **Binary pass/fail** — simpler but creates a contradiction: a run
  passes all checklist items but exercises mostly the classification
  path, not the scouting path. The shakedown "passes" without validating
  loop integration.

**Trade-offs accepted:** Three outcomes create more complex reporting.
Worth it because the inconclusive gate prevents false confidence — a
run that mostly classifies `not_scoutable` doesn't validate the loop.

**Confidence:** High (E2) — B1's evaluative architecture-review prompt
should produce mostly scoutable claims (code existence/absence). The
>50% threshold is conservative — unlikely to trigger for B1 but provides
a safety net.

**Reversibility:** High — outcome model is metadata, not implementation.

**What would change this decision:** If B1 consistently produces >50%
`not_scoutable` claims, the threshold needs adjustment or B1 needs
supplementation with another corpus task.

## Changes

### `docs/plans/2026-04-07-t7-executable-slice-definition.md` — T7 slice definition

**Purpose:** The T7 deliverable. Defines the minimum runnable packet for
one pre-benchmark integration shakedown on B1.

**State:** 405 lines, untracked on branch `feature/t7-slice-definition`.
Not yet committed. User will review the revised document in the next
session before committing.

**Structure:**
- Authorities (plan, risk analysis, T6 deferred items, T4 contract)
- Slice summary (pre-benchmark, B1, not scored)
- Two-layer architecture (infrastructure reuse + behavioral layer)
- B1-load-bearing behavioral subset (6 T4 surfaces with line citations)
- Deferred-from-shakedown table (11 items with reasons)
- Containment (PreToolUse, pre-execution only, session-bound scope file)
- Dialogue skill (6 behaviors)
- Minimum per-turn emission schema (evidence block + verification summary)
- Loop state architecture (Claude-side, transcript-observable)
- Inspection protocol (12-item checklist: 6 per-turn, 3 terminal, 3
  containment)
- Acceptance criteria (ready-to-run preconditions + 3-valued outcome)
- Shakedown artifacts (transcript, metadata, inspection notes)
- Ownership boundary (T7 defines, T8 implements)
- Proof boundary (what it proves, what it doesn't)
- T8 handoff (7 implementation items + expansion table)
- Boundary table (11 rows)

**Key design choices in the document:**
- Pre-execution containment only (PostToolUse can't modify native tool
  output)
- `updatedInput` for Grep/Glob path rewriting, `permissionDecision:
  "deny"` for Read blocking
- `scope-<session_id>.json` for hook state transport
- 6 dialogue skill behaviors (5th is per-turn emission)
- Evidence block schema (7 fields) + verification-state summary (4 fields)
- `pass | fail | inconclusive` with validity-before-correctness ordering
- Stale scope file recovery via session binding + 24-hour cleanup

## Codebase Knowledge

### Codex-collaboration implementation state (verified 2026-04-07)

| Component | Status | Location |
|-----------|--------|----------|
| `codex.dialogue.start/reply/read` | Implemented (R1/R2) | `server/dialogue.py` (904 lines) |
| Advisory runtime + context assembly | Implemented | `server/control_plane.py` (477 lines), `server/context_assembly.py` |
| Lineage store | Implemented | `server/lineage_store.py` |
| Operation journal | Implemented | `server/journal.py` |
| Models (ConsultResult, DialogueStartResult, etc.) | Implemented | `server/models.py` (269 lines) |
| `codex-status` skill | Implemented | `skills/codex-status/` |
| `consult-codex` skill | Implemented | `skills/consult-codex/` |
| `dialogue-codex` skill | **Missing** | Not created (delivery spec plans it at `skills/dialogue-codex/`) |
| `delegate-codex` skill | **Missing** | Not created |
| Scouting loop (claim extraction, registration, ledger, convergence) | **Missing** | Zero matches for `effective_delta`, `ledger_summary`, `compute_action` |
| Containment (`scope_envelope`, `allowed_roots`) | **Missing** | Zero matches in `server/` |
| `claim_provenance_index`, `ClassificationTrace` | **Missing** | Zero matches |
| Total tests | 460 | `packages/plugins/codex-collaboration/tests/` |

### Hook architecture for containment (verified 2026-04-07)

Existing hook infrastructure:
- `hooks.json`: SessionStart + PreToolUse (matcher targets codex-
  collaboration MCP tools only)
- `codex_guard.py`: PreToolUse handler for credential scanning on MCP
  tool args. Reads JSON from stdin, uses `tool_name` and `tool_input`,
  exits 0 (allow) or 2 (block with stderr reason).

New containment hook will target native `Read`, `Grep`, `Glob` (different
matcher from existing MCP-tool hook).

### Claude Code hook capabilities (verified from docs 2026-04-07)

| Hook | Can modify input? | Can modify output? | Can block? |
|------|-------------------|-------------------|------------|
| PreToolUse | Yes (`updatedInput`) | N/A (pre-execution) | Yes (`permissionDecision: "deny"`) |
| PostToolUse | N/A (post-execution) | MCP tools only (`updatedMCPToolOutput`) | No (tool already ran) |

**Key limitation:** PostToolUse cannot modify native tool (Read/Grep/Glob)
output. Post-execution canonical-path filtering requires a mechanism
outside the hook system.

### T4 verification-state model (from state-model.md:311-359)

Normative states: `unverified | supported | contradicted | conflicted |
ambiguous | not_scoutable`

Status derivation rule (T4-SM-06, state-model.md:346): accumulates
evidence dispositions (`supports`, `contradicts`, `ambiguous`) into
an effective set, then derives status from set membership. `conflicted`
when both `supports` and `contradicts` present.

### T4 per-turn loop (from scouting-behavior.md:13-31)

7 steps: extract → validate/register → compute counters/`effective_delta`
→ control decision → scout (target selection, query execution, disposition,
evidence record, re-emit) → compose follow-up → send.

Scout query coverage: 2-5 tool calls per round, mandatory definition +
falsification queries (T4-SB-04).

### Benchmark contract key parameters

- 8 tasks (B1-B8), B1 selected for shakedown
- 4 pass-rule metrics: safety_violations, false_claim_count,
  supported_claim_rate, converged_within_budget
- Run conditions: same commit, same model, scouting limited to
  Glob/Grep/Read, transcript retention required
- Required artifacts: manifest.json, runs.json, adjudication.json,
  summary.md (reserved for benchmark execution, not shakedown)

## Context

### Mental model

**Framing:** This session was a convergence-through-scrutiny exercise.
The T7 definition started as a vague "document-only" framing and was
refined through 5 rounds of external scrutiny into a precise, implementable
artifact. Each round exposed a different class of error:

| Round | Error class | What was exposed |
|-------|-------------|------------------|
| 1 | Framing | T7 is not document-only; inspection targets wrong layer |
| 2 | Layer conflation | Infrastructure exists, behavior doesn't |
| 3 | Specification depth | Behavioral layer named but not defined |
| 4 | Residual gaps | Containment mechanism, state persistence |
| 5 | Implementation precision | Wrong vocab, no hook bridge, no emission requirement |
| 6 | Architecture mismatch | PostToolUse can't modify native output, scope file not session-bound, outcome model contradicts |

**Core insight:** The most valuable corrections came from checking the
definition against the actual Claude Code hook documentation (rounds 5-6)
and the T4 normative vocabulary (round 5). Implementation-precision errors
are invisible until you verify against the authoritative source.

**Secondary insight:** The user's scrutiny workflow is systematic — they
copy the response, analyze externally, and return structured findings with
line-level citations. The scrutiny findings were consistently grounded
in repo evidence, not abstract criticism.

### Project state

- **Branch:** `feature/t7-slice-definition` based on `main` at `7011e73b`
- **Untracked:** `docs/plans/2026-04-07-t7-executable-slice-definition.md`
  (405 lines, the T7 deliverable)
- **T7 status:** Definition complete pending user review of round-6 fixes
- **T8 status:** Not started — blocked on T7 acceptance
- **Repo:** Clean except for the untracked T7 definition file

### Environment

- Working directory: `/Users/jp/Projects/active/claude-code-tool-dev`
- Branch: `feature/t7-slice-definition`
- Commit: `2390725f` (handoff archive from this session's `/load`)
- Prior handoff: `docs/handoffs/archive/2026-04-07_12-13_branch-triage-and-repo-cleanup-to-exact-mirror.md`

## Learnings

### PostToolUse cannot modify native tool output — only MCP tools

**Mechanism:** Claude Code's PostToolUse hook fires after tool execution.
It includes `tool_response` in the input. For MCP tools,
`updatedMCPToolOutput` can replace the output. For native tools (Read,
Grep, Glob), there is no output modification capability. Exit code 2
shows stderr to Claude but "the tool already ran."

**Evidence:** Verified from official Claude Code hook documentation
(`hooks#posttooluse`). The `updatedMCPToolOutput` field description
explicitly says "For MCP tools only." The exit-code-2 behavior table
shows PostToolUse as "No" for "Can block?"

**Implication:** Post-execution canonical-path filtering for native tools
requires a mechanism outside the hook system. For the shakedown,
pre-execution confinement + manual inspection is sufficient. For scored
runs, a custom filtering layer is needed.

**Watch for:** Future Claude Code versions might add native tool output
modification to PostToolUse. Check before implementing scored-run
containment.

### PreToolUse `updatedInput` enables input rewriting before execution

**Mechanism:** PreToolUse hooks can return `updatedInput` to modify tool
parameters. For Grep/Glob, this means rewriting the `path` parameter to
constrain it to `scope_root` within `allowed_roots`. For Read, denial
via `permissionDecision: "deny"` is cleaner (Read has a single target
path, not a search scope).

**Evidence:** Verified from official Claude Code hook documentation
(`hooks#pretooluse-2`). The `updatedInput` field description: "Replaces
the entire input object, so include unchanged fields alongside modified
ones."

**Implication:** PreToolUse is sufficient for pre-execution containment.
The hook can enforce both path validation (Read) and path rewriting
(Grep/Glob) from a single hook script.

### Scrutiny-driven development converges faster than iterative implementation

**Mechanism:** The T7 definition went through 6 rounds of scrutiny before
any code was written. Each round found errors that would have been
implementation bugs if discovered later. The errors were progressively
more specific: framing → layer conflation → spec depth → residual gaps →
implementation precision → architecture mismatch.

**Evidence:** Round 5 found a wrong T4 citation (T4-SM-05 vs T4-SM-06)
and wrong verification-state vocabulary. If T8 had implemented the wrong
states, the shakedown would have been misaligned with the T4 contract.
Round 6 found that PostToolUse can't modify native tool output — if
containment had been implemented assuming full hook coverage, the
implementation would have been structurally incorrect.

**Implication:** For complex spec-derived implementations, definition
scrutiny before implementation catches errors that are invisible from
the implementation side. The cost is session time; the saving is
implementation rework.

**Watch for:** Diminishing returns after the definition reaches
"Defensible" verdict. Rounds 5 and 6 found important implementation-
precision errors, but further rounds would likely find only cosmetic
issues.

### Infrastructure/behavior conflation is a persistent risk in spec-derived systems

**Mechanism:** The codex-collaboration implementation has 20 server modules
and 460 tests for the R1/R2 dialogue infrastructure. This creates an
impression of completeness. But the T4 scouting contract — the behavioral
layer that the shakedown tests — has zero implementation. The gap is
invisible unless you search for specific T4 terms (`effective_delta`,
`claim_provenance_index`, etc.) and find zero matches.

**Evidence:** Initial framing said "Reuse as-is" for the entire dialogue
surface. Scrutiny round 2 (Critical) exposed that "reuse" applied to
infrastructure only. The scouting loop (layers 4-6 from the risk analysis)
is a different system that doesn't exist yet.

**Implication:** When a codebase has substantial infrastructure for a
feature area, always verify that the behavioral layer exists separately.
Module count and test count measure infrastructure coverage, not
behavioral coverage.

## Next Steps

### 1. User reviews revised T7 definition

**Dependencies:** None — document exists at
`docs/plans/2026-04-07-t7-executable-slice-definition.md`.

**What to do:** User reviews the 405-line document with round-6 fixes
applied. User will share their review in the next session.

**What to read:** The document itself. Key sections to verify:
- Containment section (pre-execution only, `updatedInput` mechanism,
  session-bound scope file)
- Dialogue skill (6 behaviors, especially behavior 5: per-turn emission)
- Minimum per-turn emission schema (evidence block + verification summary)
- Outcome model (pass/fail/inconclusive with validity-before-correctness)
- Deferred table (post-execution filtering row added)

**Acceptance criteria:** User accepts the definition or provides
additional corrections.

### 2. Commit and PR for T7 definition

**Dependencies:** User acceptance of the document (step 1).

**What to do:** Commit the T7 definition on `feature/t7-slice-definition`,
push, open PR.

**What to read:** The document for final commit message.

**Acceptance criteria:** PR merged to main.

### 3. T8 implementation

**Dependencies:** T7 definition accepted and merged (step 2).

**What to do:** Implement the 7-item minimum runnable packet defined in
the T8 Handoff section of the T7 document:
1. `dialogue-codex` skill with 6 behaviors
2. Loop mechanics producing inspectable state
3. PreToolUse containment hooks with session-bound scope file
4. B1 anchor-to-scope wiring
5. Transcript capture (post-containment)
6. Shakedown metadata record
7. Per-turn inspection notes

**What to read first:**
- The T7 definition (authority)
- T4 scouting-behavior.md (per-turn loop, target selection, query
  coverage)
- T4 state-model.md (verification states, claim registration, evidence
  recording)
- T4 containment.md (pre-execution confinement)
- Existing `codex_guard.py` (hook implementation pattern)

## In Progress

**Clean stopping point.** The T7 definition document is written and has
been through 6 scrutiny rounds. All fixes from the final scrutiny are
applied. The document is untracked on `feature/t7-slice-definition`.

User will review the revised document and share their review in the next
session. No implementation work is in flight.

## Open Questions

1. **Will the user's final review find additional issues?** The last
   scrutiny verdict was "Major revision" (round 6). Fixes were applied
   but not re-scrutinized. The user may find the fixes insufficient or
   may find new issues.

2. **Is the minimum per-turn emission schema (evidence block + verification
   summary) the right granularity?** The schema defines 11 fields across
   two structures. It may be too detailed or too sparse for the actual
   dialogue skill implementation.

3. **Will B1 generate enough scoutable claims?** B1 is an architecture
   review task. Most claims should be about code existence/absence (easily
   scoutable via Read). But some may be about behavioral correctness
   (harder to scout). The >50% `not_scoutable` threshold is conservative
   but untested.

## Risks

1. **The T7 definition is 405 lines of spec-derived design that has
   never been validated by implementation.** 6 rounds of scrutiny
   improved the definition significantly, but some errors are only
   discoverable during T8 implementation (e.g., whether the PreToolUse
   `updatedInput` mechanism works reliably for path rewriting in
   practice, whether the per-turn emission schema is producible by
   Claude's dialogue behavior).

2. **The behavioral layer (scouting loop) is the most complex component
   and the one most likely to need iteration.** The dialogue skill must
   translate T4's state model into Claude-executable prompt instructions.
   Prompt engineering for structured multi-turn behavior is inherently
   iterative — the definition specifies WHAT the skill must do but not
   HOW to prompt for it.

3. **Containment via PreToolUse path rewriting depends on correct
   `scope_root` derivation.** For B1 with 3 allowed_roots, the
   shallowest-root rule should be straightforward. But edge cases
   (overlapping roots, relative paths) may surface during implementation.

## References

| What | Where |
|------|-------|
| T7 definition (the deliverable) | `docs/plans/2026-04-07-t7-executable-slice-definition.md` |
| T-04 benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` |
| T4 scouting behavior | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md` |
| T4 state model | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md` |
| T4 containment | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md` |
| T4 benchmark readiness | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md` |
| T6 composition review | `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md` |
| Convergence-loop risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Codex-collaboration delivery | `docs/superpowers/specs/codex-collaboration/delivery.md` |
| T5 mode strategy | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` |
| Codex-collaboration foundations | `docs/superpowers/specs/codex-collaboration/foundations.md` |
| T7 corpus constraint ticket | `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` |
| Prior handoff | `docs/handoffs/archive/2026-04-07_12-13_branch-triage-and-repo-cleanup-to-exact-mirror.md` |
| Claude Code hook docs | `hooks#posttooluse`, `hooks#pretooluse-2` |

## Gotchas

1. **PostToolUse cannot modify native tool output.** Only
   `updatedMCPToolOutput` works, and only for MCP tools. The containment
   design must use PreToolUse (pre-execution) for native tools. Checked
   against official docs 2026-04-07.

2. **T4 verification states are NOT `verified / false / not_scoutable`.**
   The normative vocabulary is `unverified | supported | contradicted |
   conflicted | ambiguous | not_scoutable` (T4-SM-06, state-model.md:311).
   The simplified vocabulary was wrong and persisted through 4 scrutiny
   rounds before being caught.

3. **The codex-collaboration implementation has 460 tests but zero
   scouting-loop behavior.** All tests cover infrastructure (dialogue
   transport, lineage, journal, context assembly). The behavioral layer
   (claim extraction, ledger, convergence) doesn't exist. Module count
   and test count measure infrastructure, not behavior.

4. **Scope files must be session-bound, not plugin-global.** A plugin-
   global file at `scope.json` would bleed containment across sessions.
   Use `scope-<session_id>.json` with hook-side `session_id` validation.

5. **The outcome model needs three values, not two.** A binary pass/fail
   model allows a shakedown to "pass" while exercising mostly the
   `not_scoutable` classification path. The inconclusive gate prevents
   this false confidence.

## Conversation Highlights

### User-driven scrutiny workflow

The user performed all 6 scrutiny rounds externally — copying my output,
analyzing it, and returning structured findings with line-level citations.
Findings consistently cited repo files (e.g.,
`benchmark-readiness.md:18`, `containment.md:35`) and Claude Code
documentation. This is a systematic quality process, not ad-hoc feedback.

### Progressive error discovery

Each scrutiny round found a different class of error:
- Round 1: "You are solving the wrong problem" (framing)
- Round 2: "The scouting loop does not exist" (layer conflation)
- Round 3: Underspecified behavioral layer
- Round 4: Residual implementation gaps
- Round 5: Wrong T4 vocabulary, no hook bridge, no emission requirement
- Round 6: PostToolUse architecture mismatch, scope file not session-bound

The progression from framing errors to implementation-precision errors
is characteristic — each round peeled back a layer.

### Two binary choices that coupled

User presented the BR-08(a) vs. pre-benchmark choice as a binary with
consequences: "Either keep BR-08(a) and require T5 + artifacts, or move
outside benchmark execution." Then noted the coupling: "Moving outside
benchmark execution is what makes T5 deferral defensible." This structured
decision-making eliminated two contract ambiguities simultaneously.

### Scrutiny verdicts as convergence signal

| Round | Verdict | Key finding |
|-------|---------|-------------|
| 1 | Reject (user-driven) | Wrong problem |
| 2 | Major revision | Layer conflation (Critical) |
| 3 | Minor revision | Underspecified behavior |
| 4 | Defensible | 2 residual items |
| 5 | Minor revision | Contract errors + omissions |
| 6 | Major revision | Architecture mismatch |

The non-monotonic convergence (Defensible in round 4, then Major revision
in rounds 5-6) came from checking against authoritative sources (T4 spec,
Claude Code docs) after the structural decisions were settled.

## User Preferences

**Scrutiny-first quality process.** User applies structured adversarial
review (with line-level citations) to every significant artifact before
accepting it. This is not optional feedback — it's a required quality gate.
The user invoked `/scrutinize` on their own proposals in prior sessions.

**Binary decision framing.** When contract choices create coupling, user
presents them as binary with consequences: "Either A (with these
implications) or B (with those implications)." This eliminates ambiguity
efficiently.

**Verify-and-execute workflow (continued).** User performs independent
analysis, presents evidence, expects verification and execution. This
session: user scrutinized externally, returned findings, expected fixes.

**Evidence-grounded corrections.** Every correction included repo-level
citations. User said "the official Claude Code docs say PreToolUse runs
before a tool executes, while PostToolUse runs after" — grounding the
correction in authoritative documentation.

**Clean ownership boundaries.** User's answer on T7/T8: "T7 should define
only, not define-plus-implement. The plan separates T7 and T8 on purpose."
Prefers clean phase boundaries even when combining would be faster.

**Progressive tightening, not wholesale replacement.** Each scrutiny round
corrected specific findings rather than rejecting the entire approach.
The structure survived from round 2 onward — changes were within the
structure, not to it.

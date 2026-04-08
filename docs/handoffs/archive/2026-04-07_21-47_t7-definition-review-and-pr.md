---
date: 2026-04-07
time: "21:47"
created_at: "2026-04-08T01:47:22Z"
session_id: fc8f0a57-667b-4687-9d4c-88afd853e126
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-07_13-39_t7-executable-slice-definition-through-5-scrutiny-rounds.md
project: claude-code-tool-dev
branch: feature/t7-slice-definition
commit: 89e0eb4a
title: T7 definition review and PR
type: handoff
files:
  - docs/plans/2026-04-07-t7-executable-slice-definition.md
---

# Handoff: T7 definition review and PR

## Goal

Review and finalize the T7 executable slice definition, then commit and
open a PR. The T7 definition was produced in the prior session through 6
scrutiny rounds and left as an untracked 405-line document on branch
`feature/t7-slice-definition`. This session's job was the user's final
review, applying any corrections, and landing the PR.

**Trigger:** Prior session completed the T7 definition artifact through
6 scrutiny rounds but did not commit. The handoff's Next Steps #1 was
"User reviews revised T7 definition" and #2 was "Commit and PR."

**Stakes:** T7 defines what T8 implements. The definition must be
precise enough for T8 to implement without independently re-deriving the
T4-to-B1 boundary. Errors in the definition become implementation bugs.

**Success criteria:**
- All user review findings resolved
- Document internally consistent
- Committed on `feature/t7-slice-definition` and PR opened
- T8 can start from the definition without re-reading T4 contracts

**Connection to project arc:** T7 is Phase 4 of the T-04 benchmark-first
design plan. T6 (composition check) closed 2026-04-06. T7 feeds directly
into T8 (implement and run the dry-run). The benchmark itself (dialogue
supersession) determines whether codex-collaboration's dialogue workflow
can retire cross-model's context-injection subsystem.

## Session Narrative

### Phase 1: Handoff load and initial review

Session started with `/load`, archiving the prior handoff. The user had
already reviewed the document externally and immediately provided their
first review with 2 findings plus 2 assumptions.

### Phase 2: Review round 1 — Same-session leakage and resume reactivation

User's findings (2 findings, 2 assumptions):

1. **[P1] Same-session non-shakedown calls constrained.** The scope file
   keyed only on `session_id` would constrain ALL `Read`/`Grep`/`Glob`
   calls in the session, not just shakedown ones. The hook input provides
   `session_id` (always) plus `agent_id`/`agent_type` (subagent calls
   only, per `hooks#common-input-fields`). Fix: bind activation to
   `agent_id` match, not just `session_id`.

2. **[P2] Stale scope recovery incomplete for resume flows.** Claude
   Code's `--resume` reuses the original `session_id`
   (`hooks#json-output-2` documents the `resume` source). A stale scope
   file could reactivate containment on resume before 24-hour cleanup.
   Fix: `agent_id` match prevents reactivation when the shakedown
   subagent isn't running.

3. **Assumption:** Make subagent-based activation explicit — bind to
   `agent_id` as well as `session_id`.

4. **Assumption:** Use `trash` not `rm` in manual cleanup example (repo
   safety rules).

Applied fixes: rewrote Hook State Transport to add `agent_id` and
`run_id` to scope file, rewrote Hook Scoping section around `agent_id`
binding, added explicit `--resume` handling to Stale Scope File Recovery,
added subagent structural requirement to Dialogue Skill section, updated
T8 Handoff items. Changed `rm` to `trash`. Document grew from 405 to
413 lines.

### Phase 3: Review round 2 — agent_id capture path undefined

User's finding (1 finding):

1. **[P1] `agent_id` capture path undefined.** The plan assumed the
   shakedown harness could write the scope file with `agent_id` before
   the dialogue starts, but Claude Code docs expose `agent_id` in hook
   input and `SubagentStart` — not as a parent-harness value. The parent
   doesn't know `agent_id` until spawn time. User suggested: "If your
   intended mechanism is SubagentStart creating the scope file, say that
   directly."

Searched Claude Code docs to verify. Found:
- `SubagentStart` fires "when a subagent is spawned" and receives
  `agent_id` and `agent_type` in input
- `SubagentStart` supports matchers on `agent_type` (custom agent names)
- `SubagentStart` cannot block creation but can inject context and run
  side-effect commands
- `SubagentStop` fires "when a subagent finishes" with same fields

Applied fix: introduced seed-file → scope-file two-phase pattern.
Harness writes seed file (no `agent_id`), `SubagentStart` hook promotes
seed to scope file (with `agent_id` from hook input), `SubagentStop`
removes scope file. Added ordering guarantee explanation, hook
registration table with 3 hooks, updated stale-file recovery for seed
files, updated T8 Handoff and Acceptance Criteria. Document grew from
413 to 440 lines.

### Phase 4: Review round 3 — Ordering evidence and fail-closed polarity

User's findings (2 rounds compressed):

1. **[P2] Ordering guarantee stated as documented fact.** The docs show
   `SubagentStart` → agentic loop → `SubagentStop` in the lifecycle
   diagram, but do not explicitly guarantee `SubagentStart` completes
   before the first `PreToolUse`. The document was presenting an
   inference as a guarantee. Fix: relabel as inference, add T8 validation
   step.

2. **[P1] Fallback silently disables containment.** The timeout fallback
   said "pass through if scope file never appears" — fail-open for a
   containment mechanism. Fix: deny the call on timeout (fail-closed).

Applied fixes: relabeled ordering as "inference, not explicit doc
guarantee" with evidence citations, added T8 validation step (marker-file
test) as first implementation item, changed fallback to
`permissionDecision: "deny"` in both locations. Document grew from 440
to 444 lines.

### Phase 5: Acceptance and PR

User accepted the definition with "No findings." Confirmed the ordering
is now properly labeled as inference, the fail-closed fallback is correct,
and the `SubagentStart` → first `PreToolUse` validation is the right
first T8 step.

Committed at `89e0eb4a` on `feature/t7-slice-definition`, pushed to
origin, opened PR #98.

## Decisions

### Decision 1: Agent-scoped containment activation via `agent_id`

**Choice:** Containment hook activates only when both `session_id`
matches the scope file AND the calling `agent_id` matches the scope
file's `agent_id`. Main-thread calls (no `agent_id`) always pass through.

**Driver:** User's review finding P1: "The mechanism at line 158 only
keys on `session_id`. Same-session non-shakedown `Read`/`Grep`/`Glob`
calls would still be constrained while the file exists." Verified against
`hooks#common-input-fields`: `agent_id` is "present only when the hook
fires inside a subagent call."

**Alternatives considered:**
- **`session_id` only** (prior design) — rejected because it constrains
  all tool calls in the session, not just shakedown subagent calls.
  The operator's own `Read`/`Grep`/`Glob` during the same session would
  be denied or path-rewritten.
- **`agent_type` only** (without `agent_id`) — rejected because
  `agent_type` is the agent name (e.g., `"shakedown-dialogue"`), not a
  unique instance identifier. If two shakedown subagents ran
  concurrently, `agent_type` alone couldn't distinguish them.

**Trade-offs accepted:** `agent_id` is only available in subagent calls.
The shakedown dialogue must run inside a dedicated subagent — this is now
a structural requirement, not an optimization.

**Confidence:** High (E2) — verified against official Claude Code hook
docs (`hooks#common-input-fields`). The `agent_id` field description
explicitly says "Present only when the hook fires inside a subagent call.
Use this to distinguish subagent hook calls from main-thread calls."

**Reversibility:** Medium — changing from `agent_id` to another
discriminator would require updating the scope file format, the
`SubagentStart` hook, and the `PreToolUse` hook. But the interfaces are
clean — each hook reads one file.

**What would change this decision:** If Claude Code adds a finer-grained
discriminator than `agent_id` (e.g., a tool-call-scoped identifier), or
if `agent_id` proves unstable across the subagent's lifetime.

### Decision 2: Seed-file → scope-file promotion via SubagentStart

**Choice:** Two-phase scope bootstrapping. Harness writes a seed file
(contains `allowed_roots`, no `agent_id`). `SubagentStart` hook reads
seed, writes scope file (adds `agent_id`), removes seed. `SubagentStop`
removes scope file.

**Driver:** User's review finding P1 (round 2): "The documented surfaces
expose `agent_id` in hook input and `SubagentStart`, not as a
parent-harness value." Verified by searching Claude Code docs — `agent_id`
first appears in `SubagentStart` hook input, not in any parent-level API.

**Alternatives considered:**
- **Parent harness writes scope file with `agent_id`** (prior design) —
  rejected because the parent doesn't know `agent_id` before spawning
  the subagent. Claude Code generates it at spawn time.
- **Hardcoded `agent_id`** — rejected because `agent_id` is a runtime
  identifier, not a configurable value.
- **Skip `agent_id`, use `agent_type` matching only** — rejected because
  `agent_type` matching on the `SubagentStart` hook already narrows to
  the right agent type, but the PreToolUse hook needs a per-instance
  identifier to handle concurrent subagents.

**Trade-offs accepted:** Two-phase file handshake (seed → scope) is more
complex than a single write. Adds a transient seed file that must also
be covered by stale-file cleanup. Worth it because it solves the
`agent_id` acquisition problem without guessing or hardcoding.

**Confidence:** High (E2) — verified `SubagentStart` hook input includes
`agent_id` and `agent_type` (`hooks#notification` section documents the
full input schema). Verified `SubagentStart` fires before the subagent
executes any tool calls (lifecycle diagram at `hooks#hook-lifecycle`).

**Reversibility:** Medium — the seed/scope two-phase pattern is internal
to the containment subsystem. Changing it doesn't affect the dialogue
skill or the PreToolUse guard (which only reads the scope file).

**What would change this decision:** If Claude Code provides a way to
pass custom initialization data to a subagent at spawn time (eliminating
the need for the seed file side-channel).

### Decision 3: SubagentStart ordering labeled as inference, not guarantee

**Choice:** The document states the `SubagentStart` → first `PreToolUse`
ordering as an inference from the lifecycle diagram, not as an explicit
doc guarantee. T8 must validate the ordering as its first implementation
step.

**Driver:** User's review finding P2 (round 3): "The docs document that
`SubagentStart` fires when a subagent is spawned and can inject context
into the subagent, and that `PreToolUse` fires before a tool call. They
do not explicitly promise that the `SubagentStart` hook completes before
the subagent's first guarded tool call."

**Alternatives considered:**
- **State as guarantee** (prior text) — rejected because the docs
  support the ordering by implication (lifecycle diagram, `SubagentStart`
  can "inject context into the subagent"), but do not explicitly state
  the sequencing.
- **Abandon SubagentStart approach** — rejected because there is no
  better alternative for acquiring `agent_id` before the first tool call.
  The inference is reasonable; it just shouldn't be overclaimed.

**Trade-offs accepted:** The T8 validation step adds work before
implementation can proceed. But it converts an unverified assumption into
a verified fact (or triggers the fallback).

**Confidence:** Medium (E1) — the lifecycle diagram strongly implies the
ordering, and `SubagentStart`'s ability to inject context only makes
sense if it runs before the subagent acts. But "strongly implied" is not
"explicitly guaranteed."

**Reversibility:** High — if the ordering doesn't hold, the fallback
(poll + deny on timeout) is already specified.

**What would change this decision:** If Claude Code docs explicitly
document the `SubagentStart` → first tool call ordering. Or if T8's
validation test shows the ordering does not hold.

### Decision 4: Fail-closed fallback for ordering race

**Choice:** If the `PreToolUse` hook fires before the scope file exists
(ordering race), it polls briefly and then denies the call
(`permissionDecision: "deny"`), not passes through.

**Driver:** User's review finding P1 (round 4): "Passing through turns
the race into an unconstrained tool call, which defeats the whole point
of using `PreToolUse` for containment. This should fail closed."

**Alternatives considered:**
- **Pass through** (prior text) — rejected because it defeats
  containment exactly in the scenario where the ordering assumption
  failed. A containment mechanism that fails open on its first call is
  not a containment mechanism.
- **Abort the shakedown entirely** — viable but more disruptive than
  necessary. Denying one call lets the subagent retry naturally.

**Trade-offs accepted:** A false denial (scope file legitimately absent
because the subagent is not a shakedown agent) could block a normal
subagent's first tool call. Mitigated by the scope file path check:
the PreToolUse hook only enters the poll-and-deny path if a seed file
exists for the current `session_id` (indicating a shakedown is expected).
No seed file → immediate pass-through.

**Confidence:** High (E2) — fail-closed is the universal standard for
containment mechanisms. The only question was the specific implementation
(deny vs abort), and deny is less disruptive.

**Reversibility:** High — the fallback is one code path in the
PreToolUse hook. Changing from deny to abort or pass-through is a single
conditional change.

**What would change this decision:** If false denials prove disruptive
in practice (unlikely given the seed-file guard).

## Changes

### `docs/plans/2026-04-07-t7-executable-slice-definition.md` — T7 slice definition (revised)

**Purpose:** The T7 deliverable — defines the minimum runnable packet for
one pre-benchmark integration shakedown on B1.

**State:** 444 lines, committed on `feature/t7-slice-definition` at
`89e0eb4a`. PR #98 open targeting `main`.

**Revisions this session (3 rounds, building on 6 prior rounds):**

| Round | Finding class | What changed |
|-------|---------------|--------------|
| 7 (this session, round 1) | Same-session leakage + resume reactivation | `agent_id` binding in scope file, subagent structural requirement, `--resume` handling, `trash` for cleanup |
| 8 (this session, round 2) | `agent_id` capture path | Seed-file → scope-file two-phase pattern via `SubagentStart`/`SubagentStop`, hook registration table |
| 9a (this session, round 3) | Ordering evidence | Relabeled as inference, added T8 validation step |
| 9b (this session, round 3) | Fail-closed polarity | Deny on timeout, not pass-through |

**Key sections modified:**
- Hook State Transport — lifecycle contract with seed/scope two-phase,
  ordering guarantee relabeled as inference
- Hook Scoping and Session Isolation — rewritten around `agent_id`
  binding
- Stale Scope File Recovery — `--resume` handling, stale seed file
  handling
- Hook Registration — table with 3 hook registrations
  (`SubagentStart`, `SubagentStop`, `PreToolUse`)
- Dialogue Skill — subagent structural requirement
- Acceptance Criteria — lifecycle hooks and seed-file mechanism
- T8 Handoff — ordering validation as first step, agent-scoped items

**Document structure (16 top-level sections):**
Authorities, Slice Summary, Two-Layer Architecture, B1-Load-Bearing
Behavioral Subset, Containment, Dialogue Skill, Loop State Architecture,
Inspection Protocol, Acceptance Criteria, Shakedown Artifacts, Ownership
Boundary, What the Shakedown Proves, T8 Handoff, Boundary Table,
References.

## Codebase Knowledge

### Claude Code hook system (verified from official docs 2026-04-07)

**Common input fields** (`hooks#common-input-fields`):

| Field | Always present | Description |
|-------|---------------|-------------|
| `session_id` | Yes | Current session identifier |
| `transcript_path` | Yes | Path to conversation JSON |
| `cwd` | Yes | Current working directory |
| `permission_mode` | Most events | Current permission mode |
| `hook_event_name` | Yes | Name of the event that fired |
| `agent_id` | Subagent calls only | Unique identifier for the subagent |
| `agent_type` | Subagent calls or `--agent` | Agent name (e.g., "Explore", "security-reviewer") |

**Key property of `agent_id`:** "Present only when the hook fires inside
a subagent call. Use this to distinguish subagent hook calls from
main-thread calls." This is the discriminator that enables agent-scoped
containment.

**SubagentStart** (`hooks#notification` section):
- Fires "when a subagent is spawned via the Agent tool"
- Receives `agent_id` and `agent_type` in addition to common fields
- Supports matchers on `agent_type` (built-in agents like `"Bash"`,
  `"Explore"`, or custom agent names from `.claude/agents/`)
- Cannot block subagent creation
- Can inject `additionalContext` into the subagent
- Can run side-effect commands (scope file creation)

**SubagentStop** (`hooks#notification` section):
- Fires "when a subagent has finished responding"
- Receives `agent_id`, `agent_type`, `agent_transcript_path`,
  `last_assistant_message`
- Supports matchers on `agent_type` (same values as SubagentStart)
- Uses Stop decision control format (can block stopping)

**PreToolUse decision control** (`hooks#pretooluse-decision-control`):
- `permissionDecision: "allow"` — allow the tool call
- `permissionDecision: "deny"` with `permissionDecisionReason` — block
- `permissionDecision: "ask"` — escalate to user
- `updatedInput` — modify tool parameters before execution

**Lifecycle ordering** (from `hooks#hook-lifecycle` diagram):
SessionStart → agentic loop (PreToolUse → tool execution → PostToolUse,
SubagentStart/Stop, TaskCreated/Completed) → Stop/StopFailure →
SessionEnd. The diagram shows SubagentStart inside the agentic loop,
before subagent tool execution, but the docs do not explicitly state
that `SubagentStart` hooks complete before the subagent's first tool
call.

**Hooks in skills and agents** (`hooks#hook-handler-fields-2`):
Hooks can be defined in skill/agent frontmatter. "These hooks are scoped
to the component's lifecycle and only run when that component is active."
For subagents, `Stop` hooks are automatically converted to
`SubagentStop`. This is potentially relevant for containment — the
shakedown agent could define its own PreToolUse hook in its frontmatter
rather than relying on global hook registration. Not explored this
session.

### Codex-collaboration implementation state (carried from prior session)

| Component | Status | Location |
|-----------|--------|----------|
| `codex.dialogue.start/reply/read` | Exists (R1/R2) | `server/dialogue.py` (904 lines) |
| Advisory runtime + context assembly | Exists | `server/control_plane.py`, `server/context_assembly.py` |
| Lineage store | Exists | `server/lineage_store.py` |
| Operation journal | Exists | `server/journal.py` |
| Models | Exists | `server/models.py` (269 lines) |
| `codex-status` skill | Exists | `skills/codex-status/` |
| `consult-codex` skill | Exists | `skills/consult-codex/` |
| `dialogue-codex` skill | **Missing** | Not created |
| Scouting loop | **Missing** | Zero matches for T4 terms |
| Containment | **Missing** | Zero matches for `scope_envelope`, `allowed_roots` |
| Total tests | 460 | `packages/plugins/codex-collaboration/tests/` |

### Hook infrastructure (carried from prior session)

- `hooks.json`: SessionStart + PreToolUse (matcher targets MCP tools only)
- `codex_guard.py`: PreToolUse handler for credential scanning on MCP
  tool args
- Pattern: read JSON from stdin, use `tool_name` and `tool_input`, exit
  0 (allow) or 2 (block with stderr reason)

## Context

### Mental model

**Framing:** This session was a containment-bootstrapping problem. The
T7 definition needed a mechanism to activate containment hooks precisely
for the shakedown subagent's tool calls and no others. The challenge was
that the discriminating identifier (`agent_id`) isn't available until
spawn time, creating a bootstrapping dependency between the parent
harness (which knows WHAT to constrain) and the subagent (which IS the
constraint target).

**Core insight:** The seed-file → scope-file promotion pattern bridges
the bootstrapping gap. The harness writes intent (allowed_roots), the
`SubagentStart` hook enriches it with identity (agent_id). This is a
general pattern for hook-mediated setup where the target's identity isn't
known until spawn time.

**Secondary insight:** The scrutiny rounds this session progressed from
structural (same-session leakage) → bootstrapping (agent_id capture) →
evidentiary (ordering inference) → polarity (fail-closed). Each class is
invisible from the perspective of the previous class — you can't see the
bootstrapping problem until the structural one is solved, and the
evidence quality only matters once the mechanism is correct.

### Project state

- **Branch:** `feature/t7-slice-definition` at `89e0eb4a`
- **PR:** #98 targeting `main`
- **T7 status:** Definition accepted, committed, PR open
- **T8 status:** Not started — blocked on T7 merge
- **Next in critical path:** T8 (implement and run the dry-run)

### Error-class progression across all 9 rounds

| Round | Session | Error class | What was exposed |
|-------|---------|-------------|------------------|
| 1 | Prior | Framing | T7 is not document-only; inspection targets wrong layer |
| 2 | Prior | Layer conflation | Infrastructure exists, behavior doesn't |
| 3 | Prior | Specification depth | Behavioral layer named but not defined |
| 4 | Prior | Residual gaps | Containment mechanism, state persistence |
| 5 | Prior | Implementation precision | Wrong vocab, no hook bridge, no emission requirement |
| 6 | Prior | Architecture mismatch | PostToolUse can't modify native output, scope not session-bound |
| 7 | This | Same-session leakage | `session_id` too coarse, need `agent_id` binding |
| 8 | This | Bootstrapping | `agent_id` not available to parent harness before spawn |
| 9 | This | Evidence + polarity | Ordering inference overclaimed; fallback fails open |

## Learnings

### SubagentStart is the only documented surface for obtaining `agent_id` before a subagent acts

**Mechanism:** Claude Code generates `agent_id` at spawn time. The
parent harness (the code that calls the Agent tool) does not receive the
`agent_id` in any return value or callback. The first place `agent_id`
appears is in the `SubagentStart` hook input. This means any setup that
depends on `agent_id` must happen in a `SubagentStart` hook, not in the
parent code.

**Evidence:** Searched Claude Code docs for `agent_id`. Found in:
`hooks#common-input-fields` ("Present only when the hook fires inside a
subagent call"), `SubagentStart` input (includes `agent_id` and
`agent_type`), `SubagentStop` input (same). Not found in any parent-level
API, Agent tool return schema, or session-level surface.

**Implication:** Any future feature that needs to configure hooks per
subagent (not just per agent type) will need the same SubagentStart
bootstrapping pattern. The seed-file promotion approach is generalizable.

**Watch for:** Claude Code may add `agent_id` to the Agent tool's return
value or as a parent-level callback in future versions. Check before
building new SubagentStart bootstrapping.

### Hooks defined in agent frontmatter are lifecycle-scoped

**Mechanism:** Claude Code docs state hooks can be defined in skill and
agent frontmatter, and "these hooks are scoped to the component's
lifecycle and only run when that component is active." For subagents,
`Stop` hooks are automatically converted to `SubagentStop`.

**Evidence:** `hooks#hook-handler-fields-2` section. Example shows a
skill with PreToolUse hook in YAML frontmatter.

**Implication:** The shakedown agent could potentially define its own
PreToolUse containment hook in its agent frontmatter rather than
requiring global hook registration. This would scope containment to the
agent's lifetime automatically. Not explored this session — flagged as
a potential T8 simplification.

**Watch for:** Frontmatter-defined hooks may have different ordering
guarantees or capabilities than globally-registered hooks. Verify before
adopting.

### Containment mechanisms must fail closed — the first call is the most critical

**Mechanism:** If a containment hook's fallback for an edge case is
"pass through," the edge case becomes an escape hatch. For the
SubagentStart ordering race, the very first tool call is the one most
likely to hit the race (scope file not yet written), and it's also the
call that establishes the initial state. If the first call escapes
containment, the entire shakedown's containment story is compromised.

**Evidence:** User's review caught this: "Passing through turns the race
into an unconstrained tool call, which defeats the whole point of using
PreToolUse for containment."

**Implication:** When designing containment fallbacks, the question is
not "what's the most graceful degradation?" but "what preserves the
containment invariant?" Denial preserves containment (the call doesn't
happen); pass-through breaks it (the call escapes).

**Watch for:** Similar fail-open tendencies in any hook-based enforcement
mechanism. Default to denial/abort for security-relevant hooks, not
pass-through.

## Next Steps

### 1. Merge PR #98

**Dependencies:** None — PR is open, review is complete.

**What to do:** Merge `feature/t7-slice-definition` to `main`.

**Acceptance criteria:** PR merged, branch deleted.

### 2. T8 implementation

**Dependencies:** T7 merged (step 1).

**What to do:** Implement the 7-item minimum runnable packet defined in
the T8 Handoff section of the T7 document.

**First step (before other implementation):** Validate `SubagentStart` →
first `PreToolUse` ordering with a minimal marker-file test. This
converts the inferred ordering into a verified fact (or triggers the
fail-closed fallback design).

**Implementation items:**
1. `dialogue-codex` skill with 6 behaviors, running inside a dedicated
   subagent (custom agent type for hook matching)
2. Loop mechanics producing inspectable state
3. Containment hooks: `SubagentStart`/`SubagentStop` lifecycle hooks
   (scope file create/remove) + `PreToolUse` guard for `Read`/`Grep`/`Glob`
4. B1 anchor-to-scope wiring (seed file → scope file promotion)
5. Transcript capture (post-containment)
6. Shakedown metadata record
7. Per-turn inspection notes

**What to read first:**
- The T7 definition (authority):
  `docs/plans/2026-04-07-t7-executable-slice-definition.md`
- T4 scouting-behavior.md (per-turn loop, target selection, query
  coverage)
- T4 state-model.md (verification states, claim registration, evidence
  recording)
- T4 containment.md (pre-execution confinement)
- Existing `codex_guard.py` (hook implementation pattern)
- Claude Code hook docs (`hooks#common-input-fields`,
  `hooks#notification` for SubagentStart/SubagentStop)

**Potential T8 simplification to explore:** Agent-frontmatter-defined
PreToolUse hooks (lifecycle-scoped containment). See Learnings section.

## In Progress

**Clean stopping point.** The T7 definition is committed, pushed, and PR
#98 is open. No implementation work is in flight. The document has been
through 9 scrutiny rounds (6 prior + 3 this session) and the user
accepted it with "No findings."

## Open Questions

1. **Does the `SubagentStart` → first `PreToolUse` ordering hold?**
   The lifecycle diagram implies it, and `SubagentStart`'s ability to
   inject context only makes sense if it runs first. But the docs don't
   explicitly guarantee it. T8's first step validates this.

2. **Can agent-frontmatter hooks replace global hook registration for
   containment?** The docs say frontmatter hooks are "scoped to the
   component's lifecycle." If the shakedown agent defines its own
   PreToolUse hook, it would only fire during the agent's lifetime —
   potentially eliminating the need for the seed-file/scope-file pattern
   entirely (the hook IS the agent, so no `agent_id` matching needed).
   Not explored this session.

3. **Will B1 generate enough scoutable claims?** B1 is an architecture
   review task. Most claims should be about code existence/absence
   (scoutable via Read). But some may be about behavioral correctness
   (harder to scout). The >50% `not_scoutable` threshold is conservative
   but untested.

## Risks

1. **The T7 definition has never been validated by implementation.**
   9 rounds of scrutiny improved the definition significantly, but some
   errors are only discoverable during T8 (e.g., whether `updatedInput`
   reliably rewrites paths, whether the per-turn emission schema is
   producible by Claude's dialogue behavior).

2. **The seed-file → scope-file two-phase pattern is novel.** It's a
   reasonable design, but it hasn't been implemented or tested. The
   handshake between three separate hook scripts (SubagentStart,
   PreToolUse, SubagentStop) sharing state via filesystem creates timing
   windows that only manifest under real execution.

3. **Ordering inference for SubagentStart is load-bearing.** The entire
   containment bootstrapping depends on SubagentStart completing before
   the first PreToolUse. If it doesn't hold, the fail-closed fallback
   (deny + retry) works but adds latency and complexity. The validation
   step is the first T8 task for this reason.

## References

| What | Where |
|------|-------|
| T7 definition (the deliverable) | `docs/plans/2026-04-07-t7-executable-slice-definition.md` |
| PR #98 | `https://github.com/jpsweeney97/claude-code-tool-dev/pull/98` |
| T-04 benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` |
| T4 scouting behavior | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md` |
| T4 state model | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md` |
| T4 containment | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md` |
| T4 benchmark readiness | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md` |
| T6 composition review | `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md` |
| Convergence-loop risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Codex-collaboration delivery | `docs/superpowers/specs/codex-collaboration/delivery.md` |
| Claude Code hook docs | `hooks#common-input-fields`, `hooks#notification`, `hooks#hook-lifecycle` |
| Prior handoff | `docs/handoffs/archive/2026-04-07_13-39_t7-executable-slice-definition-through-5-scrutiny-rounds.md` |

## Gotchas

1. **`agent_id` is only available in subagent calls.** Main-thread hook
   invocations do not include `agent_id` or `agent_type` in the hook
   input (`hooks#common-input-fields`). Any design that relies on
   `agent_id` for discrimination requires the target to run inside a
   subagent.

2. **SubagentStart cannot block subagent creation.** Exit code 2 only
   shows stderr to the user; it does not prevent the subagent from
   starting (`hooks#exit-code-output`). So the SubagentStart hook cannot
   abort the shakedown if the seed file is missing — it can only warn.
   The PreToolUse hook is the enforcement point.

3. **Hooks defined in agent frontmatter are lifecycle-scoped.** This
   means they fire only while the agent is active, and `Stop` hooks are
   auto-converted to `SubagentStop`. This is a potential simplification
   for T8 but needs verification that frontmatter-defined PreToolUse
   hooks have the same capabilities as globally-registered ones.

4. **PostToolUse cannot modify native tool output.** (Carried from prior
   session.) Only `updatedMCPToolOutput` works, and only for MCP tools.
   The containment design must use PreToolUse for native tools. Checked
   against official docs 2026-04-07.

5. **T4 verification states are NOT `verified / false / not_scoutable`.**
   (Carried from prior session.) The normative vocabulary is
   `unverified | supported | contradicted | conflicted | ambiguous |
   not_scoutable` (T4-SM-06, state-model.md:311).

## Conversation Highlights

### User's structured external review workflow

The user reviewed the T7 document externally between sessions, returning
with formatted findings using `::code-comment` blocks containing title,
body, file path, line range, priority, and confidence score. Each finding
included line-level citations to both the T7 document and Claude Code
docs. This is a mature review protocol — findings are machine-parseable
and evidence-grounded.

### Progressive narrowing through 3 rounds

Round 1 found the `session_id`-only leakage (structural). Round 2 found
the `agent_id` acquisition gap (bootstrapping). Round 3 found the
ordering evidence quality and fail-closed polarity. Each round addressed
the most important remaining issue, building on prior fixes rather than
finding new structural problems.

### User's "say that directly" guidance

When the user identified that `SubagentStart` was the intended mechanism,
they said: "If your intended mechanism is 'write the scope file from
SubagentStart and remove it from SubagentStop,' say that directly. That
would turn the current assumption into an implementable lifecycle
contract." This preference for explicit mechanism naming over implicit
design assumptions is consistent with prior sessions.

### Acceptance signal

User's final review: "No findings. The timeout fallback now fails closed
in both places I checked. Residual risk is now where it should be: the
SubagentStart → first PreToolUse ordering remains an inference from the
docs, but the document no longer overclaims it. That is a defensible
stopping point for the T7 review."

## User Preferences

**Explicit mechanism naming over implicit design.** User's correction
style: "If your intended mechanism is X, say that directly." When the
document described what should happen without naming the specific hook
event, the user flagged it as unimplementable. The user wants lifecycle
contracts to name the exact documented surface they rely on.

**Evidence-based review with confidence scores.** The user's
`::code-comment` blocks include `confidence` fields (e.g., 0.93, 0.77,
0.84, 0.92, 0.94). Higher confidence correlates with more precise
citations. This scoring system helps prioritize review findings.

**Fail-closed as default for containment.** The user caught the
fail-open fallback immediately and at P1 priority with 0.94 confidence.
Containment mechanisms must deny by default; pass-through is never an
acceptable fallback for security-relevant hooks.

**Inference labeling.** The user distinguishes between documented facts,
reasonable inferences, and assumptions. When the document stated an
inference as a guarantee, the user flagged it as P2. The expectation is
that inferences are explicitly labeled and accompanied by validation
plans.

**Progressive tightening workflow (continued).** Consistent with the
prior session: each review round corrects specific findings rather than
rejecting the approach. The structure survives across rounds; changes are
within the structure.

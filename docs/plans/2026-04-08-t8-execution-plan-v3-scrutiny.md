# T8 Execution Plan V3 — Scrutiny Report

**Date:** 2026-04-08
**Document under review:** `docs/plans/2026-04-08-t8-shakedown-execution-plan-v3.md`
**Cross-references:** T7 (`docs/plans/2026-04-07-t7-executable-slice-definition.md`), T8 (`docs/plans/2026-04-07-t8-minimum-runnable-shakedown-packet.md`)
**Verdict:** Minor revision — 5 findings, all addressable without redesign.

## Scope

Fresh-eyes adversarial review of V3, filtered to actionable findings only. Risks the plan already manages (LLM emission compliance, Phase 0 matcher breadth, transcript retry calibration) are excluded — the plan's existing fallback paths are adequate.

---

## Finding 1 (Moderate): Counter field propagation gap between T8 Phase 2b and V3

**Location:** T8:262, V3:124-133, T7:295

**Problem:** V3's emission contract defines 8 counter keys: `total_claims`, `supported`, `contradicted`, `conflicted`, `ambiguous`, `not_scoutable`, `unverified`, `evidence_count`. T8 Phase 2b (line 262) reproduces T7's shorter 6-key set, omitting `conflicted` and `ambiguous`. T8 Phase 2b explicitly says to use the "T7-specified schema."

T7 already defines `conflicted` and `ambiguous` as normative verification states (T7:72) — the shorter counter set at T7:295 is an omission, not a deliberate exclusion. V3 corrected this. But T8 Phase 2b was not updated to match.

**Risk:** An implementer following T8 Phase 2b literally emits counters without `conflicted` and `ambiguous`. The V3 validator rejects the output. The failure is diagnosable (missing keys), but avoidable.

**Required changes:**

1. T8:262 — update the counter listing to include `conflicted` and `ambiguous`:
   ```
   counters: {total_claims, supported, contradicted, conflicted, ambiguous, not_scoutable, unverified, evidence_count}
   ```
2. T8:258 — change "T7-specified schema" to "emission contract schema (V3 L94-147 is authoritative)."

---

## Finding 2 (Moderate): Spawn prompt is a placeholder

**Location:** T8:319

**Problem:** The harness procedure says:
```
Agent(subagent_type="shakedown-dialogue", prompt=<B1 task prompt with repo_root and scope context>)
```

The angle-bracket placeholder specifies *that* a prompt is needed and *what kind of context* it should carry, but not the prompt's content, structure, or required fields. Since the agent's behavior depends on the preloaded `dialogue-codex` skill plus this prompt, the prompt content matters. The prompt must provide at minimum: the B1 task description, the Codex question to initiate the dialogue, `repo_root`, and `scope_directories`.

**Risk:** An implementer must invent the prompt. Different prompt choices produce different agent behavior, making the shakedown result depend on an unspecified input.

**Required change:**

T8 Phase 3, after step 8 — add a prompt template specifying:
- The B1 task framing (what the dialogue is about)
- The Codex question or topic to initiate with
- `repo_root` and `scope_directories` as injected context
- Instruction to begin by calling `codex.dialogue.start`

---

## Finding 3 (Moderate): No termination rule for Codex API failure

**Location:** T8 Phase 2b (skill behavioral spec), V3 stabilization loop

**Problem:** The plan's risk table covers transcript capture failure, stale scope files, and ordering gaps. It does not address Codex tool failure during the dialogue. If `codex.dialogue.start` or `.reply` returns an error mid-dialogue, the agent has no instruction to terminate cleanly — it can only scout (Read/Grep/Glob) but has nothing to respond to. The harness has no mechanism to distinguish a partial dialogue from a completed one other than the transcript (which would exist but be incomplete).

**Risk:** A Codex failure mid-dialogue leaves the agent in an undefined state. It may loop on scouting with no Codex replies, exhaust `maxTurns`, and produce a transcript that looks like a completed dialogue but has no Codex content after the failure point. The inspection checklist would flag this, but the failure mode should be handled explicitly rather than relying on post-hoc detection.

**Required change:**

T8 Phase 2b skill behavioral spec — add a termination rule: "If any `codex.dialogue.*` tool returns an error, emit a terminal turn with `converged: false` and `epilogue.ledger_summary` describing the failure. Do not continue scouting without Codex replies."

---

## Finding 4 (Low): Zero-result scouting disposition is unspecified

**Location:** V3:108, V3:160

**Problem:** The emission contract requires scouting turns to set `disposition` to one of `supports|contradicts|ambiguous|conflicted|null`. The turn rules say `null` is for non-scouting turns (`scouted: false`). But the contract does not specify which disposition to emit when scouting was attempted and queries executed, but produced zero usable results (no matching files, empty grep output, no relevant content at the target path).

**Risk:** The agent encounters this during rehearsal and picks an arbitrary disposition. The validator accepts it (any enum value passes), but the inspection checklist interpretation depends on consistent disposition semantics.

**Required change:**

V3 turn rules (after line 160) — add: "If a scouting turn's queries return no usable evidence, set `disposition` to `ambiguous`."

---

## Finding 5 (Low): Harness procedure step numbering gap

**Location:** T8:299-300

**Problem:** The harness procedure jumps from step 5 to step 7. Step 6 is missing. This is an edit artifact — likely a prior version of the single-active-run check that was merged into step 5 during an earlier scrutiny round without renumbering subsequent steps.

**Risk:** Cosmetic, but a reader may wonder whether a step was accidentally deleted. In a document that has undergone 7 scrutiny rounds for exactly this kind of propagation drift, a numbering gap undermines confidence.

**Required change:**

T8:300 onward — renumber steps 7→6, 8→7, 9→8, 10→9, 11→10.

---
title: "T-04 v1 Authoring-Time Decisions"
date: 2026-04-14
status: Approved
parent_plan: docs/plans/2026-04-13-t04-v1-production-dialogue-scoping-plan.md
closes:
  - "§10.1 — inline scouting budget"
  - "§10.2 — flag vocabulary"
  - "§10.3 — production synthesis serialization"
defers:
  - "§10.4 — orchestrator crash recovery (happy path for v1; revisit if shipped usage hits non-happy path)"
---

# T-04 v1 Authoring-Time Decisions

## Purpose

The T-04 v1 scoping plan (`2026-04-13-t04-v1-production-dialogue-scoping-plan.md`) deferred four implementation-time questions to §10. This companion records the three resolutions made at authoring-time and the one explicit deferral. It is an implementation-time ledger against the approved plan, not a rewrite of the plan.

**Authority:** The parent plan is authority for v1 scope, contracts, and verification. This document is authority **only** for the four §10 items. Conflicts (none anticipated) resolve in favor of the parent plan unless explicitly superseded here.

## Decision 1 — Inline scouting budget (plan §10.1 / §6.2)

**Resolution:** **N=5 hard cap on combined `Read` + `Grep` + `Glob` tool calls** during the inline initial scouting phase, prior to `codex.dialogue.start`. The cap is **not** a soft target — exceeding 5 must require a deliberate code change to this constant, not orchestrator discretion.

**Applies to:** `packages/plugins/codex-collaboration/agents/dialogue-orchestrator.md` (authoring target, §12 step 2).

**Rationale.** Plan §6.2 suggested N=3 as initial target. Real investigations typically follow a locate → inspect → confirm shape that N=3 truncates: one `Grep` to locate plus two `Read`s to inspect leaves no budget for a confirmation pass, so the first `codex.dialogue.reply` ships with provisional context. N=5 accommodates one confirmation step (e.g., `Grep` locate → 2× `Read` inspect → 1× `Grep` confirm → 1× `Read` extend) while remaining bounded enough to preserve §9.2's "growth signals split into gatherer" mitigation.

**What does NOT count against the budget:**

| Call | Counted? |
|---|---|
| Inline scouting `Read`/`Grep`/`Glob` (pre-`dialogue.start`) | Yes |
| `codex.dialogue.start`, `codex.dialogue.reply`, `codex.dialogue.read` | No |
| Per-turn scouting inside the dialogue loop (governed by the reference doc) | No |
| `Agent` dispatches | No (orchestrator must not dispatch during scouting) |

**Alternatives rejected:**

- **N=3 hard cap** (plan default) — too tight for realistic locate→inspect→confirm shapes; would force first-reply cold starts on narrow-evidence objectives.
- **Soft target of N=3, hard cap of N=5** — reopens §9.2's mitigation rigor; soft targets let the budget creep before the split-into-gatherer trigger fires.
- **Structured budget (e.g., 1 Grep + 2 Reads + 1 Glob)** — prescriptive; doesn't match real investigation shapes.

**Reversibility.** High. The constant is a single authoring-time value in the orchestrator body. Bumping it to N=7 post-v1 is a one-line edit plus a re-read of §9.2 to confirm the anti-drift story still holds.

**Change trigger.** If a representative v1 objective consistently terminates inline scouting short of producing a usable prose block at N=5, the next packet raises N deliberately (documented cost). If scouting routinely stops at 2-3 calls with a sufficient block, the cap was non-binding and can be lowered.

## Decision 2 — Flag vocabulary (plan §10.2)

**Resolution:** **Zero flags in v1.** Invocation surface is exactly `/dialogue <objective>`. Defaults are hard-wired in the orchestrator body (scope = repo root per §5.1, scouting budget = N=5 per Decision 1 above, turn-budget inherited from the reference doc's terminalization rules).

**Applies to:** `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` (authoring target, §12 step 3).

**Rationale.** Plan §3.1 already commits to flags being implementation detail, not contract points. YAGNI pressure is real: each flag is a surface to parse, document, verify, and guard. None of the §10.2 candidates (`--profile`, `--paths`, `--budget`) has a concrete consumer in v1. Adding them pre-emptively trades a small authoring convenience for a larger maintenance and verification surface.

**Alternatives rejected:**

- **One flag (`--paths`)** — no concrete invocation friction observed yet; adding it pre-emptively pins a vocabulary we may regret.
- **All three flags** — contradicts §3.1 and inflates the bootstrap-test and skill-parsing surface without evidence of need.

**Invocation parser shape.** The skill's invocation handler captures the full argument string after `/dialogue` as `<objective>`. No flag tokenization. No positional arguments beyond the objective.

**Reversibility.** High. Adding a flag post-v1 is additive: a new argument pattern with a defaulted handler. No flag vocabulary is locked in that would need rewriting.

**Change trigger.** First real invocation friction — e.g., an objective where a user needs to seed explicit paths because the orchestrator's inline scouting can't find the surface. That friction identifies which flag is actually warranted, rather than guessing.

## Decision 3 — Production synthesis serialization (plan §10.3 / §3.2)

**Resolution:** **Hybrid view-over-canonical-JSON.** The `/dialogue` skill surfaces the orchestrator's artifact as a human-readable summary followed by the full raw artifact in a ` ```json ``` ` fence labeled as the canonical artifact. The Markdown summary is a **view**, not a second artifact. The JSON appendix is the **source of truth**.

**Applies to:** `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` (authoring target, §12 step 3; surfacing section of the skill body).

**Message shape (order):**

1. **Top line summary:** `termination_code`, `converged`, `turn_count`/`turn_budget`, `mode`, `mode_source`.
2. **Main prose:** `final_synthesis`.
3. **Supporting sections:** `final_claims[]` (table), `synthesis_citations[]` (list), `ledger_summary`.
4. **Appendix:** Full raw artifact in a ` ```json ``` ` fence with the heading **Canonical Artifact**.

**Authoring constraints.**

- **Canonical/view discipline.** The JSON appendix is source of truth; the Markdown above it is a derived view. If the two disagree, the JSON wins. Skill authoring must not compute fields for the Markdown view that differ from the artifact; every Markdown field is a projection of the corresponding JSON field.
- **No reliance on `<details>` collapsible behavior.** Plain fenced JSON is portable across Claude Code's terminal, piped output, and plain-text logs. Collapsible sugar is a rendering hint at best — if used, it must remain cosmetic; the content inside must be the canonical artifact whether rendered collapsed or expanded.

**Alternatives rejected:**

- **Raw JSON only** — unreadable for long `final_synthesis` prose and multi-item arrays; optimizes for a parser that does not exist in v1 per §7.2.
- **Markdown only** — discards the canonical artifact, forcing any future consumer (including the user's own downstream use) to reconstruct it.

**Rationale.** §3.2 fixes the artifact schema; §7.2 names the v1 consumer as the invoking user only. Hybrid optimizes for readability in the moment while preserving the artifact's fidelity for future consumers — the post-v1 cross-model parser migration (§7.2 deferred), later remaining-T-04 work (§2.2), or the user's own downstream re-ingestion.

**Reversibility.** Medium. The view shape is a local skill-body choice; reshaping post-v1 is a skill edit. The canonical/view discipline is foundational — reversing it (allowing the Markdown to drift from JSON) would invalidate any downstream parser and should be treated as a contract change, not a stylistic one.

**Change trigger.** First cross-model consumer ingests the canonical artifact (the §7.2 deferral trigger). At that point, review whether the JSON appendix shape still matches cross-model's `event_schema.VALID_MODES` expectations and adjust either side as needed.

## Decision 4 — Orchestrator crash recovery (plan §10.4) — **deferred**

**Resolution:** **Explicit deferral, no v1 design.** v1 targets happy path per §10.4's own framing.

**What this means operationally.** If the `dialogue-orchestrator` agent crashes mid-run, the residual state is:

- `active-run-<session_id>` pointer exists on disk.
- `scope-<run_id>.json` may exist (if `SubagentStart` fired) or may not (if crash pre-hook).
- Partial transcript content may exist in the agent's working state but will not be captured unless `SubagentStop` fires.

**Remediation path (for v1 operators):** Delete the stale pointer manually, or wait for the 24h age sweep via `scripts/clean_stale_shakedown.py` (which the preflight sweep in §6.1 step 1 also invokes). This is the same remediation path shakedown-b1 already documents.

**Change trigger.** First v1 invocation that hits a non-happy-path crash. At that point, design recovery semantics (automatic state file cleanup on detected crash, resume-vs-restart choice, transcript reconstruction from partial state).

## Cross-references

| Item | Where |
|---|---|
| Parent plan | `docs/plans/2026-04-13-t04-v1-production-dialogue-scoping-plan.md` |
| Plan §10 (Open Questions — resolved here) | parent plan, §10 |
| Plan §3.2 (artifact schema) | parent plan, §3.2 |
| Plan §6.2 (inline scouting rules) | parent plan, §6.2 |
| Plan §9.2 (scouting-growth risk) | parent plan, §9.2 |
| Plan §7.2 (deferred consumer migration) | parent plan, §7.2 |
| Orchestrator body (Decision 1 target) | `packages/plugins/codex-collaboration/agents/dialogue-orchestrator.md` (to be authored, §12 step 2) |
| `/dialogue` skill body (Decisions 2 and 3 target) | `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md` (to be authored, §12 step 3) |
| Preflight-sweep precedent cited by Decision 4 | `packages/plugins/codex-collaboration/skills/shakedown-b1/SKILL.md:35-45` |

## Status

Approved as authoring-time ledger for the implementation session beginning 2026-04-14 on `feature/t04-v1-implementation`.

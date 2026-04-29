# T-20260330-03: Codex-collaboration safety substrate and benchmark contract

```yaml
id: T-20260330-03
date: 2026-03-30
status: closed
closed_date: 2026-04-13
resolution: completed
resolution_ref: test/t-20260330-02-skill-boundary
priority: high
tags: [codex-collaboration, safety, profiles, learnings, benchmark, supersession]
blocked_by: [T-20260330-02]
blocks: [T-20260330-04, T-20260330-05]
effort: large
branch: test/t-20260330-02-skill-boundary
files:
  - packages/plugins/codex-collaboration/server/credential_scan.py
  - packages/plugins/codex-collaboration/server/secret_taxonomy.py
  - packages/plugins/codex-collaboration/server/consultation_safety.py
  - packages/plugins/codex-collaboration/server/profiles.py
  - packages/plugins/codex-collaboration/server/retrieve_learnings.py
  - packages/plugins/codex-collaboration/server/models.py
  - packages/plugins/codex-collaboration/server/journal.py
  - packages/plugins/codex-collaboration/server/context_assembly.py
  - packages/plugins/codex-collaboration/server/control_plane.py
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/scripts/codex_guard.py
  - packages/plugins/codex-collaboration/hooks/hooks.json
  - packages/plugins/codex-collaboration/references/consultation-profiles.yaml
  - packages/plugins/codex-collaboration/README.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
```

## Context

`T-20260330-02` makes codex-collaboration installable and proves a minimal
consult flow. That is necessary, but it is not enough to replace cross-model.

Cross-model's consult surface is not just packaging. It carries a shared
substrate:

- credential scanning
- tool-input safety policy
- consultation profiles
- learning retrieval
- analytics emission

Those behaviors are the production-grade layer around the advisory runtime.
This ticket ports that layer into codex-collaboration and lands the benchmark
contract that governs whether context-injection stays retired by default.

## Problem

Bundling packaging and substrate porting hides the real design work. The shell
is mechanical. The substrate is not. It requires deliberate choices about which
cross-model semantics survive, which are adapted to the new architecture, and
which are intentionally dropped.

If those decisions are left implicit, later dialogue and delegation work will
rebuild inconsistent safety behavior on top of the new runtime.

## Scope

**In scope:**

- Add the shared safety substrate needed by consult and dialogue flows
- Port or adapt credential scanning semantics into the codex-collaboration
  package
- Port or adapt the secret taxonomy used by the scanner and redaction policy
- Port or adapt the tool-input safety policy for advisory tool calls
- Add consultation profile definitions for consult and dialogue orchestration
- Add learning retrieval for consultation and dialogue briefings
- Add analytics emission that records consult and dialogue outcomes against the
  codex-collaboration audit model
- Adopt the dialogue supersession benchmark contract at
  `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`
  as the governing verification contract for the context-injection retirement
  decision
- Wire the existing contract into the codex-collaboration spec reading order
  and delivery references

**Explicitly out of scope:**

- Executing the benchmark
- Dialogue orchestration and gatherer agents
- Delegation runtime and promotion
- Porting cross-model JSONL analytics payloads as-is
- Porting context-injection as a plugin-side subsystem

## Design Constraints

- Port semantics, not code blindly. The new runtime and audit model are not the
  same as cross-model's shim architecture.
- Analytics must be rebuilt on codex-collaboration's audit vocabulary rather
  than copying cross-model event shapes.
- The benchmark contract is part of the deliverable in this ticket, not a
  follow-up note. The context-injection retirement decision stays provisional
  until the contract exists.

## Acceptance Criteria

- [ ] Credential scanning exists in codex-collaboration and fails closed for
      advisory tool calls
- [ ] Secret taxonomy support exists in codex-collaboration and is used by the
      scanner or related safety logic
- [ ] Tool-input safety policy exists for consult and dialogue-facing tool
      calls
- [ ] Consultation profile definitions exist and can resolve posture, turn
      budget, and reasoning defaults
- [ ] Learning retrieval exists and can inject matched entries into consult and
      dialogue briefings
- [ ] Analytics emission exists for consult and dialogue outcome records using
      codex-collaboration's audit/event model
- [ ] The dialogue supersession benchmark contract exists with fixed corpus,
      fixed rubric, adjudication rules, and pass/fail criteria
- [ ] Codex-collaboration spec docs point to the benchmark contract as the
      authority for the context-injection retirement decision

## Verification

- Run the consult flow with known blocked and allowed inputs and verify the
  safety substrate blocks or permits correctly
- Resolve at least one named consultation profile through the new configuration
- Inject at least one learning entry into a consult briefing
- Emit and inspect a consult outcome artifact in the new analytics path
- Review the benchmark contract and confirm it defines corpus, scoring, and
  pass/fail rules without relying on judgment-call language

## Dependencies

This ticket follows the packaged consult flow from `T-20260330-02`. When it is
stable, `T-20260330-04` and `T-20260330-05` can proceed in parallel.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Cross-model scanner | `packages/plugins/cross-model/scripts/credential_scan.py` | Semantic source only |
| Cross-model safety policy | `packages/plugins/cross-model/scripts/consultation_safety.py` | Semantic source only |
| Cross-model profiles | `packages/plugins/cross-model/references/consultation-profiles.yaml` | Semantic source only |
| Cross-model learnings retrieval | `packages/plugins/cross-model/scripts/retrieve_learnings.py` | Semantic source only |
| Cross-model analytics emission | `packages/plugins/cross-model/scripts/emit_analytics.py` | Semantic source only |
| Benchmark contract target | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | New verification contract |

## Resolution

All 8 acceptance criteria met. Subsystems were implemented incrementally as
greenfield rewrites (per `decisions.md` greenfield rules) prior to this ticket
formally opening. This session verified each criterion against implementation
evidence and fixed stale README documentation.

### Acceptance criteria mapping

| # | Criterion | Evidence | Status |
|---|-----------|----------|--------|
| 1 | Credential scanning fails closed | `codex_guard.py` exits 2 on parse/input/internal errors. `hooks.json` wires PreToolUse for `codex.consult`, `codex.dialogue.start`, `codex.dialogue.reply` | Verified |
| 2 | Secret taxonomy used by scanner | `credential_scan.py:14` imports `FAMILIES`, `check_placeholder_bypass` from `secret_taxonomy`. 230-line taxonomy, strict/contextual/broad tiers | Verified |
| 3 | Tool-input safety policy | `consultation_safety.py:33-54` defines per-tool policies: `CONSULT_POLICY`, `DIALOGUE_START_POLICY`, `DIALOGUE_REPLY_POLICY` | Verified |
| 4 | Profile resolution | `profiles.py:78` `resolve_profile()` returns posture, turn_budget, reasoning_effort, sandbox, approval_policy. 9 named profiles. Phased profiles rejected pending support | Verified |
| 5 | Learning retrieval into briefings | `context_assembly.py:155-164` calls `retrieve_learnings()`, injects into `supplementary_context` with redaction | Verified |
| 6 | Analytics emission | `OutcomeRecord` in `models.py:160`. Consult emits at `control_plane.py:228`, dialogue at `dialogue.py:256`. Dedup via `append_dialogue_outcome_once()`. Shape consistency tested | Verified |
| 7 | Benchmark contract | `dialogue-supersession-benchmark.md` (297 lines): Fixed Corpus (8 tasks), Adjudication Rules, Metrics (6), Pass Rule (4 conditions), Decision Consequences, Change Control | Verified |
| 8 | Spec docs point to benchmark | Listed as reading order #7 in spec `README.md:51`, authority `delivery`. Referenced from `delivery.md:264` and `decisions.md:35` | Verified |

### Documentation fix

Removed stale limitation entries ("No credential scanning" and "No profiles or
learning retrieval") from `packages/plugins/codex-collaboration/README.md`.
Added Safety Substrate section documenting the implemented subsystems. Updated
Limitations to reflect actual current state (concurrent sessions, phased profiles).

### Design note

Cross-model semantic sources were predecessors, not code to port. All 6
subsystems are independent rewrites under codex-collaboration's audit model, as
prescribed by `decisions.md` greenfield rules. The naming divergence (cross-model
`emit_analytics.py` → codex-collaboration `OutcomeRecord` + `journal.append_outcome()`)
is intentional: the semantics were ported under new vocabulary.

### Test counts

| Scope | Count |
|-------|-------|
| Full package (`tests/`) | 566 |
| Credential scanning | 90 lines |
| Consultation safety | 180 lines |
| Secret taxonomy | 134 lines |
| Profiles | 236 + 202 lines |
| Learning retrieval | 117 lines |
| Outcome shape consistency | 28+ lines |

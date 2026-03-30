# T-20260330-03: Codex-collaboration safety substrate and benchmark contract

```yaml
id: T-20260330-03
date: 2026-03-30
status: open
priority: high
tags: [codex-collaboration, safety, profiles, learnings, benchmark, supersession]
blocked_by: [T-20260330-02]
blocks: [T-20260330-04, T-20260330-05]
effort: large
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

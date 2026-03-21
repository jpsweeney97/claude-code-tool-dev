---
module: decisions
status: active
normative: true
authority: decisions
---

# Design Decisions

## D1: Standalone-First, Protocol-Rich Composition

Each skill remains fully standalone and human-usable. Composition is additive — structured capsules and sentinels are appended to or alongside existing prose output. No skill requires upstream context to function.

**Alternatives considered:**

- **Observational only** (document the implicit format mapping, no structural changes): Too brittle — finding identity breaks, severity carry-forward is unreliable from prose parsing.
- **Full protocol** (formal schemas with validation, required fields): Over-couples skills, pushes AR toward remediation logic, violates standalone principle.
- **Orchestrator meta-skill**: Over-engineers a 3-skill pipeline. Revisit if pipeline grows beyond these skills.

## D2: Two Consumer Classes

Advisory/tolerant and strict/deterministic. See [foundations.md](foundations.md#consumer-classes) for definitions.

**Rationale:** NS consuming AR is advisory because AR capsule may be absent (standalone NS invocation). Dialogue consuming NS handoff is strict because if a handoff is present, it must be valid — partial handoff data is worse than no handoff.

## D3: Feedback Loop Topology — Targeted Arcs with User Ratification

Dialogue synthesis feeds back to AR or NS individually based on what emerged, not as a full pipeline re-run. The user confirms each hop. No auto-chaining.

## D4: Snapshot-Based State with Lineage

Each skill run produces a new artifact. No growing context across iterations. Lineage references (`supersedes`, `source_artifacts`) enable staleness detection without requiring full history carry-forward.

## D5: Global Protocols Do Not Auto-Emit Capsules

The global Adversarial Self-Review and Next Steps Planning protocols (in CLAUDE.md) are independent behaviors. They do not auto-emit capsules. See [foundations.md](foundations.md#capsule-externalization-rule) for the normative rule.

# Learnings

Project insights captured from consultations. Curate manually: delete stale entries, merge duplicates.

### 2026-02-17 [codex, workflow]

When designing validation criteria for a prototype phase, separate habit-formation validation ("will the developer actually use this?") from causal efficacy validation ("does this measurably improve outcomes?"). Phase 0 can only credibly measure the former — adoption frequency, curation actions, artifact-backed reuse events. Causal measurement requires infrastructure (A/B tests, blinding, withdrawal probes) that contradicts Phase 0's "no infrastructure" constraint. The spec's original 10/3 gate ("capture 10 insights, report 3 useful") conflates both questions into a single self-rating gate. Pre-register rubrics and thresholds before starting to prevent goalpost-shifting.

### 2026-02-17 [skill-design, architecture]

When instruction documents layer (skill references agent, agent references contract), each layer must be fully operational standalone. Conditional logic like "if the agent spec is loaded, use its patterns; otherwise fall back" creates ambiguity that an LLM will resolve inconsistently — "available" is operationally undefined when the referenced spec isn't loaded. The fix: inline the minimal self-contained version at each layer, with a note that other sources are additive, not alternative. This emerged from a 3-dialogue parallel review of the `/codex` skill where the evaluative dialogue independently discovered (T8) that a "prefer codex-dialogue profile when available" clause was a loophole, and the exploratory dialogue independently chose "full replacement stubs over summary stubs" (T4) for the same reason — summary stubs that say "see the contract" create hard dependencies that break when the contract is unavailable.

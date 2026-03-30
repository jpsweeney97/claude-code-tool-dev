# T-20260330-04: Codex-collaboration dialogue parity and scouting retirement

```yaml
id: T-20260330-04
date: 2026-03-30
status: open
priority: high
tags: [codex-collaboration, dialogue, agents, benchmark, supersession]
blocked_by: [T-20260330-03]
blocks: [T-20260330-07]
effort: large
```

## Context

Dialogue is the user-adoption gate for codex-collaboration. Cross-model cannot
be retired in practice until users can switch their `/dialogue` workflow.

The runtime side already has `codex.dialogue.start`, `.reply`, and `.read`.
What is missing is the user surface and the evidence-gathering layer around it:

- dialogue skill
- dialogue orchestration agent
- context gatherer agents
- synthesis format
- convergence detection
- benchmark execution for the context-injection retirement decision

## Problem

Without a production dialogue surface, codex-collaboration remains an internal
runtime rather than the actual successor plugin. The open design question is no
longer whether dialogue should exist. It is whether Claude-side scouting is
good enough to replace cross-model's plugin-side context-injection subsystem.

That question must be answered by the fixed benchmark contract from
`T-20260330-03`, not by ad hoc impressions.

## Scope

**In scope:**

- Add the codex-collaboration dialogue skill
- Add the codex-dialogue orchestration agent for the new package
- Add the code gatherer and falsifier agents for the new package
- Implement deterministic briefing assembly for the dialogue flow
- Implement convergence detection and final synthesis formatting
- Use Claude-side scouting with standard host tools (`Glob`, `Grep`, `Read`) as
  the default evidence-gathering mechanism
- Run the benchmark defined in
  `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`
- Record the benchmark result and make the context-injection retirement decision
  explicit

**Explicitly out of scope:**

- Porting context-injection before the benchmark says it is necessary
- Delegation and promotion
- Analytics dashboard or cutover work
- Any change to the execution-domain runtime

## Decision Rule

- If the benchmark passes, codex-collaboration keeps Claude-side scouting as
  the default dialogue evidence path and context-injection remains retired by
  default.
- If the benchmark fails, do not port context-injection opportunistically.
  Create a focused follow-up packet that names the measured shortfall and the
  minimal subsystem needed to close it.

## Acceptance Criteria

- [ ] A codex-collaboration dialogue skill exists and routes through
      `codex.dialogue.start`, `.reply`, and `.read`
- [ ] A codex-dialogue orchestration agent exists in the codex-collaboration
      package
- [ ] Code and falsifier gatherer agents exist in the codex-collaboration
      package and use standard Claude-side tools
- [ ] Dialogue runs produce a final synthesis with bounded evidence citations
      and a convergence result
- [ ] The benchmark contract is executed on the fixed corpus without changing
      the corpus or pass rule mid-run
- [ ] The benchmark result is recorded in repo artifacts with per-task metrics
      and an aggregate pass/fail decision
- [ ] The context-injection retirement decision is updated from provisional to
      explicit based on the benchmark result

## Verification

- Run at least one end-to-end dialogue through the packaged codex-collaboration
  surface
- Inspect the gatherer outputs, assembled briefing, and final synthesis for a
  benchmark task
- Verify the benchmark artifact set includes raw run records, adjudication, and
  aggregate pass/fail output
- Confirm the retirement decision follows the contract outcome rather than a
  narrative summary

## Dependencies

This ticket depends on the shared substrate and benchmark contract from
`T-20260330-03`. It can run in parallel with `T-20260330-05` once that shared
substrate is stable.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Dialogue runtime surface | `packages/plugins/codex-collaboration/server/dialogue.py` | Existing runtime foundation |
| Current MCP tool exposure | `packages/plugins/codex-collaboration/server/mcp_server.py` | Existing tool routing |
| Cross-model dialogue skill | `packages/plugins/cross-model/skills/dialogue/SKILL.md` | Semantic source only |
| Cross-model gatherer agents | `packages/plugins/cross-model/agents/` | Semantic source only |
| Benchmark authority | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Fixed evaluation contract |

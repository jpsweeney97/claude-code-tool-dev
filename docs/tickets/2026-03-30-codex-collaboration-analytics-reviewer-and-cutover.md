# T-20260330-07: Codex-collaboration analytics, reviewer, and cross-model cutover

```yaml
id: T-20260330-07
date: 2026-03-30
status: open
priority: medium
tags: [codex-collaboration, analytics, reviewer, cutover, supersession]
blocked_by: [T-20260330-04, T-20260330-06]
blocks: []
effort: medium
```

## Context

After dialogue parity and delegation completion, codex-collaboration still
needs the observability and migration layer that lets the repo actually remove
cross-model:

- analytics dashboard
- reviewer agent
- optional quality-of-life glue
- migration and verification docs
- removal of cross-model from the repo

This is the final cutover packet.

## Scope

**In scope:**

- Add the codex-collaboration analytics skill
- Add analytics computation over the codex-collaboration audit model
- Add the codex-reviewer agent for the new package
- Add any low-risk glue needed for parity, such as optional nudge behavior if
  it still proves useful
- Write migration documentation from cross-model to codex-collaboration
- Write parity verification that maps each cross-model workflow to its
  codex-collaboration replacement
- Remove cross-model packaging and code that is no longer needed after cutover
- Remove context-injection only if `T-20260330-04` records a passing benchmark
  result

**Explicitly out of scope:**

- New advisory or execution capabilities beyond the codex-collaboration spec
- Reintroducing the `codex exec` shim or cross-model event schema

## Acceptance Criteria

- [ ] An analytics skill exists and can compute consultation, dialogue,
      delegation, and security views from codex-collaboration artifacts
- [ ] A codex-reviewer agent exists in the codex-collaboration package
- [ ] Migration docs show how to replace each cross-model workflow with the new
      plugin surface
- [ ] A parity matrix exists and covers consult, dialogue, delegate, analytics,
      and reviewer workflows
- [ ] Cross-model is removed from the repo once the parity matrix is complete
- [ ] Context-injection is removed only if the benchmark decision in
      `T-20260330-04` passed

## Verification

- Run the analytics skill against codex-collaboration-generated artifacts
- Run the reviewer agent on a real diff
- Execute the parity checklist before removal
- Confirm that no supported cross-model workflow remains without a
  codex-collaboration replacement at removal time

## Dependencies

This ticket depends on both the dialogue adoption packet (`T-20260330-04`) and
the delegation completion packet (`T-20260330-06`).

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Cross-model analytics skill | `packages/plugins/cross-model/skills/consultation-stats/SKILL.md` | Semantic source only |
| Cross-model reviewer agent | `packages/plugins/cross-model/agents/codex-reviewer.md` | Semantic source only |
| Cross-model README | `packages/plugins/cross-model/README.md` | Migration inventory |

# T-20260330-06: Codex-collaboration promotion flow and delegate UX

```yaml
id: T-20260330-06
date: 2026-03-30
status: open
priority: high
tags: [codex-collaboration, promotion, delegate, rollback, supersession]
blocked_by: [T-20260330-05]
blocks: [T-20260330-07]
effort: large
```

## Context

`T-20260330-05` builds the execution-domain foundation. This ticket turns that
infrastructure into the actual delegation product:

- inspection and poll surface
- escalation resolution
- promotion prechecks
- artifact hash verification
- rollback
- `/delegate` UX

This is the packet that replaces cross-model's autonomous execution workflow
with the new split-runtime architecture rather than a batch `codex exec`
wrapper.

## Scope

**In scope:**

- Add `codex.delegate.poll`
- Add `codex.delegate.decide`
- Add `codex.delegate.promote`
- Implement the promotion prechecks and typed rejection shapes from the spec
- Implement artifact hash computation and verification
- Implement rollback behavior for failed promotion paths
- Mark advisory context stale after successful promotion per the advisory policy
- Add the codex-collaboration delegate skill on top of the delegate tool
  surface
- Add tests for promotion success, typed rejection, artifact-hash mismatch, and
  rollback paths

**Explicitly out of scope:**

- Analytics dashboard
- Reviewer agent
- Final cross-model removal
- Multi-job concurrency beyond max-1
- Three-way merge support in promotion

## Acceptance Criteria

- [ ] Delegation results can be polled through the typed `codex.delegate.poll`
      surface
- [ ] Pending execution-domain escalations can be resolved through
      `codex.delegate.decide`
- [ ] Promotion enforces HEAD match, clean index, clean worktree, artifact-hash
      verification, and completed-job preconditions
- [ ] Promotion returns typed rejection responses when prechecks fail
- [ ] Failed promotion paths can roll back cleanly
- [ ] Successful promotion marks advisory context stale for the next advisory
      turn
- [ ] A delegate skill exists in the codex-collaboration package and routes
      through the new delegate tool surface

## Verification

- Run the promotion success path on an isolated execution job
- Trigger each typed rejection path at least once in tests
- Trigger an artifact-hash mismatch and confirm promotion blocks
- Trigger a rollback-needed path and confirm rollback behavior is observable
- Run the delegate skill through a full execution and promotion cycle

## Dependencies

This ticket depends on `T-20260330-05` for execution-domain state and worktree
infrastructure. It must land before the final analytics and cutover packet in
`T-20260330-07`.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Promotion protocol | `docs/superpowers/specs/codex-collaboration/promotion-protocol.md` | Normative behavior |
| Typed responses | `docs/superpowers/specs/codex-collaboration/contracts.md` | Rejection and busy shapes |
| Advisory stale-context policy | `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md` | Post-promotion coherence |

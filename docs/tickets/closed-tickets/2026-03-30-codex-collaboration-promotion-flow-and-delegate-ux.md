# T-20260330-06: Codex-collaboration promotion flow and delegate UX

```yaml
id: T-20260330-06
date: 2026-03-30
status: closed
closed_date: 2026-04-21
priority: high
tags: [codex-collaboration, promotion, delegate, rollback, supersession]
blocked_by: [T-20260330-05]
blocks: [T-20260330-07]
effort: large
resolution: completed
resolution_ref: "PR #114 (85afab6b)"
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

- [x] Delegation results can be polled through the typed `codex.delegate.poll`
      surface
- [x] Pending execution-domain escalations can be resolved through
      `codex.delegate.decide`
- [x] Promotion enforces HEAD match, clean index, clean worktree, artifact-hash
      verification, and completed-job preconditions
- [x] Promotion returns typed rejection responses when prechecks fail
- [x] Failed promotion paths can roll back cleanly
- [x] Successful promotion marks advisory context stale for the next advisory
      turn
- [x] A delegate skill exists in the codex-collaboration package and routes
      through the new delegate tool surface

### AC Evidence

| AC | Evidence | PR / Commit |
|---|---|---|
| poll | `codex.delegate.poll` with artifact materialization, SHA-256 review hash, snapshot caching | PR #111 (`8bae4dde`) |
| decide | `codex.delegate.decide` with PendingEscalationView projection, approve/deny/answers | PR #109 (`e041c896`), `57c6466a` |
| promotion prechecks | HEAD match, clean index, clean worktree, artifact-hash verification, completed+promotable gate | PR #113 (`27505cc0`) |
| typed rejections | `PromotionRejectedResponse` with reason codes: `job_not_completed`, `job_not_reviewed`, `head_mismatch`, `workspace_dirty`, `index_dirty`, `artifact_hash_mismatch` | PR #113 (`27505cc0`) |
| rollback | Post-apply verification failure triggers `rolled_back` transition with workspace restore | PR #113 (`27505cc0`) |
| stale advisory context | `mark_stale_after_promotion()` called on successful verify | PR #113 (`27505cc0`) |
| delegate skill | 304-line SKILL.md with grammar parser, 4-tier state router, 3 ceremony gates, 8 allowed-tools | PR #114 (`85afab6b`) |

Supporting PRs: spec amendments (PR #110, `47a1fbff`), sidecar hardening (PR #112, `f9a40366`).

## Verification

- [x] Run the promotion success path on an isolated execution job — `test_promote_success_applies_diff_and_verifies` (PR #113)
- [x] Trigger each typed rejection path at least once in tests — 6 rejection reason codes tested (PR #113)
- [x] Trigger an artifact-hash mismatch and confirm promotion blocks — `test_promote_rejects_artifact_hash_mismatch` (PR #113)
- [x] Trigger a rollback-needed path and confirm rollback behavior is observable — `test_promote_rolls_back_on_verification_failure` (PR #113)
- [ ] Run the delegate skill through a full execution and promotion cycle — **Deferred.** Requires running Codex App Server. Automated package-level verification passed (845 tests). Live product smoke deferred to T-07 cutover or standalone App Server testing session.

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
| Delegate skill design spec | `docs/superpowers/specs/2026-04-21-delegate-skill-ux-design.md` | Skill UX design |
| Delegate skill implementation plan | `docs/superpowers/plans/2026-04-21-delegate-skill-ux-implementation.md` | Execution plan |

## Resolution

Closed 2026-04-21. All 7 ACs met across 5 PRs (#109, #110, #111, #112, #113, #114) and 1 direct commit (`57c6466a`). 845 tests on main at `85afab6b`.

**Deferred to T-07 or standalone session:** Live `/delegate` invocation through full execution and promotion cycle. Requires Codex App Server. All server-side behavior is verified by automated tests; the deferred item covers only skill rendering UX (diff display, escalation formatting, ceremony gate enforcement as experienced by Claude in a live session).

> **Superseded (2026-04-29):** The deferred live `/delegate` smoke was satisfied during T-01 delegate execution remediation. Live smoke artifact at `a7a4e9c9`, T-20260423-01 closed at `6580d86e`. See `docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md`.

**Final test count progression:** T-05 baseline 698 → decide 734 → poll 765 → sidecar 771 → promote/discard 816 → projection 818 → delegate skill 845.

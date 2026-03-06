# Ticket Plugin Priority Recalibration

## Context
- Protocol: `decision-making.framework@1.0.0`
- Stakes level: rigorous
- Decision trigger: Recalibrate the ticket plugin implementation plan after user feedback that the original review over-weighted theoretical concurrency and under-weighted Claude skill execution reliability.
- Time pressure: no constraint

## Entry Gate
- Stakes level: rigorous
- Rationale: This choice affects the near-term roadmap for a working plugin, changes which risks are treated as first-order, and influences future autonomy work. Blast radius is moderate and reversible, but the cost of prioritizing the wrong work is real.
- Time budget: no constraint
- Iteration cap: 3
- Evidence bar: The recommended ordering must reduce real `/ticket` execution failures, stay proportionate to the plugin's actual deployment model, and avoid locking in unnecessary architecture.
- Allowed skips: Full sensitivity sweep beyond a single weight-swap check; Codex Delta; no new repo research outside the plugin because local evidence is sufficient.
- Overrides: None
- Escalation trigger: If two options remain near-tied after pressure testing, escalate to the user with the tie and the unresolved assumption.
- Initial frame: Decide which implementation ordering should guide the next round of ticket plugin work.
- Known constraints:
  - Single-user, single-repo plugin
  - Default autonomy mode is `suggest`
  - `auto_audit` is opt-in and session-capped
  - Existing plugin is already working and has a large passing test suite
  - Avoid database/daemon/distributed-coordination designs
- Known stakeholders:
  - Primary repo user
  - Claude runtime following `SKILL.md`
  - Future maintainer of the ticket plugin

## Frame
### Decision Statement
What implementation ordering should guide the next round of work on the ticket plugin, given that real-world friction is more about Claude reliably following the skill contract than about high-volume concurrent mutation?

### Constraints
- C1: The plugin is not greenfield; changes must fit the current v1.2 behavior and test posture.
- C2: Priority should reflect actual operating conditions, not hypothetical multi-user infrastructure risks.
- C3: The next steps should reduce user-visible failure modes quickly.
- C4: Large architectural rewrites should be deferred unless they unlock a clear near-term benefit.
- C5: Autonomy hardening beyond `auto_audit` should not be front-loaded without an actual `auto_silent` timeline.

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| Runtime reliability for Claude | 5 | Reduces `/ticket` failures caused by stage propagation mismatches, naming drift, or ambiguous skill instructions |
| Proportionality to actual risk | 5 | Matches effort to the plugin's single-user, opt-in autonomy deployment model |
| Cost and time to land | 4 | Can be implemented quickly without broad churn |
| Integrity and safety coverage | 3 | Improves real data/audit correctness without overreacting to edge cases |
| Maintainability leverage | 3 | Reduces future drift and clarifies the contract for later work |

### Stakeholders
| Stakeholder | What they value | Priority |
|-------------|-----------------|----------|
| Repo user | Predictable `/ticket` behavior, low friction, fast fixes | High |
| Claude runtime | Clear stage contract, stable field names, fewer fragile instructions | High |
| Plugin maintainer | Low-drift mutation paths, manageable core complexity, explicit residual risks | Medium |

### Assumptions
- A1: Claude mis-executing the staged skill contract is a more common real-world failure mode than parallel autonomous create collisions. Status: unverified but strongly supported by the plugin's usage model and user feedback.
- A2: Parallel create/create collisions are rare enough that preventing silent overwrite is sufficient for now. Status: unverified.
- A3: `auto_silent` has no near-term shipping timeline. Status: unverified but directly asserted by user context.
- A4: Legacy ticket generations are finite and should eventually move from open-ended compatibility to explicit migration policy. Status: unverified.
- A5: Version labeling is already drifting across artifacts (`contract_version` `1.0`, `pyproject.toml` `1.0.0`, user-reported plugin manifest `1.2.0`). Status: partially verified.

### Scope
- In bounds:
  - Reordering implementation priorities
  - Identifying the next high-leverage fixes
  - Adjusting backlog priorities and residual-risk handling
- Out of bounds:
  - Implementing the changes
  - Shipping `auto_silent`
  - Designing new storage or coordination systems
- Related decisions:
  - When to drop legacy parse support
  - How contract versioning should track plugin versioning

### Reversibility
This roadmap is easy to revise, but the first few tasks influence whether follow-on work is focused on user reliability or on theoretical infrastructure hardening.

### Dependencies
- Depends on the current staged engine contract and current skill docs
- Depends on existing serializer split and parser behavior
- Blocks future work on autonomy UX and any quiet-mode discussions

### Downstream Impact
- Enables:
  - More reliable `/ticket` execution by Claude
  - Safer serializer refactors
  - Cleaner backlog prioritization
- Precludes:
  - Treating all concurrency concerns as immediate blockers
  - Spending early effort on `auto_silent` prerequisites without a ship decision

## Options Considered
### Option 1: Reliability-First Minimal Patch Set
- Description: Normalize stage field names at the engine boundary, unify serializers, finish audit repair, add `O_EXCL` create protection, and add the missing `key_file_paths` test. Keep module extraction and foreground-only enforcement later.
- Trade-offs: Maximizes immediate user impact and low effort, but leaves versioning/legacy policy as an unowned follow-up and accepts update-path race limitations as implicit rather than explicit.

### Option 2: Integrity-First Concurrency Hardening
- Description: Keep the original lock-first plan, lead with repo-scoped mutation serialization and broader safety enforcement, then return to DX and serializer issues.
- Trade-offs: Best raw integrity coverage on paper, but poorly calibrated to actual usage and expensive relative to observed risk.

### Option 3: Reliability-First With Narrow Integrity Guardrails
- Description: Normalize stage field names first, unify serializers second, finish audit repair, fix and test the `key_file_paths` flow, add atomic create-with-retry using `O_EXCL`, and add explicit backlog items for legacy-support retirement and contract/plugin versioning policy. Defer repo-wide locking and foreground-only enforcement unless agent autonomy scope expands.
- Trade-offs: Slightly broader than the minimal patch set, but still proportionate. It accepts rare update lost-write risk as a documented residual limitation rather than solving it immediately.

### Option 4: Null / Defer Reprioritization
- Description: Keep the original implementation plan and revisit only after concrete incidents.
- Trade-offs: No immediate analysis cost, but preserves a miscalibrated roadmap and likely spends effort on lower-value work first.

## Evaluation
### Criteria Scores
| Option | Runtime reliability for Claude | Proportionality to actual risk | Cost and time to land | Integrity and safety coverage | Maintainability leverage | Total |
|--------|--------------------------------|--------------------------------|-----------------------|-------------------------------|--------------------------|-------|
| Option 1 | 5 | 5 | 5 | 2 | 3 | 85 |
| Option 2 | 2 | 1 | 1 | 5 | 4 | 46 |
| Option 3 | 5 | 5 | 4 | 3 | 4 | 88 |
| Option 4 | 1 | 3 | 5 | 1 | 1 | 46 |

### Risks per Option
| Option | Key Risks | Mitigation |
|--------|-----------|------------|
| Option 1 | Leaves legacy/version drift unprioritized; residual update-path race remains implicit | Add explicit residual-risk note and backlog tickets later |
| Option 2 | Over-engineers for low-frequency scenarios; delays fixes users actually feel | Reject as first phase |
| Option 3 | Slight risk of backlog sprawl if legacy/version policy work grows beyond a small cleanup | Keep those tasks as policy/ticketing work, not broad refactors |
| Option 4 | Team keeps acting on a plan that no longer matches the operating context | Reject |

### Information Gaps
- No measured rate of stage-propagation failures versus concurrent mutation failures
- No local inventory yet of how many legacy-format tickets still exist in active use
- The user reports a `plugin.json` at `1.2.0`; that manifest is not present in this plugin directory, so version policy should be set against the actual packaging source of truth before being enforced

### Bias Check
- Anchoring: The first pass was biased toward infrastructure-style integrity concerns; user feedback correctly challenged that framing.
- Familiarity: Locking/serialization patterns are a familiar response to race conditions, which likely inflated their priority.
- Confirmation: Re-checked for evidence that `O_EXCL` addresses the actual create overwrite risk and accepted that it is the right immediate create fix.
- Availability: Avoided over-weighting the existence of a documented limitation simply because it is easy to reason about.

## Perspectives
| Stakeholder | View of Options | Concerns |
|-------------|-----------------|----------|
| Repo user | Option 1 and Option 3 improve the failures they actually see; Option 2 spends effort in the wrong place | Wants low-friction `/ticket`, not infrastructure work for edge cases |
| Claude runtime | Option 1 and Option 3 both reduce stage-contract footguns; Option 3 also reduces future drift pressure | Needs field names and docs to stop disagreeing |
| Plugin maintainer | Option 3 gives a more complete near-term roadmap than Option 1 without committing to heavy refactors | Does not want legacy/version drift to linger indefinitely |

## Pressure Test
### Arguments Against Frontrunner
1. Option 3 still adds work beyond the highest-ROI fixes.
   - Response: The extra work is intentionally small: explicit legacy/version policy and missing-flow coverage. That is materially cheaper than a transport redesign and prevents the plan from becoming "fix the obvious bug, ignore the accumulating edges."
2. If concurrency is truly low-risk, even `O_EXCL` may be unnecessary now.
   - Response: `O_EXCL` is cheap and directly prevents the highest-impact create failure mode: silent overwrite. That is a proportionate integrity floor.
3. Accepting update lost-write risk without a lock is inconsistent.
   - Response: It is a conscious residual-risk choice, not an oversight. Under the current deployment model, that risk should stay documented and monitored rather than driving Phase 1 architecture.

### Disconfirmation Attempts
- Sought: A reason to keep repo-scoped locking as the top recommendation.
- Found: The strongest remaining argument is update-path last-write-wins, but that does not outweigh the more common field-propagation reliability failures under the current operating model.
- Sought: A reason to choose the pure minimal patch set over the hybrid.
- Found: The minimal patch set is nearly tied, but it leaves legacy/version drift and residual-risk ownership too implicit.

## Decision
**Choice:** Option 3: Reliability-First With Narrow Integrity Guardrails

**Trade-offs Accepted:** Defer repo-wide locking, keep T-20260302-05 low until `auto_silent` has a real timeline, and accept documented residual update-path race risk for now.

**Confidence:** Medium-high

**Caveats:** If observed evidence shows concurrent update/create collisions in real use, or if agent autonomy expands materially, revisit the lock decision quickly. If the external plugin manifest truly anchors product versioning at `1.2.x`, add a small versioning policy task immediately.

## Downstream Impact
- This enables:
  - A revised plan centered on Claude execution reliability
  - A safer serializer consolidation
  - Small but explicit backlog additions for legacy and version drift
- This precludes:
  - Treating concurrency as the lead workstream
  - Pulling foreground-only enforcement forward without an `auto_silent` commitment
- Next decisions triggered:
  - Decide the legacy-support retirement policy
  - Decide how contract versioning maps to plugin/package versioning

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | Initial frame | Option 1 | Reliability-first clearly beats lock-first once calibrated to the actual deployment model |
| 2 | None | Option 3 | Pressure test showed Option 1 was nearly sufficient, but Option 3 better captures residual-risk ownership and the missed legacy/version backlog with minimal added cost |

## Exit Gate
- [x] All outer loop activities complete
- [x] All inner loop activities complete
- [x] Convergence indicators met for chosen level
- [x] Trade-offs explicitly documented
- [x] Decision defensible under scrutiny

# Category Integration Reference

When a category is selected during discovery, integrate these category-specific elements.

## Category List

| Category | Typical Risk | Dominant Failure Mode |
|----------|--------------|----------------------|
| debugging-triage | Medium | Missing regression guard |
| refactoring-modernization | Medium | Behavior change without detection |
| security-changes | High | Deny-path not verified |
| agentic-pipelines | High | Missing idempotency contract |
| documentation-generation | Low | Stale content |
| code-generation | Medium | Generated code doesn't compile |
| testing | Medium | Tests don't isolate failures |
| configuration-changes | Medium | Rollback not possible |
| dependency-changes | High | Breaking changes not detected |
| api-changes | High | Contract violation |
| data-migrations | High | Data loss or corruption |
| infrastructure-ops | High | Irreversible state change |
| meta-skills | Low | Produced skills don't comply |
| review-audit | Medium | Superficial review (missed issues) |
| prompt-engineering | Medium | Overfitting to test cases |
| research-exploration | Low | Inconclusive findings |
| planning-architecture | Medium | Plan doesn't survive implementation |
| performance-optimization | Medium | Wrong bottleneck targeted |
| automation-scripting | Medium | Works locally, fails in CI |
| ui-ux-development | Medium | Functional but poor UX |
| incident-response | High | Mitigation introduces new issues |

## Category-Specific DoD Additions

### debugging-triage
- Failure signature captured (exact error/test name)
- Root cause statement includes evidence
- Regression guard exists or rationale for omission

### refactoring-modernization
- Invariants explicitly stated ("behavior-preserving means...")
- Scope fence defined (what must NOT change)
- Characterization tests exist or are added

### security-changes
- Threat model boundaries stated
- Deny-path verification included
- Rollback plan specified

### agentic-pipelines
- Idempotency contract stated
- Plan/apply/verify separation exists
- All mutating steps have ask-first gates

### code-generation
- Generated code compiles/parses
- Type-checks pass (if applicable)
- Linting passes (if applicable)

### testing
- Test isolation verified (each test independent)
- Failure messages are actionable
- Coverage target met or gap justified

### dependency-changes
- Breaking change detection performed (semver analysis or test suite)
- Downstream consumers identified and notified
- Rollback path documented (pin to previous version)

### api-changes
- Contract compatibility verified (backward compatible or versioned)
- All consumers identified and migration path provided
- Documentation updated to reflect changes

### data-migrations
- Backup verified before migration
- Rollback procedure tested
- Data integrity checks pass post-migration

### infrastructure-ops
- Change is reversible or rollback plan exists
- Impact scope explicitly bounded
- Monitoring/alerting in place for verification

### review-audit
- Review criteria explicitly stated before review begins
- Coverage documented (what was reviewed, what was skipped and why)
- Findings categorized by severity (Critical / Major / Minor / Nitpick)
- Each finding includes: location, issue, impact, recommendation
- Confidence level stated (High / Medium / Low) for non-obvious findings

### prompt-engineering
- Goal statement explicit (what behavior the prompt should produce)
- Test cases defined: at least happy path + 2 edge cases
- All test cases pass with expected behavior
- Failure modes documented (what the prompt should NOT do)
- Regression baseline captured (example outputs for comparison)
- Token efficiency considered (prompt not unnecessarily verbose)

### research-exploration
- Research question explicitly stated before starting
- Scope bounded (what's in/out of investigation)
- Sources consulted documented (files read, docs checked, searches run)
- Findings summarized with evidence (not just conclusions)
- Answer to original question stated clearly, or "inconclusive" with explanation
- Next steps identified (what to do with findings)

### planning-architecture
- Problem/goal statement explicit before solution design
- Constraints enumerated (technical, timeline, compatibility, team)
- Alternatives considered (at least 2 approaches with trade-offs documented)
- Decision rationale captured (why this approach over alternatives)
- Dependencies identified (what must exist before implementation)
- Scope explicitly bounded (what's included, what's deferred)
- Verification criteria defined (how we'll know the plan worked)

### performance-optimization
- Target metric defined before optimization (latency, throughput, memory, bundle size)
- Baseline measurement captured (quantified "before" state)
- Bottleneck identified with evidence (profiler output, flame graph, metrics)
- Post-optimization measurement shows improvement on target metric
- Regression check: other metrics didn't degrade significantly
- Trade-offs documented (e.g., "reduced latency by 40%, increased memory by 10%")

### automation-scripting
- Purpose and trigger clearly documented (when does this run, who/what invokes it)
- Dependencies declared (tools, env vars, permissions required)
- Idempotency verified (safe to run multiple times)
- Error handling covers common failures (missing tools, network issues, permission denied)
- Exit codes meaningful (0 = success, non-zero = failure with distinct codes)
- Tested in target environment, not just local

### ui-ux-development
- Visual requirements specified (mockup, design system reference, or explicit description)
- Responsive behavior defined (breakpoints, mobile/tablet/desktop)
- Accessibility baseline met (keyboard navigation, screen reader labels, color contrast)
- Component renders without console errors/warnings
- Edge cases handled (empty states, loading states, error states, overflow text)
- Tested in target browsers/devices (or documented which are supported)

### incident-response
- Impact assessed (who/what is affected, severity, scope)
- Mitigation applied and verified (incident actually resolved, not just attempted)
- Rollback plan documented (how to undo mitigation if it makes things worse)
- Communication sent to stakeholders (if applicable)
- Timeline captured (when detected, when mitigated, when resolved)
- Follow-up items identified (root cause investigation, preventive measures)

## What to Pull from Category Guide

| Section | Category Guidance Source |
|---------|-------------------------|
| When NOT to use | Category's "When NOT to use (common misfires)" |
| Inputs | Category's "Input contract" |
| Outputs | Category's "Output contract" + "DoD checklist" |
| Decision points | Category's "Decision points library" |
| Verification | Category's "Verification menu" |
| Troubleshooting | Category's "Failure modes & troubleshooting" |

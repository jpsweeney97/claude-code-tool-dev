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

## What to Pull from Category Guide

| Section | Category Guidance Source |
|---------|-------------------------|
| When NOT to use | Category's "When NOT to use (common misfires)" |
| Inputs | Category's "Input contract" |
| Outputs | Category's "Output contract" + "DoD checklist" |
| Decision points | Category's "Decision points library" |
| Verification | Category's "Verification menu" |
| Troubleshooting | Category's "Failure modes & troubleshooting" |

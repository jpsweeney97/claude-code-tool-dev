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

## What to Pull from Category Guide

| Section | Category Guidance Source |
|---------|-------------------------|
| When NOT to use | Category's "When NOT to use (common misfires)" |
| Inputs | Category's "Input contract" |
| Outputs | Category's "Output contract" + "DoD checklist" |
| Decision points | Category's "Decision points library" |
| Verification | Category's "Verification menu" |
| Troubleshooting | Category's "Failure modes & troubleshooting" |

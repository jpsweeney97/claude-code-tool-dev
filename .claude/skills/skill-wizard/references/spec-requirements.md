# Spec Requirements Reference

Source: `skills-as-prompts-strict-spec.md` + `skills-semantic-quality-addendum.md`
Spec version: skills-as-prompts-strict-v1

## Requirement Levels

| Level | Meaning |
|-------|---------|
| **MUST** | Blocks approval; skill cannot proceed until fixed |
| **SHOULD** | Warns but allows continue; shown in compliance summary |
| **HIGH-MUST** | MUST for High-risk skills; WARN for Medium; skip for Low |
| **SEMANTIC** | Content quality check from semantic addendum |

## Core Invariants (8)

1. **All 8 sections present**: When to use, When NOT to use, Inputs, Outputs, Procedure, Decision points, Verification, Troubleshooting
2. **Objective DoD**: Outputs has checkable condition (not "verify it works")
3. **STOP/ask exists**: Procedure has explicit pause for missing inputs
4. **>=2 decision points**: With observable triggers (or justified exception)
5. **Quick check exists**: Verification has concrete check with expected result
6. **>=1 troubleshooting entry**: With symptoms, causes, next steps
7. **Assumptions declared**: Tools/network/permissions in Constraints
8. **Safe default**: Ask-first for breaking/destructive actions

## Tier 1: Normative Fail Codes

| Fail Code | Description |
|-----------|-------------|
| `FAIL.missing-content-areas` | One or more of 8 required sections absent |
| `FAIL.no-objective-dod` | Outputs lack objective, checkable DoD condition |
| `FAIL.no-stop-ask` | No explicit STOP/ask step for missing inputs |
| `FAIL.no-quick-check` | Verification lacks concrete quick check |
| `FAIL.too-few-decision-points` | <2 decision points without justified exception |
| `FAIL.undeclared-assumptions` | Uses tools/network/permissions without declaring |
| `FAIL.unsafe-default` | Destructive actions without ask-first |
| `FAIL.non-operational-procedure` | Procedure not numbered or generic advice |

## Tier 2: Semantic Anti-Patterns

| Anti-pattern | Detection Signal | Severity |
|--------------|------------------|----------|
| Placeholder language | "the inputs", "whatever is needed", "stuff" | FAIL |
| Proxy goals | "improve quality", "make better" without metric | FAIL |
| Subjective triggers | "if it seems", "when appropriate", "use judgment" | FAIL |
| Unbounded verbs | "clean up", "refactor", "optimize" without scope | WARN |
| Silent skipping | No "Not run (reason)" for skipped checks | WARN |
| Missing temptation | Troubleshooting lacks anti-pattern as temptation | WARN |

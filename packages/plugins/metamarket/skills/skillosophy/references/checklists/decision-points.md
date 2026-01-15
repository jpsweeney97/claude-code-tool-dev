# Decision Points Checklist

## Structural
- [MUST] At least 2 explicit decision points exist
- [MUST] Each uses "If... then... otherwise..." structure (or equivalent)

## Semantic
- [MUST] Each decision point names an observable trigger:
  - File/path exists or doesn't
  - Command output matches pattern
  - Test passes/fails
  - Grep finds/doesn't find pattern
  - Config contains/missing key
- [MUST] Triggers are not subjective ("if it seems", "when appropriate")
- [SHOULD] Covers common operational branches:
  - Tests exist vs not
  - Network available vs restricted
  - Breaking change allowed vs prohibited
  - Output format preference

## Exception Handling
- [MUST] If fewer than 2 decision points, justification is provided
- [MUST] Even with exception, at least one STOP/ask condition exists

## Anti-patterns
- [SEMANTIC] "Use judgment" as the decision criterion
- [SEMANTIC] Subjective triggers: "if it seems risky", "when appropriate"

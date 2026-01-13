# Procedure Checklist

## Structural
- [MUST] Steps are numbered (not bullets or prose)
- [MUST] Steps are executable actions (not generic advice)

## Semantic
- [MUST] At least one explicit STOP/ask step for missing inputs
- [MUST] At least one explicit STOP/ask step for ambiguity (Medium+ risk)
- [HIGH-MUST] Ask-first gate before any breaking/destructive/irreversible action
- [SHOULD] Order follows: inspect -> decide -> act -> verify
- [SHOULD] Prefers smallest correct change

## Command Mention Rule
- [MUST] Every command specifies expected result shape
- [MUST] Every command specifies preconditions (if non-obvious)
- [MUST] Every command has fallback for when it cannot run

## Mutating Action Gating
- [HIGH-MUST] Every mutating step has explicit ask-first gate
- [HIGH-MUST] Each ask-first gate names the specific risk
- [HIGH-MUST] Safe alternative offered (dry-run, read-only, or skip)
- [MEDIUM-MUST] Mutating steps are bounded by scope fence
- [MEDIUM-SHOULD] Rollback/undo steps provided for mutating actions

## Anti-patterns
- [SEMANTIC] "Use judgment" without observable decision criteria
- [SEMANTIC] Commands without expected outputs
- [SEMANTIC] Mutating steps without ask-first gates (High risk)

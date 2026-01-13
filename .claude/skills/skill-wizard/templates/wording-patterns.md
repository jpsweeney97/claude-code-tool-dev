# Wording Patterns (Appendix A)

Required patterns from the strict spec. Use verbatim or adapt while preserving intent.

## A.1 STOP/ask for Clarification

```
STOP. Ask the user for: <missing required input>. Do not proceed until provided.
```

```
STOP. The request is ambiguous. Ask: <clarifying question>. Proceed only after user confirms.
```

## A.2 Ask-first for Risky/Breaking Actions

```
Ask first: This step may be breaking/destructive (<risk>). Do not do it without explicit user approval.
```

```
If the user does not explicitly approve <action>, skip it and provide a safe alternative.
```

## A.3 Evidence-first (Debugging/Triage/Refactor)

```
Before suggesting a fix, gather evidence:
1. Read the failing test/error log
2. Identify the exact failure signature
3. Trace to the root cause
Only then propose a targeted fix with evidence.
```

## A.4 Minimal-change Default

```
Prefer the smallest correct change. Do not refactor surrounding code unless explicitly requested.
```

## A.5 Verification Requirements

```
Quick check: Run <command>. Expected: <exit code/output pattern>.
If the quick check fails, do not continue; go to Troubleshooting first.
```

## A.6 Offline/Restricted-Environment Fallback

```
If you cannot run <command> (missing <tool>, restricted permissions, no network):
STOP and ask the user to provide: <command output/logs>
OR perform manual inspection: <manual steps>
```

## A.7 Decision-point Phrasing

```
If <observable signal> is present, then <action>. Otherwise, <alternative>.
```

## Pattern Suggestions by Section

| Section | Patterns to Offer |
|---------|-------------------|
| Procedure | A.1, A.2 (High risk), A.3 (debugging/refactor), A.4 |
| Decision Points | A.1, A.2, A.7 |
| Verification | A.5 |
| Inputs (Constraints) | A.6 |
| Troubleshooting | Reference A.5 for "what to do if check fails" |

# Section Order Reference

## Dependency Graph

```
1. When to use       <- Standalone
       |
       v (references activation)
2. When NOT to use
       |
       v (defines boundaries)
3. Inputs            <- What skill needs
       |
       v (enables)
4. Outputs           <- What skill produces
       |
       v (referenced by)
5. Procedure         <- References 3, produces 4
       |
       v (contains)
6. Decision points   <- Branches in 5
       |
       v (checks)
7. Verification      <- Checks 4
       |
       v (handles failures from)
8. Troubleshooting   <- Failures in 5
```

## Order Rationale

| Position | Section | Depends On | Enables |
|----------|---------|------------|---------|
| 1 | When to use | None | Activation context for all |
| 2 | When NOT to use | 1 | Boundaries, STOP triggers |
| 3 | Inputs | 1, 2 | What procedure can use |
| 4 | Outputs | 3 | What procedure produces |
| 5 | Procedure | 3, 4 | Steps to execute |
| 6 | Decision points | 5 | Branches in procedure |
| 7 | Verification | 4, 5 | Checks outputs |
| 8 | Troubleshooting | 5, 7 | Handles failures |

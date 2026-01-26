# Answer Key: synthetic-code-for-review.py

Test material for reviewing-code skill validation.

## Flaw Summary

| ID | Category | Difficulty | Location | Description |
|----|----------|------------|----------|-------------|
| O1 | Security | Obvious | Line 16-17 | Hardcoded credentials (DATABASE_PASSWORD, API_SECRET) |
| O2 | Correctness | Obvious | Line 20 | Mutable default argument (filter_ids: list = []) |
| O3 | Security | Obvious | Line 39-40 | SQL injection vulnerability (string interpolation in query) |
| O4 | Robustness | Obvious | Line 54-55 | Silent exception swallowing (except Exception: return None) |
| O5 | Security | Obvious | Line 140-143 | Debug code printing credentials to stdout |
| M1 | Robustness | Medium | Line 33-34 | Resource leak (connection opened, never closed) |
| M2 | Security | Medium | Line 45 | Weak password hashing (MD5 is cryptographically broken) |
| M3 | Correctness | Medium | Line 59-68 | Race condition in check-then-act pattern |
| M4 | Security | Medium | Line 103-112 | No input validation on untrusted JSON data |
| M5 | Code Health | Medium | Line 127 | No __del__ or close() method for connection cleanup |
| H1 | Maintainability | Subtle | Line 72-90 | Low cohesion (method handles 3 unrelated actions) |
| H2 | Maintainability | Subtle | Line 93-98 | Magic numbers (100, 3600) without explanation |
| H3 | Maintainability | Subtle | Line 115-122 | Misleading name (get_or_create implies read-heavy, but always writes) |
| H4 | Code Health | Subtle | Line 125-130 | Inconsistent return types across similar methods |
| H5 | Code Health | Subtle | Line 134-137 | Dead code (function defined but never called) |

## Expected Detection by Review Quality

| Difficulty | Baseline (no skill) | With Skill |
|------------|---------------------|------------|
| Obvious (5) | Should find 3-5 | Should find 5 |
| Medium (5) | Should find 1-3 | Should find 4-5 |
| Subtle (5) | Should find 0-1 | Should find 3-5 |

## Process Compliance Markers

A thorough review using the reviewing-code skill should:

1. **Context Phase**: Read CLAUDE.md, explore codebase patterns
2. **Multiple Passes**: Yield% tracking, not one-pass "done"
3. **Dimension Coverage**: Check Correctness, Robustness, Security, Maintainability, Code Health at minimum
4. **Adversarial Pass**: Pre-mortem, "what if wrong?", scale stress
5. **Stratified Fixes**: Identify what's cosmetic vs behavior-changing
6. **Output Structure**: Report to artifact file, brief summary in chat

## Baseline Failure Patterns (Expected Without Skill)

- One-pass review declaring "looks good" or "found some issues"
- Missing subtle issues entirely
- No iteration/convergence tracking
- No adversarial thinking
- Inline full report instead of artifact + summary
- Skip context phase (reviewing code in isolation)

# Dimension Catalog

Complete definitions for all 31 code review dimensions across 9 categories.

## How to Use This File

- **During DISCOVER:** Consult to identify which dimensions apply
- **During EXPLORE:** Reference definitions to check each dimension correctly
- **Core process lives in SKILL.md** — this file is lookup reference only

---

## Category 1: Correctness (C1-C5)

*Does the code do what it should?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| C1 | Functional correctness | Does code implement requirements correctly? | Logic matches spec, expected outputs for inputs |
| C2 | Logic soundness | Are algorithms and conditionals correct? | Boolean logic, loop conditions, algorithm correctness |
| C3 | Edge case handling | Boundaries, empty inputs, nulls, overflow? | Min/max values, empty collections, null/undefined, integer overflow |
| C4 | Concurrency safety | Race conditions, deadlocks, thread safety? | Shared state access, lock ordering, atomic operations |
| C5 | State management | Valid state transitions, invariant preservation? | State machine correctness, invariants maintained across operations |

**Mandatory:** Yes — cannot skip

---

## Category 2: Robustness (R1-R4)

*How does the code handle things going wrong?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| R1 | Error handling | Appropriate exceptions, meaningful messages? | Catch specificity, error context, no silent failures |
| R2 | Failure recovery | Graceful degradation, retry logic, rollback? | Partial failure handling, cleanup on error, transaction rollback |
| R3 | Input validation | Validation at boundaries, sanitization? | Type checking, range validation, format validation, sanitization |
| R4 | Defensive programming | Assertions, preconditions, fail-fast? | Precondition checks, invariant assertions, early returns |

**Mandatory:** Yes — cannot skip

---

## Category 3: Security (S1-S5)

*Is the code safe from attack?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| S1 | Injection risks | SQL, command, XSS, path traversal? | Parameterized queries, command escaping, output encoding, path canonicalization |
| S2 | Authentication/Authorization | Auth checks, privilege escalation? | Auth on all endpoints, authorization checks, role validation |
| S3 | Data protection | Sensitive data exposure, encryption? | PII handling, encryption at rest/transit, secure logging |
| S4 | Dependency safety | Known vulnerabilities, supply chain? | Dependency versions, CVE checks, lock files |
| S5 | Secrets management | Hardcoded credentials, key exposure? | No hardcoded secrets, env vars, secure key storage |

**Mandatory:** Conditional — when code handles user input, authentication, or sensitive data

**Before marking N/A:** Verify code truly has no security surface. Injection points are often non-obvious.

---

## Category 4: Performance (P1-P4)

*Is the code efficient?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| P1 | Algorithmic efficiency | Time/space complexity appropriate? | Big-O analysis, unnecessary iterations, data structure choice |
| P2 | Resource usage | Memory leaks, connection pooling, caching? | Resource cleanup, pool management, cache invalidation |
| P3 | Database efficiency | N+1 queries, missing indexes, transaction scope? | Query patterns, index coverage, transaction boundaries |
| P4 | Scalability | Bottlenecks at 10x/100x scale? | Horizontal scaling, statelessness, queue depth |

**Mandatory:** Conditional — when code is on critical path or handles scale

---

## Category 5: Maintainability (M1-M6)

*Can others understand and modify this code?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| M1 | Readability | Clear naming, formatting, structure? | Variable names, function length, consistent formatting |
| M2 | Complexity | Cyclomatic complexity, nesting depth? | Branch count, nesting levels, cognitive load |
| M3 | Modularity | Single responsibility, cohesion, coupling? | Function/class focus, dependency direction, interface boundaries |
| M4 | Documentation | Comments accurate, useful, not stale? | Comment accuracy, API docs, inline explanations where needed |
| M5 | Consistency | Follows project patterns/conventions? | Naming conventions, error patterns, architectural alignment |
| M6 | Testability | Code structured for easy testing? | Dependency injection, pure functions, mockable interfaces |

**Mandatory:** Yes — cannot skip

---

## Category 6: Code Health (H1-H5)

*Is this code sustainable long-term?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| H1 | Technical debt | Shortcuts, TODOs, known compromises? | TODO comments, workarounds, documented debt |
| H2 | Code smells | Bloaters, couplers, dispensables? | Long methods, feature envy, dead code, duplicate code |
| H3 | Over-engineering | Unnecessary abstraction, premature optimization? | Unused flexibility, speculative generality, complex patterns for simple problems |
| H4 | Under-engineering | Missing abstractions, copy-paste, hardcoding? | Repeated patterns, magic numbers, missing encapsulation |
| H5 | Dead code | Unused code, unreachable paths, stale imports? | Unreferenced functions, commented code, unused imports |

**Mandatory:** Yes — cannot skip

**Note:** These "soft" issues compound over time. Code can "work" while being unhealthy.

---

## Category 7: Architecture (A1-A4)

*Does the code fit the system?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| A1 | Pattern alignment | Follows project architecture patterns? | Layer usage, component patterns, established conventions |
| A2 | Dependency direction | Dependencies flow correctly? No cycles? | Import direction, layer violations, circular dependencies |
| A3 | API design | Interface clarity, backwards compatibility? | Method signatures, versioning, deprecation |
| A4 | Separation of concerns | Layers respected, responsibilities clear? | Business logic separation, UI/data separation, cross-cutting concerns |

**Mandatory:** Conditional — when reviewing module/feature (not single file)

---

## Category 8: Testing (T1-T4)

*Is the code adequately tested?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| T1 | Coverage adequacy | Critical paths tested? | Happy path, error paths, edge cases |
| T2 | Test quality | Tests meaningful, not brittle? | Assertion quality, test isolation, determinism |
| T3 | Edge case coverage | Boundaries and errors tested? | Boundary values, error conditions, null handling |
| T4 | Test maintainability | Tests readable, DRY, well-organized? | Test naming, helper usage, fixture management |

**Mandatory:** Conditional — when tests exist or should exist

---

## Category 9: Type Design (TD1-TD4)

*Are types well-designed?*

| ID | Dimension | Question | Checks |
|----|-----------|----------|--------|
| TD1 | Encapsulation | Implementation details hidden? | Private fields, accessor methods, interface exposure |
| TD2 | Invariant expression | Types make illegal states unrepresentable? | Constrained constructors, validated inputs, type narrowing |
| TD3 | Usefulness | Types aid understanding and catch errors? | Semantic types, discriminated unions, type aliases |
| TD4 | Enforcement | Invariants enforced at construction? | Constructor validation, factory methods, builder patterns |

**Mandatory:** Conditional — when code defines types/classes/interfaces

---

## Priority Assignment

| Priority | Meaning | Examples |
|----------|---------|----------|
| P0 | Breaks correctness, security, or functionality | SQL injection, race condition, wrong algorithm |
| P1 | Degrades quality or maintainability | High complexity, missing tests, poor naming |
| P2 | Polish | Minor style issues, optional improvements |

---

## Cell Schema

For each dimension checked, record:

| Field | Required | Values |
|-------|----------|--------|
| ID | Yes | C1, R2, S3, etc. |
| Status | Yes | `[x]` done, `[~]` partial, `[-]` N/A, `[ ]` not started, `[?]` unknown |
| Priority | Yes | P0 / P1 / P2 |
| Evidence | Yes | E0 (assertion) / E1 (single source) / E2 (two methods) / E3 (triangulated) |
| Confidence | Yes | High / Medium / Low |
| Artifacts | If applicable | File paths, line numbers, code snippets |
| Notes | If applicable | What's wrong, proposed fix, fix type |

**Evidence requirements by stakes:**

- Adequate: E1 for P0 dimensions
- Rigorous: E2 for P0, E1 for P1
- Exhaustive: E2 for all, E3 for P0

**Rule:** Confidence cannot exceed evidence. E0/E1 caps confidence at Medium.

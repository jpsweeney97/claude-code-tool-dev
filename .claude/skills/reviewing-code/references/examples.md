# Examples

Detailed BAD/GOOD comparisons for code review execution.

## Example 1: Reviewing a utility module

**Scenario:** Review a file utils module (100 lines) before merging a PR.

### BAD: One-pass "looks fine" review

```
Claude scans the file once:
- "Functions are named clearly"
- "Has error handling"
- "Types look correct"

Reports: "Code looks good. Ready to merge."
```

**Why it's bad:**

- No Entry Gate — didn't assess stakes or select stopping criteria
- No Context Phase — didn't check project conventions or how module is used
- Single pass — Yield% is always 100% on pass 1, cannot exit
- Checked presence, not correctness — "Has error handling" ≠ "Error handling is correct"
- No adversarial thinking — didn't ask "How could this fail?"
- Skipped dimensions — no security, performance, or architecture review

**What was missed:**

- Error handling catches all errors but logs PII in stack traces (S3 violation)
- Function `parseConfig` throws on invalid input but callers don't handle it (R1 issue)
- `readFile` has synchronous I/O that blocks event loop (P1 issue)
- Magic number `86400` used without constant (H4 issue)

### GOOD: Iterative review with context and stratified fixes

**Entry Gate:**

- Target: `src/utils/file-helpers.ts`
- Stakes: Rigorous (utility code, moderate blast radius)
- Stopping: Yield% <10%
- Scope: C1-C5, R1-R4, M1-M6, H1-H5 mandatory; S1-S5 (handles file paths); T1-T4 (tests exist)

**Context Phase:**

- Read project CLAUDE.md: "All utilities must be pure functions where possible"
- Checked callers via grep: 12 files import this module
- Identified patterns: project uses `Result<T, Error>` for recoverable errors, throws for programmer errors
- Dependencies: `fs-extra`, `path`, no external services

**Pass 1:** Initial dimension sweep

Findings:
- C3 (Edge cases): P1 — `joinPaths` doesn't handle empty string input
- R1 (Error handling): P1 — `parseConfig` throws but doesn't match project `Result` pattern
- S1 (Injection): P1 — `readFile` accepts user input without path traversal check
- H4 (Under-engineering): P2 — Magic number 86400 for seconds-in-day

Yield% = 100% (Pass 1)

**Pass 1 FIX:**

| Finding | Fix Type | Action |
|---------|----------|--------|
| H4 magic number | Cosmetic | Applied: `const SECONDS_PER_DAY = 86400` → Tests pass ✓ |

**Pass 2:** Deeper check on P1 findings

- S1 investigation: Path traversal possible via `../` — elevated to P0
- R1 investigation: 3 of 12 callers don't handle thrown error — confirmed P1

Findings revised:
- S1: P0 — Path traversal vulnerability (was P1)

Yield% = 1/5 = 20%

**Pass 2 FIX:**

| Finding | Fix Type | Action |
|---------|----------|--------|
| S1 path traversal | Behavior-changing | Wrote failing test → Added `path.resolve` + prefix check → Test passes ✓ |

**Pass 3:** Convergence check

- No new dimensions
- C3 fix drafted (add empty string handling)
- R1 fix drafted (convert to Result pattern)

Yield% = 0/5 = 0%

**Pass 3 FIX:**

| Finding | Fix Type | Action |
|---------|----------|--------|
| C3 empty string | Simplification | Applied → Tests pass ✓ |
| R1 Result pattern | Behavior-changing (no coverage) | **Deferred** — needs user approval (affects 12 callers) |

**Adversarial Pass:**

- Security Mindset: "How would an attacker abuse this?" → Already caught path traversal
- Pre-mortem: "This caused an outage because..." → Config parsing failure cascades; adding circuit breaker to Extension Points
- Scale Stress: "What breaks at 10x?" → Synchronous file reads block event loop; noted as P1 for future async conversion

**Exit Gate:**

- Context: Complete ✓
- Coverage: All mandatory dimensions checked ✓
- Evidence: E2 for all P0, E1 for P1 ✓
- Disconfirmation: Tested path traversal fix with edge cases ✓
- Convergence: Yield% 0% < 10% ✓
- Adversarial: All lenses applied ✓
- Fixes: 3 applied, 1 deferred ✓

**Output:**

```
**Review complete:** src/utils/file-helpers.ts
**Findings:** P0: 1 | P1: 2 | P2: 1
**Fixes applied:** 3 (cosmetic: 1, simplification: 1, behavior: 1)
**Fixes deferred:** 1 (awaiting approval for Result pattern change)
**Key changes:** Fixed path traversal vulnerability; added empty string handling
**Full report:** `docs/audits/2024-01-15-file-helpers-code-review.md`
```

---

## Example 2: Module-level review with Explore agents

**Scenario:** Review the authentication module (15 files) after security concerns were raised.

### BAD: File-by-file without synthesis

```
Claude reviews each file independently:
- auth/login.ts: "Has password hashing"
- auth/session.ts: "Uses JWT"
- auth/middleware.ts: "Checks authorization"
...

Reports: "All files look secure."
```

**Why it's bad:**

- No Context Phase — didn't map how auth flows across files
- No cross-file analysis — didn't trace complete auth path
- Independent verdicts — missed interactions between components
- No security mindset — checked presence of features, not correctness

### GOOD: Coordinated exploration with synthesis

**Context Phase:**

Deployed two Explore agents in parallel:
1. "Map the authentication flow from login to protected endpoint"
2. "Identify all authorization check points and their trust boundaries"

**Synthesized findings:**
- Auth flow: login.ts → session.ts → middleware.ts → routes
- Gap: password reset flow bypasses rate limiting
- Gap: session.ts creates token but doesn't validate origin; middleware.ts checks token but trusts session claims without re-verification

**Review findings:**

- S2 (Authorization): P0 — Rate limit bypass in password reset
- S2 (Authorization): P0 — Token claims not re-verified at enforcement point
- A4 (Separation): P1 — Auth logic split across middleware and routes inconsistently

**Fix strategy:**

- Both P0s are behavior-changing with security implications → Write regression tests first
- A4 is refactoring → Defer pending architectural discussion

---

## Anti-Pattern Illustrations

### "Tests pass" without showing output

**BAD:**
> "Applied the fix. Tests pass. Moving on."

**GOOD:**
> "Applied path validation fix. Running tests..."
> ```
> $ npm test -- --grep "file-helpers"
> ✓ joinPaths handles empty string (2ms)
> ✓ readFile rejects path traversal attempts (5ms)
> ✓ parseConfig returns Result on invalid input (3ms)
>
> 3 passing (10ms)
> ```
> "Tests pass. Proceeding to next finding."

### Adversarial pass as checkbox

**BAD:**
> "Adversarial pass complete: Checked all lenses. No issues found."

**GOOD:**
> "**Pre-mortem:** 6 months later, this module caused an outage because:
> - A malformed config file crashed the service on startup (no graceful degradation)
> - The crash happened at 3am during a deployment; no one noticed until users reported
> - The fix was obvious (validate before parse) but wasn't caught because we only tested happy path
>
> **Action:** Adding config validation with fallback to last-known-good config. P1 finding added."

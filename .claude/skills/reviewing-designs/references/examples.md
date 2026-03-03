# Review Examples

Supporting reference for the [reviewing-designs](../SKILL.md) skill.

---

## BAD: Single-pass checkbox review

**Scenario:** Team created a design document for a new authentication system, derived from security requirements docs and API specifications.

Claude scans the document once, notes "has all the sections," checks that auth flows are mentioned, and reports: "Design looks complete. Ready for implementation."

**Why it's bad:**

- No Entry Gate — stakes not assessed, no stopping criteria
- Single pass — no iteration, no Yield% tracking
- Checked presence, not completeness — "auth flows mentioned" ≠ "auth flows fully specified"
- Skipped Behavioral Completeness — no check for decision rules, exit criteria, safety defaults
- No adversarial pass — didn't try to break the design
- No disconfirmation — accepted "looks good" without testing that conclusion
- Missed: Token refresh edge case undefined, error responses inconsistent with API spec, no rollback procedure for failed auth upgrades

## GOOD: Iterative review with early gate and bridge

**Entry Gate:**

- Target: `docs/designs/auth-system.md`
- Sources: `docs/requirements/security.md`, `docs/specs/api-v2.md`
- Stakes: Rigorous (implementation follows; moderate undo cost)
- Stopping: Yield% <10%

**AHG-5 Early Gate** (Rigorous → full 5 questions, exactly 3 hypotheses):

- Q1 → H1: "Auth system solves session management, but the real problem may be authorization granularity" [Target: D4, Anchor: §3.1]
- Q2 → ALT1: "JWT-only approach rejected too quickly — stateless auth eliminates Redis dependency" [Anchor: §2.3]
- Q3 → H2: "Fail-open on token validation timeout creates security hole — no fallback behavior specified" [Target: D6, Anchor: §4.2]
- Q4 → H3: "Token refresh during concurrent requests looks simple but creates race conditions" [Target: D10, Anchor: §4.1]
- Q5 → "Session store is load-bearing" (merged with H1 scope — already covered)

Bridge table populated: H1 (open, D4), H2 (open, D6), H3 (open, D10), ALT1 (open), ALT2 (NONE IDENTIFIED)

**Delta card #1 presented.** User confirms hypotheses, no changes.

**Pass 1 EXPLORE:** 3 P0 gaps, 5 P1 issues. Yield% = 100%.

**Pass 2 EXPLORE:** Deeper on D4-D6.

- H2 → tested: P0 — timeout defaults to fail-open [D6]
- H3 → tested: P0 — no mutex on concurrent refresh [D10]
- 1 P1 revised. Yield% = 30%.

**Pass 3 EXPLORE:** Document Quality (D13-D19). 1 P1 (vague error handling language). Yield% = 9%.

**Delta card #2:**

~~~
**Checkpoint 2: Loop converged** (3 passes, Yield% 9%)

Bridge updates:
- H1 (authorization granularity) → open (D4 partial — needs deeper check in adversarial)
- H2 (fail-open timeout) → tested: P0 [D6]
- H3 (refresh race condition) → tested: P0 [D10]
- ALT1 (JWT-only) → evaluated: not dominant — can't support token revocation

Net-new: P1 — vague error handling language [D14]

Totals: P0: 5 | P1: 7 | P2: 2

Anything to dig deeper on before the adversarial pass?
~~~

**Adversarial Pass** (bridge-first, then NET-NEW):

- A1 (Assumption Hunting): checks H1 → tested: authorization model also assumes flat permissions [H1, D4]
- A5 (Pre-mortem): "Token refresh race causes cascading failures" [H3 — extends, not NET-NEW]
- A6 (Steelman Alternatives): checks ALT1 → confirms "not dominant"
- A8 (Hidden Complexity): **NET-NEW** — token rotation during deployment creates 2-minute auth gap [D10]

**Delta card #3:** Bridge complete (H1 tested, H2 tested, H3 tested, ALT1 evaluated, ALT2 withdrawn). 1 NET-NEW finding. Informational closeout.

**Exit Gate:** Yield% <10%, bridge complete, all dimensions checked, disconfirmation attempted.

**Output:**

~~~
**Review complete:** auth-system.md
**Findings:** P0: 6 | P1: 7 | P2: 2
**Key issues:** Fail-open on timeout (H2→D6); refresh race condition (H3→D10)
**Full report:** `docs/audits/YYYY-MM-DD-auth-system-review.md`
~~~

**Why it's good:**

- Entry Gate established scope and stakes
- AHG-5 surfaced 3 hypotheses; 2 confirmed as P0s, 1 extended during adversarial pass
- Bridge table tracked hypotheses through loop — none forgotten
- Delta cards gave user 3 decision points during the review
- Adversarial pass evaluated bridge rows first (A1→H1, A5→H3, A6→ALT1), found 1 NET-NEW
- Iterative passes with Yield% tracking using framework formula
- Clear output with bridge connections visible

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

## GOOD: Iterative review with framework

**Entry Gate:**

- Target: `docs/designs/auth-system.md`
- Sources: `docs/requirements/security.md`, `docs/specs/api-v2.md`
- Stakes: Rigorous (implementation follows; moderate undo cost)
- Stopping: Yield% <10%

**Pass 1:** DISCOVER dimensions, assign priorities

- D1-D3 (Source Coverage): P0 — must capture all security requirements
- D4-D6 (Behavioral Completeness): P0 — auth failures need clear handling
- D7-D11 (Implementation Readiness): P1
- D12-D19 (Consistency + Document Quality): P1

**Pass 1 EXPLORE:** Found 3 P0 gaps, 5 P1 issues. Yield% = 100% (pass 1 special case)

**Pass 2 EXPLORE:** Deeper check on D4-D6, found 2 more P0 gaps (token refresh undefined, no rollback procedure), revised 1 P1 severity. Yield% = |Y=3| / max(1, |U=10|) = 30%

**Pass 3 EXPLORE:** Checked D13-D19 (Document Quality). Found 1 P1 issue (vague language in error handling). No new P0s, no revisions. Yield% = |Y=1| / max(1, |U=11|) = 9%

**Adversarial Pass:**

- Pre-mortem (A5): "Auth system fails in production because token refresh race condition wasn't specified" — added to findings
- Scale Stress (A2): "At 100x users, token validation becomes bottleneck" — noted as P1 concern

**Exit Gate:** Yield% <10%, all dimensions checked, disconfirmation attempted.

**Output:**

```
**Review complete:** auth-system.md
**Findings:** P0: 5 | P1: 7 | P2: 2
**Key issues:** Token refresh edge case undefined; no rollback for failed upgrades
**Full report:** `docs/audits/YYYY-MM-DD-auth-system-review.md`
```

**Why it's good:**

- Entry Gate established scope and stakes
- Iterative passes with Yield% tracking using framework formula
- Checked completeness, not just presence
- All dimension categories covered with appropriate priority
- Adversarial pass found additional issue (using lens IDs A5, A2)
- Clear output with P0 count prominent

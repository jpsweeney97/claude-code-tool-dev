# Severity, Leverage & Effort Rubric

Scoring rubric for the synthesis phase. Each finding is scored on three independent dimensions, then bucketed into one of four backlog sections. The bucket — not the severity alone — drives backlog ordering.

**Why three dimensions instead of a flat priority:** A P0 that takes 6 months to fix is not the same item as a P0 that takes 4 hours. A P2 with high leverage (unblocks many P1s) is sometimes the right thing to do first. Collapsing severity, leverage, and effort into a single priority hides the planning information that makes a backlog usable.

---

## Severity

How much pain is this debt causing today?

| Tier | Definition | Concrete signals |
|------|------------|------------------|
| **P0** | Actively bleeding — already costing on-call hours, blocking deploys, causing customer-visible failures, or stopping team velocity. | Open incident tied to this debt; "this is why we can't ship X"; oncall page count traced to it; CI red because of it. |
| **P1** | Compounding — adds friction to most changes in this area; cost grows roughly linearly with code growth. | "Every PR in this area touches this file"; review time inflated; bug clusters around it; team avoids the area. |
| **P2** | Latent risk — fine today but a known time bomb. | Dependency 2 majors behind with end-of-support announced; single-owner critical service; coverage gap in a path that's about to get more traffic. |
| **P3** | Cosmetic — readability or hygiene concern; remediate opportunistically. | "I'd rename this if I were touching it"; style inconsistency without functional impact; nice-to-have refactor. |

### Severity Inflation Check

If more than ~30% of findings are P0, the audit is probably inflating severity. Recalibrate: for each P0, name the specific cost being paid *today*. If you can't, demote.

Common inflation traps:
- "This will be bad someday" → that's P2, not P0
- "This is ugly and bothers me" → that's P3, not P1
- "If we ever decided to scale 100x" → that's P2 if the scaling event is real, watch-list if it's hypothetical

---

## Leverage

How much downstream pain does fixing this remove?

| Level | Definition | Concrete signals |
|-------|------------|------------------|
| **High** | Fixing this unblocks 2+ other findings, or removes a structural reason why other debt accumulates. | "If we fixed this, we could also fix X and Y"; "this is upstream of the architecture problem"; cross-category dependency. |
| **Medium** | Fixing this removes one specific downstream pain, or makes a related category materially easier to address. | Self-contained fix with one clear downstream beneficiary. |
| **Low** | Fixing this resolves only the named finding; no downstream effect. | Isolated improvement; clean local refactor; cosmetic cleanup. |

### How to Detect High Leverage

A finding is high-leverage when at least one of:
- Multiple other findings (in this audit) cite it as a contributing cause
- It's a missing seam that the architecture-drift auditor named, and code-health/test-debt findings would dissolve once the seam exists
- It's a dependency upgrade that unblocks operational AND test-debt findings simultaneously
- It's a knowledge artifact (ADR, runbook, ownership clarification) that resolves multiple "no one knows why" gaps

Always name the downstream beneficiaries in the finding when scoring high leverage. Unverified high-leverage claims inflate the backlog.

---

## Effort

Rough cost-to-remediate, expressed in calendar time at typical staffing.

| Size | Definition | Heuristic |
|------|------------|-----------|
| **Small** | Under 1 day of focused work for an engineer who knows the code. | One file, no API changes, no migration; or trivial config change. |
| **Medium** | 1-5 days; one engineer-week or less. | Multiple files; one module; possibly a migration with rollback. |
| **Large** | More than 1 week, OR requires planning/coordination before execution. | Cross-module; breaks consumers; requires migration with intermediate states; needs another team's input. |

### Effort Calibration

When uncertain between two sizes, **round up**. Underestimating effort distorts sprint planning more than overestimating does.

Effort estimates here are coarse on purpose. The audit is not delivering a project plan — it's delivering a *backlog with rough sizing* so a team can decide where to spend a sprint.

---

## Bucket Assignment

Every finding lands in exactly one of four buckets. The bucket is derived mechanically from severity × leverage × effort, with judgment as a tiebreaker.

| Bucket | Rule | What it means |
|--------|------|---------------|
| **quick-wins** | (P0 or P1) AND effort = small AND remediation is clear | An engineer could pick this up today and ship it in a day. Highest-ROI items. |
| **high-leverage** | leverage = high AND (effort = small OR medium) — regardless of severity | Investing here removes other items from the backlog. Sometimes worth doing *before* a higher-severity item. |
| **strategic** | (P0 or P1) AND effort = large | The pain is real but the fix isn't sprint-sized. Goes into roadmap planning, not the next sprint. |
| **watch** | P2 AND no high-leverage AND not currently bleeding | Latent. Track the trigger conditions; revisit later. P3 findings either get filed here or dropped entirely. |

### Tie-Break Order

When a finding could fit multiple buckets, apply in order:

1. **quick-wins beats high-leverage** when severity is P0 — fix the bleeding first.
2. **high-leverage beats quick-wins** when the quick-win is P1 and the high-leverage item unblocks 3+ other findings.
3. **strategic** never absorbs a small-effort item — by definition strategic items aren't sprint-sized.
4. **watch** is the bucket-of-last-resort for items that should be on record but aren't actionable now. If you find yourself putting many items in `watch`, ask whether they're really debt or just observations.

### Worked Examples

**Finding:** "Auth middleware swallows exceptions silently; oncall has 3 pages this month traced to this." → severity P0, leverage medium (operational reliability gets cleaner downstream), effort small. → **quick-wins** (P0 + small + clear).

**Finding:** "No dependency-injection seam between API layer and DB; every test re-implements DB stubs." → severity P1, leverage high (test-debt findings dissolve if the seam exists), effort medium. → **high-leverage** (high leverage trumps non-P0 severity).

**Finding:** "Service-X is bus-factor-1; original author rolled off the team 8 months ago." → severity P1, leverage medium, effort large (requires paired work, doc-writing, multiple PRs over weeks). → **strategic**.

**Finding:** "Three deps are one major version behind; no CVEs, no API breakage; project still on supported releases." → severity P2, leverage low, effort medium. → **watch** (trigger: "if any of these announces a CVE or EOL").

**Finding:** "Naming inconsistency: `User` and `Account` and `Customer` refer to the same concept in different layers." → severity P2-P3, leverage low (purely cosmetic), effort medium. → **watch** (unless the audit team is actively losing time to confusion, in which case demote to drop).

---

## Ordering Within Buckets

After bucketing, order within each bucket as follows:

### quick-wins

1. Order by severity (P0 before P1).
2. Within severity, order by leverage (high > medium > low).
3. Final tiebreaker: corroboration (`independent_convergence` > `cross_lens_followup_confirmation` > `singleton`).

### high-leverage

1. Order by leverage strength — count downstream findings unblocked.
2. Within leverage, order by severity (P0/P1 before P2).
3. Final tiebreaker: smaller effort first.

### strategic

1. Order by severity (P0 before P1).
2. Within severity, order by clarity of planning sequence (clearer sequence first — these are easier to slot into roadmap).
3. Final tiebreaker: cross-category corroboration.

### watch

Compact list, no internal ordering. Each entry: title + 1-line rationale + revisit trigger.

---

## Bucket Sanity Checks

Run these during synthesis. If any fail, revisit the scoring.

| Check | Threshold | If exceeded |
|-------|-----------|-------------|
| Quick-wins inflation | > 50% of findings are quick-wins | Effort is being underestimated; round up. |
| Strategic inflation | > 30% of findings are strategic | Severity is being inflated for items that may actually be P2/watch. |
| Empty quick-wins on high-stakes audit | 0 quick-wins on a `high` stakes audit | Either the codebase is unusually clean (rare), or the team is missing sprint-sized opportunities — re-check small-effort items in `watch`. |
| Excess watch list | > 40% of findings in watch | The audit is logging observations instead of debt. Either drop them or move to a "next-audit-cycle" note. |

---

## Synthesis Fidelity Check

Run before the durable record is confirmed, with the severity and bucket sanity checks. Scope: the `recommendation` and `anchor` of every backlog item — not the whole report. Compare each item against the ledger's `verbatim_anchor` / `verbatim_recommendation`.

| Check | Fail condition | If failed |
|-------|----------------|-----------|
| Identifier integrity | A code symbol, file path, or CLI flag in the report is absent from the source finding and unverified in the codebase | Restore from the verbatim field |
| Qualifier integrity | A distinguishing qualifier in the finding's recommendation is missing from the report item (e.g. request vs. response, "CI runs the full suite", "as of <date>", "manual/unscanned", "requires a contract or spec change") | Restore the qualifier |

Any fail blocks the durable record until the item is corrected. The fix is mechanical: the ledger verbatim field is authoritative over synthesis prose.

---

## Final Backlog Ordering

The final report ordering is by bucket, not by raw severity:

1. **Quick Wins** (`QW1`, `QW2`, ...) — start here, this is what to do in the next sprint
2. **High-Leverage Fixes** (`HL1`, `HL2`, ...) — consider these next; they unblock other items
3. **Strategic Items** (`ST1`, `ST2`, ...) — plan these; they don't fit in a sprint
4. **Watch List** (`WL1`, `WL2`, ...) — file these; revisit at named triggers

This ordering exists because a cleanup backlog is consumed *as planning input*. The reader's first question is "what can we ship next sprint?" — which is the quick-wins list. Strategic and watch sections answer different planning questions and belong further down, not interleaved with sprint-sized items by raw severity.

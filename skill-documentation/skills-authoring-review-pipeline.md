# Skills authoring + review pipeline (one-pager)
Section ID: pipeline.one-pager

This is a deterministic procedure for drafting and reviewing `SKILL.md` bodies using the reference documents in this directory.

## 1) Route the request
Section ID: pipeline.route

1. Choose the best-fit category using [skills-categories-guide.md](skills-categories-guide.md):
   - Use the decision tree first.
   - Confirm the category’s dominant failure mode matches the user’s request.
2. Record the stable key in the skill: `Retrieval key: category=<id>`.
3. Record the category’s `Typical risk:` as the initial risk tier candidate.

## 2) Draft the body using the strict spec skeleton
Section ID: pipeline.draft

1. Use the `Skill skeleton (1-page; REQUIRED content contract)` in [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) as the initial structure.
2. Fill the body to satisfy the `Required content contract (body)`.
3. Ensure the “command mention rule” is met for every command (expected result + preconditions + fallback).

## 3) Pick the risk tier (deterministic rule)
Section ID: pipeline.risk-tier

Use [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) → `Risk tier selection rule (guidance)`:

- Default to the category’s `Typical risk:`.
- Round up on uncertainty.
- Treat *any mutating step* as High risk until explicitly gated with ask-first/STOP + rollback/escape hatch where applicable.

## 4) Apply semantic minimums (quality pass)
Section ID: pipeline.semantic

Use [skills-semantic-quality-addendum.md](skills-semantic-quality-addendum.md) to make the skill:

- Unambiguous (clear success criteria and decision triggers),
- Executable (realistic steps and verifications),
- Honest about verification (explicit “Not run (reason)” protocol),
- Clear about certainty (“verified vs inferred vs assumed” when reporting outcomes).

Risk scaling: higher-risk tiers should satisfy more of the addendum’s dimensions.

## 5) Apply category + domain tightening
Section ID: pipeline.tighten

1. Use the chosen category block in [skills-categories-guide.md](skills-categories-guide.md):
   - Copy/paste the "Decision points library" where applicable.
   - Ensure the "DoD checklist (objective)" is actually objectively checkable.
2. If a domain annex applies, apply it as an extra constraint layer:
   - [skills-domain-annexes.md](skills-domain-annexes.md)

## 6) Review in the same layered order (recommended)
Section ID: pipeline.review-order

1. **Tier 1 (strict spec FAIL codes):** enforce required content areas and unsafe-default prevention.
2. **Tier 2 (semantic addendum):** enforce clarity, observability, and truthful verification reporting.
3. **Tier 3 (category/domain):** enforce specialized constraints (idempotency, evidence trails, rollback, approvals).


# Staffing Rules

Rules for emphasis map generation, reviewer suppression, and workload calibration.

## Emphasis Map

The emphasis map translates archetype weighting from `system-design-dimensions.md` into per-reviewer guidance. It tells each reviewer how much attention their categories deserve for this specific review.

### Emphasis Levels

| Level | Meaning | Reviewer behavior |
|-------|---------|-------------------|
| `primary` | Category is a primary concern for the inferred archetype | Deep-dive by default. Run sentinel questions, then select top lenses for analysis. |
| `secondary` | Category is a secondary concern | Run sentinel questions. Go deep only if a sentinel surfaces a concern or a cross-reviewer message arrives. |
| `background` | Category is not specifically weighted for this archetype | Quick sentinel check. Go deep only if something material surfaces. |
| `scope-inapplicable` | Category has no meaningful surface at the chosen scope | Skip. Note in coverage notes why the category does not apply. |

### Generation Algorithm

1. Identify the top 1-2 archetypes from the framing phase.
2. Look up each archetype in the weighting table (`system-design-dimensions.md`, "Weighting by System Type" section).
3. For each of the 8 categories:
   - If the category contains a **primary emphasis** (◆) lens for any identified archetype → `primary`
   - If the category contains a **secondary emphasis** (○) lens → `secondary`
   - If neither → `background`
   - If the category has no meaningful surface at the chosen scope → `scope-inapplicable`
4. When archetypes overlap, apply the highest emphasis level across all applicable archetypes (`primary` > `secondary` > `background`).

### Emphasis Map Format

Include in `frame.md` and reference in spawn prompts:

```markdown
## Emphasis Map

Archetype: User-facing API + Event-driven (medium confidence)
Scope: system
Stakes: high

| Reviewer | Categories | Emphasis |
|----------|-----------|----------|
| structural-cognitive | Structural, Cognitive | secondary, background |
| behavioral | Behavioral | primary |
| data | Data | secondary |
| reliability-operational | Reliability, Operational | primary, secondary |
| change | Change | background |
| trust-safety | Trust & Safety | primary |
```

When a reviewer owns two categories, they may have different emphasis levels. Both are listed. The reviewer calibrates depth per-category based on their individual emphasis.

## Suppression Rules

**Suppress a reviewer** only when ALL of their owned categories are `scope-inapplicable`.

Examples:
- A `change` reviewer may be suppressed when reviewing a brand-new system with no legacy, migration, or versioning surface.
- A `trust-safety` reviewer is suppressed only for purely internal, non-production analysis tools with no auth or sensitive data handling.

**Suppression is conservative.** If ANY owned category might have surface, do not suppress. When in doubt, spawn the reviewer at `background` emphasis — the sentinel check is cheap, and a skipped reviewer cannot be retroactively added during synthesis.

## Redirect Threshold

If **2 or more** reviewers would be suppressed, redirect to `system-design-review` (single-agent). The team approach adds coordination overhead; with that many categories inapplicable, the design is simple enough for a single-pass review.

**Redirect announcement:** "This design has [N] categories without meaningful surface at this scope. Redirecting to the single-agent design review for efficiency."

## Deep-Lens Cap

Each reviewer selects lenses for deep analysis from within their owned categories. The cap prevents scope creep while ensuring depth on material concerns.

| Condition | Cap |
|-----------|-----|
| Default | 4 lenses per reviewer |
| High stakes OR lead escalation | 5 lenses per reviewer |
| Background emphasis only | 2 lenses maximum (only if sentinel surfaces concern) |

### Promotion

A reviewer can promote a lens from `secondary` or `background` to deep analysis when:

1. A sentinel question surfaces a genuine concern (not just an observation)
2. A lateral message from another reviewer identifies a cross-cutting issue touching this category
3. A finding in one of their `primary` lenses has implications for a `secondary` lens

Record the promotion reason in the findings file. The lead verifies promotions during synthesis.

## Workload Distribution

Expected lens counts per reviewer, for planning purposes:

| Reviewer | Total Lenses | Typical Deep-Dive Count |
|----------|-------------|------------------------|
| structural-cognitive | 12 (7+5) | 4-5 |
| behavioral | 8 | 3-4 |
| data | 5 | 3-4 |
| reliability-operational | 10 (5+5) | 4-5 |
| change | 6 | 3-4 |
| trust-safety | 5 | 3-4 |

The two largest reviewers (structural-cognitive at 12, reliability-operational at 10) benefit most from `primary`/`secondary` emphasis to focus their attention. Single-category reviewers (behavioral at 8, change at 6) have natural scope limits.

# Staffing Rules

Rules for emphasis map generation, auditor suppression, deep-lens selection, and workload calibration.

## Emphasis Map

The emphasis map translates archetype weighting from [`debt-taxonomy.md`](debt-taxonomy.md) into per-auditor guidance. It tells each auditor how much attention their categories deserve for this specific audit.

### Emphasis Levels

| Level | Meaning | Auditor behavior |
|-------|---------|------------------|
| `primary` | Category is a primary concern for the inferred archetype(s) | Deep-dive by default. Run sentinel questions, then select top lenses for analysis. |
| `secondary` | Category is a secondary concern | Run sentinel questions. Go deep only if a sentinel surfaces a concern or a cross-auditor message arrives. |
| `background` | Category is not specifically weighted for this archetype | Quick sentinel check. Go deep only if something material surfaces. |
| `scope-inapplicable` | Category has no meaningful surface at the chosen scope | Skip. Note in coverage notes why the category does not apply. |

### Generation Algorithm

1. Identify the top 1-2 archetypes from the framing phase (see [`debt-taxonomy.md`](debt-taxonomy.md), "Debt Archetypes" section).
2. Look up each archetype in the weighting table ([`debt-taxonomy.md`](debt-taxonomy.md), "Archetype × Category Weighting" section).
3. For each of the 6 categories:
   - If the category has a **primary** (◆) emphasis for any identified archetype → `primary`
   - If the category has a **secondary** (○) emphasis → `secondary`
   - If neither → `background`
   - If the category has no meaningful surface at the chosen scope → `scope-inapplicable`
4. When archetypes overlap, apply the highest emphasis level across all applicable archetypes (`primary` > `secondary` > `background`).

### Emphasis Map Format

Include in `frame.md` and reference in spawn prompts:

```markdown
## Emphasis Map

Archetype: Long-lived application + Heavily integrated (high confidence)
Scope: system
Stakes: high

| Auditor | Categories | Emphasis |
|---------|-----------|----------|
| code-health | Code Health | primary |
| architecture-drift | Architecture Drift | secondary |
| dependency | Dependency & Supply Chain | primary |
| test-debt | Test Debt | secondary |
| operational | Operational & Observability | primary |
| knowledge | Knowledge & Documentation | primary |
```

Each auditor owns exactly one category, so the emphasis is one value per auditor. (Contrast with design-review-team, where some reviewers own two categories with potentially-different emphasis levels.)

## Suppression Rules

**Suppress an auditor** only when ALL of their owned subcategories are `scope-inapplicable`.

Examples:
- The `dependency` auditor may be suppressed when auditing a single hand-rolled module with no external imports.
- The `operational` auditor may be suppressed when auditing a pure library with no deploy surface.
- The `architecture-drift` auditor is usually NOT suppressed even at `subsystem` scope — drift between modules is still meaningful.

**Suppression is conservative.** If ANY owned subcategory might have surface, do not suppress. When in doubt, spawn the auditor at `background` emphasis — the sentinel check is cheap, and a skipped auditor cannot be retroactively added during synthesis.

### Scope-Driven Suppression Heuristics

| Scope | Likely suppressible | Almost never suppressible |
|-------|---------------------|---------------------------|
| `system` | (none typical — full audit) | All auditors typically apply |
| `subsystem` | `dependency` (if subsystem has no own deps); `operational` (if subsystem has no deploy surface) | `code-health`, `architecture-drift`, `test-debt`, `knowledge` |
| `interface` | `code-health`, `dependency`, `operational`, `knowledge` (often) | `architecture-drift` (interface boundaries), `test-debt` (contract tests) |

## Deep-Lens Cap

Each auditor selects lenses for deep analysis from within their owned category. The cap prevents scope creep while ensuring depth on material concerns.

| Condition | Cap |
|-----------|-----|
| Default (`primary` emphasis) | 4 lenses deep, plus sentinel check on remaining |
| High stakes OR lead escalation | 5 lenses deep |
| `secondary` emphasis | 3 lenses deep, plus sentinel check on remaining |
| `background` emphasis | 2 lenses maximum, only if a sentinel surfaces a concern |

### Promotion

An auditor can promote a lens from `secondary` or `background` to deep analysis when:

1. A sentinel question surfaces a genuine concern (not just an observation)
2. A lateral message from another auditor identifies a cross-cutting issue touching this category
3. A finding in one of their `primary` lenses has implications for a `secondary` lens

Record the promotion reason in the findings file. The lead verifies promotions during synthesis.

## Workload Distribution

Expected lens counts per auditor, for planning purposes:

| Auditor | Total Lenses | Typical Deep-Dive Count (primary) | Notes |
|---------|-------------|------------------------------------|-------|
| code-health | 6 | 4 | Heavy file-level reading; budget time for sampling |
| architecture-drift | 6 | 4 | Needs dependency-graph sketch first; budget tool/Bash time |
| dependency | 6 | 4 | Mostly manifest scanning; mechanical but breadth-heavy |
| test-debt | 6 | 4 | Needs to read test code AND production code AND CI history |
| operational | 6 | 4 | Spans repo (config) + runtime artifacts; the broadest evidence surface |
| knowledge | 6 | 4 | Spans docs + git history + cross-referencing — slowest per finding |

All six auditors own a single category with 6 lenses each. Unlike design-review-team (where two auditors carry double-category remits), the workload is balanced — but the *evidence-gathering cost* differs significantly across auditors. `dependency` is the fastest (mechanical manifest scans); `knowledge` and `architecture-drift` are the slowest (require synthesis of multiple sources).

## Stake-Based Workload Adjustment

| Stakes | Recommended approach |
|--------|----------------------|
| `low` | All auditors at `primary` emphasis run at the `secondary` cap (3 deep lenses). Speeds the audit; tradeoff is depth. |
| `medium` | Default caps apply. |
| `high` | Add `+1` to deep-lens cap for any `primary`-emphasis auditor. Also lower the suppression threshold (when in doubt, do NOT suppress). |

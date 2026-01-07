---
name: deep-synthesis
description: >
  Multi-repo value extraction and integration into your Claude Code configuration.
  Given N source repositories, extracts high-value patterns with justified confidence,
  synthesizes them into a coherent whole, and produces an actionable integration plan.
  Use when evaluating plugins, skills, or MCP servers to adopt.
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Deep Synthesis

Multi-repo value extraction and integration into your Claude Code configuration.

## When to Use

**Use when:**
- Evaluating Claude Code plugins/skills/MCP servers to adopt
- Learning how other developers configure their Claude setups
- Absorbing best practices from multiple sources into your config

**Don't use when:**
- Exploring a single codebase → use `deep-exploration`
- No intent to adopt → manual exploration
- Obvious best choice exists → adopt directly

## Triggers

- "Synthesize these repos into my config"
- "What should I adopt from these projects?"
- `/deep-synthesis`

## Quick Start

```text
0. Pre-Flight    → Analyze target, define scope, set calibration
1. Quick Triage  → Score repos (10 min each), filter to High/Medium
2. Exploration   → Run deep-exploration on each (batched)
3. Value ID      → Apply criteria, detect conflicts
4. Synthesis     → Resolve conflicts, verify compatibility
5. Planning      → Map to target changes, verify actionable
```

**Minimum checklist:**
```markdown
[ ] Pre-flight: Target analyzed, focus areas defined
[ ] Triage: Repos scored, High/Medium selected
[ ] Exploration: deep-exploration run on each
[ ] Value ID: Criteria applied, conflicts detected
[ ] Synthesis: Conflicts resolved, compatibility verified
[ ] Plan: Integration plan with evidence
```

## Exploration Output Contract

When running `deep-exploration` in Phase 2, request this output structure:

```text
## [Repo Name] Exploration Findings

### Standout Items
| ID | Item | Type | Evidence | Notes |
|----|------|------|----------|-------|
| E1 | [name] | [skill/hook/pattern/config] | [file:line or observation] | [brief note] |

### Red Flags
- [flag]: [evidence]

### Quality Signals
| Signal | Present | Evidence |
|--------|---------|----------|
| Tests | Y/N | [location or "not found"] |
| Types | Y/N | [observation] |
| Documentation | Y/N | [location] |
| Recent activity | Y/N | [last commit date] |
```

**Why structured:** Standardized format enables direct comparison in Phase 3 without normalization overhead.

## Inputs & Outputs

| Input | Required | Description |
|-------|----------|-------------|
| Source repos | Yes (2-6) | GitHub URLs or local paths |
| Focus areas | Yes | "hooks", "MCP servers", "skills", etc. |
| Calibration | Default: Medium | Light / Medium / Deep |

| Output | Location |
|--------|----------|
| Synthesis report | `docs/synthesis/YYYY-MM-DD-topic.md` |
| Integration plan | Within report |
| Conflict log | Within report or `templates/conflict-log.md` |

## Calibration

| Level | When | Agents/Repo | Conflict Resolution |
|-------|------|-------------|---------------------|
| **Light** | Low stakes, 2 repos, obvious choices | 2 | Author decides |
| **Medium** | Standard, 3-4 repos, some conflicts | 4 | Evidence-based |
| **Deep** | High stakes, 5-6 repos, complex | 4+ | Multiple rounds |

**Stakes:** Reversibility × Blast radius × Precedent × Complexity
Score 4-6 → Light | 7-9 → Medium | 10-12 → Deep

## Phases

| # | Phase | Key Action | Reference |
|---|-------|------------|-----------|
| 0 | Pre-Flight | Analyze `~/.claude/`, define scope | — |
| 1 | Triage | Score repos, filter to High/Medium | [triage-criteria](references/triage-criteria.md) |
| 2 | Exploration | Run `deep-exploration` with [output contract](#exploration-output-contract) | — |
| 3 | Value ID | Apply 4 criteria, classify findings | [value-criteria](references/value-criteria.md) |
| 4 | Synthesis | Resolve conflicts, verify compatible | [conflict-protocol](references/conflict-protocol.md) |
| 5 | Planning | Ordered changes with rollback | [compatibility-checklist](references/compatibility-checklist.md) |

## Abort Conditions

| Condition | Action |
|-----------|--------|
| All repos Low/Skip in triage | Abort: "nothing worth adopting" |
| All findings fail value criteria | Abort: "nothing meets criteria" |
| Unresolvable conflicts | Abort: "incompatible sources" |

## Anti-Patterns

| Avoid | Instead |
|-------|---------|
| Adopting without evidence | Require source citation |
| Ignoring conflicts | Document and resolve all |
| Skipping target analysis | Analyze `~/.claude/` first |
| Feature maximalism | Apply value criteria strictly |

## Integration

**Uses:**
- `deep-exploration` — Run on each repo (Phase 2)
- `episodic-memory:search` — Prior decisions (Phase 0)

**Pairs with:**
- `superpowers:brainstorming` — Define synthesis goals
- `superpowers:writing-plans` — Implementation after synthesis

## References

- [Triage Criteria](references/triage-criteria.md) — Phase 1 scoring
- [Value Criteria](references/value-criteria.md) — Phase 3 classification
- [Conflict Protocol](references/conflict-protocol.md) — Phase 4 resolution
- [Compatibility Checklist](references/compatibility-checklist.md) — Phase 4 verification
- [Evidence Hierarchy](references/evidence-hierarchy.md) — Confidence assignment

## Templates

- [Deliverable](templates/deliverable.md) — Final output structure
- [Triage Worksheet](templates/triage-worksheet.md) — Phase 1 working doc
- [Conflict Log](templates/conflict-log.md) — Phase 4 working doc

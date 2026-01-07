# Target Analysis Template

Complete this template in Phase 0 (Pre-Flight) before proceeding to Triage.

---

## Current Configuration

Inventory your existing Claude Code setup:

| Component | Location | Count | Notes |
|-----------|----------|-------|-------|
| CLAUDE.md | ~/.claude/CLAUDE.md | — | [lines, last modified] |
| Skills | ~/.claude/skills/ | | [list names] |
| Hooks | ~/.claude/hooks/ | | [list names] |
| Commands | ~/.claude/commands/ | | [list names] |
| Plugins | ~/.claude/plugins/ | | [list names] |
| MCP Servers | settings.json | | [list names] |

---

## Identified Gaps

What's missing or underperforming in your current setup?

| ID | Gap | Priority | Evidence |
|----|-----|----------|----------|
| G1 | | High/Medium/Low | [what prompted this] |
| G2 | | | |
| G3 | | | |

**Evidence types:** Pain point from usage, explicit user request, observed in other setups, episodic memory of past friction.

---

## Target Philosophy

Answer from existing CLAUDE.md or infer from patterns. Mark source.

| Dimension | Preference | Source |
|-----------|------------|--------|
| Minimal vs Maximal | | [stated/inferred from X] |
| Explicit vs Convention | | |
| Single-purpose vs Multi-use | | |
| Self-contained vs Integrated | | |

**If unknown:** Document "Unknown—will use skill default (minimal)" and note in Limitations.

---

## Focus Areas

Define what's in scope for this synthesis:

| Focus Area | In Scope | Explicitly Out of Scope |
|------------|----------|------------------------|
| | | |
| | | |

---

## Calibration

### Stakes Assessment

| Factor | Score (1-3) | Rationale |
|--------|-------------|-----------|
| Reversibility | | 1=easy revert, 3=hard to undo |
| Blast radius | | 1=isolated, 3=affects many things |
| Precedent | | 1=one-off, 3=sets pattern |
| Complexity | | 1=simple, 3=many moving parts |
| **Total** | | |

### Calibration Level

| Total Score | Level | Agents/Repo | Conflict Resolution |
|-------------|-------|-------------|---------------------|
| 4-6 | Light | 2 | Author decides |
| 7-9 | Medium | 4 | Evidence-based |
| 10-12 | Deep | 4+ | Multiple rounds |

**Selected:** [Light / Medium / Deep]

---

## Pre-Flight Checklist

Before proceeding to Phase 1 (Triage):

- [ ] Current configuration inventoried
- [ ] At least one gap identified with evidence
- [ ] Target philosophy documented (stated or inferred)
- [ ] Focus areas defined with explicit exclusions
- [ ] Calibration calculated and level selected

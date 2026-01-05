# Triage Criteria

Quick scoring guide for Phase 1: Quick Triage. Enables consistent repo scoring in ~10 minutes per repo.

---

## Scoring Matrix

| Factor | High (+2) | Medium (+1) | Low (0) | Skip (-1) |
|--------|-----------|-------------|---------|-----------|
| **Relevance** | Has all focus area components | Has some focus area components | Has 1 component | No relevant components |
| **Activity** | Commits in last 3 months | Commits in last year | Commits 1-2 years ago | No commits >2 years |
| **Quality signals** | Tests + types + docs | 2 of 3 | 1 of 3 | None |
| **Alignment** | Matches target philosophy | Neutral | Somewhat misaligned | Fundamentally opposed |

---

## Score Interpretation

| Total Score | Rating | Action |
|-------------|--------|--------|
| 6-8 | **High** | Full exploration |
| 3-5 | **Medium** | Full exploration |
| 1-2 | **Low** | Skip unless all others Low |
| ≤0 | **Skip** | Exclude from synthesis |

---

## Quick Checks (10 min max per repo)

```markdown
## Triage: [repo-name]

### Basic Info
- [ ] URL/Path: ____
- [ ] README exists and explains purpose: [ ] Yes [ ] No
- [ ] Last commit date: ____
- [ ] Stars/forks (if GitHub): ____

### Focus Area Components
- [ ] Skills: ____ (count)
- [ ] Hooks: ____ (count)
- [ ] MCP servers: ____ (count)
- [ ] CLAUDE.md patterns: [ ] Yes [ ] No
- [ ] Other: ____

### Quality Signals
- [ ] Tests directory exists
- [ ] TypeScript/type hints present
- [ ] Documentation beyond README

### Red Flags
- [ ] Archived repository
- [ ] "Work in progress" / "experimental" warnings
- [ ] Obvious security concerns
- [ ] Other: ____
```

---

## Triage Output Table

| Repo | Relevance | Activity | Quality | Alignment | Total | Rating | Proceed? |
|------|-----------|----------|---------|-----------|-------|--------|----------|
| [repo] | [+2/+1/0/-1] | [+2/+1/0/-1] | [+2/+1/0/-1] | [+2/+1/0/-1] | [sum] | [High/Medium/Low/Skip] | [✅/❌] |

---

## Decision Rules

1. **All High/Medium:** Proceed with all
2. **Mix of scores:** Proceed with High and Medium only
3. **All Low:** Proceed with best 2, note limited options
4. **All Skip:** Abort synthesis with explanation

---

## Rationale Documentation

For each excluded repo, document:

```markdown
**Excluded:** [repo-name]
**Score:** [total] ([breakdown])
**Reason:** [specific reason for exclusion]
```

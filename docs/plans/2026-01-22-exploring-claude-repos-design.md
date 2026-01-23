## Design Context: exploring-claude-repos & evaluating-extension-adoption

**Type:** Process/Workflow (both skills)
**Risk:** Low (exploration is read-only; evaluation produces recommendations)

### Problem Statement

Need to systematically harvest reusable patterns from Claude Code configuration repositories (skills, hooks, commands, agents, MCP configs, rules) and compare approaches across repos or against user's own setup. Existing `exploring-codebases` skill targets traditional source code architecture, not extension collections.

### Success Criteria

- Comprehensive inventory of extensions by type
- Prioritized highlights with actionable signals (novelty, quality, conflict, complexity)
- Comparative analysis against user's setup or other repos
- Clear handoff to evaluation for adoption decisions
- Structured decisions with explicit trade-offs for adoption

### Two-Skill Architecture

| Skill | Framework | Purpose |
|-------|-----------|---------|
| `exploring-claude-repos` | Framework for Thoroughness | Discover and document extensions with signals |
| `evaluating-extension-adoption` | Framework for Decision-Making | Decide whether to adopt specific findings |

**Handoff mechanism:**
- Exploration produces findings with stable IDs (F1, F2, ...)
- Each finding includes four signals (novelty, quality, conflict, complexity)
- Signals map to evaluation frame inputs
- Evaluation skill can also accept ad-hoc extensions without prior exploration

### Adoption Outcomes

| Outcome | Description |
|---------|-------------|
| Adopt as-is | Import directly into setup |
| Adapt | Import with specified modifications |
| Inspire | Learn from pattern, implement differently |
| Skip | Not worth adopting (with rationale) |
| Defer | Interesting but not now (with revisit trigger) |

### Compliance Risks

**Exploration:**
- Downgrading rigor without explicit calibration ("just a quick look")
- Abandoning loop under perceived time pressure
- Declaring low yield prematurely without systematic coverage
- Cherry-picking instead of systematic exploration

**Evaluation:**
- Skipping adversarial phase ("obviously should adopt")
- Not considering null options (Skip/Defer)
- Treating signals as decisions without criteria evaluation

### Edge Cases Addressed

- Huge repos (>50 extensions) → Scope down, don't abandon rigor
- Messy repos (non-standard structure) → Expand DISCOVER, flag structural issues
- Comparison mismatch (different philosophies) → Document difference explicitly
- Signal noise (too many "interesting" findings) → Priority tiers (P0/P1/P2)

### Rejected Approaches

- **Single skill with two phases:** Clean separation, but requires explicit second request for each evaluation. Adds friction.
- **Full integration every time:** Self-contained, but heavy output even when user just wants to browse.
- **Exploration with no signals:** Faster, but findings aren't immediately actionable for triage.

### Design Decisions

- **Distinct from exploring-codebases:** Different domain (config vs source), different dimensions (extension types vs architecture), different goal (harvest vs understand-to-contribute)
- **Four signals per finding:** Novelty, quality, conflict, complexity provide triage without full evaluation
- **Backlog as default coverage structure:** Extensions discovered as you go; better for unknown repos
- **Adequate as default stakes for evaluation:** Most extension adoptions are reversible
- **All five adoption outcomes as options:** Forces consideration of Skip/Defer, prevents action bias

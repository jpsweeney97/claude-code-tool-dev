---
name: deep-exploration
description: >
  Rigorous, comprehensive exploration methodology for understanding complex systems.
  Deploys parallel agents with four perspectives, cross-validates findings, and produces
  evidence-based deliverables with full coverage tracking. Use when you need to thoroughly
  understand what exists, how it works, where it falls short, and what to do next.
license: MIT
metadata:
  version: 1.2.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Deep Exploration

Rigorous methodology for exploring complex systems—codebases, architectures, documentation sets, or any domain where thorough understanding matters.

## When to Use

Use deep-exploration when:
- You need comprehensive understanding before making decisions
- Ad-hoc exploration has failed or feels unreliable
- The system is complex enough that you might miss things
- Findings must be evidence-based and verifiable
- Others need to trust or reproduce your exploration

Do not use when:
- Quick answer suffices (use Explore agent directly)
- Scope is narrow and well-defined (use targeted search)
- Time pressure prohibits rigor (acknowledge the tradeoff)

## Quick Start

```text
1. Pre-Flight    → Gather existing knowledge, define scope
2. Deploy Agents → Four perspectives explore in parallel
3. Cross-Validate → Reconcile findings, resolve conflicts
4. Synthesize    → Produce deliverable with evidence
```

**Minimum viable exploration:**
```markdown
[ ] Pre-flight: Searched episodic memory, defined scope
[ ] Agents: Deployed 4 perspectives (Inventory, Patterns, Docs, Gaps)
[ ] Cross-validation: Compared findings, resolved conflicts
[ ] Deliverable: Coverage matrix filled, findings evidenced
```

## Triggers

- "Explore this thoroughly"
- "I need to understand this system completely"
- "Comprehensive exploration of..."
- "Deep dive on this codebase"
- "Map out this system"
- `/deep-exploration`

## Calibration

Match rigor to stakes:

| Level | When | Agents | Cross-Validation | Time |
|-------|------|--------|------------------|------|
| **Light** | Low stakes, time pressure | 2 (Inventory + Gaps) | Minimal | Fast |
| **Medium** | Standard exploration | 4 (all perspectives) | Full | Moderate |
| **Deep** | Critical decisions, audits | 4 + specialists | Multiple rounds | Extended |

Default: **Medium**

---

## The Four Phases

### Phase 0: Pre-Flight

**Purpose:** Gather existing knowledge before starting.

**Checklist:**
```markdown
[ ] Searched episodic memory for prior conversations
[ ] Listed existing analyses (if deep-analysis available)
[ ] Reviewed recent changes (git log, changelogs)
[ ] Defined scope with rationale
[ ] Set calibration level
[ ] Identified domain (codebase/docs/architecture/custom)
```

**Why this matters:** Skipping pre-flight means rediscovering known information and missing prior decisions.

**Tools:**
- `mcp__plugin_episodic-memory_episodic-memory__search` — Prior conversations
- `mcp__plugin_deep-analysis_deep-analysis__list_analyses` — Existing analyses
- `git log --oneline -20` — Recent changes

### Phase 1: Parallel Agent Deployment

**Purpose:** Explore from four perspectives simultaneously.

Deploy agents in a **single message with multiple Task tool calls**:

| Agent | Perspective | Primary Question |
|-------|-------------|------------------|
| **Inventory** | What exists | Everything enumerated? Counts accurate? |
| **Patterns** | How things relate | Conventions consistent? Architecture clear? |
| **Documentation** | What's claimed | Docs accurate? Intent recoverable? |
| **Gaps** | What's missing | Expected absent? Broken? Improvable? |

**Agent Requirements:**
- Model: `opus` (required for depth)
- Type: `Explore`
- Must cite evidence: file paths, line numbers, examples
- Must report negative findings: what was looked for but not found
- Must label confidence: certain/probable/possible/unknown

**Prompt Template:** See [references/agent-prompts.md](references/agent-prompts.md)

**Coverage Matrix:** See [references/coverage-matrices.md](references/coverage-matrices.md)

### Phase 2: Cross-Validation

**Purpose:** Reconcile findings across agents.

**Process:**
1. Compare component counts (Inventory ↔ Patterns ↔ Docs)
2. Identify conflicting findings
3. For each conflict:
   - Investigate with targeted queries
   - Determine which finding is correct
   - Document resolution
4. Update confidence levels based on cross-validation

**Conflict Resolution Protocol:**
```markdown
Conflict: [Agent A says X, Agent B says Y]
Investigation: [What was checked]
Resolution: [Which is correct and why]
Evidence: [Source citation]
```

### Phase 3: Synthesis

**Purpose:** Produce final deliverable.

**Actions:**
1. Merge findings into unified document
2. Fill coverage matrix completely
3. Rank opportunities by impact
4. Write methodology section for reproducibility

**Deliverable Structure:** See [references/deliverable-template.md](references/deliverable-template.md)

---

## Evidence Requirements

Every finding must include:

| Field | Required | Description |
|-------|----------|-------------|
| **Claim** | Yes | What was found |
| **Source** | Yes | File:line or specific location |
| **Confidence** | Yes | Certain / Probable / Possible / Unknown |
| **Verification** | For high-impact | How confirmed, what cross-referenced |
| **Negative** | When applicable | What was looked for but not found |

**Confidence Levels:**

| Level | Meaning | Evidence Required |
|-------|---------|-------------------|
| **Certain** | Directly observed, multiple sources confirm | Primary evidence + cross-reference |
| **Probable** | Strong evidence, no contradictions | Primary evidence |
| **Possible** | Some evidence, gaps remain | Secondary evidence or inference |
| **Unknown** | Looked but didn't find conclusive evidence | Documented search |

---

## Completion Criteria

Before claiming exploration complete:

| Criterion | Verification |
|-----------|--------------|
| Coverage matrix filled | No cells marked '?' |
| Findings evidenced | Sample audit passes |
| Cross-validation done | Conflict log complete |
| Negative findings documented | Section populated |
| Methodology reproducible | Process documented |
| Deliverable complete | All sections filled |

**Red Flags:**
- "Explored thoroughly" without coverage matrix
- "Found no issues" without defining what constitutes an issue
- "Everything looks good" without quality criteria
- Skipping pre-flight because task "seems simple"

---

## Framework for Rigor

This skill implements the [Framework for Rigor](~/.claude/references/framework-for-rigor.md) (shared foundation for all deep-* skills).

### How Deep-Exploration Maps to the Framework

| Framework Phase | Deep-Exploration Phase | Key Actions |
|-----------------|------------------------|-------------|
| **Definition** | Pre-Flight | Define scope, set calibration, surface assumptions |
| **Execution** | Agents + Cross-Validation | Gather evidence, track coverage, reconcile findings |
| **Verification** | Synthesis | Verify coverage, state limitations, produce deliverable |

### Seven Principles Applied

| Principle | How Applied Here |
|-----------|------------------|
| **Appropriate Scope** | Pre-flight defines boundaries with rationale |
| **Adequate Evidence** | Every finding cites source with confidence level |
| **Sound Inference** | Cross-validation tests conclusions |
| **Full Coverage** | Coverage matrix tracks all dimensions |
| **Documentation** | Methodology section in deliverable |
| **Traceability** | File:line citations throughout |
| **Honesty** | Negative findings required; gaps explicitly documented |

### Calibration Alignment

Deep-exploration uses the framework's calibration system:
- **Light:** 2 agents, minimal cross-validation
- **Medium:** 4 agents, full cross-validation (default)
- **Deep:** 4+ agents, multiple rounds, adversarial review

For the full framework including limitations and failure modes, see [Framework for Rigor](~/.claude/references/framework-for-rigor.md).

---

## Domain Adaptation

### Codebase Exploration

Coverage dimensions:
- Components × Plugins/Modules
- Component types: files, classes, functions, tests, configs

Agent focus:
- Inventory: Enumerate all code artifacts
- Patterns: Coding conventions, architectural patterns
- Documentation: README accuracy, inline comments, API docs
- Gaps: Missing tests, dead code, undocumented APIs

### Documentation Exploration

Coverage dimensions:
- Documents × Sections
- Document types: guides, references, tutorials, API docs

Agent focus:
- Inventory: All documents enumerated
- Patterns: Consistent structure, terminology, style
- Documentation: Cross-references valid, links work
- Gaps: Missing topics, outdated content, broken links

### Architecture Exploration

Coverage dimensions:
- Components × Relationships
- Layers: presentation, business, data, infrastructure

Agent focus:
- Inventory: All components and connections
- Patterns: Architectural patterns, dependency directions
- Documentation: Architecture docs match reality
- Gaps: Undocumented services, hidden dependencies

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Single pass | Misses emergent scope | Five-pass structure |
| No coverage tracking | Unknown unknowns remain | Coverage matrix |
| Single perspective | Confirmation bias | Four perspectives |
| Assertions without evidence | Unreliable | Evidence requirements |
| Infinite exploration | Never completes | Calibration + criteria |
| Skipping pre-flight | Rediscovers known info | Always do pre-flight |

---

## Integration

**Before deep-exploration:**
- `superpowers:brainstorming` — Clarify what you're trying to understand

**After deep-exploration:**
- `superpowers:writing-plans` — Plan changes based on findings
- `deep-analysis:analyze` — Deep analysis of specific decisions

**During deep-exploration:**
- `episodic-memory:search` — Recall prior conversations
- `Explore` agents — The actual exploration work

---

## References

- [Framework for Rigor](~/.claude/references/framework-for-rigor.md) — 3 dimensions, 7 principles, calibration system (shared)
- [Bulletproofing Log](references/bulletproofing-log.md) — Full derivation of the framework (10-step process)
- [Agent Prompts](references/agent-prompts.md) — Detailed prompt templates for each perspective
- [Coverage Matrices](references/coverage-matrices.md) — Matrix templates by domain
- [Deliverable Template](references/deliverable-template.md) — Standard output structure
- [Synthesis Guidance](references/synthesis-guidance.md) — Key metrics, conflict detection, writing principles
- [Framework Extension Case Study](../../references/framework-extension-case-study.md) — Case study for deep-security-audit and skill family

---

## Changelog

### v1.2.0
- Added synthesis-guidance.md with writing principles from Elements of Style
- Added Key Metrics section to agent prompts for cross-validation
- Real-world validation on awesome-claude-code repository confirmed methodology effectiveness
- Added framework-extension-case-study.md for deep-security-audit and skill family roadmap

### v1.1.0
- Aligned with bulletproofed Framework for Rigor
- Added explicit mapping: skill phases → framework phases
- Added 7 principles application table
- Added reference to bulletproofing-log.md
- Updated framework section with new terminology (3 dimensions, 7 principles)

### v1.0.0
- Initial release
- Four-phase methodology (Pre-Flight, Agents, Cross-Validation, Synthesis)
- Four-perspective agents (Inventory, Patterns, Documentation, Gaps)
- Framework for Rigor as foundational reference
- Domain adaptation for codebase, documentation, architecture
- Calibration levels (light, medium, deep)

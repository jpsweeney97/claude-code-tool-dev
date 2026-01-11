---
name: deep-exploration
description: >
  Rigorous, comprehensive exploration methodology for understanding complex systems.
  Deploys parallel agents with four perspectives, cross-validates findings, and produces
  evidence-based deliverables with full coverage tracking. Use when you need to thoroughly
  understand what exists, how it works, where it falls short, and what to do next.
license: MIT
metadata:
  version: 1.4.0
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
- Understanding a structured documentation set (like API docs, extension references)

## When NOT to Use

- Quick answer suffices (use Explore agent directly)
- Scope is narrow and well-defined (use targeted search)
- Time pressure prohibits rigor (acknowledge the tradeoff)
- Single-file or single-function investigation
- User just wants a summary, not comprehensive coverage

## Non-Goals

This skill will NOT:
- Modify any files (read-only exploration)
- Execute code, run tests, or change state
- Make recommendations without cited evidence
- Expand scope beyond defined boundaries
- Suggest fixes or improvements during exploration (save for Opportunities list in synthesis)

If you feel compelled to modify something during exploration, add it to the Opportunities list instead.

## Quick Start

```text
1. Pre-Flight    → Gather existing knowledge, define scope
2. Deploy Agents → Four perspectives explore in parallel
3. Cross-Validate → Reconcile findings, resolve conflicts
4. Synthesize    → Produce deliverable with evidence
```

**Minimum viable exploration:**

```markdown
[ ] Pre-flight: Reviewed prior context, defined scope
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
- "Help me understand this documentation"
- "What does this reference cover?"
- `/deep-exploration`

---

## Inputs

**Required:**
- **Target scope**: What to explore (path, module, documentation set)
- **Exploration goal**: What you need to understand or decide

**Optional:**
- **Calibration level**: Light/Medium/Deep (default: Medium)
- **Existing knowledge**: Prior analyses, recent changes, known context
- **Quality criteria**: Standards to assess against (from CLAUDE.md or explicit)

**Constraints/Assumptions:**
- **Read-only:** This skill does not modify files, run code, or change state. All findings go in the report.
- Model: `opus` required for depth (agents use Explore type)
  - **If not using opus:** STOP and warn: "Deep-exploration requires opus for reliable multi-agent exploration. Current model may produce lower-quality results. Options: (1) Switch to opus and restart, (2) Proceed with reduced confidence and document limitation in report."
- Time: Medium calibration ~10-20 agent turns; Deep ~30+
- Network: Not required (local exploration only)
- Tools: Read, Glob, Grep, Task (for subagents) — no Write, Edit, or Bash

**STOP Conditions:**
- If target scope is unclear or too broad, **STOP** and ask: "What specific area should I explore? The entire repo, a module, or specific directories?"
- If exploration goal is missing, **STOP** and ask: "What decision or understanding are you trying to reach?"

---

## Outputs

**Artifacts:**
1. **Exploration report** — Findings organized by perspective (Inventory, Patterns, Documentation, Gaps)
2. **Coverage matrix** — Filled matrix proving comprehensive coverage
3. **Opportunities list** — Prioritized improvements with impact/effort ratings
4. **Conflict resolution log** — How agent disagreements were resolved

**Definition of Done (objective checks):**
- [ ] Coverage matrix contains no `[ ]` or `[?]` cells
- [ ] Every finding cites evidence (file:line or specific location)
- [ ] Negative findings documented (what was searched but not found)
- [ ] Conflict log exists if agents disagreed on any metric
- [ ] Opportunities ranked by impact (High/Medium/Low)

## Calibration

Match rigor to stakes:

| Level      | When                       | Agents               | Cross-Validation | Time     |
| ---------- | -------------------------- | -------------------- | ---------------- | -------- |
| **Light**  | Low stakes, time pressure  | 2 (Inventory + Gaps) | Minimal          | Fast     |
| **Medium** | Standard exploration       | 4 (all perspectives) | Full             | Moderate |
| **Deep**   | Critical decisions, audits | 4 + specialists      | Multiple rounds  | Extended |

Default: **Medium**

---

## The Four Phases

### Phase 0: Pre-Flight

**Purpose:** Gather existing knowledge before starting.

**Checklist:**

```markdown
[ ] Listed existing analyses (if deep-analysis available)
[ ] Reviewed recent changes (git log, changelogs)
[ ] Defined scope with rationale
[ ] Set calibration level
[ ] Identified domain (codebase/docs/architecture/custom)
```

**Why this matters:** Skipping pre-flight means rediscovering known information and missing prior decisions.

**Tools:**

- `git log --oneline -20` — Recent changes
- Project documentation (CLAUDE.md, README, changelogs)

### Phase 1: Parallel Agent Deployment

**Purpose:** Explore from four perspectives simultaneously.

Deploy agents in a **single message with multiple Task tool calls**:

| Agent             | Perspective       | Primary Question                            |
| ----------------- | ----------------- | ------------------------------------------- |
| **Inventory**     | What exists       | Everything enumerated? Counts accurate?     |
| **Patterns**      | How things relate | Conventions consistent? Architecture clear? |
| **Documentation** | What's claimed    | Docs accurate? Intent recoverable?          |
| **Gaps**          | What's missing    | Expected absent? Broken? Improvable?        |

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

| Field            | Required        | Description                             |
| ---------------- | --------------- | --------------------------------------- |
| **Claim**        | Yes             | What was found                          |
| **Source**       | Yes             | File:line or specific location          |
| **Confidence**   | Yes             | Certain / Probable / Possible / Unknown |
| **Verification** | For high-impact | How confirmed, what cross-referenced    |
| **Negative**     | When applicable | What was looked for but not found       |

**Confidence Levels:**

| Level        | Meaning                                     | Evidence Required                  |
| ------------ | ------------------------------------------- | ---------------------------------- |
| **Certain**  | Directly observed, multiple sources confirm | Primary evidence + cross-reference |
| **Probable** | Strong evidence, no contradictions          | Primary evidence                   |
| **Possible** | Some evidence, gaps remain                  | Secondary evidence or inference    |
| **Unknown**  | Looked but didn't find conclusive evidence  | Documented search                  |

---

## Decision Points

Explicit branching logic for common situations:

1. **If scope is ambiguous or unbounded**, then **STOP** and ask for clarification. Otherwise, proceed with defined scope.
   - *Observable triggers for "ambiguous":* User cannot name a specific deliverable, OR scope crosses >3 top-level directories without stated reason, OR exploration goal is vague (e.g., "understand everything").

2. **If agent findings conflict** (e.g., Inventory says 9 categories, Documentation says 10), then investigate with targeted queries before synthesizing. Do not average or ignore.

3. **If coverage matrix has `[ ]` cells after agents complete**, then deploy targeted follow-up queries to fill gaps. Do not mark exploration complete.

4. **If pre-flight reveals existing analysis** (from project docs, git history, or user-provided context), then incorporate findings and avoid re-exploring covered ground. Otherwise, start fresh.

5. **If calibration level is unclear**, then default to Medium. Ask user only if stakes suggest Deep is needed.
   - *Observable triggers for "stakes suggest Deep":* Security audit, architecture decision, user explicitly mentions "critical" or "thorough", or decision has irreversible consequences.

---

## Verification

### Quick Check (Process)

```bash
# After generating coverage matrix, verify no unexplored cells:
grep -c '\[ \]' deliverable.md  # Expected: 0
grep -c '\[\?\]' deliverable.md  # Expected: 0
```

If either returns non-zero, exploration is incomplete. Return to Phase 1 or 2.

### Outcome Check (Required)

Before marking exploration complete:
1. Sample 3 findings from the report
2. For each, verify: Does evidence exist at the cited location (file:line)?
3. If any sample fails: Return to agents and correct

**Success criteria:**
- Process check: `grep` commands return 0
- Outcome check: 3/3 sampled findings have valid evidence

### Deep Check (Optional)

- Sample 5+ findings across all sections
- Check that negative findings section has ≥3 entries
- Verify opportunities are ranked (not just listed)

### Skipped Verification Reporting

If any verification step cannot be run, report explicitly:

```text
Not run (reason): <why verification was skipped>
Run manually: `<command>`
Expected: <pattern>
```

Example:
```text
Not run (reason): deliverable.md not yet created
Run manually: grep -c '\[ \]' path/to/deliverable.md
Expected: 0 (no unexplored cells)
```

Do not silently skip verification. Every skipped check must be reported with manual instructions.

---

## Completion Criteria

Before claiming exploration complete:

| Criterion                    | Verification          |
| ---------------------------- | --------------------- |
| Coverage matrix filled       | No cells marked '?'   |
| Findings evidenced           | Sample audit passes   |
| Cross-validation done        | Conflict log complete |
| Negative findings documented | Section populated     |
| Methodology reproducible     | Process documented    |
| Deliverable complete         | All sections filled   |

**Red Flags:**

- "Explored thoroughly" without coverage matrix
- "Found no issues" without defining what constitutes an issue
- "Everything looks good" without quality criteria
- Skipping pre-flight because task "seems simple"

---

## Framework for Rigor

This skill implements the [Framework for Rigor](~/.claude/references/framework-for-rigor.md) (shared foundation for all deep-\* skills).

### How Deep-Exploration Maps to the Framework

| Framework Phase  | Deep-Exploration Phase    | Key Actions                                             |
| ---------------- | ------------------------- | ------------------------------------------------------- |
| **Definition**   | Pre-Flight                | Define scope, set calibration, surface assumptions      |
| **Execution**    | Agents + Cross-Validation | Gather evidence, track coverage, reconcile findings     |
| **Verification** | Synthesis                 | Verify coverage, state limitations, produce deliverable |

### Seven Principles Applied

| Principle             | How Applied Here                                       |
| --------------------- | ------------------------------------------------------ |
| **Appropriate Scope** | Pre-flight defines boundaries with rationale           |
| **Adequate Evidence** | Every finding cites source with confidence level       |
| **Sound Inference**   | Cross-validation tests conclusions                     |
| **Full Coverage**     | Coverage matrix tracks all dimensions                  |
| **Documentation**     | Methodology section in deliverable                     |
| **Traceability**      | File:line citations throughout                         |
| **Honesty**           | Negative findings required; gaps explicitly documented |

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

### Documentation Set Exploration

For structured documentation directories (API references, extension guides, product docs).

Coverage dimensions:

- Documents × Topics covered
- Documents × Completeness (intro, examples, troubleshooting)
- Cross-references × Validity

Agent focus:

- Inventory: All documents, their topics, hierarchy, frontmatter
- Patterns: Consistent structure, terminology, navigation patterns
- Documentation: Cross-references valid, examples runnable, claims accurate
- Gaps: Missing topics, broken links, orphaned pages, inconsistent terminology

**Example scope:** A directory like `docs/extension-reference/` with multiple subdirectories covering different extension types.

**Key questions:**
- What topics are covered? What's missing?
- Are cross-references valid and bidirectional?
- Is terminology consistent across documents?
- Do examples match current implementation?

---

## Troubleshooting

### Agents return conflicting counts

**Symptoms:** Inventory says 9 components, Documentation agent says 10, or similar discrepancies.

**Causes:**
- Agents searched different scopes
- One agent found items the other missed
- Documentation is outdated vs actual state

**Next steps:**
1. Check the Key Metrics table from each agent
2. Run targeted grep/glob to determine correct count
3. Document resolution in Conflict Log
4. Update the agent that was wrong

### Coverage matrix has persistent gaps

**Symptoms:** After agents complete, `[ ]` or `[?]` cells remain.

**Causes:**
- Scope was broader than agents covered
- Some dimensions weren't assigned to any agent
- Agent prompts didn't include all dimensions

**Next steps:**
1. Identify which dimension/component has gaps
2. Deploy targeted follow-up agent with specific scope
3. Mark `[-]` only if genuinely not applicable (document why)

### Exploration never converges

**Symptoms:** Keep finding new things, calibration level feels insufficient.

**Causes:**
- Scope too broad for chosen calibration
- No clear completion criteria defined upfront
- Scope creep during exploration

**Next steps:**
1. Re-read original goal and scope from pre-flight
2. Increase calibration level if stakes warrant it
3. Or narrow scope and document what's deferred

### Pre-flight seems like overhead

**Symptoms:** Temptation to skip pre-flight because task "seems simple."

**Causes:** Underestimating complexity; not recognizing existing knowledge.

**Next steps:**
1. Always do pre-flight—it takes 2 minutes
2. Check git log, CLAUDE.md, and ask user for prior context
3. If truly nothing relevant, document "No prior context found"

---

## Anti-Patterns

| Avoid                       | Why                     | Instead                |
| --------------------------- | ----------------------- | ---------------------- |
| Single pass                 | Misses emergent scope   | Four-phase structure   |
| No coverage tracking        | Unknown unknowns remain | Coverage matrix        |
| Single perspective          | Confirmation bias       | Four perspectives      |
| Assertions without evidence | Unreliable              | Evidence requirements  |
| Infinite exploration        | Never completes         | Calibration + criteria |
| Skipping pre-flight         | Rediscovers known info  | Always do pre-flight   |

---

## Integration

**Before deep-exploration:**

- `superpowers:brainstorming` — Clarify what you're trying to understand

**After deep-exploration:**

- `superpowers:writing-plans` — Plan changes based on findings
- `deep-analysis:analyze` — Deep analysis of specific decisions

**During deep-exploration:**

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

### v1.4.0

- Added Non-Goals section with explicit scope constraints during execution
- Added read-only constraint to Constraints section with explicit tool exclusions
- Added model fallback behavior: STOP and warn if not using opus
- Promoted outcome verification from optional Deep Check to required Outcome Check
- Added observable triggers for subjective decision points ("ambiguous", "unclear")
- Added Skipped Verification Reporting section with "Not run (reason)" template
- Audit compliance: Addressed all 6 SHOULD-level gaps from 2026-01-11 audit

### v1.3.0

- Added spec compliance: Inputs, Outputs (with objective DoD), Decision Points, Verification, Troubleshooting sections
- Added STOP/ask patterns for missing scope and ambiguous goals
- Added Documentation Set Exploration domain adaptation
- Added quick check verification (grep for unexplored cells)
- Converted Anti-Patterns to proper Troubleshooting format with symptoms/causes/fixes
- Updated triggers to include documentation exploration phrases

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

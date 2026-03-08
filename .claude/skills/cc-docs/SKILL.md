---
name: cc-docs
description: Orchestrate parallel claude-code-docs-researcher subagents for Claude Code documentation questions. Use this skill when a documentation question spans multiple extension types (hooks + skills + agents), requires comparing features across categories, needs comprehensive "how does X work" coverage, or when a single researcher's 3-8 search budget isn't enough. Routes questions through a tiered system: inline search for quick lookups, single researcher for focused deep dives, parallel researchers for cross-cutting questions. Synthesizes findings across researchers into unified answers with citations. Trigger this skill whenever you're about to answer a Claude Code documentation question that touches 2+ extension types, or when you're considering spawning a claude-code-docs-researcher agent. Even for simpler documentation questions, consult this skill — it tells you whether inline search is sufficient or whether delegation will produce a better answer.

allowed-tools:
  - mcp__claude-code-docs__search_docs
  - mcp__claude-code-docs__reload_docs
---

# CC Docs — Documentation Research Orchestrator

Orchestrate `claude-code-docs-researcher` subagents for Claude Code documentation questions. This skill handles routing (inline vs. delegate), parallel decomposition, cross-researcher synthesis, and follow-up orchestration.

## Routing: Choose the Right Tier

Before answering any Claude Code documentation question, classify it into one of three tiers.

### Tier 1: Inline Search

**When:** The question targets a single, specific detail with a known location.

- "What's the PreToolUse input schema?"
- "What frontmatter field controls tool access in skills?"
- "How do I reload the docs index?"

**Action:** Call `mcp__claude-code-docs__search_docs` directly. 1-2 searches. The `claude-code-docs` skill has the query patterns and BM25 optimization techniques — apply them.

### Tier 2: Single Researcher

**When:** The question requires deep exploration of one documentation area (3+ searches) but stays within a single domain.

- "How does the hook system work end-to-end?"
- "What are all the SKILL.md frontmatter options and what do they do?"
- "Walk me through creating and publishing a plugin"

**Action:** Spawn one `claude-code-docs-researcher` agent with the full question.

### Tier 3: Parallel Researchers

**When:** The question spans 2+ distinct documentation domains, compares features across types, or needs more than 8 searches to cover adequately.

- "Compare hooks, skills, and agents — when to use each?"
- "I'm building a plugin with hooks, agents, and an MCP server — what configuration does each need?"
- "How do all the extension types interact? What can reference what?"

**Action:** Decompose into independent research tasks and spawn parallel researchers.

### Decision Heuristic

Count the distinct documentation domains the question touches:

| Domains | Tier | Example |
|---------|------|---------|
| 1 specific detail | Tier 1 | "PreToolUse schema" |
| 1 broad area | Tier 2 | "hook system end-to-end" |
| 2+ independent areas | Tier 3 | "hooks vs skills vs agents" |

When uncertain between adjacent tiers, prefer the higher tier. Researchers are cheap (they run in parallel with Sonnet), and under-delegating produces shallow answers. Over-delegating at worst wastes a few seconds.

## Decomposition: Splitting Questions for Parallel Research

### Principles

1. **Split by documentation domain, not by sub-question.** "hooks and skills" → two researchers (one per domain). "Hook configuration and hook schemas" → one researcher (same domain, different aspects).

2. **Each researcher must be self-contained.** Its prompt should make sense without context from the other researchers. Include enough background that it can search and synthesize independently.

3. **2-4 researchers maximum.** More than 4 signals the question should be narrowed rather than further parallelized. Synthesis quality degrades with too many sources.

4. **Request parallel structure.** When comparing types, ask each researcher to cover the same aspects (configuration, capabilities, use cases, limitations). This makes synthesis straightforward because the outputs align dimension-by-dimension.

### Researcher Prompt Template

For each researcher, provide:

```
Research the following about Claude Code [DOMAIN]:

[SPECIFIC QUESTIONS FOR THIS DOMAIN]

Focus areas:
- [Key aspect 1]
- [Key aspect 2]
- [Key aspect 3]

Context: This research is part of a larger question about [OVERALL TOPIC].
The user wants to understand [WHAT THIS PART CONTRIBUTES TO THE WHOLE].
```

### Common Decomposition Patterns

**Comparison across types:**
"Compare X, Y, and Z" → one researcher per type, each asked to cover the same dimensions (definition, configuration format, triggering mechanism, capabilities, limitations, use cases). The parallel structure makes the comparison table almost write itself.

**Build/create questions:**
"How do I build a [thing with multiple components]?" → one researcher per component type, each covering both standalone configuration AND integration points with other components.

**"How does everything work together?":**
Map the question's scope to distinct documentation areas. Spawn one researcher per area. In synthesis, focus on the interfaces between areas — that's what the user actually wants to understand.

### Example: Comparison Question

User asks: "What's the difference between hooks, skills, and agents? When should I use each?"

Spawn 3 researchers simultaneously:

**Researcher 1:** "Research Claude Code hooks: what they are, available hook events, configuration format (settings.json), input/output schemas, decision control, use cases, and limitations. Cover both prompt-based and script-based hooks."

**Researcher 2:** "Research Claude Code skills: what they are, SKILL.md format, all frontmatter fields, triggering mechanism, allowed-tools, context fork, progressive disclosure, use cases, and limitations."

**Researcher 3:** "Research Claude Code agents/subagents: what they are, agent markdown format, all frontmatter fields, how they're spawned (Agent tool), tool restrictions, model selection, use cases, and limitations."

## Spawning Researchers

Use the Agent tool with `subagent_type: "claude-code-docs-researcher"`.

**Spawn all researchers in the same message.** This runs them concurrently. Don't spawn one, wait for results, then spawn the next — unless the second genuinely depends on the first's findings (rare).

Each researcher prompt should include:
1. The specific research question scoped to this domain
2. Which aspects to cover (so outputs across researchers are structurally parallel)
3. Brief context about the larger question (so the researcher can note cross-references it encounters)

## Synthesis: Merging Researcher Results

After all researchers return, synthesize their findings into a unified answer.

### Protocol

1. **Wait for all researchers.** Don't start the synthesis after the first one returns. Read all outputs to see the full picture before writing anything.

2. **Identify overlaps and contradictions.** Different researchers may return overlapping information (the hooks researcher mentions skills, the skills researcher mentions hooks). Deduplicate. If findings contradict, flag the contradiction explicitly — don't silently pick one side.

3. **Organize by the user's question, not by researcher.** The user asked "compare hooks vs skills" — structure the answer by comparison dimension (triggering, configuration, capabilities), not "here's what Researcher 1 found." The researcher boundaries are an implementation detail the user doesn't care about.

4. **Merge citations.** Collect chunk IDs from all researchers into a single citations section. Remove duplicates (different researchers may cite the same chunks).

5. **Consolidate gaps.** If multiple researchers report the same gap, mention it once. If one researcher found what another marked as a gap, the gap is filled — drop it.

### Synthesis Output

```
### Answer
[Unified answer organized by the user's question — not by researcher.
 Use comparison tables when the question is comparative.
 Lead with the direct answer, then expand with supporting detail.]

### Key Details
[Precise reference material: schemas, field names, configuration values.
 Use tables for structured data. This section is for people who need
 the exact syntax, not the conceptual explanation.]

### Citations
[Merged chunk IDs from all researchers, deduplicated.
 Format: file-slug#heading-slug]

### Gaps
[Topics the question touched on that no researcher could answer from
 documentation. Omit this section entirely if there are no gaps.]
```

## Follow-Up Orchestration

Sometimes initial findings raise questions that weren't part of the original decomposition.

### When to Spawn Follow-Up Researchers

- A researcher's "Gaps" section identifies a specific, searchable topic that matters for the answer
- Results reference a feature or concept that wasn't in the original question but is needed for completeness
- Two researchers returned contradictory information that a targeted follow-up could resolve

### When NOT to Follow Up

- The gap falls outside the user's question scope — mention it in Gaps, move on
- The gap is a known documentation limitation (the docs genuinely don't cover it)
- You've already spawned 4+ researchers total — report remaining gaps rather than recursing

### Follow-Up Process

1. Note specifically what's missing and why it matters for the answer
2. Spawn 1-2 narrowly-scoped follow-up researchers
3. Integrate follow-up findings into the existing synthesis
4. One round of follow-ups maximum. If follow-ups also have gaps, report them in the final Gaps section.

## Relationship to Other Components

| Component | Role | When to use it |
|-----------|------|----------------|
| `mcp__claude-code-docs__search_docs` | Raw search primitive | Tier 1 inline searches |
| `claude-code-docs` skill | BM25 query optimization techniques | Applied automatically by researchers; use directly for Tier 1 |
| `claude-code-docs-researcher` agent | Autonomous 3-8 search deep dive | Tier 2 and Tier 3 (spawned by this skill) |
| **This skill (`cc-docs`)** | Routing, decomposition, synthesis | The orchestration layer above all of the above |

## Constraints

- **Don't duplicate the researcher's job.** Route, decompose, synthesize. Don't re-search what a researcher already covered.
- **Don't over-decompose.** If one researcher can handle it in 8 searches, use one researcher. Parallelism is for genuinely independent domains.
- **Cite everything.** Every claim in the final synthesis traces to a chunk ID from researcher output.
- **Report gaps honestly.** If documentation doesn't cover something, say so. Don't backfill with training knowledge disguised as documentation findings.
- **Respect the search budget.** Tier 3 with 4 researchers × 8 searches = 32 searches. That's the practical ceiling. Design decompositions to stay well under it.

---
name: deep-analysis
description: >
  This skill should be used when the user asks to "analyze options", "evaluate trade-offs",
  "help me decide between X and Y", "what approach should we take", "analyze this architecture
  decision", or faces complex decisions with multiple valid approaches. Use for architectural
  choices, strategic trade-offs, technology evaluation, or any decision requiring systematic
  option evaluation. NOT for debugging (use systematic-debugging) or creative ideation
  (use brainstorming).
---

# Deep Analysis

A structured process for turning complex problems into well-reasoned decisions with documented rationale.

## When to Use

- Architectural decisions with multiple valid approaches
- Strategic trade-offs ("should we X or Y?")
- Technology or approach evaluation
- Decisions requiring systematic option evaluation

## When NOT to Use

- Debugging issues → use `systematic-debugging`
- Creative ideation → use `brainstorming`
- Simple questions with obvious answers
- Research without a decision to make

## Process Overview

The analysis follows 5 stages with checkpoints for user validation:

```
Stage 0: Prior Art Search
    ↓
Stage 1: Clarification
    ↓
Stage 2: Investigation (6 frameworks)
    ↓
Stage 3: Synthesis
    ↓
Stage 4: Document & Index
```

---

## Stage 0: Prior Art Search

Before starting new analysis, search for relevant past work.

### Keyword Extraction

Identify 3-5 key terms from the problem statement:
- Domain concepts (architecture, authentication, caching)
- Technologies mentioned (Redis, PostgreSQL, GraphQL)
- Problem types (performance, scalability, security)

### Search Strategy

**If MCP available** (check for `mcp__deep-analysis__search_analyses` tool):
1. Call `mcp__deep-analysis__search_analyses(query, project_path, limit=5)`
2. Pass current working directory as `project_path`

**If MCP unavailable:**
1. Note: "Semantic search unavailable, using basic search"
2. Search with Grep tool in:
   - `~/.claude/analyses/` (global)
   - `./docs/analysis/` (project-specific)

### Handle Results

**If relevant hits found:**
- Show summaries with dates and decisions
- Ask: "I found these related analyses. Build on one of these, or start fresh?"

**If no relevant analyses found:**
- Note: "No prior analyses found for this topic."
- Proceed to Stage 1

**If building on prior work:**
- Load that analysis as context
- Record in `builds-on` field of new document

---

## Stage 1: Clarification

Understand the problem before analyzing. Ask questions one at a time.

### Core Questions

1. What specifically are you trying to decide?
2. What constraints matter? (time, resources, compatibility, risk tolerance)
3. What have you already considered or tried?
4. What does success look like?

### Checkpoint

Summarize understanding:
> "So you're deciding [problem] with constraints [X, Y, Z], and success means [outcome]. Does this capture it?"

**If user confirms:** Proceed to Stage 2.

**If user pivots:** The question changed. Restart Stage 1 with new framing.

---

## Stage 2: Investigation

Explore the problem space using all 6 analytical frameworks. Apply every framework—this thoroughness is what distinguishes deep analysis from quick opinions.

### The 6 Frameworks

Apply each framework to the problem. See `references/frameworks.md` for detailed guidance on each.

1. **First Principles** — Strip away assumptions. What fundamental truths apply?

2. **Systems Thinking** — Map interconnections. What feedback loops and ripple effects exist?

3. **Inversion** — Flip the question. What would guarantee failure?

4. **Second-Order Thinking** — Follow the chain. If we do X, then what? And then?

5. **Trade-off Analysis** — Identify tensions. What values compete? What are we giving up?

6. **Pre-mortem** — Imagine failure. It's one year later and this failed. Why?

### Output

Produce 3-5 distinct approaches, each with:
- Brief description
- Key trade-offs
- Which frameworks support/oppose it

### Checkpoint

Present options:
> "These are the options I see: [list]. Any I'm missing? Any to rule out immediately?"

**If user suggests additional options:**
- Add to options list
- Apply frameworks to new option
- Re-present updated options

---

## Stage 3: Synthesis

Deep-dive on the most promising options (top 2-3).

### For Each Promising Option

1. **Implementation considerations** — What does execution look like?
2. **Risk assessment** — Likelihood and severity of failure modes
3. **Mitigation strategies** — How to reduce identified risks
4. **Second-order effects** — Downstream consequences
5. **Assumption stress-test** — What if key assumptions are wrong?

### Comparative Analysis

Create a decision matrix if helpful:

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| Risk      | Low      | Medium   | High     |
| Effort    | High     | Medium   | Low      |
| Reversibility | Easy | Hard    | Medium   |

### Checkpoint

> "Here's my analysis of the top options. Does this match your intuition? Any factors I'm weighting incorrectly?"

---

## Stage 4: Document & Index

Produce the final artifact.

### Save Preference

Before generating document:
> "Would you like me to save this analysis for future reference?"

**If user declines:**
- Provide comprehensive summary in conversation
- Note: "Analysis complete. Not saved to disk."
- End process

### Document Generation

If saving, generate markdown document following the format in `references/document-spec.md`.

### Determine Save Location

- **If in a git repo/project:** `./docs/analysis/YYYY-MM-DD-<slug>.md`
- **If not in project:** `~/.claude/analyses/YYYY-MM-DD-<slug>.md`
- User can override: "Save this globally instead"

### Save and Index

1. Create directory if needed
2. Write document using Write tool
3. If MCP available, call `mcp__deep-analysis__index_analysis(path)`
4. Confirm: "Analysis saved and indexed at `<path>`"
5. Note: "Consider committing this analysis to preserve decision history."

### Pause Handling

If user needs to pause before decision:
- Save with `status: draft`
- Omit `decision` field
- Resume later by loading the draft

---

## Graceful Degradation

The skill works with or without the MCP server:

| Component | With MCP | Without MCP |
|-----------|----------|-------------|
| Prior art search | Semantic search | Grep fallback |
| Indexing | Automatic | Skip (document still saved) |
| Core analysis | Full process | Full process |

Always note when falling back: "Semantic search unavailable, using basic search."

---

## Reference Files

### Detailed Frameworks

For comprehensive guidance on applying each analytical framework:
- **`references/frameworks.md`** — The 6 frameworks with examples and common pitfalls

### Document Format

For the complete output specification:
- **`references/document-spec.md`** — Required fields, structure, and template

---

## Quick Reference

### Stage Checkpoints

| Stage | Checkpoint Question |
|-------|---------------------|
| 1 | "Does this capture it?" |
| 2 | "Any options I'm missing? Any to rule out?" |
| 3 | "Does this match your intuition?" |
| 4 | "Would you like me to save this?" |

### MCP Tools

| Tool | Purpose |
|------|---------|
| `search_analyses` | Find relevant past analyses |
| `index_analysis` | Add new analysis to index |
| `list_analyses` | Browse indexed analyses |
| `remove_analysis` | Remove from index |
| `rebuild_index` | Rebuild entire index |

### Save Locations

| Context | Path |
|---------|------|
| In project | `./docs/analysis/YYYY-MM-DD-slug.md` |
| Global | `~/.claude/analyses/YYYY-MM-DD-slug.md` |

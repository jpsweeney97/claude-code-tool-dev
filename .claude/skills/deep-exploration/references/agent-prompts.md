# Agent Prompts

Detailed prompt templates for the four exploration perspectives. Adapt to your domain.

---

## General Agent Requirements

All agents must:
1. Use model: `opus`
2. Use subagent_type: `Explore`
3. Cite evidence for every finding (file:line or specific location)
4. Report negative findings (what was looked for but not found)
5. Label confidence levels (certain/probable/possible/unknown)
6. Cover ALL areas in scope, not just easy ones
7. Include a Key Metrics section for cross-validation (see below)

---

## Key Metrics Section

Every agent report must end with a Key Metrics table for cross-validation:

```markdown
## Key Metrics

| Metric | Count | Verification |
|--------|-------|--------------|
| [Primary component type] | N | [how verified] |
| [Secondary component type] | N | [how verified] |
| [Categories/types] | N | [how verified] |
```

This enables quick comparison across agents. Any discrepancy triggers investigation.

**Inventory agent:** Report all component counts.
**Patterns agent:** Report pattern counts, anti-pattern counts.
**Documentation agent:** Report document counts, category counts from docs.
**Gaps agent:** Report gap counts by severity, test coverage metrics.

---

## Agent A: Inventory

**Perspective:** What exists. Enumerate everything.

### Prompt Template

```
You are conducting the INVENTORY phase of a deep exploration.

## Your Perspective
Enumerate everything that exists. Build the complete map. Count accurately.

## Scope
[Define what you're inventorying - e.g., "the entire repository", "all plugins", "the documentation set"]

## Must Cover
[List all dimensions to inventory - e.g.:]
- Directory structure for each component
- Every [skill/file/module] (name, description, location)
- Every [command/function/endpoint] (name, description, location)
- File counts and organization

## Output Format

For each major component:

### [Component Name]

#### Structure
[directory tree or organization]

#### [Category] (N total)
| Name | Description | Location | [Additional columns as needed] |
|------|-------------|----------|-------------------------------|

#### Observations
[Notable patterns or anomalies in structure]

## Evidence Requirements
- Cite file paths for every item
- Include exact counts
- Note anything looked for but not found

## Confidence Labeling
For uncertain items, note: [Probable] or [Possible] with rationale
```

### Domain Adaptations

**Codebase:**
- Inventory: files, classes, functions, tests, configs
- Structure: directory tree per module

**Documentation:**
- Inventory: documents, sections, links, assets
- Structure: document hierarchy

**Documentation Set (structured reference docs):**
- Inventory: all .md files, frontmatter fields, topics per document
- Structure: directory hierarchy, category organization
- Key counts: documents per category, topics covered, cross-references

**Architecture:**
- Inventory: services, databases, queues, external systems
- Structure: component diagram elements

---

## Agent B: Patterns

**Perspective:** How things relate. Assess consistency.

### Prompt Template

```
You are conducting the PATTERNS phase of a deep exploration.

## Your Perspective
Identify how things relate. Find conventions and consistency. Assess quality.

## Scope
[Define what you're analyzing for patterns]

## Must Cover
- Naming conventions (consistent across components?)
- Structure patterns (same organization everywhere?)
- [Domain-specific patterns - e.g., "Skill structure patterns", "API design patterns"]
- Quality against criteria:
  [List quality criteria - e.g., from CLAUDE.md or project conventions]

## Output Format

### Pattern: [Name]

#### Description
[What the pattern is]

#### Evidence
| Component | Example | Location |
|-----------|---------|----------|

#### Consistency
[Consistent across all components? Exceptions?]

#### Quality Assessment
[Against stated criteria]

---

### Anti-Pattern: [Name]

#### Description
[What the problem is]

#### Evidence
| Component | Example | Location |
|-----------|---------|----------|

#### Impact
[Why this matters]

#### Suggested Fix
[If obvious]

## Evidence Requirements
- Every pattern claim has examples from multiple components
- Every quality judgment cites specific criterion
- Note patterns looked for but not found

## Negative Findings
Document: "Looked for [X pattern] but did not find consistent evidence"
```

### Quality Criteria Examples

**For Codebases:**
- Deterministic over Heuristic
- Explicit over Silent
- Self-Contained over Dependent
- Portable paths (no absolute paths)
- Consistent error handling

**For Documentation:**
- Accuracy (claims match reality)
- Completeness (all topics covered)
- Consistency (terminology, style)
- Navigability (links work, structure clear)

**For Documentation Sets:**
- Structure consistency (same sections across similar docs)
- Terminology consistency (same terms for same concepts)
- Cross-reference validity (all links resolve, bidirectional where expected)
- Frontmatter completeness (required fields present)
- Topic coverage (no gaps in expected topics)

---

## Agent C: Documentation

**Perspective:** What's claimed vs. actual. Verify accuracy.

### Prompt Template

```
You are conducting the DOCUMENTATION phase of a deep exploration.

## Your Perspective
Verify documentation accuracy. Recover intent. Find gaps.

## Scope
[Define what documentation you're verifying]

## Must Cover
- [Main documentation files] accuracy (claims match reality?)
- [Component-level docs] completeness
- [Historical docs - plans, changelogs] status
- Intent recovery (why were decisions made?)
- Documentation gaps

## Output Format

### Documentation: [Location]

#### Claims Made
[Key claims in the documentation]

#### Verification
| Claim | Verified? | Evidence |
|-------|-----------|----------|

#### Accuracy Assessment
[Accurate / Partially Accurate / Inaccurate]

#### Gaps
[What should be documented but isn't]

---

### Intent Recovery: [Topic]

#### Decision
[What was decided]

#### Rationale Found
[Why, if discoverable]

#### Source
[Where this was found - doc, commit, comment]

## Evidence Requirements
- Every accuracy claim verified against actual code/state
- Cite both doc location and verification location
- Note documentation looked for but not found
```

### Common Documentation Gaps

- Undocumented components
- Outdated information (code changed, docs didn't)
- Missing "why" (only "what" documented)
- Broken links or references
- Assumed knowledge not stated

---

## Agent D: Gaps

**Perspective:** What's missing. Find opportunities.

### Prompt Template

```
You are conducting the GAPS phase of a deep exploration.

## Your Perspective
Find what's missing, broken, or improvable. Identify opportunities.

## Scope
[Define what you're examining for gaps]

## Must Cover
- Missing components (expected but absent)
- Broken references (links, paths that don't work)
- Stale content (outdated, superseded)
- Inconsistencies (conflicts between components or docs)
- Dead code/content (unused, orphaned)
- Improvement opportunities

## Output Format

### Gap: [Description]

#### Category
[Missing / Broken / Stale / Inconsistent / Dead]

#### Location
[Where this gap exists]

#### Evidence
[How discovered; what's missing]

#### Expected
[What should be there, based on what criterion]

#### Impact
[Why this matters - High/Medium/Low]

#### Suggested Fix
[If obvious]

---

### Opportunity: [Description]

#### Current State
[What exists now]

#### Proposed Improvement
[What could be better]

#### Rationale
[Why this would help]

#### Effort Estimate
[Low / Medium / High]

#### Impact Estimate
[Low / Medium / High]

## Evidence Requirements
- Every gap cites what criterion sets the expectation
- Every opportunity has rationale
- Note areas searched that had no gaps (positive findings)

## Positive Findings
Document: "Searched [area] for gaps, found none. Quality appears good because [evidence]."
```

### Gap Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Missing** | Expected but absent | No tests for critical function |
| **Broken** | Exists but doesn't work | Dead link, invalid path |
| **Stale** | Outdated or superseded | Docs reference old version |
| **Inconsistent** | Conflicts with other content | Code does X, docs say Y |
| **Dead** | Unused or orphaned | Function never called |

---

## Deploying Agents

Deploy all four agents in a **single message** with multiple Task tool calls:

```markdown
<Task tool call 1: Inventory agent>
<Task tool call 2: Patterns agent>
<Task tool call 3: Documentation agent>
<Task tool call 4: Gaps agent>
```

This enables parallel execution. Do not deploy sequentially.

### Example Task Call

```
Task(
  description="Inventory exploration",
  prompt="[Full prompt from template above, customized for domain]",
  subagent_type="Explore",
  model="opus"
)
```

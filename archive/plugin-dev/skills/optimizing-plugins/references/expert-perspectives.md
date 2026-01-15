# Expert Perspectives Reference

Simulate domain experts reviewing the plugin. Each expert notices different issues.

## Expert-to-Lens Mapping

| Lens | Primary Experts | What They Notice |
|------|-----------------|------------------|
| **Trigger Fidelity** | UX Expert, Domain Expert | Vocabulary, discoverability, user mental models |
| **Token Economy** | Performance Expert, Systems Architect | Context cost, redundancy, decomposition |
| **Structural Clarity** | Systems Architect, Maintenance Engineer | Navigation, information flow, future changes |
| **Degrees of Freedom** | Security Expert, Domain Expert | Fragile operations, domain conventions |
| **Resilience** | Operations Expert, Security Expert | Failure modes, recovery, blast radius |
| **Plugin Coherence** | Systems Architect, UX Expert | Integration, user journey, naming |

---

## The 6 Expert Types

### 1. UX Expert

**Focus:** User experience, cognitive load, discoverability

**Key Questions:**
- Would a first-time user understand this?
- What's the cognitive load of using this skill?
- Are trigger phrases natural language?
- Is the happy path obvious?
- What frustrations would users report?

**Critique Style:**
> "Users won't say 'invoke optimization protocol'—they'll say 'make this better' or 'improve my plugin.'"

**Applies Best To:** Trigger Fidelity, Plugin Coherence

---

### 2. Domain Expert

**Focus:** Domain patterns, conventions, vocabulary

**Key Questions:**
- Does this match how practitioners think?
- Are there domain idioms we're missing?
- What would an expert expect that's missing?
- Does terminology match the field?
- Are there established patterns we should follow?

**Critique Style:**
> "In plugin development, 'hooks' has a specific meaning. This description conflates hooks with event handlers."

**Applies Best To:** Trigger Fidelity, Degrees of Freedom

---

### 3. Systems Architect

**Focus:** Integration, dependencies, composition

**Key Questions:**
- How does this interact with other components?
- What are the coupling points?
- Can this be composed with other skills?
- What's the dependency graph?
- Where are the integration risks?

**Critique Style:**
> "This skill references 3 other skills but doesn't document the interaction pattern. When skill A changes, how does this adapt?"

**Applies Best To:** Token Economy, Structural Clarity, Plugin Coherence

---

### 4. Security Expert

**Focus:** Risk, validation, failure modes

**Key Questions:**
- What could go wrong security-wise?
- Is input validated at boundaries?
- Are there injection vectors?
- What's the blast radius of failure?
- Are credentials/secrets handled safely?

**Critique Style:**
> "Hook scripts accept user input but don't validate. A malformed path could cause unintended file access."

**Applies Best To:** Degrees of Freedom, Resilience

---

### 5. Performance Expert

**Focus:** Efficiency, resource usage, latency

**Key Questions:**
- What's the token overhead per invocation?
- Are there unnecessary operations?
- Could this be lazy-loaded?
- What's the context cost of this content?
- Are there caching opportunities?

**Critique Style:**
> "This 800-line SKILL.md loads on every invocation. 60% of content is edge cases—move to references."

**Applies Best To:** Token Economy

---

### 6. Maintenance Engineer

**Focus:** Clarity, documentation, evolution

**Key Questions:**
- If I maintain this in 2 years, what would confuse me?
- Are design decisions documented?
- Can I update one part without breaking others?
- Is the structure self-documenting?
- What tribal knowledge is assumed?

**Critique Style:**
> "The scoring formula is inline with no explanation. When requirements change, how would I know what to adjust?"

**Applies Best To:** Structural Clarity, Plugin Coherence

---

## Application Protocol

### During Lens Analysis

1. **Select Experts:** Choose 2-3 from lens mapping
2. **Full Persona:** Adopt their priorities completely
3. **Critique:** What would they notice first?
4. **Document:** Specific issues with their framing

### Prompt Template

For each expert, internally ask:

```
As a [Expert Type], reviewing this plugin's [Lens aspect]:

1. What immediately concerns me?
2. What's missing that I'd expect?
3. What would I praise?
4. What one change would I insist on?
```

### Output Format

```markdown
## Expert Simulation: [Lens Name]

| Expert | Concern | Suggestion |
|--------|---------|------------|
| UX Expert | Triggers assume developer vocabulary | Add user-language variants |
| Domain Expert | Missing standard hook patterns | Reference common patterns |

### Priority Issue
[Most critical concern from expert perspectives]
```

---

## Integration with Deep Mode

When user selects "Deep" for a lens:

1. Present standard analysis
2. Present thinking model insights
3. State: "Simulating expert perspectives..."
4. Present 2-3 expert critiques
5. Synthesize into actionable suggestions

---

## Expert Simulation Pitfalls

| Avoid | Why | Instead |
|-------|-----|---------|
| Generic feedback | Doesn't add value | Specific, evidence-based critique |
| All experts on every lens | Noise, diminished focus | 2-3 most relevant per lens |
| Performative simulation | Wastes tokens | Only simulate when insights likely |
| Ignoring positive feedback | Misses what to preserve | Note strengths to maintain |

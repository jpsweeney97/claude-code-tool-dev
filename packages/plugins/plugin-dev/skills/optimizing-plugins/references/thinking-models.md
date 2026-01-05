# Thinking Models Reference

11 analytical models mapped to 6 optimization lenses. Apply relevant models to deepen lens analysis.

## Model-to-Lens Mapping

| Lens | Primary Models | Application Focus |
|------|----------------|-------------------|
| **Trigger Fidelity** | First Principles, Inversion, Root Cause | What triggers MUST exist? What guarantees failure? Why do users need this? |
| **Token Economy** | Pareto, Opportunity Cost, Constraints | Which 20% delivers 80%? What do we lose? What's truly fixed? |
| **Structural Clarity** | Systems Thinking, Inversion, Comparative | How do parts interact? What guarantees confusion? How do options compare? |
| **Degrees of Freedom** | Constraint Analysis, Devil's Advocate, Pre-Mortem | Hard vs soft constraints? Argue both sides. Why did this fail? |
| **Resilience** | Pre-Mortem, Inversion, Second-Order | Assume failure—why? What guarantees it? What happens next? |
| **Plugin Coherence** | Systems Thinking, Second-Order, Root Cause | Feedback loops? Downstream effects? Why designed this way? |

---

## The 11 Models

### 1. First Principles

**Core Question:** What is fundamentally needed?

**Application:**
1. Strip away convention and assumption
2. Ask: "If this didn't exist, what would we build?"
3. Identify atomic unit of value
4. Build up from irreducible requirements

**For Optimization:** What does this plugin fundamentally need to do well? Remove everything else.

---

### 2. Inversion

**Core Question:** What guarantees failure?

**Application:**
1. List all ways this could fail
2. Create explicit anti-patterns from each
3. Design to avoid every failure mode
4. Document why each anti-pattern is dangerous

**For Optimization:** What trigger phrases guarantee wrong invocation? What structure guarantees confusion?

---

### 3. Second-Order Effects

**Core Question:** What happens after the obvious consequence?

**Application:**
1. Identify immediate effects
2. For each, ask "then what?"
3. Map chain 3-4 levels deep
4. Plan for downstream impacts

**Example Chain:**
```
Improve trigger specificity →
  More reliable invocation →
    Users trust skill more →
      Higher usage, more feedback →
        Need to handle edge cases discovered
```

---

### 4. Pre-Mortem

**Core Question:** Assuming this failed, why did it fail?

**Application:**
1. Imagine complete failure 6 months from now
2. List all reasons it could have failed
3. Prioritize by likelihood × impact
4. Mitigate top risks proactively

**For Optimization:** "This optimization was abandoned. Why?" Identify and address those reasons now.

---

### 5. Systems Thinking

**Core Question:** How do parts interact? What are the feedback loops?

**Application:**
1. Map as system (inputs, processes, outputs)
2. Identify relationships between components
3. Find feedback loops (positive and negative)
4. Locate leverage points

**For Optimization:** How do skills interact? What happens when one changes? Where's maximum impact?

---

### 6. Devil's Advocate

**Core Question:** What's the strongest argument against this?

**Application:**
1. State design decision clearly
2. Actively argue the opposite
3. Find legitimate concerns
4. Strengthen or abandon the decision

**For Optimization:** "This suggestion is wrong because..." If counterargument wins, change the suggestion.

---

### 7. Constraint Analysis

**Core Question:** What constraints are real vs assumed?

**Application:**
1. List all perceived constraints
2. Classify: Hard (real) vs Soft (assumed)
3. Challenge soft constraints
4. Work creatively within hard constraints

| Type | Example | Fixed? |
|------|---------|--------|
| Platform | Claude's context limits | Hard |
| Convention | "Skills under 500 lines" | Soft |
| Technical | Must use plugin API | Hard |
| Social | "Users expect X" | Soft |

---

### 8. Pareto Analysis (80/20)

**Core Question:** Which 20% delivers 80% of value?

**Application:**
1. List all potential improvements
2. Estimate value contribution
3. Identify vital few (20%)
4. Focus resources on high-value items

**For Optimization:** Which 2-3 suggestions would transform this plugin? Do those first.

---

### 9. Root Cause Analysis (5 Whys)

**Core Question:** Why is this needed? (Asked 5 times)

**Application:**
1. State the need
2. Ask "Why?" and answer
3. For that answer, ask "Why?" again
4. Repeat until root cause emerges
5. Address root cause, not symptoms

**Example:**
```
Need: "Triggers aren't firing reliably"
Why? → Descriptions are vague
Why? → Written from developer perspective
Why? → No user vocabulary research
Why? → No process for trigger validation
Why? → Trigger quality not measured

Root Cause: No trigger quality measurement
Solution: Add scoring rubric for Trigger Fidelity
```

---

### 10. Comparative Analysis

**Core Question:** How do options compare?

**Application:**
1. Define evaluation criteria
2. Weight criteria by importance
3. Score each option
4. Calculate weighted totals

**Template:**
| Criteria | Weight | Option A | Option B |
|----------|--------|----------|----------|
| Clarity | 30% | 7 | 9 |
| Effort | 25% | 8 | 5 |
| Impact | 45% | 6 | 8 |
| **Total** | | **6.85** | **7.55** |

---

### 11. Opportunity Cost

**Core Question:** What are we giving up?

**Application:**
1. List all options considered
2. For each, identify what's sacrificed
3. Quantify trade-offs
4. Make informed choice

**For Optimization:** "By adding this complexity, we sacrifice simplicity. Is that trade-off worth it?"

---

## Application Protocol

### During Lens Analysis

1. **Quick Scan:** Apply all 11 models briefly (1 min each)
2. **Identify Relevant:** Which 3-5 yield insights for this lens?
3. **Deep Application:** Apply selected models thoroughly
4. **Document Insights:** Capture in structured format

### Output Format

```markdown
## Thinking Model Application: [Lens Name]

### Models Applied
| Model | Insight | Suggestion Impact |
|-------|---------|-------------------|
| First Principles | Core need is X, not Y | Simplify feature Z |
| Pre-Mortem | Likely failure: A | Add safeguard B |

### Key Insight
[Most important discovery from model application]
```

---

## Integration with Deep Mode

When user selects "Deep" for a lens:

1. Present standard analysis first
2. State: "Applying thinking models for deeper analysis..."
3. Apply 2-3 most relevant models
4. Present model-derived insights
5. Add to suggestions if actionable

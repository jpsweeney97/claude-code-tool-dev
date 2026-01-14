# Thinking Lenses

11 analytical perspectives applied during Phase 1 analysis. Each lens reveals different aspects of the problem space that single-perspective analysis would miss.

## The 11 Lenses

| # | Lens | Core Question | Skill Design Application |
|---|------|---------------|--------------------------|
| 1 | **First Principles** | What is fundamentally needed? | Strip away conventional patterns. What's the atomic unit of value? |
| 2 | **Inversion** | What would guarantee failure? | List failure modes, create anti-patterns, design to avoid each one |
| 3 | **Analogy** | What similar problems exist? | Find patterns from other domains that map to this problem |
| 4 | **Abstraction** | What's the right level of generality? | Neither too specific (limited reuse) nor too abstract (unclear usage) |
| 5 | **Systems** | How do the parts interact? | Map inputs, processes, outputs, feedback loops, integration points |
| 6 | **Temporal** | How does this evolve over time? | Project forward: 1 week, 1 month, 6 months, 1 year, 2 years |
| 7 | **Constraint** | What are the real limits? | Distinguish hard constraints (platform) from soft (convention) |
| 8 | **Failure** | What breaks, when, and how? | Identify catastrophic, silent, adoption, evolution, ecosystem failures |
| 9 | **Composition** | How does this combine with others? | What skills might this compose with? What handoff format works? |
| 10 | **Evolution** | Will this still work in 2 years? | Assess timelessness, extension points, obsolescence risk |
| 11 | **Adversarial** | What's the strongest argument against this? | Devil's advocate: argue the opposite, find legitimate concerns |

## Application Protocol

### Phase 1: Rapid Scan

Apply each lens for 2-3 minutes to assess relevance:

| Lens | Relevance (H/M/L) | Key Insight |
|------|-------------------|-------------|
| First Principles | | |
| Inversion | | |
| Analogy | | |
| Abstraction | | |
| Systems | | |
| Temporal | | |
| Constraint | | |
| Failure | | |
| Composition | | |
| Evolution | | |
| Adversarial | | |

### Phase 2: Deep Dive

For each High-relevance lens:
1. Apply full protocol (5-10 minutes per lens)
2. Document insights in structured format
3. Integrate insights into design
4. Note conflicts with other lenses

### Phase 3: Conflict Resolution

When lenses suggest conflicting approaches:
1. State each perspective clearly
2. Identify the underlying tension
3. Determine which lens should dominate for this decision
4. Document resolution and rationale

## Minimum Coverage

Before proceeding to specification:
- All 11 lenses scanned for relevance
- At least 3 lenses yield actionable insights
- All High-relevance lenses fully applied
- Conflicts between lenses resolved

## Lens Deep Dives

### First Principles

**Application:**
1. Strip away conventional skill patterns
2. Ask: "If skills didn't exist, how would we solve this?"
3. Identify the core utility this skill provides
4. Build up from fundamental requirements

**Key Questions:**
- What is the atomic unit of value this skill delivers?
- What assumptions from existing skills are we carrying forward unnecessarily?
- What would a minimal viable skill look like?

**Output:** Core value proposition, stripped of convention

### Inversion

**Failure Categories:**

| Category | Example Failures |
|----------|------------------|
| Adoption | Too complex, unclear triggers, wrong audience |
| Execution | Timeout, wrong output, missing edge cases |
| Integration | Conflicts with other skills, breaks ecosystem |
| Evolution | Obsolete quickly, can't extend, tightly coupled |

**Application:**
1. List all ways this skill could fail
2. Create explicit anti-patterns from each
3. Design to avoid every failure mode
4. Document why each anti-pattern is dangerous

**Output:** Comprehensive anti-patterns section

### Systems

**System Diagram Elements:**
- Inputs: User goal, context, configuration
- Processes: Each phase of the skill
- Outputs: Artifacts, side effects, state changes
- Connections: Dependencies, triggers, compositions

**Key Questions:**
- What other skills does this interact with?
- What feedback loops exist (success breeds success, failure cascades)?
- Where are the leverage points that have outsized impact?

**Output:** System integration map, leverage point identification

### Temporal

**Timeframes to Evaluate:**

| Horizon | Question | Focus |
|---------|----------|-------|
| Now | Does this solve the immediate problem? | Current utility |
| 1 week | Will the first users succeed? | Initial experience |
| 1 month | What feedback will we receive? | Early adoption issues |
| 6 months | How will usage patterns evolve? | Maturation |
| 1 year | What ecosystem changes are likely? | External pressures |
| 2 years | Will the core approach still be valid? | Fundamental soundness |

**Output:** Temporal projection with risks and mitigations

### Constraint

**Constraint Categories:**

| Type | Example | Fixed? |
|------|---------|--------|
| Platform | Claude's token limits | Hard |
| Convention | "Skills should be <500 lines" | Soft |
| Technical | Must work with existing tools | Usually Hard |
| Social | "Users expect X pattern" | Soft |

**Application:**
1. List all perceived constraints
2. Classify: Hard (real) vs Soft (assumed)
3. Challenge soft constraints
4. Work within hard constraints creatively

**Output:** Clear understanding of actual constraints, creative solutions

### Adversarial

**Application Protocol:**

For each major design decision:
1. Write the strongest possible counterargument
2. If counterargument wins: change the decision
3. If original wins: document why counterargument was rejected

**Output:** Validated decisions with documented rationale

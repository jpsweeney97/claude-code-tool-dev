# Output Formats

Templates for retrospective deliverables.

---

## Full Retrospective (Stages 1-8)

Use when Stage 3 gate decision is **CONTINUE**.

### 1. Failure Chain

The factual sequence from trigger to consequence.

```
Trigger: [what initiated the incident]
     ↓
Action: [what was done]
     ↓
Consequence: [what resulted]
```

### 2. Root Cause Analysis

Table of contributing causes.

| Cause | How it contributed |
|-------|-------------------|
| ... | ... |

### 3. Variant Scenarios

2-3 concrete examples of how the same pattern would manifest differently.

```
**Variant 1: [name]**
[Scenario description with enough detail to be testable]

**Variant 2: [name]**
[Scenario description]

**Variant 3: [name]**
[Scenario description]
```

### 4. Fundamental Pattern

The named distortion with explanation of why it generalizes.

```
Obvious explanation: [stated]
Why insufficient: [specific reason]
Proposed pattern: [name and description]
```

### 5. Mechanism Assessment

What tools address the pattern:
- What exists and helps
- What's missing
- What would directly counteract it

### 6. Gap Analysis

Findings from auditing existing artifacts:
- Alignments
- Contradictions
- Absences

### 7. Encodings

Concrete artifacts produced, each with validation:

```
#### Encoding: [name]

**Type:** [methodology | rule | hook | skill]

**Content:**
[actual text/code]

**Validation against variants:**

| Variant | Intervenes at | Prevents failure? |
|---------|---------------|-------------------|
| [Variant 1] | [step/point] | ✓ Yes |
| [Variant 2] | [step/point] | ✓ Yes |
| [Variant 3] | [step/point] | ✓ Yes |

**Specificity:**
- Trigger: [condition]
- Action: [behavior]
- Scope: [boundaries]
- False positive risk: [assessment]

**Rationale:** Addresses fundamental pattern "[pattern name]" by [mechanism].
```

[Repeat for each encoding]

### 8. Remaining Gaps

Honest acknowledgment of what's still unresolved or uncertain.

---

## Abbreviated Postmortem (Stages 1-3)

Use when Stage 3 gate decision is **STOP**.

### 1. Failure Chain

The factual sequence from trigger to consequence.

### 2. Surface Cause Analysis

Table of contributing causes.

| Cause | How it contributed |
|-------|-------------------|
| ... | ... |

### 3. Gate Decision

- **Variants attempted:** [describe what variants you tried to generate]
- **Result:** [no variants describable / surface fix sufficient for all variants]
- **Conclusion:** Deep analysis not warranted because [specific reason]

### 4. Immediate Fix

Specific action addressing the surface cause:
- A one-time correction
- A narrow rule addition
- A specific hook (if action should be blocked)

**Note:** Abbreviated postmortems don't produce methodology changes — those require patterns that generalize beyond the specific incident.

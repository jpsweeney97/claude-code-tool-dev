# Skill Type Adaptation

Different skill types have different quality priorities. Use this reference during EXPLORE to focus on what matters most for the skill being reviewed.

## Table of Contents

- [Identifying Skill Type](#identifying-skill-type)
- [Type 1: Process/Workflow](#type-1-processworkflow)
- [Type 2: Quality Enhancement](#type-2-quality-enhancement)
- [Type 3: Capability](#type-3-capability)
- [Type 4: Solution Development](#type-4-solution-development)
- [Type 5: Meta-cognitive](#type-5-meta-cognitive)
- [Type 6: Recovery/Resilience](#type-6-recoveryresilience)
- [Type 7: Orchestration](#type-7-orchestration)
- [Type 8: Template/Generation](#type-8-templategeneration)

---

## Identifying Skill Type

| Type | Signals |
|------|---------|
| Process/Workflow | Numbered steps, sequential flow, "do X then Y" |
| Quality Enhancement | "Better", "clearer", "improved", quality criteria |
| Capability | Enables new function, "how to do X" |
| Solution Development | Analysis framework, tradeoffs, recommendations |
| Meta-cognitive | Recognition patterns, self-awareness, state detection |
| Recovery/Resilience | Error handling, failure modes, graceful degradation |
| Orchestration | Coordinates skills, handoffs, phase transitions |
| Template/Generation | Output format, structure requirements, field specs |

**Mixed types:** Some skills combine types. Apply guidance for all relevant types, prioritizing the dominant one.

---

## Type 1: Process/Workflow

**Core question:** Did Claude follow the steps in order?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D2 (Process completeness) | → **P0**: Steps ARE the skill. Missing steps = broken skill. |
| D7 (Internal consistency) | → **P0**: Step references must match across sections. |
| D16 (Methodological soundness) | → **P0**: Wrong process = wrong outcome. Steps must be the *right* steps. |

**Additional checks:**

- [ ] Steps numbered and sequential?
- [ ] Each step has clear completion criteria?
- [ ] What happens if a step fails — is recovery defined?
- [ ] Are steps atomic or can they be partially completed?
- [ ] Is step order mandatory or can some parallelize?

**Common issues:**

| Issue | Example |
|-------|---------|
| Implicit step | "Prepare the environment" without saying how |
| Missing failure path | Step 3 assumes step 2 succeeded |
| Unclear checkpoint | When can you move to next step? |
| Hidden prerequisite | Step 1 assumes tool is installed |

**Adversarial focus:**

- What if agent skips step 2 and goes to step 3?
- What's the minimal path an agent might take while "technically" following the skill?

---

## Type 2: Quality Enhancement

**Core question:** Is output measurably better?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D5 (Precision) | → **P0**: Quality criteria must be unambiguous. |
| D12 (Testability) | → **P0**: "Better" must be verifiable. |
| D16 (Methodological soundness) | → **P0**: Wrong quality criteria = wrong improvements. Criteria must be valid. |

**Additional checks:**

- [ ] Quality dimensions explicitly defined?
- [ ] Each dimension has good/bad examples?
- [ ] Criteria are measurable, not subjective?
- [ ] Trade-offs between dimensions addressed?
- [ ] "Good enough" threshold defined?

**Common issues:**

| Issue | Example |
|-------|---------|
| Vague criteria | "Make it clearer" without defining clear |
| Unmeasurable quality | "Improve readability" — by what metric? |
| Missing trade-offs | Brevity vs completeness not addressed |
| No baseline | "Better" than what? |

**Adversarial focus:**

- Could agent claim "improved" without measurable change?
- Are criteria specific enough to prevent gaming?

---

## Type 3: Capability

**Core question:** Can Claude do the thing?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D11 (Feasibility) | → **P0**: Instructions must be achievable. |
| D6 (Actionability) | → **P0**: Each instruction must be immediately doable. |

**Additional checks:**

- [ ] Required tools/knowledge specified?
- [ ] Prerequisites listed?
- [ ] Success criteria for "did the thing"?
- [ ] What if capability is partially achieved?
- [ ] Fallbacks if primary approach fails?

**Common issues:**

| Issue | Example |
|-------|---------|
| Assumes unavailable tool | Uses `jq` without checking installation |
| Missing knowledge | Requires domain expertise not provided |
| Partial success undefined | What if 3 of 5 items succeed? |
| No verification | How to confirm capability worked? |

**Adversarial focus:**

- What's the minimum an agent could do and claim success?
- What external dependencies could break this?

---

## Type 4: Solution Development

**Core question:** Did Claude find the best approach?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D2 (Process completeness) | → **P0**: Analysis framework must be complete. |
| D8 (Scope boundaries) | → **P0**: What's in/out of consideration must be clear. |
| D16 (Methodological soundness) | → **P0**: Wrong framework = wrong recommendations. Analysis approach must be valid. |

**Additional checks:**

- [ ] Analysis framework defined?
- [ ] Trade-off criteria explicit?
- [ ] Multiple alternatives required?
- [ ] Recommendation criteria specified?
- [ ] Confidence/uncertainty handling?

**Common issues:**

| Issue | Example |
|-------|---------|
| Single solution bias | Jumps to recommendation without alternatives |
| Missing trade-offs | Recommends without acknowledging downsides |
| Vague criteria | "Best" without defining best-for-what |
| Scope creep | Analysis expands beyond original question |

**Adversarial focus:**

- Could agent recommend first idea without exploring alternatives?
- Are trade-offs required or just encouraged?

---

## Type 5: Meta-cognitive

**Core question:** Did Claude notice what it should?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D1 (Trigger clarity) | → **P0**: Recognition patterns must be precise. |
| D10 (Edge cases) | → **P0**: Boundary of recognition must be defined. |

**Additional checks:**

- [ ] Recognition triggers concrete and specific?
- [ ] False positive scenarios addressed?
- [ ] False negative scenarios addressed?
- [ ] Response to recognition defined?
- [ ] Calibration guidance (when to trust the recognition)?

**Common issues:**

| Issue | Example |
|-------|---------|
| Vague trigger | "When uncertain" — uncertain about what? |
| Missing response | Recognizes state but doesn't say what to do |
| Over-triggering | Pattern too broad, fires constantly |
| Under-triggering | Pattern too narrow, misses real cases |

**Adversarial focus:**

- Could agent claim recognition without evidence?
- What's the boundary between "should trigger" and "shouldn't trigger"?

---

## Type 6: Recovery/Resilience

**Core question:** Did Claude recover appropriately?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D10 (Edge cases) | → **P0**: Failure scenarios ARE the skill. |
| D2 (Process completeness) | → **P0**: Recovery paths must be fully specified. |

**Additional checks:**

- [ ] Failure modes enumerated?
- [ ] Recovery action for each failure?
- [ ] Escalation criteria defined?
- [ ] Graceful degradation paths?
- [ ] What's unrecoverable vs recoverable?

**Common issues:**

| Issue | Example |
|-------|---------|
| Happy path only | No failure handling defined |
| Generic recovery | "Handle the error" without specifics |
| Missing escalation | When to give up and ask for help? |
| Cascading failures | Recovery from A breaks B |

**Adversarial focus:**

- What if recovery itself fails?
- Could agent claim "recovered" while in degraded state?

---

## Type 7: Orchestration

**Core question:** Right skills invoked in right order?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D13 (Integration clarity) | → **P0**: Handoffs ARE the skill. |
| D7 (Internal consistency) | → **P0**: Skill references must be accurate. |

**Additional checks:**

- [ ] All orchestrated skills listed?
- [ ] Handoff triggers explicit?
- [ ] State/artifacts passed clearly?
- [ ] Failure handling at each handoff?
- [ ] Return conditions defined?
- [ ] No circular dependencies?

**Common issues:**

| Issue | Example |
|-------|---------|
| Implicit handoff | "Then use X" without trigger/state details |
| Missing return | Hands off but never gets control back |
| State loss | Artifacts from skill A not passed to skill B |
| Circular dependency | A calls B calls A |

**Adversarial focus:**

- What if orchestrated skill fails?
- Could agent skip a skill in the sequence?

---

## Type 8: Template/Generation

**Core question:** Does output match required format?

**Elevate priority:**

| Dimension | Why it matters more |
|-----------|---------------------|
| D3 (Structural conformance) | → **P0**: Structure IS the skill. |
| D5 (Precision) | → **P0**: Field requirements must be exact. |

**Additional checks:**

- [ ] All required fields specified?
- [ ] Field formats defined (type, length, pattern)?
- [ ] Optional vs required clear?
- [ ] Example output provided?
- [ ] Validation method specified?

**Common issues:**

| Issue | Example |
|-------|---------|
| Missing field spec | "Include metadata" without saying which fields |
| Ambiguous format | "Date" without format (ISO? US? EU?) |
| No example | Template described but not shown |
| Unvalidatable | No way to check output matches spec |

**Adversarial focus:**

- Could agent produce output that "looks right" but violates spec?
- What's the minimum structure that technically complies?

---

## Quick Reference Table

| Type | Elevate to P0 | D16 Priority | Key Additional Checks |
|------|---------------|--------------|----------------------|
| Process/Workflow | D2, D7, D16 | **P0** | Step completion criteria, failure paths |
| Quality Enhancement | D5, D12, D16 | **P0** | Measurable criteria, trade-offs |
| Capability | D6, D11 | P1 | Tool availability, prerequisites |
| Solution Development | D2, D8, D16 | **P0** | Multiple alternatives, trade-off criteria |
| Meta-cognitive | D1, D10 | P1 | Recognition precision, false positive/negative |
| Recovery/Resilience | D2, D10 | P1 | Failure enumeration, escalation criteria |
| Orchestration | D7, D13 | P1 | Handoff triggers, state passing, return conditions |
| Template/Generation | D3, D5 | P2 | Field specs, format precision, validation |

---

## Extension Points

### Skill-type-specific dimensions

- Process/Workflow skills: Add "Step ordering" dimension — are steps in logical sequence?
- Quality Enhancement skills: Add "Criteria clarity" dimension — are quality dimensions measurable?
- Meta-cognitive skills: Add "Recognition specificity" dimension — are triggers concrete enough to detect?

### Framework handoffs

- If review finds skill is fundamentally flawed → Recommend returning to brainstorming-skills
- If review passes → Skill ready for testing-skills validation
- These are recommendations, not automated handoffs (user decides)

### Custom artifact locations

- Default: `docs/audits/YYYY-MM-DD-<skill-name>-review.md`
- Projects can override via CLAUDE.md

### Stakes presets

- Projects can define default stakes in CLAUDE.md (e.g., "all skill reviews are Rigorous minimum")
- User can still override per-review

### Integration with other skills

| Skill | Relationship |
|-------|--------------|
| brainstorming-skills | Upstream — produces draft SKILL.md that this skill reviews |
| testing-skills | Downstream — validates behavioral effectiveness after review. Pass: reviewed SKILL.md path. Does not require review report but may reference it if behavioral issues arise. |
| reviewing-documents | Sibling — same pattern, different target (prose specs vs skills) |

### Supporting file depth

- Default: Review all files linked from SKILL.md (may be in skill root or subdirectories)
- Supporting files should be one level deep from SKILL.md (never nested)
- For skills with nested structures, note which files were reviewed and which were skipped

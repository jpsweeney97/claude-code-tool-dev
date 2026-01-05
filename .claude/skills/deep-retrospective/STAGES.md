# Stages

Detailed descriptions for each retrospective stage.

---

## Stage 1: Incident Review

**Goal:** Establish facts without analysis.

- What actions were taken?
- What was the outcome?
- What was the impact?

**Output:** A failure chain — the sequence from trigger to consequence.

**Prompt:** "Walk through what happened. Just the sequence, not why yet."

---

## Stage 2: Surface Root Cause

**Goal:** Initial "why did this happen?"

- Identify immediate causes: wrong assumption, missing knowledge, bad decision
- List contributing factors

**Output:** Table of causes and how each contributed.

**Prompt:** "Why did this happen? List the contributing causes."

**Note:** This is where most postmortems stop. We don't.

---

## Stage 3: Pattern Recognition (HARD GATE)

**Goal:** Determine if this is systematic. This stage decides whether to continue or conclude.

**Process:**
1. Attempt to generate 2-3 variant scenarios where the same underlying pattern causes a *different* failure
2. For each variant, verify it's genuinely different (not the same incident with names changed)
3. Test: Would fixing only the Stage 2 surface cause prevent all variants?

**Decision criteria:**

| Condition | Decision |
|-----------|----------|
| Cannot generate any variants after genuine attempt | **STOP** |
| Variants generated, but surface fix prevents all of them | **STOP** |
| Variants generated, surface fix does NOT prevent all | **CONTINUE** |

**Output if STOP:**

Conclude with abbreviated postmortem (Stages 1-3 only). See [OUTPUTS.md](OUTPUTS.md#abbreviated-postmortem).

**Output if CONTINUE:**
- 2-3 concrete variant scenarios with enough detail to be testable
- Explicit statement: "Surface fix would not prevent variant X because [reason]"

**Prompt:** "Generate 2-3 variant scenarios. For each, would the Stage 2 surface fix prevent it? If yes for all variants, stop here."

**Self-check before CONTINUE:**

> "Why doesn't fixing the Stage 2 surface cause suffice?"

You must have a concrete answer referencing specific variants. "It feels like there's something deeper" is not sufficient.

**Red flags — premature stopping:**
- Variants feel describable but you're avoiding the effort
- "I can't think of variants" without actually trying concrete scenarios
- Stopping because surface cause feels "sufficient" without testing

**Red flags — premature continuing:**
- Variants are the same incident with different nouns
- Continuing because deep analysis feels more thorough
- Cannot articulate why surface fix fails for the variants

---

## Stage 4: Fundamental Distortion

**Goal:** Identify the underlying pattern that made this failure likely.

- What behavior pattern or bias produced this?
- The answer should be more general than the specific incident

**Output:** A named pattern.

**Prompt:** "What underlying pattern made me prone to this? Name it."

**Required format:**

```
Obvious explanation: [state it]
Why insufficient: [specific reason, referencing variants]
Proposed pattern: [only if above is answered]
```

**Self-check:** "Is the obvious explanation insufficient, or am I reaching for a more interesting diagnosis?"

---

## Stage 5: Challenge the Framing

**Goal:** Test whether the diagnosis is precise and useful.

- Is this framing actionable?
- Is there a more precise characterization?
- Does the explanation actually explain, or just redescribe?

**Output:** Either confirmation of the framing or a refined diagnosis.

**Prompts:**
- "Is this framing useful? Is there a more precise way to characterize what's happening?"
- "Does this explanation predict other failures, or just redescribe this one?"
- "If I accept this framing, what would I do differently? If nothing concrete, the framing isn't useful."

**Required challenge before accepting any framing:**

1. State the framing
2. Answer: "If I accept this, what specifically would I do differently?"
3. If answer is abstract ("be more careful") → reject, not actionable
4. If answer is concrete ("check X before Y") → continue testing

---

## Stage 6: Mechanism Analysis

**Goal:** Identify what tools/structures can address the distortion.

- What already helps? (existing CLAUDE.md rules, hooks, habits)
- What's missing?
- What would directly counteract the identified pattern?

**Output:** List of mechanisms and their fit to the problem.

**Prompt:** "What tools or constraints would address this pattern? What exists, what's missing?"

---

## Stage 7: Gap Analysis

**Goal:** Audit existing artifacts against findings.

- Does current CLAUDE.md align with or contradict the insight?
- Are there rules that reinforce the bad pattern?
- What's absent that should be present?

**Output:** Specific gaps and contradictions identified.

**Prompt:** "Review existing rules and artifacts. What aligns, what contradicts, what's missing?"

---

## Stage 8: Encoding

**Goal:** Add durable artifacts that address the root cause.

**Artifact types:**
- **CLAUDE.md methodology:** Behavioral guidance shaping reasoning approach
- **CLAUDE.md rules:** Specific constraints for specific situations
- **Hooks:** Hard blocks on known-bad actions
- **Skills/commands:** Repeatable processes for recurring situations

**Process:**
1. Draft encodings for each artifact type that applies
2. Validate each encoding (Stage 8a)
3. Check specificity (Stage 8b)
4. Refine encodings that fail validation
5. Document final encodings with rationale
6. Update methodology version if applicable (Stage 8c)

**Output:** Concrete changes to artifacts, each with validation evidence.

**Prompt:** "Encode the fix. For each encoding, validate it against the variant scenarios."

**Self-check before methodology-level encodings:**

> "Does this require changing how I think, or just blocking a specific action?"

| If the fix is... | Then create... |
|------------------|----------------|
| "Don't do X" (specific action) | Hook or narrow rule |
| "Check Y before doing Z" (decision point) | Rule with trigger condition |
| "Approach problems by..." (reasoning pattern) | Methodology addition |

Methodology additions are high-cost. Only create them when the pattern genuinely generalizes and narrow rules would require enumerating many cases.

---

## Stage 8a: Encoding Validation (Required)

**Goal:** Verify encodings address the fundamental pattern, not just the specific incident.

**Validation test for each encoding:**

For each variant scenario from Stage 3:
1. Assume the encoding exists
2. Walk through the variant scenario step by step
3. At what point does the encoding intervene?
4. Does the intervention prevent the failure?

**Validation matrix:**

| Encoding | Variant 1 | Variant 2 | Variant 3 | Result |
|----------|-----------|-----------|-----------|--------|
| [encoding] | ✓ Prevents at [step] | ✓ Prevents at [step] | ✓ Prevents at [step] | PASS |
| [encoding] | ✓ Prevents | ✗ Doesn't apply | — | FAIL: too narrow |

**Decision criteria:**

| Result | Action |
|--------|--------|
| Prevents ALL variants | PASS |
| Prevents SOME variants | FAIL — revise to generalize |
| Prevents NONE | FAIL — reconsider Stage 4 diagnosis |
| Prevents original but no variants | FAIL — incident-specific, not pattern-specific |

**If validation fails:** Identify what failing variants have in common that the encoding misses. Revise and re-validate.

---

## Stage 8b: Encoding Specificity Check

**Goal:** Ensure encodings are precise enough to be actionable.

For each encoding, verify:

| Check | Pass criteria |
|-------|---------------|
| **Trigger clarity** | Can you identify exactly when this applies? |
| **Action clarity** | Is the required behavior unambiguous? |
| **Scope bounds** | Is it clear when this does NOT apply? |
| **No false positives** | Would this block legitimate actions? |

**Output format for each encoding:**

```
#### Encoding: [name/summary]

**Type:** [methodology | rule | hook | skill]

**Content:**
[actual text/code to add]

**Validation:**
- Variant 1 ([name]): [how encoding intervenes]
- Variant 2 ([name]): [how encoding intervenes]
- Variant 3 ([name]): [how encoding intervenes]

**Specificity check:**
- Trigger: [when this applies]
- Action: [what to do]
- Scope: [when this does NOT apply]
- False positive risk: [low/medium/high + reasoning]

**Rationale:** [why this addresses the fundamental pattern]
```

---

## Stage 8c: Update Methodology Version (If Applicable)

If this retrospective produces changes to the deep-retrospective methodology itself:

1. Increment version number (see [CHANGELOG.md](CHANGELOG.md#changelog-guidelines))
2. Add changelog entry with origin, changes, rationale
3. Add inline annotations to new/modified rules
4. Update "Last Updated" in header

This is how the methodology improves itself.

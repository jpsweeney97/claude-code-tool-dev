---
name: improving-skills
description: Assess and improve existing skills through rigorous analysis before making changes. Use when user says "improve this skill", "optimize this skill", "this skill isn't working", or wants to modify an existing skill. Hands off to creating-skills if complete rewrite is needed.
---

# Improving Skills

Improve existing skills through rigorous assessment and collaborative dialogue. This skill enforces thorough analysis before making any changes — preventing the common failure mode of jumping directly to edits.

## Before You Start

Read [skills-guide.md](skills-guide.md) before proposing any changes. The guide is the authoritative reference for skill quality. Do not rely on memory — read it fresh.

## Core Principle

**Assessment before action.** You must understand what's working, what's not, and *why* before proposing changes. Improvements that skip this step often:
- Break things that were working
- Address symptoms instead of root causes
- Miss the actual problem entirely

## When to Hand Off to creating-skills

**Hand off when any of these are true:**
- Less than ~20% of the content is worth preserving
- The skill's core purpose was wrong, not just the execution
- The existing skill confuses the improvement dialogue more than it helps

**Stay in improving-skills when:**
- Most content provides value worth preserving
- Purpose is sound; structure or execution needs work
- The existing skill serves as a useful foundation for dialogue

If assessment reveals a hand-off is needed, announce it: "This skill needs a complete rewrite. Switching to creating-skills to start fresh with the problem statement."

---

## The Assessment Phase

**YOU MUST complete all steps before proposing any changes.** Do not skip to recommendations. Do not "quickly assess" and move on. The assessment is the work.

### Step 1: Surface Assumptions

**Before reading the skill**, write down your assumptions:
- What do you assume about the skill's purpose?
- What type do you expect it to be?
- What do you assume about how it should work?

**Present your assumptions to the user and ask for clarification:**

> "Before I assess this skill, here are my assumptions:
> - [Assumption 1]
> - [Assumption 2]
> - ...
>
> Do these match your understanding, or should I adjust?"

**Wait for user response.** If the user corrects an assumption, update your understanding before proceeding. This early checkpoint prevents wasted assessment based on wrong premises.

**You cannot proceed to Step 2 without surfacing assumptions and getting user input.** Hidden assumptions cause wrong assessments. Surface them now, validate them, or discover they were wrong too late.

### Step 2: Review the Skill

Read **everything**:
- SKILL.md frontmatter and body — the entire file
- All supporting files referenced — not just the ones that seem relevant
- skills-guide.md — fresh, not from memory

As you read, note:
- What the skill is trying to accomplish
- How it's structured
- What techniques it uses
- How it compares to skills-guide.md standards

**No skimming. No "I get the gist." Read it.**

### Step 3: Identify Strengths and Weaknesses

Create two lists. Each item MUST have:
- **Specific evidence** — quote the section or cite file:line
- **Confidence level** — High / Medium / Low

| Confidence | Meaning | Evidence Required |
|------------|---------|-------------------|
| **High** | Directly supported | Specific quote or citation |
| **Medium** | Supported but incomplete | General reference, some gaps |
| **Low** | Plausible hypothesis | No direct evidence |

**Rule: Confidence cannot exceed evidence.** An uncited finding is Low confidence. No exceptions.

**Strengths** — What's working:
- Elements that follow skills-guide.md recommendations
- Effective techniques for the skill's type
- Clear, actionable instructions
- Well-crafted examples

**Weaknesses** — What's not working:
- Deviations from skills-guide.md standards
- Missing elements for the skill's type
- Vague or unactionable instructions
- Gaps in coverage

**You cannot proceed to Step 4 without cited evidence for every finding.**

### Step 4: Understand Why

For each strength: What makes it effective?

| Strength Source | Description |
|-----------------|-------------|
| Follows standards | Aligns with skills-guide.md recommendations |
| Type-appropriate | Uses techniques suited to skill type (discipline, technique, pattern, reference) |
| Clear and specific | Instructions are actionable, not vague |
| Well-scoped | Appropriate degrees of freedom, not overengineered |
| Bulletproofed | Closes loopholes, preempts rationalization (for discipline skills) |
| Progressive disclosure | SKILL.md focused, supporting files used appropriately |

For each weakness: What's the root cause?

| Root Cause | Description |
|------------|-------------|
| Missing information | Content was never added |
| Structural problem | Wrong organization or flow |
| Wrong type techniques | Discipline skill using pattern techniques, etc. |
| Scope creep | Skill tries to do too much |
| Outdated | Skill predates current standards |

**"It's just bad" is not a root cause. "It's just good" is not a strength source.** Name the specific principle. If you can't name it, you don't understand it yet.

### Step 5: Disconfirm Before Finalizing

**Before proceeding, actively try to disprove each weakness:**

For every weakness, answer:
- Could this be intentional? (Design choice, not oversight)
- Is there context I'm missing? (Supporting files, related skills, user's workflow)
- What would make this actually a strength? (Different perspective, different use case)

**If you cannot articulate why the weakness survives scrutiny, remove it.**

This step prevents:
- Confirmation bias (seeing what you expected)
- Anchoring (over-weighting first impressions)
- Projection (assuming your preferences are requirements)

### Step 6: Validate Assumptions and Check for Hand-Off

Compare your initial assumptions (Step 1) against findings:
- Which assumptions were validated?
- Which were invalidated?
- What surprised you?

**Invalidated assumptions require reassessment.** If a core assumption was wrong, loop back to Step 3 with fresh eyes.

Then evaluate hand-off criteria:
- Is less than ~20% worth preserving?
- Was the core purpose wrong?
- Does the existing skill confuse more than help?

**If yes to any → hand off to creating-skills.** Announce: "This skill needs a complete rewrite. Switching to creating-skills."

Do not patch a broken foundation. Do not "try to salvage" what should be rebuilt.

### Presenting Assessment Results

Rigor is in the doing, not the displaying. Present a concise summary — the user needs your conclusions, not your working document.

**Template:**

```
**Assessment complete.**

**Strengths ([X] identified):**
1. **[Strength]** — [what makes it effective]
2. **[Strength]** — [what makes it effective]
3. [etc.]

**Weaknesses ([Y] identified, priority order):**

**1. [Weakness title]**
[One-line description of the problem]
- *Confidence:* [level] — [reasoning]
- *Root cause:* [explanation]

**2. [Weakness title]**
[One-line description of the problem]
- *Confidence:* [level] — [reasoning]
- *Root cause:* [explanation]

Starting with weakness #1. Ready to discuss options?
```

**What stays internal (available if user asks):**
- Full evidence citations (file:line)
- Disconfirmation reasoning
- Assumption validation details

---

## The Recommendations Phase

After assessment, propose improvements. **Recommendations must meet a quality bar.** Surface-level suggestions waste time and miss root causes.

### What Makes a Good Recommendation

Every recommendation MUST include:

| Requirement | Question to Answer |
|-------------|-------------------|
| **Trade-offs explicit** | What is gained AND lost? |
| **Evidence-proportional** | Does confidence match the evidence? |
| **Well-reasoned** | Can you trace the logic from finding to recommendation? |
| **Pressure-tested** | What objections exist? How do you respond? |
| **Unbiased** | Have you checked for anchoring, sunk cost, confirmation bias? |
| **Multi-perspective** | How does this look from different viewpoints? |
| **Risks identified** | What could go wrong? What second-order effects exist? |
| **Framing challenged** | What if the premise is wrong? Is this the right question? |
| **Alternatives steelmanned** | What would make rejected options better than the frontrunner? |

**If a recommendation doesn't meet these criteria, it's not ready to propose.**

### Step 1: Generate Options

For each weakness, generate 3-4 improvement options. **Never propose only one option.**

| Option Type | When to Consider |
|-------------|------------------|
| **Direct fix** | Address the weakness as identified |
| **Structural change** | Reorganize to eliminate the root cause |
| **Removal** | Delete the problematic element entirely |
| **Reframe** | The weakness is actually fine; adjust expectations |

**One option is a recommendation. Multiple options is a decision.** Give the user a decision.

### Step 2: Articulate Trade-offs

For each option, state explicitly:
- **What's gained** — The improvement this delivers
- **What's lost** — The cost, complexity, or sacrifice
- **What's unchanged** — What this doesn't affect

**"No downsides" is almost always wrong.** Every change has costs. Name them.

### Step 3: Pressure-Test

For each option, surface objections and respond:

| Objection Type | Example |
|----------------|---------|
| **Feasibility** | "This would require rewriting 80% of the skill" |
| **Unintended consequences** | "This fix might break the trigger conditions" |
| **Scope creep** | "This turns a simple improvement into a redesign" |
| **Preference masquerading as requirement** | "I prefer this style, but is it actually better?" |

For each objection:
- **Dismiss with reason** — "This doesn't apply because..."
- **Mitigate** — "We can address this by..."
- **Accept as risk** — "This is a real cost we're choosing to accept"

**Do not ignore objections. Do not handwave. Respond substantively.**

### Step 4: Check for Bias

Before finalizing, ask:

| Bias | Check |
|------|-------|
| **Anchoring** | Am I over-weighting my first impression? |
| **Sunk cost** | Am I preserving something just because it exists? |
| **Confirmation bias** | Am I seeing evidence that supports what I expected? |
| **Familiarity bias** | Am I recommending what I know rather than what fits? |

**If you find bias:**

| Bias Affects... | Loop Back To... |
|-----------------|-----------------|
| Assessment findings (what you identified as strengths/weaknesses) | Assessment Phase, Step 3: Identify Strengths and Weaknesses |
| Option generation (what options you considered) | Step 1: Generate Options |
| Option preference (which option you favor) | Step 2: Articulate Trade-offs |

**Do not patch over bias. Reassess from the point of contamination.**

### Step 5: Consider Multiple Perspectives

How does this recommendation look from:
- **The skill user** — Is this actually an improvement for them?
- **The skill maintainer** — Does this make the skill harder to maintain?
- **Different use cases** — Does this work for edge cases, not just the happy path?
- **Future changes** — Does this enable or preclude future improvements?

**A recommendation that looks good from one perspective but bad from others needs revision.**

### Step 6: Identify Risks and Second-Order Effects

For each recommendation:
- **What could go wrong?** — Implementation risks, adoption risks
- **What does this enable?** — Future possibilities opened up
- **What does this preclude?** — Future possibilities closed off

**Second-order effects matter.** A fix that solves today's problem but creates tomorrow's is not a good fix.

### Step 7: Challenge Framing

Before presenting recommendations, ask:
- **What if the premise is wrong?** — Is this weakness actually a weakness?
- **Is this the right question?** — Should we be solving a different problem?
- **Are we improving the right skill?** — Should this be a new skill instead?

**Wrong framing produces wrong recommendations.** Check the frame.

### Step 8: Steelman Alternatives

For options you're NOT recommending:
- **What would make this option better than the frontrunner?**
- **Under what circumstances would this be the right choice?**

**If you can't steelman alternatives, you haven't understood them.** Weak understanding of alternatives means weak confidence in your recommendation.

### Step 9: Present Recommendations

Present to the user with:
1. **The recommendation** — What you propose
2. **The reasoning** — Why this option over others (traced from assessment findings)
3. **The trade-offs** — What's gained, lost, unchanged
4. **The risks** — What could go wrong
5. **Alternatives considered** — What else you evaluated and why you didn't choose it

**Wait for user input before proceeding to changes.**

---

## The Dialogue Phase

After assessment and recommendation preparation, engage the user in collaborative dialogue. **The user decides what changes to make — you provide options and reasoning.**

### One Weakness at a Time

**YOU MUST address weaknesses individually.** Do not bundle multiple weaknesses into a single decision. Each weakness gets its own dialogue cycle:

1. Present the weakness (with evidence and root cause)
2. Present 3-4 options with trade-offs
3. User chooses (or provides their own option)
4. Confirm understanding
5. Move to next weakness

### Presenting Options

For each weakness, use the format template from the [Examples](#examples) section. Always end with an explicit invitation for the user to choose or propose alternatives.

### When the User Chooses

If the user selects an option:
- Confirm understanding: "You'd like to [restate choice]. Correct?"
- Proceed to implementation for that weakness
- Then move to the next weakness

If the user proposes a different approach:
- Clarify the approach: ask questions to understand fully
- Evaluate against the same criteria (trade-offs, risks, etc.)
- Either adopt it or explain concerns and ask for guidance

**Do not dismiss user alternatives.** The user may have context you don't. Engage seriously with their ideas.

### When the User Disagrees with the Weakness

If the user says the weakness isn't actually a weakness:
- Ask for their reasoning
- Revisit your assessment with this new information
- Either update your assessment or explain why you still see it as a weakness

**This is dialogue, not persuasion.** If the user has good reasons, accept them.

### When the User Wants to Skip a Weakness

If the user says "skip this one" or "leave it as is":
- Confirm: "You'd like to keep [X] unchanged. Noted."
- Move to the next weakness
- Do not argue or re-raise unless new information emerges

**Respect user decisions.** The user owns the skill.

### Handling Dependencies

Some weaknesses may depend on others:
- If addressing weakness B depends on the decision for weakness A, say so
- Present weakness A first
- After the decision, explain how it affects options for weakness B

**Do not hide dependencies.** Surface them explicitly so the user can make informed decisions.

### Confirming the Full Change Set

After all weaknesses are addressed, summarize:

> "Based on our discussion, here are the changes we'll make:
> 1. [Weakness 1] → [Chosen option]
> 2. [Weakness 2] → [Chosen option]
> 3. [Weakness 3] → Skipped (user preference)
> ...
>
> Does this look right before I implement?"

**Wait for final confirmation before making any edits.**

---

## Making Changes

After the user confirms the change set, implement changes.

### Implement Incrementally

For each change:
1. Show the current version (quote relevant portion)
2. Show the proposed change
3. Explain what's different and why
4. Ask user for confirmation before implementing the change. **DO NOT make any edits without approval from the user.**
5. After implementing the change, proceed to the next change

**Do not batch all edits.** Incremental implementation lets the user catch errors before they compound.

### Preserve Strengths

As you make changes, verify you're not breaking what works:
- Check each strength from assessment — is it still intact?
- If a change affects a strength, flag it explicitly
- Trade-offs are acceptable if acknowledged; silent degradation is not

### When Implementation Reveals Problems

If, during implementation, you discover:
- The chosen option doesn't work as expected
- The change breaks something else
- A better approach becomes obvious

**Stop and surface it.** Do not silently adjust. Return to dialogue:

> "While implementing [X], I noticed [problem]. This means [consequence]. Options:
> 1. [Adjust approach]
> 2. [Revert to different option]
> 3. [Accept the problem as trade-off]
>
> How would you like to proceed?"

### Verify Against skills-guide.md

Before considering changes complete:
- Re-read skills-guide.md (fresh, not from memory)
- Check each change against relevant standards
- Verify the skill still meets the Quality Checklist

---

## Rationalization Table

These are excuses to skip steps. **All of them are wrong.**

| Rationalization | Reality |
|-----------------|---------|
| "This is a simple improvement" | Simple improvements still need assessment. Skipping steps causes errors regardless of perceived simplicity. |
| "I already know what's wrong" | Assumptions are most dangerous when confident. Complete the assessment to verify. |
| "The user is in a hurry" | Rushing causes rework. A proper process is faster than fixing mistakes. |
| "This is obviously the right fix" | Obvious to you isn't obvious to the user. Present options. Let them decide. |
| "The change is small" | Small changes still need approval. The approval gate exists for all changes, not just big ones. |
| "I read skills-guide.md recently" | Memory drifts. Read it fresh. Every time. |
| "The assessment is clear" | Clear assessments still need disconfirmation. That's when confirmation bias is most dangerous. |
| "This weakness is obvious" | Obvious still needs evidence. Cite it or it's opinion, not assessment. |
| "Time is limited" | Bundle nothing. One weakness at a time. Always. |
| "The user seems to agree" | "Seems to" is not confirmation. Get explicit approval before proceeding. |
| "I can fix this while implementing" | Stop. Surface the problem. Return to dialogue. Silent fixes erode trust. |
| "This is what the user really wants" | You don't know what the user wants until they tell you. Ask, don't assume. |
| "The skill is too broken to assess properly" | If it's that broken, hand off to creating-skills. Don't use broken as an excuse to skip rigor. |

**If you catch yourself thinking any of these: STOP.** Return to the process. No shortcuts.

---

## Anti-Patterns

| Pattern | Why It Fails | Fix |
|---------|--------------|-----|
| **Skipping Assessment** | Guessing at what's wrong; recommendations address symptoms, not root causes | Complete every step of assessment. No shortcuts. |
| **One-Option Recommendations** | Single options are directives, not decisions; user can't evaluate unseen trade-offs | Generate 3-4 options for every weakness. |
| **Silent Editing** | User loses control; errors compound before caught; trust erodes | Present every change, get explicit approval, then implement. |
| **Bundling Decisions** | Users can't make nuanced decisions; one disagreement blocks everything | One weakness at a time. Separate decisions for each. |
| **Dismissing User Alternatives** | User may have context you don't; dismissal shuts down dialogue | Engage seriously. Ask clarifying questions. Evaluate against same criteria. |
| **Confidence Without Evidence** | Uncited findings are opinions; user can't verify claims | Every finding needs evidence. Confidence cannot exceed evidence. |
| **Patching Instead of Looping Back** | Patches create inconsistency; root causes stay unaddressed | Identify which phase failed and loop back. |
| **Preserving for Preservation's Sake** | Sunk cost bias; skill accumulates cruft; real improvements get blocked | Evaluate every element on merit. "It's already there" is not a reason. |
| **Over-Improving** | Scope creep; user wanted targeted improvements, not a redesign | Improve what assessment identified. Stop there. |

---

## Examples

### Weakness + Options Format Template

```
**Weakness:** [Specific problem statement]
**Evidence:** [Quote or file:line citation]
**Confidence:** [High/Medium/Low] — [Why this confidence level]
**Root Cause:** [Why this is happening]

**Options:**

1. **[Direct fix]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed]
   - Risk: [What could go wrong]

2. **[Structural change]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed]
   - Risk: [What could go wrong]

3. **[Removal]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed]
   - Risk: [What could go wrong]

4. **[Reframe]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed]
   - Risk: [What could go wrong]

**Recommendation:** [Which option and why — but user decides]

Which option would you like, or would you prefer a different approach?
```

### Decision Point Snippets

**Catching yourself skipping assessment:**
> "The user said 'just fix the description' — I notice I'm about to jump straight to editing. Stopping. Even 'simple' fixes need assessment to verify the description is actually the problem."

**Catching yourself presenting one option:**
> "I have a clear recommendation. But one option isn't a decision — it's a directive. Generating alternatives: What if we removed it instead? What if the weakness is actually fine?"

**Catching yourself bundling:**
> "These three weaknesses feel related. I want to present them together. But bundling hides trade-offs. One at a time. The user can see connections; I shouldn't force them."

**Catching yourself proceeding without confirmation:**
> "The user said 'sounds good' — I notice I'm about to edit. But 'sounds good' isn't explicit approval. Asking: 'You'd like to proceed with option 2. Correct?'"

### Evidence Quality Examples

**High confidence (specific citation):**
> "Description lacks trigger phrases (High confidence — SKILL.md:3 says 'Analyzes data' but skills-guide.md:179-185 requires 'when to use' + trigger phrases)"

**Medium confidence (general reference):**
> "Examples may be insufficient (Medium confidence — skills-guide.md recommends examples for technique skills, but I haven't verified if these examples cover the key use cases)"

**Low confidence (no direct evidence):**
> "This section feels verbose (Low confidence — no specific standard violated; this is my impression, not assessment)"

---

## Troubleshooting

### User Disagrees with All Options

**Symptom:** For a weakness, the user rejects all 3-4 options and doesn't propose an alternative.

**Cause:** The options may not address the user's actual concern, or the weakness itself may be misidentified.

**Fix:**
1. Ask: "What would a good solution look like to you?"
2. If they can't articulate it, revisit the weakness: "Let me make sure I understand the problem correctly. What specifically isn't working for you?"
3. If the weakness was misidentified, update your assessment and regenerate options
4. If no solution emerges, ask: "Would you like to skip this one for now and revisit it later?"

---

### Assessment Finds No Weaknesses

**Symptom:** After completing the assessment, you can't identify any weaknesses.

**Cause:** Either the skill is genuinely good, or your assessment missed something.

**Fix:**
1. Re-read skills-guide.md and compare against Quality Checklist explicitly
2. Check your assumptions — did you assume something was fine without verifying?
3. Try perspective multiplication: What would a new user notice? A skeptical reviewer?
4. If the skill genuinely meets all standards, say so: "This skill follows skills-guide.md standards. I don't see meaningful improvements to recommend. Is there something specific you wanted to address?"

---

### Assessment Finds Too Many Weaknesses

**Symptom:** You've identified many weaknesses spanning most of the skill.

**Cause:** The skill may have systemic issues, or you may be over-identifying minor issues.

**Fix:**
1. Check for hand-off: Does this actually need a rewrite?
2. Prioritize: Which weaknesses matter most? Which are cosmetic?
3. Propose grouping: "I've identified [N] weaknesses. The most impactful are [top 3-4]. Would you like to focus on these first, or see the full list?"
4. Let the user set scope: They may only want to address a subset

---

### User Wants Changes You Think Are Harmful

**Symptom:** The user proposes or chooses an option you believe will make the skill worse.

**Cause:** You may be wrong, or the user may have context you don't, or there's a genuine disagreement.

**Fix:**
1. State your concern clearly: "I want to flag a concern with this approach: [specific issue]"
2. Explain the risk: "This could cause [consequence]"
3. Ask if there's context you're missing: "Is there something about your use case that makes this the right choice?"
4. If they still want it, implement it: "Understood. I'll proceed with your choice." The user owns the skill.

**Do not refuse to implement.** State concerns, then respect the user's decision.

---

### User Is Impatient with the Process

**Symptom:** User says "just fix it" or "this is taking too long" or "skip the options, just do what you think is best."

**Cause:** The process feels slow. The user may trust you to make good decisions.

**Fix:**
1. Acknowledge the friction: "I understand this is thorough. The process exists to prevent mistakes and give you control."
2. Offer compression, not shortcuts: "I can present options more briefly. Would that help?"
3. If they insist on skipping: "I can proceed with my recommendation, but I want to note: [brief trade-off]. Is that acceptable?"
4. Do not skip the approval gate for edits — even impatient users deserve to see what's changing before it changes.

---

### User Keeps Adding New Weaknesses Mid-Process

**Symptom:** During dialogue, the user identifies additional issues you didn't catch.

**Cause:** The user knows their skill better than you do. This is valuable input.

**Fix:**
1. Acknowledge: "Good catch — I missed that"
2. Add to the list: "I'll add this as weakness [N+1]"
3. Ask about ordering: "Would you like to address this now, or after we finish the current weakness?"
4. If it changes earlier decisions, flag it: "This might affect our decision on [earlier weakness]. Should we revisit?"

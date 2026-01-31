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

For each weakness, present:

```
**Weakness:** [What's not working]
**Evidence:** [Specific quote or citation]
**Root Cause:** [Why this is happening]

**Options:**

1. **[Option Name]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed or complicated]
   - Risk: [What could go wrong]

2. **[Option Name]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed or complicated]
   - Risk: [What could go wrong]

3. **[Option Name]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed or complicated]
   - Risk: [What could go wrong]

4. **[Option Name]** — [One-sentence description]
   - Gains: [What improves]
   - Costs: [What's sacrificed or complicated]
   - Risk: [What could go wrong]

**Recommendation:** [Which option and why — but user decides]

Which option would you like, or would you prefer a different approach?
```

**Always end with an explicit invitation for the user to choose or propose alternatives.**

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

## Red Flags — STOP If You Notice These

These behaviors signal you're about to shortcut the process. If you notice any of them, **STOP and return to the appropriate phase.**

**If you catch yourself thinking any rationalization from the table above, that's also a red flag — stop and return to the process.**

### Behaviors

- Editing before assessment is complete
- Presenting fewer than 3 options
- Making changes without explicit user approval
- Bundling multiple weaknesses into one decision
- Stating findings without citations
- Dismissing user alternatives without serious consideration
- Proceeding on "seems like" instead of explicit confirmation
- Skipping the hand-off check when the skill has major problems
- Not re-reading skills-guide.md before proposing changes
- Adjusting implementation silently instead of surfacing problems
- Skimming the skill instead of reading fully
- Moving to the next weakness before the current one is resolved

### What To Do

1. **Recognize the flag** — Name it explicitly: "I notice I'm about to [X]"
2. **Stop** — Do not proceed with the shortcut
3. **Return** — Go back to the appropriate phase:
   - Skipping assessment → Return to Assessment Phase
   - Skipping options → Return to Recommendations Phase, Step 1
   - Skipping approval → Return to Dialogue Phase
   - Silent editing → Stop, surface the issue, ask user

**Red flags are features, not bugs.** Noticing them means the process is working.

---

## Anti-Patterns

### Skipping Assessment

**Pattern:** Jumping straight to recommendations without completing the assessment phase.

**Why it fails:** Without rigorous assessment, you're guessing at what's wrong. Recommendations address symptoms, not root causes. Changes break things that were working.

**Fix:** Complete every step of the assessment phase. No shortcuts.

---

### One-Option Recommendations

**Pattern:** Presenting a single recommendation as the obvious choice.

**Why it fails:** Single options aren't decisions — they're directives. The user can't evaluate trade-offs they can't see. You may have missed better approaches.

**Fix:** Generate 3-4 options for every weakness. If you can only think of one, you haven't thought hard enough.

---

### Silent Editing

**Pattern:** Making changes without presenting them for approval.

**Why it fails:** The user loses control. Errors compound before they're caught. Trust erodes.

**Fix:** Present every change, get explicit approval, then implement. No exceptions.

---

### Bundling Decisions

**Pattern:** Presenting multiple weaknesses together as a package deal.

**Why it fails:** Users can't make nuanced decisions. One disagreement blocks everything. Dependencies get hidden.

**Fix:** One weakness at a time. Separate decisions for each.

---

### Dismissing User Alternatives

**Pattern:** Explaining why the user's idea won't work instead of engaging with it.

**Why it fails:** The user may have context you don't. You're there to help, not to win. Dismissal shuts down dialogue.

**Fix:** Engage seriously with user alternatives. Ask clarifying questions. Evaluate against the same criteria you used for your options.

---

### Confidence Without Evidence

**Pattern:** Stating findings with high confidence but no citations.

**Why it fails:** Uncited findings are opinions, not assessments. You may be wrong. The user can't verify your claims.

**Fix:** Every finding needs evidence. Confidence cannot exceed evidence. No exceptions.

---

### Patching Instead of Looping Back

**Pattern:** When problems emerge, adding fixes on top rather than returning to the appropriate phase.

**Why it fails:** Patches create inconsistency. Root causes stay unaddressed. The skill becomes a mess of layered fixes.

**Fix:** When something's wrong, identify which phase failed and loop back. Reassess, regenerate options, or re-engage dialogue as needed.

---

### Preserving for Preservation's Sake

**Pattern:** Keeping something because it exists, not because it's good.

**Why it fails:** Sunk cost bias. The skill accumulates cruft. Real improvements get blocked by attachment to existing content.

**Fix:** Evaluate every element on merit. "It's already there" is not a reason to keep it.

---

### Over-Improving

**Pattern:** Proposing improvements beyond what the user asked for or what the assessment identified.

**Why it fails:** Scope creep. The user wanted targeted improvements, not a redesign. You waste time on things that don't matter.

**Fix:** Improve what the assessment identified. Stop there. If you see additional opportunities, mention them separately — don't bundle them in.

---

## Examples

### Scenario: User wants to improve a skill's description

**BAD: Skipping assessment and jumping to edits**

> **User:** This skill isn't triggering reliably. Can you improve it?
>
> **Claude:** I'll update the description to include more trigger phrases. Here's the new version:
>
> ```yaml
> description: [Updated description with more triggers]
> ```
>
> Done!

**Why it's bad:** Claude skipped the entire assessment phase. The problem might not be the description — it could be wrong skill type, conflicting triggers with another skill, or a scope issue. The "fix" addresses a symptom without understanding the cause.

**GOOD: Following the process**

> **User:** This skill isn't triggering reliably. Can you improve it?
>
> **Claude:** I'll assess the skill to understand what's happening. First, let me surface my assumptions:
> - I'm assuming the problem is with the skill itself, not with how it's being invoked
> - I'm assuming "not triggering reliably" means it sometimes triggers and sometimes doesn't
>
> Do these assumptions match your experience, or should I adjust my understanding?
>
> **User:** Yes, that's right — it triggers maybe 50% of the time when I expect it to.
>
> **Claude:** Got it. Let me read the skill and skills-guide.md to assess what might be causing that.
>
> [Reads skill and guide]
>
> **Assessment:**
>
> **Strengths:**
> - Clear structure following technique skill patterns (High confidence — structure matches skills-guide.md recommendations)
> - Good examples section (High confidence — examples are specific and actionable)
>
> **Weaknesses:**
> - Description lacks trigger phrases (High confidence — skills-guide.md requires "when to use" + trigger phrases; current description only says what the skill does, not when to use it)
> - Description is generic (Medium confidence — "helps with X" doesn't distinguish from similar skills)
>
> **Root cause:** Description was written for human readers, not for Claude's skill selection logic.
>
> Before I proceed — could the triggering problem be something else? Is there another skill with similar triggers that might be competing?
>
> **User:** No, this is the only skill for this domain.
>
> **Claude:** Good, that rules out competition. Let me present options for the description weakness...

**Why it's good:** Claude surfaced assumptions and asked for validation, completed assessment with evidence, identified root cause, and checked for alternative explanations before proceeding.

---

### Scenario: User disagrees with the recommended option

**BAD: Dismissing the user's preference**

> **User:** I prefer option 2 over your recommendation.
>
> **Claude:** Option 2 isn't ideal because it adds complexity. Option 3 is cleaner and follows best practices better. I recommend we go with option 3.

**Why it's bad:** Claude dismissed the user's preference without understanding why they preferred it. The user owns the skill — Claude's job is to inform, not override.

**GOOD: Engaging with the user's preference**

> **User:** I prefer option 2 over your recommendation.
>
> **Claude:** I'd like to understand your thinking. What draws you to option 2?
>
> **User:** The added complexity is fine for my use case — I need the flexibility it provides.
>
> **Claude:** That makes sense. The flexibility trade-off is worth it if you need it. Let me note: option 2 will require updating the examples section to show the new flexibility in action. Does that work for you?
>
> **User:** Yes, that's fine.
>
> **Claude:** You'd like to go with option 2, which adds flexibility at the cost of some complexity, and we'll update examples accordingly. Correct?
>
> **User:** Correct.
>
> **Claude:** Here's the current version of the section we're changing:
>
> [Shows current version]
>
> Here's the proposed change:
>
> [Shows change]
>
> This adds [specific flexibility] while [specific complexity cost]. Ready to implement?

**Why it's good:** Claude asked for reasoning, learned context it didn't have, noted implications, confirmed understanding, and presented the change for approval.

---

### Scenario: Assessment reveals skill needs a rewrite

**BAD: Patching a broken foundation**

> **Claude:** I've identified several weaknesses across the entire skill. Let me present options for each...
>
> [Proceeds with extensive dialogue about incremental fixes to nearly every section]

**Why it's bad:** When weaknesses span most of the skill, incremental fixes create a patchwork. The hand-off check was skipped.

**GOOD: Recognizing when to hand off**

> **Claude:** I've completed the assessment. I found weaknesses in most sections of the skill — the frontmatter, the core instructions, and the examples all have significant issues. Before we proceed, I need to check if this skill should be improved or rebuilt.
>
> - Is less than ~20% worth preserving? **Checking...** The structure is sound, but the instructions are mostly outdated. Maybe 30% is solid.
> - Was the core purpose wrong? **Checking...** The purpose is valid, but the approach doesn't match current standards.
> - Does the existing skill confuse more than help? **Checking...** The outdated instructions could lead Claude astray. Yes, this is a concern.
>
> My assessment: This skill is on the boundary. We could improve it incrementally, but starting fresh with creating-skills might produce a better result faster.
>
> Options:
> 1. **Improve incrementally** — Address the most critical weaknesses. The skill will be better but still imperfect.
> 2. **Hand off to creating-skills** — Start fresh, using this skill's purpose and working elements as input.
>
> I lean toward option 2 because the rewrites would touch nearly every section. What would you prefer?

**Why it's good:** Claude recognized the pattern (weaknesses across most sections), completed the hand-off check explicitly, presented the boundary case honestly, and gave the user the decision.

---

### Scenario: User proposes their own approach

**BAD: Evaluating superficially and proceeding**

> **User:** What if instead we just removed that whole section?
>
> **Claude:** That could work. Let me remove it.
>
> [Makes the edit]

**Why it's bad:** Claude didn't evaluate the user's proposal against the same criteria (trade-offs, risks) as the generated options. No approval was sought before editing.

**GOOD: Treating user proposals seriously**

> **User:** What if instead we just removed that whole section?
>
> **Claude:** Let me evaluate that against the same criteria:
>
> **Removal approach:**
> - Gains: Simplifies the skill; eliminates the problem entirely
> - Costs: Loses the functionality that section provided — specifically [X]
> - Risk: If users expect that functionality, they'll be confused when it's missing
>
> Before we proceed — is the functionality in that section something you actually use? Or is it vestigial?
>
> **User:** It's vestigial. We haven't used it in months.
>
> **Claude:** In that case, removal is cleaner than fixing it. Here's what we'd remove:
>
> [Shows the section]
>
> This eliminates [X functionality]. You've confirmed this is unused. Ready to proceed?
>
> **User:** Yes.
>
> **Claude:** [Makes the edit]

**Why it's good:** Claude evaluated the user's proposal rigorously, asked a clarifying question that changed the risk assessment, and got explicit approval before editing.

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

### Skill Seems Too Broken to Assess

**Symptom:** The skill is so problematic that structured assessment feels pointless.

**Cause:** The skill may need a complete rewrite rather than improvement.

**Fix:**
1. Complete the hand-off check explicitly:
   - Is less than ~20% worth preserving?
   - Was the core purpose wrong?
   - Does the existing skill confuse more than help?
2. If yes to any, recommend hand-off: "This skill has fundamental issues that improvement can't address. I recommend switching to creating-skills to rebuild from the problem statement. Would you like to do that?"
3. If the user wants to improve anyway, respect that — but set expectations: "We can make improvements, but the skill will still have structural limitations."

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

### Changes Break Something During Implementation

**Symptom:** While implementing an approved change, you realize it breaks something else.

**Cause:** The change has dependencies you didn't anticipate.

**Fix:**
1. Stop immediately — do not try to fix it silently
2. Surface the problem: "While implementing [change], I noticed it breaks [X]"
3. Present options:
   - Adjust the change to avoid the break
   - Accept the break as a trade-off
   - Revert to a different option
   - Skip this change entirely
4. Get user decision before proceeding

---

### Can't Determine the Skill Type

**Symptom:** The skill doesn't clearly fit discipline, technique, pattern, or reference.

**Cause:** Most skills blend types. The skill may also be poorly defined.

**Fix:**
1. Identify the dominant behavior: What does the skill primarily do?
2. Use the skills-guide.md decision table: Which row best describes the skill's core purpose?
3. If genuinely ambiguous, name the blend: "This skill is primarily [X] with [Y] elements"
4. Assess against standards for the dominant type, borrowing from secondary types as relevant

---

### User Keeps Adding New Weaknesses Mid-Process

**Symptom:** During dialogue, the user identifies additional issues you didn't catch.

**Cause:** The user knows their skill better than you do. This is valuable input.

**Fix:**
1. Acknowledge: "Good catch — I missed that"
2. Add to the list: "I'll add this as weakness [N+1]"
3. Ask about ordering: "Would you like to address this now, or after we finish the current weakness?"
4. If it changes earlier decisions, flag it: "This might affect our decision on [earlier weakness]. Should we revisit?"

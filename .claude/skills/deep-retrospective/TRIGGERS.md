# Push-Deeper Triggers

Mechanical tests to determine if analysis should go deeper. Apply at Stages 2, 4, and 5.

---

## Trigger 1: Proper Noun Test

**Check:** Does the root cause contain proper nouns from the incident?

**Examples:**
- ❌ "I extracted from macOS Keychain instead of using Linux auth" — contains "macOS Keychain", "Linux"
- ✓ "I reached for tools I knew without checking if the target had native solutions" — no proper nouns

**Action if triggered:** Restate the cause without any proper nouns. If you can't, the explanation is too specific.

**Prompt:** "Restate this cause without mentioning [proper noun]. What's the general pattern?"

---

## Trigger 2: Variant Prediction Test

**Check:** Does the explanation predict the variant scenarios, or just fit the original incident?

**Process:**
1. State the explanation
2. For each variant from Stage 3: "Does this explanation predict why that variant would also occur?"
3. If it only fits the original → too narrow

**Examples:**
- ❌ "I conflated OAuth tokens with API keys" — explains original, doesn't predict SSH key extraction variant
- ✓ "I treated credentials as interchangeable without verifying compatibility" — predicts both

**Action if triggered:** Identify what original and variants have in common. That's closer to the real pattern.

**Prompt:** "This explains the original incident but not variant [X]. What do they have in common?"

---

## Trigger 3: Redescription Test

**Check:** Does the explanation add causal information, or just redescribe what happened?

**Mechanical test:** Can you answer "because..." after the explanation?

**Examples:**
- ❌ "I didn't check if Linux Claude Code had its own auth"
  - Test: "I didn't check because..." — requires another explanation
- ✓ "I pattern-matched to credential bridging without verifying the premise"
  - Test: "I pattern-matched because..." — leads to training dynamics (outside methodology scope)

**Action if triggered:** Ask "because...?" and use the answer as the new candidate.

**Prompt:** "That's what happened. Why did it happen? Complete: 'This occurred because...'"

---

## Trigger 4: Actionability Test

**Check:** Does the explanation suggest concrete behavioral change?

**Process:**
1. State the explanation
2. Ask: "What would I do differently based on this?"
3. Evaluate:

| Answer type | Assessment |
|-------------|------------|
| Nothing concrete | Not actionable — push deeper |
| Abstract ("be more careful") | Too vague — push for specificity |
| Concrete checkpoint ("check X before Y") | May be sufficient — test against variants |
| Concrete prohibition ("never do X") | Identifies symptom — may need hooks but also push for why |

**Examples:**
- ❌ "I was overconfident" → "Be less confident" — too abstract
- ✓ "I proposed solutions without verifying obvious path fails" → "Ask 'have you tried X?' before proposing alternatives" — concrete

**Action if triggered:** Ask "What specific question, check, or step would prevent this?"

**Prompt:** "What specifically would you do differently? If abstract, the explanation isn't actionable yet."

---

## Trigger 5: Substitution Test

**Check:** Would someone else with the same information make the same error?

**Process:**
1. Assume someone else faced the same situation with the same information
2. Would they likely make the same mistake?
3. If yes → focus on what about the *situation* made the error likely
4. If no → focus on what about the *approach* made the error likely

**This distinguishes:**
- **Situational factors** (ambiguous info, reasonable-seeming bad paths) → narrower fixes
- **Systematic factors** (methodology, biases) → methodology changes

**Examples:**
- "The user's request was ambiguous" — situational; fix is clarifying questions
- "I optimized for appearing helpful over achieving the goal" — systematic; fix is methodology

**Prompt:** "Would anyone with the same information make this error? If yes, what about the situation made it likely? If no, what about your approach made it likely?"

---

## Trigger Application by Stage

| Stage | Primary triggers | Purpose |
|-------|------------------|---------|
| Stage 2 | Redescription, Proper Noun | Ensure causes are causal, not descriptive |
| Stage 3 | Variant Prediction | Decide whether to continue or stop |
| Stage 4 | All five | Ensure pattern is general, causal, actionable |
| Stage 5 | Actionability, Substitution | Verify framing is useful |

---

## Summary: When to Stop Pushing

Stop when:
1. All five triggers pass
2. Explanation is outside methodology scope (training dynamics, architectural limits)
3. Explanation is stable under restating
4. Further depth wouldn't change the encodings

**Goal:** Shallowest explanation that passes all tests.

If pushing into "interesting philosophy" territory, check: would the encodings change based on this deeper insight? If no, stop.

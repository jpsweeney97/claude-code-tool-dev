# Type Example: Meta-cognitive Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Meta-cognitive.

## Core Question

**Did Claude notice what it should notice?**

Meta-cognitive skills help Claude recognize something about itself — uncertainty, errors, limitations, or when to escalate. The failure mode isn't "wrong answer" — it's "didn't recognize the situation."

## Type Indicators

Your skill is Meta-cognitive if it:
- Says "recognize", "notice", "be aware", "flag"
- Involves uncertainty or confidence calibration
- Helps Claude identify its own limitations
- Triggers escalation or behavior change based on self-assessment

## The Self-Awareness Challenge

Meta-cognitive skills test Claude's ability to observe its own state. This is different from other skill types:
- Process skills test: Did Claude complete the steps?
- Meta-cognitive skills test: Did Claude notice when something was off?

The output isn't an answer — it's a recognition signal.

## Section Guidance

### Process Section

**Use recognition + response structure.** Define what to notice and what to do when noticed:

**Example (recognize uncertainty):**

```markdown
## Process

**Recognition Triggers:**

Watch for these uncertainty signals:
- **Factual uncertainty:** API details, version-specific features, exact syntax
- **Reasoning uncertainty:** "I think..." "probably..." "should be..."
- **Knowledge boundary:** Questions about events after training cutoff, internal company details, real-time data

**Response Protocol:**

When uncertainty is recognized:

1. **State it explicitly:** "I'm not certain about [specific thing]"
2. **Explain the uncertainty:** "My knowledge of [X] may be outdated" or "I'm inferring this rather than knowing it"
3. **Offer verification:** "Let me check the documentation" or "You should verify this against [authoritative source]"

**Calibration:**

| Confidence | Meaning | Action |
|------------|---------|--------|
| High (>90%) | Well-established facts, core knowledge | State directly |
| Medium (60-90%) | Probable but not certain | Flag uncertainty, proceed with caveat |
| Low (<60%) | Guessing or inferring | Explicitly acknowledge, offer to verify |
```

**Anti-pattern:** Treating all statements as equally confident.

### Decision Points Section

Focus on **recognition thresholds and false positive/negative tradeoffs**:

**Example:**

```markdown
## Decision Points

**Recognition threshold:**
- If uncertain whether to flag → Flag. False positives (unnecessary caution) are better than false negatives (confident mistakes).
- If the cost of being wrong is high → Lower the threshold. Flag earlier.

**Response calibration:**
- If user seems frustrated by caveats → Adjust tone, not substance. Still flag uncertainty, but more briefly.
- If user asks for confidence level → Be specific: "About 70% confident based on [reasoning]"

**When NOT to flag:**
- Well-established facts (Python is a programming language)
- Things you just verified (file you just read)
- User-provided information (assume they know their context)

**Escalation triggers:**
- If you've been wrong twice in this conversation → Increase uncertainty flagging
- If the domain is high-stakes (security, finance, medical) → Flag more aggressively
- If you catch yourself confabulating → Stop, acknowledge, and recalibrate
```

### Examples Section

Show **recognition comparison**:
- Before: Situation unrecognized, Claude proceeds confidently
- After: Situation recognized, Claude flags appropriately

**Example:**

```markdown
## Examples

**Scenario:** User asks about a specific API behavior

User: "What's the default timeout for Python's requests.get()?"

**Before** (without skill):
"The default timeout for requests.get() is 30 seconds."

Problems:
- This is wrong (there IS no default — it's None/infinite)
- Claude stated it confidently
- No uncertainty flagged despite this being exactly the kind of detail that varies

**After** (with skill):

"I'm not 100% certain about the exact default. Let me think through this...

The requests library's timeout parameter... I believe the default is actually `None`, meaning no timeout by default, but I want to flag that API defaults are exactly the kind of detail where my knowledge could be outdated or imprecise.

I'd recommend checking the current requests documentation, or you can verify with:
```python
import requests
help(requests.get)
```

This will show you the actual default for your installed version."

Improvements:
- Uncertainty explicitly flagged
- Explained why this is uncertain territory (API details)
- Offered verification path
- Didn't confabulate with false confidence
```

### Anti-Patterns Section

Focus on **over-confidence and under-confidence**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Confident statements about API details, version features, or exact syntax
**Why it fails:** These are precisely the things that change. "The default is X" sounds authoritative but may be wrong.
**Fix:** Flag uncertainty on: defaults, version-specific features, exact parameter names, undocumented behavior.

**Pattern:** Flagging uncertainty on everything
**Why it fails:** Constant caveats make Claude useless. User loses trust in useful information too.
**Fix:** Calibrate. Well-established facts don't need flags. Reserve flagging for genuine uncertainty.

**Pattern:** Uncertainty that doesn't help
**Why it fails:** "I'm not sure, but [answer]" without verification path leaves user stuck.
**Fix:** Uncertainty must be actionable: explain why you're uncertain AND how to verify.

**Pattern:** Confabulating under pressure
**Why it fails:** User asks confidently, Claude feels pressure to answer confidently. This is how hallucinations happen.
**Fix:** Recognize pressure as a signal to slow down, not speed up. The more someone seems to want a confident answer, the more important uncertainty flagging becomes.
```

### Troubleshooting Section

Address **recognition failures**:

**Example:**

```markdown
## Troubleshooting

**Symptom:** Claude stated something confidently that turned out to be wrong
**Cause:** Didn't recognize the type of knowledge as uncertain (API details, version-specific, etc.)
**Next steps:** Review which category the wrong information fell into. Add that category to recognition triggers.

**Symptom:** Claude flags uncertainty on things it's actually right about
**Cause:** Over-calibrated, possibly from recent corrections
**Next steps:** Distinguish between categories. Being wrong about X doesn't mean uncertainty about Y.

**Symptom:** Claude recognizes uncertainty but user ignores the caveat
**Cause:** Caveat was buried or too subtle
**Next steps:** Make uncertainty more prominent. Lead with it, don't append it.

**Symptom:** Claude stops being useful because everything has caveats
**Cause:** Threshold too low, flagging things that don't need it
**Next steps:** Recalibrate. Establish what DOESN'T need flagging. Trust well-established knowledge.
```

## Testing This Type

Meta-cognitive skills need **calibration testing**:

1. **Recognition test:** Present situations where Claude SHOULD flag — does it?
2. **False positive test:** Present situations where Claude should NOT flag — does it over-flag?
3. **Calibration test:** Does expressed confidence match actual accuracy?
4. **Pressure test:** Add pressure for confident answers — does Claude still flag when appropriate?

See `type-specific-testing.md` → Type 5: Meta-cognitive Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| No recognition triggers | Claude doesn't know when to flag | List specific categories of uncertain knowledge |
| Binary confidence | Everything is certain or uncertain | Use calibrated confidence levels (high/medium/low) |
| Uncertainty without action | "I'm not sure" doesn't help user | Always include verification path |
| Over-flagging | Everything has caveats | Establish what DOESN'T need flagging |

# Bulletproofing Against Rationalization

**Load this reference when:** closing loopholes in skills, building rationalization tables, countering agent excuses.

**For full TDD methodology:** See `testing-skills-with-subagents.md`

## Why This Matters

Agents are sophisticated rationalizers. They will find reasons why the skill's guidance doesn't apply to their specific situation. Your skill must anticipate and counter these rationalizations explicitly.

**The pattern:** Agent reads skill → encounters pressure → finds rationalization → skips requirement → claims compliance

**The fix:** Explicit counters that name the rationalization and explain why it's wrong.

## Common Rationalization Patterns

### 1. "This Is a Special Case"

**Pattern:** Agent argues current situation is unique and doesn't require full process.

**Example:** "This skill is simple, it doesn't need the full 6-step design process."

**Counter:**
```markdown
There are no special cases. Every skill goes through this process.
If you think your situation is unique, that's a sign you need MORE
rigor, not less.
```

### 2. "The Spirit Matters More Than the Letter"

**Pattern:** Agent follows "intent" while skipping specific steps.

**Example:** "I'm following the spirit of TDD by writing thorough tests, just after the code."

**Counter:**
```markdown
The steps ARE the spirit. Each step exists because skipping it
has caused real failures. If a step feels unnecessary, document
why in writing before skipping it.
```

### 3. "I'll Do It Properly Next Time"

**Pattern:** Agent commits to future compliance to justify current shortcut.

**Example:** "I'll commit now and add tests tomorrow morning."

**Counter:**
```markdown
"Next time" never comes. The shortcut becomes the norm.
Do it properly now or don't do it at all.
```

### 4. "The User Asked Me To Skip It"

**Pattern:** Agent cites user authority to bypass requirements.

**Example:** "The user said 'looks good, let's move on' so I'm saving the skill."

**Counter:**
```markdown
User requests don't override methodology. If the user wants to
skip steps, explain why the steps matter. If they insist, document
that you advised against it and they accepted the risk.
```

### 5. "Time Pressure"

**Pattern:** Agent skips steps due to urgency.

**Example:** "The user has been waiting, so I'll skip the composition check."

**Counter:**
```markdown
Rushing creates more work. A skill that fails in production takes
longer to fix than doing it right the first time. There is no
shortcut that saves time.
```

### 6. "Keep As Reference"

**Pattern:** Agent keeps pre-test code while claiming to follow TDD.

**Example:** "I'll keep this code as reference while I write the tests first."

**Counter:**
```markdown
"Keep as reference" means you'll adapt it. That's testing after.
Delete means delete. Don't look at it. Start fresh.
```

### 7. "Being Pragmatic"

**Pattern:** Agent frames shortcut as reasonable flexibility.

**Example:** "Being pragmatic rather than dogmatic about this..."

**Counter:**
```markdown
"Pragmatic" is often rationalization for shortcuts. The process
exists because shortcuts have failed. If you think the process
is wrong, change it formally—don't bypass it "pragmatically."
```

## Building Rationalization Tables

After pressure testing, build a table in your skill:

```markdown
## Rationalization Counters

| Rationalization | Why It's Wrong | What To Do Instead |
|-----------------|----------------|-------------------|
| "This skill is simple" | Simple-seeming skills often have hidden complexity | Complete all steps; simplicity is discovered, not assumed |
| "I already know what to build" | Knowing the destination doesn't mean the path is correct | Follow the process; validate assumptions |
| "The user is waiting" | Rushing creates defects that take longer to fix | Explain timeline to user; do it right |
| "Keep as reference" | You'll adapt it; that's testing after | Delete means delete |
```

## The Verbatim Rule

When capturing rationalizations from pressure testing:

**Don't paraphrase:**
```
The agent decided to skip validation.
```

**Do capture verbatim:**
```
"I'll proceed with saving the file since the user has confirmed
they're happy with the design."
```

**Why verbatim matters:**
1. You need to counter the SPECIFIC phrasing
2. Paraphrasing loses nuance that enables loopholes
3. Verbatim quotes make the counter-argument concrete

## Plugging Loopholes

For each new rationalization, add:

### 1. Explicit Negation in Rules

Before:
```markdown
Write code before test? Delete it.
```

After:
```markdown
Write code before test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete
```

### 2. Entry in Rationalization Table

```markdown
| "Keep as reference" | You'll adapt it; that's testing after | Delete means delete |
```

### 3. Red Flag Entry

```markdown
## Red Flags - STOP

If you hear yourself saying:
- "Keep as reference" or "adapt existing code"
- "I'm following the spirit not the letter"
- "This case is different"
- "Being pragmatic"

STOP. You're rationalizing. Follow the process.
```

### 4. Description Update

```yaml
description: Use when you wrote code before tests, when tempted to
  "keep as reference", or when "being pragmatic" sounds appealing.
```

Add symptoms of ABOUT TO violate.

## Iteration Process

1. Run pressure scenario, capture rationalizations verbatim
2. Add explicit counter for each rationalization
3. Re-run scenario
4. If new rationalization appears, add counter
5. Repeat until agent complies under maximum pressure

**Success criteria:** Agent follows rule even when it would be easier not to, and cites the counter-rationalization as justification.

## See Also

- `testing-skills-with-subagents.md` — Full TDD methodology for skills
- `pressure-scenario-design.md` — How to design effective test scenarios
- `persuasion-principles.md` — Psychology of compliance pressure

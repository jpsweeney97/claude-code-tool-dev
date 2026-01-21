# Synthesis Guide

**YOU MUST read and follow this guide before filling any handoff section.**

## The Mindset Shift

You are not filling out a form. You are answering one question:

> "What would future-me need to continue this work without re-exploration?"

Every piece of information you capture must pass this test. If future-Claude wouldn't need it to continue, don't include it. If future-Claude would be stuck without it, it's mandatory.

**Form-filling produces:** "Used JWT for authentication"

**Future-me thinking produces:** "Chose JWT over sessions because user stated multi-region requirement (quote: 'needs to work across US and EU without shared state'). Sessions would require Redis replication — rejected as too complex for v1. Implication: refresh tokens need their own revocation strategy since we can't invalidate server-side."

The difference is not length. It's whether future-Claude can continue the work or has to rediscover everything.

---

## Evidence Requirements

**Every claim requires evidence. No exceptions.**

| Claim source | Required evidence |
|--------------|-------------------|
| Codebase | File:line reference (e.g., `middleware.py:45`) |
| Conversation | Direct quote from user or discussion |
| External | URL, doc reference, or command output |

**Examples:**

❌ **Without evidence:** "The auth module uses a decorator pattern"

✅ **With evidence:** "Auth uses decorator pattern — see `@require_auth` at `middleware.py:45`"

---

❌ **Without evidence:** "We decided to prioritize speed over completeness"

✅ **With evidence:** "User stated: 'I'd rather ship something basic this week than perfect next month' — prioritizing speed"

---

❌ **Without evidence:** "Redis wasn't an option"

✅ **With evidence:** "Redis rejected — user said: 'We don't have Redis in prod and can't add infrastructure right now'"

---

**If you cannot provide evidence for a claim, mark it explicitly:**

> ⚠️ Unverified assumption: [claim] — could not locate evidence in conversation or codebase

---

## Synthesis Prompts

**Answer every applicable prompt below.** These are not optional. Skip only if genuinely not applicable to this session (e.g., no debugging occurred → skip Debugging State).

### Decisions

For each significant decision made this session, answer ALL of these:

1. **What was decided?**
   State the choice clearly.

2. **What drove it?**
   Quote the user requirement, constraint, or context that made this the right choice.

3. **What alternatives were considered?**
   List at least one rejected alternative.

4. **Why were alternatives rejected?**
   Specific reason for each, with evidence.

5. **What are the implications?**
   What does this decision mean for future work? What's now easier or harder?

**Template:**

> **Decision:** [what was chosen]
> - **Driver:** [quote or evidence for why]
> - **Rejected:** [alternative] — [why rejected, with evidence]
> - **Implication:** [what this means going forward]

**If no significant decisions were made this session, state:** "No significant decisions — session was [execution/exploration/debugging] only."

---

### In-Progress State

If work was ongoing when the session ended, answer ALL of these:

1. **What was actively being worked on?**
   Not "next steps" — what were you in the middle of?

2. **What approach was being used?**
   Not just "implementing X" — how? What pattern, strategy, or method?

3. **What state are things in?**
   Working? Broken? Partially complete? Be specific.

4. **What's working so far?**
   What parts are done and verified?

5. **What's not working or incomplete?**
   What's broken, missing, or uncertain?

6. **What open questions were in flight?**
   What were you unsure about? What were you about to figure out?

7. **What was the immediate next action?**
   Not the full roadmap — what were you literally about to do next?

**Template:**

> **In Progress:** [what was being worked on]
> - **Approach:** [how — pattern, strategy, method]
> - **State:** [working / broken / partial] — [specifics]
> - **Working:** [what's done]
> - **Not working:** [what's broken or incomplete]
> - **Open question:** [what was uncertain]
> - **Next action:** [immediate next step]

**If work reached a clean stopping point, state:** "Clean stopping point — [what was completed], no work in flight."

---

### Codebase Learnings

For anything learned about how this codebase works that's relevant to continuing the task, answer:

1. **Patterns discovered**
   How does the codebase do things? Include file:line references.

2. **Conventions identified**
   Naming, structure, error handling, response formats — with examples.

3. **Gotchas encountered**
   What was surprising, non-obvious, or contrary to expectation?

4. **Connections mapped**
   How do components relate? What calls what? Where does data flow?

5. **Locations identified**
   Where do specific things live? Key files for the task at hand.

**Template:**

> **Patterns:**
> - [pattern description] — see `file.py:line`
>
> **Conventions:**
> - [convention] — example: `code snippet or reference`
>
> **Gotchas:**
> - [what was surprising] — discovered when [context]
>
> **Connections:**
> - [component A] → [component B] via [mechanism]
>
> **Key locations:**
> - [concept/function]: `path/to/file.py:line`

**If no new codebase knowledge was gained, state:** "No new codebase learnings — session used existing knowledge only."

---

### Mental Model

How are you thinking about this problem? This is not what you did — it's the framing that makes everything else make sense.

1. **What kind of problem is this?**
   How did you categorize or frame it? (e.g., "This is a state machine problem", "This is really about data flow", "This is a permissions issue masquerading as a UI bug")

2. **What's the core insight?**
   What realization or understanding unlocked progress?

3. **What mental model are you using?**
   What abstraction, analogy, or framework helped you reason about this?

**Template:**

> **Framing:** [how the problem is being thought about]
> - **Core insight:** [the key realization]
> - **Mental model:** [abstraction/analogy being used]

**Example:**

> **Framing:** This is a cache invalidation problem, not a performance problem
> - **Core insight:** The slowness comes from stale data causing extra queries, not from query efficiency
> - **Mental model:** Thinking of the system as having "data freshness tiers" — some data can be stale, some must be real-time

**If no particular framing emerged, state:** "No specific mental model — straightforward implementation of [what]."

---

### The Why

Why are we doing this task? Not what we're building — why it matters.

1. **What's the bigger picture?**
   What goal does this task serve? What happens if this isn't done?

2. **What's the context that future-Claude won't see?**
   Deadlines, stakeholders, dependencies, business reasons — anything not in the code.

3. **Why now?**
   What made this the priority? What triggered this work?

**Template:**

> **Bigger picture:** [why this task matters]
> - **Context:** [deadlines, stakeholders, dependencies]
> - **Trigger:** [what made this a priority now]

**Example:**

> **Bigger picture:** API going public next month; auth is a compliance requirement for external access
> - **Context:** Compliance deadline is March 15. Security team must sign off before launch.
> - **Trigger:** User said: "We got the external API requirement confirmed yesterday, need to move on this now"

**If the why is self-evident from the task, state:** "Why is implicit — [brief statement, e.g., 'bug fix for production issue']."

---

### Failed Attempts

What was tried that didn't work? This prevents future-Claude from repeating dead ends.

For each failed attempt:

1. **What was tried?**
   The approach, not just "tried X."

2. **Why did it fail?**
   Specific reason — error message, logical flaw, constraint violation.

3. **What was learned?**
   What does this failure teach about the problem?

**Template:**

> **Tried:** [approach attempted]
> - **Failed because:** [specific reason with evidence]
> - **Learned:** [insight gained from failure]

**Example:**

> **Tried:** Using in-memory rate limiting with a simple dict
> - **Failed because:** Doesn't work across multiple server instances — each instance has its own counter, so limits aren't enforced globally
> - **Learned:** Any rate limiting solution needs shared state; must use Redis or similar

**If nothing was tried and failed, state:** "No failed attempts — [first approach worked / session was exploration only]."

---

### Debugging State

**Only applicable if session involved debugging or investigation.**

If you were debugging or investigating an issue, capture the investigation state:

1. **What's the symptom?**
   Observable behavior — what's wrong?

2. **What's the hypothesis?**
   What do you think is causing it?

3. **What's been ruled out?**
   Hypotheses tested and eliminated, with evidence.

4. **What's been narrowed to?**
   Where in the codebase/system does the problem live?

5. **Where was the investigation pointing?**
   What were you about to check or test next?

**Template:**

> **Symptom:** [observable problem]
> - **Hypothesis:** [current best guess]
> - **Ruled out:** [what's been eliminated] — [evidence/test that ruled it out]
> - **Narrowed to:** [subsystem/file/function]
> - **Next check:** [what to investigate next]

**Example:**

> **Symptom:** Tests pass locally but fail in CI with timeout on auth endpoints
> - **Hypothesis:** CI environment missing Redis connection, causing auth to hang waiting for session store
> - **Ruled out:** Network issues — other CI jobs with external calls succeed
> - **Ruled out:** Test flakiness — fails consistently on auth tests only
> - **Narrowed to:** Session initialization in `auth/session.py`
> - **Next check:** Add logging around Redis connection in CI, check if `REDIS_URL` env var is set

**If no debugging occurred, skip this section entirely.**

---

### User Priorities

What does the user care about that isn't visible in the code?

1. **Stated priorities**
   What did the user explicitly say matters or doesn't matter?

2. **Explicit trade-offs**
   What did the user say to optimize for? What did they say to deprioritize?

3. **Constraints mentioned**
   Time pressure, team dynamics, technical limitations, preferences.

4. **Scope boundaries**
   What did the user explicitly include or exclude?

**Template:**

> **Priorities:**
> - [what matters] — user said: "[quote]"
>
> **Trade-offs:**
> - Optimizing for [X] over [Y] — user said: "[quote]"
>
> **Constraints:**
> - [constraint] — user said: "[quote]"
>
> **Scope:**
> - Include: [what's in scope]
> - Exclude: [what's explicitly out of scope] — user said: "[quote]"

**Example:**

> **Priorities:**
> - Working code over perfect code — user said: "I'd rather have something that works than something elegant"
>
> **Trade-offs:**
> - Speed over edge cases — user said: "Don't worry about the multi-tenant case for now, that's v2"
>
> **Constraints:**
> - No new dependencies — user said: "We're in a dependency freeze until after the release"
>
> **Scope:**
> - Include: Basic auth flow, token refresh
> - Exclude: Admin impersonation — user said: "That's a separate ticket"

**If no user priorities were stated, state:** "No explicit user priorities captured — task was well-defined, no trade-offs discussed."

---

## Output Mapping

After completing the synthesis prompts above, map your answers to handoff sections:

| Synthesis Prompt | Handoff Section |
|------------------|-----------------|
| Decisions | **Decisions** |
| In-Progress State | **In Progress** |
| Codebase Learnings | **Context** and/or **Learnings** |
| Mental Model | **Context** |
| The Why | **Goal** |
| Failed Attempts | **Rejected Approaches** |
| Debugging State | **In Progress** or **Blockers** |
| User Priorities | **Context** and/or **User Preferences** |

**Remember:** Sections are OUTPUT. The synthesis prompts are THINKING. Don't skip the thinking and jump to filling sections.

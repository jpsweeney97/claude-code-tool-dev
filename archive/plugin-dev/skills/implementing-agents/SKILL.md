---
name: implementing-agents
description: Use when building an agent from a design, "implement this agent",
  "test agent triggering", "agent not triggering", "debug agent delegation",
  or "validate agent quality". For structure reference, see agent-development.
---

# Implementing Agents

Build agents using triggering-first development: verify Claude delegates before investing in system prompt quality.

## Pipeline Context

This skill is **Stage 3: Implement** in the agent development pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Build agent from design, validate triggering |
| Previous | `/brainstorming-agents` (design document) |
| Next | `/optimizing-plugins` or personal use |

## Prerequisites Check

Before proceeding, verify:

1. **Design document exists?**
   - If yes: "I see the design at `[path]`. Proceeding with implementation."
   - If no: "I don't see a design document. Should we start with `/brainstorming-agents`?"

2. **Design has required sections?**
   - Agent identifier
   - Triggering examples (2-4)
   - System prompt structure

If any section is missing, ask: "The design is missing [sections]. Should we complete it first?"

## Core Principle

> **TEST TRIGGERING BEFORE TUNING QUALITY.**
> If Claude won't delegate to your agent, perfecting the system prompt is wasted effort.

### Why This Order Matters

- System prompt only runs AFTER Claude decides to delegate
- Beautiful system prompt + bad triggering = agent never used
- Bad triggering is cheaper to fix than bad system prompt

## Three-Phase Validation

| Phase | What to Test | How to Test | Iterate On |
|-------|--------------|-------------|------------|
| **1. Triggering** | Does Claude delegate? | Ask tasks matching your examples | description/examples |
| **2. Quality** | Does agent produce good output? | Invoke agent explicitly by name | system prompt |
| **3. Harden** | Edge cases, false positives? | Various phrasings, edge scenarios | both |

## Phase 1: Triggering (RED/GREEN)

**Goal:** Verify Claude knows when to delegate to your agent.

### Step 1: Create the agent file

Create `agents/<agent-name>.md` with:
- Frontmatter (name, description with examples)
- System prompt body

### Step 2: Write triggering test cases

Based on your design examples, create test prompts:

```markdown
| Test Prompt | Expected Behavior |
|-------------|-------------------|
| [Prompt matching example 1] | Claude delegates to agent |
| [Prompt matching example 2] | Claude delegates to agent |
| [Prompt that should NOT trigger] | Claude handles directly |
```

### Step 3: Run triggering tests

For each test prompt:
1. Send the prompt to Claude
2. Observe: Does Claude delegate to the agent?
3. Record result: PASS (delegated) or FAIL (didn't delegate)

### Step 4: Iterate on description/examples

**If Claude doesn't delegate (FAIL):**
- Add more examples covering the phrasing you used
- Make existing examples more specific
- Check that keywords from test prompt appear in examples

**If Claude delegates when it shouldn't (false positive):**
- Make examples more specific
- Add negative examples showing when NOT to use
- Narrow the description scope

**Continue until all triggering tests pass.**

## Phase 2: Quality

**Goal:** Verify the agent produces good output.

### Step 1: Invoke agent explicitly

Bypass triggering by invoking directly:
```
Use the <agent-name> agent to [specific task]
```

### Step 2: Evaluate output

| Check | Question |
|-------|----------|
| Completeness | Did it do everything requested? |
| Correctness | Is the output accurate? |
| Format | Is output structured as expected? |
| Boundaries | Did it stay within scope? |

### Step 3: Iterate on system prompt

**Common fixes:**
- Add missing instructions
- Clarify ambiguous guidance
- Add examples within system prompt
- Strengthen quality checks

**Continue until output quality is acceptable.**

## Phase 3: Harden

**Goal:** Ensure robustness across edge cases.

### Step 1: Test varied phrasings

Same intent, different words:
- "Review this code" vs "Check my code" vs "Look at this PR"
- All should trigger (or not trigger) consistently

### Step 2: Test edge cases

| Edge Case | Test |
|-----------|------|
| Boundary conditions | Tasks at the edge of agent's scope |
| Ambiguous requests | Tasks that could go either way |
| Combined requests | Tasks mixing agent's domain with others |

### Step 3: Document hardening results

Record any issues found and fixes applied.

## Three Triggering Failure Modes

| Failure Mode | Symptom | Fix |
|--------------|---------|-----|
| **Not triggering** | Claude ignores agent | Add more examples covering different phrasings |
| **Triggering too often** | Agent fires inappropriately | Make examples more specific, add negative examples |
| **Wrong scenarios** | Agent fires for wrong tasks | Revise examples to show only correct scenarios |

## Checklist

**Use TodoWrite to create todos for each item.**

**Phase 1: Triggering**
- [ ] Create agent file with frontmatter and system prompt
- [ ] Write triggering test cases (3+ scenarios)
- [ ] Run triggering tests
- [ ] All triggering tests pass

**Phase 2: Quality**
- [ ] Invoke agent explicitly (bypass triggering)
- [ ] Evaluate output against expectations
- [ ] Iterate on system prompt until quality acceptable

**Phase 3: Harden**
- [ ] Test with varied phrasings (3+ variations)
- [ ] Test edge cases at scope boundaries
- [ ] Check for false positives

**Deployment**
- [ ] Commit to git
- [ ] Verify agent appears in agent list

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Tuning system prompt first | Wasted if triggering fails | Test triggering FIRST |
| Testing only happy path | Misses false positives | Include negative cases |
| Generic test prompts | Don't match real usage | Use actual user phrasings |
| Skipping Phase 3 | Fragile agent | Always harden |

## Output

Working agent file in correct location:
- Plugin agent: `plugin-name/agents/<agent-name>.md`

Plus any updates to description/examples from triggering iteration.

## Next Step

Choose one and run:

| Situation | Command |
|-----------|---------|
| More components to build | `/brainstorming-{component}` for next component |
| Plugin complete, want polish | `/optimizing-plugins` |
| Personal use only | Done — agent is active |

## References

- agent-development — Structural reference (file format, frontmatter, tools)
- agent-development/references/triggering-examples.md — Example crafting guide
- brainstorming-agents — Design phase (if design needed)

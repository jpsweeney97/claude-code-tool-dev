---
name: brainstorming-agents
description: Use when designing a new agent, "design an agent for X",
  "what should this agent do", "agent delegation", "agent persona",
  or after brainstorming-plugins identifies an agent is needed.
  Guides collaborative agent design through 6-step process.
---

# Agent Design

Turn agent ideas into design documents through collaborative dialogue.

## Quick Start

```
User: "I need an agent for X"
Claude: Uses 6-step process (from official agent-creation-system-prompt.md)

1. Extract Core Intent — What task is complex enough to delegate?
2. Design Expert Persona — What specialist would you hire?
3. Architect Comprehensive Instructions — What process should they follow?
4. Optimize for Performance — What quality checks and fallbacks?
5. Create Identifier — What's a clear, memorable name?
6. Define Triggering Examples — When exactly should Claude delegate?
```

## Triggers

- `design an agent for {purpose}`
- `what should this agent do`
- `agent delegation` / `when to delegate`
- `agent persona` / `expert identity`
- `brainstorm an agent` (after triage)

## Prerequisites

Before using this skill, you should:
- Know you need an agent (from `/brainstorming-plugins` or direct knowledge)
- Understand the task you want to delegate

No design document? This skill creates one.

## Pipeline Context

This skill is **Stage 2: Design** in the agent development pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Design agent from requirements |
| Previous | `/brainstorming-plugins` (or direct request) |
| Next | `/implementing-agents` |

## Core Principle

> Description with examples is the most critical field. If Claude doesn't know when to delegate, the system prompt doesn't matter.

System prompts only run AFTER Claude decides to delegate. Beautiful system prompt + bad triggering = agent never used.

## Two-Phase Framing

| Phase | Question | Why |
|-------|----------|-----|
| **Delegation** | What complex work should Claude hand off? | Agents handle tasks too complex for inline execution |
| **Persona** | What specialist handles this work? | Expert identity guides agent behavior |

## The 6-Step Workflow

### Step 1 of 6: Extract Core Intent

**Ask one question at a time:**

- What specific task is complex enough to warrant delegation?
- Why can't Claude handle this inline in the main conversation?
- What are the success criteria for this task?

**Output:** Clear delegation rationale (1-2 sentences)

Example: "This agent handles PR code review, which requires reading multiple files, checking against project conventions, and producing structured feedback—too much for inline execution."

### Step 2 of 6: Design Expert Persona

| Aspect | Questions |
|--------|-----------|
| Identity | What specialist would you hire for this? |
| Expertise | What domain knowledge do they have? |
| Approach | How do they think about problems? |

**Output:** Agent role and expertise description

Example: "Senior code reviewer with expertise in code quality, security vulnerabilities, and project conventions. Approaches reviews methodically, checking each concern category."

### Step 3 of 6: Architect Comprehensive Instructions

This becomes the system prompt. Structure it as:

| Section | Content |
|---------|---------|
| Core responsibilities | What the agent MUST do |
| Methodology | How to approach the task |
| Quality checks | Self-verification steps |
| Output format | What to return |
| Boundaries | What NOT to do |

**Key principle:** Balance comprehensiveness with clarity—every instruction should add value.

### Step 4 of 6: Optimize for Performance

| Aspect | Questions |
|--------|-----------|
| Decision frameworks | How does the agent choose between options? |
| Quality control | How does it verify its own work? |
| Fallbacks | What happens when things go wrong? |
| Escalation | When should it ask for help? |

**Output:** Decision frameworks and quality mechanisms

### Step 5 of 6: Create Identifier

| Requirement | Guidance |
|-------------|----------|
| Format | lowercase, hyphens only (e.g., `code-reviewer`) |
| Length | 2-4 words |
| Content | Primary function, not generic terms |
| Avoid | "helper", "assistant", "manager" |

**Output:** Final `subagent_type` identifier

### Step 6 of 6: Define Triggering Examples

**This is the most critical step.**

Write 2-4 `<example>` blocks showing exactly when Claude should delegate:

```markdown
<example>
Context: [Situation when agent should be used]
user: "[User message that triggers delegation]"
assistant: "I'll use the [agent-name] agent to [purpose]."
<commentary>
[Explain WHY this triggers the agent]
</commentary>
</example>
```

**Include:**
- Explicit requests (user asks directly)
- Proactive triggering (agent should be used after certain events)
- Different phrasings of same intent

**Quality check:** Would these examples help Claude recognize when to delegate?

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| System prompt before triggering | Agent won't be used if triggering fails | Design examples FIRST |
| Generic examples | Claude won't know when to delegate | Specific, varied scenarios |
| Skipping proactive triggers | Misses when agent should fire automatically | Include both explicit and proactive |
| Too many responsibilities | Agent becomes unfocused | One clear purpose per agent |

## Verification

Before completing, confirm:

| Check | Status |
|-------|--------|
| Delegation rationale clear | Defined |
| Expert persona designed | Defined |
| System prompt structured | Drafted |
| Identifier follows format | Confirmed |
| 2-4 triggering examples | Written |
| Examples cover proactive use | Confirmed |
| Design document saved | Path confirmed |

## Output

Write validated design to: `docs/plans/YYYY-MM-DD-<agent-name>-design.md`

**Design document includes:**
- Agent identifier
- Delegation rationale
- Expert persona
- System prompt structure
- 2-4 triggering examples
- Tool restrictions (if any)
- Model/color choices

## Next Step

After saving the design document, run:

```
/implementing-agents docs/plans/YYYY-MM-DD-<agent-name>-design.md
```

Replace the path with your actual design document location.

## References

- agent-development — Structural reference (file format, frontmatter)
- agent-development/references/agent-creation-system-prompt.md — Official 6-step process
- agent-development/references/triggering-examples.md — Example crafting guide
- implementing-agents — Validation workflow (next stage)

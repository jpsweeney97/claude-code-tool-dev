---
name: ideating-extensions
description: Use when stuck generating Claude Code extension ideas, after a frustrating session where something felt annoying but you can't articulate what, or when deliberately exploring workflow improvements. Use when user says "I need extension ideas", "what should I build", "help me brainstorm extensions", or "I'm stuck on what to create".
argument-hint: "[focus-area]"
---

## Overview

Surfaces Claude Code extension ideas through structured dialogue. You describe your workflow and frustrations; Claude proposes specific, non-obvious extension ideas tailored to your actual context.

**The problem this solves:** Ideation is hard when you're too close to your own workflow (blind spots), don't know what's possible (scope uncertainty), or no one's asking the right questions (prompting gap).

**How it works:**
1. Discovery — Questions about workflow, recent frustrations, existing extensions
2. Proposal — Claude generates 3-5 ranked extension ideas based on what surfaced
3. Exploration — Dig deeper into selected ideas (feasibility, value, shape, risks)
4. Handoff — Offer to invoke the appropriate brainstorming-* skill for the selected idea

**Non-goals:**
- Teaching extension types abstractly (learn by doing, not lecture)
- Forcing exploration of unfamiliar extension types (follow the problem)
- Replacing brainstorming-skills/hooks/mcp/etc. (this is upstream ideation)

## When to Use

**Invoke this skill when:**
- Starting from zero — no extension ideas, need inspiration
- Vague notion — sense something could be better but can't articulate what
- Stuck in a rut — keep thinking of the same types of extensions
- Post-frustration — after a session where something felt annoying but you couldn't name it
- Exploration mode — deliberately setting aside time to think about workflow improvements
- Focused ideation — optionally pass a focus area (e.g., `/ideating-extensions testing`) to narrow discovery questions to that domain

**Do NOT invoke when:**
- You already know what to build — go directly to brainstorming-skills/hooks/mcp/etc.
- You want to learn about extension types — read documentation instead
- You have a specific, named problem AND know the extension type to solve it — use brainstorming-* directly (e.g., "I need a hook that validates X" → /brainstorming-hooks)

## Outputs

**Shortlist (Phase 3):**
3-5 ranked extension ideas, each with:
- Name, Type, Problem, Behavior, Fit

**Exploration summary (Phase 4, if requested):**
For each explored idea:
- Feasibility assessment (with confidence level)
- Value assessment
- Shape sketch (inputs, outputs, invocation)
- Risk notes

**Handoff brief (Phase 5):**
Summary suitable for passing to brainstorming-* skill:
- Problem statement
- Extension type
- Key behavior
- Constraints discovered

**Definition of Done:**
- Discovery completed (two consecutive low-yield question rounds)
- At least 3 ideas proposed (unless user explicitly wants fewer)
- Ideas are specific to user's workflow (not generic)
- User has selected an idea OR explicitly declined all
- If selected: handoff to appropriate brainstorming-* skill offered

## Process

**Protocol:** Thoroughness framework (vocabulary only — evidence/confidence levels)

### Phase 1: Context Gathering

**YOU MUST complete discovery before proposing ideas.** The skill's value is surfacing friction you didn't know you had. Skipping to Phase 3 produces generic ideas that waste everyone's time.

**If focus area provided:** Narrow workflow and friction questions to the specified domain (e.g., if `$ARGUMENTS` is "testing", ask specifically about testing workflows and friction). Still complete full discovery within that domain.

**Examine existing setup:**
- Use Glob to check `~/.claude/skills/`, `~/.claude/hooks/`, `.claude/skills/`, `.claude/hooks/` for existing extensions
- Note what types they've built (skills, hooks, agents, etc.)
- Identify gaps — extension types not represented
- If no extensions exist, note this as a blank slate — focus discovery on workflow friction rather than extension gaps

**Ask about workflow:** (one question at a time)
- What kind of work do you do most often?
- What tools/languages/frameworks do you use daily?
- Walk me through a typical session — what do you spend time on?

**Ask about friction:** (one question at a time)
- What felt annoying in your last few sessions?
- What do you do repeatedly that feels tedious?
- Where do you make mistakes or forget steps?
- What takes longer than it should?

**Probing:** If an answer hints at deeper friction (e.g., "I guess testing is slow"), probe once: "Tell me more about that — what specifically about testing?" Then move on regardless of depth. Don't interrogate.

**Convergence rule:** A "round" is one question and its answer. Continue asking until two consecutive rounds yield no new friction points or workflow details (i.e., answers repeat or generalize what was already said).

### Phase 2: Problem Synthesis

Before proposing ideas, synthesize what you've learned:

- **Friction points:** List specific pain points surfaced
- **Workflow patterns:** Recurring activities that could be improved
- **Extension gaps:** Types they haven't explored that might fit
- **Constraints:** Time, complexity tolerance, existing setup

Present this synthesis to confirm understanding before proceeding.

### Phase 3: Idea Generation

Generate 3-5 extension ideas. For each idea:

| Field | Content |
|-------|---------|
| Name | Descriptive working title |
| Type | skill / hook / agent / MCP server / plugin |
| Problem | Specific friction point it addresses |
| Behavior | What it would do (1-2 sentences) |
| Fit | Why this extension type suits this problem |

**Quality criteria for ideas:**
- Specific to their actual workflow (not generic)
- Non-obvious (they wouldn't think of it without help)
- Right abstraction (concrete enough to act on, not trivially specific)

**If focus area is too narrow:** If the focus area yields fewer than 3 ideas, broaden slightly or propose 2 ideas with a note: "The focused domain limits options — would you like to expand scope?"

**Ranking:** Order by estimated value-to-effort ratio based on what you know about their context.

### Phase 4: Deeper Exploration

For ideas the user wants to explore further, assess:

| Dimension | Questions |
|-----------|-----------|
| Feasibility | Is this buildable? What would it take? Dependencies? |
| Value | How much would this help? How often would it trigger? |
| Shape | What inputs/outputs? What would invocation look like? |
| Risks | What could go wrong? What might make this annoying? |

**Confidence labeling:** Mark assessments as High/Medium/Low based on how much you actually know vs. inferring.

### Phase 5: Handoff

Once an idea is selected:
1. Confirm which brainstorming-* skill applies (skills, hooks, mcp, etc.)
2. Summarize the idea in terms that skill can use
3. Offer to invoke that skill: "Would you like me to invoke /brainstorming-<type> to begin design?"

## Decision Points

**User impatient during discovery:**
- If user says "just give me ideas" before sufficient context → Acknowledge the impatience, then ask 2-3 more essential questions. "I hear you — a few more questions to make sure the ideas are relevant to your actual workflow."
- If user pushes back again → Proceed with what you have, but note reduced confidence in fit.

**Discovery isn't yielding friction:**
- If workflow questions don't surface pain → Shift to "what would you automate if it were easy?" hypotheticals.
- If still stuck → Ask about recent mistakes or things they forgot to do.

**All ideas feel generic:**
- If proposals sound like they could apply to anyone → Re-examine the workflow details. What's unique about their context?
- If nothing unique surfaces → Ask directly: "What makes your workflow different from a typical developer's?"

**User wants to explore multiple ideas:**
- If user is torn between 2-3 ideas → Explore all briefly (feasibility + value only), then recommend which to pursue first.
- Bias toward the one with clearest problem statement — ambiguous problems produce ambiguous designs.

**Extension type unclear:**
- If problem could be solved by multiple extension types → Present the options with tradeoffs. "This could be a hook (automatic, invisible) or a skill (guided, explicit). Which fits your preference?"
- If genuinely equivalent → Default to the simpler type.

**User rejects all ideas:**
- If none of the 3-5 ideas resonate → Ask what's missing. "What would a good idea look like? What's wrong with these?"
- If user can't articulate → Return to discovery. Something was missed.

## Examples

**Scenario:** User invokes the skill saying "I need extension ideas, I'm stuck"

### BAD: Generic proposal without discovery

**Claude's response:**
"Here are some extension ideas:
1. A commit message generator skill
2. A code review hook
3. A documentation generator
4. A test runner integration
5. An API client MCP server"

**Why it's bad:**
- No questions asked about user's actual workflow
- Ideas are generic (could apply to anyone)
- No ranking or fit explanation
- User likely already thought of these
- No connection to specific friction points

### GOOD: Tailored proposal after discovery

**Claude's discovery phase:**
- Learns user works primarily on CLI tools in Python
- Discovers user frequently forgets to update --help text when adding flags
- Notes user has only built skills, hasn't tried hooks
- Hears user complain about context-switching to check docs

**Claude's synthesis:**
"Based on our conversation:
- Main friction: forgetting to sync --help with actual flag behavior
- Secondary friction: context-switching to documentation
- Gap: you haven't explored hooks, which could catch the --help issue automatically"

**Claude's proposal:**
"Three ideas, ranked by value-to-effort:

1. **validating-cli-help** (hook)
   - Problem: Forgetting to update --help when flags change
   - Behavior: PreToolUse hook that compares argparse/click definitions to --help output, warns on mismatch
   - Fit: Hooks catch this automatically before commit — no discipline required

2. **context7-for-cli-libs** (MCP server)
   - Problem: Context-switching to check click/argparse docs
   - Behavior: MCP server wrapping Context7 with pre-configured CLI library lookups
   - Fit: MCP keeps docs in-session; you already use Context7

3. **cli-flag-changelog** (skill)
   - Problem: Tracking what flags changed across versions
   - Behavior: Skill that extracts flag definitions and diffs against previous release
   - Fit: Skills work well for on-demand analysis you run at release time"

**Why it's good:**
- Discovery surfaced specific friction (--help sync, docs context-switch)
- Ideas are specific to user's Python CLI workflow
- Extension types matched to problem characteristics
- Ranking explained with reasoning
- Includes unfamiliar type (hook) but justified by fit, not forced

## Anti-Patterns

**Pattern:** Proposing ideas before asking questions
**Why it fails:** Without context, ideas are generic. Generic ideas waste the user's time and erode trust in the skill.
**Fix:** Complete discovery until two consecutive low-yield rounds. Discovery is the skill's value.

**Pattern:** Asking about extension types instead of problems
**Why it fails:** "Would you like a hook or a skill?" puts the burden on the user. They came here because they don't know what to build.
**Fix:** Ask about workflow and friction. Infer the extension type from the problem.

**Pattern:** Forcing unfamiliar extension types
**Why it fails:** "You should try hooks since you've never built one" is curiosity-driven, not problem-driven. Unfamiliar types add learning overhead.
**Fix:** Follow the problem to the best-fit type. Mention unfamiliar types only when they genuinely fit better.

**Pattern:** Accepting "I don't know" and moving on
**Why it fails:** Friction is often invisible. "I don't know what's annoying" doesn't mean nothing is annoying — it means they've habituated.
**Fix:** Try different angles: recent mistakes, time sinks, things they do repeatedly, hypothetical magic wand.

**Pattern:** Stopping at the first good idea
**Why it fails:** The first idea that sounds reasonable isn't necessarily the best. Premature convergence is the main compliance risk.
**Fix:** Complete the full 3-5 idea generation before exploring any single idea in depth.

**Pattern:** Ideas at wrong abstraction level
**Why it fails:** "Improve your workflow" is too vague to act on. "Add a button that does X" is too specific to be interesting.
**Fix:** Ideas should name a specific problem AND a concrete behavior, but leave implementation details for brainstorming-*.

## Troubleshooting

**Symptom:** Claude proposes ideas immediately without asking questions
**Cause:** Skill pattern-matched "need ideas" to "give ideas" without following discovery phase
**Next steps:** Explicitly prompt: "Before proposing, ask me about my workflow and what's been frustrating lately."

**Symptom:** All proposed ideas feel generic or obvious
**Cause:** Discovery didn't surface enough specific context about user's actual workflow
**Next steps:** Return to discovery. Ask: "What's unique about how you work? What would a stranger not guess about your setup?"

**Symptom:** User can't articulate any friction points
**Cause:** Friction has become invisible through habituation
**Next steps:** Try indirect angles:
- "What did you do three times today that you'll do again tomorrow?"
- "If you had a magic wand, what would you automate first?"
- "What mistake did you make recently that you've made before?"

**Symptom:** Ideas don't match extension types well (e.g., "a hook that guides you through...")
**Cause:** Misunderstanding of extension type capabilities
**Next steps:** Review what each type does:
- Hooks: automatic checks/enforcement, run silently
- Skills: guided workflows, explicit invocation (commands merged into skills)
- Agents: delegated complex tasks
- MCP servers: external tool integrations
- Plugins: distributable bundles of the above

**Symptom:** User rejects all ideas but can't say why
**Cause:** Mismatch between user's unstated criteria and Claude's inferred criteria
**Next steps:** Ask directly: "What would make an idea feel right? Is it about effort, impact, novelty, or something else?"

**Symptom:** Deeper exploration reveals idea is infeasible
**Cause:** Surface-level appeal masked implementation complexity
**Next steps:** Not a failure — this is why exploration exists. Return to shortlist and explore the next idea.

## Extension Points

**Handoff to brainstorming-* skills:**
After exploration, the selected idea flows to the appropriate skill:
- Skills → `brainstorming-skills`
- Hooks → `brainstorming-hooks`
- Agents → `brainstorming-subagents`
- MCP servers → For now, use `brainstorming-skills` with MCP context; dedicated skill planned
- Plugins → For now, use `brainstorming-skills` with plugin context; dedicated skill planned

**Reference: Extension Pattern Guide**
The skill uses [references/extension-patterns.md](references/extension-patterns.md) to inform proposals — a guide covering:
- Problem archetypes and which extension types fit each
- Extension type capabilities and limitations
- Decision heuristics for matching problems to extensions

**Future integrations:**
- Could examine community extension repos for inspiration
- Could track which proposed ideas were actually built (feedback loop)
- Could learn from patterns in user's existing extensions

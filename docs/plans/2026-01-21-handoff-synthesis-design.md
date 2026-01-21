## Design Context: handoff-synthesis-guide

**Type:** Reference file for existing skill (quality enhancement)
**Risk:** Low — read-only, no external effects

### Problem Statement

Handoff synthesis is too shallow and generic. Claude treats the handoff as a form to fill out rather than asking "what would future-me need to continue this work?" Critical context is lost between sessions:

- Decision reasoning (just "used JWT" without tradeoffs, alternatives, implications)
- In-progress state (only "next steps" as future tasks, no capture of mid-task state)
- Codebase learnings (patterns, conventions, gotchas learned during session)
- Mental model / framing of the problem
- The "why" — bigger picture context
- Failed attempts (what didn't work and why)
- Debugging state (hypotheses, ruled out, narrowed to)
- User priorities and constraints

### Success Criteria

A new session can pick up where the previous left off with minimal re-exploration. The handoff captures:

1. **Decision depth** — tradeoffs, context, alternatives, implications — with evidence (quotes for conversation, file:line for code)
2. **In-progress state** — approach being used, what's working/not working, open questions, immediate next action
3. **Codebase learnings** — patterns, conventions, gotchas, connections, key locations — with file:line references
4. **Mental model** — how the problem is framed, core insight, abstraction being used
5. **The "why"** — bigger picture, deadlines/stakeholders, what triggered this work
6. **Failed attempts** — what was tried, why it failed, what was learned
7. **Debugging state** — symptom, hypothesis, ruled out, narrowed to, next check
8. **User priorities** — stated priorities, trade-offs, constraints, scope boundaries — with quotes

### Compliance Risks

| Risk | Mitigation |
|------|------------|
| "The session was simple, don't need deep synthesis" | Guide applies to ALL handoffs, no shortcuts |
| "I already know what to capture" | Strict requirement: MUST read and follow, not "consider" |
| "This is taking too long" | Guide structured as efficient prompts, not essays |
| "The sections cover this already" | Reframe: sections are OUTPUT, synthesis is THINKING |
| "I'll summarize the guide's intent" | Guide must be read each time, not recalled from memory |

### Rejected Approaches

1. **New standalone synthesis skill** — Rejected because skills can't cleanly pass structured data to each other. The Skill tool invokes inline, no "return value" pattern.

2. **Replace handoff entirely** — Rejected because handoff mechanics (storage, resume, archiving, state tracking) are solid. The problem is synthesis quality, not plumbing.

3. **Complementary skill user invokes separately** — Rejected because it adds coordination burden. User shouldn't need to remember "run synthesis, then run handoff."

### Design Decisions

1. **Reference file pattern** — Handoff references `synthesis-guide.md` which Claude MUST read before filling sections. This is the documented pattern for keeping SKILL.md focused while providing detailed guidance.

2. **Prompts not tips** — The guide is structured as questions Claude must answer, not suggestions to consider. This forces active thinking rather than allowing form-filling fallback.

3. **Evidence requirement** — All claims require backing: file:line for codebase, quotes for conversation. This prevents fabrication and makes handoffs verifiable.

4. **New "In Progress" section** — Added to section checklist because the existing structure had no place for mid-task state (only "Next Steps" as future tasks).

5. **Strict requirement language** — Handoff procedure says "YOU MUST read synthesis-guide.md completely" — not "consider reading" or "optionally consult."

### Artifacts Created

| Artifact | Location |
|----------|----------|
| Synthesis guide | `.claude/skills/handoff/synthesis-guide.md` |
| Updated handoff skill | `.claude/skills/handoff/SKILL.md` (v4.3.0) |
| Design context | `docs/plans/2026-01-21-handoff-synthesis-design.md` |

### Testing Approach

**Failure looks like:** Run `/handoff`, get shallow/generic output despite the guide existing.

**Success looks like:** Run `/handoff`, get output with:
- Evidence (quotes, file:line references)
- Decision depth (tradeoffs, alternatives, implications)
- In-progress state captured (if applicable)
- Codebase learnings captured (if applicable)

**Test approach:** Create a session with clear decisions, mid-task state, and codebase learnings. Run `/handoff`. Verify output includes evidence and depth for each dimension.

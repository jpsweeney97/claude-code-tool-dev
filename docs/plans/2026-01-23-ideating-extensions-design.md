## Design Context: ideating-extensions

**Type:** Solution Development
**Risk:** Low

### Problem Statement

User struggles to come up with Claude Code extension ideas in three situations:
- **Starting from zero** — no idea what to build, needs inspiration
- **Vague notion** — sense something could be better but can't articulate what
- **Stuck in a rut** — keeps thinking of the same types of extensions

The underlying blockers are:
- **No prompting** — needs questions to surface ideas
- **Scope uncertainty** — doesn't know what's possible with different extension types
- **Habituated friction** — has stopped noticing pain points in workflow

### Success Criteria

- Produces a shortlist of 3-5 ranked, specific, non-obvious extension ideas
- Ideas are tailored to user's actual workflow (not generic)
- Claude proposes ideas (user reacts) rather than user proposing (Claude refines)
- Supports deeper exploration of selected ideas (feasibility, value, shape, risks)
- Natural handoff to appropriate brainstorming-* skill for implementation

### Compliance Risks

- **Premature convergence** — grabbing the first decent idea without exploring alternatives
- **Question fatigue** — wanting output before sufficient discovery
- **Productivity guilt** — feeling like "real work" means building, not ideating

Mitigations:
- Convergence rule requires two low-yield rounds before proposing
- Decision points handle user impatience with grace (acknowledge, then continue)
- Skill framing positions ideation as productive work

### Rejected Approaches

- **Abstract teaching about extension types**: Rejected because learning by doing is more effective than lecture, and the skill should follow problems to extension types rather than starting from types.
- **Explicit mode branching (zero/vague/rut)**: Rejected in favor of letting the mode emerge naturally from conversation, which is simpler and adapts to reality.
- **Forcing exploration of unfamiliar extension types**: Rejected because curiosity-driven exploration adds learning overhead; following the problem to the best-fit type is more valuable.

### Design Decisions

- **Claude proposes, user reacts**: User explicitly wanted ideas proposed to them, not just questions that surface their own latent ideas. This shapes the skill as a generator, not just a facilitator.
- **Thoroughness framework (vocabulary only)**: Structured workflow with defined passes, using evidence/confidence levels, but not the full iterative protocol.
- **8-12 question discovery**: User preferred deeper exploration following the thoroughness framework rather than quick-shot ideation.
- **Extension pattern guide as reference**: Skill needs knowledge of problem-to-extension-type mapping to generate informed proposals. This lives in a reference file.
- **Handoff to brainstorming-* family**: This skill is upstream ideation; it produces what to build, then hands off to the appropriate brainstorming skill for how to build.

## Design Context: making-recommendations

**Type:** Process/Workflow
**Risk:** Low (writes files to docs/decisions/, bounded and reversible)

### Problem Statement

The current making-recommendations skill has four problems:
1. **Premature commitment** — Claude recommends too quickly without enough iteration/pressure-testing
2. **Missing convergence criteria** — No clear signal for when a recommendation is "ready" vs just "made"
3. **Stakes miscalibration** — Same process for trivial and high-stakes decisions
4. **Structural gaps** — Missing activities like null option, information gaps, sensitivity analysis

### Success Criteria

- Produces a Decision Record file following `decision-making.framework@1.0.0` template
- Saved to `docs/decisions/YYYY-MM-DD-<decision-slug>.md`
- Inline chat output: recommendation + summary reasoning
- Stakes-calibrated depth (adequate/rigorous/exhaustive)
- Explicit convergence indicators before claiming "ready"

### Compliance Risks

- **Premature convergence** — Claude claiming "stable" after one pass to exit early
- **Adversarial theater** — Going through the motions on pressure-testing without genuine challenge

### Countermeasures

1. **Iteration log requirement** — Must document what changed between passes; if nothing changed, must explain why convergence is valid
2. **Discomfort requirement** — Objections must cause discomfort if true; softball objections don't count
3. **Minimum pass requirements** — Adequate: 1, Rigorous: 2, Exhaustive: 3

### Entry Contexts

Two distinct contexts for skill invocation:
1. **Direct request** — User explicitly asks for a recommendation ("What should I use for X?")
2. **Mid-conversation pivot** — Claude has been exploring/asking questions, user says "make a recommendation"

For mid-conversation pivots: summarize prior understanding, confirm with user, then run full Entry Gate (prior conversation informs but doesn't skip steps).

### Rejected Approaches

- **File for rigorous/exhaustive only** — Rejected because even adequate decisions benefit from persistent records
- **User chooses file vs inline** — Rejected to avoid decision fatigue; always produce file
- **Skip thoroughness gate** — Rejected because weak evidence leads to poor recommendations

### Design Decisions

- **Always produce Decision Record file** — Even for adequate level, creates persistent artifact
- **Dual output** — File contains full analysis; chat contains recommendation + summary (user sees answer without opening file)
- **Thoroughness gate as hybrid** — Explicit check during Entry Gate that also blocks if option space unknown
- **Preserve adversarial lenses** — Keep the specific lenses from current skill (Kill it, Pre-mortem, Steelman, etc.)
- **Preserve and extend anti-patterns** — Keep existing anti-patterns, add new ones for convergence/iteration issues
- **Trivial decision exclusion** — Don't use skill when both scope AND reversibility are negligible (dual heuristic)

### Framework Integration

- **Protocol:** decision-making.framework@1.0.0
- **Relationship to thoroughness:** If option space unknown or evidence weak, recommend thoroughness exploration first (gate blocks or user overrides)

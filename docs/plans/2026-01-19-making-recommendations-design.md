## Design Context: making-recommendations

**Type:** Solution Development
**Risk:** Low (produces recommendations, no side effects)

### Problem Statement

Claude often recommends shallowly — jumping to familiar answers without exploring alternatives, missing second-order effects, applying a narrow lens, and not challenging its own thinking. Key failure modes:

- Over-confidently recommends things it doesn't know well
- Doesn't think through alternatives beyond the first set considered
- Missing second-order effects (downstream impacts)
- Narrow lens (missing big-picture perspectives)
- No devil's advocate / adversarial challenge
- Limited comparative analysis
- Bias, prematurity, unstated assumptions

### Key Design Decisions

1. **User-triggered only** — Invoked via `/recommend` or trigger phrases, not automatic. Avoids slowing down routine work.

2. **5-phase process** — Understand → Generate Alternatives → Evaluate → Adversarial Challenge → Recommend. Each phase must complete before the next.

3. **Adversarial framing is mandatory** — Six lenses: Kill the Recommendation, Pre-mortem, Steelman Alternatives, Challenge the Framing, Hidden Complexity, Motivated Reasoning Check.

4. **Output requirements** — Every recommendation must include: the choice, why this, why not others, tradeoffs accepted, assumptions, confidence level.

### Test Scenarios

1. **Shallow recommendation test:** Ask Claude to recommend a library without context. Skill should force Phase 1 (understand) before any recommendation.

2. **Adversarial bypass test:** Present an "obvious" choice. Skill should still require pre-mortem and steelmanning — no shortcuts for confident recommendations.

3. **Uncertainty flagging test:** Ask for recommendation in unfamiliar domain. Claude should explicitly flag uncertainty and knowledge limitations.

4. **Quick answer pressure test:** Ask for "just a quick recommendation." Claude should still surface top tradeoff and uncertainty, compressing output but not process.

### Rejected Approaches

- **Automatic activation:** Rejected because it would slow down routine responses. User-triggered keeps it focused.
- **Lighter-weight version:** Considered a "quick recommend" mode with fewer phases. Rejected because the adversarial phase is the core value — removing it defeats the purpose.
- **Formal ADR output:** Considered producing Architecture Decision Records. Rejected as too heavy for general recommendations; ADRs are for high-stakes architectural choices.

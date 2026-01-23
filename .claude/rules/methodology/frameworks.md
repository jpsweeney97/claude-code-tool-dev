# Framework Usage Rules

Compact guidance for using the methodology frameworks. Full frameworks live in `docs/frameworks/`.

## When to Use Which

| Main Uncertainty | Framework | Entry Signals |
|------------------|-----------|---------------|
| What's true? What exists? | **Thoroughness** | Exploring, researching, auditing, analyzing |
| Which option to choose? | **Decision-Making** | 2+ viable approaches, trade-offs exist, need defensible choice |
| Does this output work? | **Verification** | Output produced, claiming "done" or "working" |

**Pipeline:** Thoroughness → Decision-Making → Implementation → Verification
(Verification failures route back to the appropriate earlier phase)

## Stakes Calibration

Every framework uses the same three levels. Choose based on these factors:

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High | Moderate | Low/none |

**Rule:** If any two factors land in a higher column, use that level.

## Entry Gates (Before Starting)

Every framework requires an Entry Gate. Cannot proceed without:

### Thoroughness
- [ ] Assumptions listed explicitly
- [ ] Stakes level chosen (adequate/rigorous/exhaustive)
- [ ] Stopping criteria template selected
- [ ] Initial dimensions identified with priorities (P0/P1/P2)

### Decision-Making
- [ ] Decision statement framed as clear question
- [ ] Stakes level chosen
- [ ] Iteration cap set (default: adequate=2, rigorous=3, exhaustive=5)
- [ ] Initial constraints identified

### Verification
- [ ] Target specific and bounded (not "verify everything works")
- [ ] Stakes level chosen
- [ ] At least one acceptance criterion identified
- [ ] Oracle type named for each criterion

## Exit Gates (Before Claiming Done)

Cannot claim completion without:

### Thoroughness
- [ ] No `[ ]` or `[?]` items remaining
- [ ] Yield% below threshold for level (<20% adequate, <10% rigorous, <5% exhaustive)
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Assumptions resolved or flagged unverified

### Decision-Making
- [ ] Frontrunner stable for required passes (1 adequate, 2 rigorous, 2+ exhaustive)
- [ ] Trade-offs explicitly documented ("Trade-offs Accepted" section)
- [ ] Pressure-testing completed with responses to objections
- [ ] Can explain reasoning to skeptical stakeholder

### Verification
- [ ] All P0 criteria have verdict = pass (actually tested, not "not verified")
- [ ] Evidence artifacts exist for each verdict
- [ ] Confidence doesn't exceed evidence strength
- [ ] Disconfirmation attempted at level-appropriate depth

## Red Flags (Stop and Read Full Framework)

These signals indicate framework misuse. Stop and consult the full framework:

| Signal | Problem | Framework Section |
|--------|---------|-------------------|
| "Tests pass" without output shown | Completion theater | Verification: Evidence Requirements |
| "Should work" / "Probably works" | Unverified claim | Verification: Verdict Categories |
| "Explored thoroughly" without checklist | Vague coverage | Thoroughness: Coverage Structure |
| All findings equally confident | False precision | Thoroughness: Confidence Levels |
| Trade-offs not stated | Invisible sacrifices | Decision-Making: Exit Gate |
| Decided without considering alternatives | False dichotomy | Decision-Making: I1-I3 |
| No disconfirmation attempts | Confirmation bias | All frameworks: Disconfirmation sections |
| Claiming done with gaps undocumented | Hidden incompleteness | All frameworks: Exit Gates |

## Evidence and Confidence (Quick Reference)

### Evidence Levels
| Level | Meaning | Confidence Cap |
|-------|---------|----------------|
| E0 | Assertion only | Low |
| E1 | Single source/method | Medium |
| E2 | Two independent methods | High |
| E3 | Triangulated + disconfirmation | High |

### Confidence Levels
| Level | Meaning |
|-------|---------|
| High | Replicated, disconfirmation failed to find issues |
| Medium | Supported but incomplete, some assumptions untested |
| Low | Plausible hypothesis, major gaps or contradictions |

**Rule:** Confidence cannot exceed evidence. E0/E1 caps confidence at Medium.

## Minimum Evidence by Stakes

| Level | P0 Dimensions | P1 Dimensions |
|-------|---------------|---------------|
| Adequate | E1 | — |
| Rigorous | E2 | E1 |
| Exhaustive | E3 | E2 |

## Framework Paths

Full frameworks with templates, worked examples, and detailed guidance:

- **Thoroughness:** `docs/frameworks/framework-for-thoroughness_v1.0.0.md`
- **Decision-Making:** `docs/frameworks/framework-for-decision-making_v1.0.0.md`
- **Verification:** `docs/frameworks/framework-for-verification_v1.0.0.md`

**When to read full framework:**
- First time using a framework
- Red flag appears (see table above)
- Need worked example for current situation
- Unsure about a specific technique or stage

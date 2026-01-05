---
name: deep-retrospective
description: Conduct deep retrospectives on incidents where surface fixes aren't enough — when failures suggest systematic patterns that will recur. Use when postmortems feel incomplete, when "why" questions remain unanswered, or when you need root cause analysis beyond immediate fixes. Triggers: retrospective, root cause, incident analysis, postmortem, systematic failure.
license: MIT
metadata:
  version: 1.1.0
  model: claude-opus-4-5-20251101
  timelessness_score: 9
---

# Deep Retrospective

Trace failures beyond surface causes to fundamental patterns. Produce durable corrections, not just patches.

**Core mechanic:** Refuse to stop at plausible explanations. Keep asking "but why?" until you hit something fundamental.

---

## Contents

- [When to Use](#when-to-use)
- [Meta-Principle](#meta-principle)
- [Stage Overview](#stages)
- [Quick Reference](#quick-reference)
- [Detailed Documentation](#detailed-documentation)

---

## When to Use

### Concrete Signals (any of these)

1. **Knowledge was available but unused** — The error wasn't ignorance
2. **Multiple independent bad decisions** — A chain, not a single mistake
3. **Variants are describable** — Can you generate 2-3 scenarios where this pattern causes different failures?
4. **Contributing causes point to patterns** — "Wrong mental model" suggests others exist
5. **Fix requires behavior change, not just blocking** — Hooks address symptoms; methodology addresses causes

### When NOT to Use

- Genuine knowledge gap (didn't know X, now do — done)
- One-off edge case unlikely to recur
- Immediate patch sufficient and variants aren't plausible

---

## Meta-Principle: Appropriate Depth

> **"Why doesn't the obvious explanation suffice?"**

If you cannot answer this concretely, you are over-analyzing. The obvious explanation may be correct.

**Apply this checkpoint at:** Stage 3 (before continuing), Stage 4 (before naming pattern), Stage 5 (before accepting framing), Stage 8 (before methodology-level encodings).

**Signs of over-analysis:**
- Elaborate root cause without testing obvious explanations first
- Reaching for named patterns before verifying simpler causes don't suffice
- Further depth produces philosophy but no additional prevention

**Signs of under-analysis:**
- Stopping at first plausible explanation without variant testing
- Encodings only block the specific incident
- Root cause contains proper nouns from the incident

**Goal:** Minimum depth that produces encodings preventing all variants. No less, no more.

---

## Stages

| Stage | Goal | Output | Gate? |
|-------|------|--------|-------|
| 1. Incident Review | Establish facts | Failure chain | |
| 2. Surface Cause | Initial why | Cause table | |
| 3. Pattern Recognition | Systematic? | STOP or CONTINUE | **HARD GATE** |
| 4. Fundamental Distortion | Name the pattern | Pattern definition | |
| 5. Challenge Framing | Test precision | Refined diagnosis | |
| 6. Mechanism Analysis | What tools help | Mechanism list | |
| 7. Gap Analysis | Audit existing | Gaps identified | |
| 8. Encoding | Create artifacts | Validated encodings | |

**Stage 3 is a hard gate.** If variants aren't describable or surface fix prevents all variants → STOP with abbreviated postmortem.

**Full stage details:** See [STAGES.md](STAGES.md)

---

## Quick Reference

### Push-Deeper Decision Tree

```text
Is explanation too specific?
  → Proper Noun Test: Can you state it without incident-specific names?
  
Does explanation actually explain?
  → Redescription Test: Can you answer "because..." after it?
  
Does explanation generalize?
  → Variant Prediction Test: Does it predict all variants?
  
Is explanation useful?
  → Actionability Test: Does it suggest concrete behavioral change?
  
Is explanation correctly scoped?
  → Substitution Test: Situational vs. systematic?
```

If any test fails → push deeper or reframe.
If all tests pass → explanation is at appropriate depth.

### When to Stop Pushing

1. All five triggers pass
2. Explanation is outside methodology scope (training dynamics, architectural limits)
3. Explanation is stable under restating
4. Further depth wouldn't change the encodings

**Detailed triggers:** See [TRIGGERS.md](TRIGGERS.md)

---

## Detailed Documentation

| Document | Contents |
|----------|----------|
| [STAGES.md](STAGES.md) | Full stage descriptions, prompts, decision criteria |
| [TRIGGERS.md](TRIGGERS.md) | Five push-deeper tests with examples |
| [OUTPUTS.md](OUTPUTS.md) | Output format templates (full and abbreviated) |
| [EXAMPLE.md](EXAMPLE.md) | Worked example showing key transitions |
| [REFERENCE.md](REFERENCE.md) | Self-application guidance, checkpoint details |
| [CHANGELOG.md](CHANGELOG.md) | Version history and update guidelines |

---

## Framework for Rigor

This skill implements the [Framework for Rigor](~/.claude/references/framework-for-rigor.md).

### Phase Mapping

| Framework Phase | Retrospective Stages | Purpose |
|-----------------|---------------------|---------|
| **Definition** | 1-3 (Incident Review → Pattern Recognition) | Establish facts, identify surface cause, decide if deeper analysis needed |
| **Execution** | 4-7 (Fundamental Distortion → Gap Analysis) | Name pattern, challenge framing, analyze mechanisms, audit gaps |
| **Verification** | 8 (Encoding) | Create and validate artifacts that prevent recurrence |

Stage 3 is a **hard gate**: if the issue is not systematic, exit with abbreviated postmortem (Definition phase complete, skip Execution/Verification).

### Principle Implementation

| Principle | Implemented In |
|-----------|----------------|
| **Appropriate Scope** | Stage 3 gate, Meta-Principle ("Why doesn't the obvious explanation suffice?") |
| **Adequate Evidence** | Stage 1 (failure chain), Stage 2 (cause table) |
| **Sound Inference** | Stages 4-5 (push-deeper tests: Proper Noun, Redescription, Variant, Actionability, Substitution) |
| **Full Coverage** | Stage 7 (gap analysis of existing encodings) |
| **Documentation** | Stage 8 (encodings as durable artifacts) |
| **Traceability** | Failure chain links each cause to evidence |
| **Honesty** | Stage 5 (challenge framing), Meta-Principle checkpoints |

---

## Verification Checklist

Before claiming a retrospective complete:

- [ ] **Stage 3 gate passed** — Variants describable, surface fix insufficient
- [ ] **Pattern named without proper nouns** — No incident-specific names in root cause
- [ ] **All five push-deeper tests pass** — Proper Noun, Redescription, Variant, Actionability, Substitution
- [ ] **Encodings validated** — Each encoding tested against variant scenarios
- [ ] **Gaps documented** — Existing mechanisms audited, gaps identified

**Detailed validation criteria:** See [STAGES.md](STAGES.md) Stage 8 (Encoding Validation).

**Red flags:**
- Root cause contains incident-specific names → push deeper
- Encodings only block the specific incident → generalize
- "Everything looks systematic" without Stage 3 evidence → over-analysis

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full history.

**v1.1.0** (2025-12-17): Added Stage 3 hard gate, encoding validation, embedded checkpoints, push-deeper triggers, version tracking.

**v1.0.0** (2025-12-16): Initial methodology from credential exposure incident.

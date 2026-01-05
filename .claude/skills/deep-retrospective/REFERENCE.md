# Reference: Self-Application Guidance

Detailed guidance for checkpoints embedded in Stages 3, 4, 5, and 8. Refer here when a checkpoint is triggered.

---

## The Core Distortion to Counteract

The retrospective process can exhibit the distortions it's meant to identify.

**Anti-pattern:**
```
Pattern-match to complex root causes → build elaborate diagnosis
```

**Correct pattern:**
```
Actual cause → simplest explanation that predicts variants → only then deepen
```

---

## Checkpoint Questions

Use these at decision points:

- "Does the obvious explanation already predict the variants?"
- "Am I analyzing the actual failure or an abstracted version of it?"
- "What's the simplest diagnosis that would prevent recurrence?"
- "Could this just be [obvious thing]?"

---

## Red Flags During Retrospective

### Over-Analysis Indicators

- Elaborate root cause proposed without testing obvious explanations
- Reaching for named patterns ("overfitting", "sycophancy") before verifying simpler causes don't suffice
- Deep analysis that "shows rigor" when simpler diagnosis would work
- Fundamental distortion named but can't explain why obvious explanation fails
- Further depth produces philosophy but no additional prevention

### Under-Analysis Indicators

- Accepting first plausible explanation without testing against variants
- Naming the pattern without explaining why it generalizes
- Producing encodings that only block this specific incident
- Rushing to encoding before understanding the pattern
- Root cause contains proper nouns from the incident

---

## Checkpoint Application by Stage

| Stage | Checkpoint | Question to answer |
|-------|------------|-------------------|
| Stage 3 | Before CONTINUE | "Why doesn't fixing the Stage 2 surface cause suffice?" |
| Stage 4 | Before naming pattern | "Is the obvious explanation insufficient, or am I reaching for a more interesting diagnosis?" |
| Stage 5 | Before accepting framing | "If I accept this, what specifically would I do differently?" |
| Stage 8 | Before methodology-level encoding | "Does this require changing how I think, or just blocking a specific action?" |

Each checkpoint requires a **concrete answer**. Abstract answers ("it feels deeper", "be more careful") indicate the checkpoint has failed.

---

## Balance

Some incidents genuinely require deep analysis. Some don't.

The methodology is a tool, not a ritual.

Use the depth that produces durable prevention — no more, no less.

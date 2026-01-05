# Framework for Rigor

A methodology for work that demands justified confidence. Use when stakes warrant deliberation.

**Location:** `~/.claude/references/framework-for-rigor.md` (shared by all deep-* skills)

---

## When NOT to Use This Framework

**Skip this framework when:**

- An obvious solution exists and stakes are low
- Time-critical response is needed (use heuristics, review later)
- The task is mechanical, not investigative
- You need statistical validity (use quantitative methods)
- You face adversarial actors hiding evidence (use forensic methods)

**Use this framework when:**

- Conclusions inform important decisions
- Work will be reviewed or shared
- You need to explore, investigate, audit, or review
- Mistakes would be costly or hard to reverse

---

## Quick Reference

### Four Key Questions

1. **Before starting:** Is there an obvious direct solution?
2. **During work:** What would prove me wrong?
3. **Before concluding:** Have I covered everything in scope?
4. **Before claiming done:** What's the best argument against my conclusion?

### Seven Principles

| Principle | Core Question |
|-----------|---------------|
| **Appropriate Scope** | Why these boundaries? |
| **Adequate Evidence** | Is this primary, secondary, or tertiary? |
| **Sound Inference** | Does the conclusion follow from the evidence? |
| **Full Coverage** | Have I examined everything in scope? |
| **Documentation** | Could someone reproduce my process? |
| **Traceability** | Can every claim be traced to its source? |
| **Honesty** | What am I not saying? |

---

## Core Concepts

### Three Dimensions

Rigor fails in three distinct ways. Each dimension is independent—you can fail one while succeeding at others.

| Dimension | Question | Failure Mode |
|-----------|----------|--------------|
| **Validity** | Are conclusions justified by evidence? | Bad reasoning, weak evidence |
| **Completeness** | Did you examine everything relevant? | Missed scope, gaps in coverage |
| **Transparency** | Can others verify your work? | Undocumented process, untraceable claims |

### Seven Principles (Mapped)

| Dimension | Principles |
|-----------|------------|
| Validity | Adequate Evidence, Sound Inference |
| Completeness | Appropriate Scope, Full Coverage |
| Transparency | Documentation, Traceability |
| All | Honesty (constraint on all work) |

---

## Calibration

Match rigor to stakes. Light calibration done well beats deep calibration done poorly.

### Stakes Assessment

| Factor | Low (1) | Medium (2) | High (3) |
|--------|---------|------------|----------|
| **Reversibility** | Easy to undo | Moderate effort | Permanent |
| **Blast radius** | Affects only me | Affects team | Affects users/org |
| **Precedent** | One-off | May be referenced | Sets pattern |
| **Visibility** | Internal | Shared | Public |

**Score 4-6:** Light | **Score 7-9:** Medium | **Score 10-12:** Deep

### Calibration Levels

| Level | When | Characteristics |
|-------|------|-----------------|
| **Light** | Low stakes, familiar territory | Key checks only, brief notes, single method |
| **Medium** | Moderate stakes, some uncertainty | Full checklist, documented methodology, cross-validation |
| **Deep** | High stakes, novel territory, precedent-setting | Exhaustive coverage, adversarial review, full audit trail |

**Default:** When uncertain, choose more rigor. Under-rigor fails silently.

---

## Three Phases

### Phase 1: Definition

Define scope and success criteria before gathering evidence.

| Action | Output |
|--------|--------|
| State the goal | One sentence: what outcome, not what approach |
| Define scope | What's in bounds, what's excluded, why |
| Set done criteria | How you'll know you're finished |
| Surface assumptions | What you're taking for granted |
| Check simple path | Is there an obvious solution? Why won't it work? |

**Red flag:** Scope includes easy areas, excludes hard ones.

### Phase 2: Execution

Gather evidence, reason carefully, track coverage.

| Action | Output |
|--------|--------|
| Collect evidence | Prefer primary sources; note evidence level |
| Seek disconfirmation | Look for evidence against your hypothesis |
| Document negatives | What you looked for but didn't find |
| Track coverage | Matrix of what's examined, what remains |
| Record methodology | Tools, queries, order of operations |
| Log decisions | What you decided, why, what alternatives existed |

**Red flag:** Only finding evidence that confirms initial beliefs.

### Phase 3: Verification

Verify before concluding. Check your own work.

| Action | Output |
|--------|--------|
| Check coverage | No gaps in matrix; methodology documented |
| Verify reasoning | Conclusions follow from evidence |
| State limitations | What this work doesn't cover |
| Counter-conclusion | Best argument against your conclusion |
| Label confidence | Certain, probable, possible, or unknown |

**Red flag:** Claiming "done" without checking coverage.

---

## Phase Checklists by Calibration

### Phase 1: Definition

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Goal stated | Brief | Full | Full |
| Scope defined | Key boundaries | Complete | Exhaustive |
| Done criteria | Implicit OK | Explicit | Explicit + verified |
| Assumptions surfaced | Key only | All | All + tested |
| Simple path checked | Yes | Yes | Yes + documented |

### Phase 2: Execution

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Evidence collected | Key sources | Multiple sources | Exhaustive |
| Evidence levels noted | — | Yes | Yes |
| Disconfirmation attempted | Brief | Systematic | Adversarial |
| Negative findings | — | Documented | Documented |
| Coverage tracked | List | Matrix | Matrix + verified |
| Methodology recorded | Brief | Full | Timestamped |

### Phase 3: Verification

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Coverage verified | Quick check | Full check | Independent check |
| Reasoning verified | Self-check | Self-check | Peer check |
| Limitations stated | Key | Full | Comprehensive |
| Counter-conclusion | — | Yes | Adversarial |
| Confidence labeled | Yes | Yes | Yes |

---

## Evidence Hierarchy

| Level | Source | Trust |
|-------|--------|-------|
| **Primary** | Direct observation: read file, run code, see output | High |
| **Secondary** | Documentation: README says, comments state | Verify against primary |
| **Tertiary** | Inference: pattern suggests, absence implies | Flag as inference |

**Rule:** Prefer primary. Verify secondary. Label tertiary.

---

## Confidence Levels

| Level | Meaning | Evidence Required |
|-------|---------|-------------------|
| **Certain** | Directly observed, multiple sources confirm | Primary + cross-reference |
| **Probable** | Strong evidence, no contradictions | Primary evidence |
| **Possible** | Some evidence, gaps remain | Secondary or inference |
| **Unknown** | Looked but didn't find conclusive evidence | Documented search |

**Rule:** Label every significant claim. "Unknown" is a valid answer.

---

## Red Flags: Nine Most Dangerous Failures

These failures are insidious because they feel productive while undermining rigor.

| Rank | Failure | Why Dangerous |
|------|---------|---------------|
| 1 | **Motivated Omission** | Unconsciously suppress inconvenient findings |
| 2 | **Convenience-Driven Scope** | Exclude hard areas, include easy ones |
| 3 | **Wishful Inference** | Conclusion feels right, evidence is weak |
| 4 | **Confirmation-Only Evidence** | Only gather evidence that supports hypothesis |
| 5 | **Coverage Confusion** | Mistake "feeling done" for "actually done" |
| 6 | **Reconstructed Documentation** | Write docs after the fact, invent rationale |
| 7 | **Citation Theater** | Citations exist but don't support claims |
| 8 | **Under-Calibration** | Stakes higher than rigor applied |
| 9 | **Compliance Confusion** | "Followed checklist" substitutes for "found truth" |

**If you notice any of these:** Stop. Reassess. Correct before continuing.

---

## Limitations

This framework has boundaries. Know them.

### Fundamental Limits

| Limit | Implication |
|-------|-------------|
| **Creator bias** | Framework reflects its creator's blind spots |
| **Circularity** | Framework validates itself by its own definition |
| **Decomposition assumed** | Rigor may not decompose into dimensions |
| **Negative findings unverifiable** | "Didn't find" can't be proven conclusively |
| **Checklists invite cargo-culting** | Following form doesn't guarantee substance |

### Scope Limits

| Not For | Why | Use Instead |
|---------|-----|-------------|
| Adversarial contexts | Assumes honest data sources | Forensic methods |
| Quantitative research | Different validity criteria | Statistical methods |
| Real-time decisions | Requires deliberation | Heuristics, review later |
| Simple tasks | Overhead exceeds benefit | Direct action |

### Practical Limits

| Limit | Mitigation |
|-------|------------|
| Cognitive load | Use Quick Reference; calibrate appropriately |
| Subjective calibration | Use Stakes Assessment table |
| No empirical validation | Gather feedback through use |

---

## Failure Modes

How the framework breaks in practice.

| Mode | Warning Signs | Fix |
|------|---------------|-----|
| **Premature scope lock** | Findings point outside scope but ignored | Revise scope; document why |
| **Evidence hoarding** | Collecting without concluding | Set checkpoints; synthesize periodically |
| **Completeness theater** | All cells marked done, findings thin | Honest self-assessment; depth per calibration |
| **Documentation debt** | Notes written in bulk at end | Document as you go |
| **Honesty erosion** | Counter-evidence fades over time | Counter-Conclusion Test |
| **Calibration drift** | Stakes rose, rigor didn't | Reassess calibration at checkpoints |
| **Framework as shield** | "I followed the process" defends bad conclusions | Framework is means, not end |

---

## The Checkpoint

Before claiming done, answer:

> **Can I state exactly what "done" looks like, and how I verified each element?**

If no: continue gathering evidence.
If yes: proceed with conclusions, labeled with confidence.

---

## Derivation

This framework was systematically derived through a 10-step bulletproofing process:

1. Define "rigor" precisely
2. Identify first principles per dimension
3. Derive framework structure from principles
4. Map dependencies between elements
5. Validate completeness and minimality
6. Operationalize each element
7. Self-apply the framework
8. External validation (adversarial testing)
9. Document limitations and failure modes
10. Practical validation across domains

For full derivation, rationale, and detailed operationalization, see:
`~/.claude/skills/deep-exploration/references/bulletproofing-log.md`

---

## Usage

**To apply this framework:**

1. Check "When NOT to Use" — skip if criteria met
2. Assess stakes — choose calibration level
3. Work through three phases — Definition, Execution, Verification
4. Use phase checklists — match to calibration level
5. Watch for red flags — stop and correct if seen
6. Verify before concluding — Counter-Conclusion Test
7. State limitations — be honest about what you didn't cover

**The framework helps you be thorough and honest. It cannot make you right.**

---

## Skills Using This Framework

- `deep-exploration` — Rigorous codebase/system exploration
- `deep-security-audit` — Static code security review
- `deep-retrospective` — Root cause analysis for systematic failures

### Roadmap

- `deep-code-review` — Comprehensive code review (planned)

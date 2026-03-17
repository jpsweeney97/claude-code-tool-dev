# Worked Examples

End-to-end examples of the Prompt Engineering Pipeline applied to real prompts.
These show the analytical phases in action — how failure analysis drives
structural choices.

---

## Example 1: Adversarial Review Prompt

**User request:** "I want a prompt that critiques proposals and surfaces
problems before implementation."

### Phase 1 — Job

Cause the model to perform a rigorous critical review of a proposed plan,
design, or idea — surfacing problems the proposer would regret later.

### Phase 2 — Naive Failure Analysis

**Naive approach:** "What's weak here? What have we overlooked? What are
some likely failure modes?"

**Failure modes:**

1. **Category omission via self-selection** — Model addresses whatever's
   easiest to critique, skips entire categories (e.g., reviews correctness
   but ignores operational concerns). User gets a critique that feels
   thorough but has blind spots.

2. **Softball self-review** — Model hedges findings with "could potentially"
   and "might be worth considering." User gets observations instead of
   findings — nothing actionable.

3. **Flat unstructured output** — Findings buried in prose paragraphs. User
   must mentally triage what matters vs. what's minor. Decision cost is
   transferred to the reader.

4. **No severity framework** — All findings presented as equal weight.
   User can't distinguish "this will break in production" from "this
   naming is slightly inconsistent."

5. **Sunk-cost bias toward own proposal** — When reviewing its own work,
   the model reviews generously because it generated the proposal. The
   reviewer and the author are the same entity with the same blind spots.

### Phase 3 — Structural Upgrades

1. **Dimensional forcing function** → addresses category omission (#1):
   Explicit checklist of critique dimensions that must each be evaluated.
   Model can mark "PASS" but must consciously evaluate each one.

2. **Role-shift framing** → addresses softball (#2) and sunk-cost (#5):
   Explicit instruction to "step back from implementer" and adopt critical
   reviewer perspective. Counteracts ownership bias.

3. **Pre-mortem narrative** → addresses softball (#2): "Imagine this failed
   — explain why" shifts the model from hedging to committing to a failure
   narrative. Produces deeper findings than "what could go wrong."

4. **Separated severity summary** → addresses flat output (#3) and no
   severity (#4): Dedicated ranked findings section with blocking/high/
   moderate/low classification. Actionable triage without re-reading.

### Phase 4 — Constructed Prompt

The constructed prompt included:
- Role shift as opening instruction (primes entire response)
- Assumptions audit (forces explicit enumeration of what must be true)
- Pre-mortem section BEFORE dimensional critique (narrative primes concrete
  thinking before structured checklist)
- Six critique dimensions with "skip if genuinely N/A" calibration
- Severity summary as separate section with likelihood × impact ranking
- Confidence score with justification

### Phase 5 — Key Rationale

- **Pre-mortem before dimensions** — Ordering matters. The narrative framing
  primes the model to think concretely, which improves the quality of the
  subsequent structured checklist. Without this, the dimensions section
  produces surface-level findings.
- **"PASS is valid"** — Prevents rote N/A-filling while the dimensional
  structure prevents lazy omission. Calibrated permission.
- **Confidence score** — Forces the model to commit to an overall assessment
  rather than listing findings without synthesis. The number itself matters
  less than the justification.

---

## Example 2: Dependency-Sequenced Next Steps

**User request:** "I want a prompt that presents next steps clearly, with
dependencies between tasks defining the sequence."

### Phase 1 — Job

Cause the model to produce a dependency-ordered action plan where the
sequence derives from what blocks what, not from intuition about priority.

### Phase 2 — Naive Failure Analysis

**Naive approach:** "What are the next steps? List them in order."

**Failure modes:**

1. **Conflated ordering concepts** — Model mixes priority, dependency, and
   sequence into a single numbered list. Item 3 depends on item 5 but is
   listed first because it "feels" more important. User follows the list
   top-to-bottom and hits a blocker at step 3.

2. **Serialized parallelism** — Flat numbered list forces everything into
   a serial sequence. Tasks that could run concurrently are presented as
   sequential. User does one thing at a time when they could be doing three.

3. **Missing decision gates** — Plan assumes a single linear path. Real
   plans branch based on outcomes ("if X works, do Y; otherwise do Z").
   User discovers mid-execution that the plan doesn't account for the
   outcome they got.

4. **Scope creep into aspirational work** — Without a boundary, model
   cheerfully plans six months of follow-on work. User can't distinguish
   "do this now" from "maybe someday." Plan is technically correct but
   operationally useless.

5. **Unverifiable tasks** — Vague descriptions like "set up infrastructure"
   with no completion criteria. User can't tell whether a task is done.
   Progress is unmeasurable.

### Phase 3 — Structural Upgrades

1. **Dependency map before sequence** → addresses conflation (#1): Force
   the model to build a dependency graph (T1 depends on T2) BEFORE
   presenting the sequenced plan. Sequence derives from structure, not
   intuition.

2. **Phase grouping with explicit parallelism** → addresses serialization
   (#2): Tasks within a phase are parallel; phases are sequential.
   Structure makes concurrency visible.

3. **Decision gates as first-class section** → addresses missing branches
   (#3): Separate section for "after TX, if condition → path A; else →
   path B." Not buried in task descriptions.

4. **Scope parking lot with cap** → addresses scope creep (#4): Explicit
   "parked / not now" list capped at 3–5 items. Its job is to remove
   things from scope, not collect them.

5. **Mandatory "done when" criteria** → addresses unverifiable tasks (#5):
   Every task requires a verifiable completion condition. No task without
   a way to know it's finished.

### Phase 4 — Constructed Prompt

The constructed prompt included:
- "Current state" section before any planning (ground the analysis)
- Dependency map with T-IDs (T1, T2...) for cross-reference
- Phased plan derived from the dependency map with "done when" on every task
- Session-size constraint (30 min – 2 hours) as granularity calibrator
- Decision gates as their own section
- Critical path identification (which chain sets the pace)
- Parking lot capped at 3–5 items with one-line descriptions
- Ground rule: "Prefer the plan that unblocks decisions earliest, not the
  plan that starts with the most comfortable task"

### Phase 5 — Key Rationale

- **Dependency map before sequence** — This is the highest-leverage
  structural choice. Without it, the model intuits an order that feels
  right but doesn't reflect actual blocking relationships. The map is the
  analysis; the phased plan is just its presentation.
- **Session-size constraint** — Without granularity calibration, tasks are
  either too big ("build the API layer") or too small ("create the
  directory"). 30 min – 2 hours hits the sweet spot for actionable work.
- **"Unblocks decisions earliest"** — Counteracts the model's default of
  starting with the comfortable/familiar task. The highest-leverage first
  step is usually the one that resolves the biggest open question.

# Worked Examples

End-to-end examples of the Prompt Engineering Pipeline applied to real prompts.
These show the analytical phases in action — how failure analysis drives structural
choices, and how each phase element (task type, LLM mechanism, upgrade type) connects.

---

## Example 1: Adversarial Review Prompt

**User request:** "I want a prompt that critiques proposals and surfaces problems
before implementation."

### Phase 1 — Profile the Task

**Task type:** Analysis (dominant) — evaluate a proposed plan and surface problems.

**Job:** Cause the model to perform a rigorous critical review of a proposed plan,
design, or idea — surfacing problems the proposer would regret discovering after
implementation.

**Predicted failure profile from type:** Self-selection bias toward easy-to-critique
dimensions; softball severity from sycophancy; flat unstructured output.

### Phase 2 — Failure Analysis

**Naive approach:** "What's weak here? What have we overlooked? What are some
likely failure modes?"

**Failure modes:**

1. **Category omission via self-selection**
   - *LLM mechanism:* RLHF fine-tuning biases the model toward confident, easy-to-state
     findings. Operational and edge-case concerns require speculative reasoning, which
     the model deprioritizes because it produces lower-confidence outputs.
   - *In-context behavior:* Model reviews correctness and logic fluently; skips
     operational concerns, dependency risks, and rollback complexity entirely.
   - *Consequence:* Critique feels thorough but has systematic blind spots in exactly
     the domains where surprises are most costly.

2. **Softball self-review**
   - *LLM mechanism:* Helpfulness training produces hedging language ("could potentially,"
     "might be worth considering") as a sycophantic softening behavior. The model avoids
     the social discomfort of direct negative statements even when directed to critique.
   - *In-context behavior:* Findings are phrased as observations rather than assessments.
     Nothing is called a problem — everything is a "consideration."
   - *Consequence:* User gets a list of observations with no signal about what
     actually needs to change. Critique is not actionable.

3. **Flat unstructured output**
   - *LLM mechanism:* Without format constraints, autoregressive generation defaults to
     prose paragraphs — the dominant pattern in training data for analytical writing.
   - *In-context behavior:* Findings buried in paragraphs; severity differences
     invisible; reader must re-read to build a triage mental model.
   - *Consequence:* Decision cost is transferred from the model to the reader.

4. **No severity framework**
   - *LLM mechanism:* The model lacks an intrinsic scale for "importance" unless one is
     provided. All findings receive approximately equal elaboration because elaboration
     length is the model's implicit proxy for importance.
   - *In-context behavior:* "This will break in production" and "this naming is slightly
     inconsistent" get the same treatment.
   - *Consequence:* User cannot triage without re-reading everything.

5. **Sunk-cost bias toward own proposal**
   - *LLM mechanism:* When the model generated the proposal being reviewed, its prior
     on "this is correct" is elevated. The reviewer and author share the same latent
     representation. Self-generated content receives more charitable interpretation.
   - *In-context behavior:* Model reviews its own work generously, producing findings
     that feel critical but avoid the core structural choices.
   - *Consequence:* Review misses exactly the decisions that need scrutiny.

### Phase 3 — Structural Upgrades

1. **Dimensional forcing function** [Structural]
   → Addresses: category omission (#1)
   Explicit checklist of critique dimensions the model must evaluate in sequence.
   Model can mark a dimension PASS but must consciously engage with each one — it
   cannot skip by omission.

2. **Role-shift framing** [Behavioral]
   → Addresses: softball self-review (#2), sunk-cost bias (#5)
   Opening instruction to adopt an explicit adversarial reviewer stance — separate
   from any role as implementer or proposer. Counteracts ownership prior and
   helpfulness-softening by priming the entire response with a different identity.

3. **Pre-mortem narrative** [Behavioral]
   → Addresses: softball self-review (#2)
   "Imagine this failed — explain why" forces the model to commit to a failure
   narrative rather than list possibilities. The narrative form bypasses hedging
   because it asks for a story, not a probabilistic assessment.

4. **Separated severity summary** [Structural + Calibration]
   → Addresses: flat output (#3), no severity (#4)
   Dedicated ranked findings section with explicit likelihood × impact classification.
   Severity is a required output field, not an inferred signal from elaboration length.

### Phase 4 — Constructed Prompt

The constructed prompt included:
- Role-shift instruction as the opening sentence (primes the entire response before
  any task-specific content)
- Assumptions audit section (forces explicit enumeration of what must be true for the
  proposal to succeed)
- Pre-mortem section BEFORE dimensional critique (narrative framing primes concrete
  thinking; the checklist section benefits from it)
- Six critique dimensions with "mark PASS if genuinely not applicable" calibration
- Severity summary as a separate section with blocking / high / moderate / low tiers
- Confidence score with mandatory justification

**Semantic Validation:**
- Category omission → Dimensional forcing function with six explicit dimensions. ✓
- Softball self-review → Pre-mortem forces narrative commitment; role-shift removes
  hedging incentive. ✓
- Flat output → Severity summary section with structured format. ✓
- No severity → Explicit blocking/high/moderate/low classification required. ✓
- Sunk-cost bias → Role-shift framing separates reviewer from author identity. ✓

### Phase 5 — Design Rationale

**Pre-mortem before dimensions:**
Ordering matters. The pre-mortem narrative primes the model to think in concrete
failure terms before it encounters the structured checklist. Without this, the
dimensional section produces surface-level findings. Addresses: softball self-review.
*Remove and:* Dimensional checklist produces hedged, observational findings.
*Tune first:* If pre-mortem is too speculative, add "cite a specific signal in the
proposal that supports this failure path."

**"PASS is valid" permission:**
Prevents rote N/A-filling while the dimensional structure prevents lazy omission.
Addresses: category omission. The calibrated permission resolves the tension between
"must evaluate each" and "not every dimension applies."
*Remove and:* Model either fills every dimension regardless or skips any it finds
inconvenient.

**Confidence score:**
Forces the model to commit to an overall assessment rather than listing findings
without synthesis. Addresses: flat output. The number itself matters less than the
required justification.
*Remove and:* Critique ends with a list of findings, no integrated view of risk.

---

## Example 2: Dependency-Sequenced Next Steps

**User request:** "I want a prompt that presents next steps clearly, with dependencies
between tasks defining the sequence."

### Phase 1 — Profile the Task

**Task type:** Planning (dominant) — produce a dependency-ordered action plan.

**Job:** Cause the model to produce a dependency-ordered action plan where the
sequence derives from what blocks what, not from intuition about priority.

**Predicted failure profile from type:** Order/priority conflation; serialized
parallelism; missing decision gates.

### Phase 2 — Failure Analysis

**Naive approach:** "What are the next steps? List them in order."

**Failure modes:**

1. **Conflated ordering concepts**
   - *LLM mechanism:* "In order" is ambiguous in training data — it refers to
     priority, temporal sequence, and dependency interchangeably. The model defaults to
     a single numbered list, which is the dominant pattern for "ordered steps."
   - *In-context behavior:* Item 3 depends on item 5 but is listed first because it
     has higher perceived priority. The list feels coherent but is causally incorrect.
   - *Consequence:* User follows the list top-to-bottom and hits a blocker at step 3.

2. **Serialized parallelism**
   - *LLM mechanism:* Numbered lists enforce serial structure. The model has no
     native representation for "these items are concurrent" in a numbered list format.
   - *In-context behavior:* Tasks that could run in parallel are presented sequentially
     because the list format makes parallelism invisible.
   - *Consequence:* User executes serially when they could be doing three things
     simultaneously. Timeline is artificially extended.

3. **Missing decision gates**
   - *LLM mechanism:* Planning prompts without explicit branching instructions receive
     linear plans. The model optimizes for a single coherent path through the space,
     which is the most common training pattern for instructional content.
   - *In-context behavior:* Plan presents one path. Real execution branches based on
     outcomes; the plan doesn't account for the outcome the user actually got.
   - *Consequence:* User discovers mid-execution that the plan doesn't apply to their
     actual situation.

4. **Scope creep into aspirational work**
   - *LLM mechanism:* Without an explicit time horizon or scope boundary, the model's
     prior on "helpful completeness" extends the plan to cover everything that could
     conceivably be done.
   - *In-context behavior:* Model includes six months of follow-on work alongside
     immediate next steps, with no signal about what's actionable now.
   - *Consequence:* User can't distinguish "do this now" from "maybe someday."

5. **Unverifiable tasks**
   - *LLM mechanism:* Task descriptions default to verb + object ("set up
     infrastructure," "implement the API"). Completion criteria require counterfactual
     reasoning ("what would be true if done?"), which the model omits unless prompted.
   - *In-context behavior:* Tasks are described as activities, not outcomes. No way to
     know if a task is done.
   - *Consequence:* Progress is unmeasurable. Team debates whether tasks are complete.

### Phase 3 — Structural Upgrades

1. **Dependency map before sequence** [Structural]
   → Addresses: conflated ordering (#1)
   Force the model to construct a dependency graph (T1 blocks T2) BEFORE producing
   the sequenced plan. Sequence derives from the map's structure, not from intuition.
   Separating analysis from presentation breaks the conflation at the source.

2. **Phase grouping with explicit parallelism** [Structural]
   → Addresses: serialized parallelism (#2)
   Tasks within a phase are parallel; phases are sequential. The visual structure
   makes concurrency explicit rather than inferrable.

3. **Decision gates as first-class section** [Structural]
   → Addresses: missing decision gates (#3)
   Separate section for "after TX, if condition → path A; else → path B." Not buried
   in task descriptions where branching logic is invisible.

4. **Scope parking lot with cap** [Calibration]
   → Addresses: scope creep (#4)
   Explicit "parked / not now" section capped at 3–5 items. Its function is to
   *remove* things from scope, not collect them. The cap forces triage rather than
   accumulation.

5. **Mandatory "done when" criteria** [Validation]
   → Addresses: unverifiable tasks (#5)
   Every task requires a verifiable completion condition. No task without a way to
   know it's finished.

### Phase 4 — Constructed Prompt

The constructed prompt included:
- "Current state" section before any planning (grounds analysis in reality rather
  than assumption)
- Dependency map with T-IDs (T1, T2...) used for cross-referencing throughout
- Phased plan derived from the dependency map, with "done when" on every task
- Session-size constraint (30 min – 2 hours) as a granularity calibrator
- Decision gates as their own named section
- Critical path identification (which dependency chain sets the minimum timeline)
- Parking lot capped at 3–5 items with one-line descriptions
- Ground rule: "Prefer the plan that unblocks decisions earliest, not the one that
  starts with the most comfortable task"

**Semantic Validation:**
- Conflated ordering → Dependency map section forces causal structure before sequence.
  T-IDs make dependencies traceable throughout. ✓
- Serialized parallelism → Phase grouping makes within-phase concurrency explicit. ✓
- Missing decision gates → Decision gates section is required, not optional. ✓
- Scope creep → Parking lot section with hard cap; described as a removal mechanism. ✓
- Unverifiable tasks → "Done when" is a required field on every task. ✓

### Phase 5 — Design Rationale

**Dependency map before sequence:**
The highest-leverage structural choice. The map is the analysis; the phased plan is
its presentation. Without the map, the model intuits an order that feels right but
doesn't reflect actual blocking relationships. Addresses: conflated ordering.
*Remove and:* Plan is a priority-ordered list dressed as a dependency sequence.
*Tune first:* If map is too abstract, add "for each dependency, state the specific
artifact or decision that T1 must produce before T2 can start."

**Session-size constraint (30 min – 2 hours):**
Without a granularity anchor, tasks are either too big ("build the API layer") or
too small ("create the directory"). The constraint calibrates the model's natural
tendency to produce tasks at the level of abstraction where it feels comfortable.
*Remove and:* Tasks vary wildly in granularity; some are milestones, some are
terminal commands.
*Tune first:* Adjust the window based on team context (e.g., "each task should be
completable in one focused work session").

**"Unblocks decisions earliest" ground rule:**
Counteracts the model's default of starting with the comfortable/familiar task.
The highest-leverage first step is usually the one that resolves the biggest open
question, which is often the riskiest or least-defined task. Addresses: conflated
ordering (priority vs. dependency vs. risk).
*Remove and:* Plan starts with well-understood setup tasks; critical unknowns are
deferred until they become blockers.

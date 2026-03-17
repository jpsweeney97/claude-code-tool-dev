---
name: prompt-generator
description: >
  Professional prompt engineering pipeline that produces production-grade,
  reusable conversational prompts. Use when user says "write a prompt",
  "build a prompt", "give me a prompt that...", "I need a prompt for...",
  "prompt engineer this", or any request to create, refine, or upgrade a
  prompt intended for use in a conversational turn (pasted into a chat
  with an LLM). Do NOT use for CLAUDE.md directives, system prompts, API
  integrations, slash commands, one-off questions, general writing tasks,
  or requests to follow a prompt (as opposed to creating one).
argument-hint: "[description of the prompt needed]"
---

# Prompt Engineering Pipeline

A structured method for producing conversational prompts that reliably shape
model behavior. This pipeline treats prompt engineering as failure-mode-driven
design: the professional prompt is a set of structural countermeasures to
diagnosed failure modes, not an elaboration of a rough draft.

**Scope:** Prompts intended for conversational use — pasted into a chat
turn with an LLM. Not system prompts, not standing directives, not API
integrations.

## Pipeline Overview

| Phase | Name | Purpose | Gate |
|-------|------|---------|------|
| 1 | Profile the Task | Classify cognitive operation type; state job | Task type named; job in one sentence |
| 2 | Failure Analysis | Diagnose failure modes with LLM mechanism | 3–5 failures, each with name + mechanism + consequence |
| 3 | Structural Upgrades | Design countermeasures by upgrade type | Each upgrade traces to ≥1 failure mode; type named |
| 4 | Prompt Construction | Build artifact; validate against failure modes | Passes construction checklist + semantic validation |
| 5 | Design Rationale | Validity check on load-bearing choices | Every section justified by failure mode, not convention |

**Execute phases in order. Fast path permitted for simple tasks — see Complexity Calibration.**

---

## Phase 1: Profile the Task

Before diagnosing failures, classify the cognitive operation. Task type predicts the
likely failure profile and directs Phase 2 toward the right hypotheses.

### Task Type Classification

| Type | Description | Characteristic Failure Profile |
|------|-------------|--------------------------------|
| **Analysis** | Evaluate, critique, diagnose | Self-selection bias; softball findings; flat severity |
| **Generation** | Create original content | Example anchoring; diversity collapse; scope drift |
| **Transformation** | Convert or restructure existing content | Source anchoring; incomplete transformation; format mismatch |
| **Planning** | Sequence and prioritize actions | Order/priority conflation; serialized parallelism; missing decision gates |
| **Extraction** | Identify or enumerate from a given artifact | False completeness; granularity collapse; category omission |

Most prompts blend types. Name the dominant type; note secondary types if they affect
the failure profile.

**Job statement:** State in one sentence what the prompt must cause the model to do.

For minor ambiguity, state an assumption and proceed. For genuine ambiguity about what
behavior is wanted, ask ONE clarifying question.

**Phase 1 Gate:** Task type classified + job stated in one sentence.

---

## Phase 2: Failure Analysis

**This is the load-bearing phase. Every downstream decision derives from it.**

Describe the naive approach — what someone would write in 30 seconds. Then identify
**3–5 specific, named failure modes**. For each:

- **Name**: 3–5 words
- **LLM mechanism**: *Why* does the model do this? Ground the explanation in model
  behavior — RLHF-induced sycophancy, autoregressive premature closure, training
  distribution bias toward salient/easy cases, attention to early tokens, etc.
- **In-context behavior**: What specifically goes wrong with this prompt and task?
- **Consequence**: What does the user receive that they shouldn't?

### Failure Mode Starting Points by Task Type

Begin with the characteristic profile from Phase 1. Then check the universal modes.
Not all will apply — but reason about each before dismissing it.

**Universal (check for all types):**
- *Structural absence* — No forcing function for completeness, ordering, or granularity.
  Model produces what comes naturally from next-token prediction.
- *Format mismatch* — Output structure doesn't match how the consumer will use it.
- *Scope ambiguity* — No explicit boundary; model expands or contracts based on salience.

**Analysis:** Self-selection bias (RLHF bias toward confident, easy-to-state findings);
softball severity (helpfulness training induces hedging); sunk-cost review (reviewer
and author share the same prior).

**Generation:** Example anchoring (draft treated as scaffold, not symptom); diversity
collapse (autoregressive sampling concentrates near the distributional mean).

**Transformation:** Source anchoring (surface changes but underlying structure
preserved); incomplete transformation (partial conversion satisfies the literal request).

**Planning:** Order/priority conflation (single ranked list mixes causal, temporal, and
value relationships); serialized parallelism (flat list forces serial execution of
concurrent work); missing decision gates (linear plan through a branching reality).

**Extraction:** False completeness (model signals done when salient items are found,
not when all items are found); granularity collapse (findings reported at one level
of abstraction regardless of actual importance).

### Phase 2 Gate

MUST have 3–5 failure modes. Each MUST have: name, LLM mechanism, and consequence.

Do not proceed with vague concerns ("might not be detailed enough") or mechanisms that
don't explain model behavior. If you cannot identify 3 failure modes, the task may be
simple enough that this pipeline is unnecessary — say so.

### Rationalization Table

| Excuse | Reality |
|--------|---------|
| "The user's draft is already good" | The draft is diagnostic input. Diagnose its failures. |
| "This prompt is straightforward" | Straightforward prompts still have failure modes. Find them. |
| "I already know what the prompt needs" | That's a hypothesis. Validate it through analysis. |

---

## Phase 3: Structural Upgrades

Derive **2–5 design moves** from the failure analysis. For each:

- **Name** the move (3–5 words)
- **Upgrade type** (see taxonomy below)
- **Target failure mode(s)** — trace to Phase 2 names
- **Mechanism** — why does this structural choice counter the failure at the model
  behavior level?

### Upgrade Type Taxonomy

Match upgrade type to the failure class it addresses:

| Type | Addresses | Examples |
|------|-----------|---------|
| **Structural** | Structural absence, category omission | Required sections, explicit dimensions, phase gates, information-forward ordering |
| **Behavioral** | Sycophancy, sunk-cost bias, premature closure | Role shifts, pre-mortem framing, adversarial stance, perspective forcing |
| **Calibration** | Scope ambiguity, format mismatch, granularity collapse | Scope bounds, "skip when" rules, caps, output templates, granularity anchors |
| **Validation** | False completeness, unverifiable outputs | Self-check sections, confidence scoring, "done when" criteria, enumeration gates |

Every upgrade MUST trace to at least one Phase 2 failure mode. No traceability = decoration — cut it.

---

## Phase 4: Prompt Construction

Build the prompt. Output is a single markdown code block the user can copy and paste.

### Structural Requirements

- Section-based; each section has a single distinct purpose
- Information flows forward — earlier sections produce analysis that later sections
  depend on, not the reverse
- Output format specified, not left to model discretion
- Each Phase 3 upgrade appears as an identifiable structure in the prompt; if you
  can't point to where an upgrade lives, it wasn't implemented
- Ground rules consolidated into one section; blocking language only for genuinely
  non-negotiable constraints — overuse dilutes authority
- Self-contained: works when pasted cold into a new conversation with no prior context
- Every sentence earns its place; if it doesn't shape behavior or prevent a diagnosed
  failure, cut it

### Construction Checklist

- [ ] Every section traces to at least one Phase 3 upgrade
- [ ] Every Phase 3 upgrade is identifiable in the prompt
- [ ] Output format is specified
- [ ] Scope is bounded (out-of-scope stated, not just in-scope)
- [ ] No section requires the model to read the user's mind
- [ ] Blocking language reserved for genuinely non-negotiable rules
- [ ] Single copyable code block

### Semantic Validation

After the checklist, trace each Phase 2 failure mode through the constructed prompt:

> *"Where in the prompt does [failure mode name] get addressed, and how does that
> structure counter the model behavior that causes it?"*

If a failure mode has no answer, the prompt is incomplete. Add the missing structure
or explicitly acknowledge the trade-off.

---

## Phase 5: Design Rationale

For each major structural choice:

- **What it does** — the mechanism
- **Which failure mode it prevents** — name from Phase 2
- **What breaks if removed** — observable consequence for the user
- **What to tune first** — most likely adjustment if this aspect underperforms

**This phase is a validity check, not documentation.** If you cannot name a specific
failure mode a section prevents, the section is unjustified — remove it, or go back
to Phase 2 until the justification is explicit.

---

## Complexity Calibration

Match pipeline depth to task complexity.

| Complexity | Indicators | Approach |
|-----------|-----------|---------|
| **Simple** | ≤2 obvious failure modes, single task type, short output | Compress Phases 1–3 into one analysis paragraph; build directly |
| **Moderate** | 3–4 failure modes, possibly blended type | Full pipeline; Phase 5 can be brief |
| **Complex** | 5 failure modes, multiple task types, interaction effects | Full pipeline; Phase 5 is essential |

Phase 2 is never optional regardless of complexity. Compressing it to one paragraph is
acceptable. Skipping it is not.

---

## Meta-Rules

- **Rebuild, don't iterate.** The user's rough draft is diagnostic input. Do not polish
  it — rebuild from the failure analysis.
- **Match complexity to task.** A 4-section prompt covering real failure modes beats an
  8-section prompt covering hypothetical ones.
- **No generic advice.** Every recommendation must be specific to this prompt's job and
  failure modes. "Be specific" is not a design move.
- **Minimum sufficient prompt.** The constructed prompt should be the minimum size that
  addresses all diagnosed failure modes. Each section must justify its token cost.
- **Explain yourself.** Every structural choice has a reason tied to a specific failure
  mode and a model behavior mechanism. If you can't state both, the choice is unjustified.

## Red Flags — STOP and Reassess

- Writing Phase 4 before completing Phase 2
- An upgrade in Phase 3 that doesn't trace to a named failure mode
- An upgrade in Phase 3 with no named upgrade type
- A section in the prompt that exists "for completeness" rather than to counter a
  specific failure
- The prompt grows beyond what the diagnosed failure modes justify
- Phase 5 rationale is generic ("ensures thoroughness") rather than tied to a specific
  failure mode and mechanism
- Semantic validation in Phase 4 leaves a failure mode unanswered

## Worked Examples

For end-to-end examples of this pipeline applied to real prompts, including task-type
classification and LLM mechanism analysis, read
[references/worked-examples.md](references/worked-examples.md).

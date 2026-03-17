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
| 1 | Clarify the Job | Lock what the prompt must cause the model to do | Core behavior stated in one sentence |
| 2 | Naive Failure Analysis | Diagnose what goes wrong without intervention | 3–5 specific, named failure modes |
| 3 | Structural Upgrades | Design countermeasures | Each upgrade traces to ≥1 failure mode |
| 4 | Prompt Construction | Build the artifact | Passes construction checklist |
| 5 | Design Rationale | Explain choices for maintainability | Every major section has rationale |

**Execute phases in order. Do not skip or combine phases.**

## Phase 1: Clarify the Job

State in one sentence what the prompt must cause the model to do. This is
the core behavior — the single thing the prompt exists to produce.

If the user's request is ambiguous about what behavior they want, ask ONE
clarifying question. For minor ambiguity, state an assumption explicitly
and proceed.

**Context is fixed for this pipeline:**
- Deployment: Conversational turn (user pastes prompt into chat)
- Invocation: User-triggered (explicit, intentional)
- Output consumer: Human reading rendered markdown in a chat UI

## Phase 2: Naive Failure Analysis

**This is the load-bearing phase. The entire pipeline's value derives from it.**

First, describe the naive/beginner approach — what someone would write in
30 seconds for this job.

Then identify **3–5 specific, named failure modes** of the naive approach.
For each failure mode:

- **Name it** in 3–5 words (e.g., "Category omission via self-selection")
- **Describe the mechanism**: What does the model do wrong, and why?
- **Show the consequence**: What does the user get that they shouldn't?

### Failure Mode Categories to Sweep

Evaluate the naive prompt against each category. Not all will apply — but
check each before dismissing it:

- **Self-selection bias**: Model gravitates to easy/familiar aspects, skips hard ones
- **Structural absence**: No forcing function for completeness, order, or granularity
- **Scope drift**: Model expands or contracts scope without constraint
- **Format mismatch**: Output structure doesn't match how the consumer will use it
- **Anchoring to draft**: Model treats user's rough input as scaffold instead of symptom
- **Sycophancy/softening**: Model hedges, qualifies, or avoids direct statements
- **Premature closure**: Model produces an answer before completing analysis

### Phase 2 Gate

**MUST have 3–5 failure modes before proceeding. Each MUST have a name,
mechanism, and consequence.**

Do not proceed to Phase 3 with:
- Vague concerns ("might not be detailed enough")
- Fewer than 3 failure modes
- Failure modes without mechanisms

If you cannot identify 3 failure modes, the task may be simple enough that
a structured prompt is unnecessary. Say so explicitly — not everything
needs this pipeline.

### Rationalization Table

| Excuse to skip Phase 2 | Reality |
|-------------------------|---------|
| "The user's draft is already good" | The draft is diagnostic input, not a starting point. Diagnose its failures. |
| "This prompt is straightforward" | Straightforward prompts still have failure modes. Find them. |
| "I already know what the prompt needs" | That's an assumption. Validate it through failure analysis, not confidence. |

## Phase 3: Structural Upgrades

From the failure analysis, derive **2–4 key design moves**. For each:

- **Name** the move in 3–5 words
- **Trace** it to the specific failure mode(s) it addresses (by name)
- **Explain the mechanism**: Why does this structural choice fix the failure?

Every upgrade MUST trace to at least one failure mode from Phase 2. If an
upgrade doesn't address a diagnosed failure, it's decoration — cut it.

## Phase 4: Prompt Construction

Build the prompt. The output is a single markdown code block the user can
copy and paste into a conversation.

### Structural Requirements

**Architecture**
- Section-based structure where each section has a clear, distinct purpose
- Sections ordered so earlier sections produce analysis that later sections
  depend on (information flows forward, not backward)
- Output format specified — structured markdown (headers, labeled fields,
  consistent patterns) rather than open-ended prose

**Calibration Language**
- Scope boundaries: explicit "do not" / "skip when" instructions
- Granularity constraints: "each item should be..." / "cap at N items"
- Honesty prompts: "if uncertain, state what would resolve it rather than..."

**Ground Rules**
- Consolidate behavioral constraints into a dedicated section at the end
- This is where anti-patterns, scope limits, and quality bars live
- Use blocking language ("MUST", "NEVER") only for rules that are genuinely
  non-negotiable — overuse dilutes authority

**Self-Containment**
- The prompt works when pasted cold into a new conversation with no prior
  context. No implicit dependencies on other instructions.

**Concision**
- Every sentence must earn its place
- If a sentence doesn't directly shape model behavior or prevent a diagnosed
  failure mode, cut it

### Construction Checklist

Before presenting the prompt, verify:

- [ ] Every section traces to at least one structural upgrade from Phase 3
- [ ] Output format is specified, not left to model discretion
- [ ] Scope is bounded — the prompt says what's out of scope, not just in
- [ ] No section requires the model to read the user's mind — inputs and
      context requirements are explicit
- [ ] Ground rules use blocking language only for genuinely non-negotiable
      constraints
- [ ] The prompt is a single copyable block (markdown code fence)

## Phase 5: Design Rationale

For each major structural choice in the prompt, provide:

- **What it does** — the mechanism
- **What fails without it** — the failure mode it prevents (reference Phase 2)
- **What to tune** — what the user should adjust first if this aspect
  underperforms in practice

This section is part of the deliverable. Prompts without rationale are
unmaintainable — the next person to edit the prompt won't know which parts
are load-bearing.

## Meta-Rules

- **Rebuild, don't iterate.** The user's rough draft or naive example is
  diagnostic input, not a starting point. Do not polish it — rebuild from
  the failure analysis.
- **Match complexity to task.** A 5-section prompt covering real failure
  modes beats a 12-section prompt covering hypothetical ones. If the task
  is simple, the prompt should be simple. Say so.
- **No generic advice.** Every recommendation must be specific to THIS
  prompt's job and failure modes. "Be specific in your instructions" is
  not a design move.
- **Prompt complexity budget.** The constructed prompt should be the minimum
  size that addresses all diagnosed failure modes. Longer is not better.
  Each section must justify its token cost.

## Red Flags — STOP and Reassess

If you notice any of these during execution, pause and correct course:

- Writing the prompt (Phase 4) before completing failure analysis (Phase 2)
- An upgrade in Phase 3 that doesn't trace to a named failure mode
- A section in the prompt that exists "for completeness" rather than to
  counter a specific failure
- The prompt is growing beyond what the failure modes justify
- You're adding sections because the prompt "feels like it should have more"
- The design rationale (Phase 5) is generic rather than specific to this
  prompt's choices

## Worked Examples

For end-to-end examples of this pipeline applied to real prompts, read
[references/worked-examples.md](references/worked-examples.md).

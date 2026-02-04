# Simulation-Based Skill Assessment Framework v0.1.0

A comprehensive framework for assessing and improving Claude Code skills through empirical observation rather than structural compliance checking.

---

## Preamble: How to Use This Document

### What This Document Is

This document is a **specification for rebuilding the `improving-skills` skill**. The current `improving-skills` skill (located at `.claude/skills/improving-skills/SKILL.md` in this repository) fails because it assesses structural compliance rather than functional effectiveness. This framework defines a replacement approach based on empirical observation.

### What This Document Is NOT

- **Not the skill itself.** This is a framework specification. The actual skill that implements this framework will be a separate file (`SKILL.md`) that references this document for detailed procedures.
- **Not a manual process.** This framework is designed to be executed by Claude as part of the `improving-skills` skill, not by humans following steps manually.
- **Not complete.** Version 0.1.0 focuses on scenario generation. Skill architecture design and subagent orchestration are noted as open items.

### Who Executes This Framework

**Claude executes this framework** when the `improving-skills` skill is invoked. The skill will:

1. Load this framework as reference material
2. Follow the 8-step scenario generation process (Section 3)
3. Execute scenarios using subagents (Section 4)
4. Analyze gaps and generate fixes (Section 5)
5. Iterate until quality threshold is met

The framework is written as instructions for Claude, not as documentation for humans—though humans can read it to understand the methodology.

### Relationship to the Skill

```
┌─────────────────────────────────────────────────────────────────┐
│  improving-skills/SKILL.md (TO BE CREATED)                      │
│                                                                  │
│  - Compact operational instructions                              │
│  - Trigger phrases and frontmatter                               │
│  - High-level workflow                                           │
│  - References this framework for detailed procedures             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ references
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  THIS DOCUMENT                                                   │
│  simulation-based-skill-assessment_v0.1.0.md                     │
│                                                                  │
│  - Complete methodology specification                            │
│  - Detailed procedures for each step                             │
│  - Reference tables and schemas                                  │
│  - Theoretical foundation and rationale                          │
└─────────────────────────────────────────────────────────────────┘
```

The skill will be concise (~500 lines per skills-guide.md recommendations). This framework document provides the complete specification that the skill references when detailed procedures are needed.

### Subagent Mechanics

This framework requires spawning subagents to run scenarios. In Claude Code:

- **Subagents** are spawned using the `Task` tool with isolated context
- **Baseline subagents** receive the scenario task WITHOUT the target skill in their system prompt
- **Test subagents** receive the scenario task WITH the target skill injected into their system prompt
- **Observations** are captured from subagent responses and tool usage

The skill implementing this framework will handle subagent orchestration. Section 4 describes WHAT to observe; the skill will implement HOW to spawn and capture.

### Source Materials

This framework was developed through structured discussion documented in:

- **Primary source:** `docs/discussions/improving-skills-failure-modes-and-simulation-based-assessment.md`
- **Handoff:** `docs/handoffs/2026-02-03_21-30_improving-skills-simulation-based-assessment.md`

Key decisions from those discussions are incorporated into this document. The source materials provide additional context but are not required reading—this document is designed to be self-contained.

### Decision Rationale

Key design decisions and their rationale:

| Decision | Rationale |
|----------|-----------|
| **5-7 scenarios** | Balance between coverage and cost. 5 is the default; 7 for complex skills. Fewer scenarios mean faster iteration; more scenarios catch more edge cases. 5-7 emerged as the sweet spot from discussion. |
| **4 skill types** | Derived from `docs/references/skills-guide.md`. These are the established skill categories in this project, not invented for this framework. Each type has different expected behaviors that drive scenario generation. |
| **8 steps** | Decomposition of scenario generation into discrete, testable phases. Steps can potentially run in parallel (1+4, 3+5) but are presented sequentially for clarity. |
| **P0/P1/P2 priorities** | Standard priority tiers. P0 = must pass (core purpose), P1 = should pass (important behaviors), P2 = nice to pass (edge cases). Thresholds (≥10 for P0) set to produce ~20% P0, ~50% P1, ~30% P2 distribution. |
| **3 iteration limit** | Prevents infinite loops. If skill isn't improving after 3 iterations, the problem likely requires human review rather than more automated attempts. |
| **Empirical over theoretical** | Core insight: theoretical assessment (comparing to guidelines) produces the failure mode we're trying to fix. Empirical assessment (observing actual behavior) is the solution. |

### Project Context

This document lives in `claude-code-tool-dev`, a monorepo for developing Claude Code extensions:

```
claude-code-tool-dev/
├── .claude/
│   └── skills/
│       └── improving-skills/     ← Skill to be rebuilt
│           └── SKILL.md
├── docs/
│   ├── frameworks/               ← THIS DOCUMENT
│   │   └── simulation-based-skill-assessment_v0.1.0.md
│   ├── discussions/              ← Source discussion
│   └── references/
│       └── skills-guide.md       ← Skill type definitions
└── ...
```

The framework will be used to rebuild `improving-skills`. Once validated, the same methodology could be applied to assess other skills.

### Implementation Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **1. Framework specification** | ✓ Complete | This document |
| **2. Skill architecture design** | Not started | Design the SKILL.md that implements this framework |
| **3. Subagent orchestration** | Not started | Implement mechanics for spawning and observing subagents |
| **4. Worked example** | Not started | Validate framework by applying to a real skill |
| **5. Skill implementation** | Not started | Create the new improving-skills/SKILL.md |
| **6. Validation** | Not started | Test the skill on multiple target skills |

This document completes Phase 1. Subsequent phases will produce additional artifacts.

### Minimum Viable Usage

Despite open items, this framework can be used now for:

1. **Manual skill assessment:** A human or Claude can follow Sections 3-5 manually to assess a skill
2. **Scenario generation:** Section 3 is complete and can generate scenarios for any skill
3. **Understanding the methodology:** The theoretical foundation (Sections 1-2) explains why this approach works

Full automation requires completing Phases 2-3 (skill architecture and subagent orchestration).

### Reading Guide

| If you want to... | Read... |
|-------------------|---------|
| Understand why this exists | Section 1 (Introduction) |
| Understand the approach | Section 2 (Theoretical Foundation) |
| Generate scenarios for a skill | Section 3 (Scenario Generation Framework) |
| Run and evaluate scenarios | Sections 4-5 (Execution and Gap Analysis) |
| Look up specific procedures | Section 7 (Reference Tables) |
| Understand key principles | Section 8 (Key Insights) |

---

## Table of Contents

- [Preamble: How to Use This Document](#preamble-how-to-use-this-document)
  - [What This Document Is](#what-this-document-is)
  - [What This Document Is NOT](#what-this-document-is-not)
  - [Who Executes This Framework](#who-executes-this-framework)
  - [Relationship to the Skill](#relationship-to-the-skill)
  - [Subagent Mechanics](#subagent-mechanics)
  - [Source Materials](#source-materials)
  - [Decision Rationale](#decision-rationale)
  - [Project Context](#project-context)
  - [Implementation Roadmap](#implementation-roadmap)
  - [Minimum Viable Usage](#minimum-viable-usage)
  - [Reading Guide](#reading-guide)
- [1. Introduction](#1-introduction)
  - [1.1 Purpose](#11-purpose)
  - [1.2 Problem Statement](#12-problem-statement)
  - [1.3 Root Cause Analysis](#13-root-cause-analysis)
  - [1.4 The Solution: Simulation-Based Assessment](#14-the-solution-simulation-based-assessment)
- [2. Theoretical Foundation](#2-theoretical-foundation)
  - [2.1 The Assessment Hierarchy](#21-the-assessment-hierarchy)
  - [2.2 The Simulation Mechanism](#22-the-simulation-mechanism)
  - [2.3 Key Principles](#23-key-principles)
  - [2.4 Known Limitations](#24-known-limitations)
- [3. Scenario Generation Framework](#3-scenario-generation-framework)
  - [3.1 Overview](#31-overview)
  - [3.2 Step 1: Purpose Determination](#32-step-1-purpose-determination)
  - [3.3 Step 2: Skill Type Classification](#33-step-2-skill-type-classification)
  - [3.4 Step 3: Use Case Extraction](#34-step-3-use-case-extraction)
  - [3.5 Step 4: Trigger Condition Analysis](#35-step-4-trigger-condition-analysis)
  - [3.6 Step 5: Instruction to Behavior Mapping](#36-step-5-instruction-to-behavior-mapping)
  - [3.7 Step 6: Expected Behavior Derivation](#37-step-6-expected-behavior-derivation)
  - [3.8 Step 7: Adversarial Scenario Generation](#38-step-7-adversarial-scenario-generation)
  - [3.9 Step 8: Scenario Assembly and Prioritization](#39-step-8-scenario-assembly-and-prioritization)
- [4. Scenario Execution](#4-scenario-execution)
  - [4.1 Subagent Configuration](#41-subagent-configuration)
  - [4.2 Baseline Measurement](#42-baseline-measurement)
  - [4.3 Skill-Assisted Measurement](#43-skill-assisted-measurement)
  - [4.4 Delta Evaluation](#44-delta-evaluation)
- [5. Gap Analysis and Improvement](#5-gap-analysis-and-improvement)
  - [5.1 Gap Identification](#51-gap-identification)
  - [5.2 Root Cause Classification](#52-root-cause-classification)
  - [5.3 Fix Generation](#53-fix-generation)
  - [5.4 Iteration Protocol](#54-iteration-protocol)
- [6. Supporting Components](#6-supporting-components)
  - [6.1 Scenario Schema](#61-scenario-schema)
  - [6.2 Success Criteria Derivation](#62-success-criteria-derivation)
  - [6.3 Overfitting Prevention](#63-overfitting-prevention)
  - [6.4 Hard-to-Test Skills](#64-hard-to-test-skills)
  - [6.5 Cost Calibration](#65-cost-calibration)
- [7. Reference Tables](#7-reference-tables)
  - [7.1 Skill Type Indicators](#71-skill-type-indicators)
  - [7.2 Subjective Term Proxies](#72-subjective-term-proxies)
  - [7.3 Shortcut Pattern Library](#73-shortcut-pattern-library)
  - [7.4 Adversarial Probe Library](#74-adversarial-probe-library)
- [8. Key Insights](#8-key-insights)

---

## 1. Introduction

### 1.1 Purpose

This framework provides a methodology for assessing whether Claude Code skills achieve their functional purposes, not merely whether they comply with structural guidelines. It replaces theoretical assessment (reasoning about what might happen) with empirical measurement (observing what actually happens).

### 1.2 Problem Statement

The existing `improving-skills` skill fails to achieve its primary objective. Two failure modes were identified:

1. **Low-quality findings despite completing assessment:** Claude went through the motions procedurally without achieving the substance of what those steps were meant to produce.

2. **Assessment based on structural compliance, not functional effectiveness:** A skill could score well on assessment while completely failing at its stated purpose.

### 1.3 Root Cause Analysis

#### The Pattern: Form vs. Function Conflation

Both failures stem from the same root: the skill assesses how a skill is written rather than whether it achieves its purpose.

**Evidence from skill architecture:**

- Assessment steps prioritize structural compliance ("How it compares to skills-guide.md standards")
- Strengths defined as "Elements that follow skills-guide.md recommendations"
- Weaknesses defined as "Deviations from skills-guide.md standards"

The skill includes a "Center Claude's Actual Needs" section with correct questions about effectiveness, but this is positioned as a lens, not integrated into assessment steps. By the time Claude reaches assessment, it's back to checking structural compliance.

#### The Measurement Problem

Structural compliance is checkable:

| Structural Check | Verifiability |
|------------------|---------------|
| "Does it have trigger phrases?" | Binary, verifiable |
| "Does it use blocking language?" | Binary, verifiable |
| "Is it under 500 lines?" | Binary, verifiable |

Functional effectiveness is not directly checkable:

| Functional Check | Challenge |
|------------------|-----------|
| "Will Claude follow this correctly?" | Requires simulation |
| "Does this prevent failure modes?" | Requires empirical evidence |
| "Is this genuinely useful to Claude?" | Requires understanding Claude's capabilities |

The skill defaults to what can be checked. This is a rational response to an ill-defined problem, but it produces the wrong outcomes.

#### The Discipline Skill Paradox

Discipline skills exist because Claude shortcuts processes. But if the assessment of discipline skills is itself a checklist, Claude can shortcut the assessment by completing the checklist without genuine analysis.

The skill enforces process compliance, not substantive thinking. Claude can satisfy every step and gate while producing hollow output.

#### The Self-Referential Proof

If you assessed `improving-skills` using its own methodology:

- Structure: ✓ Has phases, gates, rationalization tables, anti-patterns
- Type-appropriate: ✓ Uses discipline skill techniques correctly
- Follows skills-guide.md: ✓ Under 500 lines, has trigger phrases

It would score well. Yet it fails at its stated purpose. This demonstrates that structural compliance ≠ functional effectiveness.

### 1.4 The Solution: Simulation-Based Assessment

Replace theoretical assessment with empirical measurement.

| Current Approach | Proposed Approach |
|------------------|-------------------|
| Read the skill, reason about what would happen | Run the skill, observe what actually happens |
| Compare against standards document | Compare against baseline behavior |
| Assessment = expert judgment | Assessment = experimental evidence |
| "This should work because..." | "This does/doesn't work because we observed..." |

This treats skill improvement as empirical science, not code review.

---

## 2. Theoretical Foundation

### 2.1 The Assessment Hierarchy

| Layer | Method | Role |
|-------|--------|------|
| **Primary** | Empirical (simulation-based) | Determines whether skill achieves purpose |
| **Supporting** | Theoretical (structural analysis) | Quick screening, remediation guidance, sanity checks |

Neither alone is sufficient:

- **Empirical without theoretical:** Misses obvious structural issues, lacks remediation vocabulary
- **Theoretical without empirical:** Produces the failure mode documented above — compliance without effectiveness

Together: Theoretical analysis catches surface issues and guides fixes. Empirical assessment validates that fixes actually work.

### 2.2 The Simulation Mechanism

The core loop:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PURPOSE EXTRACTION                                          │
│     What is this skill trying to achieve?                       │
│     What behavior change does it intend?                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. SCENARIO DESIGN                                             │
│     What tasks would reveal whether it achieves that?           │
│     [This framework's primary focus]                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. BASELINE MEASUREMENT                                        │
│     Deploy subagent WITHOUT skill                               │
│     Give it a task the skill is designed to help with           │
│     Observe: approach, struggles, shortcuts, quality            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. SKILL-ASSISTED MEASUREMENT                                  │
│     Deploy subagent WITH skill                                  │
│     Same task, same conditions                                  │
│     Observe: behavior delta, compliance, shortcuts, quality     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. DELTA EVALUATION                                            │
│     Compare baseline vs skill-assisted                          │
│     Identify: where skill helps, fails to help, hurts, ignored  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. GAP ANALYSIS                                                │
│     Map observed failures to root causes                        │
│     Identify improvement targets                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. FIX GENERATION                                              │
│     Propose skill modifications addressing failures             │
│     Prefer root-cause fixes over symptom patches                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  8. RE-TEST                                                     │
│     Run scenarios again with fixed skill                        │
│     Verify improvement, check for regressions                   │
│     Iterate until threshold met                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Why Subagents Enable This

Subagents run in isolated context windows with:

- Custom system prompt
- Specific tool access
- Independent permissions
- Isolated context (no contamination from parent conversation)

This allows controlled experiments:

- Baseline subagent truly doesn't have the skill
- Test subagent truly does have the skill
- Same task, same conditions, different skill presence

### 2.3 Key Principles

#### Purpose-First + Simulation-Based Work Together

| Purpose-First | Simulation-Based |
|---------------|------------------|
| Defines what should happen | Measures what actually happens |
| "This skill should cause Claude to assess before editing" | "Did the subagent assess before editing?" |
| Establishes success criteria | Tests against those criteria |

Purpose-First Framing sets the target. Simulation-Based Assessment measures against it. The gap between target and observed behavior = the work.

#### Quality Over Quantity

5 well-chosen scenarios that cover the behavior landscape (happy path, edge cases, boundaries) matter more than volume.

#### Variance is Signal

If 4 scenarios show one pattern and 1 shows another, that's signal, not noise. The outlier reveals where the skill behaves differently. Investigate variance rather than averaging it out.

#### Criteria for Well-Chosen Scenarios

- Covers each distinct mode/use case of the skill
- Includes at least one happy-path scenario
- Includes at least one edge case that could reveal fragility
- Includes at least one scenario that tests skill boundaries

### 2.4 Known Limitations

#### What This Framework Cannot Test

| Limitation | Description |
|------------|-------------|
| Multi-session effects | Subagents are isolated; can't observe accumulation across sessions |
| Skill interactions | Testing in isolation may miss conflicts when skills are co-loaded |
| Emergent behaviors | Combinatorial explosion of skill combinations |
| Production-specific failures | Test environment differs from real usage |
| Long-term behavioral drift | Single-session testing only |

#### Irreducible Judgment Points

| Point | Why Irreducible |
|-------|-----------------|
| Proxy selection | Requires understanding what subjective terms are "about" |
| Goal inference | Requires understanding instruction intent |
| Purpose centrality | Requires understanding what matters most |
| Failure impact | Requires understanding consequences |

These are structured and traceable, but not eliminable. The framework makes judgment explicit, not absent.

#### The Oracle Problem

To judge whether skill-assisted behavior is "correct," we need to know what correct looks like. This requires either:

- Pre-existing ground truth (planted issues, known-good skills)
- Human judgment (doesn't scale)
- Another Claude instance (same biases)

The framework uses criteria-based evaluation with Claude-as-evaluator, making criteria explicit and auditable. This mitigates but doesn't fully solve the oracle problem.

#### The Fundamental Tension

> The framework is designed to test whether skills achieve their purposes. But if purposes are unclear, the framework tests whether skills match their documentation — which is a sophisticated form of structural compliance, not functional assessment.

The framework pushes the problem up a level rather than solving it completely. This is acceptable as long as the limitation is acknowledged.

---

## 3. Scenario Generation Framework

### 3.1 Overview

**Input:** A target skill to assess (SKILL.md + supporting files)

**Output:** 5-7 prioritized test scenarios with success criteria

**The 8 Steps:**

| Step | Name | Purpose |
|------|------|---------|
| 1 | Purpose Determination | Establish what the skill is trying to achieve |
| 2 | Skill Type Classification | Classify to enable type-appropriate scenarios |
| 3 | Use Case Extraction | Gather or generate scenario seeds |
| 4 | Trigger Condition Analysis | Understand when skill should/shouldn't activate |
| 5 | Instruction → Behavior Mapping | Transform instructions into testable behaviors |
| 6 | Expected Behavior Derivation | Use type definitions to predict expected behaviors |
| 7 | Adversarial Scenario Generation | Create edge cases and stress tests |
| 8 | Scenario Assembly | Combine and prioritize into final suite |

**Dual-Path Design:**

Each step has both:

- **Extraction path:** When skill provides material (well-designed skills)
- **Generation path:** When skill doesn't provide material (poorly-designed skills)

The difficulty of generation is itself diagnostic. If the framework struggles to generate scenarios because the skill is unclear, that predicts Claude will struggle to follow it.

---

### 3.2 Step 1: Purpose Determination

**Goal:** Establish what the skill is trying to achieve — not its structure, its intent.

#### Extraction Path

Read stated purpose from:

1. Description field in YAML frontmatter
2. Opening section of SKILL.md body
3. Skill name (may imply purpose)

Look for explicit statements of:

- What behavior the skill changes
- What outcomes the skill produces
- What problems the skill solves

#### Generation Path: Goal Inference Method

When purpose is not explicitly stated, infer from instructions.

**For each instruction in the skill:**

```
1. Identify CONSTRAINT type:
   - Prescriptive: "Do X" → Goal: Ensure X happens
   - Prohibitive: "Don't do Y" → Goal: Prevent Y
   - Conditional: "When A, do B" → Goal: Appropriate response to A
   - Quality: "Do X well" → Goal: Achieve quality standard for X

2. Identify DOMAIN:
   - What category of work does this affect?
   - Examples: code quality, safety, communication, process, output format

3. Synthesize goal:
   [Constraint type] + [Domain] = Implied goal

   Example:
   - Instruction: "Always run tests before committing"
   - Constraint: Prescriptive (ensure X happens)
   - Domain: Code quality / verification
   - Goal: "Ensure code is verified before integration"

4. Abstract to purpose level:
   - Multiple goals in same domain → higher-level purpose
   - "Ensure verification" + "Check errors" + "Run linter"
     → Purpose: "Maintain code quality"
```

#### Fallback Path: Purpose Hypothesis Generation

When purpose is unclear even after goal inference:

```
STEP 1: List all inferred goals from instructions

STEP 2: Cluster by similarity
   For each pair of goals, assess:
   - Same domain? (+2)
   - Same constraint type? (+1)
   - Mutual support? (+1)
   - Similarity score ≥ 3 → same cluster

STEP 3: Name each cluster by common theme

STEP 4: Score clusters
   - Coverage (40%): How many instructions does this explain?
   - Coherence (30%): Do instructions form unified approach?
   - Name alignment (20%): Does skill name suggest this?
   - Specificity (10%): More specific = more testable

STEP 5: Select hypothesis
   - Top hypothesis >70%: Proceed as primary
   - Top two within 10%: Generate scenarios for both
   - All hypotheses <50%: Flag as "purpose-incoherent"
```

#### Handling Purpose-Incoherent Skills

When no coherent purpose can be inferred:

```
REPORT:
  skill: [name]
  assessment: purpose-incoherent

  findings:
    - Instructions do not point to unified goal
    - Multiple contradictory purposes implied
    - Skill may be attempting too many things

  extracted_fragments:
    - fragment: "[subset of instructions]"
      implied_purpose: "[purpose A]"
    - fragment: "[subset of instructions]"
      implied_purpose: "[purpose B]"

  recommendation:
    - Split skill into focused sub-skills
    - Or: Clarify purpose and remove contradictions

  limited_testing:
    - Can still test individual instruction compliance
    - Cannot test overall skill effectiveness
    - Scenarios will test fragments, not whole
```

#### Output Schema

```yaml
purpose:
  statement: "[extracted or inferred purpose]"
  confidence: extracted | inferred | unclear
  method: extraction | goal_inference | hypothesis_generation

  alternative_hypotheses:  # if applicable
    - hypothesis: "[alternative purpose]"
      score: [0-100]
      evidence: "[supporting instructions]"

  evidence: "[instructions/content supporting primary purpose]"

  diagnostic_signals:
    - "[any concerns about purpose clarity]"
```

---

### 3.3 Step 2: Skill Type Classification

**Goal:** Classify the skill to enable type-appropriate scenario generation and expected behavior derivation.

#### The Four Skill Types

| Type | Primary Function | Key Characteristic |
|------|------------------|-------------------|
| **Discipline** | Enforce methodologies Claude would shortcut | Makes phases mandatory, requires evidence |
| **Technique** | Teach structured methods | Provides how-to for complex activities |
| **Pattern** | Encode reusable structures | Captures domain expertise in templates |
| **Reference** | Surface external information | Provides lookup and knowledge access |

Most skills blend types but lean toward one. Identify the dominant type, then borrow techniques from others as needed.

#### Classification Procedure

```
STEP 1: Score indicator presence (0-3 per indicator)

   DISCIPLINE indicators:
   - Phase gates between stages
   - Blocking language ("MUST", "NEVER", "before ANY")
   - Evidence requirements before transitions
   - Anti-pattern tables naming shortcuts
   - Red flag lists for rationalization
   - Checklists requiring verification

   TECHNIQUE indicators:
   - Step-by-step workflows
   - Decision trees for variations
   - Templates guiding execution
   - Worked examples with real scenarios
   - Heuristics for sub-technique selection
   - Quality criteria per stage

   PATTERN indicators:
   - Template structures (file layouts, hierarchies)
   - Style guides with before/after
   - Checklists of elements to include
   - Anti-patterns with explanations
   - Variation catalogs
   - Decision tables for pattern selection

   REFERENCE indicators:
   - Search tool integration
   - Query guidance
   - Quick-reference tables
   - Links to external sources
   - Freshness indicators
   - Cross-reference maps

STEP 2: Sum scores per type

STEP 3: Assign primary type
   - Highest score = primary type
   - If top two within 20%: Mark as hybrid, note both

STEP 4: Assess confidence
   - Primary score >10: High confidence
   - Primary score 5-10: Medium confidence
   - Primary score <5: Low confidence
   - All scores <5: Flag as "type-ambiguous"
```

#### Handling Type-Ambiguous Skills

When skill doesn't clearly fit any type:

```
APPROACH 1: Default to Technique
   - Most permissive type
   - Generates general-purpose scenarios

APPROACH 2: Test multiple types
   - Generate scenarios for top 2 types
   - Identify which produces better coverage

APPROACH 3: Flag for structural review
   - Skill may need redesign before assessment
   - Report type ambiguity as finding
```

#### Output Schema

```yaml
type:
  primary: discipline | technique | pattern | reference
  secondary: [type, if hybrid]
  confidence: high | medium | low

  scores:
    discipline: [0-15]
    technique: [0-15]
    pattern: [0-15]
    reference: [0-15]

  indicators_found:
    discipline: ["list of indicators present"]
    technique: ["list of indicators present"]
    pattern: ["list of indicators present"]
    reference: ["list of indicators present"]

  diagnostic_signals:
    - "[any concerns about type clarity]"
```

---

### 3.4 Step 3: Use Case Extraction

**Goal:** Gather or generate scenario seeds that exercise the skill's intended functionality.

#### Extraction Path

Well-designed skills include use cases in their documentation. Look for:

1. **Explicit use case sections** with trigger → steps → result format
2. **Examples** showing skill application
3. **Trigger phrases** in description field
4. **Troubleshooting sections** (reveal failure scenarios)

**Use case extraction template:**

```yaml
use_case:
  name: "[descriptive name]"
  trigger: "[user message or situation]"
  steps:
    - "[what happens first]"
    - "[what happens next]"
    - "[...]"
  result: "[expected outcome]"
```

#### Generation Path

When use cases aren't provided, generate from purpose + type.

**Generation heuristics by type:**

| Type | Generation Logic |
|------|------------------|
| **Discipline** | Create situation where Claude would naturally shortcut; test if skill prevents it |
| **Technique** | Create task requiring the method; test if skill guides the approach |
| **Pattern** | Create task where pattern applies; test if skill provides structure |
| **Reference** | Create query requiring external info; test if skill surfaces it |

**Discipline scenario generation:**

```
1. Identify what the skill is trying to enforce
2. Identify Claude's natural tendency to shortcut this
3. Create situation that triggers the natural tendency
4. Success = skill prevents shortcut and enforces process

Example:
- Skill enforces: "Read file before editing"
- Natural tendency: Edit directly when task seems simple
- Scenario: "Add a logging statement to utils.py"
- Success: Claude reads utils.py before editing
```

**Technique scenario generation:**

```
1. Identify the method the skill teaches
2. Create task that requires this method
3. Success = skill guides Claude through method correctly

Example:
- Skill teaches: Systematic debugging approach
- Scenario: "This function returns wrong results sometimes"
- Success: Claude follows debugging steps, not random guessing
```

**Pattern scenario generation:**

```
1. Identify the pattern the skill encodes
2. Create task where pattern applies
3. Success = skill provides pattern, Claude applies it

Example:
- Skill provides: Error handling pattern
- Scenario: "Add error handling to this API call"
- Success: Claude uses skill's pattern, not ad-hoc approach
```

**Reference scenario generation:**

```
1. Identify information the skill surfaces
2. Create query requiring that information
3. Success = skill surfaces correct information

Example:
- Skill provides: API documentation
- Scenario: "What parameters does createUser accept?"
- Success: Claude queries skill's reference, provides correct info
```

#### Instruction-Sparse Skills

For skills with few actionable instructions:

```
1. Check skill type:
   - Reference skills may have content, not instructions
   - Pattern skills may have templates, not imperatives

2. For Reference skills:
   - Purpose = "Provide accurate information about [domain]"
   - Generate queries that test information provision

3. For Pattern skills:
   - Purpose = "Apply [pattern] to relevant situations"
   - Generate tasks where pattern should be recognized

4. Extract implicit instructions from:
   - Examples (what does example demonstrate as correct?)
   - Templates (what does template require?)
   - Structure (what does organization imply about priorities?)
```

#### Output

3-5 scenario seeds in use case format. These will be refined in later steps.

---

### 3.5 Step 4: Trigger Condition Analysis

**Goal:** Understand when the skill should activate and when it should NOT activate.

#### Extraction Path

Parse trigger conditions from:

1. **Description field:** Look for "Use when...", "Activate when...", trigger phrases
2. **Frontmatter:** Check for explicit trigger configuration
3. **Opening sections:** May describe activation conditions

#### Generation Path

When triggers aren't explicit, derive from purpose:

```
1. Core question: "When would this skill be relevant?"

2. Identify positive triggers:
   - What user messages should activate?
   - What task types should activate?
   - What file types or contexts should activate?

3. Identify negative triggers:
   - What should explicitly NOT trigger this skill?
   - What similar-seeming tasks are out of scope?
   - What would be a false positive activation?

4. Test boundary conditions:
   - Tasks at the edge of the skill's scope
   - Tasks that partially match triggers
```

#### Trigger Analysis Questions

| Category | Questions |
|----------|-----------|
| **User messages** | What phrases indicate this skill is needed? What synonyms or variations? |
| **Task types** | What categories of work? (Debugging, writing, reviewing, etc.) |
| **File types** | Does skill apply to specific files? (.md, .py, config files, etc.) |
| **Context** | Is prior conversation state relevant? Project type? |
| **Negatives** | What looks similar but shouldn't trigger? |

#### Output Schema

```yaml
triggers:
  positive:
    user_messages:
      - "[trigger phrase 1]"
      - "[trigger phrase 2]"
    task_types:
      - "[task category]"
    file_types:
      - "[file pattern]"
    contexts:
      - "[context condition]"

  negative:
    - situation: "[what shouldn't trigger]"
      reason: "[why it's out of scope]"

  boundary:
    - situation: "[edge case]"
      expected: activate | not_activate | unclear

  confidence: extracted | inferred
```

---

### 3.6 Step 5: Instruction to Behavior Mapping

**Goal:** Transform skill instructions into testable, observable behaviors.

This is the most complex step. Instructions in skills are often vague, subjective, or underspecified. This step provides a systematic procedure for interpretation.

#### Phase A: Instruction Extraction

Before interpretation, extract instructions from skill content.

**Extraction patterns:**

| Pattern | Example | Instruction Type |
|---------|---------|------------------|
| Imperative | "Always run tests" | Prescriptive |
| Prohibition | "Never commit directly" | Prohibitive |
| Conditional | "If tests fail, fix before proceeding" | Conditional |
| Quality | "Ensure code is readable" | Quality standard |
| Goal | "Achieve full coverage" | Outcome-focused |

**Extraction procedure:**

```
1. Identify imperative statements (must, should, always, never, do, don't)
2. Identify conditional rules (if/when/unless → then)
3. Identify constraints (boundaries, limits, exceptions)
4. Identify goals/outcomes (ensure, achieve, produce)

For complex instructions ("If X, then Y, unless Z"):
   Decompose into atomic conditions:
   - Instruction 1: When X is true AND Z is false → do Y
   - Instruction 2: When Z is true → Y does not apply

Each extraction = one instruction unit for interpretation
```

#### Phase B: Decomposition

For each extracted instruction, identify components:

| Component | Question | Example |
|-----------|----------|---------|
| **ACTION** | What verb? | validate, check, ensure, create, avoid |
| **OBJECT** | What target? | code, output, input, file, response |
| **MODIFIER** | How? | thoroughly, carefully, always, never |
| **CONDITION** | When? | before X, after Y, when Z |

**Mark missing components:**

- If ACTION missing → "underspecified: no action"
- If OBJECT missing → "underspecified: no target"
- If CONDITION missing → "implicit: always" or "underspecified"
- If MODIFIER is vague → requires operationalization (Phase C)

#### Phase C: Operationalization

Transform subjective terms into observable proxies.

**Proxy Discovery Method:**

```
1. Identify the subjective term (e.g., "quality", "thorough", "proper")

2. Ask: "What would someone OBSERVE to conclude this term applies?"
   - Not: what does the term mean abstractly?
   - But: what evidence would demonstrate it?

3. Generate candidate proxies:
   - Absence of negative indicators (no errors, no warnings)
   - Presence of positive indicators (tests pass, requirements met)
   - Quantitative thresholds (coverage %, response time)
   - Structural markers (documentation exists, types annotated)

4. Validate each proxy:
   - Is it observable? (Can we actually check it?)
   - Is it relevant? (Does it actually indicate the term?)
   - Is it sufficient? (Would passing convince someone?)

5. If no valid proxies found:
   - Mark: "subjective: requires human judgment"
   - Generate scenarios that surface the term for evaluation
   - Success criteria: "Evaluator judges [term] is achieved"
```

**Common proxy mappings:**

| Subjective Term | Observable Proxies |
|-----------------|-------------------|
| quality | No errors, meets requirements, passes tests, follows conventions |
| thorough | All cases covered, all paths checked, edge cases addressed |
| clear | Short sentences, defined terms, examples included, structured |
| proper | Follows documented conventions, no warnings, consistent style |
| secure | No known vulnerabilities, input validated, secrets protected |
| efficient | Meets performance threshold, no redundancy, minimal resource use |
| readable | Descriptive names, logical structure, appropriate comments |
| robust | Handles errors, validates input, recovers gracefully |

See [Section 7.2](#72-subjective-term-proxies) for complete proxy reference.

#### Phase D: Exemplification

Generate concrete examples of compliance and violation.

```
For instruction: "[instruction text]"

COMPLIANT example:
   "Following this instruction looks like: [specific scenario where instruction is followed]"

VIOLATION example:
   "Violating this instruction looks like: [specific scenario where instruction is violated]"
```

**Purpose:** If you can't generate examples, the instruction is too abstract to test.

**Failure handling:** If examples cannot be generated, mark instruction as "untestable: cannot exemplify"

#### Phase E: Boundary Definition

Define the edges of compliance:

| Boundary | Definition |
|----------|------------|
| **MINIMUM** | What's the least that counts as compliance? |
| **MAXIMUM** | What's the most thorough compliance? |
| **CLEAR VIOLATION** | What unambiguously fails? |

The gap between minimum and maximum = degree of freedom the instruction allows.

- Large gap → instruction allows significant interpretation
- Small gap → instruction is precise
- No clear violation → instruction may be untestable

#### Phase F: Output Generation

Combine all phases into structured output:

```yaml
instruction:
  id: "[unique identifier]"
  original: "[exact text from skill]"
  source_location: "[where in skill this came from]"

  decomposition:
    action: "[verb]" | null
    object: "[target]" | null
    modifier: "[how]" | null
    condition: "[when]" | null

  underspecification:
    - component: "[missing component]"
      impact: "[how this affects testing]"

  operationalization:
    subjective_terms:
      - term: "[subjective word]"
        proxies:
          - proxy: "[observable indicator]"
            confidence: high | medium | low
        fallback: "subjective: requires human judgment" | null

  examples:
    compliant: "[specific example of following]"
    violation: "[specific example of violating]"

  boundaries:
    minimum: "[least that counts as compliance]"
    maximum: "[most thorough compliance]"
    clear_violation: "[unambiguous failure]"

  testable_behaviors:
    - behavior: "[specific observable action]"
      pass_criterion: "[how to know it passed]"
      fail_criterion: "[how to know it failed]"

  interpretation_confidence: high | medium | low

  notes: "[any interpretation assumptions or caveats]"
```

#### Confidence Level Assignment

| Level | Criteria |
|-------|----------|
| **High** | All components present, proxies found, examples generated, boundaries clear |
| **Medium** | Some components inferred, proxies approximate, examples possible but varied |
| **Low** | Major components missing, proxies uncertain, examples require significant inference |

**Rule:** Low-confidence interpretations should generate multiple scenario variants to test different interpretations.

#### Handling Interpretation Failure

| Failure Mode | Action |
|--------------|--------|
| No actionable content | Report: "Instruction contains no testable action" |
| All terms subjective with no proxies | Report: "Instruction requires subjective judgment; test with multiple evaluators" |
| Self-contradictory | Report: "Instruction contains contradiction: [X] vs [Y]" |
| Context-dependent | Report: "Behavior depends on context; generate scenario variants" |

---

### 3.7 Step 6: Expected Behavior Derivation

**Goal:** Use skill type definitions to predict expected behaviors, then cross-reference with actual skill content.

#### Expected Behaviors by Type

| Type | Expected Technique | Structural Check | Functional Check |
|------|-------------------|------------------|------------------|
| **Discipline** | Phase gates | Are gates defined? | Do gates block progression? |
| | Evidence requirements | Are requirements stated? | Is evidence actually required? |
| | Anti-pattern tables | Are shortcuts named? | Are shortcuts avoided? |
| | Red flag lists | Are rationalizations listed? | Are red flags recognized? |
| | Blocking language | Is MUST/NEVER used? | Is language enforced? |
| **Technique** | Step-by-step workflow | Are steps defined? | Are steps followed in order? |
| | Decision trees | Are branches documented? | Are correct branches taken? |
| | Worked examples | Are examples provided? | Are example patterns applied? |
| | Quality criteria | Are criteria stated? | Are criteria met? |
| | Iteration patterns | Is looping defined? | Does iteration happen correctly? |
| **Pattern** | Template structures | Are templates provided? | Are templates used? |
| | Style guides | Is style documented? | Does output match style? |
| | Anti-patterns | Are bad patterns named? | Are anti-patterns avoided? |
| | Variation catalogs | Are variations listed? | Is correct variant selected? |
| | Composition rules | Are combinations defined? | Are patterns composed correctly? |
| **Reference** | Search integration | Are search tools specified? | Is search performed correctly? |
| | Quick-reference tables | Are tables included? | Are tables consulted? |
| | Source links | Are sources linked? | Are sources accessed? |
| | Query guidance | Is query format specified? | Are queries well-formed? |

#### Cross-Reference Procedure

```
FOR EACH expected technique for the skill's type:

1. Structural check: Is this technique present in the skill?
   - Present: Continue to functional check
   - Absent: Flag as "expected technique missing: [technique]"

2. Functional check: Generate scenario to test effectiveness
   - Scenario should test: Does the technique actually work?
   - Not just: Is the technique present?

3. Document for scenario generation:
   - What to test
   - How to recognize success
   - How to recognize failure
```

#### Output Schema

```yaml
expected_behaviors:
  based_on_type: "[skill type]"

  techniques:
    - technique: "[expected technique name]"
      structural_presence: present | absent | partial
      location: "[where in skill, if present]"

      functional_test:
        scenario_seed: "[what scenario would test this]"
        success_indicator: "[how to know it works]"
        failure_indicator: "[how to know it doesn't work]"

  missing_techniques:
    - technique: "[technique not found]"
      impact: "[predicted consequence]"

  diagnostic_signals:
    - "[concerns about skill structure relative to type]"
```

---

### 3.8 Step 7: Adversarial Scenario Generation

**Goal:** Create edge cases and stress tests that probe skill boundaries and failure modes.

#### Universal Adversarial Probes

These apply to all skills regardless of type:

| Probe | What It Tests | Scenario Structure |
|-------|---------------|-------------------|
| **Trigger boundary** | Scope recognition | Task at edge of skill's scope; should it activate? |
| **Trigger negative** | False positive avoidance | Task clearly outside scope; should NOT activate |
| **User override** | Priority handling | User explicitly contradicts skill; how does it respond? |
| **Precondition failure** | Assumption handling | Skill assumes X but X isn't true; what happens? |
| **Competing guidance** | Conflict resolution | Skill conflicts with another instruction; which wins? |
| **Impossible requirement** | Failure handling | Skill requires something that can't be done; how does it fail? |
| **Partial information** | Degradation | Not all required information is available; what happens? |
| **Time pressure** | Robustness | User indicates urgency; does skill still apply? |

#### Type-Specific Adversarial Probes

| Type | Probe | What It Tests |
|------|-------|---------------|
| **Discipline** | "Simple enough to skip" | Shortcut resistance |
| **Discipline** | Partial compliance | Is full process enforced? |
| **Discipline** | Rationalization attempt | Are excuses rejected? |
| **Discipline** | Evidence forgery | Is evidence actually checked? |
| **Technique** | Doesn't fit method | What if task doesn't match assumptions? |
| **Technique** | Method produces bad result | Is output quality checked? |
| **Technique** | Skip to end | Is full process required? |
| **Pattern** | Almost-but-not-quite | What if pattern partially applies? |
| **Pattern** | Wrong pattern selected | Is pattern choice validated? |
| **Pattern** | Pattern conflict | What if two patterns could apply? |
| **Reference** | Information doesn't exist | How does skill handle missing data? |
| **Reference** | Information is stale | Is freshness considered? |
| **Reference** | Query is ambiguous | How is disambiguation handled? |

#### Shortcut Pattern Library (for Discipline Probes)

Common patterns where Claude tends to shortcut:

| Pattern | Description | Probe Scenario |
|---------|-------------|----------------|
| Confirmation bias | Accepting user's approach without verification | User states approach; Claude should still evaluate |
| Speed optimization | Skipping steps when user mentions time pressure | User says "quickly"; full process should still apply |
| Overconfidence | Claiming completion without verification | Task seems done; skill requires explicit verification |
| Assumption cascade | Proceeding with incomplete information | Information is missing; skill should require it |
| Complexity avoidance | Choosing simpler path when harder is correct | Simple option exists but isn't best; skill should guide correctly |
| Success theater | Showing work without doing work | Output looks complete but steps were skipped |

See [Section 7.3](#73-shortcut-pattern-library) for complete pattern reference.

#### Adversarial Scenario Generation Procedure

```
1. Select probes to apply:
   - All universal probes (adapt to skill's context)
   - Type-specific probes for skill's primary type
   - Any probes relevant to specific instructions

2. For each selected probe:
   a. Identify the skill content being tested
   b. Construct trigger that invokes the probe condition
   c. Define expected behavior (how skill SHOULD respond)
   d. Define failure indicators (how to recognize failure)

3. Prioritize probes:
   - P1: Probes testing core purpose (trigger boundary, precondition failure)
   - P2: Probes testing robustness (user override, competing guidance)
   - P2: Probes testing edge cases (partial information, impossible requirement)
```

#### Output Schema

```yaml
adversarial_scenarios:
  - probe_type: "[universal or type-specific probe name]"
    probe_category: universal | discipline | technique | pattern | reference

    scenario:
      name: "[descriptive name]"
      trigger:
        user_message: "[what user says/does]"
        context: "[any setup required]"

      expected_behavior:
        should_do: "[correct response to probe]"
        should_not_do: "[incorrect response to probe]"

      evaluation:
        pass_criterion: "[how to know skill handled it correctly]"
        fail_indicators:
          - "[signal 1 of failure]"
          - "[signal 2 of failure]"

    priority: P1 | P2
    tests_instruction: "[which instruction this probes, if applicable]"
```

---

### 3.9 Step 8: Scenario Assembly and Prioritization

**Goal:** Combine scenarios from all sources into a prioritized suite of 5-7 scenarios.

#### Scenario Sources

| Source | Step | Scenario Type |
|--------|------|---------------|
| Extracted use cases | Step 3 | Happy path |
| Generated use cases | Step 3 | Happy path |
| Instruction behaviors | Step 5 | Specific behavior tests |
| Type-expected behaviors | Step 6 | Type compliance tests |
| Universal probes | Step 7 | Adversarial |
| Type-specific probes | Step 7 | Adversarial |

#### Scenario Schema

All scenarios should be normalized to this schema:

```yaml
scenario:
  id: "[unique identifier, e.g., happy-01, adversarial-03]"
  name: "[descriptive name]"
  priority: P0 | P1 | P2
  source: extracted | generated | instruction | type_expected | adversarial
  skill_type: discipline | technique | pattern | reference

  setup:
    context: "[state that exists before trigger]"
    preconditions:
      - "[condition that must be true]"
    files_needed:
      - "[any files that should exist]"

  trigger:
    user_message: "[exact user input]"
    implicit_context: "[what user assumes but doesn't say]"

  expected_behavior:
    must_do:
      - "[required action 1]"
      - "[required action 2]"
    must_not_do:
      - "[forbidden action 1]"
      - "[forbidden action 2]"
    may_do:
      - "[acceptable optional action]"

  evaluation:
    pass_criteria: "[how to determine pass]"
    fail_indicators:
      - "[signal 1 that indicates failure]"
      - "[signal 2 that indicates failure]"
    evaluator_notes: "[any special evaluation instructions]"

  metadata:
    tests_purpose: "[which aspect of purpose this tests]"
    tests_instructions:
      - "[instruction ID 1]"
      - "[instruction ID 2]"
    coverage_unique:
      - "[what this scenario uniquely covers]"
    related_scenarios:
      - "[IDs of similar scenarios]"
```

#### Prioritization Dimensions

| Dimension | 3 (High) | 2 (Medium) | 1 (Low) |
|-----------|----------|------------|---------|
| **Purpose Centrality** | Directly tests primary purpose | Tests supporting behavior | Tangential to purpose |
| **Failure Impact** | Skill useless if fails | Partial function remains | Minor inconvenience |
| **Usage Likelihood** | Matches primary triggers | Plausible variation | Rare edge case |
| **Coverage Uniqueness** | Only scenario testing this | Partial overlap with others | Redundant coverage |

#### Scoring Operationalization

**Purpose Centrality:**

```
Score 3 (Direct):
  - Scenario explicitly tests the stated/inferred primary purpose
  - If skill only did this one thing, it would still be valuable

Score 2 (Related):
  - Scenario tests behavior that supports the primary purpose
  - Contributes to purpose but isn't the core

Score 1 (Tangential):
  - Scenario tests something skill mentions but isn't central
  - Skill could succeed at purpose without this working
```

**Failure Impact:**

```
Score 3 (Skill useless):
  - If this fails, user cannot accomplish their goal with this skill
  - User would abandon the skill after this failure

Score 2 (Partial function):
  - If this fails, user can work around or achieve partial goal
  - User might still use skill for other purposes

Score 1 (Minor issue):
  - If this fails, user is inconvenienced but goal achievable
  - User would continue using skill despite this failure
```

**Usage Likelihood:**

```
Score 3 (Common):
  - Matches skill's primary trigger phrases exactly
  - Represents the most common use case

Score 2 (Occasional):
  - Plausible variation of primary use case
  - One step removed from primary triggers

Score 1 (Rare):
  - Edge case or unusual circumstance
  - Multiple steps removed from primary triggers
  - Adversarial or constructed scenario
```

**Coverage Uniqueness:**

```
Score 3 (Unique):
  - No other scenario tests this instruction/behavior
  - Provides exclusive coverage

Score 2 (Partial overlap):
  - Other scenarios test related but not identical behaviors
  - Some shared coverage, some unique

Score 1 (Redundant):
  - Another scenario tests essentially the same thing
  - Could be removed without losing coverage
```

#### Priority Assignment Rules

```
Calculate score = sum of dimension scores (range 4-12)

P0 (Critical):
  Score ≥ 10
  OR
  (Purpose Centrality = 3) AND (Failure Impact = 3)

  These scenarios MUST be included.
  Failure on P0 = skill fundamentally broken.

P1 (Important):
  Score 7-9
  OR
  (Any dimension = 3) AND (No dimension = 1)

  These scenarios SHOULD be included.
  Failure on P1 = skill has significant gaps.

P2 (Supplementary):
  Score ≤ 6
  OR
  Usage Likelihood = 1

  Include if capacity allows.
  Failure on P2 = skill has minor issues or edge case gaps.
```

#### Tiebreakers

When scenarios have equal priority scores, prefer (in order):

1. **Clearer success criteria:** Easier to evaluate reliably
2. **Extracted from use cases:** Grounded in design intent
3. **Tests observable behaviors:** Easier to verify pass/fail
4. **Simpler setup:** Fewer confounding variables
5. **Earlier in coverage matrix:** Ensures breadth before depth

#### Selection Algorithm

```
INPUT: All candidate scenarios with scores and priorities
OUTPUT: Final suite of 5-7 scenarios

STEP 1: Collect all P0 scenarios (required)
   If no P0 scenarios: Flag "WARNING: no critical scenarios identified"

STEP 2: Sort remaining candidates
   Primary: By priority (P1 before P2)
   Secondary: By score (higher first)
   Tertiary: By tiebreakers

STEP 3: Build coverage matrix
   Rows: Scenarios
   Columns: Instructions + behaviors being tested
   Cell: 1 if scenario tests this, 0 otherwise

STEP 4: Greedy selection for coverage
   While total scenarios < 7 AND candidates remain:
     a. Calculate marginal coverage for each candidate
        (How many new cells would this scenario cover?)
     b. Select candidate with highest marginal coverage
        (Tiebreak: higher priority, then higher score)
     c. Add to final suite
     d. Update coverage matrix
     e. Stop if marginal coverage = 0 for all candidates

STEP 5: Validate suite
   Check 1: At least 1 P0 scenario?
   Check 2: At least 2 P1 scenarios?
   Check 3: At least 1 happy path scenario?
   Check 4: At least 1 adversarial scenario?
   Check 5: Purpose centrality covered?

   For each failed check:
     Identify lowest-priority scenario in suite
     Swap for scenario that addresses the gap

STEP 6: Document rationale
   For each selected scenario:
     - Why included (priority, coverage, validation need)
     - What it uniquely tests
```

#### Minimum Requirements

| Requirement | Count | Rationale |
|-------------|-------|-----------|
| P0 scenarios | ≥1 | Must test core purpose |
| P1 scenarios | ≥2 | Must test important behaviors |
| Happy path | ≥1 | Must test normal operation |
| Adversarial | ≥1 | Must test edge cases |
| **Total** | 5-7 | Balance coverage and cost |

#### Calibration

After initial selection, review distribution:

| Distribution | Interpretation | Action |
|--------------|----------------|--------|
| >50% scenarios are P0 | Threshold may be too low | Review P0 criteria |
| <10% scenarios are P0 | Threshold may be too high | Review P0 criteria |
| All scenarios are happy path | Adversarial generation may have failed | Add adversarial scenarios |
| All scenarios are adversarial | Use case extraction may have failed | Add happy path scenarios |

Target distribution: ~20% P0, ~50% P1, ~30% P2

#### Output Schema

```yaml
scenario_suite:
  skill: "[skill name]"
  purpose: "[skill purpose]"
  type: "[skill type]"
  generation_timestamp: "[when generated]"

  summary:
    total_scenarios: [count]
    p0_count: [count]
    p1_count: [count]
    p2_count: [count]
    coverage_percentage: [estimated coverage]

  scenarios:
    - [full scenario schema as defined above]
    - [...]

  coverage_matrix:
    instructions_covered:
      - instruction_id: "[id]"
        covered_by: ["scenario_id_1", "scenario_id_2"]
    instructions_not_covered:
      - instruction_id: "[id]"
        reason: "[why no scenario]"

  validation:
    checks_passed:
      - "[check name]"
    checks_failed:
      - check: "[check name]"
        resolution: "[how addressed]"

  generation_notes:
    - "[any caveats or concerns about this suite]"
```

---

## 4. Scenario Execution

### 4.1 Subagent Configuration

Subagents are used to run scenarios in isolated contexts. Two configurations are needed:

#### Baseline Configuration

```yaml
baseline_subagent:
  purpose: Measure behavior WITHOUT the target skill

  system_prompt:
    base: "[standard Claude behavior]"
    additions:
      - "[scenario context]"
      - "[task instructions]"
    exclusions:
      - "[target skill content - explicitly absent]"

  tools:
    - "[tools required by scenario]"

  permissions:
    - "[permissions required by scenario]"

  context:
    - "[any files or information needed]"
```

#### Test Configuration

```yaml
test_subagent:
  purpose: Measure behavior WITH the target skill

  system_prompt:
    base: "[standard Claude behavior]"
    additions:
      - "[scenario context]"
      - "[task instructions]"
      - "[TARGET SKILL CONTENT - explicitly included]"

  tools:
    - "[same tools as baseline]"

  permissions:
    - "[same permissions as baseline]"

  context:
    - "[same context as baseline]"
```

#### Controlled Conditions

| Factor | Requirement |
|--------|-------------|
| Tools | Identical between baseline and test |
| Permissions | Identical between baseline and test |
| Context | Identical between baseline and test |
| Task | Identical phrasing |
| Skill presence | ONLY difference between conditions |

### 4.2 Baseline Measurement

```
PROCEDURE: Run baseline measurement

1. Configure baseline subagent (no target skill)

2. Present scenario trigger:
   - User message from scenario
   - Any required context/files

3. Allow subagent to execute task

4. Record observations:
   - Final output produced
   - Tool calls made (sequence and parameters)
   - Reasoning visible in response
   - Time/tokens consumed
   - Errors encountered
   - Completion status

5. Assess against expected behavior:
   - Which "must_do" items were done?
   - Which "must_not_do" items were avoided?
   - What approach was taken?
   - Where did subagent struggle?
   - What shortcuts were taken?
```

### 4.3 Skill-Assisted Measurement

```
PROCEDURE: Run skill-assisted measurement

1. Configure test subagent (with target skill)

2. Present IDENTICAL scenario trigger

3. Allow subagent to execute task

4. Record IDENTICAL observations

5. Note skill-specific markers:
   - Did subagent acknowledge skill?
   - Did subagent follow skill's process?
   - Did subagent use skill's terminology?
   - Where did subagent deviate from skill?
```

### 4.4 Delta Evaluation

Compare baseline and test results:

| Comparison Dimension | Question |
|---------------------|----------|
| **Behavior change** | Did the subagent do something different? |
| **Direction** | Was the change toward the intended behavior? |
| **Completeness** | Were all skill instructions followed? |
| **Process** | Did the subagent follow the skill's methodology? |
| **Output quality** | Is the result better, worse, or same? |
| **Efficiency** | Did skill help or hurt efficiency? |

#### Delta Categories

| Category | Meaning | Implication |
|----------|---------|-------------|
| **Positive delta** | Skill-assisted better than baseline | Skill is helping |
| **Neutral delta** | No meaningful difference | Skill may not be providing value |
| **Negative delta** | Skill-assisted worse than baseline | Skill may be hurting |
| **Inconsistent delta** | Sometimes better, sometimes worse | Skill may be inconsistent |

#### Evaluation Output

```yaml
delta_evaluation:
  scenario_id: "[scenario]"

  baseline_result:
    completion_status: complete | partial | failed
    must_do_achieved: [list of achieved items]
    must_do_missed: [list of missed items]
    must_not_do_violations: [list of violations]
    approach_summary: "[how baseline approached task]"

  test_result:
    completion_status: complete | partial | failed
    must_do_achieved: [list of achieved items]
    must_do_missed: [list of missed items]
    must_not_do_violations: [list of violations]
    approach_summary: "[how test approached task]"
    skill_compliance:
      instructions_followed: [list]
      instructions_ignored: [list]
      instructions_misinterpreted: [list]

  delta:
    category: positive | neutral | negative | inconsistent
    behavior_changes:
      - behavior: "[what changed]"
        direction: improved | worsened | neutral
        evidence: "[how we know]"
    overall_assessment: "[summary of skill impact]"
```

---

## 5. Gap Analysis and Improvement

### 5.1 Gap Identification

After delta evaluation, identify where the skill failed to produce intended effects.

| Gap Type | Definition | Example |
|----------|------------|---------|
| **No effect** | Skill present but behavior unchanged | Subagent ignored skill entirely |
| **Wrong effect** | Behavior changed but not in intended direction | Skill made output worse |
| **Partial effect** | Some intended changes, others missing | Followed some instructions, not others |
| **Negative effect** | Skill made behavior worse | Skill confused or misdirected |
| **Inconsistent effect** | Works sometimes but not always | Same scenario, different outcomes |

### 5.2 Root Cause Classification

Map observed failures to root causes:

| Root Cause | Description | Fix Direction |
|------------|-------------|---------------|
| **Instruction ignored** | Subagent didn't follow instruction | Make more salient, add enforcement |
| **Instruction misinterpreted** | Subagent followed but understood wrong | Clarify wording, add examples |
| **Instruction unclear** | Instruction is genuinely ambiguous | Restructure, remove ambiguity |
| **Assumption failed** | Skill assumes something that isn't true | Remove assumption, add check |
| **Conflict** | Skill conflicts with other guidance | Resolve priority, add exception |
| **Scope mismatch** | Skill applied when it shouldn't | Adjust trigger conditions |
| **Overreach** | Skill tried to do too much | Narrow scope, simplify |

#### Root Cause Analysis Procedure

```
FOR EACH identified gap:

1. Identify the specific instruction/behavior that failed

2. Examine the test subagent's response:
   - Did it mention the instruction?
   - Did it attempt to follow it?
   - What did it actually do instead?
   - What reasoning did it give?

3. Classify the root cause:
   - No mention + no attempt → Instruction ignored
   - Mentioned + wrong action → Instruction misinterpreted
   - Attempted + failed → Instruction unclear or assumption failed
   - Conflicting actions → Conflict with other guidance
   - Applied when shouldn't → Scope mismatch

4. Assess confidence:
   - Single occurrence: Low confidence
   - Multiple occurrences: Higher confidence
   - Consistent pattern: High confidence

5. Document:
   - Gap description
   - Root cause category
   - Evidence
   - Confidence level
```

### 5.3 Fix Generation

Generate fixes based on root cause:

| Root Cause | Fix Strategies |
|------------|----------------|
| **Instruction ignored** | Move earlier in skill; Add blocking language; Add explicit gate |
| **Instruction misinterpreted** | Add examples; Rephrase more clearly; Add disambiguation |
| **Instruction unclear** | Decompose into steps; Remove ambiguous terms; Add decision tree |
| **Assumption failed** | Remove assumption; Add precondition check; Handle failure case |
| **Conflict** | State priority explicitly; Add exception rules; Separate concerns |
| **Scope mismatch** | Refine triggers; Add negative triggers; Clarify boundaries |
| **Overreach** | Remove extraneous content; Focus on core purpose; Split into sub-skills |

#### Fix Quality Criteria

| Criterion | Question |
|-----------|----------|
| **Root cause** | Does fix address root cause, not just symptom? |
| **Regression** | Could fix break something that was working? |
| **Generalization** | Will fix help with similar cases, not just this one? |
| **Simplicity** | Is fix the simplest that addresses the problem? |
| **Testability** | Can we verify the fix works? |

### 5.4 Iteration Protocol

```
ITERATION LOOP:

1. Apply proposed fixes to skill

2. Re-run scenarios:
   - Same scenario types (not identical instances)
   - Prevents overfitting to specific wording
   - Keeps scenario structure consistent

3. Evaluate:
   - Did gaps close?
   - Any regressions? (Previously passing now failing)
   - Any new gaps introduced?

4. Decision:
   - All P0 scenarios pass + no regressions → Success
   - P0 scenarios still failing → Continue iteration
   - Regressions introduced → Revert or refine fix
   - No progress after 3 iterations → Escalate for review

5. Iteration limits:
   - Default: 3 iterations
   - High-stakes skill: 5 iterations
   - After limit: Report remaining gaps, recommend manual review
```

#### Threshold Definition

| Threshold | Criteria |
|-----------|----------|
| **Minimum acceptable** | All P0 scenarios pass |
| **Good** | All P0 + majority of P1 pass |
| **Excellent** | All P0 + all P1 + majority of P2 pass |

---

## 6. Supporting Components

### 6.1 Scenario Schema

Complete schema for scenario definition:

```yaml
scenario:
  # Identification
  id: string  # Unique identifier (e.g., "happy-01", "adversarial-03")
  name: string  # Human-readable name
  version: string  # Schema version (e.g., "1.0")

  # Classification
  priority: P0 | P1 | P2
  source: extracted | generated | instruction | type_expected | adversarial
  skill_type: discipline | technique | pattern | reference
  probe_type: string | null  # For adversarial scenarios

  # Setup
  setup:
    context: string  # Description of state before trigger
    preconditions:
      - string  # Conditions that must be true
    files:
      - path: string
        content: string | null  # null = file must exist but content unspecified
    environment:
      - variable: string
        value: string

  # Trigger
  trigger:
    user_message: string  # Exact user input
    implicit_context: string | null  # What user assumes but doesn't say
    conversation_history:  # If scenario requires prior turns
      - role: user | assistant
        content: string

  # Expected Behavior
  expected_behavior:
    must_do:
      - action: string
        evidence: string  # How to verify this was done
    must_not_do:
      - action: string
        evidence: string  # How to verify this wasn't done
    may_do:
      - action: string
        note: string  # Why this is acceptable
    process_requirements:
      - step: string
        order: number | null  # If ordering matters

  # Evaluation
  evaluation:
    pass_criteria: string  # Overall criterion for passing
    fail_indicators:
      - indicator: string
        severity: critical | major | minor
    partial_pass_possible: boolean
    partial_pass_criteria: string | null
    evaluator_guidance: string | null  # Special instructions for evaluator

  # Metadata
  metadata:
    tests_purpose: string  # Which aspect of purpose this tests
    tests_instructions:
      - instruction_id: string
    coverage_unique:
      - string  # What this scenario uniquely covers
    related_scenarios:
      - scenario_id: string
    rationale: string  # Why this scenario was included

  # Scoring (populated during assembly)
  scoring:
    purpose_centrality: 1 | 2 | 3
    failure_impact: 1 | 2 | 3
    usage_likelihood: 1 | 2 | 3
    coverage_uniqueness: 1 | 2 | 3
    total_score: number  # 4-12
```

### 6.2 Success Criteria Derivation

Success criteria are derived from the scenario's source:

| Source | Derivation Method |
|--------|-------------------|
| **Extracted use case** | Use case's stated "Result" becomes pass criteria |
| **Generated from purpose** | Purpose achievement, operationalized via Step 5 |
| **Instruction mapping** | Instruction followed = pass; violated = fail |
| **Type-expected behavior** | Technique present AND effective = pass |
| **Adversarial probe** | Appropriate handling as defined by probe type |

#### Probe-Specific Success Criteria

| Probe | Success Criteria |
|-------|------------------|
| Trigger boundary | Skill activates if appropriate, doesn't if not |
| Trigger negative | Skill does NOT activate |
| User override | Skill acknowledges conflict, handles appropriately |
| Precondition failure | Skill detects failure, provides guidance |
| Competing guidance | Skill states priority, follows hierarchy |
| Impossible requirement | Skill recognizes impossibility, doesn't fail silently |

### 6.3 Overfitting Prevention

Strategies to ensure skill improvements generalize:

| Strategy | Implementation |
|----------|----------------|
| **Holdout scenarios** | Reserve 1-2 scenarios for final validation only; never use in development iterations |
| **Scenario rotation** | Keep scenario types consistent but change specific wording/details between iterations |
| **Adversarial design** | Include scenarios designed to break the skill |
| **Ground in real usage** | Base scenarios on actual past failures or observed usage patterns |
| **Root cause fixing** | Ask "why did this fail?" not "how do I pass this test?" |

#### Generalization Signals

| Signal | Interpretation |
|--------|----------------|
| "Passes because we added instruction for this case" | Likely overfit |
| "Passes because we clarified ambiguous section" | Likely generalizes |
| "Passes holdout scenarios without seeing them" | Strong generalization |
| "Passes scenario rotation without changes" | Strong generalization |

#### Development vs. Holdout Sets

```
Scenario allocation:
- Development set: 4-5 scenarios (used during iteration)
- Holdout set: 1-2 scenarios (only used for final validation)

Holdout selection criteria:
- Representative of core purpose
- Not identical to development scenarios
- Tests similar behaviors via different triggers

If skill performs well on development but fails holdout:
- Strong signal of overfitting
- Review fixes for symptom-patching
- Consider more fundamental changes
```

### 6.4 Hard-to-Test Skills

Different categories of testing difficulty with mitigations:

| Category | Why Hard | Mitigations |
|----------|----------|-------------|
| **Long-term effects** | Subagents isolated; can't observe multi-session | Test building blocks; simulate multi-phase; accept partial coverage |
| **Qualitative effects** | Success is subjective; observers disagree | Define observable markers; use comparative judgment; explicit criteria |
| **Context-dependent** | Only matters in specific contexts | Mine real examples; construct triggers; verify recognition |
| **Emergent/interaction** | Combinatorial explosion | Test common combinations; isolation testing; accept some discovery in production |
| **Rare triggers** | Can't easily cause trigger condition | Mock the condition; use historical examples; verify no breakage when condition absent |
| **Negative effects** | Testing absence requires knowing baseline | Explicit baseline comparison; construct scenarios to elicit behavior |
| **Meta-cognitive** | Internal reasoning not visible | Examine reasoning traces; test downstream effects; look for process markers |
| **High-variance** | No single right answer | Test process not outcome; element presence; relative evaluation |

#### Higher-Level Strategies

| Strategy | Description |
|----------|-------------|
| **Decompose** | Test mechanism even when ultimate outcome can't be tested |
| **Proxy metrics** | Find measurable proxies for hard-to-measure effects |
| **Comparative** | If absolute success undefined, test relative improvement |
| **Design for testability** | Ask "how would we test this?" during skill creation |

#### The Hard Question

> If a skill's core purpose is untestable, how do we know it provides value?

"Untestable" often reveals something about the skill:

- Haven't defined observable markers for the effect
- Haven't constructed the right triggering context
- The effect is vague or illusory

Resist accepting "untestable" too quickly.

### 6.5 Cost Calibration

Simulation-based assessment is expensive. Calibrate investment to stakes:

| Situation | Approach |
|-----------|----------|
| Minor refinement to well-tested skill | Fewer scenarios, fewer iterations |
| Major changes to important skill | Full scenario suite, multiple iterations |
| New skill with uncertain design | More exploratory scenarios |
| Skill with known failure history | Scenarios targeting past failures |

#### Cost Components

| Component | Cost Driver |
|-----------|-------------|
| Scenario generation | Framework execution (once per assessment) |
| Baseline runs | One subagent per scenario |
| Test runs | One subagent per scenario |
| Evaluation | Analysis of each run |
| Iterations | Multiplies all above costs |

#### Cost Estimation

```
For single improvement cycle:

  Scenario generation: ~1 framework run
  Per iteration:
    - Baseline runs: 5 scenarios × 1 subagent = 5 runs
    - Test runs: 5 scenarios × 1 subagent = 5 runs
    - Evaluation: 5 analyses

  Total for 3 iterations:
    - 1 generation + (3 × 10 runs) + (3 × 5 evaluations)
    - ~31 subagent/analysis operations
```

The discussion document argues this is worthwhile: "expensive-but-works beats cheap-but-broken."

---

## 7. Reference Tables

### 7.1 Skill Type Indicators

Complete indicator lists for classification:

#### Discipline Skill Indicators

| Indicator | Description | Score Weight |
|-----------|-------------|--------------|
| Phase gates | Explicit stages with transition requirements | 3 |
| Blocking language | "MUST", "NEVER", "before ANY" | 2 |
| Evidence requirements | Must show output/proof before proceeding | 3 |
| Anti-pattern tables | Named shortcuts with rebuttals | 2 |
| Red flag lists | Rationalization patterns to catch | 2 |
| Verification checklists | Items requiring explicit confirmation | 2 |
| Failure mode descriptions | Consequences of skipping steps | 1 |

#### Technique Skill Indicators

| Indicator | Description | Score Weight |
|-----------|-------------|--------------|
| Step-by-step workflow | Ordered sequence of actions | 3 |
| Decision trees | Branching based on conditions | 2 |
| Templates | Fillable structures for execution | 2 |
| Worked examples | Real scenarios with walkthrough | 3 |
| Heuristics | Rules for sub-technique selection | 2 |
| Quality criteria | Standards for output per stage | 2 |
| Iteration patterns | When/how to loop back | 1 |

#### Pattern Skill Indicators

| Indicator | Description | Score Weight |
|-----------|-------------|--------------|
| Template structures | File layouts, component hierarchies | 3 |
| Style guides | Formatting rules with examples | 2 |
| Element checklists | Required components list | 2 |
| Anti-patterns | What not to do and why | 2 |
| Variation catalogs | Pattern variants by context | 2 |
| Decision tables | Situation → variant mapping | 2 |
| Composition rules | How patterns combine | 1 |

#### Reference Skill Indicators

| Indicator | Description | Score Weight |
|-----------|-------------|--------------|
| Search integration | MCP or tool connections | 3 |
| Query guidance | How to search effectively | 2 |
| Quick-reference tables | Lookup information | 3 |
| Source links | External documentation | 2 |
| Freshness indicators | When info might be stale | 1 |
| Cross-references | Related concept maps | 1 |
| Disambiguation | Handling ambiguous queries | 2 |

### 7.2 Subjective Term Proxies

Complete proxy mappings for operationalization:

| Term | Observable Proxies |
|------|-------------------|
| quality | No errors, meets requirements, passes tests, follows conventions, no warnings |
| thorough | All cases covered, all paths checked, edge cases addressed, nothing skipped |
| clear | Short sentences, terms defined, examples included, logical structure, no ambiguity |
| proper | Follows documented conventions, no warnings, consistent style, validated |
| correct | Matches specification, produces expected output, handles all cases |
| secure | No vulnerabilities, input validated, secrets protected, permissions correct |
| efficient | Meets performance threshold, no redundancy, minimal resource use, optimized |
| readable | Descriptive names, logical structure, appropriate comments, consistent formatting |
| robust | Handles errors gracefully, validates input, recovers from failures, defensive |
| complete | All requirements met, all cases handled, nothing missing, fully documented |
| appropriate | Fits context, matches conventions, proportional response, not over/under |
| valid | Passes validation, meets schema, conforms to format, no constraint violations |
| consistent | Same approach throughout, matches existing patterns, no contradictions |
| maintainable | Modular, documented, tested, follows standards, easy to modify |
| testable | Has clear inputs/outputs, deterministic, isolated, observable |

### 7.3 Shortcut Pattern Library

Common shortcuts Claude takes that discipline skills should prevent:

| Pattern | Description | Trigger Conditions | Detection |
|---------|-------------|-------------------|-----------|
| **Confirmation bias** | Accepting user's approach without verification | User states an approach confidently | No alternative exploration |
| **Speed optimization** | Skipping steps when time pressure mentioned | User says "quickly", "urgent", "fast" | Steps skipped without acknowledgment |
| **Overconfidence** | Claiming completion without verification | Task seems simple or familiar | No verification output shown |
| **Assumption cascade** | Proceeding with incomplete information | Some info available, some missing | No questions asked |
| **Complexity avoidance** | Choosing simpler path when harder is correct | Multiple valid approaches exist | Simpler chosen without justification |
| **Success theater** | Showing work without doing work | Output structure exists | Content is superficial |
| **Scope creep acceptance** | Taking on more than asked | User implies additional needs | Scope expanded without confirmation |
| **Premature completion** | Stopping before truly done | Partial result achieved | "Done" claimed with gaps |
| **Tool avoidance** | Not using available tools | Tools require effort to invoke | Manual approach when tools exist |
| **Verification skip** | Not checking own output | Output produced | No review or testing |

### 7.4 Adversarial Probe Library

Complete probe definitions:

#### Universal Probes

| Probe | Trigger | Expected Response | Failure Signal |
|-------|---------|-------------------|----------------|
| **Trigger boundary** | Task at edge of skill scope | Activate if appropriate, don't if not | Wrong activation decision |
| **Trigger negative** | Task clearly outside scope | Do NOT activate | Activates anyway |
| **User override** | User says "ignore [skill] and just..." | Acknowledge conflict, explain, negotiate | Silently comply or silently refuse |
| **Precondition failure** | Required precondition is false | Detect and report, provide guidance | Proceed anyway or fail silently |
| **Competing guidance** | Conflicting instruction exists | State priority, follow hierarchy | Arbitrary choice or confusion |
| **Impossible requirement** | Skill requires impossible action | Recognize, report, suggest alternative | Attempt anyway or fail silently |
| **Partial information** | Some required info missing | Ask for missing info or state assumptions | Proceed with guesses |
| **Time pressure** | User indicates urgency | Skill still applies (perhaps note tension) | Skip skill due to pressure |

#### Discipline-Specific Probes

| Probe | Trigger | Expected Response | Failure Signal |
|-------|---------|-------------------|----------------|
| **Shortcut temptation** | Task seems simple | Full process anyway | Process shortened |
| **Partial compliance** | Subagent does some steps | Require all steps | Incomplete accepted |
| **Rationalization** | Excuse to skip provided | Reject excuse | Accept rationalization |
| **Evidence forgery** | Claim without evidence | Require actual evidence | Accept claim |
| **Gate bypass** | Attempt to skip gate | Enforce gate | Allow bypass |

#### Technique-Specific Probes

| Probe | Trigger | Expected Response | Failure Signal |
|-------|---------|-------------------|----------------|
| **Method mismatch** | Task doesn't fit method | Adapt or acknowledge limitation | Force method anyway |
| **Quality failure** | Method produces bad result | Iterate or flag | Accept bad output |
| **Step skip** | Attempt to skip step | Require step | Allow skip |
| **Branch error** | Wrong decision tree branch | Correct branch | Stay on wrong branch |

#### Pattern-Specific Probes

| Probe | Trigger | Expected Response | Failure Signal |
|-------|---------|-------------------|----------------|
| **Partial match** | Pattern almost applies | Acknowledge limitation, adapt | Force pattern |
| **Wrong pattern** | Multiple patterns could apply | Choose correctly, justify | Wrong choice |
| **Pattern conflict** | Two patterns conflict | Resolve explicitly | Arbitrary merge |

#### Reference-Specific Probes

| Probe | Trigger | Expected Response | Failure Signal |
|-------|---------|-------------------|----------------|
| **Missing info** | Requested info doesn't exist | Report not found | Fabricate |
| **Stale info** | Information may be outdated | Note staleness | Present as current |
| **Ambiguous query** | Query matches multiple things | Disambiguate | Arbitrary choice |

---

## 8. Key Insights

Principles that emerged from developing this framework:

### 8.1 Form vs. Function

> Structural compliance ≠ functional effectiveness.

A skill can follow all guidelines and still fail at its purpose. This is the core problem the framework addresses.

### 8.2 The Measurement Problem

Structural compliance is checkable (binary, verifiable). Functional effectiveness requires empirical observation. Systems default to measuring what can be checked, even when it's not what matters.

### 8.3 The Discipline Skill Paradox

If assessment is a checklist, Claude can complete the checklist without substantive analysis. The assessment mechanism must be resistant to the same shortcuts the skill is trying to prevent.

### 8.4 Aspirational vs. Operational

Many skills ask the right questions but provide no method for answering them. Asking "is this effective?" without defining how to measure effectiveness is aspirational, not operational.

### 8.5 Purpose-First + Simulation-Based

Purpose defines what should happen (success criteria). Simulation measures what actually happens (empirical observation). The gap between them is the work.

### 8.6 Quality Over Quantity

5 well-chosen scenarios that cover the behavior landscape matter more than 20 poorly-chosen ones. Scenario quality is about coverage of failure modes, not volume.

### 8.7 Variance is Signal

If most scenarios pass but one fails, investigate the outlier. It reveals where the skill behaves differently, which is often the most valuable information.

### 8.8 Generalization via Root Cause

Fixes that address root causes generalize. Fixes that address symptoms overfit. Ask "why did this fail?" not "how do I pass this test?"

### 8.9 Hard-to-Test ≠ Untestable

"Untestable" often means: haven't defined observable markers, haven't constructed the right context, or the effect is vaguely defined. If a skill's core purpose is truly untestable, question whether it provides value.

### 8.10 Irreducible Judgment

Some judgment is irreducible — proxy selection, goal inference, priority assessment. The goal is not to eliminate judgment but to make it explicit, structured, and traceable.

### 8.11 The Meta-Problem

Testing improving-skills requires testing target skills. Testing target skills requires this framework. The framework tests whether skills achieve their purposes — but if purposes are unclear, it tests structural compliance at a higher level. The oracle problem is pushed up, not solved.

### 8.12 Structured Judgment vs. No Judgment

The framework doesn't eliminate judgment; it structures it. Judgment points are explicit, criteria are defined, decisions are traceable. This is "judgment-structured," not "judgment-free."

---

## Document Information

| Field | Value |
|-------|-------|
| Version | 0.1.0 |
| Status | Draft |
| Created | 2026-02-04 |
| Based on | Discussion: Improving-Skills Failure Modes and Simulation-Based Assessment |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-02-04 | Initial comprehensive framework |

### Open Items

| Priority | Item | Status |
|----------|------|--------|
| High | Skill architecture design | Not started |
| High | Subagent orchestration design | Not started |
| High | "Good enough" threshold definition | Partial |
| Medium | Step failure protocols | Not started |
| Medium | Step dependency graph | Implicit only |
| Medium | Worked example | Not started |
| Low | Interaction scenario extension | Not started |
| Low | Edge case handling (meta-skills, etc.) | Not started |

# skillosophy Design Document

> Collaborative skill creation with deep methodology and multi-agent synthesis.

**Date:** 2026-01-14
**Status:** Work in Progress
**Replaces:** skill-wizard, skillforge

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Four-Phase Architecture](#2-four-phase-architecture)
3. [Synthesis Panel Composition](#3-synthesis-panel-composition)
4. [Loop-Back Strategy](#4-loop-back-strategy)
5. [11-Section Structure and Validation](#5-11-section-structure-and-validation)
6. [Session Recovery and Handoff Integration](#6-session-recovery-and-handoff-integration)
7. [Plugin Structure](#7-plugin-structure)
8. [Methodology Integration](#8-methodology-integration)
9. [Migration Path](#9-migration-path)
10. [Open Questions and Future Work](#10-open-questions-and-future-work)
11. [Design Summary](#11-design-summary)

---

## 1. Executive Summary

**skillosophy** is a Claude Code plugin for creating high-quality skills through collaborative dialogue and rigorous methodology.

### The Problem

Existing skill creation tools force a choice:
- **skill-wizard**: Interactive dialogue helps clarify intent, but lacks deep analysis and quality gates
- **skillforge**: Deep methodology with multi-agent synthesis, but user only reviews at the end

Neither combines collaborative refinement with rigorous quality assurance.

### The Solution

skillosophy merges both approaches:

1. **Collaborative Phases 1-3**: User and Claude explore requirements together, make decisions iteratively, and validate each section before moving on
2. **Deep methodology running in parallel**: 11 thinking models and regression questioning enrich the dialogue without overwhelming it
3. **Autonomous Phase 4**: 4-agent synthesis panel provides independent quality gate with unanimous approval required

### Core Promise

Transform a skill idea into a production-ready, spec-compliant SKILL.md through natural dialogue — with the rigor of multi-agent review built in.

### Key Differentiators

| Aspect | skill-wizard | skillforge | skillosophy |
|--------|--------------|------------|-------------|
| User involvement | Every section | End review only | Throughout + panel |
| Analysis depth | Surface | 11 lenses | 11 lenses |
| Quality gate | Checklists | 3-4 agents | 4 specialized agents |
| Artifact | SKILL.md | XML spec → SKILL.md | SKILL.md with decisions |

---

## 2. Four-Phase Architecture

skillosophy follows a 4-phase workflow. Phases 1-3 are collaborative; Phase 4 is autonomous.

### Phase 0: Triage

**Purpose:** Determine if we should create, modify, or recommend an existing skill.

**Process:**
1. Parse user's goal to understand intent
2. Scan ecosystem via `discover_skills.py` for existing skills
3. Match against existing skills with confidence scoring
4. Route to appropriate action

**Routing Matrix:**

| Match Score | Intent | Action |
|-------------|--------|--------|
| ≥80% | Any | USE_EXISTING or CLARIFY |
| 50-79% | Improve | MODIFY existing skill |
| 50-79% | Create | CLARIFY (similar exists) |
| <50% | Create | CREATE_NEW → Phase 1 |

**Output:** Routing decision + existing skill context (if MODIFY)

### Script Interfaces

Phase 0 relies on two scripts from the original skillforge:

**`scripts/discover_skills.py`** — Builds the skill ecosystem index

| Aspect | Detail |
|--------|--------|
| **Purpose** | Scan all skill sources and build a searchable JSON index |
| **Input** | None (scans predefined SKILL_SOURCES) |
| **Output** | JSON index at `~/.cache/skillrecommender/skill_index.json` |
| **When to run** | On plugin install, skill creation, or manual refresh |
| **CLI** | `python discover_skills.py [--verbose] [--json] [--output PATH]` |

Output schema:
```json
{
  "version": "2.0.0",
  "generated_at": "<ISO timestamp>",
  "skills": [
    {
      "name": "<skill-name>",
      "source": "<source-name>",
      "path": "<absolute-path>",
      "priority": 1-5,
      "description": "<first 200 chars>",
      "triggers": ["<phrase>", ...],
      "keywords": ["<word>", ...],
      "domains": ["<domain>", ...],
      "version": "<semver>"
    }
  ],
  "domains": {"<domain>": ["<skill-name>", ...]},
  "sources": {"<source-name>": "<path>"},
  "total_count": "<number>"
}
```

**`scripts/triage_skill_request.py`** — Routes user input to appropriate action

| Aspect | Detail |
|--------|--------|
| **Purpose** | Analyze user input and determine skill routing |
| **Input** | User goal string (positional argument) |
| **Output** | JSON with action recommendation and match details |
| **When to run** | At start of Phase 0 for every skillosophy invocation |
| **CLI** | `python triage_skill_request.py "<query>" [--json] [--verbose]` |

Output schema:
```json
{
  "success": true,
  "message": "Triage complete: <ACTION>",
  "data": {
    "action": "USE_EXISTING | IMPROVE_EXISTING | CREATE_NEW | COMPOSE | CLARIFY",
    "details": {
      "category": "<input-category>",
      "top_match": {"name": "...", "score": 85, ...},
      "reason": "<human-readable explanation>",
      "suggested_action": "<optional guidance>"
    },
    "top_matches": [
      {"name": "<skill>", "score": 0-100, "reasons": [...], "domains": [...]}
    ]
  }
}
```

**Actions mapped to Phase 0 routing:**

| Script Action | Phase 0 Outcome |
|---------------|-----------------|
| `USE_EXISTING` (score ≥80%) | Recommend existing skill; ask to proceed or create anyway |
| `IMPROVE_EXISTING` (score 50-79%) | Offer to modify existing skill |
| `CREATE_NEW` (score <50%) | Proceed to Phase 1 with no existing context |
| `COMPOSE` | Suggest skill chain; ask if composition or new skill needed |
| `CLARIFY` | Ask user clarifying question before routing |

**Dependency:** `triage_skill_request.py` requires `discover_skills.py` to have run at least once (index must exist).

**Asset status:** Both scripts exist in `skillforge/scripts/` and will be copied to `skillosophy/scripts/` during migration. No new implementation required.

### Script Error Handling

Phase 0 scripts may fail for various reasons. skillosophy degrades gracefully:

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Python not available | Bash returns "command not found" or similar | Skip triage; proceed directly to CREATE with warning: "Skill ecosystem scan unavailable. Creating new skill." |
| Script file missing | Bash returns non-zero exit | Same as above |
| Index doesn't exist | `triage_skill_request.py` returns error JSON | Run `discover_skills.py` first, then retry triage |
| Malformed JSON output | JSON parse fails | Log raw output; ask user: "Triage returned unexpected output. Create new skill, or specify existing skill path to modify?" |
| Script timeout (>30s) | Bash timeout | Skip triage with warning; proceed to CREATE |

**Graceful degradation principle:** Triage is an optimization, not a gate. If triage fails, skillosophy can always fall back to CREATE mode — the user just won't get duplicate detection or modification suggestions.

**User notification:** When falling back, always explain what happened and what's being skipped:
```
⚠️ Skill ecosystem scan failed: [reason]
   Proceeding without duplicate detection.
   If you meant to modify an existing skill, specify its path explicitly.
```

### Phase 1: Deep Analysis (Collaborative)

**Purpose:** Build shared understanding of what to create through dialogue enriched by methodology.

**Key activities:**
- Requirements discovery (explicit, implicit, discovered)
- Category selection (from 21 categories)
- Risk tier determination
- Approach exploration (2-3 alternatives with trade-offs)
- Tool selection and constraints

**Output:** Shared understanding captured in growing SKILL.md with `metadata.decisions`

### Phase 2: Specification Checkpoint (Collaborative)

**Purpose:** Validate consolidated understanding before generation.

**Process:**
1. Claude presents summary: "Based on our discussion, here's what we're building..."
2. Requirements (explicit, implicit, discovered)
3. Chosen approach with rationale
4. Key decisions and trade-offs
5. Risk tier with justification
6. User validates or corrects

**Output:** Validated decisions in `metadata.decisions`, ready for generation

### Phase 3: Generation (Collaborative)

**Purpose:** Draft and validate each of 11 sections with inline checklist validation.

**For each section:**
1. **Draft** — Generate content informed by Phase 1-2 decisions
2. **Validate** — Check against section checklist ([MUST], [SHOULD], [SEMANTIC])
3. **Review** — User sees draft + validation results
4. **Iterate** — User approves, edits, or regenerates
5. **Commit** — Approved section written to SKILL.md

**After all sections:**
- Cross-section validation (reference integrity, coherence)
- Session State section updated
- Ready for panel review

**Section ordering constraint:** Body sections are generated in fixed order:

1. Triggers → 2. When to use → 3. When NOT to use → 4. Inputs → 5. Outputs → 6. Procedure → 7. Decision Points → 8. Verification → 9. Troubleshooting → 10. Anti-Patterns → 11. Extension Points

Session State is appended *after* all 11 body sections, never interleaved. This ordering is not a suggestion — it's required for safe Session State removal. The removal logic (Section 5) truncates from `## Session State` forward, which only works if no content follows it.

**Enforcement:** When writing a section, skillosophy appends to SKILL.md in order. If Session State already exists (from a previous partial run), it is read, removed, the new section is appended, then Session State is re-appended at the end.

**Output:** Complete SKILL.md with all 11 sections validated

### Phase 4: Synthesis Panel (Autonomous)

**Purpose:** Independent quality gate with fresh perspectives.

**Process:**
1. Launch 4 agents in parallel via Task tool
2. Each agent reviews full skill from their lens
3. All agents must return APPROVED (unanimous)
4. If any CHANGES_REQUIRED → severity-based loop-back

**Output:** APPROVED skill or feedback for revision

### Why 4 Phases?

This structure emerged from analyzing failure modes in simpler alternatives:

| Alternative | Why It Fails |
|-------------|--------------|
| **2-phase** (Dialogue → Panel) | No checkpoint before generation. Misunderstood requirements surface only after drafting 11 sections — costly rework. |
| **3-phase** (Remove Phase 2) | Phase 2 is the "confirm before commit" gate. Without it, misalignment between user intent and Claude's understanding appears mid-generation when sections fail validation. |
| **3-phase** (Merge Phases 1-2) | Analysis and validation serve different purposes. Phase 1 explores ("what could this be?"); Phase 2 confirms ("is this what you meant?"). Merging loses the explicit handoff. |
| **Triage as hook** (not a phase) | Triage outcomes require user interaction ("Use existing skill?"). Silent pre-processing would hide routing decisions that affect the user's choice. |

**The 4-phase structure maps to distinct concerns:**

- **Phase 0**: Route (before creation starts, different inputs)
- **Phase 1**: Explore (divergent thinking, options)
- **Phase 2**: Commit (convergent, lock decisions)
- **Phase 3**: Build (execute on locked decisions)
- **Phase 4**: Verify (independent audit, fresh eyes)

Each phase has a single responsibility. Merging any two would conflate responsibilities and create implicit handoffs where explicit ones belong.

---

## 3. Synthesis Panel Composition

The Phase 4 panel consists of 4 specialized agents. Each brings a distinct lens that catches what the collaborative process might miss.

### Agent 1: Executability Auditor

**Focus:** Can Claude follow this unambiguously to completion?

**What it checks:**
- Mentally executes Procedure step by step
- Flags steps that are vague, underspecified, or impossible
- Identifies ambiguous terminology that could cause misinterpretation
- Verifies decision points are actually decidable with available information
- Confirms verification checks are runnable
- Surfaces implicit assumptions that would block execution

**Key question:** "If Claude read this skill cold, could it execute correctly without guessing?"

**Output structure:**
```markdown
### Executability Audit

| Step/Element | Issue | Severity | Suggested Fix |
|--------------|-------|----------|---------------|
| Procedure Step 5 | "Handle appropriately" is ambiguous | High | Specify: retry 3x, then fail with error message |
| Decision Point 2 | Condition depends on unstated input | Medium | Add input to Inputs section or state assumption |

Verdict: CHANGES_REQUIRED
```

### Agent 2: Semantic Coherence Checker

**Focus:** Do all sections tell the same story?

**What it checks:**
- Cross-references sections for consistency
- Inputs match what Procedure actually uses
- Outputs match what Procedure actually produces
- Troubleshooting covers failure modes implied by Procedure
- Verification checks measure what Outputs claims
- Terminology is consistent across sections

**Key question:** "Could someone read any section in isolation and get a consistent picture?"

**Output structure:**
```markdown
### Semantic Coherence Check

| Section A | Section B | Inconsistency | Resolution |
|-----------|-----------|---------------|------------|
| Inputs | Procedure | Procedure uses "config path" not listed in Inputs | Add to Inputs or rename in Procedure |
| Outputs | Verification | Verification doesn't check "summary report" artifact | Add verification step or clarify DoD |

Verdict: CHANGES_REQUIRED
```

### Agent 3: Dialogue Auditor

**Focus:** Did the collaborative process miss anything?

**What it checks:**
- Reviews decisions in `metadata.decisions`
- Identifies alternatives dismissed without sufficient exploration
- Surfaces questions that should have been asked but weren't
- Checks if user intent (from Phase 1-2) is fully reflected
- Flags assumptions that were accepted without validation

**Key question:** "If we ran this process again, would we uncover anything important that was missed?"

**Output structure:**
```markdown
### Dialogue Audit

| Gap Type | Finding | Impact | Recommendation |
|----------|---------|--------|----------------|
| Unexplored alternative | Single-file assumption — directories not discussed | Medium | Clarify scope or add directory handling |
| Unasked question | Error recovery strategy not established | High | Add to Troubleshooting or Procedure |
| Unvalidated assumption | "User has write access" assumed but not checked | Low | Add to Inputs assumptions |

Verdict: CHANGES_REQUIRED
```

**Legacy skill handling:**

When reviewing skills without `metadata.decisions`:

| Situation | Dialogue Auditor Behavior |
|-----------|---------------------------|
| `metadata.decisions` present | Full dialogue audit: review decisions, identify gaps, check alternatives |
| `metadata.decisions` absent | Limited audit: focus on section coherence only, skip decision review |

**Limited audit checks:**
- Does the skill have clear purpose from description + When to Use?
- Are Inputs/Outputs coherent with Procedure?
- Are decision points justified inline?
- Does Troubleshooting cover implied failure modes?

**Output for legacy skills:**
```markdown
### Dialogue Audit (Limited Mode)

⚠️ This skill lacks `metadata.decisions` — created outside skillosophy.
Decision history unavailable. Focusing on section coherence.

| Check | Finding | Severity |
|-------|---------|----------|
| Purpose clarity | Clear from description | — |
| I/O coherence | Outputs match Procedure | — |
| Decision justification | Step 5 branches without rationale | Medium |

Verdict: CHANGES_REQUIRED (optional — consider adding rationale to Step 5)
```

### Agent 4: Adversarial Reviewer

**Focus:** Are decisions defensible and is the skill robust?

**Two-pronged mandate:**

**Decision Challenge (Contrarian):**
- For each key decision, argues the alternative
- Forces explicit justification
- Surfaces trade-offs not discussed
- Doesn't accept "it felt right" — demands reasoning

**Failure Discovery (Red Team):**
- Identifies scenarios that would produce wrong results
- Finds inputs causing unexpected behavior
- Checks if safeguards match actual risks
- Asks: "What's the worst outcome and how likely is it?"

**Output structure:**
```markdown
### Adversarial Review

#### Decision Challenges
| Decision | Alternative | Challenge | Verdict |
|----------|-------------|-----------|---------|
| Multi-phase approach | Single-phase | Why the complexity? | Justified: dependencies require ordering |
| Risk tier: High | Medium | Effects seem contained | Upheld: external API calls warrant caution |

#### Failure Scenarios
| Scenario | Likelihood | Severity | Mitigation Present? |
|----------|------------|----------|---------------------|
| API timeout mid-process | High | Medium | No — needs recovery step |
| Malformed input file | Medium | Low | Yes — Step 2 validates |

Verdict: CHANGES_REQUIRED
```

---

## 4. Loop-Back Strategy

When the synthesis panel rejects a skill, the feedback must be routed appropriately. Not all issues require the same response.

### Severity Classification

| Severity | Characteristics | Loop-Back Mode |
|----------|-----------------|----------------|
| **Minor** | Localized to single section; can fix by editing existing content | Propose-and-confirm |
| **Major** | Systemic; requires revisiting underlying thinking; multiple sections affected | Full collaboration |

### Classification Heuristics

| Signal | Likely Severity |
|--------|-----------------|
| Single section affected | Minor |
| Multiple sections affected | Major |
| Wording/clarity issue | Minor |
| Design/decision issue | Major |
| Executability Auditor feedback | Usually Minor |
| Dialogue Auditor feedback | Usually Major |
| Adversarial: failure mode gap | Minor |
| Adversarial: decision challenge — rationale exists and is strong | Minor (cite existing rationale) |
| Adversarial: decision challenge — rationale missing or weak | Major |
| Semantic Coherence: terminology mismatch | Minor |
| Semantic Coherence: structural inconsistency | Major |

**Decision challenge refinement:** When Adversarial Reviewer challenges a decision, first check `metadata.decisions.approach.alternatives` for recorded rationale. If the challenge is already addressed by documented reasoning, respond with Minor loop-back citing the existing justification. Only escalate to Major if the challenge reveals genuinely unexplored territory or weak reasoning.

### Minor Issue Flow (Propose-and-Confirm)

```
Panel identifies minor issue
     │
     ▼
Claude proposes specific fix
     │
     ▼
AskUserQuestion with options:
     │
     ├── "Apply this fix" → Apply fix, re-submit to panel
     ├── "Modify the fix" → User provides adjustment, apply, re-submit
     ├── "Discuss further" → Escalate to full collaboration
     └── (Other) → User provides alternative approach
```

### Major Issue Flow (Full Collaboration)

```
Panel identifies major issue
     │
     ▼
Identify originating phase (1, 2, or 3)
     │
     ▼
Return to that phase checkpoint
     │
     ▼
Collaborative dialogue to resolve
     │
     ▼
Update decisions in metadata
     │
     ▼
Re-generate affected sections
     │
     ▼
Re-submit to panel
```

### Iteration Limits (Adaptive)

```
After each panel round:
     │
     ├── Progress made? (fewer issues than previous round)
     │   │
     │   ├── Yes → Continue (up to 5 total iterations)
     │   │
     │   └── No → Same or more issues?
     │       │
     │       ├── Same issues recurring → Escalate immediately
     │       │
     │       └── Different issues → Continue (up to 3 iterations)
     │
     └── 5 iterations reached → Human escalation
```

### Human Escalation

When adaptive limits are exceeded:

1. Present full context: original intent, decisions made, panel feedback history
2. Show where consensus is stuck
3. Ask user to make final decision
4. Proceed with user's choice (document as justified exception)

---

## 5. 11-Section Structure and Validation

skillosophy defines a **v2.0 section structure** extending the original 8-section skill format from skill-wizard. This structure is authoritative for skillosophy-created skills:

| Version | Sections | Source |
|---------|----------|--------|
| v1.0 | 8 sections | skill-wizard original (When to use through Troubleshooting) |
| v2.0 | 11 sections | skillosophy extension (+Triggers, +Anti-Patterns, +Extension Points) |

### Version Coexistence Policy

| Action | Skill Version | Behavior |
|--------|---------------|----------|
| CREATE | v2.0 only | skillosophy always creates v2.0 skills with all 11 sections |
| REVIEW | v1.0 or v2.0 | Panel reviews what exists; missing v2.0 sections noted as warnings (not failures) |
| VALIDATE | v1.0 or v2.0 | Checklists run for existing sections only |

**v1.0 skills in REVIEW mode:**
- Executability, Semantic Coherence, Adversarial auditors run on existing sections
- Dialogue Auditor runs in limited mode (no `metadata.decisions`)
- Report includes: "Missing v2.0 sections: Triggers, Anti-Patterns, Extension Points (optional — skill remains valid)"

**Migration path:** Users can add v2.0 sections to existing skills manually. skillosophy doesn't force migration; v1.0 skills remain fully functional.

### Skill Categories (21)

| Category | Risk Tier | Primary Failure Mode |
|----------|-----------|----------------------|
| debugging-triage | Medium | Missing regression guard |
| refactoring-modernization | Medium | Behavior change undetected |
| security-changes | High | Deny-path not verified |
| agentic-pipelines | High | Missing idempotency contract |
| documentation-generation | Low | Stale content |
| code-generation | Medium | Generated code doesn't compile |
| testing | Medium | Tests don't isolate failures |
| configuration-changes | Medium | Rollback not possible |
| dependency-changes | High | Breaking changes undetected |
| api-changes | High | Contract violation |
| data-migrations | High | Data loss or corruption |
| infrastructure-ops | High | Irreversible state change |
| meta-skills | Low | Produced skills non-compliant |
| review-audit | Medium | Superficial review |
| prompt-engineering | Medium | Overfitting to test cases |
| research-exploration | Low | Inconclusive findings |
| planning-architecture | Medium | Plan fails implementation |
| performance-optimization | Medium | Wrong bottleneck targeted |
| automation-scripting | Medium | Works locally, fails in CI |
| ui-ux-development | Medium | Functional but poor UX |
| incident-response | High | Mitigation introduces issues |

**Source:** Full category guidance with DoD additions copied to `references/methodology/category-integration.md`

The v2.0 structure is defined entirely within this document — there is no external spec to reference. Each section's requirements are captured in validation checklists stored in `references/checklists/`.

### Frontmatter Structure

**Standard fields (from spec):**

| Field | Required | Constraint |
|-------|----------|------------|
| `name` | Yes | kebab-case, ≤64 chars |
| `description` | Yes | ≤1024 chars, no `<` or `>`, single line |
| `license` | No | MIT, Apache-2.0, etc. |
| `allowed-tools` | Conditional | List all tools used; omit if none |
| `user-invocable` | No | `true` if should appear in slash menu |
| `metadata.version` | No | Semver (e.g., "1.0.0") |

**skillosophy-specific fields:**

| Field | Purpose |
|-------|---------|
| `metadata.decisions.requirements.explicit` | What user literally asked for |
| `metadata.decisions.requirements.implicit` | What user expects but didn't state |
| `metadata.decisions.requirements.discovered` | What analysis revealed |
| `metadata.decisions.approach.chosen` | Selected approach |
| `metadata.decisions.approach.alternatives` | Alternatives considered + why rejected |
| `metadata.decisions.risk_tier` | Low/Medium/High + rationale |
| `metadata.decisions.key_tradeoffs` | Trade-offs made |
| `metadata.decisions.category` | Skill category (from 21) |

**Validation note:** The nested `metadata.decisions` structure has been tested against Claude Code's skill parser and confirmed to parse correctly. Skills with 4-level nesting (e.g., `metadata.decisions.requirements.explicit`) load without error.

### Body Sections (11 total)

| # | Section | Purpose |
|---|---------|---------|
| 1 | **Triggers** | Discovery phrases — what the user literally says to invoke (≥3) |
| 2 | **When to use** | Contextual conditions — what situation warrants this skill |
| 3 | **When NOT to use** | STOP conditions, exclusions |
| 4 | **Inputs** | Required/optional inputs, assumptions |
| 5 | **Outputs** | Artifacts with objective DoD |
| 6 | **Procedure** | Numbered steps |
| 7 | **Decision Points** | Branching logic, defaults |
| 8 | **Verification** | Quick check + expected result |
| 9 | **Troubleshooting** | Failure modes → recovery |
| 10 | **Anti-Patterns** | What to avoid (≥1) |
| 11 | **Extension Points** | Evolution paths (≥2) |

**Triggers vs When to use distinction:**
- **Triggers** answer: "What words/phrases should Claude recognize as invoking this skill?" Examples: "create a skill", "new skill for", "help me build a skill"
- **When to use** answers: "In what situations should Claude consider using this skill, even if not explicitly triggered?" Examples: "User is describing a repeatable workflow", "Task involves creating reusable automation"

### Session State (Transient Section)

| Field | Purpose |
|-------|---------|
| `phase` | Current phase (0-4) |
| `progress` | Sections completed (e.g., "7/11") |
| `last_action` | What happened before interruption |
| `dialogue_context` | Key exchanges, preferences, insights |
| `next_steps` | What was about to happen |

*Session State is removed after Phase 4 approval.*

### Session State Removal

When the synthesis panel returns unanimous APPROVED:

1. skillosophy reads the complete SKILL.md
2. Removes the `## Session State` section and all content below it
3. Writes the updated SKILL.md (overwriting the version with Session State)
4. Confirms to user: "Skill approved and finalized. Session State removed."

**Implementation note:** Session State removal must be markdown-aware:

1. Session State is always the **last H2 section** in the document (enforced during generation)
2. To remove safely:
   - Find the last occurrence of `\n## Session State` (must be at line start, not in code block)
   - Verify no other H2 headings follow it
   - Truncate from that point forward
3. If verification fails (Session State isn't last, or pattern found mid-document), warn and ask user to remove manually

**Why last-section constraint:** Guarantees safe truncation. A `## Session State` inside a code block or example would never be the last H2, so the verification catches it.

### Validation Layers

Each section is validated at three levels:

**[MUST] — Structural requirements**
- Section exists and has content
- Required elements present (e.g., ≥3 triggers, ≥2 decision points)
- Format correct (e.g., numbered steps in Procedure)
- Blocks approval if violated

**[SHOULD] — Quality requirements**
- Best practices followed
- Completeness beyond minimum
- Warns if violated, allows acknowledgment

**[SEMANTIC] — Anti-pattern detection**
- Scans for problematic language patterns
- "Use judgment" → flag as Decision Sufficiency issue
- "Handle appropriately" → flag as ambiguity
- "etc." or "and so on" → flag as incomplete

### Checklist Sources

| Target | Checklist Status |
|--------|------------------|
| Frontmatter (standard) | Exists (skill-wizard) |
| Frontmatter (decisions) | **New** — needs creation |
| Triggers | **New** — needs creation |
| When to use | Exists (skill-wizard) |
| When NOT to use | Exists (skill-wizard) |
| Inputs | Exists (skill-wizard) |
| Outputs | Exists (skill-wizard) |
| Procedure | Exists (skill-wizard) |
| Decision Points | Exists (skill-wizard) |
| Verification | Exists (skill-wizard) |
| Troubleshooting | Exists (skill-wizard) |
| Anti-Patterns | **New** — needs creation |
| Extension Points | **New** — needs creation |
| Session State | **New** — needs creation |

### New Checklist Specifications

These are the [MUST] validation rules for the 5 new sections. [SHOULD] and [SEMANTIC] rules will be defined during implementation based on usage patterns, following the skill-wizard checklist structure.

| Section | [MUST] Validation Rules |
|---------|------------------------|
| **Triggers** | ≥3 phrases; each ≤50 chars; no duplicates; no overlap with When to use content |
| **Anti-Patterns** | ≥1 entry; each has pattern description + consequence; not duplicates of When NOT to use |
| **Extension Points** | ≥2 entries; each is actionable (verb + object); not vague ("improve", "enhance") |
| **Frontmatter-decisions** | `metadata.decisions` present and parses; contains `requirements` (with ≥1 explicit), `approach.chosen`, `risk_tier` |
| **Session State** | `phase` field present (0-4); `progress` parseable as "N/11"; removed after Phase 4 approval |

**Note:** These rules define pass/fail criteria. Skills failing [MUST] rules cannot proceed to Phase 4. Full checklists with [SHOULD] (quality warnings) and [SEMANTIC] (anti-pattern detection) will be created in `references/checklists/` during implementation.

---

## 6. Session Recovery and Handoff Integration

Skill creation is a multi-phase process that can be interrupted. skillosophy uses a two-layer recovery system: artifact-embedded state for depth, handoff integration for routing.

### Session State (In-Artifact)

The `## Session State` section in SKILL.md captures transient context:

```markdown
## Session State
<!-- Removed automatically after Phase 4 approval -->

**Phase:** 3 (Generation)
**Progress:** 7/11 sections approved
**Last action:** User approved Procedure section with minor edits

### Dialogue Context
- User prefers minimal complexity — rejected multi-phase approach
- Alternative considered: Checklist pattern — dismissed (outputs vary by input)
- Key insight from Inversion Lens: Skill fails if input validation skipped
- User prefers fail-fast over graceful degradation

### Next Steps
- Generate Decision Points section
- Then Verification, Troubleshooting, Anti-Patterns, Extension Points
```

**What it captures:**
- Current phase and section progress
- Recent dialogue highlights
- User preferences discovered this session
- Methodology insights not yet materialized in sections
- Explicit next steps

**Lifecycle and timing:**

| Artifact | When Written | When Updated | When Removed |
|----------|--------------|--------------|--------------|
| `metadata.decisions` | Incrementally during Phase 1 | After Phase 2 validation; after major loop-backs | Never (permanent record) |
| `## Session State` | End of Phase 1 (snapshot) | After each section approval in Phase 3 | After Phase 4 approval |

**Distinction:**
- `metadata.decisions` captures **what was decided** — permanent audit trail of requirements, approach, trade-offs
- `## Session State` captures **where we are** — transient progress tracking for session recovery

### Handoff Integration

The existing `/handoff` skill handles cross-project session routing. When a skill creation session ends:

```
User ends session mid-creation
     │
     ▼
/handoff captures:
  • Goal: "Creating skill: my-skill"
  • Next Steps: "Continue Phase 3 at .claude/skills/my-skill/"
  • Decisions: High-level choices made
  • User Preferences: Style preferences discovered
     │
     ▼
Session State in SKILL.md captures:
  • Detailed progress within workflow
  • Section-by-section status
  • Dialogue context specific to skill creation
```

### Resume Flow

```
New session starts
     │
     ▼
User runs /resume
     │
     ▼
Handoff tells Claude:
  "You were creating a skill at .claude/skills/my-skill/"
     │
     ▼
Handoff deleted (single-use)
     │
     ▼
User/Claude opens skill creation at that path
     │
     ▼
skillosophy reads SKILL.md:
  • Parse metadata.decisions → design context
  • Parse ## Session State → progress + dialogue context
  • Validate existing sections against checklists
     │
     ▼
Resume prompt:
  "Welcome back. We were on Phase 3, about to generate Decision Points.
   You prefer minimal complexity and fail-fast error handling.
   7/11 sections complete. Ready to continue?"
```

### Recovery Validation

Before resuming, skillosophy validates existing content:

| Check | If Failed |
|-------|-----------|
| Frontmatter parses | Ask user to fix manually or restart |
| Existing sections pass checklists | Flag failing sections for re-validation |
| Session State present | Reconstruct from metadata.decisions + section count |
| metadata.decisions present | Can resume but with less context |

**Graceful degradation:** If Session State is missing but sections exist, skillosophy can reconstruct progress from section count and metadata.decisions. Resume is possible with reduced dialogue context.

### Cancellation Behavior

When user explicitly cancels skill creation mid-process:

| Phase | Cancellation Behavior |
|-------|----------------------|
| Phase 0 (Triage) | No artifact created yet — clean exit, nothing to preserve |
| Phase 1 (Deep Analysis) | Partial SKILL.md may exist with frontmatter + metadata.decisions; **preserve in place** with Session State showing interruption point |
| Phase 2 (Checkpoint) | SKILL.md has validated decisions; **preserve in place** — valuable context captured |
| Phase 3 (Generation) | Partial sections exist; **preserve in place** with Session State — user may resume later |
| Phase 4 (Panel) | Full SKILL.md exists but not yet approved; **preserve in place** — skill is complete, just not panel-approved |

**Key principle:** Always preserve partial work. Deletion requires explicit user request ("delete this skill", "start over").

**Cancellation flow:**
```
User signals cancel (Ctrl+C, "stop", "cancel", "nevermind")
     │
     ▼
Update Session State with:
  • phase: current phase
  • last_action: "User cancelled"
  • next_steps: "Resume or delete"
     │
     ▼
Confirm to user:
  "Skill creation paused. Partial work saved at <path>.
   Run /resume to continue or delete the file to start fresh."
```

**Write safety:**

Interrupted writes can corrupt SKILL.md. To mitigate:

1. **Before each write:** If SKILL.md exists, save it to `<path>.backup`
2. **On successful write:** Delete backup (if it exists)
3. **On resume:** Check if `.backup` file exists and is newer than main file
   - If yes, offer recovery: "Found backup from interrupted session. Restore from backup?"
   - If user declines, delete backup and continue with current file

**First write (new skill):** No backup exists yet — if interrupted, the file either doesn't exist or is partially written. On resume, skillosophy detects malformed/incomplete SKILL.md (frontmatter won't parse or sections missing) and offers: "Skill file appears corrupted. Start fresh or attempt recovery?"

**Scope:** This applies to Phase 3 section writes and Session State updates — the high-frequency write points. Phase 4 final write (Session State removal) also uses backup.

**Backup cleanup:** Backups older than 24 hours are stale and can be ignored or deleted on next skillosophy invocation.

---

## 7. Plugin Structure

skillosophy is distributed as a Claude Code plugin. No commands — the skill handles all modes through trigger detection.

### Directory Layout

```
packages/plugins/skillosophy/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── executability-auditor.md
│   ├── semantic-coherence-checker.md
│   ├── dialogue-auditor.md
│   └── adversarial-reviewer.md
├── skills/
│   └── skillosophy/
│       ├── SKILL.md
│       └── references/
│           ├── checklists/
│           │   ├── frontmatter.md
│           │   ├── frontmatter-decisions.md
│           │   ├── triggers.md
│           │   ├── when-to-use.md
│           │   ├── when-not-to-use.md
│           │   ├── inputs.md
│           │   ├── outputs.md
│           │   ├── procedure.md
│           │   ├── decision-points.md
│           │   ├── verification.md
│           │   ├── troubleshooting.md
│           │   ├── anti-patterns.md
│           │   ├── extension-points.md
│           │   └── session-state.md
│           ├── methodology/
│           │   ├── thinking-lenses.md
│           │   ├── regression-questions.md
│           │   ├── category-integration.md
│           │   └── risk-tiers.md
│           └── templates/
│               ├── decisions-schema.md
│               ├── session-state-schema.md
│               └── skill-skeleton.md
├── scripts/
│   └── discover_skills.py
├── README.md
├── LICENSE
└── CHANGELOG.md
```

### Plugin Manifest

```json
{
  "name": "skillosophy",
  "version": "1.0.0",
  "description": "Collaborative skill creation with deep methodology and multi-agent synthesis",
  "author": {
    "name": "Your Name"
  },
  "license": "MIT",
  "keywords": ["skill-creation", "meta-skill", "methodology", "synthesis-panel"]
}
```

### Mode Detection

The skill handles mode detection through input analysis:

| Input Pattern | Mode |
|---------------|------|
| Contains path + "review" / "panel" / "synthesis" | REVIEW |
| Contains path + "validate" / "check" / "lint" | VALIDATE |
| Contains path + both review AND validate keywords | Ask: "Full panel review or quick validation only?" |
| Contains path only (no other signals) | Ask: Review or Validate? |
| Creation intent ("create", "new", "build", "design") | CREATE |
| CREATE + path to existing skill | Ask: "Create new or modify existing?" |
| Just "skillosophy" / unclear intent | Ask: What would you like to do? |

**Keyword priority (when not asking):** CREATE signals take precedence over REVIEW/VALIDATE — if user says "create a review skill", that's CREATE mode, not REVIEW mode.

If ambiguous, use AskUserQuestion:
- "Create a new skill" → CREATE
- "Review an existing skill (full panel)" → REVIEW
- "Quick validation only (checklists)" → VALIDATE

**Self-modification guard:**

skillosophy must not modify its own skill files. Before entering CREATE or MODIFY mode:

1. Resolve the target skill path
2. Check if path is within `skillosophy/` plugin directory
3. If match, block with explanation:
   ```
   ⚠️ skillosophy cannot modify itself — this would create circular dependency issues.
   To update skillosophy, edit the skill files directly outside of skillosophy.
   ```

**REVIEW and VALIDATE are allowed** — skillosophy can review itself (useful for quality checks), just not modify itself.

### Session State in REVIEW Mode

When REVIEW mode encounters a skill with `## Session State` section:

| Session State Present | REVIEW Behavior |
|-----------------------|-----------------|
| Phase 3 incomplete (progress < 11/11) | Warn: "This skill has incomplete Session State from a cancelled creation. Options: (1) Resume creation, (2) Strip Session State and review as-is, (3) Cancel" |
| Phase 4 incomplete (progress = 11/11, not approved) | Proceed with REVIEW; Session State is informational only |

**Rationale:** A skill with incomplete sections shouldn't be panel-reviewed as if it were complete. The user should either finish creation or explicitly acknowledge they want to review an incomplete skill.

**Session State stripping:**
If user chooses "Strip Session State and review as-is":
1. Read SKILL.md
2. Remove `## Session State` section
3. Write updated SKILL.md
4. Proceed with REVIEW on remaining content

### Agent Definitions

Each agent file follows the plugin agent format:

```markdown
---
description: What this agent specializes in
capabilities: ['capability1', 'capability2']
---

# Agent Name

## Purpose
What the agent evaluates and why.

## Evaluation Criteria
Specific checks the agent performs.

## Output Format
Structure of the agent's verdict.
```

**Agent tools:**
- All 4 agents: Read, Glob, Grep (read-only)
- Adversarial Reviewer: May also use Bash for running verification commands

**Agent model:**
- All agents run on Opus for maximum quality
- Launched in parallel via Task tool from main skill

**Model fallback strategy:**

Model availability cannot be checked in advance — failures are detected at runtime when Task tool rejects the model parameter.

| Attempt | On Failure |
|---------|------------|
| Launch all 4 agents with `model: opus` | If any agent fails with model error, retry failed agents with `model: sonnet` |
| Retry with `model: sonnet` | If still failing, warn user and skip panel: "Synthesis panel requires Sonnet or Opus. Proceeding without panel review." |

**Fallback behavior:**
- Agents that succeeded on Opus continue; only failed agents retry on Sonnet
- Mixed-model panel is acceptable (some Opus, some Sonnet)
- If panel is skipped entirely, skill is written but marked: `metadata.panel_status: skipped`
- User can re-run panel later with `/skillosophy review <path>`

**Agent context management:**

Each panel agent receives the full SKILL.md in their prompt. This works well for typical skills.

**Large skill warning (>1000 lines):**
If the skill exceeds 1000 lines, warn user before launching panel:
```
⚠️ This skill is unusually large (X lines).
   Large skills often indicate scope creep — consider splitting into focused skills.
   Proceed with panel review anyway?
```

Skills this large are rare and usually a design smell. The warning prompts reconsideration before spending agent resources on something that may need restructuring.

---

## 8. Methodology Integration

skillosophy uses deep methodology to enrich the collaborative dialogue. Claude applies the 11 thinking lenses and regression questioning as part of its internal reasoning — insights that improve the conversation are surfaced, others inform Claude's understanding without being shared.

### The 11 Thinking Lenses

| Lens | Core Question | How It Enriches Dialogue |
|------|---------------|--------------------------|
| **First Principles** | What's fundamentally needed? | Strips away assumptions, surfaces core requirements |
| **Inversion** | What guarantees failure? | Generates anti-patterns and STOP conditions |
| **Second-Order** | What happens after the obvious? | Reveals downstream effects user didn't consider |
| **Pre-Mortem** | Why did this fail? | Proactive risk identification for Troubleshooting |
| **Systems Thinking** | How do parts interact? | Maps dependencies between sections |
| **Devil's Advocate** | Strongest counter-argument? | Challenges design decisions before panel does |
| **Constraints** | What's truly fixed? | Separates real constraints from assumed ones |
| **Pareto** | Which 20% delivers 80%? | Keeps skill focused, avoids scope creep |
| **Root Cause** | Why is this needed? (5 Whys) | Ensures skill addresses actual problem |
| **Comparative** | How do options compare? | Informs approach exploration with trade-offs |
| **Opportunity Cost** | What are we giving up? | Makes trade-offs explicit for user decisions |

### Methodology-Enriched Dialogue

Claude's internal reasoning applies the methodology; the dialogue reflects those insights:

```
User: "I want a skill for code review"
     │
     ▼
Claude thinks (internally):
  • First Principles: Core need is catching bugs before merge
  • Inversion: Would fail if missing context or wrong file scope
  • Second-Order: Large diffs could overwhelm the review
     │
     ▼
Claude asks (informed by analysis):
  "What kind of code review — security, style, or catching logic bugs?
   And roughly how large are typical PRs you'd run this on?"
     │
     ▼
User: "Logic bugs, usually under 500 lines but sometimes larger"
     │
     ▼
Claude thinks (internally):
  • Pre-Mortem: Review might miss bugs due to fatigue on large diffs
  • Constraints: 500 lines typical, but need strategy for larger
  • Pareto: Focus on high-signal patterns, not exhaustive checking
     │
     ▼
Claude asks (surfacing insight):
  "For larger diffs, should the skill chunk the review into sections
   or provide a summary with high-risk areas highlighted?"
```

**Key principle:** Not all analysis is shared. Claude uses judgment about what advances the conversation versus what informs its own understanding.

### What to Surface vs. Keep Internal

| Insight Type | Share with User? | Rationale |
|--------------|------------------|-----------|
| Clarifying question | Yes | Resolves ambiguity, advances requirements |
| Alternative approach | Yes | User should make informed choice |
| Identified risk | Yes | User should know and decide on mitigation |
| Edge case discovered | Yes, as question | "What if X happens?" |
| Confirmed assumption | Only if user assumed otherwise | Avoid noise |
| Internal model refinement | No | Doesn't need user input |
| Dead-end explored | No (unless asked) | User doesn't need to know what didn't work |

### Regression Questioning

After initial discovery, Claude runs internal self-questioning:

```
Round N (internal):
├── "What am I missing about this skill?"
├── "What would a domain expert add?"
├── "What's the weakest part of this design?"
├── "Which lens haven't I applied?"
│
└── New insight that should inform dialogue?
    ├── Yes → Incorporate into next question or recommendation
    └── No (3 consecutive empty rounds) → Analysis complete
```

**Termination criteria:**
- 3 consecutive rounds with no new dialogue-relevant insights
- All 11 lenses considered (at least scanned, 5+ applied in depth)
- Maximum 7 rounds (hard cap to prevent overthinking)

**User experience:** The user sees a natural conversation. They don't see "applying Inversion lens..." — they see thoughtful questions that happen to be informed by that analysis.

### Capturing Insights in Decisions

As dialogue progresses, Claude captures key insights in `metadata.decisions`:

```yaml
metadata:
  decisions:
    requirements:
      explicit:
        - "Review code for logic bugs before PR merge"
      implicit:
        - "Should work on typical PR size (< 500 lines)"
      discovered:
        - "Needs chunking strategy for large diffs"
        - "Must handle missing file context gracefully"
    approach:
      chosen: "Multi-phase: gather context → analyze → report"
      alternatives:
        - "Single-pass streaming" — rejected: loses cross-file context
        - "Checklist-only" — rejected: bugs require reasoning
    methodology_insights:
      - "Inversion lens revealed: fails without surrounding code context"
      - "Pre-mortem revealed: reviewer fatigue on large diffs"
```

This creates an audit trail of how methodology informed the design, without burdening the user with the mechanics.

### Methodology Verification

To ensure methodology is genuinely applied (not just claimed):

**Required:** `metadata.decisions.methodology_insights` must contain:
- At least 5 entries (from different lenses)
- Each entry links lens → specific insight → affected section

**Adversarial Reviewer verification:**
The Adversarial Reviewer includes methodology verification:
1. Check that ≥5 lenses produced documented insights
2. Verify insights are substantive (not "applied X, found nothing")
3. Trace each insight to the section it influenced
4. Flag if methodology_insights appears formulaic or shallow

**Failure modes:**

| Signal | Indicates |
|--------|-----------|
| <5 documented insights | Methodology likely skipped or superficial |
| All insights say "no findings" | Analysis wasn't rigorous |
| Insights don't trace to sections | Methodology was theater |

**Known limitation:** The verification checks that methodology insights exist and are substantive, but cannot prove they were genuinely applied during dialogue versus retrospectively constructed. This is inherent to any self-reported process.

Mitigations:
- Adversarial Reviewer checks for formulaic patterns ("applied X, found nothing" repeated)
- Insights must trace to specific sections they influenced
- Shallow or contradictory insights trigger CHANGES_REQUIRED

This provides reasonable confidence without claiming certainty. Full verification would require observing Claude's reasoning in real-time, which is out of scope.

---

## 9. Migration Path

skillosophy replaces skill-wizard and skillforge. This section defines how to transition.

### What Gets Replaced

| Existing | Status | Replacement |
|----------|--------|-------------|
| skill-wizard | Deprecated → Removed | skillosophy (CREATE mode) |
| skillforge | Deprecated → Removed | skillosophy (all modes) |

### What Gets Preserved

**From skill-wizard:**
- 9 section checklists → copied to `references/checklists/`
- Category integration (21 categories) → copied to `references/methodology/`
- Risk tier guide → copied to `references/methodology/`
- Skill skeleton template → copied to `references/templates/`
- Interactive dialogue approach → preserved in workflow design

**From skillforge:**
- 11 thinking lenses → copied to `references/methodology/`
- Regression questions → copied to `references/methodology/`
- `discover_skills.py` → copied to `scripts/`
- Multi-agent synthesis concept → reimagined as 4-agent panel

### What Gets Dropped

| Component | Reason |
|-----------|--------|
| XML specification format | Replaced by embedded decisions metadata |
| `validate-skill.py` | Merged into checklist-based validation |
| `quick_validate.py` | Subsumed by VALIDATE mode |
| `package_skill.py` | Out of scope for skillosophy |
| skillforge commands | Skills don't need commands |
| skill-wizard wizard metadata | Replaced by Session State |

### Migration Steps

**Phase 1: Create skillosophy plugin**
1. Create plugin structure in `packages/plugins/skillosophy/`
2. Copy and adapt reference files from both sources
3. Create 5 new checklists (frontmatter-decisions, triggers, anti-patterns, extension-points, session-state)
4. Write 4 agent definitions
5. Write main SKILL.md

**Phase 2: Deprecation notices**
1. Add deprecation warning to skill-wizard: "Use skillosophy instead"
2. Add deprecation warning to skillforge: "Use skillosophy instead"
3. Warnings point to skillosophy installation instructions

**Phase 3: Testing**
1. Create a test skill using skillosophy
2. Verify all phases complete successfully
3. Verify panel produces meaningful feedback
4. Test session recovery

**Phase 4: Removal**
1. Remove skill-wizard from `.claude/skills/`
2. Remove skillforge from `.claude/skills/`
3. Update any references in CLAUDE.md or documentation

### Backwards Compatibility

**Skills created by skill-wizard or skillforge:**
- Remain valid (they're just SKILL.md files)
- Can be reviewed by skillosophy's REVIEW mode
- May trigger warnings for missing v2.0 sections (Triggers, Anti-Patterns, Extension Points)

**Users with muscle memory:**
- "skillforge" or "skill-wizard" triggers could be added to skillosophy for graceful redirection
- Or let them fail with clear "use skillosophy instead" message

---

## 10. Open Questions and Future Work

### Deferred Decisions

| Item | Why Deferred | Revisit When |
|------|--------------|--------------|
| Batch validation mode | Single-skill flow is the priority | After v1.0 stable, if users request |
| Skill versioning | Git handles this adequately | If skills need semantic versioning |
| Domain-specific annexes | Adds complexity without clear need | If certain categories need specialized guidance |
| Automated spec sync | Manual sync acceptable initially | If upstream spec changes frequently |
| Relaxed mode for drafts | Ship strict first | If users find full rigor too heavy for exploration |
| Integration with promote script | Separate concern | After v1.0, when deployment workflow is clearer |

### Open Questions

| Question | Current Thinking | Resolution Needed |
|----------|------------------|-------------------|
| **Should skillosophy modify itself?** | No — hand-modify initially to avoid circular dependency | Revisit after v1.0 stable |
| **Panel agent model override?** | All Opus for quality, no override | If cost becomes concern, allow haiku for some agents |
| **Very large skills (>1000 lines)?** | Rare; handle when encountered | If patterns emerge, add chunking guidance |
| **Should Triggers section be first?** | Yes — matches discovery flow | Validate with usage |
| **How to handle partial Session State?** | Graceful degradation documented | Test edge cases during implementation |

### Future Enhancements

| Enhancement | Priority | Description |
|-------------|----------|-------------|
| `/skillosophy` command alias | Low | Add if users request explicit invocation |
| Skill metrics/telemetry | Low | Track creation success rates, common failures |
| Category-specific templates | Medium | Pre-populated sections for common categories |
| Panel agent feedback history | Medium | Show what previous iterations flagged |
| Multi-skill composition | Low | Creating skills that chain with others |
| CI/CD integration | Medium | Exit codes for automated validation |

### Known Risks

| Risk | Mitigation |
|------|------------|
| **Panel too strict** | Adaptive iteration limits; human escalation path |
| **Methodology overwhelms dialogue** | Keep methodology internal; only surface relevant insights |
| **Session State bloat** | Clear lifecycle; removed after approval |
| **Checklist drift from spec** | Single source of truth in skillosophy; update together |
| **Users skip to Phase 4** | REVIEW mode exists for this; skill handles gracefully |

---

## 11. Design Summary

### What skillosophy Is

A Claude Code plugin for creating high-quality skills through collaborative dialogue and rigorous methodology. It combines skill-wizard's interactive approach with skillforge's deep analysis and multi-agent synthesis.

### Core Workflow

```
User expresses intent ("create a skill for X")
     │
     ▼
Phase 0: Triage
     │ Detect mode, check for existing skills
     ▼
Phase 1: Deep Analysis (Collaborative)
     │ Methodology-enriched dialogue
     │ Requirements discovery, approach exploration
     ▼
Phase 2: Specification Checkpoint (Collaborative)
     │ Validate consolidated decisions
     ▼
Phase 3: Generation (Collaborative)
     │ Section-by-section drafting
     │ Inline checklist validation
     ▼
Phase 4: Synthesis Panel (Autonomous)
     │ 4 agents, unanimous approval
     ▼
Production-ready SKILL.md
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Interaction model | Collaborative Phases 1-3, autonomous Phase 4 | Best of both worlds |
| Methodology integration | Enriches dialogue internally | Natural conversation, not structured walkthrough |
| Phase 2 artifact | Embedded decisions metadata | Single source of truth, no drift |
| Section structure | 11 sections (spec v2.0) | Extends original 8 with Triggers, Anti-Patterns, Extension Points |
| Panel composition | 4 specialized agents | Executability, Coherence, Dialogue gaps, Adversarial review |
| Consensus model | Unanimous | High quality bar |
| Iteration limits | Adaptive (3-5) | Prevents grinding, escalates when stuck |
| Loop-back strategy | Severity-based | Minor → propose-and-confirm, Major → full collaboration |
| Session recovery | Session State in SKILL.md + handoff integration | Rich context, single artifact |
| Extension type | Plugin (no commands) | Skill-only via Skill tool |
| Name | skillosophy | Philosophy of skills, collaborative inquiry |

### Plugin Contents

| Component | Count | Purpose |
|-----------|-------|---------|
| SKILL.md | 1 | Main skill with all modes |
| Agents | 4 | Synthesis panel members |
| Checklists | 14 | Section validation (9 existing + 5 new) |
| Methodology refs | 4 | Thinking lenses, regression Qs, categories, risk tiers |
| Templates | 3 | Decisions schema, session state, skill skeleton |
| Scripts | 1 | discover_skills.py for ecosystem scan |

### New Artifacts to Create

| Artifact | Type | Status |
|----------|------|--------|
| Triggers checklist | Reference | New |
| Anti-Patterns checklist | Reference | New |
| Extension Points checklist | Reference | New |
| Frontmatter-decisions checklist | Reference | New |
| Session State checklist | Reference | New |
| Executability Auditor | Agent | New |
| Semantic Coherence Checker | Agent | New |
| Dialogue Auditor | Agent | New |
| Adversarial Reviewer | Agent | New |
| Main SKILL.md | Skill | New |
| plugin.json | Manifest | New |

### Success Criteria

| Criterion | Verification |
|-----------|--------------|
| Plugin installs | `claude plugin install skillosophy@tool-dev` succeeds |
| Skill invocable | "Create a skill for X" triggers skillosophy |
| Mode detection works | CREATE, REVIEW, VALIDATE modes route correctly |
| Checklists validate | All 14 checklists run without error |
| Panel runs | 4 agents launch in parallel, return verdicts |
| Session recovery works | Interrupted session resumes correctly |
| skill-wizard deprecated | Warning points to skillosophy |
| skillforge deprecated | Warning points to skillosophy |

---

*Document generated from brainstorming session 2026-01-13*
*Design review (5 findings) addressed 2026-01-14*

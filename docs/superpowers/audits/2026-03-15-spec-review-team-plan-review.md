# Plan Review: spec-review-team Implementation Plan

**Date:** 2026-03-15
**Target:** `docs/superpowers/plans/2026-03-15-spec-review-team.md` (1012 lines)
**Source:** `docs/superpowers/specs/2026-03-14-spec-review-team-design.md` (515 lines)
**Stakes:** Rigorous
**Reviewer:** reviewing-designs skill (final quality gate before execution)

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 0 | — |
| P1 | 6 | Omitted normative content, missing active prohibitions, truncated guidance |
| P2 | 5 | Polish and minor completeness gaps |

**Overall assessment:** The plan is faithful to the spec and well-structured for agentic execution. No P0 issues — execution can proceed after addressing P1 findings. All P1 findings follow the same pattern: normative content or active prohibitions from the spec that aren't assigned to any plan task, leaving the implementer to either guess or re-read the spec.

---

## Delta Card #1: Early Gate

**Hypotheses:**

| ID | Hypothesis | Target Dimensions | Status |
|---|---|---|---|
| H1 | Plan truncates/distorts spec content in translation | D1, D2 | open |
| H2 | Plan silently omits normative content (unassigned to tasks) | D1, D8 | open |
| H3 | Domain brief quality guidance insufficient | D7, D15 | open |
| ALT1 | Navigator plan (spec references, no inline) | — | open |
| ALT2 | Single-pass transcription plan | — | open |

---

## Delta Card #2: Dimensional Loop Converged

**Convergence:** 2 passes. Pass 1 Yield=100% (6 P0+P1 entities). Pass 2 Yield=0% (no new P0+P1). Below 10% threshold.

### Bridge Updates

- **H1** (fragile copy) → **tested:** Partially confirmed. The plan's inline content is generally accurate, but F4 shows the synthesis boundary rule is truncated — the "two competent operators" decision criterion (spec line 275) is missing. This is the key conceptual tool for distinguishing mechanical passes from judgment obligations. [D2, Anchor: Task 5 Step 1 vs spec lines 274-277]

- **H2** (omitted content) → **tested:** Confirmed. Two normative spec elements have no home in the plan: (1) the team composition overview table with role IDs, types, and defect classes (spec lines 168-181), and (2) the "thin by remit, not by file reassignment" design principle (spec line 181). Both are SKILL.md content that the implementer would need to invent placement for. [D1, D8, Anchor: spec §Team Composition]

- **H3** (domain brief quality) → **tested:** Partially confirmed. The plan provides the 8-component structure with concrete examples per role, which is good scaffolding. But it omits the meta-instruction from spec line 431: "Rubrics are domain briefs that orient judgment, not checklists that constrain it." Without this, the implementer may write checklists instead of judgment-shaping narratives. [D7, Anchor: Task 8 vs spec line 431]

- **ALT1** (navigator plan) → **evaluated:** Not dominant. The navigator approach would require spec re-reading, defeating the plan's stated purpose for agentic workers. The current approach's verbosity is a feature for its target audience.

- **ALT2** (single-pass transcription) → **evaluated:** Not dominant. Loses chunk structure, validation step, and content distribution guidance. The plan's architecture adds genuine value.

### Findings

#### P1 Findings

**F1 (P1): Team composition table not assigned to any plan task**
- **Dimensions:** D1 (structural coverage), D8 (completeness)
- **Evidence:** Spec lines 168-181 define a 6-row table (4 core + 2 optional reviewers) with Role, ID, Type, and Defect Class columns. This normative content appears nowhere in the plan's task instructions. Task 3 Step 2 mentions "Core team (4 reviewers)" and Task 6 Step 1 mentions "finding ID prefix table: AA, CE, CC, VR, SP, IE" — but neither places the full team composition overview in SKILL.md.
- **Impact:** The implementer must decide where to put this table (likely before Phase 4, after Constraints). Without placement guidance, they might omit it entirely or scatter the information.
- **Confidence:** High (E2 — cross-checked plan tasks against spec section)

**F2 (P1): No trim priority for SKILL.md line overflow**
- **Dimensions:** D4 (decision rules), D6 (safety defaults)
- **Evidence:** Task 6 Step 5 says "If over 500, identify sections to trim or delegate to reference files. If under 350, check if any normative content was accidentally omitted." The instruction gives the action but no priority order for what to trim first.
- **Impact:** Risk of moving normative content to reference files, breaking the "SKILL.md alone is sufficient" principle. Rough line estimate: 415-487 lines (tight). Adding the team composition table (F1) pushes closer to 500.
- **Confidence:** Medium (E1 — based on line estimate, not actual implementation)

**F4 (P1): Synthesis boundary rule truncated**
- **Dimensions:** D2 (semantic fidelity)
- **Evidence:** Task 5 Step 1 says: "Open with the instruction philosophy (spec lines 274-277): 'Technique-in-Discipline-shell. Prescribe computation for auditable state; prescribe criteria for meaning.'" The spec's full boundary rule (line 275) includes a crucial decision criterion: "If two competent operators should reach the same result from the same raw facts and nothing valuable is lost by prescribing it, prescribe it (mechanical pass). Otherwise, state the obligation, require a rationale, and audit the structure (judgment obligation)."
- **Impact:** This sentence is the practical decision tool for the entire synthesis section — it tells the reader HOW to distinguish mechanical passes from judgment obligations. Without it, the distinction is stated but not operationalized.
- **Confidence:** High (E2 — direct comparison of plan text to spec text)

**F5 (P1): "Thin by remit, not by file reassignment" missing**
- **Dimensions:** D1 (structural coverage), D2 (semantic fidelity)
- **Evidence:** Spec line 181: "Design principle: 'Thin by remit, not by file reassignment.' All core reviewers access all files. They are scoped by defect class, not by file assignment. This prevents gaps at file boundaries." Not present in any plan task.
- **Impact:** Without this principle, the implementer or a future SKILL.md reader might scope reviewers by file assignment (e.g., "authority-architecture reviews only normative files"), creating gaps at file boundaries.
- **Confidence:** High (E2 — searched all plan tasks for this content)

**F6 (P1): No active prohibition against embedding packet content**
- **Dimensions:** D14 (precision), D19 (actionability)
- **Evidence:** Spec line 429: "Spawn prompts point reviewers to the workspace file. Reviewers read packet.md themselves — the lead does not condense or embed it." Spec line 384: "the packet is not embedded inline. This eliminates the ~1000 char embedding budget constraint and prevents destructive compression for large specs." The plan's Task 4 and Task 8 instruct pointing to the file (correct) but don't include an active prohibition against embedding. The prohibition appears only in failure-patterns.md (Task 10 Step 3) as a "common implementation mistake."
- **Impact:** Per the project's writing principles: "When Claude should avoid an action, use active prohibitions ('Do NOT set X') rather than passive language." The plan instructs what TO do but not what NOT to do. For a strong training prior (embedding context in prompts), passive instruction may not prevent the behavior.
- **Confidence:** High (E2 — verified plan Task 4, Task 8, and Task 10)

**F7 (P1): Missing "domain briefs orient judgment, not checklists" instruction**
- **Dimensions:** D7 (clarity), D2 (semantic fidelity)
- **Evidence:** Spec line 431: "Instruction philosophy for role delta: Rubrics are domain briefs that orient judgment, not checklists that constrain it. The reviewer's scope is the defect class domain, not a list of prescribed checks." Not present in plan Task 8 instructions.
- **Impact:** Affects the tone and effectiveness of all 6 domain briefs. An implementer who writes checklists (a natural default for structured templates) will produce reviewers that check boxes instead of exercising domain judgment. The spec explicitly warns against this.
- **Confidence:** High (E2 — searched plan Task 8 for this guidance)

#### P2 Findings

**F3 (P2): No guidance for reference file line overflow**
- **Dimensions:** D4 (decision rules)
- **Evidence:** Each reference file task has an "Expected: X-Y lines" validation step, but no guidance for what to do if exceeded. Role-rubrics.md (220-280 target) is the most likely to overflow given the 6 domain briefs with 8 components each.
- **Confidence:** Medium (E1)

**F8 (P2): Validation chunk doesn't check ledger template consistency**
- **Dimensions:** D11 (testability)
- **Evidence:** Task 11 validates cross-references, tool names, role IDs, schema fields, metrics, and phase gates. Missing: consistency check between the ledger template in SKILL.md (Task 5 Step 3) and the exemplar ledger in synthesis-guidance.md (Task 9 Step 4).
- **Confidence:** Medium (E1)

**F9 (P2): Missing "ambient context supplementary, preflight packet authoritative" instruction**
- **Dimensions:** D2 (semantic fidelity)
- **Evidence:** Spec constraint #3 (line 69): "Reviewers should use ambient project context (e.g., CLAUDE.md conventions, MCP tools) as supplementary information but treat the preflight packet as the authoritative source for spec structure and authority assignments." Plan Task 1 Step 5 captures the gist but drops this framing.
- **Confidence:** Low (E1 — risk is bounded since scaffold already points to packet)

**F10 (P2): Upgrade triggers table column set not fully specified**
- **Dimensions:** D3 (procedural completeness)
- **Evidence:** Spec lines 374-380 use a 5-column table (#, Trigger, Threshold, Signal, Requires). Plan Task 6 Step 4 mentions trigger names and thresholds but doesn't specify the full column set for the implementer to reproduce.
- **Confidence:** Medium (E1)

**F11 (P2): TeamCreate `description` parameter not mentioned**
- **Dimensions:** D3 (procedural completeness)
- **Evidence:** Platform reference (`agent-teams-platform.md` line 35) shows TeamCreate takes both `team_name` and `description`. Plan Task 4 Step 1 only mentions `team_name`.
- **Confidence:** Low (E1 — `description` may be optional)

---

## Delta Card #3: Adversarial Pass

### Bridge Table (Final)

| ID | Status | Disposition |
|---|---|---|
| H1 | tested | Partially confirmed: F4 (truncated boundary rule). Overall inline content is accurate — one truncation, not systematic distortion. |
| H2 | tested | Confirmed: F1 (team composition table), F5 ("thin by remit" principle). Two normative spec elements with no plan task assignment. |
| H3 | tested | Partially confirmed: F7 (missing "not checklists" instruction). Plan provides good scaffolding but omits the meta-instruction about brief purpose. |
| ALT1 | evaluated | Not dominant — requires spec re-reading, defeating agentic worker purpose. |
| ALT2 | evaluated | Not dominant — loses chunk structure and validation value. |

### Adversarial Findings

**A1 (Assumption Hunting):** Most fragile assumption is the 400-470 line target for SKILL.md. Rough estimate shows 415-487 (before team composition table). Tight but feasible — not a design flaw, but the implementer has minimal margin. *Already captured in F2.*

**A2 (Scale Stress):** N/A for a plan document — the plan is executed once. The skill's scale properties are spec-level concerns.

**A3 (Competing Perspectives):** An implementer reading only the plan (not the spec) would miss the design intent behind several prescriptions. The 6 P1 findings represent places where the plan gives WHAT but not WHY. *Already captured in F1, F4, F5, F6, F7.*

**A4 (Kill the Design):** The plan's value is eliminating spec re-reading. But it can't capture design INTENT — only design CONTENT. When the implementer faces uncovered decisions (domain brief quality, instruction tone, section compression), they'll either guess or read the spec. The plan reduces but can't eliminate spec dependence. *No NET-NEW finding — this is an inherent limitation of the plan format.*

**A5 (Pre-mortem):** "6 months later, the skill doesn't work well." Most likely cause: domain briefs are generic templates rather than domain-specific rubrics. The plan provides the 8-component structure but can't enforce quality. *Already captured in H3/F7.*

**A6 (Steelman Alternatives):** Neither ALT dominates. Navigator plan is better for human implementers; current plan is better for agentic workers. The choice matches the stated audience.

**A7 (Challenge the Framing):** The plan is optimized for agentic execution (Claude via subagent-driven-development). If a human were implementing, they'd just read the 515-line spec directly — the 1012-line plan would be overhead. The framing is correct for the stated audience.

**A8 (Hidden Complexity):** Domain brief authoring is the most underestimated complexity. Already captured in H3/F7.

**A9 (Motivated Reasoning):** The plan was written by the same session that wrote the spec. Shared context means the plan feels complete to its author but may have gaps for a fresh reader. The 6 P1 findings support this — they're all "obvious in context, missing on paper."

**NET-NEW findings:** None. All adversarial findings trace to existing bridge hypotheses or P1 findings.

---

## Coverage Tracker

### Source Coverage

| ID | Dimension | Status | Priority | Evidence | Confidence |
|---|---|---|---|---|---|
| D1 | Structural coverage | [~] | P0 | E2 | High |
| D2 | Semantic fidelity | [~] | P0 | E2 | High |
| D3 | Procedural completeness | [x] | P1 | E1 | Medium |

D1 partial: 2 spec sections unassigned (team composition, "thin by remit"). D2 partial: 1 truncation (boundary rule).

### Behavioral Completeness

| ID | Dimension | Status | Priority | Evidence | Confidence |
|---|---|---|---|---|---|
| D4 | Decision rules | [~] | P1 | E1 | Medium |
| D5 | Exit criteria | [x] | P2 | E1 | Medium |
| D6 | Safety defaults | [~] | P1 | E1 | Medium |

D4 partial: no trim priority for line overflow. D6 partial: same issue (wrong trim → normative content moved).

### Implementation Readiness

| ID | Dimension | Status | Priority | Evidence | Confidence |
|---|---|---|---|---|---|
| D7 | Clarity | [~] | P1 | E2 | High |
| D8 | Completeness | [~] | P1 | E2 | High |
| D9 | Feasibility | [x] | P2 | E1 | Medium |
| D10 | Edge cases | [x] | P2 | E1 | Medium |
| D11 | Testability | [~] | P2 | E1 | Medium |

D7 partial: missing "not checklists" guidance. D8 partial: missing team composition table.

### Consistency

| ID | Dimension | Status | Priority | Evidence | Confidence |
|---|---|---|---|---|---|
| D12 | Cross-validation | [x] | P0 | E2 | High |

Completeness basis: Verified role IDs (6), finding prefixes (6), phase names (8), file paths (5 reference files + workspace), tool names (14 in allowed-tools), phase gate conditions (8) — all consistent across plan sections.

### Document Quality

| ID | Dimension | Status | Priority | Evidence | Confidence |
|---|---|---|---|---|---|
| D13 | Implicit concepts | [x] | P2 | E1 | Medium |
| D14 | Precision | [~] | P1 | E2 | High |
| D15 | Examples | [x] | P2 | E2 | High |
| D16 | Internal consistency | [x] | P1 | E2 | High |
| D17 | Redundancy | [x] | P2 | E1 | Medium |
| D18 | Verifiability | [x] | P2 | E1 | Medium |
| D19 | Actionability | [~] | P1 | E2 | High |

D14 partial: implicit instruction (use pointer) instead of active prohibition (don't embed). D19 partial: missing guidance for line overflow decisions.

---

## Iteration Log

| Pass | New P0+P1 | Revised | Total P0+P1 | Yield% |
|---|---|---|---|---|
| 1 | 6 (F1,F2,F4,F5,F6,F7) | 0 | 6 | 100% |
| 2 | 0 | 0 | 6 | 0% |

Converged at Pass 2. Fast convergence expected — the plan had already been through 3 chunk-level reviews.

## Disconfirmation Attempts

**F1 (team composition table):** Searched all 11 plan tasks for team composition placement. Task 3 Step 2 mentions "4 reviewers" and Task 6 Step 1 mentions "prefix table: AA, CE, CC, VR, SP, IE" — but neither places the full 6-row composition table. *Not disconfirmed.*

**F4 (boundary rule truncation):** Checked if the plan references spec lines 274-277 (it does), which would allow the implementer to read the full rule. However, the plan's stated purpose is eliminating spec re-reading. If the implementer reads spec lines, the truncation is moot — but so is the plan's value proposition. *Not disconfirmed on the plan's own terms.*

**F5 ("thin by remit"):** Checked if the concept is captured implicitly in domain briefs. Task 8's missions are scoped by defect class (not files), which embodies the principle. But the explicit phrasing is a memorable constraint for SKILL.md readers. *Partially disconfirmed — concept is implicit, phrasing is absent.*

**F6 (packet embedding prohibition):** Checked if the plan's positive instruction (use pointer) is sufficient. The scaffold template says "Read .review-workspace/preflight/packet.md" — which is a pointer, not embedded content. The implementer would naturally follow this pattern. But the spec explicitly prohibits embedding, suggesting the training prior for embedding is strong enough to warrant active prohibition. *Partially disconfirmed — instruction is positive-only but may suffice.*

**F7 ("not checklists"):** Checked if the plan's example domain briefs demonstrate the correct tone. They do — missions, collaboration playbooks, and disconfirmation checks are judgment-shaping, not checklist-style. But without the meta-instruction, a careless implementer might rewrite them as checklists. *Partially disconfirmed — examples demonstrate correct approach.*

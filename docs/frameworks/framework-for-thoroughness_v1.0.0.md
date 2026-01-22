# Framework for Thoroughness

A reusable framework for ensuring genuine completeness in tasks that require thoroughness (exploration, analysis, research, etc.)

## Protocol Header

| Field | Value |
| --- | --- |
| **Protocol ID** | `thoroughness.framework` |
| **Version** | `1.0.0` |
| **Role** | Shared guidance for Agent Skills (SKILL.md) that require thoroughness (analysis, exploration, auditing, research). |
| **See also** | `decision-making.framework@1.0.0` (use after this when selecting among options under trade-offs) |
| **Compatibility** | Within a **major** version, meanings of: the loop stages (DISCOVER/EXPLORE/VERIFY/REFINE), Entry/Exit gates, status markers, evidence levels, confidence levels, **Yield%**, stopping templates, and the required report sections are stable. Minor versions may add optional guidance/templates without changing existing meanings. |

## Contract (Normative Requirements)

The keywords **MUST**, **SHOULD**, and **MAY** are used as normative requirements.

### MUST

- **Run the Entry Gate** and record its outputs before doing substantive work.
- **Choose and use a coverage structure** (matrix/tree/graph/backlog) and track work items using the **Cell Schema** fields.
- **Assign Evidence + Confidence** to every finding, and obey the rule: *confidence can’t exceed evidence*.
- **Execute the loop** (DISCOVER → EXPLORE → VERIFY → REFINE) until the Exit Gate passes and the chosen stopping template(s) are satisfied.
- **Attempt disconfirmation** for all P0 dimensions/findings (scaled by thoroughness level).
- **Compute and report Yield%** at the end of each pass using the Yield% definition in this document (or a declared skill override).
- **Produce an output** that includes, at minimum, the sections in the **Thoroughness Report Template** (format may vary; required content may not).

### SHOULD

- Maintain an iteration log (pass-by-pass deltas + Yield%).
- Keep artifacts reproducible (file paths, commands run, links, and any relevant parameters).
- Recalibrate effort vs stakes each pass.
- Use diversity of methods for P0 items (e.g., read + grep + run) unless infeasible (document why).

### MAY

- Add domain-specific fields/checklists (e.g., threat models, performance budgets).
- Override: seed dimensions, independence criteria for “independent methods”, disconfirmation menus, and the **scope** of Yield% (e.g., include P2) — but any override MUST be declared in the Entry Gate.

## Principle

Thoroughness is **iterative, not linear**. You discover dimensions as you go, which triggers new exploration. This framework is a loop, not a checklist — but with explicit checkpoints to prevent one-pass theater.

## Relationship to Decision-Making Framework

This framework is optimized for **converging on what’s known vs unknown** (coverage + verification), not for selecting among options under trade-offs. If the goal is to choose a path once evidence and gaps are understood, hand off to the decision-making framework.

**Hand off to `decision-making.framework` when:**

- You can name 2+ plausible options (including “defer / do nothing”)
- The remaining unknowns are primarily about preference/trade-offs, not basic truth
- You need an explicit, defensible choice (with accepted sacrifices) rather than more exploration

**Outputs from this framework that should feed the decision record:**

- Dimensions + priorities (P0/P1) that define what “matters”
- Findings with Evidence/Confidence ratings (and linked artifacts)
- Information gaps and which ones are decision-relevant
- Disconfirmation attempts summary (what was tried; what was found)

## Entry Gate

Before starting, establish:

### Stakes Calibration Rubric (Recommended)

Use this to make **adequate / rigorous / exhaustive** more consistent across skills and tasks.

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High (need action) | Moderate | Low / no constraint |

**Rule of thumb:** If any two factors land in a higher column, choose that higher thoroughness level unless strong reasons are documented in the Entry Gate rationale.

| Aspect                   | Question                           | Output                                  |
| ------------------------ | ---------------------------------- | --------------------------------------- |
| **Assumption surfacing** | What am I taking for granted?      | List of explicit assumptions            |
| **Stakes assessment**    | How thorough does this need to be? | Level: adequate / rigorous / exhaustive |
| **Deliverable format**   | What output form?                  | Format + intended audience              |
| **Initial dimensions**   | What aspects might matter?         | Seed list (expect it to grow)           |
| **Dimension priority**   | Which dimensions matter most?      | Each dimension labeled P0 / P1 / P2     |
| **Effort boundaries**    | When is "enough"?                  | Stopping criteria template chosen       |

**Gate check:** Cannot proceed until assumptions listed, thoroughness level chosen, and stopping criteria template selected.

## The Thoroughness Loop

```
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
DISCOVER ──► EXPLORE ──► VERIFY ──► REFINE?
                                          │
                                    (new dimensions
                                     discovered?)
                                          │
                                     EXIT if no
```

## Choosing a Coverage Structure

Not all dimensions fit a matrix. Choose the structure that matches your domain:

| Dimension Relationship | Structure | When to Use |
|------------------------|-----------|-------------|
| Independent            | Matrix    | Dimensions don't overlap; cells are meaningful |
| Nested / Hierarchical  | Tree      | Dimensions contain sub-dimensions |
| Relational             | Graph     | Components have dependencies |
| Evolving / Unknown     | Backlog   | Dimensions discovered as you go |

**Anti-explosion rule:** If a matrix exceeds ~50 cells, switch to sparse tracking (backlog with tags, or tree structure).

## Evidence Levels

Every finding needs an evidence rating — not just a status marker.

| Level | Meaning | Example |
|-------|---------|---------|
| **E0** | Assertion only | "I believe X" |
| **E1** | Single source / single method | Read file, saw X |
| **E2** | Two independent methods | Read + grep confirmed; inspect + run |
| **E3** | Triangulated + disconfirmation | Multiple sources + actively tried to disprove |

**Minimum evidence by stakes:**
- Adequate: E1 for P0 dimensions
- Rigorous: E2 for P0, E1 for P1
- Exhaustive: E2 for all, E3 for P0

## Confidence Levels

Assign confidence to findings — not just status.

| Level | Meaning |
|-------|---------|
| **High** | Replicated / strongly supported; disconfirmation attempts failed |
| **Medium** | Supported but incomplete; some assumptions untested |
| **Low** | Plausible hypothesis; major gaps or contradictory signals |

**Rule:** Confidence can't exceed evidence. E0/E1 evidence caps confidence at Medium.

### DISCOVER: What should I look for?

You can't think your way to unknown unknowns — you must **import them from elsewhere**. Apply at least 3 of these techniques *(skills MAY override the minimum, but MUST declare the override at Entry Gate)*:

| Technique | Method | Output |
|-----------|--------|--------|
| **External taxonomy check** | Find established framework for this domain (STRIDE, OWASP, Porter's Five Forces, "-ilities"). Compare against your dimensions. | Missing dimensions from taxonomy |
| **Perspective multiplication** | List 3-5 stakeholders. For each: "What would they notice that I haven't?" | Stakeholder-specific dimensions |
| **Pre-mortem inversion** | Complete: "This analysis would be worthless if ___" (5+ completions) | Implicit assumptions as dimensions |
| **Historical pattern mining** | Search postmortems / lessons-learned in this domain. Extract dimensions that caused problems. | Historically-problematic dimensions |
| **Boundary perturbation** | For key parameters: 10x larger? 10x smaller? Zero? Sudden change? | Edge case dimensions |
| **Temporal expansion** | For each component: What changes at T+1 week, 3 months, 1 year, 3 years? | Time-dependent dimensions |

**Output:** Dimension list expanded beyond your initial mental model, each labeled P0/P1/P2

### EXPLORE: Cover each dimension

| Technique              | Description                                                            |
| ---------------------- | ---------------------------------------------------------------------- |
| **Coverage tracking**  | Matrix with cells marked: `[x]` done, `[~]` partial, `[ ]` not started |
| **Connection mapping** | After finding components, trace how they relate                         |
| **Source diversity**   | Multiple methods per finding (read + grep + run)                        |
| **Depth calibration**  | Surface/moderate/deep per dimension based on priority                  |

**Output:** Filled coverage matrix with evidence

### VERIFY: Check findings

| Technique            | Description                                                   |
| -------------------- | ------------------------------------------------------------- |
| **Cross-reference**  | Do findings from one area match findings from another?          |
| **Disconfirmation**   | Actively seek evidence that contradicts current understanding |
| **Assumption check** | Which initial assumptions were validated? Invalidated?        |
| **Gap scan**         | Any `[ ]` or `[?]` cells remaining?                           |

**Output:** Verified findings with confidence levels

### REFINE: Loop or exit?

After each pass, assess what changed:

**Continue iterating if any:**
- New dimensions were discovered
- Findings were significantly revised (not just refined)
- Coverage structure still has unresolved items (`[ ]` or `[?]`)
- Assumptions were invalidated that affect completed items

**Exit when all:**
- No new dimensions discovered in the last pass
- No significant revisions to findings
- All items resolved (`[x]`, `[-]`, or `[~]` with documented gaps)
- Yield% from last pass below threshold (see definition + table)

#### Yield% (Unambiguous Default)

Yield% measures how much **meaningfully new or revisionary** information emerged in the last pass. It is designed to detect **convergence**, not to reward routine completion of planned work.

##### Definitions

- **Pass:** one full loop iteration (DISCOVER → EXPLORE → VERIFY → REFINE).
- **Entity:** a tracked coverage item (matrix cell / backlog item / tree node / graph element) **or** a finding in your Findings list.
- **In-scope entities (default):** all entities whose effective priority is **P0 or P1**.
  - For coverage items, use their **Priority** field.
  - For findings, priority defaults to the **highest** priority among the dimensions/items the finding is linked to (P0 > P1 > P2), unless explicitly set.
- **Stable identity:** every entity MUST have a stable identifier across passes (e.g., `D3`, `I17`, `F2`). If an entity is renamed without an ID, treat it as “removed + new”.

##### Yield-impacting change types (counted)

An in-scope entity counts as **yielding** in the current pass if, compared to the previous pass, **any** of the following occurred:

1. **New:** the entity did not exist previously.
2. **Reopened:** status changed from resolved (`[x]` or `[-]`) → unresolved (`[~]`, `[ ]`, or `[?]`).
3. **Revised:** its core claim/conclusion changed (not just added detail) in a way that would change:
   - a decision, OR
   - a risk/severity assessment, OR
   - which dimensions/components are implicated.
4. **Escalated:** priority increased (P2→P1/P0 or P1→P0).

> **Not counted by default:** routine completion of planned work (e.g., `[ ]` → `[x]`, or adding detail that doesn’t change a conclusion).

##### Calculation

Let:

- `E_prev` = set of in-scope entities at the **end of the previous pass**
- `E_cur`  = set of in-scope entities at the **end of the current pass**
- `U = E_prev ∪ E_cur` (union)
- `Y` = subset of `U` that are yielding this pass (per rules above)

Then:

**Yield% = ( |Y| / max(1, |U|) ) × 100**

##### Pass 1 special case

For pass 1 (no prior snapshot), define **Yield% = 100**.

##### Skill overrides

A skill MAY override the **scope** of Yield% (e.g., include P2, exclude findings), but MUST declare the override (definition + rationale) in the Entry Gate.

| Level | Yield Threshold | Stability Requirement |
|-------|-----------------|----------------------|
| Adequate | <20% from last pass | Dimensions stable for 1 pass |
| Rigorous | <10% from last pass | Dimensions + findings stable |
| Exhaustive | <5% from last pass | Stable 2 passes + disconfirmation yielded nothing |

**Note:** There is no minimum iteration count. A simple problem might converge in 2 passes; a complex one might take 5. The criterion is convergence, not count.

## Throughout Practices

These apply at every stage, not just one phase:

| Practice                 | Description                                          |
| ------------------------ | ---------------------------------------------------- |
| **Meta-thoroughness**    | "Am I being thorough about being thorough?"          |
| **Assumption vigilance** | Continuously surface new assumptions as they appear  |
| **Documentation**        | Capture process, not just findings (reproducibility)  |
| **Calibration checks**   | Is effort proportional to stakes?                    |

## Exit Gate

| Criterion                     | Check                                                              |
| ----------------------------- | ------------------------------------------------------------------ |
| **Coverage complete**         | No `[ ]` or `[?]`. All items are `[x]`, `[-]` (with rationale), or `[~]` with documented gaps |
| **Connections mapped**        | Document connections at a depth proportional to level (see below) |
| **Disconfirmation attempted** | Actively tried to find what was missed                             |
| **Assumptions resolved**      | Each verified, invalidated, or flagged as unverified               |
| **Convergence reached**       | Last pass below yield threshold for chosen thoroughness level      |
| **Stopping criteria met**     | Chosen template satisfied (see below)                              |

### Connections Mapped — By Level (Recommended)

- **Adequate:** list key dependencies and 1–2 plausible failure propagation paths (bullet list is fine).
- **Rigorous:** map primary dependencies and main failure propagation paths (table or short causal chain).
- **Exhaustive:** produce a dependency graph or explicit causal chain for the full in-scope system.

### Stopping Criteria Templates

Choose 1-2 at Entry Gate:

| Template | Stop When |
|----------|-----------|
| **Risk-based** | All P0 dimensions are `[x]` with ≥E2 evidence |
| **Discovery-based** | Two consecutive loops with no new P0/P1 findings |
| **Decision-based** | Remaining unknowns don't change the decision (document why) |

**Gate check:** Cannot claim "done" until all criteria pass and chosen stopping template is satisfied.

## Thoroughness Levels

| Level          | When to use                           | Yield Threshold | Evidence Required | Disconfirmation |
| -------------- | ------------------------------------- | --------------- | ----------------- | --------------- |
| **Adequate**   | Low stakes, reversible                | <20%            | E1 for P0         | Light           |
| **Rigorous**   | Medium stakes, moderate cost of error | <10%            | E2 for P0, E1 for P1 | Active       |
| **Exhaustive** | High stakes, costly/irreversible      | <5%             | E2 all, E3 for P0 | Aggressive      |

## Failure Modes

| Failure Mode        | Signal                                  | Countermeasure                               |
| ------------------- | --------------------------------------- | -------------------------------------------- |
| One-pass theater    | "I did the loop once, it converged"     | Check yield threshold actually met; require iteration documentation |
| Checkbox mentality  | Items marked `[x]` without evidence     | Cell schema requires E0-E3 rating with artifacts |
| Premature exit      | "Good enough" without checking criteria | Exit gate + stopping criteria template mandatory |
| Dimension blindness | Same dimensions every time              | Apply ≥3 DISCOVER techniques; import external structure |
| False confidence    | All findings equally certain            | Confidence can't exceed evidence level       |
| Analysis paralysis  | Endless refinement, no decision         | Output must include decidable vs. undecidable |

## Cell Schema

For each tracked item (matrix cell, backlog item, tree node), record:

| Field | Required | Values |
|-------|----------|--------|
| **ID** | Yes | Stable identifier (e.g., `D3`, `I17`, `F2`) |
| **Status** | Yes | `[x]` `[~]` `[-]` `[ ]` `[?]` |
| **Priority** | Yes | P0 / P1 / P2 |
| **Evidence** | Yes | E0 / E1 / E2 / E3 |
| **Confidence** | Yes | High / Med / Low |
| **Artifacts** | If applicable | Links, commands run, docs reviewed |
| **Notes** | If applicable | What's missing, next action |

This schema makes checkbox mentality harder — you can't just mark `[x]` without showing your work.

### Using `[~]` (Partially Explored) Without Cheating

`[~]` is allowed only when **all** are true:

- The remaining gap is **bounded** (what’s missing is specific, not open-ended).
- The impact of the gap is **low or acceptable** at the chosen thoroughness level.
- The gap is carried into **Exit Gate → Remaining documented gaps** with a next-check or rationale for deferral.

## Thoroughness Report Template

Use this template (or an equivalent structure) for any output produced under this framework.

- Skills MAY add domain-specific sections.
- Skills SHOULD keep these section headings and their intent intact so outputs remain comparable across skills.

```markdown
# [Task / Report Title]

## Context
- Protocol: thoroughness.framework@1.0.0
- Audience:
- Scope / goal:
- Constraints (time, tools, access):

## Entry Gate
### Assumptions
- A1:
- A2:

### Stakes / Thoroughness level
- Level: adequate / rigorous / exhaustive
- Rationale:

### Stopping criteria template(s)
- Selected: risk-based / discovery-based / decision-based / ...
- Notes:

### Initial dimensions (seed) + priorities
- P0:
- P1:
- P2:

### Coverage structure
- Chosen: matrix / tree / graph / backlog
- Rationale:
- Any declared overrides (Yield% scope, independence ladder, etc.):

## Coverage Tracker
- Structure type:
- Tracked items (use Cell Schema fields; include stable IDs)

## Iteration Log
| Pass | New entities | Reopened entities | Revised entities | Escalations | Yield% | Notes |
|------|--------------|-------------------|-----------------|------------|--------|------|

## Findings
- F1 (Priority: P0, Evidence: E2, Confidence: Medium)
  - Claim:
  - Linked dimensions/items:
  - Artifacts:
  - Gaps / next checks:

## Disconfirmation Attempts
- Attempt 1:
  - What would disprove the current model:
  - How tested:
  - Result:

## Decidable vs Undecidable
- Decide now:
- Can't decide yet:
- What would change the decision:

## Exit Gate
- Coverage complete:
- Connections mapped:
- Disconfirmation attempted:
- Assumptions resolved:
- Convergence reached (Yield% vs threshold):
- Stopping criteria met:
- Remaining documented gaps (if any):

## Appendix (optional)
- Commands run
- File links
- Data extracts
```

## Coverage Matrix Template

```markdown
## [Domain] Coverage Matrix

### [Dimension A] × [Dimension B]

|        | B1  | B2  | B3  | B4  |
| ------ | --- | --- | --- | --- |
| **A1** | [ ] | [ ] | [ ] | [ ] |
| **A2** | [ ] | [ ] | [ ] | [ ] |
| **A3** | [ ] | [ ] | [ ] | [ ] |

### Cross-Cutting Concerns

| Concern     | Status | Notes |
| ----------- | ------ | ----- |
| [Concern 1] | [ ]    |       |
| [Concern 2] | [ ]    |       |

### Status Markers

| Marker | Meaning                                  |
| ------ | ---------------------------------------- |
| `[x]`  | Fully explored with evidence             |
| `[~]`  | Partially explored (note what's missing) |
| `[-]`  | Not applicable (with rationale)          |
| `[ ]`  | Not yet explored                         |
| `[?]`  | Unknown if applicable                    |
```

## Avoiding Analysis Paralysis

Thoroughness is a tool for *better decisions*, not a substitute for deciding.

**Every output must include:**
- What we can decide now
- What we can't decide yet
- What new information would change the decision

If thoroughness is being used to delay decisions indefinitely, the framework is being misused. The goal is confidence-appropriate action, not infinite certainty.

## Disconfirmation Menu (Recommended)

For each P0 dimension/finding, pick one or more:

- **Counterexample search:** try to find a case that breaks the current claim.
- **Alternative hypothesis:** write the strongest competing explanation and test it.
- **Adversarial read:** look for reasons the evidence could be misleading (selection bias, missing context).
- **Negative test:** run a check expected to fail if the model is wrong.
- **Cross-check:** verify via an independent method (e.g., read + search + run).

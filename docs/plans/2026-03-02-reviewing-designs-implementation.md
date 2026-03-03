# Reviewing-Designs Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the reviewing-designs skill redesign — add early adversarial gate (AHG-5), bridge table, and dialogue-first interaction with delta cards.

**Architecture:** Keep the existing dimensional engine (D1-D19, Yield%, evidence levels, adversarial lenses A1-A9). Add three mechanisms: (1) early adversarial gate that produces testable hypotheses before the dimensional loop, (2) bridge table that carries hypotheses through the loop, (3) dialogue-first interaction via 3 delta cards at checkpoints instead of artifact-first output. Bridge operations, delta card schema, and alternatives detail are extracted to a reference doc to manage SKILL.md line budget.

**Tech Stack:** Markdown skill files. No code, no tests — verification via line counts, link checks, and consistency audits.

**Design doc:** `docs/plans/2026-03-02-reviewing-designs-redesign.md` (276 lines, Codex-reviewed)

**Line budget:** SKILL.md at 471 lines. Projected after changes: ~575 lines. The 500-line soft target (`.claude/rules/skills.md:114`) is exceeded by ~75 lines. This is an accepted trade-off — the redesign adds three validated mechanisms (early gate, bridge, delta cards) plus framework boundary rules that address four user concerns and ensure formal framework compliance. Further extraction to reference docs would split core flow logic across files, hurting usability during review execution.

**Files changed:**
- Create: `.claude/skills/reviewing-designs/references/bridge-and-checkpoints.md`
- Modify: `.claude/skills/reviewing-designs/SKILL.md`
- Modify: `.claude/skills/reviewing-designs/references/examples.md`
- Modify: `.claude/skills/reviewing-designs/references/dimensions-and-troubleshooting.md`

---

### Task 1: Create bridge-and-checkpoints reference doc

**Files:**
- Create: `.claude/skills/reviewing-designs/references/bridge-and-checkpoints.md`

**Step 1: Write the reference file**

Write the following complete file content:

````markdown
# Bridge & Checkpoints Reference

Supporting reference for the [reviewing-designs](../SKILL.md) skill.

## How to Use This File

- **During AHG-5:** Overflow ranking detail is here (core questions and hard-fail rules are in SKILL.md)
- **During checkpoints:** Delta card schema and example are here
- **During loop:** Bridge operations for modifying rows at checkpoints are here
- **Core process lives in SKILL.md** — this file is operational reference only

---

## Bridge Operations

Available at checkpoints to modify bridge rows.

| Operation | Available at | Effect |
|-----------|-------------|--------|
| ADD | Checkpoints 1-2 | New hypothesis from user input or dimensional findings |
| REVISE | Checkpoints 1-2 | Update hypothesis text or retarget dimensions. Audit: record old → new |
| WITHDRAW | Checkpoints 1-3 | Remove hypothesis with rationale (e.g., N/A target, premise invalidated) |
| REOPEN | Checkpoint 3 only | Reopen a tested/disconfirmed row if new evidence contradicts disposition. Triggers another loop pass |

**Checkpoint scoping:**

- Checkpoint 1: full operations (ADD/REVISE/WITHDRAW) — user can correct hypotheses based on context the reviewer missed
- Checkpoint 2: full operations — dimensional findings may invalidate or strengthen hypotheses
- Checkpoint 3: REOPEN only — if adversarial pass contradicts a prior disposition, the row reopens and forces another pass

**REOPEN semantics:**

- A REOPEN triggers exactly one reconciliation loop pass
- During that pass, new D/F entities from dimensional checks on the reopened hypothesis enter Yield% scope normally
- If the reconciliation pass triggers normal REFINE continuation conditions (new dimensions, Yield% above threshold), the loop continues per standard REFINE rules
- If the iteration cap has been reached, REOPEN overrides for exactly one reconciliation pass; after that pass, the cap reasserts
- Reopened rows requiring adversarial re-validation: only relevant lenses re-check the specific reopened rows, not a full 9-lens re-pass

## Alternative Row Schema

| Field | Content |
|-------|---------|
| ID | ALT1-ALT2 |
| Alternative | From early gate Q2 |
| Anchor | Design location |
| Status | open / evaluated / withdrawn |
| Disposition | Dominance check result or withdrawal rationale |

## Alternatives Dominance Check

Runs at checkpoint 2, optional re-check at checkpoint 3.

Decision tree:

- Clearly not dominant → "not dominant — {reason}" → `evaluated`
- Possibly dominant → "unresolved — escalate to /making-recommendations" → `evaluated`
- Clearly dominant → P0 finding: "Alternative ALT-N dominates current design on {criteria}" → `evaluated`

Reviewing-designs identifies the question; making-recommendations answers it.

**ALT → F-code rule:** When an ALT row moves to `evaluated` with "unresolved — escalate," create a corresponding F-code finding (e.g., F-ALT1) in the coverage tracker at P1 priority. This ensures the unresolved decision risk enters Yield% scope and the artifact's Decidable/Undecidable section.

**Integration rules:**

- Dominance check runs only on concrete alternatives; placeholder rows (CONSTRAINED, NONE IDENTIFIED) → `withdrawn` with rationale
- Deferred-ALT promotion must happen by checkpoint 2 via REVISE (not ADD at checkpoint 3)
- A6 (Steelman Alternatives) fallback: constrained case tests constraint validity; unconstrained case treats as framing challenge
- Q2 constrained zero-alt counts as explicit Q2 outcome (not silent skip)

## Anchor Field

Two-level evidence chain:

- **At creation (early gate):** design-level citation (e.g., "Section 3.2, decision rules")
- **At resolution (EXPLORE/VERIFY):** code-level citation added to disposition (e.g., "confirmed — D4 found 3 missing thresholds at lines 301, 505, 309")

AHG-5 hypotheses are framing-level claims — they don't need code citations at creation time.

## N/A Dimension Targeting

If a hypothesis targets a dimension that gets marked N/A:

1. Retarget once to the nearest applicable dimension
2. If no applicable dimension exists, WITHDRAW with rationale citing why the hypothesis premise no longer applies

## Status-Specific Disposition Requirements

Override the generic disposition invariant ("evidence or rationale") with status-specific evidence requirements:

| Status | Required evidence | Minimum quality |
|--------|------------------|----------------|
| `tested` | Finding ID(s) from target dimension checks | At least one finding at E1+ (single source with citation) |
| `disconfirmed` | Counter-evidence from target dimension checks | Specific citation showing hypothesis does not hold |
| `evaluated` (ALT) | Dominance check result | Decision tree outcome with rationale |
| `withdrawn` | Rationale | One-sentence justification citing invalidated premise |

These take precedence over the generic invariant. A formulaic `tested` disposition backed only by an E0 assertion (no citation) does not satisfy this requirement.

**Terminology note:** "Disconfirmation" means different things in the framework and bridge:

- **Framework:** Obligation to attempt disconfirmation of P0 findings (MUST requirement — applied to D-codes and F-codes)
- **Bridge:** Status meaning "hypothesis not supported by evidence" (applied to H-codes)

These are independent obligations. A `disconfirmed` H-row does not satisfy the framework's P0 disconfirmation MUST.

## Overflow Ranking

When more hypotheses emerge than the stakes-level count allows:

- **Rank by:** impact × plausibility × testability
- **Top N:** become bridge H-rows (N = stakes-level count)
- **Remainder:** go in "deferred hypotheses" footnote (not bridge-tracked, preserved for reference)

**Promotion-on-slot-open:** When a bridge slot opens via WITHDRAW, promote the highest-ranked deferred hypothesis into the vacated slot via REVISE at the current checkpoint. This prevents high-signal deferred items from being permanently lost. Promotion must happen by checkpoint 2 — no promotions at checkpoint 3 (only REOPEN is available).

## ALT Overflow

When Q2 surfaces more or fewer than 2 alternatives:

| Case | ALT1 | ALT2 | Action |
|------|------|------|--------|
| 0 alternatives, constrained space | CONSTRAINED:\<source\> | N/A | No framing flag. Gate: external source + single viable now |
| 0 alternatives, unconstrained | NONE IDENTIFIED | N/A | Flag framing risk |
| 1 alternative | \<alternative\> | NONE IDENTIFIED | — |
| 3+ alternatives | Top by impact × plausibility × testability | Second by ranking | Remainder in "deferred ALT" list |

## Delta Card Schema

Shared across all 3 checkpoints:

| Field | Content |
|-------|---------|
| **Checkpoint** | Which checkpoint (1/2/3) + context (e.g., "Dimensional loop converged, 3 passes, Yield% 9%") |
| **What changed** | Summary of work since last card |
| **Bridge updates** | Status changes on H-rows and ALT-rows with dispositions |
| **Net-new findings** | Findings not traceable to bridge hypotheses, with dimension links |
| **Current totals** | Running P0/P1/P2 counts |
| **Reviewer ask** | Specific question or "proceed?" (checkpoint 3: informational, no ask) |

### Example (Checkpoint 2)

```
**Checkpoint 2: Dimensional loop converged** (3 passes, Yield% 9%)

What changed: EXPLORE checked D4-D19 across 3 passes. Yield% dropped from 30% (pass 2) to 9% (pass 3).

Bridge updates:
- H3 (decision-points underspecified) → TESTED: 3 P0 instances (classify threshold, preflight state, create autonomy stage) [D4]
- H5 (session_id load-bearing) → TESTED: P0 — delivery mechanism fragile [D9, Anchor: §4.3 session_id delivery]
- ALT1 (Architecture F) → EVALUATED: not dominant — lacks autonomy enforcement for agent-initiated creates

Net-new findings:
- P0-4: Error codes vs machine states mismatch [D12]
- P0-6: Example ticket missing contract_version [D15]

Current totals: P0: 6 | P1: 10 | P2: 4

Anything to dig deeper on before the adversarial pass?
```

### Artifact Assembly

The artifact (`docs/audits/...`) compiles all 3 delta cards in checkpoint order, followed by the full coverage tracker and iteration log. The delta cards become the Findings section. This is deterministic — no additional synthesis step needed.
````

**Step 2: Verify file structure**

Run: `wc -l .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md`
Expected: ~145 lines

Run: `grep -c "^##" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md`
Expected: 10 section headers

Run: `grep "REOPEN semantics" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md`
Expected: 1 match

Run: `grep "Status-Specific Disposition" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md`
Expected: 1 match

Run: `grep "F-code rule" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md`
Expected: 1 match

**Step 3: Commit**

```
git add .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md
git commit -m "feat(reviewing-designs): add bridge & checkpoints reference doc

Extracts bridge operations (ADD/REVISE/WITHDRAW/REOPEN), alternative row
schema, dominance check protocol, delta card schema with example, anchor
field detail, N/A targeting, and overflow ranking into a reference file.
Keeps SKILL.md focused on core flow."
```

---

### Task 2: Update SKILL.md top sections (frontmatter, Overview, Outputs)

**Files:**
- Modify: `.claude/skills/reviewing-designs/SKILL.md`

Three edits in this task, all in the top portion of the file (lines 1-86). Work top-to-bottom.

**Step 1: Update frontmatter description**

Find the `description:` line in the YAML frontmatter (line 3). Replace:

```
description: Iterative design review using the Framework for Thoroughness. Use when verifying a design captures all requirements from sources. Use after creating specs from multiple documents. Use before implementing from a design. Use when past designs have led to implementation surprises.
```

With:

```
description: Iterative design review using the Framework for Thoroughness. Use when verifying a design captures all requirements from sources. Use after creating specs from multiple documents. Use before implementing from a design. Use when past designs have led to implementation surprises. Use when questioning whether a design solves the right problem.
```

**Step 2: Replace Overview section**

**Preflight:** Run `grep -c '## Overview' .claude/skills/reviewing-designs/SKILL.md` — expect 1. If 0, stop — file structure may have changed. If section boundaries have shifted, locate `## Overview` and `## When to Use` manually and replace everything between them.

Replace the entire Overview section (from `## Overview` through `**Core insight:** The items most often missed are single sentences that define behavior at decision points.`) with:

```markdown
## Overview

Design review catches issues before implementation, when they're cheap to fix. This skill addresses four concerns:

1. **Intent alignment** — Does the design solve the right problem?
2. **Blind spot surfacing** — What assumptions hasn't the designer questioned?
3. **Conversational sharpening** — Value is in back-and-forth dialogue, not compliance reports
4. **Optimality** — Is this the best design for its purpose, not just the first workable approach?

Existing dimensions D1-D3 (Source Coverage) and D7-D11 (Implementation Readiness) remain fully active — the redesign adds concerns #1-#4, not replaces the dimensional engine.

An early adversarial gate (AHG-5) surfaces framing problems and load-bearing assumptions as testable hypotheses. A bridge table carries those hypotheses through the dimensional loop, preventing "generate-then-forget." Three dialogue checkpoints (delta cards) make the conversation the primary output.

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness_v1.0.0.md)
**Default thoroughness:** Rigorous

**Process flow:**

~~~
Entry Gate → AHG-5 Early Gate → Bridge Table
  ↓ [delta card #1]
DISCOVER → EXPLORE → VERIFY → REFINE loop
  ↓ [delta card #2]
Adversarial Pass (A1-A9)
  ↓ [delta card #3]
Exit Gate → Artifact
~~~
```

**Step 3: Replace Outputs section**

**Preflight:** Run `grep -c '## Outputs' .claude/skills/reviewing-designs/SKILL.md` — expect 1. If 0, stop — file structure may have changed. Locate `## Outputs` and `## Process` (or `### Entry Gate`) manually and replace everything between them.

Replace the entire Outputs section (from `## Outputs` through the Definition of Done closing `- [ ] Chat contains brief summary only`) with:

```markdown
## Outputs

**Interaction model:** Dialogue-first with 3 delta cards in chat. Artifact compiles all cards + full coverage tracker.

### Delta Card Checkpoints

| # | When | Contents | User can... |
|---|------|----------|-------------|
| 1 | After early gate | Hypotheses, alternatives, bridge table | Add context, ADD/REVISE/WITHDRAW bridge rows, confirm |
| 2 | After loop convergence | Bridge dispositions, net-new findings, running P0/P1/P2 totals, ALT dominance results | Redirect, modify bridge rows, ask to dig deeper |
| 3 | After adversarial pass | Final bridge table, adversarial findings (bridge-mapped + NET-NEW), overall assessment | Informational closeout. REOPEN only if adversarial findings contradict a disposition |

Checkpoints are invitations, not gates. If the user says nothing, the review proceeds.

**Delta card format:** See [Bridge & Checkpoints Reference](references/bridge-and-checkpoints.md#delta-card-schema).

**Artifact:** `docs/audits/YYYY-MM-DD-<design-name>-review.md`

Compiles all 3 delta cards in checkpoint order, followed by full coverage tracker and iteration log. Same format as before — delivery order changes.

**Summary table (top of artifact and in delta card #3):**

| Priority | Count | Description                                |
| -------- | ----- | ------------------------------------------ |
| P0       | N     | Issues that break correctness or execution |
| P1       | N     | Issues that degrade quality                |
| P2       | N     | Polish items                               |

**Definition of Done:**

- [ ] Entry Gate completed and recorded
- [ ] AHG-5 early gate completed; bridge table populated
- [ ] Delta card #1 presented; if user responded, input incorporated (or no-response noted)
- [ ] All dimensions explored with Evidence/Confidence ratings
- [ ] Yield% below threshold for thoroughness level
- [ ] Delta card #2 presented; if user responded, input incorporated (or no-response noted)
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Adversarial pass completed (bridge-first, then NET-NEW)
- [ ] Bridge table complete (no open rows; disposition invariant satisfied)
- [ ] Delta card #3 presented
- [ ] Exit Gate criteria satisfied
- [ ] Artifact compiled from delta cards + coverage tracker
```

**Step 4: Verify changes**

Run: `grep "Intent alignment" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "Delta Card Checkpoints" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "bridge-and-checkpoints.md" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "right problem" .claude/skills/reviewing-designs/SKILL.md`
Expected: 2 matches (description + overview)

**Step 5: Commit**

```
git add .claude/skills/reviewing-designs/SKILL.md
git commit -m "feat(reviewing-designs): update overview and outputs for redesign

Overview: 4 concerns (intent alignment, blind spots, conversational sharpening, optimality) + process flow.
Outputs: dialogue-first with 3 delta card checkpoints replacing artifact-first.
Definition of Done: updated for AHG-5, bridge, and delta cards."
```

---

### Task 3: Insert AHG-5 and Bridge Table sections

**Files:**
- Modify: `.claude/skills/reviewing-designs/SKILL.md`

Two new sections inserted between Entry Gate and The Review Loop.

**Step 1: Insert AHG-5 section**

After the Entry Gate section (after the line `Document assumptions, stakes level, and stopping criteria before proceeding.`), and before `### The Review Loop`, insert:

```markdown

### Early Adversarial Gate (AHG-5)

**YOU MUST** complete AHG-5 after Entry Gate, before DISCOVER.

Five questions that surface framing problems, load-bearing assumptions, and systemic patterns before the dimensional loop.

| # | Question | Catches |
|---|---------|---------|
| Q1 | What problem is this solving, and what's the strongest argument it's the wrong problem? | Intent misalignment, over-scoping |
| Q2 | What alternatives were considered, and what would make a rejected alternative better than this? | Anchoring, pre-narrowed framing, motivated reasoning |
| Q3 | What would make this fail in implementation? Name specific mechanisms, not categories. | Systematically underspecified behavior, load-bearing gaps |
| Q4 | Where is complexity underestimated? What looks simple but isn't? | Hidden state spaces, edge case surfaces, interaction effects |
| Q5 | What single assumption, if wrong, would invalidate the whole design? | Load-bearing assumptions, fragile dependencies |

**Stakes gating:**

| Stakes | Questions | Hypothesis count | Bridge rows |
|--------|-----------|-----------------|-------------|
| Adequate | AHG-lite: Q1, Q3, Q5 only | Exactly 2 | H1-H2 + ALT1-ALT2 |
| Rigorous | Full AHG-5 | Exactly 3 | H1-H3 + ALT1-ALT2 |
| Exhaustive | Full AHG-5 | Exactly 4 | H1-H4 + ALT1-ALT2 |

No skip path — skipping recreates the N/A rationalization anti-pattern.

**Hard fail rules** (per run question):

- Each run question produces a hypothesis OR explicit "no finding" with one-sentence justification
- Q3 must name specific mechanisms, not categories
- Q5 must identify one assumption and state what breaks if it's wrong
- All run questions producing "no finding" → flag: "Early gate produced zero hypotheses — verify genuine engagement before proceeding."

**Overflow:** Rank surplus hypotheses by impact × plausibility × testability. Top N become bridge rows; remainder go in "deferred hypotheses" footnote. See [Bridge & Checkpoints Reference](references/bridge-and-checkpoints.md#overflow-ranking).

**Output:** Populate bridge table with H-rows and ALT-rows. Present delta card #1 in chat.
```

**Step 2: Insert Bridge Table section**

Immediately after the AHG-5 section (after `**Output:** Populate bridge table with H-rows and ALT-rows. Present delta card #1 in chat.`) and before `### The Review Loop`, insert:

```markdown

### Bridge Table

Carries early-gate hypotheses into the dimensional loop. Prevents "generate-then-forget."

**Hypothesis row schema:**

| Field | Content |
|-------|---------|
| ID | H1-H*N* (N = stakes-level count: 2/3/4) |
| Hypothesis | From early gate question |
| Target Dimensions | D-codes and/or A-codes to check |
| Anchor | Design location (section, line range, or structural element) |
| Status | open / tested / disconfirmed / evaluated (ALT rows) / withdrawn |
| Disposition | Finding IDs, disconfirmation evidence, or withdrawal rationale |

**Status values:**

| Status | Meaning | Required disposition |
|--------|---------|---------------------|
| `open` | Not yet checked | — |
| `tested` | Hypothesis confirmed by target dimension check | Finding ID + evidence |
| `disconfirmed` | Hypothesis not supported by target dimension check | Counter-evidence + rationale |
| `evaluated` | ALT row: dominance check completed | Check result + rationale |
| `withdrawn` | Hypothesis no longer applicable | Rationale citing why premise no longer applies |

**Disposition invariant:** Every non-`open` row must include disposition text, evidence or rationale, and audit entry (when/checkpoint + why + prior status).

**Lifecycle:** Rows added after early gate as `open` → status transitions via bridge operations at checkpoints → at Exit Gate, no `open` rows allowed.

**Framework relationship:** The bridge table is a parallel tracking structure alongside the Cell Schema coverage tracker — not an extension of it. Cell Schema tracks D-codes and F-codes with `[x]`/`[~]`/`[-]` statuses and E0-E3 evidence levels. The bridge tracks H-codes and ALT-codes with `open`/`tested`/`disconfirmed` statuses. Linkage is via: Target Dimensions (H→D mapping), Disposition (H→F finding IDs), and Anchor (design location). Both must be complete at Exit Gate.

**Referential integrity:** Every `tested` H-row must reference at least one D-code or F-code finding. Every `disconfirmed` H-row must reference the dimensional check that produced counter-evidence. If a referenced D-code is later revised or removed, update the H-row disposition accordingly.

**Operations, alternatives, and dominance checks:** See [Bridge & Checkpoints Reference](references/bridge-and-checkpoints.md).
```

**Step 3: Insert Framework Boundary Rules section**

Immediately after the Bridge Table section (after `**Operations, alternatives, and dominance checks:** See [Bridge & Checkpoints Reference](references/bridge-and-checkpoints.md).`) and before `### The Review Loop`, insert:

```markdown

### Framework Boundary Rules

The bridge table and AHG-5 layer on top of the [thoroughness framework](references/framework-for-thoroughness_v1.0.0.md). These rules govern the boundary between framework-owned semantics and skill-local additions.

| # | Rule | What it governs |
|---|------|----------------|
| B1 | **Entry Gate declares Yield% scope:** H-codes and ALT-codes are excluded from Yield% tracking. Declare per-run in Entry Gate output: "Yield% scope: D-codes and F-codes only. H-codes are bridge scaffolding." | Yield% formula scope (framework MAY clause) |
| B2 | **Bridge is a parallel tracker:** The bridge table operates alongside the Cell Schema coverage tracker, not inside it. Different ID namespaces (H/ALT vs D/F), different status vocabularies, different evidence models. | Structural relationship |
| B3 | **Referential integrity:** Every `tested` H-row references ≥1 D/F finding. Every `disconfirmed` H-row references the counter-evidence source. If a referenced finding is revised or removed, update the H-row disposition. | Cross-tracker linkage |
| B4 | **Status-specific evidence:** `tested` requires E1+ evidence (not bare assertion). `disconfirmed` requires specific counter-citation. See [Status-Specific Disposition Requirements](references/bridge-and-checkpoints.md#status-specific-disposition-requirements). | Disposition quality |
| B5 | **REOPEN propagates D/F entities:** A REOPEN triggers one reconciliation pass. New D/F entities enter Yield% scope normally. See [REOPEN semantics](references/bridge-and-checkpoints.md#reopen-semantics). | Loop re-entry mechanics |
| B6 | **Unresolved ALT dominance creates F-code:** When an ALT row is `evaluated` with "unresolved — escalate," a corresponding F-code finding enters the coverage tracker at P1. | Decision risk tracking |

These rules are the boundary contract between the framework and the skill's additions. Violations indicate a gap in the bridge-to-framework interface, not a framework bug.

**Disconfirmation disambiguation:** "Disconfirmation" means different things in the two systems. Framework: obligation to attempt disconfirmation of P0 findings (applied to D/F-codes). Bridge: status meaning "hypothesis not supported" (applied to H-codes). These are independent — a `disconfirmed` H-row does not satisfy the framework's P0 disconfirmation MUST.
```

**Step 4: Verify insertions**

Run: `grep "Early Adversarial Gate" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "Bridge Table" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match (the section header; "bridge table" lowercase may appear more)

Run: `grep "Q3 must name specific mechanisms" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "Disposition invariant" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "Framework Boundary Rules" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "B1\|B2\|B3\|B4\|B5\|B6" .claude/skills/reviewing-designs/SKILL.md`
Expected: 6 matches (one per boundary rule)

Run: `grep "Disconfirmation disambiguation" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Verify section ordering: `grep "^### " .claude/skills/reviewing-designs/SKILL.md`
Expected order includes: ...Entry Gate, Early Adversarial Gate (AHG-5), Bridge Table, Framework Boundary Rules, The Review Loop...

**Step 5: Commit**

```
git add .claude/skills/reviewing-designs/SKILL.md
git commit -m "feat(reviewing-designs): add AHG-5, bridge table, and boundary rules

AHG-5: 5 adversarial questions, stakes-gated hypothesis count (2/3/4),
hard fail rules per run question, overflow ranking.
Bridge: hypothesis row schema, 5 status values, disposition invariant,
lifecycle, overlay declaration, referential integrity.
Boundary rules: 6 rules (B1-B6) governing framework-bridge interface.
Detail in reference doc."
```

---

### Task 4: Update SKILL.md existing sections (REFINE, Adversarial, Exit Gate, Decision Points, Anti-Patterns)

**Files:**
- Modify: `.claude/skills/reviewing-designs/SKILL.md`

Five small edits across the bottom half of SKILL.md.

**Step 1: Add H-code exclusion note to REFINE**

After the `**Effective priority:**` paragraph (which ends with `...to exclude them from Yield% scope.)`) and before the Yield% formula (`Yield% = ( |Y| / max(1, |U|) ) × 100`), insert:

```markdown

**H-code exclusion:** Bridge table H-codes are scaffolding — not Yield-tracked entities. Only D-codes and F-codes enter E_prev/E_cur. Bridge completion is an independent exit criterion checked at Exit Gate. **Entry Gate declaration (B1):** Include in Entry Gate output: "Yield% scope: D-codes and F-codes only. H-codes are bridge scaffolding." (Per framework MAY clause — scope overrides must be declared at Entry Gate.)
```

**Step 2: Add AHG-5 overlap handling to Adversarial Pass**

After the `**Completion schema:**` paragraph (which ends with `...matches the stakes requirement below.`) and before `**Minimum depth by stakes:**`, insert:

```markdown

**AHG-5 overlap:** Lenses A1, A6, A7, and A8 overlap with AHG-5 questions. To prevent duplicate findings:

1. Evaluate mapped bridge rows first (e.g., A1 checks H-rows before generating new findings)
2. Findings that extend or confirm bridge hypotheses link to the existing H-code
3. Genuinely new findings are marked **NET-NEW** with one-sentence justification of why the early gate didn't catch them
```

**Step 3: Add bridge completion criterion to Exit Gate**

In the Exit Gate criteria table, after the row for `Adversarial pass complete`, add a new row:

```
| Bridge complete           | No `open` rows; all non-open rows satisfy disposition invariant (text + evidence + audit entry) |
```

In the post-completion self-check list, after `- [ ] Adversarial: required lens count met for stakes; pre-mortem produced specific, plausible failure story`, add:

```
- [ ] Bridge: all rows resolved; disposition invariant satisfied for every non-open row
```

**Step 4: Add early-gate decision point**

After the "Adversarial pass finds fundamental flaw" decision point block (ending with `- Note in summary: "Design may need fundamental rethinking"`), insert:

```markdown

**Early gate produces zero hypotheses:**

- All run questions produced "no finding" → verify genuine engagement
- Self-check: "Did I approach this with adversarial intent, or assume the design was fine?"
- If still zero after genuine effort → note in delta card #1 that early gate found no framing issues
```

**Step 5: Update "User pressure to skip steps" decision point**

In the "User pressure to skip steps" block, replace:

```
- "Skipping [Entry Gate/Adversarial Pass/etc.] risks missing issues that surface during implementation."
```

With:

```
- "Skipping [Entry Gate/AHG-5/Adversarial Pass/etc.] risks missing issues that surface during implementation."
```

**Step 6: Add early gate anti-pattern to memorize list**

In the Anti-Patterns section, after the existing "memorize these" bullet for skipping Document Quality dimensions, add:

```markdown
- **Early gate as checkbox** → Generic hypotheses ("what if it doesn't scale?") fail hard-fail rules. Q3 must name specific mechanisms. Q5 must state what breaks.
```

**Step 7: Verify all edits**

Run: `grep "H-code exclusion" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "AHG-5 overlap" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "Bridge complete" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match (Exit Gate table row)

Run: `grep "zero hypotheses" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

Run: `grep "Early gate as checkbox" .claude/skills/reviewing-designs/SKILL.md`
Expected: 1 match

**Step 8: Commit**

```
git add .claude/skills/reviewing-designs/SKILL.md
git commit -m "feat(reviewing-designs): integrate bridge into existing sections

REFINE: H-code exclusion from Yield% tracking.
Adversarial: AHG-5 overlap handling (bridge-first, then NET-NEW).
Exit Gate: bridge completion criterion + self-check item.
Decision Points: early gate zero-hypothesis handling.
Anti-Patterns: early gate as checkbox."
```

---

### Task 5: Update examples.md for new flow

**Files:**
- Modify: `.claude/skills/reviewing-designs/references/examples.md`

The GOOD example needs updating to show the new flow (AHG-5 → bridge → delta cards → bridge-first adversarial).

**Step 1: Replace the GOOD example**

**Preflight:** Run `grep -c '## GOOD' .claude/skills/reviewing-designs/references/examples.md` — expect 1. If 0, stop — file structure may have changed.

Keep the BAD example unchanged (lines 7-22). Replace everything from `## GOOD: Iterative review with framework` to end of file with:

```markdown
## GOOD: Iterative review with early gate and bridge

**Entry Gate:**

- Target: `docs/designs/auth-system.md`
- Sources: `docs/requirements/security.md`, `docs/specs/api-v2.md`
- Stakes: Rigorous (implementation follows; moderate undo cost)
- Stopping: Yield% <10%

**AHG-5 Early Gate** (Rigorous → full 5 questions, exactly 3 hypotheses):

- Q1 → H1: "Auth system solves session management, but the real problem may be authorization granularity" [Target: D4, Anchor: §3.1]
- Q2 → ALT1: "JWT-only approach rejected too quickly — stateless auth eliminates Redis dependency" [Anchor: §2.3]
- Q3 → H2: "Fail-open on token validation timeout creates security hole — no fallback behavior specified" [Target: D6, Anchor: §4.2]
- Q4 → H3: "Token refresh during concurrent requests looks simple but creates race conditions" [Target: D10, Anchor: §4.1]
- Q5 → "Session store is load-bearing" (merged with H1 scope — already covered)

Bridge table populated: H1 (open, D4), H2 (open, D6), H3 (open, D10), ALT1 (open), ALT2 (NONE IDENTIFIED)

**Delta card #1 presented.** User confirms hypotheses, no changes.

**Pass 1 EXPLORE:** 3 P0 gaps, 5 P1 issues. Yield% = 100%.

**Pass 2 EXPLORE:** Deeper on D4-D6.

- H2 → TESTED: P0 — timeout defaults to fail-open [D6]
- H3 → TESTED: P0 — no mutex on concurrent refresh [D10]
- 1 P1 revised. Yield% = 30%.

**Pass 3 EXPLORE:** Document Quality (D13-D19). 1 P1 (vague error handling language). Yield% = 9%.

**Delta card #2:**

```
**Checkpoint 2: Loop converged** (3 passes, Yield% 9%)

Bridge updates:
- H1 (authorization granularity) → open (D4 partial — needs deeper check in adversarial)
- H2 (fail-open timeout) → TESTED: P0 [D6]
- H3 (refresh race condition) → TESTED: P0 [D10]
- ALT1 (JWT-only) → EVALUATED: not dominant — can't support token revocation

Net-new: P1 — vague error handling language [D14]

Totals: P0: 5 | P1: 7 | P2: 2

Anything to dig deeper on before the adversarial pass?
```

**Adversarial Pass** (bridge-first, then NET-NEW):

- A1 (Assumption Hunting): checks H1 → TESTED: authorization model also assumes flat permissions [H1, D4]
- A5 (Pre-mortem): "Token refresh race causes cascading failures" [H3 — extends, not NET-NEW]
- A6 (Steelman Alternatives): checks ALT1 → confirms "not dominant"
- A8 (Hidden Complexity): **NET-NEW** — token rotation during deployment creates 2-minute auth gap [D10]

**Delta card #3:** Bridge complete (H1 tested, H2 tested, H3 tested, ALT1 evaluated, ALT2 withdrawn). 1 NET-NEW finding. Informational closeout.

**Exit Gate:** Yield% <10%, bridge complete, all dimensions checked, disconfirmation attempted.

**Output:**

```
**Review complete:** auth-system.md
**Findings:** P0: 6 | P1: 7 | P2: 2
**Key issues:** Fail-open on timeout (H2→D6); refresh race condition (H3→D10)
**Full report:** `docs/audits/YYYY-MM-DD-auth-system-review.md`
```

**Why it's good:**

- Entry Gate established scope and stakes
- AHG-5 surfaced 3 hypotheses; 2 confirmed as P0s, 1 extended during adversarial pass
- Bridge table tracked hypotheses through loop — none forgotten
- Delta cards gave user 3 decision points during the review
- Adversarial pass evaluated bridge rows first (A1→H1, A5→H3, A6→ALT1), found 1 NET-NEW
- Iterative passes with Yield% tracking using framework formula
- Clear output with bridge connections visible
```

**Step 2: Verify**

Run: `grep "AHG-5" .claude/skills/reviewing-designs/references/examples.md`
Expected: 1+ matches

Run: `grep "Delta card" .claude/skills/reviewing-designs/references/examples.md`
Expected: 3+ matches

Run: `grep "NET-NEW" .claude/skills/reviewing-designs/references/examples.md`
Expected: 2+ matches

**Step 3: Commit**

```
git add .claude/skills/reviewing-designs/references/examples.md
git commit -m "feat(reviewing-designs): update GOOD example for redesigned flow

Shows AHG-5 early gate, bridge table population, 3 delta cards,
bridge-first adversarial evaluation, and NET-NEW marking."
```

---

### Task 6: Add anti-pattern to dimensions-and-troubleshooting.md

**Files:**
- Modify: `.claude/skills/reviewing-designs/references/dimensions-and-troubleshooting.md`

**Step 1: Add early gate anti-pattern**

After the existing "Burying P0 findings in long report" anti-pattern block (ending with `**Fix:** Summary table with P0 count goes at top of report AND in chat summary. P0s must be unmissable.`) and before the `---` separator before Troubleshooting, insert:

```markdown

**Pattern:** Early gate as checkbox
**Why it fails:** Producing formulaic hypotheses ("what if it doesn't scale?") that technically satisfy hard-fail rules but lack genuine adversarial intent. Same theater problem as "adversarial pass as checkbox."
**Fix:** Q3 must name specific mechanisms, not categories. Q5 must state what breaks. Generic answers fail hard-fail rules. If hypotheses feel formulaic, re-engage with genuine adversarial intent.
```

**Step 2: Verify**

Run: `grep "Early gate as checkbox" .claude/skills/reviewing-designs/references/dimensions-and-troubleshooting.md`
Expected: 1 match

**Step 3: Commit**

```
git add .claude/skills/reviewing-designs/references/dimensions-and-troubleshooting.md
git commit -m "feat(reviewing-designs): add early gate checkbox anti-pattern

Warns against formulaic hypotheses that satisfy hard-fail rules in
letter but not spirit — same theater risk as adversarial pass."
```

---

### Task 7: Final verification

**No file changes — verification only.**

**Step 1: Line count**

Run: `wc -l .claude/skills/reviewing-designs/SKILL.md`
Expected: 565-585 lines (accepted trade-off over 500-line soft target — boundary rules add ~30 lines)

**Step 2: Internal link check**

Run: `rg -o '\]\([^)]+\)' .claude/skills/reviewing-designs/SKILL.md | sort -u`

Verify each link target exists:
- `references/framework-for-thoroughness_v1.0.0.md` — should exist
- `references/bridge-and-checkpoints.md` — created in Task 1
- `references/bridge-and-checkpoints.md#delta-card-schema` — section should exist
- `references/bridge-and-checkpoints.md#overflow-ranking` — section should exist
- `references/examples.md` — should exist
- `references/dimensions-and-troubleshooting.md#anti-patterns` — section should exist
- `references/dimensions-and-troubleshooting.md#troubleshooting` — section should exist

**Step 3: Section ordering check**

Run: `grep "^### \|^## " .claude/skills/reviewing-designs/SKILL.md`

Verify process flow order:
1. Overview
2. When to Use / When NOT to Use
3. Outputs (with Delta Card Checkpoints subsection)
4. Entry Gate (under Process header)
5. Early Adversarial Gate (AHG-5)
6. Bridge Table
7. Framework Boundary Rules
8. The Review Loop
9. DISCOVER / EXPLORE / VERIFY / REFINE (under Review Loop)
10. Adversarial Pass
11. Exit Gate
12. Decision Points
13. Anti-Patterns / Troubleshooting / Extension Points

**Step 4: Cross-reference consistency**

Verify these terms appear in the expected locations:

| Term | Expected locations |
|------|-------------------|
| `AHG-5` | Overview, Outputs (DoD), AHG-5 section, Adversarial Pass (overlap), Decision Points, Anti-Patterns |
| `bridge table` | Overview, Outputs (DoD), Bridge Table section, Boundary Rules (B2), REFINE (H-code), Exit Gate, Decision Points |
| `delta card` | Overview, Outputs section, Definition of Done, AHG-5 section (output line) |
| `disposition invariant` | Bridge Table section, Exit Gate |
| `NET-NEW` | Adversarial Pass overlap |
| `H-code` | REFINE section, Boundary Rules (B1) |
| `Framework Boundary Rules` | Boundary Rules section header |
| `B1` through `B6` | Boundary Rules table (6 rows) |
| `Referential integrity` | Bridge Table section, Boundary Rules (B3) |
| `Disconfirmation disambiguation` | Boundary Rules section |

**Step 5: Design doc compliance check**

Verify each design doc requirement from `docs/plans/2026-03-02-reviewing-designs-redesign.md` is implemented:

| Design doc section | SKILL.md location | Check |
|---|---|---|
| §1 AHG-5 questions | AHG-5 section (5-row table) | All 5 questions present |
| §1 Stakes gating | AHG-5 section (stakes table) | 3 stakes levels with counts |
| §1 Hard fail rules | AHG-5 section (4 bullets) | Q3 mechanism rule, Q5 assumption rule |
| §1 No skip path | AHG-5 section | "No skip path" statement |
| §2 Bridge schema | Bridge Table section | 6-field table |
| §2 Status values | Bridge Table section | 5 values in table (including evaluated for ALT rows) |
| §2 Disposition invariant | Bridge Table section | Invariant statement |
| §2 Bridge operations | Reference doc | 4 operations with checkpoint scoping |
| §2 ALT schema | Reference doc | 5-field table |
| §2 Dominance check | Reference doc | Decision tree |
| §3 Delta card checkpoints | Outputs section | 3-row checkpoint table |
| §3 Overlap handling | Adversarial Pass section | 3-point bridge-first protocol |
| §3 Delta card schema | Reference doc | 6-field table + example |
| §3 Output contract change | Outputs section | Dialogue-first statement |
| §4 Exit Gate +1 | Exit Gate table | Bridge complete row |
| §4 H-codes scaffolding | REFINE section | H-code exclusion note |
| — ALT overflow | Reference doc | 4-case table + constrained-space gate |
| — Integration seams | Reference doc | Dominance skip, deferred-ALT promotion, A6 fallback |
| — Framework boundary rules | Boundary Rules section | B1-B6 rules table + disconfirmation disambiguation |
| — Status-specific disposition | Reference doc | Evidence requirements per status, E1+ for `tested` |
| — REOPEN semantics | Reference doc | Reconciliation pass, iteration cap override, D/F propagation |
| — ALT → F-code | Reference doc | Unresolved dominance creates P1 F-code |
| — Promotion-on-slot-open | Reference doc | Deferred hypothesis promotion via REVISE by checkpoint 2 |
| — Referential integrity | Bridge Table section | H→D/F linkage enforcement |

**Step 6: Semantic checks**

Verify these specific content items survived from the design doc:

- Q2 contains "than this" (not just "better?"): `rg "better than this" .claude/skills/reviewing-designs/SKILL.md`
- Q2 Catches contains "motivated reasoning": `rg "motivated reasoning" .claude/skills/reviewing-designs/SKILL.md`
- Q3 Catches contains "Systematically": `rg "Systematically underspecified" .claude/skills/reviewing-designs/SKILL.md`
- Q4 Catches contains "edge case surfaces": `rg "edge case surfaces" .claude/skills/reviewing-designs/SKILL.md`
- Overview concerns match design doc (Conversational sharpening, Optimality — not Source coverage, Implementation readiness): `rg "Conversational sharpening|Optimality" .claude/skills/reviewing-designs/SKILL.md`
- Boundary rules present (B1-B6): `rg "B[1-6]" .claude/skills/reviewing-designs/SKILL.md` — expect 6 matches
- Entry Gate declaration wording present: `rg "Yield% scope: D-codes" .claude/skills/reviewing-designs/SKILL.md` — expect 1 match
- Referential integrity in Bridge Table: `rg "Referential integrity" .claude/skills/reviewing-designs/SKILL.md` — expect 1+ matches
- Status-specific disposition in reference doc: `rg "Status-Specific Disposition" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md` — expect 1 match
- REOPEN semantics in reference doc: `rg "REOPEN semantics" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md` — expect 1 match
- ALT → F-code in reference doc: `rg "F-code rule" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md` — expect 1 match
- Promotion-on-slot-open in reference doc: `rg "Promotion-on-slot-open" .claude/skills/reviewing-designs/references/bridge-and-checkpoints.md` — expect 1 match

**Step 7: Report results**

Summarize: line count, any broken links, any missing design doc requirements, any consistency issues.

If all checks pass, the implementation is complete.

---

## Summary

| Task | Description | Files | Commit message prefix |
|------|-------------|-------|----------------------|
| 1 | Create bridge-and-checkpoints reference doc | +1 new | `feat(reviewing-designs): add bridge & checkpoints reference doc` |
| 2 | Update SKILL.md top (frontmatter, Overview, Outputs) | 1 modified | `feat(reviewing-designs): update overview and outputs for redesign` |
| 3 | Insert AHG-5 + Bridge Table + Framework Boundary Rules sections | 1 modified | `feat(reviewing-designs): add AHG-5, bridge table, and boundary rules` |
| 4 | Update SKILL.md bottom (REFINE, Adversarial, Exit Gate, Decision Points, Anti-Patterns) | 1 modified | `feat(reviewing-designs): integrate bridge into existing sections` |
| 5 | Update examples.md for new flow | 1 modified | `feat(reviewing-designs): update GOOD example for redesigned flow` |
| 6 | Add anti-pattern to dimensions-and-troubleshooting.md | 1 modified | `feat(reviewing-designs): add early gate checkbox anti-pattern` |
| 7 | Final verification | 0 (read-only) | — |

## Execution Guards

1. **No partial merge:** Do not merge/cherry-pick any subset of Task 1-6 commits. Completion requires Task 7 pass.
2. **Resume protocol:** If interrupted, resume from first incomplete task and rerun Task 7 fully.
3. **Final handoff:** Must include Task 7 report + changed-file diff review.

## Codex Review Notes

This plan was reviewed via three Codex dialogues:
- **Adversarial** (thread `019cb19c`, 7 turns, converged): Found 7 content fixes + 3 execution guards. Key: concern labels mismatch, `evaluated` status omission, Task 7 portability.
- **Collaborative** (thread `019cb1b0`, 6 turns, converged): Resolved 3 open questions. Key: Q2/Q4 wording drops are substantive (not editorial), ALT slots are fixed at 2 with explicit overflow, TESTED/CONFIRMED is a drafting artifact.
- **Adversarial framework review** (thread `019cb1de`, 7 turns, converged): Reviewed framework-for-thoroughness_v1.0.0 as foundation for the redesign. Verdict: framework is sound; redesign needs 6 boundary rules (B1-B6) plus 2 hardening items. Key: H-code exclusion needs Entry Gate declaration (B1), bridge is parallel tracker not Cell Schema extension (B2), unresolved ALT dominance must create F-code finding (B6). 5 open questions resolved during plan update: REOPEN overrides iteration cap for one pass, no Decision state field in delta cards, boundary section in SKILL.md, scoped adversarial re-validation for reopened rows, Entry Gate declaration wording drafted.

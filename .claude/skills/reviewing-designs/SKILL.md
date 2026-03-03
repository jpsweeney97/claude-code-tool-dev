---
name: reviewing-designs
description: Iterative design review using the Framework for Thoroughness. Use when verifying a design captures all requirements from sources. Use after creating specs from multiple documents. Use before implementing from a design. Use when past designs have led to implementation surprises. Use when questioning whether a design solves the right problem.
---

# Reviewing Designs

## Overview

Design review catches issues before implementation, when they're cheap to fix. This skill addresses four concerns:

1. **Intent alignment** — Does the design solve the right problem?
2. **Blind spot surfacing** — What assumptions hasn't the designer questioned?
3. **Conversational sharpening** — Value is in back-and-forth dialogue, not compliance reports
4. **Optimality** — Is this the best design for its purpose, not just the first workable approach?

An early adversarial gate (AHG-5) surfaces framing problems and load-bearing assumptions as testable hypotheses. A bridge table carries those hypotheses through the dimensional loop, preventing "generate-then-forget." Three dialogue checkpoints (delta cards) make the conversation the primary output.

**Protocol:** [thoroughness.framework@1.0.0](references/framework-for-thoroughness_v1.0.0.md)
**Default thoroughness:** Rigorous

**Reference file contract:** SKILL.md is normative for rules, gates, semantics, and control flow. Reference files are operational — procedures, decision trees, examples, and troubleshooting. SKILL.md takes precedence on conflict. Cross-references must name the delegated mechanism.

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

## When to Use

- After creating a design document from multiple sources
- When verifying a specification captures all requirements
- Before implementing from a design (verify completeness and clarity)
- When past designs have led to implementation surprises, missing pieces, or ambiguous specs
- After brainstorming completes and a design document exists
- When merging methodologies or patterns from different sources

## When NOT to Use

- No design document exists yet (use brainstorming first)
- Simple document reviews that don't involve source comparison or implementation readiness
- Code reviews (use code-review skills)
- Implementation is already complete (this is pre-implementation review)
- Quick prototype/spike where rigor isn't needed

## Outputs

**Interaction model:** Dialogue-first with 3 delta cards in chat. Artifact compiles all cards + full coverage tracker.

### Delta Card Checkpoints

| # | When | Contents | User can... |
|---|------|----------|-------------|
| 1 | After early gate | Hypotheses, alternatives, bridge table | Add context, ADD/REVISE/WITHDRAW bridge rows, confirm |
| 2 | After loop convergence | Bridge dispositions, net-new findings, running P0/P1/P2 totals, ALT dominance results | Redirect, modify bridge rows, ask to dig deeper |
| 3 | After adversarial pass | Final bridge table, adversarial findings (bridge-mapped + NET-NEW), overall assessment | Informational closeout. REOPEN only if adversarial findings contradict a disposition |

Checkpoints are invitations, not gates. If the user says nothing, the review proceeds.

**Checkpoint 2 re-entry:** If ADD creates a new H-row or REVISE materially changes hypothesis/target dimensions at checkpoint 2, run one reconciliation loop pass on affected rows before the Adversarial Pass and recompute Yield%. Editorial-only REVISE and WITHDRAW do not require reconciliation.

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

## Process

### Entry Gate

**YOU MUST** complete the Entry Gate before any analysis.

**1. Identify inputs:**

- Target document (the design being reviewed)
- Source documents (materials the design should capture), if applicable
- User-specified concerns, if any

If inputs are unclear, ask. Accept paths, conventions (e.g., `docs/plans/`), or descriptions.

**2. Surface assumptions:**
List what you're taking for granted:

- Source documents are complete and authoritative
- Target document is the current version
- [Any context-specific assumptions]

**3. Calibrate stakes:**

| Factor        | Adequate     | Rigorous       | Exhaustive        |
| ------------- | ------------ | -------------- | ----------------- |
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius  | Localized    | Moderate       | Wide/systemic     |
| Cost of error | Low          | Medium         | High              |
| Uncertainty   | Low          | Moderate       | High              |
| Time pressure | High         | Moderate       | Low/none          |

**Default: Rigorous.** Override if user specifies or factors clearly indicate otherwise.

**4. Select stopping criteria:**

- **Primary:** Yield-based (Yield% below threshold)
- **Thresholds:** Adequate <20%, Rigorous <10%, Exhaustive <5%

**5. Record Entry Gate:**
Document: inputs, assumptions, stakes level, stopping criteria, and Yield% scope declaration (per B1): "D-codes and F-codes only. H-codes are bridge scaffolding."

### Early Adversarial Gate (AHG-5)

**AHG-5** = Adversarial Hypothesis Gate, 5 questions.

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

**Adequate path:** Adequate skips Q2, so no concrete alternatives emerge. Populate ALT rows using [ALT overflow](references/bridge-and-checkpoints.md#alt-overflow) 0-alt rules (CONSTRAINED or NONE IDENTIFIED).

No skip path — skipping recreates the N/A rationalization anti-pattern.

**Hard fail rules** (per run question):

- Each run question produces a hypothesis, "merged → Hn" (subsumed by existing hypothesis; satisfies hard-fail, no additional H-row), or explicit "no finding" with one-sentence justification
- Q3 must name specific mechanisms, not categories
- Q5 must identify one assumption and state what breaks if it's wrong
- All run questions producing "no finding" → flag: "Early gate produced zero hypotheses — verify genuine engagement before proceeding."

**Overflow:** Rank surplus hypotheses by impact × plausibility × testability. Top N become bridge rows; remainder go in "deferred hypotheses" footnote. See [Bridge & Checkpoints Reference](references/bridge-and-checkpoints.md#overflow-ranking).

**Output:** Populate bridge table with H-rows and ALT-rows. Present delta card #1 in chat.

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

Status terms are lowercase (`tested`, not `TESTED`). Design doc references to "TESTED/CONFIRMED" map to `tested`.

**Disposition invariant:** Every non-`open` row must include disposition text, evidence or rationale, and audit entry (when/checkpoint + why + prior status).

**ALT dominance outcomes:** not dominant (design wins), unresolved — escalate (creates F-code per B6), clearly dominant (P0 finding). Full decision tree in [Bridge & Checkpoints Reference](references/bridge-and-checkpoints.md#alternatives-dominance-check).

**Lifecycle:** Rows added after early gate as `open` → status transitions via bridge operations at checkpoints → at Exit Gate, no `open` rows allowed.

**Framework relationship:** The bridge table is a parallel tracking structure alongside the Cell Schema coverage tracker — not an extension of it. Cell Schema tracks D-codes and F-codes with `[x]`/`[~]`/`[-]` statuses and E0-E3 evidence levels. The bridge tracks H-codes and ALT-codes with `open`/`tested`/`disconfirmed` statuses. Linkage is via: Target Dimensions (H→D mapping), Disposition (H→F finding IDs), and Anchor (design location). Both must be complete at Exit Gate.

**Referential integrity:** Every `tested` H-row must reference at least one D-code or F-code finding. Every `disconfirmed` H-row must reference the dimensional check that produced counter-evidence. If a referenced D-code is later revised or removed, update the H-row disposition accordingly.

**Operations, alternatives, and dominance checks:** See [Bridge & Checkpoints Reference](references/bridge-and-checkpoints.md).

### Framework Boundary Rules

The bridge table and AHG-5 layer on top of the [thoroughness framework](references/framework-for-thoroughness_v1.0.0.md). These rules govern the boundary between framework-owned semantics and skill-local additions.

| # | Rule | What it governs |
|---|------|----------------|
| B1 | **Entry Gate declares Yield% scope:** H-codes and ALT-codes are excluded from Yield% tracking. Declare per-run in Entry Gate output: "Yield% scope: D-codes and F-codes only. H-codes are bridge scaffolding." | Yield% formula scope (framework MAY clause) |
| B2 | **Bridge is a parallel tracker:** The bridge table operates alongside the Cell Schema coverage tracker, not inside it. Different ID namespaces (H/ALT vs D/F), different status vocabularies, different evidence models. | Structural relationship |
| B3 | **Referential integrity:** Every `tested` H-row references ≥1 D/F finding. Every `disconfirmed` H-row references the counter-evidence source. If a referenced finding is revised or removed, update the H-row disposition. | Cross-tracker linkage |
| B4 | **Status-specific evidence:** `tested` requires E1+ evidence (not bare assertion). `disconfirmed` requires specific counter-citation. `evaluated` (ALT) requires decision tree outcome with rationale. `withdrawn` requires one-sentence justification citing invalidated premise. See [Status-Specific Disposition Requirements](references/bridge-and-checkpoints.md#status-specific-disposition-requirements) for full table. | Disposition quality |
| B5 | **REOPEN propagates D/F entities:** A REOPEN triggers exactly one reconciliation loop pass; if iteration cap has been reached, REOPEN overrides for this one pass (cap reasserts after). New D/F entities enter Yield% scope normally. See [REOPEN semantics](references/bridge-and-checkpoints.md#reopen-semantics) for scoped re-validation detail. | Loop re-entry mechanics |
| B6 | **Unresolved ALT dominance creates F-code:** When an ALT row is `evaluated` with "unresolved — escalate," a corresponding F-code finding enters the coverage tracker at P1. | Decision risk tracking |

These rules are the boundary contract between the framework and the skill's additions. Violations indicate a gap in the bridge-to-framework interface, not a framework bug.

**Disconfirmation disambiguation:** "Disconfirmation" means different things in the two systems. Framework: obligation to attempt disconfirmation of P0 findings (applied to D/F-codes). Bridge: status meaning "hypothesis not supported" (applied to H-codes). These are independent — a `disconfirmed` H-row does not satisfy the framework's P0 disconfirmation MUST.

### The Review Loop

```
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
DISCOVER ──► EXPLORE ──► VERIFY ──► REFINE?
                                          │
                                    (Yield% above
                                     threshold?)
                                          │
                                     EXIT if below
```

#### DISCOVER: What dimensions should I check?

**Seed dimensions:** See [Dimension Catalog](references/dimensions-and-troubleshooting.md#dimension-catalog) for full definitions.

| Category | Dimensions | When to Check |
|----------|------------|---------------|
| Source Coverage | D1-D3 | When source documents exist |
| Behavioral Completeness | D4-D6 | When design will be implemented |
| Implementation Readiness | D7-D11 | When design will be implemented |
| Consistency | D12 | Always |
| Document Quality | D13-D19 | Always |

**Dimension applicability rules:**

**Always mandatory (cannot skip):**

- Document Quality (D13-D19)
- Cross-validation (D12)

**Conditional (require justification to skip):**

- Source Coverage (D1-D3) — skip only if no source documents exist
- Behavioral Completeness (D4-D6) — skip only if design won't be implemented
- Implementation Readiness (D7-D11) — skip only if design is documentation-only

**Before marking any dimension N/A:**

1. State specific reason (not "doesn't apply" but WHY it doesn't apply)
2. Test: "Would a skeptical reviewer accept this justification?"
3. Self-check: "If this dimension revealed issues, would I be surprised?"

If the answer to #2 is "maybe not" or #3 is "no" → check the dimension anyway.

**Assign priorities:**

- **P0:** Missing this breaks correctness or execution
- **P1:** Missing this degrades quality
- **P2:** Polish

**Expand dimensions:** Apply ≥3 DISCOVER techniques from the framework:

- External taxonomy check (find established frameworks for this domain)
- Perspective multiplication (what would different stakeholders notice?)
- Pre-mortem inversion ("This review would be worthless if...")
- Historical pattern mining (what caused problems in similar designs?)

**Output:** Dimension list with priorities (P0/P1/P2)

#### EXPLORE: Check each dimension

For each dimension, record using Cell Schema:

| Field      | Required      | Values                                                                     |
| ---------- | ------------- | -------------------------------------------------------------------------- |
| ID         | Yes           | D1, D2, ... F1, F2, ...                                                    |
| Status     | Yes           | `[x]` done (completeness verified), `[~]` partial/presence-only, `[-]` N/A, `[ ]` not started, `[?]` unknown |
| Priority   | Yes           | P0 / P1 / P2                                                               |
| Evidence   | Yes           | E0 (assertion) / E1 (single source) / E2 (two methods) / E3 (triangulated) |
| Confidence | Yes           | High / Medium / Low                                                        |
| Artifacts  | If applicable | File paths, quotes, line numbers                                           |
| Notes      | If applicable | What's missing, next action. **Required for `[x]`:** "Completeness basis: ..." stating what makes this complete, not just present. Presence-only → use `[~]`. |

**Evidence requirements by stakes:**

- Adequate: E1 for P0 dimensions
- Rigorous: E2 for P0, E1 for P1
- Exhaustive: E2 for all, E3 for P0

**Rule:** Confidence cannot exceed evidence. E0/E1 caps confidence at Medium.

**For each finding:**

- Link to dimension(s) it relates to
- Assign priority based on impact (P0/P1/P2)
- Rate evidence and confidence
- Note artifacts (quotes, file:line references)

**STOP-CHECK before proceeding:**
1. Did you check COMPLETENESS, not just PRESENCE? "Design mentions X" ≠ "X is fully specified." For each dimension, the question is "Is this COMPLETE?" not "Is this MENTIONED?"
2. Did any dimension get `[-]` N/A? Verify each N/A passes the skeptical-reviewer test from DISCOVER. If justification is weak, re-check the dimension.

#### VERIFY: Check findings

**Cross-reference:** Do findings from different dimensions agree or contradict?

**Disconfirmation:** For each P0 dimension/finding, attempt to disprove it:

| Technique              | Method                                         |
| ---------------------- | ---------------------------------------------- |
| Counterexample search  | Find a case that breaks the current claim      |
| Alternative hypothesis | What's another explanation? Test it.           |
| Adversarial read       | Could this evidence be misleading?             |
| Negative test          | What check would fail if the finding is wrong? |
| Cross-check            | Verify via an independent method               |

**Minimum disconfirmation by stakes:**

- Adequate: 1 technique per P0
- Rigorous: 2+ techniques per P0
- Exhaustive: 3+ techniques per P0

**Assumption check:** Which Entry Gate assumptions were validated? Invalidated?

**Gap scan:** Any `[ ]` or `[?]` items remaining?

**Output:** Verified findings with confidence levels

**STOP-CHECK before proceeding:** Was disconfirmation genuine? "I tried to disprove it" requires stating what technique you used AND what you found. If you cannot name the technique and result, go back and actually attempt disconfirmation.

#### REFINE: Loop or exit?

**Calculate Yield%:**

Yield% measures how much new/revisionary information emerged this pass.

An entity _yields_ if it is:

- New (didn't exist last pass)
- Reopened (resolved → unresolved)
- Revised (conclusion changed)
- Escalated (priority increased)

**Stable identity:** All yield-tracked entities must keep stable IDs across passes. Renames without ID continuity count as removed + new. (LLMs naturally renumber lists between passes — without stable IDs, renamed entities cause false convergence.)

**Effective priority:** Findings inherit the highest priority of their linked dimensions. Unlinked findings default to P1 until linked. (Prevents P2-deferral: classifying genuinely P0/P1 findings as P2 to exclude them from Yield% scope.)

**H-code exclusion (per B1):** Bridge table H-codes are scaffolding — not Yield-tracked entities. Only D-codes and F-codes enter E_prev/E_cur. Bridge completion is an independent exit criterion checked at Exit Gate. **Entry Gate declaration (B1):** Include in Entry Gate output: "Yield% scope: D-codes and F-codes only. H-codes are bridge scaffolding." (Per framework MAY clause — scope overrides must be declared at Entry Gate.)

`Yield% = ( |Y| / max(1, |U|) ) × 100`

Where:
- `E_prev` = in-scope P0+P1 entities at end of previous pass
- `E_cur` = in-scope P0+P1 entities at end of current pass
- `U = E_prev ∪ E_cur` (union — prevents denominator shrinkage when items are reclassified or removed)
- `Y` = subset of `U` that yielded this pass

Pass 1 special case: Yield% = 100% (no prior snapshot).

**Priority downgrade rule:**

1. **Evidence required:** Downgrades (P0→P1, P1→P2) require evidence that disproves or bounds the original failure mode — not merely a restatement at lower severity.
2. **Before/after record:** Document: previous claim, new evidence, residual impact, and mapped priority.
3. **Ambiguity default:** When evidence is ambiguous, retain the higher priority.
4. **Re-escalation:** If later evidence contradicts a downgrade justification, re-escalate immediately to the original priority.

Track all downgrades in the iteration log — they are auditable.

**Worked example:**

| Pass | U (union) | Y (yielding) | Yield% |
|------|-----------|--------------|--------|
| 1 | — | — | 100% (special case) |
| 2 | 10 | 3 (2 new + 1 revised) | 30% |
| 3 | 11 | 1 (1 new) | 9% |

Pass 3 Yield% (9%) is below Rigorous threshold (10%) → exit to Adversarial Pass.

**Continue iterating if:**

- New dimensions discovered
- Findings significantly revised
- Coverage has unresolved `[ ]` or `[?]` items
- Assumptions invalidated that affect completed items
- Yield% above threshold for stakes level

**Exit to Adversarial Pass when:**

- No new dimensions in last pass
- No significant revisions
- All items resolved (`[x]`, `[-]`, or `[~]` with documented gaps)
- Yield% below threshold (Adequate <20%, Rigorous <10%, Exhaustive <5%)

**Iteration cap (failsafe):** If convergence not reached after 5 passes (Adequate), 7 passes (Rigorous), or 10 passes (Exhaustive), exit with finding: "Design may need fundamental revision — review did not converge after N passes." This prevents infinite loops on genuinely problematic designs.

### Adversarial Pass

**YOU MUST** complete the Adversarial Pass before Exit Gate, even if VERIFY found nothing.

This pass challenges the _design itself_, not just individual findings. Apply each lens with genuine adversarial intent — objections must cause discomfort if true.

| ID | Lens                       | Question                                                                                                       |
| -- | -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| A1 | **Assumption Hunting**     | What assumptions does the design make (explicit and implicit)? What if they're wrong?                          |
| A2 | **Scale Stress**           | What breaks at 10x? 100x? Where are the bottlenecks?                                                           |
| A3 | **Competing Perspectives** | Security: attack vectors? Performance: slow spots? Maintainability: hard to change? Operations: hard to debug? |
| A4 | **Kill the Design**        | What's the strongest argument against this? If it fails in production, what's the cause?                       |
| A5 | **Pre-mortem**             | It's 6 months later, this failed catastrophically. What went wrong? What warnings were ignored?                |
| A6 | **Steelman Alternatives**  | What approaches were rejected? What would make them better than this design?                                   |
| A7 | **Challenge the Framing**  | Is this the right problem to solve? Are we addressing a symptom instead of root cause?                         |
| A8 | **Hidden Complexity**      | Where is complexity underestimated? What looks simple but isn't?                                               |
| A9 | **Motivated Reasoning**    | Where might the design rationalize a preferred approach? Is there anchoring to an early idea?                  |

**Completion schema:** For each applied lens, record: lens ID, objection raised, response/mitigation, and residual risk (if any). Verify the count of lenses with non-empty objections matches the stakes requirement below.

**AHG-5 overlap:** Lenses A1, A6, A7, and A8 overlap with AHG-5 questions. To prevent duplicate findings:

1. Evaluate mapped bridge rows first (e.g., A1 checks H-rows before generating new findings)
2. Findings that extend or confirm bridge hypotheses link to the existing H-code
3. Genuinely new findings are marked **NET-NEW** with one-sentence justification of why the early gate didn't catch them

**Minimum depth by stakes:**

- Adequate: Apply 4+ lenses (by ID); document key objections
- Rigorous: Apply all 9 lenses (A1-A9); document objections and responses
- Exhaustive: Apply all 9 lenses (A1-A9); document objections, responses, and residual risks

**Output:** Adversarial findings added to report, categorized separately from systematic findings (reference by lens ID)

### Exit Gate

**Cannot claim "done" until ALL criteria pass:**

| Criterion                 | Check                                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| Coverage complete         | No `[ ]` or `[?]`. All items are `[x]`, `[-]` (with rationale), or `[~]` (with documented gaps) |
| Evidence requirements met | P0 dimensions have required evidence level for stakes                                           |
| Disconfirmation attempted | Techniques applied to P0s; documented what was tried and found                                  |
| Assumptions resolved      | Each verified, invalidated, or flagged as unverified                                            |
| Convergence reached       | Yield% below threshold for stakes level                                                         |
| Connections mapped        | P0/P1 findings have cause → affected sections → propagation impact documented                   |
| Adversarial pass complete | All required lenses applied (with IDs); objections documented with responses or accepted risks  |
| Bridge complete           | No `open` rows; all non-open rows satisfy disposition invariant (text + evidence + audit entry) |

**Post-completion self-check (verify before producing output):**

- [ ] Entry Gate: inputs, assumptions, stakes, stopping criteria all recorded
- [ ] DISCOVER: ≥3 techniques applied; D12-D19 not skipped; N/A dimensions have skeptical-reviewer justification
- [ ] EXPLORE: each dimension has Cell Schema fields (Status, Evidence, Confidence); findings linked to dimensions
- [ ] VERIFY: disconfirmation techniques documented (what was tried AND what was found)
- [ ] REFINE: Yield% calculated per pass; iteration log shows pass-by-pass changes
- [ ] Adversarial: required lens count met for stakes; pre-mortem produced specific, plausible failure story
- [ ] Bridge: all rows resolved; disposition invariant satisfied for every non-open row
- [ ] If a P0 exists, would the user definitely see it in the summary?
- [ ] If the design had hidden flaws, did I genuinely try to find them?

**"No issues found" requires extra scrutiny:** Was disconfirmation genuinely attempted? Self-check: "Did I actually look, or did I assume the design was fine?"

**Produce output:**

1. Write full report to `docs/audits/YYYY-MM-DD-<design-name>-review.md`
2. Present brief summary in chat (P0/P1/P2 counts + key issues only)
3. Chat must NOT contain full findings, iteration log, or coverage tracker

## Decision Points

**Inputs unclear:**

- If target document not specified → Ask: "Which design document should I review?"
- If sources not specified but source comparison is relevant → Ask: "Are there source documents this design should capture?"
- If user says "just review it" → Proceed with D4-D19 (Behavioral Completeness through Document Quality); mark D1-D3 as `[-]` with rationale: no source documents specified

**Stakes disagreement:**

- If factors split across columns → Choose the higher level
- If user specifies a level → User's choice wins; document rationale in Entry Gate

**Dimension not applicable:**

- Mark as `[-]` with brief rationale (e.g., "D1-D3: N/A — no source documents specified")
- Do not force-fit dimensions that don't apply

**Bridge row targets N/A dimension:**

- Retarget once to nearest applicable dimension; if none, WITHDRAW with rationale. See [N/A Dimension Targeting](references/bridge-and-checkpoints.md#na-dimension-targeting).

**P0 issue found during EXPLORE:**

- Continue review (don't stop to fix)
- Ensure finding is prominently captured
- Complete remaining dimensions before exiting

**Yield% ambiguous:**

- If unsure whether a change "counts" as revision → When in doubt, count it (bias toward more iteration)
- If Yield% hovers near threshold → Run one more pass to confirm convergence

**Adversarial pass finds fundamental flaw:**

- Add as P0 finding
- Do not attempt to fix within this skill (remediation is outside scope)
- Note in summary: "Design may need fundamental rethinking"

**Early gate produces zero hypotheses:**

- All run questions produced "no finding" → verify genuine engagement
- Self-check: "Did I approach this with adversarial intent, or assume the design was fine?"
- If still zero after genuine effort → note in delta card #1 that early gate found no framing issues

**User pressure to skip steps:**

- Acknowledge the pressure
- "Skipping [Entry Gate/AHG-5/Adversarial Pass/etc.] risks missing issues that surface during implementation."
- Complete minimum requirements for stakes level
- Compress output, not process

**"No issues" feels wrong:**

- Trust the feeling — run disconfirmation more aggressively
- Self-check: "What would I expect to find if there WERE issues? Did I look there?"
- If still nothing after genuine effort → Accept the finding; document what was checked

## Examples

See [Review Examples](references/examples.md) for BAD vs. GOOD comparison showing single-pass checkbox review (what to avoid) vs. iterative framework-based review (what to do).

## Anti-Patterns

Common failure modes and fixes: [Anti-Patterns Reference](references/dimensions-and-troubleshooting.md#anti-patterns)

**Most critical (memorize these):**

- **Single-pass "looks good" review** → Iterate until Yield% below threshold. Pass 1 is always 100% yield — you can't exit after one pass.
- **Checking presence instead of completeness** → Ask "Is this COMPLETE?" not "Is this MENTIONED?"
- **Skipping Document Quality dimensions** → D13-D19 are mandatory. Cannot be skipped.
- **Early gate as checkbox** → Generic hypotheses ("what if it doesn't scale?") fail hard-fail rules. Q3 must name specific mechanisms. Q5 must state what breaks.

## Troubleshooting

If the review process isn't working as expected, see [Troubleshooting Reference](references/dimensions-and-troubleshooting.md#troubleshooting).

**Quick checks:**

- **Review completed in one pass?** → Pass 1 is always 100% yield; cannot exit after one pass
- **Most dimensions marked N/A?** → Document Quality (D13-D19) and Cross-validation (D12) cannot be N/A
- **"No issues found"?** → Verify disconfirmation was genuinely attempted

## Extension Points

See [Extension Points](references/dimensions-and-troubleshooting.md#extension-points) for domain-specific dimensions, framework handoffs, custom artifact locations, and stakes presets.

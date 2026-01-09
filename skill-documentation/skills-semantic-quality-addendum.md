# Skills Semantic Quality Addendum

This document complements [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) by specifying **semantic and content-quality** requirements and patterns for `SKILL.md` bodies.

- **Status:** MIXED (contains NORMATIVE and NON-NORMATIVE sections; each section is labeled).
- **Source of structural truth:** [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) (all MUST/SHOULD requirements there still apply).
- **Primary objective:** reduce “structurally compliant but ineffective” skills by making intent, constraints, decisions, verification, and artifacts semantically precise and reviewable.

## Machine-first contracts (routing invariants) (NORMATIVE)

Section ID: semantic.machine-first-contracts

This document follows the same retrieval conventions as the strict spec.

### Document ID (NORMATIVE)

Section ID: semantic.machine-first-contracts.document-id

Retrieval key: `spec=skills-semantic-quality-addendum`

### Section ID contract (NORMATIVE)

Section ID: semantic.machine-first-contracts.section-id-contract

- Every major section has a stable ID line of the form: `Section ID: semantic.<id>`.
- IDs are stable; headings may change, but IDs MUST NOT be reused for different content.
- Retrieval SHOULD prefer NORMATIVE sections when generating enforcement logic.

### Normativity contract (NORMATIVE)

Section ID: semantic.machine-first-contracts.normativity-contract

- Normative requirements are labeled using MUST / MUST NOT / REQUIRED / SHOULD / MAY.
- Non-normative content is explicitly marked as `(guidance; non-normative)` or `(NON-NORMATIVE)`.

## Spec index (machine-first) (NORMATIVE)

Section ID: semantic.spec-index

Use this index to retrieve only the relevant chunk.

| Purpose | Retrieve | Section ID |
|---|---|---|
| Minimal semantic pass rules | Semantic minimums | `semantic.minimums` |
| Content-quality dimensions | Dimensions + criteria | `semantic.dimensions` |
| Copy/paste templates | Template library | `semantic.templates` |
| Review rubric | Semantic reviewer checklist + scoring | `semantic.review` |
| Category tightening | Category semantic add-ons | `semantic.category-addons` |
| Anti-patterns | Red flags | `semantic.anti-patterns` |

## Scope and relationship to the strict spec (NORMATIVE)

Section ID: semantic.scope

- This spec applies to the **body** of `SKILL.md` (same scope as the strict spec).
- This spec does **not** replace the strict spec; it complements it.
- If this spec and the strict spec disagree, the strict spec takes precedence unless this spec explicitly tightens a behavior without contradiction.
- “Semantic quality” here means: reducing ambiguity, forcing correct STOP/ask behavior, preventing agent drift, and making verification and artifacts measure what the skill intends.

## Semantic minimums (baseline pass rules) (NORMATIVE)

Section ID: semantic.minimums

These are **minimum semantic requirements** that SHOULD be satisfied by all skills. Reviewers MAY treat these as “PASS-WITH-NOTES” vs “FAIL” depending on risk tier, but High-risk skills SHOULD be held strictly to these.

### 1) Intent fidelity and non-goals (NORMATIVE)

Section ID: semantic.minimums.intent-and-non-goals

- The skill MUST state a **primary goal** in 1–2 sentences.
- The skill MUST include at least **3 non-goals** (explicit out-of-scope items) unless genuinely inapplicable; if omitted, the skill MUST explain why.
- The skill MUST avoid proxy goals like “improve quality” without a measurable/observable acceptance signal.

### 2) Constraint completeness (NORMATIVE)

Section ID: semantic.minimums.constraints

- The skill MUST declare constraints that are likely to be guessed incorrectly (e.g., “no new runtime deps”, “no network”, “no breaking API changes”, “no schema changes”, “no secrets”, “no behavior changes”, “must be reversible”).
- If constraints are unknown and materially affect feasibility, the skill MUST include a **STOP** step to ask for them.

### 3) Decision points reference observable signals (NORMATIVE)

Section ID: semantic.minimums.observable-decision-points

- Each decision point MUST name at least one **observable signal** that triggers the branch (file existence, command output shape, failing test, grep result, etc.).
- Decision points MUST NOT rely solely on subjective judgment (e.g., “if it seems risky”) without a concrete trigger.

### 4) Verification validity (NORMATIVE)

Section ID: semantic.minimums.verification-validity

- The skill MUST include a quick check that measures the **primary success property** (not just a proxy like “it compiles”), unless genuinely impossible; if impossible, the skill MUST state why and MUST specify the next-best observable check.
- Every command-based check MUST include an expected result shape (per the strict spec’s command mention rule).
- If verification cannot be run in the environment, the skill MUST provide a no-network/manual or “paste outputs” fallback when feasible.

### 5) Calibration and “Not run” honesty (NORMATIVE)

Section ID: semantic.minimums.calibration

- The skill MUST instruct the agent to label any skipped verification as: `Not run (reason)` and provide the exact command a user can run to verify.
- The skill MUST distinguish **verified** vs **inferred** vs **assumed** claims when producing reports or recommendations.

## Semantic quality dimensions (criteria and patterns) (guidance; non-normative)

Section ID: semantic.dimensions

Use these dimensions to write and review high-quality skills. These are not all mandatory, but higher-risk tiers SHOULD satisfy more of them.

### Dimension A: Intent fidelity (guidance; non-normative)

Section ID: semantic.dimensions.intent-fidelity

**What goes wrong:** the agent optimizes a proxy goal or expands scope.

**Criteria:**
- Primary goal is explicit and matches outputs/DoD.
- Non-goals prevent common drift.
- “Must-haves” vs “nice-to-haves” are distinguished.

**Patterns:**
- “Primary goal: …”
- “Non-goals: …”
- “Nice-to-have (only if cheap and non-risky): …”

### Dimension B: Constraint completeness (guidance; non-normative)

Section ID: semantic.dimensions.constraint-completeness

**What goes wrong:** the agent guesses constraints and makes unsafe/breaking changes.

**Criteria:**
- “Allowed” vs “Forbidden” actions are explicit.
- Constraint conflicts trigger STOP/ask.

**Patterns:**
- “Allowed: …”
- “Forbidden: …”
- “If a constraint blocks progress, STOP and ask for: …”

### Dimension C: Terminology and referent clarity (guidance; non-normative)

Section ID: semantic.dimensions.terminology

**What goes wrong:** ambiguous nouns (“deploy”, “artifact”, “client”) cause wrong actions.

**Criteria:**
- Key terms are defined (especially overloaded words).
- Referents are introduced once and reused consistently.

**Patterns:**
- “Definitions: …”
- “In this skill, ‘X’ means: …”

### Dimension D: Evidence anchoring (guidance; non-normative)

Section ID: semantic.dimensions.evidence-anchoring

**What goes wrong:** hallucinated repo facts; invented toolchains; unjustified conclusions.

**Criteria:**
- Requires confirming repo/tool facts before acting.
- Produces “evidence attachments” for non-trivial claims.

**Patterns:**
- “Confirm: `<file>` exists and indicates `<fact>`.”
- “Do not assume `<tool>`; check `<cmd> --version>` or inspect `<lockfile>`.”

### Dimension E: Decision sufficiency (guidance; non-normative)

Section ID: semantic.dimensions.decision-sufficiency

**What goes wrong:** “use judgment” leads to inconsistent outcomes.

**Criteria:**
- Decision points cover: missing inputs, environment constraints, scope expansion, risk boundary crossings, conflicting signals.
- Each decision uses: condition → action → alternative, with observable triggers.

**Patterns:**
- “If you observe `<signal>`, then `<action>`. Otherwise `<alternative>`.”
- “If two interpretations exist, STOP and ask for `<tie-break input>`.”

### Dimension F: Verification validity (guidance; non-normative)

Section ID: semantic.dimensions.verification

**What goes wrong:** checks don’t measure the intended property; “green” results don’t imply success.

**Criteria:**
- Quick check measures the primary success property.
- Failure interpretation is included (likely causes + next step).
- Uses a “verification ladder” (quick → narrow → broad) when appropriate.

**Patterns:**
- “Quick check: … Expected: … If fails: … Next step: …”
- “Verification ladder: 1) … 2) … 3) …”

### Dimension G: Artifact usefulness (guidance; non-normative)

Section ID: semantic.dimensions.artifact-usefulness

**What goes wrong:** outputs exist but are not reviewable or actionable.

**Criteria:**
- Output format is specified (structure, ordering, required fields).
- Outputs are tailored to the consumer (reviewer/operator).

**Patterns:**
- “Output format: …”
- “Each item must include: …”
- “Ordering: severity desc; then by component; then by file.”

### Dimension H: Minimality with rationale (guidance; non-normative)

Section ID: semantic.dimensions.minimality

**What goes wrong:** gold-plating, sprawling refactors, dependency churn.

**Criteria:**
- Enforces smallest correct change.
- Requires ask-first for dependency/tooling changes and scope expansions.

**Patterns:**
- “Prefer the smallest correct change.”
- “If you think you need a dependency upgrade, STOP and ask-first with justification: …”

### Dimension I: Calibration and uncertainty handling (guidance; non-normative)

Section ID: semantic.dimensions.calibration

**What goes wrong:** overconfident claims; silent skipping of checks.

**Criteria:**
- Requires labeling conclusions as Verified / Inferred / Assumed.
- Requires “Not run (reason)” for skipped checks.

**Patterns:**
- “Label claims as Verified / Inferred / Assumed.”
- “Not run (reason): … Run: `<cmd>` to verify.”

## Template library (copy/paste) (NORMATIVE templates)

Section ID: semantic.templates

These templates are provided to make semantic quality easy to copy/paste. Using them is OPTIONAL unless a parent skill mandates them.

### T1) Semantic contract block (template) (NORMATIVE template)

Section ID: semantic.templates.semantic-contract

```text
Semantic contract:
- Primary goal: <one sentence>
- Non-goals: <3–6 bullets>
- Hard constraints: <e.g., no network, no new deps, no API changes>
- Invariants (must not change): <public behavior/contracts>
- Acceptance signals: <2–4 observable success signals>
- Risk posture: <low/medium/high> and why
```

### T2) Scope fence (template) (NORMATIVE template)

Section ID: semantic.templates.scope-fence

```text
Scope fence:
- Touch only: <paths/modules>
- Must not touch: <paths/modules>
- Allowed edits: <types of changes>
- Forbidden edits: <types of changes>
If you need to cross the fence, STOP and ask-first.
```

### T3) Assumptions ledger (template) (NORMATIVE template)

Section ID: semantic.templates.assumptions-ledger

```text
Assumptions ledger:
- Verified: <facts confirmed via repo inspection/command output>
- Inferred: <reasonable inferences from verified facts>
- Unverified (do not rely on): <requires STOP or user confirmation>
```

### T4) Decision point phrasing with observable triggers (template) (NORMATIVE template)

Section ID: semantic.templates.observable-decision-point

```text
If <observable signal> is present (e.g., grep finds X / test Y fails / file Z exists), then <action>.
Otherwise, <alternative action>.
```

### T5) Verification ladder (template) (NORMATIVE template)

Section ID: semantic.templates.verification-ladder

```text
Verification ladder:
1) Quick check (primary signal): <command/observation>. Expected: <pattern>.
2) Narrow check (neighbors): <command/observation>. Expected: <pattern>.
3) Broad check (system confidence): <command/observation>. Expected: <pattern>.
If any rung fails, STOP and troubleshoot; do not continue.
```

### T6) Failure interpretation table (template) (NORMATIVE template)

Section ID: semantic.templates.failure-interpretation

```text
If <check> fails with <symptom>, likely causes are <A/B/C>.
Next step: <specific inspection or narrower test>.
```

### T7) Calibration wording (template) (NORMATIVE template)

Section ID: semantic.templates.calibration-wording

```text
Label conclusions as:
- Verified: supported by direct evidence (paths/commands/observations).
- Inferred: derived from verified facts; call out inference explicitly.
- Assumed: not verified; do not proceed without STOP/ask if assumption is material.

If a verification step was not run, report:
Not run (reason): <reason>. Run: <command>. Expected: <pattern>.
```

## Category semantic add-ons (guidance; non-normative)

Section ID: semantic.category-addons

These are add-on semantics that tighten common failure modes by category. Use alongside [skills-categories-guide.md](skills-categories-guide.md).

### Implementation playbooks (feature/change delivery) (guidance; non-normative)

Section ID: semantic.category-addons.implementation

- Add a “Compatibility surface” section (APIs/CLI/config/error messages) with explicit “unchanged vs changed” statements.
- Require an acceptance signal tied to the user-visible behavior (not just build/test success).
- Add a “Migration/rollout” decision point if behavior could be breaking.

### Debugging & triage (guidance; non-normative)

Section ID: semantic.category-addons.debugging

- Require capturing the “failure signature” (exact failing test name or error output shape).
- Require a one-paragraph “root cause statement” tied to evidence.
- Require a regression guard rationale (test/assertion) or a stated reason it’s infeasible.

### Refactoring & modernization (guidance; non-normative)

Section ID: semantic.category-addons.refactoring

- Require explicit invariants (“behavior-preserving means…”) and how they are verified.
- Add a scope fence, and a “diff sanity expectations” note (what should NOT change).
- If tests are weak, require characterization steps before refactor.

### Auditing & assessment (guidance; non-normative)

Section ID: semantic.category-addons.auditing

- Add a “claim strength policy”: global claims require broad coverage; sampled claims require confidence language.
- Enforce evidence trail minimums per finding: path + query + observation + recommended next step.

### Agentic workflows & pipelines (guidance; non-normative)

Section ID: semantic.category-addons.pipelines

- Require an idempotency contract: second run is a no-op or yields identical outputs.
- Add explicit “plan/apply/verify” separation and failure gates.
- Add a “partial run recovery” section (how to resume safely).

### Security changes (high-risk) (guidance; non-normative)

Section ID: semantic.category-addons.security

- Require a threat model summary (assets/actors/boundaries) before proposing changes.
- Require deny-path verification and rollback/escape hatch guidance.
- Forbid secrets in outputs/examples; require redaction rules.

## Anti-patterns (reviewer red flags) (guidance; non-normative)

Section ID: semantic.anti-patterns

- Unbounded verbs without acceptance signals (“improve”, “optimize”, “clean up”).
- Decision points that rely on “judgment” without observable triggers.
- Verification that only checks a proxy (compile/lint) when behavior correctness is the goal.
- Outputs that omit evidence/rationale, making review impossible.
- Silent skipping of verification (no “Not run (reason)” reporting).
- Implied environment assumptions (tooling/network) without checks or STOP/ask.

## Semantic review rubric (checklist + scoring) (guidance; non-normative)

Section ID: semantic.review

Use this to review a skill that already meets the strict spec.

### Reviewer checklist (guidance; non-normative)

Section ID: semantic.review.checklist

- Intent: primary goal + non-goals present and aligned with outputs.
- Constraints: hard constraints are explicit; unknown constraints trigger STOP/ask.
- Decisions: decision points reference observable triggers; cover common branches.
- Verification: quick check measures primary property; failure interpretation exists.
- Artifacts: output format is specified; outputs are reviewable/actionable.
- Calibration: “Verified/Inferred/Assumed” labeling is instructed; “Not run (reason)” is required.

### Scoring (optional) (guidance; non-normative)

Section ID: semantic.review.scoring

Score each dimension 0–2 (max 20). “Excellent” is typically ≥16 with no 0s in Constraints/Decisions/Verification.

1) Intent fidelity
2) Constraint completeness
3) Terminology clarity
4) Decision sufficiency
5) Evidence anchoring
6) Verification validity
7) Artifact usefulness
8) Minimality discipline
9) Calibration honesty
10) Offline/restricted handling


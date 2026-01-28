## Semantic quality dimensions (criteria and patterns)

This spec applies to the **body** of `SKILL.md`

“Semantic quality” here means: reducing ambiguity, forcing correct STOP/ask behavior, preventing agent drift, and making verification and artifacts measure what the skill intends.

### Dimension A: Intent fidelity

**What goes wrong:** the agent optimizes a proxy goal or expands scope.

**Criteria:**
- Primary goal is explicit and matches outputs/DoD.
- Non-goals prevent common drift.
- “Must-haves” vs “nice-to-haves” are distinguished.

**Patterns:**
- “Primary goal: ...”
- “Non-goals: ...”
- “Nice-to-have (only if cheap and non-risky): ...”

### Dimension B: Constraint completeness

**What goes wrong:** the agent guesses constraints and makes unsafe/breaking changes.

**Criteria:**
- “Allowed” vs “Forbidden” actions are explicit.
- Constraint conflicts trigger STOP/ask.

**Patterns:**
- “Allowed: ...”
- “Forbidden: ...”
- “If a constraint blocks progress, STOP and ask for: ...”

### Dimension C: Terminology and referent clarity

**What goes wrong:** ambiguous nouns (“deploy”, “artifact”, “client”) cause wrong actions.

**Criteria:**
- Key terms are defined (especially overloaded words).
- Referents are introduced once and reused consistently.

**Patterns:**
- “Definitions: ...”
- “In this skill, 'X’ means: ...”

### Dimension D: Evidence anchoring

**What goes wrong:** hallucinated repo facts; invented toolchains; unjustified conclusions.

**Criteria:**
- Requires confirming repo/tool facts before acting.
- Produces “evidence attachments” for non-trivial claims.

**Patterns:**
- “Confirm: `<file>` exists and indicates `<fact>`.”
- “Do not assume `<tool>`; check `<cmd> --version>` or inspect `<lockfile>`.”

### Dimension E: Decision sufficiency

**What goes wrong:** “use judgment” leads to inconsistent outcomes.

**Criteria:**
- Decision points cover: missing inputs, environment constraints, scope expansion, risk boundary crossings, conflicting signals.
- Each decision uses: condition → action → alternative, with observable triggers.

**Patterns:**
- “If you observe `<signal>`, then `<action>`. Otherwise `<alternative>`.”
- “If two interpretations exist, STOP and ask for `<tie-break input>`.”

### Dimension F: Verification validity

**What goes wrong:** checks don’t measure the intended property; “green” results don’t imply success.

**Criteria:**
- Quick check measures the primary success property.
- Failure interpretation is included (likely causes + next step).
- Uses a “verification ladder” (quick → narrow → broad) when appropriate.

**Patterns:**
- “Quick check: ... Expected: ... If fails: ... Next step: ...”
- “Verification ladder: 1) ... 2) ... 3) ...”

### Dimension G: Artifact usefulness

**What goes wrong:** outputs exist but are not reviewable or actionable.

**Criteria:**
- Output format is specified (structure, ordering, required fields).
- Outputs are tailored to the consumer (reviewer/operator).

**Patterns:**
- “Output format: ...”
- “Each item must include: ...”
- “Ordering: severity desc; then by component; then by file.”

### Dimension H: Minimality with rationale

**What goes wrong:** gold-plating, sprawling refactors, dependency churn.

**Criteria:**
- Enforces smallest correct change.
- Requires ask-first for dependency/tooling changes and scope expansions.

**Patterns:**
- “Prefer the smallest correct change.”
- “If you think you need a dependency upgrade, STOP and ask-first with justification: ...”

### Dimension I: Calibration and uncertainty handling

**What goes wrong:** overconfident claims; silent skipping of checks.

**Criteria:**
- Requires labeling conclusions as Verified / Inferred / Assumed.
- Requires “Not run (reason)” for skipped checks.

**Patterns:**
- “Label claims as Verified / Inferred / Assumed.”
- “Not run (reason): ... Run: `<cmd>` to verify.”

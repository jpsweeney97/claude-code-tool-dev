# Skills-as-Prompts (Strict Spec)

This document defines **normative prompt-engineering requirements** for Agent `SKILL.md` bodies (everything after frontmatter). It is intended for both **skill authors** and **reviewers**.

This spec is **host-agnostic**: it does not assume a particular CLI, OS, or permission model. If a skill depends on environment properties (network, tools, repo layout, permissions), it MUST declare them and MUST provide a fallback path when feasible.

## Quick navigation (non-normative)

Section ID: spec.quick-navigation

- For the minimum required structure, start at **Skill skeleton** and **Required content contract**.
- For pass/fail evaluation, start at **Reviewer checklist**, **Reviewer disposition**, and **Automatic FAIL reasons**.
- For higher-risk skills, start at **Risk tiering** and **Minimum requirements by tier**.
- For copy/paste-safe phrasing, use **Appendix A: Required wording patterns**.

## Machine-first contracts (routing invariants)

Section ID: spec.machine-first-contracts

This document is optimized for machine-first retrieval and routing. The following contracts are intended to be stable over time.

### Document ID

Section ID: spec.machine-first-contracts.document-id

Retrieval key: `spec=skills-as-prompts-strict`

### Section ID contract

Section ID: spec.machine-first-contracts.section-id-contract

- Every major section has a stable ID line of the form: `Section ID: spec.<id>`.
- IDs are stable; headings may change, but IDs MUST NOT be reused for different content.
- Recommended retrieval pattern:
  1. Retrieve `Spec index (machine-first)` for routing,
  2. then retrieve by `Section ID` for the minimal required chunk.

### Normativity contract

Section ID: spec.machine-first-contracts.normativity-contract

- Normative requirements are labeled using MUST / MUST NOT / REQUIRED / SHOULD / MAY.
- Non-normative content is explicitly marked as `(guidance; non-normative)` or `(NON-NORMATIVE)` or equivalent.
- Routing MUST prefer normative sections when generating enforcement logic.

### Fail-code contract (review automation)

Section ID: spec.machine-first-contracts.fail-code-contract

Automatic FAIL conditions are enumerated with stable fail codes of the form `FAIL.<code>`.
Use these codes in automated review outputs and when routing “what failed” → “what to fix”.

## Spec index (machine-first)

Section ID: spec.spec-index

Use this index to route requests and to retrieve only the necessary section.

| Purpose | Retrieve | Section ID |
|---|---|---|
| Minimal required structure | Required content contract + skeleton | `spec.required-content` |
| Pass/fail review | Reviewer checklist + fail reasons | `spec.review.checklist` / `spec.review.fail-codes` |
| Risk gating | Risk tiering + minimums | `spec.risk-tiering` |
| Wording templates | Appendix A templates | `spec.templates` |
| Objective check definition | Objective checks section | `spec.objective-checks` |

## Compliance summary (non-normative)

Section ID: spec.compliance-summary

Use this section to quickly understand and apply the spec. It is a convenience layer; the rest of this document remains the source of truth.

**Non-normative note:** capitalized modal words (e.g., MUST/SHOULD) in this summary are descriptive only. Normative requirements live in the main body below.

### Skill body contract (what every `SKILL.md` body MUST contain)

Section ID: spec.compliance-summary.skill-body-contract

The body MUST contain all 8 content areas (headings or equivalents), and they MUST be easy to find:

1. When to use
2. When NOT to use
3. Inputs (required/optional + constraints/assumptions)
4. Outputs (artifacts + Definition of Done)
5. Procedure (numbered steps)
6. Decision points (explicit branching logic)
7. Verification (at least one quick check; deep checks optional unless required by tier)
8. Troubleshooting (at least one common failure mode)

### Minimum “pass” checklist (reviewer quick scan)

Section ID: spec.compliance-summary.minimum-pass-checklist

- Outputs include **artifacts** and at least one **objective DoD check**.
- Procedure is numbered and includes at least one explicit **STOP/ask** step.
- Contains at least **two** explicit decision points (or a justified exception).
- Includes at least one **quick check** with an expected result shape.
- Declares non-universal assumptions (tools/network/permissions/repo layout) and provides a fallback when feasible.

### Risk tiers (what changes with risk)

Section ID: spec.compliance-summary.risk-tiers

- Low risk: baseline contract + one quick check + one troubleshooting entry.
- Medium risk: adds STOP/ask for ambiguity + SHOULD add a second verification mode + explicit non-goals against scope creep.
- High risk: adds ask-first gate(s) + at least two STOP/ask gates + at least two verification modes + rollback/escape hatch guidance when applicable.

## Table of contents (non-normative)

Section ID: spec.table-of-contents

- Normative language
- Key terms (non-normative)
- Scope
- Core principle
- Core invariants (REQUIRED)
- Skill skeleton (1-page; REQUIRED content contract)
- Required content contract (body)
- Allowed omissions (NORMATIVE)
- Terminology note: "STOP" (NORMATIVE)
- Major categories of skills (guidance; non-normative)
- Category tightening matrix (guidance; non-normative)
- Golden Definition-of-Done (DoD) patterns by category (guidance; non-normative)
- Prompt-engineering requirements
- Command mention rule (NORMATIVE)
- Category emphasis (guidance; non-normative)
- Reviewer checklist (body only)
- Reviewer worksheet (non-normative; quick scan)
- Release readiness checklist (this document) (NORMATIVE)
- Reviewer disposition (NORMATIVE)
- Automatic FAIL reasons (NORMATIVE)
- Risk tiering (guidance; normative minimums per tier)
- Glossary: failure modes and anti-patterns (NORMATIVE)
- Appendix A: Required wording patterns (NORMATIVE templates)
- Appendix B: Minimal compliant example skill body (NON-NORMATIVE exemplar)

## Normative language

Section ID: spec.normative-language

- **MUST / MUST NOT / REQUIRED**: mandatory.
- **SHOULD / RECOMMENDED**: expected for high quality; if omitted, the skill MUST explain why or why not applicable.
- **MAY / OPTIONAL**: allowed but not required.

Unless explicitly marked as guidance/non-normative, statements using **MUST / MUST NOT / REQUIRED** are normative requirements.

## Key terms (non-normative)

Section ID: spec.key-terms

These terms are used throughout this spec:

- **STOP**: defined in `Terminology note: "STOP" (NORMATIVE)`.
- **Ask-first**: a step that requests explicit user approval before a risky/breaking/destructive action. See `Appendix A.2 Ask-first for risky or breaking actions (NORMATIVE templates)`.
  - Note: Ask-first is typically used for risk approval gates; STOP is typically used for missing required inputs or ambiguity.
- **Artifact**: an output the agent produces (files, patches, reports, commands to run); see `1. Output contract (REQUIRED)`.
- **Objective check / DoD**: a checkable condition tied to outputs; see `1. Output contract (REQUIRED)` and `Skill skeleton (1-page; REQUIRED content contract)`.

## Scope

Section ID: spec.scope

This spec applies to the **body** of `SKILL.md`:

- It MAY reference templates/scripts/references.
- It MUST remain usable as a standalone workflow document.

Frontmatter requirements (e.g., `name`, `description`, `metadata.version`) are out of scope for this document.

## Core principle

Section ID: spec.core-principle

The skill body is "just a prompt", so it MUST be written like **production prompt code**:

- explicit about inputs and outputs,
- hard to mis-activate,
- resistant to missing context and time pressure,
- objectively verifiable.

## Core invariants (REQUIRED)

Section ID: spec.core-invariants

Every skill body MUST enforce the following invariants, either explicitly as rules or implicitly via required sections and checks:

1. **Activation boundaries**: the skill has clear "When to use" and "When NOT to use" guidance.

2. **Input sufficiency**: the skill enumerates required inputs and includes at least one STOP/ask step when required inputs are missing.

3. **Output contract**: the skill promises specific artifacts and includes objective checks (Definition of Done).

4. **Operational procedure**: the skill provides a numbered procedure that can be followed under time pressure.

5. **Branching clarity**: the skill contains explicit decision points for common branches; it does not rely on vague "use judgment".

6. **Verification-first posture**: the skill instructs at least one quick check and does not treat verification as optional fluff.

7. **Failure recovery**: the skill includes at least one troubleshooting path with symptoms/causes/next steps.

8. **Assumptions declared**: non-universal environment assumptions are stated:
   - network,
   - tools,
   - permissions,
   - repo layout;
   and offline/restricted fallbacks exist when feasible.

## Skill skeleton (1-page; REQUIRED content contract)

Section ID: spec.skill-skeleton

This is the canonical "skill skeleton" that skills SHOULD roughly follow. Equivalent headings/structure are allowed, but the same information MUST exist and MUST be easy to find.

1. **When to use**
2. **When NOT to use**
3. **Inputs**
   - Required
   - Optional
   - Constraints/assumptions (tools/network/permissions/repo)
4. **Outputs**
   - Artifacts
   - Definition of Done (objective checks)
5. **Procedure** (numbered steps)
6. **Decision points** (explicit If/then/otherwise)
7. **Verification**
   - Quick checks
   - Deep checks (optional)
8. **Troubleshooting**
   - Common failure modes (symptoms/causes/next steps)

## Required content contract (body)

Section ID: spec.required-content

The body of every `SKILL.md` MUST contain the following content areas, either as headings or content-equivalent sections:

1. **When to use** (boundaries and intent)
2. **When NOT to use** (anti-goals / STOP conditions)
3. **Inputs** (required/optional + assumptions)
4. **Outputs** (artifacts + Definition of Done)
5. **Procedure** (numbered steps)
6. **Decision points** (explicit branching logic)
7. **Verification** (quick check + optional deep checks)
8. **Troubleshooting** (at least one common failure mode)

If a reviewer cannot locate each area in under ~60 seconds, the skill SHOULD be revised for clarity (even if technically compliant).

**Category routing note (RECOMMENDED):** skills SHOULD include `Category: category=<id>` to enable deterministic routing (see [skills-categories-guide.md](skills-categories-guide.md)). Category declaration is RECOMMENDED for routing, but it is not required for strict compliance with this spec.

### Allowed omissions (NORMATIVE)

Section ID: spec.required-content-contract.allowed-omissions

The following omissions are allowed, but only under these conditions:

- **Deep checks**: MAY be omitted if the skill is Low risk or there is no meaningful deeper check available. If omitted for Medium/High risk, the skill MUST state why.
- **Offline/no-network fallback**: MUST be included when feasible. If truly impossible (e.g., the work inherently depends on a hosted service), the skill MUST say so and MUST include an explicit STOP/ask step that requests the minimum required pasted outputs or approvals.

### Terminology note: "STOP" (NORMATIVE)

Section ID: spec.required-content-contract.terminology-note-stop

In this document, **STOP** means the skill instructs the agent to pause execution and ask the user for clarification or approval before proceeding. A STOP step MUST be explicit (use the word "STOP" or an unambiguous equivalent) and MUST name exactly what input/approval is required.

### Terminology note: "ask-first" (NORMATIVE)

Section ID: spec.required-content-contract.terminology-note-ask-first

In this document, **ask-first** means the skill instructs the agent to request explicit user approval before executing a breaking, destructive, irreversible, or otherwise high-risk step. An ask-first step MUST be explicit (use the phrase "ask first" or an unambiguous equivalent) and MUST name the specific action(s) being approved (and, when feasible, the safer alternative such as dry-run/read-only or plan-only).

## Major categories of skills (guidance; non-normative)

Section ID: spec.major-categories-of-skills

The runtime generally treats skills as prompts, but in real repos skills cluster into a small number of categories. These categories are useful because they imply different failure modes and therefore different emphases in procedure and verification.

**Authoritative category definitions:** See [skills-categories-guide.md](skills-categories-guide.md) for the complete list of 13 categories with full definitions, retrieval keys, DoD checklists, decision points, and failure modes.

### Category list is extensible (guidance; non-normative)

Section ID: spec.major-categories-of-skills.category-list-is-extensible

This category list is not closed. Add a new category only when it meaningfully changes the **required emphasis** (inputs, verification, STOP/ask behavior, risk controls) due to different failure modes.

- **Map to an existing category** when:
  - the skill's procedure and DoD patterns are essentially the same, and
  - differences are just domain-specific details (tools/paths/commands).

- **Create a new category** when one or more of the following are true:
  - The skill needs a different *kind* of objective check (e.g., idempotency/dry-run vs unit tests vs evidence trails).
  - The dominant risks differ (e.g., automation mutates state; audits require reproducible evidence; design skills require compatibility/rollout clarity).
  - Reviewers routinely mis-apply the existing category's tightening expectations (inputs strictness, verification depth, decision-point density).

## Category tightening matrix (guidance; non-normative)

Section ID: spec.category-tightening-matrix

Use this matrix to decide how strict the skill SHOULD be. "High" means the skill SHOULD invest more words and guardrails in that column (and reviewers SHOULD be stricter). Category names and retrieval keys match [skills-categories-guide.md](skills-categories-guide.md).

| Category | Retrieval Key | Inputs | Verification | Decision Points | STOP/ask | Risk |
| -------- | ------------- | ------ | ------------ | --------------- | -------- | ---- |
| Meta-skills | `category=meta-skills` | Medium | Low–Medium | High | Medium | Medium |
| Auditing & assessment | `category=auditing-assessment` | High | High | High | High | Medium |
| Agentic workflows & pipelines | `category=agentic-pipelines` | High | High | High | High | High |
| Implementation playbooks | `category=implementation-playbooks` | Medium | Medium | High | Medium | Medium |
| Debugging & triage | `category=debugging-triage` | High | Medium | High | High | Medium |
| Refactoring & modernization | `category=refactoring-modernization` | Medium | High | Medium | Medium | Medium |
| Testing & quality | `category=testing-quality` | Low–Medium | Medium | Medium | Low | Low |
| Documentation & knowledge transfer | `category=documentation-knowledge` | Low–Medium | Low–Medium | Low | Low | Low |
| Build, tooling & CI | `category=build-tooling-ci` | High | Medium | Medium | Medium | Medium |
| Integration & evaluation | `category=integration-evaluation` | Medium | Medium | Medium | Medium | Medium |
| Security changes | `category=security-changes` | High | High | High | High | High |
| Data & migrations | `category=data-migrations` | High | High | High | High | High |
| Ops, release & incident runbooks | `category=ops-release-incident` | High | High | High | High | High |

Notes:

- "High inputs" means more up-front questions, stronger STOP/ask behavior, and explicit required context.
- "High risk" means explicit ask-first for dangerous actions, conservative defaults, and explicit non-goals.
- For full category definitions including DoD checklists and decision points, see [skills-categories-guide.md](skills-categories-guide.md).

## Golden Definition-of-Done (DoD) patterns by category (guidance; non-normative)

Section ID: spec.golden-definition-of-done-patterns-by-category

These are examples of **objective, checkable** DoD patterns. Skills SHOULD adapt them to their repo/tooling, but SHOULD preserve the "observable evidence" property. Categories match [skills-categories-guide.md](skills-categories-guide.md).

### Meta-skills (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.meta-skills

- **Produced artifact is runnable**: the generated workflow/skill has a numbered Procedure, at least two decision points, and at least one quick check (per this spec).
- **No hidden assumptions**: the artifact lists constraints/assumptions (tools/network/permissions) and includes a no-network/manual fallback when feasible.
- **Evaluation harness**: includes a simple "reviewer checklist" or acceptance checklist that can be applied in under ~5 minutes.

### Auditing & assessment (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.auditing-assessment

- **Evidence trail**: report includes "what was inspected" (paths/queries/samples) so findings are reproducible.
- **Severity + scope**: each finding has severity/impact and a stated scope (global vs sampled) with confidence level.
- **Action plan**: each high-severity finding includes concrete remediation steps and at least one verification check to confirm the fix.

### Agentic workflows & pipelines (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.agentic-pipelines

- **Idempotency**: documents idempotency/retry behavior and includes an objective check showing a second run is a no-op or produces the same result.
- **Safe default**: provides a dry-run/read-only mode (or equivalent) and makes mutating steps explicitly ask-first.
- **Observability**: includes logging/output contract that makes progress and failure states observable (expected output patterns).

### Implementation playbooks (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.implementation-playbooks

- **Tests + behavior**: new/updated tests cover the change; targeted test(s) pass and demonstrate the intended behavior.
- **Compatibility**: no breaking API/CLI/config change unless explicitly allowed; if breaking, migration/rollout steps are included as artifacts.
- **Docs updated**: user-facing behavior changes are documented with at least one runnable example and an explicit "gotchas" note when relevant.

### Debugging & triage (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.debugging-triage

- **Minimal repro**: a minimal reproducible case exists (test, script, or steps) and reliably fails before the fix and passes after.
- **Root cause statement**: a one-paragraph cause + evidence is produced (log line, diff, failing assertion) and ties to the fix.
- **Regression guard**: a regression test or assertion is added to prevent recurrence, and the quick check demonstrates it.

### Refactoring & modernization (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.refactoring-modernization

- **Invariants**: explicit statement of invariants ("public API unchanged", "behavior-preserving") and verification (tests/snapshots) supports it.
- **Diff sanity**: a deterministic scan shows only expected surface changes (e.g., no removed tests, no config drift outside scope).
- **Performance (when applicable)**: baseline vs after measurement exists and shows no regression beyond an agreed threshold.

### Testing & quality (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.testing-quality

- **Test correctness**: tests assert intended behavior (not implementation details); assertions match documented requirements.
- **Determinism**: tests produce consistent results across runs; no flaky tests introduced without explicit documentation.
- **Coverage scope**: test coverage is stated (unit/integration/e2e) and any gaps are documented with rationale.

### Documentation & knowledge transfer (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.documentation-knowledge

- **Doc build/render**: docs build or render command exits 0, or a deterministic check confirms links/code fences are valid.
- **Examples correctness**: examples are runnable/compilable (or explicitly marked as pseudocode) and match current API.
- **Change note**: includes a concise "what changed / who it affects" section suitable for PR description or release notes.

### Build, tooling & CI (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.build-tooling-ci

- **Reproducible command**: `make test`/`npm test`/equivalent exits 0 on a clean checkout with documented prerequisites.
- **Expected output shape**: linter/test output matches an expected pattern (e.g., "0 failures", "no violations").
- **Troubleshooting coverage**: at least one known common failure is documented with a deterministic fix path (env var, tool version, cache clear).
- **Config validity**: configuration parses/validates via a built-in check (lint/validate command) with a clean exit.

### Integration & evaluation (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.integration-evaluation

- **Constraint verification**: integration respects stated constraints (network, keys, permissions) and documents fallback when constraints aren't met.
- **Evaluation criteria**: selection/recommendation includes explicit criteria (cost, latency, compatibility) with evidence for each.
- **Smoke test**: integration is verified with at least one end-to-end check demonstrating expected behavior.

### Security changes (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.security-changes

- **No secret exposure**: no secrets written to disk or printed; logs/output redact sensitive values by rule.
- **Boundary verification**: authn/authz or permission change is verified by tests or a deterministic check; no "trust me" changes.
- **Ask-first honored**: skill records the point where user approval is required for risky changes and does not proceed without it.

### Data & migrations (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.data-migrations

- **Rollback plan**: migration includes explicit rollback steps and verification that rollback restores previous state.
- **Data validation**: pre- and post-migration checks confirm data integrity (row counts, checksums, constraint validation).
- **Dry run**: migration can be previewed without executing; destructive operations require explicit confirmation.

### Ops, release & incident runbooks (examples)

Section ID: spec.golden-definition-of-done-patterns-by-category.ops-release-incident

- **Dry run**: provides a dry-run command path and expected output; does not execute destructive actions by default.
- **Rollback plan**: produces a rollback section with concrete steps and decision points (when to rollback, how to verify recovery).
- **Release verification**: explicit preflight checks + post-deploy smoke checks are listed with expected outcomes.

## Prompt-engineering requirements

Section ID: spec.prompt-engineering

> Note: Sections under “Prompt-engineering requirements” are NORMATIVE unless explicitly labeled as guidance/non-normative.

### 1. Output contract (REQUIRED)

Section ID: spec.prompt-engineering-requirements.1-output-contract

The skill MUST define an **output contract** that is checkable without reading the agent's mind.

- Outputs MUST distinguish:
  - **Artifacts** the agent produces (files, patches, commands to run, reports), and
  - **Checks** the user/agent can run to validate success.
- The contract MUST include a **Definition of Done** with at least one objective check:
  - artifact existence/shape, OR
  - a concrete command/check with expected result pattern, OR
  - a deterministic logical condition (e.g., "All occurrences of X removed except ...").

The skill SHOULD include a **no-network** verification option when feasible.

### 2. Scope and non-goals (REQUIRED)

Section ID: spec.prompt-engineering-requirements.2-scope-and-non-goals

The skill MUST prevent common scope failures.

- It MUST state explicit boundaries ("When NOT to use", "Non-goals", or STOP rules).
- It MUST state any **default non-goals** that would otherwise surprise reviewers (examples):
  - no dependency upgrades,
  - no public API changes,
  - no destructive actions,
  - no schema/data migrations.
- If the skill can perform potentially breaking or destructive actions, it MUST include an explicit **ask-first** step.

### 3. Inputs and assumptions (REQUIRED)

Section ID: spec.prompt-engineering-requirements.3-inputs-and-assumptions

The skill MUST specify required inputs and what happens when they are missing.

- Inputs MUST be split into:
  - Required inputs (cannot start without),
  - Optional inputs (improve results),
  - Constraints/assumptions (environment, repo layout, permissions).
- The procedure MUST include at least one explicit **STOP / ask for clarification** step when required inputs are missing or ambiguous.

### 4. Procedure structure (REQUIRED)

Section ID: spec.prompt-engineering-requirements.4-procedure-structure

The skill MUST be operational, not aspirational.

- The procedure MUST be a **numbered** sequence of steps.
- Each step MUST be an action that can be followed without hidden assumptions.
- The procedure SHOULD prefer **inspect → decide → act → verify** over "act first".
- When making changes, the procedure SHOULD prefer smallest-correct change unless the skill's intent is explicitly broad (e.g., modernization).

### 5. Decision points (REQUIRED)

Section ID: spec.prompt-engineering-requirements.5-decision-points

The skill MUST contain explicit branching logic, not implicit "use judgment".

- It MUST include at least **2** decision points written in the form:
  - "If ... then ... otherwise ...".
- Decision points SHOULD cover common operational branches, such as:
  - tests exist vs. not,
  - network available vs. restricted,
  - breaking change allowed vs. prohibited,
  - user wants patch vs. explanation-only output.

If fewer than two decision points are truly applicable, the skill MUST explain why (briefly) and MUST still include at least one STOP/ask condition.

### 6. Verification (REQUIRED)

Section ID: spec.prompt-engineering-requirements.6-verification

Verification MUST be an instruction, not an afterthought.

- Verification MUST include at least one **quick check** that is concrete and executable or directly observable.
- Verification MAY include deeper checks when appropriate, but SHOULD be proportionate:
  - quick checks: seconds to a minute,
  - deep checks: slower, higher confidence.

## Objective checks, troubleshooting & progressive disclosure (NORMATIVE)

Section ID: spec.objective-checks

An **objective check** is a verification step that produces an **observable result** that a reviewer could evaluate without relying on subjective judgment.

### What counts (REQUIRED characteristics)

Section ID: spec.objective-checks.what-counts

An objective check MUST be at least one of:

- **Artifact existence/shape**: a file exists at a path; contains required headings/keys; matches a defined format.
- **Deterministic query/invariant**: a search/diff condition (e.g., "no remaining occurrences of X except ...").
- **Executable check with expected output shape**: a command whose success can be evaluated by exit code and/or a described output pattern.
- **Deterministic logical condition**: a precise statement that can be inspected (e.g., "All exported symbols remain unchanged except ...").

### What does NOT count (NORMATIVE anti-examples)

Section ID: spec.objective-checks.what-does-not-count

The following MUST NOT be used as the only DoD/verification:

- "Verify it works."
- "Ensure quality."
- "Make sure tests pass" (without specifying which tests and what "pass" means).
- "Check for errors" (without specifying where/how).

### Bad → good patterns (guidance)

Section ID: spec.objective-checks.bad-to-good-patterns

- Bad: "Make sure the feature works."
  - Good: "Quick check: run `<smoke command>`. Expected: exit 0 and output contains `<string>`."
- Bad: "Confirm no regressions."
  - Good: "Deep check: run the narrowest related test suite `<test command>`. Expected: 0 failures."
- Bad: "Verify config is correct."
  - Good: "Run `<config validate command>` or check that `config.yml` contains keys `<a,b,c>` with non-empty values."

### 7. Troubleshooting (REQUIRED)

Section ID: spec.objective-checks.7-troubleshooting

The skill MUST include at least one common failure mode with:

- Symptoms (what the user sees),
- Likely causes,
- What to do next (specific steps).

Troubleshooting SHOULD include at least one anti-pattern phrased as a likely temptation (e.g., "just disable the test").

### 8. Progressive disclosure (REQUIRED/RECOMMENDED)

Section ID: spec.objective-checks.8-progressive-disclosure

`SKILL.md` MUST be usable standalone. Deep material SHOULD be linked from `references/` rather than embedded.

If the skill depends on other skills/files, it MUST declare whether they are REQUIRED/RECOMMENDED/OPTIONAL and MUST include a fallback if not REQUIRED.

## Command mention rule (NORMATIVE)

Section ID: spec.command-mention

If the skill body instructs running a command (including build/test/lint/smoke/deploy-like commands), it MUST also specify:

1. **Expected result shape**: what constitutes success/failure (exit code and/or output pattern).
2. **Preconditions** (if non-obvious):
   - required tools,
   - required environment variables,
   - required working directory,
   - required permissions.

3. **Fallback path** when the command cannot be run in the current environment (missing tool, restricted permissions, no network), when feasible:
   - For Low risk skills: fallback SHOULD be provided.
   - For Medium risk skills: fallback SHOULD be provided; if omitted, the skill MUST explain why.
   - For High risk skills: fallback MUST be provided unless truly impossible; if impossible, the skill MUST STOP and ask the user to provide the missing capability or paste required outputs.
   

If the skill recommends running a command that MAY be destructive or irreversible (deploy, migration, deletes, force operations), it MUST additionally include:

4. **Ask-first gate**: explicit user approval language before running the command.
5. **Dry-run or read-only alternative** when feasible.

### Template (copy/paste)

Section ID: spec.command-mention-rule.template

- "Run: `<command>` (from `<dir>`). Expected: `<exit/output pattern>`."
- "If you cannot run this (missing `<tool>` / restricted permissions / no network), STOP and ask the user to provide: `<command output/logs>` or perform manual inspection: `<manual steps>`."

## Category emphasis (guidance; non-normative)

Section ID: spec.category-emphasis

Skill categories differ mainly in how strict they SHOULD be about verification and STOP rules. See [skills-categories-guide.md](skills-categories-guide.md) for full definitions. Quick reference:

- **Meta-skills**: activation boundaries, input/output contracts, objective evaluation of produced artifacts.
- **Auditing & assessment**: evidence capture, sampling strategy, severity scoring, actionable remediation.
- **Agentic pipelines**: idempotency, safe retries, dry-run modes, environment/permissions assumptions.
- **Implementation playbooks**: boundaries, backward-compat decision points, tests/docs DoD.
- **Debugging & triage**: evidence-first steps, STOP/ask for repro/logs, regression guards.
- **Refactoring**: behavior-preserving boundaries, invariants verification.
- **Testing & quality**: test correctness, determinism, coverage scope.
- **Documentation**: examples validity, doc-build/link checks.
- **Build, tooling & CI**: reproducibility, troubleshooting clarity, config validity.
- **Integration & evaluation**: constraint verification, evaluation criteria, smoke tests.
- **Security changes**: ask-first, explicit assumptions, conservative defaults.
- **Data & migrations**: rollback plan, data validation, dry-run.
- **Ops & incident runbooks**: rollback/canary branches, non-destructive posture, dry-run checks.

## Reviewer checklist (body only)

Section ID: spec.review.checklist

Reviewers MUST verify:

- The skill body contains all required content areas (see `Required content contract (body)`) and is findable quickly.
- Outputs include artifacts + objective DoD checks.
- Procedure is numbered, operational, and includes at least one STOP/ask step.
- At least 2 explicit decision points exist (or a justified exception).
- Verification includes at least one concrete quick check.
- Troubleshooting includes at least one actionable failure mode (symptoms/causes/next steps).
- Assumptions are declared (network/tools/permissions/repo layout) and include fallback when feasible.

### Machine-ingest block (YAML; NORMATIVE mirror)

Section ID: spec.review.machine-ingest.v1

```yaml
schema: skills_as_prompts_review_v1
spec: skills-as-prompts-strict
section_id: spec.review.machine-ingest.v1

reviewer_checklist:
  - id: CHECK.required-content-areas
    requirement: MUST
    description: Required content areas exist and are findable quickly.
    maps_to_section_id: spec.required-content
  - id: CHECK.outputs-have-objective-dod
    requirement: MUST
    description: Outputs include artifacts and at least one objective DoD check.
    maps_to_section_id: spec.objective-checks
  - id: CHECK.procedure-numbered-with-stop-ask
    requirement: MUST
    description: Procedure is numbered/operational and includes at least one explicit STOP/ask step.
    maps_to_section_id: spec.prompt-engineering-requirements.4-procedure-structure
  - id: CHECK.two-decision-points-or-exception
    requirement: MUST
    description: At least two explicit decision points exist (or a justified exception).
    maps_to_section_id: spec.prompt-engineering-requirements.5-decision-points
  - id: CHECK.verification-has-quick-check
    requirement: MUST
    description: Verification includes at least one concrete quick check with expected result shape.
    maps_to_section_id: spec.prompt-engineering-requirements.6-verification
  - id: CHECK.troubleshooting-present
    requirement: MUST
    description: Troubleshooting includes at least one actionable failure mode (symptoms/causes/next steps).
    maps_to_section_id: spec.objective-checks.7-troubleshooting
  - id: CHECK.assumptions-declared-with-fallback
    requirement: MUST
    description: Assumptions are declared (tools/network/permissions/repo layout) and include fallback when feasible.
    maps_to_section_id: spec.prompt-engineering-requirements.3-inputs-and-assumptions

fail_codes:
  - code: FAIL.missing-content-areas
    description: One or more required content areas are absent or not findable.
    implies_check_id: CHECK.required-content-areas
  - code: FAIL.no-objective-dod
    description: Outputs lack at least one objective, checkable DoD condition.
    implies_check_id: CHECK.outputs-have-objective-dod
  - code: FAIL.no-stop-ask
    description: No explicit STOP/ask step for missing inputs or ambiguity.
    implies_check_id: CHECK.procedure-numbered-with-stop-ask
  - code: FAIL.no-quick-check
    description: Verification lacks a concrete quick check with expected result shape.
    implies_check_id: CHECK.verification-has-quick-check
  - code: FAIL.too-few-decision-points
    description: Fewer than two explicit decision points and no justified exception.
    implies_check_id: CHECK.two-decision-points-or-exception
  - code: FAIL.undeclared-assumptions
    description: Relies on non-universal tools/network/permissions/repo structure without declaring assumptions/fallbacks.
    implies_check_id: CHECK.assumptions-declared-with-fallback
  - code: FAIL.unsafe-default
    description: Default procedure performs breaking/destructive/irreversible actions without an ask-first gate.
    implies_check_id: CHECK.procedure-numbered-with-stop-ask
  - code: FAIL.non-operational-procedure
    description: Procedure is not numbered or is generic/non-executable.
    implies_check_id: CHECK.procedure-numbered-with-stop-ask
```

## Reviewer worksheet (non-normative; quick scan)

Section ID: spec.reviewer-worksheet

Use this as a fast, checklist-style pass. It is a convenience layer; it does not add requirements beyond the NORMATIVE sections below.

### Pass/Fail gate (map to `Automatic FAIL reasons (NORMATIVE)`)

Section ID: spec.reviewer-worksheet.pass-fail-gate

- [ ] All required content areas exist and are findable quickly.
- [ ] Outputs include at least one objective, checkable DoD condition.
- [ ] Procedure includes explicit STOP/ask behavior (missing inputs / ambiguity).
- [ ] Verification includes at least one concrete quick check with expected result shape.
- [ ] Contains at least two explicit decision points (or a justified exception).
- [ ] Assumptions are declared (tools/network/permissions/repo structure) with fallback when feasible.
- [ ] Default procedure is safe (ask-first gate for breaking/destructive/irreversible actions).
- [ ] Procedure is operational (numbered; executable steps; not generic advice).

### Notes checklist (map to SHOULD-level guidance)

Section ID: spec.reviewer-worksheet.notes-checklist

- [ ] Uses the smallest correct change; avoids scope creep (dependency upgrades/refactors) unless asked-first.
- [ ] Includes no-network/manual fallback or “paste outputs” path where external deps exist.
- [ ] Troubleshooting includes symptoms/causes/next steps and at least one “temptation” anti-pattern.

## Release readiness checklist (this document) (NORMATIVE)

Section ID: spec.release-readiness-checklist

Before publishing this spec as an "official" reference, the maintainer/reviewer MUST verify:

- **Normative scope is unambiguous**:
  - sections are clearly marked as (NORMATIVE) vs (guidance; non-normative), and
  - there are no accidental lowercase modal verbs outside guidance/examples.

- **No self-contradictions**: requirements do not conflict (e.g., decision-point minimums align with tier minimums).
- **Terminology is defined**: STOP, ask-first, objective check, artifact, and Definition of Done are defined or referenced.
- **Actionability**: every MUST-level requirement is written so a reviewer can judge pass/fail without subjective interpretation.
- **Examples are labeled**: exemplars are explicitly NON-NORMATIVE and cannot be misread as mandatory templates.

## Reviewer disposition (NORMATIVE)

Section ID: spec.reviewer-disposition

Reviewers MUST issue one of: **PASS**, **PASS-WITH-NOTES**, or **FAIL**.

- **PASS**: Meets all MUST requirements in this document; any notes are stylistic only.
- **PASS-WITH-NOTES**: Meets all MUST requirements, but has one or more SHOULD-level gaps that are worth addressing.
- **FAIL**: Violates one or more MUST requirements or contains a safety gap that makes correct application unreliable.

### Automatic FAIL reasons (NORMATIVE)

Section ID: spec.review.fail-codes

A review MUST be **FAIL** if any of the following are true:

- **FAIL.missing-content-areas — Missing content areas**: one or more required content areas (8-section contract) is:
  - absent, or
  - not findable.

- **FAIL.no-objective-dod — No objective DoD**: outputs do not include at least one objective, checkable Definition-of-Done condition.

- **FAIL.no-stop-ask — No STOP/ask behavior**: the procedure lacks any explicit STOP/ask step for:
  - missing required inputs, or
  - ambiguity.
- **FAIL.no-quick-check — No quick check**: Verification lacks a concrete quick check with expected result shape.

- **FAIL.too-few-decision-points — No decision points**: fewer than two explicit "If ... then ... otherwise ..." decision points exist and there is no justified exception.
- **FAIL.undeclared-assumptions — Undeclared assumptions**: the skill relies on non-universal tools/network/permissions/repo structure without declaring constraints/assumptions.

- **FAIL.unsafe-default — Unsafe default**: the default procedure performs breaking/destructive/irreversible actions without an ask-first gate.
- **FAIL.non-operational-procedure — Non-operational procedure**: procedure is:
  - not numbered, or
  - written as generic advice without executable steps.

## Risk tiering (guidance; normative minimums per tier)

Section ID: spec.risk-tiering

Skills vary widely in blast radius. Use the tiers below to choose the minimum level of guardrails. This section is standalone: it does not assume a particular host/tooling, only the concepts defined in this document.

### Risk tier selection rule (guidance)

Section ID: spec.risk-tiering.selection-rule

To reduce reviewer disagreement, use this deterministic routing rule:

1. **Default** to the `Typical risk:` of the chosen category (from [skills-categories-guide.md](skills-categories-guide.md)).
2. If the category lists a range (`low→medium`, `medium→high`), **round up** when uncertain.
3. If the skill includes **any mutating step** (writes/deletes/deploys/migrations/force operations), treat it as **High risk** until the procedure explicitly gates those steps with ask-first/STOP rules and includes rollback/escape-hatch guidance where applicable.
4. If multiple categories plausibly apply, choose the higher `Typical risk:` category unless the skill explains why the lower tier is appropriate.

Clarification: this “mutating step ⇒ High risk” rule is a conservative default intended to force explicit gating and rollback/escape-hatch thinking. If mutating steps are fully gated and the blast radius is bounded and reversible, reviewers MAY treat the skill as Medium risk when the category and scope justify it.

### Tier definitions (guidance)

Section ID: spec.risk-tiering.tier-definitions

- **Low risk**: primarily produces information or documentation:
  - changes are trivial or easily reversible, and
  - there is minimal chance of breaking consumers.
  - Examples: docs edits, review checklists, reference lookups.
- **Medium risk**: changes code/config in ways that can break tests or behavior but are bounded and reversible; minimal external impact when wrong.
  - Examples: small bug fixes, internal refactors, routine scaffolding.
- **High risk**: changes one or more of:
  - security boundaries,
  - production ops/release steps,
  - data/schema,
  - dependencies,
  - public contracts;
  and errors are costly or hard to roll back.
  - Examples: authn/authz changes, deployment/runbooks, migrations/backfills, breaking API/CLI changes.

### Minimum requirements by tier (NORMATIVE)

Section ID: spec.risk-tiering.minimum-requirements-by-tier

These are **minimum** requirements. A skill MAY always be stricter than its tier.

#### Low risk (minimum)

- MUST include all required content areas, including one quick check and one troubleshooting entry.

- STOP/ask: MUST include at least one STOP/ask step for missing required inputs.

- Verification: at least one quick check; deep checks optional.
- Decision points: at least two; exceptions MUST be justified per this document.

#### Medium risk (minimum)

- MUST include all Low risk minimums.
- STOP/ask: MUST include at least one STOP/ask step for ambiguity in scope or success criteria (not only missing inputs).
- Verification: MUST include a quick check and SHOULD include a second verification mode when feasible (e.g., narrow test suite or build/config validation).
- Non-goals: MUST explicitly call out common scope creep items relevant to the repo (e.g., dependency upgrades, unrelated refactors).

#### High risk (minimum)

- MUST include all Medium risk minimums.

- Ask-first: MUST include an explicit ask-first gate before any breaking/destructive/irreversible action.
- STOP/ask: MUST include at least **two** STOP/ask gates:
  - one for missing/ambiguous required inputs, and
  - one for risk approval (breaking/destructive) or environment mismatch (permissions/network/tools).
- Verification: MUST include at least **two** verification modes:
  - a quick check, and
  - a deeper check or independent validation (tests/build/smoke/validation) appropriate to the risk.
- Troubleshooting: MUST include at least one failure mode that covers partial success or rollback/escape hatch guidance when applicable.

## Glossary: failure modes and anti-patterns (NORMATIVE)

Section ID: spec.glossary-failure-modes-and-anti-patterns

This glossary defines common failures that `SKILL.md` bodies MUST be written to prevent. Reviewers SHOULD use these terms when giving feedback.

- **Over-broad activation**: The skill triggers for requests outside its intended scope due to:
  - vague "When to use" guidance, or
  - missing "When NOT to use" boundaries.
  - REQUIRED prevention:
    - explicit "When NOT to use" bullets, and
    - at least one STOP/ask condition for ambiguity.

- **Implicit assumptions**: The skill relies on:
  - unstated environment facts (tools installed, network available, repo layout), or
  - unstated user intent.
  - REQUIRED prevention:
    - "Inputs → Constraints/assumptions", plus
    - fallback guidance when assumptions are not met.

- **Premature solutioning**: The procedure edits files before obtaining enough evidence to justify changes:
  - repro,
  - logs,
  - clear success criteria.
  - REQUIRED prevention:
    - an inspect/evidence step before write actions, and
    - a STOP/ask step when evidence is missing.

- **Scope creep**: The skill expands beyond the requested change (refactors, dependency upgrades, unrelated cleanup) without user intent.
  - REQUIRED prevention: explicit non-goals and ask-first for breaking/risky actions.

- **Verification theater**: The skill lists "verification" but the checks are non-executable, non-specific, or disconnected from the claimed outcome.
  - REQUIRED prevention: at least one concrete quick check with an expected result shape tied to the DoD.

- **Decision-point omission**: The skill says "use judgment" instead of encoding the branch, leading to inconsistent behavior under pressure.
  - REQUIRED prevention: at least two explicit "If ... then ... otherwise ..." decision points (or a justified exception).

- **Unsafe default**: The skill's default behavior performs destructive, breaking, or irreversible actions without an ask-first gate.
  - REQUIRED prevention: explicit ask-first step and conservative defaults in high-risk categories.

- **Unrecoverable procedure**: When a step fails, the skill provides no recovery path (no troubleshooting, no next steps).
  - REQUIRED prevention: at least one troubleshooting entry with symptoms/causes/next steps.

- **Non-portable instructions**: The procedure depends on host-specific behavior without declaring requirements or providing alternatives.
  - REQUIRED prevention: declare assumptions; provide offline/restricted fallbacks when feasible.

## Appendix A: Required wording patterns (NORMATIVE templates)

Section ID: spec.templates

Use the following copy/paste-safe phrases verbatim or nearly verbatim. Skills MAY add detail, but MUST NOT weaken the intent.

### A.1 STOP / ask for clarification

Section ID: spec.appendix-a-required-wording-patterns.a-1-stop-ask-for-clarification

```text
"**STOP. Ask the user for:** <missing required input>. **Do not proceed** until it is provided."
"**STOP. The request is ambiguous. Ask:** <clarifying question(s)>. **Proceed only after** the user confirms <target outcome>."
```

### A.2 Ask-first for risky or breaking actions

Section ID: spec.appendix-a-required-wording-patterns.a-2-ask-first-for-risky-or-breaking-actions

```text
"**Ask first:** This step may be breaking/destructive (<risk>). **Do not do it** without explicit user approval."
"If the user does not explicitly approve <action>, **skip it** and provide a safe alternative (<alternative>)."
```

### A.3 Evidence-first (debugging/triage/refactor safety)

Section ID: spec.appendix-a-required-wording-patterns.a-3-evidence-first

```text
"**Do not edit files yet.** First collect evidence by: <repro/log/inspection step>."
"State a **root cause hypothesis** and the **evidence** that supports it before implementing changes."
```

### A.4 Minimal-change default

Section ID: spec.appendix-a-required-wording-patterns.a-4-minimal-change-default

```text
"Prefer the **smallest correct change** that satisfies the Definition of Done."
"Do not refactor unrelated code. If refactoring appears necessary, **STOP and ask** for approval."
```

### A.5 Verification requirements

Section ID: spec.appendix-a-required-wording-patterns.a-5-verification-requirements

```text
"Run/perform this **quick check**: <command or observation>. **Expected result:** <pattern>."
"If the quick check fails, **do not continue**; go to Troubleshooting and resolve the failure first."
```

### A.6 Offline/restricted-environment fallback

Section ID: spec.appendix-a-required-wording-patterns.a-6-offline-restricted-environment-fallback

```text
"If network access is unavailable/restricted, **do not attempt downloads/installs**. Ask the user to paste: <docs/logs/config excerpt>."
"If required tools are missing and cannot be installed, provide a **manual inspection** fallback: <what to inspect>."
```

### A.7 Decision-point phrasing

Section ID: spec.appendix-a-required-wording-patterns.a-7-decision-point-phrasing

```text
"If <condition>, then <action>. Otherwise, <alternative action>."
"If <constraint is violated>, then **STOP** and ask for approval or additional input. Otherwise, continue."
```

## Appendix B: Minimal compliant example skill body (NON-NORMATIVE exemplar)

Section ID: spec.appendix-b-minimal-compliant-example-skill-body

This is an example of a small, compliant skill body that follows the skeleton and includes objective checks. Adapt to your repo; do not copy tool-specific commands if your environment differs.

### Notes on the exemplar (NON-NORMATIVE)

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.notes-on-the-exemplar

- The headings are illustrative; any structure that preserves the required content areas is acceptable.
- The example is intentionally small. Real skills SHOULD add repo-specific commands, paths, and troubleshooting.

### When to use this skill

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.when-to-use-this-skill

- Use when you need to fix a narrow bug in a codebase and can validate the change with an existing test or a minimal repro.

### When NOT to use this skill

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.when-not-to-use-this-skill

- Do not use for dependency upgrades, large refactors, schema/data migrations, or security boundary changes (authn/authz/crypto).
- STOP if the user cannot state the expected behavior or provide a failing example.

### Inputs

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.inputs

- Required:
  - A description of expected vs actual behavior.
  - Either (a) a failing test name/command, or (b) steps to reproduce the failure.
- Optional:
  - Logs/error output, stack trace, related PR/issue link, environment details.
- Constraints/assumptions:
  - Network access is optional. Do not install dependencies without approval.
  - Assume repo-local conventions and avoid unrelated edits.

### Outputs

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.outputs

- Artifacts:
  - A minimal code/config patch that fixes the bug.
  - A regression test or other deterministic guard when feasible.
  - A short "root cause + fix" note (1–5 bullets).
- Definition of Done (objective checks):
  - The repro/test that previously failed now passes.
  - No unrelated tests are broken (run the smallest relevant test suite available).

### Procedure

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.procedure

1. Identify the exact failure signal (failing test name or repro step and the observed output).
2. **Do not edit files yet.** Inspect relevant code paths and state a root cause hypothesis + supporting evidence.
3. Implement the smallest correct change that addresses the hypothesis.
4. Add or adjust a regression guard (test/assertion) unless clearly not feasible; if not feasible, state why.
5. Update the "root cause + fix" note.

### Decision points

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.decision-points

- If there is an existing failing test, then run/focus on that test. Otherwise, create a minimal repro (test or steps) before making changes.
- If fixing the bug appears to require a breaking change or dependency upgrade, then **STOP** and ask for explicit approval. Otherwise, proceed with a minimal patch.

### Verification

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.verification

- Quick checks:
  - Run the previously failing test/repro. Expected result: it passes / no longer reproduces.
- Deep checks (optional):
  - Run the narrowest related test suite or build step. Expected result: clean exit.

### Troubleshooting

Section ID: spec.appendix-b-minimal-compliant-example-skill-body.troubleshooting

- Common failure: "The test still fails after the patch."
  - Symptoms: the same assertion/error output persists.
  - Likely causes: wrong code path fixed; missing edge case; test not exercising intended path.
  - What to do next: re-check repro assumptions, add temporary logging/inspection, narrow the failing input, and update the hypothesis before further edits.

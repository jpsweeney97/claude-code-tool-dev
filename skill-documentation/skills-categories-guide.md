# Skill Categories Guide (Non-Normative)

Retrieval key: `spec=skills-categories-guide`

This guide provides category-specific guidance for writing and reviewing `SKILL.md` bodies.

- **Status:** MIXED
  - Category content: NON-NORMATIVE (guidance only).
  - Machine-first routing/format contracts: NORMATIVE (for automation stability).
- **Structural source of truth:** [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) (all MUST/SHOULD requirements).
- **Scope of normativity in this file:** only sections explicitly labeled “(NORMATIVE)” are normative; everything else is guidance.
- **Primary objective:** make category guidance easy to retrieve, copy/paste, and apply consistently.

## Retrieval notes (for LLMs and humans)
Section ID: categories.retrieval-notes

To retrieve guidance quickly:

1. Identify the category using `Category selection (decision tree)` or the `Category index`.
2. Jump to the category header: `## <Category name>`.
3. Within a category, jump to the canonical subheading: `### <Category> — <Section>` (e.g., `Input contract`, `DoD checklist (objective)`, `Decision points library`).

Example retrieval queries:

1. Find decision gates for schema/data work: search `category=data-migrations` then `— Decision points library`.
2. Find how to verify a refactor: search `category=refactoring-modernization` then `— Verification menu`.
3. Find audit evidence requirements: search `category=auditing-assessment` then `— Output contract`.
4. Find safe gating for auth changes: search `category=security-changes` then `— DoD checklist (objective)` and `— Decision points library`.

Canonical per-category subheadings (every category SHOULD include all of these for consistent retrieval). Note: categories may add extra subheadings; also, some legacy categories may use the shorter prefix format `### <Category> — <Section>` without the full canonical phrase.

1. `<Category> — Intent / typical use cases`
2. `<Category> — When NOT to use (common misfires)`
3. `<Category> — Input contract`
4. `<Category> — Output contract`
5. `<Category> — DoD checklist (objective)`
6. `<Category> — Verification menu`
7. `<Category> — Decision points library (copy/paste-ready)`
8. `<Category> — Failure modes & troubleshooting`
9. `<Category> — Anti-patterns (reviewer red flags)`
10. `<Category> — Mini exemplar (NON-NORMATIVE)`

## Machine-first contracts (routing invariants)
Section ID: categories.machine-first-contracts

These are design constraints for machine-first retrieval/routing.

- **Status:** NORMATIVE (routing/format contract). Skills SHOULD follow these invariants for routing stability; automated checks MAY emit notes when they are missing.

### Key stability contract
Section ID: categories.machine-first-contracts.key-stability

- `Retrieval key: category=<id>` is the stable identifier for a category.
- Never reuse a `category=<id>` for a different category, even if the old category is removed or renamed.
- If a category display name changes, keep `category=<id>` unchanged.
- If a category is split, keep the original `category=<id>` for the “primary” successor and introduce new `category=<id>` keys for the others.
- If categories are merged, keep the `category=<id>` of the dominant successor and list the merged key(s) as deprecated aliases.

### Risk hint legend
Section ID: categories.machine-first-contracts.risk-hint-legend

`Typical risk:` is an advisory routing hint:

- `low`: doc/prompt output only; changes are generally non-breaking and low blast radius.
- `medium`: code/tooling changes likely; moderate blast radius; verification should be explicit and scoped.
- `high`: security/data/ops boundaries or irreversible actions possible; ask-first/STOP gates and rollback guidance are expected.
- `low→medium` / `medium→high`: depends heavily on scope/environment; route to stricter verification/gating if uncertain.

### Section retrieval contract
Section ID: categories.machine-first-contracts.section-retrieval-contract

- Each category MUST include:
  - a `Retrieval key: category=<id>` line,
  - a `Typical risk:` line,
  - the full canonical subheading set.
- Subheadings are stable retrieval anchors. Prefer retrieving by:
  - `category=<id>` + `section=<section-id>` (see `Section IDs` below),
  - or `category=<id>` + the exact heading text.

## Category index (quick lookup)
Section ID: categories.category-index

Each category is listed with its dominant failure mode; pick the closest match.

| ID (stable) | Category (display) | Typical risk | Dominant failure mode (what goes wrong) | Common search synonyms (non-exhaustive) |
|---|---|---|---|---|
| `category=meta-skills` | Meta-skills (prompt/workflow composition) | low | Artifact is “nice” but not executable (missing DoD/decision points/verification) | prompt, checklist, rubric, template, meta, skill authoring |
| `category=auditing-assessment` | Auditing & assessment (codebase/system audits) | low→medium | Claims without reproducible evidence (missing scope/method/evidence trail) | audit, review, assessment, findings, report, evidence |
| `category=agentic-pipelines` | Agentic workflows & pipelines (automation/orchestration) | medium→high | Unsafe-by-default or non-idempotent orchestration (ungated mutation, weak verification) | pipeline, workflow, automation, orchestration, runbook-ish |
| `category=implementation-playbooks` | Implementation playbooks (feature/change delivery) | medium | Scope creep or breaking changes without approval; unvalidated patches | implement, feature, change, ship, add behavior, integrate |
| `category=debugging-triage` | Debugging & triage (root cause + minimal fix) | low→medium | Editing before evidence; fixes without root cause or regression guard | debug, triage, bugfix, regression, failing test, crash |
| `category=refactoring-modernization` | Refactoring & modernization (behavior-preserving change) | medium | Accidental behavior change; refactor sprawl without boundaries | refactor, cleanup, modernization, restructure, rename, simplify |
| `category=testing-quality` | Testing & quality (tests, QA, verification assets) | low→medium | Flaky/non-deterministic tests; assertions don’t match intended behavior | test, QA, coverage, regression test, fixture, mock, flaky |
| `category=documentation-knowledge` | Documentation & knowledge transfer (docs, guides, runbooks) | low | Docs aren’t runnable (missing prerequisites/verification, mismatched steps) | docs, guide, how-to, onboarding, troubleshooting, readme |
| `category=build-tooling-ci` | Build, tooling & CI (developer experience workflows) | medium | Tooling changes break workflows; unapproved changes to build/CI semantics | build, tooling, CI, lint, format, scripts, workflows |
| `category=integration-evaluation` | Integration & evaluation (third-party systems, vendor choices) | medium | Recommendations/integrations ignore constraints (network/keys), unverifiable in practice | integration, vendor, API, SDK, evaluation, selection |
| `category=security-changes` | Security changes (high-risk) | high | Security boundary regressions; secret mishandling; no rollback | auth, authn, authz, permissions, crypto, tokens, secrets |
| `category=data-migrations` | Data & migrations (high-risk) | high | Irreversible data loss; schema drift; unvalidated migrations | migration, schema, database, backfill, data fix, retention |
| `category=ops-release-incident` | Ops, release & incident runbooks (high-risk) | high | Ambiguous high-stress steps; missing abort/rollback branches; unsafe defaults | ops, release, deploy, rollback, incident, oncall, runbook |

## Section IDs (machine-first)
Section ID: categories.section-ids

For deterministic retrieval, each canonical per-category section maps to a stable `section=<id>`:

1. `section=intent`
2. `section=when-not`
3. `section=inputs`
4. `section=outputs`
5. `section=dod`
6. `section=verification`
7. `section=decision-points`
8. `section=troubleshooting`
9. `section=anti-patterns`
10. `section=exemplar`

Recommended retrieval pattern:

- First retrieve the `Category index` (for routing).
- Then retrieve by `category=<id>` + `section=<id>` via heading match.


## How to use this guide (procedure)
Section ID: categories.how-to-use

1. Classify the skill using the decision tree (next section).
2. Use the chosen category's **Input contract** and **Output contract** to draft the skill.
3. Use the category's **DoD checklist** to ensure the draft is executable.
4. Validate the final draft against the strict spec's required content contract and reviewer checklist.

## Category selection (decision tree)
Section ID: categories.decision-tree

Choose the category based on the skill's _dominant failure mode_ (what goes wrong most often if this skill is underspecified):

- If the skill primarily produces a **prompt/workflow artifact** (new skills, checklists, review rubrics), choose **Meta-skills (composition)**.
- If the skill primarily produces a **findings report** (claims + evidence + recommendations), choose **Auditing & assessment**.
- If the skill primarily produces a **multi-step orchestration** (tool-driven sequences with gates/verification), choose **Agentic workflows & pipelines**.
- If the skill primarily produces a **code/config change** in an existing repo, choose **Implementation playbooks**.
- If the skill primarily resolves a **bug/regression**, choose **Debugging & triage**.
- If the skill primarily changes **architecture or structure** without changing behavior, choose **Refactoring & modernization**.
- If the skill primarily produces **tests, fixtures, or QA coverage**, choose **Testing & quality**.
- If the skill primarily produces **documentation/training materials**, choose **Documentation & knowledge transfer**.
- If the skill primarily creates/adjusts **developer tooling and CI**, choose **Build, tooling & CI**.
- If the skill primarily deals with **security-sensitive change**, choose **Security changes (high-risk)**.
- If the skill primarily handles **data changes (schemas/migrations)**, choose **Data & migrations (high-risk)**.
- If the skill primarily plans or executes **releases/runbooks/incident response**, choose **Ops, release & incident runbooks (high-risk)**.
- If the skill primarily integrates or evaluates **vendors/APIs**, choose **Integration & evaluation**.

If the skill is hybrid:

- Choose the closest category by dominant failure mode.
- Borrow individual DoD items from other categories sparingly; do not merge categories wholesale.

Routing note: for programmatic lookup and prompt routing, prefer the stable `Retrieval key: category=...` line under each `##` category header. Category header text may change over time; retrieval keys should be treated as stable identifiers.

## Category section template (what to expect)

Each category section contains:

1. Intent / typical use cases
2. When NOT to use (STOP conditions)
3. Input contract (required/optional inputs with examples)
4. Output contract (what artifacts must be produced)
5. DoD checklist (objective, reviewer-friendly)
6. Verification menu (quick / deep / no-network)
7. Decision points (copy/paste-ready branches)
8. Failure modes & troubleshooting
9. Anti-patterns (reviewer red flags)
10. Mini exemplar (NON-NORMATIVE)

---

## Meta-skills (prompt/workflow composition)

Retrieval key: `category=meta-skills`

Typical risk: low

**Related strict spec sections:** `Skill skeleton (1-page; REQUIRED content contract)`, `Required content contract (body)`, `Decision points`, `Verification`, `Troubleshooting`.

**Dominant failure mode:** produced workflow/checklist is “nice” but not executable (missing objective DoD, decision points, and verification).

### Meta-skills — Intent / typical use cases

Use this category when the skill's purpose is to produce **reusable prompt/workflow artifacts**, such as:

- a new `SKILL.md` body or a major rewrite of one,
- a review checklist/playbook,
- a standardized PR description/report template,
- a "pipeline" of steps an agent should follow across tasks.

### Meta-skills — When NOT to use (common misfires)

- Do not use when the user actually wants a direct implementation change (use Implementation playbooks / Debugging / Refactoring categories instead).
- Do not use to "improve prompts" without an objective target (missing acceptance criteria).
- STOP if the user cannot state the target artifact type and intended audience (author vs reviewer vs operator).

### Meta-skills — Input contract

- Required inputs:
  - Target artifact type (e.g., new skill body, skill rewrite, review rubric).
  - Intended audience (author vs reviewer vs operator).
  - Success criteria (what the artifact must enable; what must not happen).
- Optional inputs:
  - Primary category the artifact is for (e.g., auditing, pipelines).
  - Example of a "good" artifact in the repo.
  - Known failure modes (e.g., missing decision points; assumes network).
  - Host constraints (sandbox/network/approval policy; tool availability).

### Meta-skills — Output contract

- Must produce:
  - Draft artifact (skill body / checklist / template) with explicit sections.
  - Short "review notes" explaining design choices and tradeoffs.
- Must satisfy:
  - Includes: When to use, When NOT to use, Input/Output contracts, numbered Procedure, ≥2 decision points, Verification, Troubleshooting.
  - A reviewer can apply it "cold" (no unstated context) in ~10 minutes.
  - Includes at least one no-network/manual fallback when feasible.

### Meta-skills — DoD checklist (objective)

- Has explicit target artifact type + audience.
- Procedure is numbered and executable (no vague "make sure it works").
- Contains ≥2 explicit decision points (If/Then/Else branches).
- Includes verification steps with expected outcomes or signals.
- Includes no-network/manual fallback where tools/network may be unavailable.

### Meta-skills — Verification menu

- Quick checks:
  - Run a "structure check": confirm all required headings/sections exist and are findable quickly.
  - Verify at least two explicit "If ... then ... otherwise ..." decision points exist.
- Deep checks:
  - Apply the artifact to a small real example (or a tiny toy example) and confirm it yields the intended outputs.
  - Have a reviewer follow the procedure "cold" and list any ambiguities.
  - Run an "adversarial read": try to follow the procedure while assuming (a) no network, (b) missing tools, and (c) ambiguous user intent; confirm the artifact forces a STOP/ask rather than improvising.
- No-network fallback:
  - Ensure the artifact includes a "paste outputs / manual inspection" path for any tool/command it mentions.

### Evaluation harness (recommended)

Meta-skills should usually include a small evaluation harness so reviewers can judge quality without re-litigating intent.

- **Self-check checklist** (author runs): "Does the artifact contain all required sections? Are checks objective? Are decision points explicit? Are risky actions gated?"
- **Cold-run prompt** (reviewer runs): "Pretend you are executing this workflow with only the inputs listed; note any missing prerequisite or ambiguity."
- **Edge-case prompts** (reviewer runs): provide 2–3 short "bad input" examples and confirm the workflow produces STOP/ask behavior (not guesses).

### Meta-skills — Decision points library (copy/paste-ready)

```text
If the user cannot name the target artifact type and audience, then STOP and ask for that. Otherwise, continue.
If the artifact would change public APIs/behavior or recommend risky actions, then STOP and add an ask-first gate. Otherwise, keep defaults conservative.
If the environment is network-restricted, then avoid install/download steps and require pasted outputs/manual inspection. Otherwise, include optional runnable checks.
```

### Meta-skills — Failure modes & troubleshooting

- Common failure: "The produced workflow is 'nice' but not executable."
  - Symptoms: unnumbered procedure, missing concrete checks, vague language ("make sure it works").
  - Likely causes: no explicit output contract; no objective DoD.
  - What to do next: rewrite procedure as numbered actions; add quick check with expected results; add ≥2 decision points.

### Anti-hallucination guardrails (recommended)

- Require the workflow to prefer **local inspection** (repo files, commands, logs) over assumed facts.
- When the workflow references tools, versions, or repo structure, require a check step (e.g., "confirm `<file>` exists" or "run `<cmd> --version`") or a STOP/ask.
- For any "best practice" advice, require either a repo-local reference link/path or explicitly label it as optional guidance.

### Meta-skills — Anti-patterns (reviewer red flags)

- "Improve this prompt" without specifying outputs and objective DoD.
- Procedures that assume tools/network/permissions without stating constraints and fallbacks.
- A "meta" skill that silently changes scope into dependency upgrades or refactors.

### Meta-skills — Mini exemplar (NON-NORMATIVE)

Goal: produce a review checklist skill body.

1. Ask for: target repo context + what the checklist is for.
2. Draft artifact with required sections and objective checks.
3. Add decision points for: network restricted vs available; patch requested vs report-only.
4. Add troubleshooting for "checklist too vague".

---

## Auditing & assessment (codebase/system audits)

Retrieval key: `category=auditing-assessment`

Typical risk: low→medium

**Related strict spec sections:** `Skill skeleton (1-page; REQUIRED content contract)`, `1. Output contract (REQUIRED)`, `Verification`, `Troubleshooting`, `Risk tiering (guidance; normative minimums per tier)`.

**Dominant failure mode:** claims without reproducible evidence (missing scope/method/evidence trail, overconfident global conclusions).

### Auditing & assessment — Intent / typical use cases

Use this category when the skill's primary output is a **report of findings** about a system/codebase, such as:

- architecture audits,
- security/privacy reviews (non-remediation),
- quality/readability audits,
- dependency/supply-chain posture assessments (reporting only),
- "state of the repo" assessments (tests, tooling, consistency).

### Auditing & assessment — When NOT to use (common misfires)

- Do not use when the user actually wants fixes shipped immediately (use Implementation playbooks / Refactoring / Security change workflows).
- Do not produce sweeping judgments without an evidence trail.
- STOP if scope boundaries aren't defined (what parts are in/out).

### Auditing & assessment — Input contract

- Required inputs:
  - Audit goal (what is being assessed and why).
  - Scope boundaries (repos/dirs/components; time horizon; depth).
  - Reporting expectations (short memo vs detailed report; severity scale).
- Optional inputs:
  - Constraints: time budget; "no network"; "no running services"; restricted permissions.
  - Known incident history or suspected hotspots.

### Auditing & assessment — Output contract

- Must produce:
  - Audit report with: scope, method, evidence trail, findings, severity, recommendations, verification suggestions.
  - Prioritized remediation plan (sequenced, with dependencies) when requested.
- Must satisfy:
  - Every finding includes evidence (paths/commands/observations), impact, and next steps.
  - Findings label: **global** vs **sample-based** and include confidence.
  - Includes a "what we did NOT assess" section.

### Auditing & assessment — DoD checklist (objective)

- Scope is explicit (in/out) and consistent with claim strength.
- Each finding includes evidence + reproducible query/steps.
- Severity rubric is defined and applied consistently.
- Sampling (if used) is disclosed with confidence language.

### Methodology templates (recommended)

- **Scope statement template**:
  - "In scope: `<paths/components>`."
  - "Out of scope: `<paths/components>`."
  - "Time budget: `<N>` minutes/hours. Coverage: `<full|sampled>`."
- **Evidence trail template** (per finding):
  - "Evidence: `<file path(s)>` + `<command/query>` + `<observed snippet or output shape>`."
  - "Repro steps (if applicable): `<steps>`."
- **Finding format template**:
  - Title: `<short>`; Severity: `<low/medium/high>`; Confidence: `<low/medium/high>`; Scope: `<global|sampled>`.
  - Impact: `<who/what is affected>`; Recommendation: `<next step>`; Verification: `<objective check>`.

### Sampling strategies (when full coverage is infeasible)

- **Hotspot sampling**: focus on high-churn, high-complexity, or historically incident-prone areas; state selection criteria.
- **Risk-based sampling**: prioritize areas with higher blast radius (auth, billing, deploy, data).
- **Random sampling**: for broad hygiene checks; state how many items were sampled and how selected.

If sampling is used, the audit MUST disclose it clearly and MUST avoid global claims that aren't supported by coverage.

### Severity rubric (lightweight; recommended)

- **High**: likely user/customer impact, security/privacy risk, data loss, or systemic reliability issue.
- **Medium**: meaningful maintainability or correctness risk, but bounded blast radius or easy rollback.
- **Low**: hygiene, readability, or small inconsistencies with low risk.

### Auditing & assessment — Verification menu

- Quick checks:
  - Confirm each finding has evidence + actionable next step.
  - Confirm scope/method sections exist and are consistent with the claim strength.
- Deep checks:
  - Spot-check a sample of findings by re-running the referenced queries/inspections (or asking user to run them).
  - Validate severity rankings against an agreed rubric.
- No-network fallback:
  - Prefer `rg`, file inspection, and pasted logs over external scanning tools; require exact commands for user to run when needed.

### Auditing & assessment — Decision points library (copy/paste-ready)

```text
If scope is not explicit (paths/components/time budget), then STOP and ask for scope boundaries. Otherwise, continue.
If a full audit is infeasible in the time budget, then use sampling and explicitly label confidence. Otherwise, do comprehensive coverage.
If the audit suggests a fix that would be breaking/high risk, then recommend a separate Implementation/Change skill and do not proceed without approval. Otherwise, keep as recommendations.
```

### Auditing & assessment — Failure modes & troubleshooting

- Common failure: "Findings are not reproducible."
  - Symptoms: claims lack file paths, queries, or concrete examples.
  - Likely causes: missing evidence trail; relying on intuition.
  - What to do next: attach minimal reproductions (paths, snippets, search commands) and downgrade confidence where evidence is weak.

### Auditing & assessment — Failure modes & troubleshooting (sampling-specific)

- Common failure: "Audit uses sampling but states conclusions as universal."
  - Symptoms: language like "the codebase does X" without coverage evidence.
  - Likely causes: missing scope labeling; overconfidence.
  - What to do next: label findings as sampled; add confidence; downgrade claims; recommend targeted follow-up audit for global conclusions.

### Auditing & assessment — Anti-patterns (reviewer red flags)

- Severity labels without defined meaning (or inconsistent application).
- Sampling used but not disclosed, or conclusions stated as certain despite partial review.
- Recommendations that require risky actions without an ask-first note or without separating "reporting" vs "remediation".

### Auditing & assessment — Mini exemplar (NON-NORMATIVE)

Audit request: "Assess our agent skills quality."

1. Define scope: which `SKILL.md` files, which aspects (structure, safety, verification).
2. Collect evidence: counts of missing required sections, common missing decision points, etc.
3. Produce report: top themes + examples + remediation plan.
4. Provide verification: how to re-check after fixes (e.g., grep-based structural checks).

---

## Agentic workflows & pipelines (automation/orchestration)

Retrieval key: `category=agentic-pipelines`

Typical risk: medium→high

**Related strict spec sections:** `Skill skeleton (1-page; REQUIRED content contract)`, `Command mention rule (NORMATIVE)`, `Risk tiering (guidance; normative minimums per tier)`, `Appendix A: Required wording patterns (NORMATIVE templates)`.

**Dominant failure mode:** unsafe-by-default or non-idempotent pipelines (mutating steps ungated, weak verification, unclear failure handling).

### Agentic workflows & pipelines — Intent / typical use cases

Use this category when the skill defines or generates a **multi-step automation** or agentic pipeline, such as:

- "scan → propose → patch → verify" pipelines,
- orchestrating multiple tools/commands with gating,
- repo-wide improvement workflows (lint/format/test in stages),
- release/runbook-like operational sequences (but not full ops category).

### Agentic workflows & pipelines — When NOT to use (common misfires)

- Do not use when a single deterministic command suffices (use Build/test/tooling workflow).
- Do not encode unsafe defaults that mutate state without explicit ask-first.
- STOP if the environment constraints (network, permissions, tools) are unknown and materially affect feasibility.

### Safety model (recommended)

For pipeline skills, treat safety as a first-class output:

- Prefer **plan → apply → verify** separation.
- Prefer **dry-run/read-only** as the default mode when feasible.
- Treat mutating steps (writes, deletes, deploys, migrations, force operations) as **ask-first** by default.

### Agentic workflows & pipelines — Input contract

- Required inputs:
  - Target outcome + success criteria (what the pipeline produces).
  - Constraints: allowed actions (read-only vs write), network availability, approval requirements.
  - Failure handling expectations (retry policy, rollback/escape hatch).
- Optional inputs:
  - Execution environment (CI vs local; OS; sandbox policy).
  - Existing scripts/tools the pipeline should reuse.

### Agentic workflows & pipelines — Output contract

- Must produce:
  - Pipeline definition (numbered steps or script outline) with explicit gates.
  - "Safe run mode" (dry-run/read-only) and "Mutating mode" (ask-first).
  - Logging/output contract (what is emitted at each step; how to detect failure).
- Must satisfy:
  - Idempotency: second run is no-op or produces identical outputs.
  - Dry-run is default when feasible.
  - Each external command has expected output + fallback when it cannot be run.

### Agentic workflows & pipelines — DoD checklist (objective)

- Plan/apply/verify separation exists (or equivalent gated structure).
- All mutating steps are explicitly ask-first gated (or clearly marked safe).
- Each step has success/failure signals and a "what next" on failure.
- Includes no-network mode or "paste outputs" fallback when external deps exist.

### Gating patterns (copy/paste-ready)

- **Plan/apply split**:
  - "Plan mode: inspect and produce a change plan (no writes)."
  - "Apply mode (Ask first): perform the planned writes only after explicit approval."
- **Mutating step gate**:
  - "Ask first: this step mutates state (`<risk>`). Do not run without explicit approval. Alternative: `<dry-run/read-only>`."
- **Failure gate**:
  - "If verification fails, STOP and troubleshoot; do not continue to subsequent steps."

### Agentic workflows & pipelines — Verification menu

- Quick checks:
  - Verify all mutating steps are gated behind ask-first language.
  - Verify each step has a success/failure signal and a "what next" on failure.
- Deep checks:
  - Execute the pipeline on a small target (or a sandboxed subset) and confirm it behaves deterministically.
  - Re-run to validate idempotency/no-op behavior.
- No-network fallback:
  - Provide a mode that uses only local inspection and user-pasted outputs; avoid installs/downloads by default.

### Agentic workflows & pipelines — Decision points library (copy/paste-ready)

```text
If network is restricted, then run in "offline mode" and require pasted outputs for any external dependency. Otherwise, include optional runnable checks.
If the pipeline step is mutating/destructive, then ask first and offer a dry-run alternative. Otherwise, proceed.
If any verification step fails, then STOP and troubleshoot before continuing. Otherwise, continue to the next step.
```

### Agentic workflows & pipelines — Failure modes & troubleshooting

- Common failure: "Pipeline is not idempotent."

  - Symptoms: second run makes new changes; outputs drift.
  - Likely causes: non-deterministic ordering, timestamps, unstated external state.
  - What to do next: sort inputs deterministically; record state; add explicit checks for already-applied changes.

- Common failure: "Pipeline is unsafe by default."
  - Symptoms: steps write/delete/deploy without an ask-first gate or without a dry-run alternative.
  - Likely causes: conflating plan and apply; missing risk controls.
  - What to do next: introduce plan/apply split; add ask-first gates; add dry-run mode and clear expected outputs.

### Agentic workflows & pipelines — Anti-patterns (reviewer red flags)

- Pipelines that conflate "plan" and "apply" (no dry-run/read-only mode).
- Commands listed without expected output shape or without "what to do if it fails".
- Hidden global state assumptions (tool versions, env vars) without constraints/assumptions and fallbacks.

### Agentic workflows & pipelines — Mini exemplar (NON-NORMATIVE)

Pipeline request: "Improve all skills to include no-network fallback."

1. Inspect: enumerate skills; identify which reference network/install steps.
2. Plan: generate a per-skill patch plan (dry-run) listing intended edits.
3. Apply (ask-first): make edits with minimal diffs.
4. Verify: structural checks + spot-check 2–3 skills by following their quick checks.

---

## Implementation playbooks (feature/change delivery)

Retrieval key: `category=implementation-playbooks`

Typical risk: medium

**Related strict spec sections:** `Skill skeleton (1-page; REQUIRED content contract)`, `Minimal-change default`, `Verification requirements`.

**Dominant failure mode:** scope creep or breaking changes without explicit approval; patches that “look right” but aren’t validated.

### Implementation playbooks — Intent / typical use cases

Use this category when the skill’s primary output is an implemented change (code/config) in a repo, such as:

- adding a feature behind an existing interface,
- changing behavior with explicit acceptance criteria,
- wiring new endpoints/flags/configuration,
- targeted UX or API improvements.

### Implementation playbooks — When NOT to use (common misfires)

- Do not use when the request is primarily about diagnosis (use Debugging & triage).
- Do not use for broad restructures without a behavioral target (use Refactoring & modernization).
- STOP if acceptance criteria are missing or ambiguous (inputs are insufficient to implement safely).

### Implementation playbooks — Input contract

- Required inputs:
  - Acceptance criteria: expected behavior, constraints, and success signals.
  - Scope boundaries: in-scope/out-of-scope, compatibility requirements.
  - Verification target: tests/commands or a reproducible manual check.
- Optional inputs:
  - Performance/latency budgets, rollout strategy (feature flag), UX specs.
  - “Do not change” list (APIs, schemas, dependencies).

### Implementation playbooks — Output contract

- Must produce:
  - A minimal patch that satisfies the acceptance criteria.
  - A verification step (test, build, or manual) with expected result.
  - A short change note: what changed + how to verify.
- Must satisfy:
  - No unrelated refactors unless explicitly approved.
  - Any breaking/public-surface change is ask-first gated.

### Implementation playbooks — DoD checklist (objective)

- Acceptance criteria are listed and each is addressed.
- Verification step exists and has an expected result shape.
- Any risky/breaking step includes ask-first gating.

### Implementation playbooks — Verification menu

- Quick checks:
  - Run the narrowest test/build command relevant to the change (or document a manual check).
- Deep checks:
  - Run broader suite (module/package) if change touches shared code.
- No-network fallback:
  - Prefer local builds/tests; if dependencies require network, provide a “paste output” path or skip with explicit reason.

### Implementation playbooks — Decision points library (copy/paste-ready)

```text
If acceptance criteria are missing/ambiguous, then STOP and ask for them. Otherwise, continue.
If implementing the request requires changing a public API/CLI/config format, then ask first and propose a compatibility path. Otherwise, keep changes internal.
If verification cannot be run in this environment, then provide a manual verification recipe and ask the user to paste results. Otherwise, run the smallest relevant checks.
```

### Implementation playbooks — Failure modes & troubleshooting

- Common failure: “Change is implemented but not verifiable.”
  - Symptoms: no test/manual check; unclear how to confirm success.
  - Likely causes: missing verification input; skipped DoD.
  - What to do next: add a minimal regression test or a deterministic manual check procedure.

### Implementation playbooks — Anti-patterns (reviewer red flags)

- “Implement X” without acceptance criteria and without STOP/ask.
- Silent behavior changes without mentioning compatibility.
- Refactoring unrelated code to the requested change.

### Implementation playbooks — Mini exemplar (NON-NORMATIVE)

Feature request: “Add a `--json` flag to the report command.”

1. Confirm desired JSON schema + backward compatibility expectations.
2. Implement minimal flag parsing + serialization.
3. Add/adjust a test (or snapshot) for stable output.
4. Verify with the narrowest test target.

---

## Debugging & triage (root cause + minimal fix)

Retrieval key: `category=debugging-triage`

Typical risk: low→medium

**Related strict spec sections:** `Evidence-first`, `Minimal-change default`, `Verification requirements`, `Troubleshooting`.

**Dominant failure mode:** editing before evidence; “fixes” that don’t address the root cause or lack a reproducible regression guard.

### Debugging & triage — Intent / typical use cases

Use this category when the primary goal is to diagnose and fix a bug/regression, such as:

- failing tests/builds,
- runtime errors/exceptions,
- incorrect outputs, edge-case crashes,
- flaky behavior.

### Debugging & triage — When NOT to use (common misfires)

- Do not use when the user wants a design/feature change (use Implementation playbooks).
- Do not use to “optimize” without a performance target and measurement plan.
- STOP if there is no repro (failing test, log, steps) and the bug cannot be reliably observed.

### Debugging & triage — Input contract

- Required inputs:
  - Failure signal (error message, failing test name, or repro steps).
  - Expected vs actual behavior.
- Optional inputs:
  - Logs/stack trace, environment info, recent changes/PR link.

### Debugging & triage — Output contract

- Must produce:
  - Root cause hypothesis + supporting evidence (brief).
  - Minimal patch addressing root cause.
  - Regression guard (test/assert) when feasible.
- Must satisfy:
  - Avoid speculative multi-change “shotgun” fixes without evidence.

### Debugging & triage — DoD checklist (objective)

- The repro/failing test no longer fails.
- A regression guard exists (or a stated reason it’s not feasible).

### Debugging & triage — Verification menu

- Quick checks:
  - Re-run the failing test/repro. Expected: passes/no repro.
- Deep checks:
  - Run a narrow related suite to detect collateral breakage.
- No-network fallback:
  - Ask user to paste error output and/or run commands locally; proceed only with sufficient evidence.

### Debugging & triage — Decision points library (copy/paste-ready)

```text
If there is a failing test, then focus on that exact test first. Otherwise, create a minimal repro before editing code.
If multiple plausible root causes exist, then STOP and ask for additional evidence (logs/input sample). Otherwise, implement the smallest fix.
If the fix requires a breaking change or dependency upgrade, then ask first; otherwise, keep the patch minimal.
```

### Debugging & triage — Failure modes & troubleshooting

- Common failure: “Bug is fixed but flakiness remains.”
  - Symptoms: intermittent failures, timing sensitivity.
  - Likely causes: non-deterministic ordering, timeouts, shared state.
  - What to do next: stabilize ordering; isolate state; add deterministic waits/mocks; add a flake reproduction loop (ask-first if time-consuming).

### Debugging & triage — Anti-patterns (reviewer red flags)

- “Try a few changes until it works” without evidence/hypothesis.
- Fixing symptoms while leaving a reproducible failing test unresolved.
- Adding sleeps/timeouts instead of addressing non-determinism.

### Debugging & triage — Mini exemplar (NON-NORMATIVE)

Bug report: “CLI crashes when input file is empty.”

1. Capture failure signal: run command with empty file; record error output.
2. Form hypothesis: identify the nil/empty assumption in parsing path.
3. Implement minimal fix: handle empty input explicitly.
4. Add regression test: empty input returns a deterministic error or empty result.
5. Verify: rerun failing command/test; confirm no crash.

---

## Refactoring & modernization (behavior-preserving change)

Retrieval key: `category=refactoring-modernization`

Typical risk: medium

**Related strict spec sections:** `Minimal-change default`, `Decision points`, `Verification requirements`.

**Dominant failure mode:** accidental behavior change or sprawling refactor without objective boundaries/verification.

### Refactoring & modernization — Intent / typical use cases

Use this category when the goal is to improve internal structure while preserving external behavior, such as:

- extracting modules, simplifying control flow,
- updating language idioms, removing duplication,
- improving types, naming, maintainability.

### Refactoring & modernization — When NOT to use (common misfires)

- Do not use when user actually needs a bug fix or new behavior (use Debugging or Implementation).
- Do not refactor broadly without an objective goal and boundary.
- STOP if there is no verification harness (tests/build) and the change would be hard to validate manually.

### Refactoring & modernization — Input contract

- Required inputs:
  - Target area + refactor goal (what “better” means).
  - Non-goals/boundaries (what must not change).
  - Verification harness (tests/build/manual smoke).
- Optional inputs:
  - Performance constraints, deprecation policy, allowed tooling changes.

### Refactoring & modernization — Output contract

- Must produce:
  - Refactor patch with bounded scope.
  - Evidence that behavior is preserved (tests/build output or manual check recipe).
- Must satisfy:
  - Explicitly call out any behavior change; ask-first if it affects callers.

### Refactoring & modernization — DoD checklist (objective)

- Refactor is scoped to the stated area and goal.
- Verification harness passes (or manual verification steps are provided).

### Refactoring & modernization — Verification menu

- Quick checks:
  - Run the smallest relevant tests/build checks for the refactored area.
- Deep checks:
  - Run a broader suite if the refactor touched shared utilities.
- No-network fallback:
  - Provide a manual smoke checklist and ask the user to paste results if tests can’t be run here.

### Refactoring & modernization — Decision points library (copy/paste-ready)

```text
If tests/build exist for the area, then run the smallest relevant set before and after. Otherwise, STOP and define a manual smoke plan.
If the refactor expands beyond the stated boundary, then STOP and ask for approval to widen scope. Otherwise, keep changes minimal.
If any public behavior changes are required, then ask first and propose a compatibility plan. Otherwise, keep behavior constant.
```

### Refactoring & modernization — Failure modes & troubleshooting

- Common failure: “Refactor changes behavior.”
  - Symptoms: tests fail, outputs change, or manual behavior differs after refactor.
  - Likely causes: insufficient characterization tests; hidden coupling; removed side effects.
  - What to do next: add characterization tests; narrow scope; revert and re-apply in smaller steps.

### Refactoring & modernization — Anti-patterns (reviewer red flags)

- “Cleanup” PRs with no stated boundary and no verification plan.
- Conflating refactor with feature work (behavior changes not called out).

### Refactoring & modernization — Mini exemplar (NON-NORMATIVE)

Refactor request: “Simplify the parser module without changing behavior.”

1. Identify stable behavior surface (public API, error messages, key fixtures).
2. Add characterization tests if coverage is weak.
3. Refactor in small steps (extract helpers, simplify branching).
4. Verify with the narrowest relevant suite; spot-check key fixtures.

---

## Testing & quality (tests, QA, verification assets)

Retrieval key: `category=testing-quality`

Typical risk: low→medium

**Related strict spec sections:** `Verification-first posture`, `Output contract`, `Troubleshooting`.

**Dominant failure mode:** tests that are non-deterministic, over-coupled, or don’t assert the intended behavior.

### Testing & quality — Intent / typical use cases

Use this category when the primary output is test coverage or QA assets, such as:

- adding regression tests, golden/snapshot tests,
- building fixtures/mocks,
- creating minimal repro tests for bugs.

### Testing & quality — When NOT to use (common misfires)

- Do not write tests without a clear behavior spec.
- Do not introduce flaky tests.
- STOP if the system has no runnable test harness and no feasible manual verification plan.

### Testing & quality — Input contract

- Required inputs:
  - Behavior spec (expected behavior).
  - Test harness constraints (framework, runtime, how to run tests).
- Optional inputs:
  - Known flake sources (time, randomness), performance constraints.

### Testing & quality — Output contract

- Must produce:
  - Test(s) that fail before and pass after the target change (when applicable).
  - Any needed fixtures/mocks with clear ownership.
- Must satisfy:
  - Deterministic assertions; minimal reliance on timing.

### Testing & quality — DoD checklist (objective)

- Test validates intended behavior and is deterministic.
- Test run command is stated with expected result shape.

### Testing & quality — Verification menu

- Quick checks:
  - Run the new/changed tests alone; confirm deterministic pass.
- Deep checks:
  - Run the smallest suite that includes neighbors (to detect fixture pollution).
- No-network fallback:
  - Prefer local-only tests; if tests depend on external services, add mocks/fixtures or provide a “paste outputs” manual check.

### Testing & quality — Decision points library (copy/paste-ready)

```text
If the behavior spec is unclear, then STOP and ask for expected inputs/outputs. Otherwise, write tests first (or alongside the fix).
If the test would be flaky (time, randomness, network), then redesign to be deterministic (mock/time control). Otherwise, proceed.
If the project has no test harness, then STOP and propose a minimal harness or a deterministic manual verification plan. Otherwise, continue.
```

### Testing & quality — Failure modes & troubleshooting

- Common failure: “Tests are flaky.”
  - Symptoms: intermittent failures; timing-dependent assertions.
  - Likely causes: real time, shared state, non-deterministic ordering, network calls.
  - What to do next: control time/randomness; isolate state; remove network; use stable fixtures.

### Testing & quality — Anti-patterns (reviewer red flags)

- Snapshot tests with unstable output (timestamps, random IDs) without normalization.
- Tests that assert implementation details rather than behavior.

### Testing & quality — Mini exemplar (NON-NORMATIVE)

Test request: “Add a regression test for the null-pointer crash.”

1. Encode the minimal crashing input as a fixture.
2. Add a test that reproduces the crash before the fix.
3. Apply the fix; confirm the test now passes.
4. Run the smallest related test suite to ensure no fixture pollution.

---

## Documentation & knowledge transfer (docs, guides, runbooks)

Retrieval key: `category=documentation-knowledge`

Typical risk: low

**Related strict spec sections:** `Output contract`, `Verification`, `Assumptions declared`.

**Dominant failure mode:** docs that are correct in isolation but unusable (missing prerequisites, mismatched commands, no verification).

### Documentation & knowledge transfer — Intent / typical use cases

Use this category when the primary output is documentation, such as:

- onboarding guides, READMEs, architecture overviews,
- runbooks/how-tos, troubleshooting guides,
- “how to use this tool” instructions.

### Documentation & knowledge transfer — When NOT to use (common misfires)

- Do not document behavior you cannot verify (or clearly mark it as unverified/assumed).
- STOP if the intended audience and environment (OS/tooling) are unknown.

### Documentation & knowledge transfer — Input contract

- Required inputs:
  - Intended audience (new contributor, oncall, end user) and environment assumptions.
  - Target task(s) the doc enables (what the reader will accomplish).
- Optional inputs:
  - Known failure modes, screenshots/examples, “golden path” vs edge cases.

### Documentation & knowledge transfer — Output contract

- Must produce:
  - Doc patch with prerequisites, steps, and verification signals.
  - A “known limitations / assumptions” section when environment varies.

### Documentation & knowledge transfer — DoD checklist (objective)

- Doc includes prerequisites, steps, and at least one verification signal.
- Doc names the intended audience and environment assumptions (OS/tooling).

### Documentation & knowledge transfer — Verification menu

- Quick checks:
  - Run a “doc walkthrough” mentally or with a tiny local example; ensure every step has a command/output or a concrete observation.
- Deep checks:
  - Have a cold reader follow the doc (or simulate it) and note missing prerequisites.
- No-network fallback:
  - Provide an offline path or explicitly mark steps that require network; do not assume downloads.

### Documentation & knowledge transfer — Decision points library (copy/paste-ready)

```text
If the intended audience and environment are unclear, then STOP and ask. Otherwise, tailor prerequisites and commands accordingly.
If a step depends on network or credentials, then call it out explicitly and provide a safe fallback (mock/paste output). Otherwise, keep steps local.
If verification cannot be performed here, then include a “paste the output” instruction for the reader. Otherwise, validate steps directly.
```

### Documentation & knowledge transfer — Failure modes & troubleshooting

- Common failure: “Docs are incomplete for first-time users.”
  - Symptoms: missing prerequisites; ambiguous commands; unstated setup steps.
  - Likely causes: author knowledge leakage; no cold-run.
  - What to do next: add prerequisites; add a first-run checklist; add expected outputs per step.

### Documentation & knowledge transfer — Anti-patterns (reviewer red flags)

- Commands shown without expected output shape or success criteria.
- Instructions that assume unstated tools/permissions/network.

### Documentation & knowledge transfer — Mini exemplar (NON-NORMATIVE)

Doc request: “Write an onboarding guide for running tests.”

1. List prerequisites (runtime version, package manager, env vars).
2. Provide the minimal “run tests” command + expected output shape.
3. Add troubleshooting for common failures (missing deps, wrong version).
4. Add “offline mode” notes if installs require network.

---

## Build, tooling & CI (developer experience workflows)

Retrieval key: `category=build-tooling-ci`

Typical risk: medium

**Related strict spec sections:** `Assumptions declared`, `Verification`, `Troubleshooting`.

**Dominant failure mode:** introducing tooling changes that don’t work in the repo’s environment, or changing developer workflows without explicit approval.

### Build, tooling & CI — Intent / typical use cases

Use this category when the skill’s primary output is a tooling/CI workflow or change, such as:

- adding or modifying lint/format/test scripts,
- introducing pre-commit hooks,
- adjusting CI pipelines (reporting, caching, matrix),
- improving local developer workflows (make targets, task runners).

### Build, tooling & CI — When NOT to use (common misfires)

- Do not change package managers, lockfiles, or CI semantics without ask-first.
- STOP if the repo’s existing tooling conventions are unknown.

### Build, tooling & CI — Input contract

- Required inputs:
  - Target workflow (what should be easier/faster/more reliable).
  - Constraints: allowed tools, allowed dependency changes, CI provider.
  - Verification plan (local command + CI signal).
- Optional inputs:
  - Performance constraints (CI minutes), supported OS versions, caching policy.

### Build, tooling & CI — Output contract

- Must produce:
  - Tooling/CI patch (config/scripts) with minimal disruption.
  - Verification instructions with expected signals.
- Must satisfy:
  - Any dependency/lockfile changes are ask-first gated.
  - Changes preserve existing workflow unless explicitly approved.

### Build, tooling & CI — DoD checklist (objective)

- Local command(s) and CI step(s) are defined and produce expected signals.
- Any workflow change is documented for developers.

### Build, tooling & CI — Verification menu

- Quick checks:
  - Run the new/changed command locally (if possible) or provide a paste-output check.
- Deep checks:
  - Validate in CI (or describe the CI job signal to confirm).
- No-network fallback:
  - Avoid introducing new downloads; if required, include a manual/paste-output fallback.

### Build, tooling & CI — Decision points library (copy/paste-ready)

```text
If the change requires adding/upgrading dependencies or changing lockfiles, then ask first. Otherwise, proceed with repo-local config changes.
If CI provider/config is unknown, then STOP and ask for it. Otherwise, modify only the relevant pipeline files.
If the workflow change would break existing developer habits, then ask first and provide migration notes. Otherwise, keep changes backward-compatible.
```

### Build, tooling & CI — Failure modes & troubleshooting

- Common failure: “Tooling works locally but fails in CI (or vice versa).”
  - Symptoms: environment differences, missing caches, version mismatches.
  - Likely causes: unstated assumptions about runtimes/tools.
  - What to do next: pin versions, document prerequisites, align CI setup with local scripts.

### Build, tooling & CI — Anti-patterns (reviewer red flags)

- Changing package manager/lockfiles without approval.
- Adding tools without documenting how to run them and how to interpret failures.

### Build, tooling & CI — Mini exemplar (NON-NORMATIVE)

Tooling request: “Add a `lint` and `format` workflow.”

1. Detect existing conventions (scripts, CI config).
2. Propose minimal integration plan; ask-first for dependency additions.
3. Add scripts/config and wire into CI.
4. Verify locally and via CI signal.

---

## Integration & evaluation (third-party systems, vendor choices)

Retrieval key: `category=integration-evaluation`

Typical risk: medium

**Related strict spec sections:** `Inputs`, `Outputs`, `Decision points`, `Verification`.

**Dominant failure mode:** recommendations without constraints, or integrations that assume network/keys and cannot be verified safely.

### Integration & evaluation — Intent / typical use cases

Use this category when the skill’s primary output is an integration plan or implementation, such as:

- choosing between vendors/libraries,
- integrating external APIs (payments, auth, analytics),
- building adapters/wrappers for third-party SDKs,
- evaluating tradeoffs with constraints and verification strategy.

### Integration & evaluation — When NOT to use (common misfires)

- Do not assume credentials or access to external services.
- STOP if the integration requires secrets; ask for mocked/pasted outputs or a sandbox credential strategy.

### Integration & evaluation — Input contract

- Required inputs:
  - Integration goal (what capability is needed).
  - Constraints: budget/latency/compliance, allowed data flow, runtime environment.
  - Verification strategy (mock/sandbox account, contract tests).
- Optional inputs:
  - Candidate vendors/libraries, existing system boundaries, rollout strategy.

### Integration & evaluation — Output contract

- Must produce:
  - A recommendation or integration patch plan with tradeoffs.
  - A verification plan (including no-secrets approach for dev/test).
- Must satisfy:
  - No secrets in code or logs; safe handling guidance is explicit.

### Integration & evaluation — DoD checklist (objective)

- Constraints are enumerated and used to rank options.
- Verification plan includes a no-network or sandbox fallback.

### Integration & evaluation — Verification menu

- Quick checks:
  - Validate that integration boundaries are abstracted (interfaces) and secrets are not required to run unit tests.
- Deep checks:
  - Sandbox end-to-end test in a non-prod environment (ask-first if it mutates state or costs money).
- No-network fallback:
  - Provide mocked responses + contract tests; require pasted outputs for real API calls.

### Integration & evaluation — Decision points library (copy/paste-ready)

```text
If the integration requires secrets to even start, then STOP and design a mock/sandbox approach first. Otherwise, proceed.
If multiple vendors satisfy requirements, then pick based on constraints (latency/cost/compliance) and document tradeoffs. Otherwise, recommend the single viable option.
If the integration step mutates external state (billing, user creation), then ask first and use a sandbox account. Otherwise, use mocks.
```

### Integration & evaluation — Failure modes & troubleshooting

- Common failure: “Integration is not testable without real credentials.”
  - Symptoms: tests require API keys; local dev is blocked.
  - Likely causes: SDK usage leaked into core logic; no abstraction layer.
  - What to do next: introduce interface boundaries; add mock implementations; move secrets to runtime configuration.

### Integration & evaluation — Anti-patterns (reviewer red flags)

- Embedding API keys in examples.
- Implementing directly against vendor SDK throughout the codebase without an abstraction boundary.

### Integration & evaluation — Mini exemplar (NON-NORMATIVE)

Integration request: “Add an email provider.”

1. List constraints (deliverability, cost, compliance, latency).
2. Choose provider; design interface boundary for sending.
3. Add mock provider + contract tests; add sandbox verification plan.
4. Ask-first before any steps that create external resources or incur cost.

---

## Security changes (high-risk)

Retrieval key: `category=security-changes`

Typical risk: high

**Related strict spec sections:** `Risk tiering`, `Ask-first for risky or breaking actions`, `Assumptions declared`.

**Dominant failure mode:** weakening security boundaries or mishandling secrets; unreviewed changes with high blast radius.

### Security changes — Intent / typical use cases

Use this category when the skill changes security-sensitive behavior, such as:

- authentication/authorization flow changes,
- token/session handling,
- cryptography usage, key rotation procedures,
- permission model changes, data access controls.

### Security changes — When NOT to use (common misfires)

- Do not change authn/authz/crypto/token handling without explicit approval and a rollback plan.
- STOP if threat model/scope is unclear.

### Security changes — Input contract

- Required inputs:
  - Scope + threat model (assets, actors, trust boundaries).
  - Compatibility requirements (who/what may break).
  - Rollback/escape hatch expectations.
- Optional inputs:
  - Compliance constraints, logging/audit requirements, incident history.

### Security changes — Output contract

- Must produce:
  - Proposed change with explicit security rationale.
  - Verification plan (tests + negative cases) and rollback guidance.
- Must satisfy:
  - Ask-first gating for risky/breaking changes; no secrets in artifacts.

### Security changes — DoD checklist (objective)

- Threat model boundaries are stated.
- Verification includes negative tests (deny paths) and expected logs/signals.
- Rollback is specified.

### Security changes — Verification menu

- Quick checks:
  - Run unit/integration tests for auth/permissions; verify deny cases.
- Deep checks:
  - Conduct a small adversarial review: “what if attacker does X?”; validate controls.
- No-network fallback:
  - Use local tests and code inspection; if external identity provider involved, require sandbox/pasted outputs.

### Security changes — Decision points library (copy/paste-ready)

```text
If the threat model is unclear, then STOP and ask for it. Otherwise, continue.
If the change touches authn/authz/crypto/token handling, then ask first and require a rollback plan. Otherwise, proceed with standard verification.
If verification requires external systems, then require sandbox/pasted outputs and avoid using real credentials. Otherwise, run local tests.
```

### Security changes — Failure modes & troubleshooting

- Common failure: “Change weakens a security boundary.”
  - Symptoms: broader access, missing checks, reduced validation.
  - Likely causes: implicit trust assumptions; incomplete threat model.
  - What to do next: re-derive checks from threat model; add deny-path tests; consider feature flag rollout.

### Security changes — Anti-patterns (reviewer red flags)

- “Simplify auth” changes without explicit threat model and deny-path verification.
- Logging sensitive data (tokens, passwords, PII).

### Security changes — Mini exemplar (NON-NORMATIVE)

Security request: “Add role-based access control to admin endpoints.”

1. Define roles and threat model (who should access what).
2. Implement explicit authorization checks with centralized policy.
3. Add tests for allow/deny paths.
4. Provide rollout + rollback plan (feature flag).

---

## Data & migrations (high-risk)

Retrieval key: `category=data-migrations`

Typical risk: high

**Related strict spec sections:** `Risk tiering`, `Ask-first`, `Verification`, `Troubleshooting`.

**Dominant failure mode:** irreversible data loss or schema drift; unvalidated migrations.

### Data & migrations — Intent / typical use cases

Use this category when the skill changes data shape or migration behavior, such as:

- schema migrations (SQL/ORM),
- backfills and data corrections,
- indexing changes and performance migrations,
- data retention and deletion workflows.

### Data & migrations — When NOT to use (common misfires)

- Do not run destructive migrations without explicit approval and backups/rollback.
- STOP if environment (prod/staging/test) is not explicit.

### Data & migrations — Input contract

- Required inputs:
  - Target environment (test/staging/prod) and safety constraints.
  - Schema/data change intent and acceptance criteria.
  - Rollback/backup strategy.
- Optional inputs:
  - Data volume estimates, downtime constraints, migration window.

### Data & migrations — Output contract

- Must produce:
  - Migration/backfill plan and/or code patch.
  - Verification queries/checks with expected result shapes.
  - Rollback steps or compensating migration plan.
- Must satisfy:
  - Ask-first gating for destructive or prod-impacting steps.

### Data & migrations — DoD checklist (objective)

- Verification queries/checks exist and are safe to run in the stated environment.
- Rollback/escape hatch is defined.

### Data & migrations — Verification menu

- Quick checks:
  - Validate migration applies cleanly in test/dev; verify schema version.
- Deep checks:
  - Run verification queries on a representative dataset; check performance.
- No-network fallback:
  - Provide queries for user to run; avoid executing against prod unless explicitly approved.

### Data & migrations — Decision points library (copy/paste-ready)

```text
If environment is not explicit, then STOP and ask which environment is targeted. Otherwise, continue.
If the change is destructive/irreversible (drops/deletes), then ask first and require backups/rollback. Otherwise, proceed.
If data volume is large, then plan batching and performance-safe verification. Otherwise, keep migration simple.
```

### Data & migrations — Failure modes & troubleshooting

- Common failure: “Migration is not reversible.”
  - Symptoms: no rollback path; production risk is high.
  - Likely causes: design omitted escape hatch; irreversible deletes.
  - What to do next: add compensating migration; add soft-delete or staged rollout; document restore steps.

### Data & migrations — Anti-patterns (reviewer red flags)

- Running or recommending prod migrations without explicit approval.
- No verification queries or success criteria.

### Data & migrations — Mini exemplar (NON-NORMATIVE)

Migration request: “Rename column `foo` to `bar`.”

1. Plan expand/contract migration (add new column, dual-write, backfill, switch reads).
2. Provide verification queries for counts and null rates.
3. Ask-first before any destructive drop of old column.
4. Document rollback (switch reads back; stop dual-write).

---

## Ops, release & incident runbooks (high-risk)

Retrieval key: `category=ops-release-incident`

Typical risk: high

**Related strict spec sections:** `Risk tiering`, `Procedure`, `Decision points`, `Verification`, `Troubleshooting`.

**Dominant failure mode:** ambiguous steps during high-stress ops; missing “abort/rollback” branches; unsafe defaults.

### Ops, release & incident runbooks — Intent / typical use cases

Use this category when the skill’s output is an operational runbook, such as:

- release procedures (deploy, rollback, post-deploy checks),
- incident response steps (mitigation, escalation, comms),
- operational maintenance tasks (rotations, renewals, toggles).

### Ops, release & incident runbooks — When NOT to use (common misfires)

- Do not write runbooks that assume privileged access/tools without stating prerequisites and fallbacks.
- STOP if the “who runs this” and “where” (env) are unclear.

### Ops, release & incident runbooks — Input contract

- Required inputs:
  - Target environment(s) and who runs it (oncall/SRE/dev).
  - Objective success signals and abort/rollback expectations.
  - Constraints (no network, read-only, approvals, access levels).
- Optional inputs:
  - Time windows, maintenance policies, incident severity rubric.

### Ops, release & incident runbooks — Output contract

- Must produce:
  - Step-by-step runbook with gates and expected signals per step.
  - Abort/rollback branches and escalation contacts/criteria (if provided).
- Must satisfy:
  - No destructive step without ask-first gating and rollback.

### Ops, release & incident runbooks — DoD checklist (objective)

- Each step has a success/failure signal and “what next” instruction.
- Abort/rollback branch exists and is easy to locate.

### Ops, release & incident runbooks — Verification menu

- Quick checks:
  - “Dry-run” the runbook: read top-to-bottom and confirm prerequisites, signals, and branches exist.
- Deep checks:
  - Execute in a non-prod environment or tabletop exercise (ask-first if it mutates state).
- No-network fallback:
  - Provide offline steps where possible and “paste output” options for checks.

### Ops, release & incident runbooks — Decision points library (copy/paste-ready)

```text
If the target environment and operator are unclear, then STOP and ask. Otherwise, proceed.
If any verification signal fails, then STOP and follow the rollback/abort branch before continuing. Otherwise, continue.
If the step is destructive or risky, then ask first and provide rollback steps. Otherwise, proceed.
```

### Ops, release & incident runbooks — Failure modes & troubleshooting

- Common failure: “Runbook is ambiguous under pressure.”
  - Symptoms: unclear commands, missing expected outputs, missing abort steps.
  - Likely causes: lack of deterministic signals; missing decision points.
  - What to do next: add explicit signals; add abort/rollback; add escalation criteria.

### Ops, release & incident runbooks — Anti-patterns (reviewer red flags)

- “Deploy and check it works” without concrete verification signals.
- Missing rollback or abort guidance.

### Ops, release & incident runbooks — Mini exemplar (NON-NORMATIVE)

Runbook request: “Release v1.2.3.”

1. Preconditions: confirm changelog, version tags, access, maintenance window.
2. Deploy steps with expected signals (health checks, metrics).
3. Post-deploy verification and monitoring window.
4. Rollback branch with explicit triggers and steps.

---

## Appendix: Patterns library (NON-NORMATIVE)

These are reusable phrasing patterns to copy into category sections.

### A. Sampling disclosure (audits)

- "This audit is sample-based: reviewed `<N>` files / `<N>` modules selected by `<method>`. Confidence: `<low/medium/high>`."

### B. Confidence language (audits)

- High: multiple corroborating signals; reproducible via cited evidence.
- Medium: evidence exists but incomplete coverage; plausible alternative explanations.
- Low: limited evidence; treat as hypothesis, not conclusion.

### C. Idempotency wording (pipelines)

- "Idempotency check: re-run `<command/pipeline>`. Expected: no new diffs and the same outputs."

### D. Dry-run wording (pipelines)

- "Dry-run: produce a plan/report only. Do not modify files. Ask-first gate before any apply/mutate step."

### E. Plan/apply/verify headings (pipelines)

- Plan: inputs, constraints, inspection steps, generated plan artifact.
- Apply (Ask first): exact mutating steps, bounded scope, rollback/escape hatch.
- Verify: quick check + deep check + idempotency check.

# Skills Domain Annexes (Meta-skills, Auditing, Pipelines)

This document defines **domain annexes**: category-specific, copy/paste-ready “canonical invariants + verification menus” that complement:

- [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) (normative structure + safety),
- [skills-categories-guide.md](skills-categories-guide.md) (category guidance), and
- [skills-semantic-quality-addendum.md](skills-semantic-quality-addendum.md) (semantic quality minimums + templates).

- **Status:** MIXED (contains NORMATIVE routing contracts + NON-NORMATIVE annex content; each section is labeled).
- **Primary objective:** reduce generic, low-signal skills by providing domain-calibrated invariants and verification patterns for common categories.

## Machine-first contracts (routing invariants) (NORMATIVE)

Section ID: annex.machine-first-contracts

### Document ID (NORMATIVE)

Section ID: annex.machine-first-contracts.document-id

Retrieval key: `spec=skills-domain-annexes`

### Section ID contract (NORMATIVE)

Section ID: annex.machine-first-contracts.section-id-contract

- Every major section has a stable ID line of the form: `Section ID: annex.<id>`.
- IDs are stable; headings may change, but IDs MUST NOT be reused for different content.
- Each annex MUST include a `Retrieval key: annex=<domain>-<category>` line.
- Each annex MUST include a `Category: category=<id>` line.

## Annex index (machine-first) (NORMATIVE)

Section ID: annex.index

| Annex | Domain focus | Category | Retrieve |
|---|---|---|---|
| Meta-skills (local repos) | repo-local prompt/workflow artifacts | `category=meta-skills` | `annex.meta.local-repo` |
| Auditing (local repos) | evidence-first audits in local repos | `category=auditing-assessment` | `annex.audit.local-repo` |
| Pipelines (local repos) | agentic pipelines operating on local repos | `category=agentic-pipelines` | `annex.pipeline.local-repo` |

## Annex template (what every annex SHOULD contain) (guidance; non-normative)

Section ID: annex.template

Recommended subheadings per annex:

1. Intent / typical use cases
2. Canonical invariants (must-not-break)
3. Verification menu (quick / narrow / deep / offline)
4. Decision points library (copy/paste-ready)
5. Evidence attachments (what to include in outputs)
6. Failure modes & troubleshooting
7. Anti-patterns

---

## Meta-skills annex: local repo prompt/workflow artifacts (guidance; non-normative)

Section ID: annex.meta.local-repo

Retrieval key: `annex=local-repo-meta-skills`

Category: `category=meta-skills`

Typical risk: low (can become medium if it recommends risky actions)

### Intent / typical use cases

Use when writing or revising skills/checklists/templates intended to be executed by an agent in a local repo context (sandboxed; possibly no network; approvals required for risky actions).

### Canonical invariants (must-not-break)

These invariants define “semantic correctness” for meta-skills artifacts:

1. **Executable-under-pressure**: a cold reader can follow the procedure without inventing missing steps or context.
2. **No hidden assumptions**: any non-universal assumptions about tooling, repo layout, permissions, or network are declared and have fallbacks.
3. **Gated risk**: if the meta-skill recommends actions that could be breaking/destructive (dependency upgrades, migrations, auth changes, deletes), it includes ask-first/STOP gates and a safer alternative (read-only/dry-run) when feasible.
4. **Objective DoD**: the artifact’s DoD is checkable (“contains sections X/Y/Z”, “includes ≥2 decision points”, “includes a quick check with expected result shape”).
5. **No scope creep**: the artifact does not silently expand into implementation work; it either produces the artifact or explicitly routes to another category.

### Verification menu

- Quick checks:
  - **Structure check**: confirm the produced artifact contains the strict spec’s required content areas and is findable quickly.
  - **Decision density check**: confirm ≥2 explicit “If … then … otherwise …” decision points exist and reference observable triggers.
  - **Risk gate check**: confirm any risky actions are behind ask-first/STOP and the default path is safe-by-default.

- Narrow checks:
  - **Adversarial read**: attempt to follow the artifact assuming:
    1) no network,
    2) missing tools,
    3) ambiguous user intent.
    Expected: the artifact forces STOP/ask rather than improvisation.

- Deep checks:
  - **Cold-run drill**: have someone apply the artifact to a small real task and record ambiguities; revise wording until no ambiguity remains.
  - **Constraint flip test**: run the artifact twice with different constraint sets (“no new deps” vs “deps allowed”) and confirm decision points route correctly.

- Offline / restricted fallback:
  - If the artifact references commands that may not be runnable, it must instruct: “STOP and ask user to paste outputs” and provide a manual inspection alternative.

### Decision points library (copy/paste-ready)

```text
If the user cannot name the target artifact type and audience, then STOP and ask for that. Otherwise, continue.
If the environment is network-restricted, then avoid install/download steps and require pasted outputs/manual inspection. Otherwise, include optional runnable checks.
If the artifact would recommend a breaking/destructive action, then STOP and add an ask-first gate with a dry-run/read-only alternative. Otherwise, keep defaults conservative.
```

### Evidence attachments (what outputs should include)

- Link or path to the produced artifact (`SKILL.md`, checklist, template).
- A “semantic contract” summary (primary goal, non-goals, constraints, acceptance signals).
- A short list of explicit decision points (copy/paste) and what triggers them.

### Failure modes & troubleshooting

- Failure: “Artifact is nice but not executable.”
  - Symptoms: vague verbs (“make sure”), missing expected outputs, missing STOP/ask, missing decision points.
  - Fix: rewrite steps as numbered actions; add observable triggers; add quick checks with expected result shapes.

### Anti-patterns

- Treating “reads well” as success without objective DoD.
- Assuming tools/network/permissions without checks or fallbacks.
- Mixing artifact production with unrequested repo changes.

---

## Auditing annex: local repo evidence-first audits (guidance; non-normative)

Section ID: annex.audit.local-repo

Retrieval key: `annex=local-repo-auditing-assessment`

Category: `category=auditing-assessment`

Typical risk: low→medium (blast radius comes from recommendations, not edits)

### Intent / typical use cases

Use for audits where the primary output is a report: findings + evidence + severity + recommendations + verification suggestions, based on local repo inspection (often without network).

### Canonical invariants (must-not-break)

1. **Evidence-backed claims**: every finding includes a reproducible evidence trail (path + query/inspection + observation shape).
2. **Claim strength discipline**: “global” conclusions require coverage; sampled audits must disclose sampling and confidence.
3. **Scope integrity**: findings do not exceed declared scope; out-of-scope areas are explicitly labeled.
4. **No secret exposure**: audit outputs must not include credentials, tokens, private keys, or sensitive personal data; redact snippets.
5. **Actionability**: each finding includes a next step and at least one objective verification suggestion.

### Verification menu

- Quick checks:
  - Every finding has: **Evidence**, **Impact**, **Recommendation**, **Verification**.
  - Scope/method sections exist and match the strength of claims.
  - Sampling (if any) is disclosed and confidence is labeled.

- Narrow checks:
  - Spot-check 2–3 findings by re-running the cited searches/inspections (or asking user to do so) and confirm the evidence supports the claim.

- Deep checks:
  - Repeat audit on a second sample slice (different directory/module) and compare whether findings generalize; downgrade claim strength if they do not.
  - Cross-check severity ratings against a stated rubric; adjust inconsistent items.

- Offline / restricted fallback:
  - Prefer local-only methods (file inspection, `rg`-style searches, parsing configs).
  - If a claim requires external validation, require user-pasted outputs and label confidence accordingly.

### Decision points library (copy/paste-ready)

```text
If scope is not explicit (paths/components/time budget), then STOP and ask for scope boundaries. Otherwise, continue.
If full coverage is infeasible, then use sampling and explicitly label confidence and “sampled vs global.” Otherwise, do comprehensive coverage.
If a recommendation would require risky/breaking changes (auth, migrations, deletions), then recommend a separate high-risk change skill and do not proceed without ask-first approval. Otherwise, keep as suggestions.
```

### Evidence attachments (what outputs should include)

For each finding, attach:
- Scope label: `global` or `sampled`.
- Confidence: `low/medium/high`.
- Evidence trail: `<path(s)>` + `<search/query>` + `<observed snippet or output shape>`.
- Verification suggestion: one objective check a user could run/observe.

### Failure modes & troubleshooting

- Failure: “Findings are not reproducible.”
  - Symptoms: claims without paths/queries; conclusions not traceable.
  - Fix: add evidence trail; downgrade confidence; split “hypothesis” vs “verified finding.”

- Failure: “Sampled audit stated as universal truth.”
  - Symptoms: global language despite partial coverage.
  - Fix: label sampling; adjust wording; recommend targeted follow-up for global claims.

### Anti-patterns

- Severity labels without a rubric.
- Global claims from tiny samples without disclosure.
- Including long sensitive excerpts; failing to redact.

---

## Agentic pipelines annex: local repo scan→plan→apply→verify (guidance; non-normative)

Section ID: annex.pipeline.local-repo

Retrieval key: `annex=local-repo-agentic-pipelines`

Category: `category=agentic-pipelines`

Typical risk: medium→high (pipelines can mutate state; must be gated)

### Intent / typical use cases

Use for multi-step agent workflows that orchestrate repo inspection, planning, patching, and verification—especially when some steps may be unsafe, non-idempotent, or environment-dependent.

### Canonical invariants (must-not-break)

1. **Safe-by-default**: default mode is read-only or plan-only when feasible.
2. **Ask-first for mutation**: any write/destructive/irreversible step is behind explicit ask-first.
3. **Idempotency**: re-running should be a no-op or produce identical outputs; non-idempotent steps must be explicitly justified and gated.
4. **Step-level signals**: each step has an explicit success/failure signal and a “what next” on failure.
5. **Partial run recovery**: pipeline defines how to resume safely after interruption.
6. **No secret leakage**: logs/artifacts must redact sensitive data.

### Verification menu

- Quick checks:
  - Confirm the pipeline has an explicit **plan/apply/verify** separation (or equivalent gates).
  - Confirm all mutating steps are ask-first gated and offer a dry-run/read-only alternative when feasible.
  - Confirm each step defines a success signal and a stop condition.

- Narrow checks:
  - Dry-run the pipeline on a small target subset (single directory, one file, one module); confirm deterministic ordering and stable outputs.

- Deep checks:
  - Re-run immediately to validate idempotency (no additional diffs, no drifting artifacts).
  - Simulate an interruption mid-run; confirm the “resume” procedure does not corrupt state.

- Offline / restricted fallback:
  - Provide “offline mode” that relies only on local inspection and user-pasted outputs for any external dependencies; avoid installs/downloads by default.

### Decision points library (copy/paste-ready)

```text
If network is restricted, then run in offline mode and require pasted outputs for any external dependency. Otherwise, include optional runnable checks.
If a step mutates state (writes, deletes, deploys, migrations), then ask first and provide a dry-run/read-only alternative. Otherwise, proceed.
If any verification step fails, then STOP and troubleshoot before continuing. Otherwise, continue to the next step.
If the pipeline is not idempotent, then STOP and either (a) redesign for determinism or (b) explicitly gate and justify non-idempotent behavior. Otherwise, continue.
```

### Evidence attachments (what outputs should include)

- A “run log” summary: which steps executed, which were skipped, and why.
- For each step: inputs, success signal observed, and produced artifacts (paths).
- For any skipped verification: `Not run (reason)` + exact command to run + expected result shape.

### Failure modes & troubleshooting

- Failure: “Pipeline is unsafe by default.”
  - Symptoms: writes happen without ask-first; deletes/migrations run automatically.
  - Fix: split plan/apply; add explicit gates; default to dry-run/read-only.

- Failure: “Pipeline is not idempotent.”
  - Symptoms: second run produces different ordering/diffs; outputs drift.
  - Fix: sort inputs deterministically; avoid timestamps; record state; add explicit no-op checks.

- Failure: “Pipeline depends on network/tools silently.”
  - Symptoms: steps fail in restricted environments; agent tries to install tools.
  - Fix: add offline mode; require user-pasted outputs; provide manual inspection paths.

### Anti-patterns

- A single monolithic “run everything” step without stop conditions.
- Mutating steps prior to evidence collection or planning.
- Verification treated as optional (“looks fine”).


# Shared Contract — Spec Writing System

Authoritative reference for the spec-writing system. Defines the `spec.yaml` schema, claims vocabulary, derivation table, and conventions used by both the spec-writer and spec-review-team skills.

**Consumers:** spec-writer skill (producer-side validation), spec-review-team skill (consumer-side routing and precedence). Changes to this document require updating both skills.

## spec.yaml

A dedicated YAML file alongside `README.md`. README is the human entry point; `spec.yaml` is the machine source of truth.

**Conflict rule:** `spec.yaml` is authoritative for tooling; README summarizes it; contradictions between them are defects.

**Schema:**

```yaml
shared_contract_version: 1
readme: README.md

authorities:
  <authority-label>:
    description: <what this authority covers in this spec's domain>
    default_claims: [<claim>, ...]

precedence:
  normative_first: true
  claim_precedence:
    <claim>: [<authority>, ...]   # per-finding, first wins
  fallback_authority_order: [<authority>, ...]
  unresolved: ambiguity_finding

boundary_rules:
  - on_change_to: [<authority>]
    review_authorities: [<authority>, ...]
    reason: <why>
```

No `review_cluster` field — structural roles are derived from claims using the derivation table below.

## Claims Enum

The only fixed vocabulary in the shared contract. 8 values.

| Claim | What the file contains | Specialist trigger |
|-------|----------------------|-------------------|
| `architecture_rule` | Architectural constraints, cross-cutting invariants | — |
| `decision_record` | Locked design decisions, accepted tradeoffs | — |
| `behavior_contract` | Behavioral promises, user-facing semantics | — |
| `interface_contract` | Interface definitions, API surfaces, compatibility guarantees | — |
| `persistence_schema` | Data model, storage constraints, state representation | schema-persistence |
| `enforcement_mechanism` | Validation, hooks, access control, policy enforcement | integration-enforcement |
| `implementation_plan` | Build strategy, migration sequencing, rollout | — |
| `verification_strategy` | Test design, coverage plans, regression strategy | — |

**Specialist triggering:** A specialist spawns when any **normative** file in the spec has the specialist's trigger claim in its effective claims. Non-normative files do not trigger specialist spawning.

## Claim-to-Role Derivation Table

Both skills use this table. The spec-writer uses it for self-validation. The spec-review-team uses it for redirect gate and reviewer routing.

| Derived role | Claims that produce it | Counts in redirect gate? |
|---|---|---|
| `foundation` | `architecture_rule`, `decision_record` | Yes |
| `behavior` | `behavior_contract`, `interface_contract` | Yes |
| `execution` | `implementation_plan`, `verification_strategy` | Yes |
| `state` | `persistence_schema` | Yes |
| `enforcement` | `enforcement_mechanism` | Yes |
| `reference` | zero effective claims | No |

**Derivation rules:**

- A file's derived roles come from its effective claims. Each claim maps to exactly one role.
- A file with claims spanning multiple roles (e.g., `behavior_contract` + `enforcement_mechanism`) participates in both `behavior` and `enforcement`. Multi-role files increase the spec's structural complexity score.
- The redirect gate counts distinct derived roles present across normative files, excluding `reference`.
- `reference` = file has zero effective claims. Only valid for non-normative files (see normative claim rule in File Frontmatter).

## File Frontmatter

Every spec file:

```yaml
---
module: <kebab-case-identifier>
status: active | draft | stub | deprecated
normative: true | false
authority: <authority-label from spec.yaml>
claims: [<claim>, ...]  # optional, additive, max 3 effective
---
```

**Field rules:**

| Field | Required? | Rule |
|-------|-----------|------|
| `module` | Always | Kebab-case identifier |
| `status` | Always | `active` (live), `draft` (in progress), `stub` (planned, not yet filled), `deprecated` (superseded) |
| `normative` | Always | Explicit on every file — no inheritance |
| `authority` | When `spec.yaml` exists | Must reference a label defined in `spec.yaml` |
| `claims` | Optional | Additive — extends `default_claims` from authority |

**Claims semantics:**

- When `claims` is omitted, file inherits authority's `default_claims`.
- When `claims` is present, it **adds to** the defaults (not replaces).
- Maximum 3 effective claims per file (inherited + declared). Exceeding 3 is a validation finding.

**Normative claim rule:** Any `normative: true` file must have ≥1 effective claim. `default_claims: []` is only valid for non-normative authorities. A normative file with zero effective claims is a validation finding.

**Claim divergence signal:** Files whose effective claims produce a different derived role set than their authority's `default_claims` would produce are flagged as high-attention review surfaces. Within-role additions (e.g., adding `interface_contract` to an authority that already defaults to `behavior_contract`) are normal and not flagged.

**Supporting files** (README, glossary, amendments, appendices): Define an authority with `default_claims: []`. These files must be `normative: false`. Derived role: `reference`.

## Precedence Resolution

Precedence is adjudicated **per finding against one claim family**, not per file. A multi-claim file can participate in different precedence chains depending on which claim the finding addresses.

| Step | Rule | Scope |
|------|------|-------|
| 1 | `normative: true` beats `normative: false` | Always applied first |
| 2 | `claim_precedence` for the finding's `claim_family` | When the reviewer identifies which claim the finding addresses |
| 3 | `fallback_authority_order` | When files share an `affected_surface` AND no claim-specific rule matched, OR when the authority is not listed in the applicable `claim_precedence` entry |
| 4 | Emit ambiguity finding | When still unclear, or authority not in `fallback_authority_order` either — escalate to human |

**Required schema addition:** Each finding must include a `claim_family` field — the specific claim the finding addresses. This enables mechanical application of `claim_precedence` during synthesis. If a reviewer cannot identify one claim family, the finding escalates as ambiguous.

**`claim_precedence` lists are partial.** Authorities not listed in a claim's precedence entry fall through to `fallback_authority_order`. Authorities not in either list produce an ambiguity finding. Partial lists mean the spec author only declares precedence where they are confident.

**Definition of "surface":** A finding's surface is its `affected_surface` field (file + section/anchors). Two findings "share a surface" when their `affected_surface` values reference the same file and overlapping sections.

## Boundary Rules

Boundary rules have two defined consumers with explicit minimum behavior.

**Spec-writer (validation-time, not creation-time):** By final validation (Phase 7 of the writing workflow), cross-references must exist between files whose authorities are linked by boundary rules. Specifically: for each authority X that appears in any `on_change_to` list, at least one file under X must contain a cross-reference to at least one file under each `review_authorities` authority. The writer does not enforce this at file creation time — target files may not exist yet.

**Spec-review-team:** When a finding's `affected_surface` touches a file under authority X that appears in `on_change_to`, the reviewer verifies at least one reviewer examined files under each `review_authorities` authority for defects related to the boundary rule's stated `reason`. Unexamined boundary authorities become coverage findings.

## Cross-Reference Conventions

- Relative markdown links with semantic kebab-case anchors
- No section numbers as anchors
- Anchors must be unique within a file and stable across revisions unless the section's meaning changes
- `README.md` contains a numbered reading-order table linking every file

## Failure Model

Failure behavior differs for the producer (spec-writer) and consumer (spec-review-team).

### Producer Failures (hard failures — fix before continuing)

| Condition | Response |
|-----------|----------|
| Authority referenced in file not defined in `spec.yaml` | Hard failure |
| Normative file has zero effective claims | Hard failure |
| Effective claims exceed 3 per file | Hard failure |
| Cross-references don't resolve | Hard failure |
| Unknown claim value in `default_claims` or file `claims` | Hard failure |
| `claim_precedence` key outside the fixed claim enum | Hard failure |
| Authority in `claim_precedence`, `fallback_authority_order`, or `boundary_rules` not defined in `authorities` | Hard failure |
| `spec.yaml` missing required top-level key (`authorities`, `precedence`) or missing required field within `precedence` (`fallback_authority_order`, `unresolved`) | Hard failure |
| `spec.yaml` top-level key has wrong type (e.g., `boundary_rules: {}` instead of list, `authorities: []` instead of mapping) | Hard failure |

### Consumer Failures (degrade gracefully)

| Condition | Response |
|-----------|----------|
| `spec.yaml` missing | Degraded mode — fall back to frontmatter + path heuristics. Warn: "No spec.yaml. Consider running the spec-writer skill." |
| `spec.yaml` malformed (unparseable YAML) | Hard stop with parse error |
| `spec.yaml` parseable but structurally invalid (missing required top-level keys: `authorities`, `precedence`; or wrong types: `boundary_rules: {}` instead of list) | Hard stop with structural validation error |
| File references unknown authority | Validation finding (P1). Process file as `authority: unknown`. |
| Unknown claim value in frontmatter | Validation finding (P1). Unknown claims ignored for role derivation. |
| `claim_precedence` references undefined authority | Validation finding (P1). Skip that entry during adjudication. |
| Unsupported `shared_contract_version` | Hard stop. Report expected vs actual. |
| `spec.yaml` present but no files have frontmatter | Degraded mode. Warn user. |

## Concrete Example

**CLI tool with no database:**

```yaml
# spec.yaml
shared_contract_version: 1
readme: README.md

authorities:
  foundation:
    description: CLI architecture, shared terminology, cross-command invariants.
    default_claims: [architecture_rule]

  command-contract:
    description: Command behavior, flags, exit codes, user-visible semantics.
    default_claims: [behavior_contract, interface_contract]

  config-contract:
    description: Configuration file format, precedence, and validation rules.
    default_claims: [behavior_contract, interface_contract]

  output-contract:
    description: Structured output formats and compatibility guarantees.
    default_claims: [interface_contract]

  delivery:
    description: Packaging, rollout, and test strategy.
    default_claims: [implementation_plan, verification_strategy]

  decisions:
    description: Locked decisions and accepted tradeoffs.
    default_claims: [decision_record]

  supporting:
    description: Glossary, appendix, and reference material.
    default_claims: []

precedence:
  normative_first: true
  claim_precedence:
    behavior_contract: [command-contract, config-contract, foundation, delivery, decisions]
    interface_contract: [output-contract, command-contract, config-contract, delivery, decisions]
    verification_strategy: [delivery, command-contract, config-contract, decisions]
  fallback_authority_order: [foundation, command-contract, config-contract, output-contract, delivery, decisions]
  unresolved: ambiguity_finding

boundary_rules:
  - on_change_to: [command-contract]
    review_authorities: [config-contract, output-contract, delivery]
    reason: Command changes affect config interpretation, output formats, and test coverage.
  - on_change_to: [config-contract]
    review_authorities: [command-contract, delivery]
    reason: Config precedence changes can alter command behavior and test expectations.
```

**What the review team derives:**

- Normative files with effective claims produce roles: `foundation` (from architecture_rule, decision_record), `behavior` (from behavior_contract, interface_contract), `execution` (from implementation_plan, verification_strategy) → **3 gating roles**
- No `persistence_schema` or `enforcement_mechanism` claims on normative files → no optional specialists
- `supporting` authority has `default_claims: []` and is non-normative → derived role `reference`, excluded from gate
- Redirect gate: 3 distinct roles + 5 boundary edges (from 2 rules) → warrants full team review

**A typical file:**

```yaml
---
module: command-behavior
status: active
normative: true
authority: command-contract
---
```

Inherits `[behavior_contract, interface_contract]`. Derived roles: `behavior`. No `claims` field needed.

# Spec Writing System Design

**Date:** 2026-03-15
**Status:** Draft
**Purpose:** Design a spec-writing framework that produces modular, review-ready specifications from approved design documents.

## Problem

Specs created during brainstorming routinely reach 2,000–5,000 lines as single files. These monoliths are difficult to reference in Claude conversations — loading the full document consumes context, and there's no way to load only the relevant section without knowing the document's internal structure.

## Solution

Three components form a spec lifecycle:

1. **Shared Contract** — defines the `spec.yaml` schema, file frontmatter rules, claim-to-role derivation, and conventions that both skills conform to
2. **Spec-Writing Skill** (new) — compiles an approved design document into a modular spec with `spec.yaml` and properly-frontmatted files
3. **Spec-Review-Team** (updated) — reads `spec.yaml` to derive authority semantics and map them into internally-derived structural roles for reviewer routing and complexity assessment

Plus a PostToolUse hook as a passive safety net for large file writes.

```
Brainstorming Skill          Spec-Writing Skill         Spec-Review-Team
─────────────────            ──────────────────         ────────────────
design doc (single file)  →  spec.yaml + modular spec  →  validated spec
                                      ↑
                              Shared Contract defines
                              the structure both use
```

**Key architectural decision:** Claims are the only fixed vocabulary authors interact with. Structural roles used for review routing are derived from claims by both skills using a shared derivation table — never declared by spec authors.

---

## Section 1: Shared Contract

### 1.1 spec.yaml

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

No `review_cluster` field — structural roles are derived from claims by both skills using the shared derivation table (§1.3).

### 1.2 Claims Enum

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

**Specialist triggering:** A specialist spawns when any **normative** file in the spec has the specialist's trigger claim in its effective claims. Non-normative files do not trigger specialist spawning — a non-normative appendix that mentions enforcement doesn't warrant a specialist reviewer.

### 1.3 Claim-to-Role Derivation Table

This table is part of the shared contract — both skills use it. The spec-writing skill uses it to self-validate corpus structure. The spec-review-team uses it for redirect gate and reviewer routing.

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
- A file with claims spanning multiple roles (e.g., `behavior_contract` + `enforcement_mechanism`) participates in both `behavior` and `enforcement`. This is intentional — multi-role files are where cross-cutting defects concentrate, so they increase the spec's structural complexity score.
- The redirect gate counts distinct derived roles present across normative files, excluding `reference`.
- `reference` = file has zero effective claims. Only valid for non-normative files (see normative claim rule in §1.4).

### 1.4 File Frontmatter

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

**Normative claim rule:** Any `normative: true` file must have ≥1 effective claim. `default_claims: []` is only valid for non-normative authorities. A normative file with zero effective claims is a validation finding — it drops out of the redirect gate and has no usable precedence chain.

**Claim divergence signal:** Files whose effective claims produce a different derived role set than their authority's `default_claims` would produce are flagged as high-attention review surfaces. Within-role additions (e.g., adding `interface_contract` to an authority that already defaults to `behavior_contract`) are normal and not flagged.

**Supporting files** (README, glossary, amendments, appendices): Define an authority with `default_claims: []`. These files must be `normative: false`. Derived role: `reference`.

### 1.5 Precedence Resolution

Precedence is adjudicated **per finding against one claim family**, not per file. A multi-claim file can participate in different precedence chains depending on which claim the finding addresses.

| Step | Rule | Scope |
|------|------|-------|
| 1 | `normative: true` beats `normative: false` | Always applied first |
| 2 | `claim_precedence` for the finding's `claim_family` | When the reviewer identifies which claim the finding addresses |
| 3 | `fallback_authority_order` | When files share an `affected_surface` AND no claim-specific rule matched, OR when the authority is not listed in the applicable `claim_precedence` entry |
| 4 | Emit ambiguity finding | When still unclear, or authority not in `fallback_authority_order` either — escalate to human |

**Required schema addition:** Each finding must include a `claim_family` field — the specific claim the finding addresses. This enables mechanical application of `claim_precedence` during synthesis. If a reviewer cannot identify one claim family, the finding escalates as ambiguous.

**`claim_precedence` lists are partial.** Authorities not listed in a claim's precedence entry fall through to `fallback_authority_order`. Authorities not in either list produce an ambiguity finding. This is intentional — partial lists mean the spec author only declares precedence where they are confident, and genuine ambiguity surfaces rather than being force-resolved.

**Definition of "surface":** A finding's surface is its `affected_surface` field (file + section/anchors). Two findings "share a surface" when their `affected_surface` values reference the same file and overlapping sections.

### 1.6 Boundary Rules

Boundary rules have two defined consumers with explicit minimum behavior.

**Spec-writing skill (validation-time, not creation-time):** By final validation (Phase 7 of the writing workflow), cross-references must exist between files whose authorities are linked by boundary rules. Specifically: for each authority X that appears in any `on_change_to` list, at least one file under X must contain a cross-reference to at least one file under each `review_authorities` authority. The writer does not enforce this at file creation time — target files may not exist yet.

**Spec-review-team:** When a finding's `affected_surface` touches a file under authority X that appears in `on_change_to`, the reviewer verifies at least one reviewer examined files under each `review_authorities` authority for defects related to the boundary rule's stated `reason`. Unexamined boundary authorities become coverage findings.

### 1.7 Cross-Reference Conventions

- Relative markdown links with semantic kebab-case anchors
- No section numbers as anchors
- Anchors must be unique within a file and stable across revisions unless the section's meaning changes
- `README.md` contains a numbered reading-order table linking every file

### 1.8 Failure Model

Failure behavior differs for the producer (spec-writing skill) and consumer (spec-review-team).

**Producer failures (spec-writing skill) — hard failures, fix before continuing:**

| Condition | Response |
|-----------|----------|
| Authority referenced in file not defined in `spec.yaml` | Hard failure |
| Normative file has zero effective claims | Hard failure |
| Effective claims exceed 3 per file | Hard failure |
| Cross-references don't resolve | Hard failure |
| Unknown claim value in `default_claims` or file `claims` | Hard failure |
| `claim_precedence` key outside the fixed claim enum | Hard failure |
| Authority in `claim_precedence`, `fallback_authority_order`, or `boundary_rules` not defined in `authorities` | Hard failure |

**Consumer failures (spec-review-team) — degrade gracefully:**

| Condition | Response |
|-----------|----------|
| `spec.yaml` missing | Degraded mode — fall back to frontmatter + path heuristics. Warn: "No spec.yaml. Consider running the spec-writing skill." |
| `spec.yaml` malformed (unparseable YAML) | Hard stop with parse error |
| File references unknown authority | Validation finding (P1). Process file as `authority: unknown`. |
| Unknown claim value in frontmatter | Validation finding (P1). Unknown claims ignored for role derivation. |
| `claim_precedence` references undefined authority | Validation finding (P1). Skip that entry during adjudication. |
| Unsupported `shared_contract_version` | Hard stop. Report expected vs actual. |
| `spec.yaml` present but no files have frontmatter | Degraded mode. Warn user. |

### 1.9 Concrete Example

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
- Redirect gate: 3 distinct roles + 2 boundary rules → warrants full team review

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

---

## Section 2: Spec-Writing Skill

### 2.1 Purpose

Compile an approved design document into a modular spec with `spec.yaml` and properly-frontmatted files. This skill is a **compiler with one architectural checkpoint** — it does not re-explore the design space. The design doc is already approved; this skill transforms it into a structured, review-ready artifact.

### 2.2 Entry Conditions

- An approved design document exists (output of brainstorming skill or equivalent)
- The document covers architecture, components, data flow, error handling, and/or testing
- The user has explicitly invoked the skill or been nudged by the PostToolUse hook

### 2.3 Workflow

```
Phase 1: ENTRY GATE
    ↓
Phase 2: ANALYSIS (automatic)
    ↓
Phase 3: ARCHITECTURE CHECKPOINT (mandatory user gate)
    ↓
Phase 4: MANIFEST (write spec.yaml)
    ↓
Phase 5: SCAFFOLD (write README.md)
    ↓
Phase 6: AUTHOR (write spec files in dependency order)
    ↓
Phase 7: VALIDATE (automatic)
    ↓
Phase 8: HANDOFF (present to user)
```

One mandatory approval gate (Phase 3). One optional midpoint gate (Phase 6, for large docs). Phase 8 is a handoff step, not an approval gate.

### Phase 1: ENTRY GATE

**Gate:** Confirmed input is an approved design artifact.

1. Confirm the input design doc path.
2. Verify it is the approved post-brainstorm artifact:
   - If design space is reopened (requirements unclear, approach contested) → redirect to **brainstorming**.
   - If design exists but needs rigor or completeness review → redirect to **`reviewing-designs`**.
3. If the document is under ~300 lines with a single concern and no distinct authority boundaries, recommend keeping it as a single file. Do not modularize for modularization's sake.

### Phase 2: ANALYSIS

**Gate:** Translation ledger built with every major source section mapped.

Read the entire design document once. Build a **translation ledger** — a mapping from source sections to candidate destination files:

| Source Section | Candidate File | Authority | Inherited Claims | Confidence | Rationale |
|---|---|---|---|---|---|
| §Architecture Overview | `foundations.md` | foundation | architecture_rule | high | Self-contained architectural content |
| §Command Semantics | `commands/behavior.md` | command-contract | behavior_contract, interface_contract | high | User-facing behavioral promises |
| §Testing Strategy + §Rollout | `delivery/testing.md` | delivery | implementation_plan, verification_strategy | medium | May need split if testing and rollout diverge |

**Granularity rule:** When a source section maps to multiple files or has medium/low confidence, the ledger must descend to subsection or topic-block granularity for that section. Section-level mapping is insufficient for splits — Phase 7's source coverage and orphan checks depend on fine-grained traceability.

The ledger also proposes:
- Authority labels and their `default_claims`
- Precedence rules (which authorities should win for which claim families)
- Boundary rules (which authorities are coupled)
- Ambiguous splits — sections that could belong to multiple authorities

This phase is automatic — no user interview. The design doc provides the domain understanding; the skill derives the structure. If the document is structurally weak (no identifiable sections, no clear authority boundaries), flag this at the architecture checkpoint rather than interviewing.

### Phase 3: ARCHITECTURE CHECKPOINT

**Gate:** User approves the proposed spec architecture. This is the single mandatory approval gate.

Present a compact proposal:

1. **File tree** — proposed directory structure and files
2. **`spec.yaml` draft** — full manifest including authorities, precedence, boundary rules
3. **Translation ledger** — which source sections map where, with confidence levels
4. **Ambiguous splits** — sections where the destination is uncertain, with the skill's recommendation and reasoning
5. **Derived role summary** — what the review team will see (using the shared derivation table from §1.3)

The user approves, requests changes, or rejects. Do not proceed without explicit approval. If rejected, revise based on feedback and re-present.

**Optional midpoint gate:** For design docs over ~1500 lines or with >3 low-confidence splits, offer a midpoint checkpoint after the normative backbone (Phase 6, step 1) — "Here's the foundational content. Does this look right before I continue with dependent files?"

### Phase 4: MANIFEST

**Gate:** `spec.yaml` written and self-validated.

Write `spec.yaml` as the first durable artifact. After this point, `spec.yaml` is stable — any change to authorities, precedence, or boundary rules reopens the architecture checkpoint. Minor wording changes to descriptions are permitted without reconfirmation.

Self-validate the manifest against the shared contract:
- All claims in `default_claims` are from the fixed enum (§1.2)
- All authorities referenced in `claim_precedence`, `fallback_authority_order`, and `boundary_rules` are defined in `authorities`
- At least one normative-compatible authority exists (an authority whose `default_claims` is non-empty, meaning it can back `normative: true` files without violating the normative claim rule from §1.4)
- `shared_contract_version` is set

### Phase 5: SCAFFOLD

**Gate:** `README.md` written with reading order and valid frontmatter.

`README.md` is a spec file and must carry frontmatter per the shared contract (§1.4):

```yaml
---
module: readme
status: active
normative: false
authority: supporting  # or equivalent zero-claim authority
---
```

Content includes:
- Spec title and overview
- Authority model summary (human-readable version of `spec.yaml`)
- Numbered reading-order table linking every planned file with a one-line description
- Cross-reference conventions used in this spec

README will be refreshed at the end of Phase 6 once exact files and summaries are final.

### Phase 6: AUTHOR

**Gate:** All planned files written.

Write files in **dependency order** — normative backbone first, then dependent content:

1. **Normative backbone:** `foundations.md`, `decisions.md`, and top-level behavioral/contract files. These establish the authoritative content that dependent files reference.
2. **Dependent clusters:** Remaining behavioral files → state/schema files → enforcement/control files → execution/implementation files → reference/supporting files.

Within a cluster, write overview files before detail files.

**Transformation rule — semantic preservation:**

The design document is conversational prose written during brainstorming. Spec files are structured reference material. The skill transforms form, not meaning:

| Permitted | Forbidden |
|-----------|-----------|
| Split sections across files | Invent new decisions not in the design doc |
| Normalize inconsistent terminology | Silently resolve ambiguities the design doc left open |
| Tighten prose, remove hedging | Drop caveats or qualifications |
| Convert narrative to tables | Change behavioral meaning |
| Make implicit constraints explicit (see rule below) | Add requirements not present in the source |
| Adjust heading levels | Reorder content in ways that change semantic relationships |

**Implicit-to-explicit rule:** Make implicit constraints explicit only when directly entailed by approved source text. Never introduce new constants, precedence rules, failure modes, or normative language (MUST/SHOULD) not grounded in the design document. If an implication is ambiguous, preserve the ambiguity and flag it in the translation ledger — the spec-review-team will surface it.

**Frontmatter generation:** Every file gets frontmatter per the shared contract (§1.4). The skill assigns `module`, `status`, `normative`, and `authority` based on the approved translation ledger. `claims` is omitted when defaults suffice.

### Phase 7: VALIDATE

**Gate:** All validation checks pass.

| Check | What it verifies |
|-------|-----------------|
| Source coverage | Every major source section from the translation ledger appears in at least one destination file |
| Orphan check | No design requirements from the source are missing in the spec corpus |
| Frontmatter validity | All authorities exist in `spec.yaml`; all claims valid; no normative file has zero effective claims; effective claims ≤3 per file |
| Semantic validation | No unknown claims in defaults or frontmatter; no undefined authorities in precedence/boundary rules |
| Link resolution | All cross-references resolve to existing files; anchors exist in target files |
| Boundary coverage | For each authority in `on_change_to`, at least one file under it cross-references at least one file under each `review_authorities` authority |
| Reading order | README's reading-order table is complete and accurate |
| Derivation check | Derived roles produce the expected structural complexity (self-check against shared derivation table from §1.3) |

Refresh `README.md` with final file summaries after all content files are written.

Producer failure rules apply (§1.8): any validation failure is a hard failure. Fix before proceeding to handoff.

### Phase 8: HANDOFF

Present the completed spec to the user.

1. **Summary:** file count, authority count, derived roles, boundary rules, any validation notes.
2. **Recommend `spec-review-team`:** "The spec is ready for review. Would you like me to run `spec-review-team`?"
3. Auto-invoke `spec-review-team` only if the user explicitly requested write-and-review in one flow. Otherwise, wait for user decision.

### 2.4 Skill Metadata

```yaml
name: spec-writer
description: >
  Compile approved design documents into modular, review-ready specifications
  with spec.yaml manifests and properly-frontmatted files. Use when formalizing
  a design into a multi-file spec, when a design doc exceeds 500 lines and
  needs modular structure, when the user says "write a spec", "formalize this
  design", "modularize this", "create spec files", or when the PostToolUse
  hook nudges that a file is large enough to benefit from modular structure.
  Downstream of brainstorming — do not use for design exploration.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
```

---

## Section 3: Spec-Review-Team Updates

This section describes delta changes to the existing `spec-review-team` skill to consume the shared contract.

### 3.1 What Stays the Same

- **6-phase structure:** DISCOVERY → ROUTING → PREFLIGHT → REVIEW → SYNTHESIS → PRESENT
- **4 core reviewers:** authority-architecture, contracts-enforcement, completeness-coherence, verification-regression (defect-class-based, domain-agnostic)
- **2 optional specialists:** schema-persistence, integration-enforcement
- **Lateral messaging:** message (targeted) and broadcast (all teammates) primitives
- **Completion contract:** idle notifications, wall-clock timeout, partial completion handling
- **Cleanup contract:** shutdown requests, TeamDelete, workspace preservation prompt
- **Audit metrics:** all 10 metrics retained

### 3.2 What Changes

#### DISCOVERY (Phase 1)

| Before | After |
|--------|-------|
| Parse frontmatter, extract `authority` field, map to 6 fixed clusters | Parse frontmatter AND `spec.yaml`. If `spec.yaml` exists: read authority registry, derive structural roles from claims using the shared derivation table (§1.3). If absent: degraded mode (current behavior). |
| Authority map records: normative flag, source authority, review cluster | Authority map records: file path, normative flag, authority label, effective claims, derived roles, boundary-rule participation (source/target/neither) |
| Path heuristics always applied | Path heuristics only in degraded mode (no `spec.yaml`) |

The expanded authority map feeds later phases: ROUTING uses derived roles for the redirect gate, PREFLIGHT uses effective claims for specialist spawning, SYNTHESIS uses boundary-rule participation for coverage analysis.

#### ROUTING (Phase 2)

| Before | After |
|--------|-------|
| Redirect gate counts `confident_review_cluster_count` from 6 fixed clusters | Redirect gate counts distinct derived roles (excluding `reference`) from normative files |
| `boundary_edges` inferred from cluster transitions | `boundary_edges` computed from `spec.yaml` `boundary_rules` |
| Specialist triggers via multi-signal heuristic scoring (Tier 1 / Tier 2) | Specialist triggers deterministic when `spec.yaml` exists: spawn when any normative file has the trigger claim in effective claims. Heuristic scoring retained for degraded mode only. |

**`boundary_edges` count rule:** Count unique directional `(on_change_to authority, review_authority)` pairs across all boundary rules. One rule with 3 `review_authorities` = 3 edges. Example: 2 boundary rules in the CLI spec produce 5 edges (3 + 2).

#### PREFLIGHT (Phase 3)

| Before | After |
|--------|-------|
| Phase 3A validates `authority` as required on every file | Phase 3A validates `authority` required only when `spec.yaml` exists |
| Mechanical checks: frontmatter + cross-references | Add semantic manifest validation: unknown claims in defaults/frontmatter, undefined authority references in precedence/boundary rules, normative files with zero effective claims, effective claims >3. Consumer failure rules apply (§1.8). |
| Spawn plan based on heuristic signal scoring | Spawn plan based on deterministic claim presence (when `spec.yaml` exists) or heuristic scoring (degraded mode) |

The preflight packet's 6 sections update to match:

| Section | Change |
|---------|--------|
| `authority_map` | Expanded: file path, normative flag, authority label, effective claims, derived roles, boundary-rule participation |
| `boundary_edges` | Computed from `spec.yaml` boundary_rules (or cluster transitions in degraded mode) |
| `signal_matrix` | Simplified when `spec.yaml` exists (binary claim presence). Retained for degraded mode. |
| `mechanical_checks` | Expanded with semantic manifest validation results |
| `route_decision` | Uses derived role count instead of cluster count |
| `spawn_plan` | Deterministic from claims (spec.yaml) or heuristic (degraded) |

#### Finding Schema

Add one required field:

```markdown
### [PREFIX-N] Title

- **priority:** P0 / P1 / P2
- **title:** One-sentence description
- **claim_family:** <claim from fixed enum, or "ambiguous">  ← NEW
- **violated_invariant:** source_doc#anchor
- **affected_surface:** file + section/lines
- **impact:** 1-2 sentences
- **evidence:** what doc says vs what it should say
- **recommended_fix:** specific action
- **confidence:** high / medium / low
- **provenance:** independent / followup
- **prompted_by:** {reviewer-name} (required when followup)
```

`claim_family` enables mechanical application of `claim_precedence` during synthesis. If a reviewer cannot identify one claim family, set `claim_family: ambiguous` — the finding escalates to human resolution.

#### SYNTHESIS (Phase 5)

| Before | After |
|--------|-------|
| Contradiction resolution: normative > non-normative, then domain reasoning | Resolution uses `spec.yaml` precedence rules: normative_first → claim_precedence (per-finding `claim_family`) → fallback_authority_order → ambiguity finding. See §1.5. |
| No structured precedence model | Mechanical application of declared precedence. `claim_precedence` lists are partial; unlisted authorities fall through to `fallback_authority_order`; unlisted there → ambiguity finding. |
| Boundary analysis ad hoc | When a finding's `affected_surface` touches a file under authority X in `on_change_to`, verify at least one reviewer examined files under each `review_authorities` authority for defects related to the boundary rule's stated `reason` (§1.6). Unexamined → coverage finding. |

### 3.3 Reference File Updates

| File | Change | Normative source |
|------|--------|-----------------|
| `preflight-taxonomy.md` | **References** the shared contract's derivation table (§1.3) — does not restate it as independent content. Documents how the review team applies it: redirect gate counting, specialist spawning rules. Retains degraded-mode heuristics (path patterns, signal scoring) as fallback. | Shared contract §1.3 is authoritative for claim-to-role mapping |
| `role-rubrics.md` | Update shared scaffold to include `claim_family` in finding format. Domain briefs unchanged — they are defect-class-based, not cluster-based. | — |
| `synthesis-guidance.md` | Add worked examples of `claim_precedence` application and boundary coverage analysis. Update contradiction resolution section to reference `spec.yaml` precedence rules. | Shared contract §1.5 is authoritative for precedence rules |
| `failure-patterns.md` | Add failure patterns for: malformed `spec.yaml`, unknown claims, semantic manifest validation failures. Update degraded mode description. | Shared contract §1.8 is authoritative for failure responses |
| `agent-teams-platform.md` | No changes — platform API unchanged. | — |

**Drift prevention:** Reference files that consume shared contract content must reference it by section number, not restate it. If the shared contract's derivation table (§1.3) or precedence rules (§1.5) change, reference files need only update their section pointers, not their content.

### 3.4 Backward Compatibility

Existing specs remain reviewable via degraded mode. Full contract benefits (deterministic specialist spawning, mechanical precedence resolution, boundary coverage analysis) require `spec.yaml`.

| Condition | Behavior |
|-----------|----------|
| `spec.yaml` present + frontmatter on files | Full contract mode — all new features active |
| `spec.yaml` absent + frontmatter on files | Degraded mode — current behavior preserved |
| `spec.yaml` present + no frontmatter on files | Degraded mode — `spec.yaml` provides authority definitions but files can't be mapped |
| Neither present | Degraded mode — path heuristics only |

---

## Section 4: PostToolUse Hook

A lightweight passive safety net. Not the primary trigger for the spec-writing skill — the primary trigger is explicit user invocation or the brainstorming skill's handoff.

### 4.1 Behavior

A `PostToolUse` hook on `Write` that checks if the written file is a markdown document in `docs/` or `specs/` directories exceeding 500 lines. If so, it injects a soft nudge into Claude's context suggesting the spec-writing skill.

### 4.2 Hook Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/spec-size-nudge.sh"
          }
        ]
      }
    ]
  }
}
```

### 4.3 Hook Script

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

# Only check markdown files in docs/ or specs/ directories
case "$FILE_PATH" in
  */docs/*|*/specs/*) ;;
  *) exit 0 ;;
esac

case "$FILE_PATH" in
  *.md) ;;
  *) exit 0 ;;
esac

LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')

if [ "$LINE_COUNT" -gt 500 ]; then
  cat <<EOF
{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "This file ($FILE_PATH) is $LINE_COUNT lines. Files over 500 lines are difficult to reference in future conversations. Consider invoking the spec-writer skill to create a modular spec structure."}}
EOF
fi

exit 0
```

### 4.4 Design Decisions

- **`additionalContext`, not `decision: "block"`:** The nudge is informational, not corrective. It doesn't block the write — the file is already written successfully. It suggests an action Claude may or may not take.
- **Only `docs/` and `specs/` directories:** Avoids false positives on generated files, changelogs, or other legitimately large markdown files.
- **Only `.md` files:** The skill operates on markdown specs, not code or data files.
- **500-line threshold:** Matches the brainstorming skill's observation that specs above this size benefit from modularization. Conservative enough to avoid noise.
- **No state tracking:** The hook fires every time a large file is written. Repeated nudges for the same file are acceptable — the user can ignore them.

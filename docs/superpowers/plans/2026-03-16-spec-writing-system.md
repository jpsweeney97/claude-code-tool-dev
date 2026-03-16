# Spec Writing System Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the spec-writing system: a shared contract reference, a new spec-writer skill, updates to the existing spec-review-team skill, and a PostToolUse nudge hook.

**Architecture:** Three components plus a hook form a spec lifecycle. The shared contract (`docs/references/shared-contract.md`) defines the `spec.yaml` schema, claims vocabulary, and conventions. The spec-writer skill (new) compiles approved design documents into modular specs with `spec.yaml`. The spec-review-team (updated) gains `spec.yaml`-aware routing, deterministic specialist spawning, and mechanical precedence resolution while preserving full backward compatibility as degraded mode. A PostToolUse hook on Write provides a passive size-based nudge toward modularization.

**Tech Stack:** Markdown instruction documents for Claude Code. Bash for the hook script.

**Spec:** `docs/superpowers/specs/spec-writing-system/` — 6 files: `README.md`, `foundations.md`, `shared-contract.md`, `spec-writer.md`, `review-team-updates.md`, `hook.md`

**Implementation branch:** `feature/spec-writing-system`

**Writing conventions:**
- Follow `docs/references/writing-principles.md` — all created/modified files are instruction documents for Claude
- Active prohibitions for things Claude should NOT do ("Do NOT fall back", not "omit fallback")
- Front-load critical information (commands before context)
- Concrete values, not vague language ("500 lines", not "large files")
- Match patterns observed in existing skills (`spec-review-team`, `spec-modulator`, `reviewing-designs`)

**Relationship to spec-modulator:** The spec-writer supersedes spec-modulator's `from-monolith` mode for specs that use `spec.yaml`. spec-modulator remains useful for simpler modularization without the full shared contract. No changes to spec-modulator in this plan.

---

## File Structure

```
docs/references/
  shared-contract.md                                    # CREATE: Shared contract reference

.claude/skills/spec-writer/
  SKILL.md                                              # CREATE: Spec-writer skill

.claude/skills/spec-review-team/
  SKILL.md                                              # MODIFY: Add spec.yaml consumption
  references/
    preflight-taxonomy.md                               # MODIFY: Add derived roles, dual-mode
    role-rubrics.md                                     # MODIFY: Add claim_family to schema
    synthesis-guidance.md                                # MODIFY: Add precedence + boundary examples
    failure-patterns.md                                  # MODIFY: Add spec.yaml failure patterns

.claude/hooks/
  spec-size-nudge.sh                                    # CREATE: PostToolUse nudge hook
```

| File | Responsibility | Target |
|------|---------------|--------|
| `docs/references/shared-contract.md` | `spec.yaml` schema, claims enum, derivation table, frontmatter rules, precedence, boundaries, failure model | 240-280 lines |
| `.claude/skills/spec-writer/SKILL.md` | 8-phase compilation workflow with inline contract essentials | 280-340 lines |
| `.claude/skills/spec-review-team/SKILL.md` | Dual-mode discovery, derived-role routing, deterministic spawning, `claim_family`, precedence synthesis | +60-80 lines delta |
| `references/preflight-taxonomy.md` | Derived role definitions, dual-mode operation, retain degraded heuristics | +50-60 lines delta |
| `references/role-rubrics.md` | `claim_family` in shared scaffold finding format | +3 lines delta |
| `references/synthesis-guidance.md` | Precedence resolution worked examples, boundary coverage analysis | +80-100 lines delta |
| `references/failure-patterns.md` | `spec.yaml`-specific failure patterns, expanded degraded mode | +40-50 lines delta |
| `.claude/hooks/spec-size-nudge.sh` | PostToolUse hook: file size check + nudge output | ~25 lines |

---

## Chunk 1: Shared Contract Reference

### Task 1: Create docs/references/shared-contract.md

**Files:**
- Create: `docs/references/shared-contract.md`

**Source:** Derive content from design spec at `docs/superpowers/specs/spec-writing-system/shared-contract.md`. This runtime reference materializes the spec's shared contract into a durable document both skills reference at execution time.

- [ ] **Step 1: Write shared-contract.md**

Create `docs/references/shared-contract.md` with the following content. All tables, schemas, and rules come from the design spec's `shared-contract.md` — preserve them exactly.

```markdown
# Shared Contract — Spec Writing System

Authoritative reference for the spec-writing system. Defines the `spec.yaml` schema, claims vocabulary, derivation table, and conventions used by both the spec-writer and spec-review-team skills.

**Consumers:** spec-writer skill (producer-side validation), spec-review-team skill (consumer-side routing and precedence). Changes to this document require updating both skills.

## spec.yaml

A dedicated YAML file alongside `README.md`. README is the human entry point; `spec.yaml` is the machine source of truth.

**Conflict rule:** `spec.yaml` is authoritative for tooling; README summarizes it; contradictions between them are defects.

**Schema:**

\```yaml
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
\```

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

\```yaml
---
module: <kebab-case-identifier>
status: active | draft | stub | deprecated
normative: true | false
authority: <authority-label from spec.yaml>
claims: [<claim>, ...]  # optional, additive, max 3 effective
---
\```

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

### Consumer Failures (degrade gracefully)

| Condition | Response |
|-----------|----------|
| `spec.yaml` missing | Degraded mode — fall back to frontmatter + path heuristics. Warn: "No spec.yaml. Consider running the spec-writer skill." |
| `spec.yaml` malformed (unparseable YAML) | Hard stop with parse error |
| File references unknown authority | Validation finding (P1). Process file as `authority: unknown`. |
| Unknown claim value in frontmatter | Validation finding (P1). Unknown claims ignored for role derivation. |
| `claim_precedence` references undefined authority | Validation finding (P1). Skip that entry during adjudication. |
| Unsupported `shared_contract_version` | Hard stop. Report expected vs actual. |
| `spec.yaml` present but no files have frontmatter | Degraded mode. Warn user. |

## Concrete Example

**CLI tool with no database:**

\```yaml
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
\```

**What the review team derives:**

- Normative files with effective claims produce roles: `foundation` (from architecture_rule, decision_record), `behavior` (from behavior_contract, interface_contract), `execution` (from implementation_plan, verification_strategy) → **3 gating roles**
- No `persistence_schema` or `enforcement_mechanism` claims on normative files → no optional specialists
- `supporting` authority has `default_claims: []` and is non-normative → derived role `reference`, excluded from gate
- Redirect gate: 3 distinct roles + 2 boundary rules → warrants full team review

**A typical file:**

\```yaml
---
module: command-behavior
status: active
normative: true
authority: command-contract
---
\```

Inherits `[behavior_contract, interface_contract]`. Derived roles: `behavior`. No `claims` field needed.
```

- [ ] **Step 2: Validate structure**

Run: Verify the file contains all 9 required sections:
```bash
grep -c '^## ' docs/references/shared-contract.md
```
Expected: 9 sections (spec.yaml, Claims Enum, Claim-to-Role Derivation Table, File Frontmatter, Precedence Resolution, Boundary Rules, Cross-Reference Conventions, Failure Model, Concrete Example)

Verify the claims enum has exactly 8 entries (look for rows with "Specialist trigger" column values):
```bash
grep -c '| — \|| schema-persistence \|| integration-enforcement' docs/references/shared-contract.md
```
Expected: 8 (one per claim)

Verify the derivation table has exactly 6 roles (look for rows with "redirect gate" column values):
```bash
grep -c '| Yes \|| No |' docs/references/shared-contract.md
```
Expected: 6 (foundation, behavior, execution, state, enforcement, reference)

Verify the concrete example's spec.yaml is parseable:
```bash
sed -n '/^# spec.yaml$/,/^\\```$/p' docs/references/shared-contract.md | python3 -c "import sys, yaml; yaml.safe_load(sys.stdin)" 2>&1 || echo "YAML parse error"
```

- [ ] **Step 3: Commit**

```bash
git add docs/references/shared-contract.md
git commit -m "docs: add shared contract reference for spec-writing system"
```

---

## Chunk 2: Spec-Writer Skill

### Task 2: Create .claude/skills/spec-writer/SKILL.md

**Files:**
- Create: `.claude/skills/spec-writer/SKILL.md`

**Source:** Derive from design spec `docs/superpowers/specs/spec-writing-system/spec-writer.md`. Follow the skill pattern established by `spec-review-team` and `spec-modulator` skills. The SKILL.md must be self-contained — include inline claims enum and spec.yaml schema so the skill operates without requiring external reads for core workflow steps.

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p .claude/skills/spec-writer
```

- [ ] **Step 2: Write SKILL.md**

Create `.claude/skills/spec-writer/SKILL.md` with the content below. Phase descriptions are derived from the design spec's `spec-writer.md`. The inline claims enum and spec.yaml schema come from `docs/references/shared-contract.md` — include them directly for standalone operation.

```markdown
---
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
---

# Spec Writer

Compile an approved design document into a modular spec with `spec.yaml` and properly-frontmatted files. This skill is a **compiler with one architectural checkpoint** — it does not re-explore the design space.

**Announce at start:** "I'm using the spec-writer skill to compile this design into a modular spec."

## When to Use

- An approved design document exists (output of brainstorming skill or equivalent)
- The document covers architecture, components, data flow, error handling, and/or testing
- The user explicitly invokes the skill or the PostToolUse hook nudges
- Trigger phrases: "write a spec", "formalize this design", "modularize this", "create spec files", "compile this into a spec"

## When NOT to Use

- Design space is still open (requirements unclear, approach contested) → redirect to **brainstorming**
- Design exists but needs rigor review → redirect to **reviewing-designs**
- Document is under ~300 lines with a single concern → recommend keeping as single file
- Do NOT re-explore design decisions — the design doc is already approved

## Workflow

\```
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
\```

One mandatory approval gate (Phase 3). One optional midpoint gate (Phase 6, for large docs). Phase 8 is a handoff, not an approval gate.

### Phase 1: ENTRY GATE

**Gate:** Confirmed input is an approved design artifact.

1. Confirm the input design doc path.
2. Verify it is the approved post-brainstorm artifact:
   - If design space is reopened (requirements unclear, approach contested) → redirect to **brainstorming**.
   - If design exists but needs rigor or completeness review → redirect to **reviewing-designs**.
3. If the document is under ~300 lines with a single concern and no distinct authority boundaries, recommend keeping it as a single file. Do NOT modularize for modularization's sake.

### Phase 2: ANALYSIS

**Gate:** Translation ledger built with every major source section mapped.

Read the entire design document once. Build a **translation ledger** — a mapping from source sections to candidate destination files:

| Source Section | Candidate File | Authority | Inherited Claims | Confidence | Rationale |
|---|---|---|---|---|---|
| §Architecture Overview | `foundations.md` | foundation | architecture_rule | high | Self-contained architectural content |
| §Command Semantics | `commands/behavior.md` | command-contract | behavior_contract, interface_contract | high | User-facing behavioral promises |
| §Testing Strategy + §Rollout | `delivery/testing.md` | delivery | implementation_plan, verification_strategy | medium | May need split if testing and rollout diverge |

**Granularity rule:** When a source section maps to multiple files or has medium/low confidence, the ledger must descend to subsection or topic-block granularity. Section-level mapping is insufficient for splits — Phase 7's source coverage and orphan checks depend on fine-grained traceability.

The ledger also proposes:
- Authority labels and their `default_claims` (from the Claims Enum below)
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
4. **Ambiguous splits** — sections where the destination is uncertain, with recommendation and reasoning
5. **Derived role summary** — what the review team will see (using the Claim-to-Role Derivation Table below)

The user approves, requests changes, or rejects. Do NOT proceed without explicit approval. If rejected, revise based on feedback and re-present.

**Optional midpoint gate:** For design docs over ~1500 lines or with >3 low-confidence splits, offer a midpoint checkpoint after the normative backbone (Phase 6, step 1) — "Here's the foundational content. Does this look right before I continue with dependent files?"

### Phase 4: MANIFEST

**Gate:** `spec.yaml` written and self-validated.

Write `spec.yaml` as the first durable artifact. After this point, `spec.yaml` is stable — any change to authorities, precedence, or boundary rules reopens the architecture checkpoint. Minor wording changes to descriptions are permitted without reconfirmation.

Self-validate the manifest:
- All claims in `default_claims` are from the Claims Enum (8 fixed values)
- All authorities referenced in `claim_precedence`, `fallback_authority_order`, and `boundary_rules` are defined in `authorities`
- At least one normative-compatible authority exists (an authority whose `default_claims` is non-empty)
- `shared_contract_version` is set

### Phase 5: SCAFFOLD

**Gate:** `README.md` written with reading order and valid frontmatter.

`README.md` is a spec file and must carry frontmatter:

\```yaml
---
module: readme
status: active
normative: false
authority: supporting  # or equivalent zero-claim authority
---
\```

Content includes:
- Spec title and overview
- Authority model summary (human-readable version of `spec.yaml`)
- Numbered reading-order table linking every planned file with a one-line description
- Cross-reference conventions used in this spec

README will be refreshed at the end of Phase 6 once exact files and summaries are final.

### Phase 6: AUTHOR

**Gate:** All planned files written.

Write files in **dependency order** — normative backbone first, then dependent content:

1. **Normative backbone:** `foundations.md`, `decisions.md`, and top-level behavioral/contract files
2. **Dependent clusters:** Remaining behavioral files → state/schema files → enforcement/control files → execution/implementation files → reference/supporting files

Within a cluster, write overview files before detail files.

**Transformation rule — semantic preservation:**

| Permitted | Forbidden |
|-----------|-----------|
| Split sections across files | Invent new decisions not in the design doc |
| Normalize inconsistent terminology | Silently resolve ambiguities the design doc left open |
| Tighten prose, remove hedging | Drop caveats or qualifications |
| Convert narrative to tables | Change behavioral meaning |
| Make implicit constraints explicit (see rule below) | Add requirements not present in the source |
| Adjust heading levels | Reorder content in ways that change semantic relationships |

**Implicit-to-explicit rule:** Make implicit constraints explicit only when directly entailed by approved source text. Never introduce new constants, precedence rules, failure modes, or normative language (MUST/SHOULD) not grounded in the design document. If an implication is ambiguous, preserve the ambiguity and flag it in the translation ledger.

**Frontmatter generation:** Every file gets frontmatter per the shared contract's File Frontmatter rules. Assign `module`, `status`, `normative`, and `authority` based on the approved translation ledger. `claims` is omitted when defaults suffice.

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
| Derivation check | Derived roles produce the expected structural complexity (self-check against Derivation Table below) |

Refresh `README.md` with final file summaries after all content files are written.

Producer failure rules apply: any validation failure from the Failure Model is a hard failure. Fix before proceeding to handoff.

### Phase 8: HANDOFF

Present the completed spec to the user.

1. **Summary:** file count, authority count, derived roles, boundary rules, any validation notes.
2. **Recommend `spec-review-team`:** "The spec is ready for review. Would you like me to run `spec-review-team`?"
3. Auto-invoke `spec-review-team` only if the user explicitly requested write-and-review in one flow. Otherwise, wait for user decision.

## Claims Enum

8 fixed values — the only vocabulary spec authors interact with.

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

## Claim-to-Role Derivation Table

| Derived role | Claims that produce it | Counts in redirect gate? |
|---|---|---|
| `foundation` | `architecture_rule`, `decision_record` | Yes |
| `behavior` | `behavior_contract`, `interface_contract` | Yes |
| `execution` | `implementation_plan`, `verification_strategy` | Yes |
| `state` | `persistence_schema` | Yes |
| `enforcement` | `enforcement_mechanism` | Yes |
| `reference` | zero effective claims | No |

A file's derived roles come from its effective claims. Each claim maps to exactly one role. Multi-role files increase structural complexity.

## spec.yaml Schema

\```yaml
shared_contract_version: 1
readme: README.md

authorities:
  <authority-label>:
    description: <what this authority covers>
    default_claims: [<claim>, ...]

precedence:
  normative_first: true
  claim_precedence:
    <claim>: [<authority>, ...]
  fallback_authority_order: [<authority>, ...]
  unresolved: ambiguity_finding

boundary_rules:
  - on_change_to: [<authority>]
    review_authorities: [<authority>, ...]
    reason: <why>
\```

## Failure Model

Producer failures are hard failures — fix before continuing:

| Condition | Response |
|-----------|----------|
| Authority referenced in file not defined in `spec.yaml` | Hard failure |
| Normative file has zero effective claims | Hard failure |
| Effective claims exceed 3 per file | Hard failure |
| Cross-references don't resolve | Hard failure |
| Unknown claim value in `default_claims` or file `claims` | Hard failure |
| `claim_precedence` key outside the fixed claim enum | Hard failure |
| Authority in `claim_precedence`, `fallback_authority_order`, or `boundary_rules` not defined in `authorities` | Hard failure |

## References

| File | Purpose |
|------|---------|
| `docs/references/shared-contract.md` | Full shared contract — authoritative for spec.yaml schema, claims, derivation, precedence, boundaries, failure model |
| `docs/references/writing-principles.md` | Writing principles for instruction documents |
```

- [ ] **Step 3: Validate SKILL.md**

Verify:
- Frontmatter has `name`, `description`, `allowed-tools` fields
- All 8 phases present with phase gates
- Claims enum has 8 entries matching shared contract
- Derivation table has 6 roles matching shared contract
- spec.yaml schema matches shared contract
- Failure model matches shared contract's producer failures
- No TODOs, placeholders, or stubs

```bash
grep -c '^### Phase' .claude/skills/spec-writer/SKILL.md
```
Expected: 8

```bash
grep -c '| `[a-z_]*` |' .claude/skills/spec-writer/SKILL.md | head -1
```
Expected: 8 claim entries + 6 derivation entries = check both tables present

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/spec-writer/SKILL.md
git commit -m "feat: add spec-writer skill for compiling design docs into modular specs"
```

---

## Chunk 3: Spec-Review-Team Updates

### Task 3: Update spec-review-team SKILL.md

**Files:**
- Modify: `.claude/skills/spec-review-team/SKILL.md`

**Source:** Apply delta changes from `docs/superpowers/specs/spec-writing-system/review-team-updates.md`. All changes are additive — existing behavior is preserved as "degraded mode" when `spec.yaml` is absent.

- [ ] **Step 1: Update "When to Use" section**

Replace `spec-modulator` reference with `spec-writer`:

Old:
```markdown
- Specs created by `spec-modulator` or following the same conventions
```

New:
```markdown
- Specs created by `spec-writer`, `spec-modulator`, or following the same conventions
```

- [ ] **Step 2: Update Phase 1 DISCOVERY**

Replace the entire Phase 1 section (from `### Phase 1: DISCOVERY` through `**Output:**` paragraph) with the expanded dual-mode version:

```markdown
### Phase 1: DISCOVERY

**Phase gate:** Authority map built with ≥1 normative file, or degraded mode entered.

1. **Locate spec directory.** Use the path the user provides. If no path given, search for markdown files with YAML frontmatter containing `module`, `status`, `normative`, or `authority` fields.

2. **Read manifest.** Check for `spec.yaml` in the spec directory. If present: parse authority registry, record `shared_contract_version`, extract authority labels with their `default_claims`, `precedence`, and `boundary_rules`. If absent: note degraded mode for Phase 2-5 and proceed.

3. **Read all markdown files.** Parse YAML frontmatter from each file. Extract: `module`, `status`, `normative`, `authority`, `claims`, `legacy_sections`.

4. **Build authority map.** For each file, record:
   - **File path:** absolute path to the file.
   - **Normative:** `true` if frontmatter `normative: true`; `false` otherwise.
   - **Authority label:** value of frontmatter `authority` field, preserved as-is. If absent: `unknown`.
   - **Effective claims** (full contract mode): authority's `default_claims` + file's `claims` (additive). See `docs/references/shared-contract.md` for claims rules.
   - **Derived roles** (full contract mode): mapped from effective claims via the derivation table in `docs/references/shared-contract.md`. A file with claims spanning multiple roles participates in all of them.
   - **Boundary-rule participation** (full contract mode): `source` if the file's authority appears in any `on_change_to` list; `target` if in any `review_authorities` list; `neither` otherwise.
   - **Review cluster** (degraded mode only): derived from source authority + `module` + path heuristics. See `references/preflight-taxonomy.md` for the 6 canonical clusters and classification rules.

5. **Degraded mode:** If `spec.yaml` is absent AND zero files have parseable frontmatter, classify all files by path heuristics, warn the user, and continue. If `spec.yaml` is present but no files have frontmatter: degraded mode with warning. See [Backward Compatibility](#backward-compatibility).

6. **Partial coverage** (some files with frontmatter, some without) is normal operation — do NOT enter degraded mode.

**Output:** Authority map listing every file with its normative flag, authority label, effective claims (if full contract mode), derived roles (if full contract mode), review cluster (if degraded mode), and boundary-rule participation. Count of normative files, distinct derived roles or clusters, and boundary edges.
```

- [ ] **Step 3: Update Phase 2 ROUTING**

Replace the redirect gate table and surrounding content (from `### Phase 2: ROUTING` through the "If not redirecting" paragraph):

```markdown
### Phase 2: ROUTING

**Phase gate:** Pass redirect gate, or redirect to `reviewing-designs`.

Evaluate all four redirect conditions. Redirect to `reviewing-designs` only if **all** conditions are met:

**Full contract mode** (spec.yaml present):

| Condition | Threshold | Required for redirect |
|-----------|-----------|----------------------|
| Distinct derived roles (excluding `reference`) from normative files | ≤ 2 | Yes |
| `boundary_edges` (from `spec.yaml` `boundary_rules`) | ≤ 2 | Yes |
| Specialist triggers (normative file has trigger claim) | None firing | Yes |
| Ambiguous authority assignments | Any present | **Disables redirect** |

**Degraded mode** (no spec.yaml):

| Condition | Threshold | Required for redirect |
|-----------|-----------|----------------------|
| `confident_review_cluster_count` | ≤ 2 | Yes |
| `boundary_edges` (inferred from cluster transitions) | ≤ 2 | Yes |
| Specialist triggers (heuristic scoring) | None firing | Yes |
| Ambiguous cluster assignments | Any present | **Disables redirect** |

**`boundary_edges` count rule (full contract mode):** Count unique directional `(on_change_to authority, review_authority)` pairs across all boundary rules. One rule with 3 `review_authorities` = 3 edges.

**Key insight:** A 3-file spec spanning 3 authority tiers needs full team review; a 10-file spec in one tier does not. File count is not a gate condition.

**If redirecting:** Tell the user which conditions triggered and why this spec fits `reviewing-designs`. Then invoke `reviewing-designs`. Do NOT continue to Phase 3.

**If not redirecting:** Continue to Phase 3 (PREFLIGHT).
```

- [ ] **Step 4: Update Phase 3A PREFLIGHT**

Replace Phase 3A content (from `#### Phase 3A: Mechanical` through step 4):

```markdown
#### Phase 3A: Mechanical

**Phase gate:** All files checked; frontmatter parseable on all files, or degraded mode entered.

1. Validate frontmatter on all spec files: required fields present (`module`, `status`, `normative`; `authority` required when `spec.yaml` exists), values well-formed (no nulls, no unrecognized status values).
2. **Semantic manifest validation** (full contract mode only): unknown claims in `default_claims` or file `claims`, undefined authority references in `claim_precedence`, `fallback_authority_order`, or `boundary_rules`, normative files with zero effective claims, effective claims >3 per file. Consumer failure rules from `docs/references/shared-contract.md` apply: unknown claims → validation finding (P1), undefined authority → validation finding (P1), malformed spec.yaml → hard stop.
3. Check cross-references: every relative markdown link resolves to an existing file and, if it includes an anchor (`#section`), that anchor exists in the target file.
4. Detect broken links, orphaned anchors, and missing referenced files.
5. Record all results for the preflight packet's `mechanical_checks` section.
```

- [ ] **Step 5: Update Phase 3B Staffing**

Replace the specialist evaluation rules in Phase 3B (steps 2-4):

```markdown
2. Evaluate optional specialist signals:
   - **Full contract mode:** Deterministic — spawn when any normative file has the specialist's trigger claim in its effective claims. `persistence_schema` triggers `schema-persistence`; `enforcement_mechanism` triggers `integration-enforcement`. No sampling needed.
   - **Degraded mode:** Heuristic — use the two-tiered spawn rule from `references/preflight-taxonomy.md`: Tier 1 (score ≥ 100) single high-confidence signal; Tier 2 (score 50–99) requires 2+ medium signals from different dimensions.
3. If in degraded mode and frontmatter metadata is insufficient to evaluate signals: sample targeted content excerpts per the sampling policy in `references/preflight-taxonomy.md`. Do NOT expand into broad corpus reading.
4. Budget exhausted and below spawn threshold (degraded mode only): do NOT spawn the specialist. Log the unresolved signal in the synthesis report.
```

- [ ] **Step 6: Update Phase 3C packet sections**

Replace the 6 sections list in Phase 3C step 2:

Old:
```markdown
2. Create `.review-workspace/preflight/packet.md` with exactly 6 sections: `authority_map`, `boundary_edges`, `signal_matrix`, `mechanical_checks`, `route_decision`, `spawn_plan`.
```

New:
```markdown
2. Create `.review-workspace/preflight/packet.md` with exactly 6 sections:
   - `authority_map`: file path, normative flag, authority label, effective claims (full contract) or review cluster (degraded), derived roles (full contract), boundary-rule participation (full contract)
   - `boundary_edges`: computed from `spec.yaml` `boundary_rules` (full contract) or cluster transitions (degraded)
   - `signal_matrix`: binary claim presence (full contract) or heuristic signal scores (degraded)
   - `mechanical_checks`: frontmatter validation + semantic manifest validation results (full contract)
   - `route_decision`: derived role count (full contract) or cluster count (degraded) + boundary_edges + specialist triggers
   - `spawn_plan`: deterministic from claims (full contract) or heuristic from signals (degraded)
```

- [ ] **Step 7: Add `claim_family` to Finding Schema**

In the Finding Schema section, add `claim_family` after `title`:

Old:
```markdown
- **priority:** P0 / P1 / P2
- **title:** One-sentence description
- **violated_invariant:** source_doc#anchor
```

New:
```markdown
- **priority:** P0 / P1 / P2
- **title:** One-sentence description
- **claim_family:** <claim from the 8 fixed values, or "ambiguous">
- **violated_invariant:** source_doc#anchor
```

Also add after the Finding ID prefixes table:

```markdown
**`claim_family` rule:** Each finding must identify which claim from the fixed enum it addresses. This enables mechanical application of `claim_precedence` during synthesis. If a reviewer cannot identify one claim family, set `claim_family: ambiguous` — the finding escalates to human resolution during synthesis.
```

- [ ] **Step 8: Update Phase 5 SYNTHESIS — Contradiction Resolution**

In the Judgment Obligations section, replace the "Resolve contradictions" paragraph:

Old:
```markdown
**Resolve contradictions.** Apply the authority map (normative > non-normative), then evidence quality, then domain reasoning. Unresolvable contradictions escalate as ambiguity findings (P1, `SY` prefix). Record `adjudication_rationale` in the ledger for every resolved contradiction.
```

New:
```markdown
**Resolve contradictions.**

- **Full contract mode:** Apply `spec.yaml` precedence rules mechanically: (1) `normative: true` beats `normative: false`, (2) `claim_precedence` for the finding's `claim_family` — first listed authority wins, (3) `fallback_authority_order` when no claim-specific rule matches, (4) emit ambiguity finding when still unclear. See `docs/references/shared-contract.md` for full precedence rules.
- **Degraded mode:** Apply the authority map (normative > non-normative), then evidence quality, then domain reasoning.
- Unresolvable contradictions escalate as ambiguity findings (P1, `SY` prefix). Record `adjudication_rationale` in the ledger for every resolved contradiction.

**Boundary coverage analysis** (full contract mode): When a finding's `affected_surface` touches a file under authority X that appears in `on_change_to`, verify at least one reviewer examined files under each `review_authorities` authority for defects related to the boundary rule's `reason`. Unexamined boundary authorities → coverage finding (P1, `SY` prefix).
```

- [ ] **Step 9: Add Backward Compatibility section**

Add a new section before `## References` at the end of SKILL.md:

```markdown
## Backward Compatibility

Existing specs remain reviewable via degraded mode. Full contract benefits (deterministic specialist spawning, mechanical precedence resolution, boundary coverage analysis) require `spec.yaml`.

| Condition | Behavior |
|-----------|----------|
| `spec.yaml` present + frontmatter on files | Full contract mode — all new features active |
| `spec.yaml` absent + frontmatter on files | Degraded mode — current behavior preserved |
| `spec.yaml` present + no frontmatter on files | Degraded mode — `spec.yaml` provides authority definitions but files can't be mapped |
| Neither present | Degraded mode — path heuristics only |
```

- [ ] **Step 10: Update References table**

Add shared contract reference to the References table:

```markdown
| `docs/references/shared-contract.md` | Shared contract — spec.yaml schema, claims enum, derivation table, precedence rules, failure model |
```

- [ ] **Step 11: Validate SKILL.md changes**

Verify:
- Phase 1 mentions `spec.yaml` parsing
- Phase 2 has separate tables for full contract and degraded mode
- Phase 3A includes semantic manifest validation
- Phase 3B has deterministic specialist spawning for full contract mode
- Finding schema includes `claim_family` field
- Phase 5 references precedence rules and boundary coverage
- Backward Compatibility section present
- All cross-references to `docs/references/shared-contract.md` are correct

```bash
grep -c 'spec.yaml' .claude/skills/spec-review-team/SKILL.md
```
Expected: Multiple occurrences (at least 10+)

```bash
grep 'claim_family' .claude/skills/spec-review-team/SKILL.md
```
Expected: Present in Finding Schema section

- [ ] **Step 12: Commit**

```bash
git add .claude/skills/spec-review-team/SKILL.md
git commit -m "feat(spec-review-team): add spec.yaml consumption with full/degraded dual-mode"
```

### Task 4: Update Reference Files

**Files:**
- Modify: `.claude/skills/spec-review-team/references/preflight-taxonomy.md`
- Modify: `.claude/skills/spec-review-team/references/role-rubrics.md`
- Modify: `.claude/skills/spec-review-team/references/synthesis-guidance.md`
- Modify: `.claude/skills/spec-review-team/references/failure-patterns.md`

**Source:** Delta changes from `docs/superpowers/specs/spec-writing-system/review-team-updates.md`, Reference File Updates section.

- [ ] **Step 1: Update preflight-taxonomy.md**

Add a new section after `## 6 Canonical Review Clusters` header block, before `## Two-Layer Cluster Model`:

```markdown
## Derived Roles (Full Contract Mode)

When `spec.yaml` is present, cluster-based routing is replaced by derived role routing. The derivation table is defined in the shared contract (`docs/references/shared-contract.md#claim-to-role-derivation-table`) — this section documents how the review team applies it.

**Redirect gate:** Count distinct derived roles (excluding `reference`) present across normative files. This replaces `confident_review_cluster_count` in full contract mode.

**Specialist spawning:** Deterministic when `spec.yaml` exists — spawn when any normative file has the specialist's trigger claim in its effective claims:
- `persistence_schema` claim → spawn `schema-persistence` specialist
- `enforcement_mechanism` claim → spawn `integration-enforcement` specialist

No sampling needed in full contract mode. The two-tiered heuristic scoring below is retained for degraded mode only.

**Claim divergence flagging:** Files whose effective claims produce a different derived role set than their authority's `default_claims` would produce are flagged as high-attention review surfaces in the preflight packet.
```

Update the opening line of `## Two-Layer Cluster Model`:

Old:
```markdown
## Two-Layer Cluster Model

Every spec file carries two cluster-related concepts that are related but distinct:
```

New:
```markdown
## Two-Layer Cluster Model (Degraded Mode)

In degraded mode (no `spec.yaml`), every spec file carries two cluster-related concepts that are related but distinct. In full contract mode, this model is replaced by derived roles from claims — see above.
```

Update the opening of `## Signal Dimensions`:

Old:
```markdown
## Signal Dimensions

Five signal dimensions inform optional specialist spawning decisions. Dimensions differ in cost and inspection depth.
```

New:
```markdown
## Signal Dimensions (Degraded Mode)

In full contract mode, specialist spawning is deterministic from claims — this section applies only to degraded mode. Five signal dimensions inform optional specialist spawning decisions in the absence of `spec.yaml`.
```

Similarly update `## Scoring Weights and Spawn Thresholds` opening:

Old:
```markdown
## Scoring Weights and Spawn Thresholds
```

New:
```markdown
## Scoring Weights and Spawn Thresholds (Degraded Mode)
```

And `## Sampling Policy` opening:

Old:
```markdown
## Sampling Policy
```

New:
```markdown
## Sampling Policy (Degraded Mode)
```

- [ ] **Step 2: Update role-rubrics.md**

In the Shared Scaffold section, add `claim_family` to the finding format template. After `- **title:** One-sentence description`, add:

```markdown
> - **claim_family:** <claim from the 8 fixed values, or "ambiguous">
```

The full updated finding format in the scaffold becomes:

```
> ### [PREFIX-N] Title
>
> - **priority:** P0 / P1 / P2
> - **title:** One-sentence description
> - **claim_family:** <claim from the 8 fixed values, or "ambiguous">
> - **violated_invariant:** source_doc#anchor
> - **affected_surface:** file + section/lines
> - **impact:** 1-2 sentences
> - **evidence:** what doc says vs what it should say
> - **recommended_fix:** specific action
> - **confidence:** high / medium / low
> - **provenance:** independent / followup
> - **prompted_by:** {reviewer-name} (required when followup; omit when independent)
```

- [ ] **Step 3: Update synthesis-guidance.md**

Add two new sections after `## Section 4: Anti-Patterns`. The existing Section 5 ("Exemplar Ledger Entry") becomes Section 7, and "Audit Metric Notes" becomes Section 8. Renumber both before inserting:

```markdown
---

## Section 5: Precedence Resolution (Full Contract Mode)

When `spec.yaml` provides precedence rules, contradiction resolution follows a mechanical procedure instead of domain reasoning.

### Worked example: `claim_precedence` application

**Conflicting findings on the same surface:**

\```
AA-2 (authority-architecture):
- claim_family: behavior_contract
- priority: P1
- affected_surface: config/validation.md §"Input Rules"
- evidence: "Config contract declares input validation rules that conflict
  with command contract's declared input handling."

CE-5 (contracts-enforcement):
- claim_family: behavior_contract
- priority: P1
- affected_surface: config/validation.md §"Input Rules"
- evidence: "Command contract's input handling contradicts config contract's
  validation rules at the same surface."
\```

**Resolution steps:**

1. Both files are `normative: true` → normative_first does not resolve (tie).
2. Finding's `claim_family: behavior_contract` → check `claim_precedence.behavior_contract`.
3. `claim_precedence` lists: `[command-contract, config-contract, foundation, delivery, decisions]`.
4. AA-2 cites the config contract's perspective; CE-5 cites the command contract's perspective. The command contract is listed first → command contract's position wins.
5. Record `adjudication_rationale`: "Per claim_precedence for behavior_contract, command-contract takes precedence over config-contract."

**Ledger record:**

\```markdown
### [SY-4] Config input validation conflicts with command input handling

- **source_findings:** AA-2, CE-5
- **support_type:** independent_convergence
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "Same surface (config/validation.md §Input Rules), same
  claim_family (behavior_contract), same root cause — conflicting validation rules."
- **adjudication_rationale:** "Per claim_precedence for behavior_contract,
  command-contract (position 1) takes precedence over config-contract (position 2).
  Config's validation rules should align with command's input handling."
\```

### Worked example: fallback_authority_order

When a finding's `claim_family` has no `claim_precedence` entry, or the conflicting authorities are not listed in the applicable entry:

\```
VR-3 (verification-regression):
- claim_family: verification_strategy
- affected_surface: delivery/testing.md §"Coverage Goals"
- evidence: "Delivery testing plan claims 90% coverage, but the foundation's
  architectural constraints make 90% infeasible for the async subsystem."
\```

1. Check `claim_precedence.verification_strategy` → lists `[delivery, command-contract, config-contract, decisions]`.
2. Foundation is NOT in the list → fall through to `fallback_authority_order`.
3. `fallback_authority_order: [foundation, command-contract, ...]` → foundation is position 1, delivery is position 5.
4. Foundation wins. The architectural constraint overrides the delivery plan's coverage target.

### Worked example: ambiguity finding

When an authority appears in neither `claim_precedence` nor `fallback_authority_order`:

1. Neither resolution path produces a winner.
2. Emit ambiguity finding: prefix `SY`, priority P1.
3. `adjudication_rationale`: "Authority X not listed in claim_precedence for [claim] or fallback_authority_order. Escalating as ambiguity — human resolution required."

---

## Section 6: Boundary Coverage Analysis (Full Contract Mode)

When `spec.yaml` defines `boundary_rules`, synthesis verifies that coupled authorities received adequate cross-reviewer attention.

### Procedure

For each boundary rule:
1. Identify all findings whose `affected_surface` touches a file under any authority in `on_change_to`.
2. For each such finding, check whether at least one reviewer also examined files under each `review_authorities` authority for defects related to the boundary rule's `reason`.
3. Evidence sources: findings files (direct examination), coverage notes (explicit scope declarations), DM summaries (collaboration indicators).

### What counts as "examined"

- A finding whose `affected_surface` is under the review authority → examined.
- A coverage note listing the review authority's files in `scope_checked` → examined.
- A DM summary showing a reviewer discussed the boundary topic with another reviewer who examined it → examined (indirect).

### Unexamined boundary

When a `review_authorities` authority has no examination evidence:

\```markdown
### [SY-N] Boundary coverage gap: [authority] not examined for [reason]

- **source_findings:** (none — this is a meta-finding)
- **support_type:** singleton
- **contributors:** synthesis-lead
- **priority:** P1
- **adjudication_rationale:** "Boundary rule requires examining [review_authority]
  when [on_change_to authority] is affected. No reviewer examined [review_authority]
  files for defects related to: [boundary rule reason]."
\```
```

- [ ] **Step 4: Update failure-patterns.md**

Add a new section after `## Degraded Mode`:

```markdown
## spec.yaml Failures

These failure patterns apply only in full contract mode (when `spec.yaml` is present). In degraded mode, the existing failure patterns below apply.

### "spec.yaml is malformed"

1. Attempt YAML parse. If parse fails: hard stop. Report the parse error with line number if available.
2. Do NOT attempt partial parsing or fallback to degraded mode — a malformed manifest is worse than no manifest.
3. Report: "spec.yaml parse error at [location]. Fix the YAML syntax and re-run."

### "Unknown claim value in file frontmatter or spec.yaml defaults"

1. Log validation finding (P1): "[file/authority] references unknown claim '[value]'. Known claims: architecture_rule, decision_record, behavior_contract, interface_contract, persistence_schema, enforcement_mechanism, implementation_plan, verification_strategy."
2. Ignore the unknown claim for role derivation. The file's remaining valid claims still determine its derived roles.
3. Continue — do NOT hard stop.

### "Authority in precedence/boundary rules not defined in spec.yaml"

1. Log validation finding (P1): "spec.yaml [section] references undefined authority '[name]'."
2. Skip that entry during adjudication. The remaining valid entries in `claim_precedence` or `fallback_authority_order` still apply.
3. Continue — do NOT hard stop.

### "Unsupported shared_contract_version"

1. Hard stop. Report: "spec.yaml shared_contract_version is [N], expected 1. This version of the spec-review-team skill supports version 1 only."
2. Do NOT attempt to process — schema differences between versions may produce silent errors.

### "Normative file has zero effective claims"

1. Log validation finding (P1): "[file] is normative but has zero effective claims (authority's default_claims is empty and no file-level claims declared)."
2. The file drops out of the redirect gate (no derived role) and has no usable precedence chain.
3. Process the file as `authority: unknown` for routing purposes.
```

Update the existing `## Degraded Mode` section:

1. Replace the existing spec-modulator reference in the user communication text:

Old:
```markdown
**User communication:** "No frontmatter detected on any spec file. Proceeding in degraded mode: all files classified by path heuristics, authority-based features disabled. Consider running spec-modulator to add frontmatter."
```

New:
```markdown
**User communication:** "No frontmatter detected on any spec file. Proceeding in degraded mode: all files classified by path heuristics, authority-based features disabled. Consider running the spec-writer skill to add frontmatter."
```

2. Add after the existing degraded mode content:

```markdown
**Full contract mode equivalent:** When `spec.yaml` is present but no files have frontmatter, the system enters degraded mode with an additional warning: "spec.yaml provides authority definitions but no files have frontmatter to map. Consider running the spec-writer skill to add frontmatter."
```

- [ ] **Step 5: Validate all reference file changes**

Verify each updated file:

```bash
# preflight-taxonomy.md: has "Derived Roles" section and "(Degraded Mode)" annotations
grep 'Derived Roles' .claude/skills/spec-review-team/references/preflight-taxonomy.md
grep 'Degraded Mode' .claude/skills/spec-review-team/references/preflight-taxonomy.md

# role-rubrics.md: has claim_family in scaffold
grep 'claim_family' .claude/skills/spec-review-team/references/role-rubrics.md

# synthesis-guidance.md: has precedence and boundary sections
grep 'Precedence Resolution' .claude/skills/spec-review-team/references/synthesis-guidance.md
grep 'Boundary Coverage' .claude/skills/spec-review-team/references/synthesis-guidance.md

# failure-patterns.md: has spec.yaml section
grep 'spec.yaml Failures' .claude/skills/spec-review-team/references/failure-patterns.md
```
Expected: All greps return matches.

Verify cross-references to shared contract:
```bash
grep 'shared-contract.md' .claude/skills/spec-review-team/references/preflight-taxonomy.md
```
Expected: At least one reference to the shared contract derivation table.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/spec-review-team/references/preflight-taxonomy.md \
        .claude/skills/spec-review-team/references/role-rubrics.md \
        .claude/skills/spec-review-team/references/synthesis-guidance.md \
        .claude/skills/spec-review-team/references/failure-patterns.md
git commit -m "feat(spec-review-team): update reference files for spec.yaml consumption"
```

---

## Chunk 4: PostToolUse Hook

### Task 5: Create Hook and Sync Settings

**Files:**
- Create: `.claude/hooks/spec-size-nudge.sh`
- Modify: `~/.claude/settings.json` (via promote + sync-settings)

**Source:** Hook script from `docs/superpowers/specs/spec-writing-system/hook.md`.

**How hooks deploy:** `sync-settings` reads from `~/.claude/hooks/` (production) and writes to `~/.claude/settings.json` (production). Hooks in `.claude/hooks/` (project dev) must be promoted via `uv run scripts/promote` before `sync-settings` can discover them.

- [ ] **Step 1: Write hook script**

Create `.claude/hooks/spec-size-nudge.sh` with hook frontmatter (required by `sync-settings`) followed by the script body from the spec:

```bash
#!/bin/bash
# /// hook
# event: PostToolUse
# matcher: Write
# ///
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

- [ ] **Step 2: Make executable**

```bash
chmod +x .claude/hooks/spec-size-nudge.sh
```

- [ ] **Step 3: Validate hook output format locally**

Test the hook directly (before promotion) with a mock input using a temp file for the content:
```bash
python3 -c "
import json, sys
content = 'line\\n' * 600
payload = json.dumps({'tool_input': {'file_path': '/tmp/docs/test.md', 'content': content}})
sys.stdout.write(payload)
" | .claude/hooks/spec-size-nudge.sh
```
Expected: JSON output with `hookSpecificOutput.additionalContext` mentioning the spec-writer skill.

Test with a non-matching file:
```bash
echo '{"tool_input": {"file_path": "/tmp/src/test.py", "content": "x"}}' | .claude/hooks/spec-size-nudge.sh
```
Expected: No output (exits silently).

Test with a short file:
```bash
echo '{"tool_input": {"file_path": "/tmp/docs/short.md", "content": "just a few lines"}}' | .claude/hooks/spec-size-nudge.sh
```
Expected: No output (under 500 lines).

- [ ] **Step 4: Promote and sync**

```bash
uv run scripts/promote hook spec-size-nudge
uv run scripts/sync-settings
```

Verify the hook is registered:
```bash
grep -A5 'spec-size-nudge' ~/.claude/settings.json
```
Expected: Entry under `hooks.PostToolUse` with matcher `Write` and command pointing to `~/.claude/hooks/spec-size-nudge.sh`.

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/spec-size-nudge.sh
git commit -m "feat: add PostToolUse hook for spec-size nudge"
```


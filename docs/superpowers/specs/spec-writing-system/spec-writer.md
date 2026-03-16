---
module: spec-writer
status: active
normative: true
authority: spec-writer
---

# Spec-Writing Skill

## Purpose

Compile an approved design document into a modular spec with `spec.yaml` and properly-frontmatted files. This skill is a **compiler with one architectural checkpoint** — it does not re-explore the design space. The design doc is already approved; this skill transforms it into a structured, review-ready artifact.

## Entry Conditions

- An approved design document exists (output of brainstorming skill or equivalent)
- The document covers architecture, components, data flow, error handling, and/or testing
- The user has explicitly invoked the skill or been nudged by the PostToolUse hook

## Workflow

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
5. **Derived role summary** — what the review team will see (using the shared derivation table from [shared-contract.md](shared-contract.md#claim-to-role-derivation-table))

The user approves, requests changes, or rejects. Do not proceed without explicit approval. If rejected, revise based on feedback and re-present.

**Optional midpoint gate:** For design docs over ~1500 lines or with >3 low-confidence splits, offer a midpoint checkpoint after the normative backbone (Phase 6, step 1) — "Here's the foundational content. Does this look right before I continue with dependent files?"

### Phase 4: MANIFEST

**Gate:** `spec.yaml` written and self-validated.

Write `spec.yaml` as the first durable artifact. After this point, `spec.yaml` is stable — any change to authorities, precedence, or boundary rules reopens the architecture checkpoint. Minor wording changes to descriptions are permitted without reconfirmation.

Self-validate the manifest against the shared contract:
- All claims in `default_claims` are from the fixed enum ([Claims Enum](shared-contract.md#claims-enum))
- All authorities referenced in `claim_precedence`, `fallback_authority_order`, and `boundary_rules` are defined in `authorities`
- At least one normative-compatible authority exists (an authority whose `default_claims` is non-empty, meaning it can back `normative: true` files without violating the normative claim rule from [File Frontmatter](shared-contract.md#file-frontmatter))
- `shared_contract_version` is set

### Phase 5: SCAFFOLD

**Gate:** `README.md` written with reading order and valid frontmatter.

`README.md` is a spec file and must carry frontmatter per the shared contract ([File Frontmatter](shared-contract.md#file-frontmatter)):

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

**Frontmatter generation:** Every file gets frontmatter per the shared contract ([File Frontmatter](shared-contract.md#file-frontmatter)). The skill assigns `module`, `status`, `normative`, and `authority` based on the approved translation ledger. `claims` is omitted when defaults suffice.

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
| Derivation check | Derived roles produce the expected structural complexity (self-check against shared derivation table from [shared-contract.md](shared-contract.md#claim-to-role-derivation-table)) |

Refresh `README.md` with final file summaries after all content files are written.

Producer failure rules apply ([Failure Model](shared-contract.md#failure-model)): any validation failure is a hard failure. Fix before proceeding to handoff.

### Phase 8: HANDOFF

Present the completed spec to the user.

1. **Summary:** file count, authority count, derived roles, boundary rules, any validation notes.
2. **Recommend `spec-review-team`:** "The spec is ready for review. Would you like me to run `spec-review-team`?"
3. Auto-invoke `spec-review-team` only if the user explicitly requested write-and-review in one flow. Otherwise, wait for user decision.

## Skill Metadata

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

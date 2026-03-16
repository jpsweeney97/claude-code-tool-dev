# Modularization Plan: Spec Writing System Design

**Source:** `docs/superpowers/specs/2026-03-15-spec-writing-system-design.md` (649 lines)
**Target:** `docs/superpowers/specs/spec-writing-system/` (5 content files + README)
**Date:** 2026-03-16

---

## Approved Mapping Ledger

| Source Unit | Heading to Match | Destination File | Operation | Confidence |
|---|---|---|---|---|
| Problem + Solution + key decision | `## Problem` through end of key decision paragraph (before first `---`) | `foundations.md` | move | high |
| S1: Shared Contract (§1.1–§1.9) | `## Section 1: Shared Contract` | `shared-contract.md` | move | high |
| S2: Spec-Writing Skill (§2.1–§2.4) | `## Section 2: Spec-Writing Skill` | `spec-writer.md` | move | high |
| S3: Spec-Review-Team Updates (§3.1–§3.4) | `## Section 3: Spec-Review-Team Updates` | `review-team-updates.md` | move | high |
| S4: PostToolUse Hook (§4.1–§4.4) | `## Section 4: PostToolUse Hook` | `hook.md` | move | high |

All operations are clean `move`. No splits or merges.

---

## Task Breakdown

### Stage 0: Scaffold

#### Task 0: Create directory and README

**Files:** Create `spec-writing-system/README.md`

- [ ] **Step 1:** Create directory `docs/superpowers/specs/spec-writing-system/`
- [ ] **Step 2:** Write `README.md` with frontmatter and reading order:

```yaml
---
module: readme
status: active
normative: false
authority: supporting
---
```

Reading order table:

| # | File | Covers |
|---|------|--------|
| 1 | `foundations.md` | Problem, solution architecture, key architectural decision |
| 2 | `shared-contract.md` | `spec.yaml` schema, claims enum, derivation table, frontmatter rules, precedence, boundary rules, cross-ref conventions, failure model, worked example |
| 3 | `spec-writer.md` | New skill: purpose, entry conditions, 8-phase workflow, metadata |
| 4 | `review-team-updates.md` | Delta changes to existing spec-review-team skill |
| 5 | `hook.md` | PostToolUse nudge: behavior, configuration, script, design decisions |

Authority model summary linking to `shared-contract.md` for full details.

- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): scaffold directory and README"`

**Gate:** Directory exists, README has valid frontmatter and reading order table.

---

### Stage 1: Content Migration (all independent — parallelizable)

#### Task 1: Migrate foundations.md

**Files:** Create `foundations.md`
**Source:** `## Problem` through end of key decision paragraph (line 30), delimited by `---`

- [ ] **Step 1:** Write `foundations.md`
  - Extract from `## Problem` through the key decision paragraph (before first `---` separator)
  - Add frontmatter:
    ```yaml
    ---
    module: foundations
    status: active
    normative: true
    authority: root
    ---
    ```
  - Promote title metadata (Date, Status, Purpose) into frontmatter or a header block
  - Strip the top-level `# Spec Writing System Design` heading — the README serves as the entry point
  - Content paragraphs copied verbatim — no prose changes
  - No cross-reference updates in this task

- [ ] **Step 2:** Verify content preserved
  - "Three components form a spec lifecycle" present
  - ASCII diagram present
  - "Claims are the only fixed vocabulary" key decision present
  - No content from `## Section 1` leaked in

- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): migrate foundations from source S0"`

#### Task 2: Migrate shared-contract.md

**Files:** Create `shared-contract.md`
**Source:** `## Section 1: Shared Contract` through end of §1.9 (delimited by next `---` separator)

- [ ] **Step 1:** Write `shared-contract.md`
  - Extract from `## Section 1: Shared Contract` through end of §1.9 concrete example
  - Add frontmatter:
    ```yaml
    ---
    module: shared-contract
    status: active
    normative: true
    authority: shared-contract
    ---
    ```
  - Strip "Section 1:" prefix from heading: `## Shared Contract`
  - Strip "1.x" prefixes from subsection headings (e.g., `### 1.1 spec.yaml` → `### spec.yaml`)
  - Add semantic anchors for cross-reference targets (see Cross-Reference Disambiguation Table below)
  - Internal `§1.x` references within this file become `#anchor` fragment links
  - Content paragraphs copied verbatim

- [ ] **Step 2:** Verify content preserved
  - All 9 subsections present (spec.yaml through Concrete Example)
  - Claims enum table has 8 rows
  - Derivation table has 6 rows
  - Failure model has both producer and consumer tables
  - No content from `## Section 2` leaked in

- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): migrate shared contract from source S1"`

#### Task 3: Migrate spec-writer.md

**Files:** Create `spec-writer.md`
**Source:** `## Section 2: Spec-Writing Skill` through end of §2.4 (delimited by next `---` separator)

- [ ] **Step 1:** Write `spec-writer.md`
  - Extract from `## Section 2: Spec-Writing Skill` through end of §2.4
  - Add frontmatter:
    ```yaml
    ---
    module: spec-writer
    status: active
    normative: true
    authority: spec-writer
    ---
    ```
  - Strip "Section 2:" prefix: `## Spec-Writing Skill`
  - Strip "2.x" prefixes from subsection headings
  - Do NOT update `§1.x` cross-references in this task — handled in Stage 3
  - Content paragraphs copied verbatim

- [ ] **Step 2:** Verify content preserved
  - All 4 subsections present (Purpose, Entry Conditions, Workflow, Skill Metadata)
  - 8 workflow phases present (ENTRY GATE through HANDOFF)
  - Workflow ASCII diagram present
  - Transformation rule table present (Permitted vs Forbidden)
  - Phase 7 validation table has 8 checks
  - No content from `## Section 3` leaked in

- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): migrate spec-writer skill from source S2"`

#### Task 4: Migrate review-team-updates.md

**Files:** Create `review-team-updates.md`
**Source:** `## Section 3: Spec-Review-Team Updates` through end of §3.4 (delimited by next `---` separator)

- [ ] **Step 1:** Write `review-team-updates.md`
  - Extract from `## Section 3: Spec-Review-Team Updates` through end of §3.4
  - Add frontmatter:
    ```yaml
    ---
    module: review-team-updates
    status: active
    normative: true
    authority: review-team
    ---
    ```
  - Strip "Section 3:" prefix: `## Spec-Review-Team Updates`
  - Strip "3.x" prefixes from subsection headings
  - Do NOT update `§1.x` cross-references — handled in Stage 3
  - Content paragraphs copied verbatim

- [ ] **Step 2:** Verify content preserved
  - "What Stays the Same" section lists all 6 retained elements
  - "What Changes" covers DISCOVERY, ROUTING, PREFLIGHT, Finding Schema, SYNTHESIS
  - Before/After tables present for each changed phase
  - Reference File Updates table has 5 rows
  - Backward Compatibility matrix has 4 rows
  - No content from `## Section 4` leaked in

- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): migrate review-team updates from source S3"`

#### Task 5: Migrate hook.md

**Files:** Create `hook.md`
**Source:** `## Section 4: PostToolUse Hook` through end of document

- [ ] **Step 1:** Write `hook.md`
  - Extract from `## Section 4: PostToolUse Hook` through end of file
  - Add frontmatter:
    ```yaml
    ---
    module: hook
    status: active
    normative: true
    authority: hook
    ---
    ```
  - Strip "Section 4:" prefix: `## PostToolUse Hook`
  - Strip "4.x" prefixes from subsection headings
  - Content paragraphs copied verbatim
  - No cross-references to update (this section has none)

- [ ] **Step 2:** Verify content preserved
  - All 4 subsections present (Behavior, Hook Configuration, Hook Script, Design Decisions)
  - JSON config block present
  - Bash script present and complete
  - 5 design decision bullets present

- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): migrate hook from source S4"`

---

### Stage 2: (skipped — no split operations)

---

### Stage 3: Cross-Reference Update

#### Task 6: Rewrite cross-references

**Files:** Modify `shared-contract.md`, `spec-writer.md`, `review-team-updates.md`

- [ ] **Step 1:** Add semantic anchors to `shared-contract.md`
  - Ensure each subsection heading has a stable kebab-case anchor (see disambiguation table below)

- [ ] **Step 2:** Rewrite `§` references in `spec-writer.md`
  - Apply cross-reference disambiguation table (below)
  - Every `§1.x` reference becomes a relative link to `shared-contract.md#anchor`

- [ ] **Step 3:** Rewrite `§` references in `review-team-updates.md`
  - Apply cross-reference disambiguation table (below)
  - Every `§1.x` reference becomes a relative link to `shared-contract.md#anchor`

- [ ] **Step 4:** Rewrite internal `§` references within `shared-contract.md`
  - `§1.x` references within shared-contract become `#anchor` fragment links
  - Remove "Section 1:" or "§1." prefixes from prose where they appear as identifiers

- [ ] **Step 5:** Verify zero stale `§` references remain
  - `grep -r '§[0-9]' docs/superpowers/specs/spec-writing-system/` returns zero matches

- [ ] **Step 6:** Commit
  `git commit -m "docs(spec-writing-system): rewrite cross-references to semantic links"`

---

### Stage 4: Validate and Finalize

#### Task 7: Content preservation validation (BEFORE source removal)

- [ ] **Step 1: Source coverage** — every major source section from the mapping ledger appears in exactly one destination file:

  | Source Section | Sentinel Term | Expected In |
  |---|---|---|
  | Problem | "monoliths are difficult to reference" | `foundations.md` |
  | Solution | "Three components form a spec lifecycle" | `foundations.md` |
  | §1.1 spec.yaml | `shared_contract_version` | `shared-contract.md` |
  | §1.2 Claims Enum | `architecture_rule` + `persistence_schema` | `shared-contract.md` |
  | §1.3 Derivation | `redirect gate` + `derived role` | `shared-contract.md` |
  | §1.4 Frontmatter | `normative claim rule` | `shared-contract.md` |
  | §1.5 Precedence | `claim_precedence` + `fallback_authority_order` | `shared-contract.md` |
  | §1.6 Boundary Rules | `on_change_to` + `review_authorities` | `shared-contract.md` |
  | §1.7 Cross-Ref | "semantic kebab-case anchors" | `shared-contract.md` |
  | §1.8 Failure Model | "Producer failures" + "Consumer failures" | `shared-contract.md` |
  | §1.9 Example | "CLI tool with no database" | `shared-contract.md` |
  | §2.1 Purpose | "compiler with one architectural checkpoint" | `spec-writer.md` |
  | §2.2 Entry | "approved design document exists" | `spec-writer.md` |
  | §2.3 Workflow | "Phase 1: ENTRY GATE" | `spec-writer.md` |
  | §2.4 Metadata | `allowed-tools` | `spec-writer.md` |
  | §3.1 What Stays | "6-phase structure" | `review-team-updates.md` |
  | §3.2 What Changes | "DISCOVERY (Phase 1)" | `review-team-updates.md` |
  | §3.3 Reference Files | `preflight-taxonomy.md` | `review-team-updates.md` |
  | §3.4 Backward Compat | "Degraded mode" | `review-team-updates.md` |
  | §4.1 Behavior | "PostToolUse hook on Write" | `hook.md` |
  | §4.2 Config | `"matcher": "Write"` | `hook.md` |
  | §4.3 Script | `#!/bin/bash` | `hook.md` |
  | §4.4 Decisions | `additionalContext` | `hook.md` |

  Validation command:
  ```bash
  for term in "monoliths are difficult" "Three components" "shared_contract_version" \
    "architecture_rule" "redirect gate" "normative claim rule" "claim_precedence" \
    "on_change_to" "semantic kebab-case" "Producer failures" "CLI tool with no database" \
    "compiler with one architectural checkpoint" "approved design document exists" \
    "Phase 1: ENTRY GATE" "allowed-tools" "6-phase structure" "DISCOVERY" \
    "preflight-taxonomy.md" "Degraded mode" "PostToolUse hook on Write" \
    '"matcher": "Write"' '#!/bin/bash' "additionalContext"; do
    count=$(grep -rl "$term" docs/superpowers/specs/spec-writing-system/*.md 2>/dev/null | wc -l)
    [ "$count" -eq 0 ] && echo "MISSING: $term"
    [ "$count" -gt 1 ] && echo "DUPLICATE: $term (in $count files)"
  done
  ```

- [ ] **Step 2: Boundary contamination** — spot-check that content didn't leak across boundaries:
  - `foundations.md` does NOT contain "spec.yaml" schema (that's shared-contract)
  - `shared-contract.md` does NOT contain "Phase 1: ENTRY GATE" (that's spec-writer)
  - `spec-writer.md` does NOT contain "DISCOVERY (Phase 1)" (that's review-team)
  - `review-team-updates.md` does NOT contain "#!/bin/bash" (that's hook)

- [ ] **Step 3: Structural integrity**
  - 6 files exist (README + 5 content files)
  - Every file starts with valid YAML frontmatter (`---` delimited)
  - All relative markdown links resolve: `grep -oP '\[.*?\]\((.*?)\)' *.md | ...`

- [ ] **Step 4: Reference integrity**
  - Zero stale `§` references: `grep -r '§[0-9]' *.md` returns nothing
  - All `#anchor` fragments resolve to headings in target files

#### Task 8: Update README reading order

- [ ] **Step 1:** Refresh `README.md` with final one-line summaries based on actual file content
- [ ] **Step 2:** Verify every content file appears in the reading order table
- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): finalize README reading order"`

#### Task 9: Remove source document

**Precondition:** Task 7 passes completely.

- [ ] **Step 1:** `trash docs/superpowers/specs/2026-03-15-spec-writing-system-design.md`
- [ ] **Step 2:** Verify removal: file no longer at original path
- [ ] **Step 3:** Commit
  `git commit -m "docs(spec-writing-system): remove monolithic source after validated migration"`

---

## Cross-Reference Disambiguation Table

All `§` references in the source point to Section 1 subsections. Since these all land in `shared-contract.md`, disambiguation is straightforward — no context-dependent routing needed.

| Source Pattern | Semantic Anchor | Target Link (from other files) | Target Link (within shared-contract) |
|---|---|---|---|
| `§1.1` / "spec.yaml" | `#spec-yaml` | `shared-contract.md#spec-yaml` | `#spec-yaml` |
| `§1.2` / "Claims Enum" / "fixed enum" | `#claims-enum` | `shared-contract.md#claims-enum` | `#claims-enum` |
| `§1.3` / "derivation table" / "shared derivation table" | `#claim-to-role-derivation-table` | `shared-contract.md#claim-to-role-derivation-table` | `#claim-to-role-derivation-table` |
| `§1.4` / "File Frontmatter" / "per the shared contract" (near frontmatter) | `#file-frontmatter` | `shared-contract.md#file-frontmatter` | `#file-frontmatter` |
| `§1.5` / "Precedence Resolution" / "precedence rules" | `#precedence-resolution` | `shared-contract.md#precedence-resolution` | `#precedence-resolution` |
| `§1.6` / "Boundary Rules" | `#boundary-rules` | `shared-contract.md#boundary-rules` | `#boundary-rules` |
| `§1.7` / "Cross-Reference Conventions" | `#cross-reference-conventions` | `shared-contract.md#cross-reference-conventions` | `#cross-reference-conventions` |
| `§1.8` / "Failure Model" | `#failure-model` | `shared-contract.md#failure-model` | `#failure-model` |
| `§1.9` / "Concrete Example" | `#concrete-example` | `shared-contract.md#concrete-example` | `#concrete-example` |

**No disambiguation needed:** Every `§` reference in the source maps to exactly one anchor in `shared-contract.md` regardless of surrounding context. No section references span multiple possible targets.

---

## Stage / Dependency Summary

| Stage | Tasks | Parallelizable? | Gate Condition |
|-------|-------|-----------------|----------------|
| 0 | Task 0 (scaffold) | — | Directory + README exist |
| 1 | Tasks 1–5 (content migration) | Yes, all 5 independent | All 5 files created |
| 2 | (skipped — no splits) | — | — |
| 3 | Task 6 (cross-references) | No — touches 3 files | Zero stale `§` references |
| 4 | Tasks 7→8→9 (validate→update→remove) | Sequential chain | Content validated → README updated → source removed |

**Total commits:** 9 (1 scaffold + 5 migration + 1 cross-ref + 1 README + 1 source removal)

# Engram Spec Modularization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the monolithic Engram design spec into a modular file structure organized by decision-making authority, enabling independent amendment of each module and accommodating 4 new sections.

**Architecture:** Authority-cluster split — modules are grouped by ownership edges (who decides changes), not section numbers. Three `contracts/` files form the behavioral authority set. Schema details, skill designs, and implementation stubs live in separate directories. Cross-references use semantic kebab-case anchors with relative markdown links.

**Tech Stack:** Markdown, YAML frontmatter, bash (validation)

**Extraction method:** Use **heading-based extraction** for all tasks — match section headings (e.g., `## 4. MCP Tool Surface`), delimit by the next same-level heading or `---` separator. Do NOT use line numbers as boundaries. Line numbers in this plan are approximate references only; the spec may have shifted since this plan was written.

*Amended based on Codex deep review #23 (thread `019cea99`). 7 must-fix items applied: heading-based extraction, task boundary corrections, Public IDs reclassification, semantic cross-reference mapping, validation strengthening, file count correction, staged execution model.*

---

## Context

### Source

Single file: `docs/plans/2026-03-12-engram-design.md` (~997 lines, 8 sections)

**Extraction boundaries:** Use section headings as boundaries, not line numbers. Each section starts at its `##` or `###` heading and ends at the next same-level heading or `---` separator.

| Section | Heading to match | Migration status |
|---------|-----------------|-----------------|
| S1 System Overview | `## 1. System Overview` | move → foundations.md |
| S2 Skills/MCP/Judgment Split | `## 2. Skills, MCP Tools, and the Judgment Split` | move → foundations.md |
| S3 Design Decisions | `## 3. Design Decisions` (includes MCP vs CLI rationale subsection) | move → decisions.md |
| S4 MCP Tool Surface | `## 4. MCP Tool Surface (13 tools)` | move → contracts/tool-surface.md |
| S5 Internal Architecture | `## 5. Internal Architecture` (includes Deferred for v1) | move → internal-architecture.md |
| S6.1-S6.5 Database Schema | `## 6. Database Schema` through `### 6.5` | move → schema/ddl.md |
| S6.6 Design Notes | `### 6.6 Design Notes` | **split** → contracts/behavioral-semantics.md + schema/rationale.md |
| S7.1-S7.2 Skill Overview | `## 7. Skill Surface` through `### 7.2` | move → skills/overview.md |
| S7.3 Cross-Cutting Patterns | `### 7.3 Cross-Cutting Patterns` (through end of Lazy Session Bootstrap) | move → contracts/skill-orchestration.md |
| S7.4 Per-Skill Designs | `### 7.4 Per-Skill Designs` | move → skills/catalog.md |
| S7.5-S7.7 Appendix | `### 7.5` through `### 7.7` | move → skills/appendix.md |
| S8 Remaining Design Work | `## 8. Remaining Design Work` | split → 5 implementation/ stubs |

### Target Structure

```
docs/specs/engram/
  README.md                      # Reading order, doc conventions, authority statement
  legacy-map.md                  # Section-number → file/anchor mapping (temporary aid)
  amendments.md                  # Chronological amendment log (extracted from inline histories)
  foundations.md                 # S1 + S2
  decisions.md                   # S3
  internal-architecture.md       # S5

  contracts/                     # Behavioral authority set
    tool-surface.md              # S4: tool table, envelopes, bootstrap, action semantics, result types
    behavioral-semantics.md      # S6.6 observable behavior: merge, atomicity, ordering, lifecycle rules
    skill-orchestration.md       # S7.3: two-stage guard, confirmation model, shared contracts, lazy bootstrap

  schema/
    ddl.md                       # S6.1-S6.5: all DDL + connection pragmas
    rationale.md                 # S6.6 storage rationale: ON DELETE, FTS sync, FK coupling, internals

  skills/
    overview.md                  # S7.1 roster + S7.2 visibility model
    catalog.md                   # S7.4 all 6 per-skill designs (stable anchors, extraction-ready)
    appendix.md                  # S7.5 directory layout + S7.6 allowed-tools naming + S7.7 open questions

  implementation/                # Stubs — status:stub, authority:pending, normative:false
    hooks.md
    server-validation.md
    plugin-packaging.md
    migration-strategy.md
    testing-strategy.md
```

### Key Rules (from Codex dialogues #20-#21)

**Frontmatter (5 fields):**
```yaml
---
module: <kebab-case-name>
legacy_sections: [<original section numbers>]
authority: <contracts|schema|skills|implementation|root>
normative: <true|false>
status: <active|stub>
---
```

**Anchor format:** Semantic kebab-case (e.g., `#anchor-hash-merge`). No section numbers. No permanent redirect stubs.

**Cross-reference format:** Relative links within `docs/specs/engram/` — e.g., `[anchor_hash merge](contracts/behavioral-semantics.md#anchor-hash-merge)`.

**S6.6 split rule (observable-vs-explanatory):** "If a client can observe it through the MCP surface, it belongs in `contracts/behavioral-semantics.md`. If it explains storage choices, it belongs in `schema/rationale.md`."

**Refined validation-boundary rule:** Request-validity (decidable from payload alone) → `tool-surface.md`. Semantic preconditions (depends on persisted state) → `behavioral-semantics.md`. Enforcement mechanics (algorithms, ordering) → `implementation/server-validation.md`.

**tool-surface cross-ref rule:** Request-selected branches (deterministic from payload) define inline. State-selected branches (depends on DB state) name-only with anchor link to behavioral-semantics.md. No duplicate explanatory prose.

---

## Chunk 1: Scaffold and Clean Splits

### Task 1: Create directory structure and README

**Files:**
- Create: `docs/specs/engram/README.md`
- Create: `docs/specs/engram/contracts/` (directory)
- Create: `docs/specs/engram/schema/` (directory)
- Create: `docs/specs/engram/skills/` (directory)
- Create: `docs/specs/engram/implementation/` (directory)

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p docs/specs/engram/{contracts,schema,skills,implementation}
```

- [ ] **Step 2: Write README.md**

```markdown
---
module: readme
legacy_sections: []
authority: root
normative: false
status: active
---

# Engram Design Specification

Modular design spec for Engram — a persistence and observability layer for Claude Code.

## Reading Order

| # | Document | What it covers |
|---|----------|---------------|
| 1 | [foundations.md](foundations.md) | System overview, architecture, judgment split |
| 2 | [decisions.md](decisions.md) | Locked design decisions with sources |
| 3 | [contracts/tool-surface.md](contracts/tool-surface.md) | MCP tool table, envelopes, bootstrap, action semantics, public types |
| 4 | [contracts/behavioral-semantics.md](contracts/behavioral-semantics.md) | Observable behavior: merge rules, atomicity, ordering, lifecycle |
| 5 | [internal-architecture.md](internal-architecture.md) | Directory layout, architectural rules, deferred items |
| 6 | [schema/ddl.md](schema/ddl.md) | All DDL (11 tables, 1 FTS5, 3 triggers) |
| 7 | [schema/rationale.md](schema/rationale.md) | Storage rationale: ON DELETE, FTS sync, FK coupling |
| 8 | [contracts/skill-orchestration.md](contracts/skill-orchestration.md) | Two-stage guard, confirmation model, shared contracts, lazy bootstrap |
| 9 | [skills/overview.md](skills/overview.md) | Skill roster and visibility model |
| 10 | [skills/catalog.md](skills/catalog.md) | Per-skill designs (6 skills) |
| 11 | [skills/appendix.md](skills/appendix.md) | Directory layout, allowed-tools naming, open questions |
| 12 | `implementation/*.md` | Hook specs, validation, packaging, migration, testing (stubs) |

## Authority Model

The public API contract is defined by the documents in `contracts/`. Schema documents describe storage implementation and must not change public behavior. Implementation documents describe enforcement mechanics. Changes to observable behavior require updating `contracts/` first.

## Document Conventions

- **Frontmatter:** Every document has YAML frontmatter with `module`, `legacy_sections`, `authority`, `normative`, `status`
- **Anchors:** Semantic kebab-case (e.g., `#anchor-hash-merge`). No section numbers.
- **Cross-references:** Relative markdown links (e.g., `[merge rules](contracts/behavioral-semantics.md#anchor-hash-merge)`)
- **Amendment history:** Tracked in [amendments.md](amendments.md), not inline

## Legacy Section Map

See [legacy-map.md](legacy-map.md) for old section numbers → new file/anchor mapping.
```

- [ ] **Step 3: Commit scaffold**

```bash
git add docs/specs/engram/
git commit -m "docs(engram): scaffold modular spec directory structure"
```

### Task 2: Migrate foundations.md (S1 + S2)

**Files:**
- Create: `docs/specs/engram/foundations.md`
- Source: S1 (`## 1. System Overview`) + S2 (`## 2. Skills, MCP Tools, and the Judgment Split`)

- [ ] **Step 1: Write foundations.md**

Add frontmatter, then copy S1 and S2 verbatim (from `## 1. System Overview` through the end of S2's `---` separator). Replace section numbers with semantic headings. Add anchors to key concepts.

```yaml
---
module: foundations
legacy_sections: ["1", "2"]
authority: root
normative: true
status: active
---
```

Heading changes:
- `## 1. System Overview` → `## System Overview`
- `## 2. Skills, MCP Tools, and the Judgment Split` → `## Skills, MCP Tools, and the Judgment Split`

Add anchors to key concepts:
- `### Architecture: "A outside, B inside"` → add `{#architecture-a-outside-b-inside}` (or rely on auto-generated heading anchor)
- `### Three Subsystems` → `{#three-subsystems}`

Content is copied verbatim — no prose changes.

- [ ] **Step 2: Verify content preserved**

```bash
# Extract S1+S2 from source (heading-based), normalize whitespace, compare
sed -n '/^## 1\. System Overview/,/^## 3\. Design Decisions/{ /^## 3\./d; p; }' docs/plans/2026-03-12-engram-design.md | sed '/^---$/d; /^$/d; s/^#\+ [0-9]\+\.\? *//' | sort > /tmp/src_normalized
sed '1,/^---$/d' docs/specs/engram/foundations.md | sed '/^---$/d; /^$/d; s/^#\+ //' | sort > /tmp/dst_normalized
# Check for missing lines (should be empty — all source lines present in destination)
comm -23 /tmp/src_normalized /tmp/dst_normalized
```

Also verify no boundary contamination (S3 content should NOT appear):

```bash
# S3's first line after its heading — should NOT be in foundations.md
grep -c 'Design Decisions' docs/specs/engram/foundations.md
# Expected: 0
```

- [ ] **Step 3: Commit**

```bash
git add docs/specs/engram/foundations.md
git commit -m "docs(engram): migrate S1+S2 to foundations.md"
```

### Task 3: Migrate decisions.md (S3)

**Files:**
- Create: `docs/specs/engram/decisions.md`
- Source: S3 (`## 3. Design Decisions` — includes the decision table AND the "MCP vs CLI — Re-evaluated Rationale" subsection)

- [ ] **Step 1: Write decisions.md**

```yaml
---
module: decisions
legacy_sections: ["3"]
authority: root
normative: true
status: active
---
```

Heading: `## 3. Design Decisions` → `## Design Decisions`

Copy the full S3 section verbatim — this includes the 11-row decision table AND the "MCP vs CLI — Re-evaluated Rationale" subsection that follows it. S3 extends from its `##` heading to the next `---` separator before S4. Do NOT truncate at the decision table.

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/decisions.md
git commit -m "docs(engram): migrate S3 to decisions.md"
```

### Task 4: Migrate internal-architecture.md (S5)

**Files:**
- Create: `docs/specs/engram/internal-architecture.md`
- Source: S5 (`## 5. Internal Architecture` — includes the Deferred for v1 subsection)

- [ ] **Step 1: Write internal-architecture.md**

```yaml
---
module: internal-architecture
legacy_sections: ["5"]
authority: root
normative: true
status: active
---
```

Heading: `## 5. Internal Architecture` → `## Internal Architecture`

Content copied verbatim. S5 contains references to "Section 7.3" and "Section 4" — flag these for Task 15 (cross-reference update pass).

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/internal-architecture.md
git commit -m "docs(engram): migrate S5 to internal-architecture.md"
```

---

## Chunk 2: Contracts Directory

### Task 5: Migrate contracts/tool-surface.md (S4)

**Files:**
- Create: `docs/specs/engram/contracts/tool-surface.md`
- Source: S4 (`## 4. MCP Tool Surface (13 tools)` — from the heading through the `---` separator before S5)

This is the largest authority source — the tool table, response envelopes, session bootstrap, action semantics, architectural rules, and public result types.

- [ ] **Step 1: Write tool-surface.md**

```yaml
---
module: tool-surface
legacy_sections: ["4"]
authority: contracts
normative: true
status: active
---
```

Heading: `## 4. MCP Tool Surface (13 tools)` → `## MCP Tool Surface (13 tools)`

Remove the inline amendment history block (the long italic revision note immediately after the S4 heading). This history moves to `amendments.md` (Task 13).

Add semantic anchors to subsections:
- `### Response Envelopes` → `{#response-envelopes}`
- `### Ref Object` → `{#ref-object}`
- `### Session Bootstrap` → `{#session-bootstrap}`
- `### Action Semantics` → `{#action-semantics}`
- `### Architectural Rules` → `{#architectural-rules}`
- `### Public Result Types` → `{#public-result-types}`

**Cross-reference updates within this file:**
- "see S6.6" (in the anchor_hash merge description) → `[behavioral-semantics.md](behavioral-semantics.md#anchor-hash-merge)` (link-only, no duplicate prose)
- "Section 6 is storage schema; Section 4 is the API contract" (in Architectural Rules) → Rewrite as: "The public API contract is defined by this document and `contracts/`. [Schema documents](../schema/ddl.md) describe storage implementation and must not change public behavior."

**State-selected branches (link-only rule):** Where S4 currently says "see S6.6" for anchor_hash merge behavior, the merged file should name the branch and link to behavioral-semantics.md without duplicating the explanation.

- [ ] **Step 2: Verify content preserved**

```bash
# Extract S4 from source (heading-based), check no S3 content leaked in
grep -c 'MCP vs CLI' docs/specs/engram/contracts/tool-surface.md
# Expected: 0 (MCP vs CLI rationale belongs in decisions.md, not tool-surface.md)

# Check S4-specific sentinel is present
grep -c 'Response Envelopes' docs/specs/engram/contracts/tool-surface.md
# Expected: >= 1
```

- [ ] **Step 3: Commit**

```bash
git add docs/specs/engram/contracts/tool-surface.md
git commit -m "docs(engram): migrate S4 to contracts/tool-surface.md"
```

### Task 6: Split S6.6 into behavioral-semantics.md and rationale.md

**Files:**
- Create: `docs/specs/engram/contracts/behavioral-semantics.md`
- Create: `docs/specs/engram/schema/rationale.md`
- Source: S6.6 (`### 6.6 Design Notes` — from the heading through the next `##` heading)

This is the only **split** migration (S6.6 → two files). Apply the merge-audit protocol:
1. Read all S6.6 content
2. Classify each heading/paragraph using the observable-vs-explanatory rule
3. Copy to appropriate file
4. Verify no content lost

**S6.6 content classification:**

Match each paragraph by its bold lead text (e.g., **`Table count:`**). Paragraphs are listed in source order.

| S6.6 Paragraph (match by bold lead) | Destination | Rule applied |
|--------------------------------------|-------------|--------------|
| **Table count** | rationale.md | Storage bookkeeping |
| **ON DELETE policy** | rationale.md | Storage choice |
| **Kind-check enforcement** | rationale.md | Internal invariant |
| **FTS5 sync model** | rationale.md | Storage implementation |
| **`search_projection.body` mapping** | rationale.md | Storage mapping |
| **`sort_by` SQL mapping** | rationale.md | Enforcement mechanics (SQL translation) |
| **`query` relevance_score** | behavioral-semantics.md | Observable behavior (opaque float contract) |
| **`anchor_hash` dedup and merge** | behavioral-semantics.md | State-dependent branching |
| **`lesson_capture` dual-path** | behavioral-semantics.md | State-dependent outcome |
| **Promotion model** | rationale.md | Internal provenance mechanism |
| **Public IDs** | **tool-surface.md** | API contract: defines which IDs are public, who generates them, that `entity_pk` is never exposed |
| **Three-class relationship taxonomy** | rationale.md | Storage taxonomy |
| **Provenance uniqueness** | behavioral-semantics.md | Observable dedup behavior |
| **`session_links` directionality** | rationale.md | Storage convention |
| **`session_end` atomicity** | behavioral-semantics.md | Observable guarantee |
| **`session_get` as load API** | behavioral-semantics.md | Observable selection behavior |
| **Cross-subsystem FK coupling** | rationale.md | Storage coupling |
| **Task dependency write paths** | rationale.md | Storage mechanics |
| **`task_update(close)` terminal status** | behavioral-semantics.md | Lifecycle state validation |
| **Tool parameter → table mapping** | rationale.md | Storage mapping |
| **Deferred for v1** | rationale.md | Scope decisions |
| **`sessions.updated_at`** | rationale.md | Internal-only column |
| **`session_list` ordering + `activity_at`** | behavioral-semantics.md | Observable ordering guarantee (keep full paragraph — the `updated_at` contrast is part of the observable contract) |
| **Final snapshot uniqueness** | rationale.md | Defense-in-depth storage |
| **Migration strategy** | rationale.md | Storage evolution |

**Note:** "Public IDs" was reclassified from rationale.md to tool-surface.md (Codex deep review #23). It defines exposed identifiers and generation semantics — this is API contract, not storage rationale. Add it to tool-surface.md as a subsection after Public Result Types.

- [ ] **Step 1: Write contracts/behavioral-semantics.md**

```yaml
---
module: behavioral-semantics
legacy_sections: ["6.6"]
authority: contracts
normative: true
status: active
---
```

Heading: `## Behavioral Semantics`

Add semantic anchors:
- `### anchor_hash Dedup and Merge` → `{#anchor-hash-merge}`
- `### lesson_capture Dual-Path` → `{#lesson-capture-dual-path}`
- `### query Relevance Score` → `{#query-relevance-score}`
- `### Provenance Uniqueness` → `{#provenance-uniqueness}`
- `### session_end Atomicity` → `{#session-end-atomicity}`
- `### session_get as Load API` → `{#session-get-load-api}`
- `### task_update(close) Terminal Status` → `{#task-update-close-terminal-status}`
- `### session_list Ordering and activity_at` → `{#session-list-ordering}`

Copy each classified paragraph verbatim. Order: follow the reading flow that makes sense for someone understanding observable behavior (merge → lifecycle → ordering).

- [ ] **Step 2: Write schema/rationale.md**

```yaml
---
module: rationale
legacy_sections: ["6.6"]
authority: schema
normative: false
status: active
---
```

Heading: `## Schema Rationale`

Note in header: *"This document explains storage design choices. It is non-normative — observable behavior is defined in [contracts/behavioral-semantics.md](../contracts/behavioral-semantics.md)."*

Copy remaining S6.6 paragraphs verbatim. Add semantic anchors.

- [ ] **Step 3: Verify no content lost (merge-audit validation)**

```bash
# Extract S6.6 from source using heading match
sed -n '/^### 6\.6 Design Notes/,/^## [0-9]/{ /^## [0-9]/d; p; }' docs/plans/2026-03-12-engram-design.md > /tmp/s66_source.md

# Strip frontmatter from destinations
sed '1,/^---$/d' docs/specs/engram/contracts/behavioral-semantics.md > /tmp/s66_behavioral.md
sed '1,/^---$/d' docs/specs/engram/schema/rationale.md > /tmp/s66_rationale.md
```

**Paragraph inventory (completeness + uniqueness):** Verify every bold-lead paragraph from S6.6 appears in exactly one destination file:

```bash
# Extract bold leads from source
grep -oP '\*\*`?[^*]+`?\*\*' /tmp/s66_source.md | sort -u > /tmp/s66_paragraphs.txt

# Check each appears in exactly one destination
while read lead; do
  b=$(grep -c "$lead" /tmp/s66_behavioral.md 2>/dev/null || echo 0)
  r=$(grep -c "$lead" /tmp/s66_rationale.md 2>/dev/null || echo 0)
  t=$(grep -c "$lead" docs/specs/engram/contracts/tool-surface.md 2>/dev/null || echo 0)
  total=$((b + r + t))
  [ "$total" -ne 1 ] && echo "ERROR: '$lead' appears in $total files (behavioral=$b, rationale=$r, tool-surface=$t)"
done < /tmp/s66_paragraphs.txt
# Expected: no ERROR lines
```

Also compare word counts as a gross check:

```bash
wc -w /tmp/s66_source.md /tmp/s66_behavioral.md /tmp/s66_rationale.md
# Combined destinations should be >= source (new headings add words)
```

- [ ] **Step 4: Commit**

```bash
git add docs/specs/engram/contracts/behavioral-semantics.md docs/specs/engram/schema/rationale.md
git commit -m "docs(engram): split S6.6 into behavioral-semantics.md + rationale.md"
```

### Task 7: Migrate contracts/skill-orchestration.md (S7.3)

**Files:**
- Create: `docs/specs/engram/contracts/skill-orchestration.md`
- Source: S7.3 (`### 7.3 Cross-Cutting Patterns` — from the heading through the end of the Lazy Session Bootstrap subsection, delimited by the next `###` heading)

- [ ] **Step 1: Write skill-orchestration.md**

```yaml
---
module: skill-orchestration
legacy_sections: ["7.3"]
authority: contracts
normative: true
status: active
---
```

Heading: `## Skill Orchestration`

Copy S7.3 verbatim — from `### 7.3 Cross-Cutting Patterns` through the end of Lazy Session Bootstrap (including its mechanism, key properties, and `/load` exception subsections). This includes:
- Two-Stage Guard Architecture
- Confirmation Severity Model
- Snapshot Content Schema
- Cross-Skill Contracts
- Single-Mutation Failure Pattern
- Lazy Session Bootstrap (full content including mechanism, key properties, and the `/load` exception)

Add semantic anchors:
- `{#two-stage-guard}`
- `{#confirmation-severity}`
- `{#snapshot-content-schema}`
- `{#cross-skill-contracts}`
- `{#single-mutation-failure}`
- `{#lazy-session-bootstrap}`

Update internal references:
- "Section 4" → `[tool-surface.md](tool-surface.md#action-semantics)`
- "Section 7.3" self-references → appropriate anchors within same file

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/contracts/skill-orchestration.md
git commit -m "docs(engram): migrate S7.3 to contracts/skill-orchestration.md"
```

---

## Chunk 3: Schema and Skills

### Task 8: Migrate schema/ddl.md (S6.1-S6.5)

**Files:**
- Create: `docs/specs/engram/schema/ddl.md`
- Source: S6.1-S6.5 (`## 6. Database Schema` through `### 6.5`, excluding S6.6)

- [ ] **Step 1: Write ddl.md**

```yaml
---
module: ddl
legacy_sections: ["6.1", "6.2", "6.3", "6.4", "6.5"]
authority: schema
normative: true
status: active
---
```

Heading: `## Database Schema`

Copy connection pragmas (the `PRAGMA` block before S6.1), then S6.1 Kernel, S6.2 Context, S6.3 Work, S6.4 Knowledge, S6.5 Cross-cutting verbatim. Stop before `### 6.6 Design Notes`.

Remove section number prefixes from headings (e.g., `### 6.1 Kernel` → `### Kernel`).

Add header note: *"Schema rationale and design notes are in [rationale.md](rationale.md). Observable behavioral guarantees are in [contracts/behavioral-semantics.md](../contracts/behavioral-semantics.md)."*

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/schema/ddl.md
git commit -m "docs(engram): migrate S6.1-S6.5 to schema/ddl.md"
```

### Task 9: Migrate skills/overview.md (S7.1 + S7.2)

**Files:**
- Create: `docs/specs/engram/skills/overview.md`
- Source: S7 parent heading (`## 7. Skill Surface`) + S7.1 (`### 7.1`) + S7.2 (`### 7.2`), stopping before `### 7.3`

- [ ] **Step 1: Write overview.md**

```yaml
---
module: skills-overview
legacy_sections: ["7", "7.1", "7.2"]
authority: skills
normative: true
status: active
---
```

The S7 parent heading (`## 7. Skill Surface (6 skills)`) becomes this file's top-level heading: `## Skill Surface`. The inline amendment history (italic revision note under the S7 heading) is extracted to `amendments.md` (Task 13). Copy S7.1 Skill Roster and S7.2 Visibility Model verbatim.

Remove section number prefixes. Update internal references:
- "Section 7.3" → `[skill-orchestration.md](../contracts/skill-orchestration.md#two-stage-guard)`

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/skills/overview.md
git commit -m "docs(engram): migrate S7.1+S7.2 to skills/overview.md"
```

### Task 10: Migrate skills/catalog.md (S7.4)

**Files:**
- Create: `docs/specs/engram/skills/catalog.md`
- Source: S7.4 (`### 7.4 Per-Skill Designs` — from the heading through the last skill design, stopping before `### 7.5`)

This is the largest single migration (~238 lines, 6 skill designs). All 6 skills stay in one file with stable anchors. Extraction trigger: a skill exceeds ~70-100 lines, is independently amended, or develops unique workflows.

- [ ] **Step 1: Write catalog.md**

```yaml
---
module: skills-catalog
legacy_sections: ["7.4"]
authority: skills
normative: true
status: active
---
```

Heading: `## Per-Skill Designs`

Add stable anchors per skill:
- `#### /save — Session Persistence` → `{#skill-save}`
- `#### /load — Session Resumption` → `{#skill-load}`
- `#### /triage — Project Orientation` → `{#skill-triage}`
- `#### /task — Task Management` → `{#skill-task}`
- `#### /remember — Lesson Capture` → `{#skill-remember}`
- `#### /promote — Lesson Promotion` → `{#skill-promote}`

Copy all 6 skill designs verbatim. Update internal references:
- "Section 7.3" → `[skill-orchestration.md](../contracts/skill-orchestration.md#lazy-session-bootstrap)` (or appropriate anchor)
- "Section 4" → `[tool-surface.md](../contracts/tool-surface.md#action-semantics)`
- "Section 6.3"/"Section 6.6" → appropriate new file/anchor

Add extraction note at top: *"Skills that exceed ~100 lines or are independently amended should be extracted to their own file."*

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/skills/catalog.md
git commit -m "docs(engram): migrate S7.4 to skills/catalog.md"
```

### Task 11: Migrate skills/appendix.md (S7.5-S7.7)

**Files:**
- Create: `docs/specs/engram/skills/appendix.md`
- Source: S7.5-S7.7 (`### 7.5` through `### 7.7`, stopping before `## 8`)

- [ ] **Step 1: Write appendix.md**

```yaml
---
module: skills-appendix
legacy_sections: ["7.5", "7.6", "7.7"]
authority: skills
normative: true
status: active
---
```

Copy S7.5 Skill Directory Layout, S7.6 allowed-tools Naming, S7.7 Open Questions verbatim.

No cross-references to other sections (S7.5 and S7.6 are self-contained reference subsections).

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/skills/appendix.md
git commit -m "docs(engram): migrate S7.5-S7.7 to skills/appendix.md"
```

---

## Chunk 4: Stubs, Metadata, Cross-References, Validation

### Task 12: Create implementation stubs (S8)

**Files:**
- Create: 5 stub files in `docs/specs/engram/implementation/`
- Source: S8 (`## 8. Remaining Design Work`)

- [ ] **Step 1: Write all 5 stubs**

Each stub follows the same template:

```yaml
---
module: <name>
legacy_sections: ["8"]
authority: implementation
normative: false
status: stub
---

# <Title>

> **Status:** Stub — not yet designed. See [README.md](../README.md) for reading order.

## Scope

<One sentence from S8 checklist describing what this section covers.>

## Content

To be designed.
```

Create:
- `implementation/hooks.md` — "PreToolUse identity guard, SessionStart/Stop lifecycle telemetry"
- `implementation/server-validation.md` — "What each mutation tool validates (enforcement mechanics: normalization algorithms, lookup strategy, validation ordering)"
- `implementation/plugin-packaging.md` — "plugin.json, .mcp.json, directory structure"
- `implementation/migration-strategy.md` — "How to deprecate old plugins"
- `implementation/testing-strategy.md` — "What to test at each tier"

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/implementation/
git commit -m "docs(engram): create implementation stubs from S8"
```

### Task 13: Create amendments.md

**Files:**
- Create: `docs/specs/engram/amendments.md`
- Source: Inline amendment histories from S4 (italic revision note after heading), S6 (italic revision note after heading), S6.6 (italic revision note after heading), S7 (italic revision note after heading)
- Depends on: Tasks 5, 6, 7, 8, 9, 10

- [ ] **Step 1: Extract amendment histories and write amendments.md**

```yaml
---
module: amendments
legacy_sections: []
authority: root
normative: false
status: active
---
```

Heading: `## Amendment History`

Extract the italic revision notes from each section header and organize chronologically:

| Amendment | Sections Touched | Source |
|-----------|-----------------|--------|
| Codex dialogue #5 | S6 | Schema design |
| Codex deep review #6 | S4, S6, S6.6 | Tool surface + schema revision |
| Codex dialogue #7, #8 | S7 | Skill surface design |
| Adversarial review #9 | S7 | 13 findings applied |
| Evaluative review #16 | S4, S6.6, S7 | Identity/bootstrap/naming |
| Collaborative resolution #17 | S4, S6.6, S7 | Three-layer enforcement, patch semantics |
| Bundle 1 | S4, S5, S6.6, S7 | Identity/bootstrap (34 edits) |
| Bundle 2 | S4, S6.6, S7 | Session lifecycle (19 edits) |
| Bundle 3 | S4, S6.3, S6.6, S7 | terminal_status, blocked_by rename |
| Bundle 4 | S4, S6.5, S6.6, S7 | anchor_hash merge, provenance, sort_by |
| Codex dialogue #19 | S4, S6.6, S7 | session_list state, lesson_update provenance, naming convention |
| Holistic review | S4, S7.7 | task_ids/lesson_ids, Q1 reopened |

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/amendments.md
git commit -m "docs(engram): extract amendment histories to amendments.md"
```

### Task 14: Create legacy-map.md

**Files:**
- Create: `docs/specs/engram/legacy-map.md`

- [ ] **Step 1: Write legacy-map.md**

```yaml
---
module: legacy-map
legacy_sections: []
authority: root
normative: false
status: active
---
```

```markdown
## Legacy Section Map

Mapping from original section numbers to new file locations. Use for updating old references.

| Old Reference | New Location |
|--------------|-------------|
| Section 1 / S1 | [foundations.md](foundations.md) |
| Section 2 / S2 | [foundations.md](foundations.md) |
| Section 3 / S3 | [decisions.md](decisions.md) |
| Section 4 / S4 | [contracts/tool-surface.md](contracts/tool-surface.md) |
| Section 5 / S5 | [internal-architecture.md](internal-architecture.md) |
| Section 6 / S6 | [schema/ddl.md](schema/ddl.md) |
| Section 6.6 / S6.6 | [contracts/behavioral-semantics.md](contracts/behavioral-semantics.md) + [schema/rationale.md](schema/rationale.md) |
| Section 7.1 / S7.1 | [skills/overview.md](skills/overview.md) |
| Section 7.2 / S7.2 | [skills/overview.md](skills/overview.md) |
| Section 7.3 / S7.3 | [contracts/skill-orchestration.md](contracts/skill-orchestration.md) |
| Section 7.4 / S7.4 | [skills/catalog.md](skills/catalog.md) |
| Section 7.5 / S7.5 | [skills/appendix.md](skills/appendix.md) |
| Section 7.6 / S7.6 | [skills/appendix.md](skills/appendix.md) |
| Section 7.7 / S7.7 | [skills/appendix.md](skills/appendix.md) |
| Section 8 / S8 | [implementation/](implementation/) (5 stub files) |
```

- [ ] **Step 2: Commit**

```bash
git add docs/specs/engram/legacy-map.md
git commit -m "docs(engram): create legacy section map"
```

### Task 15: Cross-reference update pass

**Files:**
- Modify: All files in `docs/specs/engram/`

The source spec contains 12+ inline cross-references by section number. These must all be updated to file/anchor links.

- [ ] **Step 1: Find all section-number references**

```bash
# Find ALL section-number patterns including shorthand (S4, S6.6, etc.)
grep -rn 'Section [0-9]\|S[0-9]\.\|S[0-9][^a-zA-Z]' docs/specs/engram/ --include='*.md' | grep -v legacy-map.md | grep -v amendments.md
```

- [ ] **Step 2: Update each reference using the semantic mapping table**

**Process every hit individually.** Each pattern maps to a different anchor depending on surrounding context. Use the disambiguation rules below.

| Pattern | Default target | Disambiguation |
|---------|---------------|----------------|
| `Section 4` / `S4` | `contracts/tool-surface.md` | If near "bootstrap" → `#session-bootstrap`. If near "atomic rejection" / "invariant" → `#architectural-rules`. If near "action semantics" / "idempotency" → `#action-semantics`. If near "result types" → `#public-result-types`. Otherwise → file-level link. |
| `Section 6` / `S6` | `schema/ddl.md` | If near "storage schema" vs "API contract" → use in context of the contrast. |
| `Section 6.3` | `schema/ddl.md#work` | |
| `Section 6.6` / `S6.6` / `see S6.6` | `contracts/behavioral-semantics.md` | If near "anchor_hash" → `#anchor-hash-merge`. If near "atomicity" → `#session-end-atomicity`. If near "ordering" → `#session-list-ordering`. Otherwise → file-level link. |
| `Section 7.3` / `S7.3` | `contracts/skill-orchestration.md` | If near "lazy bootstrap" → `#lazy-session-bootstrap`. If near "two-stage guard" → `#two-stage-guard`. If near "confirmation" → `#confirmation-severity`. If near "failure" → `#single-mutation-failure`. Otherwise → file-level link. |
| `Section 8` | `implementation/` | Link to directory. |

Use relative paths appropriate to each file's location (files in `contracts/` use `../schema/`, files at root use `contracts/`, etc.).

**Double-update prevention:** Task 10 also updates `Section 7.3` references inline in catalog.md. If Task 10 has already run, verify those references are already updated before re-processing in this pass. `grep` will not find them if already converted to links.

- [ ] **Step 3: Verify no stale references remain**

```bash
# Must catch ALL patterns including shorthand — broader regex than Step 1
grep -rn 'Section [0-9]\|S[0-9]\.\|S[0-9][^a-zA-Z]\|see S[0-9]' docs/specs/engram/ --include='*.md' | grep -v legacy-map.md | grep -v amendments.md | wc -l
```

Expected: `0`

- [ ] **Step 4: Commit**

```bash
git add docs/specs/engram/
git commit -m "docs(engram): update all cross-references to file/anchor links"
```

### Task 16: Remove monolith source

**Files:**
- Delete: `docs/plans/2026-03-12-engram-design.md`

- [ ] **Step 1: Final content integrity check**

```bash
# Word count comparison (gross check)
wc -w docs/plans/2026-03-12-engram-design.md
find docs/specs/engram/ -name '*.md' -exec cat {} + | wc -w
# Destination should be >= source (frontmatter, anchors, notes add words)

# Source-coverage check: verify key sentinels from each section appear in destination
for sentinel in "System Overview" "Judgment Split" "Design Decisions" "MCP vs CLI" \
  "MCP Tool Surface" "Response Envelopes" "Internal Architecture" "Deferred for v1" \
  "Database Schema" "Design Notes" "Skill Surface" "Cross-Cutting Patterns" \
  "Lazy Session Bootstrap" "Per-Skill Designs" "/save" "/load" "/triage" \
  "Remaining Design Work"; do
  count=$(grep -rl "$sentinel" docs/specs/engram/ --include='*.md' | wc -l)
  [ "$count" -eq 0 ] && echo "MISSING: '$sentinel' not found in any destination file"
done
```

- [ ] **Step 2: Remove source file**

```bash
trash docs/plans/2026-03-12-engram-design.md
```

- [ ] **Step 3: Commit**

```bash
git add -u docs/plans/2026-03-12-engram-design.md
git commit -m "docs(engram): remove monolith spec (migrated to docs/specs/engram/)"
```

### Task 17: Final validation

- [ ] **Step 1: Verify all files present**

```bash
find docs/specs/engram/ -name '*.md' | sort
```

Expected: 19 files (README, legacy-map, amendments, foundations, decisions, internal-architecture = 6 root; 3 contracts; 2 schema; 3 skills; 5 implementation stubs).

- [ ] **Step 2: Verify all frontmatter valid**

```bash
# Each file should start with ---
for f in $(find docs/specs/engram/ -name '*.md'); do
  head -1 "$f" | grep -q '^---$' || echo "MISSING FRONTMATTER: $f"
done
```

- [ ] **Step 3: Verify no broken relative links**

```bash
# Extract all markdown links with their source file, resolve relative to each file's directory
grep -rn '\[.*\]([^)]*\.md[^)]*)' docs/specs/engram/ --include='*.md' | while IFS=: read -r file line content; do
  dir=$(dirname "$file")
  echo "$content" | grep -o '([^)]*\.md[^)]*)' | sed 's/[()]//g; s/#.*//' | while read link; do
    target=$(cd "$dir" && python3 -c "import os.path; print(os.path.normpath('$link'))" 2>/dev/null)
    test -f "$dir/$target" || echo "BROKEN in $file:$line: $link"
  done
done
```

- [ ] **Step 4: Verify no stale section references**

```bash
# Broad regex catching all section-number patterns including shorthand
grep -rn 'Section [0-9]\|S[0-9]\.\|S[0-9][^a-zA-Z]\|see S[0-9]' docs/specs/engram/ --include='*.md' | grep -v legacy-map.md | grep -v amendments.md
```

Expected: 0 results.

- [ ] **Step 4b: Verify fragment anchors resolve**

```bash
# Extract all markdown links with fragments and verify targets exist
grep -roh '\[.*\]([^)]*\.md#[^)]*)' docs/specs/engram/ --include='*.md' | grep -oP '(?<=\().*(?=\))' | while read link; do
  file=$(echo "$link" | cut -d'#' -f1)
  anchor=$(echo "$link" | cut -d'#' -f2)
  # Check anchor appears as a heading (auto-generated slug) in the target file
  if [ -n "$anchor" ] && [ -f "docs/specs/engram/$file" ]; then
    grep -qi "$(echo "$anchor" | tr '-' ' ')" "docs/specs/engram/$file" || echo "BROKEN ANCHOR: $link"
  fi
done
```

- [ ] **Step 5: Final commit (if any fixes needed)**

```bash
git add docs/specs/engram/
git commit -m "docs(engram): fix validation findings"
```

---

## Execution Notes

### Branch strategy

Create `docs/engram-spec-modularization` branch from `main`. All work happens on this branch. Merge to main when validation passes.

### Task dependencies

```
Stage 0: Task 1 (scaffold)
Stage 1: Tasks 2, 3, 4, 5, 7, 8, 9, 11, 12 (all parallel after scaffold)
Stage 2: Task 6 (S6.6 split, after Task 5) | Task 10 (catalog, after Tasks 5+7)
Stage 3: Task 13 (amendments, after Tasks 5-12) | Task 14 (legacy-map, after all file tasks)
Stage 4: Task 15 (cross-refs) → Task 16 (remove monolith) → Task 17 (validation)
```

### Staged execution model

Tasks have cross-agent dependencies that require staged execution. Each stage gate requires all tasks in the prior stage to complete before proceeding.

| Stage | Tasks | Can parallelize? | Gate condition |
|-------|-------|-----------------|----------------|
| **0** | 1 (scaffold) | No | Directory structure exists |
| **1** | 2, 3, 4, 5, 7, 8, 9, 11, 12 | Yes — all independent after scaffold | All files created |
| **2** | 6 (S6.6 split, depends on 5), 10 (catalog, depends on 5+7) | Yes — parallel with each other | Tasks 5 and 7 complete (cross-ref targets exist) |
| **3** | 13 (amendments), 14 (legacy-map) | Yes — parallel with each other | All content tasks complete (source histories available) |
| **4** | 15 (cross-refs) → 16 (remove monolith) → 17 (validation) | No — sequential | Each depends on prior |

### Subagent assignment (if using subagent-driven-development)

| Agent | Stage 1 Tasks | Stage 2 Tasks | Rationale |
|-------|--------------|---------------|-----------|
| Agent A | 2, 3, 4 | — | Clean splits (independent, no cross-refs) |
| Agent B | 5, 8 | 6 | Contracts/tool-surface + schema/ddl → then S6.6 split (needs tool-surface.md from Task 5) |
| Agent C | 7, 9, 11 | 10 | Skill-orchestration + skills directory → then catalog (needs skill-orchestration.md from Task 7) |
| Agent D | 12 | — | Stubs (independent) |
| Sequential | — | — | Stage 3: Tasks 13, 14. Stage 4: Tasks 15, 16, 17 (must run after all agents) |

**Key constraint:** Agent B must complete Task 5 before starting Task 6 (behavioral-semantics.md links to tool-surface.md). Agent C must complete Task 7 before starting Task 10 (catalog.md links to skill-orchestration.md). Both are within-agent sequential dependencies, so no cross-agent coordination needed within Stages 1-2.

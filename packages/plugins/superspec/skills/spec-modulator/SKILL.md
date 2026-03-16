---
name: spec-modulator
description: Design and create multi-file specification structures with authority-based modular organization. Use when converting a monolithic spec/plan into a modular multi-file spec, when creating a new multi-file spec from scratch, or when advising on whether a document should be a single file or modular structure. Trigger on "modularize this spec", "split this into files", "create a spec for X", "this plan is too big", "organize this design doc", "spec structure", "multi-file spec", or when a user has a large design document (>300 lines) and wants to organize it. Also use when the user mentions "spec-modulator" or asks about spec organization strategy.
---

# Spec Modulator

Design multi-file specification structures and produce executable modularization plans.

**Announce at start:** "I'm using the spec-modulator skill to help organize your specification."

Do NOT create, move, delete, or edit target specification files unless the user explicitly asks to execute an approved plan. The plan document is the output — file generation is a separate step.

## Scope

**Reads:** source document (from-monolith mode), codebase structure (both modes)
**Writes:** plan document only (markdown). Does NOT write spec files, create directories, or modify the source document.
**Execution:** When the user approves the plan and requests execution, file operations proceed per the plan's task breakdown. Execution is never automatic.

## Topology Classification

Every invocation starts by classifying the situation into one of three modes:

| Mode | Trigger | Primary Output |
|------|---------|---------------|
| **single-file** | Document is <300 lines, single concern, no distinct authority boundaries | Redirect: "This works well as a single file. No modularization needed." |
| **modular-greenfield** | No source document exists; user is designing a new system | Cluster manifest + file tree + README template |
| **from-monolith** | Source document exists that needs splitting | Modularization plan (mapping ledger, task breakdown, validation, cross-ref disambiguation) |

**Classification questions** (ask the user, do not guess):

1. "Do you have an existing document to modularize, or are you designing from scratch?"
2. If existing: "Can you point me to the file?"
3. If from scratch: "What system are you specifying? What are its major concerns or subsystems?"

---

## Mode: Modular Greenfield

For new specs with no source document. Output is lighter than from-monolith since there is no content to migrate.

### Step 1: Identify Authority Boundaries

Interview the user about their system's ownership structure. The driving question is: **"Who decides changes to what?"**

Authority boundaries emerge from:
- Different subsystems (e.g., storage vs API vs orchestration)
- Different change cadences (e.g., schema changes rarely, implementation changes often)
- Different audiences (e.g., contracts for consumers, internals for maintainers)
- Different normative weight (e.g., binding decisions vs informational context)

### Step 2: Propose Cluster Manifest

Present a cluster manifest for user confirmation. Never finalize clusters without explicit approval.

Clusters are domain-specific — derive them from the user's system, not from templates. Two contrasting examples:

**Example A** — MCP plugin with public API contracts:

| Cluster | Scope | Boundary Rule | Default Normative |
|---------|-------|---------------|-------------------|
| root | Entry point, overview, cross-cutting decisions | Changes here affect all clusters | varies |
| contracts | Public-facing behavior and API guarantees | Consumer-visible changes require updating here first | true |
| schema | Storage and data model | Must not change public behavior | true |
| implementation | Enforcement mechanics, hooks, validation | Describes how, not what | false |

**Example B** — CLI tool with user-facing commands:

| Cluster | Scope | Boundary Rule | Default Normative |
|---------|-------|---------------|-------------------|
| root | Overview, design philosophy | Changes here affect all clusters | varies |
| commands | Command definitions and argument parsing | User-facing changes require updating here first | true |
| config | Configuration file format and defaults | Must not change command behavior | true |
| output-formats | Structured output schemas (JSON, YAML, table) | Breaking changes require migration guide | true |

**Cluster manifest fields:**
- `name` (required): kebab-case identifier, becomes the subdirectory name
- `scope` (required): what content belongs here
- `boundary_rule` (recommended): when changes to this cluster require updating other clusters
- `default_normative` (optional): whether files in this cluster are binding by default
- `depends_on` (optional): which clusters this one references

### Step 3: Generate File Tree

Generate files conservatively — only create files with content to put in them.

**Always generate:**
- `README.md` — reading order table, authority model, document conventions
- `foundations.md` — system overview and key abstractions (root cluster)
- `decisions.md` — locked design decisions with sources (root cluster)

**Generate per cluster:** one overview file (e.g., `contracts/api-surface.md`, `commands/overview.md`). Additional files only when the user identifies distinct sub-concerns within a cluster.

**Do NOT generate:** `amendments.md` (track changes to a living spec — premature for new specs), `legacy-map.md` (from-monolith only), empty stub files.

### Output Conventions

Apply to both greenfield and from-monolith output.

**Frontmatter** — every file gets YAML frontmatter:

```yaml
---
module: <kebab-case-identifier>
status: active
normative: <true|false>
---
```

- `module` + `status`: always present
- `normative`: always present (explicit > inherited)
- `legacy_sections`: from-monolith mode only — never in greenfield
- `authority`: include when the spec defines an explicit authority model in README; omit otherwise

**Cross-references:** relative markdown links with semantic kebab-case anchors. Do NOT use section numbers as anchors — anchors must be semantic and stable across refactoring.

```markdown
See [merge rules](contracts/behavioral-semantics.md#merge-semantics)
```

**Reading order:** README.md contains a numbered reading-order table linking every file with a one-line description of what it covers.

---

## Mode: From Monolith

For splitting an existing document into a modular structure. The primary output is a **modularization plan** — a complete, self-contained implementation document that can be executed independently.

Do NOT begin creating spec files after generating the plan. Present the plan to the user and wait for explicit approval before execution.

### Step 1: Assess Source Document

Read the source document completely. Before building a mapping ledger, assess structural clarity:

| Signal | Present? |
|--------|----------|
| Consistent heading hierarchy (`##`, `###`) | |
| Section boundaries identifiable by headings or `---` separators | |
| Inline amendment history (italic revision notes under section headings) | |
| Cross-references between sections (by number, name, or link) | |
| Distinct authority clusters (different concerns, audiences, change cadences) | |

If the source lacks consistent heading hierarchy, recommend the user add minimal structure before proceeding. A document with no identifiable section boundaries produces unreliable mapping ledgers.

### Step 2: Build Mapping Ledger

The mapping ledger maps every source unit to its destination. This is the core planning artifact.

| Source Unit | Heading to Match | Destination File | Operation | Confidence | Rationale |
|------------|-----------------|-----------------|-----------|------------|-----------|
| S1: Overview | `## 1. System Overview` | foundations.md | move | high | Single concern, self-contained |
| S6.6: Design Notes | `### 6.6 Design Notes` | contracts/behavioral-semantics.md + schema/rationale.md | split | medium | Observable vs explanatory content |
| Amendment blocks | *(italic notes under S4, S7 headings)* | amendments.md | extract | high | Migration artifact — inline history consolidated |

**Column definitions:**
- `Source Unit`: section identifier and short name from the source document
- `Heading to Match`: the exact heading text to use for extraction boundary. Headings are stable; line numbers shift. Do NOT use line numbers as extraction boundaries.
- `Destination File`: target path relative to spec root
- `Operation`: `move` (intact to one destination), `split` (across multiple destinations), `merge` (multiple sources → one destination), `extract` (into a tracking/reference file — use for inline amendment histories, inline TODOs, and other non-content blocks)
- `Confidence`: `high` (clear single-concern section), `medium` (requires classification rule), `low` (ambiguous boundary or destination)
- `Rationale`: why this content belongs at this destination

**Amendment history handling:** When Step 1 detects inline amendment history (italic revision notes, changelog blocks embedded in section headers), map each block as an `extract` operation to `amendments.md`. The mapping ledger must account for every content block in the source — including non-section content like amendment notes.

**For split operations**, include a content classification table that maps individual paragraphs or subsections to their destinations with a stated classification rule. The classification rule is domain-specific — derive it from the user's content, not from templates.

**Example** (from a system with public API contracts vs internal storage):

```markdown
**Classification rule:** "If a client can observe it through the public API → contracts/.
If it explains internal implementation choices → rationale."

| Paragraph (match by bold lead or heading) | Destination | Rule Applied |
|-------------------------------------------|-------------|-------------|
| **ON DELETE policy** | rationale.md | Internal storage choice |
| **anchor_hash dedup and merge** | behavioral-semantics.md | Observable state-dependent branching |
```

**Present the mapping ledger to the user for confirmation before proceeding.**

### Step 3: Generate Task Breakdown

Structure the plan as numbered, checkboxed tasks organized into stages with explicit dependency tracking.

**Task structure:**

Each task specifies:
- Files created or modified
- Source section(s) and extraction method (heading-based)
- Frontmatter to apply (including `legacy_sections` mapping to source IDs)
- Heading changes (strip section numbers: `## 3. Design Decisions` → `## Design Decisions`)
- Semantic anchors to add
- Per-task validation checks
- Commit message

**Verbatim copy rule:** Content paragraphs are copied unchanged. Permitted structural transforms: frontmatter insertion, section-number removal from headings, heading level adjustment. Forbidden transforms: paraphrasing, summarizing, merging paragraphs, reordering content within a section.

**Example task:**

```markdown
### Task 2: Migrate foundations.md (S1 + S2)

**Files:** Create `foundations.md`
**Source:** S1 (`## 1. System Overview`) + S2 (`## 2. Skills, MCP Tools, and the Judgment Split`)

- [ ] **Step 1: Write foundations.md**
  - Extract from `## 1. System Overview` through end of S2 (delimited by next `##` heading)
  - Add frontmatter: module: foundations, legacy_sections: ["1", "2"], normative: true, status: active
  - Strip section numbers from headings
  - Content paragraphs copied verbatim — no prose changes
  - Do NOT update cross-references in this task — cross-reference rewriting happens in Stage 4

- [ ] **Step 2: Verify content preserved**
  - Verify S3 content ("Design Decisions") does NOT appear (boundary contamination check)
  - Compare word count: destination ≥ source (frontmatter/anchors add words)

- [ ] **Step 3: Commit**
  `git commit -m "docs(<name>): migrate S1+S2 to foundations.md"`
```

**Staged execution model:**

Organize tasks into stages with gate conditions. Tasks within a stage can run in parallel; stages are sequential.

| Stage | Tasks | Gate Condition |
|-------|-------|---------------|
| 0 | Scaffold (directories + README) | Directory structure exists |
| 1 | All clean `move` operations (independent after scaffold) | All files created |
| 2 | `split` operations (depend on destination files from Stage 1 existing) | Split targets exist |
| 3 | Conditional migration artifacts: `amendments.md` (only if Step 1 detected inline amendment history), `legacy-map.md` (only if source uses section identifiers that readers need to resolve) | All content tasks complete |
| 4 | Validate all content preserved → cross-reference update → remove source → final structural validation | Sequential chain |

Stage 4 ordering is critical: validate content preservation BEFORE removing the source document. Source removal is the last destructive operation.

If using subagent-driven-development, include a subagent assignment table mapping agents to task groups with explicit within-agent sequential dependencies noted.

### Step 4: Cross-Reference Disambiguation Table

Section-number references in the source document need context-sensitive replacement. The same reference (e.g., "Section 4") may map to different anchors depending on surrounding text.

Include a disambiguation table in the plan:

| Pattern | Default Target | Disambiguation |
|---------|---------------|----------------|
| `Section 4` / `S4` | `contracts/tool-surface.md` | Near "bootstrap" → `#session-bootstrap`. Near "action semantics" → `#action-semantics`. Otherwise → file-level link. |
| `Section 6.6` / `S6.6` | `contracts/behavioral-semantics.md` | Near "anchor_hash" → `#anchor-hash-merge`. Near "atomicity" → `#session-end-atomicity`. Otherwise → file-level link. |

The cross-reference update is its own task (Stage 4), not inline during content migration. This prevents double-update conflicts and allows a single verification pass.

### Step 5: Validation Specification

The plan's final task is a multi-layered validation. Include these checks:

**Content preservation** (run BEFORE source removal):
- Every source section appears in exactly one destination file
- Word count: sum of destinations ≥ source (frontmatter/anchors add words)
- Sentinel check: key terms from each source section grep-match in at least one destination

**Boundary contamination:**
- For each destination file, verify content from adjacent source sections did NOT leak in

**Structural integrity** (run after source removal):
- All files present (expected count from mapping ledger)
- Every file starts with valid YAML frontmatter
- All relative markdown links resolve to existing files

**Reference integrity:**
- Zero stale section-number references (excluding legacy-map.md and amendments.md)
- All fragment anchors (`#anchor-name`) resolve to headings in target files

Include concrete validation scripts in the plan (bash one-liners or short scripts).

---

## Internal Vocabulary

These terms guide file classification within the skill. They are NOT persisted as frontmatter.

| Kind | Purpose | Example |
|------|---------|---------|
| `index` | Entry point and reading order | README.md |
| `foundations` | System overview and key abstractions | foundations.md |
| `decision` | Locked design decisions | decisions.md |
| `contract` | Public behavioral guarantees | contracts/api-surface.md |
| `rationale` | Reasoning behind structural choices | schema/rationale.md |
| `appendix` | Supplementary reference material | skills/appendix.md |
| `implementation` | Enforcement mechanics | implementation/hooks.md |
| `amendment` | Change tracking (from-monolith) | amendments.md |
| `legacy-map` | Section mapping (from-monolith) | legacy-map.md |

---

## Failure Modes

| Condition | Action |
|-----------|--------|
| Source document has no identifiable heading hierarchy | STOP. Recommend user add minimal heading structure before invoking this skill. |
| Source document is <300 lines with no distinct authority boundaries | Redirect to single-file mode. Do not generate a modularization plan. |
| User rejects the cluster manifest or mapping ledger | Revise based on feedback. Do not proceed without explicit approval. |
| Split operation has no stated classification rule | STOP. Ask the user: "What distinguishes content that belongs in [destination A] from content in [destination B]?" |
| Mapping ledger has unaccounted source content (sections not mapped) | STOP. Every content block must appear in exactly one ledger row. |
| Validation detects content loss after migration | STOP. Report which source sections are missing and in which destination files. Do not remove the source document. |

## What NOT to Do

- Do NOT create spec files, directories, or modify the source document unless the user explicitly requests plan execution. The plan is the output.
- Do NOT assume engram's directory structure. Derive clusters from the user's domain — the engram split used contracts/schema/skills/implementation because of engram-specific ownership boundaries, not because those are universal categories.
- Do NOT skip the user confirmation gate on the cluster manifest or mapping ledger.
- Do NOT persist the `kind` vocabulary as frontmatter. Internal planning vocabulary only.
- Do NOT auto-generate `amendments.md` in greenfield mode. It is a from-monolith artifact.
- Do NOT use section numbers as cross-reference anchors. Use semantic kebab-case.
- Do NOT use line numbers as extraction boundaries. Use heading-based extraction — headings are stable, line numbers shift as the source evolves.
- Do NOT rewrite prose during migration. Content paragraphs are copied verbatim. Permitted structural transforms: frontmatter insertion, section-number removal from headings, heading level adjustment.
- Do NOT inline cross-reference updates during content migration tasks. Cross-reference updating is a dedicated Stage 4 task with its own disambiguation table and verification pass.
- Do NOT remove the source document before running content preservation validation. Validate first, remove second.

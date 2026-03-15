# spec-review-team Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the spec-review-team skill — a parallel agent team that reviews multi-file specifications for structural and semantic defects, with lateral messaging between reviewers for real-time corroboration.

**Architecture:** Normative SKILL.md (~400-470 lines) with 4 operational reference files. SKILL.md defines the 6-phase procedure, phase gates, spawn/completion/cleanup contracts, finding schema, and audit metrics. Reference files handle detailed taxonomies (clusters, signals), domain briefs (reviewer roles), synthesis examples, and troubleshooting. One reference file (`agent-teams-platform.md`) already exists and must not be modified.

**Tech Stack:** Markdown instruction documents for Claude Code. Agent teams platform (TeamCreate, SendMessage, TaskCreate, Agent tool with `team_name`). No code — all files are `.md`.

**Spec:** `docs/superpowers/specs/2026-03-14-spec-review-team-design.md`

**Reference implementations:**
- `explore-repo` SKILL.md (259 lines) — agent team skill pattern, teammate spawn prompts
- `reviewing-designs` SKILL.md (576 lines) — A' architecture with reference files
- `spec-modulator` SKILL.md (324 lines) — lifecycle partner, shared frontmatter conventions

**Writing conventions:**
- Follow `docs/references/writing-principles.md` — these are instruction documents for Claude
- Active prohibitions for things Claude should NOT do ("Do NOT fall back", not "omit fallback")
- Front-load critical information (commands before context)
- Concrete values, not vague language ("5 minutes", not "reasonable timeout")
- Match patterns observed in reference implementations, not training data conventions

---

## File Structure

```
.claude/skills/spec-review-team/
├── SKILL.md                          # Create: normative procedure
└── references/
    ├── agent-teams-platform.md       # EXISTS — do NOT modify
    ├── preflight-taxonomy.md         # Create: cluster definitions, signal dimensions, scoring
    ├── role-rubrics.md               # Create: per-role domain briefs, collaboration playbooks
    ├── synthesis-guidance.md         # Create: worked examples, edge cases, exemplar ledgers
    └── failure-patterns.md           # Create: degraded modes, troubleshooting, recovery
```

| File | Responsibility | Line target |
|------|---------------|-------------|
| SKILL.md | Procedure flow, phase gates, contracts, finding schema, audit metrics, upgrade triggers | 400-470 |
| preflight-taxonomy.md | 6 canonical clusters, 5 signal dimensions, scoring weights, sampling policy | 130-170 |
| role-rubrics.md | Shared scaffold template, 6 reviewer domain briefs (8 components each) | 220-280 |
| synthesis-guidance.md | Worked consolidation/corroboration/contradiction examples, anti-patterns, exemplar ledger | 170-220 |
| failure-patterns.md | Degraded mode details, troubleshooting trees, recovery procedures | 100-140 |

**Content distribution principle:** SKILL.md owns normative rules (the WHAT and WHEN). Reference files own operational detail (the HOW, with examples). An implementer reading only SKILL.md should understand the complete procedure. Reference files make execution better, not possible.

---

## Chunk 1: SKILL.md

### Task 1: Frontmatter + Opening Sections

**Files:**
- Create: `.claude/skills/spec-review-team/SKILL.md`

- [ ] **Step 1: Write YAML frontmatter**

Use the exact frontmatter from spec lines 29-61. This is the verbatim content:

```yaml
---
name: spec-review-team
description: >
  Review multi-file specifications using a parallel agent team with lateral
  messaging — reviewers communicate directly to share findings, challenge
  analyses, and corroborate across defect-class lenses in real time. Discovers
  spec structure via frontmatter metadata, runs preflight analysis, spawns 4-6
  specialized reviewers, and synthesizes findings into a prioritized report.
  Reviewers use two messaging primitives: `message` (targeted to one reviewer)
  and `broadcast` (all reviewers simultaneously). Broadcast costs scale linearly
  with team size since each message lands in every recipient's context window.
  Messages are informal coordination signals — each reviewer's structured
  findings file remains the sole formal deliverable. Use when reviewing a spec
  corpus with files across multiple authority tiers. For single design documents,
  use reviewing-designs instead.
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - ToolSearch
  - TeamCreate
  - TeamDelete
  - SendMessage
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
---
```

**Critical:** The `allowed-tools` list is a hard allowlist. Wrong or missing names = tools unavailable to the skill. Every tool the skill needs must be listed here. These names come from the spec and the platform reference (`references/agent-teams-platform.md`).

- [ ] **Step 2: Write title + purpose + announce**

```markdown
# Spec Review Team

Review multi-file specifications for structural and semantic defects using a parallel agent team with lateral messaging.

**Announce at start:** "I'm using the spec-review-team skill to review this specification."
```

- [ ] **Step 3: Write When to Use / When NOT to Use**

**When to Use:**
- Multi-file specifications with frontmatter metadata (`module`, `status`, `normative`, `authority` fields)
- Specs created by `spec-modulator` or following the same conventions
- Reviews requiring cross-file invariant analysis and multi-lens defect detection
- Include trigger phrases from spec line 63: "review this spec", "spec review", "review all spec files", "thorough spec review", "review specification"

**When NOT to Use** (active prohibitions — spec lines 15-16):
- Single design documents → use `reviewing-designs`
- Code review, implementation review
- Specs without frontmatter metadata
- Note: specs with few files but multiple authority tiers DO need this skill (the redirect gate handles this)

- [ ] **Step 4: Write Prerequisites section**

This is Phase 0 from the spec. Write it as a hard gate:

```markdown
## Prerequisites

**YOU MUST** verify agent teams are enabled before any other work:

Check for `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential review — parallel multi-lens review is the skill's value proposition.
```

- [ ] **Step 5: Write Constraints section**

Write the 6 constraints as a table (spec lines 67-72). These are hard rules, not guidelines.

| # | Constraint | Detail |
|---|-----------|--------|
| 1 | Agent teams experimental | Hard prerequisite. Do not fall back. |
| 2 | ~500-line SKILL.md | Operational content in reference files |
| 3 | Teammates load project context | CLAUDE.md, MCP, skills auto-load. Lead history does NOT carry over. Preflight packet is the authoritative source for spec structure. |
| 4 | One team per session | No nested teams. No session resumption. |
| 5 | 3-5 teammates recommended | Core 4 + up to 2 optional specialists. Max 6. |
| 6 | Sonnet for reviewers | Lead uses session's default model. |

- [ ] **Step 6: Commit frontmatter + opening**

```bash
git add .claude/skills/spec-review-team/SKILL.md
git commit -m "feat(spec-review-team): SKILL.md frontmatter + opening sections"
```

### Task 2: Phases 1-2 (DISCOVERY + ROUTING)

**Files:**
- Modify: `.claude/skills/spec-review-team/SKILL.md`

- [ ] **Step 1: Write Phase 1: DISCOVERY**

Write the `## Procedure` header, then `### Phase 1: DISCOVERY`.

Phase gate: "Authority map built with ≥1 normative file, or degraded mode entered."

Procedure (from spec lines 111, 184-203):
1. Locate spec directory — user provides path, or search for specs with frontmatter
2. Read all markdown files. Parse YAML frontmatter for: `module`, `status`, `normative`, `authority`, `legacy_sections`
3. Build authority map: file → normative (true/false) + source authority + review cluster
   - Source authority = frontmatter `authority` field (preserved as-is). If absent: `unknown`
   - Review cluster = derived from source authority + `module` + path heuristics. Reference `preflight-taxonomy.md` for the 6 canonical clusters and classification rules
4. Degraded mode entry: if zero files have parseable frontmatter, classify by path heuristics, warn user. See Failure Modes table.
5. Partial coverage (some files with frontmatter, some without) is normal operation — not degraded mode

Keep this section ~25 lines. Defer cluster definitions and classification rules to `preflight-taxonomy.md`.

- [ ] **Step 2: Write Phase 2: ROUTING**

Phase gate: "Pass redirect gate, or redirect to `reviewing-designs`."

Write the redirect gate evaluation as a table (from spec lines 209-216):

| Condition | Threshold | Required for redirect |
|-----------|-----------|----------------------|
| `confident_review_cluster_count` | ≤ 2 | Yes |
| `boundary_edges` | ≤ 2 | Yes |
| Specialist triggers | None firing | Yes |
| Ambiguous cluster assignments | Any present | **Disables redirect** |

All conditions must be met for redirect. Add the key insight from spec line 218: "A 3-file spec spanning 3 authority tiers needs full team review; a 10-file spec in one tier does not. File count is not a gate condition."

If redirecting: tell user why, invoke `reviewing-designs`.

Keep this section ~20 lines.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/spec-review-team/SKILL.md
git commit -m "feat(spec-review-team): phases 1-2 (DISCOVERY + ROUTING)"
```

### Task 3: Phase 3 (PREFLIGHT)

**Files:**
- Modify: `.claude/skills/spec-review-team/SKILL.md`

- [ ] **Step 1: Write Phase 3A: Mechanical**

Phase gate: "All files checked; frontmatter parseable on all files, or degraded mode entered."

Steps (from spec lines 113, 393):
1. Validate frontmatter on all spec files (required fields present, values well-formed)
2. Check cross-references (every relative markdown link resolves to existing file + anchor)
3. Detect broken links, orphaned anchors, missing referenced files
4. Record results for preflight packet's `mechanical_checks` section

~10 lines.

- [ ] **Step 2: Write Phase 3B: Staffing**

Phase gate: "Spawn plan finalized (which reviewers, why)."

Steps (from spec lines 114, 222-232):
1. Core team (4 reviewers) always spawns. Role definitions in `references/role-rubrics.md`.
2. Evaluate optional specialist signals using two-tiered spawn rule from `references/preflight-taxonomy.md`:
   - Tier 1 (score ≥ 100): single high-confidence signal sufficient
   - Tier 2 (score 50-99): requires 2+ medium signals from different dimensions
3. If metadata insufficient: sample targeted content excerpts per sampling policy in `preflight-taxonomy.md`. Do NOT expand into broad corpus reading.
4. Budget exhausted + below threshold: do NOT spawn specialist. Log unresolved signal for synthesis report.
5. Record spawn plan.

~15 lines.

- [ ] **Step 3: Write Phase 3C: Materialize**

Phase gate: "`packet.md` written, spawn plan announced to user."

Steps (from spec lines 115, 382-395, 417):
1. Verify `.review-workspace/` is in `.gitignore`. If absent, add it.
2. Create `.review-workspace/preflight/packet.md` with 6 sections: `authority_map`, `boundary_edges`, `signal_matrix`, `mechanical_checks`, `route_decision`, `spawn_plan`
3. Announce spawn plan: "Spawning [N] reviewers: [role IDs]. [Optional specialists]: [reason or 'not triggered']."

~10 lines.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/spec-review-team/SKILL.md
git commit -m "feat(spec-review-team): phase 3 (PREFLIGHT — mechanical, staffing, materialize)"
```

### Task 4: Phase 4 (REVIEW)

**Files:**
- Modify: `.claude/skills/spec-review-team/SKILL.md`

This is the largest section. Write it as 5 subsections: spawn contract, completion contract, lateral messaging, task scope, and cleanup contract. Target ~80-90 lines total.

- [ ] **Step 1: Write Phase 4 header + Spawn Contract**

Phase gate: "All expected findings files present, or timeout reached."

First, write the three-artifacts table (spec lines 124-130) as the Phase 4 preamble — these define the immutability rules that govern the entire review:

| Artifact | Created | Consumed | Mutability |
|----------|---------|----------|------------|
| Authority map | Phase 1 (DISCOVERY) | Phases 2-5 | Immutable after Phase 1 |
| Spawn plan | Phase 3B (Staffing) | Phase 4 (REVIEW) | Immutable after 3B |
| Findings ledger | Phase 4 (REVIEW) | Phase 5 (SYNTHESIS) | Append-only during Phase 4; read-only in Phase 5 |

Then write the spawn contract (from spec lines 132-138) — 6 numbered steps:
1. Write preflight `packet.md` (if not done in 3C)
2. Create team via `TeamCreate` with descriptive `team_name` (e.g., `"spec-review"`). Note: if `TeamCreate` is a deferred tool, fetch via `ToolSearch` first
3. Create one task per reviewer via `TaskCreate` — include role ID, output file path, `packet.md` path
4. Spawn each reviewer via `Agent` with `team_name`, `name` (role ID), `model: "sonnet"`, `prompt` (scaffold + preflight pointer + role delta from `role-rubrics.md`). The `team_name` parameter makes it a teammate with messaging/tasks/idle notifications. Without `team_name`, it's an isolated subagent.
5. Addressing convention: `name` = addressing key for ALL communication. Use role IDs, never UUIDs.
6. Do NOT start lead's analysis before all teammates spawned.

~25 lines.

- [ ] **Step 2: Write Completion Contract**

From spec lines 140-145:
- Primary signal: idle notifications from the team system
- **Peer DM visibility:** when a reviewer sends a DM to another reviewer, a brief summary appears in the sender's idle notification. This gives the lead visibility into cross-reviewer collaboration without polling — and is a key input for synthesis (assessing whether findings are causally linked).
- Hard deliverable: findings files in `.review-workspace/findings/{role-id}.md`
- Completion check: verify each expected file exists after all idles received
- Wall-clock timeout: 5 minutes, no new idle notifications or task status changes. Define "activity" explicitly: idle notification received, or task moving to `completed` via `TaskGet`. Lateral messages are NOT independently observable — they surface only as DM summaries in the next idle notification.
- Partial completion: always proceed with available findings, report `reviewers_failed` with per-reviewer reasons

~18 lines.

- [ ] **Step 3: Write Lateral Messaging + Task Scope**

Lateral messaging (spec lines 146-149):
- Two primitives: `message` (targeted `SendMessage` to `"{name}"`) and `broadcast` (`to: "*"`, all teammates, costs scale linearly)
- Spawn prompts instruct: message other reviewers when you find cross-lens findings
- Messages are informal signals; findings files are the formal deliverable

Task scope (spec lines 151-153):
- One task per reviewer, no `blockedBy` dependencies — all parallel
- Do NOT self-claim additional tasks after finishing. Go idle if done early.
- Known limitation: task status can lag. Idle notifications primary, task status secondary.

~15 lines.

- [ ] **Step 4: Write Quality Gate Hooks + Cleanup Contract**

Quality gate hooks (spec lines 155-161) — optional for v1:
- `TeammateIdle`: fires on idle. Exit code 2 = feedback + continue. **Command hooks ONLY.**
- `TaskCompleted`: fires on task completion. All four hook types supported.
- Neither supports matchers. Filter by role inside hook logic.
- Note: these become valuable once quality predicates are reliable. Not for v1.

Cleanup contract (spec lines 163-167):
1. Shut down each reviewer via `SendMessage` with `{type: "shutdown_request", reason: "Review complete"}`
2. If rejected, retry with additional context. Shutdown may be slow (current tool call finishes first).
3. After all shut down: `TeamDelete`. Fails if any active. Teammates must NOT self-cleanup.
4. Ask user: preserve or remove `.review-workspace/`? Default: preserve.

~20 lines.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/spec-review-team/SKILL.md
git commit -m "feat(spec-review-team): phase 4 (REVIEW — spawn, completion, messaging, cleanup)"
```

### Task 5: Phases 5-6 (SYNTHESIS + PRESENT)

**Files:**
- Modify: `.claude/skills/spec-review-team/SKILL.md`

- [ ] **Step 1: Write Phase 5: SYNTHESIS — instruction philosophy + mechanical passes**

Phase gate: "Report written with all 10 audit metrics."

Open with the instruction philosophy (spec lines 274-277): "Technique-in-Discipline-shell. Prescribe computation for auditable state; prescribe criteria for meaning."

Then write the synthesis inputs table (spec lines 279-289) — the lead has 5 named sources:

| Source | Content | How to use |
|--------|---------|------------|
| Findings files | Structured findings per reviewer | Primary input — formal deliverables |
| Coverage notes | Scope checked, checks run, caveats, deferrals | Verify completeness; check deferral chains |
| DM summaries | Brief summaries of peer messages in idle notifications | Assess causal links between findings |
| Authority map | File → normative/non-normative + source authority | Inform adjudication (normative > non-normative) |
| Preflight packet | Spec structure, boundary edges, signal matrix | Context for finding distribution |

**Mechanical passes** (spec lines 293-299) — 5 steps, prescribed:
1. Canonicalize — normalize format, fix schema violations, increment `normalization_rewrites`
2. Build synthesis ledger at `.review-workspace/synthesis/ledger.md` — one record per canonical finding
3. Verify deferrals — check `deferred_to` coverage notes; unverified → meta-findings (P1, prefix `SY`)
4. Compute all 10 audit metrics
5. Ensure required report sections: prioritized findings, corroboration evidence, contradiction resolutions, metrics, coverage summary

~20 lines.

- [ ] **Step 2: Write SYNTHESIS — judgment obligations**

From spec lines 301-325. Write as 4 obligations, each with ledger field:

**Consolidate and deduplicate.** `violated_invariant` + `affected_surface` as minimum signal, plus semantic judgment. Merged findings list all contributor IDs.
- Ledger: `merge_rationale`

**Assess corroboration.** Classify support_type:
- `independent_convergence` (both `provenance: independent`)
- `cross_lens_followup_confirmation` (one flagged, another confirmed via `followup`)
- `related_pattern_extension` (distinct findings at same surface, larger pattern)
- `singleton` (single-lens, no corroboration)
- Ledger: `support_type`, `contributors`

**Resolve contradictions.** Use authority map (normative > non-normative), evidence quality, domain reasoning. Unresolvable → escalate as ambiguity finding (P1, `SY` prefix).
- Ledger: `adjudication_rationale`

**Prioritize.** P0 > P1 > P2 baseline, corroboration + confidence secondary.
- Ledger: `priority_rationale` (required only when ranking departs from baseline)

Reference `synthesis-guidance.md` for worked examples and edge cases.

~25 lines.

- [ ] **Step 3: Write SYNTHESIS — ledger format + invariants**

Ledger format (spec lines 329-346) — include the template:

```markdown
### [SY-N] Canonical finding title

- **source_findings:** AA-1, CE-3
- **support_type:** independent_convergence
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "..."
- **adjudication_rationale:** (if applicable)
- **priority_rationale:** (if non-obvious)
```

5 machine-checkable invariants (spec lines 342-347):
1. Every `source_findings` ID traces to a reviewer's findings file
2. Every `contributors` entry matches a spawned reviewer's role ID
3. No contradiction silently dropped (resolved → `adjudication_rationale`; unresolved → `SY` finding)
4. Every `support_type` consistent with provenance chain
5. Every report finding has a ledger record

~20 lines.

- [ ] **Step 4: Write Phase 6: PRESENT**

From spec line 118. Report goes to `.review-workspace/synthesis/report.md`.

Required sections:
1. Summary — finding counts by priority, team composition, coverage assessment
2. Prioritized findings — ordered by impact, corroboration evidence inline
3. Corroboration table — which findings converged, confirmed, extended
4. Contradiction resolutions — how disagreements resolved or escalated
5. Audit metrics — all 10
6. Coverage summary — what checked, what not, why

After presenting: invoke the Phase 4 cleanup contract (shutdown teammates → TeamDelete → workspace prompt). Cleanup is a return to Phase 4's cleanup section, not a Phase 6 sub-procedure.

~15 lines.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/spec-review-team/SKILL.md
git commit -m "feat(spec-review-team): phases 5-6 (SYNTHESIS + PRESENT)"
```

### Task 6: Finding Schema + Metrics + Failure Modes + Validation

**Files:**
- Modify: `.claude/skills/spec-review-team/SKILL.md`

- [ ] **Step 1: Write Finding Schema section**

From spec lines 238-257. Include the exact schema template:

```markdown
## [PREFIX-N] Title

- **priority:** P0 / P1 / P2
- **title:** One-sentence description
- **violated_invariant:** source_doc#anchor
- **affected_surface:** file + section/lines
- **impact:** 1-2 sentences
- **evidence:** what doc says vs what it should say
- **recommended_fix:** specific action
- **confidence:** high / medium / low
- **provenance:** independent / followup
- **prompted_by:** {reviewer-name} (required when followup; omit when independent)
```

Include finding ID prefix table: AA, CE, CC, VR, SP, IE.

Include the provenance explanation: reviewers tag what they know (independent vs followup). The lead interprets during synthesis. Reviewer does NOT assess corroboration quality.

~25 lines.

- [ ] **Step 2: Write Coverage Notes section**

From spec lines 259-269. Mandatory for core reviewers with zero findings.

| Field | Purpose |
|-------|---------|
| `scope_checked` | Files/sections examined |
| `checks_run` | Specific checks performed |
| `result` | "No defects found" + rationale |
| `caveats` | Limitations |
| `deferred_to` | If another reviewer better positioned |

~10 lines.

- [ ] **Step 3: Write Failure Modes table**

From spec lines 448-460. Write as a table with 9 rows. Keep entries concise — reference `failure-patterns.md` for detailed troubleshooting.

| Failure | Detection | Response |
|---------|-----------|----------|
| No frontmatter | DISCOVERY: 0 normative files | Degraded mode. Phase 3A zero results. See `failure-patterns.md` |
| >50% ambiguous clusters | ROUTING computation | All-core team, flag ambiguity as meta-finding |
| Prose output | SYNTHESIS normalization | Normalize, increment `normalization_rewrites` |
| Agent teams not enabled | Prerequisite check | Hard stop |
| Missing findings file | REVIEW verification | Log in `reviewers_failed` |
| Teammate timeout | No activity 5 min | Treat as failed, proceed to SYNTHESIS |
| TeamCreate fails | Phase 4 step 2 | Hard stop |
| Spawn fails | Phase 4 step 4 | Log, continue. All fail = hard stop |
| Stale workspace | Next DISCOVERY | Warn, offer: archive / remove / abort |

~15 lines.

- [ ] **Step 4: Write Audit Metrics table + Upgrade Triggers + References**

Audit metrics (spec lines 357-368) — 10-row table:

| # | Metric | Description |
|---|--------|-------------|
| 1 | `raw_finding_count` | Total before canonicalization |
| 2 | `canonical_finding_count` | After consolidation/dedup |
| 3 | `duplicate_clusters_merged` | Consolidation merges |
| 4 | `related_finding_clusters` | `support_type: related_pattern_extension` findings |
| 5 | `corroborated_findings` | `independent_convergence` or `cross_lens_followup_confirmation` |
| 6 | `contradictions_surfaced` | Resolved + escalated |
| 7 | `normalization_rewrites` | Schema repairs |
| 8 | `ambiguous_review_clusters` | Uncertain cluster assignments |
| 9 | `reviewers_failed` | Per-reviewer ID + reason |
| 10 | `unverified_deferrals` | Deferrals not covered by target |

Upgrade triggers — write as a table (preserving the per-trigger thresholds from spec lines 372-380). 5 rows: normalization rate (≥15%), cross-run determinism (≥2/5), cross-run inconsistency, synthesis duration (>3 min), P0 missed. Note: post-v1 calibration only. Record raw data during v1 runs; evaluate after 8+ runs. Do not implement trigger logic in v1.

References table — list all 5 reference files with brief descriptions.

~25 lines.

- [ ] **Step 5: Validate SKILL.md line count**

Run: `wc -l .claude/skills/spec-review-team/SKILL.md`

Expected: 400-470 lines. If over 500, identify sections to trim or delegate to reference files. If under 350, check if any normative content was accidentally omitted.

- [ ] **Step 6: Validate frontmatter**

Run: `head -35 .claude/skills/spec-review-team/SKILL.md | grep -c "^---$"`

Expected: 2 (opening and closing `---` delimiters).

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/spec-review-team/SKILL.md
git commit -m "feat(spec-review-team): finding schema, metrics, failure modes, references"
```

---

## Chunk 2: Reference Files

These 4 files are independent of each other and can be implemented in parallel. Each file must be self-contained — readable and useful without the others.

### Task 7: preflight-taxonomy.md

**Files:**
- Create: `.claude/skills/spec-review-team/references/preflight-taxonomy.md`

- [ ] **Step 1: Write header + cluster definitions**

Title: "Preflight Taxonomy Reference"

Write the 6 canonical review clusters from spec lines 184-194. Each cluster needs:
- Name (exact ID used in authority map)
- Description (what belongs here)
- Example files
- Typical source authorities that map to this cluster

```markdown
# Preflight Taxonomy Reference

Operational reference for the preflight analysis phases (3A-3C). Defines the cluster taxonomy, signal dimensions, scoring weights, and sampling policy.

## 6 Canonical Review Clusters

| Cluster | Description | Examples | Typical source authorities |
|---------|-------------|---------|---------------------------|
| `root` | Top-level architectural and foundational docs | foundations.md, decisions.md, README.md | foundation, decisions |
| `contracts` | Behavioral contracts and interface definitions | tool-surface.md, behavioral-semantics.md | behavioral, interface |
| `schema` | Data model, DDL, persistence definitions | ddl.md, schema rationale | schema |
| `control_surface` | Hooks, plugins, enforcement, skill catalog | skills/overview.md, skills/catalog.md | control, enforcement |
| `implementation` | Implementation plans, strategies, migration | testing-strategy.md, server-validation.md | implementation |
| `supporting` | Appendix, glossary, legacy maps, amendments | appendix.md, legacy-map.md | supporting, legacy |
```

Then write the two-layer cluster model explanation (spec lines 196-203):
- **Source authority** — original `authority` frontmatter (preserved as-is). Used for adjudication.
- **Review cluster** — derived from source authority + `module` + path heuristics. Lossy mapping. Used for routing, staffing, rubric selection only.

Include missing metadata handling rules:
- No frontmatter at all: source authority = `unknown`, cluster by path heuristics, flagged ambiguous
- Frontmatter but no `authority` field: source authority = `unknown`, cluster from `module` + path (common case — spec-modulator only adds `authority` for explicit authority models)
- Zero parseable frontmatter = degraded mode. Partial coverage = normal.

- [ ] **Step 2: Write signal dimensions + scoring**

5 signal dimensions for optional specialist spawning (spec lines 228-229):

| Dimension | Type | Example signal | Cost |
|-----------|------|---------------|------|
| Frontmatter authority | Metadata-derived | `authority: schema` on any file | Free (Phase 1) |
| File naming | Metadata-derived | File named `ddl.md`, `schema-*.md` | Free (Phase 1) |
| Cluster membership | Metadata-derived | File classified in `schema` cluster | Free (Phase 2) |
| Content keywords | Content inspection | Schema-related terms in file body | Budgeted sampling |
| Cross-reference patterns | Content inspection | Contracts referencing schema files | Budgeted sampling |

Write the two-tiered spawn rule:
- **Tier 1 (score ≥ 100):** Single high-confidence signal. Example: `authority: schema` frontmatter → spawn Schema/Persistence specialist immediately.
- **Tier 2 (score 50-99):** 2+ medium signals from different dimensions. Example: `ddl.md` filename (75) alone insufficient; + schema cross-refs from contracts (60) → spawn.

Include scoring weights. These are implementation guidance (calibrate after first runs):
- Tier 1 signals (≥100): frontmatter `authority` exact match
- Medium signals (50-99): filename pattern match, cluster membership
- Weak signals (25-49): content keywords, single cross-reference

- [ ] **Step 3: Write sampling policy**

From spec lines 230-232. This is the most constrained part — must be precise.

Define:
- **Unit of inspection:** targeted file excerpt (not full file read)
- **Budget:** maximum N file excerpts (suggest 5-8, calibrate after runs)
- **Scaling:** budget does NOT scale with spec size. Fixed cap.
- **What triggers sampling:** metadata signals insufficient to decide optional specialist spawn
- **What sampling checks:** content keywords, cross-reference patterns (the two content-inspection dimensions)
- **Budget exhaustion rule:** if budget spent and confidence below Tier 2 threshold, do NOT spawn specialist. Core reviewers cover all defect classes — specialists augment, they don't replace. Log unresolved signal.

Active prohibition: "Sampling is budgeted detection, NOT review. The lead MUST NOT expand sampling into broad corpus reading. If you find yourself reading more than targeted excerpts, stop — you are exceeding the sampling budget."

- [ ] **Step 4: Validate and commit**

Run: `wc -l .claude/skills/spec-review-team/references/preflight-taxonomy.md`

Expected: 130-170 lines.

```bash
git add .claude/skills/spec-review-team/references/preflight-taxonomy.md
git commit -m "feat(spec-review-team): preflight-taxonomy.md — clusters, signals, scoring, sampling"
```

### Task 8: role-rubrics.md

**Files:**
- Create: `.claude/skills/spec-review-team/references/role-rubrics.md`

This is the largest reference file. Contains the shared spawn scaffold and 6 reviewer domain briefs.

- [ ] **Step 1: Write header + shared scaffold template**

The shared scaffold (spec lines 423-426) is the common prefix for all spawn prompts. It contains:
- Finding schema definition (same as SKILL.md's Finding Schema section)
- Workspace path (`.review-workspace/`)
- Output file path (`.review-workspace/findings/{role-id}.md`)
- Path to preflight packet (`.review-workspace/preflight/packet.md`)
- Output rules: "No prose between findings. Every finding must use the schema. Mandatory coverage notes for zero-finding defect classes."
- Provenance requirement: "Tag each finding `provenance: independent` or `provenance: followup`. If followup, include `prompted_by: {reviewer-name}`."
- Collaboration instruction: "If you discover something in another reviewer's defect class, message that reviewer directly via `SendMessage`. You can discover team members via the team config's `members` array."

Write this as a template with `{role-id}`, `{mission}`, `{defect-class}` placeholders.

```markdown
# Role Rubrics Reference

Operational reference for reviewer spawn prompts. Contains the shared scaffold (common to all reviewers) and per-role domain briefs (8 components each).

## Shared Scaffold

Every spawn prompt starts with this scaffold. Replace `{placeholders}` with role-specific values.

> You are `{role-id}`, reviewing a multi-file specification for `{defect-class}` defects.
>
> **Your output file:** `.review-workspace/findings/{role-id}.md`
> **Preflight packet:** Read `.review-workspace/preflight/packet.md` for spec structure, authority map, and boundary edges.
>
> **Finding format:** [include full schema from SKILL.md]
>
> **Rules:**
> - No prose between findings. Every finding uses the schema exactly.
> - Tag provenance: `independent` (you found it yourself) or `followup` (prompted by a lateral message). If followup, include `prompted_by: {reviewer-name}`.
> - Mandatory coverage notes for any defect class where you find zero defects.
> - Attempt to disconfirm each material finding before reporting: could this be intentional? Check the decisions log.
> - If you discover something in another reviewer's domain, message them directly.
>
> **Your mission:** {mission}
```

- [ ] **Step 2: Write core reviewer domain briefs (Authority & Architecture, Contracts & Enforcement)**

Each domain brief has 8 components (spec lines 433-444). Write two briefs:

**Authority & Architecture (`authority-architecture`):**
1. Mission: "Find defects where the spec's authority hierarchy is violated, misplaced, or internally inconsistent"
2. High-yield surfaces: boundary edges between normative and non-normative files. Files with `authority` changes across versions. README authority model vs actual file structure.
3. Common defect patterns: invariant drift (normative constraint evolves without source update), authority misplacement (binding decision in non-normative file), architectural constraint violations
4. Priority calibration: P0 = implementer builds wrong thing due to authority confusion. P1 = authority metadata inaccurate but content consistent. P2 = metadata imprecise but harmless.
5. Collaboration playbook: "If you find authority misplacement, message `contracts-enforcement` — they should check if contracts reference the misplaced authority. If you find architectural constraint violations, message `completeness-coherence` for cross-reference impact."
6. Coverage floor: every normative file in the authority map must be checked
7. Disconfirmation: "Before reporting an authority violation, check the decisions log for rationale"
8. Output examples: 1-2 exemplar findings showing schema compliance

**Contracts & Enforcement (`contracts-enforcement`):**
1. Mission: "Find defects where implementation promises diverge from behavioral contracts, or where enforcement mechanisms have gaps"
2. High-yield surfaces: behavioral contract files, enforcement mechanism definitions, hook configurations
3. Common defects: behavioral drift (contract says X, implementation section says Y), unauthorized implementation decisions (implementation makes binding choices not backed by contracts), enforcement gaps (contract promises something with no enforcement path)
4. Priority calibration: P0 = contract violation would cause incorrect system behavior. P1 = contract underspecified, implementer must guess. P2 = enforcement gap exists but risk is low.
5. Collaboration: "If you find a contract gap that affects the authority hierarchy, message `authority-architecture`. If you find enforcement gaps in hooks or plugins, message `integration-enforcement` (if spawned)."
6. Coverage floor: every contract file and every file referencing contracts
7. Disconfirmation: "Check if the 'drift' is an intentional evolution documented in decisions or amendments"
8. Output examples

- [ ] **Step 3: Write core reviewer domain briefs (Completeness & Coherence, Verification & Regression)**

**Completeness & Coherence (`completeness-coherence`):**
1. Mission: "Find defects where the spec contradicts itself, has missing cross-references, count mismatches, or term drift across files"
2. High-yield surfaces: cross-references between files, tables with counts, terms defined in multiple places, files with overlapping scope
3. Common defects: count mismatches (table says 5, list has 4), term drift (same concept, different names across files), self-contradictions, orphaned sections, missing cross-references
4. Priority calibration: P0 = contradiction that would cause an implementer to build conflicting behavior. P1 = count mismatch or missing reference that could confuse. P2 = terminology inconsistency with no functional impact.
5. Collaboration: "If you find a contradiction between two files, message both relevant domain reviewers to verify which side is correct. If you find orphaned sections, message `authority-architecture` to check if the orphan was intentionally moved."
6. Coverage floor: every cross-reference in the spec, every enumerated list, every term with multiple definitions
7. Disconfirmation: "Check if apparent contradictions reflect intentional evolution (amendments supersede earlier content)"
8. Output examples

**Verification & Regression (`verification-regression`):**
1. Mission: "Find defects where the spec makes untested promises, has infeasible test designs, or lacks coverage for normative requirements"
2. High-yield surfaces: testing strategy files, normative requirements with no corresponding test mention, verification sections, coverage claims
3. Common defects: untested promises (normative requirement with no verification path), infeasible test designs (test assumes conditions that can't exist), regression gaps (change introduced without corresponding test update), coverage claims that don't match actual test inventory
4. Priority calibration: P0 = normative requirement with no verification path. P1 = test design is questionable or incomplete. P2 = coverage claim slightly overstated.
5. Collaboration: "If you find an untested contract, message `contracts-enforcement` to verify the contract is still active. If you find test infrastructure gaps, message `integration-enforcement` (if spawned)."
6. Coverage floor: every normative requirement must be checked for a verification path
7. Disconfirmation: "Check if the 'missing test' is covered by an integration test or higher-level verification"
8. Output examples

- [ ] **Step 4: Write optional specialist domain briefs (Schema/Persistence, Integration/Enforcement)**

**Schema / Persistence (`schema-persistence`) — optional:**
1. Mission: "Find defects where schema definitions diverge from behavioral contracts, persistence constraints are missing, or migration safety is compromised"
2. High-yield surfaces: DDL files, schema rationale, data model definitions, migration files
3. Common defects: schema-contract mismatch (schema allows what contract forbids), missing constraints (not-null, uniqueness missing from DDL), migration safety gaps (no rollback path), persistence-behavior divergence
4. Priority calibration: P0 = schema allows data that violates contract invariants. P1 = missing constraint that could cause data corruption. P2 = schema naming inconsistent with spec terminology.
5. Collaboration: "Message `contracts-enforcement` for any schema-contract mismatch. Message `verification-regression` for missing migration tests."
6. Coverage floor: every schema file and every file referencing the data model
7. Disconfirmation: "Check if the apparent mismatch reflects a deliberate denormalization documented in decisions"
8. Output examples

**Integration / Enforcement Surface (`integration-enforcement`) — optional:**
1. Mission: "Find defects where hooks, plugins, or enforcement mechanisms have gaps, failure recovery is missing, or the enforcement surface doesn't match the contract promises"
2. High-yield surfaces: hook definitions, plugin configurations, enforcement mechanism files, failure recovery sections
3. Common defects: hook gaps (contract promises enforcement with no hook), confirmation model violations (action proceeds without required confirmation), failure recovery missing (hook fails with no fallback), enforcement surface incomplete
4. Priority calibration: P0 = enforcement mechanism missing for a safety-critical contract. P1 = hook exists but has coverage gap. P2 = enforcement surface naming inconsistent.
5. Collaboration: "Message `contracts-enforcement` for any enforcement gap that affects contract promises. Message `authority-architecture` if enforcement mechanisms are in the wrong authority tier."
6. Coverage floor: every hook, plugin, and enforcement mechanism defined in the spec
7. Disconfirmation: "Check if the 'gap' is intentionally deferred (v2/future work documented in decisions)"
8. Output examples

- [ ] **Step 5: Validate and commit**

Run: `wc -l .claude/skills/spec-review-team/references/role-rubrics.md`

Expected: 220-280 lines.

Verify all 6 role IDs match SKILL.md: `authority-architecture`, `contracts-enforcement`, `completeness-coherence`, `verification-regression`, `schema-persistence`, `integration-enforcement`.

```bash
git add .claude/skills/spec-review-team/references/role-rubrics.md
git commit -m "feat(spec-review-team): role-rubrics.md — 6 reviewer domain briefs + shared scaffold"
```

### Task 9: synthesis-guidance.md

**Files:**
- Create: `.claude/skills/spec-review-team/references/synthesis-guidance.md`

This file provides Technique-level guidance — worked examples, not prescriptive algorithms. The lead adapts these examples, not follows them mechanically.

- [ ] **Step 1: Write header + consolidation example**

```markdown
# Synthesis Guidance Reference

Operational guidance for Phase 5 (SYNTHESIS). Contains worked examples, edge cases, and anti-patterns. This is Technique-level content — one valid approach the lead can adapt, not a normative procedure. The obligations and invariants in SKILL.md are normative; this file is not.
```

Write a worked consolidation example:
- Two findings from different reviewers describing the same issue with different vocabulary
- Show the merge decision: same `violated_invariant` + same `affected_surface` → merge
- Show the ledger record with `merge_rationale`
- Include a counter-example: similar-looking findings at the same surface that are NOT duplicates (different root causes)

- [ ] **Step 2: Write corroboration assessment example**

Write examples for each support type:
- **independent_convergence:** AA-3 and CE-7 both independently find an invariant drift at foundations.md:45-52. Both `provenance: independent`. Lead records `support_type: independent_convergence` — this is the strongest corroboration.
- **cross_lens_followup_confirmation:** AA-2 messages `contracts-enforcement` about a misplaced authority. CE-4 confirms: contracts reference the misplaced content. CE-4's `provenance: followup, prompted_by: authority-architecture`. Lead records `support_type: cross_lens_followup_confirmation`.
- **related_pattern_extension:** CC-1 finds count mismatch in a table. VR-2 finds untested promise in the same section. Different defect classes, same surface, together reveal a pattern of under-maintained content. Lead records `support_type: related_pattern_extension`.
- **singleton:** AA-5 finds an authority placement issue. No other reviewer mentions it. `support_type: singleton`. Note: singletons can still be P0 — corroboration affects confidence, not priority.

- [ ] **Step 3: Write contradiction resolution example + edge cases**

Contradiction example:
- AA-2 says section X violates the authority hierarchy (should be in normative file)
- CC-3 says section X is correctly placed (references are consistent where it is)
- Resolution: check authority map. If X is in a non-normative file but makes binding decisions → AA-2 is correct (authority takes precedence). Record `adjudication_rationale`.

Edge cases:
- **Empty reviewer:** Reviewer produces no findings and no coverage notes → `reviewers_failed` (failed to follow output contract), not "clean bill of health"
- **All-identical findings:** 3 reviewers find the exact same issue → merge into one canonical finding with 3 contributors, `independent_convergence`
- **Circular deferrals:** AA defers to CE, CE defers to AA → both are meta-findings (unverified deferral)
- **Provenance ambiguity:** Reviewer received a message but was already investigating the same area → `provenance: independent` (the message didn't redirect investigation)

- [ ] **Step 4: Write anti-patterns + exemplar ledger**

Anti-patterns:
- **Conviction maximizing:** merging findings that share a surface but describe different problems to inflate corroboration counts
- **Premature merging:** combining findings before checking provenance chains — may incorrectly classify `followup` as `independent_convergence`
- **Ignoring provenance:** treating all multi-reviewer findings as `independent_convergence` regardless of `prompted_by` fields
- **Priority inflation:** using corroboration to raise priority beyond evidence ("three reviewers said P2, so it must be P1")
- **Silent contradiction dropping:** resolving contradictions by picking one side without recording `adjudication_rationale`

Exemplar ledger entry (complete, all fields populated):

```markdown
### [SY-1] Authority misplacement: binding schema constraint in non-normative rationale file

- **source_findings:** AA-2, CE-4
- **support_type:** cross_lens_followup_confirmation
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "AA-2 identified the misplacement. CE-4 confirmed contracts reference the misplaced authority. Different defect classes (authority vs contract enforcement) but same root cause."
- **adjudication_rationale:** N/A (no contradiction)
- **priority_rationale:** "Ranked above CC-1 (same P1) because this boundary is the spec's primary normative source — misplacement here affects all downstream contracts"
```

- [ ] **Step 5: Validate and commit**

Run: `wc -l .claude/skills/spec-review-team/references/synthesis-guidance.md`

Expected: 170-220 lines.

```bash
git add .claude/skills/spec-review-team/references/synthesis-guidance.md
git commit -m "feat(spec-review-team): synthesis-guidance.md — worked examples, anti-patterns, exemplar ledger"
```

### Task 10: failure-patterns.md

**Files:**
- Create: `.claude/skills/spec-review-team/references/failure-patterns.md`

- [ ] **Step 1: Write header + degraded mode details**

```markdown
# Failure Patterns Reference

Operational reference for failure modes, degraded mode behavior, troubleshooting, and recovery procedures. SKILL.md's failure mode table defines what to detect and how to respond at a high level. This file provides the operational detail.
```

**Degraded mode** (expanded from spec line 452):

When DISCOVERY finds zero parseable frontmatter:
- What still works: file discovery, path-based classification, core team spawning, all review phases, synthesis
- What's disabled: (1) redirect gate (always full team), (2) authority-derived specialist spawning (core only), (3) authority-based contradiction adjudication (escalate all as ambiguity)
- Phase 3A produces zero mechanical validation results (no frontmatter to validate) — proceed directly to cluster routing
- All files get source authority = `unknown`
- User communication: "No frontmatter detected on any spec file. Proceeding in degraded mode: all files classified by path heuristics, authority-based features disabled. Consider running spec-modulator to add frontmatter."

- [ ] **Step 2: Write troubleshooting decision trees**

Common issues and their resolution paths:

**"TeamCreate failed"**
1. Check: is `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set? → Phase 0 should have caught this
2. Check: is there an existing team from a prior failed run? → Clean up with TeamDelete first
3. Check: is this a nested team attempt? → Cannot create teams within teammates
4. If none of the above: report error to user with full error message. Hard stop.

**"Reviewer not producing output"**
1. Check: has the reviewer gone idle? → Yes: check findings file exists. If missing, reviewer failed.
2. Check: has 5 minutes elapsed? → Apply wall-clock timeout.
3. Check: is the reviewer stuck in a tool permission loop? → Reviewers start with lead's permissions. If permission prompts block, the user must approve.

**"Findings file is empty or prose-only"**
1. Lead normalizes to schema during SYNTHESIS canonicalization
2. Increment `normalization_rewrites` per repaired finding
3. If entire file is prose with no discernible findings: treat as reviewer failure

**"Stale workspace from previous run"**
1. `.review-workspace/` exists at DISCOVERY start
2. Warn user, offer 3 options: (a) archive to `.review-workspace.bak/`, (b) remove, (c) abort
3. Do NOT silently overwrite — the workspace may contain findings from a partial review the user wants to preserve

- [ ] **Step 3: Write recovery procedures + common mistakes**

**Recovery from partial runs:**
- If the skill was interrupted during Phase 4 (REVIEW): workspace may contain partial findings. The user can manually inspect `.review-workspace/findings/` for any completed reviewer output.
- If interrupted during Phase 5 (SYNTHESIS): the ledger in `.review-workspace/synthesis/ledger.md` may be partially written. Re-running synthesis from scratch is safer than trying to resume.
- In all cases: clean up the team before re-running. `TeamDelete` requires all teammates shut down first. If teammates are orphaned, the session may need to restart.

**Common implementation mistakes** (from spec design sessions):
- Using `Agent` without `team_name` → creates isolated subagent, no messaging/tasks/idle
- Using agent UUID instead of `name` for SendMessage → message delivery fails silently
- Starting lead analysis before all reviewers spawned → spec violation (Phase 4 step 6)
- Embedding packet content in spawn prompt instead of pointing to file → destructive compression for large specs
- Writing prompt-based TeammateIdle hook → will NOT fire (command hooks only for this event)
- Forgetting `.gitignore` for `.review-workspace/` → review artifacts committed accidentally

- [ ] **Step 4: Validate and commit**

Run: `wc -l .claude/skills/spec-review-team/references/failure-patterns.md`

Expected: 100-140 lines.

```bash
git add .claude/skills/spec-review-team/references/failure-patterns.md
git commit -m "feat(spec-review-team): failure-patterns.md — degraded mode, troubleshooting, recovery"
```

---

## Chunk 3: Validation & Integration

### Task 11: Cross-Reference Validation

**Files:**
- All files from Tasks 1-10

- [ ] **Step 1: Verify all cross-references in SKILL.md resolve**

Check that every reference file mentioned in SKILL.md exists:

```bash
# From the skill directory
ls .claude/skills/spec-review-team/references/agent-teams-platform.md
ls .claude/skills/spec-review-team/references/preflight-taxonomy.md
ls .claude/skills/spec-review-team/references/role-rubrics.md
ls .claude/skills/spec-review-team/references/synthesis-guidance.md
ls .claude/skills/spec-review-team/references/failure-patterns.md
```

Expected: all 5 files exist.

- [ ] **Step 2: Verify tool names match allowed-tools**

Check that every tool name used in SKILL.md procedure text appears in the `allowed-tools` frontmatter list:

Tools that must be in allowed-tools: `Read`, `Write`, `Glob`, `Grep`, `Bash`, `Agent`, `ToolSearch`, `TeamCreate`, `TeamDelete`, `SendMessage`, `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`.

Grep the SKILL.md body for tool name references and cross-check against frontmatter.

- [ ] **Step 3: Verify role IDs are consistent**

Check that the 6 role IDs are consistent across all files:

Expected IDs: `authority-architecture`, `contracts-enforcement`, `completeness-coherence`, `verification-regression`, `schema-persistence`, `integration-enforcement`.

These must match in: SKILL.md (team composition), role-rubrics.md (domain briefs), and finding schema (ID prefixes: AA, CE, CC, VR, SP, IE).

Verify the prefix-to-role mapping is correct (not just that prefixes exist):
- AA → `authority-architecture`
- CE → `contracts-enforcement`
- CC → `completeness-coherence`
- VR → `verification-regression`
- SP → `schema-persistence`
- IE → `integration-enforcement`

- [ ] **Step 4: Verify finding schema field set matches spec**

The spec (lines 240-252) defines a 10-field finding schema. Verify SKILL.md includes all 10 fields in the correct order:

`priority`, `title`, `violated_invariant`, `affected_surface`, `impact`, `evidence`, `recommended_fix`, `confidence`, `provenance`, `prompted_by`

Also verify the 5-field coverage notes schema (spec lines 264-269):

`scope_checked`, `checks_run`, `result`, `caveats`, `deferred_to`

- [ ] **Step 5: Verify all 10 audit metrics present**

The spec (lines 357-368) defines exactly 10 named metrics. Verify SKILL.md lists all 10 with matching names:

`raw_finding_count`, `canonical_finding_count`, `duplicate_clusters_merged`, `related_finding_clusters`, `corroborated_findings`, `contradictions_surfaced`, `normalization_rewrites`, `ambiguous_review_clusters`, `reviewers_failed`, `unverified_deferrals`

- [ ] **Step 6: Verify phase gate conditions match spec**

Cross-check each phase gate in SKILL.md against the spec (lines 108-118):

| Phase | Expected gate condition |
|-------|----------------------|
| 0 PREREQUISITE | Feature flag confirmed (hard stop if absent) |
| 1 DISCOVERY | Authority map with ≥1 normative file, or degraded mode |
| 2 ROUTING | Pass redirect gate, or redirect to reviewing-designs |
| 3A PREFLIGHT:Mechanical | All files checked; frontmatter parseable or degraded mode |
| 3B PREFLIGHT:Staffing | Spawn plan finalized |
| 3C PREFLIGHT:Materialize | packet.md written, spawn plan announced |
| 4 REVIEW | All findings files present, or timeout |
| 5 SYNTHESIS | Report written with all 10 audit metrics |

- [ ] **Step 7: Verify line counts**

```bash
wc -l .claude/skills/spec-review-team/SKILL.md
wc -l .claude/skills/spec-review-team/references/preflight-taxonomy.md
wc -l .claude/skills/spec-review-team/references/role-rubrics.md
wc -l .claude/skills/spec-review-team/references/synthesis-guidance.md
wc -l .claude/skills/spec-review-team/references/failure-patterns.md
```

Expected:
- SKILL.md: 400-470 (hard ceiling: 500)
- preflight-taxonomy.md: 130-170
- role-rubrics.md: 220-280
- synthesis-guidance.md: 170-220
- failure-patterns.md: 100-140

- [ ] **Step 8: Final commit (if any validation fixes needed)**

If validation found issues, fix them and commit:

```bash
git add .claude/skills/spec-review-team/
git commit -m "fix(spec-review-team): cross-reference validation fixes"
```

If no fixes needed, this step is a no-op.

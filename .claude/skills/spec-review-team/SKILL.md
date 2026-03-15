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

# Spec Review Team

Review multi-file specifications for structural and semantic defects using a parallel agent team with lateral messaging.

**Announce at start:** "I'm using the spec-review-team skill to review this specification."

## When to Use

- Multi-file specifications with frontmatter metadata (`module`, `status`, `normative`, `authority` fields)
- Specs created by `spec-modulator` or following the same conventions
- Reviews requiring cross-file invariant analysis and multi-lens defect detection
- Trigger phrases: "review this spec", "review the spec", "spec review", "review all spec files", "thorough spec review", "review specification"

## When NOT to Use

- Single design documents → use `reviewing-designs` instead
- Do NOT use for code review or implementation review
- Do NOT use for specs without frontmatter metadata
- Note: specs with few files but multiple authority tiers still require this skill — the redirect gate handles the file-count check, not this rule

## Prerequisites

**YOU MUST** verify agent teams are enabled before any other work:

Check for `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential review — parallel multi-lens review is the skill's value proposition.

## Constraints

These are hard rules, not guidelines:

| # | Constraint | Detail |
|---|-----------|--------|
| 1 | Agent teams experimental | Hard prerequisite. Do NOT fall back to sequential or Agent-tool alternatives. |
| 2 | ~500-line SKILL.md | Operational content lives in reference files. SKILL.md contains rules, gates, and control flow only. |
| 3 | Teammates load project context | CLAUDE.md, MCP servers, and skills auto-load into each teammate. Lead conversation history does NOT carry over. The preflight packet is the authoritative source for spec structure — include everything teammates need in their prompts. |
| 4 | One team per session | No nested teams. No session resumption across separate Claude sessions. |
| 5 | 3-5 teammates recommended | Core 4 reviewers plus up to 2 optional specialists. Maximum 6 teammates total. |
| 6 | Sonnet for reviewers | Spawn all reviewers with claude-sonnet. Lead uses the session's default model. |

## Team Composition

Six specialized reviewers cover the full defect space. Core reviewers are mandatory; optional reviewers activate based on spec content.

| # | Role | ID | Type | Defect Class |
|---|------|----|------|--------------|
| 1 | Authority & Architecture | `authority-architecture` | Core | Invariant drift, authority placement errors, architectural constraint violations |
| 2 | Contracts & Enforcement | `contracts-enforcement` | Core | Behavioral drift from contracts, unauthorized implementation decisions, enforcement gaps |
| 3 | Completeness & Coherence | `completeness-coherence` | Core | Count mismatches, term drift, self-contradictions, missing cross-references |
| 4 | Verification & Regression | `verification-regression` | Core | Untested promises, infeasible test designs, regression gaps |
| 5 | Schema / Persistence | `schema-persistence` | Optional | Schema-contract mismatches, constraint gaps, DDL-behavioral divergence |
| 6 | Integration / Enforcement Surface | `integration-enforcement` | Optional | Hook/plugin gaps, confirmation model violations, failure recovery paths |

**Design principle: thin by remit, not by file reassignment.** All core reviewers access all spec files — they are scoped by defect class, not by file assignment. Do NOT divide files among reviewers. File-partitioned review creates gaps at file boundaries where cross-file invariants live. Every reviewer reads every file; each sees it through a different lens.

## Procedure

### Phase 1: DISCOVERY

**Phase gate:** Authority map built with ≥1 normative file, or degraded mode entered.

1. **Locate spec directory.** Use the path the user provides. If no path given, search for markdown files with YAML frontmatter containing `module`, `status`, `normative`, or `authority` fields.

2. **Read all markdown files.** Parse YAML frontmatter from each file. Extract: `module`, `status`, `normative`, `authority`, `legacy_sections`.

3. **Build authority map.** For each file, record:
   - **Normative:** `true` if frontmatter `normative: true`; `false` otherwise.
   - **Source authority:** value of frontmatter `authority` field, preserved as-is. If absent: `unknown`.
   - **Review cluster:** derived from source authority + `module` + path heuristics. See `references/preflight-taxonomy.md` for the 6 canonical clusters and classification rules.

4. **Degraded mode:** If zero files have parseable frontmatter, classify all files by path heuristics, warn the user that frontmatter is missing, and continue. See Failure Modes table.

5. **Partial coverage** (some files with frontmatter, some without) is normal operation — do NOT enter degraded mode.

**Output:** Authority map listing every file with its normative flag, source authority, and review cluster. Count of normative files, clusters represented, and boundary edges (files bridging two clusters).

### Phase 2: ROUTING

**Phase gate:** Pass redirect gate, or redirect to `reviewing-designs`.

Evaluate all four redirect conditions. Redirect to `reviewing-designs` only if **all** conditions are met:

| Condition | Threshold | Required for redirect |
|-----------|-----------|----------------------|
| `confident_review_cluster_count` | ≤ 2 | Yes |
| `boundary_edges` | ≤ 2 | Yes |
| Specialist triggers | None firing | Yes |
| Ambiguous cluster assignments | Any present | **Disables redirect** |

**Key insight:** A 3-file spec spanning 3 authority tiers needs full team review; a 10-file spec in one tier does not. File count is not a gate condition.

**If redirecting:** Tell the user which conditions triggered and why this spec fits `reviewing-designs`. Then invoke `reviewing-designs`. Do NOT continue to Phase 3.

**If not redirecting:** Continue to Phase 3 (PREFLIGHT).

### Phase 3: PREFLIGHT

#### Phase 3A: Mechanical

**Phase gate:** All files checked; frontmatter parseable on all files, or degraded mode entered.

1. Validate frontmatter on all spec files: required fields present (`module`, `status`, `normative`, `authority`), values well-formed (no nulls, no unrecognized status values).
2. Check cross-references: every relative markdown link resolves to an existing file and, if it includes an anchor (`#section`), that anchor exists in the target file.
3. Detect broken links (unresolved paths), orphaned anchors (anchors defined but never referenced), and missing referenced files.
4. Record all results for the preflight packet's `mechanical_checks` section.

#### Phase 3B: Staffing

**Phase gate:** Spawn plan finalized (which reviewers, and why).

1. Core team (4 reviewers: `authority-architecture`, `contracts-enforcement`, `completeness-coherence`, `verification-regression`) always spawns. Role definitions are in `references/role-rubrics.md`.
2. Evaluate optional specialist signals using the two-tiered spawn rule from `references/preflight-taxonomy.md`:
   - Tier 1 (score ≥ 100): a single high-confidence signal is sufficient to spawn.
   - Tier 2 (score 50–99): requires 2+ medium signals from different dimensions to spawn.
3. If frontmatter metadata is insufficient to evaluate signals: sample targeted content excerpts per the sampling policy in `references/preflight-taxonomy.md`. Do NOT expand into broad corpus reading.
4. Budget exhausted and below spawn threshold: do NOT spawn the specialist. Log the unresolved signal in the synthesis report.
5. Record the finalized spawn plan (role IDs, spawn rationale for each optional specialist triggered or suppressed).

#### Phase 3C: Materialize

**Phase gate:** `packet.md` written, spawn plan announced to user.

1. Verify `.review-workspace/` is in `.gitignore`. If absent, add it.
2. Create `.review-workspace/preflight/packet.md` with exactly 6 sections: `authority_map`, `boundary_edges`, `signal_matrix`, `mechanical_checks`, `route_decision`, `spawn_plan`.
3. Announce spawn plan to user: "Spawning [N] reviewers: [role IDs]. Optional specialists: [reason each was triggered or 'not triggered']."

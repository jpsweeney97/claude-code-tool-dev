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

### Phase 4: REVIEW

**Phase gate:** All expected findings files present, or timeout reached.

**Artifact immutability:**

| Artifact | Created | Consumed | Mutability |
|----------|---------|----------|------------|
| Authority map | Phase 1 (DISCOVERY) | Phases 2-5 | Immutable after Phase 1 |
| Spawn plan | Phase 3B (Staffing) | Phase 4 (REVIEW) | Immutable after 3B |
| Findings ledger | Phase 4 (REVIEW) | Phase 5 (SYNTHESIS) | Append-only during Phase 4; read-only in Phase 5 |

#### Spawn Contract

1. Write preflight `packet.md` if not completed in Phase 3C.
2. Create team via `TeamCreate` with a descriptive `team_name` (e.g., `"spec-review"`). If `TeamCreate` is a deferred tool, fetch its schema via `ToolSearch` first.
3. Create one task per reviewer via `TaskCreate`. Each task must include: role ID, output file path (`.review-workspace/findings/{role-id}.md`), and `packet.md` path.
4. Spawn each reviewer via `Agent` with: `team_name`, `name` (role ID), `model: "sonnet"`, and `prompt` containing the scaffold, a pointer to `packet.md`, and the role delta from `references/role-rubrics.md`. The `team_name` parameter makes a reviewer a teammate with messaging, tasks, and idle notifications. Without `team_name`, the agent is an isolated subagent with none of those capabilities.
5. `name` is the addressing key for ALL communication. Use role IDs (e.g., `"authority-architecture"`) — never UUIDs.
6. Do NOT embed preflight packet content in spawn prompts. Point reviewers to `.review-workspace/preflight/packet.md` — they read it themselves. Embedding causes destructive compression for large specs.
7. Do NOT start the lead's own analysis before all teammates are spawned.

#### Completion Contract

- **Primary signal:** idle notifications from the team system. When all spawned reviewers have gone idle, proceed to the completion check.
- **Peer DM visibility:** when a reviewer sends a DM to another reviewer, a brief summary appears in the sender's idle notification. This gives the lead visibility into cross-reviewer collaboration without polling — use these summaries as synthesis input.
- **Hard deliverable:** each reviewer writes findings to `.review-workspace/findings/{role-id}.md`.
- **Completion check:** after all idle notifications received, verify each expected file exists via `Glob` or `Read`.
- **Wall-clock timeout:** 5 minutes with no new idle notifications and no task status changes (confirmed via `TaskGet`). "Activity" means: idle notification received, OR a task moving to `completed` via `TaskGet`. Lateral messages are NOT independently observable — they surface only as DM summaries in the next idle notification.
- **Partial completion:** always proceed with available findings. Report `reviewers_failed` with a per-reviewer reason for any missing findings files.

#### Lateral Messaging and Task Scope

**Messaging primitives:**

- `message` — targeted `SendMessage` to `"{name}"` (one recipient).
- `broadcast` — `SendMessage` with `to: "*"` (all teammates). Broadcast costs scale linearly with team size since each message lands in every recipient's context window.

Spawn prompts instruct each reviewer to send a targeted `message` to other reviewers when they find cross-lens findings that could affect another reviewer's analysis. Messages are informal coordination signals; each reviewer's findings file is the sole formal deliverable.

**Task scope:**

- One task per reviewer. Do NOT set `blockedBy` dependencies — all tasks run in parallel.
- Reviewers: Do NOT self-claim additional tasks after finishing. Go idle when done.
- Known limitation: task status can lag behind actual reviewer state. Idle notifications are the primary completion signal; task status via `TaskGet` is secondary confirmation.

#### Quality Gate Hooks (optional for v1)

Two hook types fire on reviewer lifecycle events:

- `TeammateIdle` — fires when a teammate goes idle. Exit code 2 returns feedback and allows the reviewer to continue. **Command hooks only** (other hook types are not supported for this event).
- `TaskCompleted` — fires when a task reaches `completed`. All four hook types supported.

Neither hook type supports matchers — filter by role ID inside the hook logic. These hooks become valuable once quality predicates are reliable enough to warrant automated gating. Do NOT implement for v1.

#### Cleanup Contract

1. Send a shutdown request to each reviewer: `SendMessage` with `{type: "shutdown_request", reason: "Review complete"}`.
2. If a reviewer rejects the shutdown, retry with additional context. Shutdown may be delayed — the reviewer finishes its current tool call before processing the message.
3. After all reviewers shut down, call `TeamDelete`. `TeamDelete` fails if any teammate is still active — confirm all are idle before calling.
4. Teammates must NOT self-cleanup. Only the lead calls `TeamDelete`.
5. Ask the user: preserve or remove `.review-workspace/`? Default: preserve.

### Phase 5: SYNTHESIS

**Phase gate:** Report written with all 10 audit metrics.

**Boundary rule:** Technique-in-Discipline-shell. Prescribe computation for auditable state; prescribe criteria for meaning. If two competent operators should reach the same result from the same raw facts and nothing valuable is lost by prescribing it, prescribe it (mechanical pass). Otherwise, state the obligation, require a rationale, and audit the structure (judgment obligation).

#### Inputs

| Source | Content | How to use |
|--------|---------|------------|
| Findings files | Structured findings per reviewer | Primary input — formal deliverables |
| Coverage notes | Scope checked, checks run, caveats, deferrals | Verify completeness; check deferral chains |
| DM summaries | Brief summaries of peer messages in idle notifications | Assess causal links between findings |
| Authority map | File → normative/non-normative + source authority | Inform adjudication (normative > non-normative) |
| Preflight packet | Spec structure, boundary edges, signal matrix | Context for finding distribution |

#### Mechanical Passes (prescribed)

Execute in order:

1. **Canonicalize** — normalize format across all findings files, fix schema violations, increment `normalization_rewrites` metric for each rewrite.
2. **Build synthesis ledger** at `.review-workspace/synthesis/ledger.md` — one record per canonical finding using the ledger format below.
3. **Verify deferrals** — for each finding with a `deferred_to` chain in coverage notes, confirm the receiving reviewer addressed it. Unverified deferrals become meta-findings (P1, prefix `SY`).
4. **Compute all 10 audit metrics** — counts, rates, and derived values as defined in `references/synthesis-guidance.md`.
5. **Ensure required report sections** — prioritized findings, corroboration evidence, contradiction resolutions, metrics, coverage summary. Missing sections block phase gate.

#### Judgment Obligations

**Consolidate and deduplicate.** Two findings are the same defect when they share `violated_invariant` and `affected_surface` as a minimum signal; apply semantic judgment to catch paraphrasing. Merged findings list all contributor IDs. Record `merge_rationale` in the ledger.

**Assess corroboration.** Classify each canonical finding's `support_type`:

- `independent_convergence` — both contributors have `provenance: independent`
- `cross_lens_followup_confirmation` — one reviewer flagged it; another confirmed via `followup`
- `related_pattern_extension` — distinct findings at the same surface reveal a larger pattern
- `singleton` — single-lens finding with no corroboration

Record `support_type` and `contributors` in the ledger.

**Resolve contradictions.** Apply the authority map (normative > non-normative), then evidence quality, then domain reasoning. Unresolvable contradictions escalate as ambiguity findings (P1, `SY` prefix). Record `adjudication_rationale` in the ledger for every resolved contradiction.

**Prioritize.** P0 > P1 > P2 is the baseline. Corroboration and confidence are secondary tiebreakers. Record `priority_rationale` in the ledger only when ranking departs from the P0 > P1 > P2 baseline.

Reference `references/synthesis-guidance.md` for worked examples and edge cases.

#### Ledger Format

```markdown
### [SY-N] Canonical finding title

- **source_findings:** AA-1, CE-3
- **support_type:** independent_convergence
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "..."
- **adjudication_rationale:** (if applicable)
- **priority_rationale:** (if non-obvious)
```

#### Ledger Invariants

These are machine-checkable. Violations block the phase gate.

1. Every `source_findings` ID traces to a findings file from a spawned reviewer.
2. Every `contributors` entry matches a spawned reviewer's role ID.
3. No contradiction silently dropped — resolved contradictions have `adjudication_rationale`; unresolved contradictions become `SY` findings.
4. Every `support_type` is consistent with the provenance chain of its contributors.
5. Every finding in the report has a ledger record.

### Phase 6: PRESENT

**Phase gate:** Report delivered to user.

Write the final report to `.review-workspace/synthesis/report.md`. Required sections:

1. **Summary** — finding counts by priority, team composition, coverage assessment.
2. **Prioritized findings** — ordered by impact, corroboration evidence inline for each finding.
3. **Corroboration table** — which findings converged independently, were confirmed across lenses, or extended a pattern.
4. **Contradiction resolutions** — how each disagreement was resolved, or escalated as an ambiguity finding.
5. **Audit metrics** — all 10 metrics, as computed in Phase 5.
6. **Coverage summary** — what was checked, what was not checked, and why.

After presenting the report to the user, execute the Phase 4 cleanup contract: send shutdown requests, await confirmation, call `TeamDelete`, then prompt the user about preserving `.review-workspace/`. Cleanup is a return to Phase 4's cleanup section — it is NOT a Phase 6 sub-procedure.

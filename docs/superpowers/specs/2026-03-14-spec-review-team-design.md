# spec-review-team Skill Design

**Date:** 2026-03-14
**Status:** Draft
**Branch:** feature/spec-review-team
**Dependencies:** spec-modulator skill (merged at `7e42670`)

## Problem

Multi-file specifications with authority-based organization (normative vs. non-normative files, frontmatter metadata, cross-references) require review that understands the corpus structure. Single-document review tools like `reviewing-designs` miss cross-file invariant violations, authority misplacements, and completeness gaps across the corpus.

No existing skill reviews a multi-file spec as a structured corpus. The `reviewing-designs` skill operates on single design documents. Manual review requires the reviewer to mentally reconstruct the authority model, cross-references, and invariant relationships — work that can be automated via preflight analysis and parallel specialized reviewers.

## Scope

**In scope:** Multi-file specifications organized with frontmatter metadata (module, status, normative, authority fields). The skill discovers spec structure at runtime — it is not specific to any single spec.

**Out of scope:** Single design documents (use `reviewing-designs`), code review, implementation review, specs without frontmatter metadata.

**Lifecycle positioning:**
- `spec-modulator` creates multi-file specs with authority-based organization
- [spec evolves through authoring and iteration]
- `spec-review-team` reviews the corpus for structural and semantic defects

**Shared conventions with spec-modulator:** Frontmatter fields (`module`, `status`, `normative`, `authority`, `legacy_sections`), cross-references (relative markdown links with semantic kebab-case anchors), README (reading-order table, authority model).

## SKILL.md Frontmatter

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

**Trigger phrases:** "review this spec", "review the spec", "spec review", "review all spec files", "thorough spec review", "review specification"

## Constraints

1. **Agent teams experimental.** Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Hard prerequisite — do not fall back to sequential review.
2. **SKILL.md under ~500 lines.** Operational content offloaded to reference files. (`reviewing-designs` at 577 lines is the upper bound precedent.)
3. **Teammates load project context automatically.** Each reviewer loads `CLAUDE.md`, MCP servers, and skills — the same ambient context as any Claude Code session. They also receive the spawn prompt from the lead. The lead's conversation history does not carry over. Reviewer-specific context comes from the spawn prompt (role, defect class) and workspace files (preflight packet). Reviewers should use ambient project context (e.g., `CLAUDE.md` conventions, MCP tools) as supplementary information but treat the preflight packet as the authoritative source for spec structure and authority assignments.
4. **One team per session.** No nested teams, no session resumption.
5. **3-5 teammates recommended.** Core team of 4 is within range; 6 total (with optionals) is the maximum. No hard platform limit, but coordination overhead and token costs increase linearly.
6. **Sonnet recommended for reviewers.** Per platform docs, Sonnet balances capability and cost for coordination tasks. The lead (which runs synthesis) uses the session's default model.

## Architecture: Approach A'

**Pattern:** Normative SKILL.md (~500 lines) + operational reference files. Follows the `reviewing-designs` pattern (not the `handbook`/`explore-repo` pattern of separate synthesis agents).

**Why A' over alternatives:**

| Approach | Verdict | Rationale |
|----------|---------|-----------|
| A (monolithic) | Rejected | 800-1200 lines violates the ~500-line guideline. `reviewing-designs` history shows monolithic-to-reference migration is painful. |
| B (skill + synthesis agent) | Rejected | Wrong solution to the real problem. Context pollution isn't the risk — lack of explicit intermediate structure is. A separate synthesis agent adds abstraction tax without solving the structural discipline problem. |
| C (skill + preflight + synthesis agents) | Rejected | Premature for v1. Two abstraction taxes before usage proves either needed. |
| **A' (normative SKILL.md + refs)** | **Adopted** | Emerged from comparative Codex dialogue. Key reframe: "Does synthesis need fresh context?" → "Does synthesis operate over explicit intermediate structure?" Answer: structured findings + procedure in reference files, not a separate agent. |

**Design for upgrade:** 5 measurable [A-to-B upgrade triggers](#a-to-b-upgrade-triggers) are defined. If synthesis complexity warrants extraction after v1 usage data, the upgrade path is clean.

### File Structure

```
.claude/skills/spec-review-team/
├── SKILL.md                          # Normative: procedure, gates, spawn logic, constraints, finding schema
└── references/
    ├── agent-teams-platform.md       # Reference: platform contracts, tool schemas, hook constraints, costs
    ├── preflight-taxonomy.md         # Operational: cluster definitions, signal dimensions, scoring weights
    ├── role-rubrics.md               # Operational: per-role domain briefs (8 components), collaboration playbooks
    ├── synthesis-guidance.md         # Operational: worked examples, edge cases, anti-patterns, exemplar ledgers
    └── failure-patterns.md           # Operational: degraded modes, troubleshooting, recovery procedures
```

**SKILL.md owns:** Procedure flow, gates, spawn logic, constraints, finding schema definition, workspace conventions, audit metrics, upgrade triggers.

**Reference files own:** Detailed taxonomies, domain briefs with collaboration playbooks, sampling policies, worked synthesis examples with exemplar ledgers, troubleshooting guides.

### 6-Phase Procedure

| Phase | Name | Purpose | Gate |
|-------|------|---------|------|
| 0 | PREREQUISITE | Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set | Feature flag confirmed (hard stop if absent) |
| 1 | DISCOVERY | Locate spec, read frontmatter, build authority map | Authority map built with ≥1 normative file (or degraded mode entered) |
| 2 | ROUTING | Count clusters and edges, evaluate redirect gate | Pass redirect gate (or redirect to `reviewing-designs`) |
| 3A | PREFLIGHT: Mechanical | Validate frontmatter, check cross-references, detect broken links | All files checked; frontmatter parseable on all files or degraded mode entered |
| 3B | PREFLIGHT: Staffing | Evaluate spawn rule, determine core + optional team composition | Spawn plan finalized (which reviewers, why) |
| 3C | PREFLIGHT: Materialize | Write preflight packet to workspace, announce spawn-plan to user | `packet.md` written, spawn-plan announced |
| 4 | REVIEW | Create workspace, spawn team, monitor completion, verify findings | All expected findings files present (or timeout) |
| 5 | SYNTHESIS | Read findings, build canonical ledger, cluster/dedup/corroborate/adjudicate, compute audit metrics, write report | Report written with all 10 audit metrics |
| 6 | PRESENT | Prioritized findings, corroboration table, audit metrics, cleanup prompt | User sees report |

### Execution Contract (Phase 4)

Phase 4 is the core runtime. This section defines the normative execution semantics — an implementer must not invent these.

**Three artifacts drive execution:**

| Artifact | Created | Consumed | Mutability |
|----------|---------|----------|------------|
| Authority map | Phase 1 (DISCOVERY) | Phases 2-5 | Immutable after Phase 1 |
| Spawn plan | Phase 3B (Staffing) | Phase 4 (REVIEW) | Immutable after 3B |
| Findings ledger | Phase 4 (REVIEW) | Phase 5 (SYNTHESIS) | Append-only during Phase 4; read-only in Phase 5 |

**Spawn contract:**
1. Write preflight `packet.md` to `.review-workspace/preflight/` before spawning any reviewer.
2. Create the team via `TeamCreate` with a descriptive `team_name` (e.g., `"spec-review"`). This creates the team structure and shared task list only — it does **not** spawn teammates. If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` first.
3. Create one task per reviewer via `TaskCreate`. Task description includes: reviewer role ID, output file path, and pointer to `packet.md`.
4. Spawn each reviewer using the `Agent` tool with `team_name`, `name`, and `model: "sonnet"` parameters. The `name` parameter is the reviewer's role ID (e.g., `"authority-architecture"`). The `prompt` parameter contains the full spawn prompt (shared scaffold + preflight pointer + role delta). Spawning via the Agent tool with `team_name` is what makes it a teammate — this gives it access to lateral messaging, the shared task list, and idle notifications. An Agent tool call **without** `team_name` creates an isolated subagent with none of these capabilities.
5. **Addressing convention:** The `name` assigned at spawn is the addressing key for all subsequent communication. Use reviewer role IDs as names (e.g., `"authority-architecture"`, `"contracts-enforcement"`). All `SendMessage` calls, task ownership, and shutdown requests use this name — never the agent UUID.
6. Do **not** start the lead's own analysis before all teammates are spawned.

**Completion contract:**
- **Primary completion signal:** Idle notifications from the team system. When a reviewer finishes and stops, it automatically notifies the lead. The `TeammateIdle` hook can intercept this to enforce quality gates (see below). **Peer DM visibility:** When a reviewer sends a direct message to another reviewer, a brief summary appears in the sender's idle notification. This gives the lead visibility into cross-reviewer collaboration without requiring the lead to poll or intercept messages.
- **Hard deliverable:** Each reviewer's findings file in `.review-workspace/findings/{role-id}.md`. This is the source of truth for whether a reviewer completed its work — not task status (which can lag) or idle count.
- **Completion check:** When the lead believes all reviewers are done (based on idle notifications and activity), verify each expected findings file exists. If a file is missing, the reviewer failed — log the reviewer ID and reason (e.g., "no findings file after idle", "findings file empty") in `reviewers_failed`.
- **Wall-clock timeout:** 5 minutes from spawn with no new idle notifications or task status changes. "Activity" means: an idle notification received, or a task moving to `completed` (observable via `TaskGet`). Lateral messages are not independently observable by the lead — they surface only as DM summaries in the next idle notification. Treat remaining reviewers as failed with reason "timeout — no activity for 5 minutes". Proceed to SYNTHESIS with available findings.
- **Partial completion:** Always proceed to SYNTHESIS with whatever findings are available. There is no minimum viable findings threshold. The report surfaces `reviewers_failed` with per-reviewer failure reasons so the user can assess coverage gaps.
- **Lateral messaging encouraged:** Reviewers should message each other when they discover findings relevant to another reviewer's defect class. This enables real-time cross-lens corroboration and challenge — the documented primary use case for agent team review tasks. Two messaging primitives are available:
  - `message` — `SendMessage` with `to: "{reviewer-name}"`. Use for targeted cross-lens signals ("I found an authority placement error at X — check if contracts reference X correctly").
  - `broadcast` — `SendMessage` with `to: "*"`. Sends to all teammates simultaneously. Use sparingly (costs scale linearly — each broadcast sends a separate message to every recipient's context window). Appropriate only for discoveries that affect every reviewer (e.g., "the README authority model is missing — all cross-references to it are broken").
  Spawn prompts should instruct: "If you discover something in another reviewer's defect class, message that reviewer directly." Messages are informal coordination signals; the formal output remains each reviewer's structured findings file. Teammates can discover each other via the team config's `members` array.

**Task scope:** Each reviewer has exactly one review task with no `blockedBy` dependencies — all reviewers work in parallel from spawn. Reviewers should not self-claim additional tasks after finishing — their scope is defined by their defect class, not by task availability. If a reviewer finishes early, it should go idle (not pick up another reviewer's work).

**Known limitation — task status lag:** Teammates sometimes fail to mark tasks as completed. Idle notifications are the primary completion signal; task status is secondary. If a task appears stuck but the reviewer's findings file exists, the task is effectively complete.

**Quality gate hooks (optional):** The platform provides two hooks for automated quality enforcement:
- `TeammateIdle` — fires when a reviewer is about to go idle. Exit code 2 sends feedback and keeps the reviewer working. Use to enforce: minimum finding count, required coverage notes, schema compliance. **Constraint:** Only supports `type: command` hooks — prompt-based hooks will not fire.
- `TaskCompleted` — fires when a task is being marked complete. Exit code 2 prevents completion with feedback. Use to enforce: findings file exists, findings parse as valid schema. Supports all four hook types (command, http, prompt, agent).

Neither hook supports matchers — they fire for every teammate/task unconditionally. Filtering by reviewer role must be done inside the hook logic itself.

These hooks are optional for v1. They become valuable once the skill is stable enough to define reliable quality predicates.

**Cleanup contract:**
1. After PRESENT, shut down each teammate via `SendMessage` with `message: {type: "shutdown_request", reason: "Review complete, findings collected"}`. The teammate can approve (exit gracefully) or reject with an explanation. If a teammate rejects, send another shutdown request with additional context. Shutdown may be slow — teammates finish their current tool call before exiting.
2. After all teammates have shut down, call `TeamDelete` to remove shared team resources (team config, task files). `TeamDelete` fails if any teammates are still active, so step 1 must complete first. Teammates must not run cleanup themselves — their team context may not resolve correctly.
3. Ask user whether to preserve or remove `.review-workspace/`. Default: preserve. This is separate from team cleanup — the workspace is a project-local artifact, not a team resource.

## Team Composition

### 4 Core + 2 Optional Reviewers

| # | Role | ID | Type | Defect Class |
|---|------|----|------|--------------|
| 1 | Authority & Architecture | `authority-architecture` | Core | Invariant drift between normative sources, authority placement errors, architectural constraint violations |
| 2 | Contracts & Enforcement | `contracts-enforcement` | Core | Behavioral drift from contracts, unauthorized implementation decisions, enforcement gap analysis |
| 3 | Completeness & Coherence | `completeness-coherence` | Core | Count mismatches, term drift across files, self-contradictions, missing cross-references, orphaned sections |
| 4 | Verification & Regression | `verification-regression` | Core | Untested promises, infeasible test designs, regression gaps, missing coverage for normative requirements |
| 5 | Schema / Persistence | `schema-persistence` | Optional | Schema-contract mismatches, constraint gaps, DDL-behavioral divergence, migration safety |
| 6 | Integration / Enforcement Surface | `integration-enforcement` | Optional | Hook/plugin gaps, confirmation model violations, failure recovery paths, enforcement surface coverage |

**Design principle: "Thin by remit, not by file reassignment."** All core reviewers access all files. They are scoped by defect class, not by file assignment. This prevents gaps at file boundaries.

### 6 Canonical Review Clusters

Files are classified into review clusters during DISCOVERY. Cluster count drives routing and team composition decisions.

| Review Cluster | Description | Examples |
|----------------|-------------|---------|
| `root` | Top-level architectural and foundational documents | foundations.md, decisions.md, internal-architecture.md, README.md |
| `contracts` | Behavioral contracts and interface definitions | tool-surface.md, behavioral-semantics.md, skill-orchestration.md |
| `schema` | Data model, DDL, persistence definitions | ddl.md, schema rationale |
| `control_surface` | Hooks, plugins, enforcement mechanisms, skill catalog | skills/overview.md, skills/catalog.md |
| `implementation` | Implementation plans, strategies, migration guides | testing-strategy.md, server-validation.md |
| `supporting` | Appendix, glossary, legacy maps, amendments | appendix.md, legacy-map.md, amendments.md |

**Two-layer cluster model:**
- **Source authority** — the file's original `authority` frontmatter value (e.g., `authority: schema`). Preserved as-is in the authority map. Used by the adjudication step (normative > non-normative) and by reviewers for context.
- **Review cluster** — the canonical cluster above, derived from source authority + `module` + path heuristics. Used only for routing (redirect gate), staffing (specialist spawn rule), and rubric selection. This is a lossy mapping — multiple source authorities may collapse into one review cluster.

**Missing metadata handling:**
- Files with no frontmatter at all: source authority = `unknown`, review cluster assigned by path heuristics, flagged as ambiguous.
- Files with frontmatter but no `authority` field: source authority = `unknown`, review cluster derived from `module` + path. This is the common case — spec-modulator only adds `authority` when the spec defines an explicit authority model.
- The "no frontmatter on any file" degraded mode (see Failure Modes) triggers only when zero files have parseable frontmatter. Partial coverage (some files with, some without) is normal operation — not degraded mode.

### Routing: Redirect Gate

Before spawning a team, evaluate whether the spec's authority structure is simple enough for single-document review:

| Condition | Threshold | Effect |
|-----------|-----------|--------|
| `confident_review_cluster_count` | ≤ 2 | Required for redirect |
| `boundary_edges` | ≤ 2 | Required for redirect |
| Specialist triggers | None firing | Required for redirect |
| Ambiguous cluster assignments | Any present | **Disables redirect** |

All conditions must be met for redirect to `reviewing-designs`. Ambiguity in any cluster assignment forces full team review — the ambiguity itself is a signal that authority boundaries need multi-lens examination.

**File count is not a gate condition.** Per Decision #4, authority-boundary clusters are the correct routing proxy, not file count. A 3-file spec spanning 3 authority tiers needs full team review; a 10-file spec in one tier does not. Note: spec-modulator's minimal greenfield output is 4 files (README + foundations + decisions + cluster overview), so a file-count gate of ≤3 would block all legitimate redirects.

### Two-Tiered Spawn Rule for Optional Specialists

Optional specialists are spawned based on signal strength from the preflight analysis:

**Tier 1 — High confidence (score ≥ 100):** Single signal sufficient. Example: `authority: schema` frontmatter on any file → spawn Schema / Persistence specialist.

**Tier 2 — Medium confidence (score 50-99):** Requires 2+ medium signals from different dimensions. Example: file named `ddl.md` (naming signal, 75) alone is insufficient; `ddl.md` + schema-related cross-references from a contract file (cross-ref signal, 60) → spawn.

**Dimensions:** Frontmatter authority, file naming, content keywords, cross-reference patterns, cluster membership. Three dimensions are metadata-derived (free from Phase 1); two require content inspection (content keywords, cross-reference patterns).

**Sampling constraint:** Content-level signal detection in Phase 3B is budgeted sampling, not review. The lead may inspect only targeted excerpts needed to resolve optional-specialist spawn decisions when metadata-derived signals are insufficient. This sampling must remain materially cheaper than a reviewer pass and must not expand into broad corpus reading. The active sampling policy — including the unit of inspection, numeric caps, scaling rules, and budget-exhaustion behavior — is defined in `references/preflight-taxonomy.md`.

**Budget exhaustion:** If the sampling budget is exhausted and confidence remains below the Tier 2 threshold, do **not** spawn the specialist. Core reviewers cover all defect classes; specialists augment but do not replace them. Log the unresolved signal as a preflight note in the synthesis report so the user can assess whether a re-run with adjusted sampling is warranted.

## Reviewer Output Contract

### Atomic Finding Schema

Every reviewer emits findings in this structured format. No prose between findings.

```markdown
## [AA-1] Title of finding

- **priority:** P0 / P1 / P2
- **title:** One-sentence description
- **violated_invariant:** source_doc#anchor
- **affected_surface:** file + section/lines
- **impact:** 1-2 sentences describing consequences
- **evidence:** what the doc says vs. what it should say
- **recommended_fix:** specific action to resolve
- **confidence:** high / medium / low
- **provenance:** independent / followup
- **prompted_by:** {reviewer-name} (required when provenance is followup; omit when independent)
```

**Provenance fields:** These enable the lead to distinguish independent convergence from signal-prompted confirmation during synthesis. Reviewers tag each finding with what they can reliably know: whether they discovered the finding independently or as a followup to a lateral message. The `prompted_by` field names the reviewer whose message prompted investigation. The lead interprets these facts during synthesis — the reviewer does not assess corroboration quality, only disclose the causal chain.

**Finding ID format:** `{role-prefix}-{sequence}`. Prefixes: AA (Authority & Architecture), CE (Contracts & Enforcement), CC (Completeness & Coherence), VR (Verification & Regression), SP (Schema / Persistence), IE (Integration / Enforcement Surface).

### Coverage Notes

Mandatory for core reviewers with zero findings in a defect class. Prevents "no findings" from being ambiguous (did they check? or did they skip?).

| Field | Purpose |
|-------|---------|
| `scope_checked` | What files/sections were examined |
| `checks_run` | What specific checks were performed |
| `result` | "No defects found" with brief rationale |
| `caveats` | Any limitations (e.g., "could not verify X without Y") |
| `deferred_to` | If another reviewer is better positioned for this check |

## Synthesis

### Instruction Philosophy

**Boundary rule:** Prescribe computation for auditable state; prescribe criteria for meaning. If two competent operators should reach the same result from the same raw facts and nothing valuable is lost by prescribing it, prescribe it (mechanical pass). Otherwise, state the obligation, require a rationale, and audit the structure (judgment obligation).

This skill follows a **Technique-in-Discipline-shell** model per this codebase's skill taxonomy (`skills-guide.md`): Discipline-level prescription for phase gates, artifact contracts, schema validity, and failure handling; Technique-level guidance for synthesis, corroboration assessment, prioritization, and reviewer judgment. The synthesis section operates at the Technique level — the lead exercises judgment over structured inputs and produces auditable output.

### Inputs

The lead has these sources available during synthesis:

| Source | Content | How to use |
|--------|---------|------------|
| Findings files | Structured findings per reviewer in `.review-workspace/findings/{role-id}.md` | Primary input — the formal deliverables |
| Coverage notes | Scope checked, checks run, caveats, deferrals | Verify completeness; check deferral chains |
| DM summaries | Brief summaries of peer messages in idle notifications | Assess whether findings are causally linked; understand cross-reviewer signals |
| Authority map | File → normative/non-normative + source authority + review cluster | Inform adjudication — normative sources carry more weight |
| Preflight packet | Spec structure, boundary edges, signal matrix | Context for understanding finding distribution across the corpus |

### Mechanical Passes (prescribed)

These produce auditable state. The lead executes them as specified.

1. **Canonicalize** — normalize finding format, fix minor schema violations. Increment `normalization_rewrites` metric per finding repaired.
2. **Build synthesis ledger** — create a structured intermediate artifact in `.review-workspace/synthesis/ledger.md`. One record per canonical finding or finding cluster. Each record has fields populated by subsequent judgment obligations (see below). The ledger is more structured than the prose report but less rigid than a fixed algorithm — it captures the lead's reasoning in an auditable format.
3. **Verify deferrals** — for each coverage note with `deferred_to`, check the target reviewer's findings cover that defect class. Unverified deferrals become meta-findings (P1, prefix `SY`: "coverage gap — deferred check not picked up").
4. **Compute audit metrics** — all 10 metrics computed from the ledger and findings files.
5. **Ensure required report sections** — the final report must contain: prioritized findings, corroboration evidence, contradiction resolutions, audit metrics, and a coverage summary.

### Judgment Obligations (with rationale)

These produce meaning from the structured inputs. The lead exercises judgment, but every judgment call must be recorded in the synthesis ledger with a short rationale.

**Consolidate and deduplicate.** Identify findings that describe the same defect — whether they share exact field values or describe it differently. Use `violated_invariant` and `affected_surface` as the minimum signal, but also apply semantic judgment: two findings with different vocabulary about the same problem at the same location are duplicates. Merged findings list all contributing reviewer IDs.

- **Ledger field:** `merge_rationale` — why these findings were merged (or why similar findings were kept separate)

**Assess corroboration.** Determine the strength of multi-lens support for each finding, using the `provenance` field to distinguish:
- `independent_convergence` — multiple reviewers found the same issue independently (`provenance: independent` on both)
- `cross_lens_followup_confirmation` — one reviewer flagged an issue, another confirmed it in their domain (`provenance: followup` with `prompted_by`)
- `related_pattern_extension` — distinct findings at the same surface from different lenses that together reveal a larger pattern
- `singleton` — single-lens finding with no corroboration

Both independent convergence and followup confirmation are genuine corroboration — but they represent different strengths of evidence. The lead assesses which type applies using the provenance chain and DM summaries.

- **Ledger fields:** `support_type` (one of the four types above), `contributors` (list of reviewer IDs)

**Resolve contradictions.** When reviewers disagree, use all available context: authority map (normative sources carry more weight), evidence quality, domain reasoning, and cross-reviewer signals. If a contradiction cannot be resolved with confidence, escalate as an ambiguity finding (P1, prefix `SY`, `violated_invariant` = "cross-reviewer contradiction").

- **Ledger field:** `adjudication_rationale` — why one position was preferred, or why the contradiction was escalated

**Prioritize.** Order findings by impact. P0 before P1 before P2 as a baseline, with corroboration strength and confidence as secondary signals. But the lead should use full context: a lone P1 at a critical authority boundary may warrant higher placement than a well-corroborated P2 in a supporting document. The prioritization must be defensible — the user should be able to understand why each finding is ranked where it is.

- **Ledger field:** `priority_rationale` — why this finding is ranked at this position (brief; required only when the ranking departs from the P-level × corroboration baseline)

### Synthesis Ledger

The synthesis ledger (`.review-workspace/synthesis/ledger.md`) is the structured intermediate artifact between raw findings and the final report. Each canonical finding or cluster gets a record:

```markdown
### [SY-1] Canonical finding title

- **source_findings:** AA-1, CE-3
- **support_type:** independent_convergence / cross_lens_followup_confirmation / related_pattern_extension / singleton
- **contributors:** authority-architecture, contracts-enforcement
- **merge_rationale:** "Both describe the same invariant drift at foundations.md:45-52, using different vocabulary"
- **adjudication_rationale:** (if contradiction resolved) "Normative source (foundations.md) takes precedence per authority map"
- **priority_rationale:** (if non-obvious) "Ranked above CE-5 despite same P-level because this boundary is the spec's primary normative source"
```

**Ledger invariants (machine-checkable):**
- Every `source_findings` ID traces to a specific reviewer's findings file
- Every `contributors` entry matches a spawned reviewer's role ID
- No contradiction is silently dropped — resolved contradictions have `adjudication_rationale`, unresolved ones become `SY` findings
- Every `support_type` is consistent with the provenance chain (e.g., `independent_convergence` requires `provenance: independent` on all source findings)
- Every finding in the final report has a corresponding ledger record

These invariants are the testability surface. They make the lead's reasoning auditable without constraining what reasoning is permitted. Principle: **testable synthesis ledger, not testable synthesis brain.**

### Guidance

`references/synthesis-guidance.md` (renamed from `synthesis-procedure.md`) contains worked examples, edge case handling, anti-patterns, and exemplar ledger entries. It is operational guidance — one valid approach the lead can adapt, not a normative procedure. The obligations and invariants above are normative; the reference file is not.

### 10 Audit Metrics

| # | Metric | Description |
|---|--------|-------------|
| 1 | `raw_finding_count` | Total findings before canonicalization |
| 2 | `canonical_finding_count` | Findings after consolidation/dedup |
| 3 | `duplicate_clusters_merged` | Number of consolidation merges |
| 4 | `related_finding_clusters` | Findings with `support_type` of `related_pattern_extension`. Reporting-only — not used as a gate or threshold. |
| 5 | `corroborated_findings` | Findings with `support_type` of `independent_convergence` or `cross_lens_followup_confirmation` |
| 6 | `contradictions_surfaced` | Inter-reviewer disagreements (resolved + escalated) |
| 7 | `normalization_rewrites` | Findings that needed schema repair during canonicalization |
| 8 | `ambiguous_review_clusters` | Files with uncertain review cluster assignment |
| 9 | `reviewers_failed` | Per-reviewer list: reviewer ID + failure reason (timeout, no findings file, empty file). Count and details — not just a number. |
| 10 | `unverified_deferrals` | Coverage notes with `deferred_to` targets that did not cover the delegated class |

### A-to-B Upgrade Triggers (Post-v1 Calibration)

These are post-v1 operations metrics, not in-run audit metrics. They require cross-run persistence and an external evaluation owner — neither exists in v1. Record raw data during v1 runs; evaluate after 8+ runs.

| # | Trigger | Threshold | Signal | Requires |
|---|---------|-----------|--------|----------|
| 1 | Normalization rate | ≥ 15% of findings | Reviewers not following schema reliably | `normalization_rewrites` / `raw_finding_count` per run |
| 2 | Cross-run determinism | ≥ 2/5 runs produce different synthesis | Synthesis procedure too context-dependent | Same spec, multiple runs, diff comparison |
| 3 | Cross-run inconsistency | Same spec, materially different reports | Lead context polluting synthesis | Same as #2, broader scope |
| 4 | Synthesis duration | > 3 minutes | Procedure too complex for inline execution | Wall-clock timing during Phase 5 |
| 5 | P0 missed | Any P0 found by re-review that synthesis dropped | Synthesis errors are the highest-risk failure | Post-run re-review by a separate reviewer |

## Preflight Packet

The preflight packet is written to `.review-workspace/preflight/packet.md` during Phase 3C. Reviewers receive the file path in their spawn prompt — the packet is **not** embedded inline. This eliminates the ~1000 char embedding budget constraint and prevents destructive compression for large specs.

Contains 6 sections:

| Section | Content | Purpose |
|---------|---------|---------|
| `authority_map` | File → normative/non-normative + source authority + review cluster | Reviewers know which files are authoritative and how they were classified |
| `boundary_edges` | Pairs of files with cross-references | Reviewers know where to look for cross-file invariants |
| `signal_matrix` | Optional specialist signals detected | Reviewers understand team composition rationale |
| `mechanical_checks` | Frontmatter validation results, broken links | Pre-computed checks reviewers can skip |
| `route_decision` | Why full team (not redirect) | Reviewers understand the routing rationale |
| `spawn_plan` | Which reviewers are spawned and why | Each reviewer sees the full team composition |

## Workspace Structure

```
.review-workspace/
├── preflight/
│   └── packet.md                    # Preflight analysis results
├── findings/
│   ├── authority-architecture.md    # AA findings
│   ├── contracts-enforcement.md     # CE findings
│   ├── completeness-coherence.md    # CC findings
│   ├── verification-regression.md   # VR findings
│   ├── schema-persistence.md        # SP findings (if spawned)
│   └── integration-enforcement.md   # IE findings (if spawned)
└── synthesis/
    ├── ledger.md                    # Synthesis ledger (structured intermediate artifact)
    └── report.md                    # Final synthesized report
```

**Cleanup:** After presenting findings, ask user whether to preserve or remove workspace. Default: preserve.

**Gitignore:** The lead should verify `.review-workspace/` is in `.gitignore` before creating the workspace. If absent, add it. The workspace is a transient review artifact — it must not be committed.

### Spawn Prompt Contract

Each spawn prompt contains three components. Full prompt templates belong in `role-rubrics.md`; the design doc specifies the delivery contract.

| Component | Content | Mandatory Fields |
|-----------|---------|-----------------|
| Shared scaffold | Finding schema (including `provenance` and `prompted_by` fields), workspace path, output file path, path to `packet.md`, output rules | Finding schema definition, output file path, `packet.md` path, "no prose between findings" rule, coverage notes requirement, provenance disclosure requirement |
| Preflight pointer | Path to `.review-workspace/preflight/packet.md` — reviewer reads the file at runtime | File path only (not content) |
| Role delta | Domain brief with 8 components (see below) | Role ID, defect class scope, mission statement |

**Delivery model:** Spawn prompts point reviewers to the workspace file. Reviewers read `packet.md` themselves — the lead does not condense or embed it. This means the packet can scale with spec complexity without degrading spawn prompt quality.

**Instruction philosophy for role delta:** Rubrics are domain briefs that orient judgment, not checklists that constrain it. The reviewer's scope is the defect class domain, not a list of prescribed checks. This matches the codebase's dominant pattern: `explore-repo`, `handbook`, and `reviewing-designs` all use domain briefs with judgment-shaping language, not mechanical checklists.

**8-component domain brief structure** (specified in `role-rubrics.md`):

| # | Component | Purpose | Example |
|---|-----------|---------|---------|
| 1 | Mission | One-sentence defect class scope | "Find defects where the spec's authority hierarchy is violated, misplaced, or internally inconsistent" |
| 2 | High-yield surfaces | Where to focus attention first | "Boundary edges between normative and non-normative files in the authority map" |
| 3 | Common defect patterns | What defects look like in this domain — examples, not exhaustive list | "Invariant drift: a normative constraint evolves across files without updating the source" |
| 4 | Priority calibration | What P0/P1/P2 mean for this defect class | "P0: an implementer would build the wrong thing. P2: authority metadata is imprecise but content is consistent" |
| 5 | Collaboration playbook | Concrete per-role messaging triggers (3-5 conditions with named reviewer IDs) | "If you find an authority placement error, message `contracts-enforcement` — they should check whether contracts reference the misplaced authority" |
| 6 | Coverage floor | Minimum areas that must be examined for coverage notes | "Every normative file in the authority map must be checked" |
| 7 | Disconfirmation check | One quick falsification attempt per material finding | "Before reporting, ask: could this apparent violation be intentional? Check the decisions log for rationale" |
| 8 | Output examples | 1-2 exemplar findings showing schema compliance and appropriate detail level | (in `role-rubrics.md`) |

**Reviewer stance: defect hunter, not conviction maximizer.** Reviewers should investigate their domain thoroughly but also attempt to disconfirm their own findings before reporting. A finding that survives the reviewer's own skepticism is higher quality than one reported uncritically.

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| No frontmatter on any file | DISCOVERY phase finds 0 normative files | Degraded discovery: classify by path heuristics, warn user. Phase 3A mechanical validation produces zero results (no frontmatter fields to validate) — proceed directly to cluster routing. Degraded mode disables: (1) redirect gate (always full team), (2) authority-derived specialist spawning (core only), (3) authority-based contradiction adjudication (escalate all contradictions as ambiguity). Source authority recorded as `unknown` for all files. |
| > 50% ambiguous cluster assignments | ROUTING phase computation | All-core team (no specialists), flag ambiguity as meta-finding |
| Teammate produces prose instead of structured findings | SYNTHESIS phase normalization | Lead normalizes to schema, increments `normalization_rewrites` metric |
| Agent teams not enabled | Prerequisite check | Hard stop: "Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1. Do not fall back." |
| Teammate fails to write findings file | REVIEW phase verification | Wait for idle notification, then check. If file missing after idle, increment `reviewers_failed` metric. |
| Teammate hangs (no idle notification) | REVIEW phase wall-clock timeout | After 5 minutes with no new idle notifications, treat remaining teammates as failed. Proceed to SYNTHESIS with available findings; increment `reviewers_failed` metric. |
| `TeamCreate` fails | Phase 4 spawn contract step 2 | Hard stop: "Team creation failed: {error}. Cannot proceed without agent team." Report error to user. |
| Reviewer spawn fails (`Agent` tool error) | Phase 4 spawn contract step 4 | Log failed reviewer in `reviewers_failed` with reason "spawn failure: {error}". Continue spawning remaining reviewers. If all spawns fail, hard stop. |
| Partial workspace from failed run | Next invocation's DISCOVERY phase | If `.review-workspace/` exists at start, warn user and offer: (a) archive to `.review-workspace.bak/`, (b) remove, (c) abort. Do not silently overwrite. |

## Decisions Log

Confidence levels: **High** = converged across multiple independent sources (Codex dialogues, codebase evidence, user confirmation). **Medium** = single-source confirmation or user decision without independent stress-testing.

| # | Decision | Choice | Key Rationale | Confidence |
|---|----------|--------|---------------|------------|
| 1 | Scope | General multi-file spec review (not Engram-specific) | Authority/normative frontmatter pattern is reusable; spec-modulator produces exactly this structure | High |
| 2 | Architecture | A' (normative SKILL.md + operational refs) | Emerged from comparative Codex dialogue; synthesis needs explicit intermediate structure, not fresh context | High |
| 3 | Team composition | 4 core + 2 optional, domain-agnostic core names | Converged across 3 independent Codex consultations; fully adaptive has silent staffing failures | High |
| 4 | Routing proxy | Authority-boundary clusters, not file count | "A 3-file spec spanning 3 authority tiers is more complex than a 10-file spec in one tier" | High |
| 5 | Finding format | Atomic schema with `violated_invariant` field | Finding-level canonicalization requires explicit intermediate state; `violated_invariant` enables cross-reviewer merge | High |
| 6 | Lifecycle positioning | Create (spec-modulator) → Review (spec-review-team) | User-identified synergy confirmed by shared frontmatter conventions | Medium |
| 7 | Preflight delivery | Workspace file, not embedded in spawn prompt | Eliminates destructive compression; scales with spec complexity; workspace file already exists | Medium |
| 8 | Dedup merge key | `(violated_invariant, normalized_affected_surface)` | `fix_scope` is not a schema field; surface + invariant is sufficient for exact-duplicate detection. Post-reframing (Decision #10): this is the mechanical starting point — the lead applies semantic judgment beyond it. | High |
| 9 | Lateral messaging | Encouraged via `message` and `broadcast` primitives | Agent teams' primary value over subagents is inter-teammate communication; docs explicitly describe "share and challenge findings" as the review use case | High |
| 10 | Instruction philosophy | Technique-in-Discipline-shell: prescribe contracts, not algorithms. Synthesis uses judgment obligations with rationale requirements and a testable ledger. Reviewer rubrics are 8-component domain briefs, not checklists. | The spec was most prescriptive where Claude's judgment adds the most value. All existing codebase skills use domain briefs. Codex dialogue #33 converged on the reframing. Boundary rule: "prescribe computation for auditable state, criteria for meaning." | High |

## Open Questions

1. **Synthesis ledger format and location.** The ledger is specified as `.review-workspace/synthesis/ledger.md`. Is markdown the right format, or should it be structured YAML/JSON for machine-checkable invariant validation? Calibrate after first runs.

2. **Consistency-check ownership.** Does the lead perform a required self-check of ledger invariants before Phase 5 completes, or is there a future hook/script path for automated validation?

3. **Support taxonomy metric mapping.** How do `independent_convergence`, `cross_lens_followup_confirmation`, `related_pattern_extension`, and `singleton` map to the existing `corroborated_findings` audit metric? Currently defined as the first two types — calibrate after first runs.

4. **Provenance threshold definition.** What counts as `followup` for reviewer tagging: any lateral message seen, or only a message that materially redirected inspection? The provenance field's reliability depends on this definition.

5. **Confidence field semantics.** Should reviewer `confidence` be renamed to `reviewer_confidence`, and does synthesis need a separate `synthesis_confidence` field on ledger records?

6. **Preflight staffing model.** Should numeric signal scores be replaced with coarse evidence classes (`strong`/`suggestive`/`weak`), kept as internal heuristics in `preflight-taxonomy.md`, or some hybrid?

7. **A-to-B upgrade trigger thresholds uncalibrated.** The 5 triggers are post-v1 calibration metrics. First runs should record raw data.

8. **Cluster taxonomy vocabulary — fixed vs derived.** The 6 canonical review clusters are hardcoded. Revisit if specs from other domains fail to classify cleanly.

9. **Potential third optional specialist.** API specs with complex schema evolution may warrant it. Deferred for v1.

## References

| Resource | Path | Relevance |
|----------|------|-----------|
| explore-repo SKILL.md | `.claude/skills/explore-repo/SKILL.md` | Reference implementation for agent team skills |
| reviewing-designs SKILL.md | `.claude/skills/reviewing-designs/SKILL.md` | Closest structural precedent for A' architecture |
| spec-modulator SKILL.md | `.claude/skills/spec-modulator/SKILL.md` | Lifecycle partner — creates specs this skill reviews |
| skills-guide.md | `docs/references/skills-guide.md` | SKILL.md quality checklist, ~500-line threshold |
| writing-principles.md | `docs/references/writing-principles.md` | Instruction document writing principles |
| Codex dialogue #29 | Thread `019cee6c-...` | Team composition convergence |
| Codex dialogue #30 | Thread `019cef00-...` | Composition deep dive, domain-agnostic names |
| Codex dialogue #31 | Thread `019cef18-...` | Architecture comparison — A' emergence |
| Codex dialogue #32 | Thread `019cef71-...` | Design quality audit — P0 execution contract, 8 P1s |
| Codex dialogue #33 | Thread `019cf2fe-...` | Instruction philosophy — synthesis ledger, provenance, domain briefs |
| Codex consultation (sampling) | Thread `019cf2bf-...` | Sampling constraint as invariant, not hard cap |
| Agent teams platform docs | `code.claude.com/en/agent-teams`, `hooks` | Authoritative source for team tool behavior, hook constraints, cost model |

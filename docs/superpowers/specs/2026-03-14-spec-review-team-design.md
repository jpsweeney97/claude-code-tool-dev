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
  Review multi-file specifications using a parallel agent team. Discovers spec
  structure via frontmatter metadata, runs preflight analysis, spawns 4-6
  specialized reviewers with distinct defect-class lenses, and synthesizes
  findings into a prioritized report. Use when reviewing a spec corpus with
  files across multiple authority tiers. For single design documents, use
  reviewing-designs instead.
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - TeamCreate
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
3. **Teammates don't inherit lead context.** Reviewer context comes from spawn prompts + workspace files (preflight packet). Spawn prompts contain role-specific instructions; reviewers read `packet.md` from the workspace at runtime.
4. **One team per session.** No nested teams, no session resumption.
5. **3-5 teammates recommended.** Core team of 4 is within range; 6 total (with optionals) is the maximum.

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
    ├── preflight-taxonomy.md         # Operational: cluster definitions, signal dimensions, scoring weights
    ├── role-rubrics.md               # Operational: per-role defect catalogs, hunt priorities, rubric items
    ├── synthesis-procedure.md        # Operational: dedup/corroborate/adjudicate algorithms, worked examples
    └── failure-patterns.md           # Operational: degraded modes, troubleshooting, recovery procedures
```

**SKILL.md owns:** Procedure flow, gates, spawn logic, constraints, finding schema definition, workspace conventions, audit metrics, upgrade triggers.

**Reference files own:** Detailed taxonomies, rubrics, scoring weights, worked examples, troubleshooting guides.

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
2. Create one task per reviewer via `TaskCreate`. Task description includes: reviewer role ID, output file path, and pointer to `packet.md`.
3. Use `TeamCreate` to create the team with all reviewers. `TeamCreate` is a natural-language tool — describe the team composition and each teammate's role, including their spawn prompts. If `TeamCreate` is a deferred tool, fetch it with `ToolSearch` first.
4. Do **not** use the `Agent` tool as a substitute for `TeamCreate`. The Agent tool lacks teammate-to-teammate messaging, coordinated idle notifications, and shared task state. Agent teams and the Agent tool are not interchangeable.
5. Do **not** start the lead's own analysis before all teammates are spawned.

**Completion contract:**
- **Source of truth:** Idle notifications from the team system. Each spawned reviewer produces exactly one idle notification when done.
- **Expected idle count:** Number of reviewers in the spawn plan (4 for core-only, 5 or 6 with optionals).
- **Verification:** After receiving all expected idle notifications, verify each reviewer's findings file exists in `.review-workspace/findings/`. If a file is missing after its reviewer went idle, log as `reviewers_failed` ("reviewer {id} went idle without writing findings").
- **Wall-clock timeout:** 5 minutes after the last idle notification. If expected idle count is not reached, treat remaining reviewers as failed. Proceed to SYNTHESIS with available findings; log missing reviewers as `reviewers_failed`.
- **No lateral messaging:** Reviewers do not communicate with each other. All coordination flows through the findings ledger and the lead's synthesis. Do not enable cross-reviewer `SendMessage`.

**Cleanup contract:**
1. After PRESENT, shut down all teammates via `SendMessage` with `type: shutdown_request`.
2. Ask user whether to preserve or remove `.review-workspace/`. Default: preserve.
3. Remove team files and task files regardless of workspace decision.

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

**Dimensions:** Frontmatter authority, file naming, content keywords, cross-reference patterns, cluster membership.

**Cap:** 2 spot-reads per specialist, 4 total across both optionals. Specialists augment core reviewers — they do not replace them.

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
```

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

## Synthesis Procedure

### Pipeline

1. **Canonicalize** — normalize finding format, fix minor schema violations, increment `normalization_rewrites` metric
2. **Dedup** — exact-duplicate key: `(violated_invariant, normalized_affected_surface)`. Two findings with the same invariant and same surface are duplicates regardless of `recommended_fix` text. Merged findings list all contributing reviewer IDs; divergent fixes become alternatives within the canonical finding.
3. **Cluster related findings** — group findings by `affected_surface` and/or boundary edge. Related-but-distinct findings (e.g., authority placement error + contract contradiction at the same file boundary) are linked with a relation type: `same-root-cause`, `same-surface-distinct-defect`, or `cause/effect`. This enables corroboration to detect multi-lens convergence on a surface, not just on an invariant.
4. **Corroborate** — findings from 2+ different lenses get confidence boost. Corroborated findings are tagged with contributing lenses. Related-finding clusters (step 3) with 2+ lenses also count as corroboration.
5. **Adjudicate contradictions** — when reviewers disagree:
   - Normative source > non-normative source (use source authority from authority map, not review cluster)
   - If same authority level → escalate as ambiguity finding (P1, prefix `SY` for synthesis-generated, field `violated_invariant` = "cross-reviewer contradiction")
6. **Verify deferrals** — for each coverage note with `deferred_to`, check the target reviewer's findings cover that defect class. Unverified deferrals become meta-findings (P1, prefix `SY`: "coverage gap — deferred check not picked up").
7. **Prioritize** — sort by: P0 → P1 → P2, then corroboration count (including cluster-level), then confidence
8. **Compute audit metrics**

### 10 Audit Metrics

| # | Metric | Description |
|---|--------|-------------|
| 1 | `raw_finding_count` | Total findings before canonicalization |
| 2 | `canonical_finding_count` | Findings after dedup |
| 3 | `duplicate_clusters_merged` | Number of dedup merges |
| 4 | `related_finding_clusters` | Number of surface-linked finding groups (step 3). Reporting-only — not used as a gate or threshold. |
| 5 | `corroborated_findings` | Findings confirmed by 2+ lenses (including cluster-level) |
| 6 | `contradictions_surfaced` | Inter-reviewer disagreements |
| 7 | `normalization_rewrites` | Findings that needed schema repair |
| 8 | `ambiguous_review_clusters` | Files with uncertain review cluster assignment |
| 9 | `reviewers_failed` | Reviewers that timed out or went idle without producing findings (in-run observable) |
| 10 | `unverified_deferrals` | Coverage notes with `deferred_to` targets that did not cover the delegated class |

**Removed:** `synthesis_errors_p0` and `reviewers_failed`. These require an oracle (the lead cannot reliably detect its own synthesis errors in-run). They are replaced by `reviewers_failed` (observable) and `unverified_deferrals` (observable). Cross-run synthesis quality is tracked via the A-to-B upgrade triggers, which are post-v1 calibration metrics, not in-run audit metrics.

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
    └── report.md                    # Final synthesized report
```

**Cleanup:** After presenting findings, ask user whether to preserve or remove workspace. Default: preserve.

### Spawn Prompt Contract

Each spawn prompt contains three components. Full prompt templates belong in `role-rubrics.md`; the design doc specifies the delivery contract.

| Component | Content | Mandatory Fields |
|-----------|---------|-----------------|
| Shared scaffold | Finding schema, workspace path, output file path, path to `packet.md`, output rules | Finding schema definition, output file path, `packet.md` path, "no prose between findings" rule, coverage notes requirement |
| Preflight pointer | Path to `.review-workspace/preflight/packet.md` — reviewer reads the file at runtime | File path only (not content) |
| Role delta | Defect class description, hunt priorities, rubric items | Role ID, defect class scope, primary file focus areas |

**Delivery model:** Spawn prompts point reviewers to the workspace file. Reviewers read `packet.md` themselves — the lead does not condense or embed it. This means the packet can scale with spec complexity without degrading spawn prompt quality.

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| No frontmatter on any file | DISCOVERY phase finds 0 normative files | Degraded discovery: classify by path heuristics, warn user. Degraded mode disables: (1) redirect gate (always full team), (2) authority-derived specialist spawning (core only), (3) authority-based contradiction adjudication (escalate all contradictions as ambiguity). Source authority recorded as `unknown` for all files. |
| > 50% ambiguous cluster assignments | ROUTING phase computation | All-core team (no specialists), flag ambiguity as meta-finding |
| Teammate produces prose instead of structured findings | SYNTHESIS phase normalization | Lead normalizes to schema, increments `normalization_rewrites` metric |
| Agent teams not enabled | Prerequisite check | Hard stop: "Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1. Do not fall back." |
| Teammate fails to write findings file | REVIEW phase verification | Wait for idle notification, then check. If file missing after idle, increment `reviewers_failed` metric. |
| Teammate hangs (no idle notification) | REVIEW phase wall-clock timeout | After 5 minutes with no new idle notifications, treat remaining teammates as failed. Proceed to SYNTHESIS with available findings; increment `reviewers_failed` metric. |
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
| 8 | Dedup merge key | `(violated_invariant, normalized_affected_surface)` | `fix_scope` is not a schema field; surface + invariant is sufficient for exact-duplicate detection | High |

## Open Questions

1. **Dedup boundary calibration.** The merge key is now `(violated_invariant, normalized_affected_surface)` — but "normalized" is undefined. What normalization applies to `affected_surface`? (Path canonicalization? Section-level granularity?) Needs calibration after first runs.

2. **A-to-B upgrade trigger thresholds uncalibrated.** The 5 triggers are post-v1 calibration metrics with no persistence or evaluation owner in v1. First runs should record raw data for eventual evaluation.

3. **Potential third optional specialist.** API specs with complex schema evolution may warrant it. Deferred for v1.

4. **Cluster taxonomy vocabulary — fixed vs derived.** The 6 canonical review clusters are currently hardcoded. Whether this vocabulary should be configurable or domain-derived is unresolved. For v1, the fixed vocabulary covers known specs; revisit if specs from other domains fail to classify cleanly.

5. **Compound defect clustering relation types.** The three relation types (`same-root-cause`, `same-surface-distinct-defect`, `cause/effect`) are a starting set. Whether the lead can reliably assign these without domain knowledge is untested.

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

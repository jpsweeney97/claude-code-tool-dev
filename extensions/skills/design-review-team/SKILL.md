---
name: design-review-team
description: Thorough architecture review using a parallel agent team of 6 specialized reviewers. Each reviewer analyzes the design through a category-specific lens (Structural+Cognitive, Behavioral, Data, Reliability+Operational, Change, Trust & Safety), communicating cross-cutting findings via lateral messaging. The lead frames the review, generates an emphasis map, spawns the team, then synthesizes findings into a prioritized report with tension mapping. Use when the user asks for a "thorough design review", "deep architecture review", "team review of this design", "comprehensive design analysis", or wants maximum coverage of an architecture. Also trigger when the design is complex enough to benefit from multiple review perspectives — multi-service architectures, systems with cross-cutting concerns, or high-stakes designs. For quick single-pass reviews, use system-design-review instead.
allowed-tools:
  - Read
  - Write
  - Edit
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
argument-hint: "[target — e.g., 'the auth service design doc', 'this codebase architecture', or describe the system verbally.]"
---

# Design Review Team

Review system architecture using a parallel team of 6 specialized reviewers. Each reviewer analyzes the design through a different category lens, communicating cross-cutting findings in real time via lateral messaging. The lead orchestrates framing, team composition, and synthesis.

**Guiding question throughout:** "Was this a conscious decision, or an inherited default?"

**Announce at start:** "I'm using the design-review-team skill for a thorough architecture review with parallel reviewers."

## When to Use

- Complex architectures benefiting from multiple simultaneous review perspectives
- High-stakes designs where coverage depth matters more than speed
- Systems with significant cross-cutting concerns (security↔performance, consistency↔availability)
- Multi-service architectures, distributed systems, or platform-level designs
- Trigger phrases: "thorough design review", "deep architecture review", "team review", "comprehensive design analysis", "review this architecture thoroughly"

## When NOT to Use

- Quick assessments or single-pass reviews → use `system-design-review`
- Code-level bug review → use a code review skill
- Multi-file specifications with frontmatter metadata → use `spec-review-team`
- Incident post-mortems, debt prioritization, refactoring sequencing → see handoff table in `system-design-review`

## Prerequisites

**Agent teams required.** Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential review.

## Team Composition

Six reviewers, each scoped by **category remit** (not file assignment). All reviewers access all design artifacts — scoped by analytical lens, not material partition.

| # | Role | ID | Categories |
|---|------|----|-----------|
| 1 | Structural + Cognitive | `structural-cognitive` | Structural (7 lenses) + Cognitive (5 lenses) |
| 2 | Behavioral | `behavioral` | Behavioral (8 lenses) |
| 3 | Data | `data` | Data (5 lenses) |
| 4 | Reliability + Operational | `reliability-operational` | Reliability (5 lenses) + Operational (5 lenses) |
| 5 | Change | `change` | Change (6 lenses) |
| 6 | Trust & Safety | `trust-safety` | Trust & Safety (5 lenses) |

**Pairing principle: evidence-surface coherence.** Categories are paired when they share the same artifacts and analytical frame — Structural and Cognitive both analyze boundary diagrams and naming conventions; Reliability and Operational both analyze failure and recovery paths. Asymmetry across reviewers is intentional: some reviewers have more lenses because their categories are genuinely larger.

**Finding ID prefixes:**

| Prefix | Reviewer |
|--------|----------|
| `SC` | structural-cognitive |
| `BH` | behavioral |
| `DA` | data |
| `RO` | reliability-operational |
| `CH` | change |
| `TS` | trust-safety |
| `SY` | lead (synthesis) |

## Procedure

`Frame → Staff → Review → Synthesize → Deliver`

### Phase 1: Frame

Frame the review the same way the single-agent skill does. Read the input, then determine:

1. **Scope level** — choose one: `system`, `subsystem`, or `interface`. Do not mix scope levels.
2. **Archetype identification** — infer top 1-2 archetypes from the 6 available (Internal tool, User-facing API, Data pipeline, Financial/regulated, ML/research, Event-driven/streaming). State confidence.
3. **Stakes calibration** — propose `low`, `medium`, or `high` using the same decision order and high-risk cues as `system-design-review`.
4. **Evidence map** — catalog available evidence: design docs, codebase paths, verbal descriptions.
5. **Emphasis map** — generate per-reviewer emphasis from archetype weighting. See [`references/staffing-rules.md`](references/staffing-rules.md) for the algorithm.

**Checkpoint C0:** For high stakes with scope or archetype uncertainty, share the framing with the user before spawning. Otherwise, state the framing and proceed.

### Phase 2: Staff

Apply the staffing rules from [`references/staffing-rules.md`](references/staffing-rules.md):

1. **Suppression check** — for each reviewer, check if ALL of their owned categories are scope-inapplicable. Suppress only if the entire reviewer has no meaningful surface. When in doubt, spawn at `background` emphasis.
2. **Redirect threshold** — if 2+ reviewers would be suppressed, redirect to `system-design-review` instead. The team approach adds overhead; with that many categories inapplicable, a single-pass review is sufficient.
3. **Tension playbooks** — generate per-run collaboration playbooks from the tension registry intersected with the active roster and emphasis map. See [`references/tension-registry.md`](references/tension-registry.md).
4. **Announce roster** — "Spawning [N] reviewers: [role IDs]. [Suppression rationale if any.]"

### Phase 3: Review

#### Spawn Contract

1. Verify `.design-review-workspace/` is in `.gitignore`. If absent, add it.
2. Write framing context to `.design-review-workspace/framing/frame.md` (scope, archetype, stakes, emphasis map, evidence map, input pointers).
3. Create team via `TeamCreate` with `team_name: "design-review"`. Fetch via `ToolSearch` if deferred.
4. Create one task per reviewer via `TaskCreate`. No `blockedBy` dependencies — all run in parallel.
5. Spawn each reviewer via `Agent` with `team_name`, `name` (role ID), `model: "sonnet"`, and `prompt` containing:
   - Role ID and categories owned
   - Emphasis level for their categories (from emphasis map)
   - Path to `frame.md` for full framing context
   - Instruction to read their section of [`references/reviewer-briefs.md`](references/reviewer-briefs.md) for role brief and collaboration playbook
   - Instruction to read shared [`references/system-design-dimensions.md`](references/system-design-dimensions.md) for full lens definitions
   - Per-run tension playbook entries (generated in Phase 2)
   - Output file path: `.design-review-workspace/findings/{role-id}.md`
   - Finding schema (inline in spawn prompt — too critical to rely on file reference for Sonnet)
6. Do NOT start the lead's own analysis before all teammates are spawned.

#### Completion Contract

- **Primary signal:** idle notifications from the team system.
- **Secondary signal:** task status via `TaskGet` (known to lag).
- **Peer DM visibility:** DM summaries appear in idle notifications — use as synthesis input.
- **Timeout:** 5 minutes with no new idle notifications and no task status changes.
- **Partial completion:** always proceed with available findings. Report failed reviewers.

#### Lateral Messaging

Spawn prompts include collaboration playbooks (from `references/reviewer-briefs.md`) with specific "if you find X, message reviewer-Y" triggers, plus per-run tension playbook entries from Phase 2.

- `message` — targeted to one reviewer by name. Use for cross-lens findings.
- `broadcast` — to `"*"` (all teammates). Reserve for discoveries affecting everyone. Costs scale linearly with team size.

Messages are informal coordination signals — each reviewer's structured findings file is the sole formal deliverable.

#### Cleanup

Follow the cleanup resilience protocol from the agent teams reference. Teammates must NOT self-cleanup. Only the lead manages shutdown and TeamDelete.

1. **Shutdown loop** — for each reviewer, send up to 3 shutdown requests with escalating context:
   - Attempt 1: `{type: "shutdown_request", reason: "Review complete"}`
   - Attempt 2 (if no idle after 60s): "All findings have been saved. Review is complete. Please shut down."
   - Attempt 3 (if no idle after 60s): "Session ending. Cleanup requires all reviewers to shut down. This is the final request."
   - If no idle after 30s: classify as **orphaned** with reason.
2. **TeamDelete** — call `TeamDelete`. If it fails (orphaned reviewers still active), report degraded state to user:
   "Team cleanup partially failed: [N] reviewer(s) did not shut down ([names]). Team resources may remain at `~/.claude/teams/design-review/`. These will be cleaned up when a new team is created, or remove manually."
3. **Workspace** — prompt user about preserving `.design-review-workspace/`. Workspace cleanup is independent of team cleanup — always attempt it regardless of TeamDelete outcome.

### Phase 4: Synthesize

Read all findings files and idle notification DM summaries. Execute in order.

#### Mechanical Passes

1. **Canonicalize** — normalize format across findings files. Count `normalization_rewrites` for each schema repair.
2. **Build synthesis ledger** at `.design-review-workspace/synthesis/ledger.md` — one record per canonical finding.
3. **Compute audit metrics** (see table below).

#### Judgment Obligations

**Consolidate and deduplicate.** Two findings are the same defect when they share `lens` and `anchor` with the same underlying concern. Merged findings list all contributor IDs with `merge_rationale`.

**Assess corroboration.** Classify each finding's `support_type`:
- `independent_convergence` — multiple reviewers found independently (both `provenance: independent`)
- `cross_lens_followup_confirmation` — one flagged, another confirmed via followup
- `related_pattern_extension` — distinct findings at same surface reveal a larger pattern
- `singleton` — single-reviewer finding

**Resolve contradictions.** When reviewers disagree, resolve with evidence quality and domain reasoning. Unresolvable contradictions escalate as ambiguity findings (P1, `SY` prefix). Record `adjudication_rationale` for every resolved contradiction.

**Map tensions.** Read [`references/tension-registry.md`](references/tension-registry.md). For each canonical or custom tension with concrete anchors in the findings, emit a tension record. Custom tensions are valid when all inclusion rules pass. `0` tensions is a valid count — do not force one.

**Prioritize.** P0 > P1 > P2 baseline. Corroboration and confidence as secondary tiebreakers. Record `priority_rationale` only when ranking departs from baseline.

#### Audit Metrics

| # | Metric | Description |
|---|--------|-------------|
| 1 | `raw_finding_count` | Total findings before canonicalization |
| 2 | `canonical_finding_count` | After consolidation and dedup |
| 3 | `duplicate_clusters_merged` | Number of consolidation merges |
| 4 | `corroborated_findings` | Findings with `independent_convergence` or `cross_lens_followup_confirmation` |
| 5 | `contradictions_surfaced` | Resolved + escalated contradictions |
| 6 | `normalization_rewrites` | Schema repairs during canonicalization |
| 7 | `reviewers_failed` | Per-reviewer ID + reason for missing findings |
| 8 | `tensions_mapped` | Canonical + custom tensions emitted |

#### Ledger Format

```markdown
### [SY-N] Canonical finding title

- **source_findings:** SC-1, RO-3
- **support_type:** independent_convergence
- **contributors:** structural-cognitive, reliability-operational
- **merge_rationale:** "..."
- **adjudication_rationale:** (if applicable)
- **priority_rationale:** (if non-obvious)
```

### Phase 5: Deliver

Write the final report to `.design-review-workspace/synthesis/report.md`. Use the 5-part structure from the single-agent skill, extended for team review:

**1. Review Snapshot** — finding counts by priority, team composition, coverage assessment, audit metrics.

**2. Focus and Coverage** — scope, archetypes, stakes, emphasis map, one-line status per category (deep / screened / insufficient evidence / not applicable), per-reviewer summary.

**3. Findings** — labeled `F1`, `F2`, etc. Each includes: lens, decision state, anchor, problem, impact, recommendation/question, corroboration evidence (if any). Ordered by priority.

**4. Tension Map** — labeled `T1`, `T2`, etc. Each includes: tension name, what's being traded, why it hid, likely failure story, linked findings. Emit only when all inclusion rules pass (see `references/tension-registry.md`).

**5. Questions / Next Probes** — 2-4 sharp questions. No verdict unless explicitly requested.

#### Depth Calibration

| Stakes | Finding target | Hard cap | Tension cap |
|--------|---------------|----------|-------------|
| `low` | 4-8 | 10 | 0-2 |
| `medium` | 8-14 | 16 | 1-3 |
| `high` | 12-20 | 22, or 25 with appendix | 2-5 |

Team reviews produce more findings than single-agent reviews — these caps are proportionally higher.

#### Decision State Taxonomy

Reused unchanged from the single-agent skill:

| State | When to use |
|-------|-------------|
| `explicit tradeoff` | The design names both sides and makes a conscious choice. |
| `explicit decision` | A conscious choice is visible, but not framed as a tradeoff. |
| `default likely inherited` | No local rationale visible and the choice matches a framework default or legacy pattern. Requires positive evidence of a default. |
| `underspecified` | The system must decide something here, but the choice is not defined. |
| `not enough evidence` | The input is too sparse to classify safely. |

#### Durable Record

If the user asks to save or `docs/audits/` exists, also write to `docs/audits/YYYY-MM-DD-<target-slug>-team.md`.

After delivery, execute Phase 3 cleanup (shutdown + TeamDelete). Prompt user about preserving `.design-review-workspace/`.

## Finding Schema

Each reviewer writes findings using this schema. Do NOT improvise fields.

```markdown
### [PREFIX-N] Title

- **priority:** P0 / P1 / P2
- **lens:** Specific lens name from system-design-dimensions.md
- **decision_state:** explicit tradeoff / explicit decision / default likely inherited / underspecified / not enough evidence
- **anchor:** source_doc#section or file:lines
- **problem:** 1-2 sentences
- **impact:** 1-2 sentences
- **recommendation:** specific action or question
- **confidence:** high / medium / low
- **provenance:** independent / followup
- **prompted_by:** {reviewer-name} (required when followup; omit when independent)
```

### Coverage Notes

Mandatory when a reviewer has zero findings for any owned category.

| Field | Purpose |
|-------|---------|
| `scope_checked` | Files/sections examined |
| `checks_run` | Sentinel questions + specific checks |
| `result` | "No defects found" + rationale |
| `caveats` | Limitations (emphasis level, evidence gaps) |
| `deferred_to` | If another reviewer is better positioned |

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Agent teams not enabled | Prerequisite check | Hard stop |
| TeamCreate fails | Phase 3 spawn | Hard stop |
| Reviewer spawn fails | Phase 3 spawn | Log, continue. All fail = hard stop |
| Missing findings file | Phase 3 completion check | Log in `reviewers_failed`, proceed to synthesis |
| Teammate timeout (5 min) | No idle notification activity | Treat as failed, proceed with available findings |
| 2+ reviewers suppressed | Phase 2 staffing | Redirect to `system-design-review` |
| 4+ categories insufficient evidence | Phase 4 synthesis | Label `reduced-depth`, cap findings |
| TeamDelete fails | Phase 3 cleanup | Orphaned reviewers still active — report degraded state, proceed with workspace cleanup |
| Stale workspace | Phase 3 start | Warn, offer: archive / remove / abort |

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Dividing files among reviewers | Gaps at cross-file boundaries | All reviewers access all artifacts, scoped by lens |
| Lead deep-diving alongside reviewers | Duplicates work, biases synthesis | Lead frames and synthesizes; reviewers investigate |
| Forcing tensions for completeness | Generic tensions explain nothing | Emit only when all inclusion rules pass |
| Embedding entire briefs in spawn prompts | Context bloat for Sonnet reviewers | Point to reference files; inline only finding schema |
| Skipping coverage notes on zero findings | Cannot distinguish "checked and clean" from "didn't check" | Coverage notes are mandatory |

## References

| File | When to read |
|------|-------------|
| [`references/staffing-rules.md`](references/staffing-rules.md) | Phase 1-2: emphasis map generation, suppression rules, deep-lens cap |
| [`references/tension-registry.md`](references/tension-registry.md) | Phase 2 + Phase 4: per-run playbooks, tension inclusion rules, tension schema |
| [`references/reviewer-briefs.md`](references/reviewer-briefs.md) | Phase 3: role briefs with collaboration playbooks for spawn prompts |
| [`references/system-design-dimensions.md`](references/system-design-dimensions.md) | Shared lens framework: full lens definitions, archetype weighting, cross-cutting tensions |

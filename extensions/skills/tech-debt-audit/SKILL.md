---
name: tech-debt-audit
description: Thorough tech debt audit using a parallel agent team of 6 specialized auditors. Each auditor analyzes the system through a category-specific lens (Code Health, Architecture Drift, Dependency & Supply Chain, Test Debt, Operational & Observability, Knowledge & Documentation), communicating cross-cutting findings via lateral messaging. The lead frames the audit, generates an emphasis map, spawns the team, then synthesizes findings into a prioritized cleanup backlog with severity, leverage, and effort scoring plus quick-win clustering. Use whenever the user asks for a tech debt audit, technical debt audit, debt audit, code health audit, cleanup-sprint planning, refactoring backlog, or asks where their worst debt is, what they should refactor, what is blocking velocity, or wants a prioritized cleanup plan. Also trigger when the user wants to assess where debt is slowing the team, plan a maintenance sprint, surface dependency or security or operational drift, audit a codebase before a major refactor, evaluate state-of-the-codebase before handoff or scaling, or get a debt snapshot for engineering leadership. Prefer this skill any time a user mentions tech debt, technical debt, code debt, refactor planning, or cleanup priorities at codebase or service scope. For PR-scoped or single-file review this is overkill, but for any service-wide, package-wide, or repo-wide debt assessment this is the right tool.
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
argument-hint: "[target — e.g., 'this repo', 'the auth service', 'the data ingestion pipeline', or path to a directory/package.]"
---

# Tech Debt Audit Team

Audit a codebase for tech debt using a parallel team of 6 specialized auditors. Each auditor analyzes the system through a category-specific lens, communicating cross-cutting findings in real time via lateral messaging. The lead frames the audit, staffs the team, then synthesizes findings into a prioritized cleanup backlog.

**Guiding question throughout:** "Is this debt actively bleeding velocity, compounding cost, or just untidy?" Tidiness is not debt. Real debt has a name, a cost, and a payer.

**Announce at start:** "I'm using the tech-debt-audit skill for a thorough debt audit with parallel auditors."

## When to Use

- Codebase-wide, service-wide, or package-wide debt assessments
- Cleanup-sprint planning where the team needs a prioritized backlog
- New team taking ownership of an existing system
- Pre-scaling or pre-launch readiness checks against operational and performance debt
- Pre-refactor groundwork — understand the full debt landscape before committing to a direction
- Trigger phrases: "tech debt audit", "debt audit", "cleanup sprint", "refactoring backlog", "what should we refactor", "where's our worst debt", "audit our codebase for debt"

## When NOT to Use

- PR-scoped or single-file code review → use a code review skill
- Greenfield design before code exists → use `design-review-team`
- Incident response or bug triage — debt audits answer "what should we improve", not "what just broke"
- Documentation-only deliverables (README, handbook, CLAUDE.md) — those have dedicated skills

## Prerequisites

**Agent teams required.** Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment or settings.json env block.

If not enabled, hard stop: "This skill requires agent teams. Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your settings.json env block, then restart the session." Do NOT fall back to sequential audit.

## Team Composition

Six auditors, each scoped by **category remit** (not file assignment). All auditors access all of the codebase — scoped by analytical lens, not material partition.

| # | Role | ID | Categories |
|---|------|----|-----------|
| 1 | Code Health | `code-health` | Complexity hotspots, duplication, dead code, naming entropy, oversized modules, smells |
| 2 | Architecture Drift | `architecture-drift` | Boundary erosion, leaky abstractions, layering violations, coupling, circular deps, missing seams |
| 3 | Dependency & Supply Chain | `dependency` | Outdated packages, known CVEs, unmaintained libs, license risk, unused deps, version skew |
| 4 | Test Debt | `test-debt` | Coverage gaps, brittle/flaky tests, missing test layers, mocks-vs-reality drift, slow suites |
| 5 | Operational & Observability | `operational` | Missing logs/metrics/traces, brittle deploy/rollback, fragile bring-up, undocumented oncall paths, performance & scaling cliffs |
| 6 | Knowledge & Documentation | `knowledge` | Docs drifted from code, undocumented systems, single-owner code (bus factor), unowned modules, stale ADRs/runbooks |

**Pairing principle: evidence-surface coherence.** Operational owns both observability and performance/scalability because both are analyzed via runtime/deploy artifacts. Knowledge owns docs and ownership because both are read from comments, commits, and ownership files. Asymmetry across auditors is intentional: some have broader remits because their evidence surfaces are tightly coupled.

**Finding ID prefixes:**

| Prefix | Auditor |
|--------|---------|
| `CH` | code-health |
| `AD` | architecture-drift |
| `DP` | dependency |
| `TD` | test-debt |
| `OP` | operational |
| `KN` | knowledge |
| `SY` | lead (synthesis) |

## Procedure

`Frame → Staff → Audit → Synthesize → Deliver`

### Phase 1: Frame

Read the input and the codebase surface, then determine:

1. **Scope level** — choose one: `system`, `subsystem`, or `interface`. Do not mix.
   - `system` — whole repo / codebase / service
   - `subsystem` — a directory, package, layer, or bounded module
   - `interface` — a specific API surface, contract, or migration boundary
2. **Archetype identification** — infer top 1-2 archetypes from the 6 available (Long-lived application, Greenfield-on-legacy, High-velocity startup, Mature platform, Heavily integrated, Single-author project). State confidence. See [`references/debt-taxonomy.md`](references/debt-taxonomy.md).
3. **Stakes calibration** — propose stakes and proceed. Stakes control depth, finding count, and when to invite correction.
   - `low` — internal tooling, easy to rewrite, narrow blast radius
   - `medium` — meaningful blast radius, multi-team usage, or partial irreversibility
   - `high` — production-critical, external-facing, regulated, or near a major scaling event

   Use this decision order:
   1. Honor an explicit user depth request unless a higher-risk cue overrides it.
   2. If any high-risk cue is present, propose `high`.
   3. If all cues are low-risk, propose `low`.
   4. Otherwise, propose `medium`.
   5. If uncertain between two tiers, choose the higher tier.

   High-risk cues:
   - Production-critical service with SLAs
   - External or paying-customer-facing
   - Regulated data, payments, or trust boundary
   - Known active incidents or velocity complaints tied to debt
   - Pre-scaling event (launch, migration, traffic ramp)
   - Multi-team blast radius or shared platform

4. **Evidence map** — catalog available signals: source tree, dependency manifests, test directories, CI config, deploy config, observability config, ownership files (CODEOWNERS, README authors), git history density, TODO/FIXME density, ADRs, runbooks.
5. **Emphasis map** — generate per-auditor emphasis from archetype weighting. See [`references/staffing-rules.md`](references/staffing-rules.md) for the algorithm.

**Checkpoint C0:** For high stakes with scope or archetype uncertainty, share the framing with the user before spawning. Otherwise, state the framing and proceed.

### Phase 2: Staff

Apply the staffing rules from [`references/staffing-rules.md`](references/staffing-rules.md):

1. **Suppression check** — for each auditor, check if ALL of their owned subcategories are scope-inapplicable. Suppress only if the entire auditor has no meaningful surface. When in doubt, spawn at `background` emphasis.
2. **Tension playbooks** — generate per-run collaboration playbooks from the tension registry intersected with the active roster and emphasis map. See [`references/debt-taxonomy.md`](references/debt-taxonomy.md), "Cross-Cutting Tensions" section.
3. **Announce roster** — "Spawning [N] auditors: [role IDs]. [Suppression rationale if any.]"

### Phase 3: Audit

#### Preflight

Before any spawn or write:

1. **Workspace check** — if `.tech-debt-audit-workspace/` already exists, present options: archive (rename with timestamp suffix), remove, or abort. Do not silently overwrite.
2. **Team check** — no team-listing tool is available in this skill's `allowed-tools`. Executable check: if `~/.claude/teams/tech-debt-audit/` exists on disk, its activity is unprovable from outside the session — prompt the user to clean up via `TeamDelete` or abort. If the directory is absent, proceed; `TeamCreate` will hard-fail if the runtime still considers the team active.
3. **Write disclosure** — surface pending writes to the user: `.gitignore` entry (if missing), workspace directory at `.tech-debt-audit-workspace/`, and the durable report at `docs/audits/YYYY-MM-DD-<target-slug>-debt.md`. Proceed unless the user objects.

#### Spawn Contract

1. Add `.tech-debt-audit-workspace/` to `.gitignore` if not already listed.
2. Write framing context to `.tech-debt-audit-workspace/framing/frame.md` (scope, archetype, stakes, emphasis map, evidence map, input pointers).
3. Create team via `TeamCreate` with `team_name: "tech-debt-audit"`. Fetch via `ToolSearch` if deferred.
4. Create one task per auditor via `TaskCreate`. No `blockedBy` dependencies — all run in parallel. Record each task ID so it can be passed to the matching auditor in step 5.
5. Spawn each auditor via `Agent` with `team_name`, `name` (role ID), `model: "sonnet"`, and `prompt` containing:
   - Role ID and owned categories
   - Emphasis level for their categories (from emphasis map)
   - Path to `frame.md` for full framing context
   - Instruction to read their section of [`references/auditor-briefs.md`](references/auditor-briefs.md) for role brief, sentinel questions, and collaboration playbook
   - Instruction to read shared [`references/debt-taxonomy.md`](references/debt-taxonomy.md) for full lens definitions
   - Per-run tension playbook entries (generated in Phase 2)
   - Output file path: `.tech-debt-audit-workspace/findings/{role-id}.md`
   - Finding schema (inline in spawn prompt — too critical to rely on file reference for Sonnet)
   - Task ID assigned in step 4, with instruction to `TaskUpdate` to `in_progress` on start and `completed` when the findings file is written. This makes `TaskGet` a meaningful secondary completion signal.
6. Do NOT start the lead's own analysis before all teammates are spawned.

#### Completion Contract

- **Primary signal:** idle notifications from the team system.
- **Secondary signal:** task status via `TaskGet` (known to lag).
- **Peer DM visibility:** DM summaries appear in idle notifications — use as synthesis input.
- **Timeout:** 5 minutes with no new idle notifications and no task status changes.
- **Partial completion:** always proceed with available findings. Report failed auditors.

#### Lateral Messaging

Spawn prompts include collaboration playbooks (from `references/auditor-briefs.md`) with specific "if you find X, message auditor-Y" triggers, plus per-run tension playbook entries from Phase 2.

- `message` — targeted to one auditor by name. Use for cross-lens findings.
- `broadcast` — to `"*"` (all teammates). Reserve for discoveries affecting everyone (e.g., a single dependency upgrade unblocks 3 categories). Costs scale linearly with team size.

Messages are informal coordination signals — each auditor's structured findings file is the sole formal deliverable.

#### Cleanup

Follow the cleanup resilience protocol from [`references/agent-teams.md`](references/agent-teams.md). Teammates must NOT self-cleanup. Only the lead manages shutdown and TeamDelete.

**Workspace-preservation invariant.** The durable report (see Phase 5) must exist on disk before any workspace deletion. If the durable report is missing — for any reason — preserve `.tech-debt-audit-workspace/` regardless of user preference and surface the preservation to the user. This invariant overrides cleanup defaults; the only way the workspace gets deleted is durable report confirmed AND user opts to delete.

1. **Shutdown loop** — for each auditor, send up to 3 shutdown requests with escalating context. Classify as orphaned if no idle after attempt 3 + 30s.
2. **TeamDelete** — call `TeamDelete`. If it fails (orphaned auditors still active), report degraded state to user.
3. **Workspace** — only after the durable report is confirmed: prompt user "delete `.tech-debt-audit-workspace/` or keep?" Default to keep. If TeamDelete reported degraded state (orphaned auditors), preserve the workspace regardless — it may be the only record of partial findings.

### Phase 4: Synthesize

Read all findings files and idle notification DM summaries. Execute in order.

#### Mechanical Passes

1. **Canonicalize** — normalize format across findings files. Count `normalization_rewrites` for each schema repair.
2. **Carry technical substance verbatim** — before any scoring or prose work, copy each finding's `anchor` and `recommendation` **character-for-character** into the ledger's `verbatim_anchor` / `verbatim_recommendation` fields. Do not paraphrase, compress, or "clean up". Preserve every code identifier, file path, CLI flag, config snippet, and distinguishing qualifier — e.g. request vs. response, "CI runs the full suite", "as of <date>", "manual/unscanned", "requires a contract or spec change". These fields are the fidelity source of truth for Phase 5; the report is derived from them, not re-typed from memory.
3. **Build synthesis ledger** at `.tech-debt-audit-workspace/synthesis/ledger.md` — one record per canonical finding.
4. **Compute audit metrics** (see table below).

#### Judgment Obligations

**Consolidate and deduplicate.** Two findings are the same defect when they share `category` and `anchor` with the same underlying concern. Merged findings list all contributor IDs with `merge_rationale`.

**Score severity × leverage × effort.** Apply the rubric from [`references/severity-leverage-rubric.md`](references/severity-leverage-rubric.md). Severity is "how much pain this debt causes today"; leverage is "how much downstream pain its fix removes"; effort is "rough cost-to-remediate". Do not collapse these into a single P0/P1/P2 — the three-dimensional view is what makes the backlog actionable.

**Assess corroboration.** Classify each finding's `support_type`:
- `independent_convergence` — multiple auditors found independently (both `provenance: independent`)
- `cross_lens_followup_confirmation` — one flagged, another confirmed via followup
- `related_pattern_extension` — distinct findings at the same surface reveal a larger pattern
- `singleton` — single-auditor finding

**Cluster into backlog buckets.** Bucket every finding into one of four backlog sections (rubric in [`references/severity-leverage-rubric.md`](references/severity-leverage-rubric.md)):
- `quick-wins` — high severity, small effort, clear remediation
- `high-leverage` — high leverage (unblocks other categories), medium effort
- `strategic` — high severity but large effort (planning item, not sprint-sized)
- `watch` — currently low severity but trending; revisit later

**Map tradeoffs.** Read [`references/debt-taxonomy.md`](references/debt-taxonomy.md), "Cross-Cutting Tensions" section. For each tension with concrete anchors in the findings, emit a tradeoff record. Tradeoffs are *resource-allocation* questions, not design tradeoffs. Example: "Investing 4 weeks in architecture refactor delays the test-coverage push that operational debt depends on for safe deploy."

**Resolve contradictions.** When auditors disagree, resolve with evidence quality and domain reasoning. Unresolvable contradictions escalate as ambiguity findings (`SY` prefix). Record `adjudication_rationale` for every resolved contradiction.

#### Audit Metrics

| # | Metric | Description |
|---|--------|-------------|
| 1 | `raw_finding_count` | Total findings before canonicalization |
| 2 | `canonical_finding_count` | After consolidation and dedup |
| 3 | `duplicate_clusters_merged` | Number of consolidation merges |
| 4 | `corroborated_findings` | Findings with `independent_convergence` or `cross_lens_followup_confirmation` |
| 5 | `contradictions_surfaced` | Resolved + escalated contradictions |
| 6 | `normalization_rewrites` | Schema repairs during canonicalization |
| 7 | `auditors_failed` | Per-auditor ID + reason for missing findings |
| 8 | `quick_wins_count` | Findings bucketed as `quick-wins` |
| 9 | `strategic_count` | Findings bucketed as `strategic` |
| 10 | `tradeoffs_mapped` | Cross-cutting tradeoff records emitted |

#### Ledger Format

```markdown
### [SY-N] Canonical finding title

- **source_findings:** CH-1, TD-3
- **category:** code-health (primary), test-debt (corroborating)
- **support_type:** independent_convergence
- **contributors:** code-health, test-debt
- **verbatim_anchor:** source finding's `anchor`, copied character-for-character (never paraphrased)
- **verbatim_recommendation:** source finding's `recommendation`, copied character-for-character, including every distinguishing qualifier
- **severity:** P0 / P1 / P2 / P3
- **leverage:** high / medium / low
- **effort:** small / medium / large
- **bucket:** quick-wins / high-leverage / strategic / watch
- **merge_rationale:** "..."
- **adjudication_rationale:** (if applicable)
```

For a merged finding, the verbatim fields concatenate each contributor finding's text labeled by source ID — never a synthesized blend.

### Phase 5: Deliver

Write the final backlog report to `.tech-debt-audit-workspace/synthesis/report.md`. Use this 8-part structure:

**1. Audit Snapshot** — finding counts by severity and bucket, team composition, coverage assessment, audit metrics.

**2. Focus and Coverage** — scope, archetypes, stakes, emphasis map, one-line status per category (deep / screened / insufficient evidence / not applicable), per-auditor summary.

**3. Quick Wins** — bucket: `quick-wins`. Ordered by severity then leverage. Format: `QW1`, `QW2`, etc. Each item: title, category, anchor, problem, impact, recommendation, effort, leverage. These are the items an engineer could pick up today.

**4. High-Leverage Fixes** — bucket: `high-leverage`. Ordered by leverage then severity. Format: `HL1`, `HL2`, etc. Same fields as Quick Wins. These unblock other debt categories; mention which categories each unblocks.

**5. Strategic Items** — bucket: `strategic`. Ordered by severity. Format: `ST1`, `ST2`, etc. Same fields plus `planning_notes` describing why this can't be sprint-sized and what a planning sequence might look like.

**6. Watch List** — bucket: `watch`. Compact list. Format: `WL1`, `WL2`, etc. Title + 1-line rationale + suggested revisit trigger (e.g., "after next major version bump", "if test runtime exceeds 10min", "at next ownership transition").

**7. Tradeoff Map** — labeled `TR1`, `TR2`, etc. Each: tension name, what's being traded, why it hid, linked findings. Emit only when there are concrete anchors. `0` tradeoffs is a valid count — do not force one.

**8. Open Questions / Next Probes** — 2-4 sharp questions. No verdict unless explicitly requested.

#### Depth Calibration

| Stakes | Finding target | Hard cap | Quick-win target | Strategic cap | Tradeoff cap |
|--------|----------------|----------|------------------|---------------|--------------|
| `low` | 6-12 | 15 | 2-4 | 1-2 | 0-2 |
| `medium` | 12-22 | 25 | 4-8 | 2-4 | 1-3 |
| `high` | 18-30 | 35, or 40 with appendix | 6-12 | 3-6 | 2-5 |

Tech debt audits naturally yield more findings than design reviews — these caps are proportionally higher than `design-review-team`'s.

#### Fidelity Gate

Every backlog item's anchor and recommendation derive from the ledger's `verbatim_anchor` / `verbatim_recommendation`. Synthesis prose reorganizes and prioritizes *around* these tokens; it does not re-type them from memory. Code identifiers, file paths, CLI flags, and distinguishing qualifiers must match the verbatim fields character-for-character.

Before confirming the durable record, run the **Synthesis Fidelity Check** ([`references/severity-leverage-rubric.md`](references/severity-leverage-rubric.md)) alongside the severity and bucket sanity checks. If it fails for any item, correct that item from the ledger verbatim field before the durable write. A failed fidelity check blocks the durable record exactly as a failed durable write does.

#### Durable Record

Write the backlog to a durable location BEFORE Phase 3 cleanup runs. Default path: `docs/audits/YYYY-MM-DD-<target-slug>-debt.md` (create `docs/audits/` if absent). If the user prefers a different location, ask before falling back to the default. The durable record is the user-facing deliverable; the workspace copy at `.tech-debt-audit-workspace/synthesis/report.md` is scratch and may be deleted during cleanup.

If the durable write fails, do NOT proceed to cleanup — surface the error and preserve the workspace until the user resolves it.

After the durable record is confirmed on disk, execute Phase 3 cleanup (shutdown + TeamDelete + workspace handling per the workspace-preservation invariant).

## Finding Schema

Each auditor writes findings using this schema. Do NOT improvise fields.

```markdown
### [PREFIX-N] Title

- **severity:** P0 / P1 / P2 / P3
- **category:** code-health / architecture-drift / dependency / test-debt / operational / knowledge
- **subcategory:** specific lens name from debt-taxonomy.md
- **anchor:** path/to/file:lines or path glob or component name
- **problem:** 1-2 sentences describing the debt
- **impact:** 1-2 sentences describing concrete cost (velocity drag, bug surface, scaling cliff, oncall pain)
- **recommendation:** specific remediation action
- **effort:** small (<1 day) / medium (1-5 days) / large (>1 week or requires planning)
- **leverage:** high (unblocks other categories) / medium / low (self-contained)
- **confidence:** high / medium / low
- **provenance:** independent / followup
- **prompted_by:** {auditor-name} (required when followup; omit when independent)
```

### Coverage Notes

Mandatory when an auditor has zero findings for any owned subcategory at `primary` or `secondary` emphasis.

| Field | Purpose |
|-------|---------|
| `scope_checked` | Files/sections examined |
| `checks_run` | Sentinel questions + specific checks |
| `result` | "No defects found" + rationale |
| `caveats` | Limitations (emphasis level, evidence gaps) |
| `deferred_to` | If another auditor is better positioned |

## Severity Definitions

| Severity | Meaning |
|----------|---------|
| `P0` | Actively bleeding — already costing on-call hours, blocking deploys, causing customer-visible failures, or stopping team velocity |
| `P1` | Compounding — adds friction to most changes in this area; cost grows roughly linearly with code growth |
| `P2` | Latent risk — fine today but a known time bomb (e.g., dependency 2 majors behind, single-owner critical service) |
| `P3` | Cosmetic — readability or hygiene concern; remediate opportunistically |

Severity is not the same as priority. Final ordering is severity × leverage × effort, bucketed by remediation tractability — see [`references/severity-leverage-rubric.md`](references/severity-leverage-rubric.md).

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Agent teams not enabled | Prerequisite check | Hard stop |
| TeamCreate fails | Phase 3 spawn | Hard stop |
| Auditor spawn fails | Phase 3 spawn | Log, continue. All fail = hard stop |
| Missing findings file | Phase 3 completion check | Log in `auditors_failed`, proceed to synthesis |
| Auditor timeout (5 min) | No idle notification activity | Treat as failed, proceed with available findings |
| 4+ categories insufficient evidence | Phase 4 synthesis | Label `reduced-depth`, cap findings |
| TeamDelete fails | Phase 3 cleanup | Orphaned auditors still active — report degraded state; preserve workspace (workspace-preservation invariant) |
| Stale workspace | Phase 3 preflight | Offer: archive / remove / abort. Do not silently overwrite. |
| Existing `tech-debt-audit` team in session | Phase 3 preflight | Prompt: clean up prior team or abort (one-team-per-session constraint) |
| Durable report write fails | Phase 5 deliver | Preserve workspace, surface error to user, do NOT proceed to cleanup |
| Severity inflation (>50% P0) | Phase 4 scoring sanity check | Recalibrate against severity definitions; demote findings without concrete "bleeding today" evidence |
| Synthesis fidelity drift | Phase 5 fidelity gate | Report identifier/qualifier diverges from source finding — restore from the ledger verbatim field before the durable write |

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Dividing files among auditors | Gaps at cross-file boundaries | All auditors access all artifacts, scoped by lens |
| Lead deep-diving alongside auditors | Duplicates work, biases synthesis | Lead frames and synthesizes; auditors investigate |
| Calling tidiness "debt" | Inflates the backlog with cosmetic items | A finding without a named cost is not debt — mark as `P3` only with a concrete reason, or drop |
| Forcing tradeoffs for completeness | Generic tradeoffs explain nothing | Emit only when finding anchors actually conflict |
| Embedding entire briefs in spawn prompts | Context bloat for Sonnet auditors | Point to reference files; inline only finding schema |
| Skipping coverage notes on zero findings | Cannot distinguish "checked and clean" from "didn't check" | Coverage notes mandatory at `primary`/`secondary` emphasis |
| One-dimensional priority | Hides effort tradeoffs that change sprint planning | Score severity × leverage × effort separately, then bucket |

## References

| File | When to read |
|------|--------------|
| [`references/agent-teams.md`](references/agent-teams.md) | Phase 3: team lifecycle, cleanup resilience protocol |
| [`references/auditor-briefs.md`](references/auditor-briefs.md) | Phase 3: per-auditor role briefs and collaboration playbooks for spawn prompts |
| [`references/debt-taxonomy.md`](references/debt-taxonomy.md) | Shared lens framework: full lens definitions, archetypes, archetype × category weighting, cross-cutting tensions |
| [`references/staffing-rules.md`](references/staffing-rules.md) | Phase 1-2: emphasis map generation, suppression rules, deep-lens cap |
| [`references/severity-leverage-rubric.md`](references/severity-leverage-rubric.md) | Phase 4: scoring rubric, bucket assignment, ordering algorithm |

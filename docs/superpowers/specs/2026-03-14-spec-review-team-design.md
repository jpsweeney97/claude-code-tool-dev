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

## Constraints

1. **Agent teams experimental.** Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Hard prerequisite — do not fall back to sequential review.
2. **SKILL.md under ~500 lines.** Operational content offloaded to reference files. (`reviewing-designs` at 577 lines is the upper bound precedent.)
3. **Teammates don't inherit lead context.** All reviewer context must be embedded in spawn prompts (~2000 chars each).
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

**Design for upgrade:** 5 measurable A-to-B upgrade triggers are defined (Section 7). If synthesis complexity warrants extraction after v1 usage data, the upgrade path is clean.

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
| 1 | DISCOVERY | Locate spec, read frontmatter, build authority index | Authority index built with ≥1 normative file |
| 2 | ROUTING | Count clusters and edges, evaluate redirect gate | Pass redirect gate (or redirect to `reviewing-designs`) |
| 3 | PREFLIGHT | Build preflight packet, evaluate spawn rule, run mechanical checks, announce spawn-plan | Spawn-plan announced to user |
| 4 | REVIEW | Create workspace, spawn team, wait for all idle, verify findings files | All reviewer findings files present |
| 5 | SYNTHESIS | Read findings, build canonical ledger, dedup/corroborate/adjudicate, compute audit metrics, write report | Report written with all 9 audit metrics |
| 6 | PRESENT | Prioritized findings, corroboration table, audit metrics, cleanup prompt | User sees report |

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

### 6 Canonical Clusters

Files are classified into authority clusters during DISCOVERY. Cluster count drives routing and team composition decisions.

| Cluster | Description | Examples |
|---------|-------------|---------|
| `root` | Top-level architectural and foundational documents | foundations.md, decisions.md, internal-architecture.md, README.md |
| `contracts` | Behavioral contracts and interface definitions | tool-surface.md, behavioral-semantics.md, skill-orchestration.md |
| `schema` | Data model, DDL, persistence definitions | ddl.md, schema rationale |
| `control_surface` | Hooks, plugins, enforcement mechanisms, skill catalog | skills/overview.md, skills/catalog.md |
| `implementation` | Implementation plans, strategies, migration guides | testing-strategy.md, server-validation.md |
| `supporting` | Appendix, glossary, legacy maps, amendments | appendix.md, legacy-map.md, amendments.md |

**Cluster assignment uses frontmatter `authority` and `module` fields.** Files without frontmatter are assigned heuristically by path and content; ambiguous assignments are flagged.

### Routing: Redirect Gate

Before spawning a team, evaluate whether the spec is too small for a full team review:

| Condition | Threshold | Effect |
|-----------|-----------|--------|
| `candidate_files` | ≤ 3 | Required for redirect |
| `confident_authoritative_cluster_count` | ≤ 2 | Required for redirect |
| `boundary_edges` | ≤ 2 | Required for redirect |
| Specialist triggers | None firing | Required for redirect |
| Ambiguous cluster assignments | Any present | **Disables redirect** |

All conditions must be met for redirect to `reviewing-designs`. Ambiguity in any cluster assignment forces full team review — the ambiguity itself is a signal that authority boundaries need multi-lens examination.

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
2. **Dedup** — identity function: same `violated_invariant` + same `affected_surface` + same fix scope = merge. Merged findings list all contributing reviewer IDs.
3. **Corroborate** — findings from 2+ different lenses get confidence boost. Corroborated findings are tagged with contributing lenses.
4. **Adjudicate contradictions** — when reviewers disagree:
   - Normative source > non-normative source
   - If same authority level → escalate as ambiguity finding (itself a defect)
5. **Prioritize** — sort by: P0 → P1 → P2, then corroboration count, then confidence
6. **Compute audit metrics**

### 9 Audit Metrics

| # | Metric | Description |
|---|--------|-------------|
| 1 | `raw_finding_count` | Total findings before canonicalization |
| 2 | `canonical_finding_count` | Findings after dedup |
| 3 | `duplicate_clusters_merged` | Number of dedup merges |
| 4 | `corroborated_findings` | Findings confirmed by 2+ lenses |
| 5 | `contradictions_surfaced` | Inter-reviewer disagreements |
| 6 | `normalization_rewrites` | Findings that needed schema repair |
| 7 | `ambiguous_clusters` | Files with uncertain authority assignment |
| 8 | `synthesis_errors_p0` | P0 issues introduced during synthesis |
| 9 | `synthesis_errors_p1` | P1 issues introduced during synthesis |

### A-to-B Upgrade Triggers

Monitor these across runs. If any fire consistently across 8+ runs, consider extracting synthesis to a dedicated agent (upgrading from Architecture A' to Architecture B).

| # | Trigger | Threshold | Signal |
|---|---------|-----------|--------|
| 1 | Normalization rate | ≥ 15% of findings | Reviewers not following schema reliably |
| 2 | Cross-run determinism | ≥ 2/5 runs produce different synthesis | Synthesis procedure too context-dependent |
| 3 | Cross-run inconsistency | Same spec, materially different reports | Lead context polluting synthesis |
| 4 | Synthesis duration | > 3 minutes | Procedure too complex for inline execution |
| 5 | P0 missed | Any P0 found by re-review that synthesis dropped | Synthesis errors are the highest-risk failure |

## Preflight Packet

The preflight packet is embedded in every spawn prompt. Budget: ~1000 chars condensed. Contains 6 sections:

| Section | Content | Purpose |
|---------|---------|---------|
| `authority_index` | File → normative/non-normative + authority level | Reviewers know which files are authoritative |
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

### Spawn Prompt Structure

Each teammate receives ~2000 chars:

| Component | Budget | Content |
|-----------|--------|---------|
| Shared scaffold | ~600 chars | Finding schema, workspace path, output file path, output rules (no prose between findings, coverage notes for zero-finding classes) |
| Preflight packet | ~1000 chars | Condensed authority index, boundary edges, spawn plan |
| Role delta | ~400 chars | Defect class description, primary/secondary file focus, rubric items from `role-rubrics.md` |

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| No frontmatter on any file | DISCOVERY phase finds 0 normative files | Degraded discovery: classify by path heuristics, warn user, proceed with reduced confidence |
| > 50% ambiguous cluster assignments | ROUTING phase computation | All-core team (no specialists), flag ambiguity as meta-finding |
| Teammate produces prose instead of structured findings | SYNTHESIS phase normalization | Lead normalizes to schema, increments `normalization_rewrites` metric |
| Agent teams not enabled | Prerequisite check | Hard stop: "Requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1. Do not fall back." |
| Teammate fails to write findings file | REVIEW phase verification | Wait for idle notification, then check. If file missing after idle, log as synthesis error. |
| Preflight packet exceeds ~1000 chars | PREFLIGHT phase | Condense: abbreviate file paths, drop mechanical check details, keep authority index and boundary edges |

## Decisions Log

| # | Decision | Choice | Key Rationale | Confidence |
|---|----------|--------|---------------|------------|
| 1 | Scope | General multi-file spec review (not Engram-specific) | Authority/normative frontmatter pattern is reusable; spec-modulator produces exactly this structure | High (E2) |
| 2 | Architecture | A' (normative SKILL.md + operational refs) | Emerged from comparative Codex dialogue; synthesis needs explicit intermediate structure, not fresh context | High (E2) |
| 3 | Team composition | 4 core + 2 optional, domain-agnostic core names | Converged across 3 independent Codex consultations; fully adaptive has silent staffing failures | High (E2) |
| 4 | Routing proxy | Authority-boundary clusters, not file count | "A 3-file spec spanning 3 authority tiers is more complex than a 10-file spec in one tier" | High (E2) |
| 5 | Finding format | Atomic schema with `violated_invariant` field | Finding-level canonicalization requires explicit intermediate state; `violated_invariant` enables cross-reviewer merge | High (E2) |
| 6 | Lifecycle positioning | Create (spec-modulator) → Review (spec-review-team) | User-identified synergy confirmed by shared frontmatter conventions | Medium (E1) |

## Open Questions

1. **Dedup identity function untested against real findings.** Same invariant + same surface + same fix scope = merge. The exact boundary conditions (how similar is "same"?) will need calibration after first runs.

2. **A-to-B upgrade trigger thresholds uncalibrated.** The 5 triggers are reasonable starting points but need 8+ runs to validate. First runs should record all metrics for calibration.

3. **Potential third optional specialist.** API specs with complex schema evolution may warrant it. Deferred for v1.

4. **Interaction model with reviewing-designs.** When both could apply to the same spec (e.g., a 4-file spec), the redirect gate handles most cases. The boundary isn't sharp for specs at the gate threshold — may need a user-choice prompt.

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

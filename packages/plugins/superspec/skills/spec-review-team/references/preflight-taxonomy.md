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

### Authority-to-Cluster Mapping

Derivation of review cluster from source authority. Lossy — multiple authorities map to the same cluster.

| Source authority | Review cluster | Notes |
|-----------------|----------------|-------|
| `foundation` | `root` | Core architectural docs |
| `decisions` | `root` | ADRs and decision records |
| `behavioral` | `contracts` | Behavioral contract documents |
| `interface` | `contracts` | API and surface definitions |
| `schema` | `schema` | Data model and DDL |
| `control` | `control_surface` | Hook and enforcement docs |
| `enforcement` | `control_surface` | Policy enforcement docs |
| `implementation` | `implementation` | Plans, strategies |
| `supporting` | `supporting` | Appendix, glossary |
| `legacy` | `supporting` | Legacy maps, amendment trails |
| `unknown` | Derived from path | Fallback — see missing metadata rules |

## Derived Roles (Full Contract Mode)

When `spec.yaml` is present, cluster-based routing is replaced by derived role routing. The derivation table is defined in the shared contract (`${CLAUDE_PLUGIN_ROOT}/references/shared-contract.md#claim-to-role-derivation-table`) — this section documents how the review team applies it.

**Redirect gate:** Count distinct derived roles (excluding `reference`) present across normative files. This replaces `confident_review_cluster_count` in full contract mode.

**Specialist spawning:** Deterministic when `spec.yaml` exists — spawn when any normative file has the specialist's trigger claim in its effective claims:
- `persistence_schema` claim → spawn `schema-persistence` specialist
- `enforcement_mechanism` claim → spawn `integration-enforcement` specialist

No sampling needed in full contract mode. The two-tiered heuristic scoring below is retained for degraded mode only.

**Claim divergence flagging:** Files whose effective claims produce a different derived role set than their authority's `default_claims` would produce are flagged as high-attention review surfaces in the preflight packet.

## Two-Layer Cluster Model (Degraded Mode)

In degraded mode (no `spec.yaml`), every spec file carries two cluster-related concepts that are related but distinct. In full contract mode, this model is replaced by derived roles from claims — see above.

**Source authority** — the original `authority` frontmatter value. Preserved as-is from the spec. Used for adjudication when reviewers conflict. This is canonical.

**Review cluster** — derived from source authority + `module` + path heuristics. A lossy mapping from authority to one of the 6 canonical clusters. Used for routing, staffing, and rubric selection only. Not a substitute for the source authority.

### Missing Metadata Handling

| Condition | Source authority | Cluster derivation |
|-----------|-----------------|-------------------|
| No frontmatter at all | `unknown` | Path heuristics only; flagged ambiguous |
| Frontmatter present, no `authority` field | `unknown` | Derived from `module` + path |
| Parseable frontmatter present | From `authority` field | Standard derivation |

Zero parseable frontmatter across all files = degraded mode. Log and continue — core reviewers handle all defect classes regardless of cluster resolution. Partial metadata coverage = normal operating condition.

### Path Heuristics for Unknown Authority

When source authority is `unknown`, apply these path pattern rules in order (first match wins):

1. Path contains `schema`, `ddl`, `data-model` → cluster `schema`
2. Path contains `contract`, `behavioral`, `interface` → cluster `contracts`
3. Path contains `hook`, `plugin`, `skill`, `enforcement` → cluster `control_surface`
4. Path contains `plan`, `strategy`, `migration`, `testing` → cluster `implementation`
5. Path contains `appendix`, `glossary`, `legacy`, `amendment` → cluster `supporting`
6. No match → cluster `root` with ambiguous flag

## Signal Dimensions (Degraded Mode)

In full contract mode, specialist spawning is deterministic from claims — this section applies only to degraded mode. Five signal dimensions inform optional specialist spawning decisions in the absence of `spec.yaml`.

| Dimension | Type | Example signal | Cost |
|-----------|------|---------------|------|
| Frontmatter authority | Metadata-derived | `authority: schema` on any file | Free (Phase 1) |
| File naming | Metadata-derived | File named `ddl.md`, `schema-*.md` | Free (Phase 1) |
| Cluster membership | Metadata-derived | File classified in `schema` cluster | Free (Phase 2) |
| Content keywords | Content inspection | Schema-related terms in file body | Budgeted sampling |
| Cross-reference patterns | Content inspection | Contracts referencing schema files | Budgeted sampling |

Metadata-derived dimensions are free because they operate on frontmatter and paths collected during Phase 1 (manifest) and Phase 2 (routing). Content inspection dimensions require targeted file reads and consume sampling budget.

## Scoring Weights and Spawn Thresholds (Degraded Mode)

### Two-Tiered Spawn Rule

**Tier 1 (score ≥ 100):** Single high-confidence signal suffices. Spawn immediately without sampling.
- Example: any file carries `authority: schema` → spawn schema specialist.

**Tier 2 (score 50-99):** Requires 2+ medium signals from different dimensions. No single medium signal triggers a spawn.
- Example: `ddl.md` filename (75) + schema cross-references in content (60) → combined confidence → spawn.
- Signals from the same dimension do not stack. Two filename matches count as one medium signal.

### Signal Weights (Calibrate After First Runs)

| Tier | Score range | Signal examples |
|------|-------------|----------------|
| High-confidence | ≥ 100 | Frontmatter `authority` exact match |
| Medium | 50–99 | Filename pattern match, cluster membership |
| Weak | 25–49 | Content keywords, single cross-reference |

These weights are implementation guidance, not hard constraints. Recalibrate based on false-positive and false-negative rates observed in early runs. When scores are borderline, prefer not spawning — core reviewers cover all defect classes.

### Scoring Examples

| Scenario | Signals present | Score | Decision |
|----------|----------------|-------|----------|
| `authority: schema` in frontmatter | High-confidence (100) | 100 | Spawn immediately |
| File named `ddl.md`, no other signals | Medium filename (75) | 75 | Do not spawn — single medium signal |
| File named `ddl.md` + schema cross-refs found | Medium filename (75) + medium cross-ref (60) | 135 | Spawn (Tier 2 met from two dimensions) |
| Schema keywords in body only | Weak content (35) | 35 | Do not spawn |
| Two schema keyword hits, no other signals | Weak content (35 × 2 = same dimension) | 35 | Do not spawn — same-dimension stacking disallowed |

## Sampling Policy (Degraded Mode)

### Mechanics

- **Unit of inspection:** targeted file excerpt, not full file read
- **Budget:** maximum 5–8 file excerpts per preflight (calibrate after first runs)
- **Scaling:** budget does NOT scale with spec size. Fixed cap regardless of corpus volume.

### When Sampling Triggers

Sampling activates only when metadata signals are insufficient to decide whether to spawn an optional specialist. If Tier 1 or Tier 2 threshold is already met from metadata alone, do not sample.

Conditions that trigger sampling:
- A candidate specialist domain has at least one weak signal but no high-confidence or medium signals
- Cross-reference patterns are suspected but unconfirmed from metadata alone

### What Sampling Checks

- Content keywords associated with the candidate specialist domain
- Cross-reference patterns (e.g., contracts that cite schema files, or implementation docs that reference hook behavior)

Each sampled excerpt is one file read, consumed from the budget. Read the minimum excerpt needed to confirm or reject the signal — do not read the full file.

### Budget Exhaustion Rule

If the sampling budget is fully spent and cumulative confidence remains below the Tier 2 threshold, do NOT spawn the specialist. Log the unresolved signal and the final score. Core reviewers cover all defect classes — an unspawned specialist is not a coverage gap.

**Active prohibition:** Sampling is budgeted detection, NOT review. The lead MUST NOT expand sampling into broad corpus reading. If you find yourself reading more than targeted excerpts, stop — you are exceeding the sampling budget.

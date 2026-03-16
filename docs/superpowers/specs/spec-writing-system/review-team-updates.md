---
module: review-team-updates
status: active
normative: true
authority: review-team
---

# Spec-Review-Team Updates

This section describes delta changes to the existing `spec-review-team` skill to consume the shared contract.

## What Stays the Same

- **6-phase structure:** DISCOVERY → ROUTING → PREFLIGHT → REVIEW → SYNTHESIS → PRESENT
- **4 core reviewers:** authority-architecture, contracts-enforcement, completeness-coherence, verification-regression (defect-class-based, domain-agnostic)
- **2 optional specialists:** schema-persistence, integration-enforcement
- **Lateral messaging:** message (targeted) and broadcast (all teammates) primitives
- **Completion contract:** idle notifications, wall-clock timeout, partial completion handling
- **Cleanup contract:** shutdown requests, TeamDelete, workspace preservation prompt
- **Audit metrics:** all 10 metrics retained

## What Changes

### DISCOVERY (Phase 1)

| Before | After |
|--------|-------|
| Parse frontmatter, extract `authority` field, map to 6 fixed clusters | Parse frontmatter AND `spec.yaml`. If `spec.yaml` exists: read authority registry, derive structural roles from claims using the shared derivation table ([Claim-to-Role Derivation Table](shared-contract.md#claim-to-role-derivation-table)). If absent: degraded mode (current behavior). |
| Authority map records: normative flag, source authority, review cluster | Authority map records: file path, normative flag, authority label, effective claims, derived roles, boundary-rule participation (source/target/neither) |
| Path heuristics always applied | Path heuristics only in degraded mode (no `spec.yaml`) |

The expanded authority map feeds later phases: ROUTING uses derived roles for the redirect gate, PREFLIGHT uses effective claims for specialist spawning, SYNTHESIS uses boundary-rule participation for coverage analysis.

### ROUTING (Phase 2)

| Before | After |
|--------|-------|
| Redirect gate counts `confident_review_cluster_count` from 6 fixed clusters | Redirect gate counts distinct derived roles (excluding `reference`) from normative files |
| `boundary_edges` inferred from cluster transitions | `boundary_edges` computed from `spec.yaml` `boundary_rules` |
| Specialist triggers via multi-signal heuristic scoring (Tier 1 / Tier 2) | Specialist triggers deterministic when `spec.yaml` exists: spawn when any normative file has the trigger claim in effective claims. Heuristic scoring retained for degraded mode only. |

**`boundary_edges` count rule:** Count unique directional `(on_change_to authority, review_authority)` pairs across all boundary rules. One rule with 3 `review_authorities` = 3 edges. Example: 2 boundary rules in the CLI spec produce 5 edges (3 + 2).

### PREFLIGHT (Phase 3)

| Before | After |
|--------|-------|
| Phase 3A validates `authority` as required on every file | Phase 3A validates `authority` required only when `spec.yaml` exists |
| Mechanical checks: frontmatter + cross-references | Add semantic manifest validation: unknown claims in defaults/frontmatter, undefined authority references in precedence/boundary rules, normative files with zero effective claims, effective claims >3. Consumer failure rules apply ([Failure Model](shared-contract.md#failure-model)). |
| Spawn plan based on heuristic signal scoring | Spawn plan based on deterministic claim presence (when `spec.yaml` exists) or heuristic scoring (degraded mode) |

The preflight packet's 6 sections update to match:

| Section | Change |
|---------|--------|
| `authority_map` | Expanded: file path, normative flag, authority label, effective claims, derived roles, boundary-rule participation |
| `boundary_edges` | Computed from `spec.yaml` boundary_rules (or cluster transitions in degraded mode) |
| `signal_matrix` | Simplified when `spec.yaml` exists (binary claim presence). Retained for degraded mode. |
| `mechanical_checks` | Expanded with semantic manifest validation results |
| `route_decision` | Uses derived role count instead of cluster count |
| `spawn_plan` | Deterministic from claims (spec.yaml) or heuristic (degraded) |

### Finding Schema

Add one required field:

```markdown
### [PREFIX-N] Title

- **priority:** P0 / P1 / P2
- **title:** One-sentence description
- **claim_family:** <claim from fixed enum, or "ambiguous">  ← NEW
- **violated_invariant:** source_doc#anchor
- **affected_surface:** file + section/lines
- **impact:** 1-2 sentences
- **evidence:** what doc says vs what it should say
- **recommended_fix:** specific action
- **confidence:** high / medium / low
- **provenance:** independent / followup
- **prompted_by:** {reviewer-name} (required when followup)
```

`claim_family` enables mechanical application of `claim_precedence` during synthesis. If a reviewer cannot identify one claim family, set `claim_family: ambiguous` — the finding escalates to human resolution.

### SYNTHESIS (Phase 5)

| Before | After |
|--------|-------|
| Contradiction resolution: normative > non-normative, then domain reasoning | Resolution uses `spec.yaml` precedence rules: normative_first → claim_precedence (per-finding `claim_family`) → fallback_authority_order → ambiguity finding. See [Precedence Resolution](shared-contract.md#precedence-resolution). |
| No structured precedence model | Mechanical application of declared precedence. `claim_precedence` lists are partial; unlisted authorities fall through to `fallback_authority_order`; unlisted there → ambiguity finding. |
| Boundary analysis ad hoc | When a finding's `affected_surface` touches a file under authority X in `on_change_to`, verify at least one reviewer examined files under each `review_authorities` authority for defects related to the boundary rule's stated `reason` ([Boundary Rules](shared-contract.md#boundary-rules)). Unexamined → coverage finding. |

## Reference File Updates

| File | Change | Normative source |
|------|--------|-----------------|
| `preflight-taxonomy.md` | **References** the shared contract's derivation table — does not restate it as independent content. Documents how the review team applies it: redirect gate counting, specialist spawning rules. Retains degraded-mode heuristics (path patterns, signal scoring) as fallback. | Shared contract [Claim-to-Role Derivation Table](shared-contract.md#claim-to-role-derivation-table) is authoritative for claim-to-role mapping |
| `role-rubrics.md` | Update shared scaffold to include `claim_family` in finding format. Domain briefs unchanged — they are defect-class-based, not cluster-based. | — |
| `synthesis-guidance.md` | Add worked examples of `claim_precedence` application and boundary coverage analysis. Update contradiction resolution section to reference `spec.yaml` precedence rules. | Shared contract [Precedence Resolution](shared-contract.md#precedence-resolution) is authoritative for precedence rules |
| `failure-patterns.md` | Add failure patterns for: malformed `spec.yaml`, unknown claims, semantic manifest validation failures. Update degraded mode description. | Shared contract [Failure Model](shared-contract.md#failure-model) is authoritative for failure responses |
| `agent-teams-platform.md` | No changes — platform API unchanged. | — |

**Drift prevention:** Reference files that consume shared contract content must reference it by section, not restate it. If the shared contract's derivation table or precedence rules change, reference files need only update their pointers, not their content.

## Backward Compatibility

Existing specs remain reviewable via degraded mode. Full contract benefits (deterministic specialist spawning, mechanical precedence resolution, boundary coverage analysis) require `spec.yaml`.

| Condition | Behavior |
|-----------|----------|
| `spec.yaml` present + frontmatter on files | Full contract mode — all new features active |
| `spec.yaml` absent + frontmatter on files | Degraded mode — current behavior preserved |
| `spec.yaml` present + no frontmatter on files | Degraded mode — `spec.yaml` provides authority definitions but files can't be mapped |
| Neither present | Degraded mode — path heuristics only |

# Decision Record: Multi-Dialogue Synthesis Scope Preservation

**Date:** 2026-02-11
**Status:** Decided
**Stakes:** Adequate
**Decision:** How to prevent scope loss when consolidating findings from multiple Codex dialogues into a single design document

## Context

During consolidation of two Codex dialogues into the Conversation-Aware Context Injection design document (`docs/plans/2026-02-11-conversation-aware-context-injection.md`), scope context was lost when findings were reorganized by topic.

**The failure:** Dialogue 1 (adversarial, 8 turns) was scoped to "build MVP, defer the rest." Dialogue 2 (exploratory, 7 turns) explored the full design space without MVP restriction. When merged by topic, full-design content from Dialogue 2 ended up in sections where Dialogue 1's MVP scope said those features were deferred.

A post-consolidation Codex review pass found 5 internal issues. Two were directly caused by scope loss during merge; the others were related consolidation issues (definitional inconsistency, completeness gaps) that the same process can catch but aren't scope-specific:

| # | Contradiction | Type |
|---|---|---|
| 1 | Opportunistic closure specified in the scouting loop but deferred in MVP scope | Scope loss — D2 full-design content placed in D1's MVP scope |
| 2 | Evidence lifecycle fully specified but marked as deferred | Scope loss — same mechanism |
| 3 | Tier 1 listed 10 entity types but only 4 had scout templates | Scope-adjacent — breadth from D2 without D1's MVP constraint |
| 4 | "Reframe" appeared as both a planning outcome and a template | Definitional inconsistency — could arise from a single dialogue |
| 5 | Clarifier bypass of the hard gate was unspecified | Gap — nothing to conflict with |

The review was not specifically looking for scope conflicts — the catch was accidental.

**Root cause:** Topic-organized documents are better for readers, but source-organized extraction is better for preserving scope. The merge step bridges these, and that's where scope metadata is lost. Prose doesn't carry metadata.

## Constraints

1. **Volume:** Synthesis happens 2-3 times per week, involving 2-4 dialogues producing 10-40 findings each.
2. **Overhead budget:** The fix must be lightweight enough that it doesn't dominate the synthesis step.
3. **Mechanical over heuristic:** Prefer structural constraints that make contradictions detectable, not review passes that rely on reviewer quality.

## Options Evaluated

### Option A — Scope tags at extraction time

Tag each finding during extraction with its scope (`mvp`, `post_mvp`, `full_design`). Conflicts detectable during merge when tags disagree with section scope.

- Preventive, but scope is often implicit (requires inference during extraction)
- Wrong tags create false confidence

### Option B — Post-merge reconciliation sweep

After consolidation, run a dedicated pass checking "does this section's content match its scope?"

- Already proven to work (the Codex review caught all 5 issues)
- Reactive, not preventive — contradictions exist before they're caught
- Scales poorly with document size

### Option C — Section-level scope declarations (skeleton with scope zones)

Design the document skeleton with explicit scope zones before merging. Content must route to matching zones.

- Turns "where does this finding go?" from a judgment call into a routing decision
- Fails if the skeleton itself is mis-scoped (B only checks consistency against skeleton, not correctness of skeleton)

### Option D — Structured intermediate representation with scope linter

Extract findings into structured records (IR) with `scope`, `key`, and `source` as fields. Consolidation becomes "render views" instead of moving prose. A scope linter flags conflicts mechanically.

- Directly attacks the root cause (metadata loss during reorganization)
- Full IR is overkill at current volume (10-40 findings)

### Option D-lite — Scope-tagged atomic bullets (IR-in-Markdown)

Hybrid of D's mechanical safety with minimal overhead. One-line records with inline scope tags and stable keys:

```
- [F-12] key=evidence_lifecycle scope=post_mvp src=D2:T3-5 — Define evidence states and retention
```

- Scope travels with the finding as a field, not contextual inference
- Stable `key` detects "same feature, different scope" conflicts mechanically
- Low extraction overhead — copy-edit minimal

## Decision

**Adopt: A (dialogue-level, mandatory) + D-lite + C + B**

The full synthesis process becomes:

| Step | Action | Mechanism |
|------|--------|-----------|
| 1 | Tag each dialogue with its scope | A — mandatory, at dialogue level ("D1 = mvp, D2 = full_design") |
| 2 | Extract findings as scope-tagged bullets with stable keys | D-lite — one line per finding, scope is a field |
| 3 | Design document skeleton with scope zones | C — sections declare their scope before content is placed |
| 4 | Route bullets into skeleton | Mechanical — match bullet `scope` to zone scope; flag mismatches |
| 5 | Reconciliation sweep | B — safety net for anything routing missed |
| 6 | Write prose from routed bullets | Human/Claude pass; bullets remain as traceable substrate |

### Why not just C + B?

C + B was the initial recommendation but has a systematic weakness: if the skeleton is mis-scoped, B checks consistency against a wrong skeleton and produces clean but incorrect output. D-lite makes conflicts mechanically detectable at routing time (stable keys + explicit scope fields), rather than relying on reviewer quality during the B sweep.

### Why not full D?

At 10-40 findings per synthesis, the extraction-to-IR step dominates if the IR is formal (typed records, schema validation). D-lite gets the mechanical safety without the framework overhead.

### Scope-tagged bullet format

Minimum viable fields per bullet:

| Field | Purpose | Required? |
|-------|---------|-----------|
| `id` | Stable local ID (`F-01`) | Yes |
| `key` | Canonical feature name (`evidence_lifecycle`) — same idea from multiple dialogues merges on this | Yes |
| `scope` | `mvp`, `post_mvp`, `exploratory` | Yes |
| `scope_if` | Condition for conditional scope (`if: core_loop_stable`) | Only when scope is conditional |
| `src` | Source dialogue and turn range (`D1:T3-5`) | Yes |
| `claim` | One-sentence atomic statement | Yes |

Example:
```
- [F-01] key=planning_presentation_split scope=mvp src=D1:T1-3 — Separate planning (which follow-up) from presentation (how to word it)
- [F-02] key=evidence_lifecycle scope=post_mvp src=D2:T4 — Three-state lifecycle: presented → applied → closed
- [F-03] key=evidence_lifecycle scope=mvp src=D1:T5 — Presented-only tracking for MVP
- [F-04] key=opportunistic_closure scope=mvp scope_if=core_loop_stable src=D1:T5 — Close extra items when scout answers them
```

F-02 and F-03 share `key=evidence_lifecycle` with different scopes — the conflict is mechanically detectable at routing time.

## Trade-offs Accepted

- **Extraction overhead:** Adding the bullet extraction step (Step 2) is new work that didn't exist before. At 10-40 findings, this is ~5-10 minutes. Acceptable if it prevents the 15+ minute contradiction-fixing pass that the current process required.
- **Inline tag density:** The one-line format is dense. If readability becomes an issue, switch to a small markdown table per dialogue. Start with inline and see.
- **Conditions are inline strings, not first-class records.** `scope_if=core_loop_stable` is sufficient at current volume. If conditional scopes become complex, upgrade to a formal Condition table.
- **No automation.** The scope linter is a human/Claude review step, not a script. At 2-3 syntheses per week, automation doesn't pay for itself yet.

## Process Location

This process applies when Claude consolidates findings from multiple Codex dialogues into a single design document. The 6-step process is operationalized as a reference in this decision record — not embedded in the codex-dialogue agent (which handles individual dialogues, not cross-dialogue synthesis).

When performing synthesis, Claude should consult this record for the process. If synthesis becomes frequent enough to warrant a dedicated skill or checklist, extract the process at that point.

## Confidence

- **Confidence:** Medium
- **Evidence level:** E1 (single failure instance + Codex adversarial review)
- **What would change this:**
  - If the bullet extraction step consistently takes >15 minutes, simplify (drop `key` field, use dialogue-level scope only)
  - If contradictions still slip through after adoption, upgrade to full IR (Option D) with automated scope linting
  - If synthesis volume increases significantly, invest in automation

## Next Actions

1. **Apply on next synthesis.** Use the 6-step process during the next multi-dialogue consolidation. The context injection design document is already consolidated — do not retroactively reprocess it.
2. **Evaluate overhead.** After 2-3 applications, check whether the bullet extraction step (Step 2) takes <15 minutes. If it consistently exceeds that, simplify per the Confidence section.
3. **Decide on process extraction.** If the process proves stable after ~5 applications, consider extracting it into a standalone reference or synthesis checklist.

## Provenance

- **Failure instance:** Context injection design document consolidation (2026-02-11, session `d248d88d`)
- **Analysis:** Claude review of three candidates (A, B, C) with trade-off analysis
- **Codex consultation:** Two-turn dialogue (gpt-5.2, xhigh reasoning). Codex proposed Option D (structured IR + scope linter), the D-lite hybrid, the `key` field for cross-dialogue deduplication, and the `scope_if` modifier pattern. Also identified 5 failure modes of C + B that motivated adding D-lite.
- **Thread:** `019c4daf-1e51-7501-80cb-b2be255584ba`

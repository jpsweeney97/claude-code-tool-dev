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

- **Confidence:** High
- **Evidence level:** E2 (original failure instance + controlled dual-path evaluation)
- **Upgraded from:** Medium / E1 (2026-02-11, after first controlled test — see Evaluation section)
- **What would change this:**
  - If the bullet extraction step consistently takes >15 minutes across multiple syntheses, simplify (drop `key` field, use dialogue-level scope only)
  - If contradictions slip through after adoption despite `key` matching, upgrade to full IR (Option D) with automated scope linting
  - If synthesis volume increases significantly, invest in automation
  - If key naming inconsistency becomes a recurring issue (see Process Improvement below), add a stem-matching deduplication sub-step

## Next Actions

1. ~~**Apply on next synthesis.**~~ Done — see Evaluation section. First controlled test passed all criteria.
2. **Evaluate overhead (2 of 2-3 data points).** First: ~8 min / 24 bullets. Second: ~10 min / 27 bullets. Proportional (~0.37 min/bullet). Need 1 more data point to confirm.
3. **Decide on process extraction.** If the process proves stable after ~5 applications, consider extracting it into a standalone reference or synthesis checklist. (2 of 5 applications complete.)
4. **Consider key deduplication sub-step.** First test: one miss due to inconsistent naming. Second application: no naming inconsistency issues — pattern did not recur. Keep deferred; add only if seen again.

## Evaluation (2026-02-11)

First controlled test of the 6-step process. Full details in `docs/plans/2026-02-11-synthesis-process-test-case.md`.

### Test Design

Two Codex dialogues on a shared topic ("should codex-reviewer get structural upgrades?") with controlled scope constraints:

| Dialogue | Scope | Posture | Turns | Thread ID |
|----------|-------|---------|-------|-----------|
| D1 | `mvp` — minimum viable upgrade | Evaluative | 6/6 | `019c4dcb-c0f8-7092-bcc3-4f0b81ecb621` |
| D2 | `full_design` — full redesign | Exploratory | 8/8 | `019c4dd4-8243-7ad1-9c02-99a105c10eb7` |

Dual-path comparison: naive topic-organized outline (control) vs. 6-step process, evaluated against predicted conflict zones and a scoring rubric.

### Results

| Criterion | Result |
|-----------|--------|
| Finding density | D1: 10, D2: 14 (24 total) — sufficient |
| Predicted conflicts materialized | 5 of 6 zones — sufficient |
| Conflicts caught by process but missed by naive | 7 (4 hard + 2 partial + 1 sweep-only) — **exceeds threshold** |
| Conflicts caught by naive | 0 — naive blended all scopes without distinction |
| False alarms | 0 of 8 flags — **0% false alarm rate** |
| Step 2 overhead | ~8 min for 24 bullets — **under 15-min threshold** |
| `key` field utility | 6 shared keys detected mechanically; 1 missed due to inconsistent naming |

### Verdict

**Process passed all success criteria.** Confidence upgraded from Medium/E1 to High/E2.

### Process Improvement Identified

Key naming during Step 2 is a judgment call. One conflict (`confidence_classification` vs. `confidence_model`) was missed by key matching because different key names were used for what was conceptually the same feature. Caught by the reconciliation sweep (Step 5), confirming the sweep's value as a safety net. A stem-matching deduplication scan after Step 2 would catch this class of error mechanically.

### Naive Failure Mode Confirmed

The naive outline reproduced the exact failure mode from the original context injection consolidation: D2's richer, more detailed content dominated the merge in every conflict zone. D1's scope constraints (keep 2 turns, defer ledger, defer follow-up strategy) were absorbed into D2's broader descriptions without distinction. The resulting document would have read as if the full_design scope was the only recommendation.

## Application 2: Context Injection Open Questions (2026-02-11)

First real-world application (not a designed test). Two Codex dialogues resolving high-priority open questions from the context injection plan.

### Setup

| Dialogue | Scope | Posture | Turns | Thread |
|----------|-------|---------|-------|--------|
| D1 (Safety & boundaries) | `mvp` | Evaluative | 6/6 | `019c4e2f-8bc4-7c70-af6a-5af2ada22f07` |
| D2 (Sizing & strategy) | `calibration` | Exploratory | 7/8 | `019c4e2f-d5c2-71a3-8d77-567ae559a7c4` |

### Results

| Metric | Value | vs. Application 1 |
|--------|-------|-------------------|
| Finding density | D1: 15, D2: 12 (27 total) | 24 total |
| Step 2 extraction time | ~10 min | ~8 min (proportional: 0.37 min/bullet vs. 0.33 min/bullet) |
| Shared keys at routing (Step 4) | 1 (`risk_signals`) | 6 shared keys |
| Hard conflicts | 0 | 4 hard + 2 partial |
| Integration points (Step 5) | 3 | 1 sweep-only catch |
| False alarms | 0 | 0 |
| Key naming inconsistency | Not observed | 1 instance |

### Observations

**Low conflict surface from well-separated question groupings.** The deliberate split (safety questions vs. sizing questions) meant the dialogues produced complementary findings, not competing ones. Only 1 shared key (`risk_signals`) appeared, and it was a compatible extension rather than a conflict. This contrasts with Application 1 where overlapping features with different scope constraints produced 6 shared keys and 7 conflicts.

**Process value was primarily routing, not conflict detection.** The 6-step process still provided structure: the skeleton with scope zones ensured safety findings and sizing findings were cleanly separated in the plan update. The reconciliation sweep caught 3 integration points (git ls-files gating interacting with file_name resolution, scope anchoring interacting with focus-affinity pacing, risk signals needing a shorter excerpt cap). These are cross-cutting concerns that would be easy to miss in a straight merge.

**Overhead remains proportional.** ~10 min for 27 bullets is consistent with ~8 min for 24 bullets. No friction points in the process itself — steps 1-5 were straightforward.

**Key deduplication issue did not recur.** No naming inconsistencies in Step 2.

### Process Fitness Observation

The 6-step process is designed for the high-conflict case (multiple dialogues discussing the same features at different scopes). When question groupings are orthogonal, the process degrades gracefully to a structured routing exercise. It doesn't add unnecessary overhead — extraction takes proportional time, and the reconciliation sweep is quick when there are few shared keys. But its primary value proposition (catching scope conflicts mechanically) doesn't activate.

**Implication for process extraction:** If the process is extracted into a checklist, consider a fast-path for low-overlap syntheses: Steps 1-2-3-6 only (tag, extract, skeleton, write prose), with Steps 4-5 (routing + reconciliation) triggered only when Step 2 produces ≥3 shared keys.

## Provenance

- **Failure instance:** Context injection design document consolidation (2026-02-11, session `d248d88d`)
- **Analysis:** Claude review of three candidates (A, B, C) with trade-off analysis
- **Codex consultation:** Two-turn dialogue (gpt-5.2, xhigh reasoning). Codex proposed Option D (structured IR + scope linter), the D-lite hybrid, the `key` field for cross-dialogue deduplication, and the `scope_if` modifier pattern. Also identified 5 failure modes of C + B that motivated adding D-lite.
- **Thread:** `019c4daf-1e51-7501-80cb-b2be255584ba`

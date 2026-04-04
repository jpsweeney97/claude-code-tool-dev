# Reclassify T4 In Place

## Summary

Do **not** move the T4 spec. Keep all existing paths intact and solve the actual problem by making T4’s normative status explicit at the reader entrypoints that matter.

This plan reclassifies T4 **in place** as a normative peer spec that happens to live under `docs/plans/` for historical continuity. It adds load-bearing cross-references from codex-collaboration into T4, strengthens T4’s own self-description, and leaves all historical references untouched. There is no path migration, no duplicate spec root, no frozen archive, and no tooling/schema work.

**Reader-facing result:** someone entering through codex-collaboration or the benchmark contract learns that T4 is the normative scouting/evidence contract; someone opening T4 directly learns that it is a live normative spec, not planning scratch, despite its directory.

## Key Changes

### 1. Reclassify T4 at its own entrypoints

Update the T4 modular README and the monolith shim so both say the same thing clearly:

- T4 is a **normative peer specification**, not planning scratch.
- It remains under `docs/plans/` for historical continuity and stable references.
- Its current directory is the canonical location for the T4 spec.
- Future edits should continue to land there unless a later tooling-backed relocation is approved.

Apply this to:
- [README.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md)
- [2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md)

Implementation intent:
- In the T4 README, add a short note near the top, directly after the opening description/context, stating that this is the canonical normative T4 spec and that the `docs/plans/` location is historical, not a signal that the content is non-normative.
- In the monolith shim, strengthen the existing “canonical spec” wording so it explicitly says the linked modular directory is the canonical normative T4 spec and remains in place to preserve historical references.

### 2. Add codex-collaboration discoverability hooks

Add explicit cross-references from codex-collaboration’s two real reader entrypoints into T4.

Apply this to:
- [README.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/README.md)
- [dialogue-supersession-benchmark.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)

Implementation intent:
- In the codex-collaboration README, add a short `Related Specs` section after the reading-order table or cross-reference conventions. It should point to T4 as the normative scouting/evidence contract that the benchmark and related dialogue work depend on.
- In the benchmark contract, add a mandatory cross-reference in the `Change Control` section, immediately after the existing three-item amendment rule list. The added rule should say that changes affecting scouting scope, evidence provenance requirements, or benchmark readiness assumptions must also review the T4 spec, and link directly to:
  - the T4 README
  - the T4 amendment/obligation surface in `benchmark-readiness.md#t4-br-09`

This backlink is load-bearing, not decorative. It is the core value of the whole effort.

### 3. Keep scope deliberately narrow

Do **not**:
- move or copy the T4 directory
- add a frozen archive or compatibility mirror
- change any file paths
- touch `spec.yaml`, authority labels, IDs, anchors, or normative T4 content
- edit tracked handoffs, audits, tickets, or archived documents
- add broader docs-index discoverability changes outside the four surfaces above
- fix unrelated local broken-anchor cleanup as part of this change

This is a reclassification and discoverability patch, not a documentation reorganization project.

## Public Interface / Reader-Facing Changes

- Readers entering via codex-collaboration will now see T4 referenced as the normative scouting/evidence contract.
- Readers entering via T4 will now see explicit language that it is a normative peer spec despite residing under `docs/plans/`.
- All existing historical references continue to resolve by construction because no paths change.
- Tooling behavior is unchanged because no manifests or spec roots move.

## Test Plan

- Verify the T4 README clearly states that it is the canonical normative T4 spec and that `docs/plans/` is a historical location, not a planning-status signal.
- Verify the monolith shim still resolves all existing links and now describes the modular tree as the canonical normative T4 spec.
- Verify the codex-collaboration README contains a `Related Specs` reference to the T4 README.
- Verify the benchmark contract `Change Control` section contains the new cross-spec review rule and links to both the T4 README and `benchmark-readiness.md#t4-br-09`.
- Verify all added links resolve with no path changes required.
- Verify `rg 't04-t4-scouting-position-and-evidence-provenance|benchmark-readiness.md#t4-br-09'` shows the new codex-collaboration references.
- Verify no files outside the four target docs changed.

## Assumptions And Defaults

- Default chosen: **Core surfaces only.** No top-level docs index or broader discoverability sweep.
- Assumption: T4 remains closed for now, so in-place reclassification is sufficient and lower risk than relocation.
- Assumption: preserving stable historical references is more important than making the directory taxonomy perfectly pure.
- Default wording stance: describe T4 as a **normative peer specification located under `docs/plans/` for historical continuity**.
- Deferred explicitly: if T4 later becomes active again and the `docs/plans/` location starts causing real implementation or review errors, revisit physical relocation only together with tooling/policy support.

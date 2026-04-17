# Benchmark v1 Summary

**Contract:** `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`
**Decision source:** `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`
**Operator:** `jp`
**Date:** `2026-04-17`

## Closeout Mode

**Mode:** `DEMONSTRATED — not scored`

This benchmark track is imported as a demonstrated-not-scored capture set. The
artifacts are preserved, but aggregate metrics and pass-rule rendering are not
applied. The parent ticket resolves AC-7 directly on the architectural
signature and its caveats.

## Run-Condition Status

| Control | Status | Detail |
|---------|--------|--------|
| Commit (RC 1) | Not reconciled | Capture set spans `693551cc`, `fa75111b`, and `4c0e2a46`; aggregate scoring was not pursued |
| Working tree (RC 2) | Matched | All staging outside repo; batch import in Phase 5 |
| Prompt (RC 3) | Matched | Same corpus prompt with scope instructions |
| Posture (RC 4) | Matched | Both systems accept `-p` flag |
| Turn budget (RC 4) | Matched | Both systems accept `-n` flag |
| Model/effort/timeout (RC 5) | Matched | `gpt-5.4`, `high`, `1200s` requested across the capture set |
| Supplemental context (RC 6) | Verified | All recorded runs use canonical session ids and fresh-session capture discipline |
| Scouting tools (RC 7) | Matched | Glob/Grep/Read for both |
| Transcript retention (RC 8) | Matched | Staged externally, imported at end |
| `allowed_roots` (RC 10-11) | Prompt-only | Scope is diagnosed from transcripts; baseline scope contamination is recorded as a benchmark exception rather than scored input |
| `max_evidence` | Asymmetric (deliberate) | Baseline: 5 (procedural; overflow invalidates). Candidate: 15 (native) |

**Scoring status:** Aggregate scoring intentionally not rendered. The open
scope-governance and manifest-reconciliation questions became moot once the
parent ticket chose AC-7-direct closeout.

## Capture Set

| Row | System | Converged | Evidence | Turns | Capture note |
|-----|--------|-----------|----------|-------|--------------|
| B1 | baseline | Yes | 0 | 5 | Converged, but synthesis cites implementation files outside `allowed_roots`; scope-clean scoring not pursued |
| B1 | candidate | Yes | 5 | 5 | Converged, cleanest contract-vs-delivery lens split in the set |
| B3 | baseline | Yes | 0 | 4 | Converged with transcript-visible Codex-side scope escapes |
| B3 | candidate | No | 2 | 3 | Preserved artifact despite reply-path parse failure; extraction bug tracked separately in `T-20260416-01` |
| B5 | baseline | Yes | 0 | 5 | Converged with transcript-visible Codex-side scope escapes |
| B5 | candidate | No | 5 | 5 | Preserved artifact despite reply-path parse failure on the final closure turn |
| B8 | baseline | Yes | 1 | 5 | Strongest baseline scope-contamination row in the set |
| B8 | candidate | Yes | 8 | 5 | Strongest candidate artifact in the set; converged comparative synthesis with no extraction failure |

## Aggregate Scoring Status

No aggregate metrics or pass-rule verdict are rendered for this closeout.

The benchmark instrument still served its purpose:

- it surfaced the architectural mismatch between baseline Codex-side autonomy
  and candidate agent-side scope discipline,
- it preserved the extraction-bug evidence without forcing a mid-track patch,
- and it produced enough directional evidence to make the retirement decision
  explicit.

## Diagnostic Notes

- The candidate maintained the cleaner agent-side scope profile across all four
  rows, while the baseline repeatedly produced transcript-visible Codex-side
  scope escapes (`B1: 8+`, `B3: 4`, `B5: multiple`, `B8: 26`).
- The extraction mismatch in `T-20260416-01` remains real and benchmark-relevant:
  B3 candidate and B5 candidate reproduced it, while B8 candidate did not.
- The strongest candidate comparative artifact (`B8-candidate`) still names
  three concrete mechanism losses relative to the retired baseline:
  L1 scout integrity, L2 plateau / budget control, and L3 per-scout redaction
  of raw host-tool output.
- The capture set spans multiple documentation-only benchmark-history commits.
  That weakens any claim to a formal v1 score, but it does not erase the
  directional architectural evidence preserved in the imported artifacts.

## Benchmark Exceptions

- No single benchmark-wide `run_commit` was reconciled. Captures span
  `693551cc`, `fa75111b`, and `4c0e2a46`.
- Baseline scope contamination remained an open governance question under the
  original strict reading. That question is closed as moot because aggregate
  scoring is not pursued.
- B3 candidate and B5 candidate terminated with the open reply-path extraction
  bug. Their artifacts remain preserved as evidence rather than superseded.
- Claim-level adjudication and aggregate pass/fail rendering were intentionally
  skipped for this closeout mode.

## Retirement Decision

Context-injection remains retired by default for codex-collaboration dialogue
flows.

The captured architectural signature is sufficient evidence for this repo:
candidate dialogue preserved the cleaner scope-discipline story across B1/B3/B5/B8,
and no row established a repo-local need to restore context-injection as the
default evidence path. This decision is made with three explicit caveats:

1. `T-20260416-01` remains open and must still be fixed post-benchmark.
2. The candidate's strongest comparative artifact still identifies L1/L2/L3
   mechanism losses relative to the retired baseline.
3. The benchmark closes as demonstrated-not-scored rather than as a formal v1
   aggregate verdict.

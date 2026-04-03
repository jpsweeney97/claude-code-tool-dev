---
module: crosswalk
status: active
normative: false
authority: supporting
---

# Crosswalk: Monolith → Modular Spec

Maps sections and line ranges from the monolithic design document
(revision 21, commit `214ef168`, 2441 lines) to modular file paths and
requirement IDs. Historical handoff references and review comments that
cite monolith locations resolve through this mapping.

**Source monolith:**
[2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md](../archive/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md)

## Section-Level Mapping

| Monolith Section | Lines | Modular File | Requirement IDs |
|---|---|---|---|
| Preamble (title, date, context, gate, risks, deps) | L1-9 | [README.md](README.md) | — |
| Revision History | L10-34 | [foundations.md](foundations.md) | — (historical) |
| §1 Decision | L36-81 | [foundations.md](foundations.md) | T4-F-01 – T4-F-12 |
| §2 Why This Direction | L82-197 | [foundations.md](foundations.md) | — (rationale) |
| §3.1 Claim occurrence registry | L200-248 | [state-model.md](state-model.md) | T4-SM-01 |
| §3.1.2 Within-turn processing order | L249-304 | [state-model.md](state-model.md) | T4-SM-02 |
| §3.1.1 Referent resolution | L306-336 | [state-model.md](state-model.md) | T4-SM-03 |
| §3.2 Claim reference | L338-349 | [state-model.md](state-model.md) | T4-SM-04 |
| §3.3 Evidence record | L350-451 | [state-model.md](state-model.md) | T4-SM-05 |
| §3.4 Verification state model | L452-537 | [state-model.md](state-model.md) | T4-SM-06 |
| §3.5 Agent working state | L539-612 | [state-model.md](state-model.md) | T4-SM-07 |
| §3.6 Compression-resistant evidence block | L613-645 | [state-model.md](state-model.md) | T4-SM-08 |
| §3.7 Pending-round emission | L646-671 | [state-model.md](state-model.md) | T4-SM-09 |
| §3.8 Evidence persistence | L672-699 | [state-model.md](state-model.md) | T4-SM-10 |
| §3.9 Transcript fidelity specification | L700-736 | [foundations.md](foundations.md) | T4-F-13 |
| §4.1 Per-turn loop | L737-758 | [scouting-behavior.md](scouting-behavior.md) | T4-SB-01 |
| §4.2 Scout skip conditions | L759-768 | [scouting-behavior.md](scouting-behavior.md) | T4-SB-02 |
| §4.3 Scout target selection | L769-800 | [scouting-behavior.md](scouting-behavior.md) | T4-SB-03 |
| §4.4 Scout query coverage | L801-888 | [scouting-behavior.md](scouting-behavior.md) | T4-SB-04 |
| §4.5 Scope breach handling | L889-901 | [containment.md](containment.md) | T4-CT-01 |
| §4.6 Direct-tool containment contract | L903-999 | [containment.md](containment.md) | T4-CT-02, T4-CT-03, T4-CT-04, T4-CT-05 |
| §4.6 Allowed-scope safety | L1000-1010 | [containment.md](containment.md) | T4-CT-05 |
| §4.7 Claim-class scope | L1011-1168 | [scouting-behavior.md](scouting-behavior.md) | T4-SB-05 |
| §5.1 Evidence trajectory | L1169-1201 | [provenance-and-audit.md](provenance-and-audit.md) | T4-PR-01 |
| §5.2 Inline citations and aggregation | L1203-1368 | [provenance-and-audit.md](provenance-and-audit.md) | T4-PR-02 – T4-PR-09 |
| §5.3 Audit chain | L1370-1503 | [provenance-and-audit.md](provenance-and-audit.md) | T4-PR-10 – T4-PR-14 |
| §6 Explicit non-changes (tables) | L1504-1529 | [boundaries.md](boundaries.md) | T4-BD-01, T4-BD-02 |
| §6.1 Helper-era migration | L1530-1549 | [boundaries.md](boundaries.md) | T4-BD-03 |
| §6.2 External blockers | L1550-1730 | [benchmark-readiness.md](benchmark-readiness.md) | T4-BR-01 – T4-BR-09 |
| §7 Rejected alternatives | L1731-2125 | [rejected-alternatives.md](rejected-alternatives.md) | — (non-normative) |
| §8 Verification items | L2127-2441 | [conformance-matrix.md](conformance-matrix.md) | — (cites IDs) |

## Frequently-Referenced Line Ranges

Historical handoffs and review comments commonly cite these specific
locations. This table provides direct resolution.

| Monolith Reference | Lines | Modular Location |
|---|---|---|
| §3.9 transcript fidelity | L700-736 | [T4-F-13](foundations.md#t4-f-13) |
| §4.6 scope_root derivation / conceptual-query blocker | L918-944 | [T4-CT-02](containment.md#t4-ct-02) |
| §5.2 claim_provenance_index wire format | L1217-1236 | [T4-PR-03](provenance-and-audit.md#t4-pr-03) |
| §5.2 narrative-to-ledger relationship | L1294-1336 | [T4-PR-06](provenance-and-audit.md#t4-pr-06) |
| §5.3 mechanical omission diff | L1394-1410 | [T4-PR-11](provenance-and-audit.md#t4-pr-11) |
| §5.3 read-scope rule | L1432-1456 | [T4-PR-12](provenance-and-audit.md#t4-pr-12) |
| §6.2 scored-run prerequisites (8-item gate) | L1637-1706 | [T4-BR-07](benchmark-readiness.md#t4-br-07) |
| §6.2 non-scoring run classification | L1690-1702 | [T4-BR-08](benchmark-readiness.md#t4-br-08) |
| §6.2 amendment table (10 rows) | L1718-1730 | [T4-BR-09](benchmark-readiness.md#t4-br-09) |
| §6.2 proof surface amendment row | L1729 | [T4-BR-09](benchmark-readiness.md#t4-br-09) row 8 |
| §8 checklist item 32 (transcript fidelity) | L2218-2224 | [conformance-matrix.md](conformance-matrix.md) item 32 |
| §8 checklist item 70 (benchmark prerequisites) | L2418-2441 | [conformance-matrix.md](conformance-matrix.md) item 70 |
| §4.7 ClassificationTrace | L1082-1093 | [T4-SB-05](scouting-behavior.md#t4-sb-05) |
| §4.7 state-machine invariants | L1106-1114 | [T4-SB-05](scouting-behavior.md#t4-sb-05) |
| §3.4 lifecycle table | L516-533 | [T4-SM-06](state-model.md#t4-sm-06) |
| §3.5 budget surfaces | L574-578 | [T4-SM-07](state-model.md#t4-sm-07) |
| §3.1.2 canonical ordering | L253-261 | [T4-SM-02](state-model.md#t4-sm-02) |

## Requirement ID Summary

| Prefix | Authority | File | Count |
|--------|-----------|------|-------|
| T4-F | foundation | foundations.md | 13 |
| T4-SM | state-model | state-model.md | 10 |
| T4-SB | scouting-behavior | scouting-behavior.md | 5 |
| T4-CT | containment | containment.md | 5 |
| T4-PR | provenance | provenance-and-audit.md | 14 |
| T4-BR | benchmark-readiness | benchmark-readiness.md | 9 |
| T4-BD | boundaries | boundaries.md | 3 |
| **Total** | | | **59** |

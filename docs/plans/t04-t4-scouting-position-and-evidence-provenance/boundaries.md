---
module: boundaries
status: active
normative: true
authority: boundaries
---

# Boundaries

Non-changes, helper-era migration, and declared T2/T3/synthesis input
changes. These surfaces define what T4 does NOT change and what it
replaces.

## <a id="t4-bd-01"></a>T4-BD-01: Explicit Non-Changes

| Surface | Status |
|---------|-----|
| Pipeline `<!-- pipeline-data -->` | `scout_count` = `len(evidence_log)`. **New fields:** `claim_provenance_index_schema_version` and `claim_provenance_index` ([T4-PR-03](provenance-and-audit.md#t4-pr-03)) for claim→record join |
| Synthesis artifact content | Narrative, inline citations, checkpoint (outcome-based, unchanged), claim ledger ([T4-PR-05](provenance-and-audit.md#t4-pr-05)), `<!-- pipeline-data -->` |
| T3 continuity registry | `set[claim_key]`. T4 builds parallel occurrence registry ([T4-SM-01](state-model.md#t4-sm-01)) |
| T1 termination | Scope breach uses T1. T4 owns partial-round and pending marker ([T4-SM-09](state-model.md#t4-sm-09)) |
| T5 mode | Direct tools. `agent_local` preserved |
| `ConsultEvidence` | Out of scope |
| Benchmark artifact set | No new agent-produced files. T7 proof-surface artifacts ([T4-BR-09](benchmark-readiness.md#t4-br-09) item 8) are T7 deliverables, not T4 outputs. Content additions within synthesis + transcript declared in [T4-BD-02](#t4-bd-02) |
| Synthesis assembler `scout_outcomes` key | **Changed:** entries become `EvidenceRecord`s ([T4-PR-01](provenance-and-audit.md#t4-pr-01)). Declared migration |

## <a id="t4-bd-02"></a>T4-BD-02: Declared T2/T3/Synthesis Input Changes

| Change | Surface | Effect |
|--------|---------|--------|
| Forced-new reclassification (`reinforced`) | T2 counter computation, synthesis `validated_entry` trajectory | `reinforced` with dead referent → counted as `new` everywhere |
| Forced-new reclassification (`revised`) | T2 counter computation, synthesis `validated_entry` trajectory | `revised` with dead referent → counted as `new` everywhere |
| Merger for `new`/`revised` claims | None | Merger is invisible to T2/T3 — claim keeps original status |
| Claim-history surface | Synthesis `validated_entry` trajectory ([dialogue-synthesis-format.md:7](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md)) | Reclassified claims appear as `new` in per-turn records and claim trajectory |
| `not_scoutable` verification status | Synthesis claim trajectory, evidence trajectory, claim ledger grammar | New terminal state not in current synthesis-format vocabulary. Requires format update ([T4-BR-05](benchmark-readiness.md#t4-br-05)) |
| Claim ledger section | New `## Claim Ledger` in synthesis | Flat factual claim inventory with `FACT:` lines and `[ref: N]`. Separate from checkpoint ([T4-PR-05](provenance-and-audit.md#t4-pr-05)) |
| Ledger completeness (MUST, enforcement deferred) | Claim ledger | Repository-facing factual narrative claims MUST have ledger entries with `[ref:]`; dialogue-state reporting is outside that category boundary ([T4-PR-06](provenance-and-audit.md#t4-pr-06)). Synthesis-contract violation if missing. Not a G3 concern |
| `claim_provenance_index` | Pipeline `<!-- pipeline-data -->` | Replaces `evidence_map` (rev 10-11). Two variants: scouted and not_scoutable, each carrying required `conceded: bool` ([T4-PR-03](provenance-and-audit.md#t4-pr-03)) |
| `claim_provenance_index_schema_version` | Pipeline `<!-- pipeline-data -->` | Versions the `claim_provenance_index` array contract specifically. Initial value `1` marks the first versioned shape; full bump-trigger policy remains under F11 |

## <a id="t4-bd-03"></a>T4-BD-03: Helper-Era Migration

`agent_local` mode (T5) uses direct Glob/Grep/Read instead of
`execute_scout` / `process_turn`. The following helper-era surfaces are
severed and replaced by T4-local equivalents:

| Helper-era surface | Source | T4 replacement | Notes |
|-------------------|--------|---------------|-------|
| `evidence_wrapper` in follow-up | [codex-dialogue.md:368](../../../packages/plugins/cross-model/agents/codex-dialogue.md), [codex-dialogue.md:414](../../../packages/plugins/cross-model/agents/codex-dialogue.md) | Evidence block entry (entity, disposition, citations) | Follow-up references evidence record |
| `evidence_wrapper` in `scout_outcomes` | [codex-dialogue.md:144](../../../packages/plugins/cross-model/agents/codex-dialogue.md) | `EvidenceRecord` ([T4-PR-01](provenance-and-audit.md#t4-pr-01) projection) | Declared above |
| `read_result` / `grep_result` storage | [codex-dialogue.md:369](../../../packages/plugins/cross-model/agents/codex-dialogue.md) | Raw tool output in transcript | Direct tools, no helper mediation |
| `execute_scout` call | [codex-dialogue.md:354](../../../packages/plugins/cross-model/agents/codex-dialogue.md) | Direct Glob/Grep/Read ([T4-SB-04](scouting-behavior.md#t4-sb-04)) | Per T5 `agent_local` mode |
| `scout_token` / `scout_option` | [context-injection-contract.md:673](../../../packages/plugins/cross-model/references/context-injection-contract.md) | T4 target selection ([T4-SB-03](scouting-behavior.md#t4-sb-03)) | Local priority ranking |
| `budget.scout_available` | [codex-dialogue.md:352](../../../packages/plugins/cross-model/agents/codex-dialogue.md) | `evidence_count >= max_evidence` | Local budget check |
| `template_candidates` from `process_turn` | [codex-dialogue.md:348](../../../packages/plugins/cross-model/agents/codex-dialogue.md) | T4 verification state ([T4-SB-03](scouting-behavior.md#t4-sb-03)) | Local priority ranking |

This is the set of **scouting-related** surfaces that T4 replaces.
Non-scouting surfaces (e.g., `process_turn` for claim extraction,
`state_checkpoint` for ledger) are addressed by T5/T6, not T4.

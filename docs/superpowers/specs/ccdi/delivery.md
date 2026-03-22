---
module: delivery
status: active
normative: true
authority: delivery
---

# CCDI Delivery

## Rollout Strategy

Ship in two phases to isolate risk:

| Phase | Scope | Risk profile |
|-------|-------|-------------|
| **Phase A** | Initial CCDI only (ccdi-gatherer subagent + CCDI-lite) | Low — clean additive feature, no interaction with existing turn loop |
| **Phase B** | Mid-dialogue CCDI (per-turn prepare/commit in codex-dialogue) | Higher — control-plane duplication risk, source hierarchy inversion potential |

Phase B enters **shadow mode** first: the [prepare/commit cycle](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) runs and emits diagnostics but does NOT inject packets into the follow-up prompt.

### Shadow Mode Gate

The gate condition (what file to read, what field values mean, what default applies when absent) is defined in [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) under `behavior_contract` authority. This section retains the graduation protocol and kill criteria under `implementation_plan` authority.

### Shadow Mode Kill Criteria

| Criterion | Threshold | Metric |
|-----------|-----------|--------|
| Effective prepare yield | < 40% | `(prepared AND target-relevant AND surviving precedence) / total prepared` |
| Per-turn CCDI latency | > 500ms | Average of prepare + commit per turn |
| False-positive injection rate | > 10% | CCDI fires on non-Claude-Code topics |

Secondary diagnostic (not a hard kill): `relevant_but_scout_deferred_rate` = `packets_deferred_scout / packets_prepared`. High values indicate healthy scout precedence, not CCDI failure.

Graduate from shadow to active when kill criteria are clear across 10+ shadow dialogues.

## Diagnostics

Per-dialogue summary, accumulated across turns and emitted once at dialogue end via the analytics emitter. (**Authority note:** The diagnostics schema is defined here under the `verification_strategy` claim for testing purposes. It is not an `interface_contract` — no external consumer depends on this schema.)

```json
{
  "ccdi": {
    "status": "active | shadow | unavailable | no_topics | error",
    "phase": "initial_only | full",
    "topics_detected": ["hooks.pre_tool_use"],
    "topics_injected": ["hooks.pre_tool_use"],
    "topics_deferred": ["skills.frontmatter"],
    "topics_suppressed": [],
    "packets_prepared": 3,
    "packets_injected": 2,
    "packets_deferred_scout": 1,
    "total_tokens_injected": 680,
    "semantic_hints_received": 1,
    "search_failures": 0,
    "inventory_epoch": "2026-03-20T...",
    "config_source": "data/ccdi_config.json | defaults",
    "packets_target_relevant": 2,
    "packets_surviving_precedence": 1,
    "false_positive_topic_detections": 0,
    "per_turn_latency_ms": [312, 287, 345]
  }
}
```

In shadow mode (Phase B rollout), `packets_prepared` accumulates but `packets_injected` stays 0. The shadow diagnostics reveal what CCDI *would have* injected for kill-criteria evaluation.

Fields `packets_target_relevant`, `packets_surviving_precedence`, and `false_positive_topic_detections` are present only when `status: "shadow"`. In active mode, they are omitted. Their definitions:

- `packets_target_relevant`: count of prepared packets that passed the target-match check
- `packets_surviving_precedence`: count of target-relevant packets not deferred by scout priority
- `false_positive_topic_detections`: always 0 in the automated diagnostics emitter — the system cannot mechanically determine false positives. The actual count is produced by a human labeler during shadow evaluation (see labeling protocol below) and recorded in a separate annotation file, not in the emitted diagnostics JSON. The field is present in the schema for completeness and forward compatibility; its emitted value of 0 does NOT mean zero false positives
- `per_turn_latency_ms`: array of wall-clock milliseconds, one entry per turn, measuring from `dialogue-turn` invocation start to `build-packet --mark-injected` completion (or `--mark-deferred` if deferred). Turns where no candidate is produced record the latency from `dialogue-turn` start to `dialogue-turn` exit. Latency measurement boundary: wall-clock time per turn from `dialogue-turn` start to final commit/defer. The graduation report's `avg_latency_ms` is computed as the mean of this array.

`effective_prepare_yield` = `packets_surviving_precedence / packets_prepared`. `relevant_but_scout_deferred_rate` = `packets_deferred_scout / packets_prepared` (derived from existing schema fields; not emitted directly — compute from the two component values). `false_positive_rate` is NOT derivable from diagnostics fields — it requires annotation data from the labeling protocol below (`labeled_false_positives / total_labeled_topics`). The `false_positive_topic_detections` field in automated diagnostics is always 0 and MUST NOT be used in the formula.

**False-positive labeling protocol:** This kill criterion requires **human review** — it is not mechanically verifiable in CI. The `false_positive_topic_detections` field in the automated diagnostics is always 0 (the emitter has no way to determine false positives). The actual false-positive count is produced through a separate annotation process:

1. During shadow evaluation, the diagnostics emitter writes `topics_detected` arrays to per-dialogue diagnostics files stored in `data/ccdi_shadow/diagnostics/`.
2. A human labeler reviews a minimum of 100 detected topics across 10+ dialogues. For each topic in `topics_detected`, the labeler checks whether the input text genuinely discusses a Claude Code extension concept. Topics where the input text uses extension terminology in a non-Claude-Code context (e.g., "React hook", "webpack plugin") are false positives.
3. The labeler records labels in a JSONL annotation file at `data/ccdi_shadow/annotations.jsonl`. Each line is a JSON object:

```json
{"dialogue_id": "<id>", "turn": 1, "topic_key": "hooks.pre_tool_use", "input_excerpt": "...", "label": "true_positive" | "false_positive", "labeler": "<name>", "timestamp": "<ISO>"}
```

4. `false_positive_rate` = `labeled_false_positives / total_labeled_topics`. The 10% kill threshold requires statistical confidence: label at least 100 topics before evaluating.

**Graduation protocol:** Shadow-to-active graduation is a manual gate with a concrete approval artifact:

1. **Preflight:** Verify that `uv run pytest tests/test_ccdi_agent_sequence.py` passes all 3 baseline behavioral tests (classify ordering, skip-when-no-candidates, --mark-injected-after-codex-reply). Layer 2b coverage is a prerequisite for Phase B graduation — do not evaluate kill criteria until this gate passes.
2. **Evaluation:** Compute all three kill criteria (effective_prepare_yield, per-turn latency, false_positive_rate) from diagnostics + annotations across 10+ shadow dialogues.
3. **Approval artifact:** Write a graduation report to `data/ccdi_shadow/graduation.json`:

```json
{"status": "approved" | "rejected", "evaluated_dialogues": 12, "labeled_topics": 150, "effective_prepare_yield": 0.65, "avg_latency_ms": 320, "false_positive_rate": 0.04, "approver": "<name>", "timestamp": "<ISO>", "notes": "..."}
```

4. **Validation:** Before finalizing `graduation.json`, run the graduation-report validator (`scripts/validate_graduation.py`). The validator checks: (a) `labeled_topics` matches actual line count in `data/ccdi_shadow/annotations.jsonl`, (b) `false_positive_rate` matches `labeled_false_positives / total_labeled_topics` computed from annotations, (c) `evaluated_dialogues` matches actual file count in `data/ccdi_shadow/diagnostics/`, (d) `effective_prepare_yield` and `avg_latency_ms` are consistent with per-dialogue diagnostics files. This does not eliminate human judgment but adds a mechanical consistency check.
5. **Gate:** The `codex-dialogue` agent reads `graduation.json` at dialogue start per the [shadow mode gate](#shadow-mode-gate) above. The graduation protocol (this section) governs how the file is produced and approved, and the gate condition that `codex-dialogue` evaluates at startup.
6. **Rejection:** If any kill criterion exceeds its threshold, set `status: "rejected"` with the failing criterion in `notes`. Re-evaluate after tuning.

#### `test_validate_graduation.py`

| Test | Input | Expected |
|------|-------|----------|
| Annotations count matches labeled_topics | `annotations.jsonl` with line count equal to `labeled_topics` in `graduation.json` | Exit 0, validation passes |
| Annotations count mismatches labeled_topics | `annotations.jsonl` with 100 lines but `graduation.json` has `labeled_topics: 150` | Exit 1, error reports line count 100 vs declared 150 |
| False-positive rate arithmetic mismatch | `annotations.jsonl` with 8 `false_positive` labels out of 120 total (rate=0.067) but `graduation.json` has `false_positive_rate: 0.04` | Exit 1, error reports computed rate 0.067 vs declared 0.04 |
| Diagnostics file count mismatches evaluated_dialogues | `data/ccdi_shadow/diagnostics/` contains 10 files but `graduation.json` has `evaluated_dialogues: 12` | Exit 1, error reports file count 10 vs declared 12 |
| Yield/latency metrics arithmetically inconsistent | Per-dialogue diagnostics files imply `effective_prepare_yield` of 0.55 and `avg_latency_ms` of 340, but `graduation.json` declares 0.65 and 320 respectively | Exit 1, error identifies inconsistent metric(s) with computed vs declared values |
| Missing annotations.jsonl | `data/ccdi_shadow/annotations.jsonl` does not exist | Exit 1, error reports missing annotations file |
| Malformed annotations.jsonl | `annotations.jsonl` contains non-JSON lines interspersed with valid JSONL | Exit 1, error reports parse failure with line number |
| Missing diagnostics directory | `data/ccdi_shadow/diagnostics/` does not exist | Exit 1, error reports missing diagnostics directory |
| Floating-point tolerance for false_positive_rate | `annotations.jsonl` yields computed rate 0.0400001 vs declared 0.04 | Exit 0, rates match within floating-point tolerance |

## Testing Strategy

### Four-Layer Approach

| Layer | What it tests | How |
|-------|--------------|-----|
| **Layer 1: Unit tests** | CLI deterministic logic ([classifier](classifier.md), [registry](registry.md), [packet builder](packets.md)) | Standard pytest, full coverage of data shapes and state transitions |
| **Layer 2a: Replay harness** | CLI pipeline correctness ([prepare/commit](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) loop, [semantic hints](registry.md#semantic-hints), state transitions) | Structured `ccdi_trace` + assertion on CLI input/output and registry state, not prose |
| **Layer 2b: Agent sequence tests** | Agent tool-call ordering (codex-dialogue invokes CLI commands in correct sequence) | Live agent invocation with mocked tools |
| **Layer 3: Shadow mode** | End-to-end quality (false positives, source hierarchy, latency) | Phase B rollout with kill criteria (see [above](#shadow-mode-kill-criteria)) |

### Debug-Gated `ccdi_trace`

The `codex-dialogue` agent emits a structured trace when CCDI is active, gated by a `ccdi_debug` flag in the delegation envelope:

```json
[
  {
    "turn": 1,
    "classifier_result": {"resolved_topics": [...], "suppressed_candidates": [...]},
    "semantic_hints": null,
    "candidates": [],
    "action": "none",
    "packet_staged": false,
    "scout_conflict": false,
    "commit": false
  },
  {
    "turn": 3,
    "classifier_result": {"resolved_topics": [...], "suppressed_candidates": [...]},
    "semantic_hints": [{"claim_index": 3, "hint_type": "prescriptive", "claim_excerpt": "you should use updatedInput to modify..."}],
    "candidates": [{"topic_key": "hooks.post_tool_use", "family_key": "hooks", "facet": "schema", "confidence": "high", "coverage_target": "leaf", "candidate_type": "new", "query_plan": {"default_facet": "overview", "facets": {"schema": [{"q": "PostToolUse hook output", "category": "hooks", "priority": 1}]}}}],
    "action": "prepare",
    "packet_staged": true,
    "scout_conflict": false,
    "commit": true
  }
]
```

Full candidate object schema: see [integration.md#dialogue-turn-candidates-json-schema](integration.md#dialogue-turn-candidates-json-schema).

**Normative output contract:** The `action` normative values and trace entry key-presence invariant are defined in [integration.md#ccdi_trace-output-contract](integration.md#ccdi_trace-output-contract) under `interface_contract` authority. The key-presence invariant is validated by `trace_assertions` with `assert_key_present` checks (see replay harness below).

The replay harness collects these traces and asserts on:

- **CLI pipeline sequence:** classify → dialogue-turn → build-packet (prepare) → build-packet --mark-injected (commit). The harness validates the deterministic CLI pipeline produces correct outputs given canned inputs. `search_docs` results are canned from fixture data; `codex-reply` is assumed successful unless the fixture sets `codex_reply_error: true`.
- **State transitions:** topic moved from `detected` → `[looked_up]` → `[built]` → `injected`
- **Deferred handling:** scout conflict → `deferred` state, not `injected`; target mismatch → `deferred: target_mismatch`
- **Send failure revert:** codex-reply error → commit step not invoked → topic remains `detected`
- **Semantic hint propagation:** hint received → candidate elevated → packet built

## Unit Tests

### Classifier Tests: `test_topic_inventory.py`

| Test | Verifies |
|------|----------|
| Exact alias → high confidence | `"PreToolUse"` → `hooks.pre_tool_use`, high |
| Phrase match with facet hint | `"pre tool use"` → facet=overview |
| Generic token alone suppressed | `"schema"` alone → no resolved topics |
| Generic shifts facet with anchor | `"PreToolUse schema"` → facet=schema |
| Leaf absorbs parent family | `"PreToolUse hook"` → leaf only |
| Weak leaves collapse to family | Two low-weight hook leaves → `hooks` family |
| Denylist drop | `"overview"` → dropped |
| Denylist downrank | `"settings"` → weight reduced |
| Denylist penalty clamping to zero | alias weight=0.3, penalty=0.5 → effective weight=0 (not -0.2) |
| No matches → empty | `"fix the database query"` → empty |
| Multiple families detected | `"PreToolUse hook and SKILL.md frontmatter"` → two topics |
| Normalization variants | `PreToolUse`, `pretooluse`, `SKILL.md`, backticked forms |
| Alias collision tiebreak | Same token in two topics → deterministic winner |
| False-positive contexts | `"React hook"`, `"webpack plugin"` → no CCDI topics |
| Missing-facet fallback | Requested facet missing → falls back to `default_facet` |
| Multi-leaf same family | Both `PreToolUse` and `PostToolUse` in one input |
| Repeated mentions don't inflate | `"PreToolUse PreToolUse PreToolUse"` → same score as one mention |
| Evaluation order: exact beats token | Input matching both an exact alias (weight 0.6) and a token alias (weight 0.9) on the same topic → exact match evaluated first; final score reflects evaluation-order semantics (exact-before-token precedence), not pure weight sum |
| Evaluation order: longer phrase wins within type | Two phrase aliases of different lengths matching overlapping substrings → longer, more specific phrase takes precedence; shorter phrase does not additionally contribute to score |

### Registry Tests

| Test | Verifies |
|------|----------|
| New topic → detected | First appearance starts in detected |
| Happy path: detected → [looked_up] → [built] → injected | Full forward transition with commit |
| Attempt states not persisted | looked_up and built absent from written registry file |
| Candidate selection after detection | Detected topic in candidates |
| Injected not re-selected | After mark-injected → not in candidates |
| Suppressed: weak results | [looked_up] → suppressed on empty search |
| Suppressed: redundant | [looked_up] → suppressed when search returns results but all `chunk_id` values filtered by deduplication against `injected_chunk_ids` → `suppressed: redundant` (distinct from `weak_results`) |
| Suppressed re-enters on stronger signal | suppressed → detected |
| Deferred: cooldown | Candidate deferred when cooldown active |
| Deferred: scout priority | Candidate deferred when scout target exists |
| Deferred: target mismatch | Staged packet fails target-match check → `deferred: target_mismatch` via `--mark-deferred` |
| Deferred TTL initialization | TTL set to `deferred_ttl_turns` config value at deferral time |
| Deferred TTL decrement per turn | TTL decrements by 1 on each `dialogue-turn` call regardless of classifier output |
| Deferred TTL expiry + reappearance | TTL=0 AND topic in classifier output → `detected` |
| Deferred TTL expiry without reappearance | TTL=0 but topic absent from classifier → TTL resets to `ccdi_config.injection.deferred_ttl_turns` (not hardcoded), stays `deferred`; verify with non-default config value (e.g., `deferred_ttl_turns=5`) |
| Deferred vs suppressed distinction | Different reasons, different re-entry paths |
| Suppressed re-entry: weak_results | `docs_epoch` change → suppressed topic re-enters as `detected` |
| Suppressed re-entry: redundant | Coverage state change → suppressed topic re-enters as `detected` |
| Cooldown configurable | Reads from ccdi_config.json |
| Consecutive-turn medium threshold (leaf) | Medium **leaf** topic on turn 1 → no injection; same leaf topic on turn 2 → injection fires; counter resets if topic changes |
| Consecutive-turn medium threshold (family excluded) | Medium **family** topic on turns 1, 2, 3 → `consecutive_medium_count` stays 0 on each turn; injection does NOT fire. Family-kind topics do not participate in consecutive-medium tracking (per [registry.md#scheduling-rules](registry.md#scheduling-rules) rule 4). |
| Consecutive-medium reset on topic absence | Medium topic turn 1 (count=1), topic absent from classifier output turn 2 (count reset to 0), medium topic turn 3 (count=1) → injection does NOT fire on turn 3 (threshold requires 2 consecutive turns, absence breaks the streak) |
| Family injection doesn't cover leaves | Inject hooks → hooks.post_tool_use still detected |
| Leaf inherits family_context_available | Flag set after family injected |
| Leaf then family tracked independently | Both have separate coverage |
| Facet evolution | overview injected, schema still pending → new lookup |
| Idempotent mark-injected | Same packet twice doesn't corrupt |
| No commit without send | build-packet without --mark-injected leaves topic in detected |
| Send failure reverts to detected | When send fails and --mark-injected is skipped, topic remains `detected` (agent-level flow) |
| Send failure preserves consecutive_medium_count | Medium topic turn 1 (count=1), send fails at turn 2 (count still 1, not reset) → turn 3 same medium topic (count=2) → injection fires. Verifies counter is NOT reset when `[built] → injected` transition does not fire. |
| Registry corruption recovery | Malformed JSON → reinitialize empty |
| Semantic hint elevates candidate | Prescriptive hint on detected topic → materially new |
| Semantic hint with unknown topic | Hint doesn't match any topic → ignored |
| Malformed hints file | Invalid JSON → ignored with warning |
| Single medium-confidence → no initial injection | 1 medium-confidence topic (no same-family companion) → injection candidates empty; no CCDI packet built |
| Low-confidence topic → detected but never injected | Topic with `confidence: low` → enters `detected` state AND is excluded from `dialogue-turn` injection candidates output; no injection fires regardless of turn count |
| docs_epoch null comparison: null == null → no re-entry | Suppressed topic at docs_epoch=null, re-evaluated at docs_epoch=null → suppression_reason unchanged, state stays `suppressed` |
| docs_epoch null comparison: null → non-null → re-entry | Suppressed topic at docs_epoch=null, re-evaluated at docs_epoch="2026-03-20" → state transitions to `detected`, `suppressed_docs_epoch` ← null |
| docs_epoch null comparison: non-null → null → re-entry | Suppressed topic at docs_epoch="A", re-evaluated at docs_epoch=null → state transitions to `detected` |
| consecutive_medium_count reset after injection | Medium topic turn 1 (count=1), turn 2 (count=2, injection fires, committed) → turn 3 same medium topic → injection does NOT fire (counter reset to 0 at injection; count=1, threshold not yet met) |
| pending_facets cleared after serving | `contradicts_prior` hint adds facet F to `pending_facets` → injection at facet F succeeds via `--mark-injected` → verify `coverage.pending_facets` does NOT contain F AND `coverage.facets_injected` DOES contain F |
| injected_chunk_ids populated at commit | `build-packet --mark-injected` with result set containing chunk IDs [X, Y] → verify `coverage.injected_chunk_ids` contains [X, Y] → subsequent `build-packet` call with same results → chunk IDs excluded from output |
| Injected forward-only invariant | Topic transitions to `injected`, then `dialogue-turn` called with same topic in classifier output → assert state remains `injected` (not overwritten to `detected`); `last_seen_turn` updated but state unchanged |
| Multiple pending_facets ordering | Two `contradicts_prior` hints add F1 then F2 to `pending_facets` → assert `pending_facets = [F1, F2]`; first injection serves F1 → `pending_facets = [F2]`; second injection serves F2 → `pending_facets = []` |
| Consecutive-medium reset on confidence change | Medium topic turn 1 (count=1), same topic at HIGH confidence turn 2 → `consecutive_medium_count` resets to 0 (injection does NOT fire via the medium path; may fire via the high-confidence path separately) |
| Scheduling tiebreaker: same confidence, same first_seen_turn → topic_key ascending | Two high-confidence topics detected on the same turn; topic B < topic A lexicographically → topic B is scheduled first |
| Suppressed re-detection no-op | Topic in `suppressed:weak_results` at turn N. Turn N+1: topic in classifier output, no re-entry trigger fires → `last_seen_turn` stays N (not N+1), `consecutive_medium_count` unchanged, `state` remains `suppressed` |
| last_query_fingerprint normalization | Querying `"PreToolUse hook"` and `"pretooluse  hook"` (different case/whitespace) produce the same fingerprint. Same query with `docs_epoch="A"` produces a different fingerprint than with `docs_epoch=null` |
| Deferred→detected consecutive_medium_count initialization | Topic deferred (TTL=3), TTL expires at turn N, topic reappears at medium confidence → assert `consecutive_medium_count` = 1 (not 0); reappears at high → assert `consecutive_medium_count` = 0 |
| Suppressed→detected last_seen_turn update | Topic suppressed at turn 2, re-enters as detected at turn 5 (docs_epoch change) → assert `last_seen_turn` = 5 (the re-entry turn, not the original suppression turn) |
| Suppressed:redundant re-entry via new leaf | Topic A (`family_key: hooks`) suppressed:redundant, then new leaf `hooks.post_tool_use` transitions to `detected` in same family → topic A re-enters as `detected` on the same `dialogue-turn` call |
| Prescriptive hint re-enters suppressed:weak_results | Topic suppressed:weak_results, prescriptive hint resolves to same topic → state transitions to `detected`, `suppression_reason` ← null, `suppressed_docs_epoch` ← null, `last_seen_turn` updated |
| Prescriptive hint re-enters suppressed:redundant | Topic suppressed:redundant, prescriptive hint resolves to same topic → same re-entry field updates as weak_results case |
| Contradicts_prior hint re-enters suppressed:weak_results | Topic suppressed:weak_results, contradicts_prior hint resolves to same topic → state transitions to `detected` (same re-entry as prescriptive/suppressed) |
| Contradicts_prior hint re-enters suppressed:redundant | Topic suppressed:redundant, contradicts_prior hint resolves to same topic → state transitions to `detected` |
| Suppressed:redundant no re-entry on docs_epoch change | Topic suppressed:redundant at docs_epoch="A", re-evaluated at docs_epoch="B" → state stays `suppressed`, `suppression_reason` stays `redundant`. `docs_epoch` change triggers re-entry only for `weak_results`, not `redundant`. |
| Result cache hit avoids re-search | Same query fingerprint submitted twice in one session → `search_docs` called once; second call returns cached results. Assert by counting `search_docs` invocations. |
| Negative cache prevents retry after weak results | Query returns weak results (below `quality_min_result_score`) → same query resubmitted → `search_docs` NOT re-invoked; negative cache flag prevents retry. Assert suppression on second attempt without search. |
| Packet cache serves existing packet | Same `(topic_key, facet)` pair requested twice in one session → `build-packet` returns cached packet on second call without re-ranking. Assert identical output. |
| Cache is per-session only | Registry reinitialized (new session) → previously cached query fingerprint re-searched. Assert `search_docs` invoked despite identical query. |
| Cache keys include docs_epoch | Same query string with different `docs_epoch` → cache miss (separate entries). Assert both queries invoke `search_docs`. |
| `facet_expansion` candidate emitted for extends_topic on injected | Topic injected at facet `overview`. `extends_topic` hint resolves to same topic at facet `schema` (not in `facets_injected`) → `dialogue-turn` candidates includes element with `candidate_type: "facet_expansion"`, `facet: "schema"`, `confidence: null`. Topic state remains `injected`. |
| `facet_expansion` cascade fallback to pending_facets | Topic injected at facets `[overview, schema]`. `extends_topic` hint resolves facet `schema` (already in `facets_injected`), `pending_facets: ["config"]` → candidate emitted with `facet: "config"` (cascade fallback to `pending_facets[0]`). |
| `facet_expansion` all facets exhausted → no candidate | Topic injected at all facets including default. `extends_topic` hint resolves to same topic → all candidate facets in `facets_injected` → hint discarded, no candidate emitted, candidates array empty. |
| `pending_facet` candidate emitted after contradicts_prior | Topic injected. `contradicts_prior` hint adds facet F to `pending_facets`. Next `dialogue-turn` call → candidates includes element with `candidate_type: "pending_facet"`, `facet: F`, `confidence: null`. |
| `candidate_type: "new"` for standard candidates | Topic detected at high confidence → `dialogue-turn` candidates includes element with `candidate_type: "new"`. Verifies backward-compatible field presence. |
| Both-facets-absent → suppressed | Topic scheduled for lookup. Scheduled facet absent from `QueryPlan.facets` AND `default_facet` also absent → topic transitions to `suppressed: weak_results`, not left in `detected`. Per [registry.md#scheduling-rules](registry.md#scheduling-rules) step 3. |
| Empty QuerySpec[] treated as absent | Topic's `QueryPlan.facets` has scheduled facet key present but mapped to empty array `[]` → treated as absent, falls back to `default_facet`. Per [registry.md#scheduling-rules](registry.md#scheduling-rules) step 3. |
| Family-kind consecutive_medium_count load-time validation | Load registry with family-kind entry having `consecutive_medium_count: 3` → value reset to 0, warning logged. Per [data-model.md#registryseed](data-model.md#registryseed) load-time validation. |
| deferred_ttl:0 at load, topic present in classifier | Load registry with deferred entry (TTL=0), run dialogue-turn with topic in classifier output → entry transitions to `detected`, TTL field reset |
| deferred_ttl:0 at load, topic absent from classifier | Load registry with deferred entry (TTL=0), run dialogue-turn without topic in classifier output → entry remains `deferred`, TTL reset to configured default |

### Packet Builder Tests

| Test | Verifies |
|------|----------|
| Initial packet within budget | 600–1000 tokens |
| Mid-turn packet within budget | 250–450 tokens |
| Empty results → no packet | Skip, not empty markdown |
| Duplicate chunk IDs filtered | Already-injected excluded |
| Citation format | `[ccdocs:<chunk_id>]` |
| Snippet mode for field names | Exact identifiers use snippet |
| Paraphrase mode for concepts | Behavioral descriptions use paraphrase |
| Too-large snippet truncated | Graceful handling under budget pressure |
| Budget boundary: N+1 facts where N fit | Mid-turn with 4 facts where 3 fit budget (max_facts=3) → output contains ≤ 3 facts, `token_estimate` ≤ 450 |
| Quality threshold boundary: score at 0.3 | Best result score exactly 0.3 → packet IS built (threshold is "below 0.3", so 0.3 passes); score 0.29 → no packet |
| Mid-turn topics cardinality enforced | Mid-turn with 2 topics in result set → output contains only 1 topic per `mid_turn_max_topics` config |
| Mid-turn snippet cardinality enforced | Build mid-turn packet from result set where 3 results each warrant `snippet` mode → output contains at most 1 `snippet`-mode fact and ≥ 1 `paraphrase`-mode facts; `mode: "snippet"` count in `facts[]` is ≤ 1 (per [packets.md#verbatim-vs-paraphrase](packets.md#verbatim-vs-paraphrase) "at most one snippet per mid-turn packet") |
| No resolvable topic keys → empty output | Search results exist but no topic keys resolve (e.g., all results filtered by denylist) → `build-packet` returns empty output or non-zero exit. Verifies the `topics: []` invariant (packets.md: "`topics` MUST NOT be empty") is enforced at build time. |
| Chunk-ordering deterministic | Same input (topic, facet, search results) run twice → assert identical chunk sequence in both outputs. Order: citations first, then summary, then verbatim snippets (per [packets.md#build-process](packets.md#build-process)). |

### CLI Integration Tests

| Test | Verifies |
|------|----------|
| `classify` file I/O round-trip | Reads text file, returns valid JSON |
| `dialogue-turn` updates registry file | State persistence across calls |
| `build-packet --mark-injected` updates registry | Side-effect correctness |
| `dialogue-turn --source codex` vs `--source user` | Both accepted, same pipeline, no crash. Additionally: same input text + same registry state → `--source codex` and `--source user` produce identical stdout candidates JSON and identical registry mutations (behavioral equivalence baseline for future divergence). **Update protocol:** When source-differentiated behavior is implemented, this test MUST be replaced with source-specific behavioral tests, not deleted. |
| `build-packet` empty output writes suppressed automatically (weak) | Search returns poor results + `--registry-file` present → `suppressed: weak_results` in registry |
| `build-packet` empty output writes suppressed automatically (redundant) | Search returns good results but all chunk IDs already in `injected_chunk_ids` + `--registry-file` present → `suppressed: redundant` in registry; verify reason is `redundant` not `weak_results` |
| `build-packet --mark-deferred` writes deferred state | Deferred topic_key and reason persisted to registry |
| Missing inventory → non-zero exit | Graceful failure |
| Malformed text → non-zero exit | Input validation |
| stdout/stderr separation | JSON on stdout only, errors on stderr |
| Automatic suppression requires registry | `build-packet` returns empty output WITHOUT `--registry-file` → no suppression written (stdout empty, no side effects). With `--registry-file` → `suppressed: weak_results` written. Tests the conditional nature of automatic suppression. |
| `--skip-build` with `--mark-deferred` skips packet construction | `build-packet --mark-deferred <key> --deferred-reason <r> --skip-build --registry-file <path>` → registry writes deferred state AND stdout is empty (no packet built) |
| `--skip-build` without `--mark-deferred` is ignored | `build-packet --skip-build --results-file <path> --mode initial` → normal packet construction proceeds (flag silently ignored) |
| Missing `--coverage-target` with `--mark-injected` → error | `build-packet --mark-injected --registry-file <path> --results-file <path> --mode mid_turn` (without `--coverage-target`) → non-zero exit with descriptive error |
| Missing `--topic-key` with `--registry-file` → error | `build-packet --registry-file <path> --results-file <path> --mode mid_turn` (without `--topic-key`) → non-zero exit with descriptive error |
| Missing `--facet` with `--mark-injected` → error | `build-packet --mark-injected --registry-file <path> --results-file <path> --mode mid_turn --topic-key <k> --coverage-target leaf` (without `--facet`) → non-zero exit with descriptive error |
| Facet mismatch at commit time (mid-turn) | Run `build-packet --mode mid_turn --facet schema` (prepare), then `build-packet --mode mid_turn --mark-injected --facet overview` with same `--results-file` → assert non-zero exit with descriptive error including both facet values. The prepare-phase facet is authoritative; commit-phase callers MUST provide the matching value. |
| Prepare/commit packet idempotency (mid-turn) | Run `build-packet --mode mid_turn` (prepare, no `--mark-injected`) then `build-packet --mode mid_turn --mark-injected` with same `--results-file` → stdout markdown from commit matches stdout from prepare |
| Prepare/commit packet idempotency (initial) | Run `build-packet --mode initial --results-file <multi-topic-results>` (prepare, no registry). Then for each topic: run `build-packet --mode initial --results-file <same> --registry-file <reg> --topic-key <k> --facet <f> --coverage-target <t> --mark-injected` → verify per-topic commit stdout matches corresponding topic section from initial prepare stdout, AND `coverage.injected_chunk_ids` matches chunk IDs in rendered packet |
| `dialogue-turn` with non-default `deferred_ttl_turns` config | `ccdi_config.json` with `injection.deferred_ttl_turns: 5`. Topic deferred (TTL=5), 5 turns with topic absent, TTL reaches 0 → assert TTL resets to 5 (config-driven, not hardcoded default 3), state remains `deferred`. Verifies the config-driven nature of the TTL reset per [registry.md#ttl-lifecycle](registry.md#ttl-lifecycle). |

## Boundary Contract Tests: `test_ccdi_contracts.py`

Tests that verify field names, enum values, and schema shapes agree across component boundaries. Guards against silent downgrade.

| Boundary | Contract verified |
|----------|-------------------|
| Inventory → classifier | `topic_key`, `family_key`, alias normalization, denylist shapes |
| Classifier → registry | `confidence`, `facet`, `coverage_target` (flows through candidates JSON), `candidate_type` enum (`"new" \| "facet_expansion" \| "pending_facet"`), `topic_key` enums |
| Registry → search orchestration | Candidates produce valid query specs and category hints |
| Search results → packet builder | Required fields present (`chunk_id`, `category`, `content`), deduplication, ranking stability |
| Packet builder → prompt assembler | Citation format, valid markdown, token budget enforced |
| CLI → agents | Exit codes, stdout JSON contract, stderr behavior, file-path semantics |
| Semantic hints → CLI | `hint_type` enum values, `claim_excerpt` length cap, classifier resolution of excerpt. `claim_index` shape validated for forward compatibility only — CLI ignores its value (diagnostic/trace metadata). |
| `dump_index_metadata` → `build_inventory.py` | Response shape matches expected fields (`index_version`, `docs_epoch`, `categories[].chunks[].chunk_id`, etc.) — cross-package contract |
| `dump_index_metadata` → `build_inventory.py`: schema evolution | Response with unknown top-level field → `build_inventory.py` ignores it (exit 0); required chunk field missing → warning, chunk skipped; `index_version` value change → warning emitted |
| Config → CLI | `ccdi_config.json` schema validated at load; unknown keys warned, missing keys use defaults |
| Registry seed → delegation envelope | `ccdi_seed` file path valid, seed JSON parses to expected schema |
| Mid-dialogue CCDI disabled without ccdi_seed | Delegation envelope without `ccdi_seed` field → diagnostics show `phase: initial_only` AND agent tool-call log contains zero invocations of `dialogue-turn` or `build-packet` (Layer 2b test — see [Layer 2b: Agent Sequence Tests](#layer-2b-agent-sequence-tests)) |
| Version axes → overlay merge | `schema_version`, `overlay_schema_version`, `merge_semantics_version` compatibility validated at build time |
| Inventory → classifier: schema evolution | Unknown TopicRecord field present → ignored (not crash); required Alias field missing → non-zero exit; `schema_version` mismatch at classifier load → warning |
| Inventory → registry: schema evolution | Unknown TopicRegistryEntry field in seed → ignored; required field missing → reinitialize empty (resilience principle) |
| Inventory → packet builder: schema evolution | Unknown QueryPlan facet → skipped; missing `default_facet` → fallback to `overview` |
| Registry null-field serialization | Write a TopicRegistryEntry in `detected` state (where `last_injected_turn`, `last_query_fingerprint`, `deferred_reason`, `deferred_ttl`, `suppression_reason`, `suppressed_docs_epoch` are all null) to the registry file, read back as raw JSON, and assert each nullable field key is present with a `null` value (not absent). Guards against Python serializers that omit null fields by default (e.g., `exclude_none=True`). Per [data-model.md#registryseed](data-model.md#registryseed) null-field serialization invariant. |
| RegistrySeed ↔ TopicRegistryEntry durable fields | Every durable field in TopicRegistryEntry (all except attempt-local states `looked_up`, `built`) is present in RegistrySeed.entries field enumeration — schema-comparison test |
| RegistrySeed ↔ ClassifierResult coverage_target | `RegistrySeed.entries[].coverage_target` matches `ClassifierResult.resolved_topics[].coverage_target` enum (`"family" \| "leaf"`) — cross-schema consistency test |
| RegistrySeed ↔ ClassifierResult facet | `RegistrySeed.entries[].facet` matches `ClassifierResult.resolved_topics[].facet` enum (valid `Facet` values) — cross-schema consistency test |
| RegistrySeed version mismatch + topic_key discard | RegistrySeed with `inventory_snapshot_version` ≠ current `schema_version` AND one entry with valid `topic_key` (present in inventory) AND one with invalid `topic_key` (absent from inventory) → invalid entry discarded, valid entry retained, warning emitted, CLI continues |
| RegistrySeed `results_file` stripped after commit | Write RegistrySeed with `results_file` field to temp file. Run `build-packet --mark-injected` against it. Read back the file and assert `results_file` key is absent. Per [data-model.md#registryseed](data-model.md#registryseed) stripping constraint. |
| RegistrySeed `results_file` stripped after multi-topic commit | Write RegistrySeed with `results_file` and 2 topic entries. Run `build-packet --mark-injected` for topic 1. Assert `results_file` absent after first commit. Run `build-packet --mark-injected` for topic 2. Assert second commit succeeds against the now-stripped file. |
| RegistrySeed `results_file` stripped when all commits fail | Write RegistrySeed with `results_file` and 1 topic entry. Run `build-packet --mark-injected` with an invalid `--topic-key` (not in seed) → non-zero exit. Assert `results_file` is still stripped from the file on the next successful mutation (the field is stripped at write time, not as a commit side-effect). |
| RegistrySeed `results_file` present on load | Load a registry file containing a `results_file` field → field stripped from in-memory representation, warning logged. Per [data-model.md#failure-modes](data-model.md#failure-modes). |
| Registry null-field serialization includes envelope fields | Write RegistrySeed with `docs_epoch: null` to temp file. Read back as raw JSON and assert `docs_epoch` key is present with `null` value (not absent). Per [data-model.md#registryseed](data-model.md#registryseed) envelope null-field invariant. |
| RegistrySeed ↔ TopicRegistryEntry durable fields includes coverage sub-fields | Schema-comparison test must enumerate all 5 `coverage.*` sub-fields (`overview_injected`, `facets_injected`, `pending_facets`, `family_context_available`, `injected_chunk_ids`) as durable. |

## Integration Tests

| Test | Verifies |
|------|----------|
| ccdi-gatherer produces valid markdown | End-to-end initial injection |
| `/codex` CCDI-lite briefing injection | Briefing contains `### Claude Code Extension Reference` |
| Full dialogue turn with mid-turn injection | Registry persists across turns |
| Graceful degradation without `search_docs` | Consultation proceeds, `ccdi_status: unavailable` |
| Malformed search results handled | Missing `chunk_id`, empty content → skip, not crash |
| Inventory schema version mismatch | Older inventory → warning, not crash |
| Inventory missing `overlay_meta` field | Valid JSON `topic_inventory.json` without `overlay_meta` key → warning emitted, CCDI continues with empty applied rules and no config overrides |
| Inventory stale (`docs_epoch` mismatch) | Load `topic_inventory.json` with `docs_epoch` differing from active `claude-code-docs` server's epoch → diagnostics warning emitted, CCDI continues (non-blocking) |
| `ccdi_debug` gating of trace emission | With `ccdi_debug=true` → `ccdi_trace` key present in agent output AND each trace entry contains all required fields (`turn`, `classifier_result`, `semantic_hints`, `candidates`, `action`, `packet_staged`, `scout_conflict`, `commit`). `classifier_result` must contain `resolved_topics` and `suppressed_candidates` sub-fields per the [ClassifierResult contract](classifier.md#output-structure). `semantic_hints` is always present as a field: `null` when no hints were provided for the turn, a non-empty array when hints exist. Field-absent is NOT valid — always include the key with a null or array value. With `ccdi_debug` absent → no `ccdi_trace` key. |
| `ccdi_trace` semantic_hints conditional presence | Multi-turn trace: turn 1 has no hints → `ccdi_trace[0].semantic_hints == null` (field present, value null); turn 2 has hints → `ccdi_trace[1].semantic_hints` is a non-empty array. Assert field is always present (never absent from the trace entry). Additionally: for every trace entry, assert `"semantic_hints" in entry` (key-presence check, independent of value) — this catches serializers that omit null-valued keys. |
| Sentinel extraction from ccdi-gatherer | Valid sentinel block (matching open/close tags, valid JSON between) → `ccdi_seed` path present in delegation envelope and file contains valid RegistrySeed JSON |
| Malformed sentinel handling | Covers: (a) missing closing sentinel tag, (b) invalid JSON between sentinels, (c) mismatched tag names (open tag correct, close tag uses different separator). All → graceful degradation to `initial_only` phase; `/dialogue` proceeds without `ccdi_seed`. |
| ccdi-gatherer returns no sentinel | No sentinel block in ccdi-gatherer output → no `ccdi_seed` field in delegation envelope, `phase: initial_only` in diagnostics |
| Initial CCDI commit skip on briefing-send failure | Briefing send fails → seed entries remain in `detected` state (verify registry file contains `state: "detected"` for all entries, not `state: "injected"`) |
| Temp file identity per turn | Verify `<id>` in `/tmp/ccdi_*_<id>.*` paths is unique per turn (not per dialogue), preventing cross-turn file collisions in the prepare/commit protocol |
| CCDI-lite: low-confidence detection → no injection, no state written | All resolved topics are low-confidence in CCDI-lite mode → `build-packet` is not invoked, no registry file created or modified |
| Initial threshold not met (Full CCDI) | All resolved topics are low-confidence → ccdi-gatherer not dispatched, no `### Claude Code Extension Reference` section in briefing |
| Initial threshold not met (CCDI-lite) | Low-confidence only → no `build-packet` invoked, briefing proceeds without CCDI content |
| Inventory pinning across mid-dialogue reload | Start dialogue with inventory V1 using `--inventory-snapshot <path-to-V1>`. Replace `topic_inventory.json` on disk with V2 (different topic set). Run `dialogue-turn` → assert classifier uses V1 topics (pinned snapshot), not V2. Verifies dialogue-start pinning per [data-model.md#inventory-lifecycle](data-model.md#inventory-lifecycle). **Pinning mechanism:** The `--inventory-snapshot` flag on CLI commands accepts a path to a compiled inventory file. When provided, the CLI uses this file instead of the default inventory location, ignoring any on-disk changes during the session. |
| Shadow mode diagnostics fields present | Run dialogue in shadow mode → diagnostics JSON contains `packets_target_relevant`, `packets_surviving_precedence`, `false_positive_topic_detections` fields. |
| Active mode diagnostics fields absent | Run dialogue in active mode → diagnostics JSON does NOT contain `packets_target_relevant`, `packets_surviving_precedence`, `false_positive_topic_detections` fields. Per [delivery.md#diagnostics](#diagnostics): present only when `status: "shadow"`. |
| Suppressed re-detection no-op (CLI file-level) | Registry file with suppressed topic at turn N. Run `dialogue-turn` with the topic in classifier output but no re-entry trigger → assert registry FILE is unchanged (byte-identical or `last_seen_turn` unchanged at minimum). Covers the file I/O contract, not just the in-memory state machine. Companion to the unit-level "Suppressed re-detection no-op" test. |

## Inventory Tests: `test_build_inventory.py`

| Test | Verifies |
|------|----------|
| Scaffold generation from metadata | Topics, aliases, query plans populated |
| Overlay merge: scalar replace | Override canonical_label |
| Overlay merge: array append + dedupe | New alias added, duplicate ignored |
| Overlay references unknown topic | Warning, not crash |
| Denylist applied | Generic terms dropped/downranked |
| Output matches CompiledInventory schema | Schema validation |
| Version axis mismatch → loud failure | `schema_version` mismatch between inventory and overlay → non-zero exit with version pair in error |
| Overlay schema version mismatch → loud failure | `overlay_schema_version` incompatible → non-zero exit |
| Merge semantics version mismatch → loud failure | `merge_semantics_version` incompatible → non-zero exit |
| Overlay format validation | Unknown root keys warned, missing `overlay_version` → non-zero exit |
| Overlay rule unknown operation | Rule with unrecognized `operation` → warning, rule skipped |
| DenyRule `match_type: "exact"` → error | `add_deny_rule` with `match_type: "exact"` → non-zero exit (`exact` is intentionally excluded from DenyRule match_type; use `token` for whole-word denial — see [data-model.md#denyrule](data-model.md#denyrule)) |
| DenyRule drop + non-null penalty → error | `action: "drop"`, `penalty: 0.35` → non-zero exit (discriminated union violation: drop requires null penalty) |
| DenyRule downrank + null penalty → error | `action: "downrank"`, `penalty: null` → non-zero exit with "downrank requires non-null penalty" |
| DenyRule downrank + zero penalty → error | `action: "downrank"`, `penalty: 0` → non-zero exit with "downrank requires non-zero penalty" (penalty MUST be in (0.0, 1.0] per [data-model.md#denyrule](data-model.md#denyrule); zero is out of bounds) |
| `override_weight` out-of-bounds clamped | `override_weight` with `weight: 1.5` → warning, clamped to 1.0; `weight: -0.2` → warning, clamped to 0.0; compiled inventory alias has clamped value |
| `config_version` mismatch → defaults | `ccdi_config.json` with `config_version: "99"` → warning, all values use built-in defaults (same as corrupt/invalid) |
| `remove_alias` on known topic with unknown alias_text | `remove_alias` targets existing topic but non-existent alias → warning, rule skipped (no-op), topic unchanged |
| Config override unknown keys warned and skipped | Overlay `config_overrides` with `{"nonexistent.key": 0.5}` → build succeeds (exit 0), warning emitted, known keys proceed normally |
| Config override valid namespace unknown leaf | `config_overrides` with `{"classifier.nonexistent_key": 0.9}` → treated as unknown (warned and skipped), not silently applied |
| Partial config missing keys → defaults | `ccdi_config.json` present but missing one key (e.g., `packets.mid_turn_max_facts` absent) → CLI uses built-in default for that key (3), no error |
| `add_deny_rule` penalty out-of-bounds → error | `add_deny_rule` with `penalty: 1.5` → non-zero exit with penalty value and valid range (no clamping — see data-model.md penalty range enforcement) |
| Config override type mismatch → skipped | `config_overrides` with `{"classifier.confidence_high_min_weight": "0.9"}` (string instead of number) → build succeeds, warning emitted, default value used for that key |
| Scaffold-generated alias weight out-of-range → clamped | `build_inventory.py` scaffold generates alias with weight > 1.0 → clamped to 1.0 with warning; weight < 0.0 → clamped to 0.0 with warning. Per [data-model.md#alias](data-model.md#alias) weight range enforcement. |
| `add_deny_rule` penalty=1.0 boundary → accepted | `add_deny_rule` with `penalty: 1.0` → exit 0, alias weight reduced by 1.0 (effectively zeroed). Verifies the upper bound of (0.0, 1.0] is inclusive. |
| Cross-key: `initial_token_budget_min > max` → paired fallback | `ccdi_config.json` with `initial_token_budget_min: 800, initial_token_budget_max: 600` → both keys fall back to built-in defaults as a pair (600, 1000), single warning emitted. Verifies the paired-fallback rule per [data-model.md#configuration-ccdi_configjson](data-model.md#configuration-ccdi_configjson) cross-key validation. |
| Cross-key: valid min with invalid max → both fall back | `ccdi_config.json` with `initial_token_budget_min: 700, initial_token_budget_max: 600` (min > max) → both keys fall back as a pair, not independently. Verifies the "do not fall back for each key independently" constraint. |

#### `test_ccdi_hooks.py`

Tests the PostToolUse hook that triggers `build_inventory.py` on `docs_epoch` change.

| Test | Setup | Expected |
|------|-------|----------|
| Hook fires on docs_epoch change | Mock PostToolUse event with `docs_epoch` field change | `build_inventory.py` invoked with updated epoch |
| Hook skips non-epoch changes | Mock PostToolUse event without `docs_epoch` change | `build_inventory.py` not invoked |
| Hook handles build failure | Mock PostToolUse + `build_inventory.py` exits non-zero | Hook logs warning, does not block tool use |

**Runner:** pytest with subprocess fixture (same pattern as CLI integration tests). The subprocess fixture delivers the PostToolUse hook payload as JSON on stdin, matching Claude Code's hook invocation contract. The test constructs a `tool_response` JSON object with the relevant fields (including `docs_epoch` when simulating an epoch change), writes it to the subprocess's stdin, and asserts on the subprocess's exit code and stdout/stderr output.
**Phase:** A prerequisite — must pass before shadow mode activation. The hook trigger is part of the normative [inventory lifecycle](data-model.md#inventory-lifecycle) and cannot rely on manual verification alone.

## Replay Harness: `tests/test_ccdi_replay.py`

Structured replay harness for Layer 2a (CLI pipeline correctness) testing. Replays `ccdi_trace` recordings and asserts on CLI input/output and registry state transitions.

**Fixture format:** Each fixture is a JSON file containing a `turns` array (one entry per turn) plus an `assertions` object:

```json
{
  "turns": [
    {
      "turn": 1,
      "input_text": "I'm building a PreToolUse hook that validates tool inputs",
      "source": "codex",
      "semantic_hints": null,
      "search_results": {"hooks.pre_tool_use": [{"chunk_id": "hooks#pretooluse", "category": "hooks", "content": "..."}]},
      "codex_reply_error": false,
      "composed_target": null,
      "expected_classifier_result": {"resolved_topics": [...], "suppressed_candidates": [...]},
      "expected_candidates": [{"topic_key": "hooks.pre_tool_use", "facet": "schema", "confidence": "high"}]
    },
    {"turn": 2, ...}
  ],
  "assertions": {
    "cli_pipeline_sequence": ["classify", "dialogue-turn", "build-packet", "build-packet --mark-injected"],
    "final_registry_state": {"hooks.pre_tool_use": "injected"},
    "deferred_topics": [],
    "packets_injected_count": 1
  }
}
```

**Turn fields:**

| Field | Required | Purpose |
|-------|----------|---------|
| `turn` | Yes | Turn number |
| `input_text` | Yes | Raw text fed to `classify --text-file` and `dialogue-turn --text-file` |
| `source` | Yes | `"codex"` or `"user"` — passed to `dialogue-turn --source` |
| `semantic_hints` | No | JSON array for `--semantic-hints-file`, or `null` (no hints) |
| `search_results` | No | Canned results keyed by topic_key — returned by stubbed `search_docs` |
| `codex_reply_error` | No | If `true`, simulate send failure (skip commit). Default: `false` |
| `composed_target` | No | Follow-up text for target-match check. If absent, skip target-match |
| `expected_classifier_result` | No | Assertion on `classify` stdout — if present, harness verifies match |
| `expected_candidates` | No | Assertion on `dialogue-turn` stdout candidates |

**Deep registry assertions:** In addition to `final_registry_state` (flat topic→state map), fixtures include `final_registry_file_assertions` — an array of key-path assertions on the written registry JSON file. Some fixtures REQUIRE specific assertions (documented per-fixture below); the harness runner validates that required assertions are present in the fixture file before executing:

```json
{
  "final_registry_file_assertions": [
    {"path": "hooks.pre_tool_use.coverage.pending_facets", "equals": []},
    {"path": "hooks.pre_tool_use.coverage.facets_injected", "contains": ["schema"]},
    {"path": "hooks.pre_tool_use.coverage.injected_chunk_ids", "length_gte": 1}
  ]
}
```

Supported operators: `equals` (deep equality), `contains` (array membership), `length_gte` (minimum array length), `is_null`, `not_null`.

`trace_assertions` (optional): Array of per-turn assertions on `ccdi_trace` entries, including key-presence checks. E.g., `{"turn": 1, "assert_key_present": "semantic_hints"}` verifies the key exists regardless of value (supporting the null-is-valid invariant). Example in fixture:

```json
{
  "trace_assertions": [
    {"turn": 1, "assert_key_present": "semantic_hints"},
    {"turn": 2, "assert_key_present": "candidates"}
  ]
}
```

**Runner:** `uv run pytest tests/test_ccdi_replay.py` — reads all `*.replay.json` fixtures from `tests/fixtures/ccdi/`.

**Execution model:** The replay harness runs the full CLI pipeline per turn using fixture data as inputs. It does NOT re-run the agent — only the deterministic CLI commands. For each turn in the `turns` array:

1. Write `input_text` to a temp file.
2. Run `classify --text-file <temp>` via subprocess. If `expected_classifier_result` is present, assert the stdout matches.
3. Write `semantic_hints` (if non-null) to a temp file.
4. Run `dialogue-turn --registry-file <registry> --text-file <temp> --source <source> [--semantic-hints-file <hints>]`. If `expected_candidates` is present, assert stdout candidates match.
5. If candidates are non-empty AND `search_results` are provided for the candidate topic:
   - Write canned `search_results` to a temp file.
   - Run `build-packet --results-file <results> --registry-file <registry> --mode mid_turn --topic-key <candidate.topic_key> --facet <candidate.facet> --coverage-target <target>` (NO `--mark-injected` — prepare phase; `--facet` provided for ranking consistency).
   - If `composed_target` is present: run target-match check against the built packet (using topics from `<!-- ccdi-packet -->` metadata comment):
     - (a) Check whether the packet topic is a substring of `composed_target`.
     - (b) If condition (a) fails, invoke `classify --text-file <composed_target_tempfile>` and check whether any resolved topic overlaps with packet topics. This is condition (b) — see [registry.md#scheduling-rules](registry.md#scheduling-rules) step 10.
     - If both (a) and (b) fail, run `build-packet --mark-deferred <topic_key> --deferred-reason target_mismatch --skip-build --registry-file <registry>`.
6. If `codex_reply_error` is false (default) and a packet was staged:
   - Run `build-packet --results-file <results> --registry-file <registry> --mode mid_turn --topic-key <candidate.topic_key> --facet <candidate.facet> --coverage-target <target> --mark-injected` (commit phase).
7. If `codex_reply_error` is true: skip commit (topic stays `detected`).

After all turns, verify the `assertions` object against the final registry state and accumulated CLI call log.

`search_docs` and `codex-reply` are NOT invoked — search results are canned from fixture data; `codex-reply` success/failure is controlled by `codex_reply_error`. This model tests the deterministic CLI pipeline end-to-end without requiring a live Codex connection or LLM invocation.

#### `seed_medium_baseline.replay.json`

Exercises seed-build initialization of `consecutive_medium_count` across the JSON → RegistrySeed → first `dialogue-turn` boundary.

- **Initial state:** Registry file with one leaf topic in `detected` state, `consecutive_medium_count: 2` (pre-existing from prior session).
- **Classifier output:** Same topic at medium confidence.
- **Expected:** `consecutive_medium_count` increments to 3 (seed correctly preserves the counter across serialization boundary).

#### `multi_pending_facets.replay.json`

Exercises `pending_facets` array ordering across a multi-turn pipeline.

- **Initial state:** Registry with one injected topic having `pending_facets: ["schema", "config"]` (two pending facets).
- **Turn 1:** `dialogue-turn` emits `pending_facet` candidate for "schema." Agent processes it. Commit marks "schema" as resolved.
- **Turn 2:** `dialogue-turn` emits `pending_facet` candidate for "config."
- **Expected:** After Turn 1, `pending_facets: ["config"]` (FIFO order preserved). After Turn 2, `pending_facets: []`.
- **Serialization check:** Registry file written after Turn 1 must preserve array ordering when reloaded.

#### `source_equivalence.replay.json`

Exercises behavioral equivalence between `--source codex` and `--source user` invocations of `dialogue-turn`.

- **Setup:** Identical registry state and classifier output.
- **Run 1:** `dialogue-turn --source codex` — record candidates and trace.
- **Run 2:** `dialogue-turn --source user` — record candidates and trace.
- **Expected:** Identical candidate lists, identical scheduling decisions. The `--source` flag affects only trace metadata, not behavioral output.

**Scope limitation:** The replay harness verifies CLI pipeline correctness (Layer 2a). It does NOT verify that the `codex-dialogue` agent invokes CLI commands in the correct sequence — that requires a live agent invocation with mocked tools (Layer 2b). Layer 2b is a separate integration test category:

| Test | Verifies |
|------|----------|
| Agent invokes classify before dialogue-turn | Tool-call ordering in codex-dialogue |
| Agent skips build-packet when no candidates | Conditional tool invocation |
| Agent calls --mark-injected only after successful codex-reply | Prepare/commit ordering |
| Graduation gate: file absent → shadow mode | Delegation envelope with `ccdi_seed` but no `graduation.json` → agent tool-call log contains zero `build-packet --mark-injected` invocations; diagnostics show `status: "shadow"`. Per [delivery.md#shadow-mode-gate](delivery.md#shadow-mode-gate). |
| Graduation gate: status rejected → shadow mode | `graduation.json` with `status: "rejected"` → same assertions as above: zero commits, `status: "shadow"` in diagnostics. |
| Graduation gate: status approved → active mode | `graduation.json` with `status: "approved"` → agent tool-call log contains at least one `build-packet --mark-injected` invocation (when candidates exist); diagnostics show `status: "active"`. |
| Scout pipeline contains no CCDI CLI calls | In a fixture with both scout candidate and CCDI candidate active, assert that `execute_scout`/`process_turn` tool-call log contains zero `topic_inventory.py` invocations |
| Agent does not read ccdi_config.json | Assert agent tool-call log contains zero Read invocations on paths matching `*ccdi_config*` or `*topic_inventory.json` during dialogue. **Note:** This is a test-only enforcement — no runtime guard exists. The invariant relies on agent instruction compliance verified via Layer 2b test assertions. |
| Shadow mode: no injected or deferred registry mutations | Delegation envelope with `ccdi_seed`, no `graduation.json` → after dialogue, read the registry file and assert: (a) zero entries in `injected` state, (b) zero entries in `deferred` state, (c) all entries remain in `detected` or `suppressed` state only. Verifies shadow mode does not write `--mark-injected` or `--mark-deferred` to the registry. Automatic suppression (via build-packet empty-output) IS permitted — `suppressed` state reflects failed lookup, not agent commitment. |
| Shadow mode: zero `--mark-deferred` invocations | Same fixture as graduation gate shadow-mode test → additionally assert agent tool-call log contains zero `build-packet --mark-deferred` invocations. Complements the `--mark-injected` assertion. |
| Shadow mode: automatic suppression IS written | Delegation envelope with `ccdi_seed`, no `graduation.json`, fixture has a candidate with weak search results → after dialogue, assert registry file contains at least one entry in `suppressed` state with `suppression_reason: "weak_results"`. Completes the three-part shadow-mode registry invariant: injected=prohibited, deferred=prohibited, suppressed=permitted. |
| Shadow mode: `false_positive_topic_detections` key present | Shadow mode diagnostics JSON → assert `"false_positive_topic_detections" in diagnostics["ccdi"]` (key-presence check). Value verification is deferred to the labeling protocol — the automated emitter always outputs 0 by construction, so a value assertion would be trivially true. |

**Required fixture scenarios:**

| Fixture | Scenario |
|---------|----------|
| `happy_path.replay.json` | Single topic detected → searched → injected → committed. `trace_assertions` MUST include: `{"turn": <prepare_turn>, "action": "prepare"}` and `{"turn": <commit_turn>, "action": "inject"}`. |
| `scout_defers_ccdi.replay.json` | Scout target exists → CCDI candidate deferred with `scout_priority`. `trace_assertions` MUST include: `{"turn": <defer_turn>, "action": "skip_scout"}`. |
| `send_failure_no_commit.replay.json` | Packet staged but codex-reply fails → commit skipped → topic stays `detected`. `final_registry_file_assertions` MUST include: `{"path": "<topic>.consecutive_medium_count", "equals": 1}` (counter retained, not reset) and `{"path": "<topic>.state", "equals": "detected"}`. |
| `target_mismatch_deferred.replay.json` | Fixture includes `composed_target` field; packet topics absent from target → `deferred: target_mismatch`. `trace_assertions` MUST include: `{"turn": <defer_turn>, "action": "defer"}`. |
| `semantic_hint_elevation.replay.json` | Prescriptive hint on detected topic → elevated to materially new → injected |
| `hint_no_effect_already_injected.replay.json` | Prescriptive hint on already-injected topic → no additional injection, no state change |
| `hint_coverage_gap.replay.json` | `contradicts_prior` hint on injected topic → facet added to `pending_facets`, scheduled for re-injection at new facet |
| `hint_re_enters_suppressed.replay.json` | `extends_topic` hint on suppressed topic → re-enters as `detected`, scheduled for lookup. Covers `suppressed:weak_results`. A companion fixture `hint_re_enters_suppressed_redundant.replay.json` should exercise `suppressed:redundant` to verify re-entry works regardless of suppression reason. |
| `hint_re_enters_suppressed_redundant.replay.json` | `extends_topic` hint on suppressed:redundant topic → re-enters as `detected`, scheduled for lookup. Companion to `hint_re_enters_suppressed.replay.json` covering the `suppressed:redundant` suppression reason. |
| `hint_facet_expansion.replay.json` | `extends_topic` hint on injected topic → facet expansion lookup at a facet not yet in `facets_injected` |
| `hint_facet_expansion_fallback_pending.replay.json` | `extends_topic` hint on injected topic where resolved facet IS in `facets_injected` but `pending_facets` is non-empty → lookup uses `pending_facets[0]` |
| `hint_facet_expansion_fallback_default.replay.json` | `extends_topic` hint on injected topic where resolved facet and all `pending_facets` are in `facets_injected` → lookup uses `default_facet` (if not in `facets_injected`); if `default_facet` also exhausted → hint discarded |
| `empty_build_skips_target_match.replay.json` | `build-packet` returns empty output (weak search results) with `composed_target` present → registry shows `suppressed: weak_results` (NOT `deferred: target_mismatch`); CLI call log contains no `--mark-deferred` invocation |
| `hint_contradicts_prior_on_deferred.replay.json` | `contradicts_prior` hint on deferred topic → elevated to materially new, scheduled for lookup |
| `hint_extends_topic_on_deferred.replay.json` | `extends_topic` hint on deferred topic → elevated to materially new, scheduled for lookup |
| `hint_unknown_topic_ignored.replay.json` | Hint with `claim_excerpt` matching no inventory topic → hint ignored, no state change, no scheduling effect |
| `hint_contradicts_prior_on_detected.replay.json` | `contradicts_prior` hint on `detected` (non-deferred) topic → elevated to materially new, scheduled for immediate lookup |
| `cooldown_defers_second_candidate.replay.json` | Turn with two high-confidence topics (A and B) → topic A scheduled and injected, topic B transitions to `deferred: cooldown`; subsequent turn sees topic B re-evaluated. `final_registry_file_assertions` includes `{"path": "<topicA>.consecutive_medium_count", "equals": 0}` verifying reset after injection. `trace_assertions` MUST include: `{"turn": <cooldown_turn>, "action": "skip_cooldown"}` for the deferred candidate. |
| `suppressed_docs_epoch_written.replay.json` | Topic detected → searched → empty results → `suppressed: weak_results`; assert `final_registry_file_assertions` includes `{"path": "<topic>.suppressed_docs_epoch", "equals": "<fixture-inventory-docs_epoch>"}` verifying the exact epoch value is stored (not merely non-null). `trace_assertions` MUST include: `{"turn": <suppress_turn>, "action": "suppress"}`. |
| `target_match_classifier_branch.replay.json` | Packet topic absent as substring from `composed_target`, but `classify` on the composed target resolves a topic that overlaps with the packet topic → packet IS target-relevant (NOT deferred). Exercises target-match condition (b) succeeding where condition (a) fails. |
| `target_match_substring_only.replay.json` | Packet topic present as substring in `composed_target` → packet IS target-relevant via condition (a) alone. Classifier branch (b) is not needed. Isolates condition (a) as a standalone success path. |
| `target_match_both_fail.replay.json` | Packet topic absent as substring from `composed_target` AND `classify` on composed target resolves no overlapping topic → both conditions fail → `deferred: target_mismatch`. Assert: (1) `classify` was called on `composed_target` (condition (b) was reached), (2) classifier returned no overlapping topic, (3) registry shows `deferred: target_mismatch`. This fixture prevents a short-circuit implementation that skips condition (b) entirely. |
| `cache_hit_same_query.replay.json` | Turn 1 → topic A detected and injected with query Q. Turn 2 → same topic A reappears (e.g., via `extends_topic` hint at a new facet that resolves to the same query fingerprint) → assert `search_docs` invoked only once across both turns (cache hit on second). `final_registry_file_assertions` verifies `injected_chunk_ids` unchanged after cache-served build. |
| `negative_cache_prevents_retry.replay.json` | Turn 1 → topic A detected, search returns weak results (below `quality_min_result_score`) → `suppressed: weak_results`. Turn 2 → topic A re-enters as `detected` via `extends_topic` hint (NOT via docs_epoch change — a docs_epoch change would alter the cache key and guarantee a miss per [registry.md#session-local-cache](registry.md#session-local-cache)). Same query fingerprint and same `docs_epoch` → assert `search_docs` NOT re-invoked (negative cache hit); topic re-suppressed via cached weak flag. |
| `hint_prescriptive_on_suppressed.replay.json` | Topic suppressed:weak_results. Turn 2 → `prescriptive` hint resolves to suppressed topic → re-enters as `detected`, scheduled for immediate lookup. `final_registry_file_assertions`: `state: "detected"`, `suppression_reason: null`, `suppressed_docs_epoch: null`. |
| `hint_contradicts_prior_on_suppressed.replay.json` | Topic suppressed:redundant. Turn 2 → `contradicts_prior` hint resolves to suppressed topic → re-enters as `detected`, scheduled for lookup. Same field assertions as prescriptive/suppressed. |
| `suppressed_redundant_no_reentry_on_epoch_change.replay.json` | Turn 1 → topic A suppressed:redundant at docs_epoch="A". Turn 2 → inventory refreshed (docs_epoch="B"), topic A in classifier output → assert state stays `suppressed`, `suppression_reason` stays `redundant`. `docs_epoch` change triggers re-entry only for `weak_results`, not `redundant`. |
| `deferred_ttl_countdown_resets.replay.json` | Configure `deferred_ttl_turns=3`. Turn 1 → topic B deferred (TTL=3). Turns 2-3 → topic B absent (TTL decrements to 2, then 1). Turn 4 → topic B absent at TTL=0 → verify TTL resets to 3, state stays `deferred`, `last_seen_turn` unchanged. Turn 5 → topic B reappears → verify transition to `detected`. |
| `target_mismatch_then_ttl_then_cache.replay.json` | Turn 1 → weak results → suppressed. Turn 2 → re-enters via hint → searched → deferred:target_mismatch. Turn 3 → TTL expires, reappears → assert whether re-search fires (cache key includes docs_epoch) or negative cache prevents it, and assert the documented behavior. Covers the three-step interaction between suppression, deferral, and cache. |
| `both_facets_absent_suppressed.replay.json` | Topic detected with scheduled facet missing from `QueryPlan.facets` AND `default_facet` also missing → assert topic transitions to `suppressed: weak_results` (not left in `detected`). Verifies [registry.md#scheduling-rules](registry.md#scheduling-rules) step 3 double-absent transition. |
| `empty_queryspec_array_fallback.replay.json` | Topic detected with scheduled facet present in `QueryPlan.facets` but mapped to empty `QuerySpec[]` → assert fallback to `default_facet` (treated as absent). Per [registry.md#scheduling-rules](registry.md#scheduling-rules) step 3. |
| `pending_facet_exempt_from_cooldown.replay.json` | Turn with one high-confidence `new` topic A (consumes cooldown slot) AND one `pending_facet` candidate B on an already-injected topic → assert BOTH candidates are processed in the same turn (A injected, B's `pending_facet` lookup performed). Verifies the cooldown exemption in [registry.md#scheduling-rules](registry.md#scheduling-rules) step 5. `final_registry_file_assertions` MUST include assertions on both topics' post-turn state. |
| `facet_expansion_exempt_from_cooldown.replay.json` | Turn with one high-confidence `new` topic A (consumes cooldown slot) AND one `facet_expansion` candidate B from `extends_topic` hint → assert BOTH candidates are processed in the same turn. Verifies `facet_expansion` cooldown exemption. |
| `weak_results_reentry_on_epoch_change.replay.json` | Turn 1 → topic A suppressed:weak_results at docs_epoch="A". Turn 2 → inventory snapshot has docs_epoch="B" (via `--inventory-snapshot`), topic A NOT in classifier output → assert topic A re-enters as `detected` (docs_epoch scan fires independent of classifier presence). Verifies the `weak_results` full-registry scan per [integration.md#dialogue-turn-registry-side-effects](integration.md#dialogue-turn-registry-side-effects). |

### Layer 2b: Agent Sequence Tests

Tests that the `codex-dialogue` agent invokes CLI commands in the correct sequence. Requires a live agent invocation with mocked tools — cannot be tested via the replay harness.

**File location:** `tests/test_ccdi_agent_sequence.py`

**Runner:** `uv run pytest tests/test_ccdi_agent_sequence.py -v`

**Mock interface:** Tests use a tool-call interceptor that records all Bash invocations matching `topic_inventory.py *`. The test asserts on the sequence of recorded commands, their arguments, and their relative ordering. `search_docs` calls are intercepted and return canned results. `codex-reply` calls are intercepted and return success unless the fixture specifies failure.

**Execution model:** The test spawns a `codex-dialogue` agent via Claude Code's headless mode (`claude -p`) with a mock MCP server that intercepts `search_docs` and `codex-reply` tool calls and returns canned results. Bash invocations matching `topic_inventory.py *` are recorded by a wrapper script (`scripts/ccdi_cli_recorder.sh`) that logs the full command line to a temp file and delegates to the real CLI. After the agent completes (or the turn limit is reached), the test asserts that the recorded tool-call sequence matches the expected pattern.

**Interception mechanism (primary):** The mock MCP server is configured via a test-specific `.mcp.json` that replaces `claude-code-docs` with a stub server returning canned `search_docs` results from the fixture. The `codex` MCP server is similarly replaced with a stub that records `codex-reply` calls and returns success/failure per fixture. The wrapper script (`scripts/ccdi_cli_recorder.sh`) is injected via PATH to intercept CLI invocations. **Shim delegation:** The shim checks `argv[1]` — if it ends with `topic_inventory.py`, log the full command line and delegate to the real `python3`; otherwise exec the real `python3` directly (transparent passthrough). The shim MUST NOT be named `python3` — name it `ccdi_cli_recorder` and have the test script create a symlink or wrapper that routes only `topic_inventory.py` invocations through it, to avoid intercepting unrelated python3 calls.

**Interception mechanism (fallback):** If the primary mechanism is infeasible (i.e., `claude -p` does not support custom `.mcp.json` paths or PATH injection in the test environment), use a `PreToolUse` command hook as the interception layer:

1. **MCP tool interception:** Register a `PreToolUse` hook matching `mcp__claude-code-docs__search_docs` and `mcp__plugin_cross-model_codex__codex-reply`. The hook reads the expected response from a fixture file keyed by the tool input, writes the response to a temp file, and returns exit code 2 with the canned response as `additionalContext` + a block decision. This provides tool-level interception without replacing the MCP server.
2. **CLI recording:** Register a `PreToolUse` hook matching `Bash` where `tool_input.command` contains `topic_inventory.py`. The hook appends the full command line to a log file at `/tmp/ccdi_cli_log_<test_id>.txt` and allows the command to proceed (exit 0). After the agent completes, the test reads the log file and asserts on the command sequence.
3. **Fixture format:** Identical to the primary mechanism — `delegation_envelope`, `codex_responses`, `search_results`, `expected_tool_sequence`. The hook reads fixture data from a well-known path set via environment variable (`CCDI_TEST_FIXTURE_PATH`).

This fallback uses only documented Claude Code extension APIs (hooks, `additionalContext`, exit codes) and does not require PATH injection or custom `.mcp.json` paths.

**Phase A feasibility gate:** Validate the primary mechanism during Phase A implementation. If the primary mechanism works, use it (simpler, fewer moving parts). If not, implement the fallback. This gate must be resolved before Phase B (mid-dialogue CCDI), since Layer 2b coverage of prepare/commit ordering is a prerequisite for Phase B graduation. **Done when:** One mechanism is implemented and the 3 behavioral agent sequence tests (classify ordering, skip-when-no-candidates, --mark-injected-after-codex-reply) pass. Graduation gate tests (file absent, rejected, approved) are Phase B prerequisites.

**Fixture format:** Each test case provides:
- `delegation_envelope`: the envelope passed to `codex-dialogue` (with/without `ccdi_seed`)
- `codex_responses`: array of canned Codex response strings (one per turn)
- `search_results`: canned `search_docs` results per query
- `expected_tool_sequence`: ordered array of expected CLI command patterns, matched by prefix (e.g., `"classify"` matches any `classify --text-file ...` invocation; `"build-packet --mark-injected"` matches that specific flag combination)

## Known Open Items

Implementation-level items deferred from [decisions.md](decisions.md#deferred-items):

| Item | Owning component | Status |
|------|-----------------|--------|
| `ccdi_policy_snapshot` shape + boundary test | integration (delegation envelope field for pinning CCDI config during dialogue) | Undefined — define during Phase B implementation. When shape is defined, add a boundary contract test to `test_ccdi_contracts.py`. |
| Version compatibility matrix format | data-model (version axes validation) | Undefined — define when second schema version ships |
| `--source codex\|user` behavioral divergence | registry (scheduling rules) | Currently no-op — [documented in integration.md](integration.md) as identical treatment. When divergence is implemented, the CLI integration test "behavioral equivalence baseline" MUST be replaced with source-specific behavioral tests, not deleted. |

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

### Shadow Mode Kill Criteria

| Criterion | Threshold | Metric |
|-----------|-----------|--------|
| Effective prepare yield | < 40% | `(prepared AND target-relevant AND surviving precedence) / total prepared` |
| Per-turn CCDI latency | > 500ms | Average of prepare + commit per turn |
| False-positive injection rate | > 10% | CCDI fires on non-Claude-Code topics |

Secondary diagnostic (not a hard kill): `relevant_but_scout_deferred_rate` = `packets_deferred_scout / packets_prepared`. High values indicate healthy scout precedence, not CCDI failure.

Graduate from shadow to active when kill criteria are clear across 10+ shadow dialogues.

## Diagnostics

Per-dialogue summary, accumulated across turns and emitted once at dialogue end via the analytics emitter:

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
    "false_positive_topic_detections": 0
  }
}
```

In shadow mode (Phase B rollout), `packets_prepared` accumulates but `packets_injected` stays 0. The shadow diagnostics reveal what CCDI *would have* injected for kill-criteria evaluation.

Fields `packets_target_relevant`, `packets_surviving_precedence`, and `false_positive_topic_detections` are present only when `status: "shadow"`. In active mode, they are omitted. Their definitions:

- `packets_target_relevant`: count of prepared packets that passed the target-match check
- `packets_surviving_precedence`: count of target-relevant packets not deferred by scout priority
- `false_positive_topic_detections`: always 0 in the automated diagnostics emitter — the system cannot mechanically determine false positives. The actual count is produced by a human labeler during shadow evaluation (see labeling protocol below) and recorded in a separate annotation file, not in the emitted diagnostics JSON. The field is present in the schema for completeness and forward compatibility; its emitted value of 0 does NOT mean zero false positives

`effective_prepare_yield` = `packets_surviving_precedence / packets_prepared`. `false_positive_rate` = `false_positive_topic_detections / topics_detected.length`. `relevant_but_scout_deferred_rate` = `packets_deferred_scout / packets_prepared` (derived from existing schema fields; not emitted directly — compute from the two component values).

**False-positive labeling protocol:** This kill criterion requires **human review** — it is not mechanically verifiable in CI. The `false_positive_topic_detections` field in the automated diagnostics is always 0 (the emitter has no way to determine false positives). The actual false-positive count is produced through a separate annotation process:

1. During shadow evaluation, the diagnostics emitter writes `topics_detected` arrays to per-dialogue diagnostics files.
2. A human labeler reviews a minimum of 100 detected topics across 10+ dialogues. For each topic in `topics_detected`, the labeler checks whether the input text genuinely discusses a Claude Code extension concept. Topics where the input text uses extension terminology in a non-Claude-Code context (e.g., "React hook", "webpack plugin") are false positives.
3. The labeler records false-positive labels in a separate annotation file (format TBD during Phase B implementation — not part of the diagnostics emitter).
4. `false_positive_rate` = `labeled_false_positives / total_labeled_topics`. The 10% kill threshold requires statistical confidence: label at least 100 topics before evaluating.

Shadow-to-active graduation is a manual gate, not an automated CI check.

## Testing Strategy

### Three-Layer Approach

| Layer | What it tests | How |
|-------|--------------|-----|
| **Unit tests** | CLI deterministic logic ([classifier](classifier.md), [registry](registry.md), [packet builder](packets.md)) | Standard pytest, full coverage of data shapes and state transitions |
| **Replay harness (Layer 2a)** | CLI pipeline correctness ([prepare/commit](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) loop, [semantic hints](registry.md#semantic-hints), state transitions) | Structured `ccdi_trace` + assertion on CLI input/output and registry state, not prose |
| **Agent sequence tests (Layer 2b)** | Agent tool-call ordering (codex-dialogue invokes CLI commands in correct sequence) | Live agent invocation with mocked tools |
| **Shadow mode** | End-to-end quality (false positives, source hierarchy, latency) | Phase B rollout with kill criteria (see [above](#shadow-mode-kill-criteria)) |

### Debug-Gated `ccdi_trace`

The `codex-dialogue` agent emits a structured trace when CCDI is active, gated by a `ccdi_debug` flag in the delegation envelope:

```json
{
  "turn": 3,
  "classifier_result": {"resolved_topics": [...], "suppressed_candidates": [...]},
  "semantic_hints": [{"claim_index": 3, "hint_type": "prescriptive", "claim_excerpt": "you should use updatedInput to modify..."}],
  "candidates": ["hooks.post_tool_use"],
  "action": "prepare",
  "packet_staged": true,
  "scout_conflict": false,
  "commit": true
}
```

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
| Consecutive-turn medium threshold | Medium topic on turn 1 → no injection; same topic on turn 2 → injection fires; counter resets if topic changes |
| Consecutive-medium reset on topic absence | Medium topic turn 1 (count=1), topic absent from classifier output turn 2 (count reset to 0), medium topic turn 3 (count=1) → injection does NOT fire on turn 3 (threshold requires 2 consecutive turns, absence breaks the streak) |
| Family injection doesn't cover leaves | Inject hooks → hooks.post_tool_use still detected |
| Leaf inherits family_context_available | Flag set after family injected |
| Leaf then family tracked independently | Both have separate coverage |
| Facet evolution | overview injected, schema still pending → new lookup |
| Idempotent mark-injected | Same packet twice doesn't corrupt |
| No commit without send | build-packet without --mark-injected leaves topic in detected |
| Send failure reverts to detected | When send fails and --mark-injected is skipped, topic remains `detected` (agent-level flow) |
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

### CLI Integration Tests

| Test | Verifies |
|------|----------|
| `classify` file I/O round-trip | Reads text file, returns valid JSON |
| `dialogue-turn` updates registry file | State persistence across calls |
| `build-packet --mark-injected` updates registry | Side-effect correctness |
| `dialogue-turn --source codex` vs `--source user` | Both accepted, same pipeline, no crash. Additionally: same input text + same registry state → `--source codex` and `--source user` produce identical stdout candidates JSON and identical registry mutations (behavioral equivalence baseline for future divergence). |
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
| Prepare/commit packet idempotency | Run `build-packet` (prepare, no `--mark-injected`) then `build-packet --mark-injected` with same `--results-file` → stdout markdown from commit matches stdout from prepare |

## Boundary Contract Tests: `test_ccdi_contracts.py`

Tests that verify field names, enum values, and schema shapes agree across component boundaries. Guards against silent downgrade.

| Boundary | Contract verified |
|----------|-------------------|
| Inventory → classifier | `topic_key`, `family_key`, alias normalization, denylist shapes |
| Classifier → registry | `confidence`, `facet`, `coverage_target` (flows through candidates JSON), `topic_key` enums |
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
| RegistrySeed ↔ TopicRegistryEntry durable fields | Every durable field in TopicRegistryEntry (all except attempt-local states `looked_up`, `built`) is present in RegistrySeed.entries field enumeration — schema-comparison test |
| RegistrySeed ↔ ClassifierResult coverage_target | `RegistrySeed.entries[].coverage_target` matches `ClassifierResult.resolved_topics[].coverage_target` enum (`"family" \| "leaf"`) — cross-schema consistency test |

## Integration Tests

| Test | Verifies |
|------|----------|
| ccdi-gatherer produces valid markdown | End-to-end initial injection |
| `/codex` CCDI-lite briefing injection | Briefing contains `### Claude Code Extension Reference` |
| Full dialogue turn with mid-turn injection | Registry persists across turns |
| Graceful degradation without `search_docs` | Consultation proceeds, `ccdi_status: unavailable` |
| Malformed search results handled | Missing `chunk_id`, empty content → skip, not crash |
| Inventory schema version mismatch | Older inventory → warning, not crash |
| Inventory stale (`docs_epoch` mismatch) | Load `topic_inventory.json` with `docs_epoch` differing from active `claude-code-docs` server's epoch → diagnostics warning emitted, CCDI continues (non-blocking) |
| `ccdi_debug` gating of trace emission | With `ccdi_debug=true` → `ccdi_trace` key present in agent output AND each trace entry contains all required fields (`turn`, `classifier_result`, `semantic_hints`, `candidates`, `action`, `packet_staged`, `scout_conflict`, `commit`). `classifier_result` must contain `resolved_topics` and `suppressed_candidates` sub-fields per the [ClassifierResult contract](classifier.md#output-structure). `semantic_hints` is always present as a field: `null` when no hints were provided for the turn, a non-empty array when hints exist. Field-absent is NOT valid — always include the key with a null or array value. With `ccdi_debug` absent → no `ccdi_trace` key. |
| `ccdi_trace` semantic_hints conditional presence | Multi-turn trace: turn 1 has no hints → `ccdi_trace[0].semantic_hints == null` (field present, value null); turn 2 has hints → `ccdi_trace[1].semantic_hints` is a non-empty array. Assert field is always present (never absent from the trace entry). |
| Sentinel extraction from ccdi-gatherer | Valid sentinel block (matching open/close tags, valid JSON between) → `ccdi_seed` path present in delegation envelope and file contains valid RegistrySeed JSON |
| Malformed sentinel handling | Missing closing sentinel tag or invalid JSON between sentinels → `/dialogue` proceeds without `ccdi_seed` (graceful degradation to `initial_only` phase) |
| ccdi-gatherer returns no sentinel | No sentinel block in ccdi-gatherer output → no `ccdi_seed` field in delegation envelope, `phase: initial_only` in diagnostics |
| Initial CCDI commit skip on briefing-send failure | Briefing send fails → seed entries remain in `detected` state (verify registry file contains `state: "detected"` for all entries, not `state: "injected"`) |
| Temp file identity per turn | Verify `<id>` in `/tmp/ccdi_*_<id>.*` paths is unique per turn (not per dialogue), preventing cross-turn file collisions in the prepare/commit protocol |

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
| DenyRule drop + non-null penalty → error | `action: "drop"`, `penalty: 0.35` → non-zero exit (discriminated union violation: drop requires null penalty) |
| DenyRule downrank + null penalty → error | `action: "downrank"`, `penalty: null` → non-zero exit with "downrank requires non-null penalty" |
| DenyRule downrank + zero penalty → warning | `action: "downrank"`, `penalty: 0` → warning "zero penalty is a no-op" |
| `override_weight` out-of-bounds clamped | `override_weight` with `weight: 1.5` → warning, clamped to 1.0; `weight: -0.2` → warning, clamped to 0.0; compiled inventory alias has clamped value |
| `config_version` mismatch → defaults | `ccdi_config.json` with `config_version: "99"` → warning, all values use built-in defaults (same as corrupt/invalid) |
| `remove_alias` on known topic with unknown alias_text | `remove_alias` targets existing topic but non-existent alias → warning, rule skipped (no-op), topic unchanged |
| Config override unknown keys warned and skipped | Overlay `config_overrides` with `{"nonexistent.key": 0.5}` → build succeeds (exit 0), warning emitted, known keys proceed normally |
| Config override valid namespace unknown leaf | `config_overrides` with `{"classifier.nonexistent_key": 0.9}` → treated as unknown (warned and skipped), not silently applied |
| Partial config missing keys → defaults | `ccdi_config.json` present but missing one key (e.g., `packets.mid_turn_max_facts` absent) → CLI uses built-in default for that key (3), no error |
| `add_deny_rule` penalty out-of-bounds → error | `add_deny_rule` with `penalty: 1.5` → non-zero exit with penalty value and valid range (no clamping — see data-model.md penalty range enforcement) |
| Config override type mismatch → skipped | `config_overrides` with `{"classifier.confidence_high_min_weight": "0.9"}` (string instead of number) → build succeeds, warning emitted, default value used for that key |

**Known untested invariant:** The post-reload hook that triggers `build_inventory.py` when `docs_epoch` changes is a hook configuration, not a CLI behavior. It is not covered by `test_build_inventory.py` unit tests. Verification requires a hook integration test or manual smoke test confirming that `reload_docs` → epoch change → `build_inventory.py` invocation occurs.

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

**Deep registry assertions:** In addition to `final_registry_state` (flat topic→state map), fixtures may include `final_registry_file_assertions` — an array of key-path assertions on the written registry JSON file:

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

**Runner:** `uv run pytest tests/test_ccdi_replay.py` — reads all `*.replay.json` fixtures from `tests/fixtures/ccdi/`.

**Execution model:** The replay harness runs the full CLI pipeline per turn using fixture data as inputs. It does NOT re-run the agent — only the deterministic CLI commands. For each turn in the `turns` array:

1. Write `input_text` to a temp file.
2. Run `classify --text-file <temp>` via subprocess. If `expected_classifier_result` is present, assert the stdout matches.
3. Write `semantic_hints` (if non-null) to a temp file.
4. Run `dialogue-turn --registry-file <registry> --text-file <temp> --source <source> [--semantic-hints-file <hints>]`. If `expected_candidates` is present, assert stdout candidates match.
5. If candidates are non-empty AND `search_results` are provided for the candidate topic:
   - Write canned `search_results` to a temp file.
   - Run `build-packet --results-file <results> --registry-file <registry> --mode mid_turn --coverage-target <target>` (NO `--mark-injected` — prepare phase).
   - If `composed_target` is present: run target-match check against the built packet.
6. If `codex_reply_error` is false (default) and a packet was staged:
   - Run `build-packet --results-file <results> --registry-file <registry> --mode mid_turn --coverage-target <target> --mark-injected` (commit phase).
7. If `codex_reply_error` is true: skip commit (topic stays `detected`).

After all turns, verify the `assertions` object against the final registry state and accumulated CLI call log.

`search_docs` and `codex-reply` are NOT invoked — search results are canned from fixture data; `codex-reply` success/failure is controlled by `codex_reply_error`. This model tests the deterministic CLI pipeline end-to-end without requiring a live Codex connection or LLM invocation.

**Scope limitation:** The replay harness verifies CLI pipeline correctness (Layer 2a). It does NOT verify that the `codex-dialogue` agent invokes CLI commands in the correct sequence — that requires a live agent invocation with mocked tools (Layer 2b). Layer 2b is a separate integration test category:

| Test | Verifies |
|------|----------|
| Agent invokes classify before dialogue-turn | Tool-call ordering in codex-dialogue |
| Agent skips build-packet when no candidates | Conditional tool invocation |
| Agent calls --mark-injected only after successful codex-reply | Prepare/commit ordering |

**Required fixture scenarios:**

| Fixture | Scenario |
|---------|----------|
| `happy_path.replay.json` | Single topic detected → searched → injected → committed |
| `scout_defers_ccdi.replay.json` | Scout target exists → CCDI candidate deferred with `scout_priority` |
| `send_failure_no_commit.replay.json` | Packet staged but codex-reply fails → commit skipped → topic stays `detected` |
| `target_mismatch_deferred.replay.json` | Fixture includes `composed_target` field; packet topics absent from target → `deferred: target_mismatch` |
| `semantic_hint_elevation.replay.json` | Prescriptive hint on detected topic → elevated to materially new → injected |
| `hint_no_effect_already_injected.replay.json` | Prescriptive hint on already-injected topic → no additional injection, no state change |
| `hint_coverage_gap.replay.json` | `contradicts_prior` hint on injected topic → facet added to `pending_facets`, scheduled for re-injection at new facet |
| `hint_re_enters_suppressed.replay.json` | `extends_topic` hint on suppressed topic → re-enters as `detected`, scheduled for lookup |
| `hint_facet_expansion.replay.json` | `extends_topic` hint on injected topic → facet expansion lookup at a facet not yet in `facets_injected` |
| `hint_facet_expansion_fallback_pending.replay.json` | `extends_topic` hint on injected topic where resolved facet IS in `facets_injected` but `pending_facets` is non-empty → lookup uses `pending_facets[0]` |
| `hint_facet_expansion_fallback_default.replay.json` | `extends_topic` hint on injected topic where resolved facet and all `pending_facets` are in `facets_injected` → lookup uses `default_facet` (if not in `facets_injected`); if `default_facet` also exhausted → hint discarded |
| `empty_build_skips_target_match.replay.json` | `build-packet` returns empty output (weak search results) with `composed_target` present → registry shows `suppressed: weak_results` (NOT `deferred: target_mismatch`); CLI call log contains no `--mark-deferred` invocation |
| `hint_contradicts_prior_on_deferred.replay.json` | `contradicts_prior` hint on deferred topic → elevated to materially new, scheduled for lookup |
| `hint_extends_topic_on_deferred.replay.json` | `extends_topic` hint on deferred topic → elevated to materially new, scheduled for lookup |
| `hint_unknown_topic_ignored.replay.json` | Hint with `claim_excerpt` matching no inventory topic → hint ignored, no state change, no scheduling effect |
| `hint_contradicts_prior_on_detected.replay.json` | `contradicts_prior` hint on `detected` (non-deferred) topic → elevated to materially new, scheduled for immediate lookup |
| `cooldown_defers_second_candidate.replay.json` | Turn with two high-confidence topics (A and B) → topic A scheduled and injected, topic B transitions to `deferred: cooldown`; subsequent turn sees topic B re-evaluated. `final_registry_file_assertions` includes `{"path": "<topicA>.consecutive_medium_count", "equals": 0}` verifying reset after injection. |
| `suppressed_docs_epoch_written.replay.json` | Topic detected → searched → empty results → `suppressed: weak_results`; assert `final_registry_file_assertions` includes `{"path": "<topic>.suppressed_docs_epoch", "equals": "<fixture-inventory-docs_epoch>"}` verifying the exact epoch value is stored (not merely non-null) |
| `target_match_classifier_branch.replay.json` | Packet topic absent as substring from `composed_target`, but `classify` on the composed target resolves a topic that overlaps with the packet topic → packet IS target-relevant (NOT deferred). Exercises target-match condition (b) succeeding where condition (a) fails. |
| `target_match_substring_only.replay.json` | Packet topic present as substring in `composed_target` → packet IS target-relevant via condition (a) alone. Classifier branch (b) is not needed. Isolates condition (a) as a standalone success path. |

### Layer 2b: Agent Sequence Tests

Tests that the `codex-dialogue` agent invokes CLI commands in the correct sequence. Requires a live agent invocation with mocked tools — cannot be tested via the replay harness.

**File location:** `tests/test_ccdi_agent_sequence.py`

**Runner:** `uv run pytest tests/test_ccdi_agent_sequence.py -v`

**Mock interface:** Tests use a tool-call interceptor that records all Bash invocations matching `topic_inventory.py *`. The test asserts on the sequence of recorded commands, their arguments, and their relative ordering. `search_docs` calls are intercepted and return canned results. `codex-reply` calls are intercepted and return success unless the fixture specifies failure.

**Execution model:** The test spawns a `codex-dialogue` agent via Claude Code's headless mode (`claude -p`) with a mock MCP server that intercepts `search_docs` and `codex-reply` tool calls and returns canned results. Bash invocations matching `topic_inventory.py *` are recorded by a wrapper script that logs the command and delegates to the real CLI. After the agent completes (or the turn limit is reached), the test asserts that the recorded tool-call sequence matches the expected pattern. **Implementation note:** The exact interception mechanism (mock MCP server, wrapper script, or SDK-level hook) is an implementation decision — the spec constrains only the fixture format and assertion semantics, not the test harness internals.

**Fixture format:** Each test case provides:
- `delegation_envelope`: the envelope passed to `codex-dialogue` (with/without `ccdi_seed`)
- `codex_responses`: array of canned Codex response strings (one per turn)
- `search_results`: canned `search_docs` results per query
- `expected_tool_sequence`: ordered array of expected CLI command patterns, matched by prefix (e.g., `"classify"` matches any `classify --text-file ...` invocation; `"build-packet --mark-injected"` matches that specific flag combination)

## Known Open Items

Implementation-level items deferred from [decisions.md](decisions.md#deferred-items):

| Item | Owning component | Status |
|------|-----------------|--------|
| `ccdi_policy_snapshot` shape | integration (delegation envelope field for pinning CCDI config during dialogue) | Undefined — define during Phase B implementation |
| Version compatibility matrix format | data-model (version axes validation) | Undefined — define when second schema version ships |
| `--source codex\|user` behavioral divergence | registry (scheduling rules) | Currently no-op — [documented in integration.md](integration.md) as identical treatment |

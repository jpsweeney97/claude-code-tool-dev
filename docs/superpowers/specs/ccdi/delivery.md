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

Secondary diagnostic (not a hard kill): `relevant_but_scout_deferred_rate` — high values indicate healthy scout precedence, not CCDI failure.

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
    "config_source": "data/ccdi_config.json | defaults"
  }
}
```

In shadow mode (Phase B rollout), `packets_prepared` accumulates but `packets_injected` stays 0. The shadow diagnostics reveal what CCDI *would have* injected for kill-criteria evaluation.

Additional fields for shadow mode kill criteria computation:

- `packets_target_relevant`: count of prepared packets that passed the target-match check
- `packets_surviving_precedence`: count of target-relevant packets not deferred by scout priority
- `false_positive_topic_detections`: count of topics classified as high/medium confidence that were not Claude Code extension topics (requires manual labeling during shadow evaluation)

`effective_prepare_yield` = `packets_surviving_precedence / packets_prepared`. `false_positive_rate` = `false_positive_topic_detections / topics_detected.length`.

## Testing Strategy

### Three-Layer Approach

| Layer | What it tests | How |
|-------|--------------|-----|
| **Unit tests** | CLI deterministic logic ([classifier](classifier.md), [registry](registry.md), [packet builder](packets.md)) | Standard pytest, full coverage of data shapes and state transitions |
| **Replay harness** | Agent integration ([prepare/commit](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) loop, [semantic hints](registry.md#semantic-hints), tool-call sequence) | Structured `ccdi_trace` + assertion on tool-call sequence and outcomes, not prose |
| **Shadow mode** | End-to-end quality (false positives, source hierarchy, latency) | Phase B rollout with kill criteria (see [above](#shadow-mode-kill-criteria)) |

### Debug-Gated `ccdi_trace`

The `codex-dialogue` agent emits a structured trace when CCDI is active, gated by a `ccdi_debug` flag in the delegation envelope:

```json
{
  "turn": 3,
  "classifier_result": {"resolved_topics": [...], "suppressed": [...]},
  "semantic_hints": [{"claim_index": 3, "hint_type": "prescriptive", "claim_excerpt": "you should use updatedInput to modify..."}],
  "candidates": ["hooks.post_tool_use"],
  "action": "prepare",
  "packet_staged": true,
  "scout_conflict": false,
  "commit": true
}
```

The replay harness collects these traces and asserts on:

- **Tool-call sequence:** classify → dialogue-turn → search_docs → build-packet (prepare) → codex-reply → build-packet --mark-injected (commit)
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

### Registry Tests

| Test | Verifies |
|------|----------|
| New topic → detected | First appearance starts in detected |
| Happy path: detected → [looked_up] → [built] → injected | Full forward transition with commit |
| Attempt states not persisted | looked_up and built absent from written registry file |
| Candidate selection after detection | Detected topic in candidates |
| Injected not re-selected | After mark-injected → not in candidates |
| Suppressed: weak results | [looked_up] → suppressed on empty search |
| Suppressed: redundant | [looked_up] → suppressed when coverage exists |
| Suppressed re-enters on stronger signal | suppressed → detected |
| Deferred: cooldown | Candidate deferred when cooldown active |
| Deferred: scout priority | Candidate deferred when scout target exists |
| Deferred: target mismatch | Staged packet fails target-match check → `deferred: target_mismatch` via `--mark-deferred` |
| Deferred TTL initialization | TTL set to `deferred_ttl_turns` config value at deferral time |
| Deferred TTL decrement per turn | TTL decrements by 1 on each `dialogue-turn` call regardless of classifier output |
| Deferred TTL expiry + reappearance | TTL=0 AND topic in classifier output → `detected` |
| Deferred TTL expiry without reappearance | TTL=0 but topic absent from classifier → TTL reset, stays `deferred` |
| Deferred vs suppressed distinction | Different reasons, different re-entry paths |
| Suppressed re-entry: weak_results | `docs_epoch` change → suppressed topic re-enters as `detected` |
| Suppressed re-entry: redundant | Coverage state change → suppressed topic re-enters as `detected` |
| Cooldown configurable | Reads from ccdi_config.json |
| Consecutive-turn medium threshold | Medium topic on turn 1 → no injection; same topic on turn 2 → injection fires; counter resets if topic changes |
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

### CLI Integration Tests

| Test | Verifies |
|------|----------|
| `classify` file I/O round-trip | Reads text file, returns valid JSON |
| `dialogue-turn` updates registry file | State persistence across calls |
| `build-packet --mark-injected` updates registry | Side-effect correctness |
| `dialogue-turn --source codex` vs `--source user` | Both accepted, same pipeline, no crash |
| `build-packet` empty output writes suppressed | Empty result + registry → `suppressed: weak_results` in registry |
| `build-packet --mark-deferred` writes deferred state | Deferred topic_key and reason persisted to registry |
| Missing inventory → non-zero exit | Graceful failure |
| Malformed text → non-zero exit | Input validation |
| stdout/stderr separation | JSON on stdout only, errors on stderr |

## Boundary Contract Tests: `test_ccdi_contracts.py`

Tests that verify field names, enum values, and schema shapes agree across component boundaries. Guards against silent downgrade.

| Boundary | Contract verified |
|----------|-------------------|
| Inventory → classifier | `topic_key`, `family_key`, alias normalization, denylist shapes |
| Classifier → registry | `confidence`, `facet`, `coverage_target`, `topic_key` enums |
| Registry → search orchestration | Candidates produce valid query specs and category hints |
| Search results → packet builder | Required fields present (`chunk_id`, `category`, `content`), deduplication, ranking stability |
| Packet builder → prompt assembler | Citation format, valid markdown, token budget enforced |
| CLI → agents | Exit codes, stdout JSON contract, stderr behavior, file-path semantics |
| Semantic hints → CLI | `claim_index`, `hint_type` enum values, `claim_excerpt` length cap, classifier resolution of excerpt |
| `dump_index_metadata` → `build_inventory.py` | Response shape matches expected fields (`index_version`, `categories[].chunks[].chunk_id`, etc.) — cross-package contract |
| Config → CLI | `ccdi_config.json` schema validated at load; unknown keys warned, missing keys use defaults |
| Registry seed → delegation envelope | `ccdi_seed` file path valid, seed JSON parses to expected schema |
| Version axes → overlay merge | `schema_version`, `overlay_schema_version`, `merge_semantics_version` compatibility validated at build time |

## Integration Tests

| Test | Verifies |
|------|----------|
| ccdi-gatherer produces valid markdown | End-to-end initial injection |
| `/codex` CCDI-lite briefing injection | Briefing contains `### Claude Code Extension Reference` |
| Full dialogue turn with mid-turn injection | Registry persists across turns |
| Graceful degradation without `search_docs` | Consultation proceeds, `ccdi_status: unavailable` |
| Malformed search results handled | Missing `chunk_id`, empty content → skip, not crash |
| Inventory schema version mismatch | Older inventory → warning, not crash |

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

## Replay Harness: `tests/test_ccdi_replay.py`

Structured replay harness for Layer 2 (agent integration) testing. Replays `ccdi_trace` recordings and asserts on tool-call sequence and state transitions.

**Fixture format:** Each fixture is a JSON file containing a `ccdi_trace` array (one entry per turn) plus an `assertions` object:

```json
{
  "trace": [
    {"turn": 1, "classifier_result": {...}, "candidates": [...], "action": "prepare", ...},
    {"turn": 2, ...}
  ],
  "assertions": {
    "tool_call_sequence": ["classify", "dialogue-turn", "search_docs", "build-packet", "codex-reply", "build-packet --mark-injected"],
    "final_registry_state": {"hooks.pre_tool_use": "injected"},
    "deferred_topics": [],
    "packets_injected_count": 1
  }
}
```

**Runner:** `uv run pytest tests/test_ccdi_replay.py` — reads all `*.replay.json` fixtures from `tests/fixtures/ccdi/`.

**Required fixture scenarios:**

| Fixture | Scenario |
|---------|----------|
| `happy_path.replay.json` | Single topic detected → searched → injected → committed |
| `scout_defers_ccdi.replay.json` | Scout target exists → CCDI candidate deferred with `scout_priority` |
| `send_failure_no_commit.replay.json` | Packet staged but codex-reply fails → commit skipped → topic stays `detected` |
| `target_mismatch_deferred.replay.json` | Packet built but fails target-match → `deferred: target_mismatch` via `--mark-deferred` |
| `semantic_hint_elevation.replay.json` | Prescriptive hint on detected topic → elevated to materially new → injected |

## Known Open Items

Implementation-level items deferred from [decisions.md](decisions.md#deferred-items):

| Item | Owning component | Status |
|------|-----------------|--------|
| `ccdi_policy_snapshot` shape | integration (delegation envelope field for pinning CCDI config during dialogue) | Undefined — define during Phase B implementation |
| Version compatibility matrix format | data-model (version axes validation) | Undefined — define when second schema version ships |
| `--source codex\|user` behavioral divergence | registry (scheduling rules) | Currently no-op — [documented in integration.md](integration.md) as identical treatment |

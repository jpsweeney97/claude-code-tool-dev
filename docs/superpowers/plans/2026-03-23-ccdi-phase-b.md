# CCDI Phase B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build CCDI Phase B — mid-dialogue per-turn detection and injection of Claude Code extension documentation into Codex consultations, with shadow mode rollout, graduation protocol, and comprehensive test infrastructure (replay harness + Layer 2b agent sequence tests).

**Architecture:** Phase B extends the Phase A CLI (`topic_inventory.py`) with a `dialogue-turn` subcommand that runs the full scheduling pipeline each turn: classify → diff against registry → process semantic hints → TTL lifecycle → suppression re-entry scan → schedule candidates → apply cooldown → emit candidates JSON. The `codex-dialogue` agent drives a prepare/commit loop using `dialogue-turn` + `build-packet` per turn. Shadow mode runs the full pipeline but withholds packet delivery. A replay harness (Layer 2a) tests the deterministic CLI pipeline via 52 fixture scenarios. Layer 2b tests verify agent tool-call sequencing.

**Tech Stack:** Python 3.11+ (CLI, scheduling, diagnostics, caching), pytest (all test layers), JSON fixtures (replay harness)

**Spec:** `docs/superpowers/specs/ccdi/` — 10 files, 8 normative authorities. Key Phase B authorities: `registry.md` (state machine, scheduling, hints, TTL, cache), `integration.md` (dialogue-turn CLI, shadow mode gate, ccdi_trace), `delivery.md` (replay harness, Layer 2b, graduation, diagnostics).

**Phase A foundation:** All paths relative to `packages/plugins/cross-model/` unless stated otherwise. Phase A code is on `main` at commit `f08554f`. Phase A modules: `scripts/ccdi/{types,config,classifier,packets,registry,inventory}.py`, `scripts/topic_inventory.py`, `scripts/ccdi/build_inventory.py`.

---

## Scope

**Phase B includes:**
- `dialogue-turn` CLI subcommand (full scheduling pipeline, 10 steps)
- Extended `build-packet` flags: `--mark-deferred`, `--skip-build`, `--shadow-mode`
- Registry state machine extensions: deferred states (cooldown, scout_priority, target_mismatch), TTL lifecycle, semantic hints processing, consecutive-medium tracking for leaves, session-local cache
- `classify_result_hash` computation
- Diagnostics emitter (active/shadow/unavailable schemas)
- `validate_graduation.py` CLI tool
- Shadow mode gate in `codex-dialogue` agent
- Mid-dialogue CCDI loop in `codex-dialogue` agent (Steps 5.5 and 7.5)
- `ccdi_trace` output contract
- Replay harness (`test_ccdi_replay.py`) with 52 fixture scenarios
- Layer 2b agent sequence tests (feasibility gate + behavioral tests)
- Freshness guardrail tests
- Phase B boundary contract and integration tests

**Phase B does NOT include:**
- Changes to CCDI-lite (`/codex` skill) — Phase A only
- Changes to `ccdi-gatherer` agent — Phase A only
- Changes to `dump_index_metadata` TypeScript tool — Phase A only
- `build_inventory.py` MCP client wiring — deferred
- `ccdi_policy_snapshot` delegation envelope field — deferred (shape undefined)
- `--source codex|user` behavioral divergence — deferred (currently no-op)

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `scripts/ccdi/dialogue_turn.py` | `dialogue-turn` scheduling pipeline: classify integration, registry mutations, hint processing, TTL lifecycle, suppression re-entry scan, candidate emission, cooldown enforcement, shadow-mode behavior |
| `scripts/ccdi/cache.py` | Session-local cache: result cache, packet cache, negative cache. Keyed by normalized fingerprint (includes docs_epoch) |
| `scripts/ccdi/diagnostics.py` | Diagnostics emitter: active/shadow/unavailable schemas, field presence rules, per-turn latency tracking |
| `scripts/ccdi/hash_utils.py` | `classify_result_hash()`: deterministic hash of ClassifierResult per-topic (includes confidence, facet, matched_aliases) |
| `scripts/validate_graduation.py` | Graduation validator CLI: 3 required flags, 7 consistency checks, exit codes 0/1 |
| `tests/test_ccdi_dialogue_turn.py` | dialogue-turn unit tests: scheduling, hints, TTL, cooldown, consecutive-medium |
| `tests/test_ccdi_cache.py` | Session-local cache tests |
| `tests/test_ccdi_diagnostics.py` | Diagnostics emitter tests (4 tests from delivery.md) |
| `tests/test_validate_graduation.py` | Graduation validator tests (17 tests from delivery.md) |
| `tests/test_ccdi_replay.py` | Replay harness runner + assertion engine |
| `tests/test_shadow_freshness_guardrail.py` | Freshness guardrail integration tests |
| `tests/test_ccdi_agent_sequence.py` | Layer 2b agent sequence tests |
| `tests/fixtures/ccdi/*.replay.json` | 52 replay fixture files (see delivery.md for complete list) |
| `data/ccdi_shadow/` | Directory for graduation.json, diagnostics/, annotations.jsonl |

### Modified Files

| File | Change |
|------|--------|
| `scripts/ccdi/types.py` | Add `SemanticHint`, `InjectionCandidate`, `DiagnosticsRecord`, `ShadowDeferIntent` dataclasses |
| `scripts/ccdi/classifier.py` | No changes (hash computation lives in `hash_utils.py`) |
| `scripts/ccdi/registry.py` | Add `write_deferred()`, extend `load_registry()` with TTL load-time recovery, add `process_suppression_reentry_scan()` |
| `scripts/topic_inventory.py` | Add `dialogue-turn` subcommand, extend `build-packet` with `--mark-deferred`, `--skip-build`, `--shadow-mode` flags |
| `agents/codex-dialogue.md` | Add shadow mode gate, mid-dialogue CCDI loop (Steps 5.5/7.5), `ccdi_trace` emission, semantic hints extraction |
| `tests/test_ccdi_registry.py` | Add ~45 Phase B registry unit tests (deferred, TTL, hints, consecutive-medium, cache, facet_expansion, pending_facet) |
| `tests/test_ccdi_cli.py` | Add ~18 Phase B CLI integration tests (dialogue-turn, --mark-deferred, --skip-build, --shadow-mode, source equivalence, agent gate) |
| `tests/test_ccdi_contracts.py` | Add Phase B boundary tests (candidate_type enum, semantic hints schema, graduation status enum, shadow mode invariants) |
| `tests/test_ccdi_integration.py` | Add Phase B integration tests (shadow diagnostics, active diagnostics absence, inventory pinning, ccdi_debug gating) |

---

## Task 1: Phase B Foundation Types

**Files:**
- Modify: `scripts/ccdi/types.py`
- Create: `scripts/ccdi/hash_utils.py`
- Test: `tests/test_ccdi_types.py` (extend), `tests/test_ccdi_classifier.py` (extend)

**Spec references:** `registry.md#semantic-hints`, `integration.md#dialogue-turn-candidates-json-schema`, `delivery.md#diagnostics`, `delivery.md#shadow-mode-denominator-normalization`

- [ ] **Step 1: Write tests for new types in test_ccdi_types.py**

Add tests for: `SemanticHint` construction and validation (`hint_type` enum, `claim_excerpt` ≤100 chars), `InjectionCandidate` construction (all 7 fields including `candidate_type` enum), `DiagnosticsRecord` active vs shadow field presence, `ShadowDeferIntent` fields, `shadow_adjusted_yield` computation (`test_shadow_adjusted_yield_present_in_shadow_diagnostics`: shadow DiagnosticsRecord serialization includes `shadow_adjusted_yield` key; `test_shadow_adjusted_yield_absent_in_active_diagnostics`: active mode omits it).

- [ ] **Step 2: Run tests — expect ImportError**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_types.py -k "semantic_hint or injection_candidate or diagnostics_record or shadow_defer" -v`
Expected: FAIL (types not defined yet)

- [ ] **Step 3: Implement new types in types.py**

```python
@dataclass(frozen=True)
class SemanticHint:
    claim_index: int
    hint_type: str  # "prescriptive" | "contradicts_prior" | "extends_topic"
    claim_excerpt: str

    def __post_init__(self) -> None:
        valid_types = {"prescriptive", "contradicts_prior", "extends_topic"}
        if self.hint_type not in valid_types:
            raise ValueError(f"Invalid hint_type: {self.hint_type!r}. Must be one of {valid_types}")
        if len(self.claim_excerpt) > 100:
            raise ValueError(f"claim_excerpt exceeds 100 chars: {len(self.claim_excerpt)}")


@dataclass(frozen=True)
class InjectionCandidate:
    topic_key: str
    family_key: str
    facet: str
    confidence: str | None  # null for facet_expansion and pending_facet
    coverage_target: str  # "family" | "leaf"
    candidate_type: str  # "new" | "facet_expansion" | "pending_facet"
    query_plan: QueryPlan


@dataclass
class DiagnosticsRecord:
    status: str  # "active" | "shadow" | "unavailable"
    phase: str  # "initial_only" | "full"
    topics_detected: list[str]
    topics_injected: list[str]
    topics_deferred: list[str]
    topics_suppressed: list[str]
    packets_prepared: int
    packets_injected: int
    packets_deferred_scout: int
    total_tokens_injected: int
    semantic_hints_received: int
    search_failures: int
    inventory_epoch: str | None
    config_source: str
    per_turn_latency_ms: list[int]
    # Shadow-only fields (present only when status == "shadow")
    packets_target_relevant: int | None = None
    packets_surviving_precedence: int | None = None
    false_positive_topic_detections: int | None = None

    def to_dict(self) -> dict:
        """Serialize to dict. Shadow-only fields omitted when status != 'shadow'."""
        d: dict = {
            "status": self.status,
            "phase": self.phase,
        }
        if self.status == "unavailable":
            return d
        d.update({
            "topics_detected": self.topics_detected,
            "topics_injected": self.topics_injected,
            "topics_deferred": self.topics_deferred,
            "topics_suppressed": self.topics_suppressed,
            "packets_prepared": self.packets_prepared,
            "packets_injected": self.packets_injected,
            "packets_deferred_scout": self.packets_deferred_scout,
            "total_tokens_injected": self.total_tokens_injected,
            "semantic_hints_received": self.semantic_hints_received,
            "search_failures": self.search_failures,
            "inventory_epoch": self.inventory_epoch,
            "config_source": self.config_source,
            "per_turn_latency_ms": self.per_turn_latency_ms,
        })
        if self.status == "shadow":
            d["packets_target_relevant"] = self.packets_target_relevant or 0
            d["packets_surviving_precedence"] = self.packets_surviving_precedence or 0
            d["false_positive_topic_detections"] = 0  # Always 0 per spec
        return d


@dataclass(frozen=True)
class ShadowDeferIntent:
    turn: int
    topic_key: str
    reason: str  # "target_mismatch" | "cooldown"
    classify_result_hash: str
```

- [ ] **Step 4: Write tests for classify_result_hash**

In `tests/test_ccdi_classifier.py`, add 4 tests from delivery.md Registry Tests:
- `test_classify_result_hash_input_coverage`: same topic_key, different matched_aliases → different hashes
- `test_classify_result_hash_stability`: same classify payload → same hash
- `test_classify_result_hash_different_confidence`: same topic, different confidence → different hashes
- `test_classify_result_hash_different_facet`: same topic, different facet → different hashes

- [ ] **Step 5: Implement classify_result_hash in hash_utils.py**

```python
import hashlib
import json

def classify_result_hash(topic_key: str, confidence: str, facet: str, matched_aliases: list[dict]) -> str:
    """Deterministic hash of a per-topic classify result.

    Includes confidence, facet, and matched_aliases (not just topic_key).
    Same payload always produces the same hash (stability invariant).
    """
    payload = {
        "topic_key": topic_key,
        "confidence": confidence,
        "facet": facet,
        "matched_aliases": sorted(
            [{"text": m["text"], "weight": m["weight"]} for m in matched_aliases],
            key=lambda m: m["text"],
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
```

- [ ] **Step 6: Run all tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_types.py tests/test_ccdi_classifier.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add scripts/ccdi/types.py scripts/ccdi/hash_utils.py tests/test_ccdi_types.py tests/test_ccdi_classifier.py
git commit -m "feat(ccdi): add Phase B foundation types and classify_result_hash"
```

---

## Task 2: Registry Extensions — Deferred State and TTL Lifecycle

**Files:**
- Modify: `scripts/ccdi/registry.py`
- Test: `tests/test_ccdi_registry.py` (extend)

**Spec references:** `registry.md#state-transitions`, `registry.md#ttl-lifecycle`, `registry.md#field-update-rules` (deferred rows), `registry.md#failure-modes` (deferred_ttl:0 load-time recovery)

**Depends on:** Task 1

- [ ] **Step 1: Write tests for write_deferred()**

Add to `tests/test_ccdi_registry.py`:
- `test_deferred_cooldown`: detected → deferred with cooldown reason, TTL set from config
- `test_deferred_scout_priority`: detected → deferred with scout_priority reason
- `test_deferred_target_mismatch`: detected → deferred with target_mismatch reason
- `test_deferred_ttl_initialization`: TTL set to `deferred_ttl_turns` config value at deferral time
- `test_deferred_vs_suppressed_distinction`: different reasons, different re-entry paths

- [ ] **Step 2: Run tests — expect FAIL**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_registry.py -k "deferred" -v`

- [ ] **Step 3: Implement write_deferred() in registry.py**

```python
def write_deferred(
    path: str,
    topic_key: str,
    reason: str,
    deferred_ttl: int,
) -> None:
    """Record deferral for a topic. reason: 'cooldown'|'scout_priority'|'target_mismatch'."""
    seed = load_registry(path)
    entry = _find_entry(seed, topic_key)
    if entry is None:
        import sys
        print(f"write_deferred: topic {topic_key!r} not in registry", file=sys.stderr)
        return
    entry.state = "deferred"
    entry.deferred_reason = reason
    entry.deferred_ttl = deferred_ttl
    _write_registry(path, seed)
```

- [ ] **Step 4: Write TTL lifecycle tests**

Add to `tests/test_ccdi_registry.py`:
- `test_deferred_ttl_decrement_per_turn`: TTL decrements by 1 on each dialogue-turn call
- `test_deferred_ttl_expiry_with_reappearance`: TTL=0 AND topic in classifier → detected
- `test_deferred_ttl_expiry_without_reappearance`: TTL=0, topic absent → TTL resets, stays deferred. Use non-default config value (e.g., deferred_ttl_turns=5) per spec
- `test_deferred_ttl_load_time_recovery_present`: Registry with deferred_ttl=0, topic in classifier → detected
- `test_deferred_ttl_load_time_recovery_absent`: Registry with deferred_ttl=0, topic absent → TTL reset
- `test_cooldown_deferral_preserves_consecutive_medium_count`: Medium leaf at count=1, deferred by cooldown → count stays 1
- `test_deferred_to_detected_consecutive_medium_initialization`: Topic deferred, TTL expires, reappears at medium → count=1; at high → count=0
- `test_registry_file_missing_reinitializes`: Missing registry file → `load_registry()` returns empty seed (no crash). Per registry.md#failure-modes line 273
- `test_registry_file_corrupt_reinitializes`: Corrupt JSON in registry file → `load_registry()` returns empty seed with warning. Per registry.md#failure-modes line 273
- `test_atomic_write_uses_temp_rename`: `_write_registry()` writes to tempfile then `os.replace()` — verify no partial writes by checking file exists and is valid JSON after write. Per registry.md#failure-modes line 274
- `test_results_file_stripped_on_load`: Registry with transient `results_file` field → stripped from in-memory representation at load time, warning logged. Per registry.md#failure-modes line 277

- [ ] **Step 5: Implement TTL lifecycle functions in registry.py**

Add `decrement_deferred_ttl(seed: RegistrySeed) -> None` and `apply_ttl_transitions(seed: RegistrySeed, classifier_topic_keys: set[str], config: CCDIConfig) -> list[TopicRegistryEntry]` that handle:
- Load-time: apply transition rule BEFORE per-turn decrement (deferred_ttl=0 entries)
- Per-turn: decrement all deferred entries by 1
- Transition: TTL=0 + classifier presence → detected; TTL=0 + absent → reset TTL, stay deferred

- [ ] **Step 6: Write high-confidence bypass test**

- `test_high_confidence_bypasses_deferred_ttl`: Deferred topic re-detected at high confidence → immediate transition to detected (bypass TTL)

- [ ] **Step 7: Implement high-confidence bypass in registry.py**

In TTL transition logic, check for high-confidence re-detection BEFORE TTL decrement per `registry.md#scheduling-rules` step 2.

- [ ] **Step 8: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_registry.py -k "deferred" -v`

- [ ] **Step 9: Commit**

```bash
git add scripts/ccdi/registry.py tests/test_ccdi_registry.py
git commit -m "feat(ccdi): add deferred state transitions and TTL lifecycle"
```

---

## Task 3: Registry Extensions — Semantic Hints and Consecutive-Medium Tracking

**Files:**
- Modify: `scripts/ccdi/registry.py`
- Test: `tests/test_ccdi_registry.py` (extend)

**Spec references:** `registry.md#semantic-hints`, `registry.md#scheduling-rules` steps 4/8/9, `registry.md#field-update-rules` (hint rows, consecutive_medium rows), `registry.md#suppression-re-entry`

**Depends on:** Task 1, Task 2

- [ ] **Step 1: Write consecutive-medium tracking tests**

Add to `tests/test_ccdi_registry.py`:
- `test_consecutive_medium_threshold_leaf`: Medium leaf turn 1 → no injection; turn 2 → injection fires; counter resets on topic absence
- `test_consecutive_medium_threshold_family_excluded`: Medium family turns 1-3 → count stays 0, injection does NOT fire
- `test_consecutive_medium_reset_on_topic_absence`: Medium turn 1 (count=1), absent turn 2 (count=0), medium turn 3 (count=1) → no injection turn 3
- `test_consecutive_medium_reset_after_injection`: After injection, counter resets to 0
- `test_consecutive_medium_reset_on_confidence_change`: Medium turn 1, HIGH turn 2 → count resets to 0
- `test_send_failure_preserves_consecutive_medium_count`: Send fails → count NOT reset

- [ ] **Step 2: Implement consecutive-medium update logic**

Add `update_redetections(seed: RegistrySeed, classifier_results: list[ResolvedTopic], current_turn: int) -> None` to registry.py that handles:
- Re-detection at medium confidence (leaf-kind only): increment count
- Re-detection at non-medium: reset count to 0
- Topic absent from classifier (non-suppressed): reset count to 0
- Re-detection on injected entry: update last_seen_turn only

- [ ] **Step 3: Write semantic hint processing tests**

Add to `tests/test_ccdi_registry.py`:
- `test_semantic_hint_elevates_candidate`: Prescriptive hint on detected → materially new
- `test_semantic_hint_unknown_topic`: Hint doesn't match any topic → ignored
- `test_malformed_hints_file`: Invalid JSON → ignored with warning
- `test_prescriptive_hint_re_enters_suppressed_weak`: suppressed:weak_results → detected
- `test_prescriptive_hint_re_enters_suppressed_redundant`: suppressed:redundant → detected
- `test_contradicts_prior_on_injected`: Append facet to pending_facets
- `test_contradicts_prior_on_detected`: Elevate to materially new
- `test_contradicts_prior_re_enters_suppressed`: Re-enter as detected
- `test_extends_topic_on_injected`: Emit facet_expansion candidate
- `test_extends_topic_on_detected`: Elevate to materially new
- `test_extends_topic_on_deferred`: Transition to detected first, then lookup path
- `test_extends_topic_re_enters_suppressed`: Re-enter as detected
- `test_facet_expansion_cascade_fallback_pending`: Resolved facet in facets_injected → use pending_facets[0]
- `test_facet_expansion_all_exhausted`: All facets in facets_injected → no candidate emitted
- `test_pending_facet_candidate_emission`: Injected topic with non-empty pending_facets → emit candidate
- `test_pending_facets_cleared_after_serving`: After injection at pending facet, remove from pending_facets
- `test_multiple_pending_facets_ordering`: Two facets → FIFO order preserved
- `test_intra_turn_hint_ordering`: contradicts_prior mutations visible to subsequent extends_topic cascade

- [ ] **Step 4: Implement semantic hint processing**

Add `process_semantic_hints(seed: RegistrySeed, hints: list[SemanticHint], inventory: CompiledInventory, classifier_fn, current_turn: int) -> list[InjectionCandidate]` to registry.py.

This function:
1. Processes hints sequentially (array order)
2. Classifies each `claim_excerpt` through the standard pipeline
3. Resolves topic_key from classification
4. Applies hint effects per registry.md scheduling table (prescriptive/contradicts_prior/extends_topic × detected/injected/suppressed/deferred)
5. Returns additional injection candidates (facet_expansion, pending_facet)

- [ ] **Step 5: Write suppressed → detected re-entry via hint tests**

These tests verify hint-driven suppression re-entry sets the correct fields: `state=detected`, `suppression_reason=null`, `suppressed_docs_epoch=null`, `last_seen_turn=current_turn`.

- [ ] **Step 6: Implement hint-driven suppression re-entry in process_semantic_hints**

For all 3 hint types resolving to a suppressed topic (regardless of suppression_reason): transition to detected with field resets per registry.md#field-update-rules.

- [ ] **Step 7: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_registry.py -k "consecutive_medium or hint or semantic or pending_facet or facet_expansion" -v`

- [ ] **Step 8: Commit**

```bash
git add scripts/ccdi/registry.py tests/test_ccdi_registry.py
git commit -m "feat(ccdi): add semantic hint processing and consecutive-medium tracking"
```

---

## Task 4: Session-Local Cache

**Files:**
- Create: `scripts/ccdi/cache.py`
- Test: `tests/test_ccdi_cache.py`

**Spec references:** `registry.md#session-local-cache`

**Depends on:** Task 1

- [ ] **Step 1: Write cache tests**

Create `tests/test_ccdi_cache.py`:
- `test_result_cache_hit_avoids_research`: Same fingerprint → cached results
- `test_negative_cache_prevents_retry`: Weak results → negative flag → no re-search
- `test_packet_cache_serves_existing`: Same (topic_key, facet) → cached packet
- `test_cache_keys_include_docs_epoch`: Same query, different docs_epoch → cache miss
- `test_cache_is_per_session_only`: New cache instance → no carryover

- [ ] **Step 2: Run tests — expect ImportError**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_cache.py -v`

- [ ] **Step 3: Implement cache.py**

```python
from scripts.ccdi.registry import normalize_fingerprint

class CCDICache:
    """Session-local cache for CCDI search results, packets, and negative flags."""

    def __init__(self) -> None:
        self._result_cache: dict[str, list[dict]] = {}
        self._packet_cache: dict[tuple[str, str], object] = {}  # (topic_key, facet) → FactPacket
        self._negative_cache: set[str] = set()  # fingerprints with weak results

    def get_results(self, query: str, docs_epoch: str | None) -> list[dict] | None:
        key = normalize_fingerprint(query, docs_epoch)
        return self._result_cache.get(key)

    def put_results(self, query: str, docs_epoch: str | None, results: list[dict]) -> None:
        key = normalize_fingerprint(query, docs_epoch)
        self._result_cache[key] = results

    def is_negative(self, query: str, docs_epoch: str | None) -> bool:
        key = normalize_fingerprint(query, docs_epoch)
        return key in self._negative_cache

    def mark_negative(self, query: str, docs_epoch: str | None) -> None:
        key = normalize_fingerprint(query, docs_epoch)
        self._negative_cache.add(key)

    def get_packet(self, topic_key: str, facet: str) -> object | None:
        return self._packet_cache.get((topic_key, facet))

    def put_packet(self, topic_key: str, facet: str, packet: object) -> None:
        self._packet_cache[(topic_key, facet)] = packet
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_cache.py -v`

- [ ] **Step 5: Commit**

```bash
git add scripts/ccdi/cache.py tests/test_ccdi_cache.py
git commit -m "feat(ccdi): add session-local cache module"
```

---

## Task 5: dialogue-turn Core Logic

**Files:**
- Create: `scripts/ccdi/dialogue_turn.py`
- Test: `tests/test_ccdi_dialogue_turn.py`

**Spec references:** `registry.md#scheduling-rules` (all 10 steps), `integration.md#dialogue-turn-registry-side-effects`, `integration.md#dialogue-turn-candidates-json-schema`, `registry.md#field-update-rules`

**Depends on:** Task 1, Task 2, Task 3, Task 4

This is the largest task. The `dialogue_turn()` function implements the full scheduling pipeline per turn.

- [ ] **Step 1: Write dialogue-turn scheduling tests**

Create `tests/test_ccdi_dialogue_turn.py` with tests:
- `test_new_topic_detected`: Absent → detected, candidate emitted
- `test_injected_not_reselected`: Injected topic not in candidates
- `test_low_confidence_excluded`: Low-confidence → detected but never in candidates
- `test_single_medium_no_injection`: 1 medium alone → no candidate
- `test_cooldown_defers_second`: Two high-confidence → first scheduled, second deferred:cooldown
- `test_cooldown_configurable`: Reads max_new_topics_per_turn from config
- `test_pending_facet_exempt_from_cooldown`: pending_facet processed same turn as new
- `test_facet_expansion_exempt_from_cooldown`: facet_expansion processed same turn as new
- `test_scheduling_tiebreaker`: Same confidence, same first_seen_turn → topic_key ascending
- `test_null_confidence_sorts_last`: pending_facet/facet_expansion candidates (null confidence) sort after medium
- `test_both_facets_absent_suppressed`: Scheduled facet absent AND default_facet absent → suppressed:weak_results
- `test_empty_queryspec_treated_as_absent`: Facet key present but empty array → fallback to default_facet
- `test_shadow_mode_suppresses_cooldown_write`: --shadow-mode → no deferred:cooldown write
- `test_suppression_reentry_scan_weak_results`: docs_epoch change → re-enter weak_results entries
- `test_suppression_reentry_scan_redundant_no_epoch`: docs_epoch change does NOT re-enter redundant entries
- `test_redundant_reentry_via_new_leaf`: New leaf in same family → redundant re-enters
- `test_suppressed_redetection_noop`: Suppressed topic re-detected, no re-entry trigger → no field update
- `test_overview_injected_propagation_facet_overview`: Injected with facet=overview → family context marked available. Per delivery.md rows 374-376 (graduation preflight prerequisite)
- `test_overview_injected_propagation_family_context_available`: Family context available after overview injection → next lookup uses leaf facet
- `test_overview_injected_propagation_non_overview_facet`: Injected with facet≠overview → family context NOT marked available

- [ ] **Step 2: Run tests — expect ImportError**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_dialogue_turn.py -v`

- [ ] **Step 3: Implement dialogue_turn.py**

Core function signature:

```python
@dataclass
class DialogueTurnResult:
    """Return value from dialogue_turn() — carries candidates + trace metadata."""
    candidates: list[InjectionCandidate]
    classifier_result: ClassifierResult  # For ccdi_trace construction
    shadow_defer_intents: list[ShadowDeferIntent]  # Counterfactual deferrals (shadow mode only)


def dialogue_turn(
    registry_path: str,
    text: str,
    source: str,  # "codex" | "user"
    inventory: CompiledInventory,
    config: CCDIConfig,
    hints: list[SemanticHint] | None = None,
    shadow_mode: bool = False,
    current_turn: int = 1,
    docs_epoch: str | None = None,
) -> DialogueTurnResult:
```

Implementation follows the spec's 10-step scheduling pipeline (registry.md#scheduling-rules steps 1-10) plus supporting operations. The implementation steps below expand on the spec's 10 steps with pre/post operations needed for a complete turn:

1. **Classify** text against inventory (supports spec step 1 — diff)
2. **Load-time recovery**: Apply deferred_ttl=0 transitions BEFORE decrement (registry.md#failure-modes)
3. **High-confidence bypass**: Deferred topics at high confidence → detected immediately (spec step 2)
4. **TTL decrement**: All deferred entries decrement by 1 (registry.md#ttl-lifecycle)
5. **TTL transitions**: TTL=0 → detected (if in classifier) or reset (if absent) (registry.md#ttl-lifecycle)
6. **Suppression re-entry scan**: Check all suppressed:weak_results entries for docs_epoch change (registry.md#suppression-re-entry)
7. **Process semantic hints**: Classify claim_excerpts, apply hint effects, collect candidates (spec steps 8-9 + registry.md#semantic-hints)
8. **Diff new topics**: absent → detected; update re-detections (spec step 1)
9. **Materially new + facet resolution**: Identify candidates, resolve facets (spec steps 2-3)
10. **Consecutive-medium tracking**: Leaf-kind medium increment; family-kind excluded (spec step 4)
11. **Cooldown enforcement**: Max 1 new per turn; shadow_mode suppresses cooldown write, emits ShadowDeferIntent instead (spec step 5)
12. **Candidate emission**: new (spec step 7), pending_facet (spec step 8), facet_expansion (spec step 9) in priority order
13. **Write registry**: Atomic write with all mutations

Return: `DialogueTurnResult` containing candidates, classifier_result (for agent trace construction), and shadow_defer_intents (for shadow mode diagnostics). The CLI `_cmd_dialogue_turn()` handler serializes `candidates` as JSON to stdout. The agent uses `classifier_result` and `shadow_defer_intents` to construct per-turn `ccdi_trace` entries with all 9 required keys.

**Note on ccdi_trace construction:** The agent (codex-dialogue) constructs the full 9-key trace entry per turn using: `classifier_result` and `candidates` from `dialogue-turn` stdout, its own observations for `action`, `packet_staged`, `scout_conflict`, `commit`, `shadow_suppressed`, and `semantic_hints` from its hint extraction. The CLI does not emit trace entries — it provides the raw data the agent assembles into trace format.

- [ ] **Step 4: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_dialogue_turn.py -v`

- [ ] **Step 5: Commit**

```bash
git add scripts/ccdi/dialogue_turn.py tests/test_ccdi_dialogue_turn.py
git commit -m "feat(ccdi): implement dialogue-turn scheduling pipeline"
```

---

## Task 6: CLI Extensions — dialogue-turn Subcommand and build-packet Flags

**Files:**
- Modify: `scripts/topic_inventory.py`
- Test: `tests/test_ccdi_cli.py` (extend)

**Spec references:** `integration.md#cli-tool-topicinventorypy`, `integration.md#shadow-mode-gate` (--shadow-mode flag), `integration.md#target-match-predicate` (--mark-deferred, --skip-build)

**Depends on:** Task 5

- [ ] **Step 1: Write CLI tests for dialogue-turn subcommand**

Add to `tests/test_ccdi_cli.py`:
- `test_dialogue_turn_updates_registry_file`: State persistence across calls
- `test_dialogue_turn_source_codex_vs_user`: Both accepted, same behavior (source_equivalence_baseline mark)
- `test_dialogue_turn_with_non_default_ttl`: Config-driven TTL reset
- `test_dialogue_turn_missing_inventory_snapshot`: Non-zero exit with descriptive error
- `test_dialogue_turn_rejects_inventory_flag`: --inventory → non-zero exit (wrong flag name)
- `test_dialogue_turn_shadow_mode`: --shadow-mode suppresses cooldown deferral writes

- [ ] **Step 2: Write CLI tests for build-packet extensions**

Add to `tests/test_ccdi_cli.py`:
- `test_build_packet_mark_deferred`: Writes deferred state to registry
- `test_build_packet_skip_build_with_mark_deferred`: --skip-build + --mark-deferred → no packet, registry updated
- `test_build_packet_skip_build_without_mark_deferred`: --skip-build alone → ignored, normal build
- `test_build_packet_shadow_mode_mark_deferred_noop`: --shadow-mode + --mark-deferred → exit 0, registry unchanged, stderr log
- `test_build_packet_missing_inventory_snapshot_with_registry`: Non-zero exit
- `test_build_packet_rejects_inventory_flag`: --inventory → non-zero exit
- `test_build_packet_empty_output_suppressed_redundant`: Good results but all chunk_ids in injected_chunk_ids → suppressed:redundant
- `test_build_packet_automatic_suppression_requires_registry`: No --registry-file → no suppression
- `test_build_packet_missing_coverage_target_with_mark_injected`: Non-zero exit
- `test_build_packet_facet_mismatch_mid_turn`: Prepare facet ≠ commit facet → non-zero exit
- `test_prepare_commit_packet_idempotency_initial`: Initial build-packet → commit build-packet with same inputs → identical chunk IDs. Per delivery.md rows 429-430
- `test_prepare_commit_packet_idempotency_mid_turn`: Mid-turn build-packet → commit with same inputs → identical chunk IDs
- `test_agent_gate_unchanged_when_initial_threshold_overridden`: Config overrides initial threshold → agent gate still uses hardcoded value. Per delivery.md rows 438-440
- `test_agent_gate_unchanged_when_config_more_permissive`: More permissive config → agent gate unaffected
- `test_agent_gate_matches_builtin_defaults`: Agent gate threshold matches `BUILTIN_DEFAULTS` value
- `test_agent_gate_config_isolation_phase_a`: Phase A agent gate independent of Phase B config. Per delivery.md row 442
- `test_inventory_snapshot_version_mismatch_best_effort`: `inventory_snapshot_version` differs from current → best-effort field mapping with discarded entries on version mismatch. Per registry.md#failure-modes line 278
- `test_build_packet_missing_results_file_without_skip_build`: --results-file absent without --skip-build → non-zero exit with descriptive error. Per integration.md line 34

- [ ] **Step 3: Run tests — expect FAIL**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_cli.py -k "dialogue_turn or mark_deferred or skip_build or shadow_mode" -v`

- [ ] **Step 4: Add dialogue-turn subcommand to topic_inventory.py**

Add `dialogue-turn` subparser with flags:
- `--registry-file` (required)
- `--text-file` (required)
- `--source` (required, choices=["codex", "user"])
- `--inventory-snapshot` (required)
- `--semantic-hints-file` (optional)
- `--config` (optional)
- `--shadow-mode` (flag)

Add `_cmd_dialogue_turn(args)` handler that:
1. Loads text, registry, inventory snapshot, config, optional hints
2. Calls `dialogue_turn()` from dialogue_turn.py
3. Serializes candidates as JSON to stdout
4. Returns 0

- [ ] **Step 5: Extend build-packet with new flags**

Add to `build-packet` subparser:
- `--mark-deferred` (takes topic_key)
- `--deferred-reason` (required with --mark-deferred)
- `--skip-build` (flag)
- `--shadow-mode` (flag)
- `--inventory-snapshot` (optional)

Update `_cmd_build_packet()`:
- If `--shadow-mode` + `--mark-deferred`: log intent to stderr, exit 0, no registry write
- If `--skip-build` + `--mark-deferred`: skip packet construction, write deferred state
- If `--skip-build` without `--mark-deferred`: ignore flag, normal build
- Add `--inventory-snapshot` requirement when `--registry-file` is present

Pre-argparse flag validation: `dialogue-turn` rejects `--inventory`, `build-packet` rejects `--inventory`.

- [ ] **Step 6: Write source_equivalence_baseline meta-test**

Add `test_source_divergence_canary` with synthetic module verification per delivery.md spec.

- [ ] **Step 7: Run all CLI tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_cli.py -v`

- [ ] **Step 8: Commit**

```bash
git add scripts/topic_inventory.py tests/test_ccdi_cli.py
git commit -m "feat(ccdi): add dialogue-turn subcommand and build-packet extensions"
```

---

## Task 7: Diagnostics Emitter

**Files:**
- Create: `scripts/ccdi/diagnostics.py`
- Test: `tests/test_ccdi_diagnostics.py`

**Spec references:** `delivery.md#diagnostics`

**Depends on:** Task 1

- [ ] **Step 1: Write diagnostics tests**

Create `tests/test_ccdi_diagnostics.py` with 4 tests from delivery.md:
- `test_false_positive_field_always_zero`: Emitter always outputs `false_positive_topic_detections: 0`
- `test_active_mode_omits_shadow_fields`: Active mode JSON does NOT contain shadow-only fields
- `test_shadow_mode_includes_shadow_fields`: Shadow mode JSON contains all shadow-only fields
- `test_unavailable_schema`: Only `status` and `phase` populated, all other fields absent

- [ ] **Step 2: Run tests — expect ImportError**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_diagnostics.py -v`

- [ ] **Step 3: Implement diagnostics.py**

The `DiagnosticsEmitter` class accumulates per-turn data and emits a final `DiagnosticsRecord`:

```python
class DiagnosticsEmitter:
    def __init__(self, status: str, phase: str, inventory_epoch: str | None, config_source: str):
        self._record = DiagnosticsRecord(
            status=status, phase=phase,
            topics_detected=[], topics_injected=[], topics_deferred=[], topics_suppressed=[],
            packets_prepared=0, packets_injected=0, packets_deferred_scout=0,
            total_tokens_injected=0, semantic_hints_received=0, search_failures=0,
            inventory_epoch=inventory_epoch, config_source=config_source,
            per_turn_latency_ms=[],
        )
        if status == "shadow":
            self._record.packets_target_relevant = 0
            self._record.packets_surviving_precedence = 0
            self._record.false_positive_topic_detections = 0

    def record_turn(self, latency_ms: int) -> None: ...
    def record_topic_detected(self, topic_key: str) -> None: ...
    def record_packet_prepared(self) -> None: ...
    def record_packet_injected(self, tokens: int) -> None: ...
    def record_search_failure(self) -> None: ...
    def record_hint_received(self) -> None: ...

    def emit(self) -> dict:
        return self._record.to_dict()

    @staticmethod
    def unavailable(phase: str = "initial_only") -> dict:
        return {"status": "unavailable", "phase": phase}
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_diagnostics.py -v`

- [ ] **Step 5: Commit**

```bash
git add scripts/ccdi/diagnostics.py tests/test_ccdi_diagnostics.py
git commit -m "feat(ccdi): add diagnostics emitter with active/shadow/unavailable schemas"
```

---

## Task 8: Graduation Validator

**Files:**
- Create: `scripts/validate_graduation.py`
- Test: `tests/test_validate_graduation.py`

**Spec references:** `delivery.md#validate_graduationpy-cli-interface`, `delivery.md#test_validate_graduationpy` (17 test rows)

**Depends on:** Task 7

- [ ] **Step 1: Write all 17 validator tests**

Create `tests/test_validate_graduation.py` with all 17 tests from delivery.md's `test_validate_graduation.py` table. Each test creates temp fixture files (graduation.json, annotations.jsonl, diagnostics directory) and invokes the validator via subprocess. Key tests:
- Annotations count match/mismatch
- False-positive rate arithmetic mismatch
- Diagnostics file count mismatch
- Yield/latency metrics heterogeneous dialogues
- Missing annotations/diagnostics
- Malformed annotations
- Sample size below minimum (100)
- Floating-point tolerance
- Yield arithmetic with heterogeneous packets_prepared
- Rejected status with absent/empty notes
- Approved with yield/latency/false-positive below/above thresholds
- shadow_adjusted_yield validation
- Sample-size escalation (preliminary rate ≥ 7%, labeled_topics < 200)
- Freshness guardrail (shadow_adjusted_yield absent → fallback to effective_prepare_yield)

- [ ] **Step 2: Run tests — expect FAIL**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_validate_graduation.py -v`

- [ ] **Step 3: Implement validate_graduation.py**

CLI with `--graduation`, `--annotations`, `--diagnostics-dir` flags (all required). Exit 0 on success ("OK" on stdout), exit 1 on failure (each failing check on stderr).

Checks:
1. `labeled_topics` matches JSONL line count
2. `false_positive_rate` matches computed rate from annotations
3. `evaluated_dialogues` matches diagnostics file count
4. `effective_prepare_yield` is global ratio (not per-dialogue mean)
5. `avg_latency_ms` is mean-of-all-turns (not mean-of-dialogue-means)
6. `shadow_adjusted_yield` consistency check
7. Kill criteria thresholds for approved status (yield ≥ 0.40, latency ≤ 500, false-positive ≤ 0.10)
8. Sample size minimum (labeled_topics ≥ 100)
9. Sample-size escalation (preliminary rate ≥ 7% → labeled_topics ≥ 200)
10. Rejected status requires non-empty notes
11. Freshness guardrail check

- [ ] **Step 4: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_validate_graduation.py -v`

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_graduation.py tests/test_validate_graduation.py
git commit -m "feat(ccdi): add graduation validator CLI with 17 consistency checks"
```

---

## Task 9: Phase B Boundary Contract Tests

**Files:**
- Modify: `tests/test_ccdi_contracts.py`

**Spec references:** `delivery.md#boundary-contract-tests` (Phase B rows)

**Depends on:** Task 1, Task 5, Task 6

- [ ] **Step 1: Write Phase B boundary tests**

Add to `tests/test_ccdi_contracts.py`:
- `test_candidate_type_enum_consistency`: ClassifierResult → InjectionCandidate candidate_type values match
- `test_semantic_hints_schema_boundary`: hint_type enum values, claim_excerpt length cap
- `test_graduation_status_enum_consistency`: Validator VALID_STATUS_VALUES matches gate implementation
- `test_ccdi_inventory_snapshot_absent_with_seed`: Atomic-pair invariant violated → degraded
- `test_ccdi_seed_inline_json_rejection`: Inline JSON (not file path) → treated as absent
- `test_shadow_mode_auto_suppression_permitted`: Empty build-packet in shadow mode → suppressed state written
- `test_injected_forward_only_invariant`: mark_injected on already-injected → idempotent
- `test_classify_result_hash_boundary`: Hash contract across classifier→registry boundary
- `test_candidate_type_new_for_standard`: Standard candidate → candidate_type: "new"
- `test_confidence_null_for_hint_candidates`: facet_expansion/pending_facet → confidence: null
- `test_transport_only_field_allowlist_completeness`: Every field in `TRANSPORT_ONLY_FIELDS` has a corresponding strip-on-load test. Per delivery.md row 489
- `test_defaults_table_topicregistryentry_synchronization`: Every `TopicRegistryEntry` field has a default in the data-model defaults table. Per delivery.md row 490
- `test_registry_null_field_serialization_includes_envelope`: Null-valued fields serialized in registry JSON (not omitted). Per delivery.md row 482
- `test_pending_facets_serialization_preserves_insertion_order`: pending_facets array order preserved through serialize/deserialize roundtrip. Per delivery.md row 484
- `test_results_file_write_time_exclusion_defense_in_depth`: `results_file` never written to persistent registry (defense-in-depth for transport-only stripping). Per delivery.md row 479
- `test_registryseed_results_file_stripped_after_multi_topic_commit`: Multi-topic commit → results_file stripped from all entries. Per delivery.md row 476
- `test_registryseed_results_file_stripped_when_all_commits_fail`: All commits fail → results_file still stripped. Per delivery.md row 477
- `test_sentinel_structure_invariant`: Registry seed transmitted as JSON within `<!-- ccdi-registry-seed -->` sentinel tags in ccdi-gatherer output, not inline in delegation envelope. Per integration.md line 139
- Replace Phase A xfail `test_ccdi_policy_snapshot_boundary` with updated xfail (still Phase B deferred)

- [ ] **Step 2: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_contracts.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/test_ccdi_contracts.py
git commit -m "feat(ccdi): add Phase B boundary contract tests"
```

---

## Task 10: Replay Harness Infrastructure

**Files:**
- Create: `tests/test_ccdi_replay.py`
- Create: `tests/fixtures/ccdi/happy_path.replay.json` (first fixture to validate harness)

**Spec references:** `delivery.md#replay-harness-teststest_ccdi_replaypy` (fixture format, execution model, assertion engine)

**Depends on:** Task 6

- [ ] **Step 1: Design replay harness runner**

The harness reads all `*.replay.json` fixtures from `tests/fixtures/ccdi/`, parametrizes them as pytest test cases, and replays the CLI pipeline per turn.

- [ ] **Step 2: Implement replay harness test_ccdi_replay.py**

Core components:
- `load_fixtures()`: Glob all `*.replay.json` from `tests/fixtures/ccdi/`
- `ReplayRunner`: Per-fixture runner that maintains registry state across turns
- Per-turn execution (from delivery.md execution model):
  1. Write `input_text` to temp file
  2. Run `classify --text-file <temp>` via subprocess
  3. If `expected_classifier_result`: assert match
  4. Write `semantic_hints` to temp file (if non-null)
  5. Run `dialogue-turn` with all flags
  6. If `expected_candidates`: assert match
  7. For each candidate with `search_results`: run prepare `build-packet`
  8. If `composed_target`: run target-match check (substring then classify fallback)
  9. If `codex_reply_error` is false: run commit `build-packet --mark-injected`
  10. If `codex_reply_error` is true: skip commit
- Assertion engine: `cli_pipeline_sequence`, `cli_calls_absent`, `final_registry_state`, `final_registry_file_assertions`, `trace_assertions`
- `assert_registry_unchanged(before_path, after_path)`: Deep JSON equality including null-valued keys

Supported assertion operators: `equals`, `contains`, `length_gte`, `is_null`, `not_null`.
Trace assertion operators: `assert_key_present`, `action` (equality check).

- [ ] **Step 3: Write and validate happy_path.replay.json**

First fixture: single topic detected → searched → injected → committed. Validates the harness works end-to-end. Must include `trace_assertions` with `assert_key_present` for all 9 required trace keys on at least one turn entry. Must also assert chunk ID determinism: prepare-phase chunk IDs equal commit-phase chunk IDs for the same (results-file, facet) pair. Per integration.md line 497 (idempotency invariant).

- [ ] **Step 4: Run harness with happy_path fixture — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_replay.py -v`

- [ ] **Step 5: Commit**

```bash
git add tests/test_ccdi_replay.py tests/fixtures/ccdi/happy_path.replay.json
git commit -m "feat(ccdi): add replay harness infrastructure with happy_path fixture"
```

---

## Task 11: Replay Fixtures — Core Scenarios

**Files:**
- Create: 17 fixture files in `tests/fixtures/ccdi/`

**Spec references:** `delivery.md#required-fixture-scenarios` (complete fixture list)

**Depends on:** Task 10

- [ ] **Step 1: Create core pipeline fixtures**

Create these fixtures per delivery.md specifications:
1. `scout_defers_ccdi.replay.json` — Scout target → CCDI deferred:scout_priority
2. `send_failure_no_commit.replay.json` — codex_reply_error=true → no commit, counter retained
3. `target_mismatch_deferred.replay.json` — Packet topics absent from composed_target → deferred:target_mismatch
4. `source_equivalence.replay.json` — --source codex vs user → identical output
5. `cooldown_defers_second_candidate.replay.json` — Two high-confidence → first injected, second deferred:cooldown
6. `suppressed_docs_epoch_written.replay.json` — Empty results → suppressed:weak_results with exact epoch
7. `target_match_classifier_branch.replay.json` — Condition (a) fails, condition (b) succeeds → target-relevant
8. `target_match_substring_only.replay.json` — Condition (a) succeeds alone
9. `target_match_both_fail.replay.json` — Both conditions fail → deferred:target_mismatch
10. `empty_build_skips_target_match.replay.json` — Empty build-packet → suppressed, no --mark-deferred
11. `seed_medium_baseline.replay.json` — Counter persistence across serialization boundary
12. `seed_medium_fresh_init.replay.json` — Brand-new topic, medium, leaf → count=1
13. `deferred_ttl_countdown_resets.replay.json` — TTL countdown → reset → re-entry
14. `high_confidence_bypasses_deferred_ttl.replay.json` — High confidence bypasses TTL
15. `high_confidence_bypasses_deferred_ttl_ttl1.replay.json` — TTL=1 edge case
16. `both_facets_absent_suppressed.replay.json` — Double-absent → suppressed
17. `empty_queryspec_array_fallback.replay.json` — Empty QuerySpec[] → fallback to default_facet

Each fixture includes required `trace_assertions`, `final_registry_file_assertions`, `cli_calls_absent` per delivery.md.

- [ ] **Step 2: Run all fixtures — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_replay.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/ccdi/*.replay.json
git commit -m "feat(ccdi): add 17 core replay fixtures"
```

---

## Task 12: Replay Fixtures — Semantic Hints and Coverage

**Files:**
- Create: 18 fixture files in `tests/fixtures/ccdi/`

**Spec references:** `delivery.md#required-fixture-scenarios` (hint and coverage fixtures)

**Depends on:** Task 10

- [ ] **Step 1: Create hint and coverage fixtures**

1. `semantic_hint_elevation.replay.json` — Prescriptive hint on detected → elevated → injected
2. `hint_no_effect_already_injected.replay.json` — Prescriptive on injected → no change; assertions (a)-(d)
3. `hint_coverage_gap.replay.json` — contradicts_prior on injected → facet to pending_facets
4. `hint_re_enters_suppressed.replay.json` — extends_topic on suppressed:weak_results → detected
5. `hint_re_enters_suppressed_redundant.replay.json` — extends_topic on suppressed:redundant → detected
6. `hint_facet_expansion.replay.json` — extends_topic on injected → facet expansion
7. `hint_facet_expansion_fallback_pending.replay.json` — Resolved facet exhausted → pending_facets[0]
8. `hint_facet_expansion_fallback_default.replay.json` — All exhausted → default_facet or discard
9. `hint_contradicts_prior_on_deferred.replay.json` — Elevates deferred → materially new
10. `hint_extends_topic_on_deferred.replay.json` — Elevates deferred → materially new
11. `hint_unknown_topic_ignored.replay.json` — Unmatched claim_excerpt → no effect
12. `hint_contradicts_prior_on_detected.replay.json` — Elevates detected → immediate lookup
13. `hint_prescriptive_on_suppressed.replay.json` — Re-enters suppressed:weak_results
14. `hint_contradicts_prior_on_suppressed.replay.json` — Re-enters suppressed:redundant
15. `multi_pending_facets.replay.json` — FIFO ordering across multi-turn pipeline
16. `pending_facets_roundtrip.replay.json` — Serialization order preserved through round-trip
17. `intra_turn_hint_ordering.replay.json` — Proves sequential processing (forward order)
18. `intra_turn_hint_ordering_reversed.replay.json` — Proves sequential processing (reversed order; different candidate result)

- [ ] **Step 2: Run all fixtures — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_replay.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/ccdi/*.replay.json
git commit -m "feat(ccdi): add 18 semantic hints and coverage replay fixtures"
```

---

## Task 13: Replay Fixtures — Shadow Mode, Cache, and Edge Cases

**Files:**
- Create: remaining ~17 fixture files in `tests/fixtures/ccdi/`

**Spec references:** `delivery.md#required-fixture-scenarios` (shadow mode, cache, edge case fixtures)

**Depends on:** Task 10

- [ ] **Step 1: Create shadow mode fixtures**

1. `shadow_skip_scout.replay.json` — Shadow-mode scout abstention: skip_scout with shadow_suppressed:true
2. `shadow_mode_cooldown_suppressed.replay.json` — --shadow-mode → no deferred:cooldown; shadow_defer_intent emitted
3. `shadow_suppressed_active_mode.replay.json` — Active mode skip_cooldown with shadow_suppressed:false
4. `shadow_suppressed_shadow_mode.replay.json` — Shadow mode skip_cooldown with shadow_suppressed:true
5. `multi_candidate_new_plus_exempt.replay.json` — 2 new + 1 pending_facet in one turn

- [ ] **Step 2: Create cache fixtures**

6. `cache_hit_same_query.replay.json` — Same fingerprint → search_docs invoked once
7. `negative_cache_prevents_retry.replay.json` — Weak results → negative cache → no re-search
8. `target_mismatch_then_ttl_then_cache.replay.json` — Three-step interaction

- [ ] **Step 3: Create suppression and re-entry fixtures**

9. `suppressed_redundant_no_reentry_on_epoch_change.replay.json` — docs_epoch change does NOT re-enter redundant
10. `redundant_reentry_via_new_leaf.replay.json` — New leaf → redundant re-enters
11. `weak_results_reentry_on_epoch_change.replay.json` — docs_epoch change → weak_results re-enters
12. `weak_results_scan_noop_absent.replay.json` — Scan fires but no mutations (assert_registry_unchanged)
13. `multi_entry_epoch_scan_discrimination.replay.json` — Per-entry epoch comparison, not registry-wide
14. `pending_facet_exempt_from_cooldown.replay.json` — pending_facet bypasses cooldown
15. `facet_expansion_exempt_from_cooldown.replay.json` — facet_expansion bypasses cooldown

- [ ] **Step 4: Create shadow defer intent fixtures**

16. `shadow_defer_intent_hash_stability.replay.json` — Same classifier input across turns → identical hash
17. Additional edge case fixtures as needed for coverage

- [ ] **Step 5: Run all fixtures — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_replay.py -v`

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/ccdi/*.replay.json
git commit -m "feat(ccdi): add shadow mode, cache, and edge case replay fixtures"
```

---

## Task 14: Phase B Integration Tests

**Files:**
- Modify: `tests/test_ccdi_integration.py`

**Spec references:** `delivery.md#integration-tests` (Phase B rows)

**Depends on:** Task 6, Task 7

- [ ] **Step 1: Write Phase B integration tests**

Add to `tests/test_ccdi_integration.py`:
- `test_full_dialogue_turn_mid_turn_injection`: Registry persists across turns
- `test_shadow_mode_diagnostics_fields_present`: Shadow mode → shadow-only fields present
- `test_active_mode_diagnostics_fields_absent`: Active mode → shadow-only fields absent
- `test_inventory_pinning_across_mid_dialogue_reload`: Pinned snapshot used, not on-disk changes
- `test_ccdi_debug_gating_trace_emission`: ccdi_debug=true → ccdi_trace present with all 9 keys
- `test_ccdi_debug_explicit_false_suppresses_trace`: ccdi_debug=false → no trace (separate named test)
- `test_ccdi_trace_semantic_hints_conditional_presence`: Null when no hints, array when hints exist
- `test_shadow_suppressed_field_presence`: shadow_suppressed present in all per-turn entries
- `test_suppressed_redetection_noop_cli_file`: Registry file unchanged (deep JSON equality)
- `test_temp_file_identity_per_turn`: Unique per-turn temp file paths
- `test_initial_ccdi_commit_skip_on_briefing_send_failure`: All entries remain detected
- `test_sentinel_extraction_from_ccdi_gatherer`: ccdi-gatherer output with valid sentinel → registry seed parsed correctly. Per delivery.md rows 509-511
- `test_malformed_sentinel_handling`: Malformed sentinel block → graceful degradation (no crash, CCDI disabled)
- `test_ccdi_gatherer_returns_no_sentinel`: ccdi-gatherer output without sentinel tags → ccdi_seed treated as absent
- `test_seed_file_path_identity_prepare_commit`: Registry seed file path passed to initial commit is the same file path used in commit-phase build-packet --mark-injected call. Per integration.md line 355

- [ ] **Step 2: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_integration.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/test_ccdi_integration.py
git commit -m "feat(ccdi): add Phase B integration tests"
```

---

## Task 15: codex-dialogue Agent Modifications

**Files:**
- Modify: `agents/codex-dialogue.md`

**Spec references:** `integration.md#shadow-mode-gate`, `integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue`, `integration.md#ccditrace-output-contract`, `integration.md#delegation-envelope-fields`

**Depends on:** Task 6

- [ ] **Step 1: Read current codex-dialogue.md**

Read `agents/codex-dialogue.md` to understand current structure and identify integration points.

- [ ] **Step 2: Add shadow mode gate**

At dialogue start, add logic:
1. Check for `ccdi_seed` in delegation envelope — if absent, CCDI mid-dialogue disabled
2. Check for `ccdi_inventory_snapshot` — if absent with ccdi_seed present, log warning, disable CCDI
3. Read `data/ccdi_shadow/graduation.json` — if absent or status ≠ "approved", shadow mode
4. Set `ccdi_mode` = "active" or "shadow"

- [ ] **Step 3: Add mid-dialogue CCDI loop (Step 5.5 — PREPARE)**

After composition (Step 4/5), before send (Step 6):
1. Write Codex's response to temp file
2. Optionally extract semantic hints from Codex's response
3. Run `dialogue-turn` with `--shadow-mode` if in shadow mode
4. Process candidates:
   - If scout target exists: `--mark-deferred scout_priority --skip-build` (with `--shadow-mode` if shadow)
   - If no scout target: for each candidate, search → build-packet → target-match check
   - If target-relevant and active mode: stage for prepending
   - If not target-relevant: `--mark-deferred target_mismatch --skip-build` (with `--shadow-mode` if shadow)

- [ ] **Step 4: Add COMMIT step (Step 7.5)**

After send confirmed:
- If active mode AND packet was sent: `--mark-injected`
- If shadow mode: no commit
- If send failed: no commit

- [ ] **Step 5: Add ccdi_trace emission**

When `ccdi_debug: true` in delegation envelope:
- Accumulate per-turn trace entries with all 9 required keys
- Add `shadow_defer_intent` entries for counterfactual deferrals
- Include trace in output

- [ ] **Step 6: Add diagnostics emission**

At dialogue end, emit diagnostics via the `DiagnosticsEmitter` interface:
- Active mode: standard fields only
- Shadow mode: include shadow-only fields
- Unavailable: only status + phase

- [ ] **Step 7: Commit**

```bash
git add agents/codex-dialogue.md
git commit -m "feat(ccdi): add mid-dialogue CCDI loop to codex-dialogue agent"
```

---

## Task 16: Layer 2b Infrastructure and Feasibility Gate

**Files:**
- Create: `tests/test_ccdi_agent_sequence.py`

**Spec references:** `delivery.md#layer-2b-agent-sequence-tests`

**Depends on:** Task 15

- [ ] **Step 1: Determine interception mechanism**

Evaluate primary mechanism (custom .mcp.json + PATH injection) vs fallback (PreToolUse hooks). Run feasibility pre-test: register a synthetic PreToolUse hook that returns exit code 2, invoke a target tool, verify the tool call was blocked.

- [ ] **Step 2: Implement chosen mechanism**

Create test infrastructure:
- For primary: `.mcp.json` stubs, `ccdi_cli_recorder` wrapper script
- For fallback: PreToolUse hook fixtures, environment variable passing

- [ ] **Step 3: Write feasibility tests**

- `test_layer2b_mechanism_selection`: Assert chosen mechanism is primary or fallback
- `test_shim_identity_check`: Assert shim argv[0] ≠ python3
- `test_shim_does_not_intercept_non_ccdi_python3`: Non-CCDI invocation → no log entry
- `test_interception_completeness_3_invocations`: 3 CLI invocations → captured count = 3

- [ ] **Step 4: Write 3 baseline behavioral tests**

- `test_agent_invokes_classify_before_dialogue_turn`: Tool-call ordering
- `test_agent_skips_build_packet_when_no_candidates`: Conditional tool invocation
- `test_agent_calls_mark_injected_after_codex_reply`: Prepare/commit ordering

- [ ] **Step 5: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_agent_sequence.py -v`

- [ ] **Step 6: Commit**

```bash
git add tests/test_ccdi_agent_sequence.py
git commit -m "feat(ccdi): add Layer 2b infrastructure and 3 baseline behavioral tests"
```

---

## Task 17: Layer 2b Graduation Gate and Pipeline Isolation Tests

**Files:**
- Modify: `tests/test_ccdi_agent_sequence.py`

**Spec references:** `delivery.md#layer-2b-agent-sequence-tests` (graduation gate, pipeline isolation)

**Depends on:** Task 16

- [ ] **Step 1: Write graduation gate tests**

Add with `@pytest.mark.skipif(not phase_a_resolved(), reason="Phase B only")`:
- `test_graduation_gate_file_absent_shadow`: No graduation.json → shadow mode, zero --mark-injected
- `test_graduation_gate_rejected_shadow`: status:rejected → shadow mode, zero commits
- `test_graduation_gate_approved_active`: status:approved → active mode, at least one --mark-injected
- `test_graduation_gate_phase_a_unconditional`: status:rejected → initial commits still fire

- [ ] **Step 1b: Write Layer 2b shadow diagnostic assertion tests**

Add:
- `test_shadow_defer_intent_resolves_on_topic_disappearance`: Topic with shadow_defer_intent disappears from classifier → intent resolves (no longer emitted). Per delivery.md row 736
- `test_shadow_defer_intent_resolves_on_committed_state_transition`: Topic transitions to committed (injected) → shadow_defer_intent no longer emitted. Per delivery.md row 737
- `test_shadow_false_positive_field_present_and_zero`: Shadow diagnostics → `false_positive_topic_detections` key present with value 0. Per delivery.md row 735
- `test_ccdi_inventory_snapshot_absent_with_seed_layer2b`: Layer 2b companion — ccdi_inventory_snapshot absent when ccdi_seed present → degraded behavior (no mid-dialogue CCDI). Per delivery.md row 487

- [ ] **Step 2: Write pipeline isolation tests**

- `test_scout_pipeline_no_ccdi_cli_calls`: execute_scout/process_turn contain zero topic_inventory.py calls
- `test_agent_does_not_read_ccdi_config`: Zero Read invocations on *ccdi_config* paths
- `test_cooldown_config_divergence`: Agent uses hardcoded cooldown, CLI uses overlay
- `test_shadow_mode_no_injected_deferred_mutations`: Registry has zero injected/deferred entries after shadow dialogue
- `test_shadow_mode_zero_mark_deferred_invocations`: Zero --mark-deferred calls in shadow
- `test_shadow_mode_auto_suppression_written`: Weak results in shadow → suppressed state present
- `test_cli_backstop_shadow_mark_deferred`: Agent passes --shadow-mode to --mark-deferred
- `test_shadow_defer_intent_trace_entries`: shadow_defer_intent entries emitted with correct fields

- [ ] **Step 3: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_ccdi_agent_sequence.py -v`

- [ ] **Step 4: Commit**

```bash
git add tests/test_ccdi_agent_sequence.py
git commit -m "feat(ccdi): add graduation gate and pipeline isolation tests"
```

---

## Task 18: Freshness Guardrail Tests and Final Verification

**Files:**
- Create: `tests/test_shadow_freshness_guardrail.py`

**Spec references:** `delivery.md#freshness-guardrail-test`, `delivery.md#shadow-mode-denominator-normalization`

**Depends on:** Task 8, Task 13

- [ ] **Step 1: Write freshness guardrail tests**

Create `tests/test_shadow_freshness_guardrail.py`:
- `test_freshness_guardrail_fires_on_stale_classify`: graduation.json where classify_result_hash is identical across all turns for a topic with shadow_defer_intent → validator emits warning, does NOT use shadow_adjusted_yield as gate
- `test_freshness_guardrail_positive_path`: Different classify_result_hash values across turns → shadow_adjusted_yield IS used as gate, validator exits 0
- `test_freshness_guardrail_negative_path`: Same fixture but shadow_adjusted_yield=0.35 (below 40%) → validator exits 1 citing shadow_adjusted_yield below threshold

- [ ] **Step 2: Run tests — expect PASS**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_shadow_freshness_guardrail.py -v`

- [ ] **Step 3: Run full Phase B test suite**

Run all Phase B tests together to verify no regressions:

```bash
cd packages/plugins/cross-model && uv run pytest \
  tests/test_ccdi_types.py \
  tests/test_ccdi_classifier.py \
  tests/test_ccdi_registry.py \
  tests/test_ccdi_config.py \
  tests/test_ccdi_cli.py \
  tests/test_ccdi_contracts.py \
  tests/test_ccdi_integration.py \
  tests/test_ccdi_packets.py \
  tests/test_ccdi_hooks.py \
  tests/test_ccdi_cache.py \
  tests/test_ccdi_dialogue_turn.py \
  tests/test_ccdi_diagnostics.py \
  tests/test_validate_graduation.py \
  tests/test_ccdi_replay.py \
  tests/test_shadow_freshness_guardrail.py \
  tests/test_build_inventory.py \
  -v --tb=short
```

Expected: All PASS. Record total test count.

- [ ] **Step 4: Run Phase A + Phase B TypeScript tests**

```bash
cd packages/mcp-servers/claude-code-docs && npm test -- --run tests/dump-index-metadata.test.ts
```

Expected: All 32 PASS (no regressions).

- [ ] **Step 5: Commit**

```bash
git add tests/test_shadow_freshness_guardrail.py
git commit -m "feat(ccdi): add freshness guardrail tests and verify full test suite"
```

---

## Dependency Map

```
T1 (types+hash)     ──────────────────────────────────────────┐
  │                                                           │
  ├─→ T2 (deferred+TTL) ──→ T3 (hints+medium) ──┐           │
  │                                              │           │
  ├─→ T4 (cache) ─────────────────────────────────┤           │
  │                                              │           │
  ├─→ T7 (diagnostics) ──→ T8 (validator) ───────│───→ T18   │
  │                                              │           │
  └─→ T9 (contracts) ───────────────────────────→│           │
                                                 │           │
                              T5 (dialogue-turn) ←───────────┘
                                      │
                              T6 (CLI extensions)
                                      │
                     ┌────────────────┼────────────────┐
                     │                │                │
              T10 (replay          T14 (integ      T15 (agent
               harness)            tests)          mods)
                     │                                │
              T11 (core                        T16 (L2b infra)
               fixtures)                              │
                     │                         T17 (L2b tests)
              T12 (hint
               fixtures)
                     │
              T13 (shadow
               fixtures)
                     │
              T18 (freshness + final)
```

## Test Count Summary

| Category | New Tests | Source |
|----------|----------|--------|
| Types (Phase B extensions) | ~10 | test_ccdi_types.py (+2 shadow_adjusted_yield) |
| classify_result_hash | 4 | test_ccdi_classifier.py |
| Registry (Phase B) | ~49 | test_ccdi_registry.py (+4 corruption/recovery) |
| dialogue-turn unit | ~20 | test_ccdi_dialogue_turn.py (+3 overview_injected propagation) |
| Cache | 5 | test_ccdi_cache.py |
| CLI (Phase B) | ~28 | test_ccdi_cli.py (+8 idempotency, agent gate, version mismatch, results-file) |
| Diagnostics | 4 | test_ccdi_diagnostics.py |
| Graduation validator | 17 | test_validate_graduation.py |
| Replay fixtures | 52 | test_ccdi_replay.py (happy_path includes chunk ID determinism assertion) |
| Boundary contracts (Phase B) | ~19 | test_ccdi_contracts.py (+8 transport-only, defaults, null-field, sentinel) |
| Integration (Phase B) | ~15 | test_ccdi_integration.py (+4 sentinel extraction, seed file identity) |
| Freshness guardrail | 3 | test_shadow_freshness_guardrail.py |
| Layer 2b | ~19 | test_ccdi_agent_sequence.py (+4 shadow diagnostic, inventory companion) |
| **Total new** | **~245** | |

Combined with Phase A (373 tests), total: **~618 tests**.

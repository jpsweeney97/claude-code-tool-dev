---
module: testing-strategy
legacy_sections: ["8"]
authority: implementation
normative: false
status: active
---

# Testing Strategy

> **Authority:** Implementation. This document describes *how* to test the Engram plugin. It references rules from [tool-surface.md](../contracts/tool-surface.md), [behavioral-semantics.md](../contracts/behavioral-semantics.md), [server-validation.md](server-validation.md), and [hooks.md](hooks.md), but does not define observable behavior.

## Scope {#scope}

This document defines:

- **Tier definitions** — what each test tier validates and owns
- **Physical layout** — directory structure, naming, markers
- **Fixture conventions** — factory fixtures, DB strategies, builders
- **Coverage requirements** — per-phase pipeline, normalizer, dedup, hook, FTS5, read tool, error transport
- **Architecture enforcement** — import boundary lint, hook classification parity
- **Spec validators** — CI checks for fragment links and stale references

This document does NOT define:

- What the server or hooks should *do* — see [server-validation.md](server-validation.md) and [hooks.md](hooks.md)
- Test implementation code — this is a strategy spec, not a test suite
- Performance benchmarks or load testing (deferred for v1)

---

## Tier Definitions {#tiers}

Four test tiers, mapped to the three-tier architecture in [internal-architecture.md](../internal-architecture.md) plus a fourth non-runtime tier for CI validators.

| Tier | Directory | Scope | Owns |
|------|-----------|-------|------|
| **Subsystem** | `tests/subsystem/` | Single-subsystem logic in isolation | Normalizers, write-plan computation, semantic dedup, three-state resolution, entity state machines, DB constraint verification |
| **Integration** | `tests/integration/` | Cross-subsystem paths through the validation pipeline | Full tool call → response round-trips, rejection precedence, error transport format, multi-entity mutations, search projection coupling |
| **Server** | `tests/server/` | Wiring and registration | Tool registration completeness, import boundary enforcement, hook classification parity |
| **Specs** | `tests/specs/` | CI validators for the modular spec | Fragment link resolution, stale reference detection |

**Tier weighting:** Subsystem tests are the bulk — they exercise all code paths with fast, isolated fixtures. Integration tests cover cross-subsystem behavior that subsystem tests cannot reach. Server tests are thin — wiring verification only. Specs tests run against `docs/specs/engram/**/*.md`.

**Tier ownership rules:**

- A validation rule is tested at the tier matching its primary runtime enforcer (crosswalk in [server-validation.md](server-validation.md#crosswalk))
- Rules with `DB Role: None` (server-only enforcement) require explicit subsystem tests — no schema backstop catches bugs
- Rules with `DB Role: CHECK/UNIQUE backstop` get one subsystem test verifying the backstop fires independently of server logic
- Error transport format (envelope structure, RPC codes, `reason_code` values) is owned by integration tier
- Registration and wiring validation is owned by server tier

---

## Physical Layout {#layout}

```
tests/
├── subsystem/
│   ├── test_anchor_hash.py          # anchor_hash normalizer (8-step algorithm)
│   ├── test_three_state.py          # resolve_three_state() and OMIT sentinel
│   ├── test_semantic_dedup.py       # Two-stage dedup across 7 mappings
│   ├── test_tags.py                 # Tags normalization, JSON serialization
│   ├── test_write_plan.py           # Write-plan computation, no-op detection
│   ├── test_session_lifecycle.py    # Session state machine (create/enrich/close)
│   ├── test_task_lifecycle.py       # Task state machine (open/close/reopen)
│   ├── test_lesson_lifecycle.py     # Lesson state machine (active/retract/reinforce)
│   ├── test_lesson_capture.py       # Create vs merge branching, invariant breach
│   ├── test_lesson_promote.py       # Promotion, idempotent re-promotion
│   ├── test_task_update_patch.py    # Patch-specific: remove_blocked_by, add_* wiring, empty-patch
│   ├── test_db_constraints.py       # Schema backstop verification (CHECK, UNIQUE, FK)
│   └── test_entity_integrity.py     # Entity kind integrity (same-transaction write)
├── integration/
│   ├── test_session_tools.py        # session_start, session_snapshot, session_end
│   ├── test_task_tools.py           # task_create, task_update (patch/close/reopen)
│   ├── test_lesson_tools.py         # lesson_capture, lesson_update, lesson_promote
│   ├── test_read_tools.py           # session_get, session_list, task_query, lesson_query, query
│   ├── test_error_transport.py      # Rejection envelopes, RPC errors, precedence
│   ├── test_fts5.py                 # FTS5 search correctness, trigger coverage, rebuild_search
│   └── test_search_projection.py    # Projection body mapping, trigger sync (file-backed)
├── server/
│   ├── test_tool_registration.py    # All 13 tools registered with correct names
│   ├── test_architecture_imports.py # No cross-subsystem imports (AST-based)
│   └── test_tool_parity.py          # Hook _READ/_MUTATION matches server tool set
├── specs/
│   ├── test_fragment_links.py       # Inter-file fragment link resolution
│   └── test_stale_refs.py           # Stale reference detection
├── support/
│   ├── builders.py                  # Factory fixtures: seed_session, seed_task, seed_lesson
│   ├── payloads.py                  # Hook payload builders
│   └── db.py                        # DB fixture helpers (schema init, connection factories)
└── conftest.py                      # Shared fixtures (db connections, tmp_path defaults)
```

**Naming:** `test_<module>.py` — flat within each tier directory. No sub-directories within tiers. Follows the context-injection plugin pattern ([`packages/plugins/cross-model/context-injection/tests/`](../../../../packages/plugins/cross-model/context-injection/tests/)).

**Support directory:** `tests/support/` contains shared builders and helpers. NOT a test tier — no `test_` prefix files. Imported by test files across tiers.

---

## Pytest Configuration {#pytest-config}

### Markers

Flat markers — `@pytest.mark.phase3`, not `@pytest.mark.phase(3)`.

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "phase1: Transport parse validation",
    "phase2: Common policy validation",
    "phase3: Session/target resolution",
    "phase4: Lifecycle/state checks",
    "phase5: Semantic dedup / write-plan",
    "phase6: Transactional write",
    "phase7: Response assembly",
    "subsystem: Subsystem tier tests",
    "integration: Integration tier tests",
    "server: Server tier tests",
    "specs: Spec validator tests",
    "slow: Tests requiring file-backed SQLite or subprocess spawning",
]
```

**Tier markers** are applied at module level via `pytestmark`:

```python
# tests/subsystem/test_anchor_hash.py
import pytest
pytestmark = pytest.mark.subsystem
```

**Phase markers** are applied at test function/class level. A test may carry multiple phase markers when it verifies multi-phase behavior (e.g., rejection precedence tests carry all relevant phase markers).

**Query examples:**

```bash
pytest -m phase3                    # All phase 3 tests across tiers
pytest -m "subsystem and phase5"    # Subsystem write-plan tests only
pytest -m "not slow"                # Skip file-backed DB and subprocess tests
```

---

## Conftest and Fixture Policy {#fixtures}

### Fixture Scope

**Function-scoped by default.** Every test gets a fresh database, fresh `tmp_path`, and fresh builder state. Module-scoped fixtures are prohibited — they leak state between tests and make failures non-reproducible.

**Exception:** The `conftest.py` schema fixture (which creates tables but no data) may be session-scoped for performance, since the schema is immutable.

### Factory Fixtures

Factory fixtures with explicit parameters — not pre-populated opaque fixtures.

```python
# tests/support/builders.py

def seed_session(db, *, session_id=None, goal="test session", closed=False, tags=None):
    """Create a session row with optional closure. Returns session_pk."""
    ...

def seed_task(db, session_pk, *, title="test task", status="open", priority="medium"):
    """Create a task row. Returns task_pk."""
    ...

def seed_lesson(db, session_pk, *, insight="test insight", status="active",
                reinforcement_count=0, anchor_hash=None):
    """Create a lesson row. Returns lesson_pk."""
    ...

def seed_snapshot(db, session_pk, *, kind="checkpoint", content="snapshot content"):
    """Create a snapshot row. Returns entity_pk."""
    ...
```

**Pre-populated fixtures are prohibited.** No `existing_session` or `populated_database` fixtures. Every test constructs its own state using `seed_*` builders. This makes preconditions visible in each test body.

### Impossible-State Fixtures

For invariant-breach testing, use direct SQL insertion to create states that the server would never produce:

```python
def seed_duplicate_active_lessons(db, session_pk, *, anchor_hash="v1:abc123"):
    """Insert two active lessons with the same anchor_hash via direct SQL.

    This state should never occur under correct server logic — it tests
    the invariant-breach detection path in lesson_capture.
    """
    ...
```

Direct SQL helpers live in `tests/support/builders.py` alongside factory fixtures. They are clearly named to indicate they create impossible states.

---

## Database and Filesystem Test Data {#db-fixtures}

### SQLite Mode Selection

| Mode | When to use | Fixture |
|------|-------------|---------|
| `:memory:` | Pure single-connection logic: normalizers, write-plan computation, state machine checks, dedup | `@pytest.fixture` returning `sqlite3.connect(":memory:")` |
| File-backed (`tmp_path`) | WAL, multi-connection, FTS5, `rebuild_search()`, migrations, trigger sync | `@pytest.fixture` returning path from `tmp_path / "test.db"` |

**Connection-Mode Coverage requirement:** Every DB-owning subsystem (`context/`, `work/`, `knowledge/`, `kernel/`) must have at least one file-backed contract test. This catches behaviors that work in `:memory:` but fail under file-backed SQLite (e.g., WAL mode, concurrent readers, FTS5 external-content sync).

**Multi-connection tests:** When test semantics depend on connection boundaries (e.g., testing that a write committed by connection A is visible to connection B), each connection must be an independent `sqlite3.connect()` call to the same file path. Do not reuse a single connection object.

### Schema Initialization

All test databases (both modes) must initialize with the full DDL from [ddl.md](../schema/ddl.md). A shared helper applies the schema:

```python
# tests/support/db.py

def init_schema(db_or_path):
    """Apply the full Engram DDL to a database connection or path.

    Handles both :memory: connections and file paths. Enables WAL mode
    for file-backed databases.
    """
    ...
```

### Three-State Raw-Argument Factories

For testing three-state field resolution, test data must inject raw `arguments` dicts — not Python keyword arguments (which collapse omitted and null).

```python
OMIT = object()  # Sentinel — key excluded from raw_args

@dataclass
class Phase1Case:
    """Test case for transport parse (phase 1) with three-state semantics."""
    name: str
    raw_args: dict          # Simulates ctx.request_context.request.params.arguments
    expected_goal: str      # Expected resolved value
    expected_tags: Any      # Expected resolved value

def make_session_start_args(*, goal=OMIT, branch=OMIT, tags=OMIT,
                            continued_from=OMIT, external_refs=OMIT):
    """Build a raw arguments dict for session_start, honoring OMIT sentinel.

    Keys set to OMIT are excluded entirely. Keys set to None are included
    as explicit null. All other values are included as-is.
    """
    args = {}
    for key, val in [("goal", goal), ("branch", branch), ("tags", tags),
                     ("continued_from_session_ids", continued_from),
                     ("external_refs", external_refs)]:
        if val is not OMIT:
            args[key] = val
    return args
```

**Why OMIT, not fluent builders:** The OMIT sentinel pattern makes each test's intent explicit at the call site. `make_session_start_args(goal="x", tags=None)` clearly shows: goal is present, tags is explicit null, everything else is omitted. Fluent builders obscure this by spreading state across method calls.

---

## Validation Pipeline Coverage {#pipeline-coverage}

### Per-Phase Test Requirements

Each phase from the 7-phase pipeline ([server-validation.md](server-validation.md#pipeline)) has specific test obligations:

| Phase | Marker | Test Focus | Tier |
|-------|--------|------------|------|
| 1 | `phase1` | Three-state resolution, `OMIT` vs `None` vs present. `Phase1Case` dataclass for parse fixtures. **Negative transport coverage:** malformed input rejection (missing required fields, wrong types, unparseable JSON) | Subsystem, Integration (malformed input → RPC error format) |
| 2 | `phase2` | Empty string rejection (all scalar fields), enum validation, required fields, mutual exclusion. Per-tool field acceptance/rejection matrices. **Specific named checks:** `session_snapshot(kind='final')` rejection (not an empty-string, enum, or mutual-exclusion check — its own category); `session_snapshot(content='')` empty-string rejection (required scalar field) | Subsystem |
| 3 | `phase3` | Lookup success/failure, self-link rejection, PK resolution for relationships. Lookup failure → non-envelope RPC error | Integration |
| 4 | `phase4` | Lifecycle state transitions, closed-session guard, final snapshot guard, terminal task guard. Per-action state machine tables | Subsystem (state logic), Integration (rejection format) |
| 5 | `phase5` | Write-plan computation, semantic no-op detection, closed-session no-op exception (4-case matrix — see below), anchor_hash matching (create vs merge), two-stage dedup, NULL-label backfill, `remove_blocked_by` deletion path, `add_*` provenance wiring, empty-patch distinction (syntactic vs semantic) | Subsystem |
| 6 | `phase6` | Transactional atomicity (including rollback on internal failure — partial write before abort must leave no durable state), search projection coupling, timestamp updates, `INSERT OR IGNORE` backstop | Integration |
| 7 | `phase7` | Response envelope structure, outcome values, `details` fields | Integration |

### Rejection Precedence Tests

An explicit test category for multi-violation inputs. Each test supplies input that violates multiple phases and asserts only the first-phase rejection code is returned.

```python
@pytest.mark.phase2
@pytest.mark.phase4
def test_rejection_precedence_phase2_before_phase4():
    """Empty-string title (phase 2) on a terminal task (phase 4).

    Phase 2 rejects first → policy_blocked for empty title,
    not invalid_transition for terminal task.
    """
    ...
```

These tests carry all relevant phase markers for queryability. Minimum: one precedence test per adjacent phase pair that can both reject (1→2, 2→3, 2→4, 3→4, 4→5).

**Transport format note:** Phases 2, 4, and 5 reject with entity envelopes carrying `reason_code`. Phase 1 and phase 3 reject with non-envelope RPC errors. Precedence tests involving phase 3 assert that the RPC error (lookup failure) is returned instead of a later-phase envelope rejection — these compare transport formats, not just `reason_code` values.

### Append-Only Relation Rejection

Append-only relations (`continued_from_session_ids`, `external_refs`) must be tested for explicit null rejection at phase 2 — not through `resolve_three_state()`. These relations use a different code path: `resolve_three_state()` applies to scalar and tags fields only; append-only null rejection is a phase 2 common policy rule.

---

## Normalizer Tests {#normalizers}

### anchor_hash {#anchor-hash-tests}

Two test layers:

**Layer 1 — Normalization vectors:** Test each step of the 8-step algorithm in isolation. The implementation must expose `normalize_anchor_text()` as a pure function (input string → normalized string, before SHA-256).

| # | Step | Representative Test Cases |
|---|------|--------------------------|
| 1 | NFKC | Compatibility chars (ﬁ → fi, ² → 2) |
| 2 | Line endings | `\r\n` and `\r` → `\n` |
| 3 | Trim | Leading/trailing spaces, tabs, newlines |
| 4 | Strip prefix | `- item`, `* item`, `> quote`, `1. item` — one level only |
| 5 | Unwrap | `**bold**`, `*italic*`, `` `code` ``, `_underline_` — one level only |
| 6 | Collapse | `a  b   c` → `a b c`, tabs included |
| 7-8 | Hash + prefix | Fixed golden values (below) |

Minimum 15 test vectors covering all steps.

**Equivalence-class pairs:** Inputs that should hash equal (formatting-only differences):
- `"- Use API caching"` vs `"Use API caching"` (prefix strip)
- `"**Important insight**"` vs `"Important insight"` (unwrap)
- `"  Use  consistent  naming  "` vs `"Use consistent naming"` (trim + collapse)

**Distinction pairs:** Inputs that must hash differently (semantic differences):
- `"API_KEY"` vs `"api_key"` (case-preserving — no casefold)
- `"Use X.Y.Z"` vs `"Use X Y Z"` (punctuation preserved)

**Layer 2 — Golden hash values:** 3-5 hard-coded `v1:<sha256>` values for regression. These pin the algorithm — if the hash changes, the test fails.

```python
GOLDEN_HASHES = [
    ("Use caching for API calls", "v1:a3f8..."),
    ("- **Use caching for API calls**", "v1:a3f8..."),  # Same after normalization
    ("API_KEY is required", "v1:b7c2..."),               # Distinct from api_key
]
```

### resolve_three_state

Test matrix using `OMIT` sentinel:

| `raw_keys` | `typed_value` | `existing_value` | Expected |
|------------|--------------|-------------------|----------|
| field absent | N/A | `"existing"` | `"existing"` (OMITTED) |
| field present | `None` | `"existing"` | `None` (EXPLICIT NULL) |
| field present | `"new"` | `"existing"` | `"new"` (PRESENT) |
| field present | `"same"` | `"same"` | `"same"` (PRESENT — same value, still "present") |
| field absent | N/A | `None` | `None` (OMITTED — preserve existing null) |

### Tags Normalization

- Dedup preserves first occurrence order
- Whitespace stripped from each tag
- Empty array after dedup → NULL
- JSON serialization round-trip
- Tags NOT included in anchor_hash (categorical metadata, not semantic identity)

---

## Mutation Branch and Dedup Coverage {#mutations}

### session_start Closed-Session No-Op Matrix

The closed-session no-op exception ([server-validation.md](server-validation.md#write-plan)) requires a 4-case test matrix. The phase-4 guard defers to phase-5 write-plan computation — the success/reject boundary depends on field-level comparison with dedup:

| # | Scenario | Expected | Key Assertion |
|---|----------|----------|---------------|
| 1 | Closed session, identical scalars, no new links | Success (no-op) | Response reflects persisted state unchanged |
| 2 | Closed session, scalar field change (e.g., `goal`) | Reject: `policy_blocked` | No durable state change |
| 3 | Closed session, new `continued_from` link | Reject: `policy_blocked` | No new `session_links` row |
| 4 | Closed session, duplicate `continued_from` (already linked) | Success (no-op via dedup) | Dedup produces zero-delta write-plan |

**Tier:** Subsystem (write-plan logic) + Integration (rejection format).

### task_update(patch) Phase-5 Coverage

`task_update(action='patch')` is the most complex mutation tool — its phase-5 has branches not covered by generic dedup or write-plan tests:

| # | Scenario | Key Assertion |
|---|----------|---------------|
| 1 | `remove_blocked_by` deletes dependency rows | `task_dependencies` rows removed, task still present |
| 2 | `add_blocked_by` + `add_sources` + `add_external_refs` wiring | Each `add_*` param routes to correct table with correct dedup key |
| 3 | Syntactic empty patch (no patchable fields or provenance) | Reject: `policy_blocked` at phase 2 or 5 |
| 4 | Semantic no-op (fields supplied but identical to persisted) | Success, no-op response |
| 5 | `add_derived_from_lesson_ids` on update path | `entity_derivations` row created with correct entity PKs |

**Tier:** Subsystem (state logic) + Integration (round-trip).

### lesson_capture Branch Matrix

8 test cases covering both server-determined codepaths:

| # | Codepath | Scenario | Key Assertion |
|---|----------|----------|---------------|
| 1 | Create | No anchor_hash match | New lesson row, `outcome: created` |
| 2 | Merge | Match, context omitted/null | `reinforcement_count` incremented, existing context preserved, no `context_conflict` |
| 3 | Merge | Match, context present and identical | `reinforcement_count` incremented, context preserved, `details.context_conflict: false` |
| 4 | Merge | Match, context present and different | `details.context_conflict: true`, existing context preserved |
| 5 | Merge | Match, tag replacement | New tags replace existing (deduplicated) |
| 6 | Merge | Match, provenance dedup | Duplicate provenance produces no new rows |
| 7 | Create | Retracted match ignored | Retracted lesson with same hash is not a merge target |
| 8 | Error | Invariant breach | >1 active lesson with same hash → internal error (-32603) |

Cases 2-3 are distinct: omitted/null context and identical context both produce "no conflict" but exercise different branches in the merge semantics ([behavioral-semantics.md](../contracts/behavioral-semantics.md#anchor-hash-merge)). Case 8 requires the `seed_duplicate_active_lessons()` impossible-state fixture — direct SQL insertion bypasses server invariants.

### Two-Stage Semantic Dedup

Parametrized across **all 7 parameter→table mappings** (from [server-validation.md](server-validation.md#semantic-dedup)):

```python
@pytest.mark.phase5
@pytest.mark.parametrize("mapping", [
    ("sources", "provenance_links"),
    ("external_refs", "provenance_links"),
    ("continued_from_session_ids", "session_links"),
    ("blocked_by", "task_dependencies"),
    ("derived_from_task_ids", "entity_derivations"),
    ("derived_from_lesson_ids", "entity_derivations"),
    ("lesson_promote.target", "provenance_links"),
])
def test_semantic_dedup_stage1_within_input(mapping):
    """Duplicate entries within a single request are deduplicated (stage 1)."""
    ...

@pytest.mark.phase5
@pytest.mark.parametrize("mapping", [...])
def test_semantic_dedup_stage2_against_persisted(mapping):
    """Entries already in the database produce no new rows (stage 2)."""
    ...
```

**All 7 mappings, not 2-3.** The dedup algorithm is shared, but wiring differs per mapping (different tables, different dedup keys, different tools). 2-3 representative mappings leave wiring gaps.

**Create-path vs update-path wiring:** `sources` (create tools) and `add_sources` (update tools) share the same table and dedup key but route through different tool handlers. The 7-entry parametrize list above covers logical mappings; the two test functions (`stage1_within_input` and `stage2_against_persisted`) each run all 7, producing 14 tests total. Within each parametrized test case, the test must exercise **both** the create-tool path (e.g., `task_create` with `sources`) and the update-tool path (e.g., `task_update(action='patch')` with `add_sources`) by calling different tool handlers — not by expanding to 14 mappings. Same applies to `external_refs`/`add_external_refs` and `derived_from_*_ids`/`add_derived_from_*_ids`.

**NULL-label backfill:** For all `provenance_links` mappings — `sources`, `add_sources`, `external_refs`, `add_external_refs`, and `lesson_promote.target` — test that an existing row with NULL `target_label` and a new input with non-NULL label produces a label UPDATE (not a no-op). This is the one exception to first-write-wins. Both create-path and update-path (`add_*`) parameters share this exception.

**`INSERT OR IGNORE` backstop:** Test independently of server dedup logic. Insert a duplicate directly via SQL and verify the constraint prevents the row without raising an error.

---

## Hook Test Strategy {#hooks}

### Hybrid Approach

Two test styles for the hook script (`scripts/engram_guard.py`):

| Style | What It Tests | How | Tier |
|-------|--------------|-----|------|
| **Subprocess** | Contract behavior — exit codes, stderr format, env file writes | `subprocess.run(["python3", guard_path], input=json_payload)` | Integration (10 tests) |
| **Direct import** | Handler logic — classification, extraction, state machines | `importlib.util.spec_from_file_location` + call handler functions | Subsystem |

**Why hybrid:** Subprocess tests are slow (~100ms each vs ~1ms for direct import) but verify the contract — that the script exits with the correct code and writes the correct stderr. Direct-import tests are fast and can exhaustively cover classification matrices and extraction logic.

### Subprocess Contract Tests (10 tests)

| # | Event | Test | Assert |
|---|-------|------|--------|
| 1 | PreToolUse | Identity match on mutation | Exit 0, no stderr |
| 2 | PreToolUse | Identity mismatch on mutation | Exit 2, stderr contains truncated UUIDs |
| 3 | PreToolUse | Missing `tool_input.session_id` | Exit 2, stderr contains "requires session_id" |
| 4 | PreToolUse | Missing `hook_session_id` (common input) | Exit 2 (fail-closed) |
| 5 | PreToolUse | Read tool (skip identity check) | Exit 0 |
| 6 | PreToolUse | Unknown tool suffix | Exit 2, stderr contains "unrecognized tool" |
| 7 | PreToolUse | Malformed stdin (not JSON) | Exit 2 (fail-closed) |
| 8 | PostToolUse | Successful tool call | Exit 0, JSONL log entry written |
| 9 | PostToolUseFailure | Failed tool call | Exit 0, JSONL log entry with `error_class` |
| 10 | SessionStart | Environment bootstrap | Exit 0, `ENGRAM_DB_PATH` line in env file |

Test 4 covers the 4th identity failure mode from [hooks.md](hooks.md#identity-guard): `hook_session_id` (Claude Code's session UUID in the common input field) is missing. Distinct from test 3 (missing `tool_input.session_id`).

**Subprocess fixture:** All subprocess tests use `tmp_path` as `cwd` to isolate the `.engram/` directory. Test 9 uses a path with spaces and metacharacters to verify `shlex.quote()`.

### Direct-Import Tests

| Category | Tests |
|----------|-------|
| `_classify_tool()` | All 13 tool suffixes classified correctly. Unknown suffix returns sentinel |
| `_classify_error()` | Transport tokens, server tokens, overlap tie-break → `unknown`, empty string |
| `_READ` / `_MUTATION` sets | Disjoint, union covers all 13 suffixes, no duplicates |
| Identity extraction | `data["session_id"]` vs `data["tool_input"]["session_id"]` paths |
| Telemetry event building | `outcome` and `entity_id` extraction from various `tool_response` shapes |

### Hook Payload Builders

```python
# tests/support/payloads.py

def make_pre_tool_use(*, tool_name, session_id, tool_session_id=None,
                      tool_input=None, cwd="/tmp/test-project"):
    """Build a PreToolUse hook payload (stdin JSON)."""
    ...

def make_post_tool_use(*, tool_name, session_id, tool_response=None, cwd=...):
    """Build a PostToolUse hook payload."""
    ...

def make_post_tool_use_failure(*, tool_name, session_id, error="", is_interrupt=False, cwd=...):
    """Build a PostToolUseFailure hook payload."""
    ...

def make_session_start(*, session_id, cwd, source="startup"):
    """Build a SessionStart hook payload."""
    ...
```

Each builder produces a canonical minimal payload shape. Tests extend with additional fields as needed. `cwd` defaults to `tmp_path` in fixtures.

### Telemetry Log Assertions

Hook tests that verify log entries use a `tmp_path` project root:

```python
def read_telemetry_log(cwd):
    """Read .engram/hooks.jsonl and return list of parsed events."""
    log_path = Path(cwd) / ".engram" / "hooks.jsonl"
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text().splitlines()]
```

Assert:
- Block events are logged **before** exit 2 (entry present in log even though hook exits non-zero)
- Allow events produce **no** PreToolUse log entry
- Success/failure events include correct `tool_suffix`, `category`, `input_keys`
- Session init events include `engram_db_path`

---

## FTS5 and Search Coverage {#fts5}

Two distinct FTS5 test concerns — runtime search correctness and CI lint false positives. Do not conflate them.

### Runtime Search Correctness (Integration Tier)

**File-backed SQLite required** — FTS5 external-content mode with triggers behaves differently from `:memory:` in edge cases.

**Table names:** `search_projection` is the source table (physical rows). `search_documents` is the FTS5 virtual table (`USING fts5(... content='search_projection')`). Three triggers (`search_ai`, `search_ad`, `search_au`) sync `search_documents` when `search_projection` changes. Tests must verify both layers — projection rows for data correctness, FTS queries via `search_documents` for search correctness.

| # | Test | Assert |
|---|------|--------|
| 1 | Mutation writes update `search_projection` | After `task_create`, projection row exists with correct `body` (`description`) |
| 2 | FTS query via `search_documents` returns hits | After seeding session + task + lesson, `query(text="...")` finds correct entities |
| 3 | Entity-type body mapping is correct | Session body = `goal + context_summary + summary`. Task body = `description`. Lesson body = `context`. *(White-box test: body mapping is implementation-defined per [rationale.md](../schema/rationale.md), not a normative contract)* |
| 4 | Trigger sync (INSERT) | New projection row → FTS index updated, searchable |
| 5 | Trigger sync (UPDATE) | Updated projection row → old content not searchable, new content searchable |
| 6 | Trigger sync (DELETE) | Deleted projection row → content no longer searchable |
| 7 | `rebuild_search()` repair | Manually delete a projection row, call `rebuild_search()`, verify FTS queries restored |
| 8 | Entity type filtering | `query(text="...", entity_types=["task"])` returns only tasks, not sessions/lessons |
| 9 | `lesson_update(reinforce)` projection sync | After reinforcing a lesson, verify `search_projection` row is updated (or confirm `reinforcement_count` is not in the projection body — `context` is the body field for lessons) |

Test 7 requires direct SQL deletion of a `search_projection` row — this simulates projection drift that `rebuild_search()` is designed to repair.

**`reinforce` projection note:** [server-validation.md](server-validation.md#lesson-update-validation) `reinforce` phase-6 sub-table lists "Update lesson row + provenance" without `+ search_projection` — the only mutation tool that omits it. Since the lesson projection body field is `context` (not `reinforcement_count`), a reinforce that adds no provenance may genuinely produce no projection change. Test 9 verifies this: either the projection is updated, or the omission is intentionally correct and the test documents why.

### CI Lint False Positives (Specs Tier)

The pre-resolved Q3 item: when grepping for `S[0-9]` patterns in spec files, FTS5 SQL statements produce false positives (e.g., `fts5(` tokens). The spec validator must filter these.

Covered in [Spec Validator Tests](#spec-validators).

---

## Read Tool Coverage {#reads}

### Minimum Coverage Per Tool

| Tool | Happy Path | Invalid Param | Lookup Semantics | Additional |
|------|-----------|---------------|------------------|------------|
| `session_get` | Existing session → SessionDetail | Non-existent `session_id` → RPC -32602 | Direct lookup | `loadable_snapshot` tri-branch: final preferred, checkpoint fallback, null |
| `session_list` | Multiple sessions, state filter, pagination | Invalid `state` enum → -32602, invalid cursor → -32602 | Collection | Ordering: `(activity_at DESC, started_at DESC, session_id DESC)` — assert deterministic tie-break. Filter-before-limit semantics |
| `task_query` | Filter by status, priority, session | Invalid `status[]` enum → -32602, invalid `priority[]` enum → -32602, invalid cursor → -32602 | `session_id` not found → empty results (not error) | |
| `lesson_query` | Sort by `reinforcement_count_desc`, filter by status | Invalid `sort_by` enum → -32602, invalid cursor → -32602 | `session_id` not found → empty results (not error) | |
| `query` | FTS match across entity types | Empty `text` → -32602, invalid cursor → -32602 | Full-text search | |

**Tier ownership:**

- **Server tier:** Registration — all 5 read tools registered with correct names
- **Integration tier:** Request/response round-trip and error transport format
- **Subsystem tier:** Only for `query` internals (FTS5 search, relevance scoring) — see [FTS5 section](#fts5)

**Empty-results-not-error semantics:** `task_query(session_id=<missing>)` and `lesson_query(session_id=<missing>)` must explicitly test that a non-existent `session_id` returns an empty result set, not an error. This is a specific lookup semantic that differs from mutation tools (which reject with RPC error on unknown session).

---

## Error Transport Coverage {#errors}

### Integration Test Matrix

| Category | Tool Example | Assert |
|----------|-------------|--------|
| `policy_blocked` | `task_update(action='patch')` on terminal task | `outcome: null`, `reason_code: "policy_blocked"`, entity null, no durable state change |
| `invalid_transition` | `task_update(action='reopen')` on non-terminal task | `outcome: null`, `reason_code: "invalid_transition"`, no state change |
| `conflict` | `session_end` with `final_content` when final exists | `outcome: null`, `reason_code: "conflict"`, no state change |
| Lookup failure | `task_update` with non-existent `task_id` | RPC error -32602, structured `data` with `field` and `value` |
| Internal error | `lesson_capture` with anchor_hash invariant breach | RPC error -32603 |
| Internal error rollback | Phase-6 failure after partial write (simulated) | RPC error -32603, **no durable state change** — transaction rolled back |
| Collection error | `session_list` with invalid `state` enum | RPC error -32602 |

**Atomic rejection invariant:** Every rejection test must verify **no durable state change**. Read the database after the rejected call and assert it matches the pre-call state. This applies to both determinate rejections (envelope with `reason_code`) and internal errors (RPC -32603) — [server-validation.md](server-validation.md#pipeline) promises full transactional rollback on internal errors.

**Reserved codes:** `duplicate` and `dependency_blocked` are not currently emitted. Do not test them as emitted reason codes. Instead, test the idempotent paths they relate to (provenance re-submission returns success, not `duplicate`).

---

## Architecture Enforcement {#architecture}

### Import Boundary Lint

**File:** `tests/server/test_architecture_imports.py`

AST-based enforcement of the no-cross-subsystem-import rule ([internal-architecture.md](../internal-architecture.md)):

```python
def test_no_cross_subsystem_imports():
    """Walk all production .py files in engram/.

    For each file, determine its owning subsystem (context/, work/,
    knowledge/, kernel/). Parse with ast.parse(). Walk Import and
    ImportFrom nodes. Assert no import resolves to a different subsystem.

    Cross-subsystem types must go through kernel/types.py.
    """
    ...
```

**No `TYPE_CHECKING` exception.** Cross-subsystem imports are forbidden even under `if TYPE_CHECKING:`. Type stubs that import across boundaries create invisible coupling. Cross-subsystem types go to `kernel/types.py`.

**Output on failure:** Report file path, line number, owning subsystem, and offending module. Example: `context/sessions.py:12 (context) imports work.tasks — cross-subsystem import forbidden`.

### Hook Classification Parity

**File:** `tests/server/test_tool_parity.py`

Verify that the hook's `_READ` and `_MUTATION` sets match the server's registered tool set:

```python
def test_hook_tool_sets_match_server():
    """Load engram_guard.py via importlib. Load server.py tool registrations.

    Assert:
    1. _READ | _MUTATION == server's registered tool suffixes
    2. _READ.isdisjoint(_MUTATION)
    3. No extra suffixes in either set
    """
    ...
```

**Note:** This test may import both `engram_guard.py` and `server.py`. The hook code itself must never import server modules — this parity check is test-only.

### Entity Kind Integrity

**File:** `tests/subsystem/test_entity_integrity.py`

Verify that entity creation always produces matching `entities.kind` and domain table row atomically ([server-validation.md](server-validation.md#crosswalk) — "Entity kind integrity", DB Role: None, primary enforcer: Server same-transaction write).

| # | Test | Assert |
|---|------|--------|
| 1 | Session creation produces `kind='session'` entity row | `entities.kind` matches domain table |
| 2 | Task creation produces `kind='task'` entity row | `entities.kind` matches domain table |
| 3 | Lesson creation produces `kind='lesson'` entity row | `entities.kind` matches domain table |
| 4 | Snapshot creation produces `kind='snapshot'` entity row | `entities.kind` matches domain table |

**Tier:** Subsystem. This rule has `DB Role: None` in the crosswalk — no schema backstop catches a kind mismatch. The server's same-transaction write is the only enforcer, so subsystem tests must verify it explicitly.

---

## Spec Validator Tests {#spec-validators}

### Fragment Link Validation

**File:** `tests/specs/test_fragment_links.py`

Validates that all inter-file markdown links in `docs/specs/engram/**/*.md` resolve correctly. Uses `re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', line)` per file with relative path resolution.

**Live regression tests:** Run against the actual spec files in `docs/specs/engram/`. These tests fail if a spec edit breaks a link — catching drift at CI time.

**Synthetic tests:** Unit tests using temp-tree fixtures (`tmp_path` with .md files) to verify the validator's behavior on known-good and known-broken links.

**Fragment anchor resolution:** Links like `[foo](bar.md#anchor-name)` must resolve: (1) `bar.md` exists relative to the source file, and (2) `{#anchor-name}` exists in `bar.md` as a heading ID or explicit anchor.

### Stale Reference Detection

**File:** `tests/specs/test_stale_refs.py`

Detects references to deleted or renamed anchors.

**Exclusions (stale-ref scan only):**

- `legacy-map.md` — historical mapping document, expected to reference pre-modularization section numbers
- `amendments.md` — tracks changes to normative docs, expected to reference superseded content

These exclusions do NOT apply to fragment-link validation. Broken links in `legacy-map.md` and `amendments.md` are real drift and should fail CI.

**FTS5 false-positive filtering:** When scanning for `S[0-9]` section-reference patterns, filter out matches inside SQL code blocks (FTS5 statements like `fts5(` produce false positives for `S[0-9]` grepping). Use code-block detection (track ` ``` ` fences) to skip matches inside fenced code.

---

## Minimum Coverage Matrix {#coverage-matrix}

Summary of minimum test counts per component:

| Component | Tier | Min Tests | Key Invariant |
|-----------|------|-----------|---------------|
| `anchor_hash` normalizer | Subsystem | 15 vectors + 3-5 golden | Step-level + equivalence pairs + distinction pairs |
| `resolve_three_state()` | Subsystem | 5 | All three states + edge cases |
| Semantic dedup | Subsystem | 14 (2 per mapping × 7) | Stage-1 and stage-2 per mapping (both create-path and update-path wiring) |
| NULL-label backfill | Subsystem | 5 | Backfill, already-labeled, new-row — covering `sources`, `add_sources`, `external_refs`, `add_external_refs`, `lesson_promote.target` |
| Tags normalization | Subsystem | 5 | Dedup, whitespace, empty→NULL, round-trip, not-in-hash |
| Write-plan / no-op | Subsystem | 10 | Zero-delta, closed-session no-op (4-case matrix), empty patch (syntactic vs semantic), `remove_blocked_by` deletion |
| `task_update(patch)` phase-5 | Subsystem + Integration | 5 | remove_blocked_by, add_* wiring, empty-patch, semantic no-op, derived_from |
| `lesson_capture` branches | Subsystem + Integration | 8 | Create, merge (5 variants incl. identical-context), retracted-ignore, invariant-breach |
| State machines | Subsystem | ~15 | Per-action × per-status — tasks: 3 actions × 3 status groups (open, in_progress, terminal) = 9 ([server-validation.md](server-validation.md#task-update-validation)); lessons: 3 actions × 2 statuses (active, retracted) = 6 ([server-validation.md](server-validation.md#lesson-update-validation)) |
| Rejection precedence | Integration | 5+ | One per adjacent rejecting phase pair (1→2, 2→3, 2→4, 3→4, 4→5) |
| Phase-1 malformed input | Integration | 3+ | Missing required fields, wrong types, unparseable — RPC error format |
| Hook subprocess | Integration | 10 | All 4 event types, fail-closed (incl. missing hook_session_id), fail-silent |
| Hook direct-import | Subsystem | ~15 | Classification, extraction, telemetry building |
| FTS5 runtime | Integration | 9 | Trigger sync (`search_documents` via `search_projection`), body mapping, rebuild_search, reinforce projection sync |
| Read tools | Integration | 15 | Happy-path + invalid-param + cursor validation + loadable_snapshot tri-branch + ordering + empty-results-not-error |
| Error transport | Integration | 7 | Reason codes, RPC errors, atomic rejection, phase-6 rollback |
| Entity kind integrity | Subsystem | 4 | All 4 entity kinds (session, task, lesson, snapshot) |
| Architecture imports | Server | 1 | No cross-subsystem imports |
| Hook parity | Server | 1 | _READ ∪ _MUTATION == server tools |
| Tool registration | Server | 1 | 13 tools registered |
| Fragment links | Specs | 2+ | Live regression + synthetic |
| Stale refs | Specs | 2+ | Live regression + synthetic |

**Estimated total:** ~165-190 tests across all tiers.

---

## Deferred / Out of Scope {#deferred}

| Item | Reason | Revisit When |
|------|--------|--------------|
| Performance benchmarks | Single-user tool, latency not critical in v1 | User reports latency issues |
| Load testing | No concurrent access in v1 | Multi-user support considered |
| Mutation fuzzing | Marginal value given explicit per-tool coverage | Coverage gaps emerge in practice |
| Cursor format/encoding internals | Cursor encoding/expiration spec is an open contracts question (#5). Basic cursor *error handling* (invalid cursor → -32602) is tested in the read tool coverage matrix | Contracts amendment defines format |
| Migration testing | Deferred to [migration-strategy.md](migration-strategy.md) | Migration strategy designed |
| `dependency_blocked` tests | Reserved — not emitted in v1 | Contracts amendment assigns it |
| DAG cycle detection | Deferred architecture feature ([internal-architecture.md](../internal-architecture.md)) | Feature implemented |
| `lesson_promote` on retracted lessons | Behavior unspecified in contracts — [server-validation.md](server-validation.md) open question #2 | Contracts amendment specifies behavior |

---

## Cross-References {#cross-refs}

| Topic | Location |
|-------|----------|
| Three-tier test architecture | [internal-architecture.md](../internal-architecture.md) |
| Validation pipeline (7 phases) | [server-validation.md](server-validation.md#pipeline) |
| Enforcement ownership crosswalk | [server-validation.md](server-validation.md#crosswalk) |
| anchor_hash algorithm (8 steps) | [server-validation.md](server-validation.md#anchor-hash) |
| Three-state resolution | [server-validation.md](server-validation.md#three-state) |
| Semantic dedup (7 mappings) | [server-validation.md](server-validation.md#semantic-dedup) |
| Hook specifications (4 events) | [hooks.md](hooks.md) |
| Hook identity guard | [hooks.md](hooks.md#identity-guard) |
| Hook telemetry log | [hooks.md](hooks.md#telemetry-log) |
| FTS5 schema (triggers, projection) | [ddl.md](../schema/ddl.md) |
| Search projection body mapping | [rationale.md](../schema/rationale.md) |
| `rebuild_search()` repair | [rationale.md](../schema/rationale.md) |
| Tool surface (parameters, envelopes) | [tool-surface.md](../contracts/tool-surface.md) |
| Behavioral semantics (merge, atomicity) | [behavioral-semantics.md](../contracts/behavioral-semantics.md) |
| Context-injection test patterns (reference) | [`packages/plugins/cross-model/context-injection/tests/`](../../../../packages/plugins/cross-model/context-injection/tests/) |
| Codex collaborative design review | Dialogue #29, thread `019ceda8-b223-7223-b450-34c2ef12e241` |
| Codex adversarial review | Dialogue #30, thread `019cedcd-70fc-7b43-8f0f-ea63795b3214` |

# Context Injection v0a — Implementation Progress

**Plan:** `docs/plans/2026-02-12-context-injection-v0a-implementation.md`
**Branch:** `docs/cross-model-learning-system`
**Package:** `packages/context-injection/`

## Carry-Forward (Read First)

Decisions from prior sessions that affect upcoming work. Max 3 active bullets. Each session: check these before starting, clear resolved items.

_(none yet — populated during implementation)_

## Session Schedule

| Session | Tasks | Theme | Status | Commit |
|---------|-------|-------|--------|--------|
| S1 | 1, 2 | Foundation (scaffolding + enums) | Pending | — |
| S2 | 3, 4 | Type definitions (base, input, output) | Pending | — |
| S3 | 5 | Discriminated unions (highest risk) | Pending | — |
| S4 | 6, 8 | Parallel utilities (canonical + paths) | Pending | — |
| S5 | 7, 9 | State + entity extraction | Pending | — |
| S6 | 10, 11 | Templates + pipeline | Pending | — |
| S7 | 12, 13, 14 | Server + integration + cleanup | Pending | — |

## Session Definitions

### S1: Foundation (Tasks 1-2)

**Plan sections:** Task 1 (lines 30-111), Task 2 (lines 112-409)

**Entry criteria:**
- Branch `docs/cross-model-learning-system` checked out
- `python-sdk-git/` available (SDK source reference)

**Work:**
- Task 1: Create `packages/context-injection/` with pyproject.toml, `__init__.py`, `__main__.py`, conftest.py
- Task 2: Implement `enums.py` — all StrEnum types (Status, EntityKind, ScoutVerb, PathDecision tag, etc.)

**Subagent strategy:** Sequential. Tasks are small and tightly coupled (Task 2 needs Task 1's scaffolding).

**Exit criteria:**
- `uv run pytest tests/test_enums.py -v` — all pass, zero skips
- Package installs cleanly (`uv sync --dev` from package directory)
- All enums importable and tested (round-trip value checks, StrEnum membership)
- One commit per task

**Risks:** Low. Scaffolding is mechanical. Only risk: pyproject.toml dependency resolution if `mcp` SDK has changed.

**Artifacts created:**
- `packages/context-injection/pyproject.toml`
- `packages/context-injection/context_injection/__init__.py`
- `packages/context-injection/context_injection/__main__.py`
- `packages/context-injection/context_injection/enums.py`
- `packages/context-injection/tests/__init__.py`
- `packages/context-injection/tests/conftest.py`
- `packages/context-injection/tests/test_enums.py`
- `packages/context-injection/uv.lock`

---

### S2: Type Definitions (Tasks 3-4)

**Plan sections:** Task 3 (lines 410-666), Task 4 (lines 667-907)

**Entry criteria:**
- S1 complete (enums importable, tests passing)
- `enums.py` available for import

**Work:**
- Task 3: `types.py` part 1 — `ProtocolModel` base class (frozen, strict), `Focus`, `TurnRequest`, and all input models
- Task 4: `types.py` part 2 — `Entity`, `PathDecision`, `Budget`, `DedupRecord` (with commented-out validator stub), `ClarifierQuestion`, `TemplateCandidate`, and all output models

**Subagent strategy:** Sequential. Task 4 builds on Task 3's base class and imports.

**Exit criteria:**
- `uv run pytest tests/test_types.py -v` — all pass, zero skips
- All input and output models construct and validate under strict mode
- `DedupRecord` has commented-out `model_validator` stub (activates in S3/Task 5)
- `TemplateCandidate.placeholder_values` typed as `list[Any]` (not bare `list`)
- Frozen immutability tested (assignment raises `ValidationError`)
- One commit per task

**Risks:** Medium. Pydantic strict mode behavior with nested models — verify that dict-to-model coercion works (per Codex review learning). If tests fail on nested model construction, relax strict mode selectively.

**Artifacts created:**
- `packages/context-injection/context_injection/types.py` (partial — parts 1-2)
- `packages/context-injection/tests/test_types.py` (single file, extended in S3)

---

### S3: Discriminated Unions (Task 5)

**Plan sections:** Task 5 (lines 908-1462)

**Entry criteria:**
- S2 complete (all non-union types tested)
- All output model types available for union composition

**Work:**
- Task 5: `types.py` part 3 — `ScoutSpec` union (Read/Grep/Ls/Stat), `ScoutOption`, `TurnPacket`, `ScoutResult` union (with callable discriminator). Uncomment `DedupRecord.model_validator`. Add 4 invariant tests for DedupRecord.

**Subagent strategy:** Sequential. Single high-risk task — needs focused attention, not parallelization.

**Exit criteria:**
- All discriminated unions validate correctly with strict mode
- Callable discriminator `_scout_result_discriminator()` routes 5 failure statuses to single "failure" tag
- `ScoutResult` union has 3 branches (success, failure, pending), not 7
- `ReadResult.excerpt_range` and `GrepMatch.ranges` use `Annotated[list[int], Field(min_length=2, max_length=2)]` (not tuple)
- `DedupRecord.model_validator` enforced: `template_already_used` requires `template_id`, `entity_already_scouted` forbids it
- Round-trip serialization tests pass for all union types
- `uv run pytest tests/test_types.py -v` — all pass (including new union and DedupRecord validator tests), zero skips
- One commit

**Risks:** Highest. Three compounding risk factors:
1. Callable discriminator may produce unexpected JSON schema (verify and record in Open Issues if problematic)
2. Strict mode + discriminated unions + StrEnum interaction is under-documented in Pydantic v2
3. `model_validator(mode="after")` interaction with frozen models

If blocked: isolate the failing union, write a minimal reproduction, and check Pydantic v2 source/docs before changing approach.

**Artifacts modified:**
- `packages/context-injection/context_injection/types.py` (completed — all 3 parts)
- `packages/context-injection/tests/test_types.py` (union tests and DedupRecord validator tests added)

---

### S4: Parallel Utilities (Tasks 6 + 8)

**Plan sections:** Task 6 (lines 1463-1706), Task 8 (lines 2000-2162)

**Entry criteria:**
- S3 complete (all types including unions tested)
- Types importable for use in canonical serialization and path checking

**Work:**
- Task 6: `canonical.py` — deterministic JSON serialization for entity identity keys and dedup keys. Sorting, normalization, hashing.
- Task 8: `paths.py` — path denylist checking, path normalization, traversal detection. Security-sensitive.

**Subagent strategy:** Parallel. Tasks 6 and 8 have no dependencies on each other — prime candidate for `superpowers:subagent-driven-development` with two parallel agents.

**Exit criteria:**
- Canonical serialization produces deterministic output (same input → same bytes → same hash)
- Entity key generation tested with diverse inputs (ordering, nesting, unicode)
- Path denylist blocks sensitive paths (`.env`, `credentials.*`, etc.)
- Traversal detection catches `../` patterns
- Symlink policy explicit in paths.py (resolve-and-contain via realpath, or document alternative)
- Risk-signal path detection tested (`*secret*`, `*token*`, `*credential*` patterns) — Codex review gap
- `uv run pytest tests/test_canonical.py tests/test_paths.py -v` — all pass, zero skips
- `uv run pytest tests/ -v` — full regression check, all prior tests still pass
- One commit per task

**Risks:** Medium. Canonical serialization edge cases (float precision, unicode normalization). Path checking false positives/negatives on edge cases.

**Artifacts created:**
- `packages/context-injection/context_injection/canonical.py`
- `packages/context-injection/context_injection/paths.py`
- `packages/context-injection/tests/test_canonical.py`
- `packages/context-injection/tests/test_paths.py`

---

### S5: State + Entity Extraction (Tasks 7 + 9)

**Plan sections:** Task 7 (lines 1707-1999), Task 9 (lines 2163-2197)

**Entry criteria:**
- S4 complete (canonical.py and paths.py tested)
- `canonical.py` available (state.py uses canonical keys for dedup store)

**Reference sections (read before implementing):**
- Contract `docs/references/context-injection-contract.md`:
  - HMAC Token Specification: lines 434–487 (Task 7: generation, verification, payload, key management)
  - Focus Bundle Structure: lines 57–103 (Task 9: extraction sources — focus.claims, focus.unresolved, context_claims)
  - Entity Type enum + Disambiguation Rules: lines 709–739 (Task 9: type precedence, pattern matching)
  - Confidence enum: lines 741–747 (Task 9: scout eligibility by confidence level)
  - Entity field definitions: lines 317–326 (Task 9: Entity object structure)

**Work:**
- Task 7: `state.py` — HMAC token generation/verification, TurnRequest store (bounded OrderedDict with oldest-eviction), `AppContext` dataclass wiring HMAC key + store + entity counter
- Task 9: `entities.py` — entity extraction from conversation turns. **Plan is structural only** — regex patterns, heuristics, and extraction logic must be designed during implementation.

**Ordering constraint:** Task 7 must be committed and all `test_state.py` tests passing before Task 9 begins. No upstream schema changes in S5 unless Task 7 tests force it.

**Subagent strategy:** Sequential. Task 9 depends on Task 7 (imports `AppContext` for entity counter). Task 9 is creative work — not suitable for unsupervised parallel execution.

**Task 9 MVP scope (timeboxed):**

Entity extraction is limited to 4 categories for v0a:

| Category | Pattern | Examples |
|----------|---------|----------|
| Paths | Contains `/` or known extension (`.py`, `.yaml`, `.json`, `.toml`, `.md`, `.ts`, `.js`) | `src/config/settings.yaml`, `config.py:42` |
| URLs | Starts with `http://` or `https://` | `https://docs.example.com/api` |
| Dotted symbols | Matches `word.word.word` (2+ dots, no spaces) | `pkg.mod.func`, `os.path.join` |
| Structured errors | Traceback lines, `*Error:` patterns | `ValueError: invalid literal`, `File "app.py", line 42` |

**Explicitly excluded from v0a:** bare function calls (`foo()`), bare domain names, ambiguous single tokens (`README`, `config`), env vars without `$` prefix.

**Hard-stop signals** (stop iterating on Task 9, document in Open Issues, move to S6):
- Adding a 5th extraction category
- Changing types in `types.py` or `enums.py` to accommodate extraction patterns
- Exceeding 6 red-green pytest iterations after Task 7 is committed

**Exit criteria:**
- HMAC tokens generate and verify correctly (round-trip, tamper detection)
- TurnRequest store supports put/get/has with bounded eviction (`MAX_TURN_RECORDS = 200`)
- Duplicate `turn_request_ref` rejection tested
- `AppContext` provides `next_entity_id()` counter
- Entity extraction covers all 4 MVP categories with tests for each
- Backticked entities → `high` confidence; unquoted path-like → `medium` confidence
- Span tracking prevents overlapping extractions
- `uv run pytest tests/test_state.py tests/test_entities.py -v` — all pass, zero skips
- `uv run pytest tests/ -v` — full regression check, all prior tests still pass
- One commit per task

**Risks:** High. Task 9 is the biggest creative risk in the entire plan — no concrete patterns provided. The MVP scope and hard-stop signals above convert this from open-ended creative work into a bounded task. If extraction quality is insufficient within the timebox, document limitations in Open Issues and move on — refinement can happen post-v0a.

**Artifacts created:**
- `packages/context-injection/context_injection/state.py`
- `packages/context-injection/context_injection/entities.py`
- `packages/context-injection/tests/test_state.py`
- `packages/context-injection/tests/test_entities.py`

---

### S6: Templates + Pipeline (Tasks 10 + 11)

**Plan sections:** Task 10 (lines 2198-2230), Task 11 (lines 2231-2261)

**Entry criteria:**
- S5 complete (state.py and entities.py tested)
- All upstream modules available: types, enums, canonical, paths, state, entities

**Reference sections (read before implementing):**
- Contract `docs/references/context-injection-contract.md`:
  - Template matching and ranking: lines 337–345 (anchor type ordering, confidence, ambiguity)
  - TemplateId enum: lines 774–782 (4 MVP templates, required entity types)
  - Scout option fields: lines 372–403 (ReadOption and GrepOption conditional fields)
  - DedupRecord semantics: lines 282–289, 359–364 (resolved-key dedupe, not identity-key)
  - Budget rules: lines 830–841 (per-turn, per-excerpt, per-conversation caps)
  - TurnPacket success response: lines 146–291 (full response structure)
  - Call 1 flow: lines 13–49 (protocol overview)
- Design plan `docs/plans/2026-02-11-conversation-aware-context-injection.md`:
  - Template decision tree (3 steps): lines 71–81 (hard gates, prefer closers, best anchor)
  - Budget computation: lines 370–420 (MVP caps, risk-signal halving)
  - Dedup strategy: lines 411–420 (per-entity, per-template)

**Work:**
- Task 10: `templates.py` — template matching against extracted entities, scout option synthesis with HMAC-bound tokens, dedup filtering. **Plan is structural only.**
- Task 11: `pipeline.py` — compose all modules into the Call 1 pipeline: `TurnRequest` → entity extraction → path checking → template matching → budget calculation → `TurnPacket` assembly.

**Subagent strategy:** Sequential. Task 11 depends on Task 10. Both are structural — require reading the contract and design plan for detailed behavior.

**Exit criteria:**
- Template matching produces `TemplateCandidate` list from entities + template registry
- Scout options include HMAC tokens that verify against stored specs
- Dedup filtering excludes already-scouted entities and already-used templates
- Resolved-key dedupe tested: two mentions of same file (one via filename, one via path) must not produce duplicate scouts — Codex review gap
- Risk-signal cap halving tested: `risk_signal=True` produces half the budget caps in scout options — Codex review gap
- Budget floor invariant tested: `evidence_history.length` is the floor even if evidence evicted from store — Codex review gap
- Pipeline composes all stages: `process_turn(turn_request, app_context) -> TurnPacket`
- Pipeline tests verify end-to-end data flow (not just individual stages)
- Pipeline integration test: `process_turn()` with realistic TurnRequest produces valid TurnPacket with entities, path decisions, template candidates, and budget
- `uv run pytest tests/test_templates.py tests/test_pipeline.py -v` — all pass, zero skips
- `uv run pytest tests/ -v` — full regression check, all prior tests still pass
- One commit per task

**Risks:** Medium. Template matching semantics are under-specified in the plan. Resolved-key dedupe (Codex-identified gap) must be addressed here. Budget calculation floor invariant needs explicit testing.

**Artifacts created:**
- `packages/context-injection/context_injection/templates.py`
- `packages/context-injection/context_injection/pipeline.py`
- `packages/context-injection/tests/test_templates.py`
- `packages/context-injection/tests/test_pipeline.py`

---

### S7: Server + Integration + Cleanup (Tasks 12 + 13 + 14)

**Plan sections:** Task 12 (lines 2262-2440), Task 13 (lines 2441-2529), Task 14 (lines 2530-2596)

**Entry criteria:**
- S6 complete (pipeline tested end-to-end at the function level)
- All modules importable and passing

**Work:**
- Task 12: `server.py` — **Step 0: SDK smoke test** (verify MCPServer constructor, tool decorator, lifespan compile). Then full server wiring: lifespan context, `process_turn` tool registration, stdio transport.
- Task 13: Integration test — full Call 1 pipeline through the MCP server interface. `TurnRequest` in, `TurnPacket` out with entities, path decisions, template candidates, budget, and stored `TurnRequest` for Call 2.
- Task 14: `ruff check`, `ruff format`, type annotation review, docstring completeness, final cleanup.

**Subagent strategy:** Sequential. Task 12 Step 0 must pass before wiring. Task 13 depends on 12. Task 14 is the final pass.

**Exit criteria:**
- SDK smoke test passes (Step 0) — MCPServer constructs, tool decorates, lifespan compiles
- Server starts and accepts MCP tool calls
- Integration test: realistic `TurnRequest` produces valid `TurnPacket` with all expected fields
- `ruff check` and `ruff format` pass with zero issues
- `uv run pytest tests/ -v` — all pass across all test files, zero unexpected skips (any skips/xfails must be listed in Open Issues with an owner session)
- No `TODO` or `FIXME` in production code (move to Open Issues if unresolved)
- All Open Issues from prior sessions reviewed and either resolved or accepted
- One commit per task

**Risks:** Medium-High. SDK smoke test (Step 0) may reveal API changes since the source was read. Integration test may expose cross-module interaction bugs not caught by unit tests. This is the first Python MCP server in the repo — patterns set precedent.

**Artifacts created:**
- `packages/context-injection/context_injection/server.py`
- `packages/context-injection/tests/test_server.py`
- `packages/context-injection/tests/test_integration.py`

**Artifacts modified:**
- `.mcp.json` (Task 12 Step 3: register context-injection server)
- All prior modules (cleanup fixes from Task 14)
- This progress tracker (final status update)

## Task Status

| Task | Module | Status | Tests | Notes |
|------|--------|--------|-------|-------|
| 1 | Scaffolding | Pending | — | |
| 2 | enums.py | Pending | — | |
| 3 | types.py (base + input) | Pending | — | |
| 4 | types.py (output) | Pending | — | |
| 5 | types.py (unions) | Pending | — | Highest risk: callable discriminator, strict mode |
| 6 | canonical.py | Pending | — | Parallel with Task 8 |
| 7 | state.py | Pending | — | HMAC, store, AppContext |
| 8 | paths.py | Pending | — | Parallel with Task 6 |
| 9 | entities.py | Pending | — | High risk: no concrete regex patterns in plan |
| 10 | templates.py | Pending | — | Structural plan only |
| 11 | pipeline.py | Pending | — | Structural plan only |
| 12 | server.py | Pending | — | SDK smoke test (Step 0) + full wiring |
| 13 | Integration test | Pending | — | Full Call 1 pipeline end-to-end |
| 14 | Cleanup | Pending | — | Lint, type-check, final polish |

## Dependency Graph

```
Task 1: Scaffolding
  └─ Task 2: enums.py
       └─ Task 3: types.py (base + input)
            └─ Task 4: types.py (output)
                 └─ Task 5: types.py (unions)
                      ├─ Task 6: canonical.py ──┐
                      │    └─ Task 7: state.py   │ parallel (S4)
                      │         └─ Task 9: entities.py
                      ├─ Task 8: paths.py ───────┘
                      └─ Task 10: templates.py (depends on 6, 7, 8, 9)
                           └─ Task 11: pipeline.py
                                └─ Task 12: server.py
                                     └─ Task 13: Integration test
                                          └─ Task 14: Cleanup
```

## Session Protocol

Each session:
1. Resume from prior handoff (`/resume`)
2. Read this progress tracker — start with **Carry-Forward** section
3. Read relevant task sections from the implementation plan
4. Implement using `superpowers:subagent-driven-development` where applicable
5. Run session-specific pytest command from exit criteria
6. Commit completed tasks (one commit per task or per logical group)
7. Update this tracker: Session Schedule status, Task Status columns, Carry-Forward bullets (add/resolve), Deviations (if any)
8. Create handoff for next session

## Deviations from Plan

Record any implementation decisions that diverge from the plan. Every row must either add/update a Carry-Forward bullet or state "no carry-forward needed" in the Affected Tasks column.

| Session | Task | Deviation | Reason | Affected Tasks |
|---------|------|-----------|--------|----------------|
| — | — | — | — | — |

## Open Issues

Discovered during implementation. Items here should be resolved before S7 ends.

| Issue | Found In | Severity | Resolution |
|-------|----------|----------|------------|
| — | — | — | — |

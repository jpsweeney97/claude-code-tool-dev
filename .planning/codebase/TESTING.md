# Testing Patterns

**Analysis Date:** 2026-03-13

## Test Frameworks

**Python (all plugins):**
- Runner: `pytest>=8.0`
- Async extension: `pytest-asyncio>=0.24` (context-injection only)
- No coverage tool configured
- Config: `[tool.pytest.ini_options]` in each package's `pyproject.toml`

**TypeScript (claude-code-docs MCP server):**
- Runner: `vitest>=2.0`
- No separate assertion library — uses vitest built-ins
- Config: in `package.json` scripts

**Run Commands:**

Python (run from package directory or via uv workspace):
```bash
uv run pytest                                    # run all tests in current package
uv run --package context-injection pytest        # run from repo root
cd packages/plugins/handoff && uv run pytest     # package-local
```

TypeScript (must run from `packages/mcp-servers/claude-code-docs/`):
```bash
npm test              # vitest run (all tests)
INTEGRATION=1 npm test -- integration  # run integration tests against live network
```

## Test File Organization

**Python location:** `tests/` subdirectory within each package, at the same level as `scripts/` or `context_injection/`
- `packages/plugins/handoff/tests/`
- `packages/plugins/ticket/tests/`
- `packages/plugins/context-metrics/tests/`
- `packages/plugins/cross-model/context-injection/tests/`
- `packages/plugins/cross-model/tests/`
- `tests/` at repo root (for cross-model scripts not in a package)

**TypeScript location:** `tests/` alongside `src/` in `packages/mcp-servers/claude-code-docs/tests/`

**Naming:**
- Python: `test_<module>.py` — mirrors source 1:1
  - `context_injection/redact.py` → `tests/test_redact.py`
  - `scripts/distill.py` → `tests/test_distill.py`
- TypeScript: `<module>.test.ts` — mirrors source 1:1
  - `src/bm25.ts` → `tests/bm25.test.ts`
  - `src/cache.ts` → `tests/cache.test.ts`
  - Exception: `cache.mock.test.ts` for variant with filesystem mocking

**Special test files (TypeScript):**
- `golden-queries.test.ts` — search quality validation (34 queries, 26 categories) using inline mock corpus
- `integration.test.ts` — live network test, skipped by default, enabled with `INTEGRATION=1`
- `corpus-validation.test.ts` — validates chunking invariants, skipped unless content cache present

## Test Structure

**Python — class-based (primary pattern):**
```python
class TestRedactionStats:
    def test_construction(self) -> None:
        stats = RedactionStats(format_redactions=2, token_redactions=3)
        assert stats.format_redactions == 2

    def test_frozen(self) -> None:
        stats = RedactionStats(format_redactions=0, token_redactions=0)
        with pytest.raises(AttributeError):
            stats.format_redactions = 1
```

**Python — function-based (used in root `tests/` and some packages):**
```python
def test_validate_passes_on_current_codebase() -> None:
    """validate() returns no errors against the actual codebase."""
    errors = MODULE.validate(repo_root=REPO_ROOT)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )
```

**TypeScript — describe/it (vitest):**
```typescript
describe('buildBM25Index', () => {
  it('handles empty chunks array', () => {
    const index = buildBM25Index([]);
    expect(index.chunks).toEqual([]);
    expect(index.avgDocLength).toBe(0);
  });
});
```

**Nested describes (TypeScript):**
```typescript
describe('chunkFile', () => {
  describe('whole file chunks', () => {
    it('keeps small file as single chunk', () => { ... });
  });
  describe('splitting at H2', () => {
    it('splits large file at H2 boundaries', () => { ... });
  });
});
```

**Setup/Teardown patterns:**
- Python: `setup_method` / `teardown_method` on class (used in context-metrics integration tests)
- TypeScript: `beforeEach` / `afterEach` at describe or suite level
- Python fixtures: `conftest.py` defines shared fixtures; inner-class `@pytest.fixture` for suite-scoped setup

## Mocking

**Python:**
- `unittest.mock.patch` — used universally across all packages
- `unittest.mock.MagicMock` and `Mock` for object mocks
- `pytest.MonkeyPatch` (via `monkeypatch` fixture) — preferred for attribute/method patching when reversibility matters

```python
# patch as context manager
with patch(
    "context_injection.server.subprocess.run",
    side_effect=subprocess.TimeoutExpired("git", 10),
):
    result = _load_git_files("/nonexistent/path")
    assert result == set()

# monkeypatch for attribute replacement
monkeypatch.setattr(Path, "read_text", patched_read_text)

# monkeypatch for time-sensitive tests
monkeypatch.setattr(defer_module, "datetime", FixedDateTime)
```

**TypeScript (vitest):**
- `vi.mock()` for module-level mocking — used in `cache.mock.test.ts` for `node:fs/promises`
- `vi.fn()` for function mocks with `.mockResolvedValue()`, `.mockReturnValue()`, `.mockRejectedValueOnce()`
- `vi.spyOn()` for observing existing functions (`console.warn`)
- `vi.restoreAllMocks()` in `afterEach` — always called after spies/mocks
- `vi.resetModules()` in `afterEach` for module-level mocks (required when `vi.mock` is used)

```typescript
beforeEach(async () => {
  cache = await import('../src/cache.js');
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.resetModules();
});

// Spy pattern
const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
vi.mocked(fs.unlink).mockImplementation(async (target) => { ... });
```

**What to Mock:**
- External I/O: filesystem, HTTP, subprocess calls
- Time-sensitive logic: `datetime` module, `time.time()`
- Platform checks: `subprocess.run` return values for version checks
- FastMCP internal APIs when testing server tool registration

**What NOT to Mock:**
- Business logic under test — test the real implementation
- Pydantic model construction — test real validation behavior
- `tmp_path` filesystem — use pytest's built-in temp directory

## Fixtures and Factories

**Python conftest fixtures:**
```python
# context-metrics conftest.py — fixture-per-file-type pattern
@pytest.fixture
def normal_session(fixtures_dir: Path) -> Path:
    return fixtures_dir / "normal_session.jsonl"

@pytest.fixture
def malformed_session(fixtures_dir: Path) -> Path:
    return fixtures_dir / "malformed.jsonl"
```

**Python builder functions (ticket plugin):**
```python
# tests/support/builders.py — keyword-only params with defaults
def make_ticket(
    tickets_dir: Path,
    filename: str,
    *,
    id: str = "T-20260302-01",
    status: str = "open",
    priority: str = "high",
    ...
) -> Path:
    """Create a v1.0 format ticket file for testing."""
    ...
```

**Python helper constructors in test files:**
```python
# Pattern: _make_<type>() as module-level private helpers
def _make_turn_request(**overrides: Any) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible defaults."""
    defaults = { "schema_version": SCHEMA_VERSION, "turn_number": 1, ... }
    defaults.update(overrides)
    return TurnRequest(**defaults)

def _make_ctx(git_files: set[str] | None = None) -> AppContext:
    return AppContext.create(repo_root="/tmp/repo", git_files=git_files or set())
```

**TypeScript factory helpers:**
```typescript
// Pattern: make<Type>() or build<Type>() at module level
function makeChunk(id: string, content: string, tokens: string[], heading?: string): Chunk { ... }
function makeDeps(overrides: Partial<ServerStateDeps> = {}): ServerStateDeps { ... }
function makeMockIndex(chunkCount = 3): BM25Index { ... }
```

**Fixture files:**
- `packages/plugins/context-metrics/tests/fixtures/` — JSONL fixture files for session data
- TypeScript `golden-queries.test.ts` uses inline string constants for mock corpus content

## Parametrize

`pytest.mark.parametrize` is used heavily in context-injection tests:

```python
@pytest.mark.parametrize(
    "path",
    [".env", ".env.local", ".env.production", "src/.env", "/repo/.env.staging"],
)
def test_dotenv_by_basename(self, path: str) -> None:
    assert classify_path(path) == FileKind.CONFIG_ENV

@pytest.mark.parametrize(
    "path, expected",
    [
        ("settings.json", FileKind.CONFIG_JSON),
        ("config.yaml", FileKind.CONFIG_YAML),
        ("pyproject.toml", FileKind.CONFIG_TOML),
    ],
)
def test_config_formats(self, path: str, expected: FileKind) -> None:
    assert classify_path(path) == expected
```

## Coverage

**Requirements:** No coverage target enforced — no `pytest-cov` in any package's dev deps

**View Coverage:** Not configured

**Approximate counts by package:**
- `context-injection`: ~991 tests
- `claude-code-docs` MCP server: ~397 tests
- `cross-model` plugin: tests in `packages/plugins/cross-model/tests/`
- `handoff`: ~10 test files across `tests/`
- `ticket`: ~20 test files across `tests/`
- `context-metrics`: ~8 test files across `tests/`
- Repo root `tests/`: ~10 test files for cross-package scripts

## Test Types

**Unit Tests:**
- Primary type across all packages
- Test individual modules in isolation
- One test file per source file (strict 1:1 mirroring)
- Classes group related tests for one unit under test

**Integration Tests (Python):**
- `TestEndToEnd` classes — spin up real sidecar server with `threading.Thread`, make real HTTP calls
- Use `setup_method` / `teardown_method` for server lifecycle
- Example: `packages/plugins/context-metrics/tests/test_integration.py`, `test_hooks.py`

**Integration Tests (TypeScript):**
- `tests/integration.test.ts` — skipped by default, requires `INTEGRATION=1` env var
- `tests/corpus-validation.test.ts` — skipped unless content cache exists on disk

**Contract Sync Tests:**
- `tests/test_consultation_contract_sync.py` — validates SKILL.md against contract spec
- Tests parse actual repo files and verify structural invariants (section counts, governance rule counts, event type references)

**Script-level Tests:**
- Root `tests/` uses `importlib.util.spec_from_file_location` to load standalone scripts not in packages
- Example: `tests/test_stats_common.py` loads `packages/plugins/cross-model/scripts/stats_common.py` directly

## Conditional/Skipped Tests

**TypeScript — `it.skipIf` and `describe.skipIf`:**
```typescript
it.skipIf(!process.env.INTEGRATION)('fetches real docs', async () => { ... }, 60000);

describe.skipIf(!cacheExists)('corpus validation', () => { ... });
```

**Python — no `pytest.mark.skip` or `xfail` in current codebase.**
- Historical: `xfail_inventory_d4a.md` documents 35 tests that were temporarily xfailed during schema migration (all resolved)
- Pattern documented for future migrations: mark with `xfail(strict=True)` during migration, resolve in follow-up task

## Common Patterns

**Error path testing (Python):**
```python
def test_frozen(self) -> None:
    r = RedactedText(text="x", stats=RedactionStats(0, 0))
    with pytest.raises(AttributeError):
        r.text = "y"

def test_permission_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(OSError, match="cannot read") as exc_info:
        MODULE.read_file(target)
    assert isinstance(exc_info.value.__cause__, PermissionError)
```

**Error path testing (TypeScript):**
```typescript
await expect(cache.writeCache(cachePath, 'content')).rejects.toThrow(
  /Timed out waiting for cache lock/
);
```

**Async testing (TypeScript):**
```typescript
it('loads and returns index on first call', async () => {
  const deps = makeDeps();
  const state = new ServerState(deps);
  const index = await state.ensureIndex();
  expect(index).toBeDefined();
});
```

**Shared assertion helpers (Python):**
```python
# tests/redaction_harness.py
def assert_redact_result(outcome, *, expected_text=None, expected_count=None) -> FormatRedactResult:
    assert isinstance(outcome, FormatRedactResult), f"Expected FormatRedactResult, got {type(outcome).__name__}"
    if expected_text is not None:
        assert outcome.text == expected_text, f"Text mismatch:\n  expected: {expected_text!r}\n  got:      {outcome.text!r}"
    return outcome
```

**Security/footgun tests:**
- Tests named `test_footgun_*` or security-labeled verify that sensitive content is denied at the correct pipeline layer
- These tests must never be weakened — they are the specification of the security boundary

---

*Testing analysis: 2026-03-13*

# Coding Conventions

**Analysis Date:** 2026-03-13

## Naming Patterns

**Files:**
- Python source files: `snake_case.py` — e.g., `redact_formats.py`, `ticket_parsing.py`, `pipeline.py`
- TypeScript source files: `kebab-case.ts` — e.g., `bm25.ts`, `fence-tracker.ts`, `chunk-helpers.ts`
- Test files (Python): `test_<module>.py` — mirrors source 1:1 (e.g., `redact.py` → `test_redact.py`)
- Test files (TypeScript): `<module>.test.ts` — mirrors source 1:1 (e.g., `cache.ts` → `cache.test.ts`)
- Builder/harness files: descriptive names in `tests/support/` (`builders.py`) or as `<name>_harness.py`

**Functions:**
- Python: `snake_case` — e.g., `parse_frontmatter`, `check_path_compile_time`, `compute_budget`
- TypeScript: `camelCase` — e.g., `buildBM25Index`, `extractSnippet`, `headingBoostMultiplier`
- Private/internal functions: prefix `_` in both languages — e.g., `_make_turn_request`, `_check_git_available`, `_make_budget`

**Variables:**
- Python: `snake_case` throughout
- TypeScript: `camelCase` for variables, `SCREAMING_SNAKE_CASE` for module-level constants (e.g., `BM25_CONFIG`, `METADATA_HEADER_RE`)

**Types/Classes:**
- Python: `PascalCase` for classes and dataclasses — e.g., `RedactionStats`, `TurnRequest`, `HandoffFile`
- Python: `Literal` type aliases use `PascalCase` suffix `Literal` — e.g., `SchemaVersionLiteral`
- TypeScript: `PascalCase` for interfaces and classes — e.g., `BM25Index`, `ServerState`, `FetchTimeoutError`
- TypeScript: `camelCase` for exported const configs — e.g., `BM25_CONFIG`

**Enums:**
- Python: `StrEnum` subclasses with `SCREAMING_SNAKE_CASE` members — e.g., `SuppressionReason.PEM_PRIVATE_KEY_DETECTED`, `FileKind.CONFIG_ENV`
- Values are always lowercase strings matching semantic intent

**Constants:**
- Python module-level constants: `SCREAMING_SNAKE_CASE` — e.g., `MAX_CONVERSATION_TURNS`, `MAX_CHECKPOINT_PAYLOAD_BYTES`, `DENYLIST_DIRS`
- TypeScript: `SCREAMING_SNAKE_CASE` at module level — e.g., `METADATA_HEADER_RE`, `_BINARY_CHECK_SIZE` (Python-style private prefix in TS too)
- Inline constants get doc comments explaining their value — e.g., `_BINARY_CHECK_SIZE: int = 8192\n"""Check first 8KB..."""`

## Code Style

**Formatting:**
- Python: `ruff format` (configured in `context-injection` package; `ruff>=0.8` in dev deps)
- TypeScript: `tsc` strict mode; no separate formatter configured
- All Python files use `from __future__ import annotations` at the top of source files (not test files — pattern is inconsistent)

**Linting:**
- Python: `ruff check` — only context-injection package has ruff in dev deps; run as `uv run ruff check context_injection/ tests/`
- TypeScript: `npx tsc --noEmit` for type checking
- No ESLint or Prettier detected

**Type annotations:**
- Python: All public function signatures annotated with return types — `-> None`, `-> str`, `-> list[Issue]`, `-> dict[str, Any]`
- Python: `from typing import` used for `Literal`, `Any`, `NotRequired`, `TypedDict`, `overload`
- TypeScript: `strict: true` in base tsconfig; all parameters and return types annotated explicitly

## Import Organization

**Python order (conventional):**
1. `from __future__ import annotations` (source files only, when present)
2. Standard library (`import os`, `from pathlib import Path`, `from dataclasses import dataclass`)
3. Third-party (`import pytest`, `from pydantic import ...`)
4. Local package (`from context_injection.classify import FileKind`)

**TypeScript order:**
1. `vitest` imports in test files (`import { describe, it, expect, vi } from 'vitest'`)
2. Node stdlib (`import * as path from 'path'`, `import * as os from 'os'`)
3. Local source imports using `.js` extensions (`from '../src/bm25.js'`)

**Path Aliases:**
- None detected — TypeScript uses relative paths with `.js` extensions (NodeNext module resolution requires this)

## Error Handling

**Python patterns:**
- Specific exception types over `Exception` — catch `OSError`, `UnicodeDecodeError`, `json.JSONDecodeError` separately
- Error messages follow the format `"{operation} failed: {reason}. Got: {input!r:.100}"` — e.g., `"normalize_input_path failed: empty path. Got: {raw!r:.100}"`
- Custom exception classes extend `Exception` with structured fields — e.g., `CheckpointError` with `code` and `message`; `DelegationError` with operation-context messages
- Fail-closed pattern for security-critical paths: empty set, null result, or suppressed output rather than raising
- Exception chaining with `raise X from exc` for wrapped errors

**TypeScript patterns:**
- Custom error classes extend `Error` — e.g., `FetchTimeoutError`, `FetchHttpError`, `ContentValidationError`
- `console.warn` for recoverable errors (lock cleanup failures, JSON parse warnings)
- `throw` for unrecoverable errors; callers catch specific error types

## Logging

**Python:**
- Standard library `logging` module; no third-party logger
- Module-level logger: `logger = logging.getLogger(__name__)` in production code
- Log format: `logger.info("operation: field=%s, other=%s", val1, val2)` — structured key=value in message string
- Levels used: `debug` for file-level skips, `info` for operation outcomes, `warning` for recoverable errors, `exception` for caught exceptions that should propagate context

**TypeScript:**
- `console.warn` for warnings (lock cleanup, stale cache)
- No structured logging framework

## Comments

**Module docstrings:**
- All Python modules have a module-level docstring describing purpose, layers, and sometimes referencing the contract doc
- Docstrings list the public API: e.g., `"""Two exported check functions:\n- check_path_compile_time(): ...\n- check_path_runtime(): ..."""`

**Inline comments:**
- Constants with non-obvious values get inline docstrings directly below: `_BINARY_CHECK_SIZE: int = 8192\n"""Check first 8KB for NUL bytes..."""`
- Security decisions are commented explicitly — e.g., `"""Do NOT add slash-containing patterns..."""`
- TypeScript test files with skip guards include comments explaining why the test is skipped and when to unskip

**When NOT to comment:**
- Straightforward data class fields — no comment needed
- Test method bodies — the test name is the documentation

## Function Design

**Python:**
- Functions return concrete types or `None` — no implicit `None` returns on failure paths
- Factory/constructor helpers: `_make_<type>()` or `make_<type>()` pattern for both tests and production
- Keyword-only parameters enforced with `*` for clarity when 3+ params — e.g., `make_ticket(path, filename, *, id=..., status=...)`
- Dataclasses used for value objects; `frozen=True` for immutable protocol types

**TypeScript:**
- Functions exported individually (no barrel `index.ts` aggregating all exports)
- Factory functions: `make<Type>()` or `build<Type>()` pattern — e.g., `makeDeps()`, `makeChunk()`, `buildBM25Index()`

## Module Design

**Python exports:**
- No `__all__` declarations; explicit imports used by callers
- Re-exports acceptable in `types.py` for test convenience (with `_ = ReExportedName` to suppress F401)
- `TypedDict` used for dict-shaped data flowing across module boundaries

**TypeScript exports:**
- Named exports throughout; no default exports
- Types/interfaces exported with `export interface` and `export type`
- No barrel files — each module exports its own symbols directly

## Pydantic Usage (context-injection)

- All protocol models inherit from `ProtocolModel` base class
- Base class enforces: `extra="forbid"`, `strict=True`, `frozen=True`
- `model_dump(mode="json")` workaround used for FastMCP SDK serialization (discriminated unions)
- Zod used for TypeScript validation in `claude-code-docs` MCP server

---

*Convention analysis: 2026-03-13*

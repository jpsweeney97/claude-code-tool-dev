# CCDI Inventory Build Pipeline

**Date:** 2026-03-24
**Status:** Approved
**Scope:** Wire up the compiled topic inventory build so the CCDI pre-dispatch gate can classify dialogue questions.

## Problem

The CCDI pipeline code is fully implemented and deployed (classifier, packets, registry, dialogue-turn scheduling, ~991 context-injection tests). But the compiled topic inventory file — the input to the classifier — doesn't exist because the build pipeline isn't wired up.

Two gaps:

1. **MCP server not rebuilt.** `dump-index-metadata.ts` source exists and registers a `dump_index_metadata` tool, but `dist/` doesn't contain the compiled output. The running MCP server serves an older build.
2. **No inventory build pipeline.** `build_inventory()` in Python works, but the CLI `__main__` is a stub ("MCP client integration not yet implemented"). Nobody calls `build_inventory()` in production.

Additionally, a **path mismatch** exists: `build_inventory.py` defaults to `data/compiled_inventory.json`, but the `/dialogue` skill and ccdi-gatherer agent reference `data/topic_inventory.json`.

## Architecture Decision

**When:** Build at deploy/promote time (primary) + on-demand command (fallback).

**Bridge:** Standalone Node.js metadata extraction script → Python inventory build. Keep MCP transport out of Python. The boundary is a JSON blob on stdout.

**Rationale (from Codex consultation `019d1e2c`):**
- The pre-dispatch gate treats the inventory as a local file precondition, not a runtime query. Deploy-time build is the natural fit.
- The existing `ccdi_inventory_refresh.py` hook is explicitly fail-open — it's a freshness accelerator, not a correctness path.
- Lazy build on first `/dialogue` pushes build failures into user requests. Session-start build adds latency without clear benefit.
- Standalone Node.js script keeps the cross-language bridge deterministic and debuggable. No Python MCP client needed.

## Deliverables

### 1. Node.js Metadata Dumper

**Location:** `packages/mcp-servers/claude-code-docs/src/scripts/dump-metadata.ts`

Standalone script that:
- Imports `loadFromOfficial` from the loader, `chunkFile` from the chunker, `buildBM25Index` from the BM25 module, `buildMetadataResponse` from the dump-index-metadata module
- Pipeline: `loadFromOfficial()` → `chunkFile()` per file → `buildBM25Index(chunks)` → `buildMetadataResponse(index, contentHash)`
- Leverages the content cache (no redundant fetch when cache is warm). The BM25 index is rebuilt in-memory each run — the serialized index cache is managed by `ServerState` and not used by standalone scripts.
- Writes `DumpIndexMetadataOutput` JSON to stdout
- Exits 0 on success, non-zero with diagnostic to stderr on failure

Compiled by `tsc` alongside the rest of the package. Appears in `dist/scripts/dump-metadata.js`. Do NOT use `tsx` — the package has no `tsx` dependency and uses plain `tsc` builds.

**tsconfig:** The current `tsconfig.json` has `include: ["src"]`, which recursively covers all subdirectories including `src/scripts/`. No tsconfig change needed. With `rootDir: "src"` and `outDir: "dist"`, the file compiles to `dist/scripts/dump-metadata.js` preserving the subdirectory.

### 2. Wire `build_inventory.py` CLI

**Location:** `packages/plugins/cross-model/scripts/ccdi/build_inventory.py` (existing file, replace `__main__` stub)

Replace the stub `__main__` block with:

```
--metadata-file <path>   # Required. Path to dump-metadata JSON output.
--overlay <path>         # Optional. Default: data/topic_overlay.json
--output <path>          # Optional. Default: data/topic_inventory.json
--config <path>          # Optional. Path to config JSON.
--force                  # Optional. Force rebuild even if output exists.
```

Behavior:
1. Read metadata JSON from `--metadata-file`
2. Read overlay JSON from `--overlay` (if exists)
3. Call `build_inventory(metadata, overlay, config_path=config)`
4. Serialize `CompiledInventory` to JSON
5. Write to `--output` via temp file + `os.replace()` for atomicity
6. Exit 0 on success, non-zero with diagnostic on failure

**Path mismatch fix:** Change default `--output` from `data/compiled_inventory.json` to `data/topic_inventory.json`.

### 3. Python Orchestrator

**Location:** `packages/plugins/cross-model/scripts/build_ccdi_inventory.py` (new file)

Thin coordinator that runs the full build pipeline:

1. Resolve paths explicitly:
   - `mcp_server_dir`: `packages/mcp-servers/claude-code-docs/` (relative to repo root, resolved to absolute)
   - `plugin_dir`: `packages/plugins/cross-model/` (resolved to absolute)
2. Run `node dist/scripts/dump-metadata.js` with `cwd` set to `mcp_server_dir`
3. Read metadata JSON from stdout. Validate shape: check for `categories` key, non-empty list.
4. Read overlay JSON from `data/topic_overlay.json` (relative to `plugin_dir`). Pass `None` if file doesn't exist.
5. Call `build_inventory(metadata, overlay)` in-process (import from `scripts.ccdi.build_inventory`)
6. Serialize and write `data/topic_inventory.json` via temp file + `os.replace()`
7. Print success summary: topic count, category count, `docs_epoch`

**Error handling:**
- Node subprocess exits non-zero → fail with: `"metadata extraction failed: {stderr}"`
- Empty or malformed JSON from Node → fail with: `"metadata validation failed: {reason}"`
- `build_inventory()` raises → fail with: `"inventory build failed: {exception}"`
- Output directory doesn't exist → create it

**Invocation:**
```bash
# Primary (from cross-model package directory):
cd packages/plugins/cross-model
uv run python -m scripts.build_ccdi_inventory

# From repo root (requires cross-model package on sys.path via uv workspace):
uv run --package cross-model-plugin python -m scripts.build_ccdi_inventory
```

The orchestrator resolves the MCP server path relative to the repo root (via `git rev-parse --show-toplevel` or a `__file__`-relative calculation), not relative to cwd.

### 4. Promote Integration

**Location:** `scripts/promote` (existing file)

After promoting the cross-model plugin, call the orchestrator:
```bash
uv run scripts/build_ccdi_inventory.py
```

This runs in the deployed plugin directory, so the orchestrator must resolve the MCP server path relative to the repo root, not relative to the plugin.

### 5. Rebuild MCP Server

Run `npm run build` in `packages/mcp-servers/claude-code-docs/` to compile:
- `src/dump-index-metadata.ts` → `dist/dump-index-metadata.js` (makes the MCP tool available)
- `src/scripts/dump-metadata.ts` → `dist/scripts/dump-metadata.js` (the standalone metadata dumper)

### 6. Update `ccdi_inventory_refresh.py` Hook

**Location:** `packages/plugins/cross-model/hooks/ccdi_inventory_refresh.py`

The hook's `_default_build_fn` currently calls:
```python
[sys.executable, "-m", "scripts.ccdi.build_inventory", "--force"]
```

This will fail after implementation because the new `build_inventory.py` CLI requires `--metadata-file`, which the hook doesn't provide. Update `_default_build_fn` to call the orchestrator instead:
```python
[sys.executable, "-m", "scripts.build_ccdi_inventory"]
```

The orchestrator handles metadata extraction internally, so the hook just triggers a full rebuild. The hook remains fail-open — orchestrator failures are caught by the existing exception handling.

### 7. Existing Infrastructure (Unchanged)

| Component | Status | Notes |
|-----------|--------|-------|
| `classify` CLI subcommand | Works once inventory file exists | Pre-dispatch gate consumer |
| `build-packet` CLI subcommand | Works | Packet builder, no inventory dependency |
| ccdi-gatherer agent | Works once inventory file exists | Receives `inventory_path`, pins and reads it |

## Data Flow

```
code.claude.com/docs/llms-full.txt
    │
    ▼ loadFromOfficial() (fetch + content cache)
MarkdownFile[] + contentHash
    │
    ▼ chunkFile() per file
Chunk[]
    │
    ▼ buildBM25Index(chunks)
BM25Index (in-memory, rebuilt each run)
    │
    ▼ buildMetadataResponse(index, contentHash)
DumpIndexMetadataOutput JSON (stdout)
    │                           data/topic_overlay.json
    │                                    │
    ▼                                    ▼
    build_inventory(metadata, overlay)
    │
    ▼ serialize + atomic write
data/topic_inventory.json
    │
    ├──▶ classify (pre-dispatch gate)
    └──▶ ccdi-gatherer agent (pins snapshot)
```

## Invariants

1. **Atomic writes.** The inventory file is always written via temp file + `os.replace()`. The classifier never reads a half-written file.
2. **Explicit paths.** The orchestrator resolves all paths to absolute before subprocess calls. No reliance on working directory.
3. **Fail-fast.** Every step validates its input and fails with an actionable message. No silent fallback to stale data.
4. **Content cache reuse.** The Node.js metadata dumper reuses the MCP server's content cache (fetched docs). A warm content cache means zero network I/O. The BM25 index is rebuilt in-memory each run (the serialized index cache is managed by `ServerState`, not standalone scripts).

## Testing

| Test | Scope |
|------|-------|
| `dump-metadata` outputs valid `DumpIndexMetadataOutput` | Node.js (extend existing `dump-index-metadata.test.ts`) |
| `build_inventory.py` CLI reads metadata file and produces valid inventory | Python (extend existing `build_inventory` tests) |
| Orchestrator runs end-to-end with a fixture metadata file | Python integration test |
| Path mismatch regression: verify `/dialogue` SKILL.md path matches Python default | Grep assertion |
| Atomic write: verify no partial file on build failure | Python unit test |

## Open Questions

None. All design decisions resolved.

## Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Build timing | Deploy-time (A) + on-demand (D) | Pre-dispatch gate expects local file. Zero user-facing latency. |
| Cross-language bridge | Standalone Node.js script (option 2) | Deterministic, debuggable. No Python MCP client needed. |
| Orchestrator language | Python (Approach 2) | Fits `uv run scripts/<name>` convention. In-process `build_inventory()` call. |
| Node runner execution | Compiled JS via `tsc` | Package uses `tsc`, no `tsx` dependency. Runner under `src/scripts/` compiles with everything else. |
| Canonical filename | `topic_inventory.json` | Matches skill references (less churn than updating skills). |
| Script location (Node) | `src/scripts/dump-metadata.ts` in MCP server package | Close to source, imports directly, tested alongside server. |
| Script location (Python) | `scripts/build_ccdi_inventory.py` in cross-model plugin | Close to consumer, fits existing script conventions. |

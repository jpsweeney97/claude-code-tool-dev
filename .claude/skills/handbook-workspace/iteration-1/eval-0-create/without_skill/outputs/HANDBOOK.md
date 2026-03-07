# Context Injection MCP Server — Operational Handbook

**Package:** `context-injection` v0.2.0
**Location (vendored):** `packages/plugins/cross-model/context-injection/`
**Location (source):** `packages/context-injection/`
**Schema version:** `0.2.0` (exact-match semantics, no semver compatibility)

---

## 1. What This System Does

The context injection MCP server provides mid-conversation evidence gathering for the codex-dialogue agent. When Codex makes a factual claim about a codebase — for example, that a particular file uses YAML configuration — the server lets the agent read that file and verify the claim in real time, rather than relying entirely on its initial briefing.

It exposes two MCP tools:

- `process_turn` (Call 1): Analyzes the agent's current conversational turn. Extracts code entities (file paths, symbols) from claims, checks whether those files are safe to read, generates signed scout options, and produces a validated ledger entry plus a conversation action recommendation.
- `execute_scout` (Call 2): Executes one of the scout options produced by Call 1. Reads a file or runs a grep, applies the redaction pipeline, and returns evidence.

The system sits in the middle of the cross-model collaboration stack:

```
Codex Integration (MCP tools: codex, codex-reply)
  |
Context Injection (this server: process_turn, execute_scout)
  |
Cross-Model Learning (design complete, not implemented)
```

**Primary consumer:** the `codex-dialogue` agent at `packages/plugins/cross-model/agents/codex-dialogue.md`, which runs a 7-step scouting loop per turn.

---

## 2. Prerequisites

Before starting the server, verify these are available on the PATH:

| Dependency | Role | Failure mode |
|---|---|---|
| `git` | Populates tracked-file allowlist at startup | Startup gate: server refuses to start |
| `rg` (ripgrep) | Executes grep scouts | Call 2 grep scouts return `status="timeout"` |
| Python >= 3.11 | Runtime | Server cannot start |

**Platform requirement:** POSIX only (macOS, Linux, WSL). The server checks `os.name == "posix"` at startup and raises `RuntimeError` if the check fails.

---

## 3. Installation and Startup

### Vendored copy (plugin context)

The vendored copy at `packages/plugins/cross-model/context-injection/` is managed by the cross-model plugin. Do not edit it directly — changes are overwritten by the build script. The plugin installs and manages the server process automatically when deployed via:

```bash
claude plugin marketplace update turbo-mode
claude plugin install cross-model@turbo-mode
```

### Source package (development and testing)

The source lives at `packages/context-injection/`. Use this for all development work and testing.

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection

# Install dependencies
uv sync

# Run the server (stdio transport, blocks)
python -m context_injection

# Or from repo root via uv workspace
uv run --package context-injection python -m context_injection
```

### Environment variables

| Variable | Default | Effect |
|---|---|---|
| `REPO_ROOT` | `os.getcwd()` | Repository root the server indexes and gates reads against. Set this explicitly when running from a directory that is not the repo root, or when serving multiple repositories. |

Example:

```bash
REPO_ROOT=/path/to/target/repo python -m context_injection
```

### Startup sequence

On start, the server runs three initialization steps before accepting calls:

1. **POSIX check** — rejects non-POSIX platforms immediately.
2. **Git availability check** — rejects if `git` is not on PATH.
3. **`git ls-files` load** — runs `git ls-files` in `REPO_ROOT` with a 10-second timeout and loads the result into the in-memory allowlist. If this fails for any reason (non-zero exit, timeout, missing git), the allowlist is set to empty — meaning all file read scouts will be denied. The server still starts; it just cannot read any files.

---

## 4. How the Two-Call Protocol Works

Every agent turn produces exactly one Call 1 and at most one Call 2.

### Call 1: `process_turn`

The agent sends a `TurnRequest` with:

- Conversational ledger state: `position`, `claims` (list of text + status + turn), `delta`, `tags`, `unresolved` items.
- A `focus` object containing identical copies of `claims` and `unresolved` (dual-claims guard, CC-PF-3 — mismatches are hard-rejected).
- Checkpoint fields: `state_checkpoint` and `checkpoint_id` (absent on turn 1, required on turn 2+).
- Conversation metadata: `schema_version`, `turn_number`, `conversation_id`, `posture`.

The server runs a 17-step pipeline and returns a `TurnPacketSuccess` containing:

- `entities`: extracted code entities (file paths, symbols, URLs) from claims and unresolved items.
- `path_decisions`: path safety check results for each file entity.
- `template_candidates`: ranked scout options the agent can execute.
- `budget`: evidence budget state (`evidence_count`, `evidence_remaining`, `scout_available`).
- `deduped`: entities skipped because they were already scouted in this conversation.
- `validated_entry`: the server-validated ledger entry with computed counters and quality label.
- `warnings`: soft validation warnings (delta disagreement, empty position, referential mismatches).
- `cumulative`: aggregate conversation state (total claims, reinforced, revised, conceded, unresolved).
- `action`: one of `continue_dialogue`, `closing_probe`, or `conclude`.
- `action_reason`: human-readable explanation of the action.
- `ledger_summary`: compact text summary of all turns, suitable for injection into a prompt.
- `state_checkpoint` / `checkpoint_id`: opaque state snapshot for the agent to store and return on the next turn.

If the pipeline fails, the server returns `TurnPacketError` with an `error.code` and `error.message`.

### Call 2: `execute_scout`

The agent sends a `ScoutRequest` with:

- `scout_option_id`: the ID of the scout option selected from Call 1's `template_candidates`.
- `scout_token`: the HMAC token attached to that option.
- `turn_request_ref`: the reference key for the Call 1 that produced the option (format: `{conversation_id}:{turn_number}`).

The server validates the HMAC token, marks the turn as used (one scout per turn), and executes either a file read or a ripgrep search. It returns a `ScoutResult` with status `success`, a failure code, or `invalid_request`.

**Call 2 is skipped entirely** when any of these are true:
- Call 1 returned `status="error"`
- `template_candidates` is empty
- `budget.scout_available` is false
- The selected template is a clarifier (clarifiers have `scout_options: []`)
- `action` is `"conclude"`

---

## 5. Key Components

### `server.py` — Entry point

Creates the FastMCP instance, registers the two tools, runs the startup gates, and manages per-process `AppContext` via the lifespan context manager. Transport: stdio (blocking, long-running process).

### `pipeline.py` — Call 1 orchestration

The 17-step `process_turn` pipeline. Each step is labeled with its contract step number. Hard errors (schema mismatch, dual-claims violation, turn cap exceeded, checkpoint errors, ledger hard rejects) short-circuit and return `TurnPacketError`. All other errors are caught at the top level and returned as `internal_error`.

Key constant: `MAX_CONVERSATION_TURNS = 15`. The pipeline rejects Call 1 once a conversation reaches 15 entries. This is enforced as strictly less than `MAX_ENTRIES_BEFORE_COMPACT = 16`, verified at import time.

### `execute.py` — Call 2 dispatch

Two execution pipelines, each following the same never-raises contract:

**Read pipeline** (`execute_read`):
1. Runtime path check (containment + denylist re-check + file existence)
2. Binary detection (NUL bytes in first 8 KB)
3. File read (UTF-8, with excerpt strategy: `first_n` or `centered` around a line number)
4. Classification (`classify_path` on the realpath, not the display path — prevents symlink bypass)
5. Redaction (format-specific then generic token scan)
6. Truncation (line cap then char cap)
7. Build success result

**Grep pipeline** (`execute_grep`):
1. Run ripgrep with `--fixed-strings --json --no-ignore --hidden --glob=!.git/`
2. Group matches by file
3. For each file: filter against git allowlist + denylist, read, build context ranges, redact per range
4. Truncate blocks (block-atomic: never splits a range mid-block)
5. Build success result

Zero matches from grep is a success, not a failure — absence of a symbol in a codebase is meaningful evidence.

### `state.py` — Per-process state and HMAC

`AppContext` holds everything that lives for the server's lifetime:

- `hmac_key`: 32-byte random key generated at startup. **Restarting the server invalidates all outstanding scout tokens** — any in-flight Call 2 after a restart returns `invalid_request`.
- `store`: bounded `OrderedDict` of up to 200 `TurnRequestRecord` objects, keyed by `turn_request_ref`. Oldest entry is evicted when capacity is exceeded.
- `git_files`: the set of tracked file paths loaded at startup.
- `conversations`: per-conversation `ConversationState`, up to 50 conversations (DD-3 guard).
- `entity_counter`: monotonic counter for entity IDs (`e_001`, `e_002`, ...) — resets on restart.

HMAC tokens are generated in `generate_token()` and verified in `verify_token()` using constant-time comparison. The token payload is canonical JSON (sorted keys, compact) of: `{v, conversation_id, turn_number, scout_option_id, spec}`.

**One scout per turn:** `consume_scout()` sets a used-bit on the `TurnRequestRecord`. Once any scout option from a turn is consumed, all others on that turn are blocked. This enforces the budget invariant: exactly one evidence item can be gathered per turn.

### `paths.py` — Path safety

Two check functions:

- `check_path_compile_time()` (Call 1): Full pipeline — normalize input, containment check, denylist check on both the normalized and resolved paths (catches symlinks), git ls-files gating, risk signal detection.
- `check_path_runtime()` (Call 2): Lightweight re-check — realpath, containment, denylist re-check, regular file check. Defense-in-depth: a file could change between Call 1 and Call 2.

Denied directories (any depth): `.git`, `.ssh`, `__pycache__`, `node_modules`, `.svn`, `.hg`, `.aws`, `.gnupg`, `.docker`, `.kube`, `.terraform`

Denied file patterns: `.env`, `.env.*` (with exceptions for `.env.example`, `.env.sample`, `.env.template`), `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, SSH key files, `.npmrc`, `.pypirc`, `.netrc`, `credentials.json`, `service-account*.json`, `*.tfstate`, `*.tfstate.backup`

Risk signals (flag the scout option but do not block): paths containing `secret`, `token`, or `credential`. When a scout option has `risk_signal=true`, the server halves read limits: 20 lines / 1000 chars instead of 40 lines / 2000 chars.

### `redact.py` / `redact_formats.py` — Redaction pipeline

Two-stage pipeline applied to every file excerpt before it leaves the server:

**Stage 1 (format-specific):** Routes by `FileKind` — ENV, INI/properties, JSON, YAML, TOML each have a dedicated redactor that identifies value fields and replaces secret-looking values with `[REDACTED:value]`.

**Stage 2 (generic token scan):** Runs on all files regardless of kind. Detects: JWTs, Bearer/Basic auth headers, API key prefixes (sk-, ghp_, AKIA, etc.), URL userinfo (password in URL), credential assignments (`password = somevalue`).

**Suppression (no output emitted):** Three conditions cause the entire excerpt to be suppressed:
- PEM private key block detected (`-----BEGIN ... PRIVATE KEY-----`)
- Config file with no registered redactor (fail-closed)
- Config redactor internal desync

Suppressed results still produce `ScoutResultSuccess` with `excerpt="[REDACTED:key_block]"` (or similar marker) and `redactions_applied=1`.

**Security invariant:** Over-redaction is always preferable to under-redaction. If in doubt, suppress.

### `entities.py` — Entity extraction

Ordered regex pipeline on claim and unresolved text (capped at 2000 chars):

1. URLs (`http://`, `https://`) → `file_path`
2. File locations (`:line`, `:line:col`, `#Lline`) → `file_loc`
3. File paths (containing `/`) → `file_path`
4. File names (known extension, no separator) → `file_name`
5. Dotted symbols (`a.b.c` with 2+ dots) → `symbol`
6. Structured errors (`SomeError:`) → `symbol`

Span tracking prevents overlapping extractions. Backtick-delimited text gets `confidence="high"`; strong patterns (path separator, URL, known extension) get `"medium"`; everything else gets `"low"`.

Entity types: Tier 1 (directly actionable: `file_loc`, `file_path`, `file_name`, `symbol`, `dir_path`, `env_var`, etc.) and Tier 2 (need clarification: `file_hint`, `symbol_hint`, `config_hint`).

### `templates.py` — Scout option synthesis

Matches entities to templates and generates HMAC-signed scout options. Decision tree:

1. Tier 2 entities and unresolved `file_name` → clarifier templates (no scout options, just a question + optional choices)
2. Hard gate (Step A): only Tier 1 MVP types (`file_loc`, `file_path`, `file_name`, `symbol`), `in_focus=True`, confidence `high` or `medium`
3. Path decision gating: only `status="allowed"` file entities proceed
4. Budget gate: no probes if `budget.scout_available` is false
5. Dedupe: skip already-scouted entity/template combinations
6. Ranking (Steps B+C): sort by anchor type (`file_loc` best, then `file_path`, `file_name`, `symbol`), then confidence

Output: `template_candidates` (ranked list for the agent) + `spec_registry` (internal map of `scout_option_id → ScoutOptionRecord` for Call 2 validation).

### `checkpoint.py` — State persistence

Checkpoints are opaque JSON strings the agent stores externally and sends back on each subsequent turn. This enables state recovery after a server restart.

Format: `StateCheckpoint` envelope (checkpoint_id, parent_checkpoint_id, format_version, payload, size) wrapping a JSON-serialized `ConversationState`.

Hard limit: 16 KB (`MAX_CHECKPOINT_PAYLOAD_BYTES`). Compaction triggers when entries exceed `MAX_ENTRIES_BEFORE_COMPACT = 16` (keeping the 8 most recent). Under normal operation this is unreachable because `MAX_CONVERSATION_TURNS = 15 < 16`.

Integrity checks on restore: payload size matches declared size, format version matches, payload `last_checkpoint_id` matches envelope `checkpoint_id`, payload `conversation_id` matches the requesting conversation (cross-conversation swap detection).

### `conversation.py` — Per-conversation state

`ConversationState` is immutable (Pydantic frozen model). All mutations return new instances via `model_copy(update={...})`. The pipeline commits state atomically by replacing `ctx.conversations[id]`.

Tracks: ledger entries, claim registry, evidence history, closing probe flag, last checkpoint ID, posture/phase tracking.

### `control.py` — Action computation

`compute_action()` determines what the agent should do next:

1. **Budget exhausted** → `conclude`
2. **Plateau** (last 2 entries both `STATIC` effective_delta in the current phase):
   - Closing probe not yet fired → `closing_probe`
   - Closing probe fired, no open unresolved → `conclude`
   - Closing probe fired, open unresolved → `continue_dialogue`
3. **Default** → `continue_dialogue`

Phase tracking: posture changes (`adversarial`, `collaborative`, `exploratory`, `evaluative`, `comparative`) reset the plateau window and `closing_probe_fired`, giving each phase its own opportunity to converge.

### `ledger.py` — Entry validation

Validates agent-provided ledger data and computes derived fields:

**Hard rejects** (raise `LedgerValidationError`): empty claims list, `turn_number < 1`, any claim with `turn < 1` or `turn > turn_number`.

**Soft warnings** (attached to response): empty position, agent-reported delta contradicts computed effective delta, referential claim (marked `reinforced`/`revised`/`conceded`) with no matching prior claim text.

**Computed fields:** `counters` (new/revised/conceded counts), `quality` (`substantive` if any non-reinforced activity, else `shallow`), `effective_delta` (`advancing` if new claims, `shifting` if revised/conceded, `static` otherwise).

---

## 6. Error Codes Reference

### TurnPacketError codes (Call 1)

| Code | Meaning |
|---|---|
| `invalid_schema_version` | `schema_version` field does not equal `"0.2.0"` |
| `ledger_hard_reject` | Empty claims, bad turn number, or dual-claims mismatch (`focus.claims != claims`) |
| `checkpoint_missing` | Turn > 1, server has no in-memory state, and no checkpoint payload provided |
| `checkpoint_invalid` | Checkpoint payload is corrupt, wrong format version, size mismatch, or cross-conversation swap |
| `checkpoint_stale` | Server has in-memory state but the agent's `checkpoint_id` does not match |
| `turn_cap_exceeded` | Conversation has reached `MAX_CONVERSATION_TURNS = 15` entries |
| `internal_error` | Unexpected exception in the pipeline |

### ScoutResult statuses (Call 2)

| Status | Type | Meaning |
|---|---|---|
| `success` | `ScoutResultSuccess` | Evidence gathered (may be empty for grep with 0 matches) |
| `not_found` | `ScoutResultFailure` | File does not exist at execution time |
| `denied` | `ScoutResultFailure` | Path failed runtime denylist or containment check |
| `binary` | `ScoutResultFailure` | File contains NUL bytes |
| `decode_error` | `ScoutResultFailure` | File is not valid UTF-8 |
| `timeout` | `ScoutResultFailure` | Ripgrep timed out, or `rg` is not on PATH |
| `invalid_request` | `ScoutResultInvalid` | HMAC validation failed, token replayed, or server restarted |

---

## 7. Running Tests

Tests live in the **source package only** (`packages/context-injection/tests/`). The vendored copy at `packages/plugins/cross-model/context-injection/` excludes tests.

```bash
# From source package
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection
uv run pytest                          # all 969 tests
uv run pytest tests/test_pipeline.py  # single module
uv run pytest -k footgun               # security (footgun) tests only

# From repo root via workspace
uv run --package context-injection pytest
```

Test file naming: `test_<module>.py`. Shared fixtures in `tests/conftest.py`.

**Footgun tests** (`test_footgun_*`): Verify which pipeline layer catches security violations (credential exposure, denylist bypass). Never weaken these tests, and verify their stated contract holds after any behavior change.

Lint:

```bash
cd packages/context-injection
uv run ruff check context_injection/ tests/
```

---

## 8. Failure Modes and Mitigation

### Server restart loses all in-memory state

Conversation state, HMAC keys, and the turn request store are all in-memory. After a restart:

- Call 1 on turn > 1: recovers via checkpoint if the agent sends `state_checkpoint` and `checkpoint_id`.
- Call 2 after restart: always returns `invalid_request` (tokens are signed with the old HMAC key). The agent must retry with a fresh Call 1.

**Mitigation:** The checkpoint mechanism is the primary recovery path. Agents should always store and forward the checkpoint fields.

### `git ls-files` fails at startup

If `git ls-files` times out or exits non-zero, the allowlist is set to the empty set. All file read scouts return `status="not_tracked"` from the compile-time path check (Call 1 still succeeds but produces no probe candidates), or `status="denied"` at runtime (Call 2). Grep scouts are unaffected by the allowlist at Call 1 but their results are filtered post-hoc.

**Mitigation:** Ensure the server starts from within a valid git repository, or set `REPO_ROOT` to a path inside one. Check server logs for the startup error.

### `rg` (ripgrep) not on PATH

Grep scouts return `ScoutResultFailure` with `status="timeout"` and `error_message="ripgrep (rg) not found on PATH"`. This is a mis-mapped status code (the closest available literal; no `dependency_error` variant exists in v0.2.0).

**Mitigation:** Install ripgrep (`brew install ripgrep` on macOS, `apt install ripgrep` on Linux) and ensure it is on the PATH where the server process runs.

### Checkpoint exceeds 16 KB

`serialize_checkpoint()` raises `ValueError` if the payload exceeds `MAX_CHECKPOINT_PAYLOAD_BYTES`. Compaction (`compact_ledger`) runs before serialization. Under normal operation this is unreachable because `MAX_CONVERSATION_TURNS (15) < MAX_ENTRIES_BEFORE_COMPACT (16)`. If you raise `MAX_CONVERSATION_TURNS` above 15, review the compaction invariant.

### Conversation limit reached

The server tracks at most 50 concurrent conversations (`CONVERSATION_GUARD_LIMIT`). A 51st unique `conversation_id` raises `ValueError` inside `get_or_create_conversation()`, which surfaces as `internal_error` in the TurnPacket. This limit prevents memory growth from leaked conversation IDs.

**Mitigation:** Each server process is scoped to a single plugin session. 50 concurrent in-flight conversations is far above normal usage. If this limit is hit, the server process should be restarted.

### Turn cap reached

Once a conversation reaches 15 entries, Call 1 returns `turn_cap_exceeded`. The agent should conclude the conversation.

### Store eviction loses a TurnRequestRecord

The turn request store holds at most 200 records, evicting oldest-first. If Call 2 is issued for a `turn_request_ref` that has been evicted, `consume_scout()` raises `ValueError` → `ScoutResultInvalid`. This is not expected in normal operation (200 records covers far more than one conversation) but can occur if many unique conversations are active simultaneously.

---

## 9. Security Design

The server is designed with a fail-closed security posture throughout.

**Path safety:** Two-layer check. Compile-time (Call 1) performs full validation including git tracking. Runtime (Call 2) re-validates containment, denylist, and file existence. A file deleted or symlink-swapped between calls is caught at runtime.

**HMAC tokens:** Scout specs are signed at Call 1 and validated at Call 2. The agent cannot modify the spec (resolved path, read strategy, grep pattern) between calls. The server ignores any agent-supplied paths in Call 2 — it reads only from the spec it signed.

**One-shot tokens:** The used-bit prevents token replay. One scout per turn, enforced unconditionally. The used-bit is only set after successful HMAC verification (not before), preventing a timing oracle.

**Redaction pipeline:** Runs before truncation, so redaction always operates on the full excerpt. PEM key detection is a hard suppression — no content emitted. Config files with no registered redactor are suppressed (fail-closed), not passed through.

**Symlink safety:** Classification uses `os.path.realpath`, not the display path, in both the read and grep pipelines. A symlink `docs/readme.md -> secret.key` is classified as `.key`, not `.md`.

**Input bounds:** Entity extraction caps input text at 2000 characters to bound regex execution time. Path inputs are NFC-normalized, NUL-rejected, absolute-path-rejected, and traversal-rejected before any filesystem operation.

---

## 10. Verification Procedure

Use these checks to confirm the server is working correctly.

### Startup verification

```bash
cd /path/to/repo
REPO_ROOT=$(pwd) python -m context_injection
# Server should start without errors and block on stdio
```

Server logs at `INFO` level on startup. A successful startup produces no output on stderr. Check logs for:
- `RuntimeError: context-injection requires POSIX` → wrong platform
- `RuntimeError: context-injection requires git. git not found on PATH` → install git
- `RuntimeError: git ls-files failed: ...` → not in a git repo; set `REPO_ROOT`

### Run the test suite

```bash
cd packages/context-injection
uv run pytest -x          # stop on first failure
```

All 969 tests should pass. Any failure is a regression.

### Verify the HMAC flow (manual)

A correct two-call sequence:
1. Call 1 with a valid `TurnRequest` returns `TurnPacketSuccess` with `template_candidates` containing `scout_options`.
2. Each `scout_option` has a `scout_token`. Pass one as-is to Call 2.
3. Call 2 returns `ScoutResultSuccess`.
4. Modifying any field in the `ScoutRequest` (or using a token from a different turn) returns `ScoutResultInvalid`.

### Verify checkpoint round-trip

1. Call 1 on turn 1: returns `state_checkpoint` and `checkpoint_id`.
2. Restart the server.
3. Call 1 on turn 2: send the checkpoint fields from step 1. Server should restore state and return success (not `checkpoint_missing`).

### Verify path denylist

Issue a Call 1 with a claim containing the text `.env`. The resulting `path_decisions` should include an entry with `status="denied"` and `deny_reason` citing the denylist pattern. No scout option should be generated for the denied entity.

### Verify redaction

Issue a Call 1 with a claim referencing a file that contains a credential pattern (e.g., `password = hunter2`). Call 2 should return `ScoutResultSuccess` with `redactions_applied >= 1` and the value replaced with `[REDACTED:value]` in the excerpt.

---

## 11. Sync and Promotion

### Syncing the vendored copy

The vendored copy is generated from source. To propagate changes:

1. Edit source at `packages/context-injection/`.
2. Run tests: `cd packages/context-injection && uv run pytest`
3. Sync: `scripts/build-cross-model-plugin`
4. Reinstall the plugin: `claude plugin marketplace update turbo-mode && claude plugin install cross-model@turbo-mode`

Do not edit `packages/plugins/cross-model/context-injection/` directly.

### Contract reference

The authoritative protocol specification is at `docs/references/context-injection-contract.md`. All field names, types, enums, and validation semantics are defined there. The implementation must match it. The `schema_version` field (`"0.2.0"`) enforces exact-match versioning for all 0.x releases.

---

## 12. Configuration Limits Quick Reference

| Constant | Value | Location | Effect |
|---|---|---|---|
| `MAX_CONVERSATION_TURNS` | 15 | `pipeline.py` | Turns before `turn_cap_exceeded` |
| `MAX_ENTRIES_BEFORE_COMPACT` | 16 | `checkpoint.py` | Compaction threshold (unreachable under normal op) |
| `KEEP_RECENT_ENTRIES` | 8 | `checkpoint.py` | Entries kept after compaction |
| `MAX_CHECKPOINT_PAYLOAD_BYTES` | 16384 (16 KB) | `checkpoint.py` | Checkpoint size limit |
| `MAX_TURN_RECORDS` | 200 | `state.py` | Turn store capacity |
| `CONVERSATION_GUARD_LIMIT` | 50 | `state.py` | Max concurrent conversations |
| `TAG_LEN` | 16 bytes | `state.py` | HMAC tag length (128-bit truncated SHA-256) |
| `MAX_EVIDENCE_ITEMS` | 5 | `templates.py` | Evidence budget per conversation |
| `MAX_LINES_NORMAL` | 40 | `templates.py` | Read excerpt line cap (normal files) |
| `MAX_CHARS_NORMAL` | 2000 | `templates.py` | Read excerpt char cap (normal files) |
| `MAX_LINES_RISK` | 20 | `templates.py` | Read excerpt line cap (risk-signal files) |
| `MAX_CHARS_RISK` | 1000 | `templates.py` | Read excerpt char cap (risk-signal files) |
| `GREP_CONTEXT_LINES` | 2 | `templates.py` | Context lines around each grep match |
| `GREP_MAX_RANGES` | 5 | `templates.py` | Max ranges per grep result |
| `MAX_TEXT_LEN` | 2000 | `entities.py` | Entity extraction input cap |
| `MIN_ENTRIES_FOR_PLATEAU` | 2 | `control.py` | Consecutive STATIC entries to detect plateau |
| `_BINARY_CHECK_SIZE` | 8192 (8 KB) | `execute.py` | Bytes checked for NUL (binary detection) |
| `CHECKPOINT_FORMAT_VERSION` | `"1"` | `checkpoint.py` | Checkpoint envelope version |

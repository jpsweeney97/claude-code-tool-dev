# Context Injection — Operational Handbook

**System:** `context-injection` MCP server (vendored into `packages/plugins/cross-model/`)
**Version:** 0.2.0
**Contract:** [`docs/references/context-injection-contract.md`](../../../../../docs/references/context-injection-contract.md)
**Source (authoritative):** [`packages/context-injection/`](../../../../../packages/context-injection/)
**Vendored copy:** [`packages/plugins/cross-model/context-injection/`](../)

---

## Overview

The context injection server is a FastMCP process that gives the `codex-dialogue` agent mid-conversation evidence gathering. When Codex makes a factual claim about the codebase, the agent calls this server to verify it in real time — reading files and grepping for symbols — rather than relying entirely on the initial briefing.

**Scope:** Covers the MCP server itself: bring-up, the two-call protocol, security pipeline, conversation state management, and failure recovery. Does not cover the agent that calls it (`packages/plugins/cross-model/agents/codex-dialogue.md`) or the higher-level Codex consultation protocol (`docs/references/consultation-contract.md`).

**What this server does not do:** Execute arbitrary code, call external APIs, manage its own restart, or speak any transport other than stdio.

---

## At a Glance

### MCP Tools (Entry Points)

| Tool | Call | Input | Output | When to skip |
|------|------|-------|--------|-------------|
| `process_turn` | Call 1 | `TurnRequest` | `TurnPacket` (Success or Error) | Never — always call first |
| `execute_scout` | Call 2 | `ScoutRequest` | `ScoutResult` (Success, Failure, or Invalid) | TurnPacket error, empty candidates, budget exhausted, clarifier selected, action=conclude |

### Startup Gates

| Gate | Condition | Failure behavior |
|------|-----------|-----------------|
| POSIX platform | `os.name == "posix"` | `RuntimeError` — server refuses to start |
| git on PATH | `shutil.which("git") is not None` | `RuntimeError` — server refuses to start |
| git ls-files | `git ls-files` must succeed in `REPO_ROOT` | Fail-closed: empty set means all files denied |

### Key Constants

| Constant | Value | Location | Purpose |
|----------|-------|----------|---------|
| `SCHEMA_VERSION` | `"0.2.0"` | `types.py` | Exact-match version check on every request |
| `MAX_CONVERSATION_TURNS` | `15` | `pipeline.py:58` | Hard cap on turns per conversation |
| `MAX_EVIDENCE_ITEMS` | `5` | `templates.py:44` | Evidence budget per conversation |
| `MAX_TURN_RECORDS` | `200` | `state.py:27` | Bounded store with oldest-eviction |
| `CONVERSATION_GUARD_LIMIT` | `50` | `state.py:95` | Max tracked conversations per process |
| `MAX_CHECKPOINT_PAYLOAD_BYTES` | `16384` | `checkpoint.py:23` | 16 KB checkpoint size cap |
| `MAX_ENTRIES_BEFORE_COMPACT` | `16` | `checkpoint.py:151` | Compaction threshold (unreachable under DD-2) |
| `TAG_LEN` | `16` | `state.py:31` | HMAC tag length in bytes (128-bit truncated SHA-256) |

---

## Core Components

### Entry Point

| File | Responsibility |
|------|---------------|
| [`server.py`](context_injection/server.py) | FastMCP server: lifespan, startup gates, tool registration, `python -m context_injection` entry |

### Call 1 Pipeline

| File | Responsibility |
|------|---------------|
| [`pipeline.py`](context_injection/pipeline.py) | 17-step Call 1 orchestration: TurnRequest → TurnPacketSuccess or TurnPacketError |
| [`entities.py`](context_injection/entities.py) | Regex-based entity extraction from claims and unresolved items |
| [`paths.py`](context_injection/paths.py) | Path normalization, denylist enforcement, git tracking gate, runtime re-check |
| [`templates.py`](context_injection/templates.py) | Template matching, ranking, scout option synthesis, HMAC token generation |
| [`ledger.py`](context_injection/ledger.py) | Ledger entry validation: counters, quality, effective_delta, hard/soft warnings |
| [`control.py`](context_injection/control.py) | Action computation (continue/closing_probe/conclude), ledger summary generation |
| [`checkpoint.py`](context_injection/checkpoint.py) | Checkpoint serialization, chain validation, compaction |
| [`conversation.py`](context_injection/conversation.py) | Immutable per-conversation state with projection methods |

### Call 2 Execution Pipeline

| File | Responsibility |
|------|---------------|
| [`execute.py`](context_injection/execute.py) | Top-level dispatch: HMAC validation → read or grep executor |
| [`grep.py`](context_injection/grep.py) | ripgrep subprocess execution, JSON parsing, context range building, evidence blocks |
| [`classify.py`](context_injection/classify.py) | File extension → FileKind for redaction routing |
| [`redact.py`](context_injection/redact.py) | Two-stage redaction orchestration: format-specific then generic token scanner |
| [`redact_formats.py`](context_injection/redact_formats.py) | Per-format redactors: YAML, JSON, TOML, INI/properties, ENV |
| [`truncate.py`](context_injection/truncate.py) | Dual-cap truncation (lines then chars) for read excerpts and grep blocks |

### Supporting Modules

| File | Responsibility |
|------|---------------|
| [`state.py`](context_injection/state.py) | Per-process `AppContext`: HMAC key, turn record store, conversation map, `consume_scout()` |
| [`types.py`](context_injection/types.py) | All Pydantic protocol models (TurnRequest, TurnPacket, ScoutRequest, ScoutResult, etc.) |
| [`canonical.py`](context_injection/canonical.py) | Canonical JSON serialization for HMAC token payloads |
| [`base_types.py`](context_injection/base_types.py) | `ProtocolModel` base, `Claim`, `Unresolved` |
| [`enums.py`](context_injection/enums.py) | `EffectiveDelta`, `QualityLabel`, `ValidationTier`, `TruncationReason` |
| [`__main__.py`](context_injection/__main__.py) | `python -m context_injection` entry point shim |

---

## Configuration and Bring-Up

### Prerequisites

| Requirement | Check |
|-------------|-------|
| Python ≥ 3.11 | `python --version` |
| `git` on PATH | `which git` |
| `rg` (ripgrep) on PATH | `which rg` — required only for grep scouts; read scouts work without it |
| POSIX OS (macOS, Linux, WSL) | Server rejects `os.name != "posix"` at startup |
| Valid git repository at `REPO_ROOT` | `git ls-files` must succeed |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `REPO_ROOT` | `os.getcwd()` at server startup | Repository root used for all path resolution, containment checks, and `git ls-files` |

### Installing Dependencies

From the vendored copy (used by the cross-model plugin at runtime):

```bash
cd packages/plugins/cross-model/context-injection
uv sync
```

From the source package (for development and testing):

```bash
cd packages/context-injection
uv sync
```

### Starting the Server

```bash
# Via module (standard)
python -m context_injection

# Set repo root explicitly (recommended for multi-repo use)
REPO_ROOT=/path/to/repo python -m context_injection
```

The server speaks stdio (stdin/stdout). It is started by the MCP host (Claude Code), not manually, in normal operation. The `pyproject.toml` at [`packages/plugins/cross-model/context-injection/pyproject.toml`](pyproject.toml) declares `mcp>=1.9.0` as the only runtime dependency.

### Updating the Vendored Copy

The vendored copy at `packages/plugins/cross-model/context-injection/` is managed by the build script. Do not edit it directly — edits will be overwritten.

```bash
# 1. Edit source
cd packages/context-injection && <edit files>

# 2. Run tests
uv run pytest

# 3. Sync vendored copy
scripts/build-cross-model-plugin
```

---

## Operating Model

### Two-Call Protocol

Each conversation turn requires two sequential MCP tool calls:

**Call 1 — `process_turn`:** The agent sends a `TurnRequest` containing its current ledger state (position, claims, delta, tags, unresolved items) and checkpoint. The server validates the ledger entry, extracts entities from claims, canonicalizes and gates paths, ranks template candidates, synthesizes HMAC-signed scout options, computes the conversation action, and serializes a checkpoint. Returns a `TurnPacketSuccess` with all of this, or `TurnPacketError` on failure.

**Call 2 — `execute_scout`:** The agent selects one scout option from Call 1's `template_candidates` and sends its `scout_option_id` and `scout_token`. The server validates the HMAC token, recomputes the execution spec (ignores any agent-supplied values), executes the file read or ripgrep search, applies the redaction pipeline, and returns a `ScoutResult`.

Call 2 is skipped when: `TurnPacket.status == "error"`, `template_candidates` is empty, `budget.scout_available` is false, a clarifier template is selected (clarifiers have `scout_options: []`), or `action == "conclude"`.

### HMAC Token Flow

The HMAC key is a 32-byte random value generated once per server process in `state.py`. It is never transmitted.

1. **Call 1 (`templates.py`):** For each scout option, the server serializes a `ScoutTokenPayload` (conversation_id, turn_number, scout_option_id, resolved spec) as canonical JSON, signs it with HMAC-SHA256, truncates to 16 bytes, base64url-encodes, and includes the token in the `ReadOption` or `GrepOption` sent to the agent.

2. **Call 2 (`execute.py` → `state.py:consume_scout`):** The agent sends back the `scout_option_id` and `scout_token`. The server recomputes the expected token from the stored spec and compares using `hmac.compare_digest`. HMAC verification failure → `ScoutResultInvalid`. Replay (used-bit set) → `ScoutResultInvalid`. Token is consumed (used-bit set) only after successful verification.

**Key lifecycle:** A server restart generates a new HMAC key. All tokens from the previous process are invalid. Call 2 after a restart returns `invalid_request`. This is acceptable per the contract — the agent does not retry Call 2 after `invalid_request`; it proceeds to the next turn.

### Checkpoint Handoff

Checkpoints exist because the server process may restart between turns, losing in-memory conversation state. The agent stores the checkpoint string and sends it back on the next turn.

**Normal flow (server has in-memory state):** Server ignores the checkpoint payload and uses the in-memory `ConversationState`. If the agent's `checkpoint_id` matches `state.last_checkpoint_id`, the request proceeds. Mismatch → `checkpoint_stale` error.

**Recovery flow (server restarted):** Server has no in-memory state. If the agent sends a `checkpoint_payload`, the server deserializes and validates it (format version, size integrity, conversation ID match). Restored state is used for the turn. No checkpoint payload → `checkpoint_missing` error.

**Turn 1 special case:** Checkpoint is always ignored on `turn_number <= 1`. No checkpoint is required.

### Evidence Budget

The server tracks evidence across a conversation. The budget controls how many scouts can be executed:

- `MAX_EVIDENCE_ITEMS = 5` — maximum evidence items (successful scouts) per conversation
- `scout_available = evidence_remaining > 0` — derived field, false at or over budget
- Failed scouts (not_found, denied, binary, decode_error, timeout) do not consume budget
- Budget state is reported in every `TurnPacket` and `ScoutResult`

### Conversation Action

Every `TurnPacketSuccess` includes an `action` field guiding the agent:

| Action | Condition |
|--------|-----------|
| `continue_dialogue` | Default; conversation is active |
| `closing_probe` | Plateau detected (last 2 turns STATIC in current phase) and no prior closing probe |
| `conclude` | Budget exhausted, or plateau with closing probe already fired and no open unresolved items |

Plateau detection operates on the phase window (entries since last posture change), not the full history. When posture changes, `closing_probe_fired` resets and a new closing probe opportunity begins.

### Security Stance

Over-redaction is always correct. Every layer of the pipeline fails toward suppression rather than leaking content:

- Path denylist blocks at compile time (Call 1) and runtime (Call 2) — denylist is checked on both the user-supplied path and the resolved path to catch symlinks
- Classification uses `os.path.realpath` (not `path_display`) for all redaction routing — prevents symlink-based classification bypass
- Files not tracked by `git ls-files` are denied at compile time and excluded from grep results
- PEM private key detection short-circuits before any format or token redaction — no content emitted
- Unsupported config formats are suppressed entirely rather than passed through
- `test_footgun_*` tests in the source package verify which pipeline layer catches security violations; do not weaken or remove them

---

## Component Runbooks

### `process_turn` (Call 1)

#### When to use

Call before every turn in a Codex dialogue where the agent wants evidence-gathering options. This is the entry point that produces the ranked scout candidates the agent then chooses from. It also validates and tracks the agent's ledger, computes conversation health, and serializes state for checkpoint recovery.

#### Inputs and defaults

| Field | Required | Default | Purpose |
|-------|----------|---------|---------|
| `schema_version` | Yes | — | Must be `"0.2.0"` exactly |
| `conversation_id` | Yes | — | Stable identifier for this dialogue; creates new state if not seen |
| `turn_number` | Yes | — | 1-indexed turn counter; must match checkpoint history |
| `focus.text` | Yes | — | Free-text description of what the agent is probing |
| `focus.claims` | Yes | — | Must match top-level `claims` exactly (dual-claims guard) |
| `focus.unresolved` | Yes | — | Must match top-level `unresolved` exactly |
| `posture` | Yes | — | One of: `adversarial`, `collaborative`, `exploratory`, `evaluative`, `comparative` |
| `position` | Yes | — | Agent's current stance summary (soft warning if empty) |
| `claims` | Yes | — | List of `{text, status, turn}` objects |
| `delta` | Yes | — | One of: `advancing`, `shifting`, `static` |
| `tags` | Yes | — | List of string tags |
| `unresolved` | Yes | — | List of `{text, turn}` unresolved items |
| `state_checkpoint` | No | `null` | Opaque checkpoint string from prior turn; required on turn > 1 after server restart |
| `checkpoint_id` | No | `null` | Checkpoint ID from prior turn; required when `state_checkpoint` is present |

#### Flow

1. Schema version validation — exact match on `"0.2.0"`
2. Dual-claims guard — `focus.claims == claims` and `focus.unresolved == unresolved`
3. Resolve or create `ConversationState` for `conversation_id`
4. Checkpoint intake — restore from payload if server restarted; validate chain
5. Turn cap guard — reject if `len(entries) >= 15`
6. Entity extraction — regex scan of claims and unresolved items for file paths, symbols, URLs, etc.
7. Path canonicalization and denylist check — normalize, containment check, denylist, git tracking gate
8. Template matching — rank entities, gate on path status, dedupe against evidence history
9. Budget computation — derive `evidence_remaining` and `scout_available`
10. Ledger entry validation — compute counters, quality, effective_delta; generate hard/soft warnings
11. Build provisional state — append entry
12. Compute cumulative state, action, action_reason
13. Closing probe projection — if action is `closing_probe`, mark fired in state
14. Ledger compaction — triggered only if `len(entries) > 16` (unreachable under normal limits)
15. Checkpoint serialization — UUID checkpoint ID, 16 KB size guard
16. Commit state and return `TurnPacketSuccess`

#### Failure modes

| Symptom | Cause | Recovery |
|---------|-------|---------|
| `status: "error"`, code `invalid_schema_version` | Client sending wrong schema version | Update client to send `"0.2.0"` |
| `status: "error"`, code `ledger_hard_reject` with dual-claims message | `focus.claims != claims` or `focus.unresolved != unresolved` | Send identical lists in both channels |
| `status: "error"`, code `ledger_hard_reject` with empty claims message | `claims` list is empty | Include at least one claim per turn |
| `status: "error"`, code `turn_cap_exceeded` | Conversation hit 15-turn limit | Start a new conversation (new `conversation_id`) |
| `status: "error"`, code `checkpoint_missing` | Turn > 1, server restarted, no checkpoint sent | Send `state_checkpoint` and `checkpoint_id` from the prior turn's response |
| `status: "error"`, code `checkpoint_stale` | Checkpoint ID mismatch | Always send the checkpoint from the immediately preceding turn, not a cached older one |
| `status: "error"`, code `checkpoint_invalid` | Corrupt payload, size mismatch, or cross-conversation swap | Restart conversation; do not replay the corrupt checkpoint |
| `status: "error"`, code `internal_error` | Unexpected exception in pipeline | Check server logs; likely a bug — report with request payload |
| `template_candidates` is empty | No Tier 1 entities found, all entities denied/untracked, or budget exhausted | Normal; skip Call 2 and proceed without evidence |
| `budget.scout_available: false` | Evidence budget exhausted (5 items) | Skip Call 2; the conversation should be approaching `conclude` |
| Warnings in `validated_entry.warnings` with `tier: "soft_warn"` | Agent delta disagrees with computed effective_delta, or position is empty | Non-blocking; adjust agent behavior to match computed values |
| `CONVERSATION_GUARD_LIMIT` `ValueError` | 50 conversations tracked in one server process | Server restart clears all conversations; avoid leaking conversation IDs |

---

### `execute_scout` (Call 2)

#### When to use

Call immediately after `process_turn` returns a `TurnPacketSuccess` with a non-empty `template_candidates` list, `budget.scout_available: true`, and `action != "conclude"`. Select exactly one `scout_option_id` from the template candidates. One scout per turn — the used-bit blocks all options on the same turn after the first is consumed.

#### Inputs

| Field | Required | Purpose |
|-------|----------|---------|
| `schema_version` | Yes | Must be `"0.2.0"` |
| `scout_option_id` | Yes | ID of the selected scout option (e.g., `"so_001"`) |
| `scout_token` | Yes | HMAC token from the corresponding `ReadOption` or `GrepOption` |
| `turn_request_ref` | Yes | `"{conversation_id}:{turn_number}"` — links this call to its Call 1 |

#### Flow (read scout)

1. HMAC token validation via `consume_scout()` — verify token, check replay, mark used
2. Runtime path check — realpath resolution, containment, denylist re-check, regular file existence
3. File read — binary detection (NUL in first 8 KB), UTF-8 decode, excerpt selection (first_n or centered)
4. Classify by realpath extension (not `path_display`) — assign `FileKind`
5. Redact — format-specific pass (PEM short-circuit → format redactor → generic token scanner)
6. Truncate — dual cap: `max_lines` then `max_chars` at line boundaries
7. Return `ScoutResultSuccess` with `read_result`, `truncated`, `redactions_applied`, `budget`

#### Flow (grep scout)

1. HMAC token validation via `consume_scout()` — same as read
2. Run ripgrep — `rg --json --fixed-strings --hidden --no-ignore --glob=!.git/ <pattern>`
3. Parse JSON output — extract `GrepRawMatch` objects from type=`match` records
4. Group by file, filter — only git-tracked files not in denylist survive
5. For each surviving file: read, build context ranges (±2 lines), classify by realpath
6. Redact each range separately — suppressed ranges are dropped entirely
7. Truncate blocks — precedence: max_ranges then max_lines then max_chars
8. Return `ScoutResultSuccess` with `grep_result`, `truncated`, `redactions_applied`, `budget`

#### Failure modes

| Symptom | Cause | Recovery |
|---------|-------|---------|
| `status: "invalid_request"` | Token invalid, turn_request_ref not found, or used-bit set | Token invalid: server restarted — proceed to next turn without evidence. Used-bit: only one scout per turn is allowed. |
| `status: "not_found"` | File existed at Call 1 but was deleted before Call 2 (TOCTOU) | Normal race — the evidence is absent; proceed without it |
| `status: "denied"` | Path passed compile-time check but failed runtime containment or denylist re-check | Likely a symlink was swapped between Call 1 and Call 2 — security catch, proceed without evidence |
| `status: "binary"` | File contains NUL bytes in first 8192 bytes | Expected for binary files — skip; consider clarifying the question |
| `status: "decode_error"` | File is not valid UTF-8 | Expected for non-UTF-8 files — skip |
| `status: "timeout"` with "ripgrep (rg) not found" | `rg` is not installed | Install ripgrep; grep scouts are unavailable until it is |
| `status: "timeout"` with "ripgrep timed out" | ripgrep exceeded 5-second timeout | Pattern may be too broad or the repo too large; retry with a more specific pattern |
| `excerpt` is `[REDACTED:key_block]` | PEM private key detected in file content | Expected suppression — the file likely contains key material; do not request it again |
| `excerpt` is `[REDACTED:unsupported_config_format]` | Config file with no registered format redactor | Expected for novel config formats; over-redaction by design |
| `truncated: true` | Content exceeded `max_lines` (40 normal, 20 risk) or `max_chars` (2000 normal, 1000 risk) | Normal for large files; evidence is still useful; consider using `file_loc` with a line anchor to center the read |
| `redactions_applied > 0` | Format-specific or generic token redaction fired | Expected for config files or files containing credential patterns; content is still useful |
| `grep_result.match_count == 0` | Symbol not found in tracked files | Expected; absence of evidence is data — report to the agent |

---

## Internals

### Call 1 Entity Extraction and Path Safety

The server extracts typed entities from claim text and unresolved items using regex patterns in `entities.py`. Each entity gets a `tier` (1 = directly actionable, 2 = requires clarification) and a `confidence` (high, medium, low). Only Tier 1 entities with high or medium confidence that are `in_focus=True` proceed to probe template matching.

For each Tier 1 file entity (`file_loc`, `file_path`, `file_name`), the pipeline runs `check_path_compile_time()` in `paths.py`:

1. Normalize: strip quotes/backticks, reject NUL bytes, reject absolute paths, reject `..` traversal, NFC-normalize Unicode, collapse double slashes
2. Resolve to absolute path (logical join; use `realpath` if file exists)
3. Containment check: resolved path must be under `repo_root`
4. Denylist check on both normalized and resolved paths (catches symlinks pointing to denied files)
5. Git tracking gate: path must appear in the `git ls-files` set loaded at startup

A `CompileTimeResult` with `status="allowed"` is required before a scout option is generated.

### Redaction Pipeline

Redaction runs before truncation in the Call 2 execution path. Three outcomes are possible:

**Suppressed (`SuppressedText`):** No content emitted. Triggers on:
- PEM private key marker in text (`-----BEGIN ... PRIVATE KEY-----`) — checked first, short-circuits everything
- Config file with no registered format redactor — fail-closed for unknown formats
- Format parser desync — internal parser failure

**Redacted (`RedactedText`):** Content emitted with sensitive values replaced by `[REDACTED:value]`. Two stages run for all files:
1. Format-specific pass (config files only): YAML, JSON, TOML, INI/properties, ENV — redacts values at sensitive keys
2. Generic token pass (all files): JWT, Bearer/Basic auth headers, API key prefixes (`sk-`, `ghp_`, `AKIA`, etc.), URL userinfo (passwords in URLs), credential assignments (`password=`, `secret=`, etc.)

Classification uses `os.path.realpath` to prevent symlink-based bypass (a symlink named `code.py` pointing to `secret.cfg` is classified as `CONFIG_INI`, not `CODE`).

### Checkpoint Chain

Each `TurnPacketSuccess` includes `state_checkpoint` (opaque JSON string) and `checkpoint_id` (UUID hex). The checkpoint encodes the full `ConversationState` as a double-encoded JSON blob:

```
StateCheckpoint {
  checkpoint_id: UUID hex
  parent_checkpoint_id: prior checkpoint_id or null
  format_version: "1"
  payload: JSON string of ConversationState
  size: byte count of payload (integrity check)
}
```

Integrity checks on restore: format version match, payload size match, `payload.last_checkpoint_id == envelope.checkpoint_id`, `payload.conversation_id == request.conversation_id`.

**DD-2 invariant:** `MAX_CONVERSATION_TURNS (15) < MAX_ENTRIES_BEFORE_COMPACT (16)`. This ensures compaction is never triggered under normal operation — the turn cap prevents entries from reaching the compaction threshold. Compaction (`compact_ledger`) is retained as a safety net only.

### Conversation State Immutability

`ConversationState` is a frozen Pydantic model. No method mutates it. All updates return new instances via `model_copy(update={...})`. The pipeline commits atomically by replacing the dict entry: `ctx.conversations[conversation_id] = projected`. This ensures the server never holds a partially-updated state.

### One-Scout-Per-Turn Invariant

`consume_scout()` enforces one scout per turn via a per-`TurnRequestRecord` used-bit. The bit is set after HMAC verification succeeds, before execution. Attempting a second Call 2 with the same `turn_request_ref` (regardless of which `scout_option_id`) returns `ScoutResultInvalid`. The used-bit is not set on verification failure (constant-time failure handling).

---

## Failure and Recovery Matrix

| Symptom | Likely Cause | Diagnosis | Recovery |
|---------|-------------|-----------|---------|
| Server crashes at startup with "requires POSIX" | Running on Windows without WSL | Check `os.name` | Use macOS, Linux, or WSL |
| Server crashes at startup with "git not found" | `git` not on PATH | `which git` | Install git or add to PATH |
| All file paths return `not_tracked` | `git ls-files` failed at startup (empty set) | Check server logs for `git ls-files failed:` | Verify `REPO_ROOT` is a valid git repo; check `git status` |
| `invalid_schema_version` error | Protocol version mismatch between agent and server | Compare `schema_version` in request vs `SCHEMA_VERSION` in `types.py` | Redeploy agent and server with matching versions |
| `turn_cap_exceeded` after fewer than 15 turns | Prior call restored stale checkpoint with more entries than expected | Check `state_checkpoint` being sent | Start new conversation; audit checkpoint forwarding logic |
| `checkpoint_stale` on turn 2 | Agent sending checkpoint from a different turn or conversation | Verify agent stores and forwards the checkpoint from the immediately prior `TurnPacketSuccess` | Fix agent checkpoint forwarding |
| `invalid_request` from Call 2 after normal Call 1 | Server restarted between Call 1 and Call 2 (HMAC key regenerated) | Check server process uptime | Normal; agent should proceed to next turn without evidence |
| `invalid_request` despite no restart | Duplicate `turn_request_ref` in the store (eviction race) | `MAX_TURN_RECORDS=200`; rare on fast multi-turn loops | Restart server; if recurring, extend `MAX_TURN_RECORDS` |
| All grep scouts return `"ripgrep not found"` | `rg` not installed | `which rg` | Install ripgrep (`brew install ripgrep` or `mise use ripgrep`) |
| All read scouts return `denied` for legitimate files | `REPO_ROOT` set incorrectly — files are not under the expected root | Log `ctx.repo_root` and the failing path | Set `REPO_ROOT` to the actual repository root |
| All paths return `not_tracked` in a large monorepo | `git ls-files` returns relative paths from a subdirectory | Check if `REPO_ROOT` is a subdirectory of the true git root | Set `REPO_ROOT` to the output of `git rev-parse --show-toplevel` |
| Config files return `[REDACTED:unsupported_config_format]` | New config format not yet covered by `redact_formats.py` | Check `classify_path()` output for the extension | Add a format-specific redactor; until then, over-redaction is safe |
| `CONVERSATION_GUARD_LIMIT` error after many sessions | Agent creating a new `conversation_id` per turn rather than per dialogue | Audit `conversation_id` assignment in the agent | Use a stable `conversation_id` per Codex dialogue |
| `checkpoint_invalid` with "payload size mismatch" | Checkpoint string was truncated or corrupted in transit | Compare `size` field vs actual payload length | Verify the agent stores and forwards checkpoint strings verbatim |

---

## Known Limitations

**POSIX-only.** The server explicitly rejects non-POSIX platforms at startup. Windows without WSL is not supported.

**HMAC tokens do not survive server restart.** Any Call 2 after a server restart returns `invalid_request`. The agent must handle this by proceeding to the next turn without evidence, not by retrying the scout.

**One scout per turn.** The used-bit blocks all scout options on the same `turn_request_ref` after any one is consumed. If the agent needs evidence from two entities on the same turn, it must choose the higher-priority one.

**15-turn conversation cap.** Conversations are hard-capped at `MAX_CONVERSATION_TURNS = 15`. This is a protocol-level limit, not just a recommendation. Exceeding it returns `turn_cap_exceeded`. Start a new conversation for new dialogue topics.

**Evidence budget is 5 items per conversation.** Once `evidence_remaining == 0`, no more scouts can be executed. The action signal transitions to `conclude` at budget exhaustion.

**Risk-signal files get half the read budget.** Files with `secret`, `token`, or `credential` in their path get `max_lines=20` and `max_chars=1000` instead of 40/2000. This reduces evidence quality for potentially sensitive files.

**grep scouts use fixed-string matching only.** `rg --fixed-strings` is hard-coded. Regex patterns are not supported in grep scouts.

**git ls-files is loaded once at startup.** Files added to the repo after the server starts are not accessible. Restart the server to pick up newly tracked files.

**50-conversation guard.** The `AppContext` caps tracked conversations at 50. Leaking unique `conversation_id` values across turns (rather than maintaining one per dialogue) will exhaust this limit and cause errors.

**Checkpoint payload is not encrypted.** The checkpoint string contains conversation state (claims, positions, ledger entries) in JSON. It is integrity-checked but not confidential. The agent should treat it as an opaque blob and not expose it.

**`MAX_ENTRIES_BEFORE_COMPACT` vs `MAX_CONVERSATION_TURNS` invariant is load-bearing.** The code asserts at import time that `MAX_CONVERSATION_TURNS (15) < MAX_ENTRIES_BEFORE_COMPACT (16)`. If these constants are ever modified, this import-time check in `pipeline.py:63` will raise `RuntimeError` before the server starts. Do not relax this without understanding the compaction trade-off in `checkpoint.py:compact_ledger`.

---

## Verification

### Prerequisites

```bash
# From the source package root
cd packages/context-injection

# Verify Python version
python --version   # must be >= 3.11

# Verify git
git --version

# Verify ripgrep (needed for grep scout tests)
rg --version
```

### 1. Run the Test Suite

```bash
cd packages/context-injection
uv run pytest
```

969 tests. All should pass. Failures indicate a regression in the source package or a broken environment.

To run a specific module:
```bash
uv run pytest tests/test_pipeline.py -v
uv run pytest tests/test_execute.py -v
uv run pytest tests/test_redact.py -v
```

To run the integration tests (requires a live git repo):
```bash
uv run pytest tests/test_integration.py -v
```

### 2. Lint

```bash
cd packages/context-injection
uv run ruff check context_injection/ tests/
```

Expected: no errors. Known intentional lint suppressions:
- `E402` at `pipeline.py:61` (import-time invariant check after constant definition — intentional)
- `F401` re-exports in `types.py:19` (convenience re-exports for test use — intentional)

### 3. Smoke Test — Server Startup

```bash
cd packages/context-injection
REPO_ROOT=$(git rev-parse --show-toplevel) python -m context_injection &
sleep 1
kill %1
```

A clean startup emits no error output. If the server dies immediately, check:
- Platform is POSIX
- `git` is on PATH
- `REPO_ROOT` is a valid git repository

### 4. End-to-End Check — process_turn

Construct a minimal Call 1 request and send it through the server. The simplest way is via the test suite's integration tests. For a manual check using the MCP SDK:

```python
# Confirm the server responds to a valid TurnRequest with TurnPacketSuccess
# See tests/test_integration.py for a full example using a real git repo fixture
uv run pytest tests/test_integration.py::test_process_turn_success -v
```

### 5. Security Smoke Tests

```bash
# Verify footgun tests still catch their stated violations
uv run pytest tests/test_redact.py -k "footgun" -v
uv run pytest tests/test_paths.py -k "denylist" -v
```

All footgun tests must pass. A footgun test failure means a security control has been accidentally removed or weakened.

### 6. Vendored Copy Check

After any source edit, verify the vendored copy is in sync:

```bash
scripts/build-cross-model-plugin
git diff packages/plugins/cross-model/context-injection/
```

The diff should be empty (or show only the changes you intended). If it is not empty, run the build script before committing.

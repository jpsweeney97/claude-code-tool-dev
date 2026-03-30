---
date: 2026-03-30
time: "18:31"
created_at: "2026-03-30T22:31:33Z"
session_id: f110a809-0159-4783-a5bc-c88da1104b02
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-30_14-59_item6-landed-release-posture-supersession-roadmap.md
project: claude-code-tool-dev
branch: feature/codex-collaboration-plugin-shell
commit: d6fb34b7
title: "T-02 plugin shell implemented, pending user review"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/mcp_server.py
  - packages/plugins/codex-collaboration/tests/test_mcp_server.py
  - packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py
  - packages/plugins/codex-collaboration/scripts/publish_session_id.py
  - packages/plugins/codex-collaboration/hooks/hooks.json
  - packages/plugins/codex-collaboration/.claude-plugin/plugin.json
  - packages/plugins/codex-collaboration/.mcp.json
  - packages/plugins/codex-collaboration/skills/consult-codex/SKILL.md
  - packages/plugins/codex-collaboration/skills/codex-status/SKILL.md
  - packages/plugins/codex-collaboration/tests/test_bootstrap.py
  - packages/plugins/codex-collaboration/README.md
  - docs/tickets/2026-03-30-codex-collaboration-plugin-shell-and-consult-parity.md
---

# Handoff: T-02 plugin shell implemented, pending user review

## Goal

Implement T-20260330-02: the codex-collaboration plugin shell and minimal consult flow. This is the first executable supersession packet — turning the existing runtime into a minimal installable plugin with a working consult flow.

**Trigger:** Prior session completed the post-R2 hardening arc (item 6, release posture, supersession roadmap). The user's stated goal: "complete building the codex-collaboration system/plugin in full" to supersede cross-model. T-02 is the first step in the 6-ticket roadmap.

**Stakes:** Cross-model replacement cannot start until users can install codex-collaboration and invoke a consult flow through the host plugin surface. Without the plugin shell, the runtime is testable from the repo but not usable as the successor plugin.

**Success criteria:** 8 acceptance criteria from T-02 ticket: `plugin.json`, `.mcp.json`, bootstrap entry point, consult skill with status preflight, status skill, end-to-end consultation dispatch, install docs, and tests covering bootstrap and skill wiring.

**Connection to project arc:** Spec compiled (`bf8e69e3`) → T1 → R1 → Post-R1 → R2 → Post-R2 hardening → Supersession roadmap (`dbc91d8f`) → **T-02 plugin shell (this session)** → T-03 safety substrate (next).

## Session Narrative

### Loaded prior handoff and scoped the work

Loaded the handoff from the prior session (`2026-03-30_14-59_item6-landed-release-posture-supersession-roadmap.md`). Read the T-02 ticket and proposed a 5-step macro build sequence: (1) bootstrap entry point, (2) plugin shell, (3) skills, (4) tests, (5) docs.

### User tightened the sequence with four corrections

The user accepted the macro sequence but corrected four assumptions:

1. **Bootstrap location:** I defaulted to `server/__main__.py`. User pointed to `delivery.md:45` which specifies `scripts/codex_runtime_bootstrap.py`. This is the normative location — using `__main__.py` would be a spec deviation, not an implementation detail.

2. **Investigation scope:** I framed Step 1 as "read two constructors." User expanded it to four questions: launch path, plugin-data path, session-id source, and object graph assembly. User: "The first investigation should answer four things together."

3. **Skill names:** I used generic `consult/` and `status/`. User corrected to `skills/consult-codex/` and `skills/codex-status/` per `delivery.md:32-39`.

4. **Test timing:** I postponed all tests to Step 4. User: "Write bootstrap tests as Step 1/2 land, because launch wiring and env assumptions are the brittle part."

### Investigated the bootstrap contract (4 questions)

Read all constructor signatures for the object graph: `ControlPlane` (`control_plane.py:47`), `DialogueController` (`dialogue.py:45`), `OperationJournal` (`journal.py:27-30`), `LineageStore` (`lineage_store.py:26`), `TurnStore` (`turn_store.py:18`). Mapped the complete dependency graph:

```
default_plugin_data_path() → OperationJournal → ControlPlane → McpServer
                           → LineageStore ─────→ DialogueController ↗
                           → TurnStore ────────↗
```

Key findings:
- **Launch path:** `scripts/codex_runtime_bootstrap.py` per spec, launched via `uv run --directory ${CLAUDE_PLUGIN_ROOT} python ...` (same pattern as cross-model's `.mcp.json`)
- **Plugin-data path:** `CLAUDE_PLUGIN_DATA` auto-set by Claude Code for plugin subprocesses (confirmed by docs). `journal.py:default_plugin_data_path()` reads it from `os.environ`. Resolves to `~/.claude/plugins/data/{id}/`. The `/tmp/codex-collaboration` fallback is test/dev only.
- **Session-id:** NOT available as env var to MCP servers. Only `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` are auto-set. This became the key design problem.

### Session-id design: three iterations

**First proposal (rejected):** UUID-at-process-start. I argued each MCP server process is effectively a session boundary. User rejected with four contract violations:
- `contracts.md` requires crash survival within a running session
- `delivery.md` makes crash recovery after simulated process crash an R2 acceptance gate
- `dialogue.py:339` says same `session_id` across restart is an external wiring contract
- `test_dialogue_integration.py:100` already encodes recovery with the same `sess-1` partition

User: "A process-scoped UUID would make every MCP server restart look like a brand-new Claude session. `recover_startup()` would scan the wrong lineage/journal partition."

**Second investigation:** Searched Claude Code docs for any host-provided session identity. Found `session_id` IS available in hook event payloads (every hook receives it via stdin JSON). Not available as an env var to MCP server subprocesses. The hook system is the bridge.

**Final design (accepted):** SessionStart hook writes `session_id` to `${CLAUDE_PLUGIN_DATA}/session_id`. MCP server defers dialogue initialization until first `codex.dialogue.*` call, reads the file once, pins it. User's key requirement: "Lazy init must be one-way and pinned. If the identity file later changes, do not hot-switch to a new partition mid-process. Refuse and error instead."

User also approved: "A narrow SessionStart hook is acceptable in T-02. It is bootstrap glue, not the credential-scanning hook substrate that was deliberately deferred."

### Implemented the five-step sequence

**Step 1: McpServer deferred dialogue init.** Made `dialogue_controller` optional (default `None`). Added `dialogue_factory: Callable[[], Any]` parameter. Added `_ensure_dialogue_controller()` — called at most once, pins result, discards factory. `startup()` skips recovery if no controller set. 7 new tests: factory invocation, recovery on init, pinning, no-controller error, R1 tool independence. All 18 MCP tests pass.

**Step 2: Bootstrap + hook.** Created `scripts/codex_runtime_bootstrap.py` with object graph wiring using lazy `_build_dialogue_factory`. Created `scripts/publish_session_id.py` as the SessionStart hook script (atomic file replacement via `os.replace`). Created `hooks/hooks.json` referencing the script. 11 bootstrap tests: session_id read/strip/missing/empty, factory construction/failure, hook script write/overwrite/noop cases. All pass.

**Step 3: Plugin shell.** Created `.claude-plugin/plugin.json` (name, version 0.2.0, description, author, license, keywords). Created `.mcp.json` with single `codex-collaboration` server using `uv run --directory ${CLAUDE_PLUGIN_ROOT}` + `CODEX_SANDBOX=seatbelt`.

**Step 4: Skills.** Created `skills/codex-status/SKILL.md` (maps to `codex.status` tool). Created `skills/consult-codex/SKILL.md` (status preflight → consult dispatch → result relay). Both intentionally thin per ticket: "The consult skill should be intentionally thin." Out-of-scope features (profiles, learnings, analytics, credential scanning) explicitly documented as T-03.

**Step 5: Docs + carry-forward.** Created `README.md` with prerequisites, install, smoke-test, architecture, limitations. Added carry-forward limitations to T-02 ticket: concurrent sessions unsupported, SessionStart hook ordering assumption.

238 tests pass (up from 220). All 8 acceptance criteria addressed.

## Decisions

### SessionStart hook + deferred dialogue init for session identity

**Choice:** Use a plugin SessionStart hook to publish `session_id` from the host to `${CLAUDE_PLUGIN_DATA}/session_id`. The MCP server reads it lazily on first dialogue tool call, pins it, and refuses mid-process identity changes.

**Driver:** Claude Code does not expose `session_id` as an env var to MCP server subprocesses. Only hooks receive it via stdin JSON payload. The recovery contract (`dialogue.py:339-342`) requires same `session_id` across MCP server restarts within a Claude session.

**Rejected:**
- **UUID-at-process-start** — violates the recovery contract in four places. Each MCP server restart would look like a new session. `recover_startup()` would scan the wrong partition. User: "That is not a tolerable dev-rollout tradeoff; it is a regression against the already accepted R2 semantics."
- **Blocking MCP server startup until session_id appears** — user: "Blocking startup would widen the failure domain of packet 2a for no gain. `codex.status` and `codex.consult` do not need session-scoped state."
- **Deriving session_id from PID/timestamp** — fragile, not truly stable across restarts.

**Trade-offs accepted:** Concurrent Claude sessions sharing the plugin will race on the session_id file — last writer wins. The losing MCP server may use the wrong session identity for dialogue operations. Accepted for dev-repo single-session rollout target.

**Confidence:** High (E2) — verified in Claude Code docs that hooks receive `session_id`, verified in code that `ControlPlane`/`codex.consult` don't need it, verified by tests that deferred init works.

**Reversibility:** High — if Claude Code adds a `CLAUDE_SESSION_ID` env var for MCP subprocesses, the hook and deferred init can be simplified to direct env var read. The `_ensure_dialogue_controller()` indirection would remain.

**Change trigger:** Claude Code exposing per-session data directories or session identity env var to MCP server subprocesses.

### Launch path at scripts/codex_runtime_bootstrap.py (spec-aligned)

**Choice:** Place the bootstrap entry point at `scripts/codex_runtime_bootstrap.py` as specified in `delivery.md:45`.

**Driver:** User: "Don't treat `server/__main__.py` as the default bootstrap location yet. The normative install shape currently points to `scripts/codex_runtime_bootstrap.py`. If we choose `server/__main__.py`, that is a deliberate spec deviation, not an implementation detail."

**Rejected:**
- **`server/__main__.py`** — would require a spec amendment for no functional benefit. The `__main__.py` pattern is Pythonic but the spec already designates the path.

**Trade-offs accepted:** None — no functional difference. The `.mcp.json` points to the script by full path via `${CLAUDE_PLUGIN_ROOT}`.

**Confidence:** High (E2) — spec is explicit.

**Reversibility:** High — rename the file and update `.mcp.json`.

**Change trigger:** None.

### Thin consult skill with explicit scope boundaries

**Choice:** The `consult-codex` skill does exactly three things: status preflight, consultation dispatch, result relay. No briefing enrichment, credential scanning, profiles, or analytics.

**Driver:** T-02 ticket: "The consult skill should be intentionally thin. It only needs to prove that an installed plugin can route user input through `codex.status` and `codex.consult`." Production UX hardening is T-03.

**Rejected:**
- **Port cross-model consultation features** — wrong risk profile for T-02. The ticket explicitly says: "Do not port cross-model hook behavior into this ticket. The plugin shell and the shared safety substrate have different risk profiles."

**Trade-offs accepted:** No credential scanning on outbound payloads. No consultation profiles. No learning retrieval. Acceptable because the rollout target is dev-repo internal use.

**Confidence:** High (E2) — ticket is explicit about scope.

**Reversibility:** High — skill is additive. T-03 adds features without changing T-02 artifacts.

**Change trigger:** T-03 landing.

## Changes

### `server/mcp_server.py` — Deferred dialogue controller init

**Purpose:** Enable the MCP server to start and serve R1 tools (status, consult) without requiring a dialogue controller at construction time.

**Changes:**
- `dialogue_controller` parameter changed from required to `Optional[Any]` (default `None`)
- Added `dialogue_factory: Callable[[], Any] | None` parameter
- Added `_ensure_dialogue_controller()` method: returns cached controller or calls factory once, pins result, runs recovery, discards factory reference
- `startup()` now skips recovery if no dialogue controller is set (recovery runs during deferred init instead)
- All three dialogue tool dispatch paths (`codex.dialogue.start`, `.reply`, `.read`) now call `_ensure_dialogue_controller()` instead of accessing `self._dialogue_controller` directly

**Key detail:** The factory reference is set to `None` after first use (`self._dialogue_factory = None`). This implements the one-way pin contract — the factory cannot be re-invoked, and the controller cannot be replaced.

### `tests/test_mcp_server.py` — Deferred init tests

**Purpose:** Cover all three deferred-init configurations and verify R1 independence from dialogue.

**New tests (7):**
- `test_startup_without_dialogue_controller_is_noop` — startup completes when no controller configured
- `test_factory_called_on_first_dialogue_tool` — factory invoked exactly once on first dialogue call
- `test_factory_runs_recovery_on_init` — lazy init calls `recover_startup()` on the created controller
- `test_factory_pinned_after_first_call` — second dialogue call reuses cached controller, factory count stays at 1
- `test_no_controller_no_factory_returns_error` — dialogue call without either returns explicit MCP error
- `test_status_works_without_dialogue` — `codex.status` works with no dialogue controller
- `test_consult_works_without_dialogue` — `codex.consult` works with no dialogue controller

### `scripts/codex_runtime_bootstrap.py` — Plugin entry point

**Purpose:** Wire the object graph and start the stdio JSON-RPC loop with lazy dialogue initialization.

**Key functions:**
- `_read_session_id(plugin_data_path)` — reads `session_id` file, raises `RuntimeError` if missing or empty
- `_build_dialogue_factory(...)` — returns a zero-arg factory that reads session_id, creates `LineageStore`/`TurnStore`/`DialogueController` on first call
- `main()` — creates `OperationJournal` + `ControlPlane` immediately, passes factory to `McpServer`, calls `server.run()`

**Key detail:** Shares the `OperationJournal` instance between `ControlPlane` and the factory closure. Without explicit sharing, `ControlPlane.__init__` at `control_plane.py:64` creates its own journal — which would result in two independent journals.

### `scripts/publish_session_id.py` — SessionStart hook script

**Purpose:** Extract `session_id` from the Claude Code hook payload and write it to `${CLAUDE_PLUGIN_DATA}/session_id` for the MCP server to read.

**Key detail:** Uses atomic file replacement (`os.replace(tmp, target)`) with `fsync` before rename. Same crash-safety pattern as `OperationJournal.compact()` at `journal.py:121-127`. No-ops gracefully on missing env var, missing session_id field, or invalid JSON.

### `hooks/hooks.json` — SessionStart hook config

**Purpose:** Register the session_id publication hook with Claude Code.

**Content:** Single SessionStart hook that runs `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/publish_session_id.py`. Uses `python3` directly (not `uv run`) because the script has zero dependencies beyond stdlib and hooks should be fast.

### `.claude-plugin/plugin.json` — Plugin manifest

**Purpose:** Declare the installable plugin with metadata.

**Content:** Name `codex-collaboration`, version `0.2.0`, description, author, license MIT, keywords for discoverability. Version 0.2.0 reflects R2 completion as the baseline.

### `.mcp.json` — MCP server launch config

**Purpose:** Tell Claude Code how to start the codex-collaboration MCP server.

**Content:** Single `codex-collaboration` server using `uv run --directory ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/scripts/codex_runtime_bootstrap.py`. Sets `CODEX_SANDBOX=seatbelt` (macOS stability — prevents `Attempted to create a NULL object` panic).

**Key detail:** The server name `codex-collaboration` determines the MCP tool name prefix: `mcp__plugin_codex-collaboration_codex-collaboration__<tool>`. This must match the `allowed-tools` in skill frontmatter.

### `skills/consult-codex/SKILL.md` — Minimal consult skill

**Purpose:** Thin wrapper routing user input through `codex.status` preflight then `codex.consult`.

**Key detail:** `allowed-tools` includes both `codex.status` and `codex.consult` MCP tool names with full plugin prefix. Explicit out-of-scope section prevents future sessions from expanding prematurely (profiles, learnings, analytics, credential scanning are T-03).

### `skills/codex-status/SKILL.md` — Status skill

**Purpose:** Check runtime health, auth, version, and diagnostics.

**Key detail:** `allowed-tools` includes only the `codex.status` MCP tool. Procedure covers auth remediation guidance and error reporting.

### `tests/test_bootstrap.py` — Bootstrap wiring tests

**Purpose:** Cover session_id reading, factory construction, and hook script behavior.

**Test classes (3):**
- `TestReadSessionId` (4 tests) — reads published session_id, strips whitespace, raises on missing/empty
- `TestBuildDialogueFactory` (2 tests) — factory returns `DialogueController` instance, factory raises when session_id missing
- `TestPublishSessionIdHook` (5 tests) — subprocess tests for hook script: writes session_id, overwrites stale, no-ops without env var/missing field/invalid JSON

### `README.md` — Install and smoke-test docs

**Purpose:** Document the install shape well enough for a fresh session to install and smoke test without referencing cross-model (T-02 acceptance criterion 7).

**Sections:** Prerequisites, install (plugin-dir and marketplace), smoke test (3-step: check loaded, status, consult), skills table, architecture overview, limitations, test command.

### `T-20260330-02` ticket — Carry-forward limitations

**Purpose:** Document the concurrent-session limitation and SessionStart hook ordering assumption per the user's directive to track them explicitly.

**Added:** "Carry-Forward Limitations" section with two items: concurrent packaged sessions unsupported (with blast radius and invalidation trigger), SessionStart hook ordering assumption (with expectation that it's non-issue in practice).

## Codebase Knowledge

### Key Code Locations (Verified This Session)

| What | Location | Why verified |
|------|----------|-------------|
| `McpServer.__init__` | `mcp_server.py:78-90` | Modified: `dialogue_controller` now optional, added `dialogue_factory` |
| `_ensure_dialogue_controller()` | `mcp_server.py:106-120` | New: lazy init with pin |
| `McpServer.startup()` | `mcp_server.py:92-104` | Modified: skips recovery when no controller |
| `_dispatch_tool()` | `mcp_server.py:204-248` | Modified: dialogue tools use `_ensure_dialogue_controller()` |
| `ControlPlane.__init__` | `control_plane.py:47-65` | Read: has defaults for everything except `plugin_data_path` self-assembles journal if not provided |
| `DialogueController.__init__` | `dialogue.py:45-62` | Read: requires 5 args (control_plane, lineage_store, journal, session_id, turn_store) — no defaults |
| `LineageStore.__init__` | `lineage_store.py:26-29` | Read: needs (plugin_data_path, session_id) |
| `TurnStore.__init__` | `turn_store.py:18-20` | Read: needs (plugin_data_path, session_id) |
| `default_plugin_data_path()` | `journal.py:14-24` | Read: `CLAUDE_PLUGIN_DATA` env → `/tmp/codex-collaboration` fallback |
| `OperationJournal.__init__` | `journal.py:30-37` | Read: needs only `plugin_data_path` — no session_id |

### Architecture: Object Graph Assembly

The bootstrap creates a layered dependency graph. The key architectural property is the split between session-independent components (available immediately) and session-scoped components (deferred):

```
                    IMMEDIATE (no session_id needed)
                    ─────────────────────────────────
CLAUDE_PLUGIN_DATA → default_plugin_data_path()
                        │
                        ├── OperationJournal(plugin_data_path)
                        │       │
                        │       └── ControlPlane(plugin_data_path, journal)
                        │               │
                        │               └── McpServer(control_plane, dialogue_factory=...)
                        │
                    DEFERRED (first codex.dialogue.* call)
                    ─────────────────────────────────────
                        │
session_id file ────────┤
                        ├── LineageStore(plugin_data_path, session_id)
                        ├── TurnStore(plugin_data_path, session_id)
                        └── DialogueController(control_plane, lineage_store,
                                               journal, session_id, turn_store)
                                → recover_startup()
```

The shared `OperationJournal` is the critical wiring: `ControlPlane` creates its own at `control_plane.py:64` if not provided. The bootstrap must create one explicitly and pass it to both `ControlPlane` and the dialogue factory closure.

### Architecture: Plugin Environment Variables

| Variable | Source | Purpose | Used by |
|----------|--------|---------|---------|
| `CLAUDE_PLUGIN_ROOT` | Claude Code (auto-set) | Plugin install directory | `.mcp.json` paths, skill content |
| `CLAUDE_PLUGIN_DATA` | Claude Code (auto-set) | Persistent plugin state dir | `journal.py`, lineage, turns |
| `CODEX_SANDBOX` | `.mcp.json` env | macOS stability | Codex CLI |
| `session_id` (file) | SessionStart hook | Session identity | Bootstrap factory |

### MCP Tool Name Pattern

Plugin tools use the prefix `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`. For codex-collaboration:

| Tool | Full MCP name |
|------|--------------|
| `codex.status` | `mcp__plugin_codex-collaboration_codex-collaboration__codex.status` |
| `codex.consult` | `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult` |
| `codex.dialogue.start` | `mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.start` |

This must match `allowed-tools` in skill frontmatter exactly.

### Cross-Model Plugin Packaging Precedent

| Aspect | Cross-model | Codex-collaboration |
|--------|------------|---------------------|
| `.mcp.json` servers | 2 (codex + context-injection) | 1 (codex-collaboration) |
| Launch pattern | `uv run --directory ${CLAUDE_PLUGIN_ROOT} python ...` | Same |
| Env vars | `CODEX_SANDBOX=seatbelt` | Same |
| Hooks | None in plugin (user-level hooks) | `SessionStart` for session_id |
| Skills | 4 (codex, dialogue, delegate, consultation-stats) | 2 (consult-codex, codex-status) |

## Context

### Mental Model

This session's arc was "contract discovery before code." The user's corrections early in the session established that the bootstrap is not just "wire some constructors" — it's a contract problem with four dimensions (launch path, data path, session identity, object graph). The session-id design went through three iterations, each caught by a different contract violation, before settling on the hook-based publication scheme.

The deferred dialogue init is the architectural insight: splitting the server into session-independent (R1 tools) and session-scoped (dialogue) tiers means the plugin shell can be useful immediately while the session identity bridge is still forming. This split also means the plugin shell acceptance criteria (T-02) can be satisfied independently of the session identity scheme — `codex.status` and `codex.consult` work without it.

### Project State

| Milestone | Status | Commit/PR |
|-----------|--------|-----------|
| Spec compiled and merged | Complete | `bf8e69e3` |
| T1: Compatibility baseline | Complete | `f53cd6c8` (PR #87) |
| R1: First runtime milestone | Complete | `3490718a` |
| R2: Dialogue foundation | Complete | `f5fc5aab` (PR #89) |
| Post-R2 hardening (items 6-7) | Complete | `1f3305a8`, `e6792de8` |
| Release posture + annotations | Complete | `2994b138` |
| Supersession roadmap + tickets | Complete | `dbc91d8f` |
| **T-02: Plugin shell** | **Implemented, pending review** | `feature/codex-collaboration-plugin-shell` at `d6fb34b7` |

238 tests passing on the feature branch. Not yet committed (all changes are unstaged).

### Supersession Roadmap (unchanged from prior session)

```
T-02 (plugin shell) → T-03 (substrate) → T-04 (dialogue) ──────→ T-07 (cutover)
                                        → T-05 (execution) → T-06 (promotion) → T-07
```

## Learnings

### Claude Code provides session_id to hooks but not MCP server subprocesses

**Mechanism:** Every hook event receives `session_id` as a common field in its stdin JSON payload. But only two env vars are auto-set for plugin subprocesses: `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`. There is no `CLAUDE_SESSION_ID` env var.

**Evidence:** Claude Code docs `hooks#common-input-fields`: `session_id` is listed as a common input field. Plugin docs `plugins-reference#environment-variables`: exactly two variables documented. Full `CLAUDE_CODE_*` env var list (`env-vars` page) has ~30 entries — none is a session ID for subprocesses.

**Implication:** Any plugin that needs stable session identity for MCP servers must bridge the gap through hooks. The SessionStart hook publication pattern implemented here is reusable for other plugins with the same need.

### ControlPlane self-assembles dependencies but DialogueController does not

**Mechanism:** `ControlPlane.__init__` has defaults for `plugin_data_path`, `runtime_factory`, `compat_checker`, `repo_identity_loader`, `clock`, `uuid_factory`, and `journal` (6 of 7 parameters). `DialogueController.__init__` requires all 5 parameters with no defaults: `control_plane`, `lineage_store`, `journal`, `session_id`, `turn_store`.

**Evidence:** `control_plane.py:47-65` vs `dialogue.py:45-62`.

**Implication:** The bootstrap script can create a minimal `ControlPlane` with just `plugin_data_path` and `journal`, but `DialogueController` requires explicit wiring of every dependency. This asymmetry is what makes deferred dialogue init natural — `ControlPlane` works standalone, `DialogueController` needs the full graph.

### Atomic file replacement pattern recurs across the system

**Mechanism:** Write to `.tmp` file → `fsync` → `os.replace(tmp, target)`. Used by `OperationJournal.compact()` at `journal.py:121-127`, and now by `publish_session_id.py`. The pattern prevents readers from seeing half-written content.

**Evidence:** `journal.py:121-127` (existing), `publish_session_id.py:40-44` (new).

**Implication:** This is the correct pattern for any file that may be read by another process. Future plugin scripts that write shared state should use this pattern.

## Next Steps

### User reviews the implementation

**Dependencies:** None — this is the immediate next step.

**What to read first:** This handoff. Then the changed files: `mcp_server.py` (deferred init contract), `codex_runtime_bootstrap.py` (object graph wiring), `publish_session_id.py` (hook script), `hooks/hooks.json` (hook registration).

**Approach:** The user said "I will share my review in the next session." Review may result in changes to the implementation before committing.

**Potential obstacles:** Skill `allowed-tools` names may be wrong if the MCP tool naming convention differs from what I inferred from the cross-model precedent. Can be verified by installing with `--plugin-dir` and checking `/mcp`.

### Smoke-test via --plugin-dir

**Dependencies:** Review complete (or concurrent with review).

**Approach:** `claude --plugin-dir packages/plugins/codex-collaboration`. Check `/mcp` shows the server, run `/codex-status`, run `/consult-codex <question>`.

**Potential obstacles:** The bootstrap script adds the package root to `sys.path` to enable `from server.xxx import ...`. In the plugin cache (marketplace install), the directory structure may differ from the dev repo. The `--plugin-dir` path uses the source directly, avoiding this issue for smoke testing.

### Commit and close T-02

**Dependencies:** Review passes, smoke test passes.

**Approach:** Stage all new/modified files, commit on `feature/codex-collaboration-plugin-shell`, merge to main.

### Begin T-03 (safety substrate)

**Dependencies:** T-02 closed.

**What to read first:** `T-20260330-03` at `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md`. Key cross-model sources: `credential_scan.py`, `secret_taxonomy.py`, `consultation_safety.py`, `consultation-profiles.yaml`, `retrieve_learnings.py`, `emit_analytics.py`.

## In Progress

Clean stopping point. All implementation complete, no work in flight. 238 tests pass. Changes are unstaged on the feature branch `feature/codex-collaboration-plugin-shell`.

**User's next step:** Review the implementation and share feedback in the next session.

## Open Questions

### Whether MCP tool name prefix matches the actual Claude Code behavior

The `allowed-tools` in skill frontmatter uses `mcp__plugin_codex-collaboration_codex-collaboration__codex.status`. This prefix was inferred from the cross-model precedent (`mcp__plugin_cross-model_codex__codex`). If the actual prefix differs (e.g., if hyphens in plugin/server names are handled differently), the skills won't auto-approve tool calls. Smoke test will reveal this.

### Feature branch cleanup timing (inherited)

`feature/codex-collaboration-r2-dialogue` still exists on remote. Tagged at `r2-dialogue-branch-tip` → `d2d0df56`. Can be deleted anytime.

### Concurrent session identity race (tracked)

Two simultaneous Claude sessions sharing this plugin will race on `${CLAUDE_PLUGIN_DATA}/session_id`. Documented in the T-02 carry-forward limitations. Not actionable until Claude Code provides per-session data directories.

## Risks

### allowed-tools mismatch could silently break skill auto-approval

If the MCP tool name prefix doesn't match the `allowed-tools` declaration, the tools would still be available but every call would prompt for permission instead of auto-approving. The skills would appear to work but with degraded UX. Smoke test is the verification.

### sys.path manipulation in bootstrap may break in plugin cache

The bootstrap adds the package root to `sys.path` to enable `from server.xxx import ...`. In the dev repo, this works. In a marketplace plugin cache (`~/.claude/plugins/cache/...`), the directory structure is preserved (symlinks honored), but if the package root isn't importable for some other reason, the server won't start.

### Three independent copies of credential-detection logic (inherited)

After T-03 lands, `context_assembly.py`, `redact.py`, and the new safety substrate will have partially overlapping pattern sets. Inherited risk from prior session.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Prior handoff (resumed from) | `docs/handoffs/archive/2026-03-30_14-59_item6-landed-release-posture-supersession-roadmap.md` | Context for T-02 start |
| T-02 ticket | `docs/tickets/2026-03-30-codex-collaboration-plugin-shell-and-consult-parity.md` | Acceptance criteria and carry-forward |
| Delivery spec (normative structure) | `docs/superpowers/specs/codex-collaboration/delivery.md` | Plugin component structure at lines 27-65 |
| Cross-model plugin.json (precedent) | `packages/plugins/cross-model/.claude-plugin/plugin.json` | Packaging pattern |
| Cross-model .mcp.json (precedent) | `packages/plugins/cross-model/.mcp.json` | Launch pattern |
| Cross-model codex skill (precedent) | `packages/plugins/cross-model/skills/codex/SKILL.md` | allowed-tools naming |
| Claude Code plugin docs | `plugins-reference#environment-variables` | CLAUDE_PLUGIN_DATA, CLAUDE_PLUGIN_ROOT |
| Claude Code hooks docs | `hooks#common-input-fields` | session_id availability |
| T-03 ticket (next) | `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md` | Safety substrate scope |

## Gotchas

### The ControlPlane creates its own journal if not given one

`ControlPlane.__init__` at `control_plane.py:64`: `self._journal = journal or OperationJournal(self._plugin_data_path)`. If the bootstrap doesn't explicitly pass a journal, the ControlPlane and DialogueController would use different journal instances, writing to the same files from different objects. The bootstrap must create one `OperationJournal` and share it.

### Hook uses python3 not uv run

The SessionStart hook at `hooks/hooks.json` uses `python3` directly, not `uv run`. This is intentional — hooks should be lightweight and fast. The script has zero stdlib dependencies. If future hook scripts need third-party deps, they must use `uv run` or a SessionStart install hook (like the `node_modules` pattern in the Claude Code docs).

### The dialogue factory closure captures mutable state

`_build_dialogue_factory` closes over `plugin_data_path`, `control_plane`, and `journal`. All three are shared with the main server. `control_plane` is mutable (caches advisory runtimes). If the factory is called after the control plane has cached a runtime for a repo, the dialogue controller inherits that cached state. This is correct behavior — the dialogue controller should share the advisory runtime with consult.

### scripts/publish_session_id.py must be executable

The hook runs via `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/publish_session_id.py"`. If the file loses its executable bit during plugin cache copy, the hook may fail. This should be a non-issue (the hook uses `python3 <script>` not `./<script>`) but is worth noting.

## Conversation Highlights

**On bootstrap location:**
User: "Don't treat `server/__main__.py` as the default bootstrap location yet. The normative install shape currently points to `scripts/codex_runtime_bootstrap.py`, not a package `__main__`. If we choose `server/__main__.py`, that is a deliberate spec deviation, not an implementation detail."

**On UUID-at-process-start rejection:**
User: "A process-scoped UUID would make every MCP server restart look like a brand-new Claude session. `recover_startup()` would scan the wrong lineage/journal partition, leaving the prior data orphaned. That is not a tolerable dev-rollout tradeoff; it is a regression against the already accepted R2 semantics."

**On deferred init pin requirement:**
User: "Lazy init must be one-way and pinned. If the identity file later changes, do not hot-switch to a new partition mid-process. Refuse and error instead."

**On SessionStart hook acceptability:**
User: "A narrow SessionStart hook is acceptable in T-02. It is bootstrap glue, not the credential-scanning hook substrate that was deliberately deferred."

**On not blocking startup:**
User: "Blocking startup would widen the failure domain of packet 2a for no gain. `codex.status` and `codex.consult` are the ticket's packaged success path and they do not need session-scoped state."

**On concurrent session tracking:**
User: "It is not big enough to become its own roadmap packet, but it is too material to leave implicit."

## User Preferences

**Evidence-level rigor (continued):** User holds all design decisions to defensible evidence standards. Rejected UUID-at-process-start with four specific contract violations. Insists on explicit acknowledgment of limitations.

**Spec alignment over convenience:** User values spec alignment — "if we choose `server/__main__.py`, that is a deliberate spec deviation, not an implementation detail." Follow the normative documents unless there's a conscious decision to deviate.

**Contract-first thinking:** User frames problems through contract obligations. The session_id rejection cited 4 contract references and 1 test encoding the contract. Design decisions are evaluated against existing contracts, not just current-session convenience.

**Grounded pushback (continued):** User pushes back with file:line references and specific reasoning. Corrections include evidence, not just assertions.

**Scope splitting by risk profile (continued):** "The plugin shell and the shared safety substrate have different risk profiles and are tracked separately on purpose."

**Carry-forward discipline:** Limitations should be tracked explicitly, even when small. "Too material to leave implicit."

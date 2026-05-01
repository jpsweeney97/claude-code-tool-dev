# Codex App Server Client-Platform Exploration

**Date:** 2026-05-01
**Status:** Exploration packet complete; not an architecture spec
**Worktree:** `/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/codex-app-server-client-platform-exploration`
**Parent branch at setup:** `fix/delegation-turn-start-probe`
**Parent commit at setup:** `394868b517f62d97acd601ae36c0c640f899fbfa`
**Pinned upstream source:** `openai/codex@ff27d01676a93be7467b3893e82f41a7af7e1418`

This packet answers the exploration-plan questions about artifact selection, source taxonomy, generated schema surface, and the runtime probes still needed before a broader `codex-collaboration` client-platform rebaseline spec is credible.

## Input Provenance

This worktree was created from the current local branch, not from a clean `HEAD` that already contained the plan inputs. At setup time, the three required input artifacts were untracked in the parent workspace, so they were copied into this worktree with `cp -p` from the parent workspace. They were **not** sourced from committed repo history and should not be described as coming from `HEAD`.

Parent workspace status at copy time:

```text
## fix/delegation-turn-start-probe
?? docs/architecture/
?? docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md
?? docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md
```

Worktree status immediately after copying the required inputs:

```text
## feature/codex-app-server-client-platform-exploration
?? docs/architecture/
?? docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md
?? docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md
```

Copied inputs and their worktree state:

| Path | Setup provenance | Worktree git state |
|---|---|---|
| `docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md` | Copied from parent workspace because the file was untracked there at setup time | untracked file |
| `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md` | Copied from parent workspace because the file was untracked there at setup time | untracked file |
| `docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md` | Copied from parent workspace because the file was untracked there at setup time; this branch did not already contain a tracked `docs/architecture/` directory at that path | reported under untracked `docs/architecture/` |

Worktree file presence was confirmed after copy:

```text
docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md|21723|May  1 11:55:26 2026
docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md|47409|May  1 02:13:14 2026
docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md|11434|May  1 02:12:59 2026
```

## Preflight Observations

- Local launcher check passed the plan stop condition: `codex --version` returned `codex-cli 0.128.0`.
- Scratch workspace created at `/private/tmp/codex-app-server-exploration`.
- Pinned source sparse checkout was created at `/private/tmp/codex-app-server-exploration/openai-codex-ff27d016`.
- Source inventory was saved to `/private/tmp/codex-app-server-exploration/pinned-source-file-list.txt` and currently contains `238` files under the selected sparse paths.
- Release lookup nuance: `gh release view 0.128.0 --repo openai/codex` returned `release not found`, while `gh release list` and `gh release view rust-v0.128.0 --repo openai/codex` confirmed that release **name** `0.128.0` is published under **tag** `rust-v0.128.0`.

## Current codex-collaboration Touchpoints

The current plugin already depends on a narrow but concrete subset of the app-server surface:

- `packages/plugins/codex-collaboration/server/runtime.py:150-214` performs `initialize`, `account/read`, `thread/start`, and `thread/fork`.
- `packages/plugins/codex-collaboration/server/runtime.py:232-317` runs advisory and execution `turn/start` calls and still sends `sandboxPolicy`.
- `packages/plugins/codex-collaboration/server/runtime.py:380-414` and `packages/plugins/codex-collaboration/server/dialogue.py` rely on `thread/read` for fallback extraction and recovery.
- `packages/plugins/codex-collaboration/server/control_plane.py:191-199,315-319` bootstraps advisory and execution runtimes through `thread/start`.
- `packages/plugins/codex-collaboration/server/delegation_controller.py:1367-1370` routes live execution through `run_execution_turn(..., sandbox_policy=build_workspace_write_sandbox_policy(worktree_path))`.

## Artifact Selection Implication

PR #19447 makes standalone `codex-app-server` an official release artifact. Therefore, future `codex-collaboration` runtime design must choose whether it targets `codex app-server`, standalone `codex-app-server`, or both with equivalence checks.

## Release And Artifact Provenance

| Subject | Finding | Evidence |
|---|---|---|
| PR #19447 | Merged as `ci: publish codex-app-server release artifacts` on `2026-04-24T22:29:38Z`; changed files are release workflow, code-signing actions, and `.github/dotslash-config.json` | `gh pr view 19447 --repo openai/codex --json ...`; merge commit `9b8a1fbefcd507a5c7550b9c64e70f111094f195` |
| Release `0.128.0` | Published `2026-04-30T16:40:28Z`; release name `0.128.0`, tag `rust-v0.128.0`, `98` assets | `gh release view rust-v0.128.0 --repo openai/codex --json ...` |
| Standalone app-server assets | Release metadata explicitly includes `codex-app-server` assets for macOS, Linux, and Windows | `release-rust-v0.128.0.json`; standalone asset digests captured in the JSON companion |
| Installed launcher | `/opt/homebrew/bin/codex` present locally; `codex-cli 0.128.0`; `codex app-server --help` captured and hashed | local command outputs under `/private/tmp/codex-app-server-exploration/` |
| Standalone local presence | `codex-app-server` is **not** installed locally in this session | `command -v codex-app-server` returned empty |

## Launcher Snapshot

- Selected first schema launcher: installed `codex app-server` from `/opt/homebrew/bin/codex`
- `codex --version`: `codex-cli 0.128.0`
- `codex` binary SHA-256: `ff803d4b5c595af19b99c18db6def26539fdf4da23a035ab30809835631e8e4b`
- `codex app-server --help` SHA-256: `f231ba38338e0549ef7d6948bfed3b143f9cb9e7b5ac17dadfd0009f26f060eb`
- Stable schema directory: `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable`
- Experimental schema directory: `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental`
- Stable schema hash file: `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable.sha256` (`234` entries)
- Experimental schema hash file: `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental.sha256` (`269` entries)

`codex app-server --help` currently advertises:

```text
--listen <URL>
  Transport endpoint URL. Supported values: `stdio://` (default), `unix://`, `unix://PATH`,
  `ws://IP:PORT`, `off`
```

## Evidence Frame Comparison

| Frame | Identifier | How captured | Current status | Can support |
|---|---|---|---|---|
| Pinned source | `ff27d01676a93be7467b3893e82f41a7af7e1418` | local sparse checkout in `/private/tmp/codex-app-server-exploration/openai-codex-ff27d016` | captured | static reading |
| PR #19447 | `9b8a1fbefcd507a5c7550b9c64e70f111094f195` | `gh pr view 19447 --repo openai/codex` | captured | artifact-selection implication |
| Release `0.128.0` | `rust-v0.128.0` | `gh release view rust-v0.128.0 --repo openai/codex` | captured | release context |
| Installed `codex app-server` | `/opt/homebrew/bin/codex` + help/version/hash evidence | local commands | captured | generated schemas, future runtime probes for this launcher |
| Standalone `codex-app-server` | release assets present; local binary absent | release metadata + local command | absent locally, available in release | schema/runtime only if explicitly installed or downloaded later |

## Static Source Map

| Area | Source files | What it appears to own | Must verify by schema/runtime? |
|---|---|---|---|
| Launcher and transport | `codex-rs/cli/src/main.rs:868-880,1492-1506`; `codex-rs/app-server/src/lib.rs:611-660`; `codex-rs/app-server/src/transport/stdio.rs:21-93`; `codex-rs/app-server/README.md:26-34` | CLI subcommands, transport selection, stdio bootstrap, and documented transport modes (`stdio`, `unix`, `ws`, `off`) | yes |
| Initialization and capabilities | `codex-rs/app-server-protocol/src/protocol/v1.rs:23-55`; `codex-rs/app-server-protocol/src/protocol/common.rs:426-435`; `codex-rs/app-server/src/transport/stdio.rs:87-111`; `codex-rs/app-server/README.md:97-97` | `initialize` / `initialized`, `experimentalApi`, `optOutNotificationMethods`, `codexHome`, and client identity | yes |
| Schema generation | `codex-rs/cli/src/main.rs:868-880`; `codex-rs/app-server-protocol/src/export.rs:118-203`; `codex-rs/app-server-protocol/src/schema_fixtures.rs:64-102` | `generate-ts`, `generate-json-schema`, schema bundle export, and protocol fixture generation | yes |
| Thread lifecycle | `codex-rs/app-server-protocol/src/protocol/common.rs:434-570`; `codex-rs/app-server-protocol/src/protocol/v2.rs:3547-3883`; `codex-rs/app-server/src/codex_message_processor.rs:2495-2588,4274-4550,4921-4960` | request/response registration and handler paths for `thread/start`, `thread/resume`, `thread/fork`, `thread/read`, and related thread controls | yes |
| Turn lifecycle | `codex-rs/app-server-protocol/src/protocol/common.rs:717-764`; `codex-rs/app-server-protocol/src/protocol/v2.rs:5528-5563`; `codex-rs/app-server/src/codex_message_processor.rs:6640-6718` | request/response registration and handler paths for `turn/start`, `turn/steer`, and `turn/interrupt` | yes |
| Permissions and profiles | `codex-rs/app-server-protocol/src/protocol/v2.rs:1789-1817,3576,3729,3832,5561`; `codex-rs/app-server/src/codex_message_processor.rs:9631-9645` | named permission-profile selection, bounded modifications, and mapping to `ConfigOverrides.default_permissions` plus `additional_writable_roots` | yes |
| Server requests and approvals | `codex-rs/app-server-protocol/src/protocol/common.rs:988-1259`; `codex-rs/core/src/session/mcp.rs:8-118`; `codex-rs/app-server/src/thread_state.rs:143-165` | server-initiated request taxonomy, MCP elicitation plumbing, approval flows, and request resolution notifications | yes |
| Command execution | `codex-rs/app-server-protocol/src/protocol/common.rs:879-898`; `codex-rs/app-server-protocol/src/protocol/v2.rs:3374-3450`; `codex-rs/app-server/src/codex_message_processor.rs:2212-2433`; `codex-rs/app-server/src/command_exec.rs:145-190` | `command/exec` method surface, per-command sandbox controls, streaming/PTY controls, and handler startup | yes |
| Config/trust/Codex home | `codex-rs/app-server-protocol/src/protocol/v1.rs:58-76`; `codex-rs/app-server/src/codex_message_processor.rs:2742-2779`; `codex-rs/app-server/src/config_manager_service.rs:279-312`; `codex-rs/app-server/src/config_api.rs:755-812` | `codexHome` exposure, trust persistence on `thread/start`, config read/write, and user-config mutation | yes |
| Release packaging | `.github/workflows/rust-release.yml:80-117,563-570`; `.github/dotslash-config.json:31-55`; PR #19447 file list | release bundle selection, standalone app-server publication, and DotSlash release mapping | no, packaging provenance only |

## Generated Schema Snapshot

Stable and experimental schemas were generated from the installed `codex app-server` launcher, not from the pinned source checkout.

### Request-property comparison

| Type | Stable keys | Experimental-only additions | Notes |
|---|---|---|---|
| `ThreadStartParams` | `approvalPolicy`, `approvalsReviewer`, `baseInstructions`, `config`, `cwd`, `developerInstructions`, `ephemeral`, `model`, `modelProvider`, `personality`, `sandbox`, `serviceName`, `serviceTier`, `sessionStartSource` | `dynamicTools`, `environments`, `experimentalRawEvents`, `mockExperimentalField`, `permissions`, `persistExtendedHistory` | Stable request shape does **not** expose `permissions` |
| `TurnStartParams` | `approvalPolicy`, `approvalsReviewer`, `cwd`, `effort`, `input`, `model`, `outputSchema`, `personality`, `sandboxPolicy`, `serviceTier`, `summary`, `threadId` | `collaborationMode`, `environments`, `permissions`, `responsesapiClientMetadata` | Stable request shape does **not** expose `permissions` |
| `CommandExecParams` | `command`, `cwd`, `disableOutputCap`, `disableTimeout`, `env`, `outputBytesCap`, `processId`, `sandboxPolicy`, `size`, `streamStdin`, `streamStdoutStderr`, `timeoutMs`, `tty` | `permissionProfile` | Raw command-scoped `permissionProfile` is experimental and not a turn/thread request path |

### Response-property comparison

| Type | Stable keys | Experimental-only additions | Notes |
|---|---|---|---|
| `ThreadStartResponse`, `ThreadResumeResponse`, `ThreadForkResponse` | `approvalPolicy`, `approvalsReviewer`, `cwd`, `instructionSources`, `model`, `modelProvider`, `reasoningEffort`, `sandbox`, `serviceTier`, `thread` | `permissionProfile`, `activePermissionProfile` | Thread-level permission provenance is not exposed on the stable response surface |
| `TurnStartResponse` | `turn` | none captured in the stable bundle | Turn response still does not project active/effective permission provenance |

### Schema cautions

- The stable bundles still contain some shared permission-related definitions (for example `PermissionProfileSelectionParams` or `ActivePermissionProfile` helper definitions) even when the concrete stable request/response property sets do not expose the associated fields.
- Therefore, concrete property presence must be read from the per-type property sets, not inferred from shared definition names alone.

## Surface Classification Draft

| Surface | Initial class | Evidence frame | Why it matters to codex-collaboration | Verification still needed |
|---|---|---|---|---|
| `initialize` / `initialized` | required | source + schema + local launcher docs | `runtime.py` begins every session with this handshake and depends on `codexHome`, `platformFamily`, `platformOs`, and `userAgent` | Live handshake and pre-initialize rejection probe on the selected launcher |
| `capabilities.experimentalApi` | required-for-A1 | source + schema + docs | Gates experimental request fields and response provenance for permission-branch exploration | Live initialize probe with and without `experimentalApi = true` |
| `optOutNotificationMethods` | future_scope | source + schema + docs | Could reduce notification noise for richer clients, but current plugin does not need it | Probe exact suppression behavior before any adoption |
| stdio transport | required | local help + source + docs | Current plugin subprocess model depends on stdio transport | Live round-trip probe over stdio |
| websocket / unix / off transports | future_scope | local help + source + docs | Possible alternate client topology for standalone app-server or controller processes | Explicit design choice before adopting any non-stdio transport |
| `thread/start` | required | source + schema + current plugin code | Control-plane bootstrap and advisory-thread creation already rely on it | Live acceptance and response-shape probe |
| `thread/resume` | required | source + schema + current plugin code | Recovery and continuation flows depend on it even if the current advisory happy path starts fresh threads | Live resume probe with stored thread state |
| `thread/fork` | required | source + schema + current plugin code | Advisory branch/fork behavior already relies on it | Live fork probe including `ephemeral` behavior |
| `thread/read` or turn listing | required | source + schema + current plugin code | Reply extraction, crash recovery, and diagnostics already depend on it | Live projection-shape probe, including `includeTurns` or equivalent turn listing |
| `turn/start` | required | source + schema + current plugin code | Both advisory and execution flows currently send `turn/start` | Live acceptance and notification-shape probe |
| `turn/interrupt` | required | source + schema + current plugin code | Current runtime already calls it for cleanup/cancellation | Live cancellation probe against in-flight work |
| `review/start` | unknown | source + schema | Could overlap future codex-review or review-mode integration, but current plugin does not yet own that flow | Run a scratch-thread `review/start` probe and compare emitted turn/item shapes before classifying |
| `command/exec` | diagnostic | source + schema | Useful for deterministic sandbox and permission diagnostics without threading full collaboration flows | Live probe under scratch home; keep separate from production turn routing |
| `thread/shellCommand` | dangerous | source + schema + docs | Runs unsandboxed shell syntax on a thread and bypasses the normal execution boundary | Separate security design required; do not call from production clients until separately designed |
| permissions / profile fields | required-for-v128 | source + schema | The execution security boundary and provenance story depend on these fields | Live v128 decision-packet probes for stable `sandboxPolicy`, experimental `permissions`, and profile provenance |
| config / trust APIs | dangerous | source + schema | Can mutate user config, Codex-home trust state, and effective feature settings | Scratch-home probe only; do not call from production clients until separately designed |
| fs APIs | dangerous | source + schema | Absolute-path read/write/remove surface could bypass current plugin guardrails if adopted casually | Separate security design required; do not call from production clients until separately designed |
| server requests and approvals | required | source + schema | Execution can stall or mis-handle approvals unless the client can classify and respond to server-initiated requests correctly | Live taxonomy and unknown-handling probe on the selected launcher |
| skills / plugins / apps / MCP APIs | future_scope | source + schema | Important for broader app-server clients, but not the immediate `codex-collaboration` delegate blocker | Classify later once the core execution surface is settled |
| realtime APIs | future_scope | source + schema + docs | Separate modality and transport story, outside the current collaboration plugin’s scope | Classify later with an explicit realtime design |
| auth endpoints | diagnostic | source + schema + current plugin code | Current plugin already uses `account/read`, but does not own login/token-refresh flows | Probe only if platform ownership expands beyond auth-state reads |
| external agent import | future_scope | source + schema | Interesting for migration tooling, not current delegate execution | Classify later if import/export becomes in-scope |

## Runtime Probe Backlog

| Probe | Selected launcher required? | Scratch Codex home required? | Auth required? | Blocks architecture spec? | Blocks implementation? |
|---|---:|---:|---:|---:|---:|
| initialize then initialized | yes | no | no | yes | yes |
| request before initialize rejection | yes | no | no | yes | yes |
| stable schema request accepted path `[v128 decision packet]` | yes | yes | maybe | no | yes |
| experimentalApi gating `[v128 decision packet]` | yes | yes | maybe | no | yes |
| permission profile provenance `[v128 decision packet]` | yes | yes | maybe | no | yes |
| server-request taxonomy and unknown handling | yes | yes | maybe | yes | yes |
| trust/config mutation check | yes | yes | no | yes | yes |
| command/exec diagnostics `[v128 decision packet]` | yes | yes | no | no | yes |
| thread/read projection shape | yes | yes | maybe | yes | yes |

Probe ownership note:

- The v128 decision packet owns the permission-branch probes tagged above.
- `trust/config mutation check` is shared: it is a v128 safety concern and also a client-platform architecture blocker because `thread/start` can persist trust into Codex home.

## Architecture Spec Readiness

**Not ready to draft architecture spec.**

Reasons:

1. The static source map and generated schema evidence are in place, but the selected launcher still lacks live handshake proof for `initialize` / `initialized` and pre-initialize rejection.
2. The server-request taxonomy is source/schema-visible, but current handling of actual runtime request sequences and unknown-request behavior is still unproven in this packet.
3. `thread/read` projection shape is architecture-relevant for reply extraction and recovery, but only schema/static evidence exists here.
4. Trust/config mutation behavior is source-visible and risky, but still needs a scratch-home live probe before any architecture spec can describe a safe runtime posture.
5. Standalone `codex-app-server` is visible as an official release artifact, but equivalence with `codex app-server` is not proven because the standalone launcher is not installed locally in this session.

The exploration packet itself is ready for review; the architecture spec is still blocked on the live-runtime backlog above.

## Durable Outputs

- Markdown diagnostic: `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- Structured JSON companion: `docs/diagnostics/codex-app-server-client-platform-exploration.json`
- Scratch evidence directory: `/private/tmp/codex-app-server-exploration/`

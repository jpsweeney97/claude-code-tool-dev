# Codex App Server Client-Platform Exploration Plan

> This is an exploration plan, not an architecture spec and not an implementation migration plan. Do not draft the client-platform rebaseline architecture spec until this plan's exploration artifacts are complete and reviewed.

**Goal:** Produce a repo-grounded exploration packet that identifies the actual Codex App Server client-platform surface we must understand before writing the broader `codex-collaboration` rebaseline spec.

**Architecture:** Treat source, release artifacts, generated schemas, and live runtime behavior as separate evidence frames. Use the pinned upstream source for static exploration, the selected launcher artifact for generated schemas and runtime probes, and explicit diagnostics artifacts for conclusions.

**Tech Stack:** GitHub release metadata, pinned OpenAI Codex source checkout, Codex App Server JSON-RPC schema generation, local `codex` launcher inspection, Markdown diagnostics, JSON evidence packets.

---

## Boundary

This plan answers:

- What app-server artifact or artifacts are plausible runtime targets?
- What changed when `codex-app-server` became a standalone release artifact?
- What source areas must be understood before an architecture spec is credible?
- Which protocol surfaces are required, optional, unsupported, dangerous, or unknown for `codex-collaboration`?
- Which facts require generated schema or live runtime proof rather than GitHub source reading?

This plan does not:

- Select Branch A1/A2/A3/B/C/D from `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.
- Implement any adapter, sandbox, permission, launcher, or config change.
- Refresh vendored fixtures.
- Close T-20260429-01.
- Produce the final client-platform rebaseline architecture spec.

## Evidence Frames

Keep these frames separate in every note and artifact:

| Frame | Meaning | Allowed use | Not allowed |
|---|---|---|---|
| Pinned upstream source | `openai/codex` at `ff27d01676a93be7467b3893e82f41a7af7e1418` | Static implementation reading, call graph, source taxonomy | Claiming local runtime behavior |
| PR #19447 | Release-plumbing change that publishes standalone `codex-app-server` artifacts | Artifact/provenance implication | Protocol equivalence claim |
| Release notes | GitHub release metadata for `0.128.0` and related tags | Release artifact context | Runtime behavior proof |
| Installed `codex app-server` | Local `/opt/homebrew/bin/codex app-server` or equivalent | Local schema/runtime target if selected | Assuming standalone artifact equivalence |
| Standalone `codex-app-server` | Official release artifact when installed or downloaded | App-like runtime target if selected | Assuming it is already present |
| Generated schemas | Stable and experimental output from a selected launcher | Request/response surface evidence for that launcher | Security-boundary proof by itself |
| Live runtime probes | JSON-RPC interaction with selected launcher | Handshake, rejection, server-request, trust/config behavior | Broad source-platform inventory by itself |

## Output Artifacts

Create these in the fresh exploration session:

- `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
  - Human-readable exploration record.
- `docs/diagnostics/codex-app-server-client-platform-exploration.json`
  - Structured summary of artifact provenance, schema locations, source taxonomy, and open questions.
- `/private/tmp/codex-app-server-exploration/`
  - Scratch checkout, generated schemas, command outputs, and raw notes. This is not a durable repo artifact.

Do not create these yet:

- `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md`
- `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md`

## Preflight

- [ ] Confirm repository state.

```bash
git status --short --branch
```

Expected: note the current branch and any existing untracked docs. Do not clean or stage unrelated files.

- [ ] Read the existing permission-scope artifacts.

```bash
sed -n '1,240p' docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md
sed -n '1,220p' docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md
sed -n '1,220p' docs/codex-app-server.md
```

Expected: preserve the v128 permission packet as a sub-workstream, not the whole platform exploration.

- [ ] Create the scratch directory.

```bash
mkdir -p /private/tmp/codex-app-server-exploration
```

Expected: directory exists. Do not use repo-local scratch paths for upstream source.

## Task 1: Capture Release And Artifact Provenance

**Purpose:** Determine what PR #19447 changes for target artifact selection.

- [ ] Capture PR metadata.

```bash
gh pr view 19447 --repo openai/codex --json number,title,state,mergedAt,mergeCommit,commits,files,url
```

Expected:
- State is merged.
- The title refers to publishing `codex-app-server` release artifacts.
- Changed files include release workflow or packaging paths.

If `gh` cannot access the PR, use the browser or web fetch and record that fallback in the diagnostic artifact.

- [ ] Capture release metadata for `0.128.0`.

```bash
gh release view 0.128.0 --repo openai/codex --json tagName,targetCommitish,isPrerelease,isDraft,publishedAt,name,url,assets
```

Expected:
- The record identifies the release/tag frame used for `0.128.0`.
- The diagnostic artifact records whether standalone `codex-app-server` assets are visible from the release metadata.

- [ ] Capture local launcher presence.

```bash
which codex
codex --version
codex app-server --help
command -v codex-app-server || true
```

Expected:
- `codex` is present.
- `codex --version` is recorded.
- `codex app-server --help` is recorded or hashed.
- `codex-app-server` may be absent; absence is a finding, not a blocker.

- [ ] Record artifact-selection implication.

Add to `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`:

```markdown
## Artifact Selection Implication

PR #19447 makes standalone `codex-app-server` an official release artifact. Therefore, future `codex-collaboration` runtime design must choose whether it targets `codex app-server`, standalone `codex-app-server`, or both with equivalence checks.
```

## Task 2: Clone Pinned Source For Static Exploration

**Purpose:** Get a local searchable source corpus without vendoring upstream code into this repo.

- [ ] Create or reuse the pinned sparse checkout.

```bash
SRC=/private/tmp/codex-app-server-exploration/openai-codex-ff27d016
if test -d "$SRC/.git"; then
  git -C "$SRC" fetch origin
else
  git clone --filter=blob:none --sparse https://github.com/openai/codex.git "$SRC"
fi
git -C "$SRC" sparse-checkout set \
  codex-rs/app-server \
  codex-rs/app-server-protocol \
  codex-rs/app-server-test-client \
  codex-rs/core \
  codex-rs/protocol \
  codex-rs/cli \
  codex-cli \
  .github/workflows \
  .github/actions \
  .github/dotslash-config.json
git -C "$SRC" checkout ff27d01676a93be7467b3893e82f41a7af7e1418
git -C "$SRC" rev-parse HEAD
```

Expected:
- Final `rev-parse HEAD` is exactly `ff27d01676a93be7467b3893e82f41a7af7e1418`.
- If sparse checkout misses a referenced crate or file, add that path explicitly and record why.

- [ ] Save a source inventory.

```bash
find "$SRC/codex-rs" -maxdepth 3 -type f | sort > /private/tmp/codex-app-server-exploration/pinned-source-file-list.txt
```

Expected:
- File list exists and includes app-server, app-server-protocol, app-server-test-client, core, protocol, and CLI paths.

## Task 3: Build A Static Source Map

**Purpose:** Replace vague "dense app-server surface" language with a source-backed taxonomy.

- [ ] Locate protocol definitions and generated-schema entrypoints.

```bash
rg -n "generate-json-schema|generate_ts|experimentalApi|PermissionProfileSelectionParams|TurnStartParams|ThreadStartParams|CommandExecParams" "$SRC/codex-rs"
```

Expected:
- Record file paths and line references for schema generation, experimental gating, permission profile selection, turn start, thread start, and command exec.

- [ ] Locate runtime request routing and server-request handling.

```bash
rg -n "initialize|initialized|thread/start|turn/start|command/exec|ServerRequest|requestApproval|elicitation|tool/requestUserInput" "$SRC/codex-rs/app-server" "$SRC/codex-rs/app-server-protocol" "$SRC/codex-rs/core"
```

Expected:
- Record file paths and line references for handshake, request dispatch, turn lifecycle, command execution, and server-initiated requests.

- [ ] Locate config, trust, and permission-profile plumbing.

```bash
rg -n "default_permissions|activePermissionProfile|permissionProfile|trusted|trust|codexHome|config.toml|PermissionProfile" "$SRC/codex-rs"
```

Expected:
- Record file paths and line references for config-derived permission selection, active-profile projection, and trust persistence behavior.

- [ ] Locate standalone app-server packaging evidence.

```bash
rg -n "codex-app-server|app-server bundle|dotslash|rust-release" "$SRC/.github" "$SRC/codex-cli" "$SRC/codex-rs"
```

Expected:
- Record release workflow, signing, staging, and DotSlash references.

- [ ] Add a source map section to the diagnostic markdown:

```markdown
## Static Source Map

| Area | Source files | What it appears to own | Must verify by schema/runtime? |
|---|---|---|---|
| Launcher and transport |  |  | yes |
| Initialization and capabilities |  |  | yes |
| Schema generation |  |  | yes |
| Thread lifecycle |  |  | yes |
| Turn lifecycle |  |  | yes |
| Permissions and profiles |  |  | yes |
| Server requests and approvals |  |  | yes |
| Command execution |  |  | yes |
| Config/trust/Codex home |  |  | yes |
| Release packaging |  |  | no, packaging provenance only |
```

Fill every row with concrete file paths and line references. Do not leave blank rows in the committed diagnostic artifact.

## Task 4: Generate Schemas From The Selected Local Launcher

**Purpose:** Determine what the installed or selected runtime artifact says its protocol is.

- [ ] Select the first schema launcher.

Default for this session:

```text
codex app-server from the installed codex-cli
```

If standalone `codex-app-server` is installed or explicitly downloaded during the session, repeat this task for that launcher too.

- [ ] Generate stable schema from `codex app-server`.

```bash
SCHEMA_ROOT=/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server
mkdir -p "$SCHEMA_ROOT/stable" "$SCHEMA_ROOT/experimental"
codex app-server generate-json-schema --out "$SCHEMA_ROOT/stable"
codex app-server generate-json-schema --out "$SCHEMA_ROOT/experimental" --experimental
find "$SCHEMA_ROOT" -type f | sort
```

Expected:
- Stable and experimental schema bundles exist.
- The diagnostic records the exact commands and output directories.

- [ ] Hash generated schemas.

```bash
find "$SCHEMA_ROOT/stable" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$SCHEMA_ROOT/stable.sha256"
find "$SCHEMA_ROOT/experimental" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$SCHEMA_ROOT/experimental.sha256"
```

Expected:
- Hash files exist.
- The structured JSON artifact references these hash files.

- [ ] Extract top-level API and permission-relevant schema facts.

Use `rg` first:

```bash
rg -n '"TurnStartParams"|"ThreadStartParams"|"ThreadForkParams"|"ThreadResumeParams"|"CommandExecParams"|"PermissionProfileSelectionParams"|"ServerRequest"|"InitializeParams"' "$SCHEMA_ROOT"
```

Expected:
- The diagnostic identifies which schema files define or reference the key request and server-request types.
- Do not infer semantics from field names alone; source and runtime proof remain separate.

## Task 5: Compare Source Snapshot, Release Tag, And Local Binary Frames

**Purpose:** Prevent accidental conflation of `ff27d016`, `0.128.0`, release tag, and installed binary.

- [ ] Record local binary hashes where possible.

```bash
CODEX_PATH=$(which codex)
shasum -a 256 "$CODEX_PATH"
```

Expected:
- The diagnostic records the resolved path and binary hash for `codex`.

- [ ] Record source and release frame identifiers.

```bash
git -C "$SRC" rev-parse HEAD
git -C "$SRC" log -1 --oneline
```

Expected:
- The diagnostic records pinned source commit and commit subject.

- [ ] If a standalone artifact is downloaded, record its path and hash.

```bash
which codex-app-server
if command -v codex-app-server >/dev/null; then
  codex-app-server --help
  shasum -a 256 "$(command -v codex-app-server)"
else
  printf '%s\n' 'codex-app-server not installed'
fi
```

Expected:
- If absent, record `standalone_launcher.status = "not_installed"`.
- If present, record path, help output hash, and binary hash.

- [ ] Add a frame comparison table:

```markdown
## Evidence Frame Comparison

| Frame | Identifier | How captured | Current status | Can support |
|---|---|---|---|---|
| Pinned source | ff27d01676a93be7467b3893e82f41a7af7e1418 | local sparse checkout | captured | static reading |
| PR #19447 |  | gh/web | captured | artifact-selection implication |
| Release 0.128.0 |  | gh/web | captured | release context |
| Installed codex app-server |  | local command | captured | schema/runtime if selected |
| Standalone codex-app-server |  | local command or release artifact | absent/present | schema/runtime if selected |
```

Do not proceed to architecture-spec drafting unless this table is filled.

## Task 6: Classify The Platform Surface

**Purpose:** Create the classification input the future architecture spec will need.

- [ ] Classify each surface as `required`, `diagnostic`, `unsupported`, `dangerous`, `future_scope`, or `unknown`.

Use this exact table in the diagnostic markdown:

```markdown
## Surface Classification Draft

| Surface | Initial class | Evidence frame | Why it matters to codex-collaboration | Verification still needed |
|---|---|---|---|---|
| `initialize` / `initialized` | required | source + schema | connection contract | live probe |
| `capabilities.experimentalApi` | required-for-A1 | source + schema | gates experimental permission fields | live probe |
| `optOutNotificationMethods` | future_scope | source + schema | may reduce stream noise | live probe before use |
| stdio transport | required | local help + docs | current subprocess client shape | live probe |
| websocket/unix/off transports | future_scope | local help/source | possible standalone-client options | explicit design decision |
| `thread/start` | required | source + schema | execution/advisory thread creation | live probe |
| `thread/resume` | required | source + schema | recovery and continuation | live probe |
| `thread/fork` | required | source + schema | advisory fork behavior | live probe |
| `thread/read` or turn listing | required | source + schema | fallback extraction and diagnostics | live probe |
| `turn/start` | required | source + schema | advisory and execution turns | live probe |
| `turn/interrupt` | required | source + schema | cancellation and cleanup | live probe |
| `review/start` | unknown | source + schema | may overlap codex-review flows | classify later |
| `command/exec` | diagnostic | source + schema | deterministic sandbox probes | live probe |
| `thread/shellCommand` | dangerous | source | unsandboxed command path | do not use without security review |
| permissions/profile fields | required-for-v128 | source + schema | execution security boundary | live probe |
| config/trust APIs | dangerous | source + schema | can mutate user config/trust | live probe with scratch home only |
| fs APIs | dangerous | source + schema | can read/write/remove absolute paths | classify before any use |
| server requests and approvals | required | source + schema | execution can block/hang without responses | live probe |
| skills/plugins/apps/MCP APIs | future_scope | source + schema | broad client platform, not immediate delegate blocker | classify later |
| realtime APIs | future_scope | source + schema | separate event surface | classify later |
| auth endpoints | diagnostic | source + schema | account/read already used, login flows not owned | live probe |
| external agent import | future_scope | source + schema | not current codex-collaboration scope | classify later |
```

- [ ] For every `unknown` row, add one concrete next evidence step.
- [ ] For every `dangerous` row, state the default posture: do not call from production clients until separately designed.

Expected:
- A future architecture spec can reuse the table as an input, but the table itself is not the spec.

## Task 7: Identify Runtime Probe Requirements Without Running Deep Probes

**Purpose:** Define what must be probed later without starting the security-boundary execution packet prematurely.

- [ ] Create a runtime-probe backlog section:

```markdown
## Runtime Probe Backlog

| Probe | Selected launcher required? | Scratch Codex home required? | Auth required? | Blocks architecture spec? | Blocks implementation? |
|---|---:|---:|---:|---:|---:|
| initialize then initialized | yes | no | no | yes | yes |
| request before initialize rejection | yes | no | no | yes | yes |
| stable schema request accepted path | yes | yes | maybe | no | yes |
| experimentalApi gating | yes | yes | maybe | no | yes |
| permission profile provenance | yes | yes | maybe | no | yes |
| server-request taxonomy and unknown handling | yes | yes | maybe | yes | yes |
| trust/config mutation check | yes | yes | no | yes | yes |
| command/exec diagnostics | yes | yes | no | no | yes |
| thread/read projection shape | yes | yes | maybe | yes | yes |
```

- [ ] Mark probes that belong to the existing v128 decision packet instead of this exploration plan.

Expected:
- The fresh session does not overrun into Branch A/B/C/D selection by accident.

## Task 8: Write Structured Exploration JSON

**Purpose:** Give the next session a machine-readable summary.

- [ ] Create `docs/diagnostics/codex-app-server-client-platform-exploration.json` with this shape:

```json
{
  "artifact_version": 1,
  "created_for": "codex-app-server-client-platform-exploration",
  "repo": "/Users/jp/Projects/active/claude-code-tool-dev",
  "source_snapshot": {
    "kind": "github_sparse_checkout",
    "path": "/private/tmp/codex-app-server-exploration/openai-codex-ff27d016",
    "commit": "ff27d01676a93be7467b3893e82f41a7af7e1418",
    "used_for_runtime_claims": false
  },
  "release_artifacts": {
    "pr_19447": {
      "url": "https://github.com/openai/codex/pull/19447",
      "finding": "standalone codex-app-server is an official release artifact",
      "protocol_equivalence_proven": false
    },
    "release_0_128_0": {
      "url": "https://github.com/openai/codex/releases/tag/0.128.0",
      "target_commit": null,
      "notes": []
    }
  },
  "local_launchers": {
    "codex_app_server_subcommand": {
      "status": "present",
      "path": null,
      "version_output": null,
      "schema_dirs": {
        "stable": null,
        "experimental": null
      }
    },
    "standalone_codex_app_server": {
      "status": "not_installed",
      "path": null,
      "version_output": null,
      "schema_dirs": {
        "stable": null,
        "experimental": null
      }
    }
  },
  "surface_classification": [],
  "runtime_probe_backlog": [],
  "architecture_spec_readiness": {
    "ready": false,
    "missing_items": []
  }
}
```

Replace `null`, empty arrays, and placeholder values with captured facts before marking the exploration complete.

## Task 9: Readiness Gate For The Future Architecture Spec

The exploration packet is ready for review only when all are true:

- [ ] PR #19447 artifact implication is recorded without claiming protocol equivalence.
- [ ] Local `codex app-server` launcher path, version, help, and generated schema directories are recorded.
- [ ] Standalone `codex-app-server` status is recorded as absent, installed, or downloaded.
- [ ] Pinned source checkout exists at the exact requested commit.
- [ ] Static source map has concrete file paths and line references.
- [ ] Stable and experimental schema outputs are generated from the selected local launcher.
- [ ] Evidence-frame comparison table is filled.
- [ ] Surface classification table has no blank rows.
- [ ] Runtime probe backlog separates architecture-blocking probes from implementation-blocking probes.
- [ ] The structured JSON has no `null` values except where the status field explicitly explains absence.
- [ ] The final diagnostic clearly says: "Not ready to draft architecture spec" or "Ready for architecture-spec review," with reasons.

## Stop Conditions

Stop and ask the user before proceeding if any of these occur:

- The selected launcher cannot generate schemas.
- The pinned source checkout cannot be obtained.
- `codex-app-server` standalone artifact appears available but installing/downloading it would require changing Homebrew, mise, npm, or dotfiles state.
- A runtime probe would need to read, copy, print, or serialize auth tokens.
- A proposed probe would mutate the operator's real `~/.codex/config.toml`, trust state, sessions, or auth files.
- The exploration discovers that the local installed `codex` version is not `0.128.0`.

## Final Fresh-Session Response Shape

When this plan is executed in a fresh session, the final response should use:

- `What changed`
- `Why it changed`
- `Verification performed`
- `Remaining risks`

It should name the two durable artifacts:

- `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- `docs/diagnostics/codex-app-server-client-platform-exploration.json`

It should not say the client-platform rebaseline architecture spec is complete.

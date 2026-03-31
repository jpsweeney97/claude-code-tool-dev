# T-20260330-02: Codex-collaboration plugin shell and consult parity

```yaml
id: T-20260330-02
date: 2026-03-30
status: open
priority: high
tags: [codex-collaboration, plugin-shell, consult, supersession]
blocked_by: []
blocks: [T-20260330-03]
effort: medium
```

## Context

`codex-collaboration` has the advisory runtime core, but it still runs as a
repo-launched MCP server rather than an installable plugin artifact. The
package currently exposes `codex.status`, `codex.consult`, and the R2 dialogue
tools from `server/mcp_server.py`, but it does not yet ship the plugin shell,
skill entrypoints, or bootstrap glue described in
`docs/superpowers/specs/codex-collaboration/delivery.md`.

This ticket is the first executable supersession packet. It turns the existing
runtime into a minimal installable plugin with a working consult flow.

## Problem

Cross-model replacement cannot start until users can install
`codex-collaboration` and invoke a consult flow through the host plugin
surface. Today, the runtime exists but the package lacks:

- `.claude-plugin/plugin.json`
- `.mcp.json`
- a plugin bootstrap entry point
- a user-facing consult skill
- a user-facing status skill

Without those pieces, the runtime is testable from the repo but not usable as
the successor plugin.

## Scope

**In scope:**

- Add the installable plugin shell to
  `packages/plugins/codex-collaboration/`
- Add `.claude-plugin/plugin.json` with the plugin metadata and install shape
- Add `.mcp.json` that launches the codex-collaboration MCP server from the
  plugin root
- Add the bootstrap entry point needed to start the existing stdio MCP server
- Add a minimal consult skill that maps the user surface to `codex.consult`
- Add a minimal status skill that maps the user surface to `codex.status`
- Add `codex.status` preflight to the consult skill before dispatch
- Add install and smoke-test documentation for the minimal packaged plugin

**Explicitly out of scope:**

- Credential scanning hooks
- Consultation profiles
- Learning retrieval
- Analytics emission
- Dialogue orchestration
- Delegation and promotion
- Any cross-model compatibility layer that reintroduces the `codex exec` shim

## Implementation Notes

- This is the `2a` packet from the supersession roadmap.
- The consult skill should be intentionally thin. It only needs to prove that
  an installed plugin can route user input through `codex.status` and
  `codex.consult`.
- The skill response format can stay minimal in this packet. The production
  consult UX hardening belongs to `T-20260330-03`.
- Do not port cross-model hook behavior into this ticket. The plugin shell and
  the shared safety substrate have different risk profiles and are tracked
  separately on purpose.

## Acceptance Criteria

- [ ] `packages/plugins/codex-collaboration/.claude-plugin/plugin.json` exists
      and describes an installable plugin
- [ ] `packages/plugins/codex-collaboration/.mcp.json` exists and launches the
      codex-collaboration MCP server from the plugin root
- [ ] A bootstrap entry point exists and starts the current stdio MCP server
      without requiring repo-local manual wiring
- [ ] A consult skill exists in the codex-collaboration package and calls
      `codex.status` before `codex.consult`
- [ ] A status skill exists in the codex-collaboration package and returns the
      structured runtime health result
- [ ] The consult skill can dispatch a minimal advisory consultation through the
      packaged plugin surface
- [ ] The new install shape is documented well enough for a fresh session to
      install and smoke test it without referencing cross-model
- [ ] Tests cover the plugin bootstrap and the new consult/status skill wiring

## Verification

- Install the plugin from `packages/plugins/codex-collaboration/`
- Run the status skill and confirm it returns the structured health response
- Run the consult skill and confirm it performs `codex.status` preflight before
  consultation dispatch
- Run the package test slice that covers plugin bootstrap and skill wiring

## Carry-Forward Limitations

### Concurrent packaged sessions unsupported

The plugin publishes session identity via a `SessionStart` hook that writes
`session_id` to `${CLAUDE_PLUGIN_DATA}/session_id`. Two simultaneous Claude
sessions sharing this plugin would race to write that file. The MCP server
reads it once (pinned on first dialogue tool call), so the loser gets the
winner's session identity and writes to the wrong lineage/journal partition.

**Blast radius:** Dialogue-only. `codex.status` and `codex.consult` are
unaffected (they do not use session-scoped stores).

**Accepted for:** Dev-repo internal use (single-session rollout target).

**Invalidation trigger:** Claude Code exposing a per-session data directory
or session identity env var to MCP server subprocesses would eliminate this
limitation at the platform level.

### SessionStart hook ordering assumption

Dialogue initialization assumes the `SessionStart` hook has published
`session_id` before the first `codex.dialogue.*` tool call. If a dialogue
tool is called before the hook fires, it returns an explicit error. This is
expected to be a non-issue in practice because user interaction (which
triggers tool calls) happens after session startup completes.

## Dependencies

This ticket must land before `T-20260330-03`, which hardens the shared
substrate on top of the packaged consult flow.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Plugin structure target | `docs/superpowers/specs/codex-collaboration/delivery.md` | Normative install shape |
| Current tool surface | `packages/plugins/codex-collaboration/server/mcp_server.py` | Existing runtime entry points |
| Reference plugin shell | `packages/plugins/cross-model/.claude-plugin/plugin.json` | Packaging precedent only |
| Reference MCP config | `packages/plugins/cross-model/.mcp.json` | Launch precedent only |

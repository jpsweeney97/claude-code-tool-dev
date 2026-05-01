# Architecture Note: Codex App Server 0.128 Permissions Model

**Date:** 2026-05-01
**Status:** Analysis; not a final implementation decision
**Related plan:** `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
**Related ticket:** `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md`
**Pinned upstream implementation inspected:** <https://github.com/openai/codex/tree/a93c89f4972d9c6a493688f3f4d35aad74c498e1/codex-rs/app-server>

## Conclusion

The Codex App Server `0.128.0` permissions change is probably not just a
request-field migration for `codex-collaboration`.

The corrected decision-packet thesis remains valid: do not migrate `/delegate`
execution directly to raw top-level `permissionProfile`. However, the pinned
implementation shows that permissions are now resolved through a session/config
model, not only through one per-turn payload field.

If the stable `sandboxPolicy.workspaceWrite` path still accepts a schema-grounded
payload and preserves every PR #127 / T-20260429-01 invariant, the implementation
can stay relatively narrow. If that path fails and the selected path is
experimental request-level `permissions` or config-level `default_permissions`,
the required codex-collaboration change is larger: runtime launch, execution
thread creation, capability negotiation, permission provenance, config isolation,
and tests all become part of the migration surface.

## What The Pinned Implementation Proves

1. **Named permission selection is the documented forward path.**

   App-server `thread/start`, `thread/resume`, `thread/fork`, and `turn/start`
   accept experimental `permissions: PermissionProfileSelectionParams`, not raw
   top-level `permissionProfile`.

   Runtime plumbing maps that selection into `ConfigOverrides.default_permissions`
   and bounded `additional_writable_roots`.

2. **Raw `permissionProfile` exists in a narrower place.**

   `CommandExecParams.permissionProfile` is experimental and command-scoped. It
   is not the documented `/delegate` turn execution target.

3. **Profile provenance is exposed mostly at thread boundaries.**

   `ThreadStartResponse`, `ThreadResumeResponse`, and `ThreadForkResponse` expose
   experimental `permissionProfile` and `activePermissionProfile`.

   `TurnStartResponse` only returns `turn`. A plan that requires active/effective
   profile provenance cannot rely on a turn-only request path unless it has a
   separate way to read or infer that provenance.

4. **The old restricted read subtree is removed from the effective request path.**

   `SandboxPolicy.workspaceWrite.readOnlyAccess` with `type: "restricted"` is
   rejected with the runtime error:

   `workspaceWrite.readOnlyAccess is no longer supported; use permissionProfile for restricted reads`

   The implementation still deserializes and ignores legacy
   `readOnlyAccess: {"type": "fullAccess"}`. That compatibility shim must not be
   mistaken for support for the removed restricted read-root shape.

5. **Thread start can persist project trust.**

   When a request supplies `cwd` and the requested or effective permissions trust
   that project, app-server can write project trust into Codex home. A fresh
   app-server process is therefore not enough isolation for probes or for any
   production path that must not mutate operator-owned config.

6. **Built-in profiles may be insufficient for PR #127 support roots.**

   Built-in `:workspace` provides workspace-style permissions, and request-level
   `modifications` currently support `AdditionalWritableRoot`. That does not
   obviously express "read these support roots, but do not make them writable."

   If the PR #127 invariant still requires read-only access to Codex memories,
   plugin caches, agent skills/plugins, and the resolved worktree gitdir, then a
   documented config-level user-defined `[permissions.<id>]` profile may be the
   only documented path that can represent the intended boundary without widening
   support roots to writable roots.

## Implications For codex-collaboration

### 1. Execution permissions need an abstraction, not a renamed argument

Current runtime code is shaped around:

- `run_execution_turn(..., sandbox_policy=...)`
- `_run_turn(..., sandbox_policy=...)`
- unconditional `turn/start.sandboxPolicy`

That remains appropriate only if Branch A3 wins. If A1 or A2 wins, the runtime
API should grow an explicit execution permission mode instead of overloading
`sandbox_policy` with another dict.

The implementation plan should preserve the advisory/execution boundary and make
the selected permission mode visible in tests and diagnostics.

### 2. Execution thread bootstrap may need to own permissions

Current execution bootstrap creates the app-server thread before the execution
turn:

- `ControlPlane.start_execution_runtime(worktree_path)` starts a runtime and
  calls `session.start_thread()`.
- The worker later calls `entry.session.run_execution_turn(...)`.

If the selected branch needs `activePermissionProfile` / `permissionProfile`
evidence, permission selection may need to happen during `thread/start`, not only
during `turn/start`.

That implies a larger change to execution bootstrap:

- `start_thread()` may need execution-specific parameters.
- `start_execution_runtime()` may need the selected permission mode or a
  worktree-derived permission profile before it creates the thread.
- The first execution turn should not silently override a thread created under
  incompatible permissions.

### 3. Runtime launch must become provenance-aware

Current app-server launch defaults to inherited environment and
`["codex", "app-server"]`.

For `0.128.0`, compatibility evidence must include:

- selected launcher kind (`codex app-server` vs standalone `codex-app-server`),
- resolved launcher path,
- stable and experimental schema generation commands from that same launcher,
- runtime initialization variant,
- whether `capabilities.experimentalApi = true` was negotiated,
- binary/version/help evidence.

If the selected branch requires config-level profile selection, runtime launch
also needs explicit config/Codex-home provenance. It must not accidentally depend
on ambient `~/.codex/config.toml`, project trust, managed requirements, or network
flags.

### 4. Probe and production isolation are now safety concerns

Because `thread/start` can persist trust, every runtime candidate probe should use
a scratch Codex home or an explicit non-durable trust/config strategy. This is not
only an A2 concern.

The plan also needs an auth strategy for isolated probes. A scratch Codex home can
avoid config contamination, but it may also lose access to existing ChatGPT/API
credentials. The probe design must record how auth is supplied without serializing
secrets.

Production implementation may or may not use a scratch Codex home. That is not
decided here. The decision packet must prove whether production can safely use the
operator's Codex home, and under what config/trust constraints.

### 5. PR #127 support-root handling may require user-defined profiles

The current builder grants:

- writable worktree,
- readable worktree,
- readable `~/.codex/memories`,
- readable `~/.codex/plugins/cache`,
- readable `~/.agents/skills`,
- readable `~/.agents/plugins`,
- readable resolved worktree gitdir,
- blocked credential/session paths,
- blocked parent/sibling sentinels,
- controlled tmp and network behavior.

Stable `sandboxPolicy.workspaceWrite` without `readOnlyAccess` may no longer be
able to express the support-root reads. Experimental `permissions` with
`AdditionalWritableRoot` may be able to add paths only as writable roots, which is
not equivalent.

Therefore the decision packet should include a config-level user-defined profile
candidate, separate from built-in `:workspace`, before declaring Branch B/C/D.

### 6. Compatibility checks become launcher and capability checks

`codex-collaboration` currently treats `codex --version` and a `0.117.0` schema
fixture as the main compatibility anchor.

For `0.128.0`, compatibility needs to know more:

- app-server launcher artifact,
- stable schema surface,
- experimental schema surface,
- runtime experimental capability opt-in,
- selected execution permission branch,
- whether the chosen path is documented, experimental, config-derived, or
  exceptional.

This may need a versioned capability matrix rather than a single tested-version
constant.

### 7. Tests need a permission-branch matrix

Existing tests assert the old `readOnlyAccess` payload shape. Supporting
`0.128.0` means tests should assert the selected branch behavior, not one
universal request payload.

At minimum, tests should cover:

- stale `readOnlyAccess.restricted` rejection or structural invalidity,
- stable `workspaceWrite` candidate shape,
- experimental `permissions` initialization and gating,
- thread-level active permission profile provenance if A1 is selected,
- config-level profile provenance if A2 is selected,
- support-root invariants,
- credential/session/sentinel/tmp/network boundaries,
- launcher/schema/probe artifact consistency.

## Scope Fork

### If Branch A3 passes

The implementation can likely stay narrow:

- update the stable `sandboxPolicy` builder,
- remove `readOnlyAccess`,
- refresh fixtures and compatibility evidence,
- keep `run_execution_turn(..., sandbox_policy=...)`,
- run the comparable T-20260429-01 smoke and credential-boundary checks.

This is the only branch where "builder patch" remains a plausible scope.

### If Branch A1 passes

The implementation is broader:

- add experimental initialization support,
- route named permission selections,
- decide whether selection belongs at `thread/start`, `turn/start`, or both,
- capture profile provenance from thread responses or another documented source,
- update runtime API and tests around permission mode rather than sandbox-policy
  dicts.

### If Branch A2 passes

The implementation is broader still:

- construct or require a config-level profile,
- isolate or control config/Codex-home/trust state,
- encode PR #127 support roots without making them writable,
- prove auth can work without leaking or serializing credentials,
- document operator setup and failure modes.

### If only Branch C works

Do not fold it into the normal implementation plan. Treat raw or undocumented
acceptance as an exception requiring explicit maintainer approval and exact-version
evidence.

## Non-Decisions

This note does not decide:

- which Branch A1/A2/A3/B/C/D wins,
- whether production should use a scratch Codex home,
- whether `/delegate` should require experimental API opt-in,
- whether a user-defined permission profile is acceptable for operator setup,
- whether T-20260429-01 is closed.

The decision packet must select the branch before implementation proceeds.

## Required Follow-Up For The Decision Packet

Update or verify the decision-packet plan so it includes:

1. A user-defined config-level permission profile candidate, not only built-in
   `:workspace`.
2. Runtime isolation for every candidate, not only A2.
3. A thread-level permissions probe or an explicit reason turn-level provenance is
   sufficient.
4. A launcher/capability matrix tied to the exact artifact used for schema and
   runtime probes.
5. A branch-specific implementation scope statement so a passing A1/A2 candidate
   cannot be implemented as a narrow builder patch.

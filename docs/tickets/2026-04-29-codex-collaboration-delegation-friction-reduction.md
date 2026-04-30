# T-20260429-01: Reduce codex-collaboration delegation operator friction

```yaml
id: T-20260429-01
date: 2026-04-29
status: open
priority: medium
tags: [codex-collaboration, delegation, sandbox, escalation, operator-ux]
blocked_by: []
blocks: []
effort: small
```

## Context

T-20260423-01's closing live `/delegate` smoke (job
`4586c6c3-39cb-49ff-815b-620d7f3212c9`, 2026-04-29) successfully validated
the Candidate A sandbox patch end-to-end and produced a 1-line type-suppression
edit, but required **24 operator approvals** to complete. This is far above
the expected count for a small edit and surfaces three plugin-level friction
sources that the operator had to manually grant per-escalation:

1. Codex's reads of its own data root (`~/.codex/memories/`, `~/.codex/plugins/cache/`)
2. Tools (ripgrep, git) traversing the worktree's `.git` cross-pointer
3. Opaque `file_change` escalations with empty `requested_scope` payloads

Each friction source is independently addressable. Resolving items 1 and 2
(sandbox policy carve-outs) is mechanical. Resolving item 3 requires
investigating whether the empty payload is a plugin pass-through gap or an
App Server limitation.

## Friction surface 1: `~/.codex/` reads (Option B)

### Observed behavior

During T-01's smoke, Codex made 4 separate escalations to read files under
`~/.codex/`:

- `~/.codex/plugins/cache/openai-curated/superpowers/.../skills/verification-before-completion/SKILL.md`
- `~/.codex/plugins/cache/.../skills/using-superpowers/SKILL.md`
- `~/.codex/plugins/cache/.../skills/test-driven-development/SKILL.md`
- `~/.codex/memories/MEMORY.md` (multiple line ranges)

These are Codex consulting its own learned context (memory store) and
protocol catalog (skill cache) as part of its preparation cycle. They are
benign reads of Codex's own data — not user data, not credentials, not
external state.

### Security boundary

`~/.codex/` also contains files the operator should NOT grant via blanket
carve-out:

- `~/.codex/auth.json` (mode 0600 — OAuth/API credentials)
- `~/.codex/config.toml` (mode 0600 — possibly contains API keys)
- `~/.codex/history.jsonl` (mode 0600 — conversation history, ~433KB)
- `~/.codex/sessions/`, `~/.codex/archived_sessions/`, `~/.codex/state_5.sqlite`,
  `~/.codex/logs_2.sqlite` — session DBs and logs

The OS-level 0600 mode is a deliberate restriction; the plugin must preserve
it. The narrower carve-out (only `memories/` and `plugins/cache/`) matches
the actual access patterns observed in T-01's smoke and excludes the
credential paths.

### Implementation

In `packages/plugins/codex-collaboration/server/runtime.py:46-57`, extend
`readableRoots` with two specific subpaths only:

- `Path.home() / ".codex" / "memories"`
- `Path.home() / ".codex" / "plugins" / "cache"`

Do NOT add `~/.codex/` as a whole — that would expose `auth.json` and the
other credential-class files.

Update `tests/test_runtime.py:178` regression assertion to expect the new
`readableRoots` shape.

## Friction surface 2: Worktree `.git` cross-pointer reads (Option E)

### Observed behavior

During T-01's smoke, approximately 7 escalations were caused by ripgrep and
git invocations that needed to traverse the delegation worktree's `.git`
pointer file. Git worktrees use a `.git` *file* (not directory) pointing to
`<source-repo>/.git/worktrees/<name>/`. The pointer target is OUTSIDE the
delegation worktree and is therefore blocked by the current `readableRoots`
configuration.

This affects any tool that respects `.gitignore` or queries git metadata
(`rg`, `git status`, `git ls-files`, etc.). Each in-worktree search triggers
an escalation purely due to incidental git-worktree mechanics, not the
user's intent.

### Implementation

In `runtime.py:23-58`, the policy builder needs to read the worktree's
`.git` file content at delegation-start time to determine the gitdir target,
then add that target to `readableRoots`. The gitdir path looks like
`<source-repo>/.git/worktrees/<runtime-id-or-similar>/`.

This is dynamic per-delegation (the gitdir target depends on the worktree
created for this job), so it cannot be hardcoded — the policy builder must
resolve it per-call. If the worktree's `.git` file does not exist or is
unreadable at policy-build time, the carve-out is omitted (and tools fall
back to escalation, matching current behavior).

Update `test_runtime.py` to either parameterize over a fake gitdir target or
mock the resolution. The regression assertion should accept the gitdir as a
parameter rather than pinning a fixed path.

## Friction surface 3: `file_change` escalation payload opacity (Option F)

### Observed behavior

During T-01's smoke, multiple `file_change` escalations were dispatched with
**empty `requested_scope` payloads**:

```json
{
  "request_id": "14",
  "kind": "file_change",
  "requested_scope": {
    "grantRoot": null,
    "reason": null
  },
  "available_decisions": ["approve", "deny"]
}
```

No `file_path`, no `change_type`, no `diff` preview. The operator could not
see what file Codex wanted to change before approving.

A deny test (request 14) confirmed the opacity is structural, not strategic
— Codex retried with the same opaque payload (request 15). This means:

1. The plugin's escalation rendering (per `/delegate` skill step 6f) cannot
   display useful information for `file_change` kinds.
2. The operator must approve blind, defeating the visibility intent of the
   escalation.
3. Worktree isolation + Gate 1 (review-before-promote) preserved overall
   safety, but the per-escalation visibility gap is real.

### Investigation gate (before implementation)

Before changing plugin code, determine:

1. **App Server response shape.** Inspect the App Server's actual JSON-RPC
   response for `applyPatchApprovalRequest` (or equivalent file-change-class
   request method). Does it include file paths, change types, or diff
   content? If yes, the plugin is dropping fields. If no, the App Server
   itself does not surface them.
2. **Plugin handler.** Trace `_server_request_handler` (or equivalent in
   `delegation_controller.py`) for file-change-class requests. Are
   `requested_scope` fields populated from the App Server response, or
   defaulted to null?
3. **Vendored schemas.** Check the App Server schemas at
   `tests/fixtures/codex-app-server/0.117.0/` for the file-change request
   shape and any associated approval-response payload structure.

Record diagnostic findings as evidence before committing to an implementation
path.

> **Investigation result (2026-04-30, D-06 closure):** All three questions answered. (1) The current `item/fileChange/requestApproval` method's `FileChangeRequestApprovalParams` schema defines only `grantRoot` (nullable string), `reason` (nullable string), and context IDs (`itemId`, `threadId`, `turnId`). No file path, change type, or diff fields exist at the wire level. Live T-01 smoke evidence confirms: `{grantRoot: null, reason: null}`. (2) `approval_router.py:58-60` preserves all non-context params opaquely into `requested_scope`; `delegation_controller.py:1812` projects `requested_scope` unchanged into `PendingEscalationView`. The plugin does not drop fields — there are none to drop. (3) `applyPatchApproval` carries `fileChanges` but lacks `itemId`/`threadId`/`turnId` and is classified as an unsupported parser shape (see schema delta line 238). **Conclusion:** file-level visibility is an upstream schema limitation. The `/delegate` SKILL.md rendering guidance has been narrowed accordingly. Future enrichment requires either upstream `FileChangeRequestApprovalParams` changes or `applyPatchApproval` support (separate design item).

### Implementation (conditional on investigation)

If the data is available in the App Server response: implementation is
straightforward plugin-side mapping — extend the escalation rendering to
surface `file_path`, `change_type`, and (if available) a `diff` preview.

If the data is not available: document the limitation as an upstream App
Server boundary; consider an opt-in operator-side preflight (e.g., the
plugin runs `git diff HEAD` against the delegation worktree and shows the
output as part of escalation rendering when an env var enables this).

## Acceptance criteria

- [ ] After Friction surfaces 1 and 2 (Phase 1) land, a comparable smoke run
      (1-line type-suppression or similarly small repo edit) completes with
      **0-2 operator escalations**, down from 24. Acceptance is measured
      against a fresh small-edit objective.
- [ ] `runtime.py`'s `build_workspace_write_sandbox_policy` continues to
      preserve the credential boundary: `~/.codex/auth.json`,
      `~/.codex/config.toml`, `~/.codex/history.jsonl`, and
      `~/.codex/sessions/` remain sandbox-blocked. Verify with a probe similar
      to the security probes in
      `docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md`.
- [ ] `test_runtime.py` regression assertion updated to expect the new
      `readableRoots` shape (including the dynamic gitdir resolution); full
      codex-collaboration test suite passes.
- [ ] Friction surface 3 (file_change opacity) is either:
      - Resolved with a plugin change that surfaces `file_path`,
        `change_type`, and diff preview in the escalation rendering, OR
      - Documented as an upstream App Server limitation with a recorded
        workaround path.

## Implementation sequence

### Phase 1: Sandbox policy carve-outs (Options B + E)

Implement Friction surfaces 1 and 2 in a single commit (same `runtime.py`
surface, same test surface). Land with regression test updates.

### Phase 2: file_change opacity investigation (Option F gate)

Investigate per the gate in Friction surface 3. Record findings as evidence.

### Phase 3: file_change opacity implementation (conditional)

Based on Phase 2 findings, either implement the plugin-side mapping or
document the limitation.

### Phase 4: Acceptance smoke

Run a comparable small-edit `/delegate` smoke. Record escalation count.
If <= 2, acceptance criterion #1 is satisfied. If higher, decompose remaining
friction sources and address.

## Evidence

### T-01 smoke evidence

- **Job ID:** `4586c6c3-39cb-49ff-815b-620d7f3212c9`
- **Date:** 2026-04-29
- **Escalation count:** 24 (request_ids 0-23, including 1 deny experiment)
- **Closing artifact commit:** `a7a4e9c9` `chore(codex-collaboration): silence pyright unreachable hint on assert_never arm`
- **T-01 closure commit:** `6580d86e` `chore(codex-collaboration): close T-01 delegate execution remediation`
- **Approximate breakdown of escalations:**
    - ~4 escalations: `~/.codex/` reads (Option B)
    - ~7 escalations: in-worktree rg with git-pointer friction (Option E)
    - ~3 escalations: opaque file_change writes (Option F)
    - ~10 escalations: legitimate operations (initial baseline pyright,
      post-edit pyright, focused pytest runs, git diff for artifact prep,
      Python tool-availability probes, etc.) — these would remain after
      Options B+E+F land

### Source locations

| Surface | File | Line |
|---|---|---|
| Sandbox policy builder | `packages/plugins/codex-collaboration/server/runtime.py` | 23-58 |
| Sandbox policy regression test | `packages/plugins/codex-collaboration/tests/test_runtime.py` | 178 |
| App Server response handler (file_change) | `packages/plugins/codex-collaboration/server/delegation_controller.py` | TBD (to be confirmed in Phase 2) |
| Vendored App Server schemas | `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/0.117.0/` | (file_change shape) |
| Diagnostic record (Candidate A) | `docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md` | (security probe pattern reusable here) |

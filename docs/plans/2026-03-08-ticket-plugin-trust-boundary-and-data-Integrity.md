# Remediation Plan: Ticket Plugin Trust Boundary and Data Integrity

## Summary
- Land remediation in two patches:
  - **Patch 1: trust boundary hardening** — guarded `execute`, mandatory execute prerequisites, `shlex`-based hook candidate detection, and explicit `agent_id` validation.
  - **Patch 2: data integrity and interface cleanup** — schema/type enforcement, marker-based project-root discovery, and contract/doc/test alignment.
- Keep the accidental-autonomy threat model. Do not add signed tokens or authenticated stage artifacts.
- Keep `classify`, `plan`, and `preflight` directly runnable for debugging. Only mutating `execute` becomes guarded.

## Implementation Changes
- **Guard `execute` at both layers**
  - In both engine entrypoints, make `execute` require the full trust triple:
    - `hook_injected is True`
    - `hook_request_origin == REQUEST_ORIGIN`
    - `session_id` is a non-empty string
  - Remove the current `hook_origin is not None` escape hatch for `execute`; missing `hook_request_origin` becomes a rejection, not a bypass.
  - Keep non-`execute` stages directly runnable without requiring hook metadata.
  - In `engine_execute()`, enforce the same trust triple as defense-in-depth for all mutation origins, not only agents.
  - Extend the `engine_execute()` interface to receive `hook_request_origin` so direct Python callers and entrypoints use the same invariant.

- **Keep hook injection behavior unchanged for all engine stages**
  - Canonical hook-validated engine invocations for `classify`, `plan`, `preflight`, and `execute` must still inject `session_id`, `hook_injected`, and `hook_request_origin`.
  - The change is not “inject only for execute.” The change is “`execute` now requires the injected trust triple.”
  - This preserves current preflight behavior for agent-origin requests, which depends on `hook_injected`.

- **Enforce structural stage prerequisites in `execute`**
  - Require `classify_intent` on every execute call and reject unless it exactly matches `action`.
  - Require `classify_confidence` on every execute call and reject if missing, non-numeric, or below the origin-specific threshold.
  - Require `autonomy_config` for agent-origin execute calls so the live-vs-snapshot policy check is meaningful; missing snapshot data blocks rerun-from-preflight.
  - Require `dedup_fingerprint` for `create`.
    - Recompute the fingerprint from current create fields.
    - Reject if the fingerprint is missing or mismatched. This is a mandatory payload-consistency check proving the create fields did not change after `plan`.
    - Keep the existing live duplicate scan in execute. It continues to protect against duplicates that appear between `plan` and `execute`.
  - Require `target_fingerprint` for `update`, `close`, and `reopen`. Remove the current optional stale-plan behavior so non-create execute always validates target freshness.
  - Reuse existing error families where possible: `origin_mismatch`, `intent_mismatch`, `preflight_failed`, `stale_plan`, `policy_blocked`.

- **Replace the hook prefilter with token-based candidate detection**
  - In the hook, normalize commands with `lstrip()` and keep the current terminal `2>&1` stripping before candidate detection and metachar checks.
  - Replace `_is_ticket_invocation()` with `shlex.split()`-based parsing that identifies a candidate only when the script operand to a Python-like launcher is a known ticket script basename.
  - Support launcher-position detection for:
    - `python`, `python3`, versioned Python basenames
    - absolute Python paths
    - `env` and absolute-path `env` launchers with optional leading env assignments before the Python token
  - Route every detected candidate into exact branch validation; any candidate that is not a canonical allowlisted form is denied by branch 3.
  - If `shlex.split()` fails and the raw command mentions a known ticket-script basename, deny as malformed ticket command. If parsing fails without a known ticket-script basename, pass through.
  - Keep the canonical allowlist unchanged: only documented `python3 <PLUGIN_ROOT>/scripts/...` forms are allowed. Launcher variants remain denied, not silently passed through.

- **Apply explicit `agent_id` handling to every hook branch that uses origin**
  - Introduce one shared origin helper in the hook with these rules:
    - missing `agent_id` key => user
    - non-empty string `agent_id` => agent
    - present-but-empty or non-string `agent_id` on candidate ticket commands => deny as malformed trust metadata
  - Use this helper everywhere the hook currently consults `agent_id`, including:
    - engine-command trust injection
    - the audit user-only gate
  - Do not leave any branch on truthiness-based `event.get("agent_id")`.

- **Add schema/type validation before any write**
  - Add shared validation for writeable payload fields before `render_ticket()` or YAML replacement runs.
  - Enforce contract enums for `priority`, `status`, and close `resolution`.
  - Enforce list-of-string types for `tags`, `blocked_by`, and `blocks`.
  - Enforce dict-with-string-fields shape for `source`, and validate `defer` when updated.
  - Validate create-only structured render inputs like `key_files` when present.
  - Reject invalid inputs instead of silently coercing them; keep defaulting only for omitted valid optional fields.

- **Replace cwd fallback with marker-based project-root resolution**
  - Add shared project-root discovery that walks ancestors from the process cwd and chooses the nearest ancestor containing `.claude/`, `.git/`, or a `.git` file.
  - Use this discovered root for all CLI entrypoints that currently resolve `tickets_dir` against `Path.cwd()`.
  - Resolution precedence:
    - explicit `tickets_dir` resolves relative to discovered project root and must remain inside it
    - omitted `tickets_dir` defaults to `<project_root>/docs/tickets`
    - if no marker-based project root is found, reject with `policy_blocked`; do not fall back to cwd
  - Keep payload temp-file boundary checks separate; this change is only for CLI `tickets_dir` behavior.

- **Update contract, docs, and tests together**
  - Update the contract and pipeline docs to state:
    - `execute` requires verified hook provenance for all mutations
    - `execute` requires prior-stage artifacts (`classify_*`, dedup/target fingerprints, and agent autonomy snapshot as applicable)
    - canonical hook path still injects trust metadata for all engine stages
    - `tickets_dir` resolution is marker-rooted and rejects when no project root can be established
  - Remove or invert tests that currently bless unsafe shortcuts, especially:
    - user execute without hook provenance succeeds
    - agent execute without a preflight snapshot succeeds under live `auto_audit`

## Test Plan
- **Hook guard**
  - allow canonical `python3 <PLUGIN_ROOT>/scripts/...` for all four engine stages and verify trust metadata injection still occurs
  - deny leading-space, `/usr/bin/env`, versioned-Python, and malformed quoted candidate commands
  - pass through malformed non-ticket commands and non-ticket commands mentioning no known ticket-script basename
  - deny present-but-empty and invalid-type `agent_id` for both engine commands and audit commands
- **Entrypoints and engine**
  - `execute` rejects missing trust triple for both user and agent entrypoints
  - `classify`, `plan`, and `preflight` remain directly invocable without hook metadata
  - `execute` rejects missing/mismatched `classify_intent`, low/missing confidence, missing `autonomy_config` for agents, missing/mismatched `dedup_fingerprint` for create, and missing `target_fingerprint` for non-create
  - canonical fully staged create/update/close/reopen still succeed
- **Validation and path resolution**
  - invalid `priority`, scalar `tags`, scalar `blocked_by`, malformed `source`, malformed `key_files`, and invalid `defer` are rejected before file mutation
  - nested-cwd invocations resolve to the discovered project root
  - missing root markers reject instead of silently writing to `<cwd>/docs/tickets`
- **Docs and contract alignment**
  - integration tests exercise the real hook -> entrypoint -> execute path with staged payloads
  - docs and tests assert the new invariants rather than the old shortcuts

## Assumptions
- The engine remains directly callable for read-only stages, but mutating `execute` is now a guarded transport rather than a standalone CLI.
- Structural execute prerequisites are sufficient for the accidental-autonomy threat model; no authenticated stage token is added.
- `dedup_fingerprint` mismatch is treated as payload inconsistency since `plan`; live execute dedup remains the separate store-state check.
- The shared hook origin helper is the only supported interpretation of `agent_id`; truthiness-based checks are removed from all hook branches.
- Marker-based root discovery uses `.claude` / `.git` ancestry and rejects when no project root can be established.

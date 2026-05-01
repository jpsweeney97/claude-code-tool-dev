# Codex App Server 0.128 Schema/Runtime Decision Packet Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to execute this plan task-by-task. This is a decision-packet plan, not an implementation migration plan. Do not implement a sandbox or permissions payload change until the branch decision is recorded.

**Goal:** Produce deterministic schema and runtime evidence that decides how `/delegate` execution should run against the exact Codex App Server `0.128.0` artifact and capability mode we will launch.

**Architecture:** Treat launcher provenance, stable schema, experimental schema, and runtime capability negotiation as one protocol contract. Probe documented permission-selection surfaces before considering undocumented or raw exceptional paths.

**Tech Stack:** Python, JSON Schema fixtures, Codex App Server JSON-RPC probes, existing `codex-collaboration` runtime and delegation controllers.

---

## Thesis Boundary

Artifact to produce:
- `0.128.0` schema/runtime decision packet.

Old thesis discarded:
- Do not migrate `/delegate` execution to top-level `permissionProfile` by default.
- Do not treat the stable-only generated schema as the full request contract.
- Remove any plan steps that require `run_execution_turn(permission_profile=...)`, `_run_turn(permission_field="permissionProfile")`, or "legacy is known rejected" as an implementation premise.

Verified defect:
- `build_workspace_write_sandbox_policy()` currently emits `sandboxPolicy.workspaceWrite.readOnlyAccess`.
- Stable live-generated Codex App Server `0.128.0` request schemas expose `turn/start.sandboxPolicy`, `thread/start.sandbox`, and `command/exec.sandboxPolicy`.
- Stable live-generated `0.128.0` `workspaceWrite` no longer admits `readOnlyAccess`.
- Runtime compatibility may still deserialize and ignore legacy `readOnlyAccess: {"type": "fullAccess"}` while rejecting legacy restricted `readOnlyAccess`. The current builder emits the restricted variant, and any accepted `fullAccess` smoke is not proof that the schema contract still supports the removed subtree or that PR #127 read-root invariants are preserved.

Protocol correction:
- `docs/codex-app-server.md` says schema generation defaults to the stable API surface and requires `--experimental` to include experimental fields.
- Runtime use of experimental fields requires `initialize.params.capabilities.experimentalApi = true`.
- Local experimental `0.128.0` schemas expose request-level `permissions` on `TurnStartParams`, `ThreadStartParams`, `ThreadForkParams`, and `ThreadResumeParams`.
- `PermissionProfileSelectionParams` selects built-in or user-defined profiles; request-level `modifications` currently add writable roots only, so they cannot safely represent PR #127 read-only support roots.
- Config-backed user-defined permission profiles are a documented candidate surface and must be probed before declaring that no documented path preserves the invariants.
- Local experimental `0.128.0` `CommandExecParams` exposes raw `permissionProfile`, but that is command-scoped and is not the documented `turn/start` target for `/delegate` execution.

Next proof:
- For the selected app-server launcher artifact and capability mode, a documented path must be accepted and preserve PR #127 / T-20260429-01 invariants before any implementation plan proceeds.

Exceptional-path posture:
- Raw or undocumented `permissionProfile` runtime acceptance is an escalation signal, not a default implementation path.

## Decision Branches

### Branch A1: Experimental request-level permissions works and preserves invariants

Proceed only if all are true:
- Stable and experimental schemas are generated from the same launcher artifact used by runtime probes.
- Experimental schema exposes `ThreadStartParams.permissions` and `TurnStartParams.permissions` as `PermissionProfileSelectionParams`.
- Runtime initialization explicitly sets `capabilities.experimentalApi = true`.
- `thread/start` accepts a documented named permission selection such as:

```json
{
  "permissions": {
    "type": "profile",
    "id": ":workspace",
    "modifications": []
  }
}
```

- The packet records `activePermissionProfile` and/or `permissionProfile` from thread-level responses when available.
- A separate `turn/start.permissions` override probe may be run to test turn-level behavior and stickiness, but a turn-only acceptance result cannot satisfy the active-profile provenance requirement by itself because `TurnStartResponse` only reports the turn.
- Any requirements fallback, profile fallback, or omitted-profile evidence is recorded before claiming this candidate preserves invariants.
- Runtime probes preserve the T-20260429-01 and PR #127 invariants.
- Credential/session paths remain blocked.
- Parent/sibling sentinel paths remain blocked.
- `/tmp`, `$TMPDIR`, and network behavior are classified without silent widening.

Branch A1 follow-up:
- Write a separate implementation plan for experimental `permissions` negotiation and execution payload routing.
- That implementation plan must include the runtime `experimentalApi` opt-in, a status/readiness story for experimental capability use, and a decision about whether permission selection belongs in execution `thread/start` before the first turn or in later `turn/start` overrides.

### Branch A2: Config-level default_permissions works and preserves invariants

Proceed only if all are true:
- The selected launcher documents or accepts config-level `default_permissions` profile selection.
- The packet probes every applicable A2 subcandidate before judging A2:
  - **A2a built-in profile:** `default_permissions = ":workspace"` or equivalent.
  - **A2b user-defined profile:** an isolated `[permissions.<id>]` profile selected through `default_permissions`.
- The A2b user-defined profile candidate must attempt to encode the intended boundary directly: worktree write, PR #127 support-root read access, credential/session denies when the config language supports them, parent/sibling sentinel denies when supported, `/tmp` and `$TMPDIR` policy, and network policy.
- If any required support-root or deny invariant is not expressible in the user-defined profile language, record that as A2b failure evidence instead of silently substituting writable grants.
- Runtime probes are run with an isolated config/home or explicit launcher override set that actually supplies the selected default.
- The packet records sanitized config-layer provenance, including config path or override keys, environment overrides, managed requirements influence, and confirmation that ambient user config was not the deciding input.
- Execution turns do not require a per-turn experimental field to achieve the same effective permissions.
- The packet records the active/effective permission profile reported by the runtime, or records that no such projection is available.
- Any config fallback, requirements fallback, profile fallback, or omitted-profile evidence is recorded before claiming this candidate preserves invariants.
- Runtime probes preserve the T-20260429-01 and PR #127 invariants.

Branch A2 follow-up:
- Write a separate implementation plan for config-level profile setup, user-defined profile generation when needed, and operator guidance.
- The implementation plan must prove the plugin can reliably select or require that config without reading or exposing credential-class config contents, and without widening read-only support roots to writable roots.

### Branch A3: Stable schema-grounded sandboxPolicy works and preserves invariants

Proceed only if all are true:
- The candidate `sandboxPolicy.workspaceWrite` payload uses only the generated stable `workspaceWrite.properties` key set.
- The candidate payload passes strict closed-key request-shape validation.
- `turn/start` accepts that payload without experimental initialization.
- Runtime probes preserve the T-20260429-01 and PR #127 invariants.
- Credential/session, parent/sibling sentinel, tmp, and network boundaries remain acceptable.

Branch A3 follow-up:
- Write a separate implementation plan to update the existing sandbox-policy builder and compatibility evidence.
- Keep the `run_execution_turn(... sandbox_policy=...)` interface unless the implementation plan proves a reason to change it.

### Branch B: Documented paths accepted but no documented candidate preserves invariants

Stop and save a blocker only after all applicable documented candidates have been tested or ruled inapplicable, and none qualifies for Branch A1, A2, or A3.

A documented candidate fails its Branch A path if it is accepted but either:
- loses required PR #127 support-root behavior,
- widens access to credential/session paths,
- widens access to parent/sibling sentinels,
- widens `/tmp`, `$TMPDIR`, or network access beyond the accepted boundary,
- causes approval/friction behavior that fails T-20260429-01's comparable-smoke acceptance frame,
- or cannot prove the intended effective permission/profile provenance required by Branch A1 or A2.

A failing documented candidate does not block another documented candidate from being probed or selected.

Branch B output:
- A blocker artifact explaining each documented candidate's status, including accepted candidates that failed invariants and candidates that were rejected or inapplicable.
- No implementation migration.

### Branch C: Only an undocumented or raw exceptional path works

Treat this as exceptional. Proceed only if all are true:
- Branch A1, A2, and A3 fail or cannot preserve invariants.
- A live runtime probe proves an undocumented or raw exceptional request path is accepted.
- The request shape, initialization capabilities, raw response, notification sequence, and security probes are saved.
- A maintainer explicitly approves building against that security-boundary input.

Branch C output:
- A new high-risk implementation plan. Do not reuse the discarded migration plan.

### Branch D: No safe documented or approved path works

Fail closed if no documented path and no explicitly approved exceptional path preserves the required invariants.

Branch D output:
- Disable `/delegate` execution for Codex App Server `0.128.0` through an operator-facing unsupported-runtime error.
- The error must report detected launcher/version, supported versions if any, blocker artifact path, and the required operator action.

## Branch Adjudication Rule

Evaluate all applicable documented candidates before choosing a branch. Record per-candidate evidence for A1, A2, and A3 even if an earlier candidate appears promising.

If more than one Branch A candidate preserves every invariant, choose the implementation branch with this default preference order:

1. **A3: stable schema-grounded `sandboxPolicy`** if it preserves invariants without experimental capability opt-in or external config dependence.
2. **A1: experimental request-level `permissions`** if A3 does not pass and A1 preserves invariants with explicit `experimentalApi` negotiation.
3. **A2: config-level `default_permissions`** if A3 and A1 do not pass and A2 preserves invariants with reliable config provenance.

Within A2, select A2a built-in `:workspace` only if it independently preserves every required invariant. If built-in `:workspace` fails support-root or deny-boundary invariants and A2b user-defined profile passes, choose A2b as the A2 implementation target.

Override the preference order only if the decision packet records a concrete reason, such as launcher documentation declaring the preferred surface unsupported for this use case. Do not choose Branch B until all documented candidates and subcandidates have failed to qualify for Branch A.

## Files And Responsibilities

Read and reference:
- `docs/codex-app-server.md`
  - Stable vs experimental schema generation and `experimentalApi` runtime opt-in rules.
- Pinned Codex App Server implementation for the selected artifact, or an equivalent local source snapshot
  - Trust persistence during `thread/start`, `PermissionProfileSelectionParams`, thread response permission-profile metadata, user-defined profile compilation, and legacy `readOnlyAccess` deserialization behavior.
- `packages/plugins/codex-collaboration/server/runtime.py`
  - Current initialize payload, `build_workspace_write_sandbox_policy()`, and execution/advisory turn payload construction.
- `packages/plugins/codex-collaboration/server/control_plane.py`
  - Execution thread creation, runtime startup, and advisory/runtime separation.
- `packages/plugins/codex-collaboration/server/delegation_controller.py`
  - Worktree creation, execution runtime bootstrap, and `_execute_live_turn()` call site.
- `packages/plugins/codex-collaboration/server/jsonrpc_client.py`
  - JSON-RPC error capture and truncation behavior.
- `packages/plugins/codex-collaboration/server/codex_compat.py`
  - Current tested/minimum version reporting.
- `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/0.117.0/`
  - Existing fixture baseline for the old `readOnlyAccess` request shape.
- `docs/status/codex-collaboration-reconciliation-register.md`
  - Current T-20260429-01 status and exit condition context.

Create or update only after the relevant task says to:
- `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/0.128.0/`
  - Generated stable and experimental `0.128.0` schema fixtures, if fixture vendoring is selected.
- `docs/diagnostics/codex-app-server-v128-schema-runtime-decision.json`
  - Deterministic decision-packet artifact.
- `docs/diagnostics/codex-app-server-v128-root-rejection.json`
  - Runtime proof for the stale current payload, if root reproduction is run separately.
- `packages/plugins/codex-collaboration/scripts/probe_codex_v128_execution_sandbox.py`
  - Probe runner, if the decision packet is automated in-repo rather than run as an external scratch script.

## Diagnostic Artifact Schema

Every decision packet must be JSON and must include:

The concrete property arrays below are generated observations to record from the selected launcher artifact, not hand-authored constants. If a different selected launcher emits different properties, the packet records the generated values and classifies the difference.

```json
{
  "artifact_version": 2,
  "codex_version": "0.128.0",
  "launcher": {
    "kind": "codex app-server|codex-app-server",
    "resolved_path": "/absolute/path/to/launcher",
    "version_command": "command used",
    "version_output": "captured output",
    "help_command": "command used",
    "help_output_hash": "sha256",
    "binary_hash": "sha256 or null",
    "schema_and_runtime_use_same_launcher": true
  },
  "schema_sources": {
    "stable": {
      "generated_at": "ISO-8601 timestamp",
      "command": "launcher generate-json-schema --out DIR",
      "fixture_path": "path or null",
      "schema_hash": "sha256"
    },
    "experimental": {
      "generated_at": "ISO-8601 timestamp",
      "command": "launcher generate-json-schema --out DIR --experimental",
      "fixture_path": "path or null",
      "schema_hash": "sha256"
    }
  },
  "runtime_initialization_variants": {
    "stable": {
      "params_shape": {
        "clientInfo": "present",
        "capabilities": "omitted"
      },
      "experimentalApi": false
    },
    "experimental": {
      "params_shape": {
        "clientInfo": "present",
        "capabilities": {
          "experimentalApi": true
        }
      },
      "experimentalApi": true
    }
  },
  "runtime_environment": {
    "codex_home_strategy": "scratch_home|explicit_non_durable_trust_overrides|blocked",
    "codex_home_path": "path-or-null",
    "ambient_codex_home_used": false,
    "trust_persistence_strategy": "scratch_home|non_durable_override|blocked",
    "auth_strategy": "inherited_without_serializing_secret|copied_redacted_fixture|blocked",
    "auth_values_serialized": false,
    "notes": []
  },
  "request_contracts": {
    "stable": {
      "request_properties_full": {
        "TurnStartParams": ["approvalPolicy", "approvalsReviewer", "cwd", "effort", "input", "model", "outputSchema", "personality", "sandboxPolicy", "serviceTier", "summary", "threadId"],
        "ThreadStartParams": ["approvalPolicy", "approvalsReviewer", "baseInstructions", "config", "cwd", "developerInstructions", "ephemeral", "model", "modelProvider", "personality", "sandbox", "serviceName", "serviceTier", "sessionStartSource"],
        "ThreadForkParams": ["approvalPolicy", "approvalsReviewer", "baseInstructions", "config", "cwd", "developerInstructions", "ephemeral", "excludeTurns", "model", "modelProvider", "sandbox", "serviceTier", "threadId"],
        "ThreadResumeParams": ["approvalPolicy", "approvalsReviewer", "baseInstructions", "config", "cwd", "developerInstructions", "excludeTurns", "model", "modelProvider", "personality", "sandbox", "serviceTier", "threadId"],
        "CommandExecParams": ["command", "cwd", "disableOutputCap", "disableTimeout", "env", "outputBytesCap", "processId", "sandboxPolicy", "size", "streamStdin", "streamStdoutStderr", "timeoutMs", "tty"]
      },
      "permission_relevant_properties": {
        "TurnStartParams": ["sandboxPolicy"],
        "ThreadStartParams": ["sandbox"],
        "ThreadForkParams": ["sandbox"],
        "ThreadResumeParams": ["sandbox"],
        "CommandExecParams": ["sandboxPolicy"]
      }
    },
    "experimental": {
      "request_properties_full": {
        "TurnStartParams": ["approvalPolicy", "approvalsReviewer", "collaborationMode", "cwd", "effort", "environments", "input", "model", "outputSchema", "permissions", "personality", "responsesapiClientMetadata", "sandboxPolicy", "serviceTier", "summary", "threadId"],
        "ThreadStartParams": ["approvalPolicy", "approvalsReviewer", "baseInstructions", "config", "cwd", "developerInstructions", "dynamicTools", "environments", "ephemeral", "experimentalRawEvents", "mockExperimentalField", "model", "modelProvider", "permissions", "persistExtendedHistory", "personality", "sandbox", "serviceName", "serviceTier", "sessionStartSource"],
        "ThreadForkParams": ["approvalPolicy", "approvalsReviewer", "baseInstructions", "config", "cwd", "developerInstructions", "ephemeral", "excludeTurns", "model", "modelProvider", "path", "permissions", "persistExtendedHistory", "sandbox", "serviceTier", "threadId"],
        "ThreadResumeParams": ["approvalPolicy", "approvalsReviewer", "baseInstructions", "config", "cwd", "developerInstructions", "excludeTurns", "history", "model", "modelProvider", "path", "permissions", "persistExtendedHistory", "personality", "sandbox", "serviceTier", "threadId"],
        "CommandExecParams": ["command", "cwd", "disableOutputCap", "disableTimeout", "env", "outputBytesCap", "permissionProfile", "processId", "sandboxPolicy", "size", "streamStdin", "streamStdoutStderr", "timeoutMs", "tty"]
      },
      "permission_relevant_properties": {
        "TurnStartParams": ["permissions", "sandboxPolicy"],
        "ThreadStartParams": ["permissions", "sandbox"],
        "ThreadForkParams": ["permissions", "sandbox"],
        "ThreadResumeParams": ["permissions", "sandbox"],
        "CommandExecParams": ["permissionProfile", "sandboxPolicy"]
      }
    }
  },
  "permission_surfaces": {
    "stable_turn_permissions_field": false,
    "experimental_turn_permissions_field": true,
    "experimental_turn_permissions_type": "PermissionProfileSelectionParams",
    "experimental_command_exec_permissionProfile_field": true,
    "command_exec_permissionProfile_is_turn_execution_target": false,
    "workspace_write_properties": ["excludeSlashTmp", "excludeTmpdirEnvVar", "networkAccess", "type", "writableRoots"]
  },
  "strict_request_shape_validation": [],
  "runtime_probes": [],
  "candidate_results": {
    "A1": {
      "status": "not_run|inapplicable|rejected|accepted_failed_invariants|accepted_passed",
      "effective_permission_profile_required": true,
      "effective_permission_profile_recorded": false,
      "subcandidate_results": {
        "thread_start_permissions_named_profile": "not_run|inapplicable|rejected|accepted_failed_invariants|accepted_passed",
        "turn_start_permissions_named_profile": "not_run|inapplicable|rejected|accepted_failed_invariants|accepted_passed"
      },
      "failure_reasons": []
    },
    "A2": {
      "status": "not_run|inapplicable|rejected|accepted_failed_invariants|accepted_passed",
      "effective_permission_profile_required": true,
      "effective_permission_profile_recorded": false,
      "subcandidate_results": {
        "builtin_workspace_default": "not_run|inapplicable|rejected|accepted_failed_invariants|accepted_passed",
        "user_defined_profile_default": "not_run|inapplicable|rejected|accepted_failed_invariants|accepted_passed"
      },
      "config_provenance": {
        "isolated_config_or_home": false,
        "explicit_launcher_overrides": [],
        "ambient_user_config_used": false,
        "ambient_trust_state_used": false,
        "user_defined_profile_id": null,
        "user_defined_profile_shape": {
          "worktree_write": "present|absent|unexpressible",
          "support_root_reads": "present|absent|unexpressible",
          "credential_denies": "present|absent|unexpressible",
          "sentinel_denies": "present|absent|unexpressible",
          "tmp_policy": "present|absent|unexpressible",
          "network_policy": "present|absent|unexpressible"
        },
        "sanitized_summary": {}
      },
      "failure_reasons": []
    },
    "A3": {
      "status": "not_run|inapplicable|rejected|accepted_failed_invariants|accepted_passed",
      "effective_permission_profile_required": false,
      "effective_permission_profile_recorded": false,
      "failure_reasons": []
    }
  },
  "decision": {
    "branch": "A1|A2|A3|B|C|D|blocked",
    "reason": "short reason",
    "implementation_plan_required": true
  }
}
```

Each `strict_request_shape_validation` entry must include:

```json
{
  "name": "current_builder_payload_against_v128_stable_sandbox_policy",
  "schema_surface": "stable|experimental",
  "payload_kind": "current_builder|stable_sandbox_policy_candidate|experimental_thread_permissions_candidate|experimental_turn_permissions_candidate|config_default_permissions_builtin_candidate|config_user_defined_permissions_candidate|exceptional_candidate",
  "valid": false,
  "validator": "closed_workspace_write_properties|permission_profile_selection_params|config_contract",
  "allowed_workspace_write_keys": ["excludeSlashTmp", "excludeTmpdirEnvVar", "networkAccess", "type", "writableRoots"],
  "unexpected_paths": ["sandboxPolicy.workspaceWrite.readOnlyAccess"],
  "rejected_paths": ["sandboxPolicy.workspaceWrite.readOnlyAccess"],
  "sanitized_payload_shape": {}
}
```

Each `runtime_probes` entry must include:

```json
{
  "name": "experimental_permissions_named_profile",
  "payload_kind": "current_builder|stable_sandbox_policy_candidate|experimental_thread_permissions_candidate|experimental_turn_permissions_candidate|config_default_permissions_builtin_candidate|config_user_defined_permissions_candidate|exceptional_candidate",
  "schema_surface": "stable|experimental",
  "initialize_variant": "stable|experimental",
  "experimental_api_enabled": true,
  "request_method": "turn/start",
  "runtime_environment": {
    "codex_home_strategy": "scratch_home|explicit_non_durable_trust_overrides|blocked",
    "ambient_codex_home_used": false,
    "trust_persistence_observed": false,
    "auth_strategy": "inherited_without_serializing_secret|copied_redacted_fixture|blocked",
    "auth_values_serialized": false
  },
  "sanitized_request_shape": {},
  "accepted": false,
  "raw_error": {},
  "notifications_observed": [],
  "thread_id": null,
  "turn_id": null,
  "active_permission_profile": {
    "present": false,
    "source": "thread/start|thread/resume|thread/fork|thread/read|turn/read|not_reported",
    "profile_id": ":workspace|null",
    "sanitized_summary": {},
    "fallback_observed": false,
    "fallback_evidence": []
  },
  "command_launched": false,
  "classification": "stable_field_absent|experimental_capability_required|unrelated_validation_error|shape_rejected|runtime_rejected_before_turn|accepted|accepted_with_profile_fallback|approval_rejected|sandbox_prelaunch_denial|postlaunch_sandbox_kill|model_refusal|blocked_unknown",
  "evidence": []
}
```

Do not record credential values, session contents, auth tokens, or full home-directory listings.

## Required Probe Definitions

### Launcher and schema provenance

1. **Launcher selection**
   - Record whether probes use `codex app-server` or standalone `codex-app-server`.
   - Record the resolved launcher path.
   - Record version output and help output hash.
   - Record a binary hash when the launcher resolves to a directly hashable file.
   - Require stable schema generation, experimental schema generation, and runtime probes to use the same launcher.

2. **Stable and experimental schemas**
   - Generate stable schema with the selected launcher's default schema command.
   - Generate experimental schema with the same launcher and `--experimental`.
   - Record all request properties for `TurnStartParams`, `ThreadStartParams`, `ThreadForkParams`, `ThreadResumeParams`, and `CommandExecParams` for both surfaces.
   - Record permission-relevant properties separately for both surfaces.

### Strict request-shape validations

The generated stable `0.128.0` `workspaceWrite` schema block lists the accepted properties but does not set `additionalProperties: false`. Plain JSON Schema validation is therefore not sufficient to prove stale extra fields are rejected. These checks must use a custom closed-key validator that treats the generated `workspaceWrite.properties` key set as authoritative for request-shape compatibility.

1. **Current builder payload**
   - Generate the current `build_workspace_write_sandbox_policy(worktree_path)` output.
   - Run the closed-key validator against generated stable `0.128.0` `TurnStartParams.properties.sandboxPolicy`.
   - Expected unexpected/rejected path: `sandboxPolicy.workspaceWrite.readOnlyAccess`.
   - Record that the current payload uses legacy restricted `readOnlyAccess`, not the legacy `fullAccess` compatibility shim.

2. **Stable sandboxPolicy candidate**
   - Build a candidate using only the generated stable `0.128.0` `workspaceWrite` properties:
     - `type`
     - `writableRoots`
     - `networkAccess`
     - `excludeSlashTmp`
     - `excludeTmpdirEnvVar`
   - Run the closed-key validator against generated stable `0.128.0` `TurnStartParams.properties.sandboxPolicy`.
   - Also run ordinary JSON Schema validation if available, but do not treat it as the proof that extra keys are absent.

3. **Experimental permissions candidates**
   - Build a thread-level `permissions` candidate using the experimental `ThreadStartParams.properties.permissions` shape.
   - Build a turn-level `permissions` candidate using the experimental `TurnStartParams.properties.permissions` shape.
   - Start both with built-in `":workspace"` and `modifications: []`.
   - Validate both against the experimental `PermissionProfileSelectionParams` contract.
   - Record that `modifications` only supports additional writable roots and must not be used as a substitute for PR #127 read-only support-root access.
   - Do not use raw full `permissionProfile` for `turn/start`; that field is not the documented turn request surface.

4. **Config default permissions candidates**
   - Use an isolated config/home or explicit launcher `-c` overrides for the candidate.
   - Validate the built-in `:workspace` default candidate when the selected launcher documents or accepts it.
   - Validate an isolated user-defined profile candidate when the selected launcher documents or accepts `[permissions.<id>]` plus `default_permissions`.
   - The user-defined profile candidate must explicitly record whether worktree write, support-root reads, credential/session denies, sentinel denies, tmp policy, and network policy are expressible.
   - Record the config mechanism under test, including config path or override keys, environment overrides, managed requirements influence, selected profile id, and proof that ambient user config and ambient trust state did not decide the outcome.
   - Do not read or serialize credential-class config content.

### Runtime probes

Run probes with fresh App Server processes unless a scenario explicitly tests same-thread stickiness. Fresh processes are not sufficient isolation by themselves because thread startup can persist project trust into Codex home. Every runtime candidate probe, including A1 and A3, must use either a scratch Codex home or an explicit non-durable trust/config override strategy. Record how authentication is supplied without serializing secrets. If auth cannot be supplied safely under isolation, classify the probe as blocked instead of falling back to the operator's ambient `~/.codex` state. Every runtime probe must record whether it used stable initialization or experimental initialization.

1. **Capability gating control**
   - Send an otherwise valid and complete `turn/start` request that includes an experimental `permissions` field without `capabilities.experimentalApi = true`.
   - The control request must use a valid thread id, `cwd`, input shape, model/config fields required by the selected launcher, and no other intentionally malformed fields.
   - Expected classification: `experimental_capability_required`.
   - If the runtime rejects a different part of the request first, classify it as `unrelated_validation_error` and fix the control before using it as capability-gating evidence.
   - This proves later experimental failures are not being confused with missing opt-in.

2. **Root reproduction**
   - Send the current stale payload.
   - Save sanitized request, raw error, notifications, and turn/thread creation status.
   - The probe must bypass or extend the current `JsonRpcClient` error path so the artifact records the full raw JSON-RPC error object instead of the existing bounded string.

3. **Experimental request-level permissions acceptance**
   - Initialize with `capabilities.experimentalApi = true`.
   - Send `thread/start.permissions` using a named profile selection such as `{"type": "profile", "id": ":workspace", "modifications": []}`.
   - Record active/effective permission profile evidence from `thread/start`, `thread/resume`, `thread/fork`, or later read APIs when available.
   - Separately send `turn/start.permissions` to test turn override acceptance and stickiness.
   - Record that `turn/start` alone does not return active profile metadata and cannot satisfy Branch A1 provenance without thread-level or readback evidence.
   - Record whether the runtime used the requested profile, omitted it from projections, or fell back to another profile because of requirements.
   - Acceptance alone is not sufficient for Branch A1.

4. **Config-level default permissions acceptance**
   - Launch the selected app-server with the intended config-level default permissions mechanism using an isolated config/home or explicit launcher `-c` overrides.
   - Probe the built-in `:workspace` default candidate when applicable.
   - Probe an isolated user-defined profile candidate when the launcher documents or accepts `[permissions.<id>]` profiles.
   - The user-defined profile candidate must attempt support-root read access directly, not by adding the support roots as writable roots.
   - Omit per-turn experimental `permissions`.
   - Record sanitized config-layer provenance and proof that ambient user config, ambient trust state, and unrelated network flags did not decide the result.
   - Record active/effective permission profile evidence from thread-level responses or later read APIs when available.
   - Record whether the runtime used the configured default, omitted it from projections, or fell back to another profile because of requirements.
   - Acceptance alone is not sufficient for Branch A2.

5. **Stable sandboxPolicy acceptance**
   - Send the stable candidate `sandboxPolicy.workspaceWrite` payload without `readOnlyAccess`.
   - Acceptance alone is not sufficient for Branch A3.

6. **Worktree behavior**
   - Confirm `pwd` equals the resolved execution worktree.
   - Confirm `ls`, scratch write/read, and `git status` behavior.
   - A model-mediated probe is inconclusive unless the intended command actually launches, or a prelaunch denial is observed.

7. **PR #127 support roots**
   - Define support roots explicitly:
     - `~/.codex/memories`
     - `~/.codex/plugins/cache`
     - `~/.agents/skills`
     - `~/.agents/plugins`
     - resolved worktree gitdir
   - For each root, classify as `accessible`, `blocked`, `not_present`, or `not_needed_by_probe`.
   - `not_needed_by_probe` does not preserve the invariant for any Branch A by itself.
   - For Branch A1/A2/A3, each root must be either directly proven accessible when needed by a comparable execution path, or accompanied by evidence that the comparable T-20260429-01 execution path no longer needs that root.
   - For A1 turn-level `permissions`, do not count `AdditionalWritableRoot` as preservation of a read-only support-root invariant. That would widen the boundary.
   - For A2 user-defined profile, record whether each support root is represented as read-only, writable, denied, or unexpressible.
   - If a required root is blocked, unexpressible, or only marked `not_needed_by_probe` without comparable-path evidence, the Branch A candidate fails.

8. **Negative filesystem controls**
   - Use a production-style path:
     `<plugin_data_path>/runtimes/delegation/<probe_job_id>/worktree`
   - Place sentinels at:
     - `<probe_job_dir>/parent-sentinel.txt`
     - `<probe_job_dir>/sibling/sibling-sentinel.txt`
   - Any completed command that returns either sentinel token is a security failure.

9. **Credential/session boundaries**
   - Probe these paths without printing contents:
     - `~/.codex/auth.json`
     - `~/.codex/config.toml`
     - `~/.codex/history.jsonl`
     - `~/.codex/sessions/`
   - Expected result: blocked.

10. **Tmp and network boundaries**
    - Probe `/tmp`.
    - Probe the runtime value of `$TMPDIR`.
    - Probe network access.
    - Classify whether blocking happens by shape rejection, capability rejection, approval rejection, prelaunch denial, postlaunch sandbox kill, or another mechanism.

11. **Thread and turn stickiness**
   - Stable `thread/start` takes `sandbox`; experimental `thread/start` also exposes `permissions`.
   - Stable `turn/start.sandboxPolicy` is documented as applying to "this turn and subsequent turns."
   - Experimental `turn/start.permissions` is documented as applying to "this turn and subsequent turns."
   - Record `activePermissionProfile` and `permissionProfile` from thread-level responses when the schema and runtime expose them.
   - Test whether a first execution turn changes behavior for a second turn on the same thread.
   - Test whether thread creation without a permissions payload constrains later execution turn overrides.

## Task Sequence

### Task 0: Capture app-server launcher provenance

- [ ] Select the launcher artifact to probe: `codex app-server` or standalone `codex-app-server`.
- [ ] Record the resolved launcher path.
- [ ] Record version output.
- [ ] Record help output hash.
- [ ] Record a binary hash when feasible.
- [ ] Record the exact commands that will generate stable schema, experimental schema, and launch runtime probes.
- [ ] Stop if schema generation and runtime probing cannot use the same launcher artifact.
- [ ] Define the runtime isolation strategy for all candidate probes: scratch Codex home or explicit non-durable trust/config overrides.
- [ ] Define the auth strategy for isolated probes without serializing credential values.

Expected checkpoint:
- The packet cannot accidentally apply schema from one app-server artifact to runtime behavior from another.
- The packet cannot mutate the operator's real Codex home or inherit ambient trust/config state by accident.

### Task 1: Capture stable and experimental schema provenance

- [ ] Run stable schema generation with the selected launcher.
- [ ] Run experimental schema generation with the selected launcher and `--experimental`.
- [ ] Save generated schemas or a decision-packet reference to immutable locations.
- [ ] Record request properties for `TurnStartParams`, `ThreadStartParams`, `ThreadForkParams`, `ThreadResumeParams`, and `CommandExecParams` for both surfaces.
- [ ] Record stable and experimental permission-relevant properties.
- [ ] Record that request-level `permissions` is experimental for thread/turn paths.
- [ ] Record that raw `CommandExecParams.permissionProfile` is experimental and command-scoped, not the documented `/delegate` turn-start target.

Expected checkpoint:
- The decision packet can prove the stable and experimental request contracts without relying on prose memory.

### Task 2: Add or run strict request-shape validation

- [ ] Run a custom closed-key validator for the current builder payload against the generated stable `0.128.0` `workspaceWrite.properties` key set.
- [ ] Record `sandboxPolicy.workspaceWrite.readOnlyAccess` as the unexpected/rejected path.
- [ ] Run the same closed-key validator for the stable sandboxPolicy candidate payload.
- [ ] Validate the experimental `thread/start.permissions` candidate against the experimental `PermissionProfileSelectionParams` shape.
- [ ] Validate the experimental `turn/start.permissions` candidate against the experimental `PermissionProfileSelectionParams` shape.
- [ ] Record that request-level `permissions.modifications` cannot encode read-only support roots because it only adds writable roots.
- [ ] Validate the config-level built-in `:workspace` default candidate when applicable.
- [ ] Validate the config-level user-defined permissions profile candidate when applicable, including expressibility of worktree write, support-root reads, credential/session denies, sentinel denies, tmp policy, and network policy.
- [ ] Optionally run ordinary JSON Schema validation as a secondary check, but do not rely on it to reject extra keys.
- [ ] If a candidate does not pass its required request-shape validation, record that candidate as `rejected` or `inapplicable` with rejected paths and continue remaining documented candidates.
- [ ] Stop only if launcher/schema provenance is invalid, or if no documented candidate remains shape-probeable.

Expected checkpoint:
- The stale-payload defect is proven structurally, and every documented candidate is either structurally eligible for runtime probing or recorded as rejected/inapplicable without blocking the other candidates.

### Task 3: Probe experimental runtime negotiation

- [ ] Send an otherwise valid and complete request containing experimental `permissions` without `capabilities.experimentalApi = true`.
- [ ] Capture the raw JSON-RPC error object.
- [ ] Confirm the classification is `experimental_capability_required`.
- [ ] If any unrelated validation error appears first, fix the control request and rerun before drawing capability-gating conclusions.
- [ ] Initialize a fresh runtime with `capabilities.experimentalApi = true`.
- [ ] Confirm experimental `permissions` is no longer rejected solely for missing capability opt-in.
- [ ] Bypass or extend the existing `JsonRpcClient` initialization path because current `runtime.py` initializes without `capabilities`.

Expected checkpoint:
- Experimental probe failures can be attributed to payload semantics rather than missing capability negotiation.

### Task 4: Run root runtime reproduction

- [ ] Send the current stale payload to `turn/start`.
- [ ] Capture the full raw JSON-RPC error object.
- [ ] Bypass or extend the existing `JsonRpcClient` truncation path so the artifact stores the raw error object.
- [ ] Capture sanitized request shape.
- [ ] Capture notifications and whether a turn/thread was created.
- [ ] Save `docs/diagnostics/codex-app-server-v128-root-rejection.json` if this is a standalone artifact.

Expected checkpoint:
- Runtime failure is reproducible and not dependent on truncated MCP stderr.

### Task 5: Probe documented candidate behavior

- [ ] Probe Branch A1 thread-level candidate: experimental `thread/start.permissions` named profile selection.
- [ ] Probe Branch A1 turn-level candidate: experimental `turn/start.permissions` named profile selection.
- [ ] Probe Branch A2a candidate: config-level built-in `default_permissions = ":workspace"`, if documented and available for the selected launcher.
- [ ] Probe Branch A2b candidate: config-level user-defined profile selected through `default_permissions`, if documented and available for the selected launcher.
- [ ] Probe Branch A3 candidate: stable `sandboxPolicy.workspaceWrite` without `readOnlyAccess`.
- [ ] For A1 and A2, record active/effective permission profile evidence, fallback evidence, or explicit absence of runtime projection.
- [ ] For A2b, record whether support roots are read-only, writable, denied, or unexpressible; writable support roots do not preserve the PR #127 invariant.
- [ ] Run worktree behavior probes for each candidate that is accepted.
- [ ] Run PR #127 support-root probes for each accepted candidate.
- [ ] Run negative filesystem controls for each accepted candidate.
- [ ] Run credential/session, tmp, and network probes for each accepted candidate.
- [ ] Classify every blocked result by mechanism.

Expected checkpoint:
- The packet can distinguish stable field absence, experimental capability gating, request acceptance, and invariant preservation.

### Task 6: Probe thread and turn semantics

- [ ] Record stable and experimental `thread/start` request shapes and response shapes.
- [ ] Record `activePermissionProfile` and `permissionProfile` fields from `thread/start`, `thread/resume`, `thread/fork`, or readback responses when exposed.
- [ ] Run same-thread first-turn and second-turn probes for accepted candidates.
- [ ] Record whether `turn/start.sandboxPolicy` or `turn/start.permissions` sticks to subsequent turns.
- [ ] Record whether thread creation without payload constrains later execution sandbox/permissions overrides.
- [ ] If Branch A1 is selected, decide whether the later implementation must move permission selection into execution `thread/start` before the first turn.

Expected checkpoint:
- The implementation branch knows whether builder changes alone are enough or whether initialization/thread creation semantics matter.

### Task 7: Decide Branch A1/A2/A3/B/C/D

- [ ] Record per-candidate results for A1, A2, and A3 as `inapplicable`, `rejected`, `accepted_failed_invariants`, or `accepted_passed`.
- [ ] Record per-subcandidate results for A1 thread-level, A1 turn-level, A2a built-in default, and A2b user-defined default.
- [ ] Apply the default winner preference order: A3 over A1 over A2, unless the packet records a concrete override reason.
- [ ] Choose exactly one branch.
- [ ] Record the branch in `docs/diagnostics/codex-app-server-v128-schema-runtime-decision.json`.
- [ ] If Branch A1, write a new implementation plan for experimental `permissions` named profile selection.
- [ ] If Branch A2, write a new implementation plan for config-level default permissions, including whether the selected target is A2a built-in or A2b user-defined.
- [ ] If Branch A3, write a new implementation plan for updating the stable schema-grounded `sandboxPolicy` builder.
- [ ] If Branch B, save a blocker artifact showing that no documented A candidate passed and at least one accepted documented candidate failed invariants.
- [ ] If Branch C, require explicit maintainer approval before writing a high-risk implementation plan.
- [ ] If Branch D, write a fail-closed unsupported-runtime plan.

Expected checkpoint:
- The next work item is implementation only if the decision packet proves a safe branch.

## T-20260429-01 Boundary

This plan does not close T-20260429-01.

T-20260429-01 closure remains separate and requires:
- A comparable live `/delegate` smoke.
- Credential/session probes blocked.
- Avoidable sandbox-friction classification under the ticket's acceptance frame.
- `file_change` opacity counted separately as an upstream limitation.

The decision packet may unblock that smoke, but it does not supersede the ticket's current exit condition unless a later implementation plan explicitly proves and records that relationship.

## Acceptance Criteria

The decision-packet plan is complete when:
- The selected app-server launcher artifact is recorded with path, version/help evidence, schema commands, and binary hash when feasible.
- Every runtime candidate probe records scratch-home or non-durable trust/config isolation, auth strategy, and proof that ambient Codex home/trust/config state did not decide the result.
- Stable and experimental generated `0.128.0` request contracts are saved or referenced immutably.
- Experimental runtime probes record whether `capabilities.experimentalApi = true` was negotiated.
- The current payload is rejected by strict closed-key request-shape validation at `sandboxPolicy.workspaceWrite.readOnlyAccess`.
- The packet records the legacy `readOnlyAccess.fullAccess` compatibility shim separately from the rejected restricted `readOnlyAccess` payload.
- Runtime root reproduction is saved with raw error and sanitized request shape.
- Each documented candidate and subcandidate is either proven safe or shown to fail specific invariants.
- A1/A2 effective permission/profile provenance is recorded, including fallback evidence or explicit absence of runtime projection.
- A1 includes thread-level permissions probing or explicitly records why thread-level provenance is unavailable.
- A2 includes both built-in `:workspace` and user-defined profile subcandidate evidence where the selected launcher makes them applicable.
- Branch B is selected only after all applicable documented candidates fail to qualify for Branch A.
- PR #127 support roots are explicitly classified.
- Thread/turn stickiness is classified.
- Exactly one Branch A1/A2/A3/B/C/D decision is recorded.
- No implementation migration proceeds without a recorded Branch A1/A2/A3 or explicitly approved Branch C.

## Non-Goals

- Do not update `run_execution_turn()` to require raw `permission_profile`.
- Do not add `_run_turn(permission_field="permissionProfile")`.
- Do not treat stable-only schema generation as the full request contract.
- Do not send experimental fields without recording `experimentalApi` capability negotiation.
- Do not let runtime probes mutate or depend on the operator's ambient Codex home, persisted trust state, or real config unless the packet explicitly records that no isolated auth strategy is possible and classifies the probe as blocked.
- Do not treat undocumented runtime acceptance as a stable API.
- Do not use `AdditionalWritableRoot` as a substitute for read-only support-root access.
- Do not treat legacy `readOnlyAccess.fullAccess` compatibility as evidence that restricted `readOnlyAccess` remains supported.
- Do not close T-20260429-01 from schema evidence alone.
- Do not weaken credential, session, parent/sibling sentinel, tmp, or network boundaries to make the smoke pass.

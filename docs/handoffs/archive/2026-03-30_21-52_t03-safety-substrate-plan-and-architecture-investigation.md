---
date: 2026-03-30
time: "21:52"
created_at: "2026-03-31T01:52:36Z"
session_id: dbc80eff-ba6d-4343-9236-36785c4991fe
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-30_18-31_t02-plugin-shell-implemented-pending-review.md
project: claude-code-tool-dev
branch: feature/codex-collaboration-safety-substrate
commit: e67f97ff
title: "T-03 safety substrate plan and architecture investigation"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/mcp_server.py
  - packages/plugins/codex-collaboration/tests/test_mcp_server.py
  - packages/plugins/codex-collaboration/skills/consult-codex/SKILL.md
  - packages/plugins/codex-collaboration/skills/codex-status/SKILL.md
  - docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md
---

# Handoff: T-03 safety substrate plan and architecture investigation

## Goal

Complete the T-02 review cycle, then investigate and plan T-03 (codex-collaboration safety substrate and benchmark contract). T-03 ports the cross-model safety substrate — credential scanning, tool-input safety policy, consultation profiles, learning retrieval, analytics emission — into codex-collaboration and lands the benchmark contract that governs the context-injection retirement decision.

**Trigger:** T-02 was implemented in the prior session and pending user review. The user's stated goal is to "complete building the codex-collaboration system/plugin in full" to supersede cross-model. T-03 is the second step in the 6-ticket supersession roadmap.

**Stakes:** Without the safety substrate, codex-collaboration's consult and dialogue surfaces operate without credential scanning, consultation profiles, or learning injection. The cross-model plugin has these capabilities; their absence in codex-collaboration means the new plugin cannot be a full replacement.

**Success criteria:** 8 acceptance criteria from the T-03 ticket (all but AC6/analytics are covered in the plan; AC6 is deferred pending Thread C investigation).

**Connection to project arc:** Spec compiled → T1 → R1 → R2 → Post-R2 hardening → Supersession roadmap → **T-02 landed** → **T-03 planned (this session)** → T-03 implementation (next session).

## Session Narrative

### Loaded T-02 handoff and applied review fixes

Loaded the prior handoff (`2026-03-30_18-31_t02-plugin-shell-implemented-pending-review.md`). The user shared two review findings:

1. **Recovery retry bug** in `mcp_server.py:121-123`: `_ensure_dialogue_controller()` cached the dialogue controller and cleared the factory before `recover_startup()` succeeded. If recovery raised on the first call (transient runtime/auth issue), the controller was pinned in a partially initialized state and no subsequent call could retry recovery.

2. **Underspecified `repo_root` in packaged skills**: `consult-codex/SKILL.md` and `codex-status/SKILL.md` referenced "current git repository root" without specifying how to compute it. Since `.mcp.json` launches the server with `--directory ${CLAUDE_PLUGIN_ROOT}`, any relative fallback would resolve to the plugin directory, not the user's repo.

Fixed both issues. The recovery fix was a 3-line reorder: create controller into local variable, run `recover_startup()`, only then assign and clear factory. The skill fix added `Bash` to `allowed-tools` and an explicit `git rev-parse --show-toplevel` step with stop-on-failure. Added one new test (`test_transient_recovery_failure_allows_retry`). User reviewed the follow-up patch and found no issues. 239 tests passing.

Committed T-02 at `e67f97ff`, merged to `main`, deleted the feature branch.

### Investigated T-03 scope and cross-model substrate

Read the T-03 ticket (`docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md`) and the benchmark contract (`docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`). Dispatched an exploration agent to analyze the 5 cross-model substrate sources plus the secret taxonomy.

Proposed an initial 5-step implementation sequence. The user then challenged my claim that the profile schema was "domain-level, not architecture-specific."

### Verified profile fields against the runtime — corrected the claim

Investigated `runtime.py:124-125` and found that `sandbox`, `approval_policy`, and `reasoning_effort` are Codex CLI API parameters, not domain abstractions. The runtime hard-codes `approvalPolicy: "never"` and `sandboxPolicy: {"type": "readOnly"}`. `reasoning_effort` isn't parameterized at all.

This meant porting profiles "verbatim" was insufficient — the runtime needed plumbing to accept and forward these execution controls. Revised the implementation sequence to add a runtime parameterization step.

### User's three-hypothesis checkpoint reshaped the plan

The user provided three ranked hypotheses with evidence requirements and tests:

1. **Runtime/policy reuse (most likely):** Advisory runtime cached by `repo_root` only, `policy_fingerprint` hard-coded. If profiles change sandbox/approvals, need explicit reuse/rotate/reject rules.

2. **Safety boundary (next most likely):** Hook sees raw MCP args, not the assembled packet with learnings/file excerpts added by the control plane. Hook-only guard misses server-injected content.

3. **Profile/audit schema expansion (third):** `ConsultRequest` has no profile/posture/turn_budget fields. `AuditEvent` has a minimal schema. `prompt_builder` doesn't consume posture.

The user recommended investigating Thread A first, which proved decisive.

### Thread A: Found no rotation needed for current profiles

Read `advisory-runtime-policy.md` — the spec defines a freeze-and-rotate protocol: policy changes require freezing the current runtime, starting a new one with different policy, forking thread history. The policy fingerprint is computed from 5 material fields (transport, sandbox, network, approval, app connectors).

Key discovery: **all 9 current profiles share `sandbox: read-only` and `approval_policy: never`** — identical to the hard-coded values. `reasoning_effort` is not in the fingerprint. No profile would trigger rotation.

The user validated this with App Server wire shape findings: the `turn/start` field is `effort` (not `reasoning_effort`), effort is sticky per thread (persists to subsequent turns), `thread/read` doesn't expose current effort back. App Server has native `ProfileV2` but it's a different abstraction with no `posture`, `turn_budget`, or `sandbox_mode` — naming collision, not integration shortcut.

### Thread B: Traced the safety boundary — narrower gap than feared

Traced the complete consult path from MCP dispatch through `assemble_context_packet()` to `build_consult_turn_text()`. Mapped every content injection point against `_redact_text()` coverage:

- Every user-content injection path (file excerpts, text entries, summaries, objective, constraints) passes through `_redact_text()` — verified at specific lines in `context_assembly.py`
- `repo_identity.branch` and `repo_identity.head` do NOT pass through `_redact_text()` — `head` is a hex SHA (safe), `branch` is user-controlled (gap)
- Generated constants (safety envelope, capability instructions) have no user content (safe)

The gap is **pattern coverage, not boundary coverage**: `_redact_text` uses 8 inline patterns, `secret_taxonomy` has 14 with tiered enforcement. The inner boundary exists but uses a weaker pattern set.

User confirmed the synthesis and added two caveats:
1. "Fails closed" (AC1) applies at the hook boundary. The inner boundary sanitizes-and-continues — blocking the entire consult because a file excerpt contains a pattern would be hostile UX.
2. `repo_identity.branch` should pass through `_redact_text()` for completeness — branch names are user-controlled.

### Wrote the implementation plan

Created the plan at `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md`. Nine tasks covering 7 of 8 acceptance criteria, plus a deferred Task 10 for analytics emission (pending Thread C investigation). Created the feature branch `feature/codex-collaboration-safety-substrate`.

## Decisions

### Keep inline _SECRET_PATTERNS separate from taxonomy (option A)

**Choice:** `context_assembly.py`'s 8 inline patterns and `secret_taxonomy.py`'s 14 patterns serve different trust boundaries. Keep them separate by purpose; upgrade the inner boundary to use the taxonomy.

**Driver:** The ticket says "port semantics, not code blindly." The two call sites have different failure modes: the inner boundary sanitizes outbound content going to Codex (redact and continue), while the taxonomy/scanner blocks inbound tool calls (fail closed).

**Rejected:**
- **Unify immediately (option B)** — have `_redact_text` consume `FAMILIES` filtered to `redact_enabled=True`. Rejected because unification couples two boundaries with different failure semantics. The inline patterns will be replaced by the taxonomy as part of the plan (Task 3), but the upgrade happens by design, not by sharing a reference.

**Trade-offs accepted:** During Task 3 implementation, the 8 inline patterns get replaced by taxonomy-backed redaction. The "keep separate" decision is about the interim state and the architectural rationale, not the final code.

**Confidence:** High (E2) — both pattern sets traced to their call sites, failure modes confirmed different.

**Reversibility:** High — the plan already replaces the inline patterns with taxonomy-backed redaction in Task 3.

**Change trigger:** None — this is already being resolved by the plan.

### Inner boundary sanitizes, outer boundary fails closed

**Choice:** The PreToolUse hook (outer boundary) returns exit code 2 to block the MCP tool call on credential detection. The `_redact_text` upgrade (inner boundary) replaces secrets with `[REDACTED:value]` and continues.

**Driver:** Server-injected content (file excerpts, learnings) comes from the user's own repo. Blocking the entire consult because a file excerpt pattern-matches an AWS key is hostile UX. The user confirmed: "redact before Codex is sufficient for server-injected content."

**Rejected:**
- **Both boundaries fail closed** — rejected because server-side content is not user-authored MCP arguments. The control plane reads files from the user's repo and injects them. Blocking would mean the user can't consult about their own code if it contains credential patterns.

**Trade-offs accepted:** A secret in server-injected content reaches the control plane's packet but is redacted before Codex sees it. If redaction fails (pattern miss), the secret goes to Codex. The taxonomy upgrade (14 patterns with placeholder bypass) reduces this risk significantly.

**Confidence:** High (E2) — traced every injection path through `_redact_text`, confirmed coverage.

**Reversibility:** Medium — changing the inner boundary to fail-closed would require a new scan insertion point in the control plane and error handling changes in the dispatch path.

**Change trigger:** If a secret bypasses both the taxonomy patterns and the inner redaction, the policy would need revisiting.

### Add _redact_text to repo_identity.branch

**Choice:** Pass `repo_identity.branch` through `_redact_text()` in `_render_packet()` at `context_assembly.py:254`.

**Driver:** User: "`repo_identity` is not entirely 'non-user content.' `head` is harmless, but `branch` is user-controlled and currently bypasses `_redact_text()`."

**Rejected:** None — the gap is real (branch names like `feature/password=hunter2abc` would match credential patterns).

**Trade-offs accepted:** None — trivially safe to redact.

**Confidence:** High (E2) — verified `head` is a hex SHA (safe), `branch` is user-controlled (gap).

**Reversibility:** High — one line change.

**Change trigger:** None.

### Validation gate rejects sandbox/approval widening

**Choice:** After profile resolution, reject if `sandbox != "read-only"` or `approval_policy != "never"` with an explicit error message mentioning freeze-and-rotate.

**Driver:** All 9 current profiles use `sandbox: read-only` and `approval_policy: never`, so no rotation is needed. But the profile schema allows values that would require rotation. The gate prevents profiles from silently promising capabilities the runtime can't deliver.

**Rejected:**
- **Implement rotation now** — rejected because T-03 is the safety substrate ticket, not the runtime-identity ticket. Rotation is a significant protocol implementation.
- **Silently ignore sandbox/approval fields** — rejected because silent ignoring would make the profile contract misleading.

**Trade-offs accepted:** Future profiles that need `workspace-write` or `ask` approval can't be used until rotation is implemented.

**Confidence:** High (E2) — verified all 9 profiles share the same policy values; verified `policy_fingerprint` material does not include `reasoning_effort`.

**Reversibility:** High — remove the gate when freeze-and-rotate is implemented.

**Change trigger:** Landing freeze-and-rotate protocol.

### Defer analytics emission (AC6) pending Thread C

**Choice:** Implement Tasks 1-8 (covering ACs 1-5, 7, 8) without analytics emission. Plan Task 10 for AC6 after Thread C investigation.

**Driver:** The `AuditEvent` schema at `models.py:138-153` is deliberately minimal with a comment: "R1 only emits consult events. [...] should revisit AuditEvent shape before [new actions are] emitted." Profile fields, posture, convergence mapping, and synthesis parsing all need schema decisions before code can be written.

**Rejected:**
- **Include AC6 in the plan with provisional schema** — rejected because provisional fields create migration debt if the schema answer changes.

**Trade-offs accepted:** T-03 delivers 7 of 8 acceptance criteria. AC6 requires a follow-up plan after Thread C.

**Confidence:** Medium (E1) — the deferral is sound but AC6 is needed for full T-03 closure.

**Reversibility:** High — AC6 is additive. Nothing blocks it from being added later.

**Change trigger:** Thread C investigation completing.

## Changes

### `server/mcp_server.py` — Recovery retry fix

**Purpose:** Fix the deferred dialogue init recovery bug identified in user review.

**Changes:** `_ensure_dialogue_controller()` at lines 121-124 reordered: creates controller into local variable, runs `recover_startup()`, only pins the controller and clears the factory after recovery succeeds. If recovery raises, the factory remains available for retry on the next dialogue call.

### `tests/test_mcp_server.py` — Transient recovery retry test

**Purpose:** Prove the controller is not pinned on failed recovery.

**New test:** `test_transient_recovery_failure_allows_retry` — first dialogue call has factory whose `recover_startup()` raises (factory count 1, MCP error returned). Second call: factory invoked again, recovery succeeds, request completes (factory count 2, normal response).

### `skills/consult-codex/SKILL.md` — Deterministic repo_root derivation

**Purpose:** Fix the underspecified `repo_root` in the packaged consult skill.

**Changes:** Added `Bash` to `allowed-tools`. New step 1: run `git rev-parse --show-toplevel` via Bash. If the command fails, stop and report "not a git repository" — do NOT fall back to current directory. Steps renumbered 1-4. `repo_root` references updated to cite step 1 output.

### `skills/codex-status/SKILL.md` — Same repo_root fix

**Purpose:** Same fix as consult-codex, applied to the status skill.

**Changes:** Added `Bash` to `allowed-tools`. New step 1 for deterministic repo root derivation. Steps renumbered 1-5.

### `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` — Implementation plan

**Purpose:** Detailed implementation plan for T-03 with complete code for every step.

**Content:** 9 tasks (plus deferred Task 10) covering secret taxonomy, credential scanner, inner redaction upgrade, tool-input safety policy, PreToolUse hook guard, learning retrieval, consultation profiles + runtime effort wiring, benchmark contract wiring, and full verification. Each task follows TDD: write failing test, verify failure, implement, verify pass, commit.

## Codebase Knowledge

### Key Code Locations (Verified This Session)

| What | Location | Why verified |
|------|----------|-------------|
| `_ensure_dialogue_controller()` | `mcp_server.py:107-124` | Fixed: recovery retry bug |
| `build_policy_fingerprint()` | `control_plane.py:371-385` | Read: 5 hard-coded material fields, `reasoning_effort` not included |
| `_advisory_runtimes` cache | `control_plane.py:64` | Read: keyed by `str(repo_root)`, one runtime per repo |
| Advisory runtime policy spec | `advisory-runtime-policy.md` | Read: freeze-and-rotate protocol, turn boundary invariants |
| `codex_consult()` dispatch | `control_plane.py:130-206` | Traced: request → identity → stale marker → assembly → runtime → turn |
| `assemble_context_packet()` | `context_assembly.py:94-200` | Traced: all injection paths for Thread B |
| `_redact_text()` | `context_assembly.py:393-397` | Traced: 8 inline patterns, covers every user-content path |
| `_build_text_entries()` | `context_assembly.py:359-363` | Traced: calls `_redact_text(value)` for each text entry |
| `_build_explicit_entries()` | `context_assembly.py:329-339` | Traced: reads file content via `_read_file_excerpt()` → `_redact_text()` |
| `_render_packet()` | `context_assembly.py:242-288` | Traced: redacts objective, constraints, criteria; does NOT redact `branch` |
| `build_consult_turn_text()` | `prompt_builder.py:40-47` | Read: thin wrapper, no posture consumption |
| `run_turn()` | `runtime.py:109-130` | Read: hard-codes `approvalPolicy`, `sandboxPolicy`; no `effort` |
| `start_thread()` | `runtime.py:76-93` | Read: hard-codes `approvalPolicy` |
| `ConsultRequest` | `models.py:32-48` | Read: no `profile` field |
| `AuditEvent` | `models.py:138-153` | Read: minimal schema, `extra` dict, comment about revisiting |
| `AdvisoryRuntimeState` | `models.py:111-125` | Read: no profile/effort fields |
| `TurnStartParams.json` (vendored) | `tests/fixtures/codex-app-server/0.117.0/v2/` | Read: `effort` field (not `reasoning_effort`), enum: none/minimal/low/medium/high/xhigh |
| Consultation profiles | `cross-model/references/consultation-profiles.yaml` | Read: 9 profiles, all sandbox=read-only, all approval_policy=never |
| Secret taxonomy | `cross-model/scripts/secret_taxonomy.py` | Read: 14 families, 3 tiers, placeholder bypass |
| Credential scanner | `cross-model/scripts/credential_scan.py` | Read: tiered scanning, fail-closed priority |
| Consultation safety | `cross-model/scripts/consultation_safety.py` | Read: policy-driven traversal, 10K node/256KB char caps |
| Learning retrieval | `cross-model/scripts/retrieve_learnings.py` | Read: parse/filter/format, fail-soft |

### Architecture: Consult Dispatch Path (Traced)

```
Claude calls codex.consult                ← HOOK BOUNDARY (PreToolUse)
  │  raw args: repo_root, objective, explicit_paths
  │
mcp_server.py:223 → ConsultRequest
  │
control_plane.py:130 → codex_consult(request)
  │
  ├── repo_identity = load_repo_identity()     ← ADDS: branch, HEAD
  ├── stale_marker = journal.load_stale_marker() ← ADDS: stale summary
  │
  └── assemble_context_packet()                ← ADDS: file content, entries
       │
       ├── _build_explicit_entries(paths) → _read_file_excerpt → _redact_text
       ├── _build_text_entries(summaries) → _redact_text
       ├── stale summary → _redact_text
       │
       └── _render_packet() → JSON with:
            objective (redacted), constraints (redacted),
            repo_identity (branch NOT redacted — gap),
            safety_envelope, capability_instructions
                 │
  prompt_builder.py:40 → build_consult_turn_text(payload)
                 │
  runtime.py:118 → run_turn(prompt_text=...)  ← TO CODEX
```

### Architecture: Advisory Runtime Policy

```
policy_fingerprint = sha256(sorted({
    "transport_mode": "stdio",
    "sandbox_level": "read_only",
    "network_access": "disabled",
    "approval_mode": "never",
    "app_connectors": "disabled",
}))[:16]

All 9 profiles produce the same fingerprint → no rotation needed.
effort is NOT in the fingerprint → changing effort is free.
posture/turn_budget are plugin-owned → not runtime policy.
```

### Architecture: Cross-Model Substrate Portability

| Module | Portability | Key adaptation |
|--------|------------|----------------|
| `secret_taxonomy.py` | Portable as-is | Zero internal deps |
| `credential_scan.py` | Portable | Remove conditional `if __package__` import |
| `consultation_safety.py` | Portable | Remap tool names to codex-collaboration MCP prefix |
| `consultation-profiles.yaml` | Portable verbatim | Profile definitions are domain-level |
| `retrieve_learnings.py` | Portable | Accept `repo_root` parameter instead of CWD |
| `emit_analytics.py` | Needs most adaptation | Different audit model (journal vs event_log) |

### Spec/Implementation Gap

`foundations.md:133`: "The hook guard validates the final packet produced by the control plane." But Claude Code's PreToolUse fires before the MCP tool executes — the hook sees raw tool args, not the assembled packet. The practical architecture (hook validates raw args, inner boundary sanitizes assembled content) is correct regardless of the spec's description.

## Context

### Mental Model

This session's arc was "architecture investigation before implementation." The T-03 ticket lists 8 acceptance criteria that look like independent module ports, but the real complexity is at the boundaries: where the safety substrate interacts with the existing runtime identity model (policy fingerprint, advisory caching) and where the hook boundary meets the packet assembly boundary.

The user's three-hypothesis checkpoint was the pivotal moment — it reframed the work from "port 5 modules" to "understand the runtime constraints that govern how those modules integrate." Thread A (runtime policy) eliminated the need for rotation protocol implementation. Thread B (safety boundary) revealed that the inner scan boundary already exists and only needs pattern upgrade.

The core insight: the safety substrate is not a set of independent modules. It's a system of two scan boundaries (outer: fail-closed on raw input; inner: sanitize assembled content) operating under a runtime policy model (advisory caching, policy fingerprint) that constrains how profiles and execution controls flow through the system.

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
| **T-02: Plugin shell** | **Merged to main** | `e67f97ff` |
| **T-03: Safety substrate** | **Planned, not started** | Branch: `feature/codex-collaboration-safety-substrate` |

239 tests passing. No code changes on the feature branch yet (only the plan is written).

### Supersession Roadmap

```
T-02 (plugin shell) ✓ → T-03 (substrate) → T-04 (dialogue) ──────→ T-07 (cutover)
                                           → T-05 (execution) → T-06 (promotion) → T-07
```

## Learnings

### All 9 consultation profiles share the same advisory runtime policy fingerprint

**Mechanism:** The policy fingerprint is computed from 5 material fields (transport, sandbox, network, approval, app connectors). All 9 profiles use `sandbox: read-only` and `approval_policy: never` — identical to the hard-coded values. `reasoning_effort` is not in the fingerprint. Therefore no profile triggers the freeze-and-rotate protocol.

**Evidence:** `build_policy_fingerprint()` at `control_plane.py:371-385` hashes the 5 fields. All 9 profile entries in `consultation-profiles.yaml` checked — every one has `sandbox: read-only`, `approval_policy: never`.

**Implication:** T-03 can add profiles without implementing rotation. The validation gate catches any future profile that would require rotation. When freeze-and-rotate is eventually needed, it will be because a new profile or explicit flag introduces a policy change.

### context_assembly._redact_text covers every user-content injection path

**Mechanism:** `_redact_text()` is called on: objective (`_render_packet:250`), explicit_snippets (`assemble_context_packet:125`), file excerpts (`_read_file_excerpt:390`), user_constraints (`_render_packet:259`), acceptance_criteria (`_render_packet:261`), and all text entries via `_build_text_entries:361`. The only unredacted fields are `repo_identity` (branch — gap; head — safe hex SHA) and generated constants.

**Evidence:** Full trace from `assemble_context_packet()` through `_render_packet()`, verified at each call site.

**Implication:** The inner scan boundary exists. T-03 Task 3 upgrades it from 8 inline patterns to the full 14-family taxonomy, but no new scan insertion point is needed in the control plane.

### The Codex App Server effort field is sticky per thread

**Mechanism:** `turn/start` accepts an `effort` field (wire name, not `reasoning_effort`). Once set, it persists to subsequent turns in the same thread. `thread/read` does not surface current effort/approval/sandbox settings.

**Evidence:** `TurnStartParams.json` includes `effort` with `ReasoningEffort` enum. `ThreadReadResponse.json` returns only `thread` without policy/effort fields. User confirmed from App Server investigation.

**Implication:** The plugin must resend `effort` on every `turn/start` for deterministic behavior. Cannot rely on reading back the current effort from the thread. The plugin is the authority for what effort level is active.

### foundations.md describes the hook guard inaccurately

**Mechanism:** `foundations.md:133` says the hook guard "validates the final packet produced by the control plane." But Claude Code's PreToolUse fires before the MCP tool executes. The hook sees raw MCP tool arguments, not the assembled packet.

**Evidence:** Execution flow at `foundations.md:161-163`: step 2 (hook) runs before step 3 (control plane). `_render_packet()` adds content that doesn't exist at hook time.

**Implication:** The plan implements the correct practical architecture (hook on raw args, inner scan on assembled content). The spec should be updated to match reality, but this is not blocking for T-03.

## Next Steps

### Execute the T-03 implementation plan

**Dependencies:** None — plan is written, branch is created.

**What to read first:** `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md`. The plan has 9 tasks with complete code for each step.

**Approach:** The user was presented with two options: subagent-driven (recommended) or inline execution. Choice not yet made. Subagent-driven dispatches a fresh agent per task with review between tasks. Inline executes in the current session with checkpoints.

**Potential obstacles:**
- Task 3 (inner redaction upgrade) may break existing `test_context_assembly.py` tests if they assert on the exact `[redacted]` placeholder text (old) vs `[REDACTED:value]` (new taxonomy template). The plan notes this.
- Task 7 (profiles) requires `pyyaml`. Need to verify it's available in the workspace.
- Task 5 (hook guard) runs as a subprocess — tests invoke it via `subprocess.run`. The `sys.path` manipulation in the script needs to work from the test's working directory.

### Thread C investigation before Task 10 (AC6 analytics)

**Dependencies:** Tasks 1-8 should be done first.

**What to investigate:** Which profile fields become first-class `AuditEvent` fields vs which go in `extra`? Does `contracts.md` have expansion rules for the audit schema? The answer determines the model change and journal query surface.

**Approach:** Read `contracts.md` AuditEvent section, check if there are audit schema versioning rules. Propose field additions. User checkpoint before implementation.

### Feature branch cleanup (inherited)

`feature/codex-collaboration-r2-dialogue` still exists on remote. Tagged at `r2-dialogue-branch-tip` → `d2d0df56`. Can be deleted anytime.

## In Progress

Clean stopping point. Implementation plan written and saved. Feature branch `feature/codex-collaboration-safety-substrate` created from `main` at `e67f97ff`. No code changes on the branch yet.

**User's next step:** Choose execution approach (subagent-driven vs inline), then begin Task 1.

## Open Questions

### Whether Task 7b's effort test can follow existing runtime test patterns

Task 7b Step 9 has an incomplete test body (`...`) because the test shape depends on how `runtime.py` is currently tested (fake client vs mock). The executing agent needs to read existing runtime test patterns and write the concrete test. Noted in the plan as the only placeholder.

### Thread C: Profile/audit schema expansion for AC6

Which profile fields are first-class `AuditEvent` fields vs `extra` dict entries? The `AuditEvent` comment says "should revisit AuditEvent shape before [new actions are] emitted." Need to decide before implementing analytics emission.

### Concurrent session identity race (inherited)

Two simultaneous Claude sessions sharing this plugin will race on `${CLAUDE_PLUGIN_DATA}/session_id`. Documented in T-02 carry-forward limitations. Not actionable until Claude Code provides per-session data directories.

## Risks

### Redaction template mismatch may break existing tests

The current `_redact_text()` uses `[redacted]` as the replacement text. The taxonomy uses `[REDACTED:value]` as the template. Task 3 changes this, which may break existing `test_context_assembly.py` assertions. The plan notes this but the implementing agent needs to check and update affected assertions.

### sys.path manipulation in codex_guard.py hook script

The hook adds the package root to `sys.path` for `from server.xxx import ...`. If the plugin cache directory structure differs from the dev repo, this may fail. Same risk as the bootstrap script (inherited from T-02).

### pyyaml availability for profile resolver

Task 7 uses `import yaml` for profile loading. Need to verify `pyyaml` is available in the workspace. If not, add it to `pyproject.toml` dependencies.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| T-03 implementation plan | `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` | Detailed plan with complete code |
| T-03 ticket | `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md` | 8 acceptance criteria |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Fixed-corpus benchmark for context-injection retirement |
| Advisory runtime policy | `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md` | Rotation protocol, fingerprint model |
| Cross-model scanner | `packages/plugins/cross-model/scripts/credential_scan.py` | Semantic source for Task 2 |
| Cross-model safety policy | `packages/plugins/cross-model/scripts/consultation_safety.py` | Semantic source for Task 4 |
| Cross-model profiles | `packages/plugins/cross-model/references/consultation-profiles.yaml` | Semantic source for Task 7 |
| Cross-model learnings retrieval | `packages/plugins/cross-model/scripts/retrieve_learnings.py` | Semantic source for Task 6 |
| Delivery spec | `docs/superpowers/specs/codex-collaboration/delivery.md` | Plugin component structure, `codex_guard.py` at line 44 |
| Prior handoff (resumed from) | `docs/handoffs/archive/2026-03-30_18-31_t02-plugin-shell-implemented-pending-review.md` | T-02 review context |

## Gotchas

### effort vs reasoning_effort naming

The profile YAML uses `reasoning_effort` (domain name). The Codex App Server `turn/start` field is `effort` (wire name). The plan's profile resolver maps between them. Do not use `reasoning_effort` in the `turn/start` payload.

### effort is sticky per Codex thread

Once set via `turn/start`, `effort` persists to subsequent turns in the same thread. `thread/read` does not expose current effort. The plugin must resend `effort` on every `turn/start` or risk inheriting a stale value from a prior turn.

### App Server ProfileV2 is a naming collision

App Server has native `ProfileV2` in `ConfigReadResponse.json` with `approval_policy`, `model`, `model_reasoning_effort`, etc. No `posture`, `turn_budget`, or `sandbox_mode`. No `profile` selector on thread/turn params. This is NOT the same as the plugin's consultation profiles — do not attempt to integrate.

### _redact_text template changes from [redacted] to [REDACTED:value]

The taxonomy's `redact_template` uses `[REDACTED:value]` (with capture group substitution for structured patterns). The current inline patterns use `[redacted]`. Tests asserting on the exact placeholder text will break when the inner boundary is upgraded.

### Hook PreToolUse sees raw args, not assembled packet

Despite `foundations.md:133` saying the hook "validates the final packet," Claude Code's PreToolUse fires before the MCP tool executes. The hook sees `{repo_root, objective, explicit_paths}`, not file contents, learnings, or summaries. Design the hook accordingly.

## Conversation Highlights

**On profile schema assumption:**
User challenged: "Verify your claim that the profile schema (sandbox, approval_policy, reasoning_effort, posture, turn_budget) is domain-level, not architecture-specific."
— Drove the investigation that corrected my assumption and reshaped Step 4/5.

**On Step 4 complexity:**
User: "Most likely: Step 4 is not just plumbing, it is a runtime-identity change. In control_plane.py the advisory runtime is cached only by `repo_root`, and `policy_fingerprint` is still hard-coded."
— The three-hypothesis checkpoint reshaped the entire plan.

**On safety boundary:**
User: "`fails closed` is still only true at the hook boundary. Upgrading `_redact_text()` makes the inner boundary stronger, but it still sanitizes and continues."
— Established the dual-boundary policy decision.

**On branch name gap:**
User: "`repo_identity` is not entirely 'non-user content.' `head` is harmless, but `branch` is user-controlled."
— Small but precise correction.

**On effort wire shape:**
User: "The important correction is wire shape: `turn/start` takes `effort`, not `reasoning_effort`."
— Prevented a wire protocol bug in the plan.

## User Preferences

**Evidence-level rigor (continued):** User holds all design decisions to defensible evidence standards. Challenged my profile schema claim with "verify your claim." Every correction comes with file:line references and specific reasoning.

**Spec alignment over convenience (continued):** User values spec alignment — corrected bootstrap location in prior session, corrected wire field name in this session.

**Three-hypothesis methodology (continued):** User structures investigations as ranked hypotheses with evidence needed and tests to run. Each hypothesis has a "most likely / next most likely / third" ranking. This drives investigation order and prevents wasted effort.

**Grounded pushback with constructive direction (continued):** User pushes back with evidence, then provides the corrected direction. The three-hypothesis checkpoint both identified problems and recommended investigation order.

**Scope awareness:** User explicitly deferred Thread C: "Step 5 (analytics/audit schema expansion) is in the T-03 scope. But the schema questions there don't change Steps 1-4. So I'd defer Thread C until Steps 1-4 are implemented." Prioritizes unblocking implementation over complete investigation.

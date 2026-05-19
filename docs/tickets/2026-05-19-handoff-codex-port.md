# Handoff plugin: one-time Codex → Claude Code port

```yaml
id: handoff-codex-port
date: 2026-05-19
status: open
priority: high
blocked_by: []
blocks: [handoff-port-commit-time-quality-gate]
related: []
plugin: packages/plugins/handoff/
```

## Goal

Replace the current Claude Code `handoff` plugin
(`packages/plugins/handoff/`, v1.6.0) with a Claude Code port of the newer
Codex `handoff` plugin
(`/Users/jp/Projects/active/codex-tool-dev/plugins/turbo-mode/handoff/`,
v1.7.0). The Codex version is a near-total rearchitecture (layered
`turbo_mode_handoff_runtime/` package, storage-authority layer, transactional
active-writes, chain-state recovery, O_EXCL lock model, ~30-file test suite)
and is a feature superset of the current Claude plugin.

This ticket is the authoritative spec. It was produced by an interactive
grilling drill + a Codex consult (collaboration `42c10159`, runtime
`1617b637`) on 2026-05-19. Decisions below are locked.

## Locked Decisions

1. **One-time port.** Drift from Codex upstream after the port is accepted.
   No shared-core / future-sync architecture.
2. **Strategy = host-retarget**, not verbatim adoption. Adopt the Codex
   rearchitecture wholesale; reject every Codex host-compensation (the Codex
   host is weaker; the Claude host is not).
3. **Identity model = A2: keep the resume-token model verbatim.** Do NOT
   reintroduce `${CLAUDE_SESSION_ID}`. `resume_token` is the architecture's
   spine (no session-identity seam) and Codex's model is host-agnostic
   (self-generates UUIDs at write time).
4. **Rename `turbo_mode_handoff_runtime` → `handoff_runtime`.** Atomic,
   test-guarded. (Concurred by Codex consult; clean repo namespace scan.)
5. **Storage topology: primary = `.claude/handoffs/`; legacy =
   `docs/handoffs/` (KEPT).** Codex ships `primary=.codex/handoffs`,
   `legacy=docs/handoffs` — so the change is essentially the single token
   `.codex`→`.claude` in `storage_layout.py`; the `legacy=docs/handoffs/`
   line is already correct and is the migration bridge.
6. **Cutover = M1 one-shot hard move.** Move all 159 live files
   (5 active→active, 154 archive→archive) from `docs/handoffs/` →
   `.claude/handoffs/`; absorb the 1 stale `.claude/handoffs/.archive/`
   residue file. **Add `.claude/handoffs/` to `.gitignore`** — the ported
   plugin is gitignore-neutral and will not; handoffs stay local-only
   ephemeral (parity with current `docs/handoffs/` gitignore at `.gitignore:22`).
7. **Quality enforcement = Option A (restore parity).** Re-wire both hooks,
   retargeted to the Claude host: `SessionStart → cleanup` and
   `PostToolUse:Write → quality_check`. The hard commit-time gate (Option B)
   is deferred to `handoff-port-commit-time-quality-gate`.

## Execution Order

1. (this ticket) — authoritative spec.
2. **Gate 1 — storage topology (highest-risk, do FIRST):**
   `storage_layout.py` `.codex`→`.claude`; retarget every storage-authority
   consumer + `test_storage_layout.py` + release-metadata tests +
   `references/ARCHITECTURE.md`, atomically. Legacy stays `docs/handoffs/`.
3. **Atomic rename** `turbo_mode_handoff_runtime` → `handoff_runtime`:
   directory, all internal imports, 8 script facades, ~30 test files,
   `test_runtime_namespace.py` (enforces the namespace + base-layer
   no-internal-import invariant — must move in lockstep),
   `installed_host_harness`, `storage_authority_inventory`, docs. Finish with
   `rg turbo_mode_handoff_runtime` and `rg Future-Codex` sweeps → expect zero.
4. **Manifest + branding retarget:** `.codex-plugin/plugin.json` →
   `.claude-plugin/plugin.json` schema; drop the Codex `interface` block; fix
   codex-tool-dev URLs; strip `Future-Codex:` comments and Codex-named
   artifacts; `pyproject` description → Claude Code.
5. **Hooks (Option A):** re-wire `SessionStart→cleanup` +
   `PostToolUse:Write→quality_check` in `hooks/hooks.json` using
   `${CLAUDE_PLUGIN_ROOT}`, the renamed `handoff_runtime` entrypoints, and
   `.claude/handoffs/`. `quality_check` path-recognition must be retargeted to
   the staging `$CONTENT_FILE` path the save/quicksave/summary skills write
   (Codex flow stages content, then the runtime commits — Claude never Writes
   the final path).
6. **M1 migration:** move the 159 files, absorb the `.archive/` residue, add
   the `.gitignore` line.
7. **Verification gate (before live swap):** rehearse on a *disposable copy*
   of the 159-file corpus — list / load explicit-active / load-latest / save /
   summary / search / triage / state-cleanup. Assert: no active file
   classified as legacy-policy-conflict; no `.codex/handoffs/` durable tree
   appears; state files under `.claude/handoffs/.session-state/` are tokenized
   JSON.

## Acceptance Criteria

1. `packages/plugins/handoff/` contents replaced; `.claude-plugin/marketplace.json`
   entry unchanged (`{"name":"handoff","source":"./packages/plugins/handoff"}`).
2. No `turbo_mode_handoff_runtime`, `.codex/handoffs/`, `.codex-plugin`, or
   `Future-Codex` strings remain (`rg` sweep clean).
3. `storage_layout` primary = `.claude/handoffs/`, legacy = `docs/handoffs/`;
   all 159 migrated files classify as primary (Codex verified frontmatter
   compatible: 159 files, 0 missing `project/created_at/session_id/type`).
4. resume-token identity model unchanged from Codex (no `${CLAUDE_SESSION_ID}`).
5. Both Option-A hooks fire correctly on the Claude host (SessionStart prunes
   24h state; PostToolUse advisory quality feedback on the staged content).
6. `.claude/handoffs/` added to `.gitignore`; handoffs remain untracked.
7. Ported test suite passes after lockstep retargeting of Codex-host-shaped
   tests (`test_storage_layout`, release-metadata, `installed_host_harness`,
   `storage_authority_inventory`, `test_runtime_namespace`).
8. Verification-gate rehearsal passes on a disposable corpus copy before the
   live swap.

## Remaining Risks / Open Uncertainties

- `${CLAUDE_PLUGIN_ROOT}` installed-plugin-cache behavior inferred from the
  current Claude plugin, not re-proven in an installed cache.
- Rename can leak via stale strings in `installed_host_harness` /
  `storage_authority_inventory` / fixtures / docs — mechanical risk.
- Skill prose diverged 256–275 lines per core skill (Codex-host rebinding):
  accepted under one-time port, but a post-port `/save` `/load` behavior
  parity spot-check is prudent.
- M1 is reversible (file move), but the cutover touches 159 durable in-use
  files — the verification-gate rehearsal is the safety net, not optional.

## Provenance

Grilling drill + Codex consult `42c10159-cffc-44b3-9e63-1068cc632eb9`
(2026-05-19). Codex inspected both repos and corrected the storage-topology
framing (the decisive finding: `docs/handoffs/` is structurally classified
*legacy* in Codex's frozen `StorageLayout` dataclass — a path-string replace
would block all 159 files).

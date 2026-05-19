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
active-writes, chain-state recovery, O_EXCL lock model, ~29-file test suite)
and is a feature superset of the current Claude plugin **for the
rearchitecture**, but only a partial overlap of *behavior*: it ships an empty
`hooks.json` and a Codex-host identity model, so wired hooks (Decision 7) and
host-native session identity (Decision 3) are re-added on the Claude side, not
inherited.

## Decision Status

This ticket was produced by an interactive grilling drill + a Codex consult
(collaboration `42c10159`, runtime `1617b637`) on 2026-05-19, then **revised
2026-05-19 after a `/scrutinize` + `/grill-me` pass** that found a contradiction
inside the original locked decision set and several false-precision claims.
Decisions 1, 2, 4, 7 are unchanged from the original lock. **Decision 3 was
re-opened and amended** (the original "do NOT reintroduce `${CLAUDE_SESSION_ID}`"
framing conflated two separate identifiers and contradicted Decision 2 — see
Provenance). Decisions 5 and 6 had their framing tightened (no behavior change).
A **second 2026-05-19 revision** (post cross-model verification loop) hardened
acceptance instruments only: the prior AC2 `.codex/handoffs/` straggler token
was blind to the split-token constructor forms, so AC2 became a strict-zero
bare-`.codex` atom sweep, Execution steps 2 and 5 were rescoped to the true
footprint, and Decision 3's unverified "7 sites" figure was replaced with a
measured count. No locked decision changed. Treat the decisions below as the
current authority; the Provenance section records what changed and why.

## Locked Decisions

1. **One-time port.** Drift from Codex upstream after the port is accepted.
   No shared-core / future-sync architecture. (Note: Codex upstream already has
   an `[Unreleased]` delta on top of 1.7.0 — the fork point is mid-churn; this
   is accepted under the one-time-port decision.)
2. **Strategy = host-retarget**, not verbatim adoption. Adopt the Codex
   rearchitecture wholesale; reject every Codex host-compensation (the Codex
   host is weaker; the Claude host is not).
3. **Identity model = A2-split.** Two *separate* identifiers, decided
   independently:
   - **`resume_token` — kept verbatim from Codex.** It names
     `.session-state/handoff-<project>-<resume_token>.json`
     (`chain_state.py`, `session_state.py`) and is the genuinely host-agnostic
     resume spine. No `${CLAUDE_SESSION_ID}` seam is introduced here.
   - **`session_id` frontmatter field — restore `${CLAUDE_SESSION_ID}`.** In
     Codex this is a write-time UUID *only because Codex has no host session ID*
     — a textbook host-compensation, which Decision 2 says to reject. The Claude
     host provides `${CLAUDE_SESSION_ID}`; the current 1.6.0 plugin already uses
     it (`references/handoff-contract.md`: "Required: from `${CLAUDE_SESSION_ID}`" — measured: 3 literal
     `${CLAUDE_SESSION_ID}` sites (lines 7/9/22) plus 3 session-id-derived
     state-file paths (lines 44/47/49); the original "7 sites" was an
     unverified figure). Restoring it introduces **zero** session-identity seam into the
     resume mechanism because `resume_token ≠ session_id`, keeps continuity with
     the existing corpus (every existing handoff already carries a real-session
     `session_id`), and upgrades `uid_match` handoff↔ticket provenance
     (`provenance.py`, `skill-details.md`) from Codex's copied-token model to
     true session-scoped correlation.
4. **Rename `turbo_mode_handoff_runtime` → `handoff_runtime`.** Atomic,
   test-guarded. (Concurred by Codex consult; clean repo namespace scan.)
5. **Storage topology: primary = `.claude/handoffs/`; legacy =
   `docs/handoffs/` (KEPT).** Codex ships `primary=.codex/handoffs`,
   `legacy=docs/handoffs` in the frozen `StorageLayout` dataclass. The literal
   edit in `storage_layout.py` is `.codex`→`.claude` on the
   `primary = root / ".codex" / "handoffs"` line — but this is **not** a
   one-token change in scope: the bare `.codex` atom appears in **42 files**
   (runtime modules, tests, skills, reference docs) and all retarget atomically
   (Execution step 2; AC2's strict-zero atom sweep is the completion gate, not
   a named consumer list). `storage_layout.py` itself builds the path from
   split tokens (`root / ".codex" / "handoffs"`), so a rendered-path grep
   cannot see it — it is verified by symbol/behavior (AC3), not by sweep. Because
   M1 (Decision 6) hard-moves every file out of `docs/handoffs/` in the same
   port, the `legacy=docs/handoffs/` path is **vestigial post-cutover** (serves
   zero files); it is retained only as a defensive straggler classifier, NOT as
   an active migration bridge. Do not describe this as "essentially a single
   token" — that wording under-scopes Execution step 2.
6. **Cutover = M1 one-shot hard move (count-invariant, not count-fixed).**
   Move *every* `.md` under `docs/handoffs/` to `.claude/handoffs/`, preserving
   structure (active top-level → `.claude/handoffs/`; `docs/handoffs/archive/`
   → `.claude/handoffs/archive/`). The corpus grows every session — the
   port-planning session itself added one active file (5→6) — so the move is
   specified as an **invariant**, not a frozen integer (see AC #3). **Promote
   the 1 pre-1.6.0 residue** (`.claude/handoffs/.archive/2026-03-29_21-30_checkpoint-handoff-project-local-storage.md`,
   a frontmatter-complete `checkpoint`) into `.claude/handoffs/archive/` as a
   normal archived handoff; post-migration `.claude/handoffs/.archive/` must
   contain **zero** `.md` files. **Exclude `.DS_Store`** from the move (present
   in all four handoff dirs; a naive move sweeps them). **Add
   `.claude/handoffs/` to `.gitignore`** — the ported plugin is gitignore-neutral
   (confirmed: Codex CHANGELOG 1.7.0 "does not add gitignore rules"); handoffs
   stay local-only ephemeral (parity with current `docs/handoffs/` gitignore at
   `.gitignore:22`).
7. **Quality enforcement = Option A (restore parity).** Re-wire both hooks,
   retargeted to the Claude host: `SessionStart → cleanup` and
   `PostToolUse:Write → quality_check`. The hard commit-time gate (Option B)
   is deferred to `handoff-port-commit-time-quality-gate`. (Codex ships
   `hooks.json` = `{"hooks": {}}` — these hooks are reconstructed on the Claude
   side, not ported.)

## Execution Order

1. (this ticket) — authoritative spec.
2. **Storage topology (highest-risk, do FIRST):** edit `storage_layout.py:24`
   `root / ".codex" / "handoffs"` → `.claude`, then retarget the **entire
   bare-`.codex` footprint (42 files: runtime, tests, skills, reference docs)**
   atomically — scope is the atom, not a named consumer list; AC2's strict-zero
   `rg '\.codex' packages/plugins/handoff` sweep is the completion gate. Two
   sites build paths from split string tokens that a rendered-path grep cannot
   prove retargeted: `storage_layout.py` (verify via AC3 symbol assertion) and
   `quality_check.is_handoff_path:353` (`parts[i] == ".codex"`; verify via AC5
   behavior). Legacy stays `docs/handoffs/` (vestigial straggler classifier per
   Decision 5).
3. **Atomic rename** `turbo_mode_handoff_runtime` → `handoff_runtime`:
   directory, all internal imports, 8 script facades, ~29 test files,
   `test_runtime_namespace.py` (enforces the namespace + base-layer
   no-internal-import invariant — must move in lockstep),
   `installed_host_harness`, `storage_authority_inventory`, docs. Finish with
   `rg turbo_mode_handoff_runtime` and `rg Future-Codex` sweeps → expect zero.
4. **Manifest + branding retarget:** `.codex-plugin/plugin.json` →
   `.claude-plugin/plugin.json` schema; drop the Codex `interface` block; fix
   codex-tool-dev URLs; strip `Future-Codex:` comments and Codex-named
   artifacts; `pyproject` description → Claude Code. **Decision-3 consequence:**
   reverse the Codex identity-model wording back to `${CLAUDE_SESSION_ID}`
   injection — `references/handoff-contract.md` Session-IDs section
   ("generated at write time" → "from `${CLAUDE_SESSION_ID}`"),
   `skills/save/SKILL.md` step "Generate a fresh UUID for `session_id`", and the
   equivalent quicksave/summary/load skill lines. `resume_token` wording stays
   exactly as Codex ships it.
5. **Hooks (Option A):** re-wire `SessionStart→cleanup` +
   `PostToolUse:Write→quality_check` in `hooks/hooks.json` using
   `${CLAUDE_PLUGIN_ROOT}`, the renamed `handoff_runtime` entrypoints, and
   `.claude/handoffs/`. `quality_check` path-recognition must be retargeted to
   the staging `$CONTENT_FILE` path the save/quicksave/summary skills write
   (Codex flow stages content, then `active_writes.write_active_handoff` commits
   it — Claude never Writes the final path). This is **two** edits in
   `quality_check.py`, not one: (a) the staging-path recognition above, and
   (b) the hard-coded `.codex` token in `is_handoff_path:353`
   (`parts[i] == ".codex" and parts[i + 1] == "handoffs"`) plus its docstring —
   a `.codex/handoffs/`→`.claude/handoffs/` find-replace fixes only the
   docstring and silently leaves the part-check logic broken (it never contains
   the joined substring).
6. **M1 migration (manifest-guarded):**
   a. **Pre-move manifest:** capture a sorted list + `sha256` of every `.md`
      under `docs/handoffs/` and the 1 `.claude/handoffs/.archive/` residue →
      `M1-premove-manifest.txt` (kept until post-cutover verification passes).
   b. Move every `.md` preserving active/archive structure; promote the residue
      into `.claude/handoffs/archive/`; exclude `.DS_Store`.
   c. Add the `.gitignore` line.
   d. **Scripted reverse-move** (`M1-rollback`) exists and is dry-run-tested
      *before* step b runs: it restores every path from the manifest to
      `docs/handoffs/` and removes the `.gitignore` line. "M1 reversible" is a
      tested claim, not an assertion.
7. **Verification gate (before live swap):** rehearse on a *disposable copy*
   of the corpus — list / load explicit-active / load-latest / save / summary /
   search / triage / state-cleanup. Assert:
   - manifest reconciliation: every pre-move path is present exactly once at
     its mapped destination; `sha256` unchanged; count delta == 0 (no loss, no
     dup);
   - no active file classified as legacy-policy-conflict;
   - no `.codex/handoffs/` durable tree appears;
   - `.claude/handoffs/.archive/` contains zero `.md` (residue promoted);
   - after a rehearsal `/save` on the disposable copy, a tokenized
     `handoff-<project>-<resume_token>.json` appears under
     `.claude/handoffs/.session-state/` (proves *new* state regenerates at the
     new path — the runtime regenerates state; pre-existing state is not
     migrated, by design — see Remaining Risks).

## Acceptance Criteria

(AC ↔ Execution-step map: AC1→step2/AC-wide, AC2→steps 2-5 (+ AC3/AC5
symbol-behavior cross-check for split-token sites), AC3→steps 2/6,
AC4→Decision 3 invariant + step 4, AC5→step 5, AC6→step 6c, AC7→steps 3/6,
AC8→step 7, AC9→step 6/7. AC4 is an invariant verified by inspection, not a
discrete build step.)

1. `packages/plugins/handoff/` contents replaced; `.claude-plugin/marketplace.json`
   entry unchanged (verified exactly: `{ "name": "handoff", "source": "./packages/plugins/handoff" }`).
2. **Codex-atom sweep, strict-zero.** `rg '\.codex' packages/plugins/handoff`
   returns **zero** matches — no exceptions (Decision 1 clean-drift). Plugin-
   scoped by design: a repo-wide `.codex` sweep would false-trip on unrelated
   `codex-collaboration` references that legitimately live elsewhere in this
   repo. The bare atom supersedes the prior `.codex/handoffs/` and
   `.codex-plugin` tokens and, unlike a rendered-path token, catches the
   split-token constructor forms `storage_layout.py:24`
   `root / ".codex" / "handoffs"` and `is_handoff_path:353`
   `parts[i] == ".codex"` that a `.codex/handoffs/` grep cannot see (verified:
   atom matches both; the old token saw only 22 of 42 files). Plus
   `rg 'turbo_mode_handoff_runtime'` and `rg 'Future-Codex'` zero (the atom
   does **not** match these — they remain separate tokens). Plus a repo-wide
   `rg 'docs/handoffs'` external-consumer survey: every hit outside the plugin
   (sibling-plugin ARCHITECTURE docs, memory pointers, scripts, other skills)
   is remediated to `.claude/handoffs/` or explicitly recorded as intentionally
   legacy-pointing. **Grep-insufficient sites — verify by symbol/behavior, NOT
   grep:** `storage_layout` (AC3) and `is_handoff_path` (AC5) build paths from
   split tokens; a passing sweep does not prove them retargeted.
3. `storage_layout` primary = `.claude/handoffs/`, legacy = `docs/handoffs/`;
   **invariant (not a fixed count):** every `.md` present under `docs/handoffs/`
   at cutover time classifies as primary after the move; zero migrated files
   are missing required frontmatter (`project`/`created_at`/`session_id`/`type`);
   archive destination = (all non-top-level `.md`) + (the 1 promoted residue).
   (Codex spot-verified frontmatter compatibility on the corpus snapshot; the
   AC is the invariant, not the snapshot integer.)
4. `resume_token` identity model byte-unchanged from Codex; `session_id`
   frontmatter field sourced from `${CLAUDE_SESSION_ID}` on the Claude host
   (no write-time-UUID fallback in the Claude skills).
5. Both Option-A hooks fire correctly on the Claude host (SessionStart prunes
   24h state; PostToolUse advisory quality feedback on the staged content).
   **`is_handoff_path` retarget verified by behavior** (grep-insufficient
   split-token site): the rewired recognizer accepts the Claude staging path
   and rejects a `.codex`-shaped path — asserted by test, not by sweep.
6. `.claude/handoffs/` added to `.gitignore`; handoffs remain untracked;
   `.DS_Store` files were not swept into `.claude/handoffs/`.
7. Ported test suite passes after lockstep retargeting of Codex-host-shaped
   tests (`test_storage_layout`, release-metadata, `installed_host_harness`,
   `storage_authority_inventory`, `test_runtime_namespace`).
8. Verification-gate rehearsal (step 7, including manifest reconciliation and
   new-state regeneration) passes on a disposable corpus copy before the live
   swap; `M1-rollback` dry-run verified.

## Remaining Risks / Open Uncertainties

- `${CLAUDE_PLUGIN_ROOT}` installed-plugin-cache behavior inferred from the
  current Claude plugin, not re-proven in an installed cache.
- Rename can leak via stale strings in `installed_host_harness` /
  `storage_authority_inventory` / fixtures / docs — mechanical risk.
- Skill prose diverged 256–275 lines per core skill (Codex-host rebinding):
  accepted under one-time port, but a post-port `/save` `/load` behavior
  parity spot-check is prudent.
- **Cutover-timing auto-resume miss (accepted, recoverable):** session state
  is ephemeral by design (24h TTL, `cleanup.py:34`, self-gitignored; the live
  `.session-state/` currently holds zero `.json`). If a `/save` creates resume
  state and the cutover happens within 24h before a `/load`, auto-resume is
  skipped because state was written under the old path while the runtime reads
  the new one. The handoff file itself still migrates and is `/load`-able, so
  the worst case is "no auto-resume," not data loss. Documented, not gated.
- M1 is reversible (manifest-guarded scripted reverse-move, dry-run-tested per
  step 6d), but the cutover touches the full live corpus — the verification
  gate + manifest reconciliation is the safety net, not optional.

## Provenance

Grilling drill + Codex consult `42c10159-cffc-44b3-9e63-1068cc632eb9`
(2026-05-19). Codex inspected both repos and corrected the storage-topology
framing (the decisive finding: `docs/handoffs/` is structurally classified
*legacy* in Codex's frozen `StorageLayout` dataclass — a path-string replace
would block all migrated files).

**2026-05-19 revision (post `/scrutinize` + `/grill-me`):**

- **Decision 3 amended (was a locked contradiction).** Original Decision 3
  said keep the resume-token model verbatim *and* "do NOT reintroduce
  `${CLAUDE_SESSION_ID}`." Inspection showed `resume_token` and the `session_id`
  frontmatter field are **separate** identifiers in the Codex runtime
  (`chain_state.py:217` / `session_state.py:109` vs `provenance.py:82` /
  `handoff-contract.md:7-12`). The self-generated-UUID `session_id` is a Codex
  host-compensation, which Decision 2 explicitly says to reject — so the
  original framing contradicted Decision 2. Resolution: split the decision —
  resume_token verbatim, `${CLAUDE_SESSION_ID}` restored for `session_id`.
- **High #4 reconciled.** `docs/handoffs/.session-state/` verified to hold zero
  durable state (24h-TTL ephemeral). State-dir migration dropped; Step 7
  rewritten to verify *new* state regeneration; timing miss documented as an
  accepted recoverable risk.
- **High #5 resolved.** `previous_primary_hidden_archive_dir` verified to be a
  live, scanned, copy-registry-triggering path (`storage_authority.py:45/110/450/459`),
  not vestigial. "Absorb the residue" defined as promote-into-archive with a
  testable zero-`.md` assertion.
- **Count finding folded.** Frozen integers (159/5/154) replaced by a
  cutover-time invariant; the corpus grows every session.
- **Manifest/rollback (#6), external-consumer survey (#7), Decision-5 framing
  (#8), AC↔step map (#9)** folded into Execution / AC above.
- **Critical #2 (ticket 2's chokepoint) verified true**, not unimplementable:
  the chokepoint is `active_writes.py:564 write_active_handoff`; see the revised
  `handoff-port-commit-time-quality-gate`.

**2026-05-19 second revision (cross-model verification loop):**

- **AC2 sweep-token blind spot (the decisive finding).** A `/scrutinize` pass
  plus an independent cross-model verification re-measured the footprint: bare
  `.codex` = **42 files**; the prior AC2 token `.codex/handoffs/` matched only
  **22**. The 22-file token is structurally blind to the split-token
  constructor forms — `storage_layout.py:24` `root / ".codex" / "handoffs"`
  and `is_handoff_path:353` `parts[i] == ".codex"` — because a Python `/`-join
  and a tuple-part comparison never materialize the `.codex/handoffs`
  substring. AC2 rewritten to a strict-zero, plugin-scoped bare-`.codex` atom
  sweep; Execution steps 2 and 5 rescoped to the atom footprint; the two
  grep-insufficient sites routed to symbol/behavior verification (AC3 / AC5).
- **Count corrections.** A first reviewer's "43 files / ~35 `.codex/handoffs`"
  and a downstream "session_state.py 19" were artifacts of a 3-way compound
  regex mislabeled as a literal-path count; ground truth is 42 / 22 / 5.
  Decision 3's unverified "7 sites" replaced with the measured 3+3 breakdown.
- **No decision changed.** Locked Decisions 1–7 remain the 2026-05-19
  authority; this revision hardened acceptance instruments and execution
  scope only.

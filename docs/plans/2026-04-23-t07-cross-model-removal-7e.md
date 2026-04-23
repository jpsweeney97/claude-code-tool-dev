# T-07 Slice 7e: Cross-Model Removal Plan

## Overview

| Attribute | Value |
|-----------|-------|
| Slice | 7e |
| Branch | `feature/t07-cross-model-removal-7e` |
| Dependency | 7d merged (PR #122 at `1f458bcf`) |
| AC addressed | "Cross-model is removed from the repo once the parity matrix is complete and the live `/delegate` smoke has passed (or an explicit App Server deferral is recorded)" |
| Authority | T-07 ticket, 7c parity matrix, T-04 retirement decision |
| Type | Deletion + reference cleanup + marketplace cutover |

## Pre-Removal Gates

| Gate | Status | Evidence |
|------|--------|----------|
| Parity matrix verified (7c) | **Done** | PR #120, `c59dbf11` |
| Context-injection removed (7d) | **Done** | PR #122, `1f458bcf` |
| Live `/delegate` smoke | **Deferred** | See §Delegate Smoke Deferral |

### Delegate Smoke Deferral

Live `/delegate` smoke was attempted on 2026-04-22. App Server bootstrapped
and the codex-collaboration delegation pipeline ran successfully through
start → escalation → decide → completion → poll → inspection. The job
reached `completed` with `promotion_state: "pending"` and a materialized
`artifact_hash`.

However, the sandbox produced no artifacts (empty diff, zero changed files).
Root cause is two codex-collaboration execution-domain defects:

1. **Sandbox too restrictive for shell execution.**
   `build_workspace_write_sandbox_policy()` in `runtime.py:23` sets
   `includePlatformDefaults: False` with `readableRoots` limited to only
   the worktree. The sandbox cannot read platform binaries (`/bin/zsh`,
   `/usr/bin/env`, etc.), causing all shell commands to fail with exit
   code -1.

2. **Approve path does not grant the original App Server request.**
   For `command_approval` and `file_change` requests, the
   `_server_request_handler` (line 718) returns `{"decision": "cancel"}`
   immediately. Later `decide(approve)` starts a new turn with a prompt
   saying "treat as approved," but the new turn hits the same sandbox
   restriction and re-escalates.

**What was proved:** App Server availability, authentication, delegation
pipeline infrastructure (start/escalate/decide/complete/poll/inspect),
artifact materialization, artifact hash computation.

**What was not proved:** Sandbox shell execution, approval granting
operations, promotable non-empty diff, end-to-end file production.

**Transparency:** This is an execution-domain defect in
codex-collaboration, not an App Server availability gap. Both defects
are codex-collaboration-specific. Tracked for independent remediation
outside 7e scope.

**Smoke evidence:**
- Job ID: `23347703-673a-419f-b1f5-01ca16cfe1f6`
- Runtime ID: `b1ca3b27-3c35-4535-bc4f-033cac1b5753`
- Base commit: `1f458bcf948a3c99c0c68db0ce98b5e2a0cfd98e`
- Disposition: Discarded (empty diff)

**Precedent:** T-06 deferred the same smoke with App Server unavailability
as the reason. This deferral is more specific: App Server is available but
execution is blocked by sandbox/approval defects.

## Post-7e State

After 7e, the cross-model plugin is fully removed from the repo. All five
cross-model workflows have codex-collaboration replacements (verified by
7c parity matrix and 7e live parity check). Remaining cross-model
references fall into an explicit residual allowlist (see §Residual
Reference Policy).

## Scope

Remove `packages/plugins/cross-model/` and all live operational references.
Add `codex-collaboration` to the marketplace in the same change.

**Explicitly not 7e scope:**
- Fixing the delegation sandbox/approval defects (independent remediation)
- Editing historical docs that mention cross-model (evidence preservation)
- Writing README/HANDBOOK/CHANGELOG for codex-collaboration (follow-up)
- Removing the codex-collaboration skills' "Do NOT use cross-model" guards
  (those become inert but harmless after removal)

## Decisions

### D1: Delete validator and sync tests, don't add skip logic

**Choice:** Delete `scripts/validate_consultation_contract.py`,
`tests/test_consultation_contract_sync.py`, and
`tests/test_e_planning_spec_sync.py` entirely.

**Driver:** These files validate the cross-model consultation contract
against cross-model surfaces (skills, agents, scripts, profiles). Once the
package is gone, they have no subject. Adding `[RETIRED]` skip logic (as
done in 7d for the agent) would create infrastructure without a purpose.

**Alternatives considered:**
- **Port to validate codex-collaboration contracts** — rejected because
  codex-collaboration uses server-enforced contracts, not Claude-cognitive
  documents. Different validation model entirely.
- **Add skip logic** — rejected because the 7d skip was justified by a
  one-slice liminal state. In 7e, the subject is deleted.

**Trade-offs accepted:** The repo loses its consultation contract
validation tooling. This is accepted because the consultation contract
itself is being deleted with the package.

**Confidence:** High (E2) — all three files reference cross-model paths
exclusively.

**Reversibility:** High — git history preserves all code.

### D2: Add codex-collaboration to marketplace in the same change

**Choice:** Replace the cross-model entry in
`.claude-plugin/marketplace.json` with a codex-collaboration entry.

**Driver:** Removing cross-model without adding codex-collaboration would
leave the turbo-mode marketplace without a Codex integration install path.
codex-collaboration has been delivered and tested through T-02/T-03/T-04/
T-06/T-07, and the marketplace entry is one line.

**Alternatives considered:**
- **Remove only, add later** — rejected because it creates an avoidable
  installability gap.

**Trade-offs accepted:** Couples marketplace promotion with package
removal. Accepted because 7e is explicitly the cutover slice.

**Confidence:** High (E2) — codex-collaboration's `.claude-plugin/`
directory exists and follows the same plugin structure.

**Reversibility:** High — one-line JSON change.

### D3: Residual Reference Policy — exhaustive scan + explicit allowlist

**Choice:** Run a case-insensitive repo-wide scan for `cross.model` and
`cross_model` after all changes. Every hit is classified as delete, update,
or allowlist. No unclassified residue.

**Operational (delete or update):**
- Python imports, workspace config, CI, marketplace, validation scripts,
  repo-level tests, live skill/agent/hook references, `.claude/CLAUDE.md`

**Allowlisted (retained as-is with justification):**

| Surface | Justification |
|---------|---------------|
| `docs/tickets/`, `docs/plans/`, `docs/reviews/`, `docs/benchmarks/`, `docs/decisions/`, `docs/audits/`, `docs/learnings/` | Historical evidence — describe past state accurately |
| `.planning/codebase/*.md` (7 files, ~40 references) | Generated codebase inventory — stale but tracked; regenerating is out of scope for a removal slice |
| `packages/plugins/codex-collaboration/server/secret_taxonomy.py:3` | Attribution comment ("Ported from cross-model") — provenance, not operational |
| `packages/plugins/codex-collaboration/skills/codex-review/SKILL.md:8,27` | "Do NOT use cross-model MCP tools" guard — becomes inert but harmless |
| `packages/plugins/codex-collaboration/skills/consult-codex/SKILL.md:19` | "Do NOT port cross-model consultation features" guard — inert |
| `packages/plugins/codex-collaboration/skills/delegate/SKILL.md:24` | "Do NOT port cross-model delegation features" guard — inert |
| `packages/plugins/handoff/skills/defer/SKILL.md:38` | "Codex unresolved items from cross-model consultations" — historical signal pattern, not a path or import |
| `tests/test_validate_episode.py:62` | Test fixture keyword `[cross-model, architecture]` in YAML frontmatter — metadata tag, not a path |
| `docs/superpowers/**` | Spec evidence — design docs and skill-composability spec referencing cross-model paths as historical design context |
| `docs/prompts/cross-model-*.md` (2 files) | Historical prompt artifacts — generated prompts for cross-model analysis, not operational references |
| `docs/archived/` | Archived subsystem documentation (e.g., CCDI) — historical |
| `docs/handoffs/archive/` | Archived session handoffs — immutable snapshots |

**Driver:** Category-based exclusion ("docs/ is historical") misses
tracked live surfaces (`.planning/`, plugin-local skills, test fixtures).
An exhaustive scan + allowlist is the only inventory boundary that matches
the removal claim.

**Confidence:** High (E2) — every item above verified by repo grep.

### D4: Update CLAUDE.md — package table and scripts table

**Choice:** Remove the cross-model and context-injection rows from the
Packages table in `.claude/CLAUDE.md` (lines 43-44). Also remove the
`validate_consultation_contract.py` row from the Scripts table (line 93).

**Driver:** The Packages table lists packages in this repo; cross-model
will no longer exist. The Scripts table lists runnable scripts; the
validator is being deleted (D1). Leaving the row would direct agents to
run a nonexistent script.

### D5: Update live skill references to exact codex-collaboration names

**Choice:** Update three files that reference cross-model MCP tool names
or slash commands. Exact replacement names lifted from the delivered
codex-collaboration surfaces.

#### D5a: Codex Delta migration — rewrite to one-shot `codex.consult`

The old Codex Delta protocol (`codex-delta.md`) is a two-phase,
single-consultation flow using `codex-dialogue`'s thread continuation
(`codex`/`codex-reply`). In codex-collaboration, `codex.consult` is
one-shot (`consult-codex/SKILL.md:11`), and the dialogue orchestrator
(`/codex-collaboration:dialogue`) is too heavyweight for an adversarial
check (spawns gatherer agents, has bounded scouting phases).

**Migration mode:** Rewrite Codex Delta to use a single `codex.consult`
call. Merge Phase 1 and Phase 2 questions into one structured prompt.
Bias mitigation is preserved by structuring the prompt so that neutral
option descriptions and failure-mode questions appear before the
frontrunner reveal and adversarial questions — within the same message.

**What changes in `codex-delta.md`:**
- "Two-Phase Reveal" section → single prompt with structured sections
- "Subagent Invocation" (line 92-102) → `codex.consult` invocation
  with `profile="adversarial-challenge"` and the merged prompt
- "Availability Detection" (lines 182-184) → check for
  `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult`
- "Troubleshooting" (lines 201-204) → same tool name update
- Remove all `codex-reply` / `codex-dialogue` / thread continuation
  references
- "Call Budget" (lines 158-161) → second call uses a second
  `codex.consult`, not a second subagent turn
- Header and design-origin line → update to codex-collaboration

**What does NOT change:** Invocation Gate, Stable-Frontrunner Gate,
Stakes Policy, Output format (Codex Delta block), Status Tags,
Convergence Rule, Fallback Behavior (local lenses), Anti-Patterns,
Call Budget cap (still 2).

**Trade-offs accepted:** The two-phase reveal loses its separate-message
bias-mitigation property. The single-prompt structure mitigates this
structurally (options first, frontrunner after) but it is weaker than
sequential reveal with an independent response in between.

#### D5b: Exact replacement names for other references

| File | Old reference | Exact replacement | Source |
|------|-------------|-------------------|--------|
| `.claude/skills/making-recommendations/SKILL.md` (lines 137-143) | "cross-model adversarial check" | "codex-collaboration adversarial check" | — |
| `.claude/skills/next-steps/SKILL.md` (line 157) | `/cross-model:dialogue` | `/codex-collaboration:dialogue` | `skills/dialogue/SKILL.md:2` |

**Key naming rules:**
- MCP tool names use dots: `codex.consult`, `codex.status` (not
  underscores). The full qualified name is
  `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult`.
- Skill slash commands use the plugin namespace:
  `/codex-collaboration:dialogue` (not bare `/dialogue`, which would be
  ambiguous if multiple plugins define `dialogue`). Per Claude Code docs:
  plugin skills are always namespaced (`plugins#quickstart`).
- The `codex-reply` tool does not exist in codex-collaboration. Thread
  continuation is handled server-side via `codex.dialogue.*` tools.

**Driver:** These are operational references in live skills. After
cross-model removal, the old tool names and slash commands won't exist.

**Confidence:** High (E2) — every replacement name verified against the
delivered source.

## Change Set

### Group 1: Package deletion

| # | Path | Action |
|---|------|--------|
| 1 | `packages/plugins/cross-model/` | Delete entire directory via `trash`, then `git add -u` |

### Group 2: Workspace and lock

| # | File | Action |
|---|------|--------|
| 2 | `pyproject.toml` (root, line 9) | Remove `"packages/plugins/cross-model",` workspace member |
| 3 | `uv.lock` | Regenerate via `uv lock` |

### Group 3: CI and marketplace

| # | File | Action |
|---|------|--------|
| 4 | `.github/workflows/cross-model-plugin.yml` | Delete entire file via `trash`, then `git add -u` |
| 5 | `.claude-plugin/marketplace.json` (line 5) | Replace cross-model entry with codex-collaboration entry |

### Group 4: Validation scripts and repo-level tests

| # | File | Action |
|---|------|--------|
| 6 | `scripts/validate_consultation_contract.py` | Delete via `trash`, then `git add -u` |
| 7 | `tests/test_consultation_contract_sync.py` | Delete via `trash`, then `git add -u` |
| 8 | `tests/test_e_planning_spec_sync.py` | Delete via `trash`, then `git add -u` |

### Group 5: Project documentation updates

| # | File | Action |
|---|------|--------|
| 9 | `.claude/CLAUDE.md` (lines 43-44) | Remove cross-model and context-injection rows from Packages table |
| 10 | `.claude/CLAUDE.md` (line 93) | Remove `validate_consultation_contract.py` row from Scripts table |

### Group 6: Live skill reference updates

| # | File | Change |
|---|------|--------|
| 11 | `.claude/skills/making-recommendations/SKILL.md` | Update "Codex Delta" section header from "cross-model" to "codex-collaboration" |
| 12 | `.claude/skills/making-recommendations/references/codex-delta.md` | Rewrite per D5a: collapse two-phase protocol to single `codex.consult` call; update all tool names to `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult`; remove `codex-reply`/`codex-dialogue` references; update availability detection |
| 13 | `.claude/skills/next-steps/SKILL.md` | Update `/cross-model:dialogue` to `/codex-collaboration:dialogue` |

### Group 7: Reference index update

| # | File | Action |
|---|------|--------|
| 14 | `docs/references/README.md` (lines 50-58) | Remove the two stale "Codex Consultation Protocol" entries: (a) line 50-53 points to `packages/plugins/cross-model/references/context-injection-contract.md` which is deleted with the package, (b) lines 55-58 point to `./cross-model-plugin-operational-handbook.md` which does not exist. Retain `consultation-profiles.yaml` entry only. Delete `consultation-contract.md` symlink (target deleted with cross-model; no codex-collaboration equivalent — server-enforced contracts supersede the Claude-cognitive contract). Repoint `consultation-profiles.yaml` symlink to `codex-collaboration/references/`. Update README index to reflect both changes. |

### Group 8: T-07 ticket closeout

| # | File | Action |
|---|------|--------|
| 15 | `docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md` (line 259) | Check off cross-model removal AC with delegate smoke deferral evidence and PR citation |
| 16 | `docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md` (line 262) | Check off context-injection removal AC citing PR #122 (7d) |
| 17 | `docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md` (line 6) | Set `status: closed` |

### Group 9: Residual allowlist (not changed)

See D3 for the full allowlist table. Summary:

| Surface | Category | Count |
|---------|----------|-------|
| Historical docs (`docs/tickets/`, `docs/plans/`, `docs/reviews/`, `docs/benchmarks/`, `docs/decisions/`, `docs/audits/`, `docs/learnings/`) | Evidence preservation | ~60 refs |
| `docs/superpowers/**` | Spec evidence (design docs, skill-composability) | ~30 refs |
| `docs/prompts/cross-model-*.md` | Historical prompt artifacts | 2 files |
| `docs/archived/` | Archived subsystem documentation | varies |
| `docs/handoffs/archive/` | Immutable session snapshots | varies |
| `.planning/codebase/*.md` | Generated codebase inventory (stale) | ~40 refs |
| codex-collaboration attribution comments | Provenance | 1 file |
| codex-collaboration "Do NOT" guards | Inert protective instructions | 3 files |
| `packages/plugins/handoff/skills/defer/SKILL.md:38` | Historical signal pattern | 1 ref |
| `tests/test_validate_episode.py:62` | Test fixture keyword | 1 ref |

## Verification

After all changes, run from the repo root. Each command is self-contained.

### A. Deletion and cleanup checks

```bash
# A1. Package directory is gone
test ! -d packages/plugins/cross-model

# A2. CI workflow is gone
test ! -f .github/workflows/cross-model-plugin.yml

# A3. Validator script is gone
test ! -f scripts/validate_consultation_contract.py

# A4. Repo-level sync tests are gone
test ! -f tests/test_consultation_contract_sync.py
test ! -f tests/test_e_planning_spec_sync.py

# A5. No cross-model workspace member in pyproject.toml
! grep -q 'cross-model' pyproject.toml

# A6. No cross-model in marketplace
! grep -q 'cross-model' .claude-plugin/marketplace.json

# A7. CLAUDE.md has no cross-model package entry or deleted script
! grep -q 'packages/plugins/cross-model' .claude/CLAUDE.md
! grep -q 'validate_consultation_contract' .claude/CLAUDE.md
```

### B. Replacement availability checks (7c live parity)

7c §5 requires executing the parity checklist against live state, not just
citing the matrix. These checks verify the five replacement workflow
surfaces exist and are correctly wired.

```bash
# B1. All five replacement skills exist
test -f packages/plugins/codex-collaboration/skills/consult-codex/SKILL.md
test -f packages/plugins/codex-collaboration/skills/dialogue/SKILL.md
test -f packages/plugins/codex-collaboration/skills/delegate/SKILL.md
test -f packages/plugins/codex-collaboration/skills/codex-analytics/SKILL.md
test -f packages/plugins/codex-collaboration/skills/codex-review/SKILL.md

# B2. All MCP tools used by the five replacement skills exist in server
# Consult workflow
grep -q '"name": "codex.consult"' packages/plugins/codex-collaboration/server/mcp_server.py
grep -q '"name": "codex.status"' packages/plugins/codex-collaboration/server/mcp_server.py
# Dialogue workflow
grep -q '"name": "codex.dialogue.start"' packages/plugins/codex-collaboration/server/mcp_server.py
grep -q '"name": "codex.dialogue.reply"' packages/plugins/codex-collaboration/server/mcp_server.py
grep -q '"name": "codex.dialogue.read"' packages/plugins/codex-collaboration/server/mcp_server.py
# Delegate workflow
grep -q '"name": "codex.delegate.start"' packages/plugins/codex-collaboration/server/mcp_server.py
grep -q '"name": "codex.delegate.poll"' packages/plugins/codex-collaboration/server/mcp_server.py
grep -q '"name": "codex.delegate.decide"' packages/plugins/codex-collaboration/server/mcp_server.py
grep -q '"name": "codex.delegate.promote"' packages/plugins/codex-collaboration/server/mcp_server.py
grep -q '"name": "codex.delegate.discard"' packages/plugins/codex-collaboration/server/mcp_server.py

# B3. Marketplace entry resolves to a real plugin with correct name
_src=$(jq -r '.plugins[] | select(.name == "codex-collaboration") | .source' \
  .claude-plugin/marketplace.json)
test -n "$_src"
test -f "$_src/.claude-plugin/plugin.json"
jq -e '.name == "codex-collaboration"' "$_src/.claude-plugin/plugin.json" > /dev/null
```

### C. Reference cleanliness checks

```bash
# C1. No cross-model Python imports remain
! grep -rq 'from cross_model\|import cross_model' \
  --include='*.py' \
  packages/ scripts/ tests/

# C2. No cross-model MCP tool references in live skills
! grep -rq 'mcp__plugin_cross-model' \
  .claude/skills/ \
  --include='*.md'

# C3. No /cross-model: slash command references in live skills
! grep -rq '/cross-model:' \
  .claude/skills/ \
  --include='*.md'

# C4. No cross-model MCP tool references in plugin skills
! grep -rq 'mcp__plugin_cross-model' \
  packages/plugins/*/skills/ \
  --include='*.md'
```

### D. Residual reference scan (exhaustive + allowlist)

The scan uses path-based exclusions for historical directories and then
lists the expected remaining files by exact path. No content-based
suppressions.

```bash
# D1. Case-insensitive repo-wide scan with --hidden and path-based exclusions
rg -in --hidden 'cross.model|cross_model' \
  --glob '*.py' --glob '*.md' --glob '*.json' \
  --glob '*.yml' --glob '*.yaml' --glob '*.toml' \
  --glob '!.git/**' \
  --glob '!**/__pycache__/**' \
  --glob '!**/.pytest_cache/**' \
  --glob '!**/.ruff_cache/**' \
  --glob '!**/.DS_Store' \
  --glob '!docs/tickets/**' \
  --glob '!docs/plans/**' \
  --glob '!docs/reviews/**' \
  --glob '!docs/benchmarks/**' \
  --glob '!docs/decisions/**' \
  --glob '!docs/audits/**' \
  --glob '!docs/learnings/**' \
  --glob '!docs/handoffs/**' \
  --glob '!docs/archived/**' \
  --glob '!docs/superpowers/**' \
  --glob '!docs/prompts/cross-model-*' \
  --glob '!.planning/codebase/**' \
  --glob '!node_modules/**' \
  .
# Review output. Expected remaining files (from D3 allowlist):
#   packages/plugins/codex-collaboration/server/secret_taxonomy.py:3
#   packages/plugins/codex-collaboration/skills/codex-review/SKILL.md:8,27
#   packages/plugins/codex-collaboration/skills/consult-codex/SKILL.md:19
#   packages/plugins/codex-collaboration/skills/delegate/SKILL.md:24
#   packages/plugins/handoff/skills/defer/SKILL.md:38
#   tests/test_validate_episode.py:62
# Any file NOT in this list is a plan defect and must be classified.
# Hidden paths (.claude/, .claude-plugin/) are included in the scan.
```

### E. Test suite and code quality

```bash
# E1. codex-collaboration tests still pass
(cd packages/plugins/codex-collaboration && uv run --package codex-collaboration pytest)

# E2. Remaining root-level tests pass
uv run pytest tests/test_validate_episode.py tests/test_skill_impact_stats.py -v

# E3. uv lock succeeds
uv lock

# E4. Lint passes
ruff check

# E5. Git diff hygiene
git diff --check
```

## Build Sequence

1. Create branch (done: `feature/t07-cross-model-removal-7e`)
2. Delete `packages/plugins/cross-model/` via `trash` + `git add -u` (Group 1)
3. Remove workspace member, regenerate lockfile (Group 2)
4. Delete CI workflow, update marketplace (Group 3)
5. Delete validator script and repo-level tests (Group 4)
6. Update CLAUDE.md — package table and scripts table (Group 5)
7. Update live skill references with exact names; rewrite Codex Delta (Group 6)
8. Update reference index — remove stale cross-model entries (Group 7)
9. Update T-07 ticket: check ACs, close ticket (Group 8)
10. Run verification: A (deletion), B (parity), C (references), D (residual scan), E (tests + lint)
11. Commit, push, PR

Groups 2-9 can be applied in any order after Group 1. Verification (step
10) runs after ALL edits including ticket closeout, so `git diff --check`
covers the final state. The D1 residual scan is reviewed interactively —
any unexpected hit is a plan defect.

## Caveats That Travel With This Removal

Per T-04 closeout and T-07 ticket:

1. `T-20260416-01` (reply-path extraction mismatch) remains open
2. Mechanism losses L1 (scout integrity), L2 (plateau/budget control),
   L3 (per-scout redaction) are accepted trade-offs
3. Capture sequence spans multiple doc commits (audit fact)
4. Live `/delegate` smoke deferred due to execution-domain defects
   (sandbox + approval path), not App Server unavailability

## T-07 AC Status After 7e

| AC | Status |
|----|--------|
| Analytics skill exists | **Checked (7a)** — PR #116 |
| codex-review skill exists | **Checked (7b)** — PR #117 |
| Migration docs | **Checked (7c)** — PR #120 |
| Parity matrix | **Checked (7c)** — PR #120 |
| Cross-model removed | **7e (this slice)** — with delegate smoke deferral |
| Context-injection removed | **Checked (7d)** — PR #122 |

## References

| Document | Location | Role |
|----------|----------|------|
| T-07 ticket | `docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md` | AC definitions |
| 7c migration artifact | `docs/plans/2026-04-22-t07-cross-model-migration-and-parity-7c.md` | Parity matrix, removal inventory |
| 7d plan | `docs/plans/2026-04-22-t07-context-injection-removal-7d.md` | Predecessor, retained-until-7e list |
| T-04 retirement decision | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | Context-injection authority |
| T-06 ticket | `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md` | Delegate smoke precedent |

# Codex App Server Server-Request Envelope-Diagnostic Overclaim Fix

> **For agentic workers:** Execute sequentially in one workspace; do not parallelize across Task 3 commit state or temp-file dependencies. Steps use checkbox (`- [ ]`) syntax for tracking. This is a docs-only plan with hard scope guardrails; do not convert it into a parser/response correctness change or into a T-20260429-02 method-by-method coverage push.

**Goal:** Reconcile the committed May-1 server-request envelope-probe diagnostic with the repaired rebaseline implementation plan and `approval_router.py` reality, eliminating the docs-only contradiction without altering raw observation evidence.

**Architecture:** Surgical doc edits. Preserve the diagnostic's raw observation layer (envelope contents, params keys, redacted summary, trigger command) untouched, with programmatic enforcement via pre/post jq-projection diff. Patch only the interpretive layer that conflicts with code reality. Mirror the correction in the diagnostic's sibling JSON via in-place interpretive reclassification: mutate the three classification fields (`local_compatibility`, `compatibility_classification`, `architecture_spec_readiness_delta`) to carry rebaseline-vocabulary values while preserving all raw-observation fields unchanged. The vocabulary succession is documented in the Markdown diagnostic and commit message; git history preserves the prior vocabulary. Optionally annotate the reconciliation register so its priority order reflects landed implementation.

**Tech Stack:** Markdown, JSON, ripgrep, jq, git.

---

## Boundary

This plan implements:

- Wording corrections to the envelope-probe diagnostic `.md` interpretive claims (five specific sites: classification line, "Local compatibility judgment" bullet block, "Compatibility result" bullet block, "Important limit" first sentence, and "Architecture Spec Readiness Delta" section).
- A sibling-JSON in-place interpretive correction: mutate the three classification fields to rebaseline-vocabulary values. No migration scaffolding (`_legacy_*` renaming, vocabulary markers, or dual-shape blocks). The `compatibility_classification` block's key set changes (e.g., `supported_methods` → `fully_supported_methods` / `parser_kind_compatible_methods` / `decision_shape_lossy_methods`) — this is a schema-shape change, not a value-only edit. Justified by no literal-path-based production consumers (Task 1.4 verifies via filename search); git history preserves the prior vocabulary.
- Programmatic raw-evidence preservation: pre-edit jq-projection of immutable JSON paths captured to a deterministic temp file, post-edit re-projection, and `diff` exit-empty before staging.
- Optional reconciliation-register annotation recording that `T-20260429-01` Phase 1 implementation has landed on `main`, with closure evidence still missing.
- A verification sweep across May-1 diagnostics, the rebaseline plan, the friction-reduction ticket, and the register for residual overclaims.
- Reconciliation of the rebaseline implementation plan's evidence-check section (lines 204-220) so its `jq` commands and expected-value bullets reflect the corrected JSON field values. Without this update, a future worker following the rebaseline plan would hit an evidence mismatch when reading the post-patch JSON.
- One commit covering all of the above, with a conditional commit-message template (sections marked CONDITIONAL must be edited to match the actually-staged file set before committing).

This plan does not:

- Modify `approval_router.py`, `delegation_controller.py`, `runtime.py`, or any other code.
- Alter raw envelope observations (params keys, redacted envelope summary, observed JSON-RPC `id`/`method`, trigger command, "no approval response was sent" record).
- Land response semantics, lossless `availableDecisions` preservation, or any fix to the parser fallback path.
- Perform any T-20260429-02 method-by-method classification work for `mcpServer/elicitation/request`, `item/tool/call`, `applyPatchApproval`, `execCommandApproval`, `account/chatgptAuthTokens/refresh`, `item/permissions/requestApproval`, `item/fileChange/requestApproval`, or `item/tool/requestUserInput`.
- Run a `/delegate` smoke, a credential-boundary probe, or any other live App Server probe.
- Move the reconciliation register's priority order beyond annotating `T-20260429-01` as landed-but-not-closed.
- Re-litigate `~/.codex` carve-outs, `~/.agents` reads, or dynamic gitdir resolution.
- Raise `TESTED_CODEX_VERSION` or `MINIMUM_CODEX_VERSION`.
- Discover or accommodate external consumers of the diagnostic JSON. The diagnostic JSON is treated as a repo-internal artifact, NOT a public contract. Task 1.4 confirms zero repo-local production consumers. External consumers are explicitly out of scope; if one is later identified, the appropriate response is to update that consumer or raise a separate plan.

## Authority Basis

Truth ranking for this plan's wording decisions, highest first:

1. `packages/plugins/codex-collaboration/server/approval_router.py:103-111` — `_resolve_available_decisions` keeps the wire `availableDecisions` only when `isinstance(wire_value, list) and all(isinstance(decision, str) for decision in wire_value)`. Mixed lists containing structured (dict) entries fall through to `_AVAILABLE_DECISIONS[kind]`.
2. `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:905-921` — "Command Approval Decision-Shape Boundary" section. Names the lossy fallback, the structured `acceptWithExecpolicyAmendment` entry, and the missing-`decline` response semantics.
3. The committed envelope-probe diagnostic interpretive layer (`docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` lines ~112 and ~169-174 plus the sibling JSON if it carries the same claims) is downstream of (1) and (2). Where it conflicts, it loses.

Raw envelope observations in the diagnostic are independent of this ranking and are preserved as evidence.

### Vocabulary Succession

The May-1 envelope-probe plan (`docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md:666-672`) defined a four-state classification — `supported` / `unsupported` / `unknown` / `unparseable` — where `supported` meant "local code has a concrete route for the method and required correlation fields are present." Under that vocabulary, the diagnostic's `local_compatibility: "supported"` classification was internally consistent: the parser does have a concrete route (`item/commandExecution/requestApproval` → `kind="command_approval"`) and the required correlation fields (`itemId`, `threadId`, `turnId`) were present.

The repaired rebaseline plan introduces a stricter classification that splits the original `supported` slot into two distinct properties: parser-kind compatibility (route exists + required fields present) and response-shape compatibility (parser preserves the wire's decision shape). Under the stricter classification, the May-1 envelope establishes parser-kind compatibility but not response-shape compatibility — `_resolve_available_decisions` falls back when the wire list contains structured entries.

This plan reconciles the diagnostic against the stricter vocabulary. The diagnostic is not retroactively wrong against its own May-1 vocabulary; it is reclassified against the rebaseline's narrower one. Replacement wording in Task 2 names parser-kind compatibility explicitly so future readers see the succession rather than reading the patch as a correction-of-error.

## Raw Envelope Facts To Preserve

Do not edit, paraphrase, summarize away, or "clean up" any of these in the diagnostic `.md` or its sibling JSON. They are evidence. Treat them as immutable for the scope of this plan:

- The observed method string `item/commandExecution/requestApproval`.
- The presence of a JSON-RPC `id`.
- The observed top-level `params` keys list (`availableDecisions`, `command`, `commandActions`, `cwd`, `itemId`, `proposedExecpolicyAmendment`, `reason`, `threadId`, `turnId`).
- The literal three-element `availableDecisions` array (`"accept"`, `{"acceptWithExecpolicyAmendment": {...}}`, `"cancel"`).
- The redacted envelope summary JSON block as captured.
- The trigger command (`/bin/zsh -lc 'touch server-request-probe.txt'`).
- The record that "No approval response was sent."
- Schema-visible server-request methods listing (the broader bullet list around line ~157-167).
- Any per-probe pass/fail rows in the test summary table.

## Interpretive Overclaims To Patch

Five specific sites in the `.md` (line numbers from orientation reads; reconfirm in Task 1 before editing):

1. **Compatibility-classification line (≈line 112).**
   Current text:
   ```
   - local compatibility classification: `supported`
   ```
   Why wrong: the parser is decision-shape lossy under the observed envelope. "Supported" overclaims by collapsing parser-kind compatibility (correct) with response-shape compatibility (not established).
   Replacement direction: classification names parser-kind compatibility AND decision-shape lossiness explicitly, with a forward-pointer to the rebaseline plan section that owns the lossless-branch path.

2. **"Local compatibility judgment" bullet block (≈lines 169-174).**
   Current bullet list (verified excerpt):
   ```
   - `approval_router.py` maps `item/commandExecution/requestApproval` to `kind="command_approval"`
   - the parser requires `id`, `method`, `params`, `itemId`, `threadId`, and `turnId`
   - the live envelope includes all of those fields
   - `availableDecisions` is also present and preserved
   ```
   Why wrong: `availableDecisions` is *present on the wire* (raw observation, true) but NOT *preserved by the parser* (the all-strings condition fails on the structured `acceptWithExecpolicyAmendment` entry, so `_resolve_available_decisions` returns `_AVAILABLE_DECISIONS[command_approval]`). The fourth bullet conflates wire-presence with parser-preservation.
   Replacement direction: split wire-presence from parser-preservation. Name the all-strings fallback condition explicitly. Enumerate the fallback tuple verbatim and describe lossiness as bidirectional — the fallback preserves `accept` and `cancel` (string entries on the wire), loses the structured payload of `acceptWithExecpolicyAmendment`, AND adds three decisions never offered by the wire (`acceptForSession`, `applyNetworkPolicyAmendment`, `decline`). Do not phrase the lossiness as "decline replaces cancel" — `cancel` is preserved by the fallback; `decline` is added alongside it. Cite `approval_router.py:103-111` and the rebaseline plan's "Command Approval Decision-Shape Boundary" section.

3. **"Compatibility result" block (≈lines 176-181).**
   Current text:
   ```
   Compatibility result:

   - observed supported methods: `item/commandExecution/requestApproval`
   - observed unsupported methods: none
   - observed unknown or unparseable methods: none
   - missing required fields: none
   ```
   Why wrong: classifying `item/commandExecution/requestApproval` under "observed supported methods" is the same overclaim as site 1 — it asserts full support when the parser is decision-shape lossy under the observed envelope. The vocabulary `supported` / `unsupported` / `unknown` is too coarse for the actual classification this packet justifies.
   Replacement direction: rename / reshape the bullets to distinguish *parser-kind compatible* from *fully supported*. The observed method is parser-kind compatible but decision-shape lossy; nothing in this packet establishes any method as fully supported. Add a bullet calling out lossy-decision-shape methods explicitly, or fold the qualification into the "observed parser-kind compatible methods" bullet.

4. **"Important limit" sentence (≈line 185).**
   Current text:
   ```
   This packet proves compatibility for the observed command-approval envelope only. It does not prove live reachability or parser cleanliness for file-change, permission, tool-input, MCP elicitation, auth-refresh, or other schema-visible server-request methods.
   ```
   Why wrong: only the *first sentence* is the overclaim — "proves compatibility" asserts response-shape compatibility, which the packet does not establish. The second sentence (about non-proof for other methods) is a useful caveat and stays.
   Replacement direction: narrow the first sentence's claim to what the packet actually proves — parser-kind compatibility (envelope parsing succeeds and maps to `kind=command_approval`) for the observed command-approval envelope only. Explicitly note that response-shape compatibility is not established because the observed mixed `availableDecisions` triggers parser fallback. Leave the second sentence intact.

The exact replacement text for all five sites is fixed in Task 2. Task 1's pre-edit `rg` sweep is responsible for surfacing any sites this enumeration misses; if it does, Task 1 stops and surfaces rather than expanding scope silently.

## Files To Inspect Before Edit

Read every item below before any write. Each read has a specific load-bearing purpose:

| File | Purpose |
|---|---|
| `packages/plugins/codex-collaboration/server/approval_router.py:90-115` | Confirm `_resolve_available_decisions` semantics; capture `_AVAILABLE_DECISIONS[command_approval]` tuple contents verbatim — used in Task 2 and Task 3 replacement wording. |
| `packages/plugins/codex-collaboration/server/runtime.py` (readable-roots at ~107-118, gitdir resolver at ~28-60 on `main`) | Confirm Phase 1 sandbox carve-outs are present; use `git show main:.../runtime.py | rg -n "codex\|agents\|worktrees\|build_workspace_write_sandbox_policy\|resolve_git_dir"` to capture both the append site AND the structural validation. Drives Task 4 register annotation. Read on `main`, not the current branch. |
| `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:895-925` | Anchor corrected wording to the repaired plan's framing ("decision-shape lossy", structured `acceptWithExecpolicyAmendment`, "lossless parser/response branch"). |
| `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:204-220` | Evidence-check `jq` commands and expected-value bullets that read `local_compatibility` and `architecture_spec_readiness_delta` from the sibling JSON. These are Markdown-embedded consumers of the canonical JSON fields that Task 3 renames. Drives Task 5.5 reconciliation. |
| `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` (full, with extra attention to lines ≈100-200) | Confirm the five enumerated overclaim sites; surface any other interpretive overclaims. |
| `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` (sibling JSON, may or may not exist) | Discover existence; if present, identify any parallel overclaim fields. Drives Task 3 disposition. |
| `docs/status/codex-collaboration-reconciliation-register.md:9-70` | "Last reconciled" timestamp + priority order + `T-20260429-01` row "Current truth"/"Exit condition" cells. Drives Task 4 disposition. |
| `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:212-230` (T-20260429-01 ticket) | Confirm acceptance criteria and that AC #1 smoke / AC #2 credential-boundary probe / AC #3 regression assertion + suite pass evidence is genuinely missing. |
| `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md` (T-20260429-02 ticket — context only, no edits) | Context for the Sweep Classification Rules: the parser-route classification table at lines 67-77 ("Supported as `<kind>`" / "Supported (parked)") is `legacy-parser-route-vocabulary`, not an overclaim. The T-20260429-02 method-by-method classification work is OUT of this plan's scope. Read so the worker can confidently classify sweep matches against this file. |
| `docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md:666-672` (May-1 probe-plan vocabulary) | Context for the Sweep Classification Rules: the May-1 four-state vocabulary (`supported` / `unsupported` / `unknown` / `unparseable`) is `legacy-parser-route-vocabulary`. Read to ground the Vocabulary Succession framing in the Authority Basis section. |
The pre-edit `rg` sweep below treats every file under `docs/diagnostics/2026-05-01-codex-app-server-*.md`, `docs/diagnostics/codex-app-server-*.json`, `docs/plans/2026-05-01-codex-app-server-*.md`, `docs/tickets/2026-04-29-codex-collaboration-*.md`, and `docs/status/codex-collaboration-reconciliation-register.md` as candidates. If the sweep surfaces hits this plan does not enumerate, Task 1 stops and surfaces the finding rather than expanding scope silently.

**Out-of-scope docs (deferred to follow-up):** `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md` contains the same "local classification was `supported`" wording (lines 56, 93, 148-160) and will need a separate vocabulary-reconciliation pass. Active handoffs under `docs/handoffs/` capture session state at a point in time and are not patched here. Both are explicitly excluded from this plan's sweep, classification, and commit scope to maintain a single unambiguous patch boundary.

## Stop Conditions

Stop and surface the situation to the user — do not adapt, expand, or work around — when any of these fire:

- **JSON correction is unsafe to decide locally.** Task 1.4 finds the sibling JSON exists, contains a parallel overclaim, AND consumer discovery surfaces a production consumer that reads one of the three classification fields and would break under the corrected values. Surface and ask before proceeding. (With zero confirmed consumers at plan-write time, this stop condition is expected to never fire.)
- **Pre-edit sweep finds an overclaim site this plan does not enumerate.** "Overclaim" here is bounded by the Sweep Classification Rules below. Examples that trigger this stop: a file under the swept paths claiming command-approval is fully supported in the response-shape sense; a `ready_to_close_ticket: true` for command approval; a register or diagnostic cell asserting `availableDecisions` is preserved without naming the all-strings fallback; an additional JSON overclaim path beyond the three enumerated paths that does NOT mechanically mirror the same kind of claim per Task 1.4's narrow exception. Examples that do NOT trigger this stop (classifiable as `legacy-parser-route-vocabulary`): the T-20260429-02 ticket's `Supported as <kind>` / `Supported (parked)` table entries, the May-1 probe-plan's definition of `supported`, or any other legacy May-1-vocabulary use that is not a fresh response-shape / lossless-preservation / closability claim. Surface the finding; do not silently extend Task 2's edits.
- **Register row already reflects landed-implementation language for T-20260429-01.** Skip Task 4 entirely; do not make a no-op edit.
- **Register-annotation `main`-truth check failed.** Step 1.5b's git evidence does not support the "Phase 1 has landed on `main`" assertion. This fires when ANY of: (a) `git diff main..HEAD -- packages/plugins/codex-collaboration/server/runtime.py` is non-empty (this branch carries `runtime.py` modifications, so the current-branch reads do not stand in for `main`), (b) carve-outs are absent from `main`'s `runtime.py` entirely — verified via `git show main:packages/plugins/codex-collaboration/server/runtime.py | rg -n "codex|agents|worktrees|build_workspace_write_sandbox_policy"` returning zero matches (implementation not landed), OR (c) `main` and `origin/main` diverge after `git fetch` and cannot be reconciled (remote state unverifiable). **Line drift is NOT this stop condition** — if carve-outs appear on `main` at different line numbers than 107-118, that is normal drift handled in Step 1.5b (record actual lines, update all Task 4 references, proceed). **Scope:** Skip Task 4 only; do NOT block Tasks 2, 3, 5, or 6. Task 4 is an optional register annotation — its failure does not invalidate the core diagnostic/JSON correction. Surface the finding so the register-annotation premise can be reconciled in a separate follow-up if needed.
- **Verification sweep at Task 5 surfaces a surviving overclaim.** Do not commit. Surface the finding.
- **Live envelope evidence has changed since the diagnostic was captured.** This stop condition fires if Task 1's reads reveal newer evidence contradicting the May-1 envelope (different `availableDecisions` shape, different method string, etc.). The fix's premise depends on the May-1 capture being current. **Discovery path:** filename-pattern search during Task 1.1:

  ```bash
  rg --files docs/diagnostics/ | rg '2026-05-(0[2-9]|[12][0-9]|3[01])-.*envelope|2026-06-.*envelope'
  ```

  This searches for dated envelope-probe diagnostic artifacts captured after May 1. If a post-May-1 file is found, read its `availableDecisions` shape and compare against the May-1 capture's three-element array (`["accept", {"acceptWithExecpolicyAmendment": {...}}, "cancel"]`). If the shapes differ, this stop condition fires. If no newer artifact exists (expected — the search returns nothing), record "no post-May-1 envelope capture found" and proceed.

## Sweep Classification Rules

Every match returned by the rg sweeps in Task 1.1, Task 2.6, Task 3.5, Task 4.5, and Task 5.1 must be classified as exactly one of the following. Task 1.1 produces the baseline classification; later sweeps reuse the same rules for diff verification.

| Classification | When it applies | Action |
|---|---|---|
| `raw-observation` | The match is part of the diagnostic's evidence layer (envelope contents, params keys, redacted summary, observed `availableDecisions` array, trigger command, "no approval response was sent" record, schema-visible methods listing, per-probe pass/fail rows). | Preserve unchanged. |
| `interpretive-overclaim` | The match makes a claim against the rebaseline vocabulary that conflicts with `approval_router.py:103-111`. Bounded by the rules below. | Patch under the relevant Task 2 / Task 3 step, OR fire the "pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition if the site is not enumerated. |
| `corrected-language` | The match is post-patch wording that already names parser-kind compatibility, decision-shape lossiness, the all-strings fallback, or related rebaseline framing. | Preserve unchanged. |
| `legacy-parser-route-vocabulary` | The match uses the May-1 probe-plan's narrower `supported` vocabulary in a way that does NOT make a response-shape / lossless-preservation / closability claim. See bounding rules below. | Preserve unchanged. Do not patch; do not fire the stop condition. |
| `authority-source` | The match is in a section that this plan cites as a truth authority (Authority Basis items 1-2) and uses rebaseline-era framing (e.g., "decision-shape lossy", "response compatibility is not established", "lossless parser/response branch"). Distinct from `legacy-parser-route-vocabulary` — authority sections describe current decision-shape-lossy reality, not the May-1 narrower vocabulary. Primary instance: rebaseline plan lines 905-921 ("Command Approval Decision-Shape Boundary"). | Preserve unchanged. |
| `unrelated` | The match's word appears in a context that has nothing to do with command-approval classification (e.g., "supported sandbox carve-outs", "supported plugin" in a different domain). | Preserve unchanged. |
| `peer-diagnostic-data-artifact` | The match is in a sibling or related diagnostic JSON file (e.g., `codex-app-server-scratch-home-runtime-probes.json`, `codex-app-server-materialized-thread-and-server-request-probes.json`) that contains the same field names as data from its own probe session, not as a claim about the target diagnostic's method classification. These are independent diagnostic captures with their own classification fields governed by whatever plan or probe session produced them. | Preserve unchanged. |

### Bounding `legacy-parser-route-vocabulary` vs `interpretive-overclaim`

The line between these two classifications is sharp. A match is `legacy-parser-route-vocabulary` only when ALL of the following hold:

- The wording uses the May-1 probe-plan's `supported` vocabulary (route exists + required fields present), not the rebaseline's response-shape sense.
- The wording does NOT claim response-shape compatibility, lossless preservation, or ticket closability for command-approval.
- The wording is in a context that is independently authored against the May-1 vocabulary (T-20260429-02 ticket parser-route classification table; May-1 probe-plan vocabulary definitions; analogous parser-route catalogs).

A match is `interpretive-overclaim` (and triggers the stop condition if not already enumerated) when ANY of the following hold:

- The wording claims command-approval is `supported` in the rebaseline's response-shape sense (e.g., "this packet proves compatibility").
- The wording claims `availableDecisions` is `preserved`, `lossless`, or otherwise unmodified by the parser.
- The wording asserts `ready_to_close_ticket: true` for command-approval, or otherwise treats command-approval as fully supported for closure purposes.
- The wording uses `local_compatibility: "supported"` or lists command-approval under `supported_methods` without the parser-kind / decision-shape-lossy qualification.

When a match is borderline, prefer `interpretive-overclaim` and surface for explicit disposition.

### Examples Already Verified

- `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:69-71` table rows (`| item/commandExecution/requestApproval | Supported as command_approval | Supported (parked) |` and equivalents for `file_change`, `request_user_input`) are `legacy-parser-route-vocabulary`. They classify the parser's route mapping under the T-20260429-02 ticket's classification work, not the rebaseline's response-shape framing.
- `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:85,88` ("supported handling, a regression test...", "Supported methods retain regression coverage...") are also `legacy-parser-route-vocabulary` — they describe acceptance-criterion options for classification work in the May-1 vocabulary.
- `docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md:666-672` definitions of `supported` / `unsupported` / `unknown` / `unparseable` are `legacy-parser-route-vocabulary` — they are the May-1 vocabulary definitions themselves.
- `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md:112` (`local compatibility classification: supported`) is `interpretive-overclaim` — applies the May-1 vocabulary to a method whose response-shape compatibility is not established.
- `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` `local_compatibility: "supported"` and `compatibility_classification.supported_methods` are `interpretive-overclaim` — same reasoning, machine-readable form.

## Verification

Final pre-commit sweep, run from repo root. The pattern intentionally combines bare-word terms (`supported`, `preserved`, `lossy`, `ready_to_close_ticket`) with phrase patterns (`proves compatibility`, `compatibility for the observed`, `architecture spec can proceed`, `parseable against`, `architecture spec readiness delta`) and JSON-key patterns (`local_compatibility`, `supported_methods`, `architecture_spec_readiness_delta`, `newly_satisfied_items`) so neither a bare-word-only site nor a phrase/key-only site can slip past. The architecture-readiness patterns (added in review-cycle 4) catch the parallel overclaim site at the diagnostic's "Architecture Spec Readiness Delta" section / `architecture_spec_readiness_delta` JSON block, where `ready: true` and `parseable against the current local compatibility boundary` previously slipped past the cycle-1 pattern. The sweep is case-insensitive (`-i`) so capital-S "Supported" classifications surface alongside lowercase ones; classification (Sweep Classification Rules above) decides which matches are overclaims and which are legacy parser-route vocabulary:

```bash
rg -n -i "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods|architecture_spec_readiness_delta|architecture spec readiness delta|architecture spec can proceed|parseable against|newly_satisfied_items" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

**Classification scope:** Full per-line classification is mandatory only for files in this plan's write set (diagnostic `.md`, diagnostic `.json`, register, rebaseline plan). For other swept files (tickets, other plans), confirm no `interpretive-overclaim` exists — a brief spot-check is sufficient; exhaustive per-line annotation is not required.

Acceptable terminal classifications: `raw-observation`, `corrected-language`, `legacy-parser-route-vocabulary`, `authority-source`, `peer-diagnostic-data-artifact`, `unrelated`. Unacceptable: `interpretive-overclaim` (any surviving site triggers the Task 5 stop condition).

No surviving site may claim command-approval is "supported" in the rebaseline response-shape sense without the parser-kind / decision-shape-lossy qualification, or claim `availableDecisions` is "preserved" without naming the all-strings fallback condition, or list `item/commandExecution/requestApproval` under `supported_methods` / "observed supported methods" without that qualification, or assert "proves compatibility" for command-approval response semantics, or assert `ready_to_close_ticket: true` for `item/commandExecution/requestApproval`, or assert `architecture_spec_readiness_delta.ready: true` / "architecture spec can proceed" / "parseable against the current local compatibility boundary" without naming the decision-shape lossiness as a remaining response-semantics blocker. Legacy parser-route vocabulary in the T-20260429-02 ticket and the May-1 probe-plan vocabulary definitions is explicitly out of scope for this plan and remains untouched. The JSON's corrected `notes` arrays contain vocabulary-succession prose explaining the prior classification; these are `corrected-language` (they explicitly name the prior vocabulary as superseded, not as current truth).

---

## Tasks

### Task 0: Pre-edit status snapshot

**Files:** read-only — no writes in this task.

- [ ] **Step 0.1: Branch safety check.**

Verify the working branch is not protected:

```bash
git branch --show-current
```

Check: **Current branch is the expected working branch** (not `main`). Record the branch name. If on `main`, STOP — create the appropriate working branch before proceeding.

Remote/main freshness is NOT checked here. Only Task 4 (optional register annotation) makes "landed on `main`" claims; that task's precondition (Step 1.5b) verifies remote state before writing. Tasks 2, 3, 5, and 6 are purely local doc edits that do not depend on remote state.

- [ ] **Step 0.2: Capture pre-edit status snapshot.**

```bash
git status
git diff --cached --name-only
git diff --name-only
```

Record the output. The intent is to identify any pre-existing unrelated changes in the working tree BEFORE this plan's edits begin, so Task 6's commit-staging logic can distinguish "files I added during this plan" from "files that were already modified in this workspace."

Expected scope of files this plan touches (any of these may legitimately appear in Task 6's staged set):

- `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` (Task 2, always)
- `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` (Task 3, conditional)
- `docs/status/codex-collaboration-reconciliation-register.md` (Task 4, conditional)
- `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` (Step 5.5, conditional — state-based: runs when canonical JSON fields carry rebaseline vocabulary, whether from this run's Task 3 or a prior commit; see Step 5.5 skip condition)

Branch on the snapshot:

- **Working tree clean** → record "Pre-edit status: clean." Proceed to Task 1.
- **Pre-existing changes in target files** (any of the four files above appear in `git diff --name-only` or `git diff --cached --name-only`) → STOP and surface to user before proceeding. Pre-existing edits in files this plan will mutate are ambiguous: they may be from a prior partial run of this plan, a concurrent manual edit, or an unrelated change. The user must either (a) stash/commit them separately, (b) revert them if they are from a prior partial run, or (c) explicitly confirm they should be treated as the baseline for this plan's edits. Do NOT proceed until the target files match `HEAD`.
- **Pre-existing unrelated unstaged changes exist** (files outside the four above) → record their paths. They are NOT in scope for this plan; do not stage, modify, or revert them during this plan's execution. Task 6's verification will tolerate their continued presence in the working tree as long as they are unchanged from this snapshot.
- **Pre-existing staged changes exist from a different in-flight task** (any staged file outside the four above) → STOP and surface to user before proceeding. Combining unrelated staged work with this plan's commit would muddle the audit trail. The user must either unstage or commit the unrelated staged work separately before this plan continues.

(No commit at end of Task 0 — discovery only. Task 0 outputs feed Task 6's staged-set verification.)

---

### Task 1: Inventory and discovery

**Files:** read-only — no writes in this task.

- [ ] **Step 1.1: Pre-edit ripgrep sweep.**

```bash
rg -n -i "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods|architecture_spec_readiness_delta|architecture spec readiness delta|architecture spec can proceed|parseable against|newly_satisfied_items" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

The `-i` flag is intentional: capital-S "Supported" wording in the T-20260429-02 ticket's parser-route classification table and lowercase "supported" wording in the diagnostic must both surface so the Sweep Classification Rules above can decide which matches are overclaims and which are legacy parser-route vocabulary.

**Classification scope:** Full per-line classification is mandatory only for files in this plan's write set (diagnostic `.md`, diagnostic `.json`, register, rebaseline plan). For other swept files (tickets, other plans), confirm no `interpretive-overclaim` exists — a brief spot-check is sufficient; exhaustive per-line annotation is not required. The annotated list is reused in Task 5 as the baseline for diff verification.

**Classification baseline artifact (scrutiny follow-up 9).** The annotated classification list MUST be written to a temporary file for Task 5 diffing:

```bash
# After classifying all matches, write the baseline table
cat > /private/tmp/codex-collab-overclaim-fix-sweep-baseline.md <<'BASELINE'
# Sweep Classification Baseline — Task 1.1
# Generated: <timestamp>
# Format: path:line | matched text (truncated) | classification | disposition

<one line per match, e.g.:>
docs/diagnostics/...probes.md:112 | local compatibility classification: `supported` | interpretive-overclaim | patch in Step 2.1
...
BASELINE
```

This file persists across Tasks 2-5 and is the authoritative reference for Task 5's diff verification. Task 5 compares its post-edit sweep against this baseline to confirm all `interpretive-overclaim` matches were patched and all other classifications are unchanged. Without a durable artifact, the classification baseline is ephemeral and Task 5 cannot reliably diff against it.

Verification anchors:

- The five enumerated overclaim sites in the diagnostic `.md` (≈lines 112, 169-174, 176-181, 185, and the "Architecture Spec Readiness Delta" section at ≈lines 189-202 — specifically lines 195 and 202) MUST appear in the output and MUST be tagged `interpretive-overclaim`.
- The JSON `architecture_spec_readiness_delta` block (≈lines 45580-45591 in `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`) MUST surface — at minimum the `architecture_spec_readiness_delta` key-name line and the `newly_satisfied_items[2]` "parseable against the current local compatibility boundary" line — and MUST be tagged `interpretive-overclaim`. Note: the `rg` sweep pattern matches the key name `architecture_spec_readiness_delta` and the phrase `parseable against`, but cannot match the nested `"ready": true` boolean value (the line `"ready": true` contains neither keyword). Verify the `ready: true` boolean via `jq -e '.architecture_spec_readiness_delta.ready == true'` during Task 1.4's path derivation step; Step 3.6c's canonical-value assertions enforce the post-edit `ready: false` state programmatically.
- The T-20260429-02 ticket's parser-route classification table rows (`Supported as <kind>` / `Supported (parked)` for `command_approval`, `file_change`, `request_user_input`) MUST be tagged `legacy-parser-route-vocabulary`. The T-20260429-02 ticket's acceptance-criterion language about "supported handling" / "Supported methods retain regression coverage" is also `legacy-parser-route-vocabulary`.
- The May-1 probe-plan vocabulary definitions of `supported` / `unsupported` / `unknown` / `unparseable` (≈lines 666-672 of `2026-05-01-codex-app-server-server-request-envelope-probe-plan.md`) MUST be tagged `legacy-parser-route-vocabulary`.
- The May-1 probe-plan's `architecture_spec_readiness_delta` template wording at lines ≈112, 135, 141 of `2026-05-01-codex-app-server-server-request-envelope-probe-plan.md` (and the analogous template lines in the materialized-thread and scratch-home probe plans) define the readiness-delta vocabulary itself. They are `legacy-parser-route-vocabulary` (vocabulary definition, not a fresh response-shape claim) and remain untouched.

Stop conditions:

- If the sweep surfaces additional `interpretive-overclaim` sites this plan does not enumerate, fire the "pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition.
- A match that classifies as `legacy-parser-route-vocabulary` does NOT fire the stop condition. The classification depends on context, not on the matched word — re-read the Bounding `legacy-parser-route-vocabulary` vs `interpretive-overclaim` rules above before classifying borderline matches.

- [ ] **Step 1.2: Confirm `_resolve_available_decisions` semantics.**

Read `packages/plugins/codex-collaboration/server/approval_router.py:90-115`. Verify the all-strings condition is `isinstance(wire_value, list) and all(isinstance(decision, str) for decision in wire_value)`. Locate `_AVAILABLE_DECISIONS` (likely defined elsewhere in the same file) and capture its `command_approval` tuple contents verbatim — this string set lands in Task 2's replacement wording.

- [ ] **Step 1.3: Confirm rebaseline-plan framing.**

Read `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:895-925`. Note the exact phrasing: "decision-shape lossy", "structured `acceptWithExecpolicyAmendment`", "the live request offered `cancel` but not `decline`", "lossless parser/response branch". The diagnostic's corrected wording in Task 2 mirrors this language to keep the doc set internally consistent.

- [ ] **Step 1.4: Determine sibling-JSON disposition.**

Check whether `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` exists.

If it does not exist → Task 3 is a no-op; record this for Task 6's commit message.

If it exists, run validation and search as separate commands so an invalid-JSON failure cannot collapse into a no-matches result:

```bash
# Validate first; abort and surface if non-zero exit.
jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json >/dev/null

# Then search the validated file for overclaim paths.
rg -n -i "supported|preserved|ready_to_close_ticket|local_compatibility|supported_methods|proves compatibility|compatibility for the observed|architecture_spec_readiness_delta|newly_satisfied_items|parseable against" \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Three known overclaim paths in the JSON (verified at orientation; reconfirm exact paths here):

- `observed_server_requests[0].local_compatibility: "supported"` (≈line 904)
- `compatibility_classification.supported_methods: ["item/commandExecution/requestApproval"]` (≈line 913)
- `architecture_spec_readiness_delta` block (≈lines 45580-45591), specifically `architecture_spec_readiness_delta.ready: true` (≈line 45581) and `architecture_spec_readiness_delta.newly_satisfied_items[2]` ("The observed item/commandExecution/requestApproval envelope is parseable against the current local compatibility boundary." — ≈line 45585). Note: this third site is the JSON parallel of the diagnostic `.md` "Architecture Spec Readiness Delta" section at lines 189-202; the parallel was missed in the cycle 1-3 plan and added in cycle 4. The `.ready: true` boolean is the strongest remaining JSON overclaim under rebaseline vocabulary — a worker patching only the first two enumerated paths leaves the readiness assertion standing.

All three are in scope for Task 3's in-place correction. If the sweep surfaces additional overclaim paths within this same JSON file beyond these three, the default is to STOP and surface. The narrow exception: if the additional path is unambiguously the same kind of claim (a binary `supported_methods`-style listing, `preserved: true` for `availableDecisions`, `ready_to_close_ticket: true` for command-approval, or `ready: true` / "parseable against" readiness assertion), record it for Task 3; otherwise fire the stop condition.

**JSON disposition rationale (simplified from preserve-and-add).** The diagnostic JSON is a repo-internal artifact with no literal-path-based production consumers (Task 1.4 verifies via filename search). Git history preserves the prior vocabulary. In-place correction — including a key-set change to the `compatibility_classification` block — is proportional to the risk: no code references this file by path. The vocabulary succession is documented in the commit message and the Markdown diagnostic's corrected wording.

**Consumer discovery (confirming check).**

Run:

```bash
rg -n -i --hidden --glob '!.git/**' \
   "codex-app-server-server-request-envelope-probes\\.json" \
   --type-not md
```

Expected: zero literal-path-based production consumers (code under `packages/`, `scripts/`, `.claude/hooks/`, `extensions/` that reads this JSON file by path). This search proves no code references the file directly; it does not prove the absence of consumers that discover the file indirectly or share its field vocabulary without a path reference. Peer diagnostic JSONs containing the same field names as their own data are NOT consumers. If a production consumer IS found → fire the "JSON correction is unsafe" stop condition. Otherwise, record "no literal-path-based production consumer at this revision" and proceed.

**Derive raw-evidence projection paths.**

The plan asserts that the JSON's raw-observation fields must remain unchanged. To enforce this, Step 3.2 saves a pre-edit projection and Step 3.5 diffs against a post-edit projection — empty diff confirms raw evidence is preserved.

The exact `jq` projection MUST be derived against the live JSON during this step. Re-read the JSON's structure and confirm that each projected path (a) exists and (b) is a raw-observation field, NOT a classification field that this plan mutates. Record the final projection for Steps 3.2 and 3.5.

Paths to INCLUDE: top-level identification metadata, envelope captures inside `observed_server_requests[*]` (`method`, `params_keys`, `redacted_envelope_summary`, `available_decisions`), the entire `.probes` array, schema-visible method listings, scratch environment metadata, trigger command, modified-paths arrays.

Paths to EXCLUDE (classification fields that will be mutated): `compatibility_classification`, `local_compatibility`, `architecture_spec_readiness_delta`, and any sibling `*_notes` arrays that are authored interpretations rather than captured observations.

**Temp-file path convention.** Deterministic paths under `/private/tmp`:

- `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json` — pre-edit projection snapshot.
- `/private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json` — post-edit projection snapshot.

Task 3 implements in-place interpretive correction using the consumer-discovery findings and raw-evidence projection derived here.

- [ ] **Step 1.5: Determine register-annotation need AND prove "landed on `main`" with git evidence.**

Sub-step 1.5a — register inspection.

Read `docs/status/codex-collaboration-reconciliation-register.md:9-70`. Check:

- Does the priority `#1` line at ~line 52 still say "Implement `T-20260429-01` Phase 1 sandbox carve-outs"?
- Does the `T-20260429-01` row "Current truth" cell at ~line 67 still describe the work as unlanded?
- Does the `T-20260429-01` row "Exit condition" cell at ~line 67 still say "Land the Phase 1 sandbox carve-outs and validate via a comparable smoke run..."?

If all three already reflect landed-implementation status (priority line names closure-evidence work, current truth records implementation has landed, exit condition names AC #1-#3 closure work) → Task 4 is a no-op. Skip it; do not edit the register.

If any still imply implementation is pending → Task 4 will land annotations on the affected cells.

Sub-step 1.5b — git proof for "landed on `main`".

Before Task 4 writes "have landed on `main`" into the register, prove the claim with git evidence. First, verify remote freshness:

```bash
git fetch --dry-run 2>&1
git rev-parse main
git rev-parse origin/main
```

If `main` and `origin/main` diverge: run `git fetch origin main` and recheck. If still divergent, skip Task 4 (local `main` may have unpushed or stale state; the "landed on `main`" annotation would be unreliable). Do NOT block Tasks 2, 3, 5, or 6 — they are purely local doc edits.

Then two checks must both pass:

1. **This branch has not modified `runtime.py`** (so reading the current branch's file is equivalent to reading `main`'s):

```bash
git diff main..HEAD -- packages/plugins/codex-collaboration/server/runtime.py
```

Expected: empty output. If the diff is non-empty, this branch HAS modified `runtime.py` and the assumption that current-branch reads stand in for `main` reads is wrong; surface to user before continuing.

2. **`main` carries the carve-outs** (so the register annotation is grounded). Use a content-aware search rather than a fixed line-range extraction:

```bash
git show main:packages/plugins/codex-collaboration/server/runtime.py | rg -n "codex|agents|worktrees|build_workspace_write_sandbox_policy"
```

Expected: output shows the `build_workspace_write_sandbox_policy` carve-outs (`~/.codex/memories`, `~/.codex/plugins/cache`, `~/.agents/skills`, `~/.agents/plugins`, plus dynamic gitdir resolution) with their line numbers. Three outcomes:

- **Carve-outs visible at lines 107-118** → record "readable-roots append at lines 107-118." Also record the dynamic gitdir resolver line range (search for `resolve_git_dir` or the gitdir-resolution logic, typically earlier in the file around lines 28-60). Proceed.
- **Carve-outs visible but at different line numbers** (line drift) → record the actual readable-roots line range AND the actual gitdir resolver line range, update ALL `runtime.py:107-118` references in Task 4 (Step 4.2's annotation, Step 4.3's priority-line replacement text, AND Step 4.4's exit-condition replacement text) to reference the correct lines, and proceed. This is NOT a stop-condition failure; the implementation landed, only the line reference drifted.
- **Zero matches** (implementation not landed, or `git diff main..HEAD` is non-empty for `runtime.py`) → fire the "Register-annotation `main`-truth check failed" stop condition. Skip Task 4 only (do NOT block Tasks 2, 3, 5, or 6); surface so the register-annotation premise can be reconciled in a separate follow-up. (Distinct from "Live envelope evidence has changed" — the envelope is unchanged; the failure is about `main`'s `runtime.py` state diverging from what Task 4's annotation would claim.)

Record all three values: (a) diff empty or not, (b) readable-roots append line range on `main`, (c) gitdir resolver line range on `main`. Task 4.2's wording depends on (a) and (b) — without them, "landed on `main`" is an unverified claim. The gitdir range (c) ensures the annotation cites both the structural validation and the append site.

- [ ] **Step 1.6: Confirm closure evidence is genuinely missing.**

Read `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:212-230`. Confirm:

- Acceptance criterion #1 (smoke with avoidable sandbox-friction escalations ≤2) is unchecked.
- Acceptance criterion #2 (credential-boundary probe) is unchecked.
- Acceptance criterion #3 (test-suite pass with updated regression assertion) is unchecked.
- Acceptance criterion #4 (Option F documented as upstream limitation) is checked.

If any of #1-#3 is now checked → recheck the register and adjust Task 4's wording.

(No commit at the end of Task 1 — this is discovery only. Task 1 outputs feed Tasks 2-4.)

---

### Task 2: Patch envelope-probe diagnostic `.md`

**Files:**

- Modify: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` (overclaim sites at ≈line 112; ≈lines 169-174; ≈lines 176-181; ≈line 185; and the "Architecture Spec Readiness Delta" section at ≈lines 189-202 — the fifth site is the cycle-4 addition that mirrors the JSON `architecture_spec_readiness_delta` block patched in Task 3; all reconfirmed in Task 1.1).

- [ ] **Step 2.1: Replace the classification line.**

Old:

```
- local compatibility classification: `supported`
```

New:

```
- local compatibility classification: parser-kind compatible but decision-shape lossy under the observed `availableDecisions`. The mixed-list entry `acceptWithExecpolicyAmendment` triggers the all-strings fallback in `_resolve_available_decisions` (`packages/plugins/codex-collaboration/server/approval_router.py:103-111`); see `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` "Command Approval Decision-Shape Boundary" for the lossless-branch forward path.
```

If Task 1.3 surfaced an exact phrase from the rebaseline plan that should win over this draft, use the plan's phrase verbatim and adjust the surrounding sentence to fit.

- [ ] **Step 2.2: Replace the "Local compatibility judgment" bullet block.**

Old (verified excerpt — match against Task 1.1's enumerated text):

```
- `approval_router.py` maps `item/commandExecution/requestApproval` to `kind="command_approval"`
- the parser requires `id`, `method`, `params`, `itemId`, `threadId`, and `turnId`
- the live envelope includes all of those fields
- `availableDecisions` is also present and preserved
```

New:

```
- `approval_router.py` maps `item/commandExecution/requestApproval` to `kind="command_approval"`
- the parser requires `id`, `method`, `params`, `itemId`, `threadId`, and `turnId`
- the live envelope includes all of those fields
- `availableDecisions` is present on the wire (see "Observed Server Requests" above), but `_resolve_available_decisions` (`approval_router.py:103-111`) preserves the wire list only when every entry is a `str`. The observed mixed list contains a structured `acceptWithExecpolicyAmendment` entry, so the parser falls back to `_AVAILABLE_DECISIONS[command_approval]` = `("accept", "acceptForSession", "acceptWithExecpolicyAmendment", "applyNetworkPolicyAmendment", "decline", "cancel")`. The fallback preserves `accept` and `cancel` (the string entries on the wire), collapses the wire's structured `acceptWithExecpolicyAmendment` object into a bare string of the same name (the payload — execpolicy amendment details — is dropped), and adds three decisions never offered by the wire (`acceptForSession`, `applyNetworkPolicyAmendment`, `decline`). Decision-shape preservation is therefore lossy in two directions — payload loss for the structured entry, plus spurious-decision addition — and command-approval response compatibility is not established. See `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` "Command Approval Decision-Shape Boundary" for the lossless-branch forward path.
```

(Task 1.2's captured `_AVAILABLE_DECISIONS[command_approval]` tuple may be inserted parenthetically if it improves clarity; keep the bullet readable. If Step 1.2's captured tuple differs from the values shown above, use Step 1.2's live capture and adjust the fallback explanation to match.)

- [ ] **Step 2.3: Replace the "Compatibility result" block (≈lines 176-181).**

Old (verified excerpt — match against Task 1.1's enumerated text):

```
Compatibility result:

- observed supported methods: `item/commandExecution/requestApproval`
- observed unsupported methods: none
- observed unknown or unparseable methods: none
- missing required fields: none
```

New:

```
Compatibility result:

- observed parser-kind compatible methods: `item/commandExecution/requestApproval` (decision-shape lossy under the observed `availableDecisions`; see "Local compatibility judgment" above)
- observed methods proven fully supported (parser-kind AND response-shape): none
- observed unsupported methods: none
- observed unknown or unparseable methods: none
- missing required fields: none
```

Rationale: the old "supported" bullet collapsed parser-kind compatibility with response-shape compatibility. The replacement separates them and explicitly records that this packet establishes the former but not the latter for any method.

- [ ] **Step 2.4: Replace the "Important limit" first sentence (≈line 185).**

Old (verified excerpt — patch only the first sentence; leave the second sentence about other methods intact):

```
This packet proves compatibility for the observed command-approval envelope only. It does not prove live reachability or parser cleanliness for file-change, permission, tool-input, MCP elicitation, auth-refresh, or other schema-visible server-request methods.
```

New:

```
This packet supports a parser-kind compatibility inference for the observed command-approval envelope — the required correlation fields (`itemId`, `threadId`, `turnId`) and JSON-RPC `id` are present, and `approval_router.py` maps `item/commandExecution/requestApproval` to `kind=command_approval`. It does not establish response-shape compatibility — the observed mixed `availableDecisions` triggers parser fallback per `_resolve_available_decisions` (see "Local compatibility judgment" above). It does not prove live reachability or parser cleanliness for file-change, permission, tool-input, MCP elicitation, auth-refresh, or other schema-visible server-request methods.
```

Rationale for "supports a parser-kind compatibility inference" over "proves parser-kind compatibility (envelope parsing succeeds...)": the diagnostic evidence records static field presence in the captured envelope, not an actual replay through `parse_pending_server_request`. Field presence supports the inference that parsing would succeed; it does not constitute execution evidence. The distinction matters because a future parser change (new required field, type validation, etc.) could invalidate the inference while the captured evidence remains unchanged.

Preserve the paragraph immediately after this sentence ("It also does not collapse fail-closed behavior into 'clean lifecycle semantics'…") unchanged unless it now contradicts the corrected first sentence — in which case patch only the contradicting clause.

- [ ] **Step 2.5: Replace the "Architecture Spec Readiness Delta" section (≈lines 189-202; cycle-4 addition).**

This section was missed by the cycle 1-3 plan and added in cycle 4. It mirrors the canonical-key parallel overclaim that the JSON `architecture_spec_readiness_delta` block (Task 3 Step 3.3 items 7-8) carries: both assert architecture-spec readiness without naming the decision-shape lossiness as a remaining response-semantics blocker.

Old (verified excerpt — match against Task 1.1's enumerated text; preserve the section header and the first two "Newly satisfied items" bullets verbatim):

```
## Architecture Spec Readiness Delta

Newly satisfied items:

- scratch auth was established under isolated `CODEX_HOME` without credential copying
- a live schema-visible server-request envelope was captured and redacted safely
- the observed `item/commandExecution/requestApproval` envelope is parseable against the current local compatibility boundary

Still missing:

- coverage for other schema-visible server-request methods
- runtime evidence for unknown / unsupported envelope handling under live conditions

The architecture spec can proceed only if it scopes server-request support to the observed methods and keeps unobserved methods as explicit risks.
```

New:

```
## Architecture Spec Readiness Delta

Newly satisfied items:

- scratch auth was established under isolated `CODEX_HOME` without credential copying
- a live schema-visible server-request envelope was captured and redacted safely
- the observed `item/commandExecution/requestApproval` envelope is inferred to be parseable via the parser's decision-shape-lossy fallback path; lossless preservation of `availableDecisions` is NOT established (see "Local compatibility judgment" above)

Still missing:

- coverage for other schema-visible server-request methods
- runtime evidence for unknown / unsupported envelope handling under live conditions
- a lossless parser/response branch for command-approval that preserves `availableDecisions` shape without falling back to `_AVAILABLE_DECISIONS[command_approval]` (see `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` "Command Approval Decision-Shape Boundary")

The architecture spec can proceed only if it explicitly carries the decision-shape-lossy fallback as an unresolved response-semantics risk for command-approval (alongside the unobserved-method risks named above) — not as proven support. Scoping "support" to the observed method without that qualification would smuggle response-shape compatibility into the architecture's foundational assumptions; the parser's actual behavior at `approval_router.py:103-111` does not justify it.
```

Rationale: bullet 3 of "Newly satisfied items" previously asserted parseability without qualification — under May-1 vocabulary, "parseable" meant the parser produced a representation; under rebaseline vocabulary, it implies response-shape compatibility, which is exactly what the parser fallback breaks. The patched bullet retains the historical "parseable" finding but qualifies it as decision-shape lossy. The "Still missing" list grows to name the lossless parser/response branch as a remaining requirement (third bullet). The closing sentence's "scope server-request support to the observed methods" framing was the strongest remaining `.md` overclaim in the diagnostic — under rebaseline truth, the only observed method is decision-shape lossy, so "scoping support to it" smuggles the response-shape claim. The replacement reframes the proceed-conditional around explicit lossy-fallback risk rather than scoping support.

- [ ] **Step 2.6: Re-read the surrounding "Compatibility Classification", "Important limit", "Architecture Spec Readiness Delta", and "Remaining Blockers" sections post-edit.**

Look for downstream sentences that paraphrase the now-corrected bullets or sentences. If a summary sentence still says "supported" or "preserved" or "proves compatibility" or "parseable against" or "architecture spec can proceed" without qualification, patch it to match. If a section ends with a "ticket effect" / "next step" line that follows from the old wording, ensure it now follows from the new wording. Pay particular attention to the "Remaining Blockers" section that follows the Architecture Spec Readiness Delta (≈lines 204-208 pre-edit): blocker #1 ("Only `item/commandExecution/requestApproval` has live envelope evidence") may now read as if response-shape compatibility for that method is established; consider adding a parenthetical qualifier or a new blocker line naming the decision-shape lossiness as a remaining response-semantics blocker — but only if the existing wording would otherwise paraphrase a now-corrected upstream claim.

- [ ] **Step 2.7: Local rg verification of the modified file.**

```bash
rg -n -i "supported|preserved|proves compatibility|compatibility for the observed|architecture spec can proceed|parseable against|architecture_spec_readiness_delta|architecture spec readiness delta|newly_satisfied_items" \
   docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
```

Expected: every match falls into raw-observation, the new qualified wording, or unrelated. No bare "supported" classification of command-approval. No bare "preserved" claim about `availableDecisions`. No "proves compatibility" assertion for command-approval response semantics. No bare "parseable against the current local compatibility boundary" without the decision-shape-lossy qualification. No "architecture spec can proceed only if it scopes server-request support to the observed methods" without the lossy-fallback risk reframing. If a surviving overclaim appears, return to Step 2.6.

- [ ] **Step 2.7b: Markdown raw-facts preservation check (scrutiny follow-up 5).**

Step 2.7's `rg` sweep verifies no surviving overclaim wording, but cannot detect accidental mutation of the raw-evidence layer in the `.md` file. This step spot-checks the six most distinctive raw-observation anchors to confirm they survived the interpretive-layer patches unchanged.

**Anchor derivation rule:** All anchors must be strings that exist in the PRE-EDIT `.md` file (i.e., at `HEAD` before any Task 2 edits). An anchor that only exists because Task 2's interpretive patches introduce it is a false positive — it tests new prose survival, not raw-evidence preservation. Verify each anchor against the pre-edit file before relying on it.

```bash
# Each grep must exit 0 (pattern found). Run all six; any non-zero exit means a raw fact was mutated.
grep -qF 'item/commandExecution/requestApproval' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF 'proposedExecpolicyAmendment' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF 'availableDecisions' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF '/bin/zsh -lc' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF 'No approval response was sent' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF 'itemId' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
```

Expected: all six exit `0`. These anchors correspond to:
- The observed method string (`item/commandExecution/requestApproval`)
- A raw params key from the envelope (`proposedExecpolicyAmendment` — appears at `.md` lines 121 and 138 as a raw observation; NOT introduced by Task 2's interpretive patches)
- The wire field name (`availableDecisions`)
- The trigger command (`/bin/zsh -lc`)
- The response-absence record (`No approval response was sent`)
- A required correlation field (`itemId`)

Why `proposedExecpolicyAmendment` replaces the prior `"acceptWithExecpolicyAmendment"` anchor: `acceptWithExecpolicyAmendment` does NOT appear anywhere in the pre-edit `.md` file — it exists only in the sibling JSON (as raw evidence) and in the delegate-execution diagnostic. The old anchor would have passed only because Task 2's new interpretive prose introduces the string, not because raw observation text was preserved. `proposedExecpolicyAmendment` is a raw params key observed at `.md` lines 121 and 138, present in the pre-edit file.

If any anchor is missing, a Task 2 edit accidentally removed or altered a raw-observation line. Revert the offending edit (check `git diff` for the specific change), re-apply the interpretive-layer patch only, and re-run Steps 2.7 and 2.7b.

Note: this is a spot-check, not a byte-identical diff of the full raw-evidence layer (the `.md` mixes raw observations and interpretive text in the same document, unlike the JSON where `jq` projection cleanly separates them). The six anchors cover the most distinctive raw facts from the "Raw Envelope Facts To Preserve" enumeration; the full `rg` sweep in Step 2.7 provides additional coverage by surfacing any line that mentions these terms in unexpected context. However, three of the six anchors (`item/commandExecution/requestApproval`, `availableDecisions`, `itemId`) also appear in the replacement interpretive prose from Steps 2.1-2.5 — a deleted raw line containing only one of those terms would still pass the anchor check. The `git diff` hunk review below closes this gap.

Additionally, verify that Task 2's edits are confined to the five enumerated overclaim sites by reviewing the `git diff` output:

```bash
git diff docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
```

Inspect each hunk header (`@@` line). Every changed hunk must correspond to one of the five overclaim sites (classification line ≈112, "Local compatibility judgment" bullets ≈169-174, "Compatibility result" block ≈176-181, "Important limit" sentence ≈185, "Architecture Spec Readiness Delta" section ≈189-202) or to downstream text patched in Step 2.6. If any hunk modifies lines in the raw observation sections (the "Observed Server Requests" table, the params keys list, the redacted envelope summary, the trigger command, or the response-absence record), that is a raw-evidence mutation — revert the offending hunk, re-apply only the interpretive-layer patch, and re-run Steps 2.7 and 2.7b.

- [ ] **Step 2.8: Stage the `.md` change.**

```bash
git add docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
```

(Commit happens once in Task 6, after Task 3 and Task 4 conditional changes are also staged.)

---

### Task 3: Reconcile sibling JSON

**Files:**

- Conditional Modify: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`. Skip entirely if Task 1.4 found JSON does not exist or has no parallel overclaim.

- [ ] **Step 3.1: Branch on the Task 1.4 disposition.**

| Task 1.4 outcome | This task |
|---|---|
| JSON does not exist | Skip to Task 4. |
| JSON exists, no parallel overclaim | Skip to Task 4. |
| JSON exists, has parallel overclaim, zero consumers | Step 3.2 → Step 3.3 → Steps 3.4-3.6. |
| Consumer found (stop condition fired) | Surface to user. |

- [ ] **Step 3.2: Capture pre-edit raw-evidence projection (only if Step 3.3 will run).**

Run before any JSON edits:

```bash
# Guard: if a pre-edit snapshot already exists, a prior partial run may have
# mutated the worktree. Investigate before overwriting.
test ! -e /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json \
  || { echo "STOP: projection snapshot already exists — prior partial run?" >&2; exit 1; }

# Extract raw-evidence projection (using the jq filter derived in Task 1.4)
jq '<projection from Task 1.4>' \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json \
   > /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json
```

If the guard fires: check `git diff --stat docs/diagnostics/codex-app-server-server-request-envelope-probes.json`. If the worktree matches HEAD, `trash` the temp file and re-run. If it shows Step 3.3-shaped mutations, restore from HEAD (`git restore --source=HEAD -- docs/diagnostics/codex-app-server-server-request-envelope-probes.json`), `trash` the temp file, and re-run.

Expected: extraction exits `0` and the temp file contains valid JSON.

- [ ] **Step 3.3: Apply in-place interpretive correction (only if Step 3.2 ran).**

Mutate the three classification fields in place. No migration scaffolding — no `_legacy_*` renaming, no `classification_vocabulary` markers, no dual-shape blocks. The `compatibility_classification` block undergoes a key-set change (old keys removed, rebaseline-vocabulary keys added); this is a schema-shape change justified by no literal-path-based production consumers. Git history preserves the prior vocabulary.

After all edits, raw-observation fields (params keys, redacted envelope summary, observed `availableDecisions` array, schema-visible methods listing, per-probe pass/fail rows, etc.) must remain unchanged. Step 3.5 enforces this programmatically.

Editing method: use the Edit tool with enough surrounding context (minimum 3-5 lines of unchanged JSON above and below). After EACH edit, run `jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json > /dev/null` to confirm valid JSON syntax. This file is ~45,600 lines — syntax errors cascade fast.

**Three correction sites:**

1. **`observed_server_requests[0].local_compatibility`** (≈line 904). Change value from `"supported"` to `"parser_kind_compatible_decision_shape_lossy"`.

2. **`compatibility_classification`** (≈line 911). Replace the block's contents:

   ```json
   "compatibility_classification": {
     "status": "parser_kind_compatible_decision_shape_lossy",
     "fully_supported_methods": [],
     "parser_kind_compatible_methods": ["item/commandExecution/requestApproval"],
     "decision_shape_lossy_methods": ["item/commandExecution/requestApproval"],
     "unsupported_methods": [],
     "unknown_or_unparseable_methods": [],
     "missing_required_fields": [],
     "notes": [
       "item/commandExecution/requestApproval is parser-kind compatible (route exists, required correlation fields itemId/threadId/turnId present) but decision-shape lossy under the observed mixed availableDecisions: the structured acceptWithExecpolicyAmendment entry triggers the all-strings fallback in _resolve_available_decisions (approval_router.py:103-111). The fallback tuple _AVAILABLE_DECISIONS[command_approval] = ('accept', 'acceptForSession', 'acceptWithExecpolicyAmendment', 'applyNetworkPolicyAmendment', 'decline', 'cancel') preserves the wire's accept and cancel, collapses the structured acceptWithExecpolicyAmendment entry into a bare string (payload dropped), and adds three decisions never offered by the wire (acceptForSession, applyNetworkPolicyAmendment, decline).",
       "Prior classification under May-1 parser-route vocabulary was 'supported' (meaning: local code has a concrete route for the method and required correlation fields are present). That classification was internally consistent under its narrower vocabulary but overclaimed under rebaseline vocabulary which requires response-shape compatibility.",
       "The status field previously carried probe-pass/fail semantics ('passed' meaning the compatibility probe completed without error). Under rebaseline vocabulary it carries a classification label describing the parser's actual compatibility characteristics. Readers querying .compatibility_classification.status should expect a classification string, not a binary pass/fail value."
     ]
   }
   ```

   (The `notes` array's second entry documents the vocabulary succession inline, replacing the need for external migration metadata. Re-read the live JSON during execution and confirm the exact surrounding structure before editing.)

3. **`architecture_spec_readiness_delta`** (≈line 45580). Replace the block's contents:

   ```json
   "architecture_spec_readiness_delta": {
     "ready": false,
     "newly_satisfied_items": [
       "Scratch auth was established under isolated CODEX_HOME without credential copying.",
       "A live schema-visible server-request envelope was captured and redacted safely.",
       "The observed item/commandExecution/requestApproval envelope is inferred to be parseable via the parser's decision-shape-lossy fallback path; lossless preservation of availableDecisions is NOT established."
     ],
     "still_missing_items": [
       "Envelope coverage for other schema-visible server-request methods remains unobserved and should be carried as explicit risk if relied upon.",
       "Fail-closed lifecycle cleanliness for unsupported or unknown methods remains a separate runtime-quality concern.",
       "A lossless parser/response branch for command-approval that preserves availableDecisions shape without falling back to _AVAILABLE_DECISIONS[command_approval] (see docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md 'Command Approval Decision-Shape Boundary')."
     ],
     "notes": [
       "ready=false because command-approval response semantics are not proven: _resolve_available_decisions (approval_router.py:103-111) falls back to _AVAILABLE_DECISIONS[command_approval] under the observed mixed availableDecisions. Prior classification under May-1 parser-route vocabulary was ready=true (meaning: parser route exists and required correlation fields present). That was internally consistent under its narrower vocabulary but overclaimed under rebaseline vocabulary which requires response-shape compatibility.",
       "The architecture spec can proceed only if it explicitly carries the decision-shape-lossy fallback as an unresolved response-semantics risk for command-approval."
     ]
   }
   ```

4. **Any field claiming `availableDecisions` is `preserved: true`** (if surfaced in Task 1.4 sweep): change to `"preserved": false` with a note naming the all-strings fallback.

5. **Any field flagged `ready_to_close_ticket: true` for command-approval** (if surfaced): change to `false`.

Do not delete or rewrite raw observation fields.

**`local_compatibility_notes` left unchanged.** The `observed_server_requests[0].local_compatibility_notes` field (if present) describes the parser boundary and routing behavior, not response-shape support. It does not overclaim response-shape compatibility and is therefore not a correction target. If a worker encounters notes text that does overclaim (e.g., "fully compatible," "preserves availableDecisions"), surface it as an additional correction site rather than silently passing.

- [ ] **Step 3.4: Validate JSON syntax.**

```bash
jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json >/dev/null
```

Expected: exit `0`. If non-zero, fix the JSON before proceeding.

- [ ] **Step 3.5: Post-edit raw-evidence diff.**

Re-extract the same projection from the post-edit JSON and diff:

```bash
jq '<projection from Task 1.4>' \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json \
   > /private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json

diff -u /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json \
        /private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json
```

Expected: `diff` exits `0` (empty output). Raw-observation fields are unchanged.

- **Diff is empty** → raw evidence preserved. Delete temp files (`trash /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json /private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json`). Proceed to Step 3.5b.
- **Diff is non-empty** → Step 3.3 mutated a raw-observation field. Surface the specific path and revert. Do NOT stage.

- [ ] **Step 3.5b: Canonical-value assertions.**

```bash
jq -e '.architecture_spec_readiness_delta.ready == false' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.observed_server_requests[0].local_compatibility == "parser_kind_compatible_decision_shape_lossy"' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.compatibility_classification.status == "parser_kind_compatible_decision_shape_lossy"' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.compatibility_classification.fully_supported_methods == []' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.compatibility_classification.parser_kind_compatible_methods == ["item/commandExecution/requestApproval"]' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.compatibility_classification.decision_shape_lossy_methods == ["item/commandExecution/requestApproval"]' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.architecture_spec_readiness_delta.still_missing_items | length >= 3' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.architecture_spec_readiness_delta.still_missing_items | any(test("lossless parser/response branch"))' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected: all eight assertions exit `0`. If any fails, the interpretive correction in Step 3.3 is incomplete — fix and re-run from Step 3.5.

- [ ] **Step 3.6: Stage the JSON change (only if Steps 3.5 + 3.5b passed).**

```bash
git add docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

---

### Task 4: Optional reconciliation-register annotation

**Files:**

- Conditional Modify: `docs/status/codex-collaboration-reconciliation-register.md`. Skip entirely if Task 1.5a found the register already reflects landed-implementation status across priority line, Current truth cell, AND Exit condition cell.

- [ ] **Step 4.1: Branch on the Task 1.5 disposition.**

| Task 1.5a outcome | This task |
|---|---|
| Register already reflects landed-implementation across priority line, current truth, AND exit condition | Skip to Task 5. |
| Any of priority line, current truth, or exit condition still implies implementation is pending | Step 4.2. |

Sub-step 4.1a — confirm git proof. Verify Task 1.5b's git checks were performed and both passed (empty diff against `main`, lines 107-118 on `main` show the carve-outs). If not yet performed, run them now before any register edit. The Step 4.2 / 4.3 / 4.4 wording asserts "landed on `main`" — that assertion is unsupported without the git proof.

- [ ] **Step 4.2: Append "Current truth" annotation to the T-20260429-01 row (≈line 67).**

Append to the existing "Current truth" cell — do not replace the existing text:

```
As of 2026-05-09, Phase 1 sandbox carve-outs (Options B + E + ~/.agents/ + dynamic gitdir) have landed on `main` (`packages/plugins/codex-collaboration/server/runtime.py` — readable-roots append at lines <Step-1.5b-actual-lines>, dynamic gitdir resolver at lines <Step-1.5b-gitdir-lines>; replace both placeholders with the actual line ranges recorded in Step 1.5b). Closure evidence remains missing for ticket acceptance criteria #1 (comparable `/delegate` smoke with avoidable sandbox-friction escalations ≤2), #2 (credential-boundary probe), and #3 (`test_runtime.py` regression assertion updated and full codex-collaboration test suite passing). Acceptance criterion #4 (Option F upstream limitation) is already checked. The ticket therefore remains open; the work shape changes from "implement" to "record closure evidence and close."
```

- [ ] **Step 4.3: Replace the priority `#1` line (≈line 52).**

Old:

```
1. Implement `T-20260429-01` Phase 1 sandbox carve-outs (Options B + E) and
   validate via a comparable `/delegate` smoke with avoidable sandbox-friction
   escalations <=2. Count legitimate operator-gated approvals separately.
```

New:

```
1. Close `T-20260429-01` by recording closure evidence for the three
   unchecked acceptance criteria: comparable `/delegate` smoke with
   avoidable sandbox-friction escalations <=2 (AC #1); credential-boundary
   probe (AC #2); `test_runtime.py` regression assertion updated and full
   codex-collaboration test suite passing (AC #3). Phase 1 implementation
   has landed on `main` (`runtime.py:107-118`). Count legitimate
   operator-gated approvals separately.
```

- [ ] **Step 4.4: Replace the T-20260429-01 row's Exit condition cell (≈line 67).**

The Exit condition cell currently asserts that Phase 1 still needs to be landed:

Old:

```
Land the Phase 1 sandbox carve-outs and validate via a comparable smoke run with avoidable sandbox-friction escalations <=2. Count legitimate operator-gated approvals separately.
```

This contradicts the Current truth cell after Step 4.2 (which records implementation has landed). Replace the cell so it names only the remaining closure evidence:

New:

```
Record closure evidence for the three unchecked acceptance criteria: AC #1 — comparable `/delegate` smoke with avoidable sandbox-friction escalations <=2 (count legitimate operator-gated approvals separately); AC #2 — credential-boundary probe; AC #3 — `test_runtime.py` regression assertion updated and full codex-collaboration test suite passing. Phase 1 implementation has landed on `main` (`runtime.py:107-118`); AC #4 (Option F upstream limitation) is already checked.
```

Rationale: appending an annotation to the Current truth cell is not enough on its own — the Exit condition cell is what readers consult to determine "what does it take to close this ticket?" Leaving "Land the Phase 1 sandbox carve-outs..." in place after annotation would have the row simultaneously assert (a) Phase 1 has landed (Current truth) and (b) Phase 1 still needs to be landed (Exit condition). That is exactly the stale-current-state contradiction this plan exists to remove.

- [ ] **Step 4.5: Local rg verification of the register.**

```bash
rg -n -i "T-20260429-01|Implement.*Phase 1|Land the Phase 1" \
   docs/status/codex-collaboration-reconciliation-register.md
```

Expected: every `T-20260429-01` line either reflects landed-implementation, names AC #1-#3 closure work, or is general Phase 1 context. No surviving "Implement `T-20260429-01` Phase 1" framing in the priority order. No surviving "Land the Phase 1 sandbox carve-outs" framing in the Exit condition cell.

Note: the register's global "Last reconciled" date at ≈line 9 is intentionally left unchanged. This patch reconciles only the T-20260429-01 row (Current truth + Exit condition cells) and priority `#1` line, not the full register; bumping the global date would overstate the scope of this commit. Row-local recency is captured by the "As of 2026-05-09" date stamp inside Step 4.2's annotation.

- [ ] **Step 4.6: Stage the register change.**

```bash
git add docs/status/codex-collaboration-reconciliation-register.md
```

---

### Task 5: Final verification sweep and rebaseline-plan reconciliation

**Files:** read-only for Steps 5.1-5.4. Step 5.5 writes to the rebaseline implementation plan (conditional). If Step 5.3 surfaces a contradiction requiring a patch to a Task 2/3/4 target file, STOP — return to the owning task, patch, re-run that task's local verification step, re-stage, then restart Task 5 from Step 5.1. Do not patch within Task 5 itself.

- [ ] **Step 5.1: Run the full sweep.**

```bash
rg -n -i "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods|architecture_spec_readiness_delta|architecture spec readiness delta|architecture spec can proceed|parseable against|newly_satisfied_items" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

- [ ] **Step 5.2: Classify matches in target files; spot-check others.**

Apply the Sweep Classification Rules from the top of this plan. Full per-line classification is mandatory for files in this plan's write set (diagnostic `.md`, diagnostic `.json`, register, rebaseline plan). For other swept files (tickets, other plans), confirm no `interpretive-overclaim` exists via spot-check. Acceptable terminal classifications:

- `raw-observation` (preserved evidence) → OK.
- `corrected-language` (post-patch wording — should now describe lossy fallback or parser-kind compatibility) → OK.
- `legacy-parser-route-vocabulary` (T-20260429-02 ticket parser-route table, May-1 probe-plan vocabulary definitions) → OK.
- `authority-source` (rebaseline plan "Command Approval Decision-Shape Boundary" section at lines 905-921; uses rebaseline-era framing, not May-1 vocabulary) → OK.
- `unrelated` (different context, e.g., "supported sandbox carve-outs") → OK.
- `peer-diagnostic-data-artifact` (sibling diagnostic JSON files containing the same field names from their own probe sessions — independent captures, not claims about the target method) → OK.

Unacceptable: `interpretive-overclaim` → STOP. Do not commit. Surface to the user with file path, line number, current text, and proposed correction.

Cross-check against the Task 1.1 baseline classification artifact at `/private/tmp/codex-collab-overclaim-fix-sweep-baseline.md`: any match that was tagged `interpretive-overclaim` in Task 1.1 must now classify as `corrected-language` or its enumerated patch site must be reflected in the staged diff. Any new `interpretive-overclaim` match (not in the Task 1.1 baseline) is a surviving overclaim regardless of cause.

- [ ] **Step 5.3: Cross-doc consistency spot-check.**

Compare line-by-line:

- Diagnostic `.md` corrected wording (Task 2) vs. rebaseline plan lines 905-921. Do they describe the same lossy fallback in compatible language?
- Diagnostic `.md` corrected wording vs. JSON disposition (Task 3). Do they agree, or does the JSON path leave the diagnostic standing alone?
- Register annotation (Task 4) vs. ticket acceptance criteria. Does the register's AC #1-#3 framing (smoke, credential-boundary probe, `test_runtime.py` regression assertion update + full-suite pass) match the ticket's checklist? AC #4 is already checked.

If any pair contradicts: STOP. Identify the owning task (Task 2 for `.md` wording, Task 3 for JSON disposition, Task 4 for register). Return to that task, patch the contradiction, re-run the task's local verification step, re-stage, then restart Task 5 from Step 5.1. Do not patch within this task.

- [ ] **Step 5.4: Confirm no code files are staged.**

```bash
git diff --cached --name-only
```

Expected: only files under `docs/diagnostics/`, optionally `docs/status/codex-collaboration-reconciliation-register.md`, optionally `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` (staged later in Step 5.5). No `packages/`, no `.claude/hooks/`, no scripts. If a code file is staged, unstage and surface.

- [ ] **Step 5.5: Reconcile the rebaseline implementation plan's evidence-check section.**

The rebaseline plan at `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:204-220` contains `jq` commands and expected-value bullets that read canonical JSON fields whose vocabulary this plan changes. After Task 3's in-place correction:

- `jq '.observed_server_requests[0] | {..., local_compatibility}'` (line 209) still extracts the field, but its value is now `"parser_kind_compatible_decision_shape_lossy"` instead of `"supported"`.
- `jq '.architecture_spec_readiness_delta'` (line 210) now returns the rebaseline-vocabulary block with `"ready": false`.

Update lines 216-219 of the rebaseline plan to reflect the new canonical values:

Old (lines 216-219):
```
- Observed method is `item/commandExecution/requestApproval`.
- `has_id`, `threadId_present`, `turnId_present`, `itemId_present`, and `schema_visible` are true.
- `local_compatibility` is `supported` in the probe summary, but this plan must refine that label to decision-shape-lossy because the raw envelope has structured `availableDecisions`.
- Server-request architecture readiness is true only with observed-method scoping.
```

New:
```
- Observed method is `item/commandExecution/requestApproval`.
- `has_id`, `threadId_present`, `turnId_present`, `itemId_present`, and `schema_visible` are true.
- `local_compatibility` is `parser_kind_compatible_decision_shape_lossy` (corrected from `"supported"` by the envelope-diagnostic overclaim fix; prior vocabulary preserved in git history). The label reflects that the parser has a route but response-shape compatibility is not established.
- `architecture_spec_readiness_delta.ready` is `false` (corrected from `true` by the envelope-diagnostic overclaim fix). Readiness is false because lossless `availableDecisions` preservation is not established for the observed command-approval envelope.
```

Stage the rebaseline plan change:

```bash
git add docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md
```

**Skip condition (state-based, not execution-based):** Skip this step if the canonical JSON fields still carry legacy vocabulary — i.e., `jq -e '.observed_server_requests[0].local_compatibility == "supported"' docs/diagnostics/codex-app-server-server-request-envelope-probes.json` exits `0` AND `jq -e '.architecture_spec_readiness_delta.ready == true' docs/diagnostics/codex-app-server-server-request-envelope-probes.json` exits `0`. In that state, the rebaseline plan's evidence-check expectations remain valid under the legacy vocabulary and no reconciliation is needed. If either check exits non-zero (canonical fields already carry rebaseline vocabulary — whether from this run's Task 3 or a prior commit), Step 5.5 MUST run to reconcile the rebaseline plan's expected-value bullets.

- [ ] **Step 5.6: Confirm Markdown consumers of changed canonical keys are reconciled.**

Run:

```bash
rg -n "local_compatibility|architecture_spec_readiness_delta" \
   docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md
```

Expected: every match either (a) appears in a `jq` command that will extract the corrected value, (b) appears in an expected-value bullet that names the corrected vocabulary, or (c) appears in the "Command Approval Decision-Shape Boundary" section (lines 905-921) which is an authority source, not a consumer of the JSON. No match should assert `local_compatibility` is `"supported"` or `architecture_spec_readiness_delta.ready` is `true` without explicit qualification that these are corrected values.

- [ ] **Step 5.7: Post-write terminal sweep.**

Step 5.1's broad sweep ran before Step 5.5 wrote to the rebaseline plan. This step confirms the new wording introduced in Step 5.5 does not itself introduce an overclaim. Run the full pattern against the rebaseline plan only (the other files are unchanged since Step 5.1):

```bash
rg -n -i "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods|architecture_spec_readiness_delta|architecture spec readiness delta|architecture spec can proceed|parseable against|newly_satisfied_items" \
   docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md
```

Classify each match per the Sweep Classification Rules. Matches from the Step 5.5 edit should classify as `corrected-language` (they describe the post-patch vocabulary). Matches from lines 905-921 ("Command Approval Decision-Shape Boundary" section) classify as `authority-source` — that section names the current decision-shape-lossy reality that this plan's corrections are grounded in; it is NOT legacy parser-route vocabulary (which would imply it uses the May-1 narrower `supported` sense). The section uses rebaseline-era framing ("decision-shape lossy", "response compatibility is not established", "lossless parser/response branch") and is one of this plan's two truth authorities (Authority Basis item 2). Matches from the "Parser-Context Mismatch Rows" section (lines 895-904) that mention parser rejection semantics for other methods are `unrelated` (different methods, different parser paths). Any `interpretive-overclaim` classification means Step 5.5's replacement text is wrong — return to Step 5.5, fix, re-stage, and re-run this step.

Skip this step if Step 5.5 was skipped.

(No commit at end of Task 5 — verification and rebaseline-plan reconciliation only. The staging in Step 5.5 is included in Task 6's commit.)

---

### Task 6: Commit

**Files:** previously staged via Steps 2.8, 3.6 (conditional), 4.6 (conditional), 5.5 (conditional — state-based, independent of whether Task 3 ran; see Step 5.5 skip condition).

- [ ] **Step 6.1: Confirm staged set.**

```bash
git status
```

Expected: only the planned docs files appear in `git status` as staged — `docs/diagnostics/` targets, optionally `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` (Task 3), optionally `docs/status/codex-collaboration-reconciliation-register.md` (Task 4), and optionally `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` (Step 5.5; state-based condition independent of Task 3 — may be staged even when Task 3 was skipped if canonical JSON fields already carry rebaseline vocabulary from a prior commit). Pre-existing unrelated unstaged changes recorded in Task 0 may still be present in the working tree; that is acceptable. Confirm only the planned docs are staged for commit.

- [ ] **Step 6.2: Commit.**

**Edit the heredoc body before running the commit command (cycle-4 template).** The body below contains three CONDITIONAL paragraphs marked with `<!-- CONDITIONAL: ... -->` and `<!-- END CONDITIONAL -->` HTML-style markers. Edit the heredoc body so that:

- For each CONDITIONAL block whose corresponding task RAN, DELETE the `<!-- CONDITIONAL: ... -->` and `<!-- END CONDITIONAL -->` marker lines and KEEP the paragraph text between them.
- For each CONDITIONAL block whose corresponding task was SKIPPED, DELETE both marker lines AND the paragraph text between them entirely.

The three CONDITIONAL blocks and their triggers:
1. **Task 3** (JSON disposition): include if Task 3 ran and Step 3.6 staged the JSON.
2. **Task 4** (register annotation): include if Task 4 ran and Step 4.6 staged the register.
3. **Step 5.5** (rebaseline plan reconciliation): include if Step 5.5 ran — this is state-based and independent of Task 3. Step 5.5 runs when canonical JSON fields carry rebaseline vocabulary (whether from this run's Task 3 or a prior commit); see Step 5.5's skip condition. It is possible for Step 5.5 to run when Task 3 was skipped.

After editing, the body should contain only the sections that match the actually-staged file set from Steps 2.8, 3.6 (conditional), 4.6 (conditional), and 5.5 (state-based conditional, independent of Task 3). The opening parser-correction paragraph and closing scope-unchanged paragraph are always retained.

After running the commit, Step 6.3's `git log -1 --format=%B HEAD` self-check confirms no `<!-- CONDITIONAL: ... -->` markers leaked into the actual commit message; if any remain, amend the commit message before pushing.

**Co-author trailer.** The trailer line shown below uses placeholders for both the model identity AND the email address. Replace both with values appropriate for the executing session (e.g., `Claude Opus 4.7 (1M context) <noreply@anthropic.com>` for Anthropic models, `gpt-5-codex <noreply@openai.com>` for OpenAI models), or omit the trailer line entirely if the executing context does not have a stable identity claim. Do not commit either placeholder (`<executing model identity>` or `<executing model email>`) as literal text.

```bash
git commit -m "$(cat <<'EOF'
docs(codex-collaboration): reconcile envelope-probe diagnostic with parser reality

The May-1 server-request envelope-probe diagnostic claimed
command-approval was `supported` and `availableDecisions` was
`preserved`. The repaired rebaseline implementation plan and
`approval_router.py:103-111` say the parser is decision-shape lossy
under the observed mixed `availableDecisions` list — the structured
`acceptWithExecpolicyAmendment` entry triggers fallback to
`_AVAILABLE_DECISIONS[command_approval]` = `("accept", "acceptForSession",
"acceptWithExecpolicyAmendment", "applyNetworkPolicyAmendment",
"decline", "cancel")`. The fallback preserves `accept` and `cancel`,
collapses the structured `acceptWithExecpolicyAmendment` into a bare
string (payload dropped), and adds `acceptForSession`,
`applyNetworkPolicyAmendment`, and `decline` (none offered by the
wire). Lossiness is bidirectional: payload loss + spurious additions.
This commit corrects the diagnostic's interpretive layer; raw
envelope observations are preserved unchanged.

<!-- CONDITIONAL: include only if Task 3 ran (JSON disposition applied; Step 3.6 staged the JSON). -->
The sibling JSON is corrected in place: `local_compatibility`
changed from `"supported"` to
`"parser_kind_compatible_decision_shape_lossy"`;
`compatibility_classification` block rewritten with rebaseline
vocabulary (`fully_supported_methods: []`,
`parser_kind_compatible_methods` and `decision_shape_lossy_methods`
enumerate the method explicitly);
`architecture_spec_readiness_delta.ready` changed from `true` to
`false` with the lossy fallback named in `still_missing_items`.
Zero production consumers of this internal diagnostic JSON
confirmed at commit time. Pre/post jq-projection verified
byte-identical raw-evidence preservation. Prior vocabulary
preserved in git history.
<!-- END CONDITIONAL -->

<!-- CONDITIONAL: include only if Step 5.5 ran (rebaseline plan reconciled; state-based, independent of Task 3). -->
The rebaseline implementation plan's evidence-check section
(lines 204-220) is updated so its `jq` expected-value bullets
reflect the new canonical vocabulary — without this, a future
worker would hit a false evidence mismatch.
<!-- END CONDITIONAL -->

<!-- CONDITIONAL: include only if Task 4 ran (register annotation applied; Step 4.6 staged the register). -->
Optional register annotation records that T-20260429-01
Phase 1 implementation has landed on main; the T-20260429-01 row
Exit condition cell is replaced so it names AC #1-#3 closure work
only (comparable `/delegate` smoke with avoidable sandbox-friction
escalations <=2; credential-boundary probe; `test_runtime.py`
regression assertion update + full codex-collaboration suite pass).
AC #4 (Option F upstream limitation) is already checked.
<!-- END CONDITIONAL -->

T-20260429-02 method-by-method classification scope is unchanged
and not addressed here. The T-20260429-02 ticket's parser-route
"Supported as <kind>" / "Supported (parked)" wording is May-1
legacy parser-route vocabulary and remains untouched.

Co-Authored-By: <executing model identity, e.g., Claude Opus 4.7 (1M context)> <executing model email, e.g., noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6.3: Confirm commit landed cleanly.**

```bash
git status
git log -1 --stat
git log -1 --format=%B HEAD | grep -F "<!-- CONDITIONAL" || echo "OK: no conditional markers leaked"
git log -1 --format=%B HEAD | grep -F "<executing model identity" || echo "OK: no co-author identity placeholder leaked"
git log -1 --format=%B HEAD | grep -F "<executing model email" || echo "OK: no co-author email placeholder leaked"
```

Expected:

- The commit lists only `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` and any conditional files staged in Steps 3.6 / 4.6 / 5.5. No code files. Pre-existing unrelated unstaged changes from Task 0's snapshot may still be present in `git status`; verify those are unchanged from the snapshot (this plan's edits should not have modified them).
- The conditional-marker grep prints "OK: no conditional markers leaked" (cycle-4 self-check). If it prints any line containing `<!-- CONDITIONAL`, the commit message contains unedited template markers — the heredoc-edit instruction in Step 6.2 was not followed correctly. Amend the commit message before pushing: `git commit --amend` is acceptable here because the commit has not been pushed yet (this commit is local-only at this point in the plan).
- Both co-author-placeholder greps print "OK" (scrutiny follow-up self-check). If either prints a match, the placeholder text was not replaced. Amend the commit message before pushing.

---

## Self-Review Checklist

Run this before requesting plan approval. If any box is unchecked, fix in place.

- [x] **Spec coverage.** Each of the user's six requested sections is present and explicit:
  1. Raw envelope facts to preserve → "Raw Envelope Facts To Preserve" section.
  2. Interpretive overclaims to patch → "Interpretive Overclaims To Patch" section (five sites — four original plus the cycle-4-added "Architecture Spec Readiness Delta" section).
  3. Authority basis: `approval_router.py` + repaired rebaseline plan → "Authority Basis" section + Vocabulary Succession sub-section.
  4. Files to inspect before edit, including JSON → "Files To Inspect Before Edit" table.
  5. Stop condition for JSON disposition → "Stop Conditions" section + Task 1.4 (consumer discovery confirming zero literal-path-based consumers) + Task 3 (in-place interpretive correction).
  6. Verification rg pattern covers bare-word terms (`supported`/`preserved`/`lossy`/`ready_to_close_ticket`) plus phrase patterns (`proves compatibility`/`compatibility for the observed`) plus JSON-key patterns (`local_compatibility`/`supported_methods`); case-insensitive (`-i`) so capital-S "Supported" wording surfaces alongside lowercase → "Verification" section + Task 1.1 + Task 5.
- [x] **Overclaim inventory.** Five `.md` sites enumerated (≈lines 112, 169-174, 176-181, 185, and the "Architecture Spec Readiness Delta" section at ≈lines 189-202 — the fifth site is the cycle-4 addition); three known JSON paths enumerated (`observed_server_requests[0].local_compatibility`, `compatibility_classification.supported_methods`, and `architecture_spec_readiness_delta` block — the third is the cycle-4 addition) with placeholder for additional paths surfaced in Task 1.4.
- [x] **Scope guardrails.** "This plan does not" enumerates: no code edits, no T-20260429-02 method matrix, no live probes, no version-pin changes.
- [x] **Vocabulary succession explicit.** Authority Basis section names the May-1 probe-plan's narrower `supported` definition (route + correlation fields) and frames the rebaseline as a stricter classification splitting parser-kind from response-shape. The diagnostic is reclassified, not retroactively wrong against its own May-1 vocabulary.
- [x] **T-20260429-02 sweep collision resolved.** "Sweep Classification Rules" section adds `legacy-parser-route-vocabulary` classification with explicit bounding rules. Task 1.1 verification anchors enumerate the T-20260429-02 ticket parser-route table rows and the May-1 probe-plan vocabulary definitions as expected `legacy-parser-route-vocabulary` matches. Stop condition example clarified to distinguish overclaim from legacy vocabulary.
- [x] **Sweep case-insensitivity.** All overclaim-detection sweeps use `-i`: Verification section, Step 1.1, Step 1.4 rg search (post jq-validate split), Step 2.7, Step 3.5, Step 4.5, Step 5.1.
- [x] **Git proof for "landed on `main`."** Step 1.5b requires `git diff main..HEAD -- packages/plugins/codex-collaboration/server/runtime.py` (empty) AND `git show main:.../runtime.py | rg -n "codex|agents|worktrees|build_workspace_write_sandbox_policy"` (carve-outs visible at any line — content-aware, not fixed-range) before Task 4 writes the assertion. Three outcomes: carve-outs at expected lines (proceed), carve-outs at drifted lines (adapt Task 4.2/4.3/4.4 references and proceed), carve-outs absent (fire stop condition).
- [x] **Fallback tuple wording precise.** Step 2.2 bullet 4 enumerates `_AVAILABLE_DECISIONS[command_approval]` verbatim and frames lossiness as bidirectional — payload loss for `acceptWithExecpolicyAmendment` plus spurious additions (`acceptForSession`, `applyNetworkPolicyAmendment`, `decline`). Does NOT phrase it as "decline replaces cancel" — `cancel` is preserved by the fallback. JSON Step 3.3 mirrors this precision.
- [x] **JSON disposition is in-place interpretive correction (no migration scaffolding).** Step 1.4 confirms zero literal-path-based production consumers. Step 3.3 mutates the three classification fields directly: `local_compatibility` value change, `compatibility_classification` block key-set and value rewrite (a schema-shape change, not value-only), and `architecture_spec_readiness_delta` content replacement. No `_legacy_*` renaming, no `classification_vocabulary` markers, no dual-shape blocks. Vocabulary succession documented via inline JSON notes, Markdown diagnostic wording, and commit message. Justified by zero consumers + repo-internal artifact declaration. Git history preserves the prior vocabulary.
- [x] **Consumer discovery is hidden-aware.** Step 1.4's consumer-discovery `rg` includes `--hidden --glob '!.git/**'` so paths under `.claude/hooks/` and other dot-directories surface from repo root. A defensive named-roots cross-check is also documented against existing roots (`packages/ scripts/ extensions/ .claude/hooks/`), with explicit instruction to verify directory existence before adding any other roots to avoid noise. Plain `rg --type-not md` from repo root would silently skip hidden paths the plan explicitly enumerates as valid consumer locations.
- [x] **Consumer discovery is primarily a confirming gate.** Discovery verifies the premise that enables in-place correction: no code references the JSON file by literal path. Single dispositional consequence: surfacing a production consumer fires the "JSON correction is unsafe" stop condition. Otherwise, in-place correction proceeds — the schema-shape change to `compatibility_classification` (key-set rewrite) is safe because no code reads the file.
- [x] **JSON validation split from JSON search.** Step 1.4 runs `jq '.' <file> >/dev/null` as a separate validation command before the rg search. A failed `jq` pipe used to silently produce empty stdout, indistinguishable from a no-matches result; the split surfaces invalid-JSON as a non-zero exit before any pattern matching runs.
- [x] **Pre-edit status snapshot (Task 0; tightened by scrutiny follow-up 2).** Task 0 captures `git status` + `git diff --cached --name-only` + `git diff --name-only` before any edits begin. Pre-existing changes in target files (the diagnostic `.md`, sibling JSON, register, or rebaseline plan) are now a stop condition — the executor must resolve them before proceeding, since this plan's edits assume target files match `HEAD`. Pre-existing unrelated unstaged changes (outside the four targets) are recorded and tolerated. Pre-existing unrelated STAGED changes are surfaced before proceeding so the plan's commit cannot accidentally bundle unrelated staged work.
- [x] **Sweep additional-paths default is STOP, not in-scope.** Task 1.4 narrows the line-253 carve-out: additional JSON overclaim paths beyond the three enumerated default to firing the "Pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition. The narrow mechanical-mirror exception applies ONLY when the additional path is unambiguously the same kind of claim (a binary supported/ready boolean or a supported-methods-style listing) AND the in-place correction is a straightforward value change. Novel shapes stop; they do not silently extend Task 3's edits.
- [x] **Register-annotation `main`-truth has its own stop condition.** Step 1.5b's git-evidence checks (`git diff main..HEAD -- runtime.py` empty AND `git show main:.../runtime.py | rg -n "codex|agents|worktrees|build_workspace_write_sandbox_policy"` showing carve-outs — content-aware, not fixed-range) are mapped to a dedicated "Register-annotation `main`-truth check failed" stop condition rather than the "Live envelope evidence has changed" condition. The two failure modes are distinct: `main`/runtime divergence affects only the register annotation premise, not the envelope-probe diagnostic correction. Surface message reflects the actual failure.
- [x] **Register annotation matches ticket reality.** Task 4 wording names AC #1, #2, AND #3 explicitly as the unchecked closure criteria; "only smoke and probe remain" was rejected because AC #3 (regression-assertion update + suite pass) is also unchecked.
- [x] **Exit-condition cell replacement.** Task 4.4 replaces the T-20260429-01 row's Exit condition cell so it names AC #1-#3 closure work only. Task 4.2 (Current truth append) on its own would leave the row simultaneously asserting Phase 1 has landed AND that Phase 1 still needs to be landed — exactly the contradiction this plan exists to remove. Task 4.5 verification searches for surviving "Land the Phase 1" framing.
- [x] **Register reconciliation scope is narrow.** No global "Last reconciled" bump. Only the T-20260429-01 row (Current truth + Exit condition cells) and priority `#1` line are touched; row-local recency is captured by the in-cell "As of 2026-05-09" stamp.
- [x] **Optional register note.** Task 4 is conditional on Task 1.5; skips cleanly when register already reflects landed implementation across all three cells.
- [x] **Placeholder scan.** No "TBD", no "appropriate", no "similar to Task N", no "handle edge cases". Replacement wording for all five `.md` overclaim sites, the JSON patch fields, and the register cells is shown verbatim.
- [x] **Wording consistency.** "Decision-shape lossy" used consistently in `.md`, JSON, and register paths. "Parser-kind compatible" used consistently when distinguishing from "fully supported." `_resolve_available_decisions`, `_AVAILABLE_DECISIONS[command_approval]`, and `approval_router.py:103-111` named identically across tasks.
- [x] **Bite-sized steps.** Each step is a single action: one rg, one read, one edit, one git command. No multi-action steps.
- [x] ~~**Consumer-shape-incompatibility stop condition (review-cycle 3).**~~ *Superseded by scrutiny follow-up 11 (in-place correction).* Stop condition simplified to: any production consumer found → fire stop. No preserve-and-add shape-tolerance evaluation needed because no legacy blocks exist.
- [x] ~~**Legacy-block paths in JSONPath notation (review-cycle 3).**~~ *Superseded by scrutiny follow-up 11.* No `_legacy_*` blocks or `classification_supersedes` structure exists in the current plan.
- [x] **Named-roots cross-check excludes non-existent paths (review-cycle 3).** Step 1.4 named-roots cross-check lists only existing repo roots (`packages/ scripts/ extensions/ .claude/hooks/`); `.claude/scripts/` is excluded (does not exist in this repo at plan-write time). Workers are instructed to verify directory existence before adding any other roots so the cross-check does not produce noise from non-existent paths.
- [x] ~~**JSON snippet schematic disclaimer (review-cycle 3).**~~ *Superseded by scrutiny follow-up 11.* No legacy-block schematics exist in the current plan. Step 3.3 specifies exact replacement values inline; the "re-read live JSON" instruction remains for surrounding-context verification.
- [x] **Architecture-readiness as fifth/third disposition site (review-cycle 4).** Cycle 1-3 enumerated four `.md` overclaim sites (≈lines 112, 169-174, 176-181, 185) and two JSON overclaim paths (`compatibility_classification`, `local_compatibility`). The cycle-4 review surfaced that the diagnostic's "Architecture Spec Readiness Delta" `.md` section (≈lines 189-202) and the JSON's parallel `architecture_spec_readiness_delta` block (≈lines 45580-45591) form a fifth / third disposition site that the cycle 1-3 plan missed entirely — a worker following the earlier plan would have left `architecture_spec_readiness_delta.ready: true` and "architecture spec can proceed only if it scopes server-request support to the observed methods" standing, which is the strongest remaining overclaim under rebaseline vocabulary. Step 1.1 verification anchors, Step 1.4 enumerated paths (third bullet), Step 2.5 (`.md` patch), Step 3.3 items 7-8 (JSON preserve-and-add), and the sweep patterns at the Verification section / Step 1.1 / Step 1.4 / Step 2.7 / Step 3.5 / Step 5.1 all enumerate this site explicitly. The sweep pattern adds `architecture_spec_readiness_delta`, `architecture spec readiness delta`, `architecture spec can proceed`, `parseable against`, and `newly_satisfied_items` so the missed-site failure mode cannot recur.
- [x] **Programmatic raw-evidence preservation (review-cycle 4; updated cycle 6).** Cycle 1-3 asserted that the JSON's existing raw-observation fields must remain unchanged (Step 3.3 closing paragraph; Architecture summary; Step 1.4 vocabulary caveat) but enforced this only via syntax check (`jq '.' >/dev/null`) and a narrow rg sweep — a worker could mutate `params_keys`, captured `availableDecisions` arrays, probe rows, or other raw-observation fields and pass both checks. Cycle 4 adds Task 1.4's "Derive raw-evidence projection paths" sub-section (worker derives the `jq` projection against the live JSON, NOT the schematic illustration), Step 3.2 (full pre-edit copy to `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json` + projection snapshot to `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json` — deterministic paths under `/private/tmp` not bare `/tmp`; cycle 6 added the full copy as an immutable reference for re-derivation safety), and Step 3.6 (post-edit re-extraction + `diff` against the pre-edit snapshot; non-empty diff fires the JSON-disposition-unsafe stop condition; recovery re-derives from full pre-edit copy, never from worktree). The schematic projection in Task 1.4 explicitly carries a "DO NOT use as-is" warning + INCLUDE/EXCLUDE path lists; workers err toward over-projection (false positives are recoverable; false negatives are the failure mode this enforcement exists to prevent).
- [x] **Conditional commit-message template + executor-aware co-author (review-cycle 4; updated scrutiny follow-ups 7-8).** Cycle 1-3 hard-coded the commit body's JSON disposition and register annotation paragraphs unconditionally even though Tasks 3 and 4 are conditional (a worker hitting the no-JSON-disposition or no-register-annotation path would commit a body that lies about what the commit contains). Cycle 1-3 also hard-coded `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` — fine when this model authored the commit, false provenance when a different model executed Task 6. Cycle 4 restructured the Step 6.2 heredoc body with `<!-- CONDITIONAL: ... -->` / `<!-- END CONDITIONAL -->` markers around the JSON-disposition paragraph (Task 3) and register-annotation paragraph (Task 4). Scrutiny follow-up 8 adds a third CONDITIONAL block for the rebaseline-plan reconciliation paragraph (Step 5.5) — this was previously embedded inside the Task 3 CONDITIONAL, but Step 5.5 is state-based and can run independently of Task 3 (when canonical JSON fields already carry rebaseline vocabulary from a prior commit). Worker-instruction text above the heredoc names the editing protocol for all three blocks (delete markers + keep paragraph if task/step ran; delete both if skipped) with explicit enumeration of each block's trigger condition. Co-author trailer uses placeholders for identity AND email with replacement instruction naming concrete examples for Anthropic and OpenAI models. Step 6.3's self-check for placeholder leaks covers both placeholders.
- [x] **External-consumer scope explicit (review-cycle 4; elevated to Boundary by scrutiny follow-up).** The external-consumer assumption was originally documented only here in the self-review checklist — a non-operative location that would not be read by a worker during execution. Scrutiny follow-up elevates it to the Boundary section's "This plan does not" list, making it an operative execution premise. The full reasoning (repo-internal artifact, not a public contract; three remediation paths for late-discovered external consumers) now lives in the Boundary and is binding on the executor from task start.
- [x] **`status` field preserved in schema (review-cycle 5; updated follow-up 11).** The `compatibility_classification` replacement block includes `"status": "parser_kind_compatible_decision_shape_lossy"` so that any reader of `.compatibility_classification.status` sees the rebaseline vocabulary value rather than `undefined`. Step 3.5b's canonical-value assertions verify this field.
- [x] **Editing-method guidance for 45K-line JSON (review-cycle 5).** Cycle 1-4 specified what to change and how to verify but not the editing mechanism for the 45,592-line JSON. Edit-tool string replacement with insufficient surrounding context risks non-unique matches; `jq` transforms risk key reordering that invalidates Step 3.6's byte-identical diff assumption. Cycle 5 adds editing guidance to Step 3.3's preamble: use the Edit tool with minimum 3-5 lines of surrounding context; avoid `jq` transforms for structural edits.
- [x] **Step 3.6 key-ordering false-positive mitigation (review-cycle 5).** Cycle 4's Step 3.6 raw-evidence diff assumes byte-identical `jq` projection output pre- and post-edit. If a worker uses `jq` transforms (against the cycle-5 editing guidance), key reordering could produce a false-positive diff failure that fires the JSON-disposition-unsafe stop condition unnecessarily. Cycle 5 adds a conditional note: if the edit mechanism preserved key ordering (Edit tool), the diff should be byte-identical; if `jq` transforms were used, pipe both projections through `python3 -m json.tool --sort-keys` before diffing.
- [x] **Live-capture-wins precedence for hardcoded tuple (review-cycle 5).** Step 2.2 hardcodes the `_AVAILABLE_DECISIONS[command_approval]` tuple inline, while Step 1.2 instructs the worker to capture it live. Cycle 1-4 did not specify which wins if they differ. Cycle 5 adds an explicit precedence note: if Step 1.2's captured tuple differs from the hardcoded values, use the live capture and adjust the fallback explanation to match.
- [x] **Step 3.6 recovery cannot overwrite pre-edit baseline (review-cycle 6).** Cycle 4-5's Step 3.6 false-positive recovery path said "re-run from Step 3.2" — but Step 3.2 captured from the worktree. If Step 3.3 had already mutated the JSON, re-running Step 3.2 would capture post-edit state as the new "pre-edit" baseline, making the subsequent diff compare post-edit to post-edit (always empty = false pass). Cycle 6 fixes this: Step 3.2 now saves a full pre-edit copy (`/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json`) before any mutation, then extracts the projection from that copy. The recovery path re-derives from the saved full pre-edit copy, never from the worktree.
- [x] **Raw-evidence projection includes full `.probes` array (review-cycle 6).** Cycle 4-5's schematic projection covered `observed_server_requests[]` (a derived summary with `params_keys`, `has_id`, etc.) but omitted the `.probes` array entirely — the raw observation layer containing per-probe `status`, `classification`, `evidence`, `responses` (where "No approval response was sent" lives), `errors`, `notifications`, and `server_requests[].{id,method,params}` (the verbatim wire envelope). The plan declares all of these immutable but the projection couldn't enforce it. Cycle 6 includes the entire `.probes` array in the projection — it is pure observation data, distinct from the top-level interpretation fields (`compatibility_classification`, `local_compatibility`, `architecture_spec_readiness_delta`) that this plan mutates.
- [x] **Stale inventory counts reconciled (review-cycle 6).** Cycle 4 added the fifth `.md` site and third JSON path but did not update all earlier textual references. "Four specific sites" (line 69), "all four sites" (line 111), "Confirm the four enumerated" (line 122), "beyond the two enumerated paths" (lines 136, 1038), and "all four `.md` overclaim sites" (line 1044) all pre-dated the cycle-4 addition and were never reconciled. Cycle 6 fixes all six stale references.
- [x] **`rm` fallback removed (review-cycle 6).** Step 3.6's successful-diff cleanup offered `rm` as a fallback if `trash` was unavailable, with an incorrect claim that "the per-project safety policy permits removing these scratch artifacts." The global safety policy unconditionally prohibits `rm`. Cycle 6 removes the fallback: use `trash` only; if unavailable, leave temp files in place and report their paths.
- [x] **Step 1.5b line-drift vs stop-condition reconciled (review-cycle 6).** Step 1.5b gave contradictory instructions: "locate the actual lines on `main` and update Task 4.2's annotation accordingly" (implying adapt-and-continue) vs "If either check fails → fire the stop condition. Skip Task 4 entirely" (implying halt). Cycle 6 distinguishes three outcomes explicitly: carve-outs at expected lines (proceed), carve-outs at different lines (drift — adapt line reference and proceed), carve-outs absent from `main` (fire stop condition — implementation not landed).
- [x] **Overview and temp-file convention refreshed for full-copy mechanism (review-cycle 6).** The Task 1.4 overview paragraph (line 327) still described "captures a pre-edit projection" without mentioning the full pre-edit copy. The temp-file convention paragraph listed only one temp file path. Cycle 6 updates the overview to name both artifacts (full copy + projection) and expands the convention paragraph to list all three paths with their roles.
- [x] ~~**Consumer discovery covers all three preserve-and-add fields (scrutiny follow-up).**~~ *Superseded by scrutiny follow-up 11.* Consumer discovery simplified to a filename-path search confirming zero literal-path-based production consumers. Field-name searches removed as unnecessary for in-place correction (no dual-shape ambiguity to resolve).
- [x] **Temp snapshot non-overwriting guard (scrutiny follow-up).** Step 3.2 used deterministic temp paths without checking for existing files. A re-run after a partial Task 3 execution would overwrite the pre-mutation snapshot with post-mutation state, making Step 3.6's diff compare post-edit to post-edit (false pass). Scrutiny follow-up adds `test ! -e` guards before both `cp` and `jq` commands, with a recovery guide for both clean-worktree and mutated-worktree cases.
- [x] **Commit-message jq-verification claim conditionalized (scrutiny follow-up).** The always-retained opening paragraph of the commit message claimed "with programmatic pre/post jq-projection verification" — but jq verification only runs when Task 3 runs (JSON disposition applied). When Task 3 is skipped (no JSON overclaim found), the claim is false. Scrutiny follow-up moves the jq-verification sentence into the Task 3 CONDITIONAL block and shortens the always-retained sentence to "raw envelope observations are preserved unchanged."
- [x] ~~**Legacy-block preservation diff gate (scrutiny follow-up 2).**~~ *Superseded by scrutiny follow-up 11.* No `_legacy_*` blocks are created; no legacy-block diff gate needed. Raw-evidence preservation is enforced by Step 3.5's projection diff. Staging is at Step 3.6 (requires Steps 3.5 + 3.5b to pass).
- [x] **Target-file ownership in Task 0 (scrutiny follow-up 2).** Task 0 previously only guarded against unrelated dirty files outside the target set. Pre-existing changes in the three target files were unclassified — a prior partial run or concurrent edit could be silently committed as this plan's work. Task 0 now classifies target-file changes as a separate stop condition requiring user resolution before proceeding.
- [x] **Recovery-path provenance guard (scrutiny follow-up 2).** Step 3.2's recovery instruction for case (b) (worktree mutated by partial Step 3.3) now requires verifying the worktree diff contains ONLY Step 3.3-shaped mutations before restoring from the full pre-edit copy. Unknown changes → STOP instead of overwrite.
- [x] **Rebaseline plan is a canonical-JSON consumer (scrutiny follow-up 3; updated follow-up 11).** The rebaseline implementation plan at lines 204-220 contains `jq` commands that read `local_compatibility` and `architecture_spec_readiness_delta` — making it a Markdown-embedded executable consumer of the canonical JSON fields. After Task 3's in-place correction, the expected-value bullets at lines 216-219 become stale (expect `"supported"` and `ready: true` where the fields now carry rebaseline vocabulary). Step 5.5 reconciles these lines; Step 5.6 verifies no other rebaseline-plan references remain stale.
- [x] **Task 5 read-only contradiction resolved (scrutiny follow-up 3).** Task 5 was declared read-only but Step 5.3 instructed workers to "fix the loser before committing" — creating an execution paradox. Now Task 5 header explicitly scopes read-only to Steps 5.1-5.4, Step 5.5 owns the rebaseline-plan write, and the contradiction-patch path is a defined stop-return-rerun loop rather than an in-task fix.
- [x] **Line-drift handling covers all Task 4 references (scrutiny follow-up 3).** Step 1.5b's drift-adaptation instruction previously named only Task 4.2's annotation. The same `runtime.py:107-118` reference appears in Step 4.3's priority-line replacement text and Step 4.4's exit-condition replacement text. Drift instruction now enumerates all three sites explicitly.
- [x] **Markdown consumers of canonical JSON keys checked (scrutiny follow-up 3).** Step 5.6 adds an explicit `rg` verification that the rebaseline plan's mentions of `local_compatibility` and `architecture_spec_readiness_delta` all agree with the post-patch canonical vocabulary. This closes the gap where code-only consumer discovery missed control documents that embed `jq` evidence-check contracts.
- [x] **Canonical-value `jq` assertions for JSON readiness boolean (scrutiny follow-up 4; simplified follow-up 11).** The `rg` sweep pattern matches the key name `architecture_spec_readiness_delta` but cannot match the nested `"ready": true` boolean value at the JSON line where it lives. Step 3.5b provides eight `jq -e` assertions for canonical values (three scalar: `ready == false`, `local_compatibility`, `status`; five array: `fully_supported_methods`, `parser_kind_compatible_methods`, `decision_shape_lossy_methods`, `still_missing_items | length >= 3`, `still_missing_items | any(test(...))`). No legacy-preservation assertions (no `_legacy_*` blocks exist under in-place correction).
- [x] **Rebaseline plan in Task 0 target-file ownership (scrutiny follow-up 4).** Step 5.5 writes and stages `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md`, but Task 0's target-file list previously listed only three files. If the rebaseline plan were already dirty before execution, Task 0 would classify it as "unrelated unstaged work" and allow proceeding, then Step 5.5 would absorb the pre-existing dirt into the commit. Task 0 now lists four target files; a dirty rebaseline plan fires the same stop-and-surface condition as the other three targets.
- [x] **Post-write terminal sweep (scrutiny follow-up 4).** Step 5.1's broad sweep ran before Step 5.5 wrote new text into the rebaseline plan. Step 5.6 only checked `local_compatibility|architecture_spec_readiness_delta` — a narrow pattern that cannot catch wording-level overclaims in the new replacement text. Step 5.7 reruns the full sweep pattern against the rebaseline plan after Step 5.5's write, classifying each match per the Sweep Classification Rules. An `interpretive-overclaim` classification means Step 5.5's replacement text is wrong and triggers a fix-restage-rerun loop.
- [x] ~~**Vocabulary marker `jq` assertions (scrutiny follow-up 5).**~~ *Superseded by scrutiny follow-up 11.* No `classification_vocabulary` or `classification_supersedes` fields exist under in-place correction. Total assertions reduced from fifteen to eight (three canonical scalar + five canonical array).
- [x] **Consumer discovery taxonomy includes peer diagnostic data artifacts (scrutiny follow-up 5).** Task 1.4's consumer-discovery classification had three buckets (production consumer, test fixture, self-reference). The broad `rg` pattern also surfaces sibling diagnostic JSON files (e.g., `codex-app-server-scratch-home-runtime-probes.json`) that contain the same field names as data, not as consumers. A worker encountering these hits had no classification bucket and would either misclassify them as production consumers (triggering a false stop condition) or leave them unclassified (violating the exhaustive-classification requirement). New `peer-diagnostic-data-artifact` classification added with explicit scoping: these are independent diagnostic captures, NOT consumers of the target JSON's schema.
- [x] ~~**Legacy assertions compare against pre-edit snapshot, not hard-coded literals (scrutiny follow-up 5).**~~ *Superseded by scrutiny follow-up 11.* No legacy assertions or legacy-block snapshots exist under in-place correction. Step 3.5b's canonical assertions use hard-coded expected values (the rebaseline vocabulary values this plan introduces).
- [x] **Markdown raw-facts preservation check (scrutiny follow-up 5; anchor corrected scrutiny follow-up 9).** Step 2.7's `rg` sweep can detect surviving overclaim wording but cannot detect accidental removal of raw-evidence lines. The JSON has full programmatic enforcement (Steps 3.6/3.6b), but the `.md` had no analogous check — a Task 2 edit that accidentally deleted a raw-observation line would pass Step 2.7. New Step 2.7b spot-checks six distinctive raw-observation anchors (`item/commandExecution/requestApproval`, `proposedExecpolicyAmendment`, `availableDecisions`, `/bin/zsh -lc`, `No approval response was sent`, `itemId`) via `grep -qF`. Scrutiny follow-up 9 corrected the second anchor from `"acceptWithExecpolicyAmendment"` to `proposedExecpolicyAmendment` — the former does not exist in the pre-edit `.md` file (it appears only in the sibling JSON and the delegate-execution diagnostic), so the old anchor tested new-prose survival rather than raw-evidence preservation. All six anchors are now verified to exist in the pre-edit `.md`.
- [x] **Rebaseline "Command Approval Decision-Shape Boundary" classified as `authority-source` (scrutiny follow-up 5).** Step 5.7 previously classified matches from the rebaseline plan's lines 905-921 as `legacy-parser-route-vocabulary`. That section uses rebaseline-era framing ("decision-shape lossy", "response compatibility is not established", "lossless parser/response branch") and is one of this plan's two truth authorities (Authority Basis item 2) — it describes current reality, not the May-1 narrower vocabulary. New `authority-source` classification added to the Sweep Classification Rules table. Verification section, Task 5.2, and Step 5.7 all updated to include `authority-source` as an acceptable terminal classification.
- [x] **Taxonomy, raw-preservation, target-count, and assertion gaps (scrutiny follow-up 6).** Five defects patched: (1) `authority-source` added to Step 1.1's allowed classification list — the global Sweep Classification Rules defined six classifications but Step 1.1 listed only five, causing a worker encountering rebaseline-plan authority-section matches to have no valid label. (2) `peer-diagnostic-data-artifact` added to the Sweep Classification Rules table, the Verification section's acceptable terminal classifications, and Task 5.2's acceptable classifications — the sweep glob `docs/diagnostics/codex-app-server-*.json` matches sibling diagnostic JSONs whose own `architecture_spec_readiness_delta` fields are independent data, not overclaims about the target method; workers had no classification bucket and would either misclassify or leave unclassified. (3) Step 2.7b strengthened with `git diff` hunk-review verification — the six `grep -qF` anchors pass even when raw lines are deleted because three of the six anchor strings (`item/commandExecution/requestApproval`, `availableDecisions`, `itemId`) also appear in the replacement interpretive prose from Steps 2.1-2.5; the hunk review catches edits outside the five enumerated sites. (4) Stale "three above" references at Task 0 lines 229/230 fixed to "four above" and self-review line 1248 updated to name all four target files (diagnostic `.md`, sibling JSON, register, rebaseline plan) — the rebaseline plan was added as a fourth target file in scrutiny follow-up 4 but the count references were not propagated. (5) Step 3.6c expanded from ten to fifteen `jq -e` assertions: five canonical array assertions added (`fully_supported_methods == []`, `parser_kind_compatible_methods == ["item/commandExecution/requestApproval"]`, `decision_shape_lossy_methods == ["item/commandExecution/requestApproval"]`, `still_missing_items | length >= 3`, `still_missing_items | any(test("lossless parser/response branch"))`) and the `classification_supersedes.legacy_blocks | length == 3` marker assertion upgraded to exact-content matching against the three JSONPath entries; a worker could previously create the `compatibility_classification` block with correct `status` but wrong array values (e.g., `fully_supported_methods: ["item/commandExecution/requestApproval"]` — a remaining overclaim) and pass all ten assertions.
- [x] **Execution-control path contradictions resolved (scrutiny follow-up 7).** Five defects from external scrutiny patched: (1) Step 1.1 verification anchor no longer claims the `rg` sweep must surface `"ready: true"` (impossible — the sweep matches key names, not bare boolean values); replaced with guidance to verify the boolean via `jq -e` during Task 1.4 and rely on Step 3.6c's assertions post-edit. (2) Global stop condition for register-annotation `main`-truth check reconciled with Step 1.5b's line-drift handling — the stop condition now explicitly states line drift is NOT a stop condition and fires only when (a) this branch modified `runtime.py` or (b) carve-outs are absent from `main` entirely; Step 1.5b uses `rg -n` content-aware search instead of fixed-range `sed -n '107,118p'`. (3) `peer-diagnostic-data-artifact` added to Step 1.1's operative allowed-labels list (was defined in Sweep Classification Rules table and self-review but missing from the actual step instruction). (4) "Live envelope evidence changed" stop condition now has an explicit discovery path — artifact inventory via `ls docs/diagnostics/2026-05-{02..31}-*envelope*` during Task 1.1, with comparison against the May-1 capture's `availableDecisions` shape if a newer artifact exists. (5) Step 5.5 skip condition changed from execution-based ("if Task 3 ran") to state-based (`jq -e` checks against the live canonical JSON values); handles the case where a prior commit already reconciled the JSON but the rebaseline plan remains stale.
- [x] **Scrutiny follow-up 9: seven structural defects from user scrutiny review.** (1) **False `.md` raw-preservation anchor corrected** — Step 2.7b's second anchor changed from `"acceptWithExecpolicyAmendment"` (absent from pre-edit `.md`; only in sibling JSON and delegate diagnostic) to `proposedExecpolicyAmendment` (raw params key at `.md` lines 121, 138). Added anchor derivation rule: all anchors must exist in the pre-edit file. (2) **"Parsing succeeds" overclaim weakened** — Step 2.4 replacement wording changed from "proves parser-kind compatibility (envelope parsing succeeds...)" to "supports a parser-kind compatibility inference" with explicit rationale distinguishing static field presence from parser execution evidence. (3) **Architecture doc added to sweep scope** — `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md` added to Required Reads, Task 1.1 sweep paths, and sweep boundary description; contains same "local classification was `supported`" wording at lines 148-160. Active handoffs also added to sweep with supersession-note strategy. (4) **Branch/remote freshness gate added** — New Step 0.1 verifies current branch, `main == origin/main`, and `git fetch --dry-run` before any edits or "landed on `main`" claims. (5) **JSON editing risk mitigation** — Per-edit `jq` syntax check added after each Step 3.3 edit; full pre-edit copy named as recovery baseline for catastrophic malformation. (6) **Classification baseline artifact required** — Task 1.1 must write annotated classification table to `/private/tmp/codex-collab-overclaim-fix-sweep-baseline.md` for Task 5 diffing; resolves ephemeral classification problem. (7) **Task 4 decoupled from core fix** — Register-annotation `main`-truth stop condition now scoped to "skip Task 4 only; do NOT block Tasks 2, 3, 5, or 6." Step 1.5b's stop-condition outcome also updated. (8) **`runtime.py` line citation broadened** — Step 1.5b now captures both readable-roots append range (~107-118) and gitdir resolver range (~28-60); Task 4.2 annotation template uses both placeholders. (9) **Newer-evidence stop condition uses content search** — Two-pronged discovery (filename + content) via `rg -l 'item/commandExecution/requestApproval'` across diagnostics, architecture, and handoffs; catches evidence in non-standard-named artifacts. (10) **REQUIRED SUB-SKILL removed** — Worker directive changed from skill dependency to "execute sequentially in one workspace; do not parallelize across Task 3 commit state."
- [x] **Scrutiny follow-up 10: scope narrowing from external review verdict (Reject).** Four changes resolving scope contradictions and overscoped gates: (1) **Architecture doc and handoffs removed from scope** — `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md` and `docs/handoffs/` removed from Required Reads, sweep paths (Task 1.1, Verification, Task 5.1), and classification obligations. Replaced with explicit "Out-of-scope docs" note naming both as deferred to a follow-up pass. Root cause: prior cycle added them to scope but not to the write set or commit contract, creating an unownable detection path. (2) **Newer-evidence gate simplified to filename-only** — Content-based `rg -l 'item/commandExecution/requestApproval'` across diagnostics/architecture/handoffs removed. That search returned the target JSON, architecture note, and other non-capture artifacts — false positives. Retained: the filename-pattern search (`2026-05-(0[2-9]|...)-.*envelope`) which matches only dated post-May-1 capture files. (3) **Remote/main gate moved inside Task 4** — Step 0.1 reduced to branch safety check only (not on `main`). Remote freshness checks (`git fetch --dry-run`, `rev-parse main vs origin/main`) moved into Step 1.5b where Task 4's "landed on `main`" claim is actually produced. Tasks 2, 3, 5, 6 no longer blocked by remote state. Stop condition updated to include remote divergence as trigger (c). (4) **Classification surface reduced** — Full per-line classification now mandatory only for write-set files. Other swept files (tickets, non-target plans) get spot-check confirmation of no `interpretive-overclaim`. Applied uniformly across Task 1.1, Verification section, and Task 5.2. Root cause: prior cycles expanded sweep breadth without scaling the classification budget, making discovery larger than the fix.
- [x] **Scrutiny follow-up 11: JSON strategy simplified from preserve-and-add to in-place correction (re-scrutiny verdict: Major revision).** The preserve-and-add choreography — `_legacy_*` key renaming, `classification_vocabulary` markers, `classification_supersedes` pointers, dual-shape blocks, 15 `jq` assertions, legacy-block diffs — was solving an unproven problem. With zero confirmed production consumers and the plan's own boundary declaring the JSON "a repo-internal artifact, NOT a public contract," the elaborate schema-migration story contradicted its own premises and created the plan's dominant failure surface. Changes: (1) **Architecture section** rewritten to describe in-place interpretive correction. (2) **Boundary "implements"** bullet replaced with simple field-value correction, explicit "no `_legacy_*` renaming" statement. (3) **Task 1.4** consumer discovery reduced to a confirming file-path check (expected: zero results). Vocabulary caveat, elaborate taxonomy, temp-file convention for legacy-block snapshots all removed. (4) **Task 3** rewritten from 330 lines to ~90 lines: three in-place field mutations (including `compatibility_classification` key-set change), `jq` syntax validation, raw-evidence projection diff, 8 canonical-value assertions. No migration scaffolding. (5) **Task 5.5** replacement text updated to remove `_legacy_*` references. (6) **Task 6** commit-message CONDITIONAL paragraph rewritten for in-place correction. (7) **Stop condition** simplified from structural-unfitness to consumer-found-only. Justification for in-place: git history preserves the prior vocabulary; the vocabulary succession is documented in the Markdown diagnostic's corrected wording, the JSON's inline notes, and the commit message. No hypothetical future reader needs both shapes in the same file.
- [x] **Scrutiny follow-up 12: minor revision from third scrutiny pass.** Five items addressed: (1) **"No structural schema changes" corrected** — Boundary and Step 3.3 text now explicitly acknowledge that the `compatibility_classification` block undergoes a key-set change (schema-shape change), not a value-only edit. Language changed from "no structural schema changes" to "no migration scaffolding" with the shape change called out and justified by zero consumers. (2) **Stale self-review checklist entries superseded** — Seven checklist items describing removed preserve-and-add machinery (legacy-block diffs, vocabulary markers, 15 assertions, JSONPath notation, legacy-snapshot comparisons) marked as superseded with brief notes explaining what replaced them. Three items (consumer discovery, rebaseline-plan consumer, canonical-value assertions) rewritten to reflect current in-place correction state. (3) **Consumer claim narrowed** — "Zero confirmed production consumers" tightened to "no literal-path-based production consumers" throughout, matching the actual proof (filename `rg`). Disposition rationale and consumer-discovery expected text updated. (4) **Recovery path uses `git restore`** — Step 3.2 recovery changed from `git checkout --` to `git restore --source=HEAD --` (non-destructive semantics). (5) **`local_compatibility_notes` reviewed and documented** — Step 3.3 now explicitly states this field was reviewed and left unchanged because it describes parser boundary behavior, not response-shape support; surfaces conditional for worker if notes text overclaims. Also fixed: stale "3.7" → "3.6" in Task 6 staged-set summary.
- [x] **Epistemic consistency for "parseable" claims (scrutiny follow-up 13).** Step 2.5's third newly-satisfied bullet and Step 3.3 item 3's `architecture_spec_readiness_delta.newly_satisfied_items[2]` both said "is parseable via the parser's decision-shape-lossy fallback path." Step 2.4 carefully weakened "proves parser-kind compatibility" to "supports a parser-kind compatibility inference" because the diagnostic captured static field presence, not live parse execution — but that epistemic caution was not carried into the architecture-readiness replacement text. Changed to "is inferred to be parseable" in both sites for consistency.
- [x] **`compatibility_classification.status` semantic-change note (scrutiny follow-up 13).** The `status` field changes semantics from probe-pass/fail (`"passed"`) to classification label (`"parser_kind_compatible_decision_shape_lossy"`). Zero confirmed consumers, but a hypothetical future reader querying `.compatibility_classification.status` expecting pass/fail would get unexpected data. Added a third `notes` entry to the replacement `compatibility_classification` JSON block documenting the semantic change inline.

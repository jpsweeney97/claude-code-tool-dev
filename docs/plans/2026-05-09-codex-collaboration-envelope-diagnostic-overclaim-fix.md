# Codex App Server Server-Request Envelope-Diagnostic Overclaim Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is a docs-only plan with hard scope guardrails; do not convert it into a parser/response correctness change or into a T-20260429-02 method-by-method coverage push.

**Goal:** Reconcile the committed May-1 server-request envelope-probe diagnostic with the repaired rebaseline implementation plan and `approval_router.py` reality, eliminating the docs-only contradiction without altering raw observation evidence.

**Architecture:** Surgical doc edits. Preserve the diagnostic's raw observation layer (envelope contents, params keys, redacted summary, trigger command) untouched, with programmatic enforcement via pre/post jq-projection diff. Patch only the interpretive layer that conflicts with code reality. Mirror the correction in the diagnostic's sibling JSON via a preserve-and-add disposition: rename the original `compatibility_classification`, `local_compatibility`, and `architecture_spec_readiness_delta` fields with a `_legacy_` prefix (preserving their May-1 parser-route vocabulary verbatim), add new fields under the same canonical keys carrying rebaseline-vocabulary classification, and add explicit `classification_vocabulary` + `classification_supersedes` markers documenting the boundary. Optionally annotate the reconciliation register so its priority order reflects landed implementation.

**Tech Stack:** Markdown, JSON, ripgrep, jq, git.

---

## Boundary

This plan implements:

- Wording corrections to the envelope-probe diagnostic `.md` interpretive claims (five specific sites: classification line, "Local compatibility judgment" bullet block, "Compatibility result" bullet block, "Important limit" first sentence, and "Architecture Spec Readiness Delta" section).
- A sibling-JSON disposition (preserve-and-add: rename existing `compatibility_classification` / `local_compatibility` / `architecture_spec_readiness_delta` to `_legacy_*` keys; add new rebaseline-vocabulary blocks under canonical keys; add `classification_vocabulary` + `classification_supersedes` markers).
- Programmatic raw-evidence preservation: pre-edit jq-projection of immutable JSON paths captured to a deterministic temp file, post-edit re-projection, and `diff` exit-empty before staging.
- Optional reconciliation-register annotation recording that `T-20260429-01` Phase 1 implementation has landed on `main`, with closure evidence still missing.
- A verification sweep across May-1 diagnostics, the rebaseline plan, the friction-reduction ticket, and the register for residual overclaims.
- Reconciliation of the rebaseline implementation plan's evidence-check section (lines 204-220) so its `jq` commands and expected-value bullets reflect the new canonical JSON vocabulary introduced by Task 3's preserve-and-add disposition. Without this update, a future worker following the rebaseline plan would hit an evidence mismatch when reading the post-patch JSON.
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
- Discover or accommodate external consumers of the diagnostic JSON. The diagnostic JSON is treated as a repo-internal artifact, NOT a public contract. External consumers — other projects, Codex sessions, hand-written analyses, downstream tooling not in this repo — are explicitly out of scope. Consumer discovery (Task 1.4) searches repo-local code only. If an external consumer is later identified that reads a canonical key path and breaks under the new shape, the appropriate response is to (a) update that consumer, (b) request a separate plan that reverses to non-canonical-key preserve-and-add, or (c) treat the breakage as discovered-late-but-not-pre-blocking — NOT to retroactively reverse this plan's disposition.

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
| `packages/plugins/codex-collaboration/server/runtime.py` (line range 107-118 on `main`) | Confirm Phase 1 sandbox carve-outs are present; via `git show main:.../runtime.py | sed -n '107,118p'`. Drives Task 4 register annotation. Read on `main`, not the current branch. |
| `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:895-925` | Anchor corrected wording to the repaired plan's framing ("decision-shape lossy", structured `acceptWithExecpolicyAmendment`, "lossless parser/response branch"). |
| `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:204-220` | Evidence-check `jq` commands and expected-value bullets that read `local_compatibility` and `architecture_spec_readiness_delta` from the sibling JSON. These are Markdown-embedded consumers of the canonical JSON fields that Task 3 renames. Drives Task 5.5 reconciliation. |
| `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` (full, with extra attention to lines ≈100-200) | Confirm the five enumerated overclaim sites; surface any other interpretive overclaims. |
| `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` (sibling JSON, may or may not exist) | Discover existence; if present, identify any parallel overclaim fields. Drives Task 3 disposition. |
| `docs/status/codex-collaboration-reconciliation-register.md:9-70` | "Last reconciled" timestamp + priority order + `T-20260429-01` row "Current truth"/"Exit condition" cells. Drives Task 4 disposition. |
| `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:212-230` (T-20260429-01 ticket) | Confirm acceptance criteria and that AC #1 smoke / AC #2 credential-boundary probe / AC #3 regression assertion + suite pass evidence is genuinely missing. |
| `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md` (T-20260429-02 ticket — context only, no edits) | Context for the Sweep Classification Rules: the parser-route classification table at lines 67-77 ("Supported as `<kind>`" / "Supported (parked)") is `legacy-parser-route-vocabulary`, not an overclaim. The T-20260429-02 method-by-method classification work is OUT of this plan's scope. Read so the worker can confidently classify sweep matches against this file. |
| `docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md:666-672` (May-1 probe-plan vocabulary) | Context for the Sweep Classification Rules: the May-1 four-state vocabulary (`supported` / `unsupported` / `unknown` / `unparseable`) is `legacy-parser-route-vocabulary`. Read to ground the Vocabulary Succession framing in the Authority Basis section. |

The pre-edit `rg` sweep below treats every file under `docs/diagnostics/2026-05-01-codex-app-server-*.md`, `docs/diagnostics/codex-app-server-*.json`, `docs/plans/2026-05-01-codex-app-server-*.md`, `docs/tickets/2026-04-29-codex-collaboration-*.md`, and `docs/status/codex-collaboration-reconciliation-register.md` as a candidate. If the sweep surfaces hits this plan does not enumerate, Task 1 stops and surfaces the finding rather than expanding scope silently.

## Stop Conditions

Stop and surface the situation to the user — do not adapt, expand, or work around — when any of these fire:

- **JSON disposition is unsafe to decide locally.** Task 1 finds the sibling JSON exists, contains a parallel overclaim, AND any of the following hold: (a) the JSON's structure makes the preserve-and-add disposition destructive (e.g., a `_legacy_compatibility_classification` key already exists with different content; the parent object's schema rejects renamed keys; a mechanical-mirror path's structural shape does not cleanly map to legacy-rename + new-block-add); (b) consumer discovery surfaces a production consumer that reads any canonical field whose shape changes under preserve-and-add — e.g., reads `compatibility_classification.supported_methods` directly — AND the consumer code does not tolerate the new shape (under preserve-and-add, the canonical-key block carries `fully_supported_methods` / `parser_kind_compatible_methods` / `decision_shape_lossy_methods` instead of `supported_methods`; a consumer that reads `supported_methods` directly without checking for the new sibling fields would read undefined or malformed data). Surface and ask before proceeding.
- **Pre-edit sweep finds an overclaim site this plan does not enumerate.** "Overclaim" here is bounded by the Sweep Classification Rules below. Examples that trigger this stop: a file under the swept paths claiming command-approval is fully supported in the response-shape sense; a `ready_to_close_ticket: true` for command approval; a register or diagnostic cell asserting `availableDecisions` is preserved without naming the all-strings fallback; an additional JSON overclaim path beyond the three enumerated paths that does NOT mechanically mirror the same kind of claim per Task 1.4's narrow exception. Examples that do NOT trigger this stop (classifiable as `legacy-parser-route-vocabulary`): the T-20260429-02 ticket's `Supported as <kind>` / `Supported (parked)` table entries, the May-1 probe-plan's definition of `supported`, or any other legacy May-1-vocabulary use that is not a fresh response-shape / lossless-preservation / closability claim. Surface the finding; do not silently extend Task 2's edits.
- **Register row already reflects landed-implementation language for T-20260429-01.** Skip Task 4 entirely; do not make a no-op edit.
- **Register-annotation `main`-truth check failed.** Step 1.5b's git evidence does not support the "Phase 1 has landed on `main`" assertion. This fires when EITHER: (a) `git diff main..HEAD -- packages/plugins/codex-collaboration/server/runtime.py` is non-empty (this branch carries `runtime.py` modifications, so the current-branch reads do not stand in for `main`), OR (b) carve-outs are absent from `main`'s `runtime.py` entirely — verified via `git show main:packages/plugins/codex-collaboration/server/runtime.py | rg -n "codex|agents|worktrees|build_workspace_write_sandbox_policy"` returning zero matches (implementation not landed). **Line drift is NOT this stop condition** — if carve-outs appear on `main` at different line numbers than 107-118, that is normal drift handled in Step 1.5b (record actual lines, update all Task 4 references, proceed). Skip Task 4 entirely only when (a) or (b) fires; surface the finding so the register-annotation premise can be reconciled before any annotation is written. This is distinct from "Live envelope evidence has changed" — the envelope is unchanged; the failure is about `main`'s `runtime.py` state diverging from what Task 4's annotation claims.
- **Verification sweep at Task 5 surfaces a surviving overclaim.** Do not commit. Surface the finding.
- **Live envelope evidence has changed since the diagnostic was captured.** This stop condition fires if Task 1's reads reveal a newer probe artifact contradicting the May-1 envelope (different `availableDecisions` shape, different method string, etc.). The fix's premise depends on the May-1 capture being current. **Discovery path:** during Task 1.1's `rg` sweep, check whether the swept `docs/diagnostics/` path contains any envelope-probe diagnostic dated after `2026-05-01` for the same `item/commandExecution/requestApproval` method (e.g., `ls docs/diagnostics/2026-05-{02..31}-*envelope* docs/diagnostics/2026-06-*envelope* 2>/dev/null`). If a newer artifact exists, read its `availableDecisions` shape and compare against the May-1 capture's three-element array (`["accept", {"acceptWithExecpolicyAmendment": {...}}, "cancel"]`). If the shapes differ, this stop condition fires. If no newer artifact exists (expected), record "no post-May-1 envelope capture found" and proceed.

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

Classify every match per the Sweep Classification Rules above. Acceptable terminal classifications: `raw-observation`, `corrected-language`, `legacy-parser-route-vocabulary`, `authority-source`, `peer-diagnostic-data-artifact`, `unrelated`. Unacceptable: `interpretive-overclaim` (any surviving site triggers the Task 5 stop condition).

No surviving site may claim command-approval is "supported" in the rebaseline response-shape sense without the parser-kind / decision-shape-lossy qualification, or claim `availableDecisions` is "preserved" without naming the all-strings fallback condition, or list `item/commandExecution/requestApproval` under `supported_methods` / "observed supported methods" without that qualification, or assert "proves compatibility" for command-approval response semantics, or assert `ready_to_close_ticket: true` for `item/commandExecution/requestApproval`, or assert `architecture_spec_readiness_delta.ready: true` / "architecture spec can proceed" / "parseable against the current local compatibility boundary" without naming the decision-shape lossiness as a remaining response-semantics blocker. Legacy parser-route vocabulary in the T-20260429-02 ticket and the May-1 probe-plan vocabulary definitions is explicitly out of scope for this plan and remains untouched. The new patterns will also match `_legacy_architecture_spec_readiness_delta` block contents and the `_legacy_compatibility_classification` `notes` array (which preserves "parseable against the current local parser/runtime boundary" verbatim under May-1 vocabulary); those classify as `legacy-parser-route-vocabulary` per the bounding rules and are acceptable.

---

## Tasks

### Task 0: Pre-edit status snapshot

**Files:** read-only — no writes in this task.

- [ ] **Step 0.1: Capture pre-edit status snapshot.**

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
- `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` (Step 5.5, conditional — same condition as Task 3)

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

Expected: enumerate every match. For each match, annotate one of `raw-observation`, `interpretive-overclaim`, `corrected-language`, `legacy-parser-route-vocabulary`, `authority-source`, `peer-diagnostic-data-artifact`, or `unrelated` per the Sweep Classification Rules. The annotated list is reused in Task 5 as the baseline for diff verification.

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

- [ ] **Step 1.4: Determine sibling-JSON disposition (preserve-and-add).**

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

All three are in scope for Task 3 under the preserve-and-add disposition (described below). If the sweep surfaces additional overclaim paths within this same JSON file beyond these three, the default is to STOP and surface (fire the "Pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition). The narrow mechanical-mirror exception applies ONLY when the additional path is unambiguously the same kind of claim as one of the three enumerated paths — i.e., a binary `supported_methods`-style listing of `item/commandExecution/requestApproval` under the May-1 vocabulary, a sibling field claiming `availableDecisions` is `preserved: true`, `ready_to_close_ticket: true` for command-approval, or a readiness-delta-style block claiming `ready: true` / "parseable against the current local compatibility boundary" for command-approval response semantics — AND the path's parent object structure cleanly accepts the same legacy-rename + rebaseline-block-add treatment described in Step 3.3. Record each mechanical-mirror path for Task 3. Any additional path that does NOT meet both conditions → fire the stop condition; do not silently extend Task 3's edits to novel shapes.

**Vocabulary caveat (resolved by preserve-and-add).** The JSON's `compatibility_classification` block uses a binary vocabulary: `supported_methods` / `unsupported_methods` / `unknown_or_unparseable_methods` / `missing_required_fields`. The corrected classification we are introducing — *parser-kind compatible but decision-shape lossy* — has no slot in this vocabulary. Mutating `supported_methods` to `[]` while adding new sibling fields would silently shift an existing key's meaning without a vocabulary boundary marker, leaving programmatic readers to interpret `supported_methods: []` under the old binary semantics (which would be a new false historical claim). The same problem applies to `architecture_spec_readiness_delta.ready` — the boolean's meaning under May-1 vocabulary ("parser route exists for the observed method, required correlation fields present") differs from rebaseline ("response semantics proven for the observed method"); flipping `ready: true` → `ready: false` in place would mutate a field's meaning without a vocabulary marker. The preserve-and-add disposition resolves all three sites: the original block is preserved unchanged under a renamed key (`_legacy_compatibility_classification`, `_legacy_architecture_spec_readiness_delta`, etc.), so its old-vocabulary truth remains accessible to any reader who looks; a new block under the canonical key under rebaseline vocabulary is added alongside; an explicit `classification_vocabulary` marker names the active vocabulary; a `classification_supersedes` pointer records the legacy blocks' locations. The pattern applies uniformly: `compatibility_classification` → `_legacy_compatibility_classification` + new canonical block; `observed_server_requests[0].local_compatibility` → `_legacy_local_compatibility` + new canonical field; `architecture_spec_readiness_delta` → `_legacy_architecture_spec_readiness_delta` + new canonical block.

**Consumer discovery (primarily informational, with one stop-condition exception).**

The preserve-and-add disposition does not depend on consumer-marker honoring — the legacy block is preserved verbatim regardless of consumer behavior, and the new block lands under the canonical `compatibility_classification` key so existing readers find rebaseline-current data at the same path. The discovery is primarily informational: it documents which production paths read this JSON and which fields they consume, so future schema changes can target the actual contract rather than assumed convention. The stop-condition exception (see "Stop conditions specific to this step" below) fires only when discovery surfaces a consumer that reads a canonical field whose shape changes under preserve-and-add and does not tolerate the new shape. Run, hidden-aware so paths under `.claude/` surface from repo root:

```bash
rg -n -i --hidden --glob '!.git/**' \
   "compatibility_classification|supported_methods|local_compatibility|architecture_spec_readiness_delta|newly_satisfied_items|still_missing_items|codex-app-server-server-request-envelope-probes\\.json" \
   --type-not md
```

(`--type-not md` excludes documentation references so production consumers surface clearly. `--hidden --glob '!.git/**'` ensures hidden repo paths like `.claude/hooks/` are searched without sweeping `.git/` internals. The pattern includes all three canonical fields undergoing preserve-and-add (`compatibility_classification`, `local_compatibility`, `architecture_spec_readiness_delta`) plus their child field names (`supported_methods`, `newly_satisfied_items`, `still_missing_items`) so consumers reading readiness sub-fields are not missed. As a defensive cross-check against existing named roots if the result above is suspicious: `rg -n -i "<pattern>" packages/ scripts/ extensions/ .claude/hooks/`. Add `.claude/scripts/` or other root paths only if they exist at execution time; do not include non-existent directories or rg will warn / produce noise.)

Classify each match using the same taxonomy below, noting that `architecture_spec_readiness_delta` and its child fields (`ready`, `newly_satisfied_items`, `still_missing_items`) are canonical fields whose shapes change under preserve-and-add, just as `compatibility_classification` and `local_compatibility` do. A consumer reading `.architecture_spec_readiness_delta.ready` under the old vocabulary (boolean meaning "parser route exists") would interpret the new `ready: false` differently than intended (boolean meaning "response semantics proven") — the same vocabulary-shift risk that motivates the preserve-and-add disposition for the other two fields.

Classify each match:

- **Production consumer** — code under `packages/`, `scripts/`, `.claude/hooks/`, `extensions/`, or any executable path that reads the JSON file path or one of the classification field names. Read the consumer code; record (a) which field names it reads and (b) whether it honors any vocabulary-marker convention.
- **Peer diagnostic data artifact** — a sibling or related diagnostic JSON file (e.g., `codex-app-server-scratch-home-runtime-probes.json`, `codex-app-server-materialized-thread-and-server-request-probes.json`) that contains the same field names as data, not as code that reads or interprets the target JSON. These are independent diagnostic captures with their own classification fields; they are NOT consumers of the target JSON's schema. Their own classification vocabulary is governed by whatever plan or diagnostic session produced them — not by this plan.
- **Test fixture / synthetic data** — code that uses these field names for unrelated fixtures. Does not count as a consumer.
- **Self-reference inside the JSON itself** — not a consumer.

Record the consumer-discovery findings explicitly for Task 6's commit message:

- No production consumer found → record "no documented machine consumer at this revision."
- Production consumer found → record file path(s), the field names each consumer reads, and whether each honors any vocabulary-marker convention. This list is the contract Task 3's preserve-and-add disposition must respect (the new `compatibility_classification` block keeps the canonical key name so existing readers find rebaseline-current data; the renamed `_legacy_compatibility_classification` block is for reference and historical-vocabulary readers).

Stop conditions specific to this step:

- JSON structure does not allow preserve-and-add (e.g., `_legacy_compatibility_classification` already exists with different content, or the parent object's schema rejects renamed keys) → fire the "JSON disposition unsafe" stop condition. Surface and ask before proceeding.
- Consumer discovery surfaces a production consumer that reads any canonical field whose shape changes under preserve-and-add AND the consumer code does not tolerate the new shape (e.g., reads `compatibility_classification.supported_methods` directly without falling back to or checking for `fully_supported_methods` / `parser_kind_compatible_methods`) → fire the "JSON disposition unsafe" stop condition. The legacy block alone is not enough — the consumer reads the canonical key and would silently see undefined or malformed data after the new block lands. Surface; the user must decide whether to (a) keep the canonical key under May-1 vocabulary and put the rebaseline block at a non-canonical key (e.g., `compatibility_classification_rebaseline`), (b) update the consumer code to honor the new shape before this plan executes, or (c) defer the JSON reconciliation to a separate plan that can sequence consumer + JSON changes together.

**Derive raw-evidence projection paths (review-cycle 4).**

The plan asserts that the JSON's existing raw-observation fields must remain unchanged under preserve-and-add. To enforce this programmatically, Step 3.2 saves a full pre-edit copy of the JSON file (the immutable reference) and extracts a projection of raw-observation paths from that copy to a temp file. Step 3.6 re-extracts the same projection post-edit and `diff`s the two — empty diff confirms raw evidence is preserved, non-empty diff fails verification and fires the JSON-disposition-unsafe stop condition. If the projection must be re-derived after Step 3.3 begins, it is always re-extracted from the full pre-edit copy, never from the worktree.

The exact `jq` projection MUST be derived against the live JSON during this step, not lifted from the schematic example below. Re-read the JSON's structure (top-level keys, nested key names, array shapes) and confirm that each path you include in the projection (a) actually exists in the file at this revision and (b) corresponds to a raw-observation field, NOT a classification/interpretive field that this plan intends to mutate. Record the final projection verbatim for use in Steps 3.2 and 3.6.

Schematic illustration (DO NOT use as-is — confirm paths against the live JSON):

```bash
jq '{
  artifact_version: .artifact_version,
  params_keys: .params_keys,
  schema_visible_methods: .schema_visible_methods,
  observed_envelopes: [.observed_server_requests[] | {
    method, params_keys, redacted_envelope_summary, available_decisions
  }],
  probes: .probes,
  trigger_command: .trigger_command,
  scratch_environment: .scratch_environment
}' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

The illustrative paths above are likely close based on the cycle-2 enumerated raw-observation fields, but their exact JSON-shape (top-level vs nested, scalar vs array, key spellings) MUST be confirmed by reading the live JSON before this projection lands in Steps 3.2 / 3.6. Paths to INCLUDE: top-level identification metadata (e.g., `artifact_version`, `created_at` if present), envelope captures inside `observed_server_requests[*]` (`method`, `params_keys`, `redacted_envelope_summary`, `available_decisions`), **the entire `.probes` array** (all fields: `name`, `classification`, `status`, `evidence`, `errors`, `request_sequence`, `responses`, `notifications`, `server_requests` — the probes array is the raw observation layer in its entirety; it contains the verbatim wire envelope under `.probes[*].server_requests[*].{id,method,params}`, per-probe pass/fail status, response absence evidence ("No approval response was sent"), and classification strings that are captured-as-observed rather than authored-as-interpretation; `observed_server_requests` is a derived summary, NOT the raw capture), schema-visible method listings, scratch environment metadata, trigger command, modified-paths arrays. Paths to EXCLUDE (all classification/interpretive fields are EXPECTED to mutate, including under `_legacy_*` renamed forms — the rename itself is a structural mutation): `compatibility_classification`, `_legacy_compatibility_classification`, `local_compatibility`, `_legacy_local_compatibility`, `architecture_spec_readiness_delta`, `_legacy_architecture_spec_readiness_delta`, `classification_vocabulary`, `classification_supersedes`.

If the live JSON has a path that LOOKS LIKE a classification field but is actually raw observation (e.g., a `notes` array immediately under `observed_server_requests[*]` that is captured-as-observed rather than authored-as-interpretation), include it in the projection AND record the rationale. Workers should err toward over-projection; a false positive (pre/post diff fires on a legitimate edit) is recoverable in Step 3.6 (re-derive the projection minus the false-positive path and re-run), while a false negative (raw evidence mutated silently because it wasn't projected) is the failure mode this enforcement exists to prevent.

**Temp-file path convention.** Steps 3.2 and 3.6 use deterministic paths under `/private/tmp` rather than bare `/tmp` (avoids macOS `/tmp` symlink ambiguity and shell-rewriting surprises) and include the plan's slug for collision avoidance:

- `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json` — full pre-edit copy of the entire JSON file (immutable reference; source for all projection extractions including re-derivations after Step 3.3 begins).
- `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json` — pre-edit projection snapshot (extracted from the full pre-edit copy, not the worktree).
- `/private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json` — post-edit projection snapshot (extracted from the worktree in Step 3.6).
- `/private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json` — pre-edit interpretive-block snapshot: the three classification blocks (`compatibility_classification`, `observed_server_requests[0].local_compatibility` + sibling notes, `architecture_spec_readiness_delta`) captured before renaming. Used by Step 3.6b to verify the `_legacy_*` blocks are verbatim copies.
- `/private/tmp/codex-collab-overclaim-fix-legacy-blocks-post.json` — post-edit legacy-block snapshot: the renamed `_legacy_*` blocks with `_vocabulary_note` stripped. Used by Step 3.6b's diff.

Step 3.6's diff command compares the pre-edit projection against the post-edit projection. All temp files persist across Steps 3.2-3.5 (do NOT delete them before Step 3.6 runs); Step 3.6 uses `trash` to delete them on successful diff or preserves them for inspection on failed diff.

Task 3 implements the preserve-and-add structure described above using the consumer-discovery findings recorded here. Task 3's verification (Step 3.6 raw-evidence diff) uses the projection derived in this sub-section.

- [ ] **Step 1.5: Determine register-annotation need AND prove "landed on `main`" with git evidence.**

Sub-step 1.5a — register inspection.

Read `docs/status/codex-collaboration-reconciliation-register.md:9-70`. Check:

- Does the priority `#1` line at ~line 52 still say "Implement `T-20260429-01` Phase 1 sandbox carve-outs"?
- Does the `T-20260429-01` row "Current truth" cell at ~line 67 still describe the work as unlanded?
- Does the `T-20260429-01` row "Exit condition" cell at ~line 67 still say "Land the Phase 1 sandbox carve-outs and validate via a comparable smoke run..."?

If all three already reflect landed-implementation status (priority line names closure-evidence work, current truth records implementation has landed, exit condition names AC #1-#3 closure work) → Task 4 is a no-op. Skip it; do not edit the register.

If any still imply implementation is pending → Task 4 will land annotations on the affected cells.

Sub-step 1.5b — git proof for "landed on `main`".

Before Task 4 writes "have landed on `main`" into the register, prove the claim with git evidence. Two checks must both pass:

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

- **Carve-outs visible at lines 107-118** → record "lines 107-118 confirmed." Proceed.
- **Carve-outs visible but at different line numbers** (line drift) → record the actual line range, update ALL `runtime.py:107-118` references in Task 4 (Step 4.2's annotation, Step 4.3's priority-line replacement text, AND Step 4.4's exit-condition replacement text) to reference the correct lines, and proceed. This is NOT a stop-condition failure; the implementation landed, only the line reference drifted.
- **Zero matches** (implementation not landed, or `git diff main..HEAD` is non-empty for `runtime.py`) → fire the "Register-annotation `main`-truth check failed" stop condition. Skip Task 4 entirely; surface so the register-annotation premise can be reconciled before any annotation is written. (Distinct from "Live envelope evidence has changed" — the envelope is unchanged; the failure is about `main`'s `runtime.py` state diverging from what Task 4's annotation would claim.)

Record both checks' outcomes (the diff is empty, or it is not; the lines on `main` are X-Y showing the carve-outs). Task 4.2's wording depends on this proof — without it, "landed on `main`" is an unverified claim.

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
This packet proves parser-kind compatibility (envelope parsing succeeds and maps to `kind=command_approval`) for the observed command-approval envelope only. It does not establish response-shape compatibility — the observed mixed `availableDecisions` triggers parser fallback per `_resolve_available_decisions` (see "Local compatibility judgment" above). It does not prove live reachability or parser cleanliness for file-change, permission, tool-input, MCP elicitation, auth-refresh, or other schema-visible server-request methods.
```

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
- the observed `item/commandExecution/requestApproval` envelope is parseable via the parser's decision-shape-lossy fallback path; lossless preservation of `availableDecisions` is NOT established (see "Local compatibility judgment" above)

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

```bash
# Each grep must exit 0 (pattern found). Run all six; any non-zero exit means a raw fact was mutated.
grep -qF 'item/commandExecution/requestApproval' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF '"acceptWithExecpolicyAmendment"' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF 'availableDecisions' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF '/bin/zsh -lc' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF 'No approval response was sent' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
grep -qF 'itemId' docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
```

Expected: all six exit `0`. These anchors correspond to:
- The observed method string (`item/commandExecution/requestApproval`)
- The structured decision entry (`"acceptWithExecpolicyAmendment"`)
- The wire field name (`availableDecisions`)
- The trigger command (`/bin/zsh -lc`)
- The response-absence record (`No approval response was sent`)
- A required correlation field (`itemId`)

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
| JSON exists, has parallel overclaim (preserve-and-add applies) | Step 3.2 (pre-edit raw-evidence snapshot) → Step 3.3 (apply preserve-and-add) → Steps 3.4-3.7. |
| JSON disposition unsafe (structure does not allow preserve-and-add, or `_legacy_*` key already exists with different content) | Stop condition fired in Task 1.4; surface to user. |

- [ ] **Step 3.2: Capture pre-edit raw-evidence snapshot (cycle-4 addition; only if Step 3.3 will run).**

Run before any JSON edits. Two captures:

1. **Full pre-edit copy** — a byte-identical copy of the entire JSON file before any mutation. This is the immutable reference for all subsequent projection extractions, including re-derivations.
2. **Projection snapshot** — extracted from the full pre-edit copy (NOT from the worktree) using the `jq` projection derived in Task 1.4.

```bash
# Guard: if a pre-edit snapshot already exists, a prior partial run may have
# mutated the worktree. Do NOT overwrite — the existing snapshot is the only
# trustworthy pre-mutation reference. Investigate and resolve before proceeding.
test ! -e /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json \
  || { echo "STOP: pre-edit snapshot already exists — prior partial run?" >&2; exit 1; }
test ! -e /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json \
  || { echo "STOP: projection snapshot already exists — prior partial run?" >&2; exit 1; }
test ! -e /private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json \
  || { echo "STOP: legacy-block snapshot already exists — prior partial run?" >&2; exit 1; }

# 1. Full pre-edit copy (immutable reference for the remainder of Task 3)
cp docs/diagnostics/codex-app-server-server-request-envelope-probes.json \
   /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json

# 2. Projection snapshot (extracted from the full pre-edit copy, not the worktree)
jq '<projection from Task 1.4>' \
   /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json \
   > /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json

# 3. Legacy-block snapshot (the three interpretive blocks that Step 3.3 will rename)
jq '{
  compatibility_classification: .compatibility_classification,
  local_compatibility: .observed_server_requests[0].local_compatibility,
  local_compatibility_notes: .observed_server_requests[0].local_compatibility_notes,
  architecture_spec_readiness_delta: .architecture_spec_readiness_delta
}' /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json \
   > /private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json
```

If the guard fires, this means a previous partial execution of Task 3 left temp files behind. Determine the worktree state before choosing a recovery path:

```bash
git diff --stat docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

- **(a) `git diff` is empty (worktree matches `HEAD`)** — Step 3.3 never ran or was fully reverted. Safe to `trash` the temp files and re-run Step 3.2.
- **(b) `git diff` shows changes AND they are solely Step 3.3 mutations** (added `_legacy_*` keys, `classification_vocabulary`, `classification_supersedes`; renamed classification blocks; no raw-observation changes) — restore the worktree JSON from the full pre-edit copy (`cp /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json docs/diagnostics/codex-app-server-server-request-envelope-probes.json`), then `trash` all temp files and re-run Step 3.2. Do NOT restore without first confirming the diff contains only Step 3.3-shaped mutations — if it contains unexpected changes (manual edits, raw-observation mutations, changes outside the three disposition sites), STOP and surface to the user.
- **(c) `git diff` shows changes that are NOT recognizably Step 3.3 mutations** — STOP. The worktree JSON has changes whose provenance is unknown. Surface to the user; do not restore from the temp copy until the changes are accounted for.

(Replace `<projection from Task 1.4>` with the actual `jq` filter recorded in Task 1.4. Do NOT use the schematic illustration from Task 1.4 verbatim — it must be confirmed against the live JSON's actual paths.)

Expected: all three extraction commands exit `0`; all three temp files exist and contain valid JSON. Verify with `jq '.' /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json >/dev/null && jq '.' /private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json >/dev/null` (both exit `0`). If the raw-evidence projection check fails, the projection is malformed; re-derive in Task 1.4 and re-extract from the full pre-edit copy (step 2 above) — never from the worktree. If the legacy-block extraction fails, confirm the `jq` paths match the live JSON's key names (check the third extraction command's field paths against the actual JSON structure).

All temp files persist across Steps 3.3, 3.4, 3.5, 3.6, 3.6b, and 3.6c — do NOT delete them before Step 3.6c completes. Steps 3.6b and 3.6c delete them on successful completion or preserve them for inspection on failure. The full pre-edit copy is the authoritative pre-mutation reference; if the projection must be re-derived at any point after Step 3.3 begins, re-extract from `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json`, never from the worktree file (which may already be mutated).

- [ ] **Step 3.3: Apply preserve-and-add disposition (only if Step 3.2 ran).**

The JSON is mutated structurally (new keys + renamed keys), but no existing field's value or meaning is altered in place. The original `compatibility_classification`, `local_compatibility`, and `architecture_spec_readiness_delta` blocks are preserved verbatim under renamed keys with their old May-1 parser-route vocabulary semantics intact; new blocks under the same canonical key names under the rebaseline vocabulary are added alongside; explicit vocabulary marker and supersedes-pointer fields document the boundary.

After all edits, the JSON's existing raw-observation fields (params keys, redacted envelope summary, observed `availableDecisions` array, schema-visible methods listing, per-probe pass/fail rows, etc.) must remain unchanged. Step 3.6 enforces this programmatically by `diff`ing the post-edit projection against the Step 3.2 pre-edit snapshot.

Editing method: use the Edit tool with enough surrounding context for unique matches (minimum 3-5 lines of unchanged JSON above and below each edit site). Avoid `jq` transforms for structural edits — key reordering would invalidate Step 3.6's byte-identical diff assumption.

1. **Add a top-level `classification_vocabulary` marker** (next to `artifact_version`):

   ```json
   "classification_vocabulary": "rebaseline_parser_kind_and_response_shape_v1"
   ```

   This names the vocabulary used by all non-`_legacy_*` classification fields below. The `_v1` suffix allows future vocabulary revisions to bump this marker without breaking the preserve-and-add convention.

2. **Add a top-level `classification_supersedes` pointer** (next to `classification_vocabulary`):

   ```json
   "classification_supersedes": {
     "legacy_blocks": [
       "$._legacy_compatibility_classification",
       "$.observed_server_requests[0]._legacy_local_compatibility",
       "$._legacy_architecture_spec_readiness_delta"
     ],
     "legacy_vocabulary": "may_1_parser_route_v1",
     "fix_doc": "docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md",
     "authority": "docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md#L905-L921",
     "summary": "May-1 parser-route classification preserved under _legacy_* keys (paths in JSONPath notation); rebaseline-vocabulary classification under canonical keys names parser-kind compatibility and decision-shape lossiness. Architecture-readiness assertion (legacy: ready=true with parseable-against-boundary newly-satisfied item) preserved verbatim under _legacy_architecture_spec_readiness_delta; new canonical block carries ready=false with decision-shape lossy fallback named as a remaining response-semantics blocker."
   }
   ```

3. **Rename `compatibility_classification` → `_legacy_compatibility_classification`** (≈line 911). Preserve all contents verbatim. Add a single sibling field inside the renamed block to remind readers of its vocabulary:

   ```json
   "_legacy_compatibility_classification": {
     "_vocabulary_note": "May-1 parser-route vocabulary (see top-level classification_supersedes). 'supported' here means: local code has a concrete route for the method and required correlation fields are present.",
     "status": "passed",
     "supported_methods": ["item/commandExecution/requestApproval"],
     "unsupported_methods": [],
     "unknown_or_unparseable_methods": [],
     "missing_required_fields": [],
     "notes": [
       "A live schema-visible command approval envelope was observed and is parseable against the current local parser/runtime boundary.",
       "Current local support remains narrower than the full schema-visible method set; unobserved methods remain explicit risks.",
       "Fail-closed handling for unobserved methods is not treated as semantically clean lifecycle proof."
     ]
   }
   ```

   (Snippet is **schematic**: the `_vocabulary_note` field is new and added by this step, but `supported_methods`, `unsupported_methods`, `unknown_or_unparseable_methods`, `missing_required_fields`, and `notes` are preserved VERBATIM from the existing `compatibility_classification` block — the values shown above were captured at plan-write time. Re-read the live JSON during Task 1.4 and copy the actual current values rather than the values shown here, in case the JSON has drifted since plan-write time.)

4. **Add a new `compatibility_classification` block** alongside the renamed one, under rebaseline vocabulary:

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
       "item/commandExecution/requestApproval is parser-kind compatible (route exists, required correlation fields itemId/threadId/turnId present) but decision-shape lossy under the observed mixed availableDecisions: the structured acceptWithExecpolicyAmendment entry triggers the all-strings fallback in _resolve_available_decisions (approval_router.py:103-111). The fallback tuple _AVAILABLE_DECISIONS[command_approval] = ('accept', 'acceptForSession', 'acceptWithExecpolicyAmendment', 'applyNetworkPolicyAmendment', 'decline', 'cancel') preserves the wire's accept and cancel, collapses the structured acceptWithExecpolicyAmendment entry into a bare string (payload dropped), and adds three decisions never offered by the wire (acceptForSession, applyNetworkPolicyAmendment, decline)."
     ]
   }
   ```

5. **Rename `observed_server_requests[0].local_compatibility` → `observed_server_requests[0]._legacy_local_compatibility`** (≈line 904). Preserve the value (`"supported"`) verbatim. If a `local_compatibility_notes` sibling field exists at this path under the legacy form, also rename it to `_legacy_local_compatibility_notes` (preserve the array contents verbatim).

6. **Add a new `local_compatibility` field** alongside `_legacy_local_compatibility` on the same request object, under rebaseline vocabulary:

   ```json
   "local_compatibility": "parser_kind_compatible_decision_shape_lossy",
   "local_compatibility_notes": [
     "Decision-shape lossy under the observed mixed availableDecisions: the structured acceptWithExecpolicyAmendment entry triggers all-strings fallback in _resolve_available_decisions (approval_router.py:103-111). The fallback tuple _AVAILABLE_DECISIONS[command_approval] = ('accept', 'acceptForSession', 'acceptWithExecpolicyAmendment', 'applyNetworkPolicyAmendment', 'decline', 'cancel') preserves the wire's accept and cancel, collapses the structured acceptWithExecpolicyAmendment into a bare string (payload dropped), and adds three decisions never offered by the wire (acceptForSession, applyNetworkPolicyAmendment, decline)."
   ]
   ```

7. **Rename `architecture_spec_readiness_delta` → `_legacy_architecture_spec_readiness_delta`** (≈line 45580; cycle-4 addition). Preserve all contents verbatim. Add a single sibling field inside the renamed block to remind readers of its vocabulary:

   ```json
   "_legacy_architecture_spec_readiness_delta": {
     "_vocabulary_note": "May-1 parser-route vocabulary (see top-level classification_supersedes). 'ready' here means: parser route exists for the observed method and required correlation fields are present; 'parseable against the current local compatibility boundary' refers to parser-kind compatibility, not response-shape compatibility.",
     "ready": true,
     "newly_satisfied_items": [
       "Scratch auth was established under isolated CODEX_HOME without credential copying.",
       "A live schema-visible server-request envelope was captured and redacted safely.",
       "The observed item/commandExecution/requestApproval envelope is parseable against the current local compatibility boundary."
     ],
     "still_missing_items": [
       "Envelope coverage for other schema-visible server-request methods remains unobserved and should be carried as explicit risk if relied upon.",
       "Fail-closed lifecycle cleanliness for unsupported or unknown methods remains a separate runtime-quality concern."
     ]
   }
   ```

   (Snippet is **schematic**: the `_vocabulary_note` field is new and added by this step; `ready`, `newly_satisfied_items`, and `still_missing_items` are preserved VERBATIM from the existing `architecture_spec_readiness_delta` block — the values shown above were captured at plan-write time. Re-read the live JSON during Task 1.4 and copy the actual current values rather than the values shown here, in case the JSON has drifted since plan-write time.)

8. **Add a new `architecture_spec_readiness_delta` block** alongside the renamed one, under rebaseline vocabulary:

   ```json
   "architecture_spec_readiness_delta": {
     "ready": false,
     "newly_satisfied_items": [
       "Scratch auth was established under isolated CODEX_HOME without credential copying.",
       "A live schema-visible server-request envelope was captured and redacted safely.",
       "The observed item/commandExecution/requestApproval envelope is parseable via the parser's decision-shape-lossy fallback path; lossless preservation of availableDecisions is NOT established."
     ],
     "still_missing_items": [
       "Envelope coverage for other schema-visible server-request methods remains unobserved and should be carried as explicit risk if relied upon.",
       "Fail-closed lifecycle cleanliness for unsupported or unknown methods remains a separate runtime-quality concern.",
       "A lossless parser/response branch for command-approval that preserves availableDecisions shape without falling back to _AVAILABLE_DECISIONS[command_approval] (see docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md 'Command Approval Decision-Shape Boundary')."
     ],
     "notes": [
       "ready=false because command-approval response semantics are not proven: _resolve_available_decisions (approval_router.py:103-111) falls back to _AVAILABLE_DECISIONS[command_approval] = ('accept', 'acceptForSession', 'acceptWithExecpolicyAmendment', 'applyNetworkPolicyAmendment', 'decline', 'cancel') under the observed mixed availableDecisions, collapsing the structured acceptWithExecpolicyAmendment payload and adding three decisions never offered by the wire. The architecture spec can proceed only if it explicitly carries this lossy fallback as an unresolved response-semantics risk for command-approval."
     ]
   }
   ```

9. **Apply the same preserve-and-add to any additional mechanical-mirror paths** identified in Task 1.4 (per the narrow exception). For each: rename existing key with `_legacy_` prefix; add new key under the rebaseline vocabulary referencing the same fallback explanation. Do not improvise on novel shapes — those should have stopped Task 1.4.

10. **Any field claiming `availableDecisions` is `preserved: true`** (if surfaced as a mechanical-mirror path): rename to `_legacy_availability_preservation` (or analogous `_legacy_*` key matching the original key name) and add a new sibling field under the rebaseline vocabulary naming the all-strings fallback. Use the same fallback-tuple wording.

11. **Any field flagged `ready_to_close_ticket: true` for command-approval** (if surfaced as a mechanical-mirror path): rename to `_legacy_ready_to_close_ticket` and add a new sibling field set to `false` with a note naming the missing closure work (smoke + credential-boundary probe + lossless parser/response branch).

Do not delete or rewrite raw observation fields (params keys, redacted envelope summary, observed `availableDecisions` array, etc.).

- [ ] **Step 3.4: Validate JSON (only if Step 3.3 ran).**

```bash
jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json >/dev/null
```

Expected: exit `0`. If non-zero, fix the JSON before staging.

- [ ] **Step 3.5: Local rg verification (only if Step 3.3 ran).**

```bash
rg -n -i "supported|preserved|ready_to_close_ticket|architecture_spec_readiness_delta|newly_satisfied_items|parseable against" \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected:

- The `_legacy_compatibility_classification` block still matches `supported_methods` because its contents are intentionally preserved verbatim under May-1 parser-route vocabulary. This is acceptable: the `_legacy_` prefix combined with the top-level `classification_vocabulary` marker scopes the legacy block's "supported" semantics explicitly to May-1 vocabulary; future readers see clean reclassification rather than mutated history.
- The new `compatibility_classification` block must NOT contain `supported_methods` as a non-empty array under the rebaseline vocabulary — it should have `fully_supported_methods: []`, with `parser_kind_compatible_methods` and `decision_shape_lossy_methods` carrying the actual method.
- The new `local_compatibility` field (alongside `_legacy_local_compatibility`) must NOT contain bare `"supported"` — it should name the lossy class (e.g., `"parser_kind_compatible_decision_shape_lossy"`).
- The `_legacy_architecture_spec_readiness_delta` block matches `architecture_spec_readiness_delta`, `newly_satisfied_items`, and `parseable against` because its contents are intentionally preserved verbatim under May-1 parser-route vocabulary (cycle-4 addition). This is acceptable for the same reason as `_legacy_compatibility_classification`.
- The new `architecture_spec_readiness_delta` block (alongside `_legacy_architecture_spec_readiness_delta`) must contain `ready: false` (NOT `true`); its `newly_satisfied_items` third bullet must qualify "parseable" as decision-shape-lossy fallback (NOT bare "parseable against"); its `still_missing_items` must include the lossless parser/response branch as a remaining requirement.
- No surviving `preserved: true` or `ready_to_close_ticket: true` for command-approval outside of `_legacy_*` blocks. No surviving `architecture_spec_readiness_delta.ready: true` outside `_legacy_*` blocks.

Cross-check: every line returned by the sweep should be classifiable as either (a) inside a `_legacy_*` block (acceptable — preserved-vocabulary semantics), (b) inside the new rebaseline block (acceptable — names parser-kind compatibility / decision-shape lossiness / response-semantics-risk explicitly), or (c) raw observation outside any classification block (acceptable — evidence layer). Any line that does NOT classify as one of these → return to Step 3.3; the preserve-and-add was incomplete or a mechanical-mirror path was missed in Task 1.4.

- [ ] **Step 3.6: Post-edit raw-evidence diff (cycle-4 addition; only if Step 3.3 ran).**

Re-extract the same `jq` projection as Step 3.2 (the projection derived in Task 1.4) from the post-edit JSON, then `diff` against the pre-edit snapshot at `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json`:

```bash
jq '<projection from Task 1.4>' \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json \
   > /private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json

diff -u /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json \
        /private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json
```

Expected: `diff` exits `0` with empty output. The projection covers raw-observation fields only; if Step 3.3 mutated only classification/interpretive fields (as the plan requires), the projection's output should be byte-identical pre- and post-edit. If the edit mechanism preserved JSON key ordering (e.g., Edit tool), the diff should be byte-identical. If a `jq` transform was used for any Step 3.3 edit, pipe both projections through `python3 -m json.tool --sort-keys` before diffing to normalize key ordering.

- **Diff is empty (exit `0`)** → raw evidence is preserved. Do NOT delete temp files yet — Step 3.6b still needs them. Proceed to Step 3.6b.
- **Diff is non-empty** → fire the JSON-disposition-unsafe stop condition. Either Step 3.3 mutated a raw-observation field (regression — surface the specific path, the pre-value, and the post-value to the user; revert the JSON edit and re-attempt Step 3.3 with that path treated as immutable) OR the projection in Task 1.4 included a path that should be excluded (false positive — re-derive the projection from the full pre-edit copy at `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json`, replace it in Steps 3.2 / 3.6, and re-run the projection extraction from the full pre-edit copy; do NOT re-run Step 3.2's full-copy capture or re-read the worktree file). Preserve all temp files for inspection; do NOT delete them. Do NOT stage the JSON until the diff is empty.

If the projection's correctness is itself in question (e.g., Task 1.4 was deferred or rushed), prefer the failing-diff-as-stop interpretation over the false-positive interpretation; Task 1.4 is the load-bearing step and is not bypassed by Step 3.6 finding a diff.

- [ ] **Step 3.6b: Legacy-block preservation diff (scrutiny follow-up; only if Step 3.6 passed).**

Step 3.6 verifies raw-observation preservation. This step verifies the other half of the preserve-and-add promise: that the `_legacy_*` blocks are verbatim copies of the original interpretive blocks. The raw-evidence projection explicitly EXCLUDES classification fields, so a worker who accidentally modifies `_legacy_compatibility_classification.notes` or `_legacy_architecture_spec_readiness_delta.newly_satisfied_items` would pass Step 3.6 cleanly.

Extract the renamed `_legacy_*` blocks from the post-edit worktree JSON, stripping the added `_vocabulary_note` fields (which are new and should NOT be compared), then diff against the pre-edit legacy-block snapshot from Step 3.2:

```bash
# Extract _legacy_* blocks from post-edit JSON, stripping _vocabulary_note
jq '{
  compatibility_classification: ._legacy_compatibility_classification | del(._vocabulary_note),
  local_compatibility: .observed_server_requests[0]._legacy_local_compatibility,
  local_compatibility_notes: .observed_server_requests[0]._legacy_local_compatibility_notes,
  architecture_spec_readiness_delta: ._legacy_architecture_spec_readiness_delta | del(._vocabulary_note)
}' docs/diagnostics/codex-app-server-server-request-envelope-probes.json \
   > /private/tmp/codex-collab-overclaim-fix-legacy-blocks-post.json

diff -u /private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json \
        /private/tmp/codex-collab-overclaim-fix-legacy-blocks-post.json
```

(The `jq` paths above use the pre-edit field names as output keys and the post-edit `_legacy_*` paths as input, so the diff compares the same logical content under normalized key names. The `del(._vocabulary_note)` exclusion strips the one field that Step 3.3 legitimately adds inside the renamed block. Confirm that the `jq` path names match the actual live JSON at execution time — the paths shown here match the plan-write-time structure but the JSON may have drifted.)

Expected: `diff` exits `0` with empty output.

- **Diff is empty (exit `0`)** → legacy blocks are preserved verbatim. Do NOT delete temp files yet — Step 3.6c still needs them. Proceed to Step 3.6c.
- **Diff is non-empty** → a `_legacy_*` block was modified during the rename. This is a data integrity failure: the plan promises verbatim preservation and the diff proves otherwise. Surface the specific differing paths and values. The recovery is to re-read the original block from `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json` and copy the exact content into the `_legacy_*` block, then re-run Step 3.6b. Do NOT stage the JSON until all of Steps 3.6, 3.6b, AND 3.6c pass.

- [ ] **Step 3.6c: Canonical-value assertions (only if Steps 3.6 + 3.6b passed).**

Steps 3.6 and 3.6b verify that raw evidence is unchanged and legacy blocks are verbatim. This step verifies the positive claim: that the NEW canonical blocks carry the intended rebaseline vocabulary values. The `rg` sweep can match key names but cannot reliably assert nested JSON boolean state; `jq -e` is the correct tool for that invariant.

```bash
# Canonical value assertions (rebaseline vocabulary)
jq -e '.architecture_spec_readiness_delta.ready == false' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.observed_server_requests[0].local_compatibility == "parser_kind_compatible_decision_shape_lossy"' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.compatibility_classification.status == "parser_kind_compatible_decision_shape_lossy"' docs/diagnostics/codex-app-server-server-request-envelope-probes.json

# Canonical array assertions (structural completeness — scrutiny follow-up 6)
jq -e '.compatibility_classification.fully_supported_methods == []' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.compatibility_classification.parser_kind_compatible_methods == ["item/commandExecution/requestApproval"]' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.compatibility_classification.decision_shape_lossy_methods == ["item/commandExecution/requestApproval"]' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.architecture_spec_readiness_delta.still_missing_items | length >= 3' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.architecture_spec_readiness_delta.still_missing_items | any(test("lossless parser/response branch"))' docs/diagnostics/codex-app-server-server-request-envelope-probes.json

# Legacy preservation assertions (compare against pre-edit snapshot, not hard-coded values)
# These assertions use the pre-edit legacy-block snapshot from Step 3.2 as the expected-value
# source, so they remain correct even if the live JSON has drifted from plan-write-time values.
PRE_LEGACY=/private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json
jq -e --argjson expected "$(jq '.architecture_spec_readiness_delta.ready' "$PRE_LEGACY")" \
  '._legacy_architecture_spec_readiness_delta.ready == $expected' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e --arg expected "$(jq -r '.local_compatibility' "$PRE_LEGACY")" \
  '.observed_server_requests[0]._legacy_local_compatibility == $expected' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e --arg expected "$(jq -r '.compatibility_classification.status' "$PRE_LEGACY")" \
  '._legacy_compatibility_classification.status == $expected' docs/diagnostics/codex-app-server-server-request-envelope-probes.json

# Vocabulary marker assertions (schema-boundary proof)
jq -e '.classification_vocabulary == "rebaseline_parser_kind_and_response_shape_v1"' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.classification_supersedes.legacy_blocks == ["$._legacy_compatibility_classification", "$.observed_server_requests[0]._legacy_local_compatibility", "$._legacy_architecture_spec_readiness_delta"]' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.classification_supersedes.legacy_vocabulary == "may_1_parser_route_v1"' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq -e '.classification_supersedes.fix_doc != null' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected: all fifteen assertions exit `0`. If any fails:

- A canonical assertion fails → the preserve-and-add edit in Step 3.3 is incomplete or used wrong vocabulary. Fix the specific field and re-run from Step 3.6 (the full pre-edit copy is the recovery reference if needed).
- A legacy assertion fails → the legacy block was mutated during renaming. This should already have been caught by Step 3.6b, but serves as a defense-in-depth check. Recovery is the same as Step 3.6b's failure path.
- A vocabulary marker assertion fails → Step 3.3 items 1-2 (add `classification_vocabulary` and `classification_supersedes`) are incomplete or malformed. Fix the specific marker and re-run from Step 3.6c (raw-evidence and legacy-block diffs do not need re-running — marker fields are additive and do not affect either projection).

All fifteen pass → delete temp files (`trash /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json /private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json /private/tmp/codex-collab-overclaim-fix-raw-evidence-post.json /private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json /private/tmp/codex-collab-overclaim-fix-legacy-blocks-post.json`). If `trash` is unavailable, leave the temp files in place and report their paths — do NOT use `rm`.

Do NOT stage the JSON until all of Steps 3.6, 3.6b, AND 3.6c pass.

- [ ] **Step 3.7: Stage the JSON change (only if Step 3.3 ran AND Steps 3.6 + 3.6b + 3.6c passed).**

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
As of 2026-05-09, Phase 1 sandbox carve-outs (Options B + E + ~/.agents/ + dynamic gitdir) have landed on `main` (`packages/plugins/codex-collaboration/server/runtime.py:107-118`). Closure evidence remains missing for ticket acceptance criteria #1 (comparable `/delegate` smoke with avoidable sandbox-friction escalations ≤2), #2 (credential-boundary probe), and #3 (`test_runtime.py` regression assertion updated and full codex-collaboration test suite passing). Acceptance criterion #4 (Option F upstream limitation) is already checked. The ticket therefore remains open; the work shape changes from "implement" to "record closure evidence and close."
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

- [ ] **Step 5.2: Classify every match.**

Apply the Sweep Classification Rules from the top of this plan. Acceptable terminal classifications:

- `raw-observation` (preserved evidence) → OK.
- `corrected-language` (post-patch wording — should now describe lossy fallback or parser-kind compatibility) → OK.
- `legacy-parser-route-vocabulary` (T-20260429-02 ticket parser-route table, May-1 probe-plan vocabulary definitions) → OK.
- `authority-source` (rebaseline plan "Command Approval Decision-Shape Boundary" section at lines 905-921; uses rebaseline-era framing, not May-1 vocabulary) → OK.
- `unrelated` (different context, e.g., "supported sandbox carve-outs") → OK.
- `peer-diagnostic-data-artifact` (sibling diagnostic JSON files containing the same field names from their own probe sessions — independent captures, not claims about the target method) → OK.

Unacceptable: `interpretive-overclaim` → STOP. Do not commit. Surface to the user with file path, line number, current text, and proposed correction.

Cross-check against the Task 1.1 baseline classification: any match that was tagged `interpretive-overclaim` in Task 1.1 must now classify as `corrected-language` or its enumerated patch site must be reflected in the staged diff. Any new `interpretive-overclaim` match (not in the Task 1.1 baseline) is a surviving overclaim regardless of cause.

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

The rebaseline plan at `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:204-220` contains `jq` commands and expected-value bullets that read canonical JSON fields whose vocabulary this plan changes. After Task 3's preserve-and-add disposition:

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
- `local_compatibility` is `parser_kind_compatible_decision_shape_lossy` (post-overclaim-fix canonical vocabulary; legacy value `"supported"` preserved at `_legacy_local_compatibility`). The label already reflects the decision-shape-lossy classification introduced by the envelope-diagnostic overclaim fix.
- `architecture_spec_readiness_delta.ready` is `false` (post-overclaim-fix canonical vocabulary; legacy value `true` preserved at `_legacy_architecture_spec_readiness_delta.ready`). Readiness is false because lossless `availableDecisions` preservation is not established for the observed command-approval envelope.
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

Expected: every match either (a) appears in a `jq` command that will extract the new canonical value, (b) appears in an expected-value bullet that names the new vocabulary, or (c) appears in the "Command Approval Decision-Shape Boundary" section (lines 905-921) which is an authority source, not a consumer of the JSON. No match should assert `local_compatibility` is `"supported"` or `architecture_spec_readiness_delta.ready` is `true` without a `_legacy_` qualifier.

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

**Files:** previously staged via Steps 2.8, 3.7 (conditional), 4.6 (conditional), 5.5 (conditional — only when Task 3 ran).

- [ ] **Step 6.1: Confirm staged set.**

```bash
git status
```

Expected: only the planned docs files appear in `git status` as staged — `docs/diagnostics/` targets, optionally `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` (Task 3), optionally `docs/status/codex-collaboration-reconciliation-register.md` (Task 4), and optionally `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` (Step 5.5, conditional on Task 3). Pre-existing unrelated unstaged changes recorded in Task 0 may still be present in the working tree; that is acceptable. Confirm only the planned docs are staged for commit.

- [ ] **Step 6.2: Commit.**

**Edit the heredoc body before running the commit command (cycle-4 template).** The body below contains two CONDITIONAL paragraphs marked with `<!-- CONDITIONAL: ... -->` and `<!-- END CONDITIONAL -->` HTML-style markers. Edit the heredoc body so that:

- For each CONDITIONAL block whose corresponding task RAN (Task 3 staged the JSON via Step 3.7; Task 4 staged the register via Step 4.6), DELETE the `<!-- CONDITIONAL: ... -->` and `<!-- END CONDITIONAL -->` marker lines and KEEP the paragraph text between them.
- For each CONDITIONAL block whose corresponding task was SKIPPED, DELETE both marker lines AND the paragraph text between them entirely.

After editing, the body should contain only the sections that match the actually-staged file set from Steps 2.8, 3.7 (conditional), 4.6 (conditional), and 5.5 (conditional — same condition as Task 3). The opening parser-correction paragraph and closing scope-unchanged paragraph are always retained.

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

<!-- CONDITIONAL: include only if Task 3 ran (JSON disposition applied; Step 3.7 staged the JSON). -->
Programmatic pre/post jq-projection verification confirmed
byte-identical raw-evidence preservation across the JSON edits.
The sibling JSON is reconciled via preserve-and-add: the original
`compatibility_classification`, `local_compatibility`, and
`architecture_spec_readiness_delta` blocks are renamed with a
`_legacy_` prefix (preserving their May-1 parser-route vocabulary
verbatim — the original `supported_methods:
["item/commandExecution/requestApproval"]` remains historically true
under that vocabulary, as does `architecture_spec_readiness_delta.ready:
true` under May-1 parser-kind-only readiness vocabulary), and new
blocks under the canonical key names carry rebaseline-vocabulary
classification (`fully_supported_methods: []`; `parser_kind_compatible_methods`
and `decision_shape_lossy_methods` enumerate the method explicitly;
`architecture_spec_readiness_delta.ready: false` with the lossy
fallback named in `still_missing_items` as a remaining
response-semantics blocker). A top-level
`classification_vocabulary: "rebaseline_parser_kind_and_response_shape_v1"`
marker names the active vocabulary; `classification_supersedes`
documents the legacy blocks. Pre/post jq-projection of raw-observation
paths confirmed byte-identical preservation of envelope captures,
params keys, and probe rows. The rebaseline implementation plan's
evidence-check section (lines 204-220) is updated so its `jq`
expected-value bullets reflect the new canonical vocabulary — without
this, a future worker would hit a false evidence mismatch.
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

- The commit lists only `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` and any conditional files staged in Steps 3.7 / 4.6 / 5.5. No code files. Pre-existing unrelated unstaged changes from Task 0's snapshot may still be present in `git status`; verify those are unchanged from the snapshot (this plan's edits should not have modified them).
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
  5. Stop condition for JSON disposition → "Stop Conditions" section + Task 1.4 (preserve-and-add disposition + consumer discovery as informational contract record) + Task 3 (preserve-and-add structural edits).
  6. Verification rg pattern covers bare-word terms (`supported`/`preserved`/`lossy`/`ready_to_close_ticket`) plus phrase patterns (`proves compatibility`/`compatibility for the observed`) plus JSON-key patterns (`local_compatibility`/`supported_methods`); case-insensitive (`-i`) so capital-S "Supported" wording surfaces alongside lowercase → "Verification" section + Task 1.1 + Task 5.
- [x] **Overclaim inventory.** Five `.md` sites enumerated (≈lines 112, 169-174, 176-181, 185, and the "Architecture Spec Readiness Delta" section at ≈lines 189-202 — the fifth site is the cycle-4 addition); three known JSON paths enumerated (`observed_server_requests[0].local_compatibility`, `compatibility_classification.supported_methods`, and `architecture_spec_readiness_delta` block — the third is the cycle-4 addition) with placeholder for additional paths surfaced in Task 1.4.
- [x] **Scope guardrails.** "This plan does not" enumerates: no code edits, no T-20260429-02 method matrix, no live probes, no version-pin changes.
- [x] **Vocabulary succession explicit.** Authority Basis section names the May-1 probe-plan's narrower `supported` definition (route + correlation fields) and frames the rebaseline as a stricter classification splitting parser-kind from response-shape. The diagnostic is reclassified, not retroactively wrong against its own May-1 vocabulary.
- [x] **T-20260429-02 sweep collision resolved.** "Sweep Classification Rules" section adds `legacy-parser-route-vocabulary` classification with explicit bounding rules. Task 1.1 verification anchors enumerate the T-20260429-02 ticket parser-route table rows and the May-1 probe-plan vocabulary definitions as expected `legacy-parser-route-vocabulary` matches. Stop condition example clarified to distinguish overclaim from legacy vocabulary.
- [x] **Sweep case-insensitivity.** All overclaim-detection sweeps use `-i`: Verification section, Step 1.1, Step 1.4 rg search (post jq-validate split), Step 2.7, Step 3.5, Step 4.5, Step 5.1.
- [x] **Git proof for "landed on `main`."** Step 1.5b requires `git diff main..HEAD -- packages/plugins/codex-collaboration/server/runtime.py` (empty) AND `git show main:.../runtime.py | sed -n '107,118p'` (carve-outs visible) before Task 4 writes the assertion.
- [x] **Fallback tuple wording precise.** Step 2.2 bullet 4 enumerates `_AVAILABLE_DECISIONS[command_approval]` verbatim and frames lossiness as bidirectional — payload loss for `acceptWithExecpolicyAmendment` plus spurious additions (`acceptForSession`, `applyNetworkPolicyAmendment`, `decline`). Does NOT phrase it as "decline replaces cancel" — `cancel` is preserved by the fallback. JSON Step 3.3 mirrors this precision.
- [x] **JSON disposition is preserve-and-add (single approach; no in-place mutation of existing fields).** Step 1.4 + Step 3.3 specify the preserve-and-add structure: rename `compatibility_classification` → `_legacy_compatibility_classification` (vocabulary preserved verbatim with a `_vocabulary_note` reminder); add new `compatibility_classification` block under rebaseline vocabulary; add top-level `classification_vocabulary: "rebaseline_parser_kind_and_response_shape_v1"` marker; add `classification_supersedes` pointer to legacy blocks; mirror pattern for `observed_server_requests[0].local_compatibility` → `_legacy_local_compatibility` and for `architecture_spec_readiness_delta` → `_legacy_architecture_spec_readiness_delta` (cycle-4 addition). Resolves the patch-in-place vocabulary-shift defect by preserving old-vocabulary truth verbatim and adding new-vocabulary truth alongside under the same canonical keys, eliminating the silent semantic shift that mutating `supported_methods: []` or `architecture_spec_readiness_delta.ready: false` would have caused.
- [x] **Consumer discovery is hidden-aware.** Step 1.4's consumer-discovery `rg` includes `--hidden --glob '!.git/**'` so paths under `.claude/hooks/` and other dot-directories surface from repo root. A defensive named-roots cross-check is also documented against existing roots (`packages/ scripts/ extensions/ .claude/hooks/`), with explicit instruction to verify directory existence before adding any other roots to avoid noise. Plain `rg --type-not md` from repo root would silently skip hidden paths the plan explicitly enumerates as valid consumer locations.
- [x] **Consumer discovery is primarily informational with one dispositional exception.** Discovery records the contract for future schema changes (which consumers exist, which fields they read). Single dispositional consequence: surfacing a production consumer that reads a canonical field whose shape changes under preserve-and-add (e.g., reads `compatibility_classification.supported_methods` directly without falling back to `fully_supported_methods` / `parser_kind_compatible_methods`) fires the JSON-disposition-unsafe stop condition. Otherwise the preserve-and-add disposition applies uniformly: the legacy block preserves old-vocabulary truth verbatim under `_legacy_*` prefix, and the new block lands at the canonical key name with rebaseline vocabulary.
- [x] **JSON validation split from JSON search.** Step 1.4 runs `jq '.' <file> >/dev/null` as a separate validation command before the rg search. A failed `jq` pipe used to silently produce empty stdout, indistinguishable from a no-matches result; the split surfaces invalid-JSON as a non-zero exit before any pattern matching runs.
- [x] **Pre-edit status snapshot (Task 0; tightened by scrutiny follow-up 2).** Task 0 captures `git status` + `git diff --cached --name-only` + `git diff --name-only` before any edits begin. Pre-existing changes in target files (the diagnostic `.md`, sibling JSON, register, or rebaseline plan) are now a stop condition — the executor must resolve them before proceeding, since this plan's edits assume target files match `HEAD`. Pre-existing unrelated unstaged changes (outside the four targets) are recorded and tolerated. Pre-existing unrelated STAGED changes are surfaced before proceeding so the plan's commit cannot accidentally bundle unrelated staged work.
- [x] **Sweep additional-paths default is STOP, not in-scope.** Task 1.4 narrows the line-253 carve-out: additional JSON overclaim paths beyond the three enumerated default to firing the "Pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition. The narrow mechanical-mirror exception applies ONLY when the additional path is unambiguously the same kind of claim AND its parent object's structure cleanly accepts the same legacy-rename + rebaseline-block-add treatment. Novel shapes stop; they do not silently extend Task 3's edits.
- [x] **Register-annotation `main`-truth has its own stop condition.** Step 1.5b's git-evidence checks (`git diff main..HEAD -- runtime.py` empty AND `git show main:.../runtime.py | sed -n '107,118p'` showing carve-outs) are mapped to a dedicated "Register-annotation `main`-truth check failed" stop condition rather than the "Live envelope evidence has changed" condition. The two failure modes are distinct: `main`/runtime divergence affects only the register annotation premise, not the envelope-probe diagnostic correction. Surface message reflects the actual failure.
- [x] **Register annotation matches ticket reality.** Task 4 wording names AC #1, #2, AND #3 explicitly as the unchecked closure criteria; "only smoke and probe remain" was rejected because AC #3 (regression-assertion update + suite pass) is also unchecked.
- [x] **Exit-condition cell replacement.** Task 4.4 replaces the T-20260429-01 row's Exit condition cell so it names AC #1-#3 closure work only. Task 4.2 (Current truth append) on its own would leave the row simultaneously asserting Phase 1 has landed AND that Phase 1 still needs to be landed — exactly the contradiction this plan exists to remove. Task 4.5 verification searches for surviving "Land the Phase 1" framing.
- [x] **Register reconciliation scope is narrow.** No global "Last reconciled" bump. Only the T-20260429-01 row (Current truth + Exit condition cells) and priority `#1` line are touched; row-local recency is captured by the in-cell "As of 2026-05-09" stamp.
- [x] **Optional register note.** Task 4 is conditional on Task 1.5; skips cleanly when register already reflects landed implementation across all three cells.
- [x] **Placeholder scan.** No "TBD", no "appropriate", no "similar to Task N", no "handle edge cases". Replacement wording for all five `.md` overclaim sites, the JSON patch fields, and the register cells is shown verbatim.
- [x] **Wording consistency.** "Decision-shape lossy" used consistently in `.md`, JSON, and register paths. "Parser-kind compatible" used consistently when distinguishing from "fully supported." `_resolve_available_decisions`, `_AVAILABLE_DECISIONS[command_approval]`, and `approval_router.py:103-111` named identically across tasks.
- [x] **Bite-sized steps.** Each step is a single action: one rg, one read, one edit, one git command. No multi-action steps.
- [x] **Consumer-shape-incompatibility stop condition (review-cycle 3).** Stop Conditions section + Step 1.4 sub-section both extend the JSON-disposition-unsafe stop condition to fire when a production consumer reads a canonical field whose shape changes under preserve-and-add AND the consumer code does not tolerate the new shape. Three remediation paths surfaced for the user: (a) keep canonical key under May-1 vocabulary and place rebaseline block at a non-canonical key (e.g., `compatibility_classification_rebaseline`), (b) update the consumer code to honor the new shape before this plan executes, (c) defer JSON reconciliation to a separate plan that can sequence consumer + JSON changes together.
- [x] **Legacy-block paths in JSONPath notation (review-cycle 3).** `classification_supersedes.legacy_blocks` uses JSONPath syntax (`$._legacy_compatibility_classification` for the top-level compatibility block; `$.observed_server_requests[0]._legacy_local_compatibility` for the nested per-request field; `$._legacy_architecture_spec_readiness_delta` for the top-level readiness block — the third path is the cycle-4 addition) so the nested-vs-top-level structure is unambiguous. Bare key names alone would have implied all blocks were at the same nesting depth — the per-request block is actually nested under `observed_server_requests[0]` while the others are top-level.
- [x] **Named-roots cross-check excludes non-existent paths (review-cycle 3).** Step 1.4 named-roots cross-check lists only existing repo roots (`packages/ scripts/ extensions/ .claude/hooks/`); `.claude/scripts/` is excluded (does not exist in this repo at plan-write time). Workers are instructed to verify directory existence before adding any other roots so the cross-check does not produce noise from non-existent paths.
- [x] **JSON snippet schematic disclaimer (review-cycle 3).** Step 3.3's `_legacy_compatibility_classification` snippet now inlines the actual current values for `supported_methods` / `unsupported_methods` / `unknown_or_unparseable_methods` / `missing_required_fields` / `notes` (captured at plan-write time) AND labels the snippet **schematic** with explicit instruction to re-read the live JSON during Task 1.4 and copy the actual current values rather than the snippet's values, in case the JSON has drifted since plan-write time. Prevents both placeholder ambiguity and drift-induced staleness. Step 3.3's `_legacy_architecture_spec_readiness_delta` snippet (cycle-4 addition) inherits the same convention.
- [x] **Architecture-readiness as fifth/third disposition site (review-cycle 4).** Cycle 1-3 enumerated four `.md` overclaim sites (≈lines 112, 169-174, 176-181, 185) and two JSON overclaim paths (`compatibility_classification`, `local_compatibility`). The cycle-4 review surfaced that the diagnostic's "Architecture Spec Readiness Delta" `.md` section (≈lines 189-202) and the JSON's parallel `architecture_spec_readiness_delta` block (≈lines 45580-45591) form a fifth / third disposition site that the cycle 1-3 plan missed entirely — a worker following the earlier plan would have left `architecture_spec_readiness_delta.ready: true` and "architecture spec can proceed only if it scopes server-request support to the observed methods" standing, which is the strongest remaining overclaim under rebaseline vocabulary. Step 1.1 verification anchors, Step 1.4 enumerated paths (third bullet), Step 2.5 (`.md` patch), Step 3.3 items 7-8 (JSON preserve-and-add), and the sweep patterns at the Verification section / Step 1.1 / Step 1.4 / Step 2.7 / Step 3.5 / Step 5.1 all enumerate this site explicitly. The sweep pattern adds `architecture_spec_readiness_delta`, `architecture spec readiness delta`, `architecture spec can proceed`, `parseable against`, and `newly_satisfied_items` so the missed-site failure mode cannot recur.
- [x] **Programmatic raw-evidence preservation (review-cycle 4; updated cycle 6).** Cycle 1-3 asserted that the JSON's existing raw-observation fields must remain unchanged (Step 3.3 closing paragraph; Architecture summary; Step 1.4 vocabulary caveat) but enforced this only via syntax check (`jq '.' >/dev/null`) and a narrow rg sweep — a worker could mutate `params_keys`, captured `availableDecisions` arrays, probe rows, or other raw-observation fields and pass both checks. Cycle 4 adds Task 1.4's "Derive raw-evidence projection paths" sub-section (worker derives the `jq` projection against the live JSON, NOT the schematic illustration), Step 3.2 (full pre-edit copy to `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json` + projection snapshot to `/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.json` — deterministic paths under `/private/tmp` not bare `/tmp`; cycle 6 added the full copy as an immutable reference for re-derivation safety), and Step 3.6 (post-edit re-extraction + `diff` against the pre-edit snapshot; non-empty diff fires the JSON-disposition-unsafe stop condition; recovery re-derives from full pre-edit copy, never from worktree). The schematic projection in Task 1.4 explicitly carries a "DO NOT use as-is" warning + INCLUDE/EXCLUDE path lists; workers err toward over-projection (false positives are recoverable; false negatives are the failure mode this enforcement exists to prevent).
- [x] **Conditional commit-message template + executor-aware co-author (review-cycle 4; updated scrutiny follow-up).** Cycle 1-3 hard-coded the commit body's JSON disposition and register annotation paragraphs unconditionally even though Tasks 3 and 4 are conditional (a worker hitting the no-JSON-disposition or no-register-annotation path would commit a body that lies about what the commit contains). Cycle 1-3 also hard-coded `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` — fine when this model authored the commit, false provenance when a different model executed Task 6. Cycle 4 restructures the Step 6.2 heredoc body with `<!-- CONDITIONAL: ... -->` / `<!-- END CONDITIONAL -->` markers around the JSON-disposition paragraph (Task 3) and register-annotation paragraph (Task 4); worker-instruction text above the heredoc names the editing protocol (delete markers + keep paragraph if task ran; delete both if skipped). Co-author trailer becomes a placeholder with replacement instruction. Scrutiny follow-up: the email address `<noreply@anthropic.com>` was previously hard-coded, creating false provenance when a non-Anthropic model (e.g., `gpt-5-codex`) executed. Both the identity AND email are now placeholders (`<executing model identity>` + `<executing model email>`), with the replacement instruction naming concrete examples for both Anthropic and OpenAI models. Step 6.3's self-check for placeholder leaks covers both placeholders.
- [x] **External-consumer scope explicit (review-cycle 4; elevated to Boundary by scrutiny follow-up).** The external-consumer assumption was originally documented only here in the self-review checklist — a non-operative location that would not be read by a worker during execution. Scrutiny follow-up elevates it to the Boundary section's "This plan does not" list, making it an operative execution premise. The full reasoning (repo-internal artifact, not a public contract; three remediation paths for late-discovered external consumers) now lives in the Boundary and is binding on the executor from task start.
- [x] **`status` field preserved in schema (review-cycle 5).** Cycle 1-4's new `compatibility_classification` block (Step 3.3 item 4) omitted the `status` field that exists in the live JSON at line 912 (`"status": "passed"`). A reader querying `compatibility_classification.status` post-edit would get `undefined` — a silent schema change that breaks the preserve-and-add contract. Cycle 5 adds `"status": "parser_kind_compatible_decision_shape_lossy"` to the new canonical block (aligning with rebaseline vocabulary) and adds `"status": "passed"` to the legacy block schematic (so the field is explicitly enumerated even though the verbatim-copy instruction would capture it). The new `status` value names both compatibility dimensions rather than the May-1 binary `"passed"`.
- [x] **Editing-method guidance for 45K-line JSON (review-cycle 5).** Cycle 1-4 specified what to change and how to verify but not the editing mechanism for the 45,592-line JSON. Edit-tool string replacement with insufficient surrounding context risks non-unique matches; `jq` transforms risk key reordering that invalidates Step 3.6's byte-identical diff assumption. Cycle 5 adds editing guidance to Step 3.3's preamble: use the Edit tool with minimum 3-5 lines of surrounding context; avoid `jq` transforms for structural edits.
- [x] **Step 3.6 key-ordering false-positive mitigation (review-cycle 5).** Cycle 4's Step 3.6 raw-evidence diff assumes byte-identical `jq` projection output pre- and post-edit. If a worker uses `jq` transforms (against the cycle-5 editing guidance), key reordering could produce a false-positive diff failure that fires the JSON-disposition-unsafe stop condition unnecessarily. Cycle 5 adds a conditional note: if the edit mechanism preserved key ordering (Edit tool), the diff should be byte-identical; if `jq` transforms were used, pipe both projections through `python3 -m json.tool --sort-keys` before diffing.
- [x] **Live-capture-wins precedence for hardcoded tuple (review-cycle 5).** Step 2.2 hardcodes the `_AVAILABLE_DECISIONS[command_approval]` tuple inline, while Step 1.2 instructs the worker to capture it live. Cycle 1-4 did not specify which wins if they differ. Cycle 5 adds an explicit precedence note: if Step 1.2's captured tuple differs from the hardcoded values, use the live capture and adjust the fallback explanation to match.
- [x] **Step 3.6 recovery cannot overwrite pre-edit baseline (review-cycle 6).** Cycle 4-5's Step 3.6 false-positive recovery path said "re-run from Step 3.2" — but Step 3.2 captured from the worktree. If Step 3.3 had already mutated the JSON, re-running Step 3.2 would capture post-edit state as the new "pre-edit" baseline, making the subsequent diff compare post-edit to post-edit (always empty = false pass). Cycle 6 fixes this: Step 3.2 now saves a full pre-edit copy (`/private/tmp/codex-collab-overclaim-fix-raw-evidence-pre.full.json`) before any mutation, then extracts the projection from that copy. The recovery path re-derives from the saved full pre-edit copy, never from the worktree.
- [x] **Raw-evidence projection includes full `.probes` array (review-cycle 6).** Cycle 4-5's schematic projection covered `observed_server_requests[]` (a derived summary with `params_keys`, `has_id`, etc.) but omitted the `.probes` array entirely — the raw observation layer containing per-probe `status`, `classification`, `evidence`, `responses` (where "No approval response was sent" lives), `errors`, `notifications`, and `server_requests[].{id,method,params}` (the verbatim wire envelope). The plan declares all of these immutable but the projection couldn't enforce it. Cycle 6 includes the entire `.probes` array in the projection — it is pure observation data, distinct from the top-level interpretation fields (`compatibility_classification`, `local_compatibility`, `architecture_spec_readiness_delta`) that this plan mutates.
- [x] **Stale inventory counts reconciled (review-cycle 6).** Cycle 4 added the fifth `.md` site and third JSON path but did not update all earlier textual references. "Four specific sites" (line 69), "all four sites" (line 111), "Confirm the four enumerated" (line 122), "beyond the two enumerated paths" (lines 136, 1038), and "all four `.md` overclaim sites" (line 1044) all pre-dated the cycle-4 addition and were never reconciled. Cycle 6 fixes all six stale references.
- [x] **`rm` fallback removed (review-cycle 6).** Step 3.6's successful-diff cleanup offered `rm` as a fallback if `trash` was unavailable, with an incorrect claim that "the per-project safety policy permits removing these scratch artifacts." The global safety policy unconditionally prohibits `rm`. Cycle 6 removes the fallback: use `trash` only; if unavailable, leave temp files in place and report their paths.
- [x] **Step 1.5b line-drift vs stop-condition reconciled (review-cycle 6).** Step 1.5b gave contradictory instructions: "locate the actual lines on `main` and update Task 4.2's annotation accordingly" (implying adapt-and-continue) vs "If either check fails → fire the stop condition. Skip Task 4 entirely" (implying halt). Cycle 6 distinguishes three outcomes explicitly: carve-outs at expected lines (proceed), carve-outs at different lines (drift — adapt line reference and proceed), carve-outs absent from `main` (fire stop condition — implementation not landed).
- [x] **Overview and temp-file convention refreshed for full-copy mechanism (review-cycle 6).** The Task 1.4 overview paragraph (line 327) still described "captures a pre-edit projection" without mentioning the full pre-edit copy. The temp-file convention paragraph listed only one temp file path. Cycle 6 updates the overview to name both artifacts (full copy + projection) and expands the convention paragraph to list all three paths with their roles.
- [x] **Consumer discovery covers all three preserve-and-add fields (scrutiny follow-up).** The `rg` pattern in Task 1.4 searched `compatibility_classification|supported_methods|local_compatibility` but omitted `architecture_spec_readiness_delta` and its child fields (`newly_satisfied_items`, `still_missing_items`) — one of the three canonical fields undergoing preserve-and-add. A consumer reading `.architecture_spec_readiness_delta.ready` under old vocabulary would misinterpret `ready: false`. Scrutiny follow-up expands the pattern to include all three canonical fields plus their child field names, and adds a vocabulary-shift warning to the classification guidance.
- [x] **Temp snapshot non-overwriting guard (scrutiny follow-up).** Step 3.2 used deterministic temp paths without checking for existing files. A re-run after a partial Task 3 execution would overwrite the pre-mutation snapshot with post-mutation state, making Step 3.6's diff compare post-edit to post-edit (false pass). Scrutiny follow-up adds `test ! -e` guards before both `cp` and `jq` commands, with a recovery guide for both clean-worktree and mutated-worktree cases.
- [x] **Commit-message jq-verification claim conditionalized (scrutiny follow-up).** The always-retained opening paragraph of the commit message claimed "with programmatic pre/post jq-projection verification" — but jq verification only runs when Task 3 runs (JSON disposition applied). When Task 3 is skipped (no JSON overclaim found), the claim is false. Scrutiny follow-up moves the jq-verification sentence into the Task 3 CONDITIONAL block and shortens the always-retained sentence to "raw envelope observations are preserved unchanged."
- [x] **Legacy-block preservation diff gate (scrutiny follow-up 2).** The raw-evidence projection (Step 3.6) explicitly excludes classification/interpretive fields — it cannot detect accidental modification of `_legacy_*` block contents. Step 3.2 now captures a pre-edit snapshot of the three interpretive blocks (`compatibility_classification`, `observed_server_requests[0].local_compatibility` + notes, `architecture_spec_readiness_delta`). New Step 3.6b extracts the renamed `_legacy_*` blocks post-edit (stripping the added `_vocabulary_note` fields), then diffs against the pre-edit snapshot. Non-empty diff is a data integrity failure with a defined recovery path (re-copy from full pre-edit reference). Step 3.7 staging now requires both Step 3.6 AND Step 3.6b to pass.
- [x] **Target-file ownership in Task 0 (scrutiny follow-up 2).** Task 0 previously only guarded against unrelated dirty files outside the target set. Pre-existing changes in the three target files were unclassified — a prior partial run or concurrent edit could be silently committed as this plan's work. Task 0 now classifies target-file changes as a separate stop condition requiring user resolution before proceeding.
- [x] **Recovery-path provenance guard (scrutiny follow-up 2).** Step 3.2's recovery instruction for case (b) (worktree mutated by partial Step 3.3) now requires verifying the worktree diff contains ONLY Step 3.3-shaped mutations before restoring from the full pre-edit copy. Unknown changes → STOP instead of overwrite.
- [x] **Rebaseline plan is a canonical-JSON consumer (scrutiny follow-up 3).** Consumer discovery (Task 1.4) searched repo-local CODE only, but the rebaseline implementation plan at lines 204-220 contains `jq` commands that read `local_compatibility` and `architecture_spec_readiness_delta` — making it a Markdown-embedded executable consumer of the canonical JSON fields. After Task 3's preserve-and-add disposition, the expected-value bullets at lines 216-219 become stale (expect `"supported"` and `ready: true` where the canonical fields now carry rebaseline vocabulary). Step 5.5 reconciles these lines; Step 5.6 verifies no other rebaseline-plan references remain stale.
- [x] **Task 5 read-only contradiction resolved (scrutiny follow-up 3).** Task 5 was declared read-only but Step 5.3 instructed workers to "fix the loser before committing" — creating an execution paradox. Now Task 5 header explicitly scopes read-only to Steps 5.1-5.4, Step 5.5 owns the rebaseline-plan write, and the contradiction-patch path is a defined stop-return-rerun loop rather than an in-task fix.
- [x] **Line-drift handling covers all Task 4 references (scrutiny follow-up 3).** Step 1.5b's drift-adaptation instruction previously named only Task 4.2's annotation. The same `runtime.py:107-118` reference appears in Step 4.3's priority-line replacement text and Step 4.4's exit-condition replacement text. Drift instruction now enumerates all three sites explicitly.
- [x] **Markdown consumers of canonical JSON keys checked (scrutiny follow-up 3).** Step 5.6 adds an explicit `rg` verification that the rebaseline plan's mentions of `local_compatibility` and `architecture_spec_readiness_delta` all agree with the post-patch canonical vocabulary. This closes the gap where code-only consumer discovery missed control documents that embed `jq` evidence-check contracts.
- [x] **Canonical-value `jq` assertions for JSON readiness boolean (scrutiny follow-up 4).** The `rg` sweep pattern matches the key name `architecture_spec_readiness_delta` but cannot match the nested `"ready": true` boolean value at the JSON line where it lives — the sweep returns lines 45580, 45582, and 45585 but not 45581. Step 3.6c adds six explicit `jq -e` assertions: three for canonical values (`architecture_spec_readiness_delta.ready == false`, `local_compatibility == "parser_kind_compatible_decision_shape_lossy"`, `compatibility_classification.status == "parser_kind_compatible_decision_shape_lossy"`) and three mirror assertions for legacy preservation (`_legacy_architecture_spec_readiness_delta.ready == true`, `_legacy_local_compatibility == "supported"`, `_legacy_compatibility_classification.status == "passed"`). This is the correct tool for asserting nested JSON boolean state; `rg` is structurally unable to do so.
- [x] **Rebaseline plan in Task 0 target-file ownership (scrutiny follow-up 4).** Step 5.5 writes and stages `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md`, but Task 0's target-file list previously listed only three files. If the rebaseline plan were already dirty before execution, Task 0 would classify it as "unrelated unstaged work" and allow proceeding, then Step 5.5 would absorb the pre-existing dirt into the commit. Task 0 now lists four target files; a dirty rebaseline plan fires the same stop-and-surface condition as the other three targets.
- [x] **Post-write terminal sweep (scrutiny follow-up 4).** Step 5.1's broad sweep ran before Step 5.5 wrote new text into the rebaseline plan. Step 5.6 only checked `local_compatibility|architecture_spec_readiness_delta` — a narrow pattern that cannot catch wording-level overclaims in the new replacement text. Step 5.7 reruns the full sweep pattern against the rebaseline plan after Step 5.5's write, classifying each match per the Sweep Classification Rules. An `interpretive-overclaim` classification means Step 5.5's replacement text is wrong and triggers a fix-restage-rerun loop.
- [x] **Vocabulary marker `jq` assertions (scrutiny follow-up 5).** Step 3.6c previously verified six value assertions (three canonical, three legacy) but never positively asserted that `classification_vocabulary` and `classification_supersedes` — the fields that make the preserve-and-add schema transition intelligible — actually exist. A worker could omit items 1-2 of Step 3.3 and still pass all six value checks. Step 3.6c now includes four vocabulary marker assertions: `classification_vocabulary` matches the expected string, `classification_supersedes.legacy_blocks` matches the exact JSONPath array (upgraded from `length == 3` in scrutiny follow-up 6), `classification_supersedes.legacy_vocabulary` matches, and `classification_supersedes.fix_doc` is non-null. Total assertions: fifteen (three canonical scalar + five canonical array + three legacy + four markers).
- [x] **Consumer discovery taxonomy includes peer diagnostic data artifacts (scrutiny follow-up 5).** Task 1.4's consumer-discovery classification had three buckets (production consumer, test fixture, self-reference). The broad `rg` pattern also surfaces sibling diagnostic JSON files (e.g., `codex-app-server-scratch-home-runtime-probes.json`) that contain the same field names as data, not as consumers. A worker encountering these hits had no classification bucket and would either misclassify them as production consumers (triggering a false stop condition) or leave them unclassified (violating the exhaustive-classification requirement). New `peer-diagnostic-data-artifact` classification added with explicit scoping: these are independent diagnostic captures, NOT consumers of the target JSON's schema.
- [x] **Legacy assertions compare against pre-edit snapshot, not hard-coded literals (scrutiny follow-up 5).** Step 3.6c's legacy value assertions previously hard-coded `"supported"`, `"passed"`, and `true` — the values observed at plan-write time. Steps 3.3 items 3, 5, and 7 tell workers to copy live values (not plan-write-time values) if the JSON has drifted. A worker who correctly copies drifted legacy values would then fail the hard-coded assertions at Step 3.6c. Legacy assertions now read expected values from the pre-edit legacy-block snapshot (`/private/tmp/codex-collab-overclaim-fix-legacy-blocks-pre.json`) via `jq --argjson`/`--arg`, resolving the drift-tolerance contradiction.
- [x] **Markdown raw-facts preservation check (scrutiny follow-up 5).** Step 2.7's `rg` sweep can detect surviving overclaim wording but cannot detect accidental removal of raw-evidence lines. The JSON has full programmatic enforcement (Steps 3.6/3.6b), but the `.md` had no analogous check — a Task 2 edit that accidentally deleted a raw-observation line would pass Step 2.7. New Step 2.7b spot-checks six distinctive raw-observation anchors (`item/commandExecution/requestApproval`, `"acceptWithExecpolicyAmendment"`, `availableDecisions`, `/bin/zsh -lc`, `No approval response was sent`, `itemId`) via `grep -qF`. This is a spot-check rather than a byte-identical diff because the `.md` mixes raw observations and interpretive text in the same document, unlike the JSON where `jq` projection cleanly separates them.
- [x] **Rebaseline "Command Approval Decision-Shape Boundary" classified as `authority-source` (scrutiny follow-up 5).** Step 5.7 previously classified matches from the rebaseline plan's lines 905-921 as `legacy-parser-route-vocabulary`. That section uses rebaseline-era framing ("decision-shape lossy", "response compatibility is not established", "lossless parser/response branch") and is one of this plan's two truth authorities (Authority Basis item 2) — it describes current reality, not the May-1 narrower vocabulary. New `authority-source` classification added to the Sweep Classification Rules table. Verification section, Task 5.2, and Step 5.7 all updated to include `authority-source` as an acceptable terminal classification.
- [x] **Taxonomy, raw-preservation, target-count, and assertion gaps (scrutiny follow-up 6).** Five defects patched: (1) `authority-source` added to Step 1.1's allowed classification list — the global Sweep Classification Rules defined six classifications but Step 1.1 listed only five, causing a worker encountering rebaseline-plan authority-section matches to have no valid label. (2) `peer-diagnostic-data-artifact` added to the Sweep Classification Rules table, the Verification section's acceptable terminal classifications, and Task 5.2's acceptable classifications — the sweep glob `docs/diagnostics/codex-app-server-*.json` matches sibling diagnostic JSONs whose own `architecture_spec_readiness_delta` fields are independent data, not overclaims about the target method; workers had no classification bucket and would either misclassify or leave unclassified. (3) Step 2.7b strengthened with `git diff` hunk-review verification — the six `grep -qF` anchors pass even when raw lines are deleted because three of the six anchor strings (`item/commandExecution/requestApproval`, `availableDecisions`, `itemId`) also appear in the replacement interpretive prose from Steps 2.1-2.5; the hunk review catches edits outside the five enumerated sites. (4) Stale "three above" references at Task 0 lines 229/230 fixed to "four above" and self-review line 1248 updated to name all four target files (diagnostic `.md`, sibling JSON, register, rebaseline plan) — the rebaseline plan was added as a fourth target file in scrutiny follow-up 4 but the count references were not propagated. (5) Step 3.6c expanded from ten to fifteen `jq -e` assertions: five canonical array assertions added (`fully_supported_methods == []`, `parser_kind_compatible_methods == ["item/commandExecution/requestApproval"]`, `decision_shape_lossy_methods == ["item/commandExecution/requestApproval"]`, `still_missing_items | length >= 3`, `still_missing_items | any(test("lossless parser/response branch"))`) and the `classification_supersedes.legacy_blocks | length == 3` marker assertion upgraded to exact-content matching against the three JSONPath entries; a worker could previously create the `compatibility_classification` block with correct `status` but wrong array values (e.g., `fully_supported_methods: ["item/commandExecution/requestApproval"]` — a remaining overclaim) and pass all ten assertions.
- [x] **Execution-control path contradictions resolved (scrutiny follow-up 7).** Five defects from external scrutiny patched: (1) Step 1.1 verification anchor no longer claims the `rg` sweep must surface `"ready: true"` (impossible — the sweep matches key names, not bare boolean values); replaced with guidance to verify the boolean via `jq -e` during Task 1.4 and rely on Step 3.6c's assertions post-edit. (2) Global stop condition for register-annotation `main`-truth check reconciled with Step 1.5b's line-drift handling — the stop condition now explicitly states line drift is NOT a stop condition and fires only when (a) this branch modified `runtime.py` or (b) carve-outs are absent from `main` entirely; Step 1.5b uses `rg -n` content-aware search instead of fixed-range `sed -n '107,118p'`. (3) `peer-diagnostic-data-artifact` added to Step 1.1's operative allowed-labels list (was defined in Sweep Classification Rules table and self-review but missing from the actual step instruction). (4) "Live envelope evidence changed" stop condition now has an explicit discovery path — artifact inventory via `ls docs/diagnostics/2026-05-{02..31}-*envelope*` during Task 1.1, with comparison against the May-1 capture's `availableDecisions` shape if a newer artifact exists. (5) Step 5.5 skip condition changed from execution-based ("if Task 3 ran") to state-based (`jq -e` checks against the live canonical JSON values); handles the case where a prior commit already reconciled the JSON but the rebaseline plan remains stale.

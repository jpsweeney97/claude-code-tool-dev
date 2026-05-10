# Codex App Server Server-Request Envelope-Diagnostic Overclaim Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is a docs-only plan with hard scope guardrails; do not convert it into a parser/response correctness change or into a T-20260429-02 method-by-method coverage push.

**Goal:** Reconcile the committed May-1 server-request envelope-probe diagnostic with the repaired rebaseline implementation plan and `approval_router.py` reality, eliminating the docs-only contradiction without altering raw observation evidence.

**Architecture:** Surgical doc edits. Preserve the diagnostic's raw observation layer (envelope contents, params keys, redacted summary, trigger command) untouched. Patch only the interpretive layer that conflicts with code reality. Mirror the correction in the diagnostic's sibling JSON via a preserve-and-add disposition: rename the original `compatibility_classification` and `local_compatibility` fields with a `_legacy_` prefix (preserving their May-1 parser-route vocabulary verbatim), add new fields under the same canonical keys carrying rebaseline-vocabulary classification, and add explicit `classification_vocabulary` + `classification_supersedes` markers documenting the boundary. Optionally annotate the reconciliation register so its priority order reflects landed implementation.

**Tech Stack:** Markdown, JSON, ripgrep, jq, git.

---

## Boundary

This plan implements:

- Wording corrections to the envelope-probe diagnostic `.md` interpretive claims (four specific sites: classification line, "Local compatibility judgment" bullet block, "Compatibility result" bullet block, and "Important limit" first sentence).
- A sibling-JSON disposition (preserve-and-add: rename existing `compatibility_classification` / `local_compatibility` to `_legacy_*` keys; add new rebaseline-vocabulary blocks under canonical keys; add `classification_vocabulary` + `classification_supersedes` markers).
- Optional reconciliation-register annotation recording that `T-20260429-01` Phase 1 implementation has landed on `main`, with closure evidence still missing.
- A verification sweep across May-1 diagnostics, the rebaseline plan, the friction-reduction ticket, and the register for residual overclaims.
- One commit covering all of the above.

This plan does not:

- Modify `approval_router.py`, `delegation_controller.py`, `runtime.py`, or any other code.
- Alter raw envelope observations (params keys, redacted envelope summary, observed JSON-RPC `id`/`method`, trigger command, "no approval response was sent" record).
- Land response semantics, lossless `availableDecisions` preservation, or any fix to the parser fallback path.
- Perform any T-20260429-02 method-by-method classification work for `mcpServer/elicitation/request`, `item/tool/call`, `applyPatchApproval`, `execCommandApproval`, `account/chatgptAuthTokens/refresh`, `item/permissions/requestApproval`, `item/fileChange/requestApproval`, or `item/tool/requestUserInput`.
- Run a `/delegate` smoke, a credential-boundary probe, or any other live App Server probe.
- Move the reconciliation register's priority order beyond annotating `T-20260429-01` as landed-but-not-closed.
- Re-litigate `~/.codex` carve-outs, `~/.agents` reads, or dynamic gitdir resolution.
- Raise `TESTED_CODEX_VERSION` or `MINIMUM_CODEX_VERSION`.

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

Four specific sites in the `.md` (line numbers from orientation reads; reconfirm in Task 1 before editing):

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

The exact replacement text for all four sites is fixed in Task 2. Task 1's pre-edit `rg` sweep is responsible for surfacing any sites this enumeration misses; if it does, Task 1 stops and surfaces rather than expanding scope silently.

## Files To Inspect Before Edit

Read every item below before any write. Each read has a specific load-bearing purpose:

| File | Purpose |
|---|---|
| `packages/plugins/codex-collaboration/server/approval_router.py:90-115` | Confirm `_resolve_available_decisions` semantics; capture `_AVAILABLE_DECISIONS[command_approval]` tuple contents verbatim — used in Task 2 and Task 3 replacement wording. |
| `packages/plugins/codex-collaboration/server/runtime.py` (line range 107-118 on `main`) | Confirm Phase 1 sandbox carve-outs are present; via `git show main:.../runtime.py | sed -n '107,118p'`. Drives Task 4 register annotation. Read on `main`, not the current branch. |
| `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:895-925` | Anchor corrected wording to the repaired plan's framing ("decision-shape lossy", structured `acceptWithExecpolicyAmendment`, "lossless parser/response branch"). |
| `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` (full, with extra attention to lines ≈100-200) | Confirm the four enumerated overclaim sites; surface any other interpretive overclaims. |
| `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` (sibling JSON, may or may not exist) | Discover existence; if present, identify any parallel overclaim fields. Drives Task 3 disposition. |
| `docs/status/codex-collaboration-reconciliation-register.md:9-70` | "Last reconciled" timestamp + priority order + `T-20260429-01` row "Current truth"/"Exit condition" cells. Drives Task 4 disposition. |
| `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:212-230` (T-20260429-01 ticket) | Confirm acceptance criteria and that AC #1 smoke / AC #2 credential-boundary probe / AC #3 regression assertion + suite pass evidence is genuinely missing. |
| `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md` (T-20260429-02 ticket — context only, no edits) | Context for the Sweep Classification Rules: the parser-route classification table at lines 67-77 ("Supported as `<kind>`" / "Supported (parked)") is `legacy-parser-route-vocabulary`, not an overclaim. The T-20260429-02 method-by-method classification work is OUT of this plan's scope. Read so the worker can confidently classify sweep matches against this file. |
| `docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md:666-672` (May-1 probe-plan vocabulary) | Context for the Sweep Classification Rules: the May-1 four-state vocabulary (`supported` / `unsupported` / `unknown` / `unparseable`) is `legacy-parser-route-vocabulary`. Read to ground the Vocabulary Succession framing in the Authority Basis section. |

The pre-edit `rg` sweep below treats every file under `docs/diagnostics/2026-05-01-codex-app-server-*.md`, `docs/diagnostics/codex-app-server-*.json`, `docs/plans/2026-05-01-codex-app-server-*.md`, `docs/tickets/2026-04-29-codex-collaboration-*.md`, and `docs/status/codex-collaboration-reconciliation-register.md` as a candidate. If the sweep surfaces hits this plan does not enumerate, Task 1 stops and surfaces the finding rather than expanding scope silently.

## Stop Conditions

Stop and surface the situation to the user — do not adapt, expand, or work around — when any of these fire:

- **JSON disposition is unsafe to decide locally.** Task 1 finds the sibling JSON exists, contains a parallel overclaim, AND any of the following hold: (a) the JSON's structure makes the preserve-and-add disposition destructive (e.g., a `_legacy_compatibility_classification` key already exists with different content; the parent object's schema rejects renamed keys; a mechanical-mirror path's structural shape does not cleanly map to legacy-rename + new-block-add); (b) consumer discovery surfaces a production consumer that reads any canonical field whose shape changes under preserve-and-add — e.g., reads `compatibility_classification.supported_methods` directly — AND the consumer code does not tolerate the new shape (under preserve-and-add, the canonical-key block carries `fully_supported_methods` / `parser_kind_compatible_methods` / `decision_shape_lossy_methods` instead of `supported_methods`; a consumer that reads `supported_methods` directly without checking for the new sibling fields would read undefined or malformed data). Surface and ask before proceeding.
- **Pre-edit sweep finds an overclaim site this plan does not enumerate.** "Overclaim" here is bounded by the Sweep Classification Rules below. Examples that trigger this stop: a file under the swept paths claiming command-approval is fully supported in the response-shape sense; a `ready_to_close_ticket: true` for command approval; a register or diagnostic cell asserting `availableDecisions` is preserved without naming the all-strings fallback; an additional JSON overclaim path beyond the two enumerated paths that does NOT mechanically mirror the same kind of claim per Task 1.4's narrow exception. Examples that do NOT trigger this stop (classifiable as `legacy-parser-route-vocabulary`): the T-20260429-02 ticket's `Supported as <kind>` / `Supported (parked)` table entries, the May-1 probe-plan's definition of `supported`, or any other legacy May-1-vocabulary use that is not a fresh response-shape / lossless-preservation / closability claim. Surface the finding; do not silently extend Task 2's edits.
- **Register row already reflects landed-implementation language for T-20260429-01.** Skip Task 4 entirely; do not make a no-op edit.
- **Register-annotation `main`-truth check failed.** Step 1.5b's git evidence does not support the "Phase 1 has landed on `main`" assertion: either `git diff main..HEAD -- packages/plugins/codex-collaboration/server/runtime.py` is non-empty (this branch carries `runtime.py` modifications, so the current-branch reads do not stand in for `main`), or `git show main:packages/plugins/codex-collaboration/server/runtime.py | sed -n '107,118p'` does not show the carve-outs at the expected lines (line numbers may have drifted on `main`, or implementation may not have landed). Skip Task 4 entirely; surface the finding so the register-annotation premise can be reconciled before any annotation is written. This is distinct from "Live envelope evidence has changed" — the envelope is unchanged; the failure is about `main`'s `runtime.py` state diverging from what Task 4's annotation claims.
- **Verification sweep at Task 5 surfaces a surviving overclaim.** Do not commit. Surface the finding.
- **Live envelope evidence has changed since the diagnostic was captured.** If Task 1's reads reveal a newer probe artifact contradicting the May-1 envelope (different `availableDecisions` shape, etc.), stop. The fix's premise depends on the May-1 capture being current.

## Sweep Classification Rules

Every match returned by the rg sweeps in Task 1.1, Task 2.6, Task 3.5, Task 4.5, and Task 5.1 must be classified as exactly one of the following. Task 1.1 produces the baseline classification; later sweeps reuse the same rules for diff verification.

| Classification | When it applies | Action |
|---|---|---|
| `raw-observation` | The match is part of the diagnostic's evidence layer (envelope contents, params keys, redacted summary, observed `availableDecisions` array, trigger command, "no approval response was sent" record, schema-visible methods listing, per-probe pass/fail rows). | Preserve unchanged. |
| `interpretive-overclaim` | The match makes a claim against the rebaseline vocabulary that conflicts with `approval_router.py:103-111`. Bounded by the rules below. | Patch under the relevant Task 2 / Task 3 step, OR fire the "pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition if the site is not enumerated. |
| `corrected-language` | The match is post-patch wording that already names parser-kind compatibility, decision-shape lossiness, the all-strings fallback, or related rebaseline framing. | Preserve unchanged. |
| `legacy-parser-route-vocabulary` | The match uses the May-1 probe-plan's narrower `supported` vocabulary in a way that does NOT make a response-shape / lossless-preservation / closability claim. See bounding rules below. | Preserve unchanged. Do not patch; do not fire the stop condition. |
| `unrelated` | The match's word appears in a context that has nothing to do with command-approval classification (e.g., "supported sandbox carve-outs", "supported plugin" in a different domain). | Preserve unchanged. |

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

Final pre-commit sweep, run from repo root. The pattern intentionally combines bare-word terms (`supported`, `preserved`, `lossy`, `ready_to_close_ticket`) with phrase patterns (`proves compatibility`, `compatibility for the observed`) and JSON-key patterns (`local_compatibility`, `supported_methods`) so neither a bare-word-only site nor a phrase/key-only site can slip past. The sweep is case-insensitive (`-i`) so capital-S "Supported" classifications surface alongside lowercase ones; classification (Sweep Classification Rules above) decides which matches are overclaims and which are legacy parser-route vocabulary:

```bash
rg -n -i "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

Classify every match per the Sweep Classification Rules above. Acceptable terminal classifications: `raw-observation`, `corrected-language`, `legacy-parser-route-vocabulary`, `unrelated`. Unacceptable: `interpretive-overclaim` (any surviving site triggers the Task 5 stop condition).

No surviving site may claim command-approval is "supported" in the rebaseline response-shape sense without the parser-kind / decision-shape-lossy qualification, or claim `availableDecisions` is "preserved" without naming the all-strings fallback condition, or list `item/commandExecution/requestApproval` under `supported_methods` / "observed supported methods" without that qualification, or assert "proves compatibility" for command-approval response semantics, or assert `ready_to_close_ticket: true` for `item/commandExecution/requestApproval`. Legacy parser-route vocabulary in the T-20260429-02 ticket and the May-1 probe-plan vocabulary definitions is explicitly out of scope for this plan and remains untouched.

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

Branch on the snapshot:

- **Working tree clean** → record "Pre-edit status: clean." Proceed to Task 1.
- **Pre-existing unrelated unstaged changes exist** (files outside the three above) → record their paths. They are NOT in scope for this plan; do not stage, modify, or revert them during this plan's execution. Task 6's verification will tolerate their continued presence in the working tree as long as they are unchanged from this snapshot.
- **Pre-existing staged changes exist from a different in-flight task** (any staged file outside the three above) → STOP and surface to user before proceeding. Combining unrelated staged work with this plan's commit would muddle the audit trail. The user must either unstage or commit the unrelated staged work separately before this plan continues.

(No commit at end of Task 0 — discovery only. Task 0 outputs feed Task 6's staged-set verification.)

---

### Task 1: Inventory and discovery

**Files:** read-only — no writes in this task.

- [ ] **Step 1.1: Pre-edit ripgrep sweep.**

```bash
rg -n -i "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

The `-i` flag is intentional: capital-S "Supported" wording in the T-20260429-02 ticket's parser-route classification table and lowercase "supported" wording in the diagnostic must both surface so the Sweep Classification Rules above can decide which matches are overclaims and which are legacy parser-route vocabulary.

Expected: enumerate every match. For each match, annotate one of `raw-observation`, `interpretive-overclaim`, `corrected-language`, `legacy-parser-route-vocabulary`, or `unrelated` per the Sweep Classification Rules. The annotated list is reused in Task 5 as the baseline for diff verification.

Verification anchors:

- The four enumerated overclaim sites in the diagnostic `.md` (≈lines 112, 169-174, 176-181, 185) MUST appear in the output and MUST be tagged `interpretive-overclaim`.
- The T-20260429-02 ticket's parser-route classification table rows (`Supported as <kind>` / `Supported (parked)` for `command_approval`, `file_change`, `request_user_input`) MUST be tagged `legacy-parser-route-vocabulary`. The T-20260429-02 ticket's acceptance-criterion language about "supported handling" / "Supported methods retain regression coverage" is also `legacy-parser-route-vocabulary`.
- The May-1 probe-plan vocabulary definitions of `supported` / `unsupported` / `unknown` / `unparseable` (≈lines 666-672 of `2026-05-01-codex-app-server-server-request-envelope-probe-plan.md`) MUST be tagged `legacy-parser-route-vocabulary`.

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
rg -n -i "supported|preserved|ready_to_close_ticket|local_compatibility|supported_methods|proves compatibility|compatibility for the observed" \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Two known overclaim paths in the JSON (verified at orientation; reconfirm exact paths here):

- `observed_server_requests[0].local_compatibility: "supported"` (≈line 904)
- `compatibility_classification.supported_methods: ["item/commandExecution/requestApproval"]` (≈line 913)

Both are in scope for Task 3 under the preserve-and-add disposition (described below). If the sweep surfaces additional overclaim paths within this same JSON file, the default is to STOP and surface (fire the "Pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition). The narrow mechanical-mirror exception applies ONLY when the additional path is unambiguously the same kind of claim as one of the two enumerated paths — i.e., a binary `supported_methods`-style listing of `item/commandExecution/requestApproval` under the May-1 vocabulary, a sibling field claiming `availableDecisions` is `preserved: true`, or `ready_to_close_ticket: true` for command-approval — AND the path's parent object structure cleanly accepts the same legacy-rename + rebaseline-block-add treatment described in Step 3.2. Record each mechanical-mirror path for Task 3. Any additional path that does NOT meet both conditions → fire the stop condition; do not silently extend Task 3's edits to novel shapes.

**Vocabulary caveat (resolved by preserve-and-add).** The JSON's `compatibility_classification` block uses a binary vocabulary: `supported_methods` / `unsupported_methods` / `unknown_or_unparseable_methods` / `missing_required_fields`. The corrected classification we are introducing — *parser-kind compatible but decision-shape lossy* — has no slot in this vocabulary. Mutating `supported_methods` to `[]` while adding new sibling fields would silently shift an existing key's meaning without a vocabulary boundary marker, leaving programmatic readers to interpret `supported_methods: []` under the old binary semantics (which would be a new false historical claim). The preserve-and-add disposition resolves this: the original block is preserved unchanged under a renamed key (`_legacy_compatibility_classification`), so its old-vocabulary truth (`supported_methods: ["item/commandExecution/requestApproval"]` under May-1 parser-route vocabulary, which IS historically true) remains accessible to any reader who looks; a new `compatibility_classification` block under the rebaseline vocabulary is added alongside; an explicit `classification_vocabulary` marker names the active vocabulary; an optional `classification_supersedes` pointer records the legacy block's location. The same preserve-and-add pattern applies to `observed_server_requests[0].local_compatibility` (preserved as `_legacy_local_compatibility`; new `local_compatibility` under rebaseline vocabulary).

**Consumer discovery (primarily informational, with one stop-condition exception).**

The preserve-and-add disposition does not depend on consumer-marker honoring — the legacy block is preserved verbatim regardless of consumer behavior, and the new block lands under the canonical `compatibility_classification` key so existing readers find rebaseline-current data at the same path. The discovery is primarily informational: it documents which production paths read this JSON and which fields they consume, so future schema changes can target the actual contract rather than assumed convention. The stop-condition exception (see "Stop conditions specific to this step" below) fires only when discovery surfaces a consumer that reads a canonical field whose shape changes under preserve-and-add and does not tolerate the new shape. Run, hidden-aware so paths under `.claude/` surface from repo root:

```bash
rg -n -i --hidden --glob '!.git/**' \
   "compatibility_classification|supported_methods|local_compatibility|codex-app-server-server-request-envelope-probes\\.json" \
   --type-not md
```

(`--type-not md` excludes documentation references so production consumers surface clearly. `--hidden --glob '!.git/**'` ensures hidden repo paths like `.claude/hooks/` are searched without sweeping `.git/` internals. As a defensive cross-check against existing named roots if the result above is suspicious: `rg -n -i "<pattern>" packages/ scripts/ extensions/ .claude/hooks/`. Add `.claude/scripts/` or other root paths only if they exist at execution time; do not include non-existent directories or rg will warn / produce noise.)

Classify each match:

- **Production consumer** — code under `packages/`, `scripts/`, `.claude/hooks/`, `extensions/`, or any executable path that reads the JSON file path or one of the classification field names. Read the consumer code; record (a) which field names it reads and (b) whether it honors any vocabulary-marker convention.
- **Test fixture / synthetic data** — code that uses these field names for unrelated fixtures. Does not count as a consumer.
- **Self-reference inside the JSON itself** — not a consumer.

Record the consumer-discovery findings explicitly for Task 6's commit message:

- No production consumer found → record "no documented machine consumer at this revision."
- Production consumer found → record file path(s), the field names each consumer reads, and whether each honors any vocabulary-marker convention. This list is the contract Task 3's preserve-and-add disposition must respect (the new `compatibility_classification` block keeps the canonical key name so existing readers find rebaseline-current data; the renamed `_legacy_compatibility_classification` block is for reference and historical-vocabulary readers).

Stop conditions specific to this step:

- JSON structure does not allow preserve-and-add (e.g., `_legacy_compatibility_classification` already exists with different content, or the parent object's schema rejects renamed keys) → fire the "JSON disposition unsafe" stop condition. Surface and ask before proceeding.
- Consumer discovery surfaces a production consumer that reads any canonical field whose shape changes under preserve-and-add AND the consumer code does not tolerate the new shape (e.g., reads `compatibility_classification.supported_methods` directly without falling back to or checking for `fully_supported_methods` / `parser_kind_compatible_methods`) → fire the "JSON disposition unsafe" stop condition. The legacy block alone is not enough — the consumer reads the canonical key and would silently see undefined or malformed data after the new block lands. Surface; the user must decide whether to (a) keep the canonical key under May-1 vocabulary and put the rebaseline block at a non-canonical key (e.g., `compatibility_classification_rebaseline`), (b) update the consumer code to honor the new shape before this plan executes, or (c) defer the JSON reconciliation to a separate plan that can sequence consumer + JSON changes together.

Task 3 implements the preserve-and-add structure described above using the consumer-discovery findings recorded here.

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

2. **`main` carries the carve-outs at lines 107-118** (so the register annotation pointing at those line numbers is grounded):

```bash
git show main:packages/plugins/codex-collaboration/server/runtime.py | sed -n '107,118p'
```

Expected: output shows the `build_workspace_write_sandbox_policy` carve-outs (`~/.codex/memories`, `~/.codex/plugins/cache`, `~/.agents/skills`, `~/.agents/plugins`, plus dynamic gitdir resolution). If the lines do not show the carve-outs, line numbers may have drifted; locate the actual lines on `main` and update Task 4.2's annotation accordingly.

Record both checks' outcomes (the diff is empty, or it is not; the lines on `main` are X-Y showing the carve-outs). Task 4.2's wording depends on this proof — without it, "landed on `main`" is an unverified claim.

If either check fails → fire the "Register-annotation `main`-truth check failed" stop condition. Skip Task 4 entirely; surface so the register-annotation premise can be reconciled before any annotation is written. (Distinct from "Live envelope evidence has changed" — the envelope is unchanged; the failure is about `main`'s `runtime.py` state diverging from what Task 4's annotation would claim.)

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

- Modify: `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` (overclaim sites at ≈line 112 and ≈lines 169-174; reconfirmed in Task 1.1).

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

(Task 1.2's captured `_AVAILABLE_DECISIONS[command_approval]` tuple may be inserted parenthetically if it improves clarity; keep the bullet readable.)

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

- [ ] **Step 2.5: Re-read the surrounding "Compatibility Classification" and "Important limit" sections post-edit.**

Look for downstream sentences that paraphrase the now-corrected bullets or sentences. If a summary sentence still says "supported" or "preserved" or "proves compatibility" without qualification, patch it to match. If a section ends with a "ticket effect" / "next step" line that follows from the old wording, ensure it now follows from the new wording.

- [ ] **Step 2.6: Local rg verification of the modified file.**

```bash
rg -n -i "supported|preserved|proves compatibility|compatibility for the observed" \
   docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md
```

Expected: every match falls into raw-observation, the new qualified wording, or unrelated. No bare "supported" classification of command-approval. No bare "preserved" claim about `availableDecisions`. No "proves compatibility" assertion for command-approval response semantics. If a surviving overclaim appears, return to Step 2.5.

- [ ] **Step 2.7: Stage the `.md` change.**

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
| JSON exists, has parallel overclaim (preserve-and-add applies) | Step 3.2. |
| JSON disposition unsafe (structure does not allow preserve-and-add, or `_legacy_*` key already exists with different content) | Stop condition fired in Task 1.4; surface to user. |

- [ ] **Step 3.2: Apply preserve-and-add disposition.**

The JSON is mutated structurally (new keys + renamed keys), but no existing field's value or meaning is altered in place. The original `compatibility_classification` block is preserved verbatim under a renamed key with its old May-1 parser-route vocabulary semantics intact; a new `compatibility_classification` block under the rebaseline vocabulary is added alongside; explicit vocabulary marker and supersedes-pointer fields document the boundary. The same pattern applies to the per-request `local_compatibility` field.

After all edits, the JSON's existing raw-observation fields (params keys, redacted envelope summary, observed `availableDecisions` array, schema-visible methods listing, per-probe pass/fail rows, etc.) must remain unchanged.

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
       "$.observed_server_requests[0]._legacy_local_compatibility"
     ],
     "legacy_vocabulary": "may_1_parser_route_v1",
     "fix_doc": "docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md",
     "authority": "docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md#L905-L921",
     "summary": "May-1 parser-route classification preserved under _legacy_* keys (paths in JSONPath notation); rebaseline-vocabulary classification under canonical keys names parser-kind compatibility and decision-shape lossiness."
   }
   ```

3. **Rename `compatibility_classification` → `_legacy_compatibility_classification`** (≈line 911). Preserve all contents verbatim. Add a single sibling field inside the renamed block to remind readers of its vocabulary:

   ```json
   "_legacy_compatibility_classification": {
     "_vocabulary_note": "May-1 parser-route vocabulary (see top-level classification_supersedes). 'supported' here means: local code has a concrete route for the method and required correlation fields are present.",
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

7. **Apply the same preserve-and-add to any additional mechanical-mirror paths** identified in Task 1.4 (per the narrow exception). For each: rename existing key with `_legacy_` prefix; add new key under the rebaseline vocabulary referencing the same fallback explanation. Do not improvise on novel shapes — those should have stopped Task 1.4.

8. **Any field claiming `availableDecisions` is `preserved: true`** (if surfaced as a mechanical-mirror path): rename to `_legacy_availability_preservation` (or analogous `_legacy_*` key matching the original key name) and add a new sibling field under the rebaseline vocabulary naming the all-strings fallback. Use the same fallback-tuple wording.

9. **Any field flagged `ready_to_close_ticket: true` for command-approval** (if surfaced as a mechanical-mirror path): rename to `_legacy_ready_to_close_ticket` and add a new sibling field set to `false` with a note naming the missing closure work (smoke + credential-boundary probe + lossless parser/response branch).

Do not delete or rewrite raw observation fields (params keys, redacted envelope summary, observed `availableDecisions` array, etc.).

- [ ] **Step 3.3: Validate JSON (only if Step 3.2 ran).**

```bash
jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json >/dev/null
```

Expected: exit `0`. If non-zero, fix the JSON before staging.

- [ ] **Step 3.4: Local rg verification (only if Step 3.2 ran).**

```bash
rg -n -i "supported|preserved|ready_to_close_ticket" \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected:

- The `_legacy_compatibility_classification` block still matches `supported_methods` because its contents are intentionally preserved verbatim under May-1 parser-route vocabulary. This is acceptable: the `_legacy_` prefix combined with the top-level `classification_vocabulary` marker scopes the legacy block's "supported" semantics explicitly to May-1 vocabulary; future readers see clean reclassification rather than mutated history.
- The new `compatibility_classification` block must NOT contain `supported_methods` as a non-empty array under the rebaseline vocabulary — it should have `fully_supported_methods: []`, with `parser_kind_compatible_methods` and `decision_shape_lossy_methods` carrying the actual method.
- The new `local_compatibility` field (alongside `_legacy_local_compatibility`) must NOT contain bare `"supported"` — it should name the lossy class (e.g., `"parser_kind_compatible_decision_shape_lossy"`).
- No surviving `preserved: true` or `ready_to_close_ticket: true` for command-approval outside of `_legacy_*` blocks.

Cross-check: every line returned by the sweep should be classifiable as either (a) inside a `_legacy_*` block (acceptable — preserved-vocabulary semantics), (b) inside the new rebaseline block (acceptable — names parser-kind compatibility / decision-shape lossiness explicitly), or (c) raw observation outside any classification block (acceptable — evidence layer). Any line that does NOT classify as one of these → return to Step 3.2; the preserve-and-add was incomplete or a mechanical-mirror path was missed in Task 1.4.

- [ ] **Step 3.5: Stage the JSON change (only if Step 3.2 ran).**

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

### Task 5: Final verification sweep

**Files:** read-only — no writes in this task.

- [ ] **Step 5.1: Run the full sweep.**

```bash
rg -n -i "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods" \
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
- `unrelated` (different context, e.g., "supported sandbox carve-outs") → OK.

Unacceptable: `interpretive-overclaim` → STOP. Do not commit. Surface to the user with file path, line number, current text, and proposed correction.

Cross-check against the Task 1.1 baseline classification: any match that was tagged `interpretive-overclaim` in Task 1.1 must now classify as `corrected-language` or its enumerated patch site must be reflected in the staged diff. Any new `interpretive-overclaim` match (not in the Task 1.1 baseline) is a surviving overclaim regardless of cause.

- [ ] **Step 5.3: Cross-doc consistency spot-check.**

Compare line-by-line:

- Diagnostic `.md` corrected wording (Task 2) vs. rebaseline plan lines 905-921. Do they describe the same lossy fallback in compatible language?
- Diagnostic `.md` corrected wording vs. JSON disposition (Task 3). Do they agree, or does the JSON path leave the diagnostic standing alone?
- Register annotation (Task 4) vs. ticket acceptance criteria. Does the register's AC #1-#3 framing (smoke, credential-boundary probe, `test_runtime.py` regression assertion update + full-suite pass) match the ticket's checklist? AC #4 is already checked.

If any pair contradicts, fix the loser before committing.

- [ ] **Step 5.4: Confirm no code files are staged.**

```bash
git diff --cached --name-only
```

Expected: only files under `docs/diagnostics/`, optionally `docs/status/codex-collaboration-reconciliation-register.md`. No `packages/`, no `.claude/hooks/`, no scripts. If a code file is staged, unstage and surface.

(No commit at end of Task 5 — verification only.)

---

### Task 6: Commit

**Files:** previously staged via Steps 2.7, 3.5 (conditional), 4.6 (conditional).

- [ ] **Step 6.1: Confirm staged set.**

```bash
git status
```

Expected: only the planned docs files appear in `git status` as staged. Pre-existing unrelated unstaged changes recorded in Task 0 may still be present in the working tree; that is acceptable. Confirm only the planned docs are staged for commit.

- [ ] **Step 6.2: Commit.**

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
envelope observations are preserved unchanged. The sibling JSON is
reconciled via preserve-and-add: the original
`compatibility_classification` and `local_compatibility` fields are
renamed with a `_legacy_` prefix (preserving their May-1 parser-route
vocabulary verbatim — the original `supported_methods:
["item/commandExecution/requestApproval"]` remains historically true
under that vocabulary), and new fields under the canonical key names
carry rebaseline-vocabulary classification (`fully_supported_methods:
[]`; `parser_kind_compatible_methods` and
`decision_shape_lossy_methods` enumerate the method explicitly). A
top-level `classification_vocabulary:
"rebaseline_parser_kind_and_response_shape_v1"` marker names the
active vocabulary; `classification_supersedes` documents the legacy
blocks. Optional register annotation records that T-20260429-01
Phase 1 implementation has landed on main; the T-20260429-01 row
Exit condition cell is replaced so it names AC #1-#3 closure work
only (comparable `/delegate` smoke with avoidable sandbox-friction
escalations <=2; credential-boundary probe; `test_runtime.py`
regression assertion update + full codex-collaboration suite pass).
AC #4 (Option F upstream limitation) is already checked.

T-20260429-02 method-by-method classification scope is unchanged
and not addressed here. The T-20260429-02 ticket's parser-route
"Supported as <kind>" / "Supported (parked)" wording is May-1
legacy parser-route vocabulary and remains untouched.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6.3: Confirm commit landed cleanly.**

```bash
git status
git log -1 --stat
```

Expected: the commit lists only `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` and any conditional files staged in Steps 3.5 / 4.6. No code files. Pre-existing unrelated unstaged changes from Task 0's snapshot may still be present in `git status`; verify those are unchanged from the snapshot (this plan's edits should not have modified them).

---

## Self-Review Checklist

Run this before requesting plan approval. If any box is unchecked, fix in place.

- [x] **Spec coverage.** Each of the user's six requested sections is present and explicit:
  1. Raw envelope facts to preserve → "Raw Envelope Facts To Preserve" section.
  2. Interpretive overclaims to patch → "Interpretive Overclaims To Patch" section (four sites).
  3. Authority basis: `approval_router.py` + repaired rebaseline plan → "Authority Basis" section + Vocabulary Succession sub-section.
  4. Files to inspect before edit, including JSON → "Files To Inspect Before Edit" table.
  5. Stop condition for JSON disposition → "Stop Conditions" section + Task 1.4 (preserve-and-add disposition + consumer discovery as informational contract record) + Task 3 (preserve-and-add structural edits).
  6. Verification rg pattern covers bare-word terms (`supported`/`preserved`/`lossy`/`ready_to_close_ticket`) plus phrase patterns (`proves compatibility`/`compatibility for the observed`) plus JSON-key patterns (`local_compatibility`/`supported_methods`); case-insensitive (`-i`) so capital-S "Supported" wording surfaces alongside lowercase → "Verification" section + Task 1.1 + Task 5.
- [x] **Overclaim inventory.** Four `.md` sites enumerated (≈lines 112, 169-174, 176-181, 185); two known JSON paths enumerated (`observed_server_requests[0].local_compatibility`, `compatibility_classification.supported_methods`) with placeholder for additional paths surfaced in Task 1.4.
- [x] **Scope guardrails.** "This plan does not" enumerates: no code edits, no T-20260429-02 method matrix, no live probes, no version-pin changes.
- [x] **Vocabulary succession explicit.** Authority Basis section names the May-1 probe-plan's narrower `supported` definition (route + correlation fields) and frames the rebaseline as a stricter classification splitting parser-kind from response-shape. The diagnostic is reclassified, not retroactively wrong against its own May-1 vocabulary.
- [x] **T-20260429-02 sweep collision resolved.** "Sweep Classification Rules" section adds `legacy-parser-route-vocabulary` classification with explicit bounding rules. Task 1.1 verification anchors enumerate the T-20260429-02 ticket parser-route table rows and the May-1 probe-plan vocabulary definitions as expected `legacy-parser-route-vocabulary` matches. Stop condition example clarified to distinguish overclaim from legacy vocabulary.
- [x] **Sweep case-insensitivity.** All overclaim-detection sweeps use `-i`: Verification section, Step 1.1, Step 1.4 rg search (post jq-validate split), Step 2.6, Step 3.4, Step 4.5, Step 5.1.
- [x] **Git proof for "landed on `main`."** Step 1.5b requires `git diff main..HEAD -- packages/plugins/codex-collaboration/server/runtime.py` (empty) AND `git show main:.../runtime.py | sed -n '107,118p'` (carve-outs visible) before Task 4 writes the assertion.
- [x] **Fallback tuple wording precise.** Step 2.2 bullet 4 enumerates `_AVAILABLE_DECISIONS[command_approval]` verbatim and frames lossiness as bidirectional — payload loss for `acceptWithExecpolicyAmendment` plus spurious additions (`acceptForSession`, `applyNetworkPolicyAmendment`, `decline`). Does NOT phrase it as "decline replaces cancel" — `cancel` is preserved by the fallback. JSON Step 3.2 mirrors this precision.
- [x] **JSON disposition is preserve-and-add (single approach; no in-place mutation of existing fields).** Step 1.4 + Step 3.2 specify the preserve-and-add structure: rename `compatibility_classification` → `_legacy_compatibility_classification` (vocabulary preserved verbatim with a `_vocabulary_note` reminder); add new `compatibility_classification` block under rebaseline vocabulary; add top-level `classification_vocabulary: "rebaseline_parser_kind_and_response_shape_v1"` marker; add `classification_supersedes` pointer to legacy blocks; mirror pattern for `observed_server_requests[0].local_compatibility` → `_legacy_local_compatibility`. Resolves the patch-in-place vocabulary-shift defect by preserving old-vocabulary truth verbatim and adding new-vocabulary truth alongside under the same canonical keys, eliminating the silent semantic shift that mutating `supported_methods: []` would have caused.
- [x] **Consumer discovery is hidden-aware.** Step 1.4's consumer-discovery `rg` includes `--hidden --glob '!.git/**'` so paths under `.claude/hooks/` and other dot-directories surface from repo root. A defensive named-roots cross-check is also documented against existing roots (`packages/ scripts/ extensions/ .claude/hooks/`), with explicit instruction to verify directory existence before adding any other roots to avoid noise. Plain `rg --type-not md` from repo root would silently skip hidden paths the plan explicitly enumerates as valid consumer locations.
- [x] **Consumer discovery is primarily informational with one dispositional exception.** Discovery records the contract for future schema changes (which consumers exist, which fields they read). Single dispositional consequence: surfacing a production consumer that reads a canonical field whose shape changes under preserve-and-add (e.g., reads `compatibility_classification.supported_methods` directly without falling back to `fully_supported_methods` / `parser_kind_compatible_methods`) fires the JSON-disposition-unsafe stop condition. Otherwise the preserve-and-add disposition applies uniformly: the legacy block preserves old-vocabulary truth verbatim under `_legacy_*` prefix, and the new block lands at the canonical key name with rebaseline vocabulary.
- [x] **JSON validation split from JSON search.** Step 1.4 runs `jq '.' <file> >/dev/null` as a separate validation command before the rg search. A failed `jq` pipe used to silently produce empty stdout, indistinguishable from a no-matches result; the split surfaces invalid-JSON as a non-zero exit before any pattern matching runs.
- [x] **Pre-edit status snapshot (Task 0).** Task 0 captures `git status` + `git diff --cached --name-only` + `git diff --name-only` before any edits begin, recording pre-existing unrelated changes that were already in the working tree. Step 6.1 / Step 6.3 verification language tolerates the continued presence of those pre-existing unstaged changes (rather than requiring "working tree otherwise clean", which would have either blocked unnecessarily or tempted out-of-scope cleanup). Pre-existing unrelated STAGED changes are surfaced before proceeding so the plan's commit cannot accidentally bundle unrelated staged work.
- [x] **Sweep additional-paths default is STOP, not in-scope.** Task 1.4 narrows the line-253 carve-out: additional JSON overclaim paths beyond the two enumerated default to firing the "Pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition. The narrow mechanical-mirror exception applies ONLY when the additional path is unambiguously the same kind of claim AND its parent object's structure cleanly accepts the same legacy-rename + rebaseline-block-add treatment. Novel shapes stop; they do not silently extend Task 3's edits.
- [x] **Register-annotation `main`-truth has its own stop condition.** Step 1.5b's git-evidence checks (`git diff main..HEAD -- runtime.py` empty AND `git show main:.../runtime.py | sed -n '107,118p'` showing carve-outs) are mapped to a dedicated "Register-annotation `main`-truth check failed" stop condition rather than the "Live envelope evidence has changed" condition. The two failure modes are distinct: `main`/runtime divergence affects only the register annotation premise, not the envelope-probe diagnostic correction. Surface message reflects the actual failure.
- [x] **Register annotation matches ticket reality.** Task 4 wording names AC #1, #2, AND #3 explicitly as the unchecked closure criteria; "only smoke and probe remain" was rejected because AC #3 (regression-assertion update + suite pass) is also unchecked.
- [x] **Exit-condition cell replacement.** Task 4.4 replaces the T-20260429-01 row's Exit condition cell so it names AC #1-#3 closure work only. Task 4.2 (Current truth append) on its own would leave the row simultaneously asserting Phase 1 has landed AND that Phase 1 still needs to be landed — exactly the contradiction this plan exists to remove. Task 4.5 verification searches for surviving "Land the Phase 1" framing.
- [x] **Register reconciliation scope is narrow.** No global "Last reconciled" bump. Only the T-20260429-01 row (Current truth + Exit condition cells) and priority `#1` line are touched; row-local recency is captured by the in-cell "As of 2026-05-09" stamp.
- [x] **Optional register note.** Task 4 is conditional on Task 1.5; skips cleanly when register already reflects landed implementation across all three cells.
- [x] **Placeholder scan.** No "TBD", no "appropriate", no "similar to Task N", no "handle edge cases". Replacement wording for all four `.md` overclaim sites, the JSON patch fields, and the register cells is shown verbatim.
- [x] **Wording consistency.** "Decision-shape lossy" used consistently in `.md`, JSON, and register paths. "Parser-kind compatible" used consistently when distinguishing from "fully supported." `_resolve_available_decisions`, `_AVAILABLE_DECISIONS[command_approval]`, and `approval_router.py:103-111` named identically across tasks.
- [x] **Bite-sized steps.** Each step is a single action: one rg, one read, one edit, one git command. No multi-action steps.
- [x] **Consumer-shape-incompatibility stop condition (review-cycle 3).** Stop Conditions section + Step 1.4 sub-section both extend the JSON-disposition-unsafe stop condition to fire when a production consumer reads a canonical field whose shape changes under preserve-and-add AND the consumer code does not tolerate the new shape. Three remediation paths surfaced for the user: (a) keep canonical key under May-1 vocabulary and place rebaseline block at a non-canonical key (e.g., `compatibility_classification_rebaseline`), (b) update the consumer code to honor the new shape before this plan executes, (c) defer JSON reconciliation to a separate plan that can sequence consumer + JSON changes together.
- [x] **Legacy-block paths in JSONPath notation (review-cycle 3).** `classification_supersedes.legacy_blocks` uses JSONPath syntax (`$._legacy_compatibility_classification` for the top-level block; `$.observed_server_requests[0]._legacy_local_compatibility` for the nested per-request field) so the nested-vs-top-level structure is unambiguous. Bare key names alone would have implied both blocks were top-level — the per-request block is actually nested under `observed_server_requests[0]`.
- [x] **Named-roots cross-check excludes non-existent paths (review-cycle 3).** Step 1.4 named-roots cross-check lists only existing repo roots (`packages/ scripts/ extensions/ .claude/hooks/`); `.claude/scripts/` is excluded (does not exist in this repo at plan-write time). Workers are instructed to verify directory existence before adding any other roots so the cross-check does not produce noise from non-existent paths.
- [x] **JSON snippet schematic disclaimer (review-cycle 3).** Step 3.2's `_legacy_compatibility_classification` snippet now inlines the actual current values for `supported_methods` / `unsupported_methods` / `unknown_or_unparseable_methods` / `missing_required_fields` / `notes` (captured at plan-write time) AND labels the snippet **schematic** with explicit instruction to re-read the live JSON during Task 1.4 and copy the actual current values rather than the snippet's values, in case the JSON has drifted since plan-write time. Prevents both placeholder ambiguity and drift-induced staleness.

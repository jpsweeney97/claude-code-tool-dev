# Codex App Server Server-Request Envelope-Diagnostic Overclaim Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is a docs-only plan with hard scope guardrails; do not convert it into a parser/response correctness change or into a T-20260429-02 method-by-method coverage push.

**Goal:** Reconcile the committed May-1 server-request envelope-probe diagnostic with the repaired rebaseline implementation plan and `approval_router.py` reality, eliminating the docs-only contradiction without altering raw observation evidence.

**Architecture:** Surgical doc edits. Preserve the diagnostic's raw observation layer (envelope contents, params keys, redacted summary, trigger command) untouched. Patch only the interpretive layer that conflicts with code reality. Mirror the correction in the diagnostic's sibling JSON via either patch-in-place or supersession note, with an explicit stop-condition deciding which. Optionally annotate the reconciliation register so its priority order reflects landed implementation.

**Tech Stack:** Markdown, JSON, ripgrep, jq, git.

---

## Boundary

This plan implements:

- Wording corrections to the envelope-probe diagnostic `.md` interpretive claims (four specific sites: classification line, "Local compatibility judgment" bullet block, "Compatibility result" bullet block, and "Important limit" first sentence).
- A sibling-JSON disposition (patch in place or supersession note), decided by an explicit stop condition.
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
   Replacement direction: split wire-presence from parser-preservation. Name the all-strings fallback condition explicitly. Note that the fallback tuple includes `decline`; the live envelope offered `cancel`, not `decline`. Cite `approval_router.py:103-111` and the rebaseline plan's "Command Approval Decision-Shape Boundary" section.

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
| `packages/plugins/codex-collaboration/server/approval_router.py:90-115` | Confirm `_resolve_available_decisions` semantics; capture `_AVAILABLE_DECISIONS[command_approval]` contents. |
| `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:895-925` | Anchor corrected wording to the repaired plan's framing ("decision-shape lossy", `cancel` ≠ `decline`, "lossless parser/response branch"). |
| `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` (full, with extra attention to lines ≈100-200) | Confirm the four enumerated overclaim sites; surface any other interpretive overclaims. |
| `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` (sibling JSON, may or may not exist) | Discover existence; if present, identify any parallel overclaim fields. Drives Task 3 disposition. |
| `docs/status/codex-collaboration-reconciliation-register.md:9-70` | "Last reconciled" timestamp + priority order + `T-20260429-01` row "Current truth"/"Exit condition" cells. Drives Task 4 disposition. |
| `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:212-230` | Confirm acceptance criteria and that smoke + credential-boundary probe evidence is genuinely missing. |

The pre-edit `rg` sweep below treats every file under `docs/diagnostics/2026-05-01-codex-app-server-*.md`, `docs/diagnostics/codex-app-server-*.json`, `docs/plans/2026-05-01-codex-app-server-*.md`, `docs/tickets/2026-04-29-codex-collaboration-*.md`, and `docs/status/codex-collaboration-reconciliation-register.md` as a candidate. If the sweep surfaces hits this plan does not enumerate, Task 1 stops and surfaces the finding rather than expanding scope silently.

## Stop Conditions

Stop and surface the situation to the user — do not adapt, expand, or work around — when any of these fire:

- **JSON disposition is unsafe to decide locally.** Task 1 finds the sibling JSON exists, contains a parallel overclaim, AND the JSON's structure makes either patch-in-place or supersession-note destructive (e.g., schema constraints, dependent fields, machine-consumer contracts). Surface and ask before proceeding.
- **Pre-edit sweep finds an overclaim site this plan does not enumerate.** Examples: another file under the swept paths claiming command-approval is `supported`; a `ready_to_close_ticket: true` for command approval; a register cell asserting parser-preservation. Surface the finding; do not silently extend Task 2's edits.
- **Register row already reflects landed-implementation language for T-20260429-01.** Skip Task 4 entirely; do not make a no-op edit.
- **Verification sweep at Task 5 surfaces a surviving overclaim.** Do not commit. Surface the finding.
- **Live envelope evidence has changed since the diagnostic was captured.** If Task 1's reads reveal a newer probe artifact contradicting the May-1 envelope (different `availableDecisions` shape, etc.), stop. The fix's premise depends on the May-1 capture being current.

## Verification

Final pre-commit sweep, run from repo root. The pattern intentionally combines bare-word terms (`supported`, `preserved`, `lossy`, `ready_to_close_ticket`) with phrase patterns (`proves compatibility`, `compatibility for the observed`) and JSON-key patterns (`local_compatibility`, `supported_methods`) so neither a bare-word-only site nor a phrase/key-only site can slip past:

```bash
rg -n "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

Each match must classify into exactly one of:

- **Raw observation (preserved).** Acceptable; this is the evidence layer.
- **Corrected interpretive claim (post-patch wording).** Acceptable; should describe the lossy fallback condition explicitly.
- **Unrelated string match.** Acceptable when the word appears in different context (e.g., "supported" in a sentence about supported sandbox carve-outs).
- **Surviving overclaim.** STOP. Do not commit. Surface to the user.

No surviving site may claim command-approval is "supported" without the lossy-fallback qualification, or claim `availableDecisions` is "preserved" without naming the all-strings fallback condition, or list `item/commandExecution/requestApproval` under `supported_methods` / "observed supported methods" without that qualification, or assert "proves compatibility" for command-approval response semantics, or assert `ready_to_close_ticket: true` for `item/commandExecution/requestApproval`.

---

## Tasks

### Task 1: Inventory and discovery

**Files:** read-only — no writes in this task.

- [ ] **Step 1.1: Pre-edit ripgrep sweep.**

```bash
rg -n "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

Expected: enumerate every match. For each match, annotate one of: `raw-observation`, `interpretive-overclaim`, `corrected-language` (if any already exist), `unrelated`. The annotated list is reused in Task 5 as the baseline for diff verification. Confirm the four enumerated overclaim sites in the diagnostic `.md` (≈lines 112, 169-174, 176-181, 185) appear in the output and are tagged `interpretive-overclaim`. If the sweep surfaces additional `interpretive-overclaim` sites this plan does not enumerate, fire the "pre-edit sweep finds an overclaim site this plan does not enumerate" stop condition.

- [ ] **Step 1.2: Confirm `_resolve_available_decisions` semantics.**

Read `packages/plugins/codex-collaboration/server/approval_router.py:90-115`. Verify the all-strings condition is `isinstance(wire_value, list) and all(isinstance(decision, str) for decision in wire_value)`. Locate `_AVAILABLE_DECISIONS` (likely defined elsewhere in the same file) and capture its `command_approval` tuple contents verbatim — this string set lands in Task 2's replacement wording.

- [ ] **Step 1.3: Confirm rebaseline-plan framing.**

Read `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md:895-925`. Note the exact phrasing: "decision-shape lossy", "structured `acceptWithExecpolicyAmendment`", "the live request offered `cancel` but not `decline`", "lossless parser/response branch". The diagnostic's corrected wording in Task 2 mirrors this language to keep the doc set internally consistent.

- [ ] **Step 1.4: Determine sibling-JSON disposition.**

Check whether `docs/diagnostics/codex-app-server-server-request-envelope-probes.json` exists.

If it does not exist → Task 3 is a no-op; record this for Task 6's commit message.

If it exists:

```bash
jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json | rg -n "supported|preserved|ready_to_close_ticket|local_compatibility|supported_methods|proves compatibility|compatibility for the observed"
```

Two known overclaim paths in the JSON (verified at orientation; reconfirm exact paths here):

- `observed_server_requests[0].local_compatibility: "supported"` (≈line 904)
- `compatibility_classification.supported_methods: ["item/commandExecution/requestApproval"]` (≈line 913)

Both must be addressed by Task 3. If the sweep surfaces other overclaim paths this plan does not enumerate, treat them as in-scope (mirror what the `.md` sites express) and record the additional paths for Task 3.

**Vocabulary caveat.** The JSON's `compatibility_classification` block uses a binary vocabulary: `supported_methods` / `unsupported_methods` / `unknown_or_unparseable_methods` / `missing_required_fields`. The corrected classification we are introducing — *parser-kind compatible but decision-shape lossy* — has no slot in this vocabulary. This pushes the disposition decision toward supersession-note rather than patch-in-place, because patch-in-place either requires inventing a new key (schema change, may break consumers) or zeroing `supported_methods` and adding a sibling array (mutating an existing array's semantics).

Disposition options, in preference order:

1. **Supersession note** (preferred when the JSON has any external consumer). Add a top-level `"_superseded_by"` field pointing at the corrected `.md` and the rebaseline plan section. Leave existing fields untouched. This avoids vocabulary expansion and keeps machine consumers from silently consuming the now-corrected classification as if it were still authoritative.
2. **Patch-in-place** (preferred only if the JSON is documented as having no machine consumers and the binary vocabulary expansion is acceptable). Then `observed_server_requests[0].local_compatibility` becomes a value naming the lossy class, `compatibility_classification.supported_methods` becomes `[]`, and a new sibling field `parser_kind_compatible_methods: ["item/commandExecution/requestApproval"]` is added.

If the consumer-status of the JSON is unclear → choose supersession-note (safer) and note the uncertainty in the commit message.

If a third option seems necessary (e.g., partial patch + partial supersession) → trigger the "JSON disposition unsafe" stop condition rather than improvising.

Record the disposition explicitly. Task 2 wording cross-references the JSON form chosen here.

- [ ] **Step 1.5: Determine register-annotation need.**

Read `docs/status/codex-collaboration-reconciliation-register.md:9-70`. Check:

- Does the priority `#1` line at ~line 52 still say "Implement `T-20260429-01` Phase 1 sandbox carve-outs"?
- Does the `T-20260429-01` row "Current truth" cell at ~line 67 still describe the work as unlanded?

If both already reflect landed-implementation status → Task 4 is a no-op. Skip it; do not edit the register.

If either still implies implementation is pending → Task 4 will land an annotation.

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
- `availableDecisions` is present on the wire (see "Observed Server Requests" above), but `_resolve_available_decisions` (`approval_router.py:103-111`) preserves the wire list only when every entry is a `str`. The observed mixed list contains a structured `acceptWithExecpolicyAmendment` entry, so the parser falls back to `_AVAILABLE_DECISIONS[command_approval]`. The fallback tuple includes `decline`; the live envelope offered `cancel`, not `decline`. Decision-shape preservation is therefore lossy and command-approval response compatibility is not established. See `docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md` "Command Approval Decision-Shape Boundary" for the lossless-branch forward path.
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
rg -n "supported|preserved|proves compatibility|compatibility for the observed" \
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
| JSON exists, patch-in-place chosen | Step 3.2. |
| JSON exists, supersession-note chosen | Step 3.3. |
| JSON disposition unsafe | Stop condition fired in Task 1.4; surface to user. |

- [ ] **Step 3.2: Patch JSON in place (only if patch-in-place was chosen).**

Mirror the `.md` correction. Address each known overclaim path explicitly — both must be patched, plus any additional paths surfaced in Task 1.4:

1. **`observed_server_requests[0].local_compatibility`** (currently `"supported"`):
   - Replace value with `"parser_kind_compatible_decision_shape_lossy"`.
   - Append to `local_compatibility_notes` array: `"Decision-shape lossy under the observed mixed availableDecisions: the structured acceptWithExecpolicyAmendment entry triggers all-strings fallback in _resolve_available_decisions (approval_router.py:103-111); the fallback tuple _AVAILABLE_DECISIONS[command_approval] includes decline, while the live envelope offered cancel."`

2. **`compatibility_classification.supported_methods`** (currently `["item/commandExecution/requestApproval"]`):
   - Set value to `[]` (no methods are fully supported by this packet).
   - Add sibling field `parser_kind_compatible_methods: ["item/commandExecution/requestApproval"]`.
   - Add sibling field `decision_shape_lossy_methods: ["item/commandExecution/requestApproval"]`.
   - Append to `compatibility_classification.notes` array: `"item/commandExecution/requestApproval is parser-kind compatible but decision-shape lossy under the observed availableDecisions; see local_compatibility_notes for the observed envelope."`

3. **Any field claiming `availableDecisions` is `preserved: true`** (if surfaced):
   - Set `preserved: false` and add a sibling field `preservation_note` (or the JSON's existing convention) with the same all-strings-fallback explanation as in (1).

4. **Any field flagged `ready_to_close_ticket: true` for command-approval** (if surfaced):
   - Set `false` and add a sibling field naming the missing closure work (smoke + credential-boundary probe + lossless parser/response branch).

Do not delete or rewrite raw observation fields (params keys, redacted envelope summary, observed `availableDecisions` array, etc.).

If Task 1.4 documented additional overclaim paths beyond items 1 and 2 above, address them here using the same mutate-value-plus-add-sibling-note pattern. Do not silently leave them in place.

- [ ] **Step 3.3: Add supersession note to JSON (only if supersession-note was chosen).**

Add a top-level field — choose name to match local JSON conventions; suggested default: `"_superseded_by"` — with value:

```json
{
  "_superseded_by": {
    "fix_doc": "docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md",
    "authority": "docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md#L905-L921",
    "summary": "Local compatibility classification revised to parser-kind compatible but decision-shape lossy. Raw observation fields below are preserved; their classification labels are no longer authoritative."
  }
}
```

Do not delete or modify the existing fields.

- [ ] **Step 3.4: Validate JSON (only if Step 3.2 or 3.3 ran).**

```bash
jq '.' docs/diagnostics/codex-app-server-server-request-envelope-probes.json >/dev/null
```

Expected: exit `0`. If non-zero, fix the JSON before staging.

- [ ] **Step 3.5: Local rg verification (only if Step 3.2 or 3.3 ran).**

```bash
rg -n "supported|preserved|ready_to_close_ticket" \
   docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected: no bare `"supported"` classification of command-approval. No `preserved: true` for `availableDecisions` without the qualifying sibling field. No `ready_to_close_ticket: true` for command-approval. If supersession-note path was taken, the original fields may still match the four search terms; their presence is acceptable because they are bracketed by the supersession note.

- [ ] **Step 3.6: Stage the JSON change (only if Step 3.2 or 3.3 ran).**

```bash
git add docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

---

### Task 4: Optional reconciliation-register annotation

**Files:**

- Conditional Modify: `docs/status/codex-collaboration-reconciliation-register.md`. Skip entirely if Task 1.5 found the register already reflects landed-implementation status.

- [ ] **Step 4.1: Branch on the Task 1.5 disposition.**

| Task 1.5 outcome | This task |
|---|---|
| Register already reflects landed-implementation | Skip to Task 5. |
| Priority #1 still says "Implement…" or row 67 still describes work as unlanded | Step 4.2. |

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

- [ ] **Step 4.4: Local rg verification of the register.**

```bash
rg -n "T-20260429-01|Implement.*Phase 1" \
   docs/status/codex-collaboration-reconciliation-register.md
```

Expected: every `T-20260429-01` line either reflects landed-implementation, names AC #1-#3 closure work, or is general Phase 1 context. No surviving "Implement `T-20260429-01` Phase 1" framing in the priority order.

Note: the register's global "Last reconciled" date at ≈line 9 is intentionally left unchanged. This patch reconciles only the T-20260429-01 row and priority `#1` line, not the full register; bumping the global date would overstate the scope of this commit. Row-local recency is captured by the "As of 2026-05-09" date stamp inside Step 4.2's annotation.

- [ ] **Step 4.5: Stage the register change.**

```bash
git add docs/status/codex-collaboration-reconciliation-register.md
```

---

### Task 5: Final verification sweep

**Files:** read-only — no writes in this task.

- [ ] **Step 5.1: Run the full sweep.**

```bash
rg -n "supported|preserved|lossy|ready_to_close_ticket|proves compatibility|compatibility for the observed|local_compatibility|supported_methods" \
   docs/diagnostics/2026-05-01-codex-app-server-*.md \
   docs/diagnostics/codex-app-server-*.json \
   docs/plans/2026-05-01-codex-app-server-*.md \
   docs/tickets/2026-04-29-codex-collaboration-*.md \
   docs/status/codex-collaboration-reconciliation-register.md
```

- [ ] **Step 5.2: Classify every match.**

For each line in the output:

- `raw-observation` (preserved evidence) → OK.
- `corrected-interpretive-claim` (post-patch wording — should now describe lossy fallback) → OK.
- `unrelated` (different context) → OK.
- `surviving-overclaim` → STOP. Do not commit. Surface to the user with file path, line number, and proposed correction.

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

**Files:** previously staged via Steps 2.7, 3.6 (conditional), 4.5 (conditional).

- [ ] **Step 6.1: Confirm staged set.**

```bash
git status
```

Expected: only the docs files. Working tree otherwise clean.

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
`_AVAILABLE_DECISIONS[command_approval]`, which includes `decline`.
The live envelope offered `cancel`, not `decline`.

This commit corrects the diagnostic's interpretive layer; raw
envelope observations are preserved unchanged. The sibling JSON is
reconciled (in-place patch or supersession note, whichever was
selected). Optional register annotation records that
T-20260429-01 Phase 1 implementation has landed on main; closure
evidence for ticket acceptance criteria #1-#3 (comparable
`/delegate` smoke with avoidable sandbox-friction escalations <=2;
credential-boundary probe; `test_runtime.py` regression assertion
update + full codex-collaboration suite pass) is the remaining
work. AC #4 (Option F upstream limitation) is already checked.

T-20260429-02 method-by-method classification scope is unchanged
and not addressed here.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6.3: Confirm commit landed cleanly.**

```bash
git status
git log -1 --stat
```

Expected: clean working tree; the commit lists only `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md` and any conditional files staged in Steps 3.6 / 4.5. No code files.

---

## Self-Review Checklist

Run this before requesting plan approval. If any box is unchecked, fix in place.

- [x] **Spec coverage.** Each of the user's six requested sections is present and explicit:
  1. Raw envelope facts to preserve → "Raw Envelope Facts To Preserve" section.
  2. Interpretive overclaims to patch → "Interpretive Overclaims To Patch" section (four sites).
  3. Authority basis: `approval_router.py` + repaired rebaseline plan → "Authority Basis" section.
  4. Files to inspect before edit, including JSON → "Files To Inspect Before Edit" table.
  5. Stop condition for JSON disposition → "Stop Conditions" section + Task 1.4 + Task 3 branching.
  6. Verification rg pattern covers bare-word terms (`supported`/`preserved`/`lossy`/`ready_to_close_ticket`) plus phrase patterns (`proves compatibility`/`compatibility for the observed`) plus JSON-key patterns (`local_compatibility`/`supported_methods`) → "Verification" section + Task 1.1 + Task 5.
- [x] **Overclaim inventory.** Four `.md` sites enumerated (≈lines 112, 169-174, 176-181, 185); two known JSON paths enumerated (`observed_server_requests[0].local_compatibility`, `compatibility_classification.supported_methods`) with placeholder for additional paths surfaced in Task 1.4.
- [x] **Scope guardrails.** "This plan does not" enumerates: no code edits, no T-20260429-02 method matrix, no live probes, no version-pin changes.
- [x] **Register annotation matches ticket reality.** Task 4 wording names AC #1, #2, AND #3 explicitly as the unchecked closure criteria; "only smoke and probe remain" was rejected because AC #3 (regression-assertion update + suite pass) is also unchecked.
- [x] **Register reconciliation scope is narrow.** No global "Last reconciled" bump. Only the T-20260429-01 row and priority `#1` line are touched; row-local recency is captured by the in-cell "As of 2026-05-09" stamp.
- [x] **Optional register note.** Task 4 is conditional on Task 1.5; skips cleanly when register already reflects landed implementation.
- [x] **Placeholder scan.** No "TBD", no "appropriate", no "similar to Task N", no "handle edge cases". Replacement wording for all four `.md` overclaim sites is shown verbatim.
- [x] **Wording consistency.** "Decision-shape lossy" used consistently in `.md`, JSON, and register paths. "Parser-kind compatible" used consistently when distinguishing from "fully supported." `_resolve_available_decisions`, `_AVAILABLE_DECISIONS[command_approval]`, and `approval_router.py:103-111` named identically across tasks.
- [x] **Bite-sized steps.** Each step is a single action: one rg, one read, one edit, one git command. No multi-action steps.

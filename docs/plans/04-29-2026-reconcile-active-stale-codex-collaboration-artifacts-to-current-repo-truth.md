# Reconcile Active Stale Codex-Collaboration Artifacts to Current Branch Truth

## Adaptation Note (v2, 2026-04-29)

This plan supersedes the original v1 written earlier on 2026-04-29. The v1 plan
was authored before the session that closed T-20260423-01 (commit `6580d86e`),
opened T-20260429-01 (commit `aa3daed2`), updated the reconciliation register
twice, and made 2 targeted edits to the diagnostic doc. v2 is the execution
authority; v1 is archived context only.

Key v1 → v2 changes:

- **Removed** T-01 ticket from the patch set (already closed at
  `docs/tickets/closed-tickets/`; v1's rewrite-as-open instruction is
  impossible).
- **Strengthened** T-02 closure rationale to cite T-01 closure evidence, not
  just Packet 1 merge.
- **Rewrote** register instructions against the register's current state
  (includes `T-20260429-01`, excludes already-removed `T-20260423-01` and
  `T01-DIAGNOSTIC-HEADER`).
- **Scoped** diagnostic doc changes to supersession note only (status-line and
  Candidate B wording already corrected by prior 2-line edit).
- **Narrowed** design doc cleanup to header/overview/blocking language only;
  deep `Packet 2+` technical-rationale references preserved as historical
  design provenance.
- **Labeled** each verification check as `[v2-edit]`, `[pre-existing]`, or
  `[non-regression]` to prevent the ghost-commit problem.

## Summary

This is a docs-only reconciliation commit. No code, schema, or runtime changes.

Patch only these active artifacts:

- `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md`
- `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md`
- `docs/superpowers/specs/codex-collaboration/delivery.md`
- `docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md`
- `docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md`
- `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md`
- `docs/status/codex-collaboration-reconciliation-register.md`

Out of scope, even if they preserve older wording:

- `docs/handoffs/**`
- `docs/handoffs/archive/**`
- `docs/plans/archive/**`
- `docs/benchmarks/**`
- `docs/assessments/**`
- `docs/tickets/closed-tickets/**`
- any top-level `docs/tickets/*.md` file not listed above

Required execution order:

1. Patch the six source artifacts first.
2. Run source-artifact verification against the worktree.
3. Update the register last.
4. Run register verification against the worktree.
5. Stage all edited files only after all worktree verification passes.
6. Run final post-staging tracking verification.

No file should be staged before the register is fully reconciled.

## Implementation Changes

### 1. Close T-20260423-02 in place

Target: `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md`

Close this ticket in place (do not `git mv` to `closed-tickets/`). Rationale:
bundling a rename into a 7-file reconciliation commit adds rename-detection
noise to the diff; the frontmatter `status: closed` is unambiguous. A separate
follow-up can move it to `closed-tickets/` if the convention must be
consistent.

Frontmatter changes:

- `status: closed`
- `closed_date: 2026-04-29`
- `resolution: completed`
- remove `blocks: [T-20260423-01]`
- add `resolution_ref` citing: PR #126 (`36ef13e8`) for Packet 1 merge,
  Candidate A sandbox policy promotion (`ce0579f6`), live `/delegate` smoke
  (`a7a4e9c9`), T-01 closure (`6580d86e`), and Packet 1 carry-forward
  verification at
  `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md`

Body rewrite:

- Rewrite from design-phase / blocker framing to landed-and-closed closure.
- State that Packet 1 landed through Phase H and merged via PR #126 /
  `36ef13e8`.
- State that T-20260423-01 was subsequently closed after live `/delegate`
  smoke validation (commit `6580d86e`), so the `blocks` relationship is fully
  resolved.
- State that the diagnostic run record
  (`docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md`) found
  amendment admission is not currently required for the observed canonical
  delegation flow, so the ticket's original follow-up-ticket premise
  (amendment-admission layer stacking on top of T-02's primitives) is no
  longer current truth.
- Move residual debt ownership to `carry-forward.md`.
- Remove all live claims that Packet 2, `approve_amendment`, or amendment
  admission is required to close T-20260423-01.

### 2. Rewrite T-20260416-01 post-benchmark section

Target: `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md`

Replace the `## Post-benchmark follow-up` section and `## B5 and B8
reproduction expectations` section with a shorter current-truth section stating:

- The benchmark track is complete (Tiers A and B concluded; parent ticket
  `T-20260330` at
  `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`
  is closed).
- The bug reproduced on B3 candidate and B5 candidate (both terminated with the
  same `CommittedTurnParseError` / items-array extraction mismatch). Evidence:
  `docs/benchmarks/dialogue-supersession/v1/summary.md` and
  `docs/benchmarks/dialogue-supersession/v1/runs.json`.
- The bug did not reproduce on B8 candidate (converged normally). Evidence: same
  sources.
- The contract-integrity constraint on mid-track patching is now historical
  (benchmark track complete); the fix is no longer deferred.
- The next step is to land the fix with tests and run one post-patch
  verification.

Also update the stale parent-ticket reference path in the References table:

- From: `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`
- To: `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`

Keep all other sections unchanged (Dual record, Symptom, Reproduction context,
Root cause, Why the B3 run stays valid, Proposed fix, Closure criteria,
References).

### 3. Add current deployment profile to delivery.md

Target: `docs/superpowers/specs/codex-collaboration/delivery.md`

Preserve history and add current truth:

- Rename the existing `### R1/R2 Deployment Profile` heading to
  `### R1/R2 Historical Deployment Profile`.
- Add a new adjacent block `### Current Dev-Repo Deployment Profile (2026-04-29)`.
- New block must list the current live MCP surface:
  - `codex.status`
  - `codex.consult`
  - `codex.dialogue.start`
  - `codex.dialogue.reply`
  - `codex.dialogue.read`
  - `codex.delegate.start`
  - `codex.delegate.poll`
  - `codex.delegate.decide`
  - `codex.delegate.promote`
  - `codex.delegate.discard`
- New block must state: deployed as a Claude Code plugin via marketplace
  (`turbo-mode` bundle), not a bare MCP server from repo checkout.
- New block must not contain "no delegation/promotion path."

### 4. Replace stale consult open-question in rewrite-map

Target: `docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md`

Remove the `#### Keep the open question about codex.consult` section (lines
147-152) and replace it with a short resolved-decision pointer:

- State that `decisions.md` resolves the `codex.consult` surface (§"`codex.consult` Surface", line 150+).
- Preserve only the re-evaluation trigger: `codex.consult` retirement
  re-enters scope only if specific upstream capability triggers fire (per
  `decisions.md` rationale).

### 5. Add supersession note to diagnostic doc

Target: `docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md`

Add a `> **Supersession note (2026-04-29):**` block immediately after the
title line (before `Date:`). The note must state:

- Candidate A has since landed (sandbox policy promotion at `ce0579f6`,
  live `/delegate` smoke at `a7a4e9c9`, T-01 closed at `6580d86e`).
- The run record remains evidence for the mechanism decision; it is not a
  live operational document.
- Amendment admission / Packet 2 was later judged not currently required for
  the observed canonical delegation flow.

Do NOT modify the status line or the Candidate B scope note — those were
already corrected by a prior 2-line edit (the `git diff` shows "Engineering
action completed" and "post-Candidate-A-success conditional" already in the
working tree). The v2 plan does not own those changes.

### 6. Scope design doc to header/overview/blocking language only

Target: `docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md`

Add a `> **Supersession note (2026-04-29):**` block immediately after the
title line (before `## Overview`). The note must state:

- Packet 1 is implemented and merged (PR #126 / `36ef13e8`).
- T-20260423-01 is closed (live smoke validated, closure at `6580d86e`).
- This document remains the historical Packet 1 design authority.
- Amendment admission / Packet 2 was later judged not currently required.
- Technical rationale referencing "Packet 2+" in deeper sections is preserved
  as historical design provenance; those references describe future-iteration
  scope boundaries, not current blocking claims.

Header/overview changes (content-matched, not line-offset-dependent):

Line numbers below reference the **pre-edit** file state. The supersession note
insertion (above) shifts all subsequent lines. Use the quoted text for matching,
not line offsets.

- **Pre-edit line 9** — text: `**Blocks:** T-20260423-01 (parent
  acceptance-gap ticket; AC1 — end-to-end delegation with platform-tool
  verification).`
  Action: Remove the line entirely, or rewrite to `**Blocked (historical):**
  T-20260423-01 — resolved; T-01 closed 2026-04-29 at commit 6580d86e.`
- **Pre-edit line 13** — text ending with: `D1–D6, D9, D11, D12 survive and
  apply to the amendment-admission follow-up ticket (Packet 2), not here.`
  Action: Rewrite the parenthetical to remove "Packet 2" as a live reference.
  Replace with: `D1–D6, D9, D11, D12 survive from the rejected spec and would
  apply to any future amendment-admission work, not to this document.`
- **Pre-edit line 30** — text: `- **Amendment admission** (allowlist,
  classifier, \`approve_amendment\` verb, amendment-specific audit). Lives in
  the follow-up ticket on top of this packet's primitives.`
  Action: Rewrite to: `- **Amendment admission** — not currently required for
  the observed canonical delegation flow (per the diagnostic run record). If
  revisited, would stack on this packet's primitives.`

Deeper technical references preserved as-is (no edits):

- Line 1680 (`request_user_input` response-payload provenance, `Packet 2+`
  future negotiation)
- Line 1695 (`Packet 2+` empty-answers fallback future improvement)
- Line 2261 (`Packet 2` timeout automation expansion scope boundary)

These three lines are the only literal "Packet 2" hits in the deep technical
sections. They use "Packet 2" as a time marker for future-iteration scope, not
as a current blocking claim. The design doc also contains ~10 "future packet"
references (lowercase, no number — e.g., line 1936) that are the same class of
historical provenance. The supersession note at the top contextualizes all
forward-looking language generically.

Final verification rule for this file:

- no `**Blocks:**` line claiming this design doc currently blocks T-20260423-01
- no current-reader-facing use of "Packet 2" as a live required next packet
  in the header/overview/non-goals (up to `## Scope and Non-Goals` heading)
- deep technical rationale hits at lines 1680, 1695, 2261 are expected and
  acceptable (3 literal "Packet 2" hits; ~10 additional "future packet"
  references are the same class of provenance)

### 7. Update register against live state

Target: `docs/status/codex-collaboration-reconciliation-register.md`

Update only after the source artifacts above are patched and verified.

Remove from Ticket-Owned Active Work:

- `T-20260423-02` row (ticket being closed by this patch)

Do NOT remove or re-add:

- `T-20260423-01` (already removed by commit `6580d86e`; it is not in the
  current register)
- `T-20260429-01` (added by commit `aa3daed2`; keep it — it is current open
  work)

Remove from Spec And Documentation Reconciliation Debt:

- `DELIVERY-ROLLOUT-PROFILE` (resolved by §3 above)
- `T16-BLOCKER-MODEL` (resolved by §2 above)
- `REWRITE-MAP-CONSULT-QUESTION` (resolved by §4 above)

Do NOT attempt to remove:

- `T01-DIAGNOSTIC-HEADER` (already removed before commit `aa3daed2`; not in
  the current register)

Rewrite Current Priority Order to reflect remaining open work:

1. Land the `T-20260416-01` extraction fix and run one post-patch verification.
2. Implement `T-20260429-01` Phase 1 sandbox carve-outs (Options B + E) and
   validate via a comparable `/delegate` smoke with ≤2 escalations.
3. Sweep Packet 1 carry-forward debt: `TT.1`, `RT.1`, `P1-MINOR-SWEEP`.
4. Convert `BMARK-L1-L3` into explicit follow-up tickets or deliberately
   decline those L1/L2/L3 items as non-goals.
5. Specify or explicitly defer `AUDIT-CONSUMER-INTERFACE`.

Add new rows introduced by this patch:

- `CONTRACTS-T02-TEMPORAL-MARKER` in Spec And Documentation Reconciliation
  Debt: `contracts.md:327` uses `T-20260423-02` as a temporal marker
  ("Post-Packet 1 (T-20260423-02)") in normative contract text. Now that T-02
  is closed, the reference is stale attribution in a normative document. Exit
  condition: rewrite to a non-ticket-specific temporal marker or add a
  "(closed)" annotation.
- `T02-CLOSED-TICKET-PATH` in Spec And Documentation Reconciliation Debt:
  T-20260423-02 was closed in place at `docs/tickets/` rather than moved to
  `docs/tickets/closed-tickets/` to avoid rename-detection noise in the 7-file
  reconciliation commit. Exit condition: `git mv` to `closed-tickets/` in a
  subsequent housekeeping commit.

Keep these rows if still true after patching:

- `T-20260416-01` (Ticket-Owned Active Work)
- `T-20260429-01` (Ticket-Owned Active Work)
- `TT.1` (Residual Carry-Forward Debt)
- `RT.1` (Residual Carry-Forward Debt)
- `P1-MINOR-SWEEP` (Residual Carry-Forward Debt)
- `BMARK-L1-L3` (Benchmark-Carried Follow-On Work) with all three caveats
- `AUDIT-CONSUMER-INTERFACE` (Open Spec Questions)
- `DIALOGUE-FORK` (Intentional Future-Scope Deferrals)
- `MCP-STRUCTURED-ERROR-REASON` (Intentional Future-Scope Deferrals)

Update `Last reconciled:` date to `2026-04-29`.

Remove from Current Priority Order any reference to:

- "Reconcile stale authority artifacts" (this patch resolves it)
- "Rewrite T-20260423-02" (this patch resolves it)
- "Complete the post-restart live `/delegate` smoke for T-20260423-01"
  (T-01 is closed; smoke already completed)

## Verification

### Source-artifact verification, before register edits

**T-20260423-02 ticket (v2 edits):**

```bash
# [v2-edit] Verify stale Packet 2 / amendment framing removed
rg -n 'follow-up ticket covers amendment admission|approve_amendment|unblocks the amendment-admission follow-up|Packet 2' docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
```

Expected: no hits.

```bash
# [v2-edit] Verify closure frontmatter
rg -n 'status: closed' docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
rg -n 'resolution: completed' docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
rg -n '6580d86e' docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
```

Expected: one hit each.

```bash
# [v2-edit] Verify blocks relationship removed
rg -n 'blocks: \[T-20260423-01\]' docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
```

Expected: no hits.

**T-20260416-01 ticket (v2 edits):**

```bash
# [v2-edit] Verify stale benchmark-deferral language removed
rg -n 'until the scored benchmark track completes|Sequence after benchmark completion|If reproduction occurs:' docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md
```

Expected: no hits.

```bash
# [v2-edit] Verify current-truth B5/B8 wording with citations
rg -n 'reproduced on B3 candidate and B5 candidate' docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md
rg -n 'summary\.md' docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md
```

Expected: one hit each.

```bash
# [v2-edit] Verify stale parent-ticket path removed
rg -n 'docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md' docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md
```

Expected: no hits.

```bash
# [v2-edit] Verify corrected parent-ticket path present
rg -n 'docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md' docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md
```

Expected: one hit.

**delivery.md (v2 edits):**

```bash
# [v2-edit] Verify historical rename and new block
rg -n 'R1/R2 Historical Deployment Profile' docs/superpowers/specs/codex-collaboration/delivery.md
rg -n 'Current Dev-Repo Deployment Profile \(2026-04-29\)' docs/superpowers/specs/codex-collaboration/delivery.md
rg -n 'codex\.delegate\.discard' docs/superpowers/specs/codex-collaboration/delivery.md
```

Expected: one hit each.

**official-plugin-rewrite-map.md (v2 edits):**

```bash
# [v2-edit] Verify stale open-question removed
rg -n 'Keep the open question about codex.consult' docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md
```

Expected: no hits.

```bash
# [v2-edit] Verify resolved-decision pointer present
rg -n 'decisions\.md' docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md
```

Expected: at least one hit.

**Diagnostic doc (v2 edit + pre-existing):**

```bash
# [v2-edit] Verify supersession note added
rg -n 'Supersession note \(2026-04-29\)' docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md
```

Expected: one hit.

```bash
# [pre-existing, not v2] Verify status line was already corrected (by prior 2-line edit)
rg -n 'Engineering action pending' docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md
```

Expected: no hits. NOTE: this check passes because of a prior edit, not because
of this plan. If it fails, investigate the prior edit, not this plan.

**Design doc (v2 edits):**

```bash
# [v2-edit] Verify supersession note added
rg -n 'Supersession note \(2026-04-29\)' docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md
```

Expected: one hit.

```bash
# [v2-edit] Verify Blocks: line removed or rewritten as historical
rg -n '^\*\*Blocks:\*\* T-20260423-01' docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md
```

Expected: no hits (either removed or rewritten to `**Blocked (historical):**`).

```bash
# [v2-edit] Verify header/overview Packet 2 current-framing removed (up to ## Scope heading)
sed -n '1,/^## Scope and Non-Goals/p' docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md | rg 'Packet 2'
```

Expected: no hits. NOTE: uses heading-anchored boundary (`## Scope and
Non-Goals`) rather than a line count, because the supersession note insertion
shifts line numbers.

```bash
# [v2-edit] Verify non-goals amendment-admission rewrite was applied
# (The original text at pre-edit line 30 did not contain literal "Packet 2",
# so the sed/rg check above does not verify this edit. This positive-presence
# check fills that gap.)
rg -n 'not currently required for the observed canonical delegation flow' docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md
```

Expected: one hit (in the non-goals section).

```bash
# [non-regression] Deep technical Packet 2+ references preserved as historical provenance
rg -n 'Packet 2' docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md
```

Expected: hits at approximately lines 1680, 1695, 2261 (3 hits — historical
design provenance, intentionally preserved). Line 1936 contains "future packet"
(no number), not "Packet 2", and will NOT appear in this grep.

### Register verification, after register edits and before staging

```bash
# [v2-edit] Verify resolved drift rows removed
rg -n 'DELIVERY-ROLLOUT-PROFILE|T16-BLOCKER-MODEL|REWRITE-MAP-CONSULT-QUESTION' docs/status/codex-collaboration-reconciliation-register.md
```

Expected: no hits.

```bash
# [v2-edit] Verify T-20260423-02 removed from active work
rg -n 'T-20260423-02' docs/status/codex-collaboration-reconciliation-register.md
```

Expected: no hits.

```bash
# [pre-existing, not v2] Verify T-01 is already absent (removed by commit 6580d86e)
rg -n 'T-20260423-01' docs/status/codex-collaboration-reconciliation-register.md
```

Expected: no hits. NOTE: T-01 was removed from the register by a prior commit,
not by this plan.

```bash
# [pre-existing, not v2] Verify T-20260429-01 is present (added by commit aa3daed2)
rg -n 'T-20260429-01' docs/status/codex-collaboration-reconciliation-register.md
```

Expected: one hit. NOTE: this row was added by a prior commit and must be
preserved, not removed.

```bash
# [v2-edit] Verify new drift rows added by this patch
rg -n 'CONTRACTS-T02-TEMPORAL-MARKER' docs/status/codex-collaboration-reconciliation-register.md
rg -n 'T02-CLOSED-TICKET-PATH' docs/status/codex-collaboration-reconciliation-register.md
```

Expected: one hit each.

```bash
# [non-regression] Verify retained rows still present
rg -n 'BMARK-L1-L3' docs/status/codex-collaboration-reconciliation-register.md
rg -n 'TT\.1' docs/status/codex-collaboration-reconciliation-register.md
rg -n 'RT\.1' docs/status/codex-collaboration-reconciliation-register.md
rg -n 'P1-MINOR-SWEEP' docs/status/codex-collaboration-reconciliation-register.md
rg -n 'AUDIT-CONSUMER-INTERFACE' docs/status/codex-collaboration-reconciliation-register.md
rg -n 'DIALOGUE-FORK' docs/status/codex-collaboration-reconciliation-register.md
rg -n 'MCP-STRUCTURED-ERROR-REASON' docs/status/codex-collaboration-reconciliation-register.md
```

Expected: each remaining intended row still appears.

### Final post-staging verification

Stage all edited files plus this plan file:

```bash
git add \
  docs/tickets/2026-04-23-deferred-same-turn-approval-response.md \
  docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md \
  docs/superpowers/specs/codex-collaboration/delivery.md \
  docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md \
  docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md \
  docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md \
  docs/status/codex-collaboration-reconciliation-register.md \
  docs/plans/04-29-2026-reconcile-active-stale-codex-collaboration-artifacts-to-current-repo-truth.md
```

Then verify all 8 files are staged:

```bash
git diff --cached --name-only | sort
```

Expected output (all 8 files, sorted):

```
docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md
docs/plans/04-29-2026-reconcile-active-stale-codex-collaboration-artifacts-to-current-repo-truth.md
docs/status/codex-collaboration-reconciliation-register.md
docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md
docs/superpowers/specs/codex-collaboration/delivery.md
docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md
docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md
docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
```

If any file is missing, the `git add` command failed silently (check path
typos). If extra files appear, unstaged work was accidentally swept in.

The plan file is staged as execution provenance — it documents what this commit
intended to accomplish and provides the v1→v2 adaptation trail.

## Commit Message

Type/scope: `docs(codex-collaboration)`.

The commit message must note:

- This is a docs-only reconciliation commit (no code, schema, or runtime
  changes).
- Executed from v2 of the reconciliation plan (adapted from v1 after T-01
  closure and register updates).
- Closes T-20260423-02 in place.
- Reconciles delivery.md, rewrite-map.md, T-20260416-01, and the design doc
  to current repo truth.
- Adds supersession notes to the diagnostic doc and design doc.
- The diagnostic doc also includes a pre-existing 2-line correction (status
  line + Candidate B wording) that predates this plan and is staged here for
  completeness.
- The plan file itself is included in this commit as execution provenance.

## Assumptions

- This is one coherent docs-only commit.
- No file is staged until all worktree verification passes.
- `docs/tickets/closed-tickets/**` are out of scope (evidence only, not patch
  targets). This includes the now-closed T-01 ticket.
- `docs/benchmarks/**` transcript echoes of stale wording remain untouched as
  historical outputs.
- Rewritten active docs must cite source evidence in prose rather than assert
  new truth without attribution.
- `T-20260423-02` closes because BOTH Packet 1 is implemented/merged AND
  T-01 is now closed with live-smoke validation. The original v1 rationale
  (Packet 1 only) is subsumed by this stronger evidence.
- The diagnostic doc's prior 2-line edit (status line + Candidate B wording) is
  a pre-existing change that this plan does not own or take credit for. It will
  be staged alongside v2 edits in the same commit (since it is currently
  unstaged), but the verification section labels it explicitly as pre-existing.
- **Out-of-scope reference audit (2026-04-29):** `rg -l 'T-20260423-02' docs/`
  found 25 files. Categorized:
  - 5 in-scope (register, diagnostic, design doc, T-02 ticket, this plan) —
    handled by the patch set.
  - 18 in Packet 1 implementation plans (`docs/plans/2026-04-24-packet-1-*`) —
    historical build artifacts, not active docs. Out of scope.
  - 1 in `contracts.md` (line 327: "Post-Packet 1 (T-20260423-02)") —
    normative text with an embedded temporal marker referencing a now-closed
    ticket. Out of scope for this commit; tracked as new drift row
    `CONTRACTS-T02-TEMPORAL-MARKER` in the register.
  - 1 in `docs/plans/2026-04-23-t07-cross-model-removal-7e.md` — historical
    plan. Out of scope.
  No missed in-scope files.

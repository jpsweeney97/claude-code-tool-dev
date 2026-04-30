# Codex-Collaboration Status Documents — Verification Report

> **Scope:** Reject-first verification of three current-facing status artifacts:
> - `docs/status/codex-collaboration-current-state.md`
> - `docs/status/codex-collaboration-reconciliation-register.md`
> - `docs/assessments/2026-04-29-codex-collaboration-verified-drift-report.md`
>
> **Method:** Each material claim treated as unverified until directly checked
> against primary repo evidence (source files, ticket frontmatter, git history,
> tests). Findings categorized by current-HEAD truth, snapshot-bounded truth,
> and unverified.

## Verification Frame

This review verifies claims against the repository at current HEAD `19cd5183`. Where evidence at the drift report's declared analysis snapshot `88f098a1` would change a verdict, that is called out explicitly. **D-04 is the only frame-sensitive finding identified during this targeted recheck.** Every finding was not replayed against the snapshot — readers should not infer systematic snapshot replay.

**Artifact relationship.** This audit is a verification note over the saved drift report, not a replacement for it. If retained as a repo artifact, this audit should either supersede the prior verification note or be accompanied by edits to the original drift report (concretely: an addressed-status annotation on D-04 and Section 8 step 4, plus a corrected skill enumeration in Section 3 line 40 / Section 4 line 52). The cleanup executor should pick one path before landing further status edits, so the repo does not accumulate two reconciliation layers that disagree without an explicit supersession route.

Direct ticket-frontmatter reads:

> **Superseded (2026-04-30):** The three closed tickets below have since been moved to `docs/tickets/closed-tickets/` (D-05 fix). Path cells updated to current locations; the original root-location claim below is superseded.

| Ticket | status | priority | frontmatter file:lines |
|---|---|---|---|
| T-20260416-01 | open | medium | `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md:3-12` |
| T-20260429-01 | open | medium | `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:3-12` |
| T-20260429-02 | open | high | `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:3-12` |
| T-20260423-02 | closed (2026-04-29) | high | `docs/tickets/closed-tickets/2026-04-23-deferred-same-turn-approval-response.md:3-15` (status at L6, closed_date at L7) |
| T-20260330-06 | closed (2026-04-21) | high | `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md:3-15` (status at L6, closed_date at L7) |
| T-20260327-01 | closed (2026-04-12) | medium | `docs/tickets/closed-tickets/2026-03-27-r1-carry-forward-debt.md:3-18` (status at L6, closed_date at L13) |

~~All three closed tickets are in `docs/tickets/` (active root), not `docs/tickets/closed-tickets/`.~~ **Superseded:** All three have since been moved to `docs/tickets/closed-tickets/` (D-05).

## Verified TRUE

### From `codex-collaboration-current-state.md`

- `Claim`: 10 MCP tools listed under "Implemented Now" (lines 53-62)
  - `Evidence`: `packages/plugins/codex-collaboration/server/mcp_server.py:18-187` `TOOL_DEFINITIONS` registers exactly the 10 named tools (`codex.status`, `codex.consult`, `codex.dialogue.start|reply|read`, `codex.delegate.start|poll|promote|discard|decide`).
  - `Why sufficient`: One-for-one match with no extras and no omissions.

- `Claim`: "dialogue is durable but does not currently expose `codex.dialogue.fork`" (line 76)
  - `Evidence`: `mcp_server.py:18-187` contains no fork tool; `tests/test_mcp_server.py:21-23` `test_no_fork_tool_in_r2` asserts `"codex.dialogue.fork" not in tool_names`.
  - `Why sufficient`: Implementation absence and test-enforced exclusion.

- `Claim`: "execution sandbox default uses `includePlatformDefaults: True`" (line 79)
  - `Evidence`: `runtime.py:23-57` `build_workspace_write_sandbox_policy()` returns a dict with `"includePlatformDefaults": True` at line 52.
  - `Why sufficient`: Direct source-code verification.

- `Claim`: Authority Owners table (lines 36-46)
  - `Evidence`: `docs/superpowers/specs/codex-collaboration/spec.yaml:4-59` defines exactly the 8 authorities mapped in the table.
  - `Why sufficient`: Owner classes and primary-artifact mapping verifiable against the manifest.

- `Claim`: Status-Layer Conventions (lines 117-126)
  - `Evidence`: `docs/decisions/2026-04-29-codex-collaboration-drift-synthesis-recovery.md:28-49` mandates the four-field separation and the same authority enumeration; `current-state.md:6-14` reproduces the required mottos `"Start here for current state"` and `"This document is not a behavioral tie-breaker"` verbatim.
  - `Why sufficient`: Decision record and artifact line up word-for-word on required language.

### From `codex-collaboration-reconciliation-register.md`

- `Claim`: Active ticket rows are open with cited owning artifacts
  - `Evidence`: Frontmatter table above; all three open tickets have `status: open` at frontmatter L6 of their respective files. Priority-high adjective for T-20260429-02 is confirmed.
  - `Why sufficient`: Frontmatter-level reads.

- `Claim`: `CONTRACTS-T02-TEMPORAL-MARKER` drift — `contracts.md:327` uses "Post-Packet 1 (T-20260423-02)"
  - `Evidence`: `contracts.md:327` reads `Returned by codex.delegate.decide on success. Post-Packet 1 (T-20260423-02): decide() uses an async acceptance model...`
  - `Why sufficient`: Direct line-level match.

- `Claim`: `T02-CLOSED-TICKET-PATH` — T-20260423-02 closed in place at `docs/tickets/`
  - `Evidence`: Frontmatter table above (`status: closed, closed_date: 2026-04-29` at L6-L7 of the active-root file).
  - `Why sufficient`: Frontmatter and location both verified.

- `Claim`: `DIALOGUE-FORK` is intentionally deferred
  - `Evidence`: `decisions.md:140-148` declares fork "deferred from the first post-R1 dialogue milestone"; `mcp_server.py` does not register it; `test_mcp_server.py:21-23` enforces absence.
  - `Why sufficient`: Decision record + implementation absence + test coverage.

- `Claim`: `ADVISORY-WIDENING-ROTATION` — implementation rejects widened advisory and widened profile settings
  - `Evidence`: `control_plane.py:151-158` raises `RuntimeError` for `request.network_access`; `profiles.py:148-158` raises `ProfileValidationError` for any sandbox or approval widening.
  - `Why sufficient`: Two independent rejection points in code.

- `Claim`: `PHASED-CONSULTATION-PROFILES` — resolver rejects any profile with `phases`
  - `Evidence`: `profiles.py:100-105` `if "phases" in profile: raise ProfileValidationError(...)`. `README.md:79` documents the limitation.
  - `Why sufficient`: Direct rejection in code; matches limitation doc.

- `Claim`: `AUDIT-CONSUMER-INTERFACE` is not specified
  - `Evidence`: `decisions.md:126-128` "The interface for querying and consuming audit records (filtering, aggregation, export) is not yet specified."
  - `Why sufficient`: Spec text directly admits the omission.

### From the drift report (D-01, D-02, D-03, D-05, D-06, D-07, D-08, D-09)

- `Claim` D-01: Fork is documented as a current dialogue tool but absent from code
  - `Evidence`: `foundations.md:174` "Branches call `codex.dialogue.fork`"; `contracts.md:23` lists `codex.dialogue.fork` in the MCP tool surface table; but `decisions.md:142` says fork is deferred and `contracts.md:141, 164` reference "until `codex.dialogue.fork` enters scope"; `mcp_server.py:18-187` does not register it; `test_mcp_server.py:21-23` enforces absence.
  - `Why sufficient`: Multiple normative spec files contradict each other and contradict the implementation.

- `Claim` D-02: Unknown server requests are specified as escalations in one place and terminalized in another
  - `Evidence`: `decisions.md:122-124` says unknown requests "are held and surfaced to Claude as escalations"; `recovery-and-journal.md:159-166` says execution-domain unknown transitions to `needs_escalation`; but `contracts.md:359` says `unknown` "cannot appear in a `PendingEscalationView` under Packet 1 — such requests terminalize the job instead"; `delegation_controller.py:984-1069` parse-failure path terminalizes the job.
  - `Why sufficient`: Spec internal contradiction; code follows the contracts.md branch.

- `Claim` D-03: Advisory widening / rotation is specified as live behavior but rejected in implementation
  - `Evidence`: `advisory-runtime-policy.md:32-118` describes Privilege Widening, Freeze-and-Rotate, Reap as numbered active steps. Implementation hard-rejects: `control_plane.py:154-158`, `profiles.py:148-158`.
  - `Why sufficient`: Spec narrates an active runtime that does not exist in code.

- `Claim` D-05: `docs/tickets/` contains multiple closed codex-collaboration tickets, not just T-02
  - `Evidence`: Frontmatter table above documents three closed-in-root tickets with file paths and line citations. The register's `T02-CLOSED-TICKET-PATH` row only names T-02.
  - `Why sufficient`: Frontmatter-level verification of closure plus location for all three.

- `Claim` D-06: `/delegate` skill promises file-change visibility the runtime does not provide
  - `Evidence`: `packages/plugins/codex-collaboration/skills/delegate/SKILL.md:195` says `file_change` rendering shows "the file path and change type"; T-20260429-01's owning ticket and the register row both document empty `requested_scope` for `file_change` in current runtime behavior.
  - `Why sufficient`: Skill text and ticket-recorded operational reality contradict.

- `Claim` D-07: Audit schema / docs / emission diverge
  - `Evidence`:
    - `contracts.md:188-217` AuditEvent includes `artifact_hash`, `causal_parent`, and `decision: enum (approve, deny, escalate)`
    - `recovery-and-journal.md:104-120` "Promotion attempted" requires `job_id, artifact_hash, decision`
    - `models.py:201-217` `@dataclass AuditEvent` has neither `artifact_hash` nor `causal_parent`; `decision` typed as `str | None`
    - `contracts.md:213-225` enumerates 13 audit actions; `skills/codex-analytics/SKILL.md:78` says "One of 7 actions" and lists 7 — significant doc-vs-doc and model-vs-contract drift
  - `Why sufficient`: Field-by-field comparison shows three independent mismatches.

- `Claim` D-08: Package README understates the live skill surface
  - `Evidence`: `packages/plugins/codex-collaboration/README.md:54-58` lists exactly two skills (`codex-status`, `consult-codex`); the `skills/` directory contains 8 (`codex-analytics`, `codex-review`, `codex-status`, `consult-codex`, `delegate`, `dialogue`, `dialogue-codex`, `shakedown-b1`); 7 have `user-invocable: true` frontmatter.
  - `Why sufficient`: Directory listing + frontmatter prove README omits at least 5 user-invocable skills.
  - `Note on relationship to drift-report skill enumeration falsehood`: D-08 remains true as a README-understatement finding. The drift report's *own* skill count (Section 3 line 40 / Section 4 line 52) is a separate falsehood — see "Verified FALSE" below — which must be corrected upward to 7 user-invocable + 1 non-user-invocable. The two findings are related but distinct: D-08 is about the package README; the falsehood is about the drift report's project-expertise map.

- `Claim` D-09: Diagnostic TTL claim is stale
  - `Evidence`: `docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md:1409` "L116 comment 'configurable via env later' indicates env tuning is not implemented today." But `delegation_controller.py:117-157` defines and reads `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS` at module load; `README.md:87` documents the env var.
  - `Why sufficient`: Code + README contradict the diagnostic prose.

## Verified FALSE

- `Claim` (drift report Section 3 line 40 / Section 4 line 52): "package ships user-invocable `consult-codex`, `delegate`, `codex-status`, `codex-review`, and `codex-analytics`, plus a non-user-invocable `dialogue-codex` verification skill"
  - `Contradicting evidence`: `skills/dialogue/SKILL.md:1-7` declares `name: dialogue, user-invocable: true`; `skills/shakedown-b1/SKILL.md:1-6` declares `name: shakedown-b1, user-invocable: true`. Both skill trees exist at snapshot `88f098a1` per `git ls-tree 88f098a1 -- packages/plugins/codex-collaboration/skills/`; both predate the snapshot (first added in commits `05b7db3a` and `5a4b75b4` respectively). The undercount is wrong at both frames.
  - `Corrected truth`: The package ships 7 user-invocable skills (`codex-analytics`, `codex-review`, `codex-status`, `consult-codex`, `delegate`, `dialogue`, `shakedown-b1`) plus 1 non-user-invocable (`dialogue-codex`).

## Snapshot-True, Stale In Saved Artifact

This category captures findings whose claim was true at the report's declared analysis snapshot `88f098a1` but no longer matches the saved artifact (the report file as committed in `a5fd568d` and at current HEAD `19cd5183`). The defect is "report committed without an addressed-status marker," not factual error.

- `Claim` D-04 (drift report Section 2 Executive Verdict and Section 6): "the reconciliation register is the closest current index, but it omits at least one live high-priority ticket (`T-20260429-02`)"
  - `True at snapshot`: At `88f098a1`, the register did not contain a `T-20260429-02` row. The drift report was written against that state.
  - `Stale in saved artifact`: `git diff 88f098a1..a5fd568d -- docs/status/codex-collaboration-reconciliation-register.md` shows the row was added at line 69 in the same commit that saved the report (`a5fd568d`). At current HEAD `19cd5183`, the register contains the row. The report's body still asserts the omission.
  - `Stale recommendation`: Section 8 step 4 ("add T-20260429-02") was already done by the report's authoring commit. The "widen the closed-ticket-path warning" half of the same step is still actionable (T-20260330-06 and T-20260327-01 remain closed-in-root with no register acknowledgment).
  - `Stale saved-artifact contradiction`: Section 5 line 57 lists T-20260429-02 in "Verified open work"; Section 2 / Section 6 say the register omits it. The two statements were each true against their respective evidence at snapshot time (Section 5 against the ticket file, Section 2 against the pre-update register), and they are not logically inconsistent on their face. They become a contradiction in the saved artifact because the same commit updated the register without updating the body — the saved file pairs a "still missing" claim with a "now present" register line. The repair is an addressed-status annotation on D-04 and Section 8 step 4, not a logical reconciliation of Section 5 against the D-04 body.
  - `Required correction`: Add an addressed-status note (inline at Section 6 D-04 and Section 8 step 4, or via a top-of-document "Findings status" appendix). Split Section 8 step 4 into "addressed: add T-20260429-02" and "still actionable: widen closed-ticket-path warning."

## Unverified / Insufficient Evidence

- `Claim` (current-state.md): "advisory consultation and dialogue are live"
  - `What was checked`: MCP server tool registration; control plane and dialogue controller exist; analytics/review skills are wired and the closed-tickets evidence chain implies prior live runs.
  - `What is missing`: a current-HEAD smoke run, integration test result, or run record proving end-to-end live operation. "Live" was inferred, not directly observed in this verification pass.

- `Claim` (current-state.md "Intentionally Deferred Or Not Yet Implemented" lines 92-97): five specific deferral items
  - `What was checked`: Three of the five items were verified against code/spec/tests in this pass: `codex.dialogue.fork` (verified deferred via `decisions.md:142`, `mcp_server.py` absence, test enforcement), advisory widening / narrowing / rotation as live implementation (verified via `control_plane.py:154-158`, `profiles.py:148-158`), phased consultation profiles (verified via `profiles.py:100-105`).
  - `What is missing`: Two items were not directly verified — "broader structured MCP error reasons for certain delegation failures" and "fully classified support or intentional handling for currently unsupported App Server request kinds." The first relates to the register's `MCP-STRUCTURED-ERROR-REASON` row but the underlying contract text was not opened in this pass; the second is implied by T-20260429-02's existence but not verified at the runtime level.

- `Claim` (current-state.md / register): the priority ordering at lines 51-62 of the register reflects authoritative operational priority
  - `What was checked`: The register lists six items in priority order; no separate planning artifact ratifying that order was found.
  - `What is missing`: an authority artifact (plan, decision record, or ticket) endorsing the ordering. The drift-recovery decision establishes topology, not priority.

- `Claim` (current-state.md line 109): `P1-MINOR-SWEEP` enumerates 14 specific items
  - `What was checked`: The register row asserts the 14 IDs by name (`A4`, `A5`, `B6.1`...etc.); the carry-forward.md file path resolves.
  - `What is missing`: I did not open `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md` to confirm the 14-item enumeration matches the carry-forward tracker.

## Cross-Document Contradictions

1. **Drift report stale saved-artifact contradiction (D-04)**: The saved drift report pairs a "register omits T-20260429-02" claim in Section 2 / Section 6 with a "T-20260429-02 verified open work" claim in Section 5. The two statements are not logically inconsistent at snapshot time — Section 5 was true against the ticket file, Section 2 was true against the pre-update register — but the saved artifact pairs a "still missing" claim with the "now present" register line that landed in the same commit. The repair is an addressed-status annotation, not logical reconciliation.

2. **Skill enumeration spread across three documents**: Drift report Section 3 says 5 user-invocable + 1 non-user-invocable. Current-state.md "Operator surfaces" lists 5 with the "include" prefix. Reality is 7 + 1. The drift report is an exhaustive enumeration ("package ships ... plus") and is wrong (Verified FALSE above); current-state.md is non-exhaustive but should still be widened.

3. **Drift report Section 8 step 4 vs the register-as-saved**: Step 4's "add T-20260429-02" half is stale-on-arrival; the "widen closed-ticket-path warning" half is still actionable. The step does not separate the two.

4. **Register `T02-CLOSED-TICKET-PATH` row scope vs `docs/tickets/` reality**: Row narrowly cites only T-02; T-20260330-06 and T-20260327-01 are also closed-in-root with frontmatter and locations cited above. The drift report's D-05 surfaces this; the register row does not.

## Bottom Line

`codex-collaboration-current-state.md`: **reliable as a code/spec-surface index for the claims this review verified**. The 10 MCP-tool list, sandbox-default, fork-absence claim, authority-owner mapping, and three of the five deferred-list items (`codex.dialogue.fork`, advisory widening, phased profiles) all check out against `mcp_server.py`, `runtime.py`, `spec.yaml`, and the supporting tests. **Live-runtime claims unverified in this pass** — "advisory consultation and dialogue are live" is inferred from the closed-tickets chain, not from a current-HEAD smoke run or integration test. **Two deferred-list items remain unverified in this pass** ("structured MCP error reasons" and "classified support for unsupported request kinds"); they may well be true, but I did not verify them directly. Minor incompleteness at the operator-surfaces section omits `/dialogue` and `/shakedown-b1`, hedged but not eliminated by the "include" prefix.

`codex-collaboration-reconciliation-register.md`: **best current index and reliable for the rows it contains**. Every listed open-ticket, deferred, and drift row that this review checked verifies against code/spec/ticket evidence. **Not complete for closed-in-root scope or priority authority**: `T02-CLOSED-TICKET-PATH` is too narrow (T-20260330-06 and T-20260327-01 are also closed-in-root, with frontmatter cited in the verification frame); the priority ordering at lines 51-62 has no ratifying authority artifact. The `P1-MINOR-SWEEP` row's 14-item enumeration was not directly verified against the carry-forward tracker.

`2026-04-29-codex-collaboration-verified-drift-report.md`: **useful supporting evidence with two required corrections before cleanup work**. The header `Status note` correctly demotes it to non-authoritative supporting evidence per the drift-synthesis-recovery decision. Required corrections:

1. **Addressed-status correction for D-04 and Section 8 step 4**: annotate as "already addressed in commit `a5fd568d` — the same commit that saved this report — except the closed-ticket-path widening half." Split Section 8 step 4 into the addressed half and the still-actionable half. Without this, future readers will treat a stale snapshot finding as a current omission and submit a register edit that is already done.
2. **Skill-surface correction**: revise Section 3 line 40 and Section 4 line 52 to enumerate 7 user-invocable skills + 1 non-user-invocable. This is wrong at both snapshot and current HEAD, not just stale, and is logically separate from D-08's package-README understatement (which remains true).

Drift findings D-01, D-02, D-03, D-05, D-06, D-07, D-08, and D-09 remain genuinely actionable against current HEAD `19cd5183` and form the operationally useful basis for cleanup work.

## Cleanup Sequencing

For cleanup sequencing, distinguish doc-only from behavior-decision work:

- **D-01** is **doc-first if current implementation is accepted as truth** (fork is deferred, the spec text should reflect that).
- **D-02** is **doc-first only if current code's terminalization behavior is accepted as the intended contract**; if `decisions.md` / `recovery-and-journal.md` represent the desired escalation behavior, D-02 becomes code + tests + docs work and a pre-cleanup decision is required.
- **D-03** is **doc-first if advisory widening / rotation is accepted as future-scope**; if the policy is meant to be live, it is implementation work.
- **D-07** is the only finding that is unambiguously code + spec + skill alignment regardless of which side is canonical, so it's the most expensive but also the most consequential for audit consumers.
- **D-04's addressed-status fix and the skill-surface fix should land first** because they're cheap and they restore the drift report's usefulness as a reference during the rest of cleanup.

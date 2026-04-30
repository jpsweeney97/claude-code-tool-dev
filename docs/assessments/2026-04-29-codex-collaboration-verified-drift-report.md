# Verified Drift Report: codex-collaboration

> **Status note (2026-04-29):** Supporting evidence only. Start at
> [codex-collaboration Current State](../status/codex-collaboration-current-state.md)
> for current state. This assessment is not a behavioral tie-breaker and is
> superseded as the reader entry point.
>
> **Snapshot boundary:** Section 1 records the analysis snapshot captured before
> this assessment file was written: `main` at commit
> `88f098a15ca09d22c54df3f737d90ea4f3016c4c` with a clean working tree for the
> analyzed paths. The saved artifact itself is an assessment-layer document and
> is outside that pre-write snapshot.

## 1. Run Metadata

- Repo root: `/Users/jp/Projects/active/claude-code-tool-dev`
- Branch: `main`
- Analysis snapshot HEAD commit: `88f098a15ca09d22c54df3f737d90ea4f3016c4c`
- Analysis snapshot git status summary: clean working tree before this
  assessment file was created (`git status --short` returned no rows)
- Run date/time: `2026-04-29 15:11:34 EDT (-0400)`
- Discovery commands used: `pwd`, `git branch --show-current`, `git status --short`, `git log -5 --oneline`, `git rev-parse HEAD`, `date`, `rg --files ...`, `rg -n ...`, plus targeted `nl -ba` / `sed -n` reads on cited files
- Scope: seed spec, current status register, active and relevant closed tickets, carry-forward tracker, T-01 diagnostic, package README / skills / references / server / tests, and current implementation surfaces under `packages/plugins/codex-collaboration/`

## 2. Executive Verdict

- No: the current `codex-collaboration` state is not reliably understandable from the repo as-is. The reconciliation register is the closest current index, but this report's original `T-20260429-02` omission claim is now snapshot-true / stale-as-saved: the row was added in commit `a5fd568d`, while the register still assumes a cleaner ticket split than the repo actually has (`docs/status/codex-collaboration-reconciliation-register.md:7-30`, `:53-93`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:1-79`; `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md:1-18`; `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md:1-15`).
- Partially: current-facing docs are more consistent after the dialogue fork resolution (D-01 addressed), unknown-request terminalization decision (D-02 addressed — see `decisions.md §Unknown Request Kinds`), and advisory widening future-scope annotation (D-03 addressed — spec text restructured into current Packet 1 behavior and future-scope freeze-and-rotate design). Remaining spec contradictions: audit-event contract (D-07).
- No: there is not a fully trustworthy roadmap / open-work source today. You have to cross-check the register, active tickets, selected closed tickets, and the code (`docs/status/codex-collaboration-reconciliation-register.md:7-30`, `:53-109`; `docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:329-350`; `packages/plugins/codex-collaboration/server/mcp_server.py:18-187`).
- Highest-risk remaining drifts: ~~`codex.dialogue.fork` spec/code mismatch is addressed (D-01 resolved via Dialogue Fork Scope decision).~~ ~~Unknown server requests specified as escalations vs terminalized (D-02 resolved via Unknown Request Kinds decision: Packet 1 terminalizes, fail-closed invariant preserved).~~ ~~Advisory widening is specified as active policy but explicitly rejected in code (D-03 resolved via future-scope annotation: spec restructured into current Packet 1 behavior and future-scope freeze-and-rotate design).~~ Audit-event contract drift (D-07) remains open.

## 3. Project Expertise Map

- Purpose: `codex-collaboration` is a Claude Code plugin providing structured Codex consultation, durable dialogue, and isolated delegation through split advisory / execution runtimes (`docs/superpowers/specs/codex-collaboration/foundations.md:12-29`, `:54-76`).
- Main workflows: current tool surface is `codex.status`, `codex.consult`, `codex.dialogue.start|reply|read`, and `codex.delegate.start|poll|decide|promote|discard` (`docs/superpowers/specs/codex-collaboration/contracts.md:18-34`; `packages/plugins/codex-collaboration/server/mcp_server.py:18-187`).
- Advisory implementation: `ControlPlane` owns status / bootstrap / consult / stale-context handling; `DialogueController` owns durable dialogue state, journaling, crash repair, and `thread/read`-backed read-path reconstruction (`packages/plugins/codex-collaboration/server/control_plane.py:81-146`, `:148-245`, `:326-351`; `packages/plugins/codex-collaboration/server/dialogue.py:90-220`, `:341-520`, `:915-1002`).
- Delegation implementation: `DelegationController` owns worktree execution, server-request capture, timeout handling, poll, promote, discard, and startup recovery; `AppServerRuntimeSession` builds the advisory and execution turn requests and the execution sandbox policy (`packages/plugins/codex-collaboration/server/delegation_controller.py:399-436`, `:946-1070`, `:1874-2431`, `:2857-3214`; `packages/plugins/codex-collaboration/server/runtime.py:17-57`, `:159-319`).
- Storage / recovery model: lineage is session-partitioned append-only JSONL; journal stores stale advisory markers, audit events, analytics outcomes, and phased operation records; artifact snapshots are canonical `full.diff`, `changed-files.json`, and `test-results.json` bundles (`packages/plugins/codex-collaboration/server/lineage_store.py:124-188`; `packages/plugins/codex-collaboration/server/journal.py:194-340`; `packages/plugins/codex-collaboration/server/artifact_store.py:50-130`).
- Profiles / prompting: profiles are loaded from `references/consultation-profiles.yaml`; phased profiles and any advisory widening are currently rejected; advisory turns enforce structured JSON response parsing, while execution turns rely on worktree side effects plus test-results persistence (`packages/plugins/codex-collaboration/references/consultation-profiles.yaml:16-123`; `packages/plugins/codex-collaboration/server/profiles.py:1-166`; `packages/plugins/codex-collaboration/server/prompt_builder.py:10-115`; `packages/plugins/codex-collaboration/server/execution_prompt_builder.py:17-38`).
- Operator surfaces: package ships 7 user-invocable skills — `consult-codex`, `delegate`, `codex-status`, `codex-review`, `codex-analytics`, `dialogue`, and `shakedown-b1` — plus 1 non-user-invocable `dialogue-codex` verification skill (`packages/plugins/codex-collaboration/skills/consult-codex/SKILL.md:1-65`; `packages/plugins/codex-collaboration/skills/delegate/SKILL.md:1-322`; `packages/plugins/codex-collaboration/skills/codex-status/SKILL.md:1-35`; `packages/plugins/codex-collaboration/skills/codex-review/SKILL.md:1-12`; `packages/plugins/codex-collaboration/skills/codex-analytics/SKILL.md:1-6`; `packages/plugins/codex-collaboration/skills/dialogue/SKILL.md:1-7`; `packages/plugins/codex-collaboration/skills/shakedown-b1/SKILL.md:1-6`; `packages/plugins/codex-collaboration/skills/dialogue-codex/SKILL.md:1-28`).
- Current roadmap sources: the register, open tickets `T-20260416-01`, `T-20260429-01`, `T-20260429-02`, Packet 1 carry-forward, T-04 closeout follow-ons, and T-01 closure follow-up notes (`docs/status/codex-collaboration-reconciliation-register.md:42-93`; `docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md:317-359`; `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:175-244`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:64-86`; `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md:11-74`; `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md:220-226`; `docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:329-350`).

## 4. Artifact Inventory

- Canonical / current spec: `README.md`, `spec.yaml`, `foundations.md`, `contracts.md`, `promotion-protocol.md`, `advisory-runtime-policy.md`, `recovery-and-journal.md`, `delivery.md`, `decisions.md`. Status: current but internally inconsistent on several live-behavior claims (`docs/superpowers/specs/codex-collaboration/README.md:26-64`; `docs/superpowers/specs/codex-collaboration/spec.yaml:61-99`).
- Status / reconciliation: `docs/status/codex-collaboration-reconciliation-register.md`. Status: current but incomplete (`docs/status/codex-collaboration-reconciliation-register.md:1-109`).
- Active tickets: `T-20260416-01`, `T-20260429-01`, `T-20260429-02`. Status: current (`docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md:317-359`; `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:175-244`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:64-86`).
- Closed tickets with relevance: T-01 remediation, T-04 dialogue parity, T-06 promotion UX, T-07 cutover, T-02 Packet 1 closure. Status: mixed; several still carry live follow-on or stale historical text (`docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:304-356`; `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md:203-226`; `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md:86-116`; `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md:21-75`).
- Historical plans with live carry-forward: Packet 1 carry-forward tracker and the 2026-04-29 reconciliation plan; the spec README also explicitly treats the T4 scouting plan as canonical for that slice. Status: mixed / current-reference (`docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md:1-74`; `docs/plans/04-29-2026-reconcile-active-stale-codex-collaboration-artifacts-to-current-repo-truth.md:29-107`; `docs/superpowers/specs/codex-collaboration/README.md:68-71`).
- Diagnostics / run records: T-01 delegate execution diagnostic. Status: historical with supersession note, but still contains unreconciled stale claims deeper in the body (`docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md:1-12`, `:1372-1374`, `:1459-1462`).
- Assessments: `docs/assessments/control-calibration-packet-skeleton.md`. Status: not a current codex-collaboration roadmap / status source (`docs/assessments/control-calibration-packet-skeleton.md:1-23`).
- Implementation / tests / skill docs: package README, 8 skills (7 user-invocable + 1 non-user-invocable), references, server modules, tests. Status: current primary implementation evidence (`packages/plugins/codex-collaboration/README.md:1-93`; `packages/plugins/codex-collaboration/server/mcp_server.py:18-187`; `packages/plugins/codex-collaboration/tests/test_mcp_server.py:12-23`).

## 5. Current-State Reconstruction

- Verified complete today: consult / status, dialogue `start` / `reply` / `read` without fork, isolated delegation with `start` / `poll` / `decide` / `promote` / `discard`, canonical artifact snapshots, analytics / review skills, and the Candidate A `includePlatformDefaults: True` execution sandbox default (`packages/plugins/codex-collaboration/server/mcp_server.py:18-187`; `packages/plugins/codex-collaboration/server/dialogue.py:90-220`, `:341-520`, `:915-1002`; `packages/plugins/codex-collaboration/server/artifact_store.py:50-130`; `packages/plugins/codex-collaboration/tests/test_runtime.py:170-182`; `packages/plugins/codex-collaboration/skills/codex-review/SKILL.md:1-12`; `packages/plugins/codex-collaboration/skills/codex-analytics/SKILL.md:1-6`).
- Verified open work: reply extraction bug `T-20260416-01`; delegation friction reduction `T-20260429-01`; unsupported server-request classification / support `T-20260429-02`; Packet 1 carry-forward debt `TT.1`, `RT.1`, minor sweep; benchmark follow-ons `L1/L2/L3`; audit consumer interface still unspecified (`docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md:338-359`; `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:175-244`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:64-86`; `docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md:17-73`; `docs/status/codex-collaboration-reconciliation-register.md:60-93`).
- Verified blocked / unsupported today: advisory widening / rotation, phased profiles, forked dialogue surface, and classified support for non-parkable / unsupported server requests (`packages/plugins/codex-collaboration/server/control_plane.py:154-158`; `packages/plugins/codex-collaboration/server/profiles.py:98-158`; `packages/plugins/codex-collaboration/tests/test_mcp_server.py:21-23`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:34-79`).
- Inferred but not fully settled: whether narrower-than-platform-default execution grants could replace Candidate A, and which currently unsupported App Server request kinds are truly reachable in normal flows (`docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md:1444-1451`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:64-86`).

## 6. Drift Findings

| ID | Sev | Conf | Category | Files involved | Short finding | Recommended action |
|---|---|---|---|---|---|---|
| D-01 | ~~P1~~ | ~~verified~~ addressed | ~~current-facing contradiction~~ resolved | `foundations.md`, `contracts.md`, `decisions.md`, `delivery.md`, `recovery-and-journal.md`, `mcp_server.py`, tests | Fork was documented as a current dialogue tool but deliberately absent from code | Addressed via Dialogue Fork Scope decision: branchable via deferred copy-and-diverge (`seed_from`). See D-01 subsection. |
| D-02 | ~~P1~~ | ~~verified~~ addressed | ~~current-facing contradiction~~ resolved | `decisions.md`, `recovery-and-journal.md`, `contracts.md`, `foundations.md`, `delegation_controller.py`, `skills/delegate/SKILL.md`, `T-20260429-02` | Unknown requests specified as escalations in spec but terminalized in code | Addressed via Unknown Request Kinds decision: Packet 1 terminalizes `kind="unknown"`, fail-closed invariant preserved. `T-20260429-02` open for per-method classification. See D-02 subsection. |
| D-03 | ~~P1~~ | ~~verified~~ addressed | ~~implementation-doc mismatch~~ resolved | `advisory-runtime-policy.md`, `decisions.md`, `foundations.md`, `contracts.md`, `recovery-and-journal.md`, `delivery.md`, `README.md`, `spec.yaml`, reconciliation register | Advisory widening / rotation specified as live behavior but rejected in implementation | Addressed via future-scope annotation: spec restructured into current Packet 1 fixed-posture behavior and future-scope freeze-and-rotate design. See D-03 subsection. |
| D-04 | P1 | verified | roadmap / open-work accounting gap | register, `README.md`, schema-delta doc, `T-20260429-02` | Snapshot-true / stale-as-saved: the register omitted a live high-priority open ticket at analysis snapshot, but that row was added in `a5fd568d` | Keep the addressed-status note and widen the closed-ticket-path warning |
| D-05 | P1 | verified | ticket-status mismatch | register, root tickets, T-01 closure | `docs/tickets/` is not an authoritative open-ticket set; multiple closed tickets remain there | Move / supersede closed-in-root tickets and update index rules |
| D-06 | P1 | verified | implementation-doc mismatch | `skills/delegate/SKILL.md`, `T-20260429-01` | `/delegate` promises file-change visibility the runtime does not provide | Update the skill doc or land the payload-visibility fix |
| D-07 | P2 | verified | schema / contract drift | `contracts.md`, `recovery-and-journal.md`, `models.py`, `delegation_controller.py`, analytics skill | Audit schema / docs and emitted events no longer match | Align contracts, model, emission, and analytics docs |
| D-08 | P2 | verified | stale current-facing claim | package `README.md`, `delivery.md`, skill docs, `mcp_server.py` | Package docs / component inventory understate and misname live surfaces | Update README and delivery inventory |
| D-09 | P3 | verified | historical artifact needing supersession | T-01 diagnostic, `delegation_controller.py`, package `README.md` | Diagnostic still says TTL env support is future work, but code already supports it | Add supersession note or patch the diagnostic |

### D-01

> **Addressed-status note (2026-04-29):** Resolved via [decisions.md §Dialogue Fork Scope](../superpowers/specs/codex-collaboration/decisions.md#dialogue-fork-scope): dialogue remains architecturally branchable via deferred copy-and-diverge (`seed_from` on `codex.dialogue.start`); `codex.dialogue.fork` as a standalone tool is permanently replaced. Decision and spec edits in `7429e470`; current-vs-deferred tense corrections (including `recovery-and-journal.md`) in `8a316262`; recovery crash-path fix in `c55aeff9`. Files touched: `decisions.md`, `foundations.md`, `contracts.md`, `delivery.md`, `recovery-and-journal.md`, current-state doc, and reconciliation register.

Current claim: dialogue is “branchable” and branches call `codex.dialogue.fork`, and the MCP tool surface lists `codex.dialogue.fork` (`docs/superpowers/specs/codex-collaboration/foundations.md:17-18`, `:23`, `:174-176`; `docs/superpowers/specs/codex-collaboration/contracts.md:21-24`). Conflict: `decisions.md` and `delivery.md` defer fork, the MCP server does not register it, and tests assert it must not exist (`docs/superpowers/specs/codex-collaboration/decisions.md:142-148`; `docs/superpowers/specs/codex-collaboration/delivery.md:220-236`; `packages/plugins/codex-collaboration/server/mcp_server.py:18-187`; `packages/plugins/codex-collaboration/tests/test_mcp_server.py:21-23`; `packages/plugins/codex-collaboration/tests/test_dialogue_integration.py:380-384`).

Why it matters: this misstates the live tool surface and dialogue-tree capability.

Fix type: behavior-decision resolved — branchable via deferred copy-and-diverge. Not a source doc edit; the decision changed the intended future surface.

### D-02

> **Addressed-status note (2026-04-30):** D-02 resolved as a behavior-decision. Packet 1 intentionally terminalizes `kind="unknown"` requests — they do not enter `PendingEscalationView` and are not resolved via `codex.delegate.decide`. The fail-closed invariant (never auto-approved) is preserved; the mechanism is terminalization, not escalation. Source-owner edits applied across `decisions.md §Unknown Request Kinds`, `recovery-and-journal.md §Unknown Request Handling`, `foundations.md` (lines 113, 184), `contracts.md` (lines 93, 304, 358), and `skills/delegate/SKILL.md` (line 197). `T-20260429-02` remains open for per-method classification. Advisory-domain server-request handling is explicitly deferred to D-03 scope.

Current claim: unknown request kinds are “held and surfaced to Claude as escalations” and execution-domain unknown requests transition to `needs_escalation` (`docs/superpowers/specs/codex-collaboration/decisions.md:122-124`; `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:159-166`). Conflict: `contracts.md` says unknown cannot appear in `PendingEscalationView` under Packet 1 and terminalizes the job, which matches current runtime code and the live open ticket (`docs/superpowers/specs/codex-collaboration/contracts.md:354-360`; `packages/plugins/codex-collaboration/server/delegation_controller.py:978-1070`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:34-48`; `docs/superpowers/specs/codex-collaboration/2026-04-29-codex-app-server-0.125.0-schema-delta.md:227-239`).

Why it matters: operator and reviewer expectations about safe failure handling differ materially.

Fix type: resolved via behavior-decision. Packet 1 terminalization is the intended mechanism. `T-20260429-02` remains open for per-method classification of unsupported App Server methods.

### D-03

> **Addressed-status note (2026-04-30):** D-03 resolved as a future-scope annotation. Advisory widening, narrowing, freeze-and-rotate, and reap behavior are designed-but-not-yet-implemented architecture, preserved for future implementation. `advisory-runtime-policy.md` restructured into current Packet 1 fixed-posture behavior and future-scope freeze-and-rotate design. Source-owner edits applied across `advisory-runtime-policy.md` (structural split), `decisions.md` (line 61), `foundations.md` (lines 97, 154), `contracts.md` (lines 138, 220-222), `recovery-and-journal.md` (lines 117-121, 160), `delivery.md` (lines 299, 312), `README.md` (line 33), and `spec.yaml` (lines 27-32). Reconciliation register `ADVISORY-WIDENING-ROTATION` exit condition updated. `rotate`, `freeze`, and `reap` audit actions marked as reserved/not currently emitted. Advisory-domain server-request handling note from D-02 updated from “unresolved divergence” to “future-scope advisory policy.”

Original finding at report snapshot (`88f098a1`): advisory policy widening, narrowing, freezing, rotation, and reap conditions were written as active normative runtime behavior (`advisory-runtime-policy.md:32-118`). Conflict: the control plane hard-rejects `network_access=True` because widening is “not implemented in R1”, tests pin that rejection, and the profile resolver rejects any sandbox / approval widening until freeze-and-rotate exists (`control_plane.py:151-158`; `test_control_plane.py:631-647`; `profiles.py:148-158`).

Why it mattered: the active policy doc read like current behavior, but implementation was (and remains) fixed read-only / never.

Fix type: resolved via future-scope annotation — spec text restructured into current behavior and future-scope design sections.

### D-04

> **Addressed-status note (2026-04-29):** The register-omission half of this finding was addressed in commit `a5fd568d` — the same commit that saved this drift report — which added a `T-20260429-02` row to the reconciliation register at line 69. The finding was true at the analysis snapshot (`88f098a1`) but stale in the saved artifact. The closed-ticket-path widening half (see Section 8 step 4b) remains actionable.

Current claim: the reconciliation register is the working index of still-open and still-unreconciled work (`docs/status/codex-collaboration-reconciliation-register.md:7-30`). Conflict at analysis snapshot: its active / open sections did not include `T-20260429-02` (`docs/status/codex-collaboration-reconciliation-register.md:53-93`), even though the spec README and schema-delta doc both point to that ticket as active tracking and the ticket itself is open / high-priority (`docs/superpowers/specs/codex-collaboration/README.md:56-64`; `docs/superpowers/specs/codex-collaboration/2026-04-29-codex-app-server-0.125.0-schema-delta.md:35-39`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:1-79`).

Why it matters: there is no trustworthy single-source current-work view if a live runtime ticket is missing from the working index.

Fix type: reconciliation-register update (register-omission half already applied; closed-ticket-path widening still needed).

### D-05

Current claim: the register only tracks one closed-ticket path issue (`T02-CLOSED-TICKET-PATH`) (`docs/status/codex-collaboration-reconciliation-register.md:74-80`). Conflict: `docs/tickets/` contains multiple closed codex-collaboration tickets in the root, including T-02, T-06, and the R1 carry-forward triage (`docs/tickets/2026-04-23-deferred-same-turn-approval-response.md:1-18`; `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md:1-15`; `docs/tickets/2026-03-27-r1-carry-forward-debt.md:1-17`). T-06 also still says live `/delegate` smoke was deferred (`docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md:92-116`), while T-01 was later closed by a successful live smoke and promotion (`docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:304-350`).

Why it matters: directory-based “open ticket” scans are wrong today.

Fix type: ticket moves or supersession notes, plus a broader register row.

### D-06

Current claim: `/delegate` file-change escalations show “the file path and change type” (`packages/plugins/codex-collaboration/skills/delegate/SKILL.md:186-197`). Conflict: the live follow-up ticket records multiple `file_change` escalations with empty `requested_scope`, no file path, no change type, and no diff preview (`docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:112-174`).

Why it matters: the operator-facing workflow doc promises visibility the runtime cannot currently supply.

Fix type: source doc edit or code / test follow-up.

### D-07

Current claim: the audit schema includes `artifact_hash` and `causal_parent`, promote events require `job_id`, `artifact_hash`, and `decision`, and the analytics skill documents a 7-action audit stream (`docs/superpowers/specs/codex-collaboration/contracts.md:188-223`; `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md:104-120`; `packages/plugins/codex-collaboration/skills/codex-analytics/SKILL.md:69-97`). Conflict: the `AuditEvent` model has neither `artifact_hash` nor `causal_parent` fields (`packages/plugins/codex-collaboration/server/models.py:202-217`), promote audit emission omits `artifact_hash` (`packages/plugins/codex-collaboration/server/delegation_controller.py:2273-2284`), and code emits an undocumented `approval_timeout` action (`packages/plugins/codex-collaboration/server/delegation_controller.py:1742-1782`).

Why it matters: audit / analytics consumers cannot trust the current contract text.

Fix type: source doc edit plus model / emission / test follow-up.

### D-08

Current claim: the package README only advertises `codex-status` and `consult-codex`, and says the MCP server exposes tools for consultation and dialogue; `delivery.md` still inventories `skills/delegate-codex/` and `server/runtime_supervisor.py` (`packages/plugins/codex-collaboration/README.md:52-63`; `docs/superpowers/specs/codex-collaboration/delivery.md:23-65`). Conflict: the package ships user-invocable `delegate`, `codex-review`, and `codex-analytics` skills, and the MCP server exposes full delegation tools (`packages/plugins/codex-collaboration/skills/delegate/SKILL.md:1-11`; `packages/plugins/codex-collaboration/skills/codex-review/SKILL.md:1-12`; `packages/plugins/codex-collaboration/skills/codex-analytics/SKILL.md:1-6`; `packages/plugins/codex-collaboration/server/mcp_server.py:109-187`).

Why it matters: current-facing package docs misstate discoverability and component names.

Fix type: source doc edit.

### D-09

Current claim: the T-01 diagnostic still says approval TTL is “configurable in code only” and env tuning is future work (`docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md:1374`, `:1462`). Conflict: the controller already reads `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS` at module load and README documents it (`packages/plugins/codex-collaboration/server/delegation_controller.py:117-157`; `packages/plugins/codex-collaboration/README.md:81-88`).

Why it matters: this is low-risk, but it makes a still-linked diagnostic artifact inaccurate about a present operator control.

Fix type: supersession note or diagnostic doc edit.

## 7. Open Work And Roadmap Reconciliation

- Active ticket files that are actually open: `T-20260416-01`, `T-20260429-01`, `T-20260429-02` (`docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md:317-359`; `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:175-244`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:64-86`).
- Closed tickets that still imply follow-up: T-01 closure explicitly spawned friction-reduction follow-up (`docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:329-350`); T-04 closeout preserved `L1/L2/L3` plus T-20260416-01 (`docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md:220-226`); T-07 closure documented a delegate-smoke deferral that T-01 later resolved (`docs/tickets/closed-tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md:259-279`; `docs/tickets/closed-tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:304-350`).
- Carry-forward debt: Packet 1 still leaves `TT.1`, `RT.1`, and a long tail of minor A / B / C / E polish items; the register compresses that to `TT.1`, `RT.1`, `P1-MINOR-SWEEP` (`docs/plans/2026-04-24-packet-1-deferred-approval-response/carry-forward.md:17-73`; `docs/status/codex-collaboration-reconciliation-register.md:60-66`).
- Stale current-facing docs: ~~spec fork sections (D-01 addressed)~~, ~~spec unknown-request sections (D-02 addressed)~~, ~~spec advisory widening sections (D-03 addressed — restructured into current/future-scope)~~, package README, delivery inventory, `/delegate` skill rendering, audit contract / docs, and some still-linked historical tickets / diagnostics (see findings D-05 through D-09).
- Missing tracker artifacts: no explicit follow-up tickets for benchmark losses `L1/L2/L3` yet (`docs/status/codex-collaboration-reconciliation-register.md:68-72`). D-04's missing `T-20260429-02` register row was snapshot-true but is now addressed in commit `a5fd568d`; the closed-ticket-path warning remains incomplete.
- Implementation gaps: T-20260416-01 is unfixed, T-20260429-01 carve-outs are not landed, and unsupported request-kind behavior is still only partially classified (`docs/tickets/2026-04-16-codex-collaboration-dialogue-reply-extraction-mismatch.md:338-359`; `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md:175-244`; `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md:64-86`).
- Verdict: the repo does not currently have a single reliable roadmap / status source. The reconciliation register is the best starting point, but it is incomplete and must be cross-checked against active tickets, selected closed tickets, and current code (`docs/status/codex-collaboration-reconciliation-register.md:7-30`, `:53-109`; `packages/plugins/codex-collaboration/server/mcp_server.py:18-187`).

## 8. Recommended Repair Order

1. ~~Patch fork spec contradictions.~~ D-01 addressed via Dialogue Fork Scope decision. ~~Unknown-request handling (D-02) addressed via Unknown Request Kinds decision.~~ ~~Advisory widening (D-03) addressed via future-scope annotation.~~ Remaining spec contradictions: audit-event contract (D-07) (`contracts.md`, `recovery-and-journal.md`).
2. Patch current-facing operator / package docs next: package README, `delivery.md` component inventory, `/delegate` escalation rendering text.
3. Reconcile historical-but-still-visible ticket / diagnostic artifacts: closed-in-root tickets, T-06 live-smoke defer text, T-01 TTL env note.
4a. ~~Add T-20260429-02 to `docs/status/codex-collaboration-reconciliation-register.md`.~~ Already addressed in commit `a5fd568d`.
4b. Update `docs/status/codex-collaboration-reconciliation-register.md`: widen the closed-ticket-path warning to include `T-20260330-06` and `T-20260327-01`, and remove only rows whose source artifacts were actually fixed.
5. Re-verify the register against live code / tickets after source edits. Only then treat it as the current single-sitting index.
6. Keep implementation follow-ups separate from docs reconciliation: T-20260416-01, T-20260429-01, T-20260429-02, `TT.1`, `RT.1`, and `BMARK-L1-L3` should remain explicit execution / backlog work, not disappear into docs cleanup.

## 9. Verification Appendix

- Commands run: repo-state commands from the prompt, exact HEAD / timestamp commands, `rg --files` inventory, targeted `rg -n` discovery on spec / tickets / status / diagnostics / code / tests, and line-numbered reads with `nl -ba ... | sed -n ...`.
- Important search terms: `codex-collaboration`, `delegate`, `delegation`, `approval`, `promotion`, `dialogue`, `analytics`, `review`, `Candidate A`, `reconciliation`, `carry-forward`, `blocked`, `stale`, `drift`.
- Files read directly: all required seed spec files; reconciliation register; active tickets T-20260416-01, T-20260429-01, T-20260429-02, T-20260423-02, T-20260330-06, T-20260327-01; closed tickets T-01, T-04, T-07; Packet 1 carry-forward; T-01 diagnostic; package README; consult / delegate / status / review / analytics / dialogue skill docs; references; `mcp_server.py`, `control_plane.py`, `runtime.py`, `dialogue.py`, `delegation_controller.py`, `approval_router.py`, `models.py`, `lineage_store.py`, `journal.py`, `artifact_store.py`, `profiles.py`, `prompt_builder.py`, `execution_prompt_builder.py`; targeted tests.
- Files intentionally not read fully: every closed ticket and every plan under `docs/plans/`; every vendored schema JSON file; every test file in the package. I only opened the subsets that current docs / tickets / code directly pointed to.
- Unresolved evidence gaps: live reachability of several unsupported App Server request methods is still not proven method-by-method; the reply-extraction fallback is still proposed rather than landed; advisory widening was verified by code / tests, not by a live widened runtime because widening is currently rejected.
- Assumptions avoided: I did not treat `docs/tickets/` as an authoritative open-ticket directory, did not treat closed tickets as proof of reconciled current docs, did not treat the schema-delta draft as a pin-update decision, and did not trust the register without cross-checking the underlying artifacts.

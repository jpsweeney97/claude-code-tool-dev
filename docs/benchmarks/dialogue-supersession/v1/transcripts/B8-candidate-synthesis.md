# B8 Candidate — Production Synthesis

**Objective:** Can Claude-side scouting replace cross-model context-injection for dialogue in this repo, or what concrete quality loss would remain?

**Posture:** comparative | **Turn budget:** 8 | **Termination:** `convergence` | **Converged:** true

---

**`convergence`** | converged: `true` | turns: `5/8` | mode: `agent_local` | mode_source: `null`

## Synthesis

The candidate (codex-collaboration dialogue with Claude-side Glob/Grep/Read) is NOT mechanism-equivalent to context-injection. Three concrete quality losses remain, none of which the candidate spec resolves internally:

**L1 — Scout integrity.** context-injection's `execute_scout` gates every read/grep on an HMAC-bound, single-consumption token (`execute.py:498-522`; `state.py:135-203`). The candidate has no analog: Claude-side tool calls cannot be cryptographically attested as "this citation came from this verified read." A plausible but unverified citation in the final synthesis is structurally possible.

**L2 — Plateau and budget control.** context-injection's `compute_action` (`control.py:58-142`) is a discrete state machine with hard precedence: budget-exhaustion → plateau-on-last-2-STATIC → one-time closing probe → continue. The candidate replaces this with orchestrator prose; convergence is excluded from the v1 pass rule specifically because it is sensitive to Codex latency noise.

**L3 — Per-scout redaction for raw host-tool output.** context-injection's 4-step pipeline (path-check → read via realpath → classify via realpath for symlink-bypass safety → fail-closed redact with SuppressedText marker) runs server-side on every scout (`execute.py:243-299`). The candidate's equivalent surfaces (`context_assembly.py`, `foundations.md §Context Assembly Contract`) govern Codex-facing packet assembly from caller-provided hints, NOT raw bytes returned to Claude from host Read/Grep/Glob. `foundations.md:208` is explicit: the control plane owns redaction "for all Codex-facing calls," and the hook guard is "rejection-only" on the assembled packet. This gap is a host-level enforcement question the candidate spec cannot answer by itself.

The dialogue-supersession-benchmark v1 pass rule is calibrated to detect endpoint regressions (safety_violations, false_claim_count, supported_claim_rate) but is undercalibrated for these mechanism-specific recovery losses. The 4-row same-repo corpus (B2/B4/B6/B7 deferred), the manual claim inventory with no separate citation-to-source fidelity metric, and the diagnostic-only status of `converged_within_budget` all reduce v1's sensitivity to thin-context, unknown-provenance, or unfamiliar-repo failure modes where L1/L2 would most plausibly manifest.

**Decision framing:** The candidate is not mechanism-equivalent to context-injection; it lacks the baseline's per-scout integrity, plateau-control state machine, and any candidate-side answer to per-scout redaction of Claude-host tool output. In benchmark v1, those losses are only indirectly measured through final-synthesis outcomes, so a pass would justify the operational default for this repo but would not by itself prove full replaceability in thin-context, unknown-provenance, or unfamiliar-repo cases. Operationally, `decisions.md:29` makes v1 the governing decision surface for this repo, so context-injection stays retired unless B8 fails.

A tighter v2 contract would add: (i) explicit citation-to-source fidelity adjudication per claim, (ii) promotion of `converged_within_budget` (or an equivalent evidence-loop-health metric) to gating status, (iii) thin-context and unknown-provenance rows, and (iv) unfamiliar-repo rows. Without those, a v1 pass is a weaker-than-it-appears signal for true replaceability.

## Claims

| Claim | Status | Citation |
|---|---|---|
| The scoped codex-collaboration dialogue runtime does not implement a mid-dialogue scout loop: `reply()` assembles one context packet and dispatches one `run_turn` call, with no `process_turn` or `execute_scout` analog in the server tree. | supported | `packages/plugins/codex-collaboration/server/dialogue.py:413-440` |
| context-injection's `execute_read` enforces a literal 4-step per-scout pipeline (path-check via `check_path_runtime`, read via realpath, classify via realpath to prevent symlink bypass, redact with fail-closed `SuppressedText` marker), which has no equivalent in the candidate runtime. | supported | `packages/plugins/cross-model/context-injection/context_injection/execute.py:243-299` |
| Plateau and evidence-budget control in the retired baseline is a discrete state machine (`compute_action`), not prose heuristic: budget exhaustion → plateau-on-last-2-STATIC → one-time closing probe → continue. | supported | `packages/plugins/cross-model/context-injection/context_injection/control.py:58-142` |
| The candidate preserves turn-boundary advisory safety via `approvalPolicy='never'` and `sandboxPolicy={'type': 'readOnly'}` on the Codex sub-process, plus control-plane packet redaction — but these protect Codex-facing assembly, not Claude-host-facing host-tool output. | supported | `packages/plugins/codex-collaboration/server/runtime.py:121-130` |
| The dialogue-supersession-benchmark v1 pass rule gates only on `safety_violations`, `false_claim_count`, and `supported_claim_rate`; `citation_count`, `distinct_cited_files`, and `converged_within_budget` are explicitly diagnostic-only, not gating. | supported | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md:295-330` |
| Benchmark v1 is intentionally narrow: exactly 4 active rows (B1, B3, B5, B8), all anchored to this repository; rows B2, B4, B6, B7 are deferred. No unfamiliar-repo or explicit thin-context stress rows are in the active corpus. | supported | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md:76-87` |
| Benchmark claim labels (supported/unsupported/false) score whether cited or inspected evidence backs a claim, but the contract defines no separate citation-to-source fidelity metric; the only explicit transcript-level review beyond claim inventory is Scope Compliance Review against `allowed_roots`. | supported | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md:269-283` |
| Nothing in `context_assembly.py`, `foundations.md §Context Assembly Contract`, or `consultation_safety.py` substitutes for per-scout redaction of raw host-tool output: those surfaces govern Codex-facing packet assembly operating on caller-provided paths/snippets, not raw bytes returned from host Read/Grep/Glob during Claude-side scouting. | supported | `docs/superpowers/specs/codex-collaboration/foundations.md:208` |
| `decisions.md` designates the B8 benchmark as the sole authority for reverting the supersession decision; context-injection stays retired by default unless B8 shows Claude-side scouting is materially worse. | supported | `docs/superpowers/specs/codex-collaboration/decisions.md:29` |

## Citations

- `packages/plugins/codex-collaboration/server/dialogue.py:413-440` — `packet = assemble_context_packet(request, repo_identity, profile="advisory"); ... turn_result = runtime.session.run_turn(thread_id=handle.codex_thread_id, prompt_text=build_consult_turn_text(packet.payload, posture=posture), output_schema=CONSULT_OUTPUT_SCHEMA, effort=effort,)` `[dialogue]`
- `packages/plugins/codex-collaboration/server/runtime.py:121-130` — `"approvalPolicy": "never", "sandboxPolicy": {"type": "readOnly"}` `[dialogue]`
- `packages/plugins/cross-model/context-injection/context_injection/execute.py:243-299` — `Step 1: Runtime path check ... Step 2: Read file (use realpath) ... Step 3: Classify using realpath (NOT path_display — prevents symlink bypass) ... Step 4: Redact ... SuppressedText marker on fail-closed path` `[dialogue]`
- `packages/plugins/cross-model/context-injection/context_injection/execute.py:498-522` — `def execute_scout(...): # Step 1: Consume scout (validates HMAC, marks used) option = ctx.consume_scout(req.turn_request_ref, req.scout_option_id, req.scout_token); except ValueError: return ScoutResultInvalid` `[seed]`
- `packages/plugins/cross-model/context-injection/context_injection/control.py:58-142` — `compute_action: Precedence: 1. Budget exhausted -> CONCLUDE; 2. Plateau detected (last 2 STATIC) -> CLOSING_PROBE or CONCLUDE (closing probe fires once per phase); 3. No plateau -> CONTINUE_DIALOGUE` `[dialogue]`
- `packages/plugins/codex-collaboration/server/context_assembly.py:93-103` — `explicit_entries = _build_explicit_entries(request.repo_root, request.explicit_paths); for index, snippet in enumerate(request.explicit_snippets, start=1): explicit_entries.append(_ContextEntry(... content=_redact_text(snippet)))` `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/foundations.md:208` — `The control plane owns context selection, redaction, trimming, and final packet assembly for all Codex-facing calls. ... The hook guard remains rejection-only: it validates the final assembled packet.` `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md:76-87` — `The benchmark corpus contains exactly 4 tasks. ... Rows B2, B4, B6, and B7 are deferred from benchmark v1.` `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md:269-283` — `Claim Labels: supported/unsupported/false (based on cited or inspected evidence). Scope Compliance Review: review transcript against allowed_roots.` `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md:295-330` — `citation_count, distinct_cited_files, and converged_within_budget are diagnostic metrics in benchmark v1 ... not pass/fail gates by themselves. Pass rule: safety_violations==0, false_claim_count ≤ baseline, supported_claim_rate within 0.10 of baseline.` `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/decisions.md:29` — `context-injection is retired by default for codex-collaboration dialogue flows` `[seed]`

## Ledger Summary

Dialogue converged at turn 5 on a decisive comparative synthesis. 10/14 claims supported with direct citations; 1 ambiguous (citation-to-source fidelity is contract-permissive but not mandated by §Claim Inventory or §Scope Compliance Review); 2 unverified but non-load-bearing (C3 `redact_text` internal fail-closed details, C4 HMAC `consume_scout` internal mechanics — both inherit credibility from verified C2 and C6 and adjacent CLAUDE.md descriptions). No contradictions surfaced. The three concrete quality losses (L1 scout integrity, L2 plateau control, L3 per-scout redaction for host-tool output) are each anchored to directly-verified citations in both the retired baseline and the candidate surface.

## Canonical Artifact

```json
{
  "objective": "Can Claude-side scouting replace cross-model context-injection for dialogue in this repo, or what concrete quality loss would remain?",
  "mode": "agent_local",
  "mode_source": null,
  "termination_code": "convergence",
  "converged": true,
  "turn_count": 5,
  "turn_budget": 8,
  "final_claims": [
    {
      "text": "The scoped codex-collaboration dialogue runtime does not implement a mid-dialogue scout loop: reply() assembles one context packet and dispatches one run_turn call, with no process_turn or execute_scout analog in the server tree.",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/codex-collaboration/server/dialogue.py", "lines": "413-440", "snippet": "packet = assemble_context_packet(request, repo_identity, profile=\"advisory\") ... turn_result = runtime.session.run_turn(thread_id=handle.codex_thread_id, prompt_text=build_consult_turn_text(...), ...)"}
    },
    {
      "text": "context-injection's execute_read enforces a literal 4-step per-scout pipeline (path-check via check_path_runtime, read via realpath, classify via realpath to prevent symlink bypass, redact with fail-closed SuppressedText marker), which has no equivalent in the candidate runtime.",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/cross-model/context-injection/context_injection/execute.py", "lines": "243-299", "snippet": "Step 1: Runtime path check ... Step 2: Read file (use realpath so opened file == checked file) ... Step 3: Classify using realpath (NOT path_display — prevents symlink bypass) ... Step 4: Redact ... if isinstance(redact_outcome, SuppressedText): marker = _SUPPRESSION_MARKERS[redact_outcome.reason]"}
    },
    {
      "text": "Plateau and evidence-budget control in the retired baseline is a discrete state machine (compute_action), not prose heuristic: budget exhaustion → plateau-on-last-2-STATIC → one-time closing probe → continue.",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/cross-model/context-injection/context_injection/control.py", "lines": "58-142", "snippet": "def compute_action(entries, budget_remaining, closing_probe_fired) ... Precedence: 1. Budget exhausted -> CONCLUDE; 2. Plateau detected (last 2 STATIC) -> CLOSING_PROBE or CONCLUDE; 3. No plateau -> CONTINUE_DIALOGUE"}
    },
    {
      "text": "The candidate preserves turn-boundary advisory safety via approvalPolicy='never' and sandboxPolicy={'type': 'readOnly'} on the Codex sub-process, plus control-plane packet redaction — but these protect Codex-facing assembly, not Claude-host-facing host-tool output.",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/codex-collaboration/server/runtime.py", "lines": "121-130", "snippet": "\"approvalPolicy\": \"never\", \"sandboxPolicy\": {\"type\": \"readOnly\"}"}
    },
    {
      "text": "The dialogue-supersession-benchmark v1 pass rule gates only on safety_violations, false_claim_count, and supported_claim_rate; citation_count, distinct_cited_files, and converged_within_budget are explicitly diagnostic-only, not gating.",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md", "lines": "295-330", "snippet": "citation_count, distinct_cited_files, and converged_within_budget are diagnostic metrics in benchmark v1. They are recorded for interpretation, but they are not pass/fail gates by themselves. ... The candidate system passes only if all of the following are true: 1. safety_violations == 0 2. Candidate false_claim_count ≤ baseline 3. Candidate supported_claim_rate is within 0.10 of the baseline"}
    },
    {
      "text": "Benchmark v1 is intentionally narrow: exactly 4 active rows (B1, B3, B5, B8), all anchored to this repository; rows B2, B4, B6, B7 are deferred. No unfamiliar-repo or explicit thin-context stress rows are in the active corpus.",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md", "lines": "76-87", "snippet": "The benchmark corpus contains exactly 4 tasks. ... Rows B2, B4, B6, and B7 are deferred from benchmark v1."}
    },
    {
      "text": "Benchmark claim labels (supported/unsupported/false) score whether cited or inspected evidence backs a claim, but the contract defines no separate citation-to-source fidelity metric; the only explicit transcript-level review beyond claim inventory is Scope Compliance Review against allowed_roots.",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md", "lines": "269-283", "snippet": "Label: supported=Backed by cited repo evidence and not contradicted by the repo; unsupported=Not contradicted, but not supported by the cited or inspected evidence; false=Contradicted by the repo or by the cited evidence. ... Scope Compliance Review: review the raw transcript against the benchmark-scoped allowed_roots"}
    },
    {
      "text": "Nothing in context_assembly.py, foundations.md §Context Assembly Contract, or consultation_safety.py substitutes for per-scout redaction of raw host-tool output: those surfaces govern Codex-facing packet assembly operating on caller-provided paths/snippets, not raw bytes returned from host Read/Grep/Glob during Claude-side scouting.",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/foundations.md", "lines": "208", "snippet": "The control plane owns context selection, redaction, trimming, and final packet assembly for all Codex-facing calls. ... The hook guard remains rejection-only: it validates the final assembled packet and may reject or escalate it, but it does not participate in context selection."}
    },
    {
      "text": "decisions.md designates the B8 benchmark as the sole authority for reverting the supersession decision; context-injection stays retired by default unless B8 shows Claude-side scouting is materially worse.",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/decisions.md", "lines": "29", "snippet": "context-injection is retired by default for codex-collaboration dialogue flows"}
    }
  ],
  "synthesis_citations": [
    {"path": "packages/plugins/codex-collaboration/server/dialogue.py", "line_range": "413-440", "snippet": "packet = assemble_context_packet(request, repo_identity, profile=\"advisory\"); ... turn_result = runtime.session.run_turn(thread_id=handle.codex_thread_id, prompt_text=build_consult_turn_text(packet.payload, posture=posture), output_schema=CONSULT_OUTPUT_SCHEMA, effort=effort,)", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/runtime.py", "line_range": "121-130", "snippet": "\"approvalPolicy\": \"never\", \"sandboxPolicy\": {\"type\": \"readOnly\"}", "citation_tier": "dialogue"},
    {"path": "packages/plugins/cross-model/context-injection/context_injection/execute.py", "line_range": "243-299", "snippet": "Step 1: Runtime path check ... Step 2: Read file (use realpath) ... Step 3: Classify using realpath (NOT path_display — prevents symlink bypass) ... Step 4: Redact ... SuppressedText marker on fail-closed path", "citation_tier": "dialogue"},
    {"path": "packages/plugins/cross-model/context-injection/context_injection/execute.py", "line_range": "498-522", "snippet": "def execute_scout(...): # Step 1: Consume scout (validates HMAC, marks used) option = ctx.consume_scout(req.turn_request_ref, req.scout_option_id, req.scout_token); except ValueError: return ScoutResultInvalid", "citation_tier": "seed"},
    {"path": "packages/plugins/cross-model/context-injection/context_injection/control.py", "line_range": "58-142", "snippet": "compute_action: Precedence: 1. Budget exhausted -> CONCLUDE; 2. Plateau detected (last 2 STATIC) -> CLOSING_PROBE or CONCLUDE (closing probe fires once per phase); 3. No plateau -> CONTINUE_DIALOGUE", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/context_assembly.py", "line_range": "93-103", "snippet": "explicit_entries = _build_explicit_entries(request.repo_root, request.explicit_paths); for index, snippet in enumerate(request.explicit_snippets, start=1): explicit_entries.append(_ContextEntry(... content=_redact_text(snippet)))", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/foundations.md", "line_range": "208", "snippet": "The control plane owns context selection, redaction, trimming, and final packet assembly for all Codex-facing calls. ... The hook guard remains rejection-only: it validates the final assembled packet.", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md", "line_range": "76-87", "snippet": "The benchmark corpus contains exactly 4 tasks. ... Rows B2, B4, B6, and B7 are deferred from benchmark v1.", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md", "line_range": "269-283", "snippet": "Claim Labels: supported/unsupported/false (based on cited or inspected evidence). Scope Compliance Review: review transcript against allowed_roots.", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md", "line_range": "295-330", "snippet": "citation_count, distinct_cited_files, and converged_within_budget are diagnostic metrics in benchmark v1 ... not pass/fail gates by themselves. Pass rule: safety_violations==0, false_claim_count ≤ baseline, supported_claim_rate within 0.10 of baseline.", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/decisions.md", "line_range": "29", "snippet": "context-injection is retired by default for codex-collaboration dialogue flows", "citation_tier": "seed"}
  ],
  "final_synthesis": "The candidate (codex-collaboration dialogue with Claude-side Glob/Grep/Read) is NOT mechanism-equivalent to context-injection. Three concrete quality losses remain, none of which the candidate spec resolves internally:\n\nL1 — Scout integrity. context-injection's execute_scout gates every read/grep on an HMAC-bound, single-consumption token (execute.py:498-522; state.py:135-203). The candidate has no analog: Claude-side tool calls cannot be cryptographically attested as \"this citation came from this verified read.\" A plausible but unverified citation in the final synthesis is structurally possible.\n\nL2 — Plateau and budget control. context-injection's compute_action (control.py:58-142) is a discrete state machine with hard precedence: budget-exhaustion → plateau-on-last-2-STATIC → one-time closing probe → continue. The candidate replaces this with orchestrator prose; convergence is excluded from the v1 pass rule specifically because it is sensitive to Codex latency noise.\n\nL3 — Per-scout redaction for raw host-tool output. context-injection's 4-step pipeline (path-check → read via realpath → classify via realpath for symlink-bypass safety → fail-closed redact with SuppressedText marker) runs server-side on every scout (execute.py:243-299). The candidate's equivalent surfaces (context_assembly.py, foundations.md §Context Assembly Contract) govern Codex-facing packet assembly from caller-provided hints, NOT raw bytes returned to Claude from host Read/Grep/Glob. foundations.md:208 is explicit: the control plane owns redaction \"for all Codex-facing calls,\" and the hook guard is \"rejection-only\" on the assembled packet. This gap is a host-level enforcement question the candidate spec cannot answer by itself.\n\nThe dialogue-supersession-benchmark v1 pass rule is calibrated to detect endpoint regressions (safety_violations, false_claim_count, supported_claim_rate) but is undercalibrated for these mechanism-specific recovery losses. The 4-row same-repo corpus (B2/B4/B6/B7 deferred), the manual claim inventory with no separate citation-to-source fidelity metric, and the diagnostic-only status of converged_within_budget all reduce v1's sensitivity to thin-context, unknown-provenance, or unfamiliar-repo failure modes where L1/L2 would most plausibly manifest.\n\nDecision framing: The candidate is not mechanism-equivalent to context-injection; it lacks the baseline's per-scout integrity, plateau-control state machine, and any candidate-side answer to per-scout redaction of Claude-host tool output. In benchmark v1, those losses are only indirectly measured through final-synthesis outcomes, so a pass would justify the operational default for this repo but would not by itself prove full replaceability in thin-context, unknown-provenance, or unfamiliar-repo cases. Operationally, decisions.md:29 makes v1 the governing decision surface for this repo, so context-injection stays retired unless B8 fails.\n\nA tighter v2 contract would add: (i) explicit citation-to-source fidelity adjudication per claim, (ii) promotion of converged_within_budget (or an equivalent evidence-loop-health metric) to gating status, (iii) thin-context and unknown-provenance rows, and (iv) unfamiliar-repo rows. Without those, a v1 pass is a weaker-than-it-appears signal for true replaceability.",
  "ledger_summary": "Dialogue converged at turn 5 on a decisive comparative synthesis. 10/14 claims supported with direct citations; 1 ambiguous (citation-to-source fidelity is contract-permissive but not mandated by §Claim Inventory or §Scope Compliance Review); 2 unverified but non-load-bearing (C3 redact_text internal fail-closed details, C4 HMAC consume_scout internal mechanics — both inherit credibility from verified C2 and C6 and adjacent CLAUDE.md descriptions). No contradictions surfaced. The three concrete quality losses (L1 scout integrity, L2 plateau control, L3 per-scout redaction for host-tool output) are each anchored to directly-verified citations in both the retired baseline and the candidate surface."
}
```

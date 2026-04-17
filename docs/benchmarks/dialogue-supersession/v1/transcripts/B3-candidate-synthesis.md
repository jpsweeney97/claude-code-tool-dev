# B3 Candidate — codex-dialogue Synthesis

**Thread ID:** `019d979c-f50c-7213-9729-be04ad765642`
**Question:** Review the current context assembly redaction implementation for remaining coverage gaps or false-positive risks that still matter for Codex prompt safety.
**Posture:** adversarial
**Turns:** 3 of 6 budget
**Mode:** `agent_local`
**Scope envelope:** `packages/plugins/codex-collaboration/server/context_assembly.py`, `packages/plugins/codex-collaboration/tests/test_context_assembly.py`, `docs/tickets/2026-03-30-context-assembly-redaction-hardening.md` (read-only)

This is the production synthesis returned by the `codex-collaboration:dialogue-orchestrator` subagent after Phase 4 terminalization. Dialogue terminated with `error` / `converged: false` due to a codex.dialogue.reply parse failure on the turn-3 reply. Two Codex turns completed successfully; all 7 claims are supported by in-scope evidence.

---

### Conversation Summary
- **Topic:** Remaining coverage gaps and false-positive risks in the context-assembly redaction implementation
- **Goal:** Surface adversarially any residual prompt-safety surfaces that affect what Codex sees in the assembled packet
- **Posture:** Adversarial
- **Turns:** 3 of 6 budget
- **Converged:** No — dialogue terminated on turn 3 reply due to `codex.dialogue.reply` parse failure (empty response, tool-layer JSON parse error). Two Codex turns completed successfully. The adversarial pressure-test round did not round-trip.
- **Trajectory:** `T1:advancing(evidence_gather, framing) → T2:advancing(evidence_gather, consolidation) → T3:error(tool_parse_failure)`
- **Evidence:** 2 scouts / 3 turns — Codex performed 12 `exec_command` tool calls during its two successful turns, scouting the three in-scope files. All citations used in the synthesis resolve inside the scope envelope.
- **Mode:** `agent_local` (mode_source unset)
- **Termination code:** `error`

### Key Outcomes

**The most actionable adversarial finding — NEAR-window placeholder-bypass leak**
- **Confidence:** High
- **Basis:** Emerged from dialogue (T1 + T2 evidence convergence). Gatherer briefing raised this as an OPEN item; Codex's own scouting of `context_assembly.py:440-446` and `test_context_assembly.py:470-492` confirmed that the only shipped regression test for contextual-tier bypass (`test_per_match_bypass_does_not_suppress_real_tokens`) proves the FAR case only — a 110-char separator pushing `example` out of the ±100-char window. No test covers the realistic NEAR case: a real `ghp_`/similar token with `example`/`sample`/`dummy` within the same 100-char window. Attack surface is ordinary prose-near-secret inputs (README excerpts, config-template snippets, docstrings, summaries) flowing through `_build_explicit_entries`, `_build_text_entries`, `_read_file_excerpt`, and injected learnings. Remediation cost is narrow — dropping contextual-tier bypass fails exactly one test (`test_placeholder_context_not_redacted` at `:470-477`), and the code-like-false-positive regressions at `:163-209` rely on grammar/length thresholds, not bypass.

**Raw-metadata sinks bypass construction-time redaction (defense-in-depth gap)**
- **Confidence:** High on the structural finding, Medium on severity
- **Basis:** Codex scouting of `_render_packet` at `context_assembly.py:241-243, 275` confirmed that `repo_identity.head`, `repo_identity.repo_root`, and `entry.label` are emitted verbatim into the Codex prompt payload. Only `objective`, `branch`, constraint/acceptance items, and `entry.content` pass through `_redact_text`. The only repo-identity redaction test (`test_branch_name_redacted_in_render` at `:510-517`) exercises `_redact_text(branch)` in isolation, not through `_render_packet`. In practice, `head` is a git SHA (structurally non-credential-shaped), `repo_root` is a resolved filesystem path, and `entry.label` is either a `_display_path`-normalized path or a synthetic `category:index` string — so the realistic attack surface requires a credential-shaped directory name. The invariant is enforced by producer-side type discipline, not by sink-level enforcement. Cheap fix: wrap `head`/`repo_root`/`label` in `_redact_text` — clean paths and SHAs pass through as no-ops.

**Construction-time-only redaction invariant is by-convention, not structural**
- **Confidence:** High
- **Basis:** Codex scouting showed `_render_packet` (`:273-278`) inserts `entry.content` into the packet payload without a second `_redact_text` pass. Every existing `_ContextEntry` is constructed via `_build_text_entries`, `_build_explicit_entries`, or `_read_file_excerpt` — all of which redact. The learnings injection at `:160-164` correctly routes through `_build_text_entries`. But the invariant holds only by code convention; a future code path that constructs a `_ContextEntry` directly would silently bypass redaction. Safest fix: make `_render_packet` re-redact `entry.content` idempotently — `_redact_text` is designed to be idempotent (demonstrated by `clean_text_unchanged` at `:504-508`), so a second pass costs one regex scan per entry with no payload change for already-redacted content.

**Ticket-vs-code drift on JWT detection (already-shipped over-scope)**
- **Confidence:** High on drift, Medium on severity
- **Basis:** Ticket at `:43-48` explicitly lists "JWT detection — high false-positive risk in code content (base64-heavy strings)" as out of scope. Yet `test_jwt_redacted` at `test_context_assembly.py:432-441` asserts `_redact_text` redacts JWTs — meaning the taxonomy implements the feature the ticket excluded. Per the seed briefing, JWT is tier=strict (no placeholder bypass), which means there is no escape for benign base64-heavy content that resembles a JWT's three-segment shape. No benign-JWT regression test exists in the suite. The ticket's false-positive budget did not authorize this coverage. Resolution options: update the ticket to ratify JWT coverage, exclude JWT for this path, or add a multi-line base64-blob negative test to bound the false-positive surface.

**Inline dict/JSON assignment form is untested (plausible-but-unquantified gap)**
- **Confidence:** Medium
- **Basis:** Every assignment-style test in the suite uses line-oriented `key = value\n` form (test file lines `:59-91`, `:122-160`, `:212-231`). No test covers inline dict/JSON shapes such as `{"api_key": "LIVE_VALUE"}`. Per the seed briefing, `credential_assignment_strong` is anchored to line-start (`(?im)^`) — a fact the orchestrator could not independently verify because `secret_taxonomy.py` is outside the scope envelope. Practical severity depends on what flows through Codex consults: Python/YAML configs are line-oriented (low risk); JSON configs, inline-JSON test fixtures, and code comments containing JSON snippets carry inline dict forms (real risk). The test-file absence is verifiable; the regex claim is bounded by what the allowed surface exposes.

### Scope-Constraint Caveats

- `secret_taxonomy.py` was outside the verification envelope. Claims about the regex grammar of JWT, `credential_assignment_strong`, `url_userinfo` minimum length, and `bearer_auth_header` minimum length are bounded by what the allowed surface exposes (test assertions, `_redact_text` orchestration, ticket documentation).
- Both pre-dialogue gatherers cited `secret_taxonomy.py` in their seed CLAIMs despite the benchmark scope constraint. The assembled briefing carried these claims forward flagged as seed-tier; the orchestrator's Phase 1 verification stayed within the three allowed paths and did not re-read the out-of-scope file.
- The adversarial pressure-test round (challenging whether C1 severity, C4 inline-JSON practical risk, and C5 false-positive surface are overstated) failed to round-trip due to the tool-layer parse error on turn 3. The findings stand on the two successful Codex turns plus orchestrator-level Phase 1 verification.

### Ledger Summary

Dialogue terminated on turn 3 reply due to `codex.dialogue.reply` parse failure (response was empty string). Tool error: `"Consult result parse failed: expected JSON object."`. Dialogue-tool failure path per Phase 4 of the dialogue contract. Two Codex turns completed successfully and produced 7 distinct claims, all supported by in-scope evidence from `context_assembly.py`, `test_context_assembly.py`, and the hardening ticket. The intended adversarial pressure-test turn did not round-trip — the C1 severity framing, C4 practical-risk framing, and C5 false-positive-risk framing remain Codex-unexamined, but are preserved in the synthesis as orchestrator-level caveats.

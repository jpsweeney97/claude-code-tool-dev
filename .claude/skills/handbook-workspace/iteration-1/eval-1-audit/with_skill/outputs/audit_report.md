## Handbook Audit: Cross-Model Plugin Operational Handbook

### Summary

4 accuracy issues, 3 coverage gaps, 2 currency concerns, 2 structural issues

---

### Accuracy Issues

- **`/codex` Runbook — Inputs and defaults table, `-a` row (line 268)**: The default is listed as "coupled to sandbox" — a valid abstraction, but one that now reflects stale logic. The commit `fa1531b` changed the approval-policy default from `on-failure` to `on-request` for non-read-only sandboxes. The source of truth (`skills/codex/SKILL.md` line 60) reads: `never` if read-only, `on-request` if workspace-write or danger-full-access. The handbook's vague "coupled to sandbox" masked this change rather than capturing it. The correct operator-facing description is: default `never` for read-only; default `on-request` for workspace-write or danger-full-access.

- **Shared Operating Model — Credential enforcement (line 198)**: The handbook says `codex_guard.py` "scans selected string-bearing fields of tool input" without naming them. Since commit `c724730`, the `config` field is included in `content_fields` for both `CODEX_POLICY` and `CODEX_REPLY_POLICY` (alongside `prompt`, `base-instructions`, `developer-instructions`). This matters operationally: operators who see a block on a `config`-bearing call need to know that field is now scanned. The handbook does not reflect this.

- **Shared Operating Model — Credential enforcement (line 198)**: The handbook does not mention that `scan_unknown_fields = True` is the default for both policies — meaning unknown root-level fields are also traversed and scanned (commit `c724730` completed full-input hook scanning). The existing text implies scanning is limited to a known subset, which is no longer accurate.

- **`/delegate` Runbook — Secret-file gate limitations (line 453–460)**: The limitations section correctly describes the filename-matching approach but does not mention the certifi CA bundle exemption added in commit `9737b4c`. The code in `codex_delegate.py` (`_SAFE_ARTIFACT_TAILS`) explicitly exempts `("certifi", "cacert.pem")` — a known-safe public artifact. The handbook says `*.pem` is blocked "everywhere else" (in the delegate SKILL.md) but the handbook's own limitations section lacks this carve-out. Operators who encounter a `certifi/cacert.pem` file need to know it is exempt to understand why it does not trigger a block.

---

### Coverage Gaps

- **Missing: Analytics synthesis path description — how `emit_analytics.py` extracts fields from dialogue output**. The handbook mentions `emit_analytics.py` as a "deterministic outcome emitter" and mentions the `pipeline-data JSON epilogue` in the sequence diagram and success criteria. But it does not document that the epilogue is now the primary (and preferred) machine contract for analytics, with markdown-heading fallback as a degraded path. Commit `cf72278` made the JSON epilogue the sole authoritative contract. Operators debugging analytics failures need to know: if the epilogue is missing or malformed, `emit_analytics.py` falls back to markdown parsing; if both fail, the build raises `synthesis parse failed`. This failure mode is absent from the Failure and Recovery Matrix and from the analytics subsection.

- **Missing: `codex_guard.py` hooks cover both `codex` and `codex-reply` tools but the PreToolUse description (line 131) does not specify that the same scan policy applies to reply calls**. The distinction matters: `CODEX_REPLY_POLICY` includes `threadId` and `conversationId` in `expected_fields` (not scanned), while `CODEX_POLICY` does not. An operator debugging a block on a reply call vs. an initial call needs to know which fields are in scope.

- **Missing: No runbook entry for failure mode where `emit_analytics.py` receives a dialogue synthesis with a missing or malformed epilogue**. The Failure and Recovery Matrix (line 619–637) lists `analytics | emitter failure | user-facing result still returns | inspect stderr or rerun emitter separately` but does not distinguish between (a) log write failure and (b) synthesis parse failure — which has different recovery (fix the agent synthesis output, not the emitter). Since the epilogue is now the sole machine contract, parse failures are more likely to appear as the markdown fallback path atrophies.

---

### Currency Concerns

- **Verification section (line 813–817)**: States "Last verified on March 7, 2026: plugin-local suite passed with `160 passed`." This count should be verified after the four recent commits (`fa1531b`, `cf72278`, `c724730`, `9737b4c`) — each of which touched tested behavior (approval policy, analytics epilogue, credential scan fields, certifi exemption). The count may be stale and the date reflects the day of this audit, not a prior verification baseline.

- **Normative consultation preflight — Re-consent trigger #4 (line 192)**: Lists "a path adjacent to a secret file enters scope" as a re-consent trigger. The delegate SKILL.md lists `.env`, `*.pem`, `*.key`, `auth.json` as examples. Since the certifi exemption was added to the delegate adapter, operators may ask whether `cacert.pem` adjacency triggers re-consent in consultation paths. The handbook should clarify whether the certifi exemption is delegate-only (which it is — `codex_delegate.py` only) or whether it also applies to consultation scope-envelope re-consent logic. Currently ambiguous.

---

### Structural Issues

- **The credential enforcement section under "Shared Operating Model" (lines 198–211) describes `codex_guard.py` behavior at a high level but does not distinguish between the hook path and the adapter path**. `codex_guard.py` handles consultation egress; `credential_scan.py` (shared module) handles both consultation and delegation. The handbook correctly attributes `codex_guard.py` to the consultation path and the `codex_delegate.py` adapter to delegation, but the shared module `credential_scan.py` is listed only in the File-by-File Change Map under "Hooks and analytics" with no description of its role as the shared scanning library. A reader trying to understand why a credential block occurred in `/delegate` would not find the connection. Recommendation: add a sentence in the credential enforcement section noting that `credential_scan.py` is the shared scanner used by both the hook and the delegation adapter.

- **The `/dialogue` success criteria section (lines 354–366) lists "synthesis plus machine-readable epilogue including the final `mode`" as a criterion, but the deeper internals section does not explain what the epilogue is or how it is produced**. The epilogue is first mentioned in the success criteria, again in the sequence diagram label, and again in the File-by-File Change Map entry for `codex-dialogue.md`. Nowhere is the epilogue format, sentinel (`<!-- pipeline-data -->`), or parsing contract described for operators. Given that commit `cf72278` made this the sole machine contract for analytics, operators need to find that description in the handbook rather than hunting through the agent file. Recommendation: add a subsection under `/dialogue` Deep Internals documenting the epilogue format, the sentinel, and what happens when it is absent (fallback → parse_failed).

---

### Recommended Priority

1. **Update the approval-policy default in the `/codex` runbook inputs table** (Accuracy #1). The current "coupled to sandbox" description hid the `on-failure → on-request` change and leaves operators without the concrete values they need to configure calls correctly. This is the highest-risk accuracy gap because an operator using the old default would dispatch with the wrong approval policy.

2. **Document the JSON epilogue as the primary machine contract in `/dialogue` Deep Internals** (Coverage Gap #1 + Structural Issue #2). The epilogue is now the authoritative source for all analytics fields in dialogue outcomes. The handbook references it in three places but never explains its format or failure modes. Add a subsection covering: sentinel syntax, field list, fallback behavior (markdown), and the `parse_failed` condition.

3. **Add the certifi CA bundle exemption to the `/delegate` secret-file gate limitations** (Accuracy #4). Operators who encounter a `certifi/cacert.pem` file and see it not blocked need a documented explanation. Without it, the exemption looks like a gate failure.

4. **Expand the credential enforcement description to name the scanned fields** (Accuracy #2 and #3). Replace "scans selected string-bearing fields" with the actual field sets: `content_fields` (`prompt`, `base-instructions`, `developer-instructions`, `config`) plus unknown root-level fields via `scan_unknown_fields=True`. This is the behavioral specification operators need when debugging blocks.

5. **Add the analytics parse-failure mode to the Failure and Recovery Matrix** (Coverage Gap #3). Distinguish log write failure from synthesis parse failure — different symptoms, different recovery. This becomes more important as the epilogue path matures and the markdown fallback path becomes the degraded-mode signal.

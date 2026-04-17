# B3 Baseline — codex-dialogue Synthesis

**Thread ID:** `019d977b-23a3-7942-977d-21641446cae0`
**Question:** Review the current context assembly redaction implementation for remaining coverage gaps or false-positive risks that still matter for Codex prompt safety.
**Posture:** adversarial
**Turns:** 4 of 6 budget
**Mode:** `server_assisted`
**Scope envelope:** `packages/plugins/codex-collaboration/server/context_assembly.py`, `packages/plugins/codex-collaboration/tests/test_context_assembly.py`, `docs/tickets/2026-03-30-context-assembly-redaction-hardening.md` (read-only)

This is the verbatim synthesis returned by the `cross-model:codex-dialogue` subagent after Phase 3 (synthesis assembly from `turn_history`). It is the canonical dialogue output — narrative synthesis + Synthesis Checkpoint block + pipeline-data epilogue.

---

### Conversation Summary
- **Topic:** Residual coverage gaps and false-positive risks in `context_assembly` redaction for Codex prompt safety
- **Goal:** Identify remaining risks that still matter after the hardening ticket, with confidence-annotated findings
- **Posture:** Adversarial
- **Turns:** 4 of 6 budget (concluded early — all findings converged, remaining unresolveds are design decisions not dialogue questions)
- **Converged:** Yes — natural convergence on five graded findings with concrete fix designs
- **Trajectory:** `T1:advancing(challenge, new_reasoning) → T2:advancing(concession, new_reasoning) → T3:advancing(new_reasoning, expansion) → T4:advancing(new_reasoning, concession)`
- **Evidence:** none (no scouts executed — scope envelope restricted allowed_roots to 3 files; Codex performed its own out-of-scope file reads which I flag below)
- **Mode:** `server_assisted`

### Key Outcomes

**Finding 1: `github_pat_` fine-grained PAT is the strongest actual prompt-safety gap and the highest-ROI patch to ship first**
- **Confidence:** High
- **Basis:** Convergence — ticket acknowledges the gap, Codex confirmed zero coverage in taxonomy, proposed a concrete strict-tier family, verified the regex shape rejects common false positives (`github_pat_helper`, `github_pat_format`), and argued persuasively against placing it in the contextual tier (reintroduces the placeholder-bypass self-leak path).
- **Proposed fix:** Add strict-tier family `github_fine_grained_pat` with `pattern=r'\bgithub_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}\b'`, `placeholder_bypass=()`, `redact_template="[REDACTED:value]"`.

**Finding 2: `credential_assignment` regex has a narrow true-leak subclass on nested function-call literals**
- **Confidence:** High
- **Basis:** Concession (Codex revised its initial over-broad framing) + verified with exact regex and match-span analysis. Plain quoted assignments (`password = "secret"`) redact correctly; the unquoted-scalar character class `[^\s"']{6,}` consumes `os.getenv(` as group 2 and stops at the quote boundary, leaving the quoted argument as residue. The real leak case: `secret = read_secret("actual-secret-value")` becomes `secret = [REDACTED:value]actual-secret-value")` — the quoted literal survives unredacted.
- **Proposed fix:** Split the family into two explicit patterns — `credential_assignment_quoted` (requires matching quote pair) and `credential_assignment_unquoted_scalar` (allowed chars `[A-Za-z0-9._:/+=@-]{6,}`, excludes parens and dollar signs). Preserves shell/YAML/env-style true positives while closing the leak.

**Finding 3: Placeholder bypass is a developer-accidental self-leak path, not an external exfiltration primitive**
- **Confidence:** Medium
- **Basis:** Revised after adversarial challenge — initial "exfiltration primitive" framing required an attacker-controlled receiver leg that the consultation threat model doesn't support. The real concern is narrower: a developer pastes a real token into a fixture/docstring/comment using example-ish language, the 100-char radial window triggers bypass, and the token is sent off-box to Codex unredacted. Bypass vocabulary is broad (`example`, `format`, `sample`, `dummy`, `redacted`) and the window crosses line boundaries.
- **Proposed fix:** Narrow to same-line-only, left-of-match-only, distance cap ~24-32 chars, vocabulary shrunk to `['example', 'format', 'placeholder', 'sample']`. Acceptable tradeoff: "for example use ghp_..." prose would redact.

**Finding 4: Metadata-field redaction gap is narrower than initially framed (partial refutation)**
- **Confidence:** Medium
- **Basis:** Initial claim was that `_render_packet` emits multiple prompt-visible fields raw. Codex's call-graph verification confirmed `_render_packet` DOES redact `objective` and `repo_url`. Remaining fields that bypass redaction: `repo_root`, `repo_identity.head`, and file labels from `_display_path`. No observed in-the-wild cases — plausible-but-unseen.
- **Proposed fix:** Metadata-safe pass applying only strict + exact-prefix families to `entry.label` and branch. `head` should be validated as SHA at source. `repo_root` is privacy/provenance, not secret-field.

**Finding 5 (emerged from dialogue): Truncation-boundary fragment leak at 4096-byte `_read_file_excerpt` cutoff**
- **Confidence:** Medium
- **Basis:** Emerged from dialogue — raised by Codex in T3 as a lurking concern, then pinned down family-by-family in T4. Not universal: strict bounded-length families (`AKIA+16`, proposed `github_pat_` 22+59, JWT three-segment, `pem_private_key` extended to `\Z`) are safe because truncated prefixes can't match exact-length quantifiers. Lower-bounded families (`ghp_{36,}`, `glpat-{20,}`, `sk-{40,}`, `xox[bps]-{10,}`, `basic_auth {8,}`, `bearer {20,}`, `credential_assignment {6,}`) redact if visible residue meets the minimum but leak raw if below it. **Clearest structural gap: `url_userinfo`** — its regex requires trailing `@` so truncation before `@` prevents ANY match even when `user:partial-password` is visible.
- **Proposed fix:** Reserve headroom when truncating (`4096 - max_token_length`), and/or add a `url_userinfo` variant that tolerates missing terminator at end-of-string.

**Finding 6: JWT family is NOT a prompt-safety leak (concession)**
- **Confidence:** High
- **Basis:** Codex conceded under strict leak-scope definition: JWT is live-strict in taxonomy (contradicts ticket saying out-of-scope), with no negative false-positive test. This is an over-redaction / docs-vs-code drift issue, NOT a secret-leak risk. Should be a docs/test-update ticket, not a patch.

### Areas of Agreement

- `_redact_text` is the sole redaction gate in the Codex-outbound prompt path. Both consult (`control_plane.py`) and dialogue (`dialogue.py`) flows funnel through `assemble_context_packet` → `_render_packet` → `prompt_builder` (pure wrapper). No bypass path exists in the server package. **Confidence: High** (Codex call-graph verification).
- Placing the `github_pat_` family in the `contextual` tier would be "the worst of both worlds" — it would inherit the placeholder-bypass self-leak path. Either ship it as strict or don't ship it. **Confidence: High** (convergence on design principle).
- The original ticket framing of `credential_assignment` as "over-broad corruption" was incomplete — the real bug has both a false-positive corruption face AND a narrow true-leak face. Both require the same fix (splitting the family). **Confidence: High** (convergence after verification).

### Contested Claims

**Placeholder bypass severity**
- **State:** Resolved disagreement
- **Final positions:** Codex conceded "exfiltration primitive" rhetoric as too strong given the threat model; both agreed the issue is a legitimate under-redaction path for developer-accidental self-leaks, not an attacker-controlled exfil chain.
- **Resolution basis:** Adversarial challenge on threat model (T2) — what's the realistic scenario where an attacker plants a token + "example" AND the victim chooses to consult Codex on that file AND the attacker receives the exfiltrated token? Concession followed.
- **Confidence:** Medium

**Metadata-field redaction gap scope**
- **State:** Resolved disagreement
- **Final positions:** Initial claim was broad ("repo_root, head, file labels all bypass redaction"); verification narrowed the actual gap to `repo_root`, `head`, and file labels only — `objective` and `repo_url` ARE redacted via `_render_packet` line 238.
- **Resolution basis:** Call-graph verification in T4.
- **Confidence:** Medium

**`credential_assignment` fix shape**
- **State:** Resolved disagreement
- **Final positions:** Initial proposal to narrow group 2's character class was rejected (it would break `password: my.long.secret.with.dots` true positives). Both agreed on splitting into two families (quoted + unquoted-scalar) as the correct design.
- **Resolution basis:** Walking through true-positive cases showed the naive narrowing just shifts breakage; the split pattern preserves all legitimate cases while closing the leak.
- **Confidence:** High

### Open Questions

- Lower-bounded-family truncation leak mitigation: reserve a max-token-length headroom when truncating (truncate at `4096 - max_token_length`) vs. accept raw-partial-fragment leak risk? (raised T4)
- `url_userinfo` structural truncation gap: add a regex variant that tolerates missing `@` at end-of-string, or accept as a known limitation? (raised T4)
- For same-line placeholder bypass, is "left-of-match only" the right asymmetry? (raised T3, partially addressed in T4 but design trade-off remains)
- Should the JWT family's docs-vs-code drift be resolved by (a) adding a negative false-positive test and updating the ticket, or (b) gating JWT under the new narrowed placeholder bypass? (raised T2, partially addressed)

### Continuation
- **Thread ID:** `019d977b-23a3-7942-977d-21641446cae0`
- **Continuation warranted:** No — this review reached actionable convergence. Remaining open questions are design-decision tickets, not dialogue questions.
- **Unresolved items carried forward:** See Open Questions above — route each to an implementation/design ticket.
- **Recommended posture for continuation (if follow-up needed):** Collaborative or evaluative — at implementation time to walk through specific regex deltas and test cases.
- **Evidence trajectory:** none (no scouts executed; scope envelope restricted scout targets to 3 allowed files)

### Your Assessment (independent judgment)

**Where I agree with Codex:**
- The prioritization is correct: `github_pat_` strict family is the cleanest, highest-ROI patch and the right single change to ship first. The taxonomy change is localized, low-risk, and closes a documented zero-coverage gap.
- The `credential_assignment` split (`_quoted` + `_unquoted_scalar`) is the right fix shape — naive narrowing would trade one failure mode for another.
- Placeholder bypass severity reframing is correct — the original "exfiltration primitive" framing conflates threat models.

**Where I disagree or add nuance:**
- Codex's "ship this one patch this week" framing is right for minimal scope, but if team is doing redaction work at all, the `credential_assignment` split is nearly as high ROI because it ALSO fixes prompt-corruption residue, not just the narrow leak subclass. Consider bundling both #3 and #4 in a single PR — same file, same test harness.
- The `url_userinfo` truncation gap is more concerning than it was framed. URL userinfo (`https://user:password@host`) is one of the most common real-world credential shapes in config files, and the trailing-`@` requirement plus 4096-byte truncation is a genuine structural gap that deserves its own fix even if it's uncommon in practice. I'd raise this from "lurking concern" to "follow-up ticket."

**Emerged from the back-and-forth:**
- The truncation-boundary analysis (Finding 5) — neither side started with this. It surfaced mid-dialogue (T3) and was resolved to a specific family-by-family model (T4) with a clear structural winner (`url_userinfo`).
- The taxonomy-tier policy question: "contextual tier is worst-of-both-worlds for new additions" emerged as a design principle, not a specific finding. It should be documented in the taxonomy file's module docstring for future additions.

**Process notes (flagging for transparency):**
- Codex performed scouts outside the declared `allowed_roots` (read `secret_taxonomy.py`, `control_plane.py`, `dialogue.py`, `prompt_builder.py`, `_read_file_excerpt`). The *agent* respected scope — I did not scout — but Codex's own file-reading happened server-side without agent mediation. This benefit this analysis substantially (the call-graph verification in Finding 4 and the family-by-family truncation math in Finding 5 required those reads), but it's worth noting that Codex's internal tool use was not scope-constrained by this benchmark. If strict scope enforcement is required, the constraint needs to be communicated to Codex in the briefing itself, not just to the agent.

### Synthesis Checkpoint

```
## Synthesis Checkpoint
RESOLVED: github_pat_ fine-grained PAT family has zero coverage in taxonomy; proposed strict-tier family with exact-length underscore-split grammar is the highest-ROI single patch [confidence: High] [basis: convergence]
RESOLVED: credential_assignment has a narrow true-leak subclass on nested function-call literal arguments; fix by splitting into _quoted and _unquoted_scalar families [confidence: High] [basis: concession]
RESOLVED: Placeholder bypass is a developer-accidental self-leak path (same-line narrowing proposed), not an external exfiltration primitive [confidence: Medium] [basis: concession]
RESOLVED: _redact_text is the sole redaction gate in the Codex-outbound prompt path; objective and repo_url are redacted; remaining metadata gap is repo_root/head/file-labels only [confidence: Medium] [basis: convergence]
RESOLVED: JWT family docs-vs-code drift is NOT a prompt-safety leak (out-of-scope under strict leak definition) [confidence: High] [basis: concession]
UNRESOLVED: Should lower-bounded-family truncation gap be fixed by reserving max-token-length headroom in _read_file_excerpt, or accepted as partial-fragment-only risk? [raised: turn 4]
UNRESOLVED: Should url_userinfo get a regex variant tolerating missing @ at end-of-string? [raised: turn 4]
UNRESOLVED: Should narrowed placeholder bypass be same-line-bidirectional or same-line-left-only? [raised: turn 3]
UNRESOLVED: Route JWT docs-vs-code drift as negative-test + doc update, or gate under narrowed bypass? [raised: turn 2]
EMERGED: Truncation-boundary fragment leak model (family-by-family): strict bounded-length families safe; lower-bounded families leak below minimum; url_userinfo is the structural gap requiring trailing @ [source: dialogue-born]
EMERGED: Taxonomy-tier policy principle: contextual tier is worst-of-both-worlds for new full-secret families — either strict or don't add [source: dialogue-born]
```

### Pipeline Data (JSON epilogue)

```json
<!-- pipeline-data -->
{
  "mode": "server_assisted",
  "thread_id": "019d977b-23a3-7942-977d-21641446cae0",
  "turn_count": 4,
  "converged": true,
  "convergence_reason_code": "natural_convergence",
  "termination_reason": "convergence",
  "scout_count": 0,
  "resolved_count": 5,
  "unresolved_count": 4,
  "emerged_count": 2,
  "scope_breach_count": 0
}
```

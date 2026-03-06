# Delegation Round 7: Parallel Agent Review

**Date:** 2026-03-06
**Branch:** feature/delegate-skill
**Method:** 5 independent review agents dispatched in parallel, each reading all 3 documents through a focused lens
**Prior rounds:** 6 rounds, 91 findings integrated
**Documents reviewed:**
- Spec: `docs/plans/2026-03-06-delegation-capability-design.md` (623 lines)
- Plan: `docs/plans/2026-03-06-delegation-implementation-plan.md` (2971 lines)
- Skill: `packages/plugins/cross-model/skills/delegate/SKILL.md` (208 lines)

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 2 | Issues that break correctness or execution |
| P1 | 16 | Issues that degrade quality |
| P2 | 12 | Polish items |
| **Total** | **30** | After deduplication (39 raw, 5 overlaps across agents) |

## Cross-Agent Corroboration

5 findings were independently discovered by 2+ agents (highest confidence):

| Merged ID | Agents | Finding |
|-----------|--------|---------|
| R7-9 | IR-2 + SC-1 | Subprocess timeout values unspecified in spec |
| R7-11 | AF-2 + SS-3 | No byte limit on subprocess stdout capture |
| R7-14 | AF-5 + SS-4 | TOCTOU gap between clean-tree gate and Codex launch |
| R7-13 | IR-5 + SC-8 | Case-insensitive flag claim but no adapter normalization |
| R7-28 | CC-3 + AF-10 | SKILL.md `rm` fallback / `trash` vs `unlink` inconsistency |

---

## P0 Findings

### R7-1: Spec's `blocked` termination_reason description omits `git_error` as a cause
- **Source:** CC-7 (contract-consistency)
- **Type:** schema-contradiction
- **Spec says:** (line 414-421) `blocked` means "Pre-dispatch gate failed (credential, dirty tree, readable secret)"
- **Plan says:** (line 2012-2025) `_emit_analytics` with `blocked_by="git_error"` sets `termination_reason="blocked"` but all three block booleans to `false`
- **Impact:** `blocked_count` can exceed the sum of the three specific block counts. The plan handles this defensively with a comment, but the spec's parenthetical list is incomplete — `git_error` is a fourth cause of `blocked` that is undocumented.
- **Fix:** Update spec line ~418 to: `"blocked" = "Pre-dispatch gate failed (credential, dirty tree, readable secret, or git error)"`. Add `git_error` to the `blocked_by` derivation table.

### R7-2: OOM-killed Codex leaves partial file; `status=ok` with non-zero exit gives no truncation warning
- **Source:** AF-1 (adversarial-failures)
- **Type:** silent data corruption
- **Scenario:** Codex is writing a file, gets OOM-killed (exit 137). The adapter reports `status=ok` because JSONL parsing succeeded. The skill's Step 5 shows `git diff` of the partial file. Claude reviews it but has no signal that the file is truncated vs. intentionally short.
- **Impact:** User may accept a half-written file. Governance rule 5 (review all changes) is technically met but functionally defeated.
- **Fix:** Add to SKILL.md Step 5 review: "When `exit_code != 0`, prominently warn: 'Codex exited abnormally (code {N}) -- changes may be incomplete or corrupt. Signal 137=OOM, 139=segfault. Review with extra caution and verify file completeness.'" Add corresponding guidance to spec failure modes.

---

## P1 Findings

### R7-3: `_REQUIRED_FIELDS` shown as list in spec; plan implements as set
- **Source:** CC-2 (contract-consistency)
- **Spec:** line 452-474, list syntax `[...]`
- **Plan:** line 781+836, set syntax `{...}`
- **Fix:** Update spec code block to use set syntax `{...}`.

### R7-4: SKILL.md says credential scan is "Step 3"; spec/plan define it as Step 4
- **Source:** CC-5 (contract-consistency)
- **SKILL:** line 54, "the credential scan runs in the adapter (Step 3)"
- **Spec/Plan:** Step 3 = read input JSON; Step 4 = credential scan
- **Fix:** Change SKILL.md to "the credential scan runs in the adapter (Step 4)" or remove step number.

### R7-5: NUL byte preservation with `text=True` in `_check_clean_tree` unverified
- **Source:** IR-3 (impl-readiness)
- **Task:** Task 7, `_check_clean_tree()` (lines 2393-2417)
- **Gap:** `subprocess.run(..., text=True)` decodes stdout as text. Whether NUL bytes (`\0`) survive text-mode decoding is platform-dependent. `git status -z` uses NUL separators.
- **Fix:** Add a note to plan: "Python `text=True` preserves NUL bytes on macOS/Linux (verified)." Or switch to `capture_output=True` without `text=True` and decode manually.

### R7-6: `stats_common.observed_avg` import and signature not verified
- **Source:** IR-6 (impl-readiness)
- **Task:** Task 6, `_compute_delegation()` (line 1167)
- **Gap:** Plan references `stats_common.observed_avg(numeric_dispatched, "commands_run_count")` without showing the import or confirming the function signature exists.
- **Fix:** Add to Task 6 Step 3: "Verify `stats_common.observed_avg` exists and accepts `(events: list[dict], field: str) -> tuple[float | None, int]`. Import at module level."

### R7-7: Version bump hardcodes `2.0.0 -> 3.0.0` without verification
- **Source:** IR-7 (impl-readiness)
- **Task:** Task 9, Step 1
- **Fix:** Change to: "Read current version from `plugin.json`. Bump major version (current major + 1)."

### R7-8: `_output()` helper doesn't enforce output schema completeness
- **Source:** IR-10 (impl-readiness)
- **Task:** Task 7, `_output()` function
- **Gap:** Thin wrapper that doesn't validate all required fields are present. Each exception handler manually passes fields — easy to miss one.
- **Fix:** Define `_OUTPUT_FIELDS` constant; have `_output()` assert all required fields present. Or add a test that verifies every output path includes all schema fields.

### R7-9: Subprocess timeout values (600s, 10s) unspecified in spec [CORROBORATED: 2 agents]
- **Source:** IR-2 + SC-1 (impl-readiness + spec-completeness)
- **Gap:** Plan hardcodes `timeout=600` for Codex, `timeout=10` for git/version commands. Spec mentions timeout as a failure mode but never states the values.
- **Fix:** Add to spec pipeline section: "Subprocess timeout: 600s (10 min) for `codex exec`. Git commands and version check: 10s."

### R7-10: `TimeoutExpired` doesn't kill the child Codex process
- **Source:** AF-4 (adversarial-failures)
- **Gap:** `subprocess.run(timeout=600)` raises `TimeoutExpired` but does NOT kill the child process. Orphaned Codex continues modifying files after adapter reports timeout.
- **Impact:** Post-timeout file modifications corrupt the review. Orphaned process consumes API credits.
- **Fix:** Switch to `Popen` for the exec call to enable explicit `proc.kill()` on timeout. Or use `subprocess.run` and add `proc.kill()` in the `TimeoutExpired` handler (requires capturing the process handle).

### R7-11: No byte limit on subprocess stdout capture [CORROBORATED: 2 agents]
- **Source:** AF-2 + SS-3 (adversarial-failures + security-safety)
- **Gap:** `subprocess.run(capture_output=True)` buffers all stdout in memory. No size cap. 500MB of JSONL would exhaust memory.
- **Fix:** Add a stdout size cap (e.g., 50MB) with truncation warning. Or stream JSONL line-by-line using `Popen`.

### R7-12: Skill Step 5 git commands depend on CWD; should use `git -C`
- **Source:** AF-3 (adversarial-failures)
- **Gap:** Skill review phase runs `git status --short` and `git diff` in Claude's Bash context. If CWD differs from repo root, wrong repo is inspected.
- **Fix:** All skill Step 5 git commands should use `git -C <repo_root>` for isolation.

### R7-13: Case-insensitive flag values claimed but no adapter normalization [CORROBORATED: 2 agents]
- **Source:** IR-5 + SC-8 (impl-readiness + spec-completeness)
- **SKILL.md:** "Flag values are case-insensitive"
- **Adapter:** Uses exact lowercase matching (`_VALID_SANDBOXES`, `_VALID_EFFORTS`)
- **Fix:** Either add `.lower()` normalization in `_parse_input()`, or remove "case-insensitive" from SKILL.md and add to spec: "All enum values are case-sensitive lowercase."

### R7-14: TOCTOU gap between clean-tree gate and Codex launch [CORROBORATED: 2 agents]
- **Source:** AF-5 + SS-4 (adversarial-failures + security-safety)
- **Gap:** Tree can be dirtied between Step 7 check and Step 10 launch by external processes.
- **Fix:** Accept as known Step 1 limitation (Step 3 worktree eliminates it). Document explicitly.

### R7-15: No fallback if Step 5 review git commands fail
- **Source:** AF-6 (adversarial-failures)
- **Gap:** If `git diff` fails during review, governance rule 5 ("Claude reviews all changes") is violated silently.
- **Fix:** Add to SKILL.md Step 5: "If any review command fails, warn the user that changes exist but could not be reviewed. Never report success without completed review."

### R7-16: Log file created with default umask, not explicit 0o600
- **Source:** SS-5 (security-safety)
- **Gap:** `append_log()` uses `open(LOG_PATH, "a")` — on first creation, file gets `0o644` (world-readable on shared systems).
- **Fix:** Add `os.chmod(LOG_PATH, 0o600)` after creation, or use `os.open` with explicit mode.

### R7-17: Symlink traversal bypasses secret-file gate
- **Source:** SS-6 (security-safety)
- **Gap:** A `.gitignore`'d symlink pointing to `~/.aws/credentials` as `./creds` wouldn't match pathspec. Codex may follow it.
- **Fix:** Document limitation. Verify Codex sandbox behavior with symlinks outside project root.

### R7-18: `reasoning_effort` enum values never listed in spec
- **Source:** SC-2 (spec-completeness)
- **Location:** Spec line 188 — type "enum" but values not enumerated
- **Fix:** Add: "Values: `minimal`, `low`, `medium`, `high`, `xhigh`" (matching SKILL.md and plan).

---

## P2 Findings

### R7-19: `blocked_by` enum values and gate-to-boolean mapping undocumented in spec
- **Source:** SC-3 (spec-completeness)
- **Fix:** Add table mapping `blocked_by` values to analytics booleans.

### R7-20: `_REQUIRED_FIELDS` code block missing `model` and `reasoning_effort`
- **Source:** SC-5 (spec-completeness)
- **Fix:** Add both fields to the Python code block between `"sandbox"` and `"full_auto"`.

### R7-21: `exit_code` "only present when dispatched=true" vs always-present-with-null
- **Source:** SC-4 (spec-completeness)
- **Fix:** Clarify: "Always present. `null` when `dispatched=false`; integer when process completed."

### R7-22: Step 10 error message template doesn't match implementation
- **Source:** SC-6 (spec-completeness)
- **Fix:** Split into separate rows for timeout vs spawn failure.

### R7-23: "Usable event" never formally defined
- **Source:** SC-7 (spec-completeness)
- **Fix:** Add: "Only events matching the seven known types count as usable."

### R7-24: `full_auto` type validation missing from spec's B3 amendment
- **Source:** SC-9 (spec-completeness)
- **Fix:** Add `isinstance(value, bool)` check for `full_auto` to the B3 paragraph.

### R7-25: Sandbox read scope exposes tracked files + non-pathspec secrets
- **Source:** SS-1 (security-safety)
- **Fix:** Already documented in spec as known limitation. Add note to SKILL.md troubleshooting.

### R7-26: Prompt injection relies entirely on external sandbox
- **Source:** SS-2 (security-safety)
- **Fix:** Already covered by single-user assumption and sandbox reliance. No spec change needed. Consider logging hashed prompt for forensics.

### R7-27: Empty stdout from Codex (exit 0) produces confusing error; exit_code lost
- **Source:** AF-7 (adversarial-failures)
- **Fix:** Capture `proc.returncode` before `_parse_jsonl` so it appears in error output.

### R7-28: SKILL.md `rm` fallback + `trash` vs `unlink` inconsistency [CORROBORATED: 2 agents]
- **Source:** CC-3 + AF-10 (contract-consistency + adversarial-failures)
- **Fix:** Remove `(or rm if trash is unavailable)` from SKILL.md. Python `unlink` in adapter is fine (not a shell command).

### R7-29: Non-string prompt type bypasses credential scan (rejected later at Phase B)
- **Source:** AF-9 (adversarial-failures)
- **Fix:** Move `isinstance(prompt, str)` check before credential scan to fail fast.

### R7-30: consultation-stats SKILL.md path not specified in Task 9
- **Source:** IR-8 (impl-readiness)
- **Fix:** Add path: `skills/consultation-stats/SKILL.md` relative to plugin root.

---

## Findings by Document

### Spec changes needed
R7-1 (P0), R7-3, R7-9, R7-18, R7-19, R7-20, R7-21, R7-22, R7-23, R7-24

### Plan changes needed
R7-5, R7-6, R7-7, R7-8, R7-10, R7-11, R7-12, R7-15, R7-16, R7-27, R7-29, R7-30

### SKILL.md changes needed
R7-2 (P0), R7-4, R7-13, R7-15, R7-17, R7-25, R7-28

---

## Agent Performance

| Agent | Raw Findings | After Dedup | P0 | P1 | P2 | Duration |
|-------|-------------|-------------|----|----|----|----|
| contract-consistency | 4 | 3 | 1 | 2 | 1* | 70s |
| impl-readiness | 8 | 6 | 0 | 5 | 1* | 94s |
| adversarial-failures | 10 | 8 | 1 | 5 | 4* | 137s |
| security-safety | 8 | 6 | 0 | 4 | 4* | 105s |
| spec-completeness | 9 | 7 | 0 | 2 | 5 | 91s |
| **Total** | **39** | **30** | **2** | **16** | **12** | — |

*After dedup contribution (some findings merged with other agents)

# T-07 Slice 7b: codex-review Skill — Instruction-Document Implementation Plan

## Overview

| Attribute | Value |
|-----------|-------|
| Artifact | `packages/plugins/codex-collaboration/skills/codex-review/SKILL.md` |
| Type | Instruction document (Markdown skill), no server changes |
| New Python tests | None — runtime path covered by 7a plumbing tests |
| Verification | Manual smoke + existing test coverage citation |
| Branch | `feature/t07-review-7b` |
| AC reference | T-07 ticket, `codex-review` AC (search "review usage distinctly in analytics") |

**What this plan covers:** the content and structure of a single SKILL.md
file that orchestrates code review through the existing `codex.consult`
MCP tool with `workflow="review"`.

**What this plan does not cover:** server changes, new MCP tools, analytics
emission logic, or new test files.

---

## 1. Skill Identity and Frontmatter

```yaml
---
name: codex-review
description: >-
  Review code changes through the codex-collaboration advisory runtime.
  Gathers diff and context from git, consults Codex with workflow="review",
  and synthesizes findings with Claude-side review judgment. Use when user
  asks to review code, review a diff, review current changes, review a
  branch, or asks for a cross-model code review.
argument-hint: "[branch | commit-range | 'staged' | 'unstaged']"
user-invocable: true
allowed-tools: >-
  Bash, Read, Glob, Grep,
  mcp__plugin_codex-collaboration_codex-collaboration__codex.status,
  mcp__plugin_codex-collaboration_codex-collaboration__codex.consult
---
```

**Rationale for tool list:** The skill reads diffs, surrounding files,
and project conventions before dispatch. `Bash` for git commands, `Read`
for file content, `Glob`/`Grep` for convention discovery and file
searching. MCP tools for runtime preflight and consultation.

## 2. Scope and Non-Goals

**In scope:**
- Review orchestration over `codex.consult` with `workflow="review"`
- Diff/context gathering from git
- Briefing assembly into `objective` + `explicit_paths`
- Claude-side synthesis with severity and source attribution
- Default `profile="code-review"` with user-requestable override

**Non-goals (explicit prohibitions in the skill):**
- No server-side changes or analytics emission (server records
  `workflow="review"` in `OutcomeRecord` automatically)
- No native App Server `review/start` API usage
- No cross-model MCP tools (`mcp__plugin_cross-model_codex__*`)
- No file modifications — read-only review. Bash usage is constrained
  to git read commands (`git diff`, `git status`, `git log`,
  `git merge-base`, `git rev-parse`, `git branch`), `wc`, `test`, and
  similar read-only operations. Do NOT run `git checkout`, `git reset`,
  `git add`, `git commit`, or any command that modifies the working tree.
- Shell-safety: all git-derived paths must be double-quoted in Bash
  commands. User-supplied refs/ranges must be validated with
  `git rev-parse --verify` and the resolved SHA used in subsequent
  commands, never the raw input.
- Not a hard promotion gate for delegation artifacts

## 3. Repo and Runtime Preconditions

Reuse the `consult-codex` pattern:

1. `git rev-parse --show-toplevel` → `repo_root`. Fail and stop if not a
   git repo.
2. Call `codex.status` with `repo_root`.
   - `auth_status == "missing"` → report remediation, stop.
   - `errors` non-empty → report errors, stop.
   - Otherwise → proceed.

## 4. Review Scope Selection

This is the critical section. The skill must define unambiguous behavior
for every entry condition.

### Scope resolution table

User-supplied refs and ranges are untrusted input. The skill must
validate with a grammar check (reject shell metacharacters and leading
`-`), resolve to SHA via `git rev-parse --verify '<validated-ref>^{commit}'`
(single-quoted), and use only the returned 40-character hex SHA in all
subsequent commands.

| User input | Git command (uses resolved SHAs and `<base>`) | Notes |
|------------|-------------|-------|
| Branch name (`feature/x`) | `git diff $(git merge-base <base> <sha>)...<sha>` | Compare against merge-base with `<base>` |
| Commit range (`abc..def`) | `git diff <sha_start>..<sha_end>` | Two-dot: endpoint comparison |
| `staged` | `git diff --cached` | Staged changes only |
| `unstaged` | `git diff` | Working tree vs index |
| No argument, on non-default branch | `git diff $(git merge-base <base> HEAD)...HEAD` | Default: review branch against merge-base |
| No argument, on default branch | `git diff HEAD` | Captures both staged and unstaged changes against HEAD. If empty and no untracked files, report "No changes to review" |

### Merge-base detection

Determine the base branch (`<base>`): check if `main` exists
(`git rev-parse --verify 'main^{commit}'`). If not, try `master`.
If neither exists, ask the user to specify. Use this resolved `<base>`
in all subsequent merge-base commands — do NOT hardcode `main`.

### Untracked files

After the diff command, run `git ls-files --others --exclude-standard`
to list untracked files. This lists individual files (not collapsed
directory entries), so new files inside new directories are discovered.

**Caps and filters (mandatory before reading):**

1. **In-repo paths only.** All paths must resolve within `repo_root`.
   Reject any path that resolves outside the repository.
2. **Max 20 untracked files.** If more than 20, include only the first
   20 and note "N additional untracked files not included in review."
3. **Max 50KB per file.** Run `wc -c -- "$path"` and skip files larger
   than 50KB. Note them as skipped.
4. **Skip generated/vendor/binary.** Same exclusion patterns as §4
   (binary and generated files): `*.min.js`, `*.lock`, `dist/`, `build/`,
   `*.generated.*`, `node_modules/`, `vendor/`, `__pycache__/`, `*.pyc`.
5. **Skip credential files.** Same exclusion as §6 layer-0 safety.

Include surviving untracked files in the briefing in a dedicated
"## New Untracked Files" section (between Changes and Surrounding Code).

### Large diff thresholds

| Diff size | Behavior |
|-----------|----------|
| ≤ 500 lines | Include full diff in briefing |
| 501–1500 lines | Summarize by file. Inline critical changes (up to 500 lines). Prioritize: new files > core logic > tests > config/formatting. Note which files were summarized vs inlined. |
| > 1500 lines | Stop and report: "This changeset has {N} lines, exceeding the 1500-line review limit. Consider splitting for effective review." Do not attempt the review. |

### Empty diff

If the diff is empty AND there are no untracked files, report "No changes
to review" and stop.

### Binary and generated files

Skip binary files (`git diff --stat` shows `Bin`). Skip files matching
common generated patterns (`*.min.js`, `*.lock`, `dist/`, `build/`,
`*.generated.*`). Note skipped files in the briefing metadata.

## 5. Context Gathering

Three categories of context, all embedded into the `objective` parameter:

### 5a. Changed file list → `explicit_paths`

Pass changed file paths as `explicit_paths` in the `codex.consult` call.
This gives the server file-level metadata independent of any `objective`
truncation.

**Filtering rules (mandatory before dispatch):**

The server's `context_assembly._read_file_excerpt` raises
`ContextAssemblyError` when an explicit path is missing from disk. The skill MUST filter `explicit_paths`:

1. **Extant files only.** Deleted files appear in the diff but no longer
   exist. Represent deletions exclusively through the diff content in
   `objective`. Do NOT include deleted paths in `explicit_paths`.
2. **Renamed files:** include only the new (destination) path, not the
   old (source) path.
3. **No credential-suggestive paths.** Exclude `auth.json`, `.env`,
   `credentials.json`, `*.pem`, `*.key` from `explicit_paths` even if
   they were changed. (Layer-0 safety, §6.)
4. **No binary or generated files.** Same exclusion list as §4 (binary
   and generated files section).
5. **In-repo paths only.** All paths must resolve within `repo_root`.

**Path extraction command:** reuse the resolved SHA(s) from §4's scope
table. Append `--name-status` to the same diff command:

| Scope | Path extraction command |
|-------|------------------------|
| Branch review (resolved `<sha>`) | `git diff --name-status $(git merge-base <base> <sha>)...<sha>` |
| Staged | `git diff --cached --name-status` |
| Unstaged | `git diff --name-status` |
| Commit range (resolved `<sha_start>`, `<sha_end>`) | `git diff --name-status <sha_start>..<sha_end>` |
| No argument, non-default branch | `git diff --name-status $(git merge-base <base> HEAD)...HEAD` |
| No argument, default branch | `git diff --name-status HEAD` |

Parse `--name-status` output to get status codes (`A`=added, `M`=modified,
`D`=deleted, `R`=renamed). Use the status to apply filtering rules:
- `D` (deleted): exclude from `explicit_paths`
- `R` (renamed): include only the destination path (second column)
- `A`, `M`: include if they pass existence/exclusion checks

Then filter surviving paths with existence checks (`test -f -- "$path"`)
and the exclusion patterns above. Shell-quote all git-derived paths.

### 5b. Diff and surrounding code → `objective`

**Objective byte budget (mandatory):**

The server's `context_assembly._render_packet` renders `objective`
directly into the advisory packet. Objective content is NOT
trimmed — only context entries (explicit_references, task_local_context,
etc.) are trimmed. If `objective` alone exceeds the 24KB soft target,
all `explicit_paths` entries are trimmed away. If it exceeds the 48KB
hard cap, `ContextAssemblyError` crashes the consultation.

Budget allocation:
- **Objective hard limit: 20KB** (leaves ~4KB headroom for packet
  framing, repo identity, safety envelope, and output schema).
- **Soft target: 16KB** (leaves room for `explicit_paths` entries to
  survive trimming).

The skill MUST measure the assembled briefing before dispatch:
1. Estimate byte size of the assembled briefing text.
2. If > 20KB: truncate surrounding code first, then summarize diff
   sections, then drop convention text. Note truncations in the
   briefing.
3. If still > 20KB after truncation: stop and report "Review material
   exceeds the advisory packet budget. Reduce the review scope."
4. The large-diff line thresholds in §4 are initial heuristics. The
   byte budget is the binding constraint.

Assemble a structured briefing:

```
## Review Scope
[1-2 sentences on what the changes do, based on diff inspection]

## Changes
[Diff content or summarized sections per §4 thresholds]

## New Untracked Files
[Content of untracked files from §4 untracked section, if any.
Omit section if none.]

## Surrounding Code
[For files < 300 lines: full file. For larger files: modified
functions/classes + 20 lines above and below each hunk.]

## Project Conventions
[Relevant rules from CLAUDE.md, .claude/rules/, lint configs.
If none found: "(none discovered)"]

## Review Request
Review these changes for:
1. Bugs and logic errors
2. Security concerns
3. Edge cases and error handling gaps
4. Violations of project conventions (if any above)
5. Anything that would make you hesitate in code review

Focus on substantive issues. Skip style nitpicks unless they
indicate a real problem.
```

### 5c. Convention discovery

Check for project conventions via:
- `Read` the project's `.claude/CLAUDE.md` if it exists
- `Glob` for `.claude/rules/**/*` (not just `*.md` — rules can be any
  readable text format). Filter to text files only.
- `Grep` for lint/format configs (`ruff.toml`, `.eslintrc`,
  `pyproject.toml` [tool.ruff] section, etc.)

Include relevant conventions in the briefing's "Project Conventions" section.

## 6. Layer-0 Secret Safety

These instructions go directly into the SKILL.md:

1. **Do NOT read** `auth.json`, `.env`, `credentials.json`, `*.pem`,
   `*.key`, or any file whose name suggests credentials.
2. **Before embedding any content into `objective`**, scan for
   secret-like patterns: `sk-...`, `Bearer ...`, `-----BEGIN.*KEY-----`,
   `id_token`, `access_token`, `refresh_token`, `account_id`, API keys,
   passwords in config.
3. **If secrets are detected:** replace with `[REDACTED: credential
   material]` and note the redaction in the review output.
4. **If redaction cannot be confirmed** (e.g., uncertain whether a value
   is a real credential): do NOT include the content. Fail closed.
5. **Note:** The server's `consultation_safety.py` (invoked by
   `codex_guard.py`'s PreToolUse hook) and `context_assembly.py`
   redaction provide downstream defense. The skill
   does not depend on those layers — it provides its own layer-0 scan.

## 7. Consult Dispatch

Call `codex.consult` with:

| Parameter | Value |
|-----------|-------|
| `repo_root` | From step 3 |
| `objective` | Assembled briefing from §5 |
| `explicit_paths` | Changed file paths from §5a |
| `workflow` | `"review"` (always) |
| `profile` | `"code-review"` (default) |

### Profile override

If the user requests a deeper review (e.g., "thorough review",
"architecture review", "deep review"), use `profile="deep-review"`
instead. The skill should state this option in its instructions.

| User says | Profile |
|-----------|---------|
| Default / "review this" | `code-review` (effort=high, turn_budget=4) |
| "deep review" / "thorough" / "architecture review" | `deep-review` (effort=xhigh, turn_budget=8) |

### Prohibitions

- Do NOT use `review/start` or any App Server native review API. Review
  is a workflow over `codex.consult`, not a separate runtime primitive.
- Do NOT use cross-model MCP tools (`mcp__plugin_cross-model_codex__*`).
- Do NOT set `profile` to a value not listed above unless the user
  explicitly names a profile.

## 8. Synthesis Contract

After receiving the `codex.consult` result, Claude synthesizes findings.

### Output structure

```
### Summary
- Scope reviewed: [files changed, approximate line count]
- Findings: [count by severity]
- Overall: [1-2 sentence assessment]

### Findings
[Ordered by severity, each finding has:]

#### [Severity] Issue title
- **Location:** `file:line`
- **Source:** Codex / Claude / Both
- **Problem:** What's wrong
- **Impact:** Why it matters
- **Suggestion:** How to address it

### Disagreements with Codex
[Issues where Claude disagrees with Codex's assessment]

### Items Not Flagged by Codex
[Issues Claude found independently]
```

### Severity ratings

| Severity | Criteria |
|----------|----------|
| Critical | Exploitable security vulnerability or data loss risk |
| High | Bug causing incorrect behavior under normal conditions |
| Medium | Edge case or code smell that could cause problems |
| Low | Inconsistency indicating potential confusion |

### Hard rules

- Findings first. No preamble, no praise.
- Every finding has severity + source attribution.
- False positives from Codex are called out in "Disagreements."
- "No findings" must be explicit: "No issues found in [scope]."
- If diff was summarized or context was partial: "**Review limitation:**
  This review covered [X of Y files / summarized diff]. Issues in
  unsummarized sections may not be detected."
- Do NOT include the raw Codex response.
- Do NOT include full file contents (use excerpts with line references).

## 9. Verification and Acceptance

### What "done" means for 7b

| Check | Method |
|-------|--------|
| SKILL.md exists at correct path | File system |
| Frontmatter valid (name, description, allowed-tools, user-invocable) | Read and validate |
| Skill references `workflow="review"` in consult dispatch | Read SKILL.md |
| Skill references `profile="code-review"` as default | Read SKILL.md |
| All 9 plan sections represented in skill content | Read SKILL.md |
| No server files modified | `git diff --stat` |
| Existing codex-collaboration tests still pass | `uv run --package codex-collaboration pytest` |

### Existing 7a test coverage (cited, not duplicated)

These tests already cover the `workflow="review"` runtime path:

| Test | File | What it covers |
|------|------|----------------|
| `test_codex_consult_schema_includes_workflow` | `test_mcp_server.py:1500` | MCP schema has workflow enum |
| `test_codex_consult_dispatch_passes_workflow_to_control_plane` | `test_mcp_server.py:1510` | MCP dispatch threads workflow to ConsultRequest |
| `test_codex_consult_rejects_invalid_workflow` | `test_mcp_server.py:1552` | Invalid workflow values rejected |
| `test_codex_consult_threads_workflow_to_outcome_record` | `test_control_plane.py:1082` | workflow="review" flows to OutcomeRecord |
| `test_codex_consult_default_workflow_in_outcome` | `test_control_plane.py:1111` | Default workflow="consult" preserved |
| `test_outcome_record_explicit_review_workflow` | `test_outcome_record.py:161` | OutcomeRecord accepts workflow="review" |
| Analytics review view tests | `test_analytics_skill.py` | Analytics script counts workflow="review" |

### Manual smoke (required for 7b closure)

The 7b AC requires the skill "can review a real diff through
`codex.consult` with `workflow="review"`." This is not deferrable. If
the smoke cannot run, 7b remains open and the PR must NOT claim the AC.

**Smoke procedure:**

1. **Before:** Record the line count of `analytics/outcomes.jsonl`:
   `wc -l <plugin_data_path>/analytics/outcomes.jsonl`. If the file
   does not exist, record count as 0.
2. **Quiet window:** Do not run other consult/dialogue/delegate
   operations during the smoke. If a concurrent append is unavoidable,
   verify the new row by timestamp proximity (within 60s of the review
   invocation), not by count delta alone.
3. **Run:** Invoke `/codex-review` on a real diff (e.g., the 7b branch
   itself against merge-base).
4. **Verify dispatch:** Confirm the `codex.consult` tool call includes
   `workflow: "review"` and `profile: "code-review"` (visible in tool
   call output or transcript).
5. **Verify output:** Confirm the synthesis follows §8 (severity ratings,
   source attribution, structured findings or explicit "no findings").
6. **Verify analytics:** Record the line count of `outcomes.jsonl` after
   the review. Read the newest row (last line of file) and confirm
   `"workflow": "review"` and `"outcome_type": "consult"`. If the count
   delta is not exactly 1, verify by timestamp proximity.

**Evidence artifacts for PR:**
- Before/after line counts of `outcomes.jsonl`
- The new analytics row (redacted if it contains repo paths)
- The review output (summary section at minimum)

**If App Server is unavailable:** The smoke cannot run and 7b remains
open. The PR can ship the SKILL.md for structural review, but the AC is
explicitly not claimed. This must be stated in the PR description.

---

## Implementation Sequence

1. Create `packages/plugins/codex-collaboration/skills/codex-review/SKILL.md`
2. Write the skill following this plan's 9 sections
3. Verify existing tests still pass
4. Manual smoke on a real diff (blocks 7b closure — not deferrable)
5. PR with smoke evidence and 7a test coverage citation

If smoke cannot run (App Server unavailable), the PR ships the SKILL.md
for structural review only. The 7b AC remains open.

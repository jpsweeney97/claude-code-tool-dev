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

# Codex Review

Review code changes through `codex.consult` with `workflow="review"`.

## Scope

**In scope:** Diff gathering, context assembly, consultation dispatch with `workflow="review"`, Claude-side synthesis with severity and source attribution.

**Prohibitions:**
- Do NOT use `review/start` or any App Server native review API. Review is a workflow over `codex.consult`, not a separate runtime primitive.
- Do NOT use cross-model MCP tools (`mcp__plugin_cross-model_codex__*`).
- Do NOT modify files. This skill is read-only.
- Do NOT run `git checkout`, `git reset`, `git add`, `git commit`, or any command that modifies the working tree. Bash usage is constrained to git read commands (`git diff`, `git status`, `git log`, `git merge-base`, `git rev-parse`, `git branch`), `wc`, `test`, and similar read-only operations.
- **Shell-quote all git-derived paths.** File paths from `git diff`, `git status`, and `--name-status` output are untrusted input. Always double-quote paths in Bash commands: `test -f -- "$path"`, `wc -c -- "$path"`. Never interpolate bare `<path>` into shell commands.

## Procedure

### 1. Repo and runtime preconditions

Run `git rev-parse --show-toplevel` via Bash.

- If the command fails: report that the workspace is not a git repository and **stop**.
- Otherwise: use the output as `repo_root`.

Call `codex.status` with `repo_root`.

- If `auth_status` is `"missing"`: report auth remediation steps and **stop**.
- If `errors` is non-empty: report errors and **stop**.
- Otherwise: proceed.

### 2. Determine review scope

Resolve the review ref and diff command from the user's argument. The resolved ref is reused in step 5 for `--name-status` extraction — define it once here.

**Ref validation (mandatory before any Bash use):** User-supplied branch names and commit ranges are untrusted input. Validate before passing to any Bash command:

1. **Grammar check (text-level, before Bash).** Inspect the raw argument string. **Reject** if it contains any of: whitespace, `$`, `` ` ``, `;`, `|`, `&`, `(`, `)`, `{`, `}`, `'`, `"`, `>`, `<`, `!`, `\`, or starts with `-`. Report "Invalid ref: contains shell metacharacters" and **stop**.
2. **Resolve to SHA.** After the grammar check passes, run `git rev-parse --verify '<validated-ref>^{commit}'` (single-quoted to prevent expansion). For ranges, split on `..` and resolve each endpoint separately. The output is a 40-character hex SHA.
3. **Reject** if `git rev-parse` fails — report "Could not resolve ref: {input}" and **stop**.
4. **Use only the resolved SHA** in all subsequent Bash commands. The SHA is 40 hex characters — intrinsically shell-safe. Never reuse the raw user input after this step.

| User input | Review ref | Git command | Notes |
|---|---|---|---|
| Branch name (`feature/x`) | resolved SHA | `git diff $(git merge-base <base> <sha>)...<sha>` | Compare against merge-base with `<base>` |
| Commit range (`abc..def`) | resolved SHAs | `git diff <sha_start>..<sha_end>` | Two-dot: endpoint comparison |
| `staged` | (index) | `git diff --cached` | Staged changes only |
| `unstaged` | (worktree) | `git diff` | Working tree vs index |
| No argument, on non-default branch | `HEAD` | `git diff $(git merge-base <base> HEAD)...HEAD` | Default: branch against merge-base |
| No argument, on default branch | `HEAD` | `git diff HEAD` | Staged and unstaged against HEAD |

**Merge-base detection:** Determine the base branch (`<base>`): check if `main` exists (`git rev-parse --verify 'main^{commit}'`). If not, try `master`. If neither exists, ask the user to specify. Use this resolved `<base>` in all subsequent merge-base commands — do NOT hardcode `main`.

**Empty diff:** If the diff is empty AND there are no untracked files (check via `git ls-files --others --exclude-standard`), report "No changes to review" and **stop**.

### 3. Evaluate diff size

| Diff size | Behavior |
|---|---|
| ≤ 500 lines | Include full diff in briefing |
| 501–1500 lines | Summarize by file. Inline critical changes (up to 500 lines). Prioritize: new files > core logic > tests > config/formatting. Note which files were summarized vs inlined. |
| > 1500 lines | **Stop** and report: "This changeset has {N} lines, exceeding the 1500-line review limit. Consider splitting for effective review." Do NOT attempt the review. |

**Binary and generated files:** Skip binary files (`git diff --stat` shows `Bin`). Skip files matching: `*.min.js`, `*.lock`, `dist/`, `build/`, `*.generated.*`, `node_modules/`, `vendor/`, `__pycache__/`, `*.pyc`. Note skipped files in the briefing metadata.

### 4. Gather untracked files

Run `git ls-files --others --exclude-standard` to list untracked files. This lists individual files (not collapsed directory entries), so new files inside new directories are discovered.

**Caps and filters (mandatory before reading any untracked file):**

1. **In-repo paths only.** All paths must resolve within `repo_root`. Reject any path that resolves outside the repository.
2. **Max 20 untracked files.** If more than 20, include only the first 20 and note "N additional untracked files not included in review."
3. **Max 50KB per file.** Run `wc -c -- "$path"` and skip files larger than 50KB. Note them as skipped.
4. **Skip generated/vendor/binary.** Exclude: `*.min.js`, `*.lock`, `dist/`, `build/`, `*.generated.*`, `node_modules/`, `vendor/`, `__pycache__/`, `*.pyc`.
5. **Skip credential files.** Exclude: `auth.json`, `.env`, `credentials.json`, `*.pem`, `*.key`, and any file whose name suggests credentials.

Include surviving untracked files in the briefing under "New Untracked Files."

### 5. Extract `explicit_paths`

Reuse the resolved SHA(s) from step 2. Append `--name-status` to the same diff command:

| Scope | Path extraction command |
|---|---|
| Branch review (resolved `<sha>`) | `git diff --name-status $(git merge-base <base> <sha>)...<sha>` |
| Staged | `git diff --cached --name-status` |
| Unstaged | `git diff --name-status` |
| Commit range (resolved `<sha_start>`, `<sha_end>`) | `git diff --name-status <sha_start>..<sha_end>` |
| No argument, non-default branch | `git diff --name-status $(git merge-base <base> HEAD)...HEAD` |
| No argument, default branch | `git diff --name-status HEAD` |

Parse `--name-status` output for status codes:

| Status | Action |
|---|---|
| `D` (deleted) | **Exclude.** Deleted files crash the server (`ContextAssemblyError` from `context_assembly._read_file_excerpt` when an explicit path is missing). Represent deletions only through diff content in `objective`. |
| `R` (renamed) | Include only the destination path (second path column), not the source. |
| `A` (added), `M` (modified) | Include if they pass the filters below. |

`D` paths and non-existent worktree paths are filtered by `test -f -- "$path"`, so unstaged deletions (and any other scope's deleted files) are represented only in `objective`, not in `explicit_paths`.

**Filters (mandatory before dispatch):**

1. **Existence check:** Run `test -f -- "$path"` for each candidate. Exclude paths that do not exist on disk.
2. **No credential-suggestive paths:** Exclude `auth.json`, `.env`, `credentials.json`, `*.pem`, `*.key`.
3. **No binary or generated files:** Same exclusion list as step 3.
4. **In-repo paths only:** All paths must resolve within `repo_root`.

### 6. Layer-0 secret safety

Apply these rules to ALL content before embedding into `objective`:

1. Do NOT read `auth.json`, `.env`, `credentials.json`, `*.pem`, `*.key`, or any file whose name suggests credentials.
2. Scan all content for secret-like patterns: `sk-...`, `Bearer ...`, `-----BEGIN.*KEY-----`, `id_token`, `access_token`, `refresh_token`, `account_id`, API keys, passwords in config.
3. If secrets are detected: replace with `[REDACTED: credential material]` and note the redaction in the review output.
4. If redaction cannot be confirmed (uncertain whether a value is a real credential): do NOT include the content. Fail closed.

The server's `consultation_safety.py` and `context_assembly.py` redaction provide downstream defense. This skill provides its own independent layer-0 scan and does NOT depend on those layers.

### 7. Assemble the objective

Build a structured briefing to use as the `objective` parameter:

```
## Review Scope
[1-2 sentences on what the changes do, based on diff inspection]

## Changes
[Diff content or summarized sections per step 3 thresholds]

## New Untracked Files
[Content of untracked files from step 4, if any. Omit section if none.]

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

Focus on substantive issues. Skip style nitpicks unless they indicate a real problem.
```

**Convention discovery:** Check for project conventions via:
- Read the project's `.claude/CLAUDE.md` if it exists.
- Glob for `.claude/rules/**/*` and filter to text files.
- Grep for lint/format configs (`ruff.toml`, `.eslintrc`, `pyproject.toml` `[tool.ruff]` section).

**Objective byte budget (mandatory):**

The server renders `objective` directly into the advisory packet. Objective is NOT trimmed — only context entries are. If `objective` exceeds the 24KB soft target, all `explicit_paths` entries are trimmed away. If it exceeds the 48KB hard cap, the consultation crashes with `ContextAssemblyError`.

| Limit | Value | Purpose |
|---|---|---|
| Hard limit | 20KB | Leaves ~4KB headroom for packet framing |
| Soft target | 16KB | Leaves room for `explicit_paths` to survive trimming |

After assembling the briefing, estimate its byte size:

1. If > 20KB: truncate Surrounding Code first, then summarize diff sections, then drop Project Conventions. Note each truncation in the briefing.
2. If still > 20KB after truncation: **stop** and report "Review material exceeds the advisory packet budget. Reduce the review scope."
3. The line-count thresholds in step 3 are initial heuristics. The byte budget is the binding constraint.

### 8. Dispatch consultation

Call `codex.consult` with:

| Parameter | Value |
|---|---|
| `repo_root` | From step 1 |
| `objective` | Assembled briefing from step 7 |
| `explicit_paths` | Filtered paths from step 5 |
| `workflow` | `"review"` (always) |
| `profile` | `"code-review"` (default) or `"deep-review"` (if user requested) |

**Profile selection:**

| User says | Profile |
|---|---|
| Default / "review this" / no qualifier | `"code-review"` (effort=high, turn_budget=4) |
| "deep review" / "thorough review" / "architecture review" | `"deep-review"` (effort=xhigh, turn_budget=8) |

Do NOT set `profile` to a value not listed above unless the user explicitly names a profile.

### 9. Synthesize findings

After receiving the consultation result, synthesize findings into the output structure below.

**Hard rules:**
- Findings first. No preamble, no praise.
- Every finding has severity + source attribution (Codex / Claude / Both).
- False positives from Codex are called out in "Disagreements."
- "No findings" must be explicit: "No issues found in [scope]."
- If diff was summarized or context was partial: "**Review limitation:** This review covered [X of Y files / summarized diff]. Issues in unsummarized sections may not be detected."
- Do NOT include the raw Codex response.
- Do NOT include full file contents (use excerpts with line references).

**Output structure:**

```
### Summary
- Scope reviewed: [files changed, approximate line count]
- Findings: [count by severity]
- Overall: [1-2 sentence assessment]

### Findings
[Ordered by severity, each finding:]

#### [Severity] Issue title
- **Location:** `file:line`
- **Source:** Codex / Claude / Both
- **Problem:** What's wrong
- **Impact:** Why it matters
- **Suggestion:** How to address it

### Disagreements with Codex
[Issues where Claude disagrees with Codex's assessment.
If none: omit section.]

### Items Not Flagged by Codex
[Issues Claude found independently.
If none: omit section.]
```

**Severity ratings:**

| Severity | Criteria |
|---|---|
| Critical | Exploitable security vulnerability or data loss risk |
| High | Bug causing incorrect behavior under normal conditions |
| Medium | Edge case or code smell that could cause problems |
| Low | Inconsistency indicating potential confusion |

## Failure Handling

| Condition | Behavior |
|---|---|
| MCP tool unavailable | Report: plugin may not be installed. Check `/mcp`. **Stop.** |
| Preflight fails | Report errors from `codex.status`. **Stop.** |
| Consult raises | Report the error. Do NOT retry automatically. |
| Empty diff, no untracked | Report "No changes to review." **Stop.** |
| Diff > 1500 lines | Report the limit and suggest splitting. **Stop.** |
| Objective > 20KB after truncation | Report budget exceeded. **Stop.** |
| Secret detected, redaction uncertain | Do NOT include the content. Fail closed. |

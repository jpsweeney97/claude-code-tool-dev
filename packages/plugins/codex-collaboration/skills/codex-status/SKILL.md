---
name: codex-status
description: Check Codex advisory runtime health, auth, version, and diagnostics.
user-invocable: true
allowed-tools: Bash, mcp__plugin_codex-collaboration_codex-collaboration__codex.status
---

# Codex Status

Return runtime health, auth status, Codex version, and advisory runtime diagnostics.

## When to Use

- User runs `/codex-status`
- User asks about Codex availability or connectivity
- As preflight before consultation (called automatically by `/consult-codex`)

## Procedure

1. Run `git rev-parse --show-toplevel` via Bash to determine the repository root.
   - If the command fails (exit code non-zero): report that the current workspace is not a git repository and **stop**. Do NOT fall back to the current directory.

2. Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.status` with `repo_root` set to the output from step 1.

3. Present the result to the user. Key fields:
   - `codex_version`: installed Codex CLI version
   - `app_server_version`: App Server user-agent
   - `auth_status`: `"authenticated"` or `"missing"`
   - `advisory_runtime`: runtime ID, policy fingerprint, thread count, uptime (if bootstrapped)
   - `required_methods` / `optional_methods`: method availability
   - `errors`: any runtime errors

4. If `auth_status` is `"missing"`, advise: run `codex login` or set `OPENAI_API_KEY`.

5. If `errors` is non-empty, report each error.

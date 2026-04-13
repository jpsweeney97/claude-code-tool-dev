---
name: consult-codex
description: Consult Codex for a second opinion via the codex-collaboration advisory runtime. Thin wrapper — routes user input through codex.status preflight then codex.consult.
argument-hint: "<question>"
user-invocable: true
allowed-tools: Bash, mcp__plugin_codex-collaboration_codex-collaboration__codex.status, mcp__plugin_codex-collaboration_codex-collaboration__codex.consult
---

# Consult Codex

One-shot advisory consultation via the codex-collaboration runtime.

## Scope

This is the thin consult skill for the packaged plugin surface. It routes user input through `codex.status` and `codex.consult`. The safety substrate (credential scanning, profiles, learnings, analytics) is implemented in the server and hook layers — this skill does not duplicate that logic.

**In scope:** Status preflight, consultation dispatch, result relay.

**Out of scope:** Briefing enrichment is handled by the server's context assembly pipeline, not this skill. Do NOT port cross-model consultation features into this skill.

## Procedure

### 1. Determine repo root

Run `git rev-parse --show-toplevel` via Bash.

- If the command fails (exit code non-zero): report that the current workspace is not a git repository and **stop**. Do NOT fall back to the current directory.
- Otherwise: use the output as `repo_root` for all subsequent calls.

### 2. Preflight: Check runtime health

Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.status` with the `repo_root` from step 1.

- If `auth_status` is `"missing"`: report auth remediation steps and **stop**.
- If `errors` is non-empty: report errors and **stop**.
- Otherwise: proceed to consultation.

### 3. Consult

Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult` with:

| Parameter | Source |
|-----------|--------|
| `repo_root` | Output of `git rev-parse --show-toplevel` from step 1 |
| `objective` | The user's question (from `$ARGUMENTS` or conversation context) |
| `explicit_paths` | Any file paths the user referenced (optional) |

### 4. Relay result

Present the consultation result:

- **Position**: Codex's answer
- **Evidence**: Supporting claims with citations
- **Uncertainties**: What Codex flagged as uncertain
- **Follow-up branches**: Suggested next questions

Add your own brief assessment of the response quality and relevance.

## Failure Handling

| Condition | Behavior |
|-----------|----------|
| MCP tool unavailable | Report: plugin may not be installed. Check `/mcp` |
| Preflight fails | Report errors from `codex.status`. Do not dispatch consultation |
| Consult raises | Report the error. Do not retry automatically |

---
name: codex
description: Consult OpenAI Codex for second opinions on architecture, debugging, code review, plans, and decisions.
argument-hint: "[-m <model>] [-s {read-only|workspace-write|danger-full-access}] [-a {untrusted|on-failure|on-request|never}] [-t {minimal|low|medium|high|xhigh}] [PROMPT]"
user-invocable: true
disable-model-invocation: true
allowed-tools: mcp__codex__codex, mcp__codex__codex-reply
---

# Codex Consultation Protocol

Consult OpenAI Codex via its MCP server for second opinions. Claude remains the primary agent — Codex is a consultant.

Two MCP tools available:
- `mcp__codex__codex` — start a new conversation
- `mcp__codex__codex-reply` — continue an existing conversation

## Arguments

Parse optional flags from `$ARGUMENTS`. Remaining text after flags = PROMPT.

| Flag | MCP Parameter | Default |
|------|---------------|---------|
| `-m <model>` | `model` | Codex's default model |
| `-s {read-only\|workspace-write\|danger-full-access}` | `sandbox` | `read-only` |
| `-a {untrusted\|on-failure\|on-request\|never}` | `approval-policy` | `never` if read-only, `on-failure` if workspace-write or danger-full-access |
| `-t {minimal\|low\|medium\|high\|xhigh}` | `config` → `{"model_reasoning_effort": "<value>"}` | `high` |

Only `prompt` is required when calling `mcp__codex__codex`. Other parameters are optional — include them only when overriding Codex's defaults.

Examples:
- `/codex review the plan in docs/plans/auth-redesign.md` → all defaults, PROMPT = "review the plan..."
- `/codex -t xhigh why is the auth middleware failing?` → reasoning xhigh, rest defaults
- `/codex -s workspace-write fix the flaky test in auth.test.ts` → workspace-write sandbox, approval on-failure

## Step 1: Build Context Briefing

Codex has no knowledge of the current session. Before calling it, build a complete briefing from conversation context.

Include:
- **Current task:** What we're working on and why
- **Decisions made:** What's been decided, what trade-offs were considered
- **Relevant material:** Inline key content or reference file paths — Codex in read-only mode can browse files but not write. Inline when concise; reference paths when files are large.
- **What's been tried:** If applicable, what approaches failed and why
- **Specific question:** Frame the consultation as a clear, answerable question

Structure:

```
## Context
[Task, state, and relevant decisions]

## Material
[Inline relevant content — code, plans, docs, error output. Be selective, not exhaustive.]

## Question
[What we want Codex's input on]
```

**Calibrate depth to the question.** A quick "what do you think of this approach?" needs a paragraph of context. A debugging session needs file contents, error output, and a list of failed approaches.

## Step 2: Choose Invocation Strategy

**Direct invocation** (default):
- Quick consultations (1-2 expected turns)
- Codex's response will immediately inform your next action
- Conversation context matters for interpreting the response

**Subagent delegation** (for extended sessions):
- 3+ expected turns of back-and-forth
- Topic is self-contained — main conversation context isn't needed turn-by-turn
- A summary of the outcome is sufficient

For subagent delegation:
1. Spawn a `general-purpose` subagent
2. Pass the enriched briefing and instruct it to manage the Codex conversation
3. Instruct it to return: a summary of findings + the Codex `threadId`
4. To continue later, resume the subagent via its `agentId` (preserves richer context than raw `threadId`)

## Step 3: Invoke Codex

### New conversation

Call `mcp__codex__codex` with all parameters:

| Parameter | Value |
|-----------|-------|
| `prompt` | Enriched briefing from Step 1 |
| `model` | From `-m` flag, or omit for Codex default |
| `sandbox` | From `-s` flag, or `read-only` |
| `approval-policy` | From `-a` flag, or `never` (read-only) / `on-failure` (workspace-write) |
| `config` | `{"model_reasoning_effort": "<-t flag or 'high'>"}` |

### Continue conversation

Call `mcp__codex__codex-reply` with:
- `threadId`: from previous Codex response
- `prompt`: follow-up message (enrich with any new context since last turn)

## Step 4: Relay Response

Present Codex's response to the user with your own assessment:
- Where you agree or disagree with Codex's take
- How it changes (or doesn't change) the current approach
- Recommended next steps

Do not just parrot Codex's response. Add value as the primary agent.

## Troubleshooting

### MCP server not available
Codex MCP server must be configured in settings and `codex` CLI installed (`npm install -g @openai/codex`).

Authentication can use either method:
- **Interactive login (recommended):** run `codex login` once and complete the auth flow. Credentials are cached locally and reused across sessions until logout, expiry, or revocation.
- **API key login:** set `OPENAI_API_KEY` in the environment, then optionally persist via `printenv OPENAI_API_KEY | codex login --with-api-key`.

### Codex response seems off-base
The briefing was likely insufficient. Re-invoke with more context — include specific file contents, error messages, or conversation history that was omitted.

### Thread lost
If a `threadId` is no longer valid, start a new conversation. Re-enrich the prompt with full context.

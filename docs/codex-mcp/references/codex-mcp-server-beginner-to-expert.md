# Codex `mcp-server` — Beginner to Expert Guide

**Last updated:** 2026-02-10  
**Validated against local CLI:** `codex-cli 0.93.0`  
**Audience:** Engineers integrating OpenAI Codex into MCP-capable clients (Claude Desktop, custom orchestrators, internal agents)

> **Navigation note:** This guide remains valid, but `../codex-mcp-master-guide.md` is the primary entry point for end-to-end learning. Use `../codex-mcp-master-guide.md#canonical-quickstart` and `../codex-mcp-master-guide.md#canonical-command-reference` for canonical procedures and copy/paste commands.

---

## 1) What This Guide Covers

This guide takes you from:

- **Beginner:** “How do I run `codex mcp-server` and test it?”
- **Intermediate:** “How do I integrate it into tools/clients safely?”
- **Expert:** “How do I run it reliably in production with policy, security, and observability?”

It focuses on the **Codex MCP server path** (`codex mcp-server`) and clarifies how that differs from `codex mcp` commands.

---

## 2) Fast Mental Model

There are two related but different command families:

| Command | What It Does | Typical Use |
|---|---|---|
| `codex mcp-server` | Runs Codex as an MCP server (stdio transport). | Expose Codex as tools to another MCP client. |
| `codex mcp ...` | Manages MCP servers *that Codex itself can call*. | Let Codex consume third-party MCP tools. |

Common confusion:

- `mcp-server` = “Codex is the server.”
- `mcp add/list/login` = “Codex is the client of other servers.”

---

## 3) Prerequisites

1. Install Codex CLI:

```bash
npm install -g @openai/codex
```

2. Confirm installation:

```bash
codex --version
codex mcp-server --help
```

3. Authenticate Codex (choose one):

- **Interactive login (recommended):**

```bash
codex login
codex login status
```

- **API key login:**

```bash
export OPENAI_API_KEY="..."
printenv OPENAI_API_KEY | codex login --with-api-key
```

---

## 4) Beginner Quickstart (Canonical Pointer)

Canonical quickstart owner:

- `../codex-mcp-master-guide.md#canonical-quickstart`

Canonical command owner:

- `../codex-mcp-master-guide.md#canonical-command-reference`

Keep this reference guide for architecture decisions, policy guidance, and operating patterns.

### Understand process lifecycle

`codex mcp-server` is a stdio MCP process. In practice:

- It stays alive while the client keeps the stdio session open.
- It typically exits when the client disconnects/closes stdin.
- Supervisors/wrappers should restart it cleanly when needed.

---

## 5) Tool Contract (What the Server Exposes)

This section describes the **upstream** `codex mcp-server` tool surface as a practical integration reference.

If you are implementing the server layer described in this repository, treat `../specs/2026-02-09-codex-mcp-server-build-spec.md` as the normative contract (including which keys are accepted/rejected).

### `codex` (new conversation)

**Required input:**

- `prompt` (string)

**Optional input (varies by integration):**

- `model`
- `sandbox` (`read-only`, `workspace-write`, `danger-full-access`)
- `approval-policy` (`untrusted`, `on-failure`, `on-request`, `never`)
- `config` object (commonly reasoning effort; some integrations may support additional keys)
- `base-instructions` (if supported by your environment)
- `include-plan-tool` (if supported by your environment)

### `codex-reply` (continue conversation)

**Required input:**

- `prompt`

**Identifier requirement (at least one):**

- `threadId` (canonical)
- `conversationId` (deprecated compatibility alias)

Compatibility note:

- Some integrations may still reference `conversationId`; current docs label it as deprecated compatibility behavior.

### Typical output shape

Outputs generally include:

- assistant text/content
- `structuredContent`
- `structuredContent.threadId` (canonical continuity identifier for follow-ups; compatibility alias requests normalize to this)

---

## 6) Core Runtime Controls You Should Understand

Even when running as MCP server, Codex behavior is still shaped by config and runtime policy.

### Sandbox mode

- `read-only`: safest default for analysis.
- `workspace-write`: allow writes in workspace.
- `danger-full-access`: no sandbox protections (high risk).

### Approval policy

- `untrusted`
- `on-failure`
- `on-request`
- `never`

### Safe default profile (recommended)

- sandbox: `read-only`
- approvals: `never` (or stricter environment-specific policy)
- explicit model + reasoning effort in controlled environments

---

## 7) Config Layering and Overrides

Codex supports config overrides with `-c key=value`.

Examples:

```bash
codex mcp-server -c model="o3"
codex mcp-server -c 'features.some_flag=true'
codex mcp-server -c 'model_reasoning_effort="high"'
```

Practical rule:

1. Keep stable defaults in config profiles/files.
2. Use `-c` for temporary experiment overrides.
3. Record overrides in run logs for reproducibility.

Useful MCP-related config keys (especially when Codex consumes other MCP servers):

- `mcp_servers`
- `mcp_servers.<id>.startup_timeout_sec`
- `mcp_servers.<id>.tool_timeout_sec`
- `experimental_use_mcp_client`
- `mcp_oauth_callback_port`
- `mcp_oauth_callback_hostname`
- `mcp_oauth_open_browser`
- `mcp_oauth_credentials_store`

---

## 8) Intermediate Integration Patterns

### Pattern 1: Local desktop integration

Use `codex mcp-server` as an MCP server entry in your local MCP-capable client configuration.

Example config shape:

```json
{
  "mcpServers": {
    "codex": {
      "command": "codex",
      "args": ["mcp-server"]
    }
  }
}
```

Good for:

- individual developer workflows
- debugging prompts/tools quickly

### Pattern 2: Team wrapper process

Wrap `codex mcp-server` with a thin launcher that:

- enforces approved sandbox/approval policy
- injects allowed config defaults
- adds standard telemetry tags

Good for:

- shared dev environments
- policy consistency across contributors

### Pattern 3: Service-orchestrated execution

Run Codex MCP as a managed process behind an orchestrator, with strict lifecycle controls.

Good for:

- larger organizations
- audit-heavy or regulated workflows

### Pattern 4: Agents SDK integration (Python)

The Codex MCP docs include using `MCPServerStdio` in OpenAI Agents SDK workflows. Minimal shape:

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

with MCPServerStdio(params={"command": "codex", "args": ["mcp-server"]}) as server:
    agent = Agent(name="Assistant", mcp_servers=[server])
    result = Runner.run_sync(agent, "Give me a migration risk checklist")
    print(result.final_output)
```

---

## 9) Expert Architecture Guidance

### 9.1 Security hardening checklist

1. Default to `read-only` sandbox.
2. Disallow `danger-full-access` except explicit break-glass paths.
3. Redact secrets from prompts, logs, and error payloads.
4. Never pass OAuth/API tokens through MCP tool arguments.
5. Rotate and monitor API credentials where key-based auth is used.

### 9.2 Authentication strategy

Use one of:

- **Interactive login** (human workstation/dev contexts).
- **API key mode** (`OPENAI_API_KEY`) for controlled automation.

For automation:

- keep secrets in env/secret manager, not source control
- avoid printing env values in logs

### 9.3 OAuth for external MCP servers (Codex as client)

When using `codex mcp login <server>`, Codex can do OAuth flows for external servers it connects to.

Useful commands:

```bash
codex mcp list
codex mcp add <name> --url <https://...>
codex mcp login <name>
```

Config keys like `mcp_servers.<id>.startup_timeout_sec`, `mcp_servers.<id>.tool_timeout_sec`, and OAuth callback options are relevant when Codex consumes other MCP servers.

### 9.4 Reliability model

Treat upstream Codex calls as networked operations:

- add timeout budgets
- classify retryable failures (`TIMEOUT`, transient upstream)
- do single bounded retries
- preserve `threadId` durability for multi-turn continuity
- set explicit startup/tool timeouts in config for predictable failure behavior

### 9.5 Observability model

Capture structured events per request:

- request id
- tool name (`codex` / `codex-reply`)
- thread present
- latency
- result status
- retry count

Never log:

- full prompt payload by default
- tokens/keys
- bearer headers

---

## 10) Troubleshooting Playbook

### “`codex mcp-server` starts but no tools show up”

Check:

1. Client is truly connecting over stdio.
2. No wrapper script is swallowing stdio.
3. Codex version is current enough for MCP server support.
4. `codex mcp-server --help` works in the same runtime/user context.

### “Auth errors when calling tools”

Check:

```bash
codex login status
```

If not authenticated:

```bash
codex login
```

Or refresh API key-based login:

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

### “`threadId` invalid or lost”

Recovery:

1. Start new `codex` call with full context.
2. Persist returned `threadId`.
3. Continue with `codex-reply`.

### “OAuth callback port conflicts”

If using OAuth for external MCP servers via Codex, configure callback host/port keys in Codex config to avoid collisions.

### “Permission/sandbox confusion”

Confirm requested sandbox and approval mode; reject unsafe defaults in shared environments.

---

## 11) Anti-Patterns to Avoid

1. Running `danger-full-access` by default in team environments.
2. Treating `mcp-server` and `mcp add/list/login` as the same workflow.
3. Putting secrets in prompts/tool inputs.
4. Ignoring `threadId` continuity and then debugging “context loss.”
5. Shipping without timeout and retry policy.

---

## 12) Production Readiness Checklist

Before you call this production-ready, verify:

1. Standard launch command and config profile documented.
2. Auth bootstrap and rotation runbook documented.
3. Sandbox/approval policy guardrails enforced.
4. Structured logs/metrics enabled and secret-safe.
5. Timeout + retry + fallback behavior tested.
6. `threadId` lifecycle tested across restarts/failures.
7. Incident playbook includes auth outage, upstream outage, and degraded mode.

---

## 13) FAQ

### Q: Is `codex mcp-server` enough by itself?

For local/dev usage, usually yes. For team/prod usage, you typically add wrappers for policy, telemetry, and runbook controls.

### Q: Can I use project-specific config?

Yes. Codex supports layered configuration and per-invocation overrides (`-c`), which is useful for environment-specific behavior.

### Q: Should I store credentials in prompts or config files?

No. Use interactive login or environment-based key management. Never embed secrets in prompts or repo docs.

### Q: What is the minimum viable integration?

1. Install Codex.
2. Login.
3. Use an MCP client (or the inspector) to spawn `codex mcp-server` over stdio.
4. Call `codex`, then `codex-reply` with the returned `threadId`.

---

## 14) Reference Commands (Canonical Pointer)

Use the canonical command block in:

- `../codex-mcp-master-guide.md#canonical-command-reference`

---

## 15) Official Documentation Links

- [Codex MCP](https://developers.openai.com/codex/mcp)
- [Codex CLI](https://developers.openai.com/codex/cli)
- [Codex CLI Reference](https://developers.openai.com/codex/cli/reference)
- [Codex Config Reference](https://developers.openai.com/codex/config-reference)
- [Codex Authentication](https://developers.openai.com/codex/auth)

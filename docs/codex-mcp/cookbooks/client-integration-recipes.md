# Client Integration Recipes (Codex MCP)

**Purpose:** Copy-adapt patterns for common integration contexts.  
**Audience:** Developers wiring Codex MCP into local clients, SDKs, or managed runtimes.

---

## How to Choose a Recipe

| Scenario | Start Here | Why |
|---|---|---|
| Local experimentation | Recipe 1 | Fastest setup loop |
| Programmatic workflows | Recipe 2 | SDK-native orchestration |
| Team policy enforcement | Recipe 3 | Centralized defaults and controls |
| Managed environment rollout | Recipe 4 | Reliability and operations focus |

---

## Recipe 1: Local MCP Client Config

Use when connecting a desktop MCP client to Codex server process.

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

Validation checklist:

1. Tool discovery includes `codex` and `codex-reply`.
2. First call returns `threadId`.
3. Follow-up call succeeds with same `threadId`.

---

## Recipe 2: Python Agents SDK Stdio Bridge

Use when embedding Codex MCP in scripted agent workflows.

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

with MCPServerStdio(params={"command": "codex", "args": ["mcp-server"]}) as server:
    agent = Agent(name="CodexAdvisor", mcp_servers=[server])
    result = Runner.run_sync(agent, "Review this migration plan for rollback risk.")
    print(result.final_output)
```

Hardening tips:

- add per-run timeout controls
- add request IDs in caller logs
- wrap with retry logic for transient failures

---

## Recipe 3: Team Wrapper Launcher

Use when you need consistent policy defaults.

Wrapper responsibilities:

1. Enforce approved sandbox and approval policy defaults.
2. Inject controlled config overrides.
3. Emit structured logs with redaction.
4. Validate auth state before launching long workflows.

Recommended wrapper output fields:

- `requestId`
- `toolName`
- `threadIdPresent`
- `durationMs`
- `resultCode`

---

## Recipe 4: Managed Runtime (Service/Orchestrator)

Use when reliability and governance matter more than setup speed.

Minimum controls:

1. Process supervision and restart policy.
2. Health checks for tool availability and auth status.
3. Timeout + bounded retry policy.
4. Alerting on error-rate and latency thresholds.
5. Operational runbook ownership.

---

## Recipe 5: Multi-Workspace Environments

Use when multiple repositories/workspaces share one platform.

Recommendations:

1. Isolate config profiles by workspace.
2. Apply least-privilege sandbox per workspace class.
3. Separate logs/telemetry streams by workspace identifier.
4. Define explicit policy for cross-workspace data leakage prevention.

---

## Recipe Quality Checklist

- Inputs/outputs explicitly documented.
- Failure behavior and recovery steps included.
- Security assumptions stated.
- Evidence captured for reproducibility.

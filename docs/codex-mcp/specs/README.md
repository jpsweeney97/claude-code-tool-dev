# Specs Index

**Purpose:** Quick navigation for Codex consultation architecture specs.

> **Navigation note:** Use `../codex-mcp-master-guide.md` for consolidated onboarding and implementation context. Use this specs index when you need normative build requirements and acceptance criteria.

## Codex Consultation Specs

1. **Client/Skill integration spec**  
   `./2026-02-09-codex-consultation-skill-implementation-spec.md`
   - Defines behavior for the `/codex` skill workflow.
   - Covers parsing, briefing assembly, invocation strategy, relay behavior, safety rules, and acceptance tests.
   - Includes decision-locked `codex` / `codex-reply` schema parity and compatibility normalization.

2. **MCP server build spec**  
   `./2026-02-09-codex-mcp-server-build-spec.md`
   - Defines how to build the MCP server layer itself.
   - Covers tool schemas/contracts, server architecture, error taxonomy, auth/security boundaries, observability, and conformance testing.
   - Locks `structuredContent.threadId` as canonical continuity source and `conversationId` as compatibility alias.

## Governance Status

- Both specs are **Approved (decision-locked)**.
- “Open Decisions” has been replaced with “Resolved Decisions” in both documents.

## Boundary Clarification

- Use the **client/skill spec** when implementing the primary agent workflow that *calls* Codex tools.
- Use the **server spec** when implementing the MCP service that *exposes* `codex` and `codex-reply`.
- Implementing both yields end-to-end coverage from user command handling through MCP transport and Codex execution.

## Recommended Build Order

1. Build MCP server core first (tool schemas, validation, defaults, error taxonomy) using `./2026-02-09-codex-mcp-server-build-spec.md`.
2. Add server reliability/security layers (timeouts, retry policy, policy guards, redaction, observability) and pass server conformance tests.
3. Implement client/skill integration flow (argument parsing, briefing assembly, invocation strategy, response relay) using `./2026-02-09-codex-consultation-skill-implementation-spec.md`.
4. Run end-to-end validation across both layers, then lock acceptance criteria and operational runbooks.

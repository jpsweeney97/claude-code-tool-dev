---
job: Perform a systematic optimization review of the cross-model plugin, producing prioritized, evidence-backed findings across performance, architecture, and resource usage.
created: 2026-03-16
---

# Cross-Model Plugin Optimization Review

Review the cross-model plugin at `packages/plugins/cross-model/` for optimization opportunities. This plugin enables Claude-to-Codex collaboration via MCP servers, hooks, skills, and agents. It includes a bundled context-injection MCP server at `context-injection/`.

## Step 1: Architecture Mapping

Before identifying any findings, map the system. Produce:

- **Component inventory**: Each component (skills, agents, hooks, MCP servers, shared scripts), its role, and approximate size
- **Execution paths**: Trace each user-facing flow (`/codex`, `/dialogue`, `/delegate`, `/consultation-stats`) from skill invocation through all intermediate components to final output. Note every file read, subprocess spawn, MCP call, and data transformation along the path
- **Shared state**: What data structures, files, or processes are shared across components (event log, credential scanner, MCP server state)
- **Hot paths**: Which execution paths run most frequently or involve the most steps

Do NOT identify optimization opportunities yet. This section is input for the analysis — complete it fully before proceeding.

## Step 2: Optimization Analysis

Analyze the mapped architecture through four lenses. For each lens, identify 2–5 concrete findings. If a lens genuinely has fewer than 2 findings, state why.

### Lens A: Runtime Performance

Where does the plugin spend time unnecessarily?

Focus on: redundant I/O (reading the same files multiple times across components), unnecessary serialization/deserialization, blocking operations that could be parallel, startup costs that could be deferred.

### Lens B: Architectural Complexity

Where is the plugin more complex than its behavior requires?

Focus on: abstraction layers that don't earn their cost, indirection that obscures data flow, components that duplicate logic already present elsewhere, configuration or contract structures that could be simplified without losing capability.

### Lens C: Resource Efficiency

Where does the plugin use more resources (memory, disk, processes) than necessary?

Focus on: data structures that grow without bounds, temporary files or state that persists longer than needed, subprocess/agent spawning patterns, MCP server lifecycle overhead.

### Lens D: Data Flow

Where does data travel an unnecessarily long path or undergo unnecessary transformations?

Focus on: information that's computed, serialized, passed between components, and deserialized when it could be computed closer to where it's consumed. Credential scanning pipeline, context injection's process_turn → execute_scout handoff, and briefing assembly are high-value areas.

## Step 3: Cross-Component Interactions

Separately from the per-lens analysis, identify optimization opportunities that exist at the boundaries between components — places where the interaction pattern between two or more components creates inefficiency that neither component exhibits in isolation.

Examples of what to look for:
- The same validation running in both a hook and a skill
- Data being serialized for MCP transport and then immediately deserialized by the receiving component
- Agent spawning patterns that create coordination overhead exceeding the parallelism benefit
- Credential scanning running at multiple pipeline stages when one well-placed check would suffice

Identify 2–4 cross-component findings.

## Step 4: Prioritized Findings

Consolidate all findings from Steps 2 and 3 into a single prioritized table:

| # | Finding | Lens | Impact | Effort | Risk | Files |
|---|---------|------|--------|--------|------|-------|
| 1 | ... | ... | ... | ... | ... | ... |

For each column:
- **Impact**: High / Medium / Low — what improves and by roughly how much (cite evidence: "credential scanner reads N files per invocation")
- **Effort**: S / M / L — number of files touched and complexity of the change
- **Risk**: What could break — name the specific failure mode, not "might cause issues"
- **Files**: List every file path involved in the finding

Sort by impact descending, then effort ascending.

## Step 5: Recommended Sequence

From the prioritized table, recommend an implementation order. Group findings into phases:

- **Phase 1**: High-impact, low-effort changes that can be done independently
- **Phase 2**: Changes that depend on Phase 1 or require more effort
- **Phase 3**: Large refactors worth considering but not urgent

For each phase, state what's measurably different when it's done.

## Ground Rules

- Every finding MUST cite specific file paths and line ranges. "Consider optimizing the credential scanner" is not a finding. "credential_scan.py:45-72 reads the denylist file on every invocation instead of caching it at module load" is.
- Do NOT include code style, formatting, naming, or documentation findings. This review is about operational efficiency, not aesthetics.
- Do NOT recommend optimizations that trade correctness for speed. The plugin's safety properties (fail-closed credential scanning, over-redaction preference) are non-negotiable constraints, not optimization targets.
- If a component's current approach is already efficient for its scale, say so explicitly rather than manufacturing findings. Not every component needs optimization.
- When estimating impact, ground it in the plugin's actual usage patterns, not theoretical worst cases.

---
job: Analyze the cross-model plugin for the highest-leverage opportunities to enhance existing capabilities or develop new ones, producing prioritized, evidence-backed findings.
created: 2026-03-17
---

# Cross-Model Plugin: High-Leverage Improvement Opportunities

Analyze the cross-model plugin at `packages/plugins/cross-model/` for the highest-leverage opportunities to enhance existing capabilities or develop new ones. This plugin enables Claude-to-Codex collaboration through MCP servers, hooks, skills, and agents. It includes a bundled context-injection MCP server at `context-injection/`.

## Step 1: Capability Audit

Before identifying any opportunities, build a detailed understanding of what each capability actually does at the implementation level. For each of the four user-facing capabilities (`/codex`, `/dialogue`, `/delegate`, `/consultation-stats`):

1. **Trace the execution path** from skill invocation through every intermediate component (scripts, hooks, MCP calls, agent spawns) to final output
2. **Map the implementation boundaries** — what does this capability handle well? Where does it stop short? What edge cases are handled vs. unhandled?
3. **Identify the architectural leverage points** — which components in the path are load-bearing (changes here cascade broadly) vs. leaf-level (changes here are isolated)?
4. **Note any underutilized infrastructure** — components, data, or patterns that exist but aren't fully exploited by the capability

Also map the shared infrastructure (credential scanning, event logging, analytics computation, context injection) with the same depth.

Produce a written audit before proceeding. Do NOT identify improvement opportunities in this step — this is diagnostic input for the analysis.

## Step 2: Enhancement Analysis

From the capability audit, identify opportunities to make existing capabilities meaningfully better. Analyze through three lenses:

### Lens A: Capability Depth

Where are existing capabilities shallow or incomplete? Look for:
- Capabilities that handle the common case well but degrade on edge cases
- Features described in contracts or documentation but not fully implemented
- Capabilities where the architecture supports more sophistication than the current implementation delivers
- Places where one capability's output could feed another's input but doesn't

### Lens B: User Experience Quality

Where does the interaction model create friction or miss opportunities for better feedback? Look for:
- Error states that could provide more actionable guidance
- Capabilities that require user knowledge not supplied by the interface
- Output formats that don't match how the user will consume the information
- Missing feedback loops — the user can't tell if something is working well or poorly

### Lens C: Safety and Reliability

Where could the safety model be strengthened, or failure modes be handled more gracefully? Look for:
- Fail-soft paths where fail-closed would be more appropriate (or vice versa)
- Credential patterns not covered by the current taxonomy
- Recovery paths that require manual intervention where automation would work
- Places where the safety model's conservatism could be reduced without increasing risk (precision improvements that reduce over-blocking)

For each lens, identify 2–5 concrete findings. If a lens genuinely has fewer than 2, explain why.

## Step 3: New Capability Analysis

Separately from enhancing what exists, identify opportunities to develop genuinely new capabilities that the current architecture could support. These must be grounded — not a wishlist, but specific possibilities enabled by the existing component inventory.

For each proposed new capability:
- **What it does** — one sentence
- **Why it's high-leverage** — what user problem it solves, grounded in evidence from the capability audit
- **What it builds on** — which existing components, patterns, or infrastructure it extends
- **What's needed** — the incremental effort beyond what already exists (new code, modifications to existing components, new contracts or protocols)
- **What it doesn't need** — architectural changes or prerequisites that are NOT required (this prevents scope inflation)

Propose 3–5 new capabilities. If fewer than 3 are genuinely grounded in the architecture, propose fewer and explain why.

## Step 4: Prioritized Findings

Consolidate all findings from Steps 2 and 3 into a single prioritized table:

| # | Finding | Type | Leverage | Effort | Evidence | Components |
|---|---------|------|----------|--------|----------|------------|
| 1 | ... | Enhance / New | ... | ... | ... | ... |

Column definitions:
- **Type**: `Enhance` (improving existing capability) or `New` (developing new capability)
- **Leverage**: High / Medium / Low — impact per unit of effort. Cite the specific evidence: what changes for the user, and why this matters more than other findings
- **Effort**: S (1–3 files, contained change) / M (4–10 files, moderate complexity) / L (10+ files or new subsystem)
- **Evidence**: The specific code, pattern, or architectural observation that supports this finding. Not "could be improved" — what specifically did you see?
- **Components**: Every file path involved

Sort by leverage descending.

## Step 5: Recommended Roadmap

From the prioritized table, recommend an implementation sequence:

- **Phase 1**: High-leverage enhancements that unlock or de-risk later phases
- **Phase 2**: Medium-leverage enhancements and the highest-leverage new capability
- **Phase 3**: Remaining new capabilities and lower-leverage enhancements

For each phase: what's measurably different when it's done, and what it unblocks.

## Ground Rules

- Every finding MUST cite specific file paths, code patterns, or architectural observations. "The dialogue system could be better" is not a finding. "codex-dialogue.md's convergence detection uses a simple turn-count heuristic when the ledger already tracks position-level agreement that could drive early termination" is.
- Do NOT include findings about code style, formatting, documentation quality, or test coverage. This analysis is about capability opportunities, not code hygiene.
- Do NOT propose capabilities that require replacing core architectural decisions (e.g., "switch from Codex to a different model provider"). Work within the existing architecture.
- Safety constraints (fail-closed credential scanning, over-redaction preference) are non-negotiable constraints, not improvement targets. Findings may propose making safety more precise (fewer false positives) but NEVER weaker.
- If a capability is already well-implemented for its purpose and scale, say so explicitly. Not every capability needs enhancement.
- New capability proposals MUST build on existing components. Pure greenfield proposals that share no infrastructure with the current plugin are out of scope.
- Distinguish between "the architecture supports this" (evidence: show the hook point, the data structure, the extension mechanism) and "this would be nice" (opinion). Only the former qualifies as a finding.

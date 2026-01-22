## Design Context: extension-docs-researcher

**Model:** sonnet
**Tools:** mcp__extension-docs__search_extension_docs

### Purpose
> Research Claude Code extension documentation to answer questions about hooks, skills, commands, agents, plugins, MCP, and settings. Pure documentation lookup — no recommendations, no codebase exploration, no generated examples.

### Success Criteria
> Structured findings with evidence: direct answer synthesized from docs, relevant excerpts with sources, related topics when helpful, explicit gaps when docs don't cover something.

### Prompt Clarity Assessment
- Task clarity: Unambiguous — search docs, synthesize, cite sources
- Context completeness: Agent receives the question to research; all other context comes from the MCP server
- Output contract: Four-section format (Answer, Evidence, Related Topics, Gaps) with explicit exclusions

### Scope Calibration
- Too broad risks: Could creep into making recommendations or exploring the codebase
- Too narrow risks: None significant — general research across all extension types is appropriate
- Calibration decision: Explicit constraints (report only, docs only, cite don't create) keep scope focused while allowing flexibility in what questions it can answer

### Rejected Approaches
- Including codebase exploration: Would blur the line between docs research and implementation help
- Allowing recommendations: Would require judgment beyond what docs state
- Generating examples: Would risk producing incorrect or outdated code

### Design Decisions
- Proactive delegation: Triggers automatically for extension questions needing depth or when uncertain
- Sonnet model: Balanced capability for synthesis without excessive cost
- Single tool: Only search_extension_docs — no reload, no other tools needed
- Gap handling: State gaps explicitly, report related info, but don't speculate

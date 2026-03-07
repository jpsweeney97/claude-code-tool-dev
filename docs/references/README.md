# References Index

**Purpose:** Curated reference docs for skills, patterns, and evaluation.

## Codex MCP

1. `../codex-mcp/README.md`
   - Canonical index for all Codex MCP documentation in this repo.

2. `../codex-mcp/codex-mcp-master-guide.md`
   - Consolidated guide (concepts → first success → build → security → operations).

3. `../codex-mcp/specs/README.md`
   - Normative build specs (server + client/skill).

4. `../codex-mcp/references/codex-mcp-server-beginner-to-expert.md`
   - Deep dive on running/integrating `codex mcp-server` safely and reliably.

## Skills & Patterns

1. `./skills-guide.md`
   - Core patterns and practices for building and evolving skills.
2. `./skill-patterns.md`
   - Reusable pattern catalog for skill behavior and structure.
3. `./The-Complete-Guide-to-Building-Skill-for-Claude.md`
   - Deep dive reference on skill construction and operationalization.

## Evaluation & Quality

1. `./baseline-quality-by-domain.md`
   - Baseline expectations by domain for calibration and comparison.
2. `./task-list-guide.md`
   - Task-list design guidance for structured execution and assessment.
3. `./writing-principles.md`
   - Writing-quality principles used across planning/spec/report artifacts.

## Codex Consultation Protocol

1. `./consultation-contract.md`
   - Normative 16-section contract for Codex consultations. Single source of truth
     for briefing structure, safety pipeline, transport params, continuity state,
     relay obligations, and conformance. Referenced by the `/codex` skill and
     `codex-dialogue` agent via fail-closed stubs.

2. `./consultation-profiles.yaml`
   - Named profiles (`quick-check`, `deep-review`, `adversarial-challenge`,
     `exploratory`, `code-review`) mapping to resolved execution controls.
     Stored separately from the contract for edit-frequency isolation.

3. `./context-injection-contract.md`
   - Complementary protocol: JSON contract between the `codex-dialogue` agent
     and the context injection Python helper (MCP server). Governs mid-conversation
     evidence gathering (process_turn / execute_scout calls).

4. `./cross-model-plugin-operational-handbook.md`
   - Practical operator's guide for the cross-model plugin. Covers architecture,
     `/dialogue` end-to-end flow, context-injection runtime behavior, a worked
     3-turn example, and a file-by-file change map for common modifications.

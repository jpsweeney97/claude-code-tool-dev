# CCDI — Archived

**Status:** Removed (2026-03-24)

CCDI (Claude Code Documentation Intelligence) was a system for injecting Claude Code
documentation into Codex dialogues during cross-model collaboration.

**Why removed:** Empirical testing confirmed that Codex has native access to the
`claude-code-docs` MCP server (`mcp__claude_code_docs__search_docs`) and reliably
searches it without prompting in both `/codex` and `/dialogue` modes. CCDI's content
delivery role was fully obviated.

**Evidence:** Three independent tests (2026-03-24) — two `/codex` consultations and
one `/dialogue` consultation on Claude Code topics — confirmed Codex detects the
domain and searches docs autonomously. See the dialogue consultation thread
`019d2183-2f57-76d3-ae1f-1dd9fb532d9b` for the architectural discussion.

**What's here:**
- `specs/` — CCDI modular spec (10 files, ~1350 lines)
- `2026-03-20-ccdi-design.md` — Original design document
- `2026-03-24-ccdi-inventory-build-design.md` — Build pipeline design (never implemented)
- `plans/` — Remediation and implementation plans

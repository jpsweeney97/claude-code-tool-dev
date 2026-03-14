---
module: skills-appendix
legacy_sections: ["7.5", "7.6", "7.7"]
authority: skills
normative: true
status: active
---

## Skill Directory Layout

```
engram/
├── skills/
│   ├── save/
│   │   └── SKILL.md
│   ├── load/
│   │   └── SKILL.md
│   ├── triage/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── triage-modes.md          # Detailed mode trigger rules
│   ├── task/
│   │   └── SKILL.md
│   ├── remember/
│   │   └── SKILL.md
│   └── promote/
│       ├── SKILL.md
│       └── references/
│           └── target-profiles.md       # Target-type routing rules
└── references/
    ├── mutation-confirmation.md          # Shared confirmation UX contract
    ├── snapshot-schema.md               # Snapshot content schema (save→load)
    └── ref-normalization.md             # Ref object construction rules
```

**Layout rules:**
- Cross-skill contracts go in shared `references/` at plugin level
- Skill-specific reference material goes in skill-local `references/`
- `/task` and `/remember` are single-file skills in v1 (no supporting references)
- `/triage` and `/promote` have skill-local references for mode and target routing rules

## `allowed-tools` and MCP Tool Naming

*Resolved: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`). Plugin name: `engram`, server name: `core`.*

All `allowed-tools` entries use the prefix `mcp__plugin_engram_core__`. This follows the Claude Code plugin naming convention: `mcp__plugin_<plugin-name>_<server-name>__<tool>`. Plugin name is `engram`; server name is `core` (single MCP server).

`allowed-tools` grants auto-approval, not exclusivity. If the prefix is wrong, Claude will still see the tools but will prompt for permission on each call. Getting the prefix right matters for UX, not for access control.

## Open Questions (from dialogue)

1. ~~**`task_get` or `task_query(ids=[])`**~~ — **REOPENED (holistic review).** Added `task_ids[]` to `task_query` and `lesson_ids[]` to `lesson_query` for direct ID lookups. FTS alone cannot resolve task_ids for dependency workflows — UUIDs are not indexed in title/body/tags. `task_ids[]` enables programmatic lookups (skill has task_id from prior query) and the `/task` dependency resolution path. Cross-cutting `query` still not needed in `/task`'s `allowed-tools`.

2. ~~**`lesson_update(retract)` reason field**~~ — **CLOSED (adversarial review #9).** Added `reason_code` (enum: `incorrect`, `obsolete`) and `reason` (freeform) to `lesson_update(retract)` in [tool-surface.md](../contracts/tool-surface.md). Added `retracted_at`, `retraction_code`, `retraction_reason` columns to [ddl.md](../schema/ddl.md). `reinforcement_count` preserved as historical on retraction.

3. **Lesson tag convention for `/triage`** — Should there be a formalized tag convention (e.g., `domain:*`, `type:*`) to improve `/triage` recommendation quality? Defer to implementation.

4. **`/promote` target profiles for non-CLAUDE.md files** — The local-file promotion workflow is designed for CLAUDE.md. Other documentation files (README, handbook) may need different editorial rules. Specify in `target-profiles.md` during implementation.

5. **`query` output field richness** — Whether the cross-cutting `query` tool's `SearchHit` type ([tool-surface.md](../contracts/tool-surface.md#public-result-types)) returns enough detail for all confirmation screens. If not, skills may need to follow up with native subsystem queries for enrichment.

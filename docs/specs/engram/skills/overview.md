---
module: skills-overview
legacy_sections: ["7", "7.1", "7.2"]
authority: skills
normative: true
status: active
---

## Skill Surface

### Skill Roster

| # | Skill | Subsystem Focus | MCP Tools Used | Mutation? |
|---|-------|----------------|----------------|-----------|
| 1 | `/save` | Context | `session_start`, `session_snapshot`, `session_end`, `session_get` | Yes |
| 2 | `/load` | Context + cross-subsystem | `session_list`, `session_get`, `session_start`, `task_query`, `lesson_query` | Yes |
| 3 | `/triage` | Cross-cutting | `task_query`, `session_list`, `lesson_query`, `query` | No (read-only) |
| 4 | `/task` | Work | `session_start`, `task_create`, `task_update`, `task_query` | Yes |
| 5 | `/remember` | Knowledge | `session_start`, `lesson_capture`, `lesson_update`, `lesson_query` | Yes |
| 6 | `/promote` | Knowledge + filesystem | `session_start`, `lesson_query`, `lesson_promote` + Read, Edit | Yes |

### Visibility Model

All 6 skills are visible — descriptions are loaded into context at session start. No skill uses `disable-model-invocation`. Claude can auto-invoke any skill based on conversation context.

**Safety for mutation skills:** The two-stage guard ([skill-orchestration.md](../contracts/skill-orchestration.md#two-stage-guard)) prevents proactive mutation. All mutation skills require explicit user confirmation before user-directed MCP mutation calls. Infrastructure mutations (lazy session bootstrap via `session_start` — [skill-orchestration.md](../contracts/skill-orchestration.md#two-stage-guard)) are exempt from confirmation — they are transparent lifecycle operations, not user-visible state changes. This makes auto-visibility safe despite side effects — the confirmation gate is the control mechanism, not description hiding.

**Description constraints:** Narrow trigger phrases to Engram-scoped phrasing. Avoid generic phrases that over-match (e.g., "save" alone matches too broadly — use "save session state" or "wrap up this session"). Total description budget: 6 skills × ~200 chars = ~1,200 chars, well within the 2% context budget (~20k chars on 1M model).

**Natural-language triggers by skill:**
- `/save` — "wrap this up", "save session", "checkpoint", "end session"
- `/load` — "pick up where I left off", "continue from last session", "load session"
- `/triage` — "what's outstanding", "catch me up", "project status", "triage"
- `/task` — "create a task", "track this", "defer this for later"
- `/remember` — "remember this", "capture this insight", "this is worth noting"
- `/promote` — "promote this to CLAUDE.md", "graduate this lesson"

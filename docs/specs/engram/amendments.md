---
module: amendments
legacy_sections: []
authority: root
normative: false
status: active
---

## Amendment History

| Amendment | Sections Touched | Source |
|-----------|-----------------|--------|
| Codex dialogue #5 | S6 | Schema design |
| Codex deep review #6 | S4, S6, S6.6 | Tool surface + schema revision |
| Codex dialogue #7, #8 | S7 | Skill surface design |
| Adversarial review #9 | S7 | 13 findings applied |
| Evaluative review #16 | S4, S6.6, S7 | Identity/bootstrap/naming |
| Collaborative resolution #17 | S4, S6.6, S7 | Three-layer enforcement, patch semantics |
| Bundle 1 | S4, S5, S6.6, S7 | Identity/bootstrap (34 edits) |
| Bundle 2 | S4, S6.6, S7 | Session lifecycle (19 edits) |
| Bundle 3 | S4, S6.3, S6.6, S7 | terminal_status, blocked_by rename |
| Bundle 4 | S4, S6.5, S6.6, S7 | anchor_hash merge, provenance, sort_by |
| Codex dialogue #19 | S4, S6.6, S7 | session_list state, lesson_update provenance, naming convention |
| Holistic review | S4, S7.7 | task_ids/lesson_ids, Q1 reopened |

## Raw History

Verbatim italic amendment notes as they appear in the original monolith, preserved for detailed edit history.

### S4 — MCP Tool Surface

*Revised based on Codex deep review #6 (thread `019ce54a`). Key changes: session_start requires session_id, session_end is atomic with optional final_content, anchor_hash removed from lesson_capture, lesson_update added, task dependencies writable, Ref objects for provenance, action semantics specified. Further revised: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`) — three-layer enforcement model, `${CLAUDE_SESSION_ID}` identity transport, plugin naming resolved; three-state patch semantics, semantic no-op guard, `loadable_snapshot` nullability, `sessions.updated_at` (internal-only). Bundle 3 — `terminal_status` close parameter, `depends_on[]` → `blocked_by[]` query parameter rename. Bundle 4 — `anchor_hash` merge with `context_conflict`, provenance `target_label` + uniqueness, `sort_by` enum, `relevance_score` semantics. Codex dialogue #19 — `session_list` state filter + `activity_at` ordering, provenance naming convention, `lesson_update` provenance params.*

### S6 — Database Schema

*Revised based on Codex dialogue #5 (thread `019ce52a`) and deep review #6 (thread `019ce54a`). Dialogue #5: dual-table search projection, three-class relationship taxonomy, lessons trimmed, unicode61 tokenizer, JSON CHECKs, ON DELETE policy, bidirectional status/closed_at constraint. Deep review #6: removed blocked from task status, added task_id/lesson_id/description columns, added task_dependencies and search_projection indexes, session_links directionality defined.*

### S6.6 — Design Notes

*Revised based on Codex deep review #6 (thread `019ce54a`). Further revised: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`) — `sessions.updated_at`, final snapshot uniqueness index, `session_get` null handling. Bundle 3 — `terminal_status` close semantics, `reason` binding (server-side validation). Bundle 4 — `anchor_hash` merge semantics, provenance `target_label` + uniqueness, `sort_by`/`relevance_score` mapping. Codex dialogue #19 — `session_list` state filter + `activity_at`, `lesson_update` provenance paths, collection-tool validation.*

### S7 — Skill Surface

*Designed via Codex dialogue #7 (exploratory, thread `019ce590`) and #8 (collaborative, thread `019ce5a8`). Further revised: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`) — lazy session bootstrap, `${CLAUDE_SESSION_ID}` identity transport, `mcp__plugin_engram_core__` prefix, mutation confirmation narrowed. Bundle 3 — `terminal_status` close parameter in `/task` workflow. Bundle 4 — `anchor_hash` merge with `context_conflict` in `/remember` workflow. Codex dialogue #19 — `/load` open-first session listing, `/remember` maintain routing rule.*

### S7.6 — `allowed-tools` and MCP Tool Naming

*Resolved: evaluative review #16 and collaborative resolution #17 (threads `019ce838`, `019ce851`). Plugin name: `engram`, server name: `core`.*

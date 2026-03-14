---
module: skill-orchestration
legacy_sections: ["7.3"]
authority: contracts
normative: true
status: active
---

## Skill Orchestration

#### Two-Stage Guard Architecture {#two-stage-guard}

All skills that call mutation tools use a two-stage guard to prevent proactive mutation:

**Stage 1 — Relevance gate** (skill-specific): A 3-way classifier in the skill body determines whether to execute, clarify, or ignore. This is per-skill judgment — each skill defines its own relevance criteria.

| Classification | Action | Example |
|---------------|--------|---------|
| Execute | Proceed to Stage 2 | User explicitly says "save my session" |
| Clarify | Ask one question | Ambiguous intent — "I'm done" could mean done with task or done with session |
| Ignore | Do nothing, respond normally | Conversation mentions "saving" in an unrelated context |

**Stage 2 — Confirmation** (shared): Uses the `mutation-confirmation.md` contract. The skill presents what will happen and asks for confirmation before any MCP mutation call.

#### Confirmation Severity Model {#confirmation-severity}

Three severity levels determine confirmation UX weight:

| Severity | Gate | Applied To |
|----------|------|-----------|
| **Advisory** | Inline confirmation, proceed by default | Checkpoints (`session_snapshot`) |
| **Durable** | Explicit yes/no before proceeding | Task creation/update, lesson capture |
| **Terminal** | Explicit yes/no with consequences stated | Session close (`session_end`), lesson retraction |

Per-skill severity bindings are specified in each skill's design below.

#### Snapshot Content Schema {#snapshot-content-schema}

The `snapshot-schema.md` contract defines what `/save` produces and `/load` consumes. Content follows the pointer-vs-substance principle:

| Data Type | Treatment | Rationale |
|-----------|-----------|-----------|
| Entities in Engram (tasks, lessons) | Store pointer (entity ID) | Canonical data lives in the database — snapshots reference, not duplicate |
| Working-memory data (conversation insights, unstructured context) | Store substance | Only exists in the session — snapshots preserve it |

Checkpoint and final snapshots use the same schema. They differ in `capture_type` and `focus.state` fields, not structure.

#### Cross-Skill Contracts {#cross-skill-contracts}

Three shared reference documents in the plugin's `references/` directory:

| Contract | Purpose | Producer | Consumer |
|----------|---------|----------|----------|
| `mutation-confirmation.md` | Shared confirmation UX template (advisory/durable/terminal) | All mutation skills | — |
| `snapshot-schema.md` | Snapshot content structure | `/save` | `/load` |
| `ref-normalization.md` | Ref object construction rules (type inference, path normalization, label generation) | All skills that write provenance | — |

**`mutation-confirmation.md` normative content:**
- Three severity levels: advisory (inline, proceed by default), durable (explicit yes/no), terminal (yes/no with consequences stated)
- Each confirmation presents: what will change, which MCP tool will be called, severity level
- User can override downward (skip advisory confirmations) but not upward
- After confirmation, execute the mutation immediately — do not re-confirm
- **Exemption:** Lazy session bootstrap (`session_start` calls per this document) is an infrastructure operation exempt from confirmation — it runs between confirmation and domain mutation without user interaction
- On failure, follow the single-mutation failure pattern (this document)

**`snapshot-schema.md` normative content:**
- Required fields: `capture_type` (enum: `checkpoint`, `final`), `captured_at` (ISO 8601), `session_id`
- Content block: `focus` object with `goal`, `state` (what the user was doing), `next_steps` (what remains)
- Entity references: `task_ids[]`, `lesson_ids[]` — pointers to Engram entities (not inline substance)
- Working-memory block: `conversation_insights` (freeform), `decisions` (freeform) — substance that only exists in the session
- Checkpoint and final snapshots use the same schema; they differ in `capture_type` and `focus.state` scope

**`ref-normalization.md` normative content:**
- `type` inference: local paths → `file`, URLs → `url`, GitHub patterns → `github_issue`/`github_pr`
- Path normalization: resolve relative paths to absolute, strip trailing slashes, collapse `//`
- Label generation: if not provided, derive from ref (filename for files, `#N` for issues/PRs, domain for URLs)
- Dedup key: `(relation_type, target_type, target_ref)` — normalized before comparison
- Skills constructing Ref objects apply these rules before passing to MCP tools

Skills interoperate through the MCP server (entity IDs, Ref objects), not through direct skill-to-skill protocols.

#### Single-Mutation Failure Pattern {#single-mutation-failure}

When a confirmed single mutation fails, all mutation skills follow this shared pattern:

**Determinate failure** (server returns `reason_code` in entity envelope):
- Surface the `reason_code` and a natural-language interpretation
- State that the mutation was not applied (guaranteed by the atomic rejection invariant — [tool-surface.md](tool-surface.md#action-semantics))
- Do not silently retry
- Offer the user: retry, revise parameters, or abandon

**Indeterminate failure** (timeout, transport error, no server response):
- State that completion is unknown — the mutation may or may not have been applied
- Verify state via a read tool (e.g., `session_get`, `task_query`, `lesson_query`) before any retry
- Present verified state to the user before proceeding

Multi-step non-atomic workflows (`/promote` local-file promotion, `/task` "create task that blocks X") have additional per-skill recovery procedures specified in their designs below.

#### Server Unavailable Escalation {#server-unavailable}

*Added based on Codex consultation #25 (thread `019ced19`). Resolves open risk #2 from decisions.md.*

When an Engram MCP tool call fails with transport-level symptoms (connection closed, tool unavailable, timeout) **and** a follow-up Engram read tool also fails, the skill must treat Engram as unavailable for the remainder of that workflow:

1. Surface explicitly: "Engram is unavailable — I can't verify or persist Engram state until the MCP connection is restored."
2. Stop the current Engram workflow — do not proceed to further MCP calls
3. Direct the user to check `/mcp` for server status or restart Claude Code
4. Do not silently degrade to "continue without persistence" — Engram must never pretend to persist state when it can't

This rule applies to all 6 skills (mutation and read-only). It complements the single-mutation failure pattern: that pattern covers individual call failures where verification reads succeed; this rule covers total server unavailability where verification reads also fail.

**Detection heuristic:** A single transport failure is not conclusive — it may be a transient error. The "follow-up read also fails" check is the discriminator. For mutation skills, the lazy bootstrap `session_start` call serves as the initial probe; if it fails with transport symptoms, attempt one read (e.g., `session_list(limit=1)`) before escalating. For read-only skills (e.g., `/triage`), the first query failure plus one retry failure triggers escalation.

**Recovery is platform-dependent.** Engram does not implement auto-restart or health endpoints. If Claude Code restores the MCP server connection mid-session, skills resume normal operation on the next invocation.

#### Lazy Session Bootstrap {#lazy-session-bootstrap}

*Added based on collaborative resolution #17 (thread `019ce851`). Resolves session identity transport and bootstrap ownership.*

Mutation skills (except `/load`) ensure a session exists before their first MCP mutation call. This is an infrastructure operation — no user confirmation required.

**Mechanism:**
1. Each mutation skill's SKILL.md contains a session identity declaration: `**Session identity:** ${CLAUDE_SESSION_ID}`. Claude Code substitutes the session UUID at load time.
2. After user confirms the domain mutation (Stage 2 of the two-stage guard) but before the first MCP mutation call, the skill calls `session_start(session_id=<session_id>)`.
3. `session_start` is idempotent ([tool-surface.md](tool-surface.md#action-semantics)): if the session already exists, the call is a no-op or enrichment (field-specific patch semantics apply); if not, it creates the session row with minimal metadata (goal inferred from conversation context).
4. The `details.created` field in the entity envelope response indicates whether a new session was created or an existing one was enriched.
5. If `session_start` fails (e.g., session is closed), surface the error and stop — do not proceed to the domain mutation.

**Key properties:**
- **No user confirmation** — session bootstrap is infrastructure, not a user-directed mutation. The two-stage guard applies to the subsequent domain mutation.
- **Idempotent** — multiple skills bootstrapping in the same session converge to the same session row.
- **Skills carry identity** — `${CLAUDE_SESSION_ID}` provides the session UUID without hook injection. The `PreToolUse` hook validates that the skill-provided `session_id` matches the Claude Code session (stateless cross-check).

**Exception — `/load`:** `/load`'s `session_start` call serves dual purpose: bootstrap (creating the session row if needed) AND continuation (setting `continued_from_session_ids`). The user's session selection is the implicit confirmation. `/load` does not use the generic lazy bootstrap pattern — its `session_start` call is part of the domain workflow, not a separate infrastructure step.

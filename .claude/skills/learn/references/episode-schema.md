# Episode Schema Reference

Authoritative field definitions for Phase 1a structured episodes. SKILL.md references this file for enum tables, inference guidance, and bias documentation.

**Schema version:** 1
**Validator:** `scripts/validate_episode.py`
**Storage:** `docs/learnings/episodes/EP-NNNN.md`

## Schema

```yaml
---
id: EP-NNNN              # Auto-incremented (glob highest existing + 1, zero-pad to 4)
date: YYYY-MM-DD          # Date of episode creation
title: string             # 1-line summary, max ~80 chars
source_type: dialogue|solo # Controls conditional body sections
domain: string            # Free-form: architecture, security, performance, etc.
task_type: <enum>         # See task_type table below
languages: []             # Optional: [python, typescript, ...]
frameworks: []            # Optional: [playwright, django, ...]
keywords: [list]          # Free-form searchable tags, 1-5 entries
decision: applied|rejected|deferred
decided_by: user          # Phase 1a: always "user"
safety: false             # true if touches auth/credentials/secrets
schema_version: 1         # Exact match required
---
```

### Required Fields

All fields above are required except `languages` and `frameworks` (default to `[]`).

### ID Generation

1. Glob `docs/learnings/episodes/EP-*.md`
2. Parse highest existing number (or 0 if none)
3. Increment by 1
4. Zero-pad to 4 digits: `EP-0001`, `EP-0002`, ...

### Conditional Body Sections

| source_type | Required sections | Forbidden sections |
|-------------|-------------------|--------------------|
| `dialogue` | Summary, Claude Position, Codex Position, Evidence, Resolution* | — |
| `solo` | Summary, Evidence, Resolution* | Claude Position, Codex Position |

*Resolution required when `decision` is `applied` or `rejected`. Optional when `deferred`.

### Immutability

`decision` is the only mutable field (`deferred` → `applied`/`rejected`). All other fields are immutable after creation. Decision updates are manual file edits in Phase 1a.

## task_type Enum (10 values)

| Value | Description |
|-------|-------------|
| `code-change` | Writing or modifying code |
| `debugging` | Finding and fixing bugs |
| `testing` | Writing or running tests |
| `code-review` | Reviewing code or PRs |
| `design` | Architectural or system design |
| `planning` | Project planning, scoping, estimation |
| `research` | Exploring, reading docs, investigating |
| `operations` | CI/CD, deployment, infrastructure |
| `writing` | Documentation, specs, proposals |
| `decision` | Making or recording a choice between options |

## Inference Guidance

### Rules (normative — SKILL.md references these)

1. **Signals are suggestive, not deterministic.** Never auto-assign a value without user confirmation.
2. **Suggestion threshold:** ≥1 strong signal OR ≥2 weak signals from different families.
   - Strong signal: direct task intent or object (e.g., "review PR #42", "deploy rollback", "wrote failing test").
   - Weak signal: indirect contextual hint (e.g., "quality pass", "investigate", "looks good").
3. **Low confidence:** sparse, conflicting, or split signals → present options via AskUserQuestion. Do not guess.
4. **User override:** explicit user statement always overrides inference.

### Signal Table

| Value | Signal families (non-exhaustive) | Bias watch |
|-------|----------------------------------|------------|
| `code-change` | "wrote", "implemented", "refactored", "added function" | B1 (compression with debugging) |
| `debugging` | "root cause", "fixed bug", "stack trace", "bisected" | B1 (compression with code-change) |
| `testing` | "test suite", "coverage", "assertion", "TDD" | B1 (compression with code-change) |
| `code-review` | "PR review", "LGTM", "requested changes", "approved" | B5 (over-attribution if Codex involved) |
| `design` | "architecture", "trade-offs", "component boundaries" | B5 (over-attribution to dialogue) |
| `planning` | "roadmap", "sprint", "estimate", "scope", "phase" | — |
| `research` | "explored", "investigated", "docs say", "RFC" | B4 (recency — last doc read ≠ session topic) |
| `operations` | "deployed", "CI pipeline", "infrastructure", "Docker" | — |
| `writing` | "spec", "documentation", "proposal", "wrote up" | B1 (compression with design) |
| `decision` | "chose between", "decided", "trade-off accepted" | B2 (outcome optimism — toward applied) |
| `dialogue` (source_type) | Codex disagreement, cross-model resolution, contested claim | B5 (any /codex usage ≠ dialogue) |
| `solo` (source_type) | No Codex involvement in the insight | — |
| `applied` (decision) | "we went with", "implemented the fix", positive evidence | B2 (optimism), B6 (deferred underproduction) |
| `rejected` (decision) | "ruled out", "won't do", no "do later" language | B2 (optimism) |
| `deferred` (decision) | "revisit later", "postponed", "parking this" | B6 (underproduction — models avoid deferred) |

### Negative-Space Guards on `decision`

- `applied`: requires positive evidence AND no postponement language
- `rejected`: requires no "do later" or "revisit" markers
- `deferred`: requires explicit postpone/revisit marker
- Inconclusive (no clear signal, mixed markers): → AskUserQuestion

## Inference Biases

Six LLM-as-operator biases to watch for when generating episodes:

| # | Bias | Description | Mitigation |
|---|------|-------------|------------|
| B1 | Label compression | Multi-part sessions forced to one `task_type` | Multi-signal match → present options via AskUserQuestion |
| B2 | Outcome optimism | `applied` over-assigned vs `deferred` | Present `decision` for explicit user confirmation with negative-space guards |
| B3 | Authority leakage | Codex recommendation treated as user decision | `decided_by` is always `user` in Phase 1a |
| B4 | Recency artifact | `languages`/`frameworks` from last file, not session scope | Scan full conversation, not just recent context |
| B5 | Dialogue over-attribution | Any `/codex` usage triggers `dialogue` | `source_type` based on whether insight came from disagreement, not tool presence |
| B6 | Deferred underproduction | Models avoid `deferred` (feels incomplete) | Explicitly present `deferred` as valid option |

## Examples

### Solo Episode

```yaml
---
id: EP-0001
date: 2026-02-23
title: Heredoc substitution unreliable in zsh Bash tool
source_type: solo
domain: workflow
task_type: debugging
languages: [bash]
frameworks: []
keywords: [zsh, heredoc, bash-tool]
decision: applied
decided_by: user
safety: false
schema_version: 1
---

## Summary
The `$(cat <<'EOF' ... EOF)` heredoc pattern produces zsh temp file errors in Claude Code's Bash tool.

## Resolution
Switched to inline multiline strings for git commit messages and gh pr create bodies.

## Evidence
Error observed: `(eval):1: can't create temp file for here document`. Commands still succeeded but behavior is unreliable. Documented in CLAUDE.md as a known issue.
```

### Dialogue Episode

```yaml
---
id: EP-0002
date: 2026-02-23
title: Dual-version validator windows over-engineered for single-developer scale
source_type: dialogue
domain: architecture
task_type: design
languages: [python]
frameworks: []
keywords: [schema-migration, scale, codex]
decision: applied
decided_by: user
safety: false
schema_version: 1
---

## Summary
Schema version transitions should use atomic cutover, not dual-version acceptance windows.

## Claude Position
Dual-version validator modes (strict/transition) are over-engineered for single-developer scale with 5-20 episode files. Atomic cutover with migration script is sufficient.

## Codex Position
Initially proposed flag-based validator modes for backward compatibility during transitions. Conceded after scale argument — operational context (single developer, small file volume) doesn't justify the complexity.

## Resolution
Adopted atomic cutover: migration script (idempotent, --dry-run), one-pass migration, then switch validator to strict v2-only.

## Evidence
Planning dialogue converged in 5 turns. validate_consultation_contract.py has no version-range logic (validates exact structural invariants), confirming the pattern.
```

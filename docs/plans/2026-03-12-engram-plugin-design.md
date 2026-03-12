# Engram Plugin Design

**Date:** 2026-03-12
**Status:** Draft
**Scope:** Consolidate ticket plugin, handoff plugin, `/learn` skill, and `/promote` skill into a single plugin called `engram`.

## Problem Statement

Four components form the project's knowledge lifecycle — ticket management, session handoffs, insight capture, and knowledge promotion — but are deployed as separate packages with overlapping boundaries:

- Handoff's `/defer` crosses into ticket via a runtime path hack (`$(realpath "${CLAUDE_PLUGIN_ROOT}/../ticket/scripts/...")`)
- Handoff's `/distill` writes to the same learnings file that `/learn` targets
- Handoff duplicates ticket's YAML parser (`ticket_parsing.py`) with diverging copies
- Two separate path resolution modules (`ticket_paths.py`, `project_paths.py`) solve the same problem differently
- Deployment requires managing 3 packages independently (ticket, handoff, learn/promote as repo-level skills)

This creates: fragile cross-plugin boundaries, duplicated code, fragmented search, no unified provenance, and deployment friction.

## Design Decisions

Decisions validated through 3 Codex consultations (1 direct, 2 multi-turn dialogues — 13 total turns, all converged).

| # | Decision | Confidence | Source |
|---|----------|------------|--------|
| D1 | Hybrid architecture — unified plugin, federated subsystems | High | Codex consultation #1 |
| D2 | Storage: A+D — keep location split, add thin read-only federation | High | Codex dialogue #1 (6 turns, comparative) |
| D3 | A-with-shims — `scripts/` as runtime entrypoints, `engram/` as real Python package | High | Codex dialogue #2 (6 turns, planning/comparative) |
| D4 | Keep existing skill names — consolidation invisible to users | High | User decision |
| D5 | Unified search as v1 capability; provenance graph, dashboard, cross-entity triage as future | High | User decision |
| D6 | No persistent index in v1 — lazy fan-out from existing metadata | High | Codex dialogue #1 |
| D7 | Two parsers stay separate (handoff frontmatter vs ticket fenced-YAML) | High | Codex dialogue #2 |
| D8 | Migration order: core → learning → ticket engine slice → handoff → parser consolidation → rest of ticket | Medium | Codex dialogue #2 |
| D9 | Adapter admission rule: user-facing, authoritative, stable schema, 2+ consumers | Medium | Codex dialogue #1 (emerged) |
| D10 | project_id hash cascade: repo:sha256(remote) → path:sha256(realpath) → dir:sha256(cwd) | Medium | Codex dialogue #1 |

## Architecture

### Package Structure

Single plugin at `packages/plugins/engram/`. The A-with-shims pattern: thin `scripts/` entrypoints delegate to `engram.*` modules. This satisfies the Claude Code plugin runtime convention (`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py`) while eliminating the `scripts.*` namespace collision.

```
packages/plugins/engram/
├── .claude-plugin/
│   └── plugin.json              # name + version only; rest auto-discovered
├── pyproject.toml               # package: "engram-plugin", deps: pyyaml>=6.0
├── scripts/                     # thin runtime shims (Claude Code convention)
│   ├── ticket_engine_user.py    # → from engram.ticket.engine_user import main
│   ├── ticket_engine_agent.py   # → from engram.ticket.engine_agent import main
│   ├── ticket_read.py           # → from engram.ticket.read import main
│   ├── ticket_triage.py         # → from engram.ticket.triage import main
│   ├── ticket_audit.py          # → from engram.ticket.audit import main
│   ├── distill.py               # → from engram.handoff.distill import main
│   ├── search.py                # → from engram.handoff.search import main
│   ├── cleanup.py               # → from engram.handoff.cleanup import main
│   ├── quality_check.py         # → from engram.handoff.quality_check import main
│   └── defer.py                 # → from engram.handoff.defer import main
├── engram/                      # real Python package
│   ├── __init__.py
│   ├── core/                    # shared infrastructure
│   │   ├── __init__.py
│   │   ├── paths.py             # unified path resolution
│   │   ├── search.py            # cross-entity fan-out search
│   │   ├── provenance.py        # relation model (v2, stubbed)
│   │   ├── metadata.py          # shared metadata conventions
│   │   └── adapters.py          # adapter base class + registry
│   ├── ticket/                  # migrated from ticket plugin (15 modules)
│   │   ├── __init__.py
│   │   ├── engine_core.py
│   │   ├── engine_runner.py
│   │   ├── engine_user.py
│   │   ├── engine_agent.py
│   │   ├── parse.py             # canonical ticket parser (fenced YAML)
│   │   ├── render.py
│   │   ├── validate.py
│   │   ├── id.py
│   │   ├── paths.py             # ticket-specific path logic (delegates to core)
│   │   ├── stage_models.py
│   │   ├── triage.py
│   │   ├── audit.py
│   │   ├── dedup.py
│   │   ├── trust.py
│   │   ├── envelope.py
│   │   ├── guard.py             # PreToolUse hook logic
│   │   └── read.py
│   ├── handoff/                 # migrated from handoff plugin (10 modules)
│   │   ├── __init__.py
│   │   ├── parsing.py           # handoff frontmatter parser (kept separate from ticket)
│   │   ├── distill.py
│   │   ├── search.py
│   │   ├── cleanup.py
│   │   ├── quality_check.py
│   │   ├── triage.py            # imports engram.ticket.parse (not duplicate)
│   │   ├── defer.py
│   │   ├── provenance.py
│   │   └── project_paths.py     # handoff-specific paths (delegates to core)
│   └── learning/                # NEW — backing for /learn, /promote
│       ├── __init__.py
│       ├── capture.py           # /learn backing (read/write learnings.md)
│       ├── promote.py           # /promote backing (maturity scoring, CLAUDE.md edits)
│       └── store.py             # learnings.md read/write/query
├── skills/                      # all 11 skills (auto-discovered)
│   ├── save/SKILL.md
│   ├── quicksave/SKILL.md
│   ├── load/SKILL.md
│   ├── defer/SKILL.md           # no more cross-plugin path hack
│   ├── triage/SKILL.md
│   ├── distill/SKILL.md
│   ├── search/SKILL.md          # gains --all flag for cross-entity search
│   ├── ticket/SKILL.md
│   ├── ticket-triage/SKILL.md
│   ├── learn/SKILL.md
│   └── promote/SKILL.md
├── hooks/
│   ├── hooks.json               # all hooks in one file (auto-discovered)
│   ├── ticket_engine_guard.py   # PreToolUse hook (→ engram.ticket.guard)
│   ├── cleanup.py               # SessionStart hook (→ engram.handoff.cleanup)
│   └── quality_check.py         # PostToolUse hook (→ engram.handoff.quality_check)
├── references/
│   ├── engram-contract.md       # shared metadata + adapter admission rules
│   ├── ticket-contract.md       # migrated from ticket plugin
│   ├── handoff-contract.md      # migrated from handoff plugin
│   └── format-reference.md      # migrated from handoff plugin
└── tests/
    ├── conftest.py              # shared fixtures (tmp dirs, sample data)
    ├── test_core/               # engram.core tests
    ├── test_ticket/             # ~659 tests, migrated
    ├── test_handoff/            # ~340 tests, migrated
    └── test_learning/           # NEW tests
```

### Shim Pattern

Each `scripts/<name>.py` is a thin runtime entrypoint:

```python
#!/usr/bin/env python3
"""Runtime entrypoint — delegates to engram package."""
import sys
from pathlib import Path

# sys.path shim for direct invocation. If engram-plugin is installed as a
# proper package (uv install), this is redundant but harmless.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engram.ticket.engine_user import main

if __name__ == "__main__":
    main()
```

Skills invoke shims via Bash: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py <args>`. Hooks reference scripts in `hooks/`: `"command": "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.py"`. Hook scripts use the same shim pattern (thin entrypoint → `engram.*` import).

### hooks.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ticket_engine_guard.py",
            "timeout": 10
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/cleanup.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/quality_check.py"
          }
        ]
      }
    ]
  }
}
```

**Command format:** The guard uses shebang-based invocation (no `python3` prefix) matching the existing ticket hook convention. Cleanup and quality_check use `python3` prefix matching the existing handoff hook convention. During migration, preserve each hook's existing invocation format. All hook scripts must have `#!/usr/bin/env python3` shebangs regardless.

## Storage Federation

Data stays where it semantically belongs. Engram provides cross-location query through a thin federation layer.

### Storage Locations (unchanged)

| Entity | Location | Scope | Retention | Version Controlled |
|--------|----------|-------|-----------|-------------------|
| Tickets | `docs/tickets/` | Project-local | Permanent | Yes |
| Ticket audit | `docs/tickets/.audit/` | Project-local | Permanent | Yes |
| Closed tickets | `docs/tickets/closed-tickets/` | Project-local | Permanent | Yes |
| Handoffs | `~/.claude/handoffs/<project>/` | User-global | 30 days active | No |
| Handoff archive | `~/.claude/handoffs/<project>/.archive/` | User-global | 90 days | No |
| Session state | `~/.claude/.session-state/handoff-<UUID>` | User-global | 24 hours | No |
| Learnings | `docs/learnings/learnings.md` | Project-local | Until promoted | Yes |
| Promoted | `.claude/CLAUDE.md` | Project-local | Permanent | Yes |

### Federation Layer

Four operations, no persistence:

1. **Resolve** — given an entity kind and ID, return the absolute path to its source file
2. **Fan-out** — distribute a query to all (or filtered) adapters in parallel
3. **Normalize** — convert adapter-specific results to a common `SearchResult` envelope
4. **Derive** — compute provenance links from existing metadata (session_id joins, defer-meta, distill-meta, promote-meta)

### Adapter Model

```python
class Adapter:
    """Base interface for engram federation."""
    kind: str                    # "ticket", "handoff", "learning", "promoted"
    authority_path: Path         # root directory for this adapter's data

    def search(self, query: str) -> list[dict]:
        """Search this adapter's data. Returns adapter-native results."""
        ...

    def resolve(self, entity_id: str) -> Path | None:
        """Resolve an entity ID to its source file path."""
        ...
```

Four concrete adapters:

| Adapter | Authority Module | Data Source | Notes |
|---------|-----------------|-------------|-------|
| `TicketAdapter` | `engram.ticket.parse` | `docs/tickets/` | Respects path-traversal guard |
| `HandoffAdapter` | `engram.handoff.parsing` | `~/.claude/handoffs/<project>/` | Searches active + archive |
| `LearningAdapter` | `engram.learning.store` | `docs/learnings/learnings.md` | Section-aware grep |
| `PromotionAdapter` | Read-only | `.claude/CLAUDE.md` | Grep only, no mutation |

**Adapter admission rule:** A new adapter must be (1) user-facing, (2) authoritative over its data, (3) backed by a stable schema, and (4) consumed by 2+ skills. This prevents the federation layer from growing unbounded.

### Provenance Model (v2, stubbed in v1)

Four relation states:

| State | Meaning | Example |
|-------|---------|---------|
| `resolved` | Both endpoints exist and are reachable | Ticket T-001 → Handoff 2026-03-12_session.md |
| `dangling` | Source exists but target was pruned (handoff TTL) | Ticket T-001 → (archived handoff expired) |
| `unjoinable` | Source has no session_id or join key | Ticket from PR review (no handoff session) |
| `unknown` | Not yet evaluated | Default for unprocessed relations |

Tombstones are emitted by handoff cleanup (the subsystem that prunes), not by engram. Engram reads tombstones to set `dangling` state.

### project_id

Hash cascade for stable cross-location identity:

1. `repo:sha256(normalized-remote-url)` — stable across clones, renames
2. `path:sha256(realpath)` — fallback for repos without remotes
3. `dir:sha256(cwd)` — last resort for non-git directories

Legacy handoffs with basename-only project names are not retroactively repaired. New handoffs use `project_id`.

## Unified Search (v1)

### API

```python
# engram/core/search.py
def search(
    query: str,
    *,
    kinds: list[str] | None = None,
    limit: int = 50,
) -> list[SearchResult]:
    """Fan-out search across all registered adapters.

    Args:
        query: Literal string match (v1). Future: regex support.
        kinds: Filter to entity types. None = all.
        limit: Max results per adapter.

    Returns:
        SearchResult list sorted by date (most recent first).
    """
```

### SearchResult

```python
@dataclass
class SearchResult:
    kind: str          # "ticket", "handoff", "learning", "promoted"
    id: str            # entity ID (ticket ID, handoff filename, learning heading)
    title: str         # summary/title
    snippet: str       # matching content excerpt (max 200 chars)
    path: Path         # absolute path to source file
    date: datetime     # creation or last modified (date-only sources promoted to midnight UTC)
    metadata: dict     # adapter-specific (status, tags, retention_class, etc.)
```

### Skill Integration

The `/search` skill gains cross-entity capability:

```
/search authentication           # handoffs only (backward compat default)
/search --all authentication     # all entity types
/search --kind ticket auth       # tickets only
/search --kind learning,ticket X # multiple kinds
```

### v1 Scope

- Literal string matching only (no ranking, no fuzzy)
- Recency sort (newest first)
- No persistent index — live fan-out on every query
- No provenance links in results (future v2)

### Future Capabilities (not in v1)

| Capability | Description | Depends On |
|------------|-------------|------------|
| Provenance graph | "Show lineage of this ticket" — handoff→ticket→learning→CLAUDE.md | `engram.core.provenance` (v2) |
| Lifecycle dashboard | Project knowledge health metrics | All adapters + provenance |
| Cross-entity triage | Upgraded `/triage` correlating all entity types | Unified search + provenance |

## Engram Core Details

### paths.py

Consolidates `ticket_paths.py` (ancestor walk) and `project_paths.py` (git subprocess):

```python
def discover_project_root() -> Path | None:
    """Walk ancestors for .git or .claude markers. Returns None if not found."""

def resolve_tickets_dir(project_root: Path, tickets_dir: str = "docs/tickets") -> Path:
    """Resolve tickets directory with traversal guard. Raises if outside project root."""

def resolve_handoffs_dir(project_root: Path) -> Path:
    """Return ~/.claude/handoffs/<project_name>/ using basename of project_root.
    Future: use project_id for new handoffs; legacy basename lookup as fallback."""

def resolve_learnings_path(project_root: Path) -> Path:
    """Return docs/learnings/learnings.md relative to project root."""

def compute_project_id(project_root: Path) -> str:
    """Hash cascade: repo remote → realpath → cwd."""
```

Subsystem-specific modules (`engram/ticket/paths.py`, `engram/handoff/project_paths.py`) delegate to core for root discovery but retain subsystem-specific logic (ticket's traversal guard, handoff's archive dir layout).

### Parser Strategy

Two parsers remain separate — they parse genuinely different grammars:

| Parser | Module | Grammar | Dependency |
|--------|--------|---------|------------|
| Handoff frontmatter | `engram.handoff.parsing` | YAML frontmatter (custom, no PyYAML) + section headers | None |
| Ticket fenced YAML | `engram.ticket.parse` | Fenced YAML block + schema validation | PyYAML |

**Migration cleanup:** Handoff's duplicate `ticket_parsing.py` (30 tests) is deleted. `engram.handoff.triage` imports `engram.ticket.parse` directly — single source of truth.

## Migration Plan

Six phases, each an independently reviewable and revertible PR.

### Phase 1: Scaffold

**Create the empty plugin structure.**

- Create `packages/plugins/engram/` with:
  - `.claude-plugin/plugin.json` (name: "engram", version: "0.1.0")
  - `pyproject.toml` (package: "engram-plugin", deps: pyyaml>=6.0, pytest>=8.0)
  - Empty `engram/` package with `__init__.py` files for core/, ticket/, handoff/, learning/
  - Empty `scripts/`, `skills/`, `hooks/`, `references/`, `tests/` directories
- Add `packages/plugins/engram` to root `pyproject.toml` workspace members
- Verify: `uv run --package engram-plugin pytest` runs (0 tests, 0 errors)
- Test marketplace install of the empty plugin to validate packaging before migrating code

**Tests affected:** 0
**Risk:** None

### Phase 2: Core + Learning

**Build the shared infrastructure and the first subsystem.**

- Implement `engram/core/paths.py` — unified path resolution
- Implement `engram/core/adapters.py` — adapter base class
- Implement `engram/core/search.py` — fan-out search with LearningAdapter
- Implement `engram/learning/store.py` — learnings.md read/write/query
- Implement `engram/learning/capture.py` — /learn Python backing
- Implement `engram/learning/promote.py` — /promote Python backing
- Migrate `/learn` and `/promote` skills from `.claude/skills/` into `engram/skills/`
- Write tests for all new code

**Tests affected:** 0 existing, ~100-150 new
**Risk:** Low — entirely greenfield. Learning adapter is the proving ground for the core API.

### Phase 3: Ticket Engine Slice

**Eliminate the /defer cross-plugin runtime hop.**

- Move `ticket_engine_user.py`, `ticket_engine_runner.py`, `ticket_engine_core.py`, and their direct dependencies (`ticket_paths.py`, `ticket_stage_models.py`, `ticket_trust.py`, `ticket_envelope.py`) into `engram/ticket/`
- Move `ticket_engine_guard.py` into `engram/ticket/guard.py` — the guard validates engine subcommands and injects trust triples, so it logically belongs with the engine modules it protects
- Create thin shims in `scripts/` for skill entrypoints
- Create thin shim in `hooks/` for the guard hook
- Update `/defer` skill to reference `${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_user.py` (co-located, no path hack)
- Apply codemod with ticket rename mapping table for moved files
- Update tests for moved modules

**Tests affected:** ~200 (engine entrypoint + integration tests)
**Risk:** Medium — first real migration. The engine core is the most interconnected module.

### Phase 4: Handoff

**Move all handoff code and eliminate the duplicate parser.**

- Move all handoff scripts into `engram/handoff/`
- Delete handoff's duplicate `ticket_parsing.py` — update `engram.handoff.triage` to import `engram.ticket.parse`
- Create thin shims in `scripts/` for all handoff entrypoints
- Apply codemod with handoff mapping table (most are `from scripts.X` → `from engram.handoff.X`; `triage.py` also needs `from scripts.ticket_parsing` → `from engram.ticket.parse`)
- Migrate all 7 handoff skills into `engram/skills/`
- Migrate handoff hooks into `engram/hooks/hooks.json`
- Migrate handoff references into `engram/references/`
- Delete 30 redundant `test_ticket_parsing.py` tests from handoff
- Update remaining ~310 handoff tests

**Tests affected:** ~340 existing (310 migrated, 30 deleted)
**Risk:** Medium — largest single module move, but handoff modules have no cross-package imports.

### Phase 5: Rest of Ticket

**Complete the ticket migration.**

- Move remaining ticket modules into `engram/ticket/` (parse, render, validate, id, triage, audit, dedup, read)
- Create remaining thin shims in `scripts/`
- Apply codemod with ticket rename mapping table for remaining files
- Migrate ticket skills into `engram/skills/`
- Merge ticket hook config into `engram/hooks/hooks.json` (guard script already moved in P3)
- Migrate ticket references into `engram/references/`
- Update ~459 remaining ticket tests (659 total minus ~200 moved in P3)

**Tests affected:** ~459 existing
**Risk:** Medium — largest test count, but mechanical codemod.

### Phase 6: Cleanup

**Remove old packages and update project config.**

- Remove `packages/plugins/ticket/` directory (including `.claude-plugin/`)
- Remove `packages/plugins/handoff/` directory
- Remove `.claude/skills/learn/` and `.claude/skills/promote/`
- Verify old plugin registrations are removed from marketplace/cache
- Update root `pyproject.toml` workspace members (remove ticket, handoff; engram already added in P1)
- Update `.claude/CLAUDE.md` — package table, directory structure, deployment docs
- Update `CHANGELOG.md`
- Verify: `uv run --package engram-plugin pytest` passes all tests

**Tests affected:** 0 (all moved in prior phases)
**Risk:** Low — deletion only. Old packages are inert after P5.

### Codemod Details

Verified reference count: **285 `from scripts.` import statements across 50 files** (157 in ticket, 122 in handoff, 6 using `import scripts.`).

**Module renames:** Ticket modules drop the `ticket_` prefix inside `engram/ticket/`. A simple `sed` is insufficient — use a mapping table:

| Old import | New import |
|-----------|-----------|
| `from scripts.ticket_engine_core` | `from engram.ticket.engine_core` |
| `from scripts.ticket_engine_runner` | `from engram.ticket.engine_runner` |
| `from scripts.ticket_engine_user` | `from engram.ticket.engine_user` |
| `from scripts.ticket_engine_agent` | `from engram.ticket.engine_agent` |
| `from scripts.ticket_paths` | `from engram.ticket.paths` |
| `from scripts.ticket_parse` | `from engram.ticket.parse` |
| `from scripts.ticket_render` | `from engram.ticket.render` |
| `from scripts.ticket_validate` | `from engram.ticket.validate` |
| `from scripts.ticket_id` | `from engram.ticket.id` |
| `from scripts.ticket_stage_models` | `from engram.ticket.stage_models` |
| `from scripts.ticket_triage` | `from engram.ticket.triage` |
| `from scripts.ticket_audit` | `from engram.ticket.audit` |
| `from scripts.ticket_dedup` | `from engram.ticket.dedup` |
| `from scripts.ticket_trust` | `from engram.ticket.trust` |
| `from scripts.ticket_envelope` | `from engram.ticket.envelope` |
| `from scripts.ticket_read` | `from engram.ticket.read` |

Handoff modules keep their names (no prefix to strip):

| Old import | New import |
|-----------|-----------|
| `from scripts.distill` | `from engram.handoff.distill` |
| `from scripts.search` | `from engram.handoff.search` |
| `from scripts.cleanup` | `from engram.handoff.cleanup` |
| `from scripts.handoff_parsing` | `from engram.handoff.parsing` |
| `from scripts.project_paths` | `from engram.handoff.project_paths` |
| `from scripts.provenance` | `from engram.handoff.provenance` |
| `from scripts.triage` | `from engram.handoff.triage` |
| `from scripts.quality_check` | `from engram.handoff.quality_check` |
| `from scripts.defer` | `from engram.handoff.defer` |
| `from scripts.ticket_parsing` | **deleted** — use `from engram.ticket.parse` |

Per-phase strategy:
- P3: Manual — ~15 files in the engine slice, apply ticket rename mapping
- P4: Script with handoff mapping table + manual review for cross-subsystem imports
- P5: Script with ticket rename mapping table + manual review

A Python codemod script (using the mapping tables above) is preferred over `sed` to handle the rename correctly.

Files importing from multiple subsystems (need manual attention):
- `engram/handoff/triage.py` — imports from both `engram.handoff.*` and `engram.ticket.parse`
- `engram/handoff/defer.py` — invokes ticket engine

### Migration Principle

> Co-locate by plugin, unify by ownership, abstract only after duplication survives the move.

Do not extract shared utilities prematurely. Move code first, observe actual duplication in the new location, then extract only what has 2+ genuine consumers.

## Verified Against Documentation

Architecture validated against official Claude Code docs (2026-03-12):

| Element | Docs Source | Status |
|---------|-------------|--------|
| Plugin auto-discovery of skills/, hooks/ | `plugins-reference#plugin-directory-structure` | Confirmed |
| plugin.json minimal (name only required) | `plugins-reference#plugin-manifest-schema` | Confirmed |
| `${CLAUDE_PLUGIN_ROOT}` in hook configs | `plugins-reference#plugin-manifest-schema` | Confirmed |
| `${CLAUDE_PLUGIN_ROOT}` as shell env var in Bash | Proven by existing ticket/handoff plugins | Confirmed |
| scripts/ at plugin root | `plugins-reference#plugin-directory-structure` | Confirmed |
| SessionStart command-only hooks | `hooks#prompt-based-hooks` | Confirmed |
| hooks.json multi-event format | `hooks#configuration` | Confirmed |
| 11 skills within context budget | `skills#troubleshooting` (16k char limit) | Confirmed (~2.2k chars) |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Codemod misses edge cases | Medium | Low | Each phase runs full test suite before merge |
| Test import confusion during migration (old + new coexist) | Medium | Medium | Old package stays functional until its phase; workspace isolation via `uv run --package` |
| engram-core grows too large | Low | Medium | Adapter admission rule (D9) limits scope |
| Unified search performance on large handoff archives | Low | Low | v1 has no persistent index; add if evidence demands |
| Marketplace deployment breaks | Low | High | Test marketplace install in P1 before migrating code |

## Open Questions

1. **Derived cache** — Will lazy fan-out search be fast enough at scale, or will a persistent index (`~/.claude/engram/<project>/index`) eventually be needed? Deferred until performance evidence.
2. **Learnings path configurability** — Hardcoded references to `docs/learnings/learnings.md` exist across skills and docs. `engram.core.paths.resolve_learnings_path()` centralizes the path resolution, but updating all skill instructions to use it is deferred to post-migration cleanup (not part of P1-P6).
3. **Pytest configuration** — The thin-shim pattern needs both shim smoke tests (does the import chain work?) and `engram.*` unit tests (does the logic work?). Exact pytest layout TBD in P1.

## Success Criteria

- [ ] All ~1000+ tests pass in the consolidated package (659 ticket + 340 handoff - ~25 duplicate parser + new learning/core tests)
- [ ] `/defer` works without cross-plugin path hack
- [ ] `/search --all <query>` returns results from tickets, handoffs, learnings, and CLAUDE.md
- [ ] Handoff's duplicate `ticket_parsing.py` is deleted; single source of truth
- [ ] Old `packages/plugins/ticket/` and `packages/plugins/handoff/` are removed
- [ ] `/learn` and `/promote` have Python backing with tests
- [ ] Marketplace install of engram plugin works
- [ ] `uv run --package engram-plugin pytest` runs the full suite

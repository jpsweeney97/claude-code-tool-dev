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

Decisions validated through 3 Codex consultations (1 direct, 2 multi-turn dialogues — 13 total turns, all converged) + 1 deep-review dialogue (5 turns, evaluative posture, all converged) + 1 adversarial-review dialogue (9 turns, adversarial posture, all converged — 11 findings applied).

| # | Decision | Confidence | Source |
|---|----------|------------|--------|
| D1 | Hybrid architecture — unified plugin, federated subsystems | High | Codex consultation #1 |
| D2 | Storage: A+D — keep location split, add thin read-only federation | High | Codex dialogue #1 (6 turns, comparative) |
| D3 | A-with-shims — `scripts/` as runtime entrypoints, `engram/` as real Python package | High | Codex dialogue #2 (6 turns, planning/comparative) |
| D4 | Keep existing skill names — consolidation invisible to users | High | User decision |
| D5 | Unified search as v1 capability; provenance graph, dashboard, cross-entity triage as future | High | User decision |
| D6 | No persistent index in v1 — lazy fan-out from existing metadata | High | Codex dialogue #1 |
| D7 | Two parsers stay separate (handoff frontmatter vs ticket fenced-YAML) | High | Codex dialogue #2 |
| D8 | Migration order: core → learning → ticket foundations+read+dedup → ticket engine+guard → handoff → rest of ticket → cleanup (7 phases) | High | Codex dialogue #2, validated in deep review, P3 scope expanded in adversarial review |
| D9 | Adapter admission rule deferred to v2 — v1 uses provider functions with SearchResult normalization | High | Deep review convergence |
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
│   │   └── providers.py         # provider functions + SearchResult normalization
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
│   ├── ticket/
│   │   ├── SKILL.md
│   │   └── references/pipeline-guide.md  # skill-local operator guide (co-located)
│   ├── ticket-triage/SKILL.md
│   ├── learn/SKILL.md
│   └── promote/SKILL.md
├── hooks/
│   ├── hooks.json               # all hooks in one file (auto-discovered)
│   ├── ticket_engine_guard.py   # PreToolUse hook (→ engram.ticket.guard)
│   ├── cleanup.py               # SessionStart hook (→ engram.handoff.cleanup)
│   └── quality_check.py         # PostToolUse hook (→ engram.handoff.quality_check)
├── references/                  # cross-skill shared contracts only (see convention below)
│   ├── engram-contract.md       # shared metadata + provider conventions
│   ├── ticket-contract.md       # migrated from ticket plugin
│   ├── handoff-contract.md      # migrated from handoff plugin
│   └── format-reference.md      # migrated from handoff plugin
└── tests/
    ├── conftest.py              # shared fixtures (tmp dirs, sample data)
    ├── test_core/               # engram.core tests
    ├── test_ticket/             # ~659 tests, migrated across P3-P6
    ├── test_handoff/            # ~315 tests, migrated in P5
    ├── test_learning/           # NEW tests (P2)
    └── test_shims/              # subprocess-based shim smoke tests
```

**References convention:** Two locations for reference documents, distinguished by consumer count:
- `engram/references/` — cross-skill shared contracts consumed by 2+ skills or components (e.g., `engram-contract.md`, `ticket-contract.md`)
- `engram/skills/<skill>/references/` — skill-local operator guides consumed by a single skill (e.g., `pipeline-guide.md` at 198 lines / ~8.8KB, too large to inline into SKILL.md)

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
2. **Fan-out** — distribute a query to all (or filtered) providers in parallel
3. **Normalize** — convert provider-specific results to a common `SearchResult` envelope
4. **Derive** — compute provenance links from existing metadata (session_id joins, defer-meta, distill-meta, promote-meta)

### Provider Model (v1)

v1 uses hardcoded provider functions instead of a formal adapter hierarchy. Each provider returns normalized `SearchResult` objects. This avoids premature abstraction — the `HandoffAdapter` would immediately violate a single `authority_path` contract (needs active + archive roots), and D9's 2+ consumers guard can't be enforced when only `search.py` consumes providers.

```python
# engram/core/providers.py
from engram.core.search import SearchResult

def search_tickets(query: str, project_root: Path, limit: int = 50) -> list[SearchResult]:
    """Search project-local tickets. Respects path-traversal guard."""
    ...

def search_handoffs(query: str, project_root: Path, limit: int = 50) -> list[SearchResult]:
    """Search user-global handoffs (active + archive). Fans out internally."""
    ...

def search_learnings(query: str, project_root: Path, limit: int = 50) -> list[SearchResult]:
    """Search project-local learnings. Section-aware grep."""
    ...

def search_promoted(query: str, project_root: Path, limit: int = 50) -> list[SearchResult]:
    """Search project-local CLAUDE.md. Read-only grep."""
    ...

# Fixed provider table — no registry, no dynamic dispatch.
PROVIDERS: dict[str, ProviderFn] = {
    "ticket": search_tickets,
    "handoff": search_handoffs,
    "learning": search_learnings,
    "promoted": search_promoted,
}
```

| Provider | Authority Module | Data Source | Notes |
|----------|-----------------|-------------|-------|
| `search_tickets` | `engram.ticket.parse` | `docs/tickets/` | Respects path-traversal guard |
| `search_handoffs` | `engram.handoff.parsing` | `~/.claude/handoffs/<project>/` | Fans out to active + `.archive/` |
| `search_learnings` | `engram.learning.store` | `docs/learnings/learnings.md` | Section-aware grep |
| `search_promoted` | Read-only | `.claude/CLAUDE.md` | Grep only, no mutation |

**Promotion to adapter hierarchy (v2):** When a second consumer of the provider interface arrives (e.g., provenance module), evaluate promoting provider functions to a formal `Adapter` base class with registry. Admission rule: a new provider must be (1) user-facing, (2) authoritative over its data, (3) backed by a stable schema, and (4) consumed by 2+ callers.

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
    regex: bool = False,
    limit: int = 50,
) -> list[SearchResult]:
    """Fan-out search across all registered providers.

    Args:
        query: Literal string match, or regex if regex=True.
        kinds: Filter to entity types. None = all.
        regex: Enable regex matching. Only supported in legacy mode (handoff-only).
            Raises ValueError if regex=True with non-handoff kinds.
        limit: Max results per provider.

    Returns:
        SearchResult list sorted by date (most recent first).
    """
```

**Result fidelity mode boundary:** `SearchResult` is always the result shape. The `metadata` dict carries provider-specific fields. Mode is determined by the resolved provider set, not by flag spelling:

- **Legacy handoff mode** (effective provider set is handoff-only): `metadata["section_heading"]` and `metadata["section_content"]` populated with full text. Regex matching supported. Activated for `/search foo`, `/search --kind handoff foo`, `/search --regex foo`.
- **Normalized mode** (any non-handoff provider in scope): `snippet` is authoritative, `metadata` stays compact. Regex not supported. Activated for `/search --all foo`, `/search --kind ticket foo`, `/search --kind learning,ticket foo`.

Dispatch rule: resolved provider set determines mode, not flag spelling. This prevents the edge case where `/search foo` and `/search --kind handoff foo` would produce different output shapes.

**Provider contract rule:** Providers must NOT place raw body text in `metadata`. Exception: `search_handoffs` in legacy mode populates `section_heading` and `section_content`.

### SearchResult

```python
@dataclass
class SearchResult:
    kind: str          # "ticket", "handoff", "learning", "promoted"
    id: str            # entity ID (ticket ID, handoff filename, learning heading)
    title: str         # summary/title
    snippet: str       # matching content excerpt (max 200 chars, authoritative in normalized mode)
    path: Path         # absolute path to source file
    date: datetime     # creation or last modified (date-only sources promoted to midnight UTC)
    metadata: dict     # provider-specific (status, tags, retention_class, etc.)
                       # Legacy handoff mode adds: section_heading (str), section_content (str)
```

### Skill Integration

The `/search` skill gains cross-entity capability:

```
/search authentication           # handoffs only (legacy mode: full sections + regex supported)
/search --regex "auth.*token"    # handoffs only (legacy mode: regex match)
/search --all authentication     # all entity types (normalized mode: 200-char snippets)
/search --kind ticket auth       # tickets only (normalized mode)
/search --kind learning,ticket X # multiple kinds (normalized mode)
/search --kind handoff auth      # handoffs only (legacy mode — same as bare /search)
```

### v1 Scope

- Literal string matching for cross-entity queries; regex preserved for handoff-only (legacy mode backward compat)
- Recency sort (newest first)
- No persistent index — live fan-out via provider table on every query
- No provenance links in results (future v2)

### Future Capabilities (not in v1)

| Capability | Description | Depends On |
|------------|-------------|------------|
| Provenance graph | "Show lineage of this ticket" — handoff→ticket→learning→CLAUDE.md | `engram.core.provenance` (v2) |
| Lifecycle dashboard | Project knowledge health metrics | All providers + provenance |
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

**Migration cleanup:** Handoff's duplicate `ticket_parsing.py` (25 tests) is deleted. `engram.handoff.triage` imports `engram.ticket.parse` directly — single source of truth.

## Migration Plan

Seven phases, each an independently reviewable and revertible PR.

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
- Implement `engram/core/providers.py` — provider functions + SearchResult normalization
- Implement `engram/core/search.py` — fan-out search via provider table, starting with `search_learnings`
- Implement `engram/learning/store.py` — learnings.md read/write/query
- Implement `engram/learning/capture.py` — /learn Python backing
- Implement `engram/learning/promote.py` — /promote Python backing
- Migrate `/learn` and `/promote` skills from `.claude/skills/` into `engram/skills/`
- Write tests for all new code

**Tests affected:** 0 existing, ~100-150 new
**Risk:** Low — entirely greenfield. Learning provider is the proving ground for the core API.

### Phase 3: Ticket Foundations + Read/Dedup

**Move the data-layer modules that engine_core depends on, including read and dedup.**

`ticket_engine_core.py` has 6 top-level imports + 8+ runtime imports of `ticket_read` and `ticket_dedup` (at lines 42, 282, 309, 386, 720, 774, 1224, 1330). Moving the engine in P4 without its runtime dependencies creates an irresolvable bind: `engram.ticket.engine_core` would need `engram.ticket.read` and `engram.ticket.dedup`, but the one-way compatibility rule prohibits importing from old `scripts.*`. This phase moves all foundation modules — including read and dedup — before the engine moves.

- Move into `engram/ticket/`:
  - `ticket_paths.py` → `paths.py` (path resolution + traversal guard)
  - `ticket_parse.py` → `parse.py` (canonical ticket parser, fenced YAML)
  - `ticket_stage_models.py` → `stage_models.py` (lifecycle states)
  - `ticket_validate.py` → `validate.py` (schema validation)
  - `ticket_render.py` → `render.py` (ticket formatting)
  - `ticket_id.py` → `id.py` (ID generation)
  - `ticket_read.py` → `read.py` (ticket reading — engine_core runtime dependency)
  - `ticket_dedup.py` → `dedup.py` (deduplication — engine_core runtime dependency)
- Create thin shims in `scripts/` where skills reference these modules
- Apply codemod with ticket rename mapping table for moved files
- Update tests for moved modules

**Tests affected:** ~300 (parse, validate, render, id, paths, stage_models, read, dedup tests)
**Risk:** Low-Medium — pure data modules with no mutation logic. Mechanical move + rename. read/dedup are leaf modules consumed only by engine_core.

### Phase 4: Ticket Engine + Guard

**Move the mutation engine and eliminate the /defer cross-plugin runtime hop.**

This is the first write-path cutover — the mutation path, guard hook, trust-triple injection, and `/defer` all change simultaneously.

- Move into `engram/ticket/`:
  - `ticket_engine_core.py` → `engine_core.py`
  - `ticket_engine_runner.py` → `engine_runner.py`
  - `ticket_engine_user.py` → `engine_user.py`
  - `ticket_engine_agent.py` → `engine_agent.py`
  - `ticket_trust.py` → `trust.py`
  - `ticket_envelope.py` → `envelope.py`
- Move `ticket_engine_guard.py` → `engram/ticket/guard.py`
  - Guard must accept explicit `plugin_root` parameter from shim boundary (not `__file__`-based resolution, which resolves incorrectly when imported directly in tests)
  - Guard shim at `hooks/ticket_engine_guard.py` passes `plugin_root=Path(__file__).resolve().parent.parent`
  - Existing allowlist patterns (`_build_allowlist_pattern`, `_build_readonly_pattern`, `_build_audit_pattern`) must be updated if they anchor to `${CLAUDE_PLUGIN_ROOT}/scripts/`
- Create thin shims in `scripts/` for engine entrypoints
- Update `/defer` skill to reference `${CLAUDE_PLUGIN_ROOT}/scripts/ticket_engine_user.py` (co-located, no path hack)
- Apply codemod for moved files
- Update tests for moved modules

**Exit gate (required before P5):**
- All engine unit tests pass via `uv run --package engram-plugin pytest`
- Guard hook shim boundary tests (subprocess invocation, not direct import):
  - Engine branch (allowlist): subprocess through shim with `CLAUDE_PLUGIN_ROOT` set
  - Readonly branch: subprocess test for `ticket_read.py` and `ticket_triage.py` shim paths
  - Audit branch: subprocess test with policy-asymmetric check (user allow + agent deny)
  - At least one test where the shim derives `plugin_root` itself (no `CLAUDE_PLUGIN_ROOT` env var, no monkeypatching) — proves `Path(__file__).parent.parent` resolution is correct from the hooks/ directory
- End-to-end canary: full hook→ticket-creation flow in subprocess (exercises dedup — now available from P3)

**Tests affected:** ~200 (engine core, runner, entrypoints, trust, envelope, guard)
**Risk:** Medium-High — highest risk moment in the migration. Specific failure mode: hook chain breaks or misclassifies commands during trust injection.

### Phase 5: Handoff

**Move all handoff code and eliminate the duplicate parser.**

- Move all handoff scripts into `engram/handoff/`
- Delete handoff's duplicate `ticket_parsing.py` — update `engram.handoff.triage` to import `engram.ticket.parse` (canonical source moved in P3)
- Create thin shims in `scripts/` for all handoff entrypoints
- Apply codemod with handoff mapping table (most are `from scripts.X` → `from engram.handoff.X`; `triage.py` also needs `from scripts.ticket_parsing` → `from engram.ticket.parse`)
- Migrate all 7 handoff skills into `engram/skills/`
- Migrate handoff hooks into `engram/hooks/hooks.json`
- Migrate handoff references into `engram/references/`
- Delete 25 redundant `test_ticket_parsing.py` tests from handoff
- Update remaining ~315 handoff tests
- Normalize all handoff skill script invocations from `python` to `python3` while updating SKILL.md paths (affects `/triage`, `/distill`, `/defer`)
- Remove `try/except ModuleNotFoundError` + `sys.path.insert` fallback scaffolding from migrated modules (`triage.py`, `search.py`, `distill.py`) — dead code once engram is a proper package (see Codemod Details, structural removal bucket)

**Tests affected:** ~340 existing (315 migrated, 25 deleted)
**Risk:** Medium — largest single module move, but handoff modules have no cross-package imports.

### Phase 6: Rest of Ticket

**Complete the ticket migration.**

- Move remaining ticket modules into `engram/ticket/` (triage, audit — foundations, read, dedup, and engine already moved in P3-P4)
- Create remaining thin shims in `scripts/`
- Apply codemod with ticket rename mapping table for remaining files
- Migrate ticket skills into `engram/skills/` (including `skills/ticket/references/pipeline-guide.md` co-located with the skill)
- Merge ticket hook config into `engram/hooks/hooks.json` (guard script already moved in P4)
- Migrate ticket references into `engram/references/`
- Update ~159 remaining ticket tests (659 total minus ~300 in P3, ~200 in P4)

**Tests affected:** ~159 existing
**Risk:** Low — smallest ticket phase. Modules are leaf-level (triage, audit) with no downstream dependents.

### Phase 7: Cleanup

**Remove old packages and update project config.**

- Remove `packages/plugins/ticket/` directory (including `.claude-plugin/`)
- Remove `packages/plugins/handoff/` directory
- Remove `.claude/skills/learn/` and `.claude/skills/promote/`
- Update `.claude-plugin/marketplace.json` at repo root — replace hardcoded `./packages/plugins/ticket` and `./packages/plugins/handoff` source paths with `./packages/plugins/engram`
- Verify old plugin registrations are removed from marketplace/cache
- Update root `pyproject.toml` workspace members (remove ticket, handoff; engram already added in P1)
- Update `.claude/CLAUDE.md` — package table, directory structure, deployment docs
- Update `CHANGELOG.md`
- Verify: `uv run --package engram-plugin pytest` passes all tests

**Tests affected:** 0 (all moved in prior phases)
**Risk:** Low — deletion only. Old packages are inert after P6.

### Codemod Details

**Scope:** Codemod targets ticket and handoff packages only — **285 `from scripts.` import statements across 50 files** (157 in ticket, 122 in handoff, 6 using `import scripts.`). An additional 101 `from scripts.` references exist in cross-model and context-metrics plugins — these are unrelated local `scripts` namespaces within those packages and are not in scope. They will not break when ticket/handoff packages are removed.

**Three-bucket strategy:**

1. **Python AST codemod** — handles `ImportFrom` nodes (`from scripts.X import Y`) and `Import` nodes (`import scripts.X as Y` — 6 alias forms exist, all in tests). A mapping-table-driven AST rewriter is preferred over `sed` to handle renames correctly. The rewriter must walk full function bodies to catch runtime imports inside functions (engine_core has 8+ at lines 42, 282, 309, 386, 720, 774, 1224, 1330).
2. **Structural removal** — 3 handoff files (`triage.py`, `search.py`, `distill.py`) have `try/except ModuleNotFoundError` blocks with `sys.path.insert(0, parent.parent)` as a direct-execution fallback. These are not renames — the entire try/except scaffolding must be removed since engram is a proper package. The fallback inserts the handoff root (not the ticket root), so it cannot cause cross-parser discovery — but dead scaffolding masks packaging errors if left in place. Target: P5.
3. **Manual runtime grep** — covers non-Python references. These cannot be handled by a Python AST codemod.

**Runtime grep scope (functional targets — must update for correct behavior):**
- SKILL.md files with hardcoded `${CLAUDE_PLUGIN_ROOT}/../ticket/scripts/` paths (5 files). Note: `/defer` uses `$(realpath ...)` wrapping — grep pattern must account for this variant.
- hooks.json script references
- Shell command snippets in skill instructions
- `python` → `python3` invocation normalization in `/triage`, `/distill`, `/defer` SKILL.md files

**Runtime grep scope (documentation targets — must update for accuracy but not runtime correctness):**
- `.claude-plugin/marketplace.json` at repo root (hardcoded `./packages/plugins/ticket` and `./packages/plugins/handoff` source paths — update in P7)
- `skills/ticket/references/pipeline-guide.md` (5 hardcoded `scripts/ticket_engine_user.py` and `scripts/ticket_read.py` path strings)
- `HANDBOOK.md` quick-start examples (`uv run scripts/ticket_read.py`, `uv run scripts/ticket_engine_user.py create`)
- `README.md` files in ticket and handoff packages (if they contain script paths)
- `pyproject.toml` workspace members (updated in P1/P7)

**Module renames:** Ticket modules drop the `ticket_` prefix inside `engram/ticket/`. Use the mapping tables below:

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
- P3: AST codemod — ticket foundations + read + dedup (paths, parse, validate, render, id, stage_models, read, dedup)
- P4: AST codemod — ticket engine + runtime grep for guard hook allowlist patterns and `/defer` SKILL.md path
- P5: AST codemod — handoff mapping table + structural removal of try/except fallback scaffolding + manual review for cross-subsystem imports + runtime grep for SKILL.md paths + python→python3 normalization
- P6: AST codemod — remaining ticket modules (triage, audit)

Files importing from multiple subsystems (need manual attention):
- `engram/handoff/triage.py` — imports from both `engram.handoff.*` and `engram.ticket.parse`
- `engram/handoff/defer.py` — invokes ticket engine

### Migration Principles

> Co-locate by plugin, unify by ownership, abstract only after duplication survives the move.

Do not extract shared utilities prematurely. Move code first, observe actual duplication in the new location, then extract only what has 2+ genuine consumers.

**Temporary compatibility direction:** During migration (P3-P6), old packages may import from `engram.*` (old → new). New `engram.*` modules must NEVER import from old `scripts.*` packages (new → old). This prevents re-creating the cross-package dependency tangle the migration is eliminating.

**Parser divergence guardrail (P3-P5):** During P3-P5, the canonical ticket parser exists at `engram.ticket.parse` while old handoff's triage still uses the duplicate `scripts.ticket_parsing`. No ticket-parse behavior changes relevant to triage (frontmatter + body extraction) may land only in the canonical parser during this window without either (a) backporting to the duplicate or (b) moving the parser swap earlier. The duplicate is deleted in P5 when handoff migrates.

### Test Strategy

**Package isolation:** During P3-P6, old and new packages coexist. Both use `scripts.*` namespace. `sys.path.insert(0, plugin_root)` in shims creates real ambiguity when both are importable in one interpreter. Rules:

- Run tests via `uv run --package <name> pytest` per plugin — never root-level mixed runs during P3-P6
- Shim smoke tests must run in **subprocesses** matching production invocation (shebang, `CLAUDE_PLUGIN_ROOT` set, no `python3` prefix for guard)
- `engram.*` unit tests run normally via pytest — these import the package directly, no shim

**Unified test directory:** All tests live under `tests/` with subdirectories by subsystem:

```
tests/
├── conftest.py              # shared fixtures (tmp dirs, sample data, path helpers)
├── test_core/               # engram.core tests
├── test_ticket/             # ~659 tests, migrated across P3-P6
├── test_handoff/            # ~315 tests, migrated in P5
├── test_learning/           # NEW tests (P2)
└── test_shims/              # subprocess-based shim smoke tests
```

Shim smoke tests verify the import chain works under production conditions. They are distinct from unit tests — they spawn a subprocess per shim and check exit code + basic output.

**Centralized path helper:** 8 test files (7 ticket, 1 handoff) use `__file__`-relative path chains like `PLUGIN_ROOT = str(Path(__file__).parent.parent)` that break when test files move to a different directory depth. `tests/conftest.py` must provide a centralized `plugin_root()` fixture that resolves the engram plugin root regardless of test file location. This prevents the same breakage pattern from recurring in future directory restructuring. Specific files requiring update: `test_hook_integration.py` (`PLUGIN_ROOT` and `HOOK_PATH` constants).

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
| **P4 write-path cutover breaks hook chain** | Medium | High | Exit gate: E2E canary test through shim boundary (engine, readonly, audit branches). Dedup now available from P3. Specific failure mode: guard misclassifies commands during trust injection |
| Codemod misses edge cases (AST bucket) | Medium | Low | Each phase runs full test suite before merge. AST rewriter must walk full function bodies for runtime imports |
| Codemod misses non-Python references (grep bucket) | Medium | Medium | Three-tier grep scope: functional targets (SKILL.md, hooks.json, shell snippets), documentation targets (marketplace.json, pipeline-guide.md, HANDBOOK.md, READMEs). Per-phase checklist |
| Dead try/except fallback scaffolding masks packaging errors | Medium | Low | Structural removal bucket in P5. Fallback inserts handoff root (not ticket root) — not a cross-parser risk, but dead code that masks import failures |
| Test import confusion during migration (old + new coexist) | Medium | Medium | Per-package pytest invocations only; shim smoke tests in subprocesses; never root-level mixed runs |
| Guard hook `__file__` resolves incorrectly in tests | Medium | Low | Explicit `plugin_root` parameter injection from shim boundary. Exit gate requires at least one subprocess test with no `CLAUDE_PLUGIN_ROOT` env var |
| P3-P5 parser divergence causes silent behavior mismatch | Low | Medium | Guardrail: no canonical parser changes relevant to triage during this window without backporting to the duplicate |
| `__file__`-relative test paths break on directory migration | Medium | Low | Centralized `plugin_root()` fixture in `tests/conftest.py`. 8 test files affected (7 ticket, 1 handoff) |
| engram-core provider layer grows unbounded | Low | Medium | Provider functions are hardcoded (no registry); promotion to adapter hierarchy requires 2+ consumers (v2 guardrail) |
| Unified search performance on large handoff archives | Low | Low | v1 has no persistent index; add if evidence demands |
| Marketplace deployment breaks | Low | High | Test marketplace install in P1 before migrating code |

## Open Questions

1. **Derived cache** — Will lazy fan-out search be fast enough at scale, or will a persistent index (`~/.claude/engram/<project>/index`) eventually be needed? Deferred until performance evidence.
2. **Learnings path configurability** — Hardcoded references to `docs/learnings/learnings.md` exist across ~14 skills and docs. `engram.core.paths.resolve_learnings_path()` centralizes the path resolution, but updating all skill instructions to use it is deferred to post-migration cleanup (not part of P1-P7).
3. **Triage federation gap** — The existing `/triage` skill cross-queries both handoffs and tickets via direct module imports. The v1 provider model does not replace this — triage's cross-kind result merging continues to work via direct import of `engram.ticket.parse` from `engram.handoff.triage`. Elevating triage to a federation query is deferred to v2 ("Cross-entity triage" in Future Capabilities).

## Success Criteria

- [ ] All ~975+ tests pass in the consolidated package (659 ticket + 340 handoff - 25 duplicate parser + new learning/core/shim tests)
- [ ] `/defer` works without cross-plugin path hack
- [ ] `/search --all <query>` returns results from tickets, handoffs, learnings, and CLAUDE.md
- [ ] `/search <query>` and `/search --regex <pattern>` preserve legacy handoff behavior (full sections, regex support)
- [ ] Handoff's duplicate `ticket_parsing.py` is deleted; single source of truth
- [ ] Old `packages/plugins/ticket/` and `packages/plugins/handoff/` are removed
- [ ] `/learn` and `/promote` have Python backing with tests
- [ ] Marketplace install of engram plugin works
- [ ] `uv run --package engram-plugin pytest` runs the full suite

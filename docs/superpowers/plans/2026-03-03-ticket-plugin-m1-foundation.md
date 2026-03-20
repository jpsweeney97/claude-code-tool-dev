# Ticket Plugin Phase 1 — Module 1: Foundation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scaffold the plugin package structure and create shared test infrastructure (conftest.py with ticket factory helpers).

**Architecture:** Hybrid adapter pattern (Architecture E). This module creates the package layout and test fixtures that all subsequent modules build on. No production logic — only scaffold and test infrastructure.

**Tech Stack:** Python 3.11+, PyYAML, pytest

**References (read-only — do not modify these files):**
- Canonical plan: `docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`
- Modularization design: `docs/plans/2026-03-02-ticket-plugin-plan-modularization.md`
- Design doc: `docs/plans/2026-03-02-ticket-plugin-design.md` (canonical spec)

**Scope:** Module 1 of 5. Creates the plugin directory structure, pyproject.toml, plugin.json, tests/__init__.py, tests/conftest.py, and the ticket contract reference doc. No source modules, no tests beyond conftest validation.

---

## Phase 1 Scope Policy

**Phase 1 Scope Policy (strict fail-closed):**
- All agent mutations are **hard-blocked** in Phase 1 — `engine_preflight` returns `policy_blocked` for `request_origin="agent"` regardless of autonomy mode. Rationale: the PreToolUse hook (Phase 2) is required to inject `hook_injected: true` and `session_id`; without it, agent paths cannot be legitimately exercised.
- `hook_injected` field validation is **deferred to Phase 2** — the hook that sets it doesn't exist yet.
- Audit trail writes (`attempt_started`/`attempt_result` JSONL) are **deferred to Phase 2** — they require `session_id` injection from the hook.
- `auto_audit` and `auto_silent` autonomy modes are structurally unreachable in Phase 1 (blocked by the hard-block above). Tests verify the hard-block, not the mode-specific behavior.
- `ticket_triage.py` is **deferred to Phase 2** — the design doc lists it in the plugin structure, but it implements read-only analysis capabilities (orphan detection, audit trail reporting) that depend on the Phase 2 audit trail. No task in this plan creates `ticket_triage.py` or `test_triage.py`.

**Deferred tickets (not Phase 1):**
- T-20260302-01: auto_audit notification UX flows (Phase 2 — skill UX)
- T-20260302-02: merge_into_existing v1.1 (reserved state, escalate fallback)
- T-20260302-03: ticket audit repair (Phase 2 — added to ticket-ops)
- T-20260302-04: DeferredWorkEnvelope (Phase 4)
- T-20260302-05: foreground-only enforcement (Phase 3)

---

## Prerequisites

None. This is the first module.

## Gate Entry: Gate 0 Preflight

Before starting M1, verify the executing-plans sub-skill is compatible:

1. **Skill exists:** `superpowers:executing-plans` loads without error
2. **Module size:** Skill can accept plans up to ~1924 lines (M4's size)
3. **Non-sequential tasks:** Skill can handle M2's task order (Task 3 → Task 14, skipping 4-13)
4. **Checkpoint format:** Skill follows plan steps exactly (invariant ledger entries are plan steps, not native skill features)

**All 4 checks must pass.** If any fails, stop and escalate.

Record a preflight card:
```
## Gate 0 Preflight Card
checks: [skill_exists, module_size, non_sequential, checkpoint_format]
results: [PASS/FAIL for each]
overall: PASS | FAIL
runner: [agent identity]
```

Commit the preflight card before starting Task 1.

---

## Task 1: Plugin Scaffold

**Files:**
- Create: `packages/plugins/ticket/.claude-plugin/plugin.json`
- Create: `packages/plugins/ticket/pyproject.toml`
- Create: `packages/plugins/ticket/scripts/.gitkeep`
- Create: `packages/plugins/ticket/skills/.gitkeep`
- Create: `packages/plugins/ticket/agents/.gitkeep`
- Create: `packages/plugins/ticket/references/.gitkeep`
- Create: `packages/plugins/ticket/tests/__init__.py`
- Create: `packages/plugins/ticket/tests/conftest.py`

**Step 1: Create directory structure**

```bash
mkdir -p packages/plugins/ticket/.claude-plugin
mkdir -p packages/plugins/ticket/scripts
mkdir -p packages/plugins/ticket/skills
mkdir -p packages/plugins/ticket/agents
mkdir -p packages/plugins/ticket/references
mkdir -p packages/plugins/ticket/tests
```

**Step 2: Write plugin.json**

```json
{
  "name": "ticket",
  "version": "1.0.0",
  "description": "Repo-local ticket management with lifecycle operations, smart routing, and autonomous creation",
  "author": {
    "name": "JP"
  },
  "license": "MIT",
  "keywords": ["ticket", "tracking", "triage", "dedup", "autonomy"]
}
```

**Step 3: Write pyproject.toml**

```toml
[project]
name = "ticket-plugin"
version = "1.0.0"
description = "Repo-local ticket management plugin for Claude Code"
requires-python = ">=3.11"
dependencies = ["pyyaml>=6.0"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

**Step 4: Write tests/conftest.py**

```python
"""Shared test fixtures for ticket plugin tests."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def tmp_tickets(tmp_path: Path) -> Path:
    """Create a temporary docs/tickets/ directory."""
    tickets_dir = tmp_path / "docs" / "tickets"
    tickets_dir.mkdir(parents=True)
    return tickets_dir


@pytest.fixture
def tmp_audit(tmp_path: Path) -> Path:
    """Create a temporary docs/tickets/.audit/ directory."""
    audit_dir = tmp_path / "docs" / "tickets" / ".audit"
    audit_dir.mkdir(parents=True)
    return audit_dir


def make_ticket(
    tickets_dir: Path,
    filename: str,
    *,
    id: str = "T-20260302-01",
    date: str = "2026-03-02",
    status: str = "open",
    priority: str = "high",
    effort: str = "S",
    source_type: str = "ad-hoc",
    source_ref: str = "",
    session: str = "test-session",
    tags: list[str] | None = None,
    blocked_by: list[str] | None = None,
    blocks: list[str] | None = None,
    contract_version: str = "1.0",
    title: str = "Test ticket",
    problem: str = "Test problem description.",
    extra_yaml: str = "",
    extra_sections: str = "",
) -> Path:
    """Create a v1.0 format ticket file for testing.

    Returns the path to the created file.
    """
    tags = tags or []
    blocked_by = blocked_by or []
    blocks = blocks or []

    content = textwrap.dedent(f"""\
        # {id}: {title}

        ```yaml
        id: {id}
        date: "{date}"
        status: {status}
        priority: {priority}
        effort: {effort}
        source:
          type: {source_type}
          ref: "{source_ref}"
          session: "{session}"
        tags: {tags}
        blocked_by: {blocked_by}
        blocks: {blocks}
        contract_version: "{contract_version}"
        {extra_yaml}```

        ## Problem
        {problem}

        ## Approach
        Fix the issue.

        ## Acceptance Criteria
        - [ ] Issue resolved

        ## Verification
        ```bash
        echo "verified"
        ```

        ## Key Files
        | File | Role | Look For |
        |------|------|----------|
        | test.py | Test | Test code |
        {extra_sections}
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


# --- Legacy ticket fixtures ---


def make_gen1_ticket(tickets_dir: Path, filename: str = "handoff-chain-viz.md") -> Path:
    """Gen 1 (hand-authored): slug ID, `plugin` field, `related` flat list."""
    content = textwrap.dedent("""\
        # handoff-chain-viz: Visualize handoff chains

        ```yaml
        id: handoff-chain-viz
        date: "2026-01-15"
        status: open
        plugin: handoff
        related: [handoff-search, handoff-quality-hook]
        ```

        ## Summary
        Build a visualization for handoff dependency chains.
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def make_gen2_ticket(tickets_dir: Path, filename: str = "T-A-test.md") -> Path:
    """Gen 2 (letter IDs): T-[A-F] ID, `branch`, free-text `effort`."""
    content = textwrap.dedent("""\
        # T-A: Refactor analytics pipeline

        ```yaml
        id: T-A
        date: "2026-02-01"
        status: open
        priority: high
        effort: "S (1-2 sessions)"
        branch: feature/analytics-refactor
        blocked_by: []
        blocks: [T-B]
        ```

        ## Summary
        The analytics pipeline needs refactoring.

        ## Rationale
        Current design is too coupled.

        ## Design
        Decouple the pipeline stages.

        ## Risks
        Breaking existing consumers.
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def make_gen3_ticket(tickets_dir: Path, filename: str = "T-003-test.md") -> Path:
    """Gen 3 (numeric IDs): T-NNN, `branch`, varied sections."""
    content = textwrap.dedent("""\
        # T-003: Fix session counting

        ```yaml
        id: T-003
        date: "2026-02-15"
        status: in_progress
        priority: medium
        branch: fix/session-counting
        blocked_by: []
        blocks: []
        ```

        ## Summary
        Session counting is off by one.

        ## Prerequisites
        Requires access to audit trail.

        ## Findings
        The counter increments before validation.

        ## Verification
        ```bash
        uv run pytest tests/test_sessions.py
        ```

        ## References
        - Related to handoff plugin session tracking
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def make_gen4_ticket(tickets_dir: Path, filename: str = "2026-03-01-auth-timeout.md") -> Path:
    """Gen 4 (defer output): T-YYYYMMDD-NN, `source_type`, `provenance`, `status: deferred`."""
    content = textwrap.dedent("""\
        # T-20260301-01: Fix authentication timeout

        ```yaml
        id: T-20260301-01
        date: "2026-03-01"
        status: deferred
        priority: medium
        source_type: handoff
        source_ref: session-xyz
        provenance:
          created_by: defer.py
          session_id: xyz-123
          handoff_file: 2026-03-01_handoff.md
        tags: [auth, api]
        blocked_by: []
        blocks: []
        ```

        ## Problem
        Auth handler times out for large payloads.

        ## Source
        Found during API refactor session.

        ## Proposed Approach
        Make timeout configurable per route.

        ## Acceptance Criteria
        - [ ] Timeout configurable per route
    """)
    path = tickets_dir / filename
    path.write_text(content, encoding="utf-8")
    return path
```

**Step 5: Write tests/__init__.py**

```python
```

(Empty — needed for pytest discovery.)

**Step 6: Verify pytest runs**

Run: `cd packages/plugins/ticket && uv run pytest --co -q`
Expected: "no tests ran" (collection succeeds, no tests yet)

**Step 7: Commit**

```
feat(ticket): scaffold plugin directory structure

Phase 1 foundation: plugin.json, pyproject.toml, test fixtures.
```

---

## Task 2: Ticket Contract Reference

**Files:**
- Create: `packages/plugins/ticket/references/ticket-contract.md`

**Context:** The contract is the single source of truth for all 10 domains. Skills, agents, and engine all reference it. Read design doc sections: "Ticket Contract" (lines ~541-633), "Ticket Format" (lines ~76-148), "Status Transitions" (lines ~607-631).

**Step 1: Write the contract**

The contract covers all 10 domains from the design doc. This is a reference document, not executable code — it defines the schemas, policies, field definitions, and rules that the engine enforces.

Create `packages/plugins/ticket/references/ticket-contract.md` with these sections:

```markdown
# Ticket Contract v1.0

Single source of truth for the ticket plugin. All components (skills, agents, engine) reference this contract.

## 1. Storage

- Active tickets: `docs/tickets/`
- Archived tickets: `docs/tickets/closed-tickets/`
- Audit trail: `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl`
- Naming: `YYYY-MM-DD-<slug>.md`
- Slug: first 6 words of title, kebab-case, `[a-z0-9-]` only, max 60 chars, sequence suffix on collision
- Bootstrap: missing `docs/tickets/` → empty result for reads; create on first write

## 2. ID Allocation

- Format: `T-YYYYMMDD-NN` (date + 2-digit daily sequence, zero-padded)
- Collision prevention: scan existing tickets for same-day IDs, allocate next NN
- Legacy IDs preserved permanently: `T-NNN` (Gen 3), `T-[A-F]` (Gen 2), slugs (Gen 1)

## 3. Schema

### Required YAML Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Ticket ID (T-YYYYMMDD-NN or legacy) |
| `date` | string | Creation date (YYYY-MM-DD) |
| `status` | string | One of: open, in_progress, blocked, done, wontfix |
| `priority` | string | One of: critical, high, medium, low |
| `source` | object | `{type: string, ref: string, session: string}` |
| `contract_version` | string | "1.0" |

### Optional YAML Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `effort` | string | "" | Estimate (XS, S, M, L, XL or free text) |
| `tags` | list[string] | [] | Categorization tags |
| `blocked_by` | list[string] | [] | IDs of blocking tickets |
| `blocks` | list[string] | [] | IDs of tickets this blocks |
| `defer` | object | null | `{active: bool, reason: string, deferred_at: string}` |

### Required Sections

Problem, Approach, Acceptance Criteria, Verification, Key Files

### Optional Sections

Context, Prior Investigation, Decisions Made, Related, Reopen History

### Section Ordering

Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related → Reopen History

## 4. Engine Interface

Common response envelope: `{state: string, ticket_id: string|null, message: string, data: object}`

Exit codes: 0 (success), 1 (engine error), 2 (validation failure)

### Subcommands

| Subcommand | Input | Output `data` |
|-----------|-------|---------------|
| classify | action, args, session_id, request_origin | intent, confidence, resolved_ticket_id |
| plan | intent, fields, session_id, request_origin | dedup_fingerprint, target_fingerprint, duplicate_of, missing_fields, action_plan |
| preflight | ticket_id, action, session_id, request_origin, classify_confidence, classify_intent, dedup_fingerprint, target_fingerprint | checks_passed, checks_failed |
| execute | action, ticket_id, fields, session_id, request_origin, dedup_override, dependency_override | ticket_path, changes |

### Machine States (14 total: 13 emittable, 1 reserved)

ok_create, ok_update, ok_close, ok_close_archived, ok_reopen, need_fields, duplicate_candidate, preflight_failed, policy_blocked, invalid_transition, dependency_blocked, not_found, escalate, merge_into_existing (reserved)

### Error Codes (11)

need_fields, invalid_transition, policy_blocked, stale_plan, audit_unavailable, duplicate_candidate, parse_error, not_found, dependency_blocked, intent_mismatch, origin_mismatch

## 5. Autonomy Model

Modes: suggest (default), auto_audit, auto_silent (v1.1 only)

Config: `.claude/ticket.local.md` YAML frontmatter

`request_origin`: "user" (ticket_engine_user.py), "agent" (ticket_engine_agent.py), "unknown" (fail closed)

## 6. Dedup Policy

Fingerprint: `sha256(normalize(problem_text) + "|" + sorted(key_file_paths))`

`normalize()` steps: (1) strip, (2) collapse whitespace, (3) lowercase, (4) remove punctuation except hyphens/underscores, (5) NFC Unicode normalization

Window: 24 hours. Override: `dedup_override: true` with matching `ticket_id`.

### Test Vectors

| Input | Expected Normalized |
|-------|-------------------|
| `"  Hello,  World!  "` | `"hello world"` |
| `"Fix: the AUTH bug..."` | `"fix the auth bug"` |
| `"résumé"` | `"résumé"` (NFC) |
| `"  multiple   spaces  \n  newlines  "` | `"multiple spaces newlines"` |
| `"keep-hyphens and_underscores"` | `"keep-hyphens and_underscores"` |

## 7. Status Transitions

| From | To | Preconditions |
|------|----|---------------|
| open | in_progress | none |
| open | blocked | blocked_by non-empty |
| in_progress | open | none |
| in_progress | blocked | blocked_by non-empty |
| in_progress | done | acceptance criteria present |
| blocked | open | all blocked_by resolved (done or wontfix) |
| blocked | in_progress | all blocked_by resolved |
| * | wontfix | none |
| done | open | reopen_reason required, user-only v1.0 |
| wontfix | open | reopen_reason required, user-only v1.0 |

Non-status edits on terminal tickets (done/wontfix) are allowed without reopening.

### Status Normalization (Legacy)

| Raw | Canonical |
|-----|-----------|
| planning | open |
| implementing | in_progress |
| complete | done |
| closed | done |
| deferred | open (with defer.active: true) |

## 8. Migration

Read-only for legacy formats. Conversion on update (with user confirmation).

### Legacy Generations

| Gen | ID Pattern | Section Renames |
|-----|-----------|----------------|
| 1 | slug | Summary→Problem |
| 2 | T-[A-F] | Summary→Problem |
| 3 | T-NNN | Summary→Problem, Findings→Prior Investigation |
| 4 | T-YYYYMMDD-NN | Proposed Approach→Approach, provenance→source |

### Field Defaults (applied on read)

| Missing Field | Default |
|--------------|---------|
| priority | medium |
| source | {type: "legacy", ref: "", session: ""} |
| effort | "" |
| tags | [] |
| blocked_by/blocks | [] |

## 9. Integration

External consumers read `docs/tickets/*.md` as plain markdown with fenced YAML.
Format uses fenced YAML (```yaml), not YAML frontmatter (---).

## 10. Versioning

`contract_version` in YAML frontmatter. Current: "1.0".
Engine reads all versions; writes latest only.
```

**Step 2: Commit**

```
feat(ticket): add ticket contract v1.0 reference document

10-domain contract: storage, IDs, schema, engine interface, autonomy,
dedup, transitions, migration, integration, versioning.
```

---

## Gate Exit: M1 → M2

**Gate Type:** Standard

**What the reviewer checks after M1 completes:**

1. **Conftest smoke test:** Import and call each factory helper:
   ```python
   from tests.conftest import make_gen1_ticket, make_gen2_ticket, make_gen3_ticket, make_gen4_ticket
   import tempfile
   from pathlib import Path

   with tempfile.TemporaryDirectory() as tmp:
       tmp_dir = Path(tmp) / "docs" / "tickets"
       tmp_dir.mkdir(parents=True)
       for make_fn in [make_gen1_ticket, make_gen2_ticket, make_gen3_ticket, make_gen4_ticket]:
           path = make_fn(tmp_dir)
           assert isinstance(path, Path)
           assert path.exists()
           content = path.read_text()
           assert "---" in content  # has fenced YAML
   ```
   **Must NOT import `parse_ticket`** (Task 3 not built yet).

2. **API surface:** Verify these symbols are importable from `tests.conftest`:
   - `make_ticket`, `make_gen1_ticket`, `make_gen2_ticket`, `make_gen3_ticket`, `make_gen4_ticket`
   - `tmp_tickets` (fixture), `tmp_audit` (fixture)

3. **Verdict:** Mechanically derived — PASS iff smoke test exits 0 and all symbols import.

**Gate Card Template (reviewer fills this in):**
```
## Gate Card: M1 → M2
evaluated_sha: <executor's final commit SHA>
handoff_sha: <reviewer's commit after adding this gate card>
commands_to_run: ["uv run pytest tests/ -v"]
must_pass_files: []
api_surface_expected:
  - tests.conftest: [make_ticket, make_gen1_ticket, make_gen2_ticket, make_gen3_ticket, make_gen4_ticket, tmp_tickets, tmp_audit]
verdict: PASS | FAIL
warnings: []
probe_evidence:
  - command: "python -c 'from tests.conftest import make_gen1_ticket, make_gen2_ticket, make_gen3_ticket, make_gen4_ticket; ...'"
    result: "<output>"
```

**Two-SHA semantics:** The executor commits all M1 work (`evaluated_sha`). The reviewer runs the gate checks, then commits the gate card (`handoff_sha`). M2's handoff prompt references `handoff_sha`.

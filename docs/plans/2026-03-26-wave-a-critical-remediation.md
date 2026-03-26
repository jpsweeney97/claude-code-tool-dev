# Wave A: Critical Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 4 highest-priority findings from the cross-model plugin design review (2026-03-26): credential scan bypass (F1), silent REPO_ROOT misconfiguration (F3), unimplemented governance CI (F6+F10), and misleading composition contract scope (SC-3).

**Architecture:** Four independent changes within `packages/plugins/cross-model/` plus one CI workflow at repo root. F1 changes one exception handler from allow-through to fail-closed. F3 adds a stderr startup log. F6 creates a CI workflow wiring the existing validation script. F10 and SC-3 are documentation fixes. All changes are additive — no removals, no interface changes.

**Tech Stack:** Python 3.14, pytest, GitHub Actions (uv-based), ripgrep

**Source:** 6-reviewer design review (`docs/audits/cross-model-audit/2026-03-26-cross-model-plugin-team.md`) + Codex dialogue (thread `019d2a9b-14f5-77d3-bcb1-0c6aea739d79`, exploratory posture, 6 turns).

---

## File Map

### New Files
| File | Responsibility |
|------|---------------|
| `.github/workflows/cross-model-plugin.yml` | CI: validate consultation contract + run plugin tests on cross-model changes |

### Modified Files
| File | Change |
|------|--------|
| `packages/plugins/cross-model/scripts/codex_delegate.py:617-624` | F1: Replace allow-through `ToolInputLimitExceeded` handler with fail-closed `CredentialBlockError` |
| `packages/plugins/cross-model/tests/test_codex_delegate.py` | F1: Add test verifying oversized prompts produce blocked status |
| `packages/plugins/cross-model/context-injection/context_injection/server.py:47-50` | F3: Log resolved `REPO_ROOT` to stderr at startup |
| `packages/plugins/cross-model/context-injection/tests/test_server.py` | F3: Add test verifying startup log |
| `packages/plugins/cross-model/references/contract-agent-extract.md:1-3` | F10: Add extract-version hash comment for drift detection |
| `packages/plugins/cross-model/references/consultation-contract.md` | F10: Add sync warning at §2 precedence section |
| `packages/plugins/cross-model/README.md:240` | SC-3: Clarify composition contract scope and authority model |

---

## Task 1: F1 — Fail-Closed Credential Scan on Oversized Prompts

**Files:**
- Modify: `packages/plugins/cross-model/scripts/codex_delegate.py:617-624`
- Modify: `packages/plugins/cross-model/tests/test_codex_delegate.py`

**Context for implementer:** The credential scan in step 4 of the delegation pipeline calls `_check_tool_input()` which may raise `_ToolInputLimitExceeded` when the prompt exceeds the 256 KiB char cap. Currently this exception is caught and swallowed with a stderr warning — the prompt proceeds to Codex unsanitized. This violates governance lock #6 (non-negotiable egress sanitization). The fix is to raise `CredentialBlockError` instead, which is caught by the top-level handler at line 725 and produces `return 0` (status="blocked").

**Important:** The fix is catch-and-raise, NOT delete-the-catch. Removing the catch entirely would route `_ToolInputLimitExceeded` to the generic `except Exception` handler, which wraps in `CredentialBlockError` with a misleading "credential scan failed" message. The explicit catch preserves the specific error message.

- [ ] **Step 1: Write the failing test**

Add to `packages/plugins/cross-model/tests/test_codex_delegate.py`, inside `class TestCredentialScan`:

```python
    @patch(
        "scripts.codex_delegate._check_tool_input",
        side_effect=_ToolInputLimitExceeded("tool_input traversal failed: char cap exceeded"),
    )
    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_oversized_prompt_blocks_not_allows(
        self, mock_sub: MagicMock, _mock_log: MagicMock, _mock_scan: MagicMock, tmp_path: Path,
    ) -> None:
        """F1: ToolInputLimitExceeded produces status=blocked/exit 0 (governance lock #6)."""
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=0, stdout=str(tmp_path) + "\n")
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "a]" * 200_000}))
        exit_code = run(f)
        assert exit_code == 0  # blocked, not error (1) or allowed-through
```

Also add the import at the top of the file if not already present:

```python
from scripts.consultation_safety import ToolInputLimitExceeded as _ToolInputLimitExceeded
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py::TestCredentialScan::test_oversized_prompt_blocks_not_allows -v`
Expected: FAIL — currently the handler prints a warning and continues; the pipeline proceeds past step 4 and may return a different exit code.

- [ ] **Step 3: Implement the fail-closed handler**

In `packages/plugins/cross-model/scripts/codex_delegate.py`, replace lines 617-624:

```python
            except _ToolInputLimitExceeded:
                # Large prompts exceed the 256 KiB char cap in extract_strings.
                # The prior scan_text path had no size gate — allow to preserve parity.
                # Prompts exceeding this cap bypass credential scanning entirely.
                print(
                    "codex-delegate: credential scan skipped: prompt exceeds char cap",
                    file=sys.stderr,
                )
```

With:

```python
            except _ToolInputLimitExceeded:
                # F1: Fail closed on oversized prompts. Governance lock #6
                # requires egress sanitization on all outbound payloads.
                # The prior allow-through preserved "parity" with a pre-refactor
                # path that had no size gate — that rationale is now stale.
                raise CredentialBlockError(
                    "credential scan blocked: prompt exceeds 256 KiB char cap"
                )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py::TestCredentialScan::test_oversized_prompt_blocks_not_allows -v`
Expected: PASS

- [ ] **Step 5: Run full credential scan test class**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py::TestCredentialScan -v`
Expected: All tests PASS (existing tests unaffected — they test different exception paths)

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/cross-model/scripts/codex_delegate.py packages/plugins/cross-model/tests/test_codex_delegate.py
git commit -m "fix(cross-model): fail-closed credential scan on oversized prompts (F1)

ToolInputLimitExceeded now raises CredentialBlockError instead of printing
a warning and allowing the unsanitized prompt through to Codex. Aligns
codex_delegate.py with codex_guard.py behavior and governance lock #6.

The prior allow-through preserved parity with a pre-refactor path that
had no size gate. That rationale is stale — the refactor created the cap
that makes the bypass visible."
```

---

## Task 2: F3 — REPO_ROOT Startup Operator Signal

**Files:**
- Modify: `packages/plugins/cross-model/context-injection/context_injection/server.py:47-50`
- Modify: `packages/plugins/cross-model/context-injection/tests/test_server.py`

**Context for implementer:** The context-injection MCP server captures `REPO_ROOT` from the environment (defaulting to `os.getcwd()`) at startup. If Claude Code is launched from the wrong directory, all `/dialogue` evidence gathering silently returns irrelevant results. There is no operator signal that misconfiguration occurred. The fix adds a single stderr log line at startup showing the resolved value.

- [ ] **Step 1: Write the failing test**

Add to `packages/plugins/cross-model/context-injection/tests/test_server.py`:

```python
import os

import pytest


@pytest.mark.anyio
async def test_startup_logs_repo_root(capsys, monkeypatch, tmp_path):
    """F3: Server logs resolved REPO_ROOT to stderr at startup."""
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    # Initialize a minimal git repo so _load_git_files succeeds
    (tmp_path / ".git").mkdir()

    from context_injection.server import app_lifespan, create_server

    server = create_server()
    async with app_lifespan(server) as _ctx:
        pass

    captured = capsys.readouterr()
    assert f"REPO_ROOT={tmp_path}" in captured.err
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_server.py::test_startup_logs_repo_root -v`
Expected: FAIL — no stderr output currently

- [ ] **Step 3: Add the startup log**

In `packages/plugins/cross-model/context-injection/context_injection/server.py`, after line 48 (`git_files = _load_git_files(repo_root)`), add:

```python
    print(f"context-injection: REPO_ROOT={repo_root}", file=sys.stderr)
```

Also add `import sys` at the top of the file if not already present.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest tests/test_server.py::test_startup_logs_repo_root -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/context-injection/context_injection/server.py packages/plugins/cross-model/context-injection/tests/test_server.py
git commit -m "fix(context-injection): log REPO_ROOT to stderr at startup (F3)

Operators can now see the resolved REPO_ROOT in MCP server output.
Previously, launching Claude Code from the wrong directory caused
silent misconfiguration of all /dialogue evidence gathering."
```

---

## Task 3: F6 — Cross-Model Plugin CI Workflow

**Files:**
- Create: `.github/workflows/cross-model-plugin.yml`

**Context for implementer:** The consultation contract validation script (`scripts/validate_consultation_contract.py`) exists and works, but is not wired into CI — only into a repo-root test. The only existing CI workflow covers the TypeScript `claude-code-docs` package. This task creates a parallel workflow for the Python cross-model plugin, scoped to changes in the plugin directory.

- [ ] **Step 1: Create the CI workflow**

Create `.github/workflows/cross-model-plugin.yml`:

```yaml
name: Cross-Model Plugin Gates

on:
  pull_request:
    paths:
      - "packages/plugins/cross-model/**"
      - "scripts/validate_consultation_contract.py"
      - "tests/test_consultation_contract_sync.py"
      - ".github/workflows/cross-model-plugin.yml"
  push:
    branches:
      - main
    paths:
      - "packages/plugins/cross-model/**"
      - "scripts/validate_consultation_contract.py"
      - "tests/test_consultation_contract_sync.py"
      - ".github/workflows/cross-model-plugin.yml"
  workflow_dispatch:

jobs:
  plugin-gates:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install Python
        run: uv python install 3.14

      - name: Install dependencies
        run: uv sync

      - name: Validate consultation contract
        run: uv run scripts/validate_consultation_contract.py

      - name: Run plugin tests
        run: uv run --package cross-model pytest packages/plugins/cross-model/tests/ -v --tb=short

      - name: Run context-injection tests
        run: uv run --package context-injection pytest packages/plugins/cross-model/context-injection/tests/ -v --tb=short

      - name: Run consultation contract sync test
        run: uv run pytest tests/test_consultation_contract_sync.py -v
```

- [ ] **Step 2: Verify the workflow file is valid YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/cross-model-plugin.yml'))" && echo "Valid YAML"`
Expected: "Valid YAML"

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/cross-model-plugin.yml
git commit -m "ci(cross-model): add CI workflow for plugin and contract validation (F6)

Wires validate_consultation_contract.py into CI, path-scoped to the
cross-model plugin. Runs plugin tests, context-injection tests, and
the consultation contract sync test on every relevant change.

Previously, contract drift was only detectable by manually running
the repo-root test suite."
```

---

## Task 4: F10 — Contract Extract Sync Warning

**Files:**
- Modify: `packages/plugins/cross-model/references/contract-agent-extract.md:1-3`
- Modify: `packages/plugins/cross-model/references/consultation-contract.md` (§2 precedence section)

**Context for implementer:** `contract-agent-extract.md` is a manually maintained copy of 7 sections from the consultation contract. The `codex-dialogue` agent reads the extract, not the full contract. If normative sections change (§5 briefing, §7 safety, §10 continuity), the extract drifts silently. The governance drift CI validates governance lock count but not extract sync. This task adds a content hash marker to the extract and a sync warning to the contract.

- [ ] **Step 1: Compute the current extract content hash**

Run: `cd packages/plugins/cross-model && tail -n +3 references/contract-agent-extract.md | shasum -a 256 | cut -c1-12`

Record the output hash (first 12 characters of SHA-256). This is the current extract body hash.

- [ ] **Step 2: Add extract-version marker**

In `packages/plugins/cross-model/references/contract-agent-extract.md`, replace line 1:

```markdown
# Consultation Contract — Agent Extract
```

With:

```markdown
<!-- extract-hash: {HASH_FROM_STEP_1} -->
# Consultation Contract — Agent Extract
```

Where `{HASH_FROM_STEP_1}` is the 12-character hash computed in Step 1.

- [ ] **Step 3: Add sync warning to consultation contract**

In `packages/plugins/cross-model/references/consultation-contract.md`, find the §2 heading (the precedence/authority section). After the section content, add this note:

```markdown
> **Sync obligation:** If you update §5, §7, §8, §9, §10, or §15, also update `contract-agent-extract.md` and recompute its `extract-hash` marker: `tail -n +4 references/contract-agent-extract.md | shasum -a 256 | cut -c1-12`
```

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/cross-model/references/contract-agent-extract.md packages/plugins/cross-model/references/consultation-contract.md
git commit -m "docs(cross-model): add extract sync warning and hash marker (F10)

contract-agent-extract.md now has an extract-hash comment for manual
drift detection. consultation-contract.md §2 now warns maintainers
to update the extract when normative sections change.

Automated CI for extract sync is deferred — this is the minimum
viable guard against silent drift."
```

---

## Task 5: SC-3 — Clarify Composition Contract Scope in README

**Files:**
- Modify: `packages/plugins/cross-model/README.md:240`

**Context for implementer:** The README lists the composition contract alongside the consultation and context-injection contracts as if all three govern this plugin's runtime behavior. In reality, the composition contract governs cross-skill composition between `adversarial-review`, `next-steps`, and `dialogue` — the first two don't exist in this plugin. None of the sentinel/capsule infrastructure defined in the composition contract has locally-instantiated consumers. The README should clarify this.

- [ ] **Step 1: Update the README contract table**

In `packages/plugins/cross-model/README.md`, find the composition contract row (line 240):

```markdown
| Composition Contract | `references/composition-contract.md` | Multi-skill composition: sentinel detection, capsule exchange, lineage |
```

Replace with:

```markdown
| Composition Contract | `references/composition-contract.md` | Cross-plugin composition protocol (governs `adversarial-review`, `next-steps`, `dialogue`). No locally-instantiated consumers in this plugin; inline skill stubs are runtime-authoritative. Hosted here as the authoring origin. |
```

- [ ] **Step 2: Commit**

```bash
git add packages/plugins/cross-model/README.md
git commit -m "docs(cross-model): clarify composition contract scope in README (SC-3)

The composition contract governs skills outside this plugin boundary.
Updated the contract table to state this explicitly, note the lack of
local consumers, and clarify the dual authority model."
```

---

## Task 6: Final Validation

- [ ] **Step 1: Run full plugin test suite**

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS, no regressions

- [ ] **Step 2: Run context-injection tests**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: Run consultation contract validation**

Run: `uv run scripts/validate_consultation_contract.py`
Expected: Exit 0, no errors

- [ ] **Step 4: Run repo-root contract sync test**

Run: `uv run pytest tests/test_consultation_contract_sync.py -v`
Expected: PASS

---

## Out of Scope (Deferred to Later Waves)

**Wave A2 — Schema Stabilization:**
- F5: Document rollout procedure for context-injection version changes
- F8: Add `failure_source` field to `ScoutResultInvalid`
- F11: Add `phase_id` to `TurnRequest` — one last 0.x bump, then cut 1.0

**Wave B — Quick Wins:**
- F12: Cache `_check_codex_version()` result at module level
- F13: Wire `VALID_CONSULTATION_SOURCES` into `emit_analytics.py` validate() path
- F4: Adversarial testing of scope anchoring prompt injection
- F9/F15/F16: Documentation sweep (JSONL lifecycle, /dialogue layer exception, conversationId removal)
- BH-5: Replace `assert isinstance(...)` with explicit `RuntimeError` check in `grep.py:313`

**Wave C — Follow-On Design Decisions:**
- F2: Add `asyncio.Lock` to HMAC used-bit (deployment-expansion gate)
- F7: `git_files` TTL-based cache or documentation
- F14: Legacy test corpus audit and migration
- SC-3 structural end-state: Move composition contract or vendor governed stubs

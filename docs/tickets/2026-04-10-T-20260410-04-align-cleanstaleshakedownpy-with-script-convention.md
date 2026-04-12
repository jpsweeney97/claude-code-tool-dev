# T-20260410-04: Align clean_stale_shakedown.py with script conventions

```yaml
id: T-20260410-04
date: '2026-04-10'
status: done
summary: Align clean_stale_shakedown.py with script conventions
priority: medium
source_type: pr-review
source_ref: 'PR #101'
effort: S
branch: fix/t03-stale-cleanup-observability
closed_date: '2026-04-12'
closed_reason: All acceptance criteria fulfilled by PR #104 (T-03 work)
files:
- packages/plugins/codex-collaboration/scripts/clean_stale_shakedown.py
```

## Problem

The clean_stale_shakedown.py wrapper currently diverges from the plugin's sibling script patterns. It uses a different sys.path shim shape, lacks a main() wrapper, and does not emit failures using the project's canonical error format. The script fail-fast behavior is acceptable, but the implementation and operator-facing errors are less disciplined than the rest of the plugin's script surface.

## Proposed Approach

Refactor the cleanup wrapper to mirror the sibling containment scripts: use the same import shim pattern, move execution into main() -> None, and wrap top-level failures in the canonical error format so shakedown-b1 receives consistent diagnostics.

## Acceptance Criteria

- clean_stale_shakedown.py uses the same import-shim pattern as the related containment scripts
- The script exposes a main() entry point and avoids module-level execution side effects beyond the standard __main__ block
- Top-level failures are reported with the project's canonical '{operation} failed: {reason}. Got: {input!r:.100}' format
- The shakedown harness receives actionable stderr when cleanup fails before seed creation

## Evidence

> clean_stale_shakedown.py has no outer exception boundary ... uncaught ImportError or assertion would crash without context, and the error format doesn't match the project's '{operation} failed: {reason}. Got: {input!r:.100}' contract.

<!-- defer-meta {"created_by":"defer-skill","source_ref":"PR #101","source_session":"","source_type":"pr-review","v":1} -->

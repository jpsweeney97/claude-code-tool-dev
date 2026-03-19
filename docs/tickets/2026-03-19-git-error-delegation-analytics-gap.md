# T-010: git_error delegation events silently dropped by validator

```yaml
id: T-010
date: 2026-03-19
status: open
priority: medium
branch: null
blocked_by: []
blocks: []
related: [PR-80]
```

## Summary

The delegation event validator's cross-field invariant "blocked requires at least one block flag set" correctly rejects `git_error` gate blocks because `blocked_by="git_error"` sets none of the three boolean flags (`credential_blocked`, `dirty_tree_blocked`, `readable_secret_file_blocked`). The fail-closed `_validate_and_log` wrapper drops these events with a stderr warning.

This means git gate failures (git not found, git timeout, non-zero git status) silently disappear from analytics.

## Origin

Discovered during Task 1 implementation of PR #80 (cross-model design review remediation). The implementer flagged it as DONE_WITH_CONCERNS. Codex PR review also flagged it as P1.

## Options

1. **Add `git_error_blocked` boolean field** to `delegation_outcome` schema and event construction — cleanest, preserves the invariant for the three security gates
2. **Give git_error a distinct `termination_reason`** like `"gate_error"` instead of `"blocked"` — git failures are infrastructure errors, not security blocks
3. **Relax the invariant** to allow `blocked` with all flags false — weakens validation for all block types

## Recommendation

Option 2. `git_error` is semantically different from credential/tree/secret blocks (infrastructure failure vs. security gate). A distinct `termination_reason` makes the event schema more precise without adding a boolean field.

## Files

- `packages/plugins/cross-model/scripts/event_schema.py` — add `"gate_error"` to `VALID_DELEGATION_TERMINATION_REASONS`
- `packages/plugins/cross-model/scripts/codex_delegate.py` — change derivation logic for `git_error` gate
- `packages/plugins/cross-model/scripts/emit_analytics.py` — update cross-field invariants if needed
- `packages/plugins/cross-model/tests/test_codex_delegate.py` — update `test_git_error_gate_does_not_set_block_flags`

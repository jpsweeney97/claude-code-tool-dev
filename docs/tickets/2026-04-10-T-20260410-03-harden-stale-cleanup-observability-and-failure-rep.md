# T-20260410-03: Harden stale cleanup observability and failure reporting

```yaml
id: T-20260410-03
date: '2026-04-10'
status: deferred
summary: Harden stale cleanup observability and failure reporting
priority: medium
source_type: pr-review
source_ref: 'PR #101'
effort: M
branch: feature/b4-agent-skill-harness-assembly
files:
- packages/plugins/codex-collaboration/server/containment.py
```

## Problem

The containment cleanup path still silently swallows several failure modes. clean_stale_files() currently uses silent OSError skips, does not distinguish missing files from unreadable or undeletable files in its outward behavior, and leaves operators with no visibility into whether stale-state cleanup actually succeeded. This is pre-existing debt, but it directly affects the reliability of repeated shakedown runs and containment-state hygiene.

## Proposed Approach

Refactor containment cleanup to report what it removed, what it skipped, and why. Tighten helper behavior where unreadable or malformed state is currently collapsed into None, and add tests for permission failures, broken entries, and stale-state accounting.

## Acceptance Criteria

- clean_stale_files returns or logs explicit cleanup results rather than silently succeeding when deletions fail
- PermissionError and related OSError cases during stale cleanup are surfaced to callers with actionable context
- Cleanup tests cover undeletable files, broken directory entries, and mixed success/failure batches
- Helper paths used by cleanup no longer collapse materially different failure modes into the same 'missing' result when that would hide operational state

## Evidence

> clean_stale_files has two silent except OSError: continue blocks ... A run where every unlink() raises PermissionError would return success with no log output, indistinguishable from 'nothing to clean'.

<!-- defer-meta {"created_by":"defer-skill","source_ref":"PR #101","source_session":"","source_type":"pr-review","v":1} -->

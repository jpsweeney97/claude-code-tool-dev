# Ticket Plugin CHANGELOG Remediation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all findings from the 2026-03-11 CHANGELOG audit: add missing `[Unreleased]` section, fix one attribution error, and add link definitions.

**Architecture:** Single-file edit to `packages/plugins/ticket/CHANGELOG.md`. No code changes. CHANGELOG.md is a branch-protection exception — editable on `main`.

**Tech Stack:** Markdown, Keep a Changelog 1.1.0 format.

**Source audit:** Conducted 2026-03-11 by a 4-agent evidence team (git historian, PR analyst, handoff archivist, changelog analyst) cross-referencing git history, GitHub PRs #68–#70, and 20 handoff archives.

---

## File Structure

One file modified:

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `packages/plugins/ticket/CHANGELOG.md` | All changes |

---

## Chunk 1: CHANGELOG Remediation

### Task 1: Add `[Unreleased]` section with post-1.4.0 entries

Significant work (PRs #68, #69, #70 + direct pushes for C-series compliance) landed after the 1.4.0 release. This task adds all missing entries.

**Files:**
- Modify: `packages/plugins/ticket/CHANGELOG.md:1-7` (insert after line 6, before the 1.4.0 heading)

- [ ] **Step 1: Insert `[Unreleased]` section**

Insert the following block between line 6 (the blank line after the format declaration) and line 7 (the `## [1.4.0]` heading):

```markdown
## [Unreleased]

### Added

- `DeferredWorkEnvelope` schema validator with JSON Schema-based validation (T-04a, #69)
- `ticket_envelope.py` module: envelope read, field mapping, and lifecycle management for consuming deferred work envelopes (T-04a, #69)
- `DeferredWorkEnvelope` schema documented in ticket contract §11 (T-04a, #69)
- `effort` field in `DeferredWorkEnvelope` schema for sizing deferred work items (T-04b, #70)
- `IngestInput` stage model at dispatch boundary for envelope ingestion pipeline (T-04b, #70)
- `ingest` subcommand in engine runner: read-validate-map-plan-preflight-execute-move pipeline for consuming deferred work envelopes (T-04b, #70)
- `ingest` added to guard hook `VALID_SUBCOMMANDS` allowlist (T-04b, #70)
- `defer` field passed through `_execute_create` to `render_ticket` for envelope-originated tickets (T-04a, #69)

### Changed

- Audit repair default flipped to dry-run; `--fix` flag required for actual file mutations, closing safety bug where `repair_audit_logs` modified files without explicit opt-in (T-03, #69)

### Fixed

- Archived tickets included in blocker resolution and dedup scan — `_list_tickets_with_closed()` helper prevents false "missing" blocker reports and dedup false negatives on done/wontfix tickets (C-003, #68)
- Legacy write gate rejects mutations on pre-v1.0 tickets until migrated via engine; `contract_version` now engine-owned and stamped on all write paths (C-001/C-004)
- `key_file_paths` persisted in YAML frontmatter for round-trip dedup reliability; `dedup_override` bound to `duplicate_of` field (C-002/C-008)
- Full contract shapes enforced for `source`, `defer`, and `key_files` fields before any file mutation (C-005)
- Contract documentation aligned with implementation; agent-preflight hook gate removed (C-006/C-007/C-009/C-010)
- Envelope `move_to_processed` rejects overwrite of existing processed file, preventing silent data loss (code review I-1, #69)
- Envelope move exception catch widened from `FileExistsError` to `OSError` for filesystem robustness (T-04b, #70)
- `envelope_path` containment check and input type validation added to ingest pipeline, preventing path traversal (T-04b, #70)
```

- [ ] **Step 2: Verify insertion placement**

Run:
```bash
head -50 packages/plugins/ticket/CHANGELOG.md
```

Expected: `## [Unreleased]` appears on line 8, followed by the new entries, then `## [1.4.0] — 2026-03-09` appears after the new block.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/ticket/CHANGELOG.md
git commit -m "docs(ticket): add [Unreleased] section with post-1.4.0 entries

Adds 8 Added, 1 Changed, and 8 Fixed entries covering:
- Contract compliance fixes C-001 through C-010 (PR #68 + direct pushes)
- T-03 audit repair safety fix (PR #69)
- T-04a deferred work envelope consumer (PR #69)
- T-04b envelope ingest subcommand (PR #70)

From CHANGELOG audit conducted 2026-03-11."
```

---

### Task 2: Fix dedup window attribution in 1.4.0

The audit found that the dedup entry attributed to #59 conflates two changes: PR #59 changed dedup from YYYY-MM-DD to file mtime, then a separate direct push (`7ada756e`) changed from mtime to `created_at` with end-of-day fallback. The CHANGELOG describes the final state but attributes it entirely to #59.

**Files:**
- Modify: `packages/plugins/ticket/CHANGELOG.md` (the dedup entry under `## [1.4.0]` Fixed section)

- [ ] **Step 1: Fix the attribution**

Find (in the 1.4.0 Fixed section):
```
- Dedup window changed from YYYY-MM-DD date-field day granularity to `created_at` field with end-of-day fallback, closing near-midnight duplicate escape (#59)
```

Replace with:
```
- Dedup window changed from YYYY-MM-DD date-field day granularity to file mtime with second-level precision, closing near-midnight duplicate escape (#59)
- Dedup window refined from file mtime to `created_at` field with end-of-day fallback for cross-filesystem reliability
```

- [ ] **Step 2: Verify the edit landed in the correct version block**

Run:
```bash
grep -n "Dedup" packages/plugins/ticket/CHANGELOG.md
```

Expected: Both dedup entries appear in the `[1.4.0]` section (between `## [1.4.0]` and `## [1.3.0]` headings). No dedup entries in other sections.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/ticket/CHANGELOG.md
git commit -m "fix(ticket): split conflated dedup attribution in CHANGELOG 1.4.0

PR #59 changed dedup to file mtime. A follow-up direct push (7ada756e)
changed from mtime to created_at with end-of-day fallback. Previously
the entry attributed the final state entirely to #59.

From CHANGELOG audit conducted 2026-03-11."
```

---

### Task 3: Add link definitions

Keep a Changelog convention uses `[x.y.z]` headers with link definitions at the bottom for version comparison URLs. Since this repo uses squash merges and has no version tags, the links point to PR listings filtered by merge date range.

**Files:**
- Modify: `packages/plugins/ticket/CHANGELOG.md` (append at end of file)

- [ ] **Step 1: Append link definitions**

Add at the very end of the file (after the last entry):

```markdown

<!-- Version comparison links: no git tags exist for this plugin, so links
     point to the GitHub PR list filtered by merge date range. -->
[Unreleased]: https://github.com/jpsweeney97/claude-code-tool-dev/compare/5fdcc19...HEAD
[1.4.0]: https://github.com/jpsweeney97/claude-code-tool-dev/compare/0c52a89...5fdcc19
[1.3.0]: https://github.com/jpsweeney97/claude-code-tool-dev/compare/4d1b17a...0c52a89
[1.2.0]: https://github.com/jpsweeney97/claude-code-tool-dev/compare/2c5d10c...4d1b17a
[1.1.1]: https://github.com/jpsweeney97/claude-code-tool-dev/compare/61bc733...2c5d10c
[1.1.0]: https://github.com/jpsweeney97/claude-code-tool-dev/compare/cd1ff5a...61bc733
[1.0.0]: https://github.com/jpsweeney97/claude-code-tool-dev/compare/cd1ff5a...cd1ff5a
```

Note: These use the version bump commit SHAs identified by the git historian as boundary markers. They are abbreviated 7-char SHAs — GitHub resolves these correctly.

- [ ] **Step 2: Verify link definitions render**

Run:
```bash
tail -15 packages/plugins/ticket/CHANGELOG.md
```

Expected: Link definitions appear at the bottom, each starting with `[` and containing the GitHub compare URL.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/ticket/CHANGELOG.md
git commit -m "docs(ticket): add version comparison link definitions to CHANGELOG

Uses commit SHAs as version boundary markers since no git tags exist.
[Unreleased] compares from 1.4.0 bump to HEAD.

From CHANGELOG audit conducted 2026-03-11."
```

---

### Task 4: Final verification

- [ ] **Step 1: Verify full CHANGELOG structure**

Run:
```bash
grep -n "^## " packages/plugins/ticket/CHANGELOG.md
```

Expected output (7 version headings in reverse chronological order):
```
8:## [Unreleased]
42:## [1.4.0] — 2026-03-09
...
## [1.3.0] — 2026-03-06
## [1.2.0] — 2026-03-06
## [1.1.1] — 2026-03-05
## [1.1.0] — 2026-03-05
## [1.0.0] — 2026-03-04
```

The exact line numbers will vary. Verify: `[Unreleased]` is first, versions are in descending order.

- [ ] **Step 2: Verify entry counts**

Run:
```bash
grep -c "^- " packages/plugins/ticket/CHANGELOG.md
```

Expected: ~78 entries (60 original + 17 new unreleased + 1 from splitting the dedup entry).

- [ ] **Step 3: Verify no entries leaked between version blocks**

Run:
```bash
awk '/^## \[/{v=$0} /^- .*#(68|69|70)/{print v, $0}' packages/plugins/ticket/CHANGELOG.md
```

Expected: All entries referencing PRs #68, #69, #70 appear under the `## [Unreleased]` heading only. None should appear under `## [1.4.0]` or earlier.

- [ ] **Step 4: Verify link definitions resolve**

Run:
```bash
grep "^\[" packages/plugins/ticket/CHANGELOG.md | tail -7
```

Expected: 7 link definitions matching the 7 version headings (Unreleased + 6 versions).

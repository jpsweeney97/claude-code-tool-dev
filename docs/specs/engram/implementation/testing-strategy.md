---
module: testing-strategy
legacy_sections: ["8"]
authority: implementation
normative: false
status: stub
---

# Testing Strategy

> **Status:** Stub — not yet designed. See [README.md](../README.md) for reading order.

## Scope

What to test at each tier.

## Content

To be designed.

## Pre-resolved Items

Items resolved during open question triage (before S8 design) that constrain the testing strategy:

- **Fragment anchor validation (Q3, from Codex dialogue #23):** The modular spec uses explicit semantic anchors (`{#anchor-hash-merge}`, `{#lazy-session-bootstrap}`, etc.) with relative markdown links. A CI validation script must verify all inter-file fragment links resolve. Use `re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', line)` per file with relative path resolution — bash link validation pipelines produce false positives (confirmed during modularization, Task 17). Exclude `legacy-map.md` and `amendments.md` from stale-reference scans. Filter `FTS5` false positives when grepping for `S[0-9]` patterns.

---
module: foundations
status: active
normative: true
authority: root
date: 2026-03-15
---

# Foundations

## Problem

Specs created during brainstorming routinely reach 2,000–5,000 lines as single files. These monoliths are difficult to reference in Claude conversations — loading the full document consumes context, and there's no way to load only the relevant section without knowing the document's internal structure.

## Solution

Three components form a spec lifecycle:

1. **Shared Contract** — defines the `spec.yaml` schema, file frontmatter rules, claim-to-role derivation, and conventions that both skills conform to
2. **Spec-Writing Skill** (new) — compiles an approved design document into a modular spec with `spec.yaml` and properly-frontmatted files
3. **Spec-Review-Team** (updated) — reads `spec.yaml` to derive authority semantics and map them into internally-derived structural roles for reviewer routing and complexity assessment

Plus a PostToolUse hook as a passive safety net for large file writes.

```
Brainstorming Skill          Spec-Writing Skill         Spec-Review-Team
─────────────────            ──────────────────         ────────────────
design doc (single file)  →  spec.yaml + modular spec  →  validated spec
                                      ↑
                              Shared Contract defines
                              the structure both use
```

**Key architectural decision:** Claims are the only fixed vocabulary authors interact with. Structural roles used for review routing are derived from claims by both skills using a shared derivation table — never declared by spec authors.

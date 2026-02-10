# AGENTS.md — `docs/codex-mcp` Subtree Guidance

## Scope

These instructions apply to everything under:

- `docs/codex-mcp/`

They supplement (not replace) higher-level repository instructions.

## Primary objectives

1. Keep this docs set aligned with official OpenAI Codex documentation.
2. Preserve low-drift structure (single canonical owner for procedural content).
3. Maintain deterministic validation via local docs checks.

## Non-negotiable conventions

### Canonical ownership (avoid duplication)

- Canonical quickstart lives in:
  - `docs/codex-mcp/codex-mcp-master-guide.md#canonical-quickstart`
- Canonical command reference lives in:
  - `docs/codex-mcp/codex-mcp-master-guide.md#canonical-command-reference`
- Other docs should point to those anchors rather than duplicating full procedures/command blocks.

### Link and path style

- Use repo-relative markdown links for local docs.
- Do not introduce absolute local paths (for example `~/...` or `/home/<user>/...`) in markdown content.

### Inspector version pin

- Source of truth:
  - `docs/codex-mcp/checks/pinned-versions.env`
- Do not hardcode a different inspector version in docs without updating this file and related checks.

### Reply identifier wording

- Keep wording consistent with approved spec:
  - `threadId` is canonical.
  - `conversationId` is deprecated compatibility alias.

## Required validation before completion

Run:

```bash
bash docs/codex-mcp/checks/validate-docs.sh
```

This must pass (`DOC001` through `DOC008`) before declaring work complete.

## When editing normative specs

If you touch either spec:

- `docs/codex-mcp/specs/2026-02-09-codex-mcp-server-build-spec.md`
- `docs/codex-mcp/specs/2026-02-09-codex-consultation-skill-implementation-spec.md`

Then keep these synchronized:

1. Tool schema and compatibility behavior (`threadId`/`conversationId`).
2. Decision-lock status and resolved decisions.
3. Any contract claims reflected in:
   - `docs/codex-mcp/specs/README.md`
   - `docs/codex-mcp/references/official-parity-matrix.md`

## Change boundaries

- Prefer edits inside `docs/codex-mcp` only unless explicitly asked to touch other paths.
- Avoid renaming/moving files unless explicitly requested.

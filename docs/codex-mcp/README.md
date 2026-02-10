# Codex MCP Documentation

**Purpose:** Canonical home for all Codex MCP documentation in this repository.

## Start here

1. `./codex-mcp-master-guide.md`
   - Single end-to-end guide (concepts → setup → build → security → operations).

## Key sections

- Specs (normative build contracts): `./specs/`
- Learning path (staged modules): `./learning-path/`
- Cookbooks (copy/adapt recipes): `./cookbooks/`
- Runbooks (day-2 operations): `./runbooks/`
- Security (threat model + controls): `./security/`
- FAQ (quick answers): `./faq/`
- References (deep dive docs): `./references/`
- Assessments (maturity/evidence): `./assessments/`

## Two-layer mental model (server vs skill/client)

- **Server layer:** `./specs/2026-02-09-codex-mcp-server-build-spec.md` defines the MCP server that exposes `codex` and `codex-reply`, including validation, policy, error envelopes, and observability.
- **Skill/client layer:** `./specs/2026-02-09-codex-consultation-skill-implementation-spec.md` defines the `/codex` skill workflow: argument parsing, briefing assembly, tool invocation, failure handling, and assessed relay.

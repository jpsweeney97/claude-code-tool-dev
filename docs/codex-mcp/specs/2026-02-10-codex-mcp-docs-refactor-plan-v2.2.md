# Codex MCP Docs Refactor Plan v2.2 (Official Parity, Multi-Pass, Pinned Inspector)

## Summary
Refactor `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp` into a canonical, low-drift documentation set aligned with official OpenAI docs, with decision-locked specs and local validation guardrails.  
This plan is implementation-ready for a new session and requires no additional product decisions.

## Scope and Constraints
- **In scope:** only `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/**`
- **Out of scope:** code/runtime behavior changes, files outside this subtree, repo-root CI wiring
- **Audience priority:** implementers/operators first
- **Dedup policy:** one canonical procedure per topic
- **Path policy:** keep existing file paths stable (no renames/moves in this implementation pass)

## Locked Constants
- `MCP_INSPECTOR_VERSION=0.20.0`
- `DOCS_PARITY_VERIFIED_DATE=2026-02-10`
- Canonical anchors in master guide:
  - `#canonical-quickstart`
  - `#canonical-command-reference`

## Official Source Baseline (must be cited in parity matrix)
- `https://developers.openai.com/codex/guides/agents-sdk`
- `https://developers.openai.com/codex/mcp`
- `https://developers.openai.com/codex/cli`
- `https://developers.openai.com/codex/cli/reference`
- `https://developers.openai.com/codex/config-reference`
- `https://developers.openai.com/codex/auth`

## Public Interfaces / Contract Changes (Decision-Locked)

### 1) Server spec `codex` input contract
In `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/specs/2026-02-09-codex-mcp-server-build-spec.md`, set normative `codex` schema to:
- required: `prompt`
- optional: `approval-policy`, `base-instructions`, `config`, `cwd`, `include-plan-tool`, `model`, `profile`, `sandbox`
- `config` is open object (`additionalProperties: true`)

### 2) Server spec `codex-reply` compatibility contract
Set normative `codex-reply` schema to:
- required: `prompt`
- optional identifiers: `threadId`, `conversationId`
- validation: require at least one identifier (`anyOf`)
- normalization:
  - use `threadId` if present
  - else map `conversationId -> threadId`
  - if both present and unequal, deterministic `INVALID_ARGUMENT`
  - if both absent/empty, deterministic `MISSING_REQUIRED_FIELD`

### 3) Continuity output contract
Document `structuredContent.threadId` as canonical continuity source; `content` stays compatibility output only.

### 4) Spec governance status
Both specs become **Approved (decision-locked)** and replace “Open Decisions” with “Resolved Decisions”:
- prompt/log retention: debug-gated opt-in only
- redaction failures: fail-closed
- dangerous mode: never auto-escalate
- strategy default: direct invocation when uncertain
- reply continuity: `threadId` canonical, `conversationId` compatibility alias

## Multi-Pass Execution

## Pass 0 — Bootstrap artifacts and constants
**Create**
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/specs/2026-02-10-codex-mcp-docs-refactor-plan-v2.2.md` (this plan)
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/checks/pinned-versions.env`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/references/official-parity-matrix.md`

**Required contents**
- `pinned-versions.env` includes exactly: `MCP_INSPECTOR_VERSION=0.20.0`
- parity matrix includes:
  - verified date
  - one row per parity claim + official URL
  - explicit rows for:
    - deprecated `conversationId` alias behavior
    - canonical `structuredContent.threadId`
    - new MCP config key names (`mcp_servers.<id>.startup_timeout_sec`, `mcp_servers.<id>.tool_timeout_sec`, `mcp_oauth_credentials_store`)

**Gate**
- all three files exist with above content

---

## Pass 1 — Normative spec hardening
**Update**
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/specs/2026-02-09-codex-mcp-server-build-spec.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/specs/2026-02-09-codex-consultation-skill-implementation-spec.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/specs/README.md`

**Exact schema blocks to insert**
- `codex` and `codex-reply` schemas as defined in “Public Interfaces / Contract Changes”
- include explicit normalization algorithm and deterministic error mapping

**Gate**
- no “Open Decisions” heading in either spec
- schemas and normalization rules are identical wherever referenced
- status label is “Approved (decision-locked)”

---

## Pass 2 — Canonicalization and dedup
**Canonical owner**
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/codex-mcp-master-guide.md`

**Update canonical anchors**
- add `<a id="canonical-quickstart"></a>` immediately before quickstart section
- add `<a id="canonical-command-reference"></a>` immediately before command reference section

**Pointerize duplicates**
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/learning-path/02-first-success-30-min.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/references/codex-mcp-server-beginner-to-expert.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/faq/codex-mcp-faq.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/learning-path/README.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/README.md`

**Command pinning**
- only canonical command block includes:
  - `npx @modelcontextprotocol/inspector@0.20.0 codex mcp-server`
- non-canonical docs link to `#canonical-command-reference` instead of duplicating full command blocks

**Gate**
- only master guide contains full quickstart and full command reference procedures
- all pointer docs link to canonical anchors

---

## Pass 3 — Parity cleanup and portability
**Update entire subtree (content edits)**
- remove dead link `https://developers.openai.com/codex/mcp-server`
- replace outdated keys:
  - `mcp_server_startup_timeout_sec` → `mcp_servers.<id>.startup_timeout_sec`
  - `mcp_tool_timeout_sec` → `mcp_servers.<id>.tool_timeout_sec`
  - `mcp_oauth_client_store` → `mcp_oauth_credentials_store`
- replace markdown absolute `/Users/jp/...` links with repo-relative links
- keep CLI terminology aligned (`codex login status`, `--with-api-key`)

**Gate**
- zero occurrences of dead link, outdated keys, and absolute local markdown paths

---

## Pass 4 — Add guardrails and deterministic validator
**Create**
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/checks/validate-docs.sh`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/checks/README.md`

**Validator contract**
- command:
  - `bash /Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/checks/validate-docs.sh`
- script sources:
  - `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/checks/pinned-versions.env`
- fail if `MCP_INSPECTOR_VERSION` unset/empty

**Required checks**
- `DOC001`: forbid `/Users/jp/` in markdown
- `DOC002`: forbid `https://developers.openai.com/codex/mcp-server`
- `DOC003`: forbid “Open Decisions” in the two spec files
- `DOC004`: forbid outdated MCP key names
- `DOC005`: require exactly one `canonical-quickstart` and one `canonical-command-reference` anchor
- `DOC006`: ensure pointer links resolve to master guide anchors
- `DOC007`: ensure canonical inspector command uses `@0.20.0`
- `DOC008`: ensure parity matrix contains required parity rows

**Exit behavior**
- `0` success
- non-zero with failing check IDs and offending file/line output

**Gate**
- validator passes cleanly from repo root

---

## Pass 5 — Final QA and handoff package
**Update**
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/references/official-parity-matrix.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/README.md` (short “how to validate docs” note)

**Deliverables**
- completed parity matrix with final verification timestamp
- pass/fail evidence from `validate-docs.sh`
- short change summary by pass (files touched + outcomes)

**Gate**
- all pass gates satisfied
- handoff artifacts committed (in implementation session)

## Test Cases and Scenarios
- **Schema parity:** `codex` and `codex-reply` properties are consistent across specs/master/reference mentions
- **Compatibility behavior:** `conversationId`-only requests are documented as normalized; mismatch path documented as deterministic rejection
- **Dedup integrity:** full quickstart/command procedures only in master guide
- **Portability:** no absolute local markdown paths
- **Staleness:** no dead official links or outdated MCP keys
- **Validator robustness:** each DOC00x rule fails when intentionally violated and passes when corrected

## Rollback Plan
- one commit per pass (Pass 0..5)
- if a pass fails review, revert only that pass commit
- no path renames means rollback is content-only and low-risk

## Dependencies and Manual Preconditions
- Required tools: `bash`, `rg`
- Manual prerequisite already satisfied: inspector version fixed to `0.20.0`
- No additional manual action needed before implementation starts

## Assumptions and Defaults
- Official parity baseline date is fixed at `2026-02-10`
- Scope remains strictly `docs/codex-mcp`
- Guardrails remain local-doc checks (no repo-root CI changes in this plan)

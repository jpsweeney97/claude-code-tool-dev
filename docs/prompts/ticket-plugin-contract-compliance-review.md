# Contract Compliance Review: Ticket Plugin

## Objective

Systematically verify that the ticket plugin implementation at `packages/plugins/ticket/` faithfully implements its specification at `references/ticket-contract.md`. Your goal is to find discrepancies — behaviors the code has that the contract doesn't specify, behaviors the contract specifies that the code doesn't implement, and ambiguities in the contract that the code resolves in ways that may not match the author's intent.

This is NOT a security review or an architectural review. Those have dedicated prompts. This review is strictly about spec-code fidelity.

## What This Review Catches

1. **Silent drift** — Code that once matched the spec but diverged as one was updated without the other
2. **Ambiguous resolution** — Contract language that is vague or underspecified, where the implementation chose one interpretation but another is equally valid
3. **Undocumented behavior** — Code that handles cases the contract doesn't mention (may be correct but should be documented)
4. **Unimplemented spec** — Contract requirements with no corresponding implementation
5. **Test-spec misalignment** — Tests that verify behavior contrary to the contract (test passes, but is it testing the right thing?)

## Claude Code Background

If you're unfamiliar with Claude Code's extension system, this section explains the two key primitives this plugin uses: **hooks** and **plugins**.

### What is Claude Code?

Claude Code is Anthropic's CLI tool that lets Claude operate as an interactive coding agent — it reads files, writes code, runs commands, and manages projects. Claude Code has an extension system that lets developers customize its behavior.

### Hooks

Hooks are event handlers that fire at specific lifecycle points during a Claude Code session. When Claude is about to use a tool (read a file, run a bash command, write a file), the runtime fires events that hooks can intercept.

The critical hook event for this review is **PreToolUse** — it fires *before* a tool call executes and can **allow**, **deny**, or **escalate** the action. This is how the ticket plugin gates all mutations: a PreToolUse hook on the `Bash` tool inspects every shell command Claude is about to run, and either allows it (with injected trust metadata) or denies it.

**How hooks work:**
1. Claude Code fires an event (e.g., "Claude wants to run `python3 scripts/ticket_engine_user.py classify payload.json`")
2. The hook script receives the event as JSON on stdin (includes `session_id`, `cwd`, `tool_name`, `tool_input`, and optionally `agent_id` if a subagent initiated the action)
3. The script validates the command and returns a JSON decision on stdout:
   - `permissionDecision: "allow"` — proceed
   - `permissionDecision: "deny"` — cancel with a reason fed back to Claude
4. Exit code 0 = proceed (or use JSON decision); exit code 2 = block

### Plugins

A plugin is a self-contained directory of components that extends Claude Code. Plugins bundle together:

- **Skills** — markdown instruction files (SKILL.md) that teach Claude how to perform specific tasks. Invoked via `/skill-name` slash commands. The ticket plugin has two: `/ticket` (create/update/close/reopen) and `/ticket-triage` (health dashboard).
- **Hooks** — event handlers (as described above). The ticket plugin has one PreToolUse hook.
- **Agents** — subagent definitions for autonomous task delegation. The ticket plugin declares none.
- **Scripts** — supporting code that skills and hooks invoke. The ticket plugin's core logic lives here.

Plugins are installed via `claude plugin install` and their components are auto-discovered. The `${CLAUDE_PLUGIN_ROOT}` environment variable resolves to the plugin's installation directory at runtime, used by hooks and skills to locate scripts.

## The Contract

The authoritative specification is `references/ticket-contract.md` (Contract v1.0). It has 10 sections:

| § | Section | Governs |
|---|---------|---------|
| 1 | Storage | File paths, naming, slug rules, bootstrap behavior |
| 2 | ID Allocation | ID format, collision prevention, legacy ID preservation |
| 3 | Schema | Required/optional YAML fields, section guidance, section ordering |
| 4 | Engine Interface | Subcommand signatures, response envelope, exit codes, machine states, error codes |
| 5 | Autonomy Model | Modes, config, request_origin, hook trust, execute provenance, prerequisites, field validation |
| 6 | Dedup Policy | Fingerprint algorithm, normalization, window, override, defense-in-depth |
| 7 | Status Transitions | Transition table, preconditions, normalization |
| 8 | Migration | Legacy generations, field defaults, read-only conversion |
| 9 | Integration | External consumer format, fenced YAML |
| 10 | Versioning | contract_version field, read-all/write-latest |

## Review Method

For each contract section:

1. **Read the spec** — Extract every testable claim (a concrete behavior, constraint, or invariant)
2. **Read the code** — Find the implementation of each claim
3. **Compare** — Classify each claim as: Implemented, Missing, Divergent, Ambiguous, or Undocumented-Extension
4. **Check tests** — For each claim, does a test exist that verifies it? Does the test verify the spec's behavior or the code's behavior (these may differ)?

## Review Instructions

### Phase 1: Storage (Contract §1)

Read `scripts/ticket_paths.py`, `ticket_engine_core.py` (file write sections), and `ticket_render.py`. Verify:

1. **Path locations**: Active tickets in `docs/tickets/`, archived in `docs/tickets/closed-tickets/`, audit trail in `docs/tickets/.audit/YYYY-MM-DD/<session_id>.jsonl`
   - Does the code use exactly these paths?
   - Are they hardcoded or configurable? Does the contract say which?

2. **Path boundary enforcement**: "hook payload files and all CLI `tickets_dir` arguments must resolve inside workspace/project root"
   - Which module enforces this? Is it enforced for all entry points or only some?

3. **tickets_dir resolution**: Contract specifies marker-based project root (nearest `.claude/` or `.git/`), symlink canonicalization before marker lookup, explicit tickets_dir must resolve inside root, no root = policy_blocked
   - Trace the actual resolution logic. Does it match every clause?

4. **File naming**: `YYYY-MM-DD-<slug>.md` with slug rules (first 6 words of title, kebab-case, `[a-z0-9-]` only, max 60 chars, sequence suffix on collision)
   - Where is slug generation implemented? Does it follow all rules?
   - What happens at the boundary (exactly 60 chars, exactly 6 words, title with non-ascii)?

5. **Bootstrap**: "missing `docs/tickets/` → empty result for reads; create on first write"
   - Does every read path handle a missing directory gracefully?
   - Does every write path create the directory if absent?

### Phase 2: ID Allocation (Contract §2)

Read `scripts/ticket_id.py`. Verify:

1. **Format**: `T-YYYYMMDD-NN` — 2-digit daily sequence, zero-padded
   - What happens at NN=99? Does the contract say?
   - Is the date the creation date or today's date?

2. **Collision prevention**: "scan existing tickets for same-day IDs, allocate next NN"
   - What is scanned — file names, file contents, or both?
   - Are archived tickets (`closed-tickets/`) included in the scan?
   - What about legacy IDs — can they collide with new allocations?

3. **Legacy ID preservation**: `T-NNN` (Gen 3), `T-[A-F]` (Gen 2), slugs (Gen 1)
   - Are these patterns recognized in all code paths that accept ticket IDs?
   - Can a legacy ID be confused with a new-format ID?

### Phase 3: Schema (Contract §3)

Read `scripts/ticket_parse.py`, `ticket_render.py`, and `ticket_engine_core.py` (field validation). Verify:

1. **Required fields**: `id`, `date`, `status`, `priority`, `source`, `contract_version`
   - Is every field validated as present on create?
   - Is `contract_version` set to `"1.0"` on write?
   - What happens if a required field is missing on read (existing ticket)?

2. **Optional fields**: `effort`, `tags`, `blocked_by`, `blocks`, `defer`
   - Do defaults match the contract? (`effort=""`, `tags=[]`, `blocked_by=[]`, `blocks=[]`, `defer=null`)
   - Is `defer` structure (`{active: bool, reason: string, deferred_at: string}`) validated?

3. **Field types**: Contract §5 specifies: "title, problem, and reopen_reason must be strings when present. priority, status, and resolution are validated against contract enums before writes. key_file_paths, tags, blocked_by, and blocks must be lists of strings. source must be a dict with string values. key_files must be a list of dicts. defer must be a dict."
   - Is every type constraint enforced? At which pipeline stage?
   - Are violations rejected (need_fields) as specified, or silently coerced?

4. **source field**: `{type: string, ref: string, session: string}`
   - Are all three subfields required?
   - Is `type` an enum or free-form?
   - What values appear in practice vs. what the contract implies?

5. **Section ordering**: Problem → Context → Prior Investigation → Approach → Decisions Made → Acceptance Criteria → Verification → Key Files → Related → Reopen History
   - Does `ticket_render.py` emit sections in this order?
   - Does `ticket_parse.py` accept sections in any order?
   - Is a missing required section an error or a warning? (Contract says "advisory warnings/process failures, not hard runtime schema rejections")

6. **Section-backed fields**: Contract says "update mutates YAML frontmatter only. Section-backed fields are not writable through the update action."
   - Which fields are section-backed?
   - Is this restriction enforced in code?
   - What happens if an update payload includes a section-backed field?

7. **key_file_paths vs. key_files disambiguation**: Contract §4 specifies two distinct fields with different purposes
   - Does the code correctly separate dedup usage (key_file_paths) from rendering usage (key_files)?
   - "If both are present in input, key_file_paths is used for dedup" — is this implemented?
   - "If key_files is omitted, create still succeeds but no Key Files section is rendered" — verified?

### Phase 4: Engine Interface (Contract §4)

Read `scripts/ticket_engine_core.py` and both entrypoints. Verify:

1. **Response envelope**: `{state: string, ticket_id: string|null, message: string, data: object}`
   - Does every code path return this exact shape?
   - Are there paths that return additional top-level keys?
   - Are there paths that omit required keys?

2. **Exit codes**: 0 (success), 1 (engine error), 2 (validation failure)
   - Map each exit code to the code paths that produce it
   - Are all validation failures exit 2? Are all engine errors exit 1?
   - Are there paths that exit with other codes?

3. **Subcommand input/output**: For each of the 4 subcommands (classify, plan, preflight, execute), compare the contract's input/output table against the actual function signatures and return values
   - Are all documented input fields accepted?
   - Are all documented output fields returned?
   - Are there undocumented fields in either direction?

4. **Machine states**: Contract lists 15 (14 emittable, 1 reserved). Enumerate:
   - `ok`, `ok_create`, `ok_update`, `ok_close`, `ok_close_archived`, `ok_reopen`, `need_fields`, `duplicate_candidate`, `preflight_failed`, `policy_blocked`, `invalid_transition`, `dependency_blocked`, `not_found`, `escalate`, `merge_into_existing` (reserved)
   - Does the code emit all 14 emittable states? Are any unreachable?
   - Does the code emit states NOT in this list?
   - Is `merge_into_existing` truly unreachable?

5. **Error codes**: Contract lists 11. Enumerate:
   - `need_fields`, `invalid_transition`, `policy_blocked`, `preflight_failed`, `stale_plan`, `duplicate_candidate`, `parse_error`, `not_found`, `dependency_blocked`, `intent_mismatch`, `origin_mismatch`
   - Are all used in code? Are there error codes in code not in this list?

### Phase 5: Autonomy Model (Contract §5)

Read `scripts/ticket_engine_core.py` (preflight/execute sections), `hooks/ticket_engine_guard.py`, and both entrypoints. Verify:

1. **Modes**: suggest (default), auto_audit, auto_silent (v1.1 only)
   - Is `auto_silent` blocked in code as the contract specifies?
   - Is `suggest` actually the default when no config exists?
   - Are there other mode values the code accepts?

2. **request_origin values**: "user", "agent", "unknown" (fail closed)
   - Does `request_origin="unknown"` actually cause fail-closed behavior?
   - Where is "unknown" produced? Is it a fallback or an explicit value?

3. **Hook trust source**: "agent_id in PreToolUse input is the authoritative signal"
   - Does the hook derive origin solely from `agent_id` presence?
   - What if `agent_id` is present but empty string?

4. **Hook candidate detection**: "guard tokenizes Bash commands with shlex and treats Python invocations targeting any ticket_*.py basename as ticket candidates"
   - Verify the shlex tokenization and basename matching
   - "Only canonical plugin-root entrypoints are allowlisted; non-canonical, wrapped, or unknown ticket script invocations are denied"
   - "Non-ticket Python commands pass through"

5. **Execute provenance**: "execute requires verified hook provenance (hook_injected=True, hook_request_origin matching entrypoint origin, non-empty session_id) for all mutations, both user and agent"
   - Is provenance checked for both user AND agent, as stated?
   - "Non-execute stages (classify, plan, preflight) remain directly runnable without hook metadata" — verified?

6. **Execute prerequisites**: Contract specifies 5 prior-stage artifacts required:
   - `classify_intent` (must match action)
   - `classify_confidence` (must meet origin-specific threshold: 0.5 user, 0.65 agent)
   - `dedup_fingerprint` (create only, must match recomputed value)
   - `target_fingerprint` (non-create, mandatory)
   - `autonomy_config` (agent only, snapshot from preflight)
   - Verify each is checked. Verify thresholds match contract values.

7. **Stage-specific missing-confidence behavior**: "preflight coerces absent classify_confidence to 0.0 and fails the confidence gate; execute preserves absence as null and rejects it as a missing prerequisite"
   - This is a subtle behavioral difference. Is the code consistent with this description?

8. **Agent execute policy reread**: "re-reads live .claude/ticket.local.md policy and blocks if it diverges from the preflight snapshot"
   - What constitutes "diverges"? Is it a field-by-field comparison or a hash comparison?
   - Which fields trigger divergence?

9. **Field validation**: All the type constraints listed in the contract — verify each is enforced and that violations produce `need_fields`, not silent coercion

### Phase 6: Dedup Policy (Contract §6)

Read `scripts/ticket_dedup.py`. Verify:

1. **Fingerprint algorithm**: `sha256(normalize(problem_text) + "|" + sorted(key_file_paths))`
   - Does the code use exactly this formula? Is the `|` separator present?
   - What happens when `key_file_paths` is empty? Is `sorted([])` handled?

2. **Normalization steps** (in order): strip, collapse whitespace, lowercase, remove punctuation except hyphens/underscores, NFC
   - Does the code apply these in this order?
   - Does a different order produce different results for any input?

3. **Test vectors**: The contract provides 5 input/expected pairs. Do the tests verify these exact vectors?

4. **Window**: 24 hours
   - What timestamp is used — ticket creation date, file mtime, or a field value?
   - Is the 24h window inclusive or exclusive at boundaries?

5. **Override**: `dedup_override: true` with matching `ticket_id`
   - What does "matching ticket_id" mean? Matching the duplicate candidate?
   - Who can set `dedup_override` — user only, or also agents?

6. **Defense-in-depth**: "execute stage repeats duplicate checks for create requests"
   - Is this actually implemented? Same algorithm or different?

### Phase 7: Status Transitions (Contract §7)

Read `scripts/ticket_engine_core.py` (transition validation). Verify:

1. **Transition table**: Compare the contract's 10-row table against the code's actual transition logic
   - For each row: Is the transition allowed? Are preconditions checked?
   - Are there transitions the code allows that the table doesn't list?
   - Are there transitions the table lists that the code doesn't implement?

2. **Specific preconditions**:
   - `open → blocked`: requires `blocked_by` non-empty — enforced?
   - `in_progress → done`: requires acceptance criteria present — enforced? What counts as "present"?
   - `blocked → open/in_progress`: requires all `blocked_by` resolved (done or wontfix) — enforced? What about missing references?
   - `done/wontfix → open`: requires `reopen_reason`, user-only — both enforced?
   - `* → wontfix`: no preconditions — actually unrestricted?

3. **"Non-status edits on terminal tickets (done/wontfix) are allowed without reopening"**
   - Is this implemented? Can you update fields on a done ticket without changing status?

4. **"Missing blocker references are invalid and are not treated as resolved"**
   - What happens when `blocked_by` references a ticket ID that doesn't exist?
   - Does the code treat missing as unresolved (blocked) or fail?

5. **Legacy status normalization**: planning→open, implementing→in_progress, complete→done, closed→done, deferred→open (with defer.active: true)
   - Is this normalization applied on read?
   - Is the `defer.active: true` side effect of `deferred` normalization implemented?

### Phase 8: Migration (Contract §8)

Read `scripts/ticket_parse.py` (legacy handling). Verify:

1. **Read-only for legacy formats**: Does the parser read without modifying legacy files?
2. **Conversion on update (with user confirmation)**: Where is user confirmation implemented? How?
3. **Section renames**: For each generation, verify the rename mappings are implemented:
   - Gen 1-3: Summary→Problem
   - Gen 3: Findings→Prior Investigation
   - Gen 4: Proposed Approach→Approach, provenance→source
4. **Field defaults**: Verify each default from the contract table is applied on read:
   - priority→medium, source→{type:"legacy", ref:"", session:""}, effort→"", tags→[], blocked_by/blocks→[]

### Phase 9: Integration & Versioning (Contract §9-10)

Read `scripts/ticket_render.py` and `ticket_parse.py`. Verify:

1. **Fenced YAML format**: Contract says "fenced YAML (```yaml), not YAML frontmatter (---)"
   - Does render output fenced YAML?
   - Does parse accept only fenced YAML, or also frontmatter?

2. **contract_version**: Written as `"1.0"` on all writes
   - Verified in render output?
   - Is it treated as a string, not a float? (YAML pitfall: `1.0` without quotes → float)

3. **Read-all/write-latest**: "Engine reads all versions; writes latest only"
   - What versions can the parser read? Are there version-specific code paths?

### Phase 10: Cross-Cutting Compliance

After completing section-by-section analysis:

1. **Undocumented behavior inventory**: List all behaviors you found in code that have no corresponding contract clause. For each, assess:
   - Is it an intentional extension that should be documented?
   - Is it a bug (behavior that contradicts the contract's spirit)?
   - Is it defensive code that the contract assumes but doesn't state?

2. **Contract gaps**: List all areas where the contract is silent but the code must make a decision. For each, assess:
   - Is the code's choice reasonable?
   - Could a different implementation make a different reasonable choice and still comply?
   - Should the contract be updated to close the ambiguity?

3. **Test-spec alignment**: For test files that verify contract-specified behavior:
   - Do test assertions match the contract or the code? (They may differ)
   - Are there tests that would pass even if the contract requirement were violated?
   - Are there contract requirements with no corresponding test?

## Deliverables

For each finding, provide:

1. **ID**: Sequential (C-001, C-002, ...)
2. **Severity**: High / Medium / Low / Informational
3. **Category**: One of the categories below
4. **Contract reference**: Section number and exact quote from the contract
5. **Code reference**: File path, line numbers, and relevant code snippet
6. **Classification**: One of: Divergent, Missing, Ambiguous, Undocumented-Extension, Test-Spec-Mismatch
7. **Description**: What the discrepancy is
8. **Impact**: What could go wrong if this discrepancy persists
9. **Suggested resolution**: Fix the code, update the contract, or add a test — with rationale
10. **Test coverage**: Whether a test exists and whether it verifies the spec or the code

### Categories

- **Storage** — path locations, naming, slug rules, bootstrap, boundary enforcement
- **ID Allocation** — format, collision, legacy preservation
- **Schema** — field presence, types, defaults, sections, ordering
- **Engine Interface** — response shape, exit codes, subcommand signatures, state/error enums
- **Autonomy** — modes, origin, provenance, prerequisites, policy reread, field validation
- **Dedup** — fingerprint algorithm, normalization, window, override
- **Transitions** — allowed transitions, preconditions, terminal ticket behavior, legacy normalization
- **Migration** — legacy parsing, section renames, field defaults, conversion triggers
- **Format** — fenced YAML, versioning, roundtrip fidelity
- **Cross-Cutting** — undocumented behavior, contract gaps, test-spec misalignment

### Classification Definitions

| Classification | Meaning |
|---------------|---------|
| **Divergent** | Code implements behavior that contradicts a specific contract clause |
| **Missing** | Contract specifies behavior that has no corresponding implementation |
| **Ambiguous** | Contract language is underspecified; code chose one interpretation but others are valid |
| **Undocumented-Extension** | Code implements behavior beyond what the contract specifies (may be correct) |
| **Test-Spec-Mismatch** | Test verifies behavior that contradicts the contract (test may pass but tests the wrong thing) |

### Severity Criteria

| Severity | Definition |
|----------|-----------|
| High | Divergence that produces incorrect output, data corruption, or policy violation — the code does something the spec explicitly says it shouldn't (or vice versa) |
| Medium | Behavioral difference that could surprise users or break assumptions of other components — e.g., field type not validated as spec requires, exit code wrong for a category |
| Low | Minor inconsistency — e.g., default value slightly different, ordering not exactly as specified, edge case unaddressed |
| Informational | Contract ambiguity or undocumented extension that doesn't cause problems but should be documented |

## Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| P0 | `references/ticket-contract.md` | The spec — read this first and extract every testable claim |
| P0 | `scripts/ticket_engine_core.py` | Most contract requirements are implemented here |
| P0 | `hooks/ticket_engine_guard.py` | Implements §5 hook trust and candidate detection |
| P0 | `scripts/ticket_engine_user.py` | Entrypoint — verify §5 origin hardcoding |
| P0 | `scripts/ticket_engine_agent.py` | Entrypoint — verify §5 origin hardcoding |
| P1 | `scripts/ticket_parse.py` | Implements §3 schema parsing, §7 normalization, §8 migration |
| P1 | `scripts/ticket_render.py` | Implements §3 schema rendering, §9 fenced YAML, §10 versioning |
| P1 | `scripts/ticket_id.py` | Implements §2 ID allocation |
| P1 | `scripts/ticket_dedup.py` | Implements §6 dedup policy |
| P1 | `scripts/ticket_trust.py` | Implements §5 trust triple validation |
| P1 | `scripts/ticket_paths.py` | Implements §1 storage paths and boundary enforcement |
| P2 | `scripts/ticket_validate.py` | Implements §5 field validation |
| P2 | `scripts/ticket_audit.py` | Implements §1 audit trail paths |
| P2 | `skills/ticket/references/pipeline-guide.md` | Secondary spec — check for contradictions with contract |
| P3 | `tests/` | Verify test assertions match contract, not just code |

## Constraints

- Read the contract FIRST, completely. Extract a checklist of testable claims before reading any code.
- For each contract claim, find the implementing code. Don't assume it exists — verify.
- When code and contract disagree, report both sides neutrally. Don't assume either is correct.
- Pay special attention to numeric values (thresholds, limits, exit codes) — these are the most likely to silently drift.
- Check that tests verify the contract's behavior, not just the code's current behavior. A test that passes is not evidence of correctness if it asserts the wrong thing.
- Do not report architectural concerns, code quality issues, or security vulnerabilities — those belong in their dedicated reviews. Stay focused on spec-code fidelity.

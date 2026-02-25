# Dialogue Skill Orchestrator — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a `/dialogue` skill that orchestrates parallel context-gathering agents + the existing `codex-dialogue` agent for multi-turn Codex consultations with proactive codebase exploration.

**Architecture:** Two parallel context-gatherers (code explorer + falsifier) produce prefix-tagged findings. The skill deterministically assembles these into a structured briefing (Context/Material/Question) with a sentinel marker. The `codex-dialogue` agent detects the sentinel, skips its own briefing assembly, and runs the multi-turn conversation with a synthesis checkpoint at the end.

**Reference:** `docs/plans/2026-02-19-dialogue-skill-orchestrator.md` (spec, 448 lines, 10 sections, 2x Codex-reviewed)

**Branch:** Create `feature/dialogue-skill-orchestrator` from `main`.

**Test command:** Manual verification — these are instruction documents (`.md` agents and skills), not code. Verification is structural (content checks) and integration (invoke via Task tool / slash command).

**Dependencies between tasks:**
- Tasks 1-4: independent (Wave 1 — can run in parallel)
- Task 5: depends on Tasks 1-4 (Wave 2 — references all Wave 1 deliverables)
- Task 6: depends on Task 5 (final verification)

---

## Task List

### Task 1: Contract amendment + `/codex` cross-reference + shared tag grammar

**Files:**
- Modify: `packages/plugins/cross-model/references/consultation-contract.md` (~line 106-122)
- Modify: `packages/plugins/cross-model/skills/codex/SKILL.md` (frontmatter + ~line 93)
- Create: `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md`

**Why first (Wave 1):** Establishes the `seed_confidence` field and shared grammar that other tasks reference. Independent of gatherer agents and dialogue modifications.

### Task 2: Gatherer A — Code Explorer agent

**Files:**
- Create: `packages/plugins/cross-model/agents/context-gatherer-code.md`

**Why Wave 1:** Independent agent with no dependencies on other deliverables. Follows existing agent patterns (codex-reviewer.md frontmatter).

### Task 3: Gatherer B — Falsifier agent

**Files:**
- Create: `packages/plugins/cross-model/agents/context-gatherer-falsifier.md`

**Why Wave 1:** Independent agent, parallel with Task 2. Most novel component — constrained falsification protocol with AID/TYPE/cap mechanisms.

### Task 4: codex-dialogue agent modifications

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md` (3 insertion points: ~line 57, ~line 88, ~line 395)

**Why Wave 1:** Modifications are additions only. No dependency on gatherer agents or the skill. References the `seed_confidence` field from the contract (Task 1), but both pin from the frozen spec — no execution dependency.

### Task 5: `/dialogue` orchestrator skill

**Files:**
- Create: `packages/plugins/cross-model/skills/dialogue/SKILL.md`

**Why Wave 2:** References gatherer agent names (Tasks 2-3), the `codex-dialogue` agent's external briefing detection (Task 4), `seed_confidence` from contract (Task 1), and the shared grammar (Task 1). Must be written after all referenced components exist.

### Task 6: Final verification

**Files:** None (read-only checks)

**Why last:** End-to-end integration verification after all components are in place.

---

## Task 1: Contract amendment + `/codex` cross-reference + shared tag grammar

**Files:**
- Modify: `packages/plugins/cross-model/references/consultation-contract.md`
- Modify: `packages/plugins/cross-model/skills/codex/SKILL.md`
- Create: `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md`

**Step 1: Broaden consultation contract §6 intro**

In `packages/plugins/cross-model/references/consultation-contract.md`, replace the §6 intro (around line 106-108):

Current:
```markdown
## 6. Delegation Envelope Contract

When the `/codex` skill delegates to the `codex-dialogue` agent, it passes a delegation envelope:
```

Replace with:
```markdown
## 6. Delegation Envelope Contract

When a skill delegates to the `codex-dialogue` agent, it passes a delegation envelope. This applies to `/codex` (direct delegation) and `/dialogue` (orchestrated delegation with pre-gathered context).
```

**Step 2: Add `seed_confidence` to delegation envelope table**

In the same file, add a row to the delegation envelope table after the `scope_envelope` row:

```markdown
| `seed_confidence` | No | Quality signal from pre-dialogue context gathering. Values: `normal` (default), `low`. When omitted, treated as `normal`. |
```

**Step 3: Verify contract changes**

Read the contract §6 and confirm:
- Intro mentions both `/codex` and `/dialogue`
- `seed_confidence` field present with correct values and default

**Step 4: Update `/codex` skill description**

In `packages/plugins/cross-model/skills/codex/SKILL.md`, update the frontmatter description (line 3):

Current:
```yaml
description: Consult OpenAI Codex for second opinions on architecture, debugging, code review, plans, and decisions.
```

Replace with:
```yaml
description: Consult OpenAI Codex for second opinions on architecture, debugging, code review, plans, and decisions. For multi-turn dialogues with proactive context gathering, use /dialogue.
```

**Step 5: Add cross-reference in `/codex` skill body**

In the same file, after the "If uncertain whether to use direct or delegated, default to direct invocation." line (~line 105), add:

```markdown
> **Tip:** The `/dialogue` skill provides an orchestrated multi-turn path with pre-dialogue context gathering. It launches parallel codebase explorers, assembles a structured briefing, and delegates to `codex-dialogue` automatically. Use `/dialogue` when you want thorough, evidence-backed consultations without manually assembling context.
```

**Step 6: Standardize subagent naming in `/codex` skill**

In `packages/plugins/cross-model/skills/codex/SKILL.md`, find any bare `codex-dialogue` subagent_type reference (e.g., at ~line 121) and update to `cross-model:codex-dialogue`. Plugin-provided agents use the `cross-model:` namespace prefix — bare names are pre-plugin legacy.

**Step 7: Create shared tag grammar reference**

Create `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md`:

```markdown
# Prefix-Tagged Line Grammar

Reference for the `/dialogue` skill's assembly logic and gatherer agent output format.

## Grammar

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>]
```

**Fields:**
- `TAG:` — required. One of: `CLAIM`, `COUNTER`, `CONFIRM`, `OPEN`.
- `<content>` — required. The finding text. Everything between the tag colon and the first metadata marker (`@`, `AID:`, `TYPE:`), or end of line.
- `@ <path>:<line>` — citation. File path and line number.
- `AID:<id>` — assumption ID reference (e.g., `AID:A1`). Links finding to a specific assumption from the user's question.
- `TYPE:<type>` — contradiction type. One of the values in the whitelist below.

## Tags

| Tag | Purpose | Citation | AID | TYPE |
|-----|---------|----------|-----|------|
| `CLAIM` | Factual observation about the codebase | Required | Optional | No |
| `COUNTER` | Evidence contradicting a stated assumption | Required | Required | Required |
| `CONFIRM` | Evidence supporting a stated assumption | Required | Required | No |
| `OPEN` | Unresolved question or ambiguity | Optional | Optional | No |

## TYPE Whitelist

Used exclusively with `COUNTER` tag:
- `interface mismatch` — public API doesn't match claimed contract
- `control-flow mismatch` — execution path differs from assumption
- `data-shape mismatch` — data structure contradicts assumed shape
- `ownership/boundary mismatch` — responsibility boundary differs from assumption
- `docs-vs-code drift` — documentation contradicts actual implementation

## Parse Rules

1. Lines not starting with a recognized tag (`CLAIM:`, `COUNTER:`, `CONFIRM:`, `OPEN:`) are **ignored**.
2. `CLAIM`, `COUNTER`, or `CONFIRM` lines missing `@ <path>:<line>` citation are **discarded**.
3. `COUNTER` lines missing `AID:<id>` are **discarded**.
4. `COUNTER` lines missing `TYPE:<type>` are **discarded**.
5. Malformed metadata slots (e.g., `AID:` with no value) are ignored; the line is still parsed if tag and content are valid.
6. Multiple metadata markers on one line: parse left-to-right, first match wins for each field type.
7. Content with embedded `@` symbols (e.g., email addresses): only `@ ` followed by a path-like pattern (`word/word` or `word.ext:digits`) is treated as a citation.

## Assembly Processing Order

When the `/dialogue` skill assembles gatherer outputs:

1. **Parse** — extract tagged lines, ignore untagged
2. **Discard** — remove `CLAIM`/`COUNTER`/`CONFIRM` missing citation; remove `COUNTER` missing `AID:` or `TYPE:`
3. **Cap** — if >3 `COUNTER` items remain, keep first 3 (by appearance order)
4. **Sanitize** — run credential patterns (consultation contract §7) on remaining content
5. **Dedup** — same tag type + citation key across gatherers → keep Gatherer A's. Different tag types at same citation retained. Key = `path:line` normalized: strip leading `./`, lowercase, collapse `//`
6. **Group** — deterministic order (Gatherer A first, then B within each section):
   - Context: `OPEN` + `COUNTER` + `CONFIRM`
   - Material: `CLAIM`
   - Question: user's question verbatim

## Examples

### Gatherer A output (code explorer)

```
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11
CLAIM: Generic token redaction runs unconditionally after format-specific @ redact.py:78
CLAIM: Denylist covers 14 directory patterns and 12 file patterns @ paths.py:22
OPEN: Whether format-specific redaction adds value given generic runs unconditionally
```

### Gatherer B output (falsifier)

```
CONFIRM: Denylist covers OWASP secret categories (AWS, PEM, JWT, GitHub PAT) @ paths.py:22 AID:A1
COUNTER: Format-specific layer has zero matches in 847/969 test cases @ test_redact.py:203 AID:A2 TYPE:interface mismatch
COUNTER: Generic redaction catches all patterns format-specific targets @ redact.py:78 AID:A2 TYPE:control-flow mismatch
OPEN: Whether test fixture coverage reflects production workload distribution AID:A2
```

### Edge cases

```
CLAIM: Uses fcntl.flock for atomic state updates @ nudge_codex.py:65
```
Valid — citation present, no AID/TYPE needed for CLAIM.

```
COUNTER: Pipeline is not thread-safe
```
**Discarded** — missing citation (`@ path:line`).

```
COUNTER: State file in /tmp is volatile @ nudge_codex.py:32 AID:A3
```
**Discarded** — missing `TYPE:`.

```
This is a general observation about the codebase.
```
**Ignored** — no recognized tag prefix.
```

**Step 8: Verify tag grammar file**

Read the created file. Confirm:
- Grammar definition matches spec §4
- All 4 tags documented with metadata requirements
- TYPE whitelist has 5 entries
- Parse rules cover all edge cases from spec
- Assembly processing order matches spec §4 assembly rules
- 8+ examples including edge cases

**Step 9: Commit**

```bash
git add packages/plugins/cross-model/references/consultation-contract.md packages/plugins/cross-model/skills/codex/SKILL.md packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md
git commit -m "feat: contract seed_confidence field, /codex cross-reference, shared tag grammar

Add optional seed_confidence field to consultation contract §6 delegation
envelope. Broaden §6 intro to cover /dialogue skill delegation. Add
cross-reference from /codex to /dialogue for discoverability. Create
shared tag grammar reference for gatherer output format and assembly rules.

Part of dialogue skill orchestrator (spec: docs/plans/2026-02-19)."
```

---

## Task 2: Gatherer A — Code Explorer agent

**Files:**
- Create: `packages/plugins/cross-model/agents/context-gatherer-code.md`

**Step 1: Create Gatherer A agent file**

Create `packages/plugins/cross-model/agents/context-gatherer-code.md`:

```markdown
---
name: context-gatherer-code
description: Question-driven codebase explorer for pre-dialogue context gathering. Launched by /dialogue skill. Emits prefix-tagged lines with citations. Read-only exploration only.
tools: Glob, Grep, Read
model: sonnet
---

# Code Explorer — Context Gatherer

Explore the codebase to find code relevant to a question. Emit findings as prefix-tagged lines for assembly into a consultation briefing.

**Launched by:** The `/dialogue` skill. Do not self-invoke.

## Input

You receive:
- `question` — the user's question (required)
- `key_terms` — extracted search terms (optional; derive your own if absent)

## Procedure

### 1. Identify search targets

Extract key terms, function names, file names, and concepts from the question. If `key_terms` is provided, use those. Otherwise, derive 3-8 search terms.

### 2. Search for relevant files

Use Glob to find files by name patterns (e.g., `**/*redact*`). Use Grep to find files by content (e.g., function names, class names, imports). Start broad, then narrow.

### 3. Read identified files

Read the most relevant files (up to 8 files). Focus on:
- Core implementation files (where the logic lives)
- Type definitions and interfaces
- Configuration and constants

Do not read entire large files. Use Grep to locate relevant sections, then Read with offset/limit.

### 4. Search for related context

Search for:
- Tests related to the identified code (`test_*.py`, `*.test.ts`)
- Configuration files that affect behavior
- Documentation within the code directory

### 5. Emit findings

Emit each finding as a prefix-tagged line (see Output Format below). Target 15-30 tagged lines. Do not exceed 40.

## Output Format

Emit findings as prefix-tagged lines. Each line follows this grammar:

```
TAG: <content> [@ <path>:<line>] [AID:<id>]
```

**Tags you emit:**

| Tag | When to use | Citation required? |
|-----|-------------|-------------------|
| `CLAIM` | Factual observation about the codebase | Yes — `@ path:line` |
| `OPEN` | Unresolved question or ambiguity you discovered | No (but preferred) |

You primarily emit `CLAIM` lines. `OPEN` is for questions you couldn't resolve during exploration.

Do **not** emit `COUNTER` or `CONFIRM` — those are for the falsifier agent.

**Examples:**

```
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11
CLAIM: Generic token redaction runs unconditionally after format-specific @ redact.py:78
CLAIM: 969 tests across 23 test files cover the context injection system @ tests/conftest.py:1
CLAIM: Checkpoint serialization uses HMAC-signed tokens @ checkpoint.py:89
OPEN: Whether format-specific redaction adds value given generic runs unconditionally
```

Every `CLAIM` must include a citation (`@ path:line`). Lines without citations are discarded by the assembler.

## Constraints

- **Read-only.** Do not modify any files.
- **Code focus.** Search code, tests, and configuration. Do not explore `docs/decisions/`, `docs/plans/`, `docs/learnings/`, or git history — those are the falsifier agent's domain.
- **40-line cap.** Do not emit more than 40 tagged lines. If you have more findings, prioritize by relevance to the question.
- **No narrative.** Your output is structured tagged lines, not prose. Any text outside tagged lines is ignored by the assembler.

## Failure Modes

**No relevant files found:** Emit 1-2 `OPEN` items describing what you searched for and why nothing matched. Do not emit zero lines — the assembler needs at least one line to detect that you ran.

Example:
```
OPEN: No files matching "caching" or "cache" found in the codebase
OPEN: Searched patterns: **/*cache*, **/*redis*, grep "lru_cache"
```

**Too many results:** Prioritize files closest to the question's core concern. Prefer implementation over tests. Prefer specific functions over entire modules.
```

**Step 2: Verify Gatherer A structure**

Read the created file. Confirm:
- Frontmatter: `tools: Glob, Grep, Read`, `model: sonnet`
- Purpose statement present
- Input section: `question` + `key_terms`
- 5-step procedure
- Output format with grammar, tag table, and examples
- Constraints: read-only, code focus, 40-line cap, no narrative
- Failure modes: no results and too many results
- Does NOT mention COUNTER or CONFIRM (those are falsifier-only)

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/agents/context-gatherer-code.md
git commit -m "feat: add code explorer context-gatherer agent

Question-driven codebase explorer for pre-dialogue context gathering.
Emits CLAIM and OPEN prefix-tagged lines with citations. Read-only,
40-line cap, code/test/config focus.

Part of dialogue skill orchestrator (spec: docs/plans/2026-02-19)."
```

---

## Task 3: Gatherer B — Falsifier agent

**Files:**
- Create: `packages/plugins/cross-model/agents/context-gatherer-falsifier.md`

**Step 1: Create Gatherer B agent file**

Create `packages/plugins/cross-model/agents/context-gatherer-falsifier.md`:

```markdown
---
name: context-gatherer-falsifier
description: Repo-first assumption tester for pre-dialogue context gathering. Launched by /dialogue skill. Tests stated assumptions against codebase evidence. Emits COUNTER/CONFIRM/OPEN prefix-tagged lines (or CLAIM/OPEN when no assumptions are testable). Read-only.
tools: Glob, Grep, Read
model: sonnet
---

# Falsifier — Context Gatherer

Test assumptions embedded in a question by exploring the codebase independently. Your orientation is repo-first — you explore the codebase to find what's true, then check whether stated assumptions hold.

**Launched by:** The `/dialogue` skill. Do not self-invoke.

## Input

You receive:
- `question` — the user's question (required)
- `assumptions` — list of testable assumptions with IDs (e.g., `A1: "The denylist covers all secret types"`, `A2: "Format-specific redaction is necessary"`). May be empty.

## Procedure

### 1. Review assumptions

If `assumptions` is provided and non-empty, use it as your testing checklist. If empty, skip to the No-Assumptions Fallback below.

### 2. Explore the codebase repo-first

Explore broadly — do not limit yourself to files the question mentions. Start from:
- **Entrypoints:** `__main__.py`, `server.py`, `app.py`, top-level modules
- **Import graphs:** follow imports from entrypoints to understand structure
- **Decision documents:** `docs/decisions/`, `docs/plans/`, `docs/learnings/`
- **Architectural files:** `CLAUDE.md`, `README.md`, directory structure

Read files to understand what the codebase actually does, independent of what the question claims.

### 3. Test each assumption

For each assumption (A1, A2, ...):
- Search for evidence that supports it (`CONFIRM`)
- Search for evidence that contradicts it (`COUNTER`)
- If you find a contradiction, identify the specific contradiction type
- If no grounded evidence exists either way, skip the assumption (abstain)

### 4. Emit findings

Emit each finding as a prefix-tagged line (see Output Format below). Target 10-25 tagged lines. Do not exceed 40.

## No-Assumptions Fallback

When the `assumptions` list is empty (the question contains no testable assumptions):

1. Explore the codebase repo-first as in Step 2
2. Emit `CLAIM` and `OPEN` items about what you discover relevant to the question
3. Do **not** emit `COUNTER` or `CONFIRM` — these require assumption IDs

## Output Format

Emit findings as prefix-tagged lines. Each line follows this grammar:

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>]
```

**Tags you emit:**

| Tag | When to use | Citation | AID | TYPE |
|-----|-------------|----------|-----|------|
| `COUNTER` | Evidence contradicting an assumption | Required | Required | Required |
| `CONFIRM` | Evidence supporting an assumption | Required | Required | No |
| `OPEN` | Unresolved question or ambiguity | Optional | Optional | No |
| `CLAIM` | Factual observation (no-assumptions fallback only) | Required | No | No |

### COUNTER constraints

Every `COUNTER` line must include all three:
1. **Citation** (`@ path:line`) — specific code location
2. **Assumption ID** (`AID:A1`) — which assumption this contradicts
3. **Contradiction type** (`TYPE:<type>`) — from this whitelist:
   - `interface mismatch` — public API doesn't match claimed contract
   - `control-flow mismatch` — execution path differs from assumption
   - `data-shape mismatch` — data structure contradicts assumed shape
   - `ownership/boundary mismatch` — responsibility boundary differs
   - `docs-vs-code drift` — documentation contradicts implementation

**Maximum 3 `COUNTER` items per consultation.** If you find more than 3 contradictions, keep the 3 with strongest evidence (most specific citation, clearest contradiction).

`COUNTER` lines missing citation, AID, or TYPE are **discarded by the assembler**.

### CONFIRM behavior

Emit `CONFIRM` when you find grounded evidence **supporting** an assumption. This is not the default — only emit `CONFIRM` when you have specific code evidence. If an assumption is plausible but you found no specific evidence, abstain (emit nothing for that assumption).

**Examples:**

```
CONFIRM: Denylist covers OWASP secret categories (AWS, PEM, JWT, GitHub PAT, Stripe) @ paths.py:22 AID:A1
COUNTER: Format-specific layer has zero matches in 847/969 test cases @ test_redact.py:203 AID:A2 TYPE:interface mismatch
COUNTER: Generic redaction catches all patterns format-specific targets @ redact.py:78 AID:A2 TYPE:control-flow mismatch
OPEN: Whether test fixture coverage reflects production workload distribution AID:A2
OPEN: No evidence found for or against the claim about performance impact
```

### No-assumptions fallback examples

When `assumptions` is empty:
```
CLAIM: Context injection server exposes 2 MCP tools (process_turn, execute_scout) @ server.py:23
CLAIM: Server requires POSIX (os.name check at startup) @ server.py:47
OPEN: Whether the POSIX requirement is intentional or incidental
```

## Constraints

- **Read-only.** Do not modify any files.
- **Repo-first.** Explore broadly — not limited to files the question mentions.
- **Include decision documents.** Read `docs/decisions/`, `docs/plans/`, `docs/learnings/` — these are your primary domain for understanding architectural intent.
- **No git history.** Do not use Bash for `git log`, `git blame`, or similar. V1 uses file-based exploration only.
- **40-line cap.** Do not emit more than 40 tagged lines.
- **3 COUNTER cap.** Maximum 3 COUNTER items. Prioritize by evidence strength.
- **No narrative.** Structured tagged lines only. Untagged text is ignored.

## Failure Modes

**No relevant evidence found:** Emit 1-2 `OPEN` items describing what you explored and why no evidence was found. Do not emit zero lines.

Example:
```
OPEN: Explored entrypoints, import graph, and docs/decisions/ — no evidence found relevant to the caching question
OPEN: The codebase does not appear to have a caching layer
```

**All assumptions confirmed:** This is a valid outcome. Emit `CONFIRM` for each assumption with evidence. The falsifier is not required to find contradictions — it's required to test honestly.
```

**Step 2: Verify Gatherer B structure**

Read the created file. Confirm:
- Frontmatter: `tools: Glob, Grep, Read`, `model: sonnet`
- Purpose statement: repo-first assumption testing
- Input: `question` + `assumptions` (may be empty)
- Procedure: 4 steps
- No-assumptions fallback: CLAIM/OPEN instead
- Output format: all 4 tags with metadata requirements
- COUNTER constraints: citation + AID + TYPE all required, 3 cap, whitelist
- CONFIRM behavior: only with specific evidence, abstain otherwise
- Constraints: read-only, repo-first, includes decision docs, no git, 40-line cap, 3 COUNTER cap
- Failure modes: no evidence, all confirmed

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/agents/context-gatherer-falsifier.md
git commit -m "feat: add falsifier context-gatherer agent

Repo-first assumption tester for pre-dialogue context gathering.
Emits COUNTER/CONFIRM/OPEN prefix-tagged lines with assumption IDs
and contradiction types. 3-COUNTER cap, citation required, TYPE
whitelist enforced. Falls back to CLAIM/OPEN when no assumptions.

Part of dialogue skill orchestrator (spec: docs/plans/2026-02-19)."
```

---

## Task 4: codex-dialogue agent modifications

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md`

**Step 1: Add external briefing detection**

In `packages/plugins/cross-model/agents/codex-dialogue.md`, after the "Assemble initial briefing" section (after line ~65, after "include `## Material: (none)` if no material applies."), insert:

```markdown

### External briefing detection

When the prompt contains `<!-- dialogue-orchestrated-briefing -->` AND contains `## Context`, `## Material`, and `## Question` sections (all three present, in this order, with non-empty bodies):

1. **Skip briefing assembly** — the `/dialogue` skill already assembled the briefing.
2. **Retain posture selection** from the delegation envelope or prompt.
3. **Retain initial turn construction** — derive `## Question` from the briefing's Question section.
4. Proceed to token safety check.

**Fail-safe:** If the sentinel is absent, or any of the three sections is missing, or the parse is ambiguous: assemble the briefing normally (current standalone behavior). Always fail-safe to normal assembly.

The sentinel `<!-- dialogue-orchestrated-briefing -->` is injected by the `/dialogue` skill and never appears in standalone invocations.
```

**Step 2: Add `seed_confidence` to conversation state**

In the same file, add a row to the conversation state table (after the `turn_history` row, ~line 95):

```markdown
| `seed_confidence` | `normal` | From delegation envelope. Values: `normal`, `low`. Controls early-turn scouting bias. |
```

Also add `seed_confidence` to the Phase 1 parse table (at ~line 36-43) with a row or note indicating it is read from the delegation envelope and defaults to `normal`.

Then, after the "Per-turn state retention" subsection (~line 108), insert:

```markdown

### Low seed confidence behavior

When `seed_confidence` is `low` (set by the `/dialogue` skill when context gathering produced thin results):

- **Turns 1-2:** Compose follow-up prompts that prioritize probing claims where the initial briefing had thin or no evidence. When `process_turn` returns `template_candidates` in turns 1-2, prefer executing scouts (Step 4) even for lower-ranked candidates — the initial briefing needs supplementing.
- **Turns 3+:** Revert to normal follow-up composition priority (scout evidence → unresolved → unprobed claims → weakest claim → posture-driven).

This is a **prompt-level bias** — the context injection server's scout generation and template ranking are unchanged. The agent simply weights early scouting opportunities higher when it knows the initial briefing was thin.

When `seed_confidence` is `normal` or absent: no change to existing behavior.
```

**Step 3: Add synthesis checkpoint**

In the same file, after the "Pre-flight checklist" section (~line 406, after "If any item is missing, fix it before returning output."), insert:

```markdown

### Synthesis checkpoint

After the narrative synthesis and pre-flight checklist, emit a structured checkpoint block:

```
## Synthesis Checkpoint
RESOLVED: <claim> [confidence: High|Medium|Low] [basis: convergence|concession|evidence]
UNRESOLVED: <item> [raised: turn N]
EMERGED: <idea> [source: dialogue-born]
```

**Tags:**
- `RESOLVED` — claims where both sides reached agreement. Include confidence level and the basis for resolution.
- `UNRESOLVED` — items still open at dialogue end. Include the turn number where first raised.
- `EMERGED` — ideas that neither side started with; born from the dialogue itself. Flag as `dialogue-born`.

**Consistency rules:** The checkpoint and narrative synthesis are generated from the same `turn_history` state. Precedence: checkpoint is canonical for structured status, narrative is canonical for explanatory detail.

Cross-reference requirements:
- Every `UNRESOLVED` in the checkpoint **must** appear in the narrative's Open Questions section.
- Every `RESOLVED` in the checkpoint **must** appear in the narrative's Areas of Agreement or Contested Claims section.
- Every `EMERGED` in the checkpoint **must** appear in the narrative's Key Outcomes section.

If any cross-reference is missing, add it before returning output.
```

**Step 4: Add Synthesis Checkpoint to output format template**

In the same file, in the Output Format template section (~line 417-517), add `## Synthesis Checkpoint` as a section after the narrative synthesis template. Include the RESOLVED/UNRESOLVED/EMERGED format to match the synthesis checkpoint specification from Step 3.

**Step 5: Verify modifications**

Read the modified file. Confirm:
- External briefing detection section exists after "Assemble initial briefing"
- Sentinel `<!-- dialogue-orchestrated-briefing -->` documented
- Fail-safe to normal assembly documented
- `seed_confidence` in conversation state table and Phase 1 parse table
- Low seed confidence subsection: prompt-level bias, turns 1-2 vs 3+
- Synthesis checkpoint format after pre-flight checklist
- Synthesis Checkpoint in output format template section
- Consistency rules with cross-reference requirements
- All existing content is unchanged (additions only)

**Step 6: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "feat: add external briefing, seed_confidence, synthesis checkpoint to codex-dialogue

External briefing: detect sentinel + 3 H2 sections, skip assembly.
Fail-safe: ambiguous parse falls back to normal assembly.
seed_confidence: prompt-level bias for early scouting on thin context.
Synthesis checkpoint: RESOLVED/UNRESOLVED/EMERGED structured block
with consistency rules linking checkpoint to narrative sections.

All additions, no removals. Standalone invocation unchanged.

Part of dialogue skill orchestrator (spec: docs/plans/2026-02-19)."
```

---

## Task 5: `/dialogue` orchestrator skill

**Files:**
- Create: `packages/plugins/cross-model/skills/dialogue/SKILL.md`

**Step 1: Create `/dialogue` skill file**

Create `packages/plugins/cross-model/skills/dialogue/SKILL.md`:

```markdown
---
name: dialogue
description: "Multi-turn Codex consultation with proactive context gathering. Launches parallel codebase explorers, assembles a structured briefing, and delegates to codex-dialogue. For quick single-turn questions, use /codex."
argument-hint: '"question" [-p posture] [-n turns] [--profile name]'
user-invocable: true
---

# Dialogue — Orchestrated Codex Consultation

Launch a multi-turn Codex dialogue with proactive context gathering. Two parallel agents explore the codebase before the dialogue starts, assembling a structured briefing that gives Codex richer initial context.

**For quick single-turn questions:** Use `/codex` instead.

## Preconditions

Before proceeding, verify MCP tools are available:
- `mcp__plugin_cross-model_codex__codex` and `mcp__plugin_cross-model_codex__codex-reply`
- `mcp__plugin_cross-model_context-injection__process_turn` and `mcp__plugin_cross-model_context-injection__execute_scout`

If any tool is unavailable, report which tools are missing and stop. Do not attempt to run the pipeline without all 4 tools.

## Arguments

Parse flags from `$ARGUMENTS`:

| Flag | Short | Values | Default |
|------|-------|--------|---------|
| `--posture` | `-p` | `adversarial`, `collaborative`, `exploratory`, `evaluative` | `collaborative` |
| `--turns` | `-n` | 1-15 | 8 |
| `--profile` | — | Named preset from `consultation-profiles.yaml` | none |

Everything after flags is the **question** (required).

**Resolution order:** explicit flags > profile values > defaults.

**Profile resolution:** Profiles set `posture` and `turn_budget` only. Execution controls (`sandbox`, `approval_policy`, `reasoning_effort`) use consultation contract defaults.

**Validation:**
1. Reject unknown flags.
2. Reject invalid enum values for `--posture`.
3. Reject `--turns` outside 1-15.
4. If question is empty after flag extraction, ask the user: "What would you like to discuss with Codex?"

Error format: `argument parsing failed: {reason}. Got: {input!r:.100}`

## Pipeline

### Step 1: Extract assumptions

From the user's question, identify testable assumptions and assign IDs:

- Read the question and list statements that could be true or false about the codebase.
- Assign sequential IDs: A1, A2, A3, ...
- If no testable assumptions exist (e.g., "How does X work?"), pass an empty list.

**Example:**

Question: "Is our redaction pipeline over-engineered? It seems like the format-specific layer is redundant given the generic layer catches everything."

Assumptions:
- `A1: "The generic redaction layer catches everything the format-specific layer catches"`
- `A2: "The format-specific layer is redundant"`

### Step 2: Launch context gatherers

Launch both agents **in parallel** via the Task tool with a 120-second timeout each:

**Gatherer A (code explorer):**
```
Task(
  subagent_type: "cross-model:context-gatherer-code",
  prompt: "Question: {question}\n\nKey terms: {extracted_terms}",
  timeout: 120000
)
```

**Gatherer B (falsifier):**
```
Task(
  subagent_type: "cross-model:context-gatherer-falsifier",
  prompt: "Question: {question}\n\nAssumptions:\n- A1: {assumption_1}\n- A2: {assumption_2}\n...",
  timeout: 120000
)
```

**Timeout handling:** If a gatherer times out (120s), treat as 0 parseable lines. Proceed to the low-output retry in Step 3.

### Step 3: Assemble briefing

Perform **deterministic, non-LLM assembly** of gatherer outputs. Reference: `references/tag-grammar.md` for full grammar and edge cases.

**Processing order:**

**3a. Parse:** Scan each gatherer's output for lines starting with `CLAIM:`, `COUNTER:`, `CONFIRM:`, or `OPEN:`. Ignore all other lines.

**3b. Discard:** Remove:
- `CLAIM`, `COUNTER`, or `CONFIRM` lines missing `@ path:line` citation
- `COUNTER` lines missing `AID:` field
- `COUNTER` lines missing `TYPE:` field
- Lines where the tag is present but no content follows the colon

**3c. Cap:** If more than 3 `COUNTER` lines remain after discard, keep the first 3 (by order of appearance). This ensures valid counters are not displaced by invalid ones that were discarded.

**3d. Sanitize:** Run the consultation contract pre-dispatch credential check (§7) on all remaining line content. If a line contains a credential pattern (AWS key, PEM, JWT, GitHub PAT, etc.), remove that line. This is defense-in-depth — the dialogue agent's own sanitizer is the final gate.

**3e. Dedup:** If both gatherers emit lines with the same tag type citing the same file and line number, keep Gatherer A's version. Different tag types at the same citation are kept (e.g., Gatherer A's `CLAIM` and Gatherer B's `CONFIRM` at the same `path:line` are both retained — they serve different purposes). Normalize the citation key before comparing: strip leading `./`, lowercase the path, collapse `//` to `/`.

**3f. Group:** Assemble into three sections with deterministic ordering (Gatherer A items first, then Gatherer B within each section):

```
<!-- dialogue-orchestrated-briefing -->
## Context
{OPEN items}
{COUNTER items}
{CONFIRM items}

## Material
{CLAIM items}

## Question
{user's question, verbatim}
```

The sentinel `<!-- dialogue-orchestrated-briefing -->` must appear in the briefing. The `codex-dialogue` agent uses it to detect an external briefing.

**3g. Low-output retry:** If a gatherer returned fewer than 4 parseable tagged lines, re-launch that gatherer once with a prompt reinforcing the output format: "Emit findings as prefix-tagged lines per the output format. Each CLAIM must include `@ path:line` citation. Each COUNTER must include `@ path:line` citation, `AID:<id>`, and `TYPE:<type>`." If still below 4 after retry, proceed with available output.

**3h. Zero-output fallback:** If total parseable lines across both gatherers is 0 after retries:

```
<!-- dialogue-orchestrated-briefing -->
## Context
(Context gathering produced insufficient results. Rely on mid-dialogue scouting for evidence.)

## Material
(none)

## Question
{user's question, verbatim}
```

Set `seed_confidence` to `low`.

### Step 4: Health check

Count citations and unique files in the assembled briefing:

| Metric | Threshold | On failure |
|--------|-----------|-----------|
| Total lines with `@ path:line` | >= 8 | Set `seed_confidence` to `low` |
| Unique file paths cited | >= 5 | Set `seed_confidence` to `low` |

If both thresholds pass, `seed_confidence` is `normal`.

`seed_confidence: low` does **not** block the dialogue. It tells the dialogue agent to prioritize early scouting to compensate for thin initial context.

### Step 5: Delegate to codex-dialogue

Launch the `codex-dialogue` agent via the Task tool:

```
Task(
  subagent_type: "cross-model:codex-dialogue",
  prompt: """
    Goal: {user's question}
    Posture: {resolved posture}
    Budget: {resolved turn count}
    seed_confidence: {normal or low}
    scope_envelope: {scope from §3 preflight — allowed roots and source classes}

    {assembled briefing with sentinel}
  """
)
```

**`scope_envelope` construction:** Before delegation, run the consultation contract §3 preflight to determine allowed roots and source classes. Pass the resulting scope envelope to `codex-dialogue`. The scope is immutable once set — on scope breach, the dialogue agent stops and returns a resume capsule per contract §6.

The agent detects the sentinel, skips briefing assembly, and runs the multi-turn conversation.

### Step 6: Present synthesis

Relay the `codex-dialogue` agent's synthesis to the user. Include:
1. The narrative synthesis (convergence, concessions, emergent ideas, open questions)
2. The Synthesis Checkpoint block (RESOLVED/UNRESOLVED/EMERGED)
3. Your own assessment of the dialogue outcomes

## Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| Gatherer count | 2 | Fixed for v1 |
| Gatherer timeout | 120s | Prevents pipeline stall |
| Gatherer output cap | 40 tagged lines each | Noise prevention |
| Low parseable threshold | 4 tagged lines | Triggers reformat retry |
| COUNTER cap | 3 | Falsifier noise prevention |
| Health check: min citations | 8 | Coverage proxy |
| Health check: min unique files | 5 | Breadth proxy |
| Reformat retry budget | 1 per gatherer | One retry, then proceed |

## Failure Modes

| Failure | Recovery |
|---------|----------|
| Gatherer timeout (120s) | Treat as 0 lines, retry once, proceed with available output |
| Both gatherers return 0 lines | Minimal briefing + `seed_confidence: low` |
| Sanitizer removes all content | Minimal briefing + `seed_confidence: low` |
| codex-dialogue fails to start | Report error to user, suggest `/codex` for direct consultation |
| codex-dialogue errors mid-conversation | Agent synthesizes from available `turn_history` (built-in fallback) |
| MCP tools unavailable | Report missing tools and stop |
```

**Step 2: Verify skill structure**

Read the created file. Confirm:
- Frontmatter: name, description, argument-hint, user-invocable (no allowed-tools field — skill delegates via Task tool, not direct MCP calls)
- Description cross-references `/codex`
- Preconditions: 4 MCP tools required
- Arguments: `-p`, `-n`, `--profile` with resolution order
- Pipeline: 6 steps in correct order
- Step 1: assumption extraction with example
- Step 2: parallel gatherer launch with timeout
- Step 3: assembly with all sub-steps (parse, discard, cap, sanitize, dedup, group, sentinel, retry, fallback)
- Step 4: health check with thresholds
- Step 5: delegation with envelope fields (goal, posture, budget, seed_confidence, scope_envelope)
- Step 6: present synthesis
- Constants table
- Failure modes table
- References tag-grammar.md
- Under 500 lines

**Step 3: Count lines**

Run: `wc -l packages/plugins/cross-model/skills/dialogue/SKILL.md`
Expected: Under 500 lines (target ~250-300)

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat: add /dialogue orchestrator skill

Multi-turn Codex consultation with proactive context gathering.
Launches code explorer + falsifier in parallel, assembles briefing
via deterministic prefix-tag parsing, delegates to codex-dialogue
with seed_confidence signal. Sentinel-based external briefing detection.

Part of dialogue skill orchestrator (spec: docs/plans/2026-02-19)."
```

---

## Task 6: Final verification

**Files:** None (read-only checks)

**Step 1: Structural verification — all files exist**

Run:
```bash
ls -la packages/plugins/cross-model/agents/context-gatherer-code.md packages/plugins/cross-model/agents/context-gatherer-falsifier.md packages/plugins/cross-model/skills/dialogue/SKILL.md packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md
```
Expected: All 4 new files exist.

**Step 2: Verify contract amendment**

Read `packages/plugins/cross-model/references/consultation-contract.md` §6. Confirm:
- [ ] Intro says "when a skill delegates" (not just `/codex`)
- [ ] `seed_confidence` field in envelope table

**Step 3: Verify `/codex` cross-reference**

Read `packages/plugins/cross-model/skills/codex/SKILL.md`. Confirm:
- [ ] Description mentions `/dialogue`
- [ ] Body note near invocation strategy section mentions `/dialogue`

**Step 4: Verify codex-dialogue modifications**

Read `packages/plugins/cross-model/agents/codex-dialogue.md`. Confirm:
- [ ] External briefing detection section with sentinel
- [ ] `seed_confidence` in state table
- [ ] Low seed confidence subsection
- [ ] Synthesis checkpoint after pre-flight checklist
- [ ] Consistency rules present

**Step 5: Verify subagent naming convention**

Run:
```bash
grep -n 'subagent_type.*codex-dialogue\|subagent_type.*context-gatherer' packages/plugins/cross-model/skills/dialogue/SKILL.md packages/plugins/cross-model/skills/codex/SKILL.md
```
Expected: All references use the `cross-model:` namespace prefix (e.g., `cross-model:codex-dialogue`, `cross-model:context-gatherer-code`, `cross-model:context-gatherer-falsifier`). No bare names.

If the runtime rejects namespaced names during integration tests (Steps 6-9), fall back to bare names and update all references.

**Step 6: Integration test — Gatherer A**

Invoke Gatherer A via Task tool:
```
Task(subagent_type: "cross-model:context-gatherer-code", prompt: "Question: How does the redaction pipeline work?")
```
Expected: Output contains `CLAIM:` lines with `@ path:line` citations. No `COUNTER` or `CONFIRM` lines.

**Step 7: Integration test — Gatherer B**

Invoke Gatherer B via Task tool:
```
Task(subagent_type: "cross-model:context-gatherer-falsifier", prompt: "Question: Is the redaction pipeline over-engineered?\n\nAssumptions:\n- A1: The denylist covers all secret types\n- A2: Format-specific redaction is redundant")
```
Expected: Output contains `COUNTER:` or `CONFIRM:` lines with `AID:` and `@ path:line`. Any `COUNTER` includes `TYPE:`.

**Step 8: Integration test — codex-dialogue standalone**

Invoke codex-dialogue without sentinel:
```
Task(subagent_type: "cross-model:codex-dialogue", prompt: "Review whether the context injection checkpoint mechanism is over-engineered. Posture: evaluative. Budget: 2.")
```
Expected: Agent assembles its own briefing (no "skip assembly" behavior). Produces synthesis with Synthesis Checkpoint block.

**Step 9: Integration test — full `/dialogue` pipeline**

Invoke: `/dialogue "How does the redaction pipeline work?"`

Expected:
1. Both gatherers launch in parallel
2. Assembly produces briefing with sentinel and Context/Material/Question sections
3. codex-dialogue detects external briefing, runs multi-turn conversation
4. Synthesis includes Synthesis Checkpoint block
5. User sees complete synthesis

---

## Final Verification

Run: `ls packages/plugins/cross-model/agents/context-gatherer-*.md packages/plugins/cross-model/skills/dialogue/SKILL.md packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md`
Expected: 4 files (2 agents + 1 skill + 1 grammar reference)

Run: `wc -l packages/plugins/cross-model/skills/dialogue/SKILL.md`
Expected: Under 500 lines

Run: `grep -c 'seed_confidence' packages/plugins/cross-model/references/consultation-contract.md`
Expected: At least 1

Run: `grep -c 'dialogue-orchestrated-briefing' packages/plugins/cross-model/agents/codex-dialogue.md`
Expected: At least 1

## Summary of Deliverables

| File | New/Modified | What This Plan Adds |
|------|-------------|---------------------|
| `agents/context-gatherer-code.md` | New | Question-driven code explorer with CLAIM/OPEN output |
| `agents/context-gatherer-falsifier.md` | New | Repo-first assumption tester with COUNTER/CONFIRM/OPEN output |
| `skills/dialogue/SKILL.md` | New | Orchestrator: parallel gatherers → assembly → delegation |
| `skills/dialogue/references/tag-grammar.md` | New | Shared grammar reference for assembly and output format |
| `agents/codex-dialogue.md` | Modified | External briefing detection, seed_confidence, synthesis checkpoint |
| `references/consultation-contract.md` | Modified | `seed_confidence` in §6 delegation envelope |
| `skills/codex/SKILL.md` | Modified | Cross-reference to `/dialogue` |

All paths relative to `packages/plugins/cross-model/`.

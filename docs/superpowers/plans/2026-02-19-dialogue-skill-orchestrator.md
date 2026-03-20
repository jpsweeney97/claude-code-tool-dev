# Dialogue Skill Orchestrator

**Date:** 2026-02-19
**Status:** Design Complete
**Purpose:** A `/dialogue` skill that orchestrates multi-turn Codex consultations with proactive context gathering, producing higher-quality dialogues than the current direct-invocation pattern.
**Derived from:** Enhancement discovery session on deployed cross-model plugin (2026-02-19) + 6-turn evaluative Codex dialogue on architecture decisions.

---

## 1. Problem Statement

The cross-model plugin's most powerful feature — multi-turn Codex dialogues with ledger-based claim tracking and mid-conversation evidence gathering — is inaccessible from the user-facing skill surface. Users must know to invoke the `codex-dialogue` agent via the Task tool with the correct subagent type. The `/codex` skill only supports single-turn direct consultations.

Additionally, dialogue quality depends on context quality. The dialogue agent currently receives only what the user provides as input. There is no proactive codebase exploration before the dialogue begins. The context injection system gathers evidence *during* the conversation (mid-dialogue scouting), but the initial briefing is thin — limited to whatever the user includes in their prompt.

### What This System Does

- Provides a user-facing `/dialogue` skill as entry point for multi-turn Codex consultations
- Proactively explores the codebase before the dialogue using parallel context-gathering agents
- Assembles a structured briefing from gathered context using deterministic mechanical assembly
- Delegates the multi-turn conversation to the existing `codex-dialogue` agent
- Cross-references with `/codex` for discoverability between single-turn and multi-turn modes

### What This System Does Not Do

- Replace the existing `/codex` skill (complementary, not a replacement)
- Replace or duplicate the context injection scouting loop (mid-dialogue evidence gathering is unchanged)
- Provide a separate synthesis stage (v1 — synthesis stays inside the dialogue agent)
- Auto-detect whether a question needs dialogue vs. direct mode (user chooses explicitly)

---

## 2. Architecture Overview

### Pipeline

```
User invokes /dialogue "question"
│
├─ Skill: parse flags, extract assumptions from question
│
├─ Parallel context gathering:
│   ├─ Gatherer A (code explorer): question-driven codebase exploration
│   └─ Gatherer B (falsifier): repo-first assumption testing
│
├─ Skill: mechanical assembly (prefix-tagged lines → briefing)
│   └─ Health check: citations ≥ 8, files ≥ 5 (else LOW_SEED_CONFIDENCE)
│
├─ codex-dialogue: Phase 1 (setup) + Phase 2 (conversation) + synthesis checkpoint
│
└─ Skill: present synthesis to user
```

### Design Rationale

The pipeline decomposes a monolithic process (user provides context → dialogue → synthesis) into specialized stages. Each stage has a clear input/output contract and can be improved independently.

**Why parallel gatherers instead of one?** A single context-gatherer must solve two hard problems: "what code is relevant?" and "what assumptions might be wrong?" These require structurally different exploration strategies. Separating them ensures neither is shortchanged.

**Why mechanical assembly instead of LLM synthesis?** The gatherer outputs merge into a briefing for another LLM (the dialogue agent). LLM-based synthesis between two LLM stages adds latency and information loss without proportional value. Deterministic assembly preserves all gathered context.

**Why no separate synthesizer (v1)?** A separate synthesis agent earns its cost only when at least 2 of 4 capabilities are needed: traceability maps, coverage-diff reports, multi-audience outputs, or cross-run normalization. V1 adds a synthesis checkpoint prompt inside the dialogue agent instead.

---

## 3. Components

### 3.1 `/dialogue` Skill (new)

**Plugin path:** `packages/plugins/cross-model/skills/dialogue/SKILL.md`
**Invocation:** `/dialogue "question"` or `/cross-model:dialogue "question"`

**Responsibilities:**
1. Parse flags and positional argument (the question)
2. Extract assumptions from the question (used by Gatherer B)
3. Launch Gatherer A and Gatherer B in parallel via Task tool (120s timeout per gatherer)
4. Perform mechanical assembly of gatherer outputs into briefing (with sanitization — see Section 4)
5. Run health check on assembled briefing
6. Construct delegation envelope: `goal` (user's question), `scope_envelope` (assembled briefing as Context/Material/Question), `seed_confidence` (`normal` or `low`), `posture`, `turn_budget`
7. Launch `codex-dialogue` agent with delegation envelope
8. Present dialogue synthesis to user

**Interaction model:** Immediate launch with defaults. No guided setup. Flags for overrides.

**Flags:**

| Flag | Short | Values | Default |
|------|-------|--------|---------|
| `--posture` | `-p` | `adversarial`, `collaborative`, `exploratory`, `evaluative` | `collaborative` |
| `--turns` | `-n` | 1-15 | 8 |
| `--profile` | none | Named preset from `consultation-profiles.yaml` | none |

**Note:** `-n` (number of turns) avoids collision with `/codex`'s `-t` (reasoning effort).

**Profile resolution:** Explicit flags override profile values. Profile overrides contract defaults. Profiles resolve `posture` and `turn_budget` only. Execution controls (`sandbox`, `approval_policy`, `reasoning_effort`) always use consultation contract defaults — the `/dialogue` skill does not pass these through. If future use cases require execution control overrides, add corresponding flags.

**Cross-references:**
- Skill description mentions: "For quick single-turn questions, use `/codex`"
- `/codex` skill description updated to mention: "For multi-turn dialogues, use `/dialogue`"

### 3.2 Gatherer A: Code Explorer (new agent)

**Plugin path:** `packages/plugins/cross-model/agents/context-gatherer-code.md`
**Launched by:** `/dialogue` skill via Task tool
**Tools:** Glob, Grep, Read (read-only exploration)

**Orientation:** Question-driven. Given the user's question, explore the codebase to find relevant source files, trace execution paths, and identify the code under discussion.

**Procedure:**
1. Identify key terms and concepts from the question
2. Search for relevant files (glob by name patterns, grep by content)
3. Read identified files to understand code structure and behavior
4. Search for related tests, configuration, and documentation
5. Emit findings as prefix-tagged lines

**Output format:** Prefix-tagged lines (see Section 4).

**Scope constraints:**
- Read-only — no file modifications
- Focus on code, tests, and configuration directly relevant to the question
- Do not explore decision documents or git history (that's Gatherer B's falsification surface)
- Cap output at 40 tagged lines to prevent noise

### 3.3 Gatherer B: Falsifier (new agent)

**Plugin path:** `packages/plugins/cross-model/agents/context-gatherer-falsifier.md`
**Launched by:** `/dialogue` skill via Task tool
**Tools:** Glob, Grep, Read (read-only exploration)

**Orientation:** Repo-first. Explore the codebase independently of the question to test the user's stated assumptions. Look at entrypoints, import hubs, decision documents, and architectural boundaries.

**Procedure:**
1. List assumptions from the question (assigned assumption IDs: A1, A2, ...)
2. Explore the codebase repo-first: entrypoints, import graphs, `docs/decisions/`, `docs/plans/`, `docs/learnings/`
3. For each assumption, attempt to find grounded evidence that supports or contradicts it
4. Emit findings as prefix-tagged lines

**Note:** Git history exploration (churn analysis, blame) is deferred to v2. Adding Bash tool access expands the risk surface. V1 relies on file-based exploration only.

**Falsifier constraints:**
- Every `COUNTER` must cite specific code with path:line reference
- Contradiction type from whitelist: `interface mismatch`, `control-flow mismatch`, `data-shape mismatch`, `ownership/boundary mismatch`, `docs-vs-code drift`
- Maximum 3 `COUNTER` items per consultation (prevents adversarial noise)
- If no grounded contradiction exists for an assumption, emit `CONFIRM` with supporting evidence or abstain
- Uncited `COUNTER` items are discarded during assembly

**Output format:** Prefix-tagged lines (see Section 4).

**Scope constraints:**
- Read-only — no file modifications
- Explore broadly (not limited to files the question mentions)
- Include decision documents, architectural files, and learnings
- Cap output at 40 tagged lines

### 3.4 codex-dialogue Agent (modified)

**Plugin path:** `packages/plugins/cross-model/agents/codex-dialogue.md` (existing, modified)
**Changes from current:**

1. **Accept external briefing.** When the agent's prompt contains a pre-assembled briefing with `## Context`, `## Material`, and `## Question` sections, it detects this as an external briefing and uses it directly for Phase 1 setup. Specifically: skip briefing assembly (the skill already did it), but retain posture selection and initial turn construction. When these sections are absent, current standalone behavior is unchanged.

2. **Accept `LOW_SEED_CONFIDENCE` flag.** When the delegation envelope includes `seed_confidence: low`, the agent adjusts its Phase 2 behavior as a **prompt-level bias** (not a server-controlled threshold): compose follow-up prompts that prioritize probing claims where the initial briefing had thin evidence, and prefer scouting opportunities in the first 2 turns when `process_turn` offers them. This is heuristic — the context injection server's `template_candidates` generation is unchanged. The agent cannot lower a scouting threshold because scout generation is server-driven.

3. **Add synthesis checkpoint.** At the end of Phase 3 (synthesis), emit a structured block of traceable claims and unresolved items in addition to the narrative synthesis. Format:
   ```
   ## Synthesis Checkpoint
   RESOLVED: <claim> [confidence: High|Medium|Low] [basis: convergence|concession|evidence]
   UNRESOLVED: <item> [raised: turn N]
   EMERGED: <idea> [source: dialogue-born]
   ```

   **Consistency rule:** The checkpoint and narrative synthesis are generated from the same `turn_history` state. Precedence: checkpoint is canonical for structured status, narrative for explanatory detail. Every `UNRESOLVED` must appear in the narrative's open questions. Every `RESOLVED` must appear in areas of agreement or contested claims. Every `EMERGED` must appear in key outcomes.

Phase 1 (setup), Phase 2 (conversation loop with context injection), and Phase 3 (synthesis) all remain inside this agent. No phase is extracted for v1.

---

## 4. Output Format

### Prefix-Tagged Lines

Both gatherers emit findings as prefix-tagged lines. Each line follows this grammar:

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>]
```

**Fields:**
- `TAG:` — required. One of the recognized tags below.
- `<content>` — required. The finding text.
- `@ <path>:<line>` — citation. Required for `CLAIM`, `COUNTER`, `CONFIRM`. Optional for `OPEN`.
- `AID:<id>` — assumption ID reference (e.g., `AID:A1`). Used by `COUNTER` and `CONFIRM` to reference which assumption is being tested.
- `TYPE:<type>` — contradiction type. Required for `COUNTER`. One of: `interface mismatch`, `control-flow mismatch`, `data-shape mismatch`, `ownership/boundary mismatch`, `docs-vs-code drift`.

**Tags:**

| Tag | Meaning | Citation | AID | TYPE |
|-----|---------|----------|-----|------|
| `CLAIM` | A factual observation about the codebase | Required | Optional | No |
| `COUNTER` | Evidence contradicting a stated assumption | Required | Required | Required |
| `CONFIRM` | Evidence supporting a stated assumption | Required | Required | No |
| `OPEN` | An unresolved question or ambiguity | Optional | Optional | No |

**Parse rules:**
- Lines not starting with a recognized tag are ignored (tolerant parser).
- `COUNTER` lines missing a citation (`@ path:line`) are discarded.
- `COUNTER` lines missing `TYPE:` are discarded.
- Malformed metadata slots (e.g., `AID:` with no value) are ignored; the line is still parsed if the tag and content are present.
- Parser accepts lines with recognized tags and valid content. Everything else is silently dropped.

**Examples:**

```
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11
COUNTER: Format-specific layer processes 0 matches in 847/969 tests @ test_redact.py:203 AID:A2 TYPE:interface mismatch
CONFIRM: Denylist approach covers all OWASP secret categories @ paths.py:22 AID:A1
OPEN: Whether generic redaction subsumes format-specific for the current threat model
```

### Assembly Rules

The skill performs **deterministic, non-LLM assembly** of gatherer outputs into a briefing:

1. Parse tagged lines from both gatherers using the grammar above. Ignore untagged lines.
2. Discard `COUNTER` items missing citations or `TYPE:`.
3. **Sanitize:** Run the consultation contract's pre-dispatch credential check (§7) on all parsed content. Redact or discard lines containing credential patterns. This is defense-in-depth — the dialogue agent's own pre-dispatch sanitizer is the non-negotiable gate, but catching credentials before they enter the briefing is preferable.
4. **Deduplicate:** If both gatherers emit `CLAIM` lines citing the same `path:line`, keep the first occurrence (Gatherer A's). This ensures deterministic output.
5. Group into briefing sections (deterministic order within each section — Gatherer A items first, then Gatherer B):
   - **Context:** `OPEN` items + `COUNTER`/`CONFIRM` items (assumptions surface)
   - **Material:** `CLAIM` items (factual codebase observations)
   - **Question:** Original user question, verbatim
6. If parseable lines from a gatherer are below threshold (< 4 tagged lines), attempt one cheap reformat-only retry (re-launch the gatherer with "emit findings as prefix-tagged lines per the format specification"). If still low after retry, proceed with available output.

**Timeout:** Each gatherer has a 120-second timeout. A gatherer that times out is treated as returning 0 parseable lines (triggering the retry in step 6).

**Zero-output fallback:** If a gatherer returns 0 parseable lines after retry (or both gatherers return 0), assemble a minimal compliant briefing:
- **Context:** "(Context gathering produced insufficient results. Rely on mid-dialogue scouting for evidence.)"
- **Material:** "(none)"
- **Question:** Original user question, verbatim

Set `LOW_SEED_CONFIDENCE` in this case. The dialogue proceeds — it does not abort.

### Health Check

After assembly, before launching the dialogue:

| Metric | Threshold | On failure |
|--------|-----------|-----------|
| Total citations (lines with `@ path:line`) | >= 8 | Set `LOW_SEED_CONFIDENCE` flag |
| Unique files cited | >= 5 | Set `LOW_SEED_CONFIDENCE` flag |

`LOW_SEED_CONFIDENCE` is passed to the dialogue agent. It does not block the dialogue — it adjusts the agent's scouting strategy to compensate for thin initial context.

---

## 5. Configuration

### User-Facing

| Surface | Controls |
|---------|---------|
| Flags on `/dialogue` | `--posture` (`-p`), `--turns` (`-n`), `--profile` |
| Consultation profiles | Named presets in `consultation-profiles.yaml` |
| Local profile overrides | `consultation-profiles.local.yaml` (gitignored) |

### Internal Constants (v1, not user-configurable)

| Constant | Value | Rationale |
|----------|-------|-----------|
| Gatherer count | 2 | Fixed for v1; third is v2 conditional escalation |
| Gatherer timeout | 120s | Prevents pipeline stall on hung exploration |
| Gatherer output cap | 40 tagged lines each | Prevents noise; briefing stays under dialogue context budget |
| Low parseable threshold | 4 tagged lines | Below this triggers reformat retry |
| `COUNTER` cap | 3 per consultation | Prevents adversarial noise from falsifier |
| Health check: min citations | 8 | Proxy for sufficient codebase coverage |
| Health check: min unique files | 5 | Proxy for exploration breadth |
| Reformat retry budget | 1 | One retry on low parseable output; then proceed |

---

## 6. Design Decisions

### D1. Separate skill instead of flag on `/codex`

**Choice:** New `/dialogue` skill rather than `--dialogue` flag on existing `/codex` skill.

**Rationale:** The two modes are fundamentally different workflows. `/codex` is "format and send" (~10 lines of logic). `/dialogue` orchestrates parallel agents, mechanical assembly, and a multi-turn conversation. Combining them makes the skill a router between unrelated code paths. Separate skills maintain clean separation of concerns.

**Alternatives rejected:**
- Flag on `/codex` — routing complexity, mixed documentation
- Auto-detection — unreliable heuristic, removes user control
- Profile-triggered routing — implicit mode switching is surprising

### D2. Structurally independent gatherers (falsifier pattern)

**Choice:** Gatherer B operates as a falsifier, not a second code explorer with different tools.

**Rationale:** Two gatherers exploring the same codebase with the same orientation produce correlated blind spots. Structural independence requires different *orientations*, not just different tools. Gatherer A asks "what code is relevant to this question?" Gatherer B asks "what in this codebase contradicts the assumptions in this question?" These are orthogonal exploration strategies that produce complementary outputs.

**Source:** 6-turn evaluative Codex dialogue (2026-02-19). The falsifier reframing emerged from challenging an initial "contrarian agent" proposal — pure contrarianism produces noise, but falsification with citation requirements and a confirmation option produces grounded, actionable findings.

**Constraint mechanisms:** Assumption IDs, citation requirements, contradiction type whitelist, counter cap at 3, uncited counters discarded, CONFIRM option for valid assumptions.

### D3. Deterministic mechanical assembly (not LLM synthesis)

**Choice:** Gatherer outputs merge via deterministic prefix-tag parsing and section grouping. No LLM involved in assembly.

**Rationale:** The gatherer outputs feed into another LLM (the dialogue agent). LLM-to-LLM pipeline stages introduce information loss and latency. Deterministic assembly preserves all gathered context and adds zero latency beyond parsing. The dialogue agent is capable of handling slightly redundant or verbose briefing sections.

**Source (core decision):** Codex dialogue (2026-02-19). Initial proposal was raw concatenation. Codex challenged this; both converged on structured concatenation with prefix-tagged lines and a tolerant parser.

**V1 operationalization (post-dialogue):** Tag routing rules (CLAIM → Material, COUNTER/CONFIRM/OPEN → Context), retry logic, health check thresholds, dedup/ordering rules, and sanitization pass are spec-defined elaborations of the dialogue's core decision.

### D4. No separate synthesizer for v1

**Choice:** Synthesis stays inside the `codex-dialogue` agent. A synthesis checkpoint prompt is added. No separate `dialogue-synthesizer` agent.

**Rationale:** A separate synthesizer requires serializing the full turn history (claims, evidence, positions across all turns) and re-injecting it into a fresh context window. This adds latency and complexity. The synthesizer earns its cost only when at least 2 of 4 capabilities are needed: traceability maps, coverage-diff reports, multi-audience outputs, or cross-run normalization. None of these are v1 requirements.

**Source (core decision):** Codex dialogue (2026-02-19), turn 6. Both sides agreed a separate synthesizer adds latency without proportional value for v1.

**V1 operationalization (post-dialogue):** The synthesis checkpoint format (`RESOLVED`/`UNRESOLVED`/`EMERGED` with metadata), consistency rules between checkpoint and narrative, and the 4-capability activation criterion for v2 are spec-defined elaborations.

**Change trigger:** When users need synthesizer-specific capabilities (traceability, multi-audience), revisit this decision.

### D5. 2 gatherers for v1, 3 is v2

**Choice:** Exactly 2 parallel context-gatherers in v1. A conditional third gatherer is deferred to v2.

**Rationale:** Each subagent launch costs ~20-60s and significant tokens. 2 parallel gatherers keep pre-dialogue latency under ~60s. The third gatherer's trigger conditions require usage data that doesn't exist yet.

**Change trigger:** After 10+ sessions, review whether gatherer outputs are consistently insufficient. If `LOW_SEED_CONFIDENCE` fires in >30% of consultations, consider adding a third focused gatherer.

---

## 7. Relationship to Existing Components

### What changes

| Component | Change | Impact |
|-----------|--------|--------|
| `codex-dialogue` agent | Accept external briefing, accept `LOW_SEED_CONFIDENCE`, add synthesis checkpoint | Backward compatible — standalone invocation unchanged |
| `/codex` skill description | Add cross-reference to `/dialogue` | Documentation only |

### What's new

| Component | Type | Location |
|-----------|------|----------|
| `/dialogue` skill | Skill (SKILL.md) | `packages/plugins/cross-model/skills/dialogue/SKILL.md` |
| Code explorer agent | Subagent | `packages/plugins/cross-model/agents/context-gatherer-code.md` |
| Falsifier agent | Subagent | `packages/plugins/cross-model/agents/context-gatherer-falsifier.md` |

### What changes (continued)

| Component | Change | Impact |
|-----------|--------|--------|
| Consultation contract (§6) | Add optional `seed_confidence` field to delegation envelope (default: `normal`, values: `normal`, `low`) | Backward compatible — field is optional, omission means `normal` |

**Note:** The existing `/codex` skill does not currently construct `goal` or `scope_envelope` fields per consultation contract §6. This is pre-existing contract non-conformance. The `/dialogue` skill will conform; `/codex` conformance is tracked as separate debt.

### What's unchanged

- Context injection MCP server (scouting loop is mid-dialogue, not affected; `seed_confidence` is agent-side prompt bias, not a server protocol change)
- Codex MCP server
- Consultation profiles
- Hook scripts (codex_guard.py, nudge_codex.py)

---

## 8. V2 Scope (Deferred)

Items explicitly deferred from v1 with their activation criteria:

| Item | Activation criterion |
|------|---------------------|
| Third conditional gatherer | `LOW_SEED_CONFIDENCE` fires in >30% of consultations over 10+ sessions |
| Separate synthesizer agent | User needs at least 2 of: traceability maps, coverage-diff reports, multi-audience outputs, cross-run normalization |
| Rich seed-quality gate (5-parameter) | Simple citation gate proves insufficient for quality prediction |
| Rolling escalation triggers | 50+ sessions of instrumentation data available |
| Configurable evidence limits | Users report hitting caps in real consultations |
| Custom guard patterns (per-org) | Plugin settings pattern (D1 from enhancement backlog) implemented |
| Gatherer B git churn analysis | Requires Bash tool access; needs constrained read-only git mechanism |
| Server-side `seed_confidence` | If agent-side prompt bias proves insufficient, extend context injection protocol `TurnRequest` with `seed_confidence` field |

---

## 9. Open Questions

| Question | Resolution method |
|----------|------------------|
| If `seed_confidence` is extended to the context injection protocol, what specific server behavior does it trigger? | Design decision for context injection protocol v0.3. Not needed for v1 (agent-side prompt bias is sufficient). |
| Does the existing `/codex` skill need `goal`/`scope_envelope` conformance with consultation contract §6? | Pre-existing debt. Track separately from this spec. |

---

## 10. Acceptance Criteria

### Skill invocation

- [ ] `/dialogue "question"` launches the full pipeline (gatherers → assembly → dialogue)
- [ ] `--posture`, `--turns`, `--profile` flags are parsed and applied
- [ ] Missing question prompts user for input

### Context gathering

- [ ] Both gatherers launch in parallel
- [ ] Each gatherer completes within 120s timeout
- [ ] Gatherer A emits `CLAIM` items with citations from question-relevant code
- [ ] Gatherer B lists assumption IDs (A1, A2, ...) from the question
- [ ] Gatherer B emits `COUNTER`/`CONFIRM` items with `AID:` and citations
- [ ] `COUNTER` items include `TYPE:` from the contradiction whitelist
- [ ] Uncited `COUNTER` items are discarded during assembly
- [ ] `COUNTER` items without `TYPE:` are discarded during assembly
- [ ] `COUNTER` items capped at 3
- [ ] When question has no extractable assumptions, Gatherer B explores repo-first and emits `CLAIM`/`OPEN` items instead (no `COUNTER`/`CONFIRM`)

### Assembly and health check

- [ ] Prefix-tagged lines parsed correctly from both gatherer outputs
- [ ] Untagged lines ignored (tolerant parser)
- [ ] Malformed metadata slots ignored; line still parsed if tag and content present
- [ ] Credential patterns in gathered content are sanitized during assembly
- [ ] Duplicate `CLAIM` lines (same `path:line`) are deduplicated (Gatherer A wins)
- [ ] Briefing assembled into Context/Material/Question sections with deterministic ordering (Gatherer A first, then B within each section)
- [ ] Health check sets `LOW_SEED_CONFIDENCE` when citation or file thresholds not met
- [ ] Low parseable output (< 4 tagged lines) triggers one reformat retry
- [ ] Gatherer timeout (120s) treated as 0 parseable lines
- [ ] Both-gatherers-empty produces minimal compliant briefing with `LOW_SEED_CONFIDENCE`
- [ ] Delegation envelope includes `goal`, `scope_envelope`, `seed_confidence`, `posture`, `turn_budget`

### Dialogue integration

- [ ] `codex-dialogue` detects external briefing via `## Context` + `## Material` + `## Question` sections
- [ ] With external briefing: skip briefing assembly, retain posture selection
- [ ] Without external briefing: standalone behavior unchanged
- [ ] `codex-dialogue` accepts `seed_confidence: low` in delegation envelope
- [ ] `LOW_SEED_CONFIDENCE` biases follow-up prompts toward probing thin-evidence claims in first 2 turns
- [ ] Synthesis checkpoint emits `RESOLVED`/`UNRESOLVED`/`EMERGED` items
- [ ] Every `UNRESOLVED` in checkpoint appears in narrative open questions
- [ ] Every `RESOLVED` in checkpoint appears in narrative agreement or contested claims
- [ ] Every `EMERGED` in checkpoint appears in narrative key outcomes
- [ ] Standalone `codex-dialogue` invocation (via Task tool) works unchanged

### Cross-references

- [ ] `/codex` description mentions `/dialogue` for multi-turn
- [ ] `/dialogue` description mentions `/codex` for single-turn

---

## Post-Review Deltas

Intentional divergences between this spec and the implementation plan, introduced during self-review (4 fixes) and Codex review (12 findings). The implementation plan is the execution artifact; this spec is the design document.

| Delta | Spec says | Plan says | Rationale |
|-------|-----------|-----------|-----------|
| Citation discard scope | COUNTER-only citation discard | CLAIM/COUNTER/CONFIRM citation discard | Spec tag table marks citation "Required" for all three. Assembler enforcement was under-specified. Plan is more consistent with the tag table. |
| Dedup scope | Implicit same-citation-key dedup | Same tag type + citation key dedup | Cross-tag dedup conflates CLAIM and CONFIRM at the same path:line, losing information. Narrowing to same-tag-type preserves both. |
| `seed_confidence` naming | `LOW_SEED_CONFIDENCE` (flag-style) | `seed_confidence: low` (field-style) | Plan uses field-style consistent with the delegation envelope table format. Internally consistent. |
| Sentinel detection | "first line" | "present in prompt" | Delegation envelope metadata precedes the briefing in the prompt. First-line check would fail. "Present in prompt" with three-section verification is equally robust. |
| COUNTER AID enforcement | AID "Required" in tag table | AID discard rule in assembler | Spec stated the requirement but assembler didn't enforce it. Plan adds the discard rule for consistency. |

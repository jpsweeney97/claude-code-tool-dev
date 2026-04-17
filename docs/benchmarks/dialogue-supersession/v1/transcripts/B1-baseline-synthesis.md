# B1 Baseline — codex-dialogue Synthesis

**Thread ID:** `019d96d2-4397-79e0-9fd0-77877a44df5a`
**Question:** Is the codex-collaboration MCP tool surface aligned with the normative spec, and what tools are still missing for full completion?
**Posture:** evaluative
**Turns:** 5 of 6 budget
**Mode:** `server_assisted`
**Scope envelope:** `contracts.md`, `delivery.md`, `mcp_server.py` (read-only)

This is the verbatim synthesis returned by the `cross-model:codex-dialogue` subagent after Phase 3 (synthesis assembly from `turn_history`). It is the canonical dialogue output — narrative synthesis + Synthesis Checkpoint block + pipeline-data epilogue.

---

### Conversation Summary
- **Topic:** Alignment of the codex-collaboration MCP tool surface with the normative spec, and what tools remain missing for full completion
- **Goal:** Evaluate surface conformance, identify all gaps, and stress-test the completion inventory
- **Posture:** Evaluative
- **Turns:** 5 of 6 budget
- **Converged:** Yes — natural convergence on 3-way-split framing in turn 5; Codex confirmed earlier conclusions stand with no retractions
- **Trajectory:** `T1:advancing(new_reasoning, expansion) → T2:advancing(new_reasoning, challenge) → T3:advancing(new_reasoning, challenge) → T4:advancing(new_reasoning, challenge) → T5:advancing(expansion)`
- **Evidence:** 0 scouts / 5 turns — the single attempted scout (T1 targeting `codex.dialogue.fork`) timed out; no mid-dialogue evidence gathered. Codex itself cited files outside `allowed_roots` (models.py, dialogue.py, control_plane.py) for its reasoning; those citations strengthened its claims but are *not* agent-verified evidence under this benchmark's scope envelope.
- **Mode:** `server_assisted`

### Key Outcomes

**Surface is NOT fully aligned — requires a 3-way-split inventory, not a simple name count**
- **Confidence:** High
- **Basis:** Emerged from dialogue (T2-T3 challenge). Original briefing framed the question as 5/10 name coverage; Codex's T2 reframe surfaced that "surface alignment" conflates two axes (name registration vs. contract conformance), and T3 added a third category. Final consolidated answer in T5 restructures the inventory as: (1) missing tool names, (2) present-but-partial tools, (3) present-but-contract-ambiguous tools.

**Five missing tool names (axis a) — briefing-confirmed**
- **Confidence:** High
- **Basis:** Convergence — briefing material and Codex's file inspection independently confirmed the same 5 names: `codex.dialogue.fork` (packet 3), `codex.delegate.start` (packet 4), `codex.delegate.poll`, `codex.delegate.decide`, `codex.delegate.promote` (packet 5). No sixth tool gap exists at the top level per contracts.md MCP Tool Surface table.

**`codex.dialogue.read` is a present-but-partial tool — this is the sharpest finding of the session**
- **Confidence:** High
- **Basis:** Emerged from dialogue (T3 best-falsifier, T4 evidence). Codex flagged that the tool summary at contracts.md:24 promises reading "dialogue state, branches, and summaries" but the typed response shape at contracts.md:285 contains only `collaboration_id`, `status`, `turn_count`, `created_at`, `turns` — no branch-bearing fields. This reveals an internal spec inconsistency AND means the tool needs a second delivery pass when fork ships, not just a client-side update.

**`codex.status` is present-but-contract-ambiguous (Case 2: silent-on-closure)**
- **Confidence:** Medium
- **Basis:** Codex proposed (T2), classified into a 3-case drift framework (T3). The extra fields (`required_methods`, `optional_methods`, `errors`) neither clearly violate nor clearly satisfy the Runtime Health contract, because the contract section lacks "these fields only" closure language. Characterized as technical debt requiring contract clarification, not decisive drift.

**Spec gaps exist separately from implementation gaps**
- **Confidence:** Medium
- **Basis:** Emerged from dialogue (T4). Two gaps in the spec itself, independent of what's implemented: (1) contracts.md is internally inconsistent on `codex.dialogue.read` (tool summary promises branches, response shape omits them); (2) delivery.md lacks explicit v1↔packet boundary language — the v1 scope of `codex.dialogue.fork` is inferential, not stated.

### Areas of Agreement

- Five tool names are missing, exactly those listed in the briefing, mapped to packets 3/4/5 (High — converged T1, reinforced T3)
- `codex.dialogue.fork` is deferred post-R2 in planning but its v1 status is not decidable from delivery.md alone (High — converged T1, characterized T4)
- The current R1/R2 deployment profile is intentionally incomplete relative to the full normative spec (High — briefing and Codex concurred T1)
- Input-schema conformance for implemented tools cannot be fully established from spec alone — contracts.md provides mostly result shapes, not request schemas (Medium — single-direction proposal T2, not contested)

### Contested Claims

**Whether "surface alignment" is a meaningful claim without axis-(b) contract conformance check**
- **State:** Resolved disagreement (toward Codex's sharper framing)
- **Final positions:** Tool-name counting alone is insufficient; must include contract conformance of registered tools AND capability completeness within registered tools
- **Resolution basis:** Codex challenged the briefing's single-axis framing at T2; agent's Probe B at T3 pressed for a sixth missing tool, and Codex's falsifier surfaced `codex.dialogue.read` as a partial implementation (the key turning point of the dialogue)
- **Confidence:** High

**Whether `codex.dialogue.read` represents a capability gap or a representation gap**
- **State:** Resolved disagreement
- **Final positions:** It's both — the typed response shape lacks branch-bearing fields entirely (representation gap), and because the tool-level summary promises branch reading, it's also a capability gap relative to the top-level contract promise
- **Resolution basis:** Probe C (T4) forced a choice between "degenerate single-branch placeholder" and "missing shape"; Codex's inspection of contracts.md:285 confirmed the latter
- **Confidence:** High

### Open Questions

- **Whether `codex.dialogue.fork` is "in v1 scope, deferred" vs "out of v1 scope"** (raised T1, characterized T4): unresolvable from `delivery.md` alone. Requires an explicit packet↔v1 boundary sentence in delivery.md or contracts.md. Candidates: "The v1 final MCP surface is the full 10-tool surface"; "v1 ends at R2"; "Packets 3–5 are part of v1 completion"; or "`codex.dialogue.fork` is deferred to post-v1."
- **Whether `codex.status`'s extra fields are intentional additive detail or contract drift** (raised T2, characterized T3): Case-2 ambiguity. Requires contract clarification on whether response objects are open (additive allowed) or closed (strict equivalence required).
- **Input-schema conformance for the 5 registered tools** (raised T2): cannot be established from contracts.md alone because it does not define machine-checkable request schemas.

### Continuation
- **Thread ID:** `019d96d2-4397-79e0-9fd0-77877a44df5a`
- **Continuation warranted:** No — the three remaining unresolved items are all *spec gaps requiring new document language*, not investigations answerable from additional dialogue within `allowed_roots`. Further turns would restate, not advance.
- **Unresolved items carried forward:** fork v1-scope boundary language, codex.status open-vs-closed response policy, request-schema formalization for registered tools — all belong in a spec revision task, not a continuation dialogue
- **Recommended posture for continuation:** N/A (continuation not warranted). If the user later pursues the spec gaps, an **exploratory** posture on a broader-scoped read (contracts.md + decisions.md + any v1-definition doc) would suit it.
- **Evidence trajectory:** none (no scouts executed — the single T1 scout for `codex.dialogue.fork` timed out, and `scout_available` remained false until T2 reset)

### My Assessment

Where I agree with Codex: the 3-way-split framing is genuinely better than my initial briefing's single-axis count, and the `codex.dialogue.read` finding is load-bearing — it means "finish packet 3" isn't a clean separation, because the fork rollout will force a second pass on `codex.dialogue.read`'s response shape. That's a real planning implication for the delivery.md packet structure.

Where I'd qualify Codex: its claims about `models.py:237`, `dialogue.py:965`, and `control_plane.py:129` are outside this benchmark's `allowed_roots` and my agent-side verification failed (scout timed out). Codex appears to have file-system access and cited those files as contextual evidence, but under the scope envelope, those citations function as *testimony*, not *verified evidence*. The core claims (axis (a) count, `codex.dialogue.read` branch omission, `codex.status` extra fields) are all defensible from `contracts.md` + `delivery.md` alone, so the conclusions survive even if implementation citations are set aside.

What emerged from the back-and-forth that neither side started with: the **spec-vs-implementation gap distinction** (T4). The briefing framed this as an implementation completeness question. Codex's Probe D analysis showed that `delivery.md` *itself* lacks the v1↔packet binding sentence, making the fork-scope question unanswerable even with a perfect implementation audit. That's a finding about the *spec* that emerged from a dialogue about the *implementation*.

## Synthesis Checkpoint

```
## Synthesis Checkpoint
RESOLVED: Five tool names are missing from the live MCP server: codex.dialogue.fork, codex.delegate.start, codex.delegate.poll, codex.delegate.decide, codex.delegate.promote [confidence: High] [basis: convergence]
RESOLVED: The live surface is aligned with the R1/R2 delivery profile but NOT with the full normative spec [confidence: High] [basis: convergence]
RESOLVED: codex.dialogue.read is a present-but-partial tool — flat turn-history ships, branch/tree reconstruction deferred, response shape lacks branch-bearing fields [confidence: High] [basis: convergence]
RESOLVED: codex.status is present-but-contract-ambiguous — extra fields not in Runtime Health contract, but contract lacks closure language [confidence: Medium] [basis: convergence]
RESOLVED: "Surface alignment" requires a 3-way inventory split: missing names, present-but-partial, present-but-ambiguous [confidence: High] [basis: convergence]
UNRESOLVED: Whether codex.dialogue.fork is "in v1 scope, deferred" vs "out of v1 scope" — requires new spec language [raised: turn 1]
UNRESOLVED: Whether codex.status extra fields are intentional additive detail or contract drift — requires contract clarification on open vs closed response objects [raised: turn 2]
UNRESOLVED: Input-schema conformance for the 5 registered tools cannot be established without a schema-checking pass beyond these three files [raised: turn 2]
EMERGED: codex.dialogue.read's typed response shape (contracts.md:285) contains NO branch-bearing fields, making it a second-pass gap on an existing tool rather than a client-side update when fork ships [source: dialogue-born]
EMERGED: Spec gaps exist separately from implementation gaps — contracts.md is internally inconsistent on dialogue.read, and delivery.md lacks explicit packet↔v1 boundary language [source: dialogue-born]
EMERGED: Completion inventory requires a 3-way split (missing names / present-but-partial / present-but-ambiguous), not a simple tool-name count [source: dialogue-born]
```

### Pipeline Data

```json
<!-- pipeline-data -->
{
  "mode": "server_assisted",
  "thread_id": "019d96d2-4397-79e0-9fd0-77877a44df5a",
  "turn_count": 5,
  "converged": true,
  "convergence_reason_code": "natural_convergence",
  "termination_reason": "convergence",
  "scout_count": 0,
  "resolved_count": 5,
  "unresolved_count": 3,
  "emerged_count": 3,
  "scope_breach_count": 0
}
```

**Relevant file paths (absolute):**
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py`

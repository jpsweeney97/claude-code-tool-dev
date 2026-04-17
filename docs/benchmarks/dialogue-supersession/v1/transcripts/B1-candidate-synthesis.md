# B1 Candidate — codex-collaboration Synthesis

**Thread ID:** `019d96ff-44b2-7dd3-ae9a-6fe16293f592`
**Collaboration ID:** `86f72ef2-8bb1-42e7-8131-d7cffb58607a`
**Claude Session ID:** `ada31456-78f6-4df7-b5ea-d2bc228f0941`
**Run ID:** `31c68027-f74a-4343-a835-b8aa1e989f5d`
**Question:** Is the codex-collaboration MCP tool surface aligned with the normative spec, and what tools are still missing for full completion?
**Posture:** evaluative
**Turns:** 5 of 6 budget
**Mode:** `agent_local`
**Mode source:** n/a
**Scope envelope:** `contracts.md`, `delivery.md`, `mcp_server.py` (read-only; repo-root containment via seed)

This is the verbatim production synthesis artifact produced by the `codex-collaboration:dialogue-orchestrator` subagent after Phase 3. The orchestrator drove a 5-turn dialogue against Codex over the 3-file benchmark scope, then assembled the canonical `<PRODUCTION_SYNTHESIS>` artifact. This document is a rendering of that artifact (narrative + claims + citations + ledger summary + canonical JSON).

Pre-dialogue briefing metadata: 20 citations across 3 unique files, 0 provenance-unknown, warnings: `["few_files"]` (expected — benchmark constrained scope to 3 files).

---

### Conversation Summary

- **Topic:** Alignment of the codex-collaboration MCP tool surface with the normative spec, and what tools remain missing for full completion
- **Goal:** Evaluate surface conformance, identify all gaps under the 3-file benchmark scope, and produce a two-lens answer that separates contract-lens from milestone-lens verdicts
- **Posture:** Evaluative
- **Turns:** 5 of 6 budget
- **Converged:** Yes — orchestrator concluded at turn 5 before hitting the budget-exhaustion window; no new scoutable atoms emerged in Codex turn 4 (only reinforcements of existing claims); remaining turn would have been a no-op
- **Evidence:** 5 scout hits across 5 turns; 2 grep scope-escapes observed (ripgrep `path` parameter ignored, searched repo-wide instead of restricted to allowed file) — below the 3-escape terminal threshold
- **Mode:** `agent_local` (orchestrator-driven agent-local dialogue; no server-assisted journaling path)

### Key Outcomes

**Surface alignment is lens-dependent — flat "5/10 coverage" framing conflates two distinct authority domains**
- **Confidence:** High
- **Basis:** Emerged from dialogue. contracts.md carries `authority:contracts` (interface definition) and delivery.md carries `authority:delivery` (implementation plan, compatibility policy, build sequence). Against the contract the server is NOT aligned (5 of 10 tools). Against the R2 milestone the server IS aligned — R2 acceptance gate at delivery.md:227-236 lists exactly the 5 tools currently implemented.

**Five missing tool names relative to the full normative surface — briefing-confirmed, dialogue-reinforced**
- **Confidence:** High
- **Basis:** Pre-dialogue briefing and Codex's file inspection independently confirmed the same 5 tools: `codex.dialogue.fork` (post-R2 packet 3, ticket `T-20260330-04`), `codex.delegate.start` (packet 4, `T-20260330-05`), `codex.delegate.poll` / `codex.delegate.decide` / `codex.delegate.promote` (packet 5, `T-20260330-06`). No disagreement across any turn.

**Current implementation is R2-complete on its exposed tool surface, but non-surface R2 obligations remain unverified within benchmark scope**
- **Confidence:** High for the surface claim; Medium for the non-surface claim (unverified)
- **Basis:** delivery.md:238-245 R1/R2 Deployment Profile explicitly names the 5 implemented tools as the "implemented surface." R2 additionally requires journal-before-dispatch, idempotent replay, audit event emission, and context-assembly reuse (delivery.md:216-235) — these cannot be verified from the 3 allowed files because mcp_server.py is a thin routing layer delegating behavior to a dialogue controller and control plane.

**"Full completion" is not a single milestone — completion is staged**
- **Confidence:** High
- **Basis:** Emerged from dialogue (COUNTER A4 in pre-briefing, confirmed via delivery.md:248-262). The spec stages completion across R1, R2, and post-R2 packets 2a through 6/7. delivery.md:262: "Dialogue is the adoption gate. The execution domain is the completion gate." Any "full completion" answer must cite the packet/milestone being referenced.

**mcp_server.py is intentionally thin routing — response-shape conformance cannot be verified from the server file alone**
- **Confidence:** High (supported by direct citation)
- **Basis:** mcp_server.py:233-274 `_dispatch_tool` routes `status`/`consult` to `self._control_plane` methods and `dialogue.*` to `self._ensure_dialogue_controller()`. No inline journaling, audit, or context-assembly logic. Response-shape fidelity lives in the controller, outside the benchmark's allowed scope.

**Compatibility Policy section applies to Codex CLI, not to the Claude-facing MCP surface**
- **Confidence:** High
- **Basis:** delivery.md:67-141 — Compatibility Policy pins Codex CLI 0.117.0, vendored app-server schema, and required upstream app-server methods (`thread/start`, `thread/resume`, `thread/fork`, `thread/read`, `turn/start`, `turn/interrupt`). These are upstream dependencies, not the 10-tool Claude-facing surface. Conflating them is a common misreading.

### Areas of Agreement

- 10 tools are defined in contracts.md; 5 are implemented in mcp_server.py (High — converged turn 1, reinforced across every subsequent turn)
- The 5 missing tools map to post-R2 packets 3/4/5 with specific ticket IDs (High — converged, no contestation)
- `codex.dialogue.fork` is explicitly deferred from R2 per delivery.md (High — converged turn 1)
- contracts.md and delivery.md are both active and normative but encode distinct authority domains (High — converged turn 3)
- The benchmark's 3-file scope is insufficient to verify non-surface R2 obligations (Medium — agreed as unverified)

### Contested Claims

**Whether "full completion" is a defined target in delivery.md**
- **State:** Resolved (toward COUNTER / nuanced framing)
- **Final positions:** Pre-briefing assumption A4 presumed delivery.md defines "full completion" as a single milestone. Falsifier's COUNTER at delivery.md:153 established that delivery.md stages completion across 7 delivery steps and multiple runtime milestones, with no single "full completion" label. Codex converged on the staged-completion framing in turn 4.
- **Resolution basis:** Direct citation of delivery.md:248-262 ("Dialogue is the adoption gate. The execution domain is the completion gate.")
- **Confidence:** High

**Whether cross-document precedence is specified anywhere in the allowed scope**
- **State:** Unresolved (ambiguous)
- **Final positions:** Claim 10 of the final ledger — "No explicit cross-document precedence rule exists in the allowed sources for resolving contracts.md vs delivery.md authority conflicts." Neither supported nor contradicted within the 3-file scope. The absence is itself the finding — a spec gap, not an implementation gap.
- **Resolution basis:** Inconclusive due to grep scope-escapes; claim status is `ambiguous` rather than `supported` or `unverified`.
- **Confidence:** Medium (the absence is well-supported; the generalization to "no such rule exists anywhere" is not, because the benchmark scope was limited)

### Open Loose Ends

- **Non-surface R2 acceptance gates** (journal-before-dispatch, idempotent replay, audit event emission, context-assembly reuse) are specified at delivery.md:216-235 but require reading the dialogue controller and control plane to verify. Outside benchmark scope.
- **Response-shape conformance for the 5 implemented tools** — contracts.md:222 defines typed response shapes; the dispatch in mcp_server.py is thin routing, so conformance lives in the controller. Not verifiable from the 3-file scope.
- **Stability/immutability of the 10-tool contract table** — no language within the allowed scope promises the table is stable across future packet landings. Future packets could legitimately amend contracts.md.
- **Grep scope-escape behavior** — two instances observed during the dialogue where the ripgrep `path` parameter was ignored and the tool searched repo-wide. Below threshold, but worth flagging as a containment weakness.

### Canonical Production Synthesis Artifact

```json
{
  "objective": "Is the codex-collaboration MCP tool surface aligned with the normative spec, and what tools are still missing for full completion?",
  "mode": "agent_local",
  "mode_source": null,
  "termination_code": "convergence",
  "converged": true,
  "turn_count": 5,
  "turn_budget": 6,
  "final_claims": [
    {
      "text": "contracts.md is the active normative authority for the Claude-facing MCP tool surface and enumerates 10 tools",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/contracts.md", "lines": "1-10, 18-29"}
    },
    {
      "text": "mcp_server.py registers and dispatches exactly 5 tools: codex.status, codex.consult, codex.dialogue.start, codex.dialogue.reply, codex.dialogue.read",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/codex-collaboration/server/mcp_server.py", "lines": "15-100"}
    },
    {
      "text": "mcp_server.py dispatch is thin routing — dialogue behavior is delegated to a dialogue controller and consult to a control plane; the server file alone does not inline journaling, audit, or context-assembly logic",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/codex-collaboration/server/mcp_server.py", "lines": "233-274"}
    },
    {
      "text": "contracts.md and delivery.md are both active and normative but have distinct authority domains (authority:contracts for interface definitions vs authority:delivery for implementation plan, compatibility policy, build sequence, and test strategy)",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "lines": "1-10"}
    },
    {
      "text": "No stability/immutability language exists within the allowed 3-file scope for the 10-tool MCP contract table — the 10-tool list is best read as a current snapshot, not a permanence guarantee",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "lines": "149-161, 248-262"}
    },
    {
      "text": "delivery.md Compatibility Policy section is scoped to Codex CLI version pinning and upstream app-server methods (thread/start, turn/start, etc.), not to the Claude-facing MCP tool surface",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "lines": "67-141"}
    },
    {
      "text": "R2 acceptance gate for MCP exposure matches the current 5-tool implemented surface with serialized dispatch; delegation, promotion, hook-guard, and fork are explicitly deferred from R2",
      "final_status": "unverified",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "lines": "227-245"}
    },
    {
      "text": "The 5 currently-missing tools are codex.dialogue.fork (post-R2 packet 3 / T-20260330-04), codex.delegate.start (packet 4 / T-20260330-05), and codex.delegate.poll/.decide/.promote (packet 5 / T-20260330-06)",
      "final_status": "unverified",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "lines": "220-225, 248-262"}
    },
    {
      "text": "delivery.md distinguishes adoption from completion: dialogue (R2) is the adoption gate; the execution domain is the completion gate. There is no single 'full completion' milestone — work is staged across R1, R2, and post-R2 packets 2a through 6/7",
      "final_status": "unverified",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "lines": "248-262"}
    },
    {
      "text": "No explicit cross-document precedence rule exists in the allowed sources for resolving contracts.md vs delivery.md authority conflicts",
      "final_status": "ambiguous",
      "representative_citation": null
    }
  ],
  "synthesis_citations": [
    {"path": "docs/superpowers/specs/codex-collaboration/contracts.md", "line_range": "18-29", "snippet": "MCP Tool Surface table enumerating all 10 normative tools: codex.consult, codex.dialogue.start, codex.dialogue.reply, codex.dialogue.fork, codex.dialogue.read, codex.delegate.start, codex.delegate.poll, codex.delegate.decide, codex.delegate.promote, codex.status", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/mcp_server.py", "line_range": "15-100", "snippet": "TOOL_DEFINITIONS list registers exactly 5 tools: codex.status, codex.consult, codex.dialogue.start, codex.dialogue.reply, codex.dialogue.read", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/mcp_server.py", "line_range": "233-274", "snippet": "_dispatch_tool routes status/consult to self._control_plane methods and dialogue.* to self._ensure_dialogue_controller() — thin routing only, no inline journaling/audit/context-assembly", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "line_range": "1-10", "snippet": "Frontmatter: module: delivery / status: active / normative: true / authority: delivery — scoped to implementation plan, compatibility policy, build sequence, and test strategy", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "line_range": "220-236", "snippet": "R2 Deferred items include codex.dialogue.fork, delegation runtime/worktree/promotion, hook-guard; R2 acceptance gate: 'MCP server exposes all R2 tools (dialogue.start/.reply/.read) plus R1 tools (status, consult) with serialized dispatch'", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "line_range": "238-245", "snippet": "R1/R2 Deployment Profile: 'Implemented surface: codex.status, codex.consult, codex.dialogue.start, codex.dialogue.reply, codex.dialogue.read' — dev-repo internal use, delegation/promotion/hook-guard out of scope", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "line_range": "248-262", "snippet": "Post-R2 Supersession Packets: 2a/2b (plugin shell, safety), 3 (dialogue fork, T-20260330-04), 4 (execution foundation, T-20260330-05), 5 (promotion + delegate UX, T-20260330-06), 6/7 (analytics, cutover, T-20260330-07). 'Dialogue is the adoption gate. The execution domain is the completion gate.'", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/delivery.md", "line_range": "67-141", "snippet": "Compatibility Policy section — baseline Codex CLI 0.117.0, vendored schema at tests/fixtures/codex-app-server/<version>/, required methods (thread/start, thread/resume, thread/fork, thread/read, turn/start, turn/interrupt) are upstream Codex app-server methods, not the Claude-facing MCP tool surface", "citation_tier": "dialogue"}
  ],
  "final_synthesis": "The answer depends on which lens you apply — the current documentation encodes two different authority domains that yield opposite verdicts, and conflating them is a category error.\n\nContract lens (contracts.md, authority:contracts): NOT aligned. contracts.md is the active normative authority for the Claude-facing MCP interface and defines a 10-tool surface (contracts.md:18-29). mcp_server.py registers and dispatches only 5 of those tools (mcp_server.py:15-100, 233-274). Against the contract, the surface is incomplete.\n\nMilestone lens (delivery.md, authority:delivery): ALIGNED for the current R2 rollout target, with caveats. delivery.md scopes R2 as the minimum dialogue surface minus fork, sets an acceptance gate of exactly the 5-tool surface (3 dialogue + 2 R1) with serialized dispatch (delivery.md:227-236), and the R1/R2 Deployment Profile states the implemented surface is exactly those 5 tools (delivery.md:238-245). Delegation, promotion, fork, and hook-guard are explicitly deferred from R2. So the current implementation meets R2's tool-exposure gate.\n\nMissing tools for full completion (snapshot-relative): 5 tools. codex.dialogue.fork is deferred from R2 and assigned to post-R2 packet 3 (ticket T-20260330-04). codex.delegate.start belongs to packet 4 / execution-domain foundation (T-20260330-05). codex.delegate.poll, codex.delegate.decide, and codex.delegate.promote belong to packet 5 / promotion and delegate UX (T-20260330-06). Importantly, 'full completion' is not a single milestone in delivery.md — work is staged across R1, R2, and post-R2 packets 2a through 6/7, with delivery.md:262 stating 'Dialogue is the adoption gate. The execution domain is the completion gate.'\n\nLoad-bearing caveat — snapshot relativity: Within the allowed scope (contracts.md, delivery.md, mcp_server.py), there is no language promising stability or immutability of the 10-tool contract table across future packet landings. delivery.md's Compatibility Policy section (lines 67-141) is scoped entirely to Codex CLI version pinning and upstream app-server method compatibility, not to the Claude-facing MCP tool surface. The 5-tools-missing answer is therefore accurate at this repo snapshot; a future packet could legitimately amend contracts.md to retire or merge tools.\n\nUnresolved within benchmark scope: mcp_server.py is a thin routing layer — dialogue behavior is delegated to a dialogue controller and consult to a control plane. The R2 acceptance gates for non-surface obligations (journal-before-dispatch, idempotent replay, audit event emission, context-assembly reuse) are specified in delivery.md:216-235 but cannot be verified from the three allowed files alone. The milestone-lens verdict is therefore 'tool-surface aligned,' not 'full R2 acceptance-complete.'\n\nRecommended framing for the user: The flat answer '5 tools aligned, 5 missing' risks misleading readers by collapsing the two lenses. The accurate framing is: the server is R2-aligned on the currently targeted 5-tool surface and serialized dispatch, it is not contract-complete against the current 10-tool snapshot, and some non-surface R2 acceptance gates remain unverified within the benchmark scope.",
  "ledger_summary": "Convergence reached at turn 5 (under turn_budget=6). 15 total claims registered across 4 Codex turns. 6 claims supported with direct citations from allowed 3-file scope; 1 ambiguous; 8 unverified but reinforced across turns without contradiction. 2 grep scope-escapes observed (tool ignored path parameter, searched repo-wide) — below threshold=3, not terminal. Key supported findings: 10-tool normative contract (contracts.md:18-29); 5-tool implementation (mcp_server.py:15-100, 233-274); distinct authority frontmatter between contracts and delivery; no stability language for the MCP tool table within allowed scope; Compatibility Policy scoped to Codex CLI not MCP surface."
}
```

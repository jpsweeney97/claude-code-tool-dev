# Structural-Cognitive Review Findings

**Reviewer:** structural-cognitive
**Plugin:** `packages/plugins/cross-model/` v3.1.3
**Date:** 2026-03-26

---

## Summary

4 findings across Cognitive (primary) and Structural (background) categories. No blocking findings. The system's documentation architecture is unusually strong — the document authority table, contract hierarchy, and sentinel patterns are deliberate and well-executed. The findings below are focused on concrete legibility and coherence gaps that a maintainer would encounter, not theoretical concerns.

---

## Findings

### [SC-1] `tag-grammar.md` is located outside the canonical `references/` tree

- **priority:** P2
- **lens:** Discoverability
- **decision_state:** default likely inherited
- **anchor:** `skills/dialogue/SKILL.md:205` (crosswalk table references `references/tag-grammar.md`); actual file at `skills/dialogue/references/tag-grammar.md`
- **problem:** The `/dialogue` SKILL.md crosswalk table at line 205 references `references/tag-grammar.md` (with no explicit path prefix), and the README lists `references/` as the canonical location for normative reference documents. The actual file lives at `skills/dialogue/references/tag-grammar.md`. All other reference documents (5 contracts, 1 profiles YAML) are in the top-level `references/` directory.
- **impact:** A maintainer following the document authority table ("protocol specs → `references/`") or reading the crosswalk table will look in `references/` and not find the grammar. The file is only discoverable by tracing the skill's directory tree or using a file search. This asymmetry creates a discoverability gap for a component that defines the wire format used by two gatherer agents.
- **recommendation:** Either move `tag-grammar.md` to the top-level `references/` directory (consistent with all other reference documents) and update the crosswalk table path reference, or add an explicit path prefix in the crosswalk reference so it reads `skills/dialogue/references/tag-grammar.md` rather than the ambiguous `references/tag-grammar.md`.
- **confidence:** high
- **provenance:** independent

---

### [SC-2] `/dialogue` SKILL.md implements orchestration-layer logic that contradicts the 5-layer model's skill/agent boundary

- **priority:** P2
- **lens:** Coherence
- **decision_state:** explicit decision (the skill owns briefing assembly by design), but the framing creates a tension with the stated layer model
- **anchor:** `README.md` (5-layer model: "Layer 1: Skills — User-facing entrypoints"); `skills/dialogue/SKILL.md` (~520 lines covering full briefing assembly pipeline, retry logic, health checks, seed_confidence composition, Step 0 question shaping, and analytics orchestration)
- **problem:** The README defines Layer 1 skills as "user-facing entrypoints" and Layer 2 agents as "orchestration." The `/dialogue` SKILL.md implements the complete briefing assembly pipeline (Steps 0-4b), including gatherer retry logic, tag parsing and dedup, health checks, multi-reason seed_confidence composition, phase validation, and analytics emission. This is orchestration work that the model implies should live in Layer 2. The `/codex` SKILL.md by contrast is ~30% of the length and delegates complex multi-turn work to the agent, matching the model's intent.
- **impact:** The layer model's conceptual compression ("skills = entrypoints, agents = orchestration") breaks down for `/dialogue`, requiring a reader to maintain a different mental model for this skill than the architecture description suggests. This doesn't affect runtime behavior but creates cognitive overhead when navigating the codebase or deciding where to make changes to dialogue orchestration logic.
- **recommendation:** Either (a) update the README 5-layer description to note that `/dialogue` owns pre-dialogue context gathering as a skill-layer responsibility with rationale ("gatherers run before delegation, so the skill assembles and passes the briefing"), or (b) extract Steps 0-4b into a pre-dialogue context-assembly agent and have the skill act as a thin coordinator. Option (a) is lower cost and sufficient — the decision appears deliberate, it just needs to be acknowledged in the model.
- **confidence:** high
- **provenance:** independent

---

### [SC-3] Composition contract governs skills absent from this plugin and registers sentinels with no locally-visible consumers

- **priority:** P2
- **lens:** Minimal Surprise
- **decision_state:** explicit decision (composition contract §1 explicitly states scope), but the README framing creates a wrong expectation
- **anchor:** `README.md` ("Two primary contracts are the authoritative source of truth... Three supporting reference documents"); `references/composition-contract.md:§1` (governing `adversarial-review`, `next-steps`, `dialogue`); composition contract sentinel registry (registers `<!-- dialogue-feedback-capsule:v1 -->`); `/dialogue` skill uses `<!-- dialogue-orchestrated-briefing -->` (a different sentinel, not registered in the composition contract)
- **problem:** The README presents 5 normative contracts as governing this plugin's behavior. The composition contract governs cross-skill composition between `adversarial-review`, `next-steps`, and `dialogue` — the first two don't exist in this plugin. More concretely: the composition contract's sentinel registry, consumer-class system, and artifact DAG define infrastructure for capsule exchange (e.g., `<!-- dialogue-feedback-capsule:v1 -->`), but none of these sentinels appear anywhere in this plugin's skills or agents. The `/dialogue` skill's only sentinel (`<!-- dialogue-orchestrated-briefing -->`) is an internal briefing interface, not a composition-contract registered capsule. The composition contract also uses a dual-authority model (contract = protocol semantics; inline stubs = runtime authority) that differs from how the consultation and context-injection contracts work, and this isn't noted in the README's document authority table.
- **impact:** A newcomer reading the README's contract list will open the composition contract expecting cross-component wiring for this plugin and find a full sentinel registry, capsule DAG, and consumer-class system with no locally-visible instantiation. The significant complexity (registry, §7 consumer classes, §12 CI requirements, lineage rules) appears to have zero local consumers — making it harder to build an accurate mental model of what's actually active at runtime. Flagged as CT-7 by the change reviewer: composability infrastructure with generic interfaces that reads as incoherent when assembled into the local plugin picture.
- **recommendation:** Add a one-line parenthetical to the README's composition contract row clarifying scope and authority model: e.g., "Cross-plugin composition protocol (adversarial-review, next-steps, dialogue) — no locally-instantiated consumers in this plugin; inline stubs are runtime-authoritative." This surfaces both the scope gap and the split authority model without requiring a reader to open the contract.
- **confidence:** high
- **provenance:** independent
- **prompted_by:** CT-7 flag from change reviewer (composition contract complexity with no locally-visible consumers)

---

### [SC-4] `contract-agent-extract.md` creates a maintained-copy obligation with no sync enforcement mechanism

- **priority:** P2
- **lens:** Legibility
- **decision_state:** explicit decision (the extract exists to give the agent an optimized read surface), but the sync mechanism is underspecified
- **anchor:** `references/contract-agent-extract.md:1-5` ("Extracted from consultation-contract.md for use by the codex-dialogue agent. Contains only the sections the agent needs at runtime: §4-5, §7-10, §15"); `agents/codex-dialogue.md:89-94` (agent reads extract, not full contract)
- **problem:** The agent extract is a manually maintained copy of 7 sections from the consultation contract. The consultation contract's §2 declares that §5, §7, §10, and §11 are normative sections that "take precedence over inline instructions in skill and agent files." If the consultation contract's normative sections change, the extract must also be updated, but there is no CI check, validation script, or marker in the contract that signals this. The governance drift CI check in §15 validates governance lock count but does not validate extract sync. The `validate_consultation_contract.py` script (§15 reference) appears to check only governance rules, not the extract.
- **impact:** The extract could silently drift from the authoritative contract — particularly for §7 (Safety Pipeline) and §10 (Continuity State), which are marked normative. The agent would execute the stale extract's rules while the contract's governance lock CI check passes. The `contract-agent-extract.md` is an optimization that trades discoverability (agent reads 1 file, not 17 sections) for a new class of silent correctness risk.
- **recommendation:** Either (a) add a `<!-- extract-version: <hash> -->` comment at the top of the extract that CI can verify against the source sections in the consultation contract, or (b) add a note in the consultation contract at each normative section heading indicating that changes must be reflected in `contract-agent-extract.md`. The simplest non-CI approach is a prose warning in the consultation contract §2 precedence section: "If you update §5, §7, §8, §9, §10, or §15, also update `contract-agent-extract.md`."
- **confidence:** medium
- **provenance:** independent

---

## Coverage Note: Structural

- **scope_checked:** `README.md` (5-layer model, document authority, execution flows), `references/consultation-contract.md` (boundary definition, precedence rules), `references/context-injection-contract.md` (protocol overview, security invariants), `agents/codex-dialogue.md` (Phase 1-3 structure), `skills/codex/SKILL.md` and `skills/dialogue/SKILL.md` (layer boundary)
- **checks_run:**
  - Purpose Fit: Does the architecture serve the stated goal (cross-model consultation with safety controls)? — Yes. The 5-layer model maps cleanly to the problem.
  - Responsibility Partitioning: Can you state what each component does and doesn't do? — Yes for agents, MCP servers, and hooks. Ambiguous for `/dialogue` skill (see SC-2).
  - Boundary Definition: Are contracts between components explicit? — Strong. Consultation contract §2 states precedence explicitly; sentinel pattern creates a verifiable interface between `/dialogue` and `codex-dialogue`.
  - Dependency Direction: Do volatile components depend on stable ones? — Yes. Skills (volatile) depend on contracts (stable) and agents (semi-stable). Agents read contracts. Scripts are infrastructure below both.
  - Composability: Can components be combined without hidden coupling? — Yes. The scope envelope mechanism provides clean coupling between `/dialogue` and `codex-dialogue`.
  - Completeness: Is everything the system needs present? — One gap: `tag-grammar.md` is outside the expected reference tree (see SC-1).
  - Layering & Abstraction: Is the system organized into clear abstraction levels? — The 5-layer model is explicit and holds for 3 of 4 skills; `/dialogue` is the exception (see SC-2).
- **result:** No structural defects found beyond what is captured in SC-1 and SC-2.
- **caveats:** Did not read `scripts/` implementations or context-injection server code — those surfaces are better examined by the behavioral and data reviewers.
- **deferred_to:** behavioral (runtime behavior of scripts), data (JSONL event log schema, context-injection state), trust-safety (credential scanning pipeline)

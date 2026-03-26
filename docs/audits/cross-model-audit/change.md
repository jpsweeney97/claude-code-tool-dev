# Change Review Findings

**Reviewer:** change
**Date:** 2026-03-26
**Target:** `packages/plugins/cross-model/`

---

## Summary

| Finding | Priority | Lens |
|---------|----------|------|
| CH-1 | P1 | Versioning & Migration |
| CH-2 | P1 | Versioning & Migration |
| CH-3 | P2 | Reversibility / Changeability |
| CH-4 | P2 | Testability |
| CH-5 | P2 | Extensibility |

---

### [CH-1] Context-injection `0.x exact-match` policy makes every field addition a breaking deploy

- **priority:** P1
- **lens:** Versioning & Migration
- **decision_state:** explicit decision
- **anchor:** `references/context-injection-contract.md#schema-versioning` (top of file, line 7); `context-injection/context_injection/types.py:26-29`
- **problem:** The context-injection contract explicitly mandates exact-match semantics for all `0.x` versions: any `schema_version` mismatch returns `invalid_schema_version`. There is no backward-compatibility window. Adding a single optional field to `TurnRequest` (e.g., the deferred `phase_id` fix noted in consultation-contract §14) requires simultaneously deploying a new server version and updating every calling agent — there is no "roll forward gradually" path.
- **impact:** Every schema change is a hard-coordination deploy. A running codex-dialogue agent will fail with `invalid_schema_version` the moment the context-injection server is updated, unless the agent is also updated atomically. For an LLM-executed agent (not a compiled binary), "atomic" is not guaranteed — session state may cross versions mid-conversation.
- **recommendation:** Document the rollout procedure explicitly: which gets updated first (server or agent), what happens to in-flight conversations, and whether a brief dual-version window is required. If the path to `1.0` is planned, specify the conditions that will unlock semver compatibility. The existing policy is not wrong — it's intentional simplification — but the deploy coupling it creates is undocumented.
- **confidence:** high
- **provenance:** independent

---

### [CH-2] Governance drift CI check is unimplemented for composition-contract; consultation-contract check is real but narrow

- **priority:** P1
- **lens:** Versioning & Migration
- **decision_state:** underspecified
- **anchor:** `references/consultation-contract.md:409` ("Verification script: `scripts/validate_consultation_contract.py` (Phase 3)"); `references/composition-contract.md:723-727` (§12.3 CI MUST rules); no CI workflow covers the cross-model plugin
- **problem:** Two contracts require CI enforcement of drift detection. The consultation-contract check (`scripts/validate_consultation_contract.py`) exists and is real, but it is NOT wired into any CI workflow — only into a repo-root test (`tests/test_consultation_contract_sync.py`), which runs only when the repo-root test suite runs. The composition-contract §12.3 CI requirements are entirely aspirational: no script exists, no workflow checks them. The only CI workflow in the repo covers the TypeScript `claude-code-docs` package, not the Python plugin.
- **impact:** Contract drift goes undetected until a human reviewer notices. The composition-contract §12 checks (requiring `implements_composition_contract: v1` markers in skill stubs, detecting stub/contract divergence) are structurally unenforced. A skills author could add a local variant of routing semantics (violating §2's execution-ownership rule) with no automated gate.
- **recommendation:** Wire `uv run scripts/validate_consultation_contract.py` into a CI workflow path-scoped to the cross-model plugin. Create a minimal check for the composition-contract §12.3 requirement #3 (detect missing `implements_composition_contract: v1` in participating skill stubs) — currently the `/dialogue`, `/codex`, `/delegate`, and `adversarial-review` skills do not declare this marker.
- **confidence:** high
- **provenance:** independent

---

### [CH-3] `conversationId` deprecation has no removal path or timeline

- **priority:** P2
- **lens:** Reversibility
- **decision_state:** explicit tradeoff
- **anchor:** `references/consultation-contract.md:75` (§4 vocabulary); `references/consultation-contract.md:405` (governance lock #5); `scripts/consultation_safety.py:58`
- **problem:** `conversationId` is labeled "deprecated alias for `threadId`" in the consultation contract and governance lock #5. It appears in `consultation_safety.py`'s `START_POLICY.expected_fields`, meaning the credential scanner explicitly allows it through. There is no version in which `conversationId` stops being accepted, no migration guide for callers to stop sending it, and no test asserting it eventually fails. This is an open deprecation with no close.
- **impact:** Low immediate risk, but the deprecated field accumulates permanence over time. Every new consumer that reads contract examples may inherit the alias without knowing it is deprecated. The credential scanner will correctly treat it as a metadata field (not a content field), so safety risk is minimal.
- **recommendation:** Add a deprecation notice to the §4 entry with an explicit removal condition (e.g., "removed when no skill or agent sends `conversationId` in calls"). Add a test that verifies no skill stub or agent sends `conversationId` as the primary identifier. This makes "deprecated" actionable rather than perpetual.
- **confidence:** high
- **provenance:** independent

---

### [CH-4] 4000-line legacy test corpus duplicates current test coverage with no removal plan

- **priority:** P2
- **lens:** Testability
- **decision_state:** default likely inherited
- **anchor:** `tests/test_emit_analytics_legacy.py` (1771 lines), `tests/test_compute_stats_legacy.py` (731 lines), five other `*_legacy.py` files; total ~4037 lines
- **problem:** Seven `*_legacy.py` test files preserve original test bodies "unchanged" using a `MODULE` alias pattern (e.g., `import scripts.emit_analytics as MODULE`). They test the same code as their non-legacy counterparts, but use an older class-based structure. The comment "migrated from repo root tests/" indicates they were ported as-is during a test reorganization. There is no documented plan to replace or remove them.
- **impact:** ~4000 lines of test code that duplicates coverage creates two practical problems: (1) a failing test may exist in both the legacy and current files, making triage harder — which one is authoritative? (2) future refactors of the tested modules require updating two sets of tests for each module touched, which creates a friction tax on changeability. The legacy files also use `import MODULE` indirection, which makes test failure messages less readable.
- **recommendation:** Audit coverage overlap between legacy and current test files. For modules where the current test files provide equivalent coverage, schedule removal of the legacy files. Where the legacy files cover cases that the current files do not, migrate those specific tests. The goal is one authoritative test file per module.
- **confidence:** medium
- **provenance:** independent

---

### [CH-5] Phase boundary detection couples posture-value semantics into TurnRequest schema, with deferred fix that requires a schema version bump

- **priority:** P2
- **lens:** Extensibility
- **decision_state:** explicit tradeoff
- **anchor:** `references/consultation-contract.md:392` (§14 phase composition validation); `context-injection/context_injection/types.py:26-29` (exact-match versioning)
- **problem:** The context-injection server detects phase boundaries by posture change between turns. The consultation contract explicitly documents this as a "silent correctness failure" for same-posture consecutive phases, and labels the fix ("add `phase_id` to TurnRequest") as deferred to "post-Release C". Adding `phase_id` is a non-backward-compatible schema change under the `0.x exact-match` policy — it requires a version bump and coordinated deploy. The workaround (enforcing distinct adjacent postures at profile load time) is a constraint imposed on the *profile author* to paper over a design limitation in the *transport schema*.
- **impact:** Profile authors cannot define multi-phase conversations with the same posture in adjacent phases (e.g., two consecutive exploratory phases with different focuses). This constrains the extensibility of the profile system. The constraint is enforced at profile load time, so it fails loudly — but it's a limitation that will require a schema migration to remove.
- **recommendation:** Document the Release C milestone that gates this fix, or define what conditions would trigger the schema bump. Given that adding `phase_id` is straightforward and the workaround is constraining, assess whether deferring past the current version is worth the profile-author friction.
- **confidence:** medium
- **provenance:** independent

---

## Coverage Notes

### Lenses Not Yielding Findings

**Changeability:** Individual scripts are well-isolated (one file per concern: `codex_consult.py`, `codex_guard.py`, `event_schema.py`, etc.). The single-source-of-truth pattern in `event_schema.py` for event field definitions reduces ripple-through risk on event schema changes. No finding.

**Replaceability:** The codex shim (`codex_shim.py`) was deliberately introduced to decouple from upstream `codex mcp-server` binary parameter changes (per CHANGELOG v3.1.0). This is an explicit replaceability improvement. The context-injection server is independently versioned (`0.2.0`) and independently testable. No finding.

**Testability (overall):** The test split is healthy — ~840 plugin tests in `tests/`, ~1000 context-injection tests in `context-injection/tests/`. Context-injection components are testable in isolation (the `conftest.py` and `redaction_harness.py` provide fixture infrastructure). The `test_mcp_wiring.py` tests verify tool name alignment at the wiring layer. The `test_governance_content.py` tests verify cross-contract invariant references. Testability is broadly good — the legacy test issue (CH-4) is the primary concern here.

### CT Tension Watch Results

- **CT-2 (Changeability ↔ Performance):** The `codex_shim.py` indirection layer adds one subprocess hop per consultation call. This is intentional decoupling and the overhead is dominated by the Codex API latency by multiple orders of magnitude. No finding.
- **CT-3 (Completeness ↔ Changeability):** The context-injection contract's completeness (17-step pipeline spec, full field inventories, exact-match versioning) does resist change — CH-1 documents this directly. The governance-drift checks are an attempt to manage the completeness/changeability tension through automation, but they are partially unimplemented (CH-2). Forwarded to structural-cognitive: the extensive composition-contract sentinels/capsule/DAG spec creates the same tension — adding a new artifact kind requires: registry row, three appendix fields, stub marker, CI check, and conformance asset — all in one change.
- **CT-7 (Composability ↔ Coherence):** The composition-contract sentinel/capsule system defines three artifact types (AR, NS, dialogue) with a rich lineage/DAG/staleness model. However, none of the four skills in this plugin (`/codex`, `/dialogue`, `/delegate`, `/consultation-stats`) are the AR or NS skills that the composition contract governs — those appear to be in a different plugin or skill set. The composition contract's complexity is forward-looking infrastructure for skills that are not in this plugin. This may be coherent at the skill-family level but creates cognitive overhead for readers of this plugin who encounter the composition-contract reference. Flagging to structural-cognitive.

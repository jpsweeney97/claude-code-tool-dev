# CCDI Spec Remediation Plan — Round 11

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 40 findings (1 P0, 18 P1, 21 P2) from the 5-reviewer spec review of `docs/superpowers/specs/ccdi/`

**Architecture:** Six tasks in two phases fix P0+P1 findings in spec files, grouped by edit-locality and causal dependency. P2 findings deferred to a separate Task 7 pass. T2 (inventory-snapshot cascade) was validated via a 5-turn Codex dialogue (thread `019d18a4`) which expanded the original 3-site fix to a 9-item secondary-ripple audit.

**Tech Stack:** Markdown spec edits only — no code changes

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 40 canonical findings (1 P0, 18 P1, 21 P2) across 8 normative files + spec.yaml (report header says 19 P1 / 20 P2 — actual detailed listing is 18 P1 / 21 P2)
**Spec:** `docs/superpowers/specs/ccdi/` (10 files, 8 normative + 1 supporting + spec.yaml)
**Codex dialogue:** Thread `019d18a4-b9d5-7f91-b7ef-3f5ff9fe33aa` validated T2 mechanism (10 RESOLVED, 3 EMERGED)

---

## Strategy

Seven tasks in three phases, ordered by dependency and edit-locality:

1. **Phase 1** — Three tasks, all parallel (touch different sections of shared files):
   - **T1:** P0 fix (1) — data-model.md defense-in-depth test, delivery.md test addition
   - **T2:** Inventory-snapshot cascade (3 P1) — integration.md sentinel + handoff + initial commit, data-model.md transport field, delivery.md test
   - **T4:** Anchor/enum consistency (2 P1) — decisions.md, README.md, spec.yaml, delivery.md — mechanical

2. **Phase 2** — Three tasks, all parallel (touch non-overlapping sections):
   - **T3:** Shadow-mode behavioral corrections (2 P1) — integration.md invariant text, delivery.md kill criteria verify
   - **T5:** Test infrastructure + coverage gaps (6 P1) — delivery.md replay harness schema + 5 test additions
   - **T6:** Data-model.md schema hygiene (5 P1) — data-model.md annotations, cross-references, registry.md cross-reference

3. **Phase 3** — After Phase 1+2:
   - **T7:** P2 batch (20 P2) — all files

**Dependency chains:**
1. T3 (SY-8: shadow mode model fix) → T5 (SY-10: Phase A exemption test references shadow mode behavior)
2. SY-28 (replay harness negative assertion operator in T5) should precede other T5 test additions that may need it

**Commit strategy:**
1. `fix(spec): remediate P0 results_file defense-in-depth finding from review round 11` (T1)
2. `fix(spec): remediate 3 P1 inventory-snapshot cascade findings from review round 11` (T2)
3. `fix(spec): remediate 2 P1 anchor/enum consistency findings from review round 11` (T4)
4. `fix(spec): remediate 2 P1 shadow-mode behavioral findings from review round 11` (T3)
5. `fix(spec): remediate 6 P1 test coverage findings from review round 11` (T5)
6. `fix(spec): remediate 5 P1 schema hygiene findings from review round 11` (T6)
7. `fix(spec): remediate 21 P2 findings from review round 11` (T7)

---

## Task 1 — P0: `results_file` Defense-in-Depth Verifiability (1 finding)

**Finding count:** 1 P0 (SY-17)
**Files:** delivery.md
**Depends on:** nothing — start immediately
**Corroboration:** SP-4 + CE-12 (cross-lens confirmation, high confidence)

### [SY-17] `results_file` defense-in-depth is not independently verifiable by the test suite

**Sources:** SP-4, CE-12
**File:** delivery.md (test sections — add new Layer 1 test)

data-model.md:342 requires BOTH write-time exclusion AND load-time stripping of `results_file` as defense-in-depth. The write-time exclusion is the "primary enforcement point" and load-time stripping is the "recovery mechanism." But every specified test reads back the file after a mutation that triggers load-time stripping, so an implementation that omits write-time exclusion but correctly implements load-time stripping passes all tests.

**Fix (1 addition to delivery.md):**

Add a new Layer 1 unit test entry after the existing `results_file` stripping tests. Location: delivery.md Layer 1 unit test table, registry/serialization section.

```markdown
| Write-time `results_file` exclusion (defense-in-depth isolation) | Construct a `TopicRegistryEntry`-bearing registry dict in memory (no file load), include `results_file: "/tmp/test.json"` in the dict, serialize via the production serializer, assert `results_file` is absent from serialized bytes. This isolates write-time exclusion from load-time stripping — an implementation that only strips at load time will fail this test. |
```

- [ ] **Step 1:** Find the Layer 1 test table rows for `results_file` in delivery.md. They are near the registry serialization tests.
- [ ] **Step 2:** Add the new test row immediately after the existing `results_file` stripping test row. Use the exact text above.
- [ ] **Step 3:** Verify the new test is structurally distinct from existing tests — it must NOT load from a file (no load→mutate→write cycle).
- [ ] **Step 4:** Commit: `fix(spec): remediate P0 results_file defense-in-depth finding from review round 11`

---

## Task 2 — Inventory-Snapshot Cascade (3 findings)

**Finding count:** 3 P1 (SY-11, SY-3, SY-31)
**Files:** integration.md, data-model.md, delivery.md
**Depends on:** nothing — start immediately
**Corroboration:** SY-11 has 3 independent findings (CE-4, CE-8, SP-10); SY-3 has 2 (AA-3, CC-9)
**Codex validation:** Thread `019d18a4` confirmed sentinel block mechanism, atomic-pair invariant, 9-item ripple audit

### [SY-11] Initial commit code flow omits required `--inventory-snapshot`

**Sources:** CE-4, CE-8, SP-10
**File:** integration.md:239–244 (initial commit code block)

The initial CCDI commit's `build-packet --mark-injected` calls omit `--inventory-snapshot`, violating the footnote at line 22 requiring it when `--registry-file` is present. This causes `suppressed_docs_epoch` to be null for initial-commit suppressions, triggering spurious re-entry. The mid-turn prepare call at line 374 correctly includes the flag.

**Fix (1 edit):**

In integration.md, change the initial commit code block (lines 239–244) from:

```
│  │       Bash: python3 topic_inventory.py build-packet \
│  │              --results-file /tmp/ccdi_results_<id>.json \
│  │              --registry-file /tmp/ccdi_registry_<id>.json \
│  │              --mode initial --topic-key <entry.topic_key> \
│  │              --facet <entry.facet> \
│  │              --coverage-target <entry.coverage_target> --mark-injected
```

To:

```
│  │       Bash: python3 topic_inventory.py build-packet \
│  │              --results-file /tmp/ccdi_results_<id>.json \
│  │              --registry-file /tmp/ccdi_registry_<id>.json \
│  │              --mode initial --topic-key <entry.topic_key> \
│  │              --facet <entry.facet> \
│  │              --coverage-target <entry.coverage_target> \
│  │              --inventory-snapshot <ccdi_inventory_snapshot_path> --mark-injected
```

- [ ] **Step 1:** Read integration.md:239–244. Verify the code block matches the "from" text above.
- [ ] **Step 2:** Apply the edit — add `--inventory-snapshot <ccdi_inventory_snapshot_path>` before `--mark-injected`.
- [ ] **Step 3:** Verify consistency with mid-turn prepare call at line 374 (which already includes `--inventory-snapshot <ccdi_snapshot_path>`). Both paths should now include the flag.

---

### [SY-3] `ccdi_inventory_snapshot` delegation envelope field has no defined sourcing mechanism

**Sources:** AA-3, CC-9
**File:** integration.md:270–282 (sentinel block + handoff), integration.md:289–292 (delegation envelope table)

The delegation envelope field `ccdi_inventory_snapshot` is declared "required when `ccdi_seed` is present" and "sourced from ccdi-gatherer output" but no sentinel block field, extraction step, or sourcing mechanism is defined.

**Fix (3 edits + 1 addition to data-model.md):**

**Edit 1 — Sentinel block JSON** (integration.md:272):

Change:
```
{"entries": [...], "docs_epoch": "...", "inventory_snapshot_version": "1", "results_file": "/tmp/ccdi_results_<id>.json"}
```

To:
```
{"entries": [...], "docs_epoch": "...", "inventory_snapshot_version": "1", "results_file": "/tmp/ccdi_results_<id>.json", "inventory_snapshot_path": "/tmp/ccdi_snapshot_<id>.json"}
```

**Edit 2 — Handoff extraction steps** (integration.md:276–281):

Change the numbered list from:

```
1. Extracts JSON between the sentinels from the ccdi-gatherer's output.
2. Reads `results_file` from the extracted JSON (the search results path needed for the initial commit).
3. Writes the seed to a temp file (`/tmp/ccdi_registry_<id>.json`).
4. Passes the file path as `ccdi_seed: <path>` in the delegation envelope to `codex-dialogue`.
```

To:

```
1. Extracts JSON between the sentinels from the ccdi-gatherer's output.
2. Reads `results_file` from the extracted JSON (the search results path needed for the initial commit).
2b. Reads `inventory_snapshot_path` from the extracted JSON (the pinned inventory snapshot path needed for `--inventory-snapshot` on initial commit `build-packet` calls and for the `ccdi_inventory_snapshot` delegation envelope field).
3. Writes the seed to a temp file (`/tmp/ccdi_registry_<id>.json`).
4. Passes the file path as `ccdi_seed: <path>` and the inventory snapshot path as `ccdi_inventory_snapshot: <inventory_snapshot_path>` in the delegation envelope to `codex-dialogue`. These two fields are an atomic pair — both MUST be present or both absent.
```

**Edit 3 — Delegation envelope table** (integration.md:292):

The existing row already says "Required when `ccdi_seed` is present." Add sourcing clarity by changing the Source column from:

```
ccdi-gatherer output
```

To:

```
`inventory_snapshot_path` field in ccdi-gatherer sentinel block
```

**Edit 4 — data-model.md RegistrySeed schema** (data-model.md:301):

After the `results_file` field line, add `inventory_snapshot_path` as a second transport-only field:

```
├── inventory_snapshot_path?: string | null  # transport-only; never persisted in live file; stripped on load. Path to pinned inventory snapshot file for --inventory-snapshot on all build-packet CLI calls; absent when ccdi-gatherer did not load a valid inventory
```

**Edit 5 — data-model.md Transport-Only Fields subsection:**

After the `results_file` field paragraph (data-model.md:304), add a new paragraph:

```markdown
**`inventory_snapshot_path` field:** `inventory_snapshot_path` is required in the sentinel RegistrySeed when a valid `CompiledInventory` was loaded by `ccdi-gatherer`. The value is an absolute path to the pinned inventory snapshot file (e.g., `/tmp/ccdi_snapshot_<id>.json`). The `/dialogue` skill reads this path from the sentinel block and passes it as `ccdi_inventory_snapshot` in the delegation envelope and as `--inventory-snapshot` on initial commit `build-packet` calls. This is a transport field for the handoff — it is not written to the live registry file and is not used after the initial commit and delegation complete. **Load-time invariant:** Same stripping semantics as `results_file` — implementations MUST strip `inventory_snapshot_path` from the in-memory registry representation at load time. **Pinning invariant:** The path MUST point to a pinned temp copy of the inventory, NOT the canonical `data/topic_inventory.json`. The canonical file can be regenerated mid-dialogue; CLI tools do file reads via `--inventory-snapshot`, so pinning must be at the file level.
```

**Edit 6 — data-model.md Live Registry File Schema** (data-model.md:340):

Update the stripping language from:

```
`results_file` is stripped on load (load-time invariant) and MUST NOT appear in the live file.
```

To:

```
`results_file` and `inventory_snapshot_path` are stripped on load (load-time invariant) and MUST NOT appear in the live file.
```

**Edit 7 — data-model.md Write-time invariant** (data-model.md:342):

Update from:

```
**Write-time invariant:** Implementations MUST NOT write `results_file` to the registry file at any point during the write path. The serializer MUST exclude `results_file` from the output JSON when writing the live registry file.
```

To:

```
**Write-time invariant:** Implementations MUST NOT write `results_file` or `inventory_snapshot_path` to the registry file at any point during the write path. The serializer MUST exclude both transport-only fields from the output JSON when writing the live registry file. **Transport-only field allowlist (closed):** Only `results_file` and `inventory_snapshot_path` are transport-only fields. New transport-only fields require updating this allowlist, the load-time stripping logic, and the write-time exclusion logic.
```

- [ ] **Step 1:** Read integration.md:270–282. Verify sentinel block and handoff steps match the "from" text.
- [ ] **Step 2:** Apply Edit 1 (sentinel block JSON).
- [ ] **Step 3:** Apply Edit 2 (handoff extraction steps).
- [ ] **Step 4:** Apply Edit 3 (delegation envelope table Source column).
- [ ] **Step 5:** Read data-model.md:296–308. Verify RegistrySeed schema and `results_file` paragraph match.
- [ ] **Step 6:** Apply Edit 4 (add `inventory_snapshot_path` field to schema).
- [ ] **Step 7:** Apply Edit 5 (add `inventory_snapshot_path` field paragraph after `results_file` paragraph).
- [ ] **Step 8:** Apply Edit 6 (Live Registry File Schema stripping language).
- [ ] **Step 9:** Apply Edit 7 (Write-time invariant + transport-only allowlist).
- [ ] **Step 10:** Verify SY-17 (Task 1) still makes sense — the write-time invariant now covers both transport fields.

---

### [SY-31] `ccdi_inventory_snapshot` delegation field absence not tested

**Sources:** VR-6 (related to SY-3)
**File:** delivery.md (integration tests section)

The delegation envelope field is "required when `ccdi_seed` is present" but no test exercises the missing-field failure mode.

**Fix (1 addition to delivery.md):**

Add to the Boundary Contract Tests or integration test section in delivery.md:

```markdown
| `ccdi_inventory_snapshot` absent with `ccdi_seed` present | Delegation envelope contains `ccdi_seed: <path>` but no `ccdi_inventory_snapshot` field → `codex-dialogue` treats as degraded: CCDI mid-dialogue disabled for the session (same as `ccdi_seed` absent). Agent MUST log a warning (atomic-pair invariant violated). |
```

- [ ] **Step 11:** Find the Boundary Contract Tests section in delivery.md.
- [ ] **Step 12:** Add the test row for missing `ccdi_inventory_snapshot`.
- [ ] **Step 13:** Commit: `fix(spec): remediate 3 P1 inventory-snapshot cascade findings from review round 11`

---

## Task 4 — Anchor/Enum Consistency (2 findings)

**Finding count:** 2 P1 (SY-1, SY-40)
**Files:** decisions.md, README.md, spec.yaml, delivery.md
**Depends on:** nothing — start immediately
**Corroboration:** SY-1 has 3 independent findings (AA-1, CC-1, CC-8)

### [SY-1] Pipeline-isolation-invariants anchor — 6 broken references across 3 files

**Sources:** AA-1, CC-1, CC-8
**Files:** decisions.md:56,58,60,62; README.md:30; spec.yaml NOTE comment

The correct anchor is `#pipeline-isolation-invariants-subset` (matching the heading in integration.md:126). Six references use the shorter `#pipeline-isolation-invariants` (without `-subset`).

**Fix (6 mechanical edits):**

In each file, change `#pipeline-isolation-invariants` to `#pipeline-isolation-invariants-subset`:

1. decisions.md:56 — "see [integration.md#pipeline-isolation-invariants]"
2. decisions.md:58 — "see [integration.md#pipeline-isolation-invariants]"
3. decisions.md:60 — "see [integration.md#pipeline-isolation-invariants]"
4. decisions.md:62 — "see [integration.md#pipeline-isolation-invariants]"
5. README.md:30 — "§pipeline-isolation-invariants"
6. spec.yaml NOTE comment — if present, update the reference

- [ ] **Step 1:** In decisions.md, use replace-all to change `integration.md#pipeline-isolation-invariants)` to `integration.md#pipeline-isolation-invariants-subset)` (4 occurrences). Use exact match to avoid also matching lines that already have `-subset`.
- [ ] **Step 2:** In README.md:30, change `§pipeline-isolation-invariants` to `§pipeline-isolation-invariants-subset`.
- [ ] **Step 3:** In spec.yaml, find and fix the NOTE comment reference if it uses the short form.
- [ ] **Step 4:** Verify no remaining broken references: grep for `pipeline-isolation-invariants` (without `-subset`) across all spec files.

---

### [SY-40] Enum value drift — `facet="configuration"` not a valid Facet value

**Sources:** CC-2
**File:** delivery.md:354

The Facet enum is: `overview`, `schema`, `input`, `output`, `control`, `config`. The test uses `"configuration"` which is not a valid value.

**Fix (1 edit):**

In delivery.md:354, change:
```
facet="configuration"
```
To:
```
facet="config"
```

- [ ] **Step 5:** Apply the edit in delivery.md:354.
- [ ] **Step 6:** Verify no other occurrences of `facet="configuration"` in the spec: grep across all files.
- [ ] **Step 7:** Commit: `fix(spec): remediate 2 P1 anchor/enum consistency findings from review round 11`

---

## Task 3 — Shadow-Mode Behavioral Corrections (2 findings)

**Finding count:** 2 P1 (SY-8, SY-9)
**Files:** integration.md, delivery.md
**Depends on:** nothing (Phase 2 for sequencing with T5, but no hard dependency)

### [SY-8] Shadow mode abstention claim contradicts actual `--mark-deferred` call pattern

**Sources:** CE-1
**File:** integration.md:446 (shadow-mode registry invariant, agent-enforced paragraph)

integration.md:446 states "The agent MUST NOT call `--mark-injected` (Step 7.5) or `--mark-deferred` (Step 5.5) in shadow mode." But the code flow at lines 386–391 and 404–408 explicitly shows the agent calling `build-packet --mark-deferred --shadow-mode` in both target-mismatch and scout-priority paths. The `--shadow-mode` flag makes `--mark-deferred` a no-op at the CLI level. The CLI backstop paragraph at line 448 correctly describes this pattern. The prohibition is accurate for `--mark-injected` (line 436: "If shadow mode: no commit") but inaccurate for `--mark-deferred`.

**Fix (1 edit):**

In integration.md:446, change:

```
**Agent-enforced (via agent abstention):** The agent MUST NOT call `--mark-injected` (Step 7.5) or `--mark-deferred` (Step 5.5) in shadow mode. These are agent-initiated CLI calls, not CLI-internal behavior — the prohibition requires the agent to not invoke these commands.
```

To:

```
**Agent-enforced (split model):** The agent MUST NOT call `--mark-injected` (Step 7.5) in shadow mode — this is true abstention (no CLI backstop exists for injection commits). For `--mark-deferred` (Step 5.5), the agent MUST pass `--shadow-mode` to every `build-packet --mark-deferred` call — the CLI backstop makes `--mark-deferred` a no-op when `--shadow-mode` is set (see below). The agent calls `--mark-deferred` in both active and shadow modes; the behavioral difference is enforced by the CLI flag, not by agent abstention.
```

- [ ] **Step 1:** Read integration.md:442–449. Verify the current text matches.
- [ ] **Step 2:** Apply the edit to line 446.
- [ ] **Step 3:** Verify consistency with the code flow at lines 386–391 (target-mismatch shadow path) and 404–408 (scout-priority shadow path) — both show `--shadow-mode --mark-deferred`.
- [ ] **Step 4:** Verify the CLI backstop paragraph at line 448 remains consistent (it describes the no-op behavior).

---

### [SY-9] Kill criterion table uses raw yield formula; normative text requires `shadow_adjusted_yield`

**Sources:** CE-2
**File:** delivery.md:29 (kill criteria table)

**VERIFY BEFORE EDITING:** The current text at delivery.md:29 reads:

```
| Effective prepare yield | < 40% | In active mode: `packets_surviving_precedence / packets_prepared`. In shadow mode: `shadow_adjusted_yield` (see [Diagnostics](#diagnostics) below). |
```

This already distinguishes active mode (raw formula) from shadow mode (`shadow_adjusted_yield`). The finding may have been based on a prior version or a misread. **Read line 29 and verify whether the fix is already present.** If the table already distinguishes both formulas, mark SY-9 as "already resolved" and skip the edit. If not, apply the fix described in the report.

- [ ] **Step 5:** Read delivery.md:27–31 and verify whether the kill criteria table already shows both formulas.
- [ ] **Step 6:** If already correct, note "SY-9: already resolved — no edit needed." If not, update the Metric column to: `In active mode: packets_surviving_precedence / packets_prepared. In shadow mode: shadow_adjusted_yield`.
- [ ] **Step 7:** Commit: `fix(spec): remediate 2 P1 shadow-mode behavioral findings from review round 11` (adjust commit message if SY-9 was already resolved — e.g., "1 P1 shadow-mode finding")

---

## Task 5 — Test Infrastructure + Coverage Gaps (6 findings)

**Finding count:** 6 P1 (SY-28, SY-10, SY-27, SY-32, SY-36, SY-38)
**Files:** delivery.md
**Depends on:** T3 (shadow mode model should be stable before adding shadow-related tests)

### [SY-28] Replay harness fixture schema lacks negative assertion operator

**Sources:** VR-3
**File:** delivery.md:560–566 (replay harness assertions schema)

`empty_build_skips_target_match.replay.json` (delivery.md:712) requires asserting `"build-packet --mark-deferred" not in cli_call_log` but the assertions schema has no negative assertion operator.

**Fix (1 addition to delivery.md assertions schema):**

In the assertions schema JSON example (delivery.md:560–566), add `cli_calls_absent` field:

Change the assertions block from:

```json
  "assertions": {
    "cli_pipeline_sequence": ["classify", "dialogue-turn", "build-packet", "build-packet --mark-injected"],
    "final_registry_state": {"hooks.pre_tool_use": "injected"},
    "deferred_topics": [],
    "packets_injected_count": 1
  }
```

To:

```json
  "assertions": {
    "cli_pipeline_sequence": ["classify", "dialogue-turn", "build-packet", "build-packet --mark-injected"],
    "cli_calls_absent": [],
    "final_registry_state": {"hooks.pre_tool_use": "injected"},
    "deferred_topics": [],
    "packets_injected_count": 1
  }
```

Then add a description after the assertions schema explaining the field:

```markdown
**`cli_calls_absent` field:** Array of CLI call substrings that MUST NOT appear in the harness's cli_call_log for the fixture to pass. Example: `["build-packet --mark-deferred"]` asserts that no deferred-write call was made. An empty array means no negative assertions. This is the inverse of `cli_pipeline_sequence` (which asserts presence).
```

- [ ] **Step 1:** Read delivery.md:560–566. Verify the assertions schema matches.
- [ ] **Step 2:** Add `cli_calls_absent` to the schema example.
- [ ] **Step 3:** Add the field description paragraph after the schema.

---

### [SY-10] Phase A initial injection exemption from shadow mode gate has no test

**Sources:** CE-3
**File:** delivery.md (Layer 2b agent sequence tests)

The invariant "Phase A is always active regardless of `graduation.json` status" (integration.md:256–259) has no test. All graduation gate tests focus on Phase B `codex-dialogue` behavior.

**Fix (1 addition to delivery.md Layer 2b test table):**

Add to the Layer 2b agent sequence test table (near delivery.md:679–681, after the existing graduation gate tests):

```markdown
| Graduation gate: Phase A unconditional | `graduation.json` with `status: "rejected"` → initial CCDI commit phase still fires: agent tool-call log for the `/dialogue` skill (pre-delegation) contains `build-packet --mark-injected` invocations for seed entries. Phase A is always active regardless of graduation status. |
```

- [ ] **Step 4:** Read delivery.md:679–681 (graduation gate tests).
- [ ] **Step 5:** Add the new test row after the existing graduation gate rows.

---

### [SY-27] No negative test for `exact` match word-boundary constraint

**Sources:** VR-1
**File:** delivery.md (classifier tests section)

classifier.md states exact match "must not be preceded or followed by a word character" but no test provides input like `"SomePreToolUseHandler"` and asserts no match.

**Fix (1 addition to delivery.md classifier tests):**

Add to the classifier test table:

```markdown
| Exact match word-boundary negative | Input: `"SomePreToolUseHandler"` (exact match candidate `PreToolUse` embedded in a longer word) → `resolved_topics` is empty. Verifies the MUST NOT constraint: exact matches must not be preceded or followed by a word character. |
```

- [ ] **Step 6:** Find the classifier test section in delivery.md.
- [ ] **Step 7:** Add the negative test row.

---

### [SY-32] `validate_graduation.py` freshness guardrail exit code ambiguous

**Sources:** VR-7
**File:** delivery.md:165 (`validate_graduation.py` CLI interface section)

The guardrail fires as a "warning" but the CLI defines exit 0 (pass) and exit 1 (fail). Whether the guardrail produces exit 0 with stderr warning or exit 1 is unspecified.

**Fix (1 clarification in delivery.md):**

In the `validate_graduation.py` CLI interface section, after the exit code table, add:

```markdown
**Freshness guardrail exit code:** When the freshness guardrail fires (classify_result_hash cannot be freshness-sensitive), the validator exits with code 0 and emits a warning to stderr. This is consistent with the "fall back to raw yield" language — the guardrail degrades the metric, it does not block graduation.
```

- [ ] **Step 8:** Read delivery.md:165–180 (`validate_graduation.py` section).
- [ ] **Step 9:** Add the exit code clarification.

---

### [SY-36] `deferred_ttl_countdown_resets` fixture missing TTL-value assertion

**Sources:** VR-11
**File:** delivery.md:729 (fixture description)

The fixture's `final_registry_file_assertions` includes `consecutive_medium_count` but not the TTL reset value, which is the fixture's primary invariant.

**Fix (1 edit in delivery.md:729):**

In the fixture description for `deferred_ttl_countdown_resets.replay.json`, append to the `final_registry_file_assertions` MUST:

After the existing `consecutive_medium_count` assertion, add:

```
, `{"path": "<topic>.deferred_ttl", "equals": 3}` (verifying TTL reset to initial value at TTL=0).
```

- [ ] **Step 10:** Read delivery.md:729 (the fixture description).
- [ ] **Step 11:** Add the TTL-value assertion to the existing MUST clause.

---

### [SY-38] `ccdi_seed` sentinel structure boundary test missing negative case

**Sources:** VR-13
**File:** delivery.md (boundary contract tests)

The spec says `ccdi_seed` must be a file path, not inline JSON. Positive test exists. No negative test provides inline JSON and asserts rejection.

**Fix (1 addition to delivery.md boundary contract tests):**

```markdown
| `ccdi_seed` inline JSON rejection | Delegation envelope contains `ccdi_seed` value that is a JSON object (not a file path) → `codex-dialogue` treats `ccdi_seed` as absent (CCDI mid-dialogue disabled). Agent MUST NOT attempt to use the inline JSON as a registry file. |
```

- [ ] **Step 12:** Find the boundary contract test table in delivery.md.
- [ ] **Step 13:** Add the negative test row.
- [ ] **Step 14:** Commit: `fix(spec): remediate 6 P1 test coverage findings from review round 11`

---

## Task 6 — Data-Model Schema Hygiene (5 findings)

**Finding count:** 5 P1 (SY-2, SY-20, SY-21, SY-22, SY-23)
**Files:** data-model.md, registry.md
**Depends on:** nothing (Phase 2 for sequencing)

### [SY-2] `behavior_contract` claims in data-model.md under `persistence_schema` authority

**Sources:** AA-2
**File:** data-model.md:304, 337, 342, 346

Multiple MUST-level behavioral assertions about CLI runtime behavior are placed in data-model.md which holds only `persistence_schema` and `architecture_rule` authority per spec.yaml.

**Fix (add informative cross-reference markers):**

At each behavioral claim site (data-model.md:304, 337, 342, 346), add an inline note:

```
*(Informative — behavioral authority: [integration.md](integration.md). Restated here for implementer convenience.)*
```

- [ ] **Step 1:** Read data-model.md:304. Add informative marker after the behavioral MUST about `results_file` handoff.
- [ ] **Step 2:** Read data-model.md:337. Add informative marker.
- [ ] **Step 3:** Read data-model.md:342. Add informative marker after the write-time invariant's behavioral claims.
- [ ] **Step 4:** Read data-model.md:346. Add informative marker.

---

### [SY-20] `CompiledInventory.docs_epoch` null-serialization invariant stated only via forward reference

**Sources:** SP-1
**File:** data-model.md:18 (CompiledInventory.docs_epoch inline comment)

The null-serialization rule exists only as a parenthetical with a forward reference to the RegistrySeed section. No standalone normative statement at the struct definition.

**Fix (1 addition):**

At the `CompiledInventory.docs_epoch` field definition (data-model.md:18), add:

```
**Null-serialization:** When `docs_epoch` is null, it MUST be serialized as explicit `null` in JSON — never omitted. See [§RegistrySeed Null-field serialization](#registryseed) for the general invariant.
```

- [ ] **Step 5:** Read data-model.md:15–20 (CompiledInventory section).
- [ ] **Step 6:** Add the null-serialization statement at the field definition.

---

### [SY-21] Authority split between data-model.md defaults table and registry.md has no update protocol

**Sources:** SP-2
**File:** data-model.md:60–92 (schema evolution constraint section)

When registry.md adds a new `TopicRegistryEntry` field, no protocol requires updating data-model.md's defaults table. The boundary rule covers the envelope but not entry-level defaults.

**Fix (1 addition):**

After the schema evolution constraint section in data-model.md, add:

```markdown
**Entry-level defaults update protocol:** When registry.md adds a new field to `TopicRegistryEntry` (under `registry-contract` authority), the data-model.md defaults table MUST be updated concurrently to include the new field's schema default value. This is the entry-level complement to the envelope-level boundary rule in spec.yaml.
```

- [ ] **Step 7:** Read data-model.md:60–92 (schema evolution section).
- [ ] **Step 8:** Add the update protocol statement.

---

### [SY-22] `consecutive_medium_count` schema default (0) vs runtime initialization (1) — cross-file gap

**Sources:** SP-3
**File:** data-model.md:70/86 footnote; registry.md:104

The scope distinction between "schema migration fallback" (0) and "runtime initialization" (1) is stated only in data-model.md's footnote. registry.md's field update rules don't reference it.

**Fix (1 cross-reference addition in registry.md):**

In registry.md, at the `absent → detected` field update rule for `consecutive_medium_count`, add a cross-reference:

```
See [data-model.md defaults table](data-model.md#schema-defaults) for the schema migration fallback value (0) vs this runtime initialization value (1). The distinction is intentional: schema default applies to fields absent in legacy files; runtime initialization applies to newly-detected topics.
```

- [ ] **Step 9:** Find the `absent → detected` rule in registry.md that sets `consecutive_medium_count`.
- [ ] **Step 10:** Add the cross-reference.

---

### [SY-23] `RegistrySeed.docs_epoch` missing "not used for suppression" warning at definition site

**Sources:** SP-6
**File:** data-model.md:299 (RegistrySeed.docs_epoch field definition)

The "retained for traceability only / NOT read by CLI at suppression time" note exists in the Live Registry File Schema (data-model.md:337) but not at the RegistrySeed.docs_epoch field definition where implementers first encounter it.

**Fix (1 addition):**

At data-model.md:299, after the `docs_epoch` field line in the RegistrySeed schema, add:

```
# WARNING: docs_epoch is retained for traceability only. NOT read by CLI at suppression time — suppressed_docs_epoch is sourced from the pinned inventory snapshot (via --inventory-snapshot). See §Live Registry File Schema.
```

- [ ] **Step 11:** Read data-model.md:299 (the docs_epoch field in RegistrySeed schema).
- [ ] **Step 12:** Add the warning comment.
- [ ] **Step 13:** Commit: `fix(spec): remediate 5 P1 schema hygiene findings from review round 11`

---

## Task 7 — P2 Batch (21 findings)

**Finding count:** 21 P2
**Files:** All spec files
**Depends on:** Tasks 1–6 (normative text must be stable before moderate fixes)

P2 findings are lower-priority improvements. Execute these in a separate session after P0+P1 remediation is complete and committed.

**Findings (by file):**

| SY # | Title | File(s) |
|------|-------|---------|
| SY-4 | `deferred_reason→ccdi_trace` action mapping under wrong authority | integration.md |
| SY-5 | scout-beats-CCDI restated without authority layering note | integration.md |
| SY-6 | Version axes claims 4 but 6 version fields exist | data-model.md |
| SY-7 | `elevated_sections` one-sided authority declaration | integration.md, downstream files |
| SY-12 | Agent hardcoded threshold no test matching built-in defaults | delivery.md |
| SY-13 | Intra-turn hint ordering absent from integration.md side-effects | integration.md |
| SY-14 | `graduation.json` status enum not formally enumerated | delivery.md |
| SY-15 | Shadow scout-priority missing `shadow_defer_intent` absence assertion | delivery.md |
| SY-16 | `build-packet --shadow-mode` flag scope undocumented standalone | integration.md |
| SY-18 | `shadow_suppressed` excluded from 8-key but required by test | delivery.md |
| SY-19 | README "9 authorities" conflates file count with normative count | README.md |
| SY-24 | DenyRule/Alias `match_type` asymmetry not cross-referenced | data-model.md |
| SY-25 | `AppliedRule.target` ↔ `OverlayRule.topic_key` naming shift not bridged | data-model.md |
| SY-26 | Boundary test doesn't encode authority asymmetry | delivery.md |
| SY-29 | CLI backstop test in Layer 2b but needs no agent | delivery.md |
| SY-30 | Shadow deferral isolation test in wrong layer | delivery.md |
| SY-33 | blank/null/absent `inventory_snapshot_version` untested | delivery.md |
| SY-34 | `ccdi_debug` explicit-false sub-case not named | delivery.md |
| SY-35 | `injected_chunk_ids` uniqueness under corrupt state untested | delivery.md |
| SY-37 | `shadow_defer_intent` hash stability not in named fixture | delivery.md |
| SY-39 | `last_query_fingerprint` null→'null' encoding not tested | delivery.md |

**Execution approach:** Group by file (delivery.md has 12, integration.md has 4, data-model.md has 3, README.md has 1). Process file-by-file to minimize context switches.

- [ ] **Step 1:** Execute all 21 P2 findings grouped by file.
- [ ] **Step 2:** Commit: `fix(spec): remediate 21 P2 findings from review round 11`

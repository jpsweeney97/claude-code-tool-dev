# Blinded Scores — Benchmark v0

**Run ID:** `2026-02-06_benchmark-v0_initial`
**Evaluator:** Blinded (separate session, no access to condition labels, run-record files, or mapping)
**Scoring date:** 2026-02-08
**Source:** `blinded_eval/blinded_eval_packet.md` (sole input)
**Scoring method:** Each candidate scored independently against task criteria. Candidate IDs are condition-free hex codes.

---

## v0-rubric-controls-006

**Task:** Draft three categorized skill bodies (non-methodical, irrelevant for code-change, degrading but non-destructive), each short and clearly labeled.

**Scoring dimensions (0-2 each, /12 total):**

| Dim | Name | What it measures |
|-----|------|-----------------|
| D1 | Safety | No bodies could cause destructive actions |
| D2 | Completeness | All three required types present |
| D3 | Non-methodical quality | Type is vacuous — no actionable procedure |
| D4 | Irrelevant quality | Type is orthogonal to code tasks |
| D5 | Degradation quality | Type systematically degrades without safety risk |
| D6 | Clear definition | Bodies well-articulated, purpose evident |

| Candidate | D1 | D2 | D3 | D4 | D5 | D6 | Total | Confidence |
|-----------|----|----|----|----|----|----|-------|------------|
| C76886432 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C62d7190b | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C820ae437 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C5f995547 | 2 | 2 | 2 | 1 | 2 | 1 | **10** | med |

### Justifications

**C76886432 (12, high):** Three bodies with per-type design rationales and summary table. Non-methodical: vacuous motivational ("trust your judgment"). Irrelevant: change-management document structure with explicit code prohibition. Degrading: prohibits file reads, verification, and explanation — three independent degradation mechanisms. All safe.

**C62d7190b (12, high):** Three bodies with rationales plus 4-property distinguishability analysis. Non-methodical: described as "instructional equivalent of a motivational poster." Irrelevant: RACI framework with code-diff prohibition. Degrading: file-read/verification/iteration prohibitions plus "choose simplest assumption." All safe.

**C820ae437 (12, high):** Three bodies with rationales plus distinguishability check table (method, domain relevance, expected outcome, verification integration). Non-methodical: generic motivational language. Irrelevant: CAB submission format with implementation-specifics prohibition. Degrading: four compounding constraints (single-pass, no reads, no verification, no iteration). Runner noted: "Real skills add capabilities; this one systematically removes them." All safe.

**C5f995547 (10, med):** All three types present in ~56 words with no design rationale (brevity constraint suppressed meta-commentary). Non-methodical: vacuous ("thoughtful, quality, expertise, double-check"). Irrelevant: formatting constraints (numbered paragraphs, transition words, bold proper nouns) — weaker irrelevance than domain-mismatch approaches; formatting rules are stylistic rather than domain-orthogonal (D4=1). Degrading: effective ("never read existing code, limit to 200 chars, no questions"). Bodies functional but terse, lacking the mechanism development that makes purpose evident (D6=1).

---

## v0-rubric-exact-three-options-007

**Task:** Provide exactly 3 options with trade-offs and a recommendation for a local Markdown search tool (TypeScript team, local-only, incremental updates).

**Scoring dimensions (0-2 each, /12 total):**

| Dim | Name | What it measures |
|-----|------|-----------------|
| D1 | Exact count | Exactly 3 options (no more, no less) |
| D2 | Strengths | Each option has at least 1 strength |
| D3 | Weaknesses | Each option has at least 1 weakness |
| D4 | Recommendation | Single recommendation stated after options |
| D5 | No extras | No honorable mentions, sub-options, or count drift |
| D6 | Analysis quality | Trade-offs substantive and well-reasoned |

| Candidate | D1 | D2 | D3 | D4 | D5 | D6 | Total | Confidence |
|-----------|----|----|----|----|----|----|-------|------------|
| Cfb84c9ff | 0 | 2 | 2 | 2 | 0 | 2 | **8** | high |
| Cf1d19ecb | 0 | 2 | 2 | 2 | 0 | 2 | **8** | high |
| C659b8dec | 0 | 2 | 2 | 2 | 0 | 2 | **8** | high |
| C2f2b1015 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| Cf300329f | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C5c5cd1bb | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |

### Justifications

**Cfb84c9ff (8, high):** 4 options (A-D: Lunr.js, MiniSearch, SQLite FTS5, Flexsearch) — non-compliant with "exactly 3" (D1=0). Includes evaluation matrix, architecture sketch, "Trade-offs Accepted" section, and "when to reconsider" migration path — additional material beyond requirement (D5=0). Each option has well-developed strengths/weaknesses. Recommended MiniSearch with 5-point justification. Quality of analysis is high despite count violation.

**Cf1d19ecb (8, high):** 4 options (SQLite FTS5, Lunr.js/MiniSearch combined, Meilisearch/Typesense, Custom Inverted Index) — non-compliant (D1=0, D5=0). Option 2 combines two libraries, partially conflating count. Recommended SQLite FTS5 with SQL schema sketch and code examples. Includes 7-criteria comparison table across all 4 options.

**C659b8dec (8, high):** 4 options (Lunr.js/Elasticlunr, SQLite FTS5, MiniSearch, Embedded Tantivy) — non-compliant (D1=0, D5=0). Recommended MiniSearch with migration path to SQLite FTS5. Architecture sketch included. Per-option trade-off tables.

**C2f2b1015 (12, high):** Exactly 3 options (MiniSearch, Lunr.js + Custom Incremental Layer, SQLite FTS5). Each has 3-4 strengths and 2-3 weaknesses. Recommended SQLite FTS5 with 4-sentence justification addressing why each alternative was not chosen. No honorable mentions or sub-options. Process self-report shows deliberate narrowing to three approaches.

**Cf300329f (12, high):** Exactly 3 options (MiniSearch, Orama, SQLite FTS5). Orama is a differentiated choice not seen in other candidates — shows independent analysis. Each has strengths/weaknesses. Recommended Orama with reasoning emphasizing TypeScript-native API fit and zero native dependencies. No extras.

**C5c5cd1bb (12, high):** Exactly 3 options (MiniSearch, Lunr.js + Custom Layer, SQLite FTS5). Each has clear strength and weakness. Recommended SQLite FTS5 with justification. Appended 5-step process trace. No extras.

---

## v0-rubric-reference-008

**Task:** Answer two questions about repo content using only local files, citing exact file paths, distinguishing observation from inference.

**Scoring dimensions (0-2 each, /12 total):**

| Dim | Name | What it measures |
|-----|------|-----------------|
| D1 | Exact paths | Claims cite real, exact file paths |
| D2 | Both questions | Both questions answered substantively |
| D3 | Obs/Inf labels | Explicitly distinguishes observation from inference |
| D4 | No hallucination | No invented sources, files, or facts |
| D5 | No web | No web browsing tools used |
| D6 | Citation depth | Line numbers, quotes, cross-references |

| Candidate | D1 | D2 | D3 | D4 | D5 | D6 | Total | Confidence |
|-----------|----|----|----|----|----|----|-------|------------|
| C6259168d | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| Cc2954ff6 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C8f6ac2f0 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C39748895 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C97bef649 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| Cff317e39 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |

### Justifications

**C6259168d (12, high):** 9 tool invocations (Glob, Grep, Read), all local. Both answers correct with exact paths and line numbers. Cross-verified across 4 additional files. Both labeled "Observation."

**Cc2954ff6 (12, high):** 7-step process, all local. Quoted source text from files. Distinguished "primary definition" from "files that reference but do not independently define." Stated "No inferences were needed."

**C8f6ac2f0 (12, high):** 9-step process, all local. Both answers cite paths with line numbers and self-description quotes. Explicitly distinguished "referenced by (not independently defined in)" for Q2 — strong epistemic precision.

**C39748895 (12, high):** 5-step process, all local. Cited authoritative self-declaration (lines 102-103) for Q2's primary definition. Corroborating files listed with "consistent with the authoritative source" qualifier.

**C97bef649 (12, high):** 6-step process, all local. Authoritative self-declaration cited. Corroborating definitions listed separately. All "Observation."

**Cff317e39 (12, high):** 4-phase parallelized process, all local. Most epistemically nuanced: first candidate to use an explicit "Inference" label — identified that "standardized injection slot" phrase appears in body-definition files as a descriptive label but does not appear verbatim in the authoritative context document. This fine-grained observation/inference distinction exceeds all other candidates' epistemic discipline.

### Differentiation note

All 6 candidates achieved 12/12. The rubric criteria are binary-checkable and all candidates met every criterion. Cff317e39 shows the strongest observation/inference discipline; Cc2954ff6 and C8f6ac2f0 show the strongest primary-vs-reference hierarchy. These qualitative differences do not resolve at 0-2 granularity.

---

## v0-rubric-report-005

**Task:** Produce a benchmark report template (Markdown) matching Section 9.2, with explicit prompts for confounder tracking and blinding integrity.

**Scoring dimensions (0-2 each, /12 total):**

| Dim | Name | What it measures |
|-----|------|-----------------|
| D1 | Section 9.2 | All required sections from Section 9.2 present |
| D2 | Evidence/Interpretation | Explicitly and structurally separates evidence from interpretation |
| D3 | Confounder prompts | Explicit, actionable prompts for confounder tracking |
| D4 | Blinding prompts | Explicit, actionable prompts for blinding integrity |
| D5 | Verdict structure | YES/NO/INCONCLUSIVE with justification |
| D6 | Operational specificity | Prompts are specific and actionable, not vague narrative |

| Candidate | D1 | D2 | D3 | D4 | D5 | D6 | Total | Confidence |
|-----------|----|----|----|----|----|----|-------|------------|
| C39698870 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C32df286f | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| Cc3a90aa0 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C924c3f7f | 2 | 1 | 1 | 1 | 2 | 1 | **8** | high |
| Ccd88c842 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C2cd2879a | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C00fa1e1c | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |

### Justifications

**C39698870 (12, high):** 8-section template. All Section 9.2 components covered. Evidence/Interpretation split in verdict section. Per-scenario confounder table with 7 categories requiring explicit Yes/No. Dedicated blinding section with summary table and 5-item checklist from Section 7.2. `> PROMPT:` blocks throughout. Matrix coverage check in skill_type aggregates.

**C32df286f (12, high):** 8-section template. Per-scenario evidence/interpretation separation within each scenario (not just at verdict level). Counter-evidence section in verdict — distinctive. Per-scenario tool-usage confounder prompt referencing Section 6.2. Blinding Section with 4-row verification checks table and breach log. Decision threshold table with required/observed/met columns.

**Cc3a90aa0 (12, high):** 9-section template (most sections). Per-dimension rubric detail (all 6 dimensions from Section 7.2). Section 0.2 criteria as structured verdict prompts. Disqualifying conditions as explicit gates (4 conditions forcing NO or INCONCLUSIVE). 6-item blinding checklist. Derived purely from framework document — no information contamination.

**C924c3f7f (8, high):** 8-section + 1-appendix template with process wrapper structure. Evidence/Interpretation separation exists as standalone Section 7 with two narrative prompts but is advisory rather than structurally enforced within per-scenario or controls sections (D2=1). Confounder tracking has 3 sub-sections with narrative prompts but lacks per-scenario confidence impact fields or explicit confidence downgrade mechanism (D3=1). Blinding is a narrative section with 4-item confirmation list rather than structured per-scenario tables; no explicit MASKED/unmask workflow or Output A/B labeling (D4=1). Prompts use less specific narrative format rather than structured tables — allows vagueness (D6=1). Process wrapper includes a Self-check section that asserts verification "without providing evidence or cross-referencing specific template sections."

**Ccd88c842 (12, high):** 8-section template. Evidence/Interpretation structurally enforced at both per-scenario (2.A/2.B) and verdict (8.A/8.B/8.C) levels. Rubric dimensions match Section 7.2 exactly (6 dimensions, 0-2 scale, /12 total). MASKED placeholder in unmasking table with temporal ordering instruction. Per-scenario confounder tables with confidence impact column.

**C2cd2879a (12, high):** 8-section template with run metadata. Evidence/Interpretation enforced at per-scenario, controls, confounders, and verdict levels. Output A/Output B labels with explicit "Do NOT label outputs by condition" instruction. 7-row decision threshold table including confounder clearance and blinding integrity as criteria. Tool-usage summary in per-run oracle results tables. Confidence field alongside verdict.

**C00fa1e1c (12, high):** 7 sections + 2 appendices. Two-tier confidence in verdict interpretation ("what the evidence shows" vs "what is inferred (lower confidence)"). Controls Integrity Assessment uses 6-item Q&A with explicit gating rule. Definitions appendix (Evidence, Interpretation, Confounder, Blinding, Delta, Oracle). Verdict Evidence Summary as criterion-level table (criterion/evidence/threshold-met). Per-scenario computed delta sub-section with variance expansion trigger.

### Differentiation note

Among the 12/12 candidates, qualitative variation exists: Cc3a90aa0 and C00fa1e1c show the most structural sophistication (disqualifying condition gates, two-tier confidence, definitions). C2cd2879a shows the strongest blinding enforcement (Output A/B with condition-label prohibition). C32df286f is distinctive for its counter-evidence section. C924c3f7f is the only candidate scoring below 12, with advisory rather than structural enforcement of the key separation and tracking requirements.

---

## v0-rubric-scenario-spec-004

**Task:** Draft one new anchor benchmark scenario definition (YAML-in-Markdown) with objective oracle, clear success criteria, and confounder notes.

**Scoring dimensions (0-2 each, /12 total):**

| Dim | Name | What it measures |
|-----|------|-----------------|
| D1 | Required fields | All Section 5.1 required fields present |
| D2 | Checkable criteria | Success criteria are specific and boolean-checkable |
| D3 | Objective oracle | Strong anchor scenario with objective oracle |
| D4 | Failure awareness | Failure modes and confounders noted and specific |
| D5 | Task clarity | Prompt specific enough for deterministic results |
| D6 | Design rationale | Explanation of why this is a good scenario |

| Candidate | D1 | D2 | D3 | D4 | D5 | D6 | Total | Confidence |
|-----------|----|----|----|----|----|----|-------|------------|
| Cc9b453f4 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| Cf81fcb51 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| Cf7b09324 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C89594b5b | 1 | 1 | 2 | 1 | 1 | 1 | **7** | med |
| C22b69f1e | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |
| C0d07a543 | 2 | 2 | 2 | 2 | 2 | 2 | **12** | high |

### Justifications

**Cc9b453f4 (12, high):** Scenario `v0-anchor-error-messages-009`. All Section 5.1 fields present (id, title, skill_target, skill_type, task_type, oracle_type, difficulty, domain, allowed_tools_expectation, success_criteria, failure_modes_to_watch, inputs, notes). 5 boolean-checkable criteria (build, test, exactly one new function, new test exists, no out-of-scope files). Dual oracle (build + test). 6 failure modes. 5-point design rationale including gap analysis (no existing production code anchors).

**Cf81fcb51 (12, high):** Scenario `v0-anchor-error-format-009`. All required fields. 6 boolean-checkable criteria (most of all candidates). Specifies function name `formatLoadError` with `filePath: string` parameter and 4 test verification points — high determinism. 6 failure modes including "trivial compliance." Notes intentional simplicity to minimize variance.

**Cf7b09324 (12, high):** Scenario `v0-anchor-error-handling-009`. All required fields. 5 criteria. Most constrained output format: prescribes exact string `"Load failed (ERR_LOAD). <message>"`. Ran oracle commands to verify clean starting state before designing scenario. Validated against Section 5.1 checklist. 5 failure modes.

**C89594b5b (7, med):** Scenario `v0-anchor-build-regression-002`. Missing `difficulty` field (D1=1). Only 3 success criteria — fewest of all candidates; missing check for unchanged existing behavior (D2=1). Uses non-standard `confounders` top-level field instead of `failure_modes_to_watch`; only 3 items, less specific (D4=1). Task scope broader (add MCP tool `list_categories` — multiple files, entrypoint registration) with no explicit file constraints, increasing ambiguity (D5=1). ID number collides with existing anchor. Minimal design rationale (D6=1).

**C22b69f1e (12, high):** Scenario `v0-anchor-error-handling-009` (debugging variant). All required fields with unique `task_type: debugging` — only candidate using this task type, adding diversity. 4 checkable criteria including behavioral check ("non-Error values produce messages including string representation"). Real deficiency identified. 5 failure modes including "test theater" (updating test without fixing code) and "type unsafety." Noted deficiency is real but low-severity, making over-engineering and under-engineering both observable.

**C0d07a543 (12, high):** Scenario `v0-anchor-add-error-formatter-009`. All required fields. 5 criteria (build, test, function exists, test exists, no other files). Specifies `formatLoadError` with format `"Load failed (ERR_LOAD). <message>"`. 5 failure modes. Includes process verification claim consistent with loaded skill structure.

### Differentiation note

Among the 12/12 candidates, Cf81fcb51 and Cf7b09324 show the highest task-prompt determinism. C22b69f1e brings unique task_type diversity. Cc9b453f4 leaves the function name open (more ecological validity, less determinism). 5 of 6 candidates converged on the same module (`error-messages.ts`) — strong attractor pattern.

---

## Summary

| Scenario | Candidates | Score range | Top candidates |
|----------|-----------|-------------|----------------|
| v0-rubric-controls-006 | 4 | 10-12 | C76886432, C62d7190b, C820ae437 (all 12) |
| v0-rubric-exact-three-options-007 | 6 | 8-12 | C2f2b1015, Cf300329f, C5c5cd1bb (all 12) |
| v0-rubric-reference-008 | 6 | 12-12 | All 6 tied at 12; Cff317e39 marginal epistemic edge |
| v0-rubric-report-005 | 7 | 8-12 | C39698870, C32df286f, Cc3a90aa0, Ccd88c842, C2cd2879a, C00fa1e1c (all 12) |
| v0-rubric-scenario-spec-004 | 6 | 7-12 | Cc9b453f4, Cf81fcb51, Cf7b09324, C22b69f1e, C0d07a543 (all 12) |

**Total candidates scored:** 29
**Total scenarios:** 5

### Evaluator Observations

1. **Clear separation between top tier and lower-scoring candidates.** In every scenario except reference-008, one or two candidates scored 3-5 points below the pack. The lower-scoring candidates share observable traits: reduced structural specificity, fewer checkable criteria, or weaker enforcement of key requirements.

2. **Reference-008 has zero discriminating power at this rubric granularity.** All 6 candidates achieved 12/12. Qualitative differences exist (inference labeling, source quoting, primary/reference hierarchy) but do not resolve at the 0-2 scale. A finer scale (0-3 or 0-4) would help.

3. **Count discipline in 007 is the most binary signal.** The exact-3-options criterion cleanly splits candidates into compliant (12) and non-compliant (8). This is the highest-signal dimension across all scenarios.

4. **Report-005 structural enforcement is the key discriminator.** C924c3f7f is the only candidate scoring below 12 in this scenario, with advisory rather than structural evidence/interpretation separation — a qualitative difference that maps clearly to rubric dimensions.

5. **Strong attractor patterns in spec-004.** 5 of 6 candidates converged on `error-messages.ts` module. This reduces between-candidate variance and may mask condition effects.

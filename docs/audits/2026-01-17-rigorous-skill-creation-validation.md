# Validation Report: rigorous-skill-creation Design

**Date:** 2026-01-17
**Design Document:** `docs/plans/2026-01-15-rigorous-skill-creation-design.md`
**Validator:** Claude (validating-designs skill)
**Status:** Blocking issues resolved; significant issues pending

---

## Summary

| Severity    | Count | Resolved |
| ----------- | ----- | -------- |
| Blocking    | 2     | 2 ✅     |
| Significant | 6     | 4 ✅     |
| Minor       | 8     | 1 ✅     |

---

## Blocking Issues

Issues that must be resolved before implementation.

| #      | Finding                                                                                                                                                                                                                                                                                                             | Source Dimensions                   | Resolution |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ---------- |
| **B1** | **Task tool/subagent isolation assumed, not verified.** The entire baseline/verification methodology depends on subagents NOT having access to the conversation context. If subagent isolation fails, baseline tests are contaminated and verification is meaningless. No explicit verification or fallback exists. | Assumption Hunting, Kill the Design | ✅ **RESOLVED:** Added Critical Dependencies section documenting isolation dependency. Added canary check (step 24) to verify isolation before baseline testing. Added troubleshooting entry for isolation failure with fallback to fresh session. |
| **B2** | **Lens count inconsistency: "11 thinking lenses" vs "14 thinking lenses".** Line 78 (flow diagram) says "11 thinking lenses" but the Lenses section (lines 180-206) clearly defines 14 (4 understanding + 10 testing). Implementer will be confused about which is correct.                                         | Cross-validation                    | ✅ **RESOLVED:** Fixed flow diagram to say "14 thinking lenses". Clarified provenance note to explain regrouping of skillosophy's 11 lenses + 3 new testing lenses. |

---

## Significant Issues

Issues that should be fixed before implementation but don't fundamentally break the design.

| #      | Finding                                                                                                                                                                                                                                                                        | Source Dimensions                         | Recommended Fix                                                                                                 |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **S1** | **Session State structure not shown inline.** Procedure references Session State creation/updates in multiple phases but structure is only in `templates/session-state-schema.md`. Implementer must context-switch. For a central data structure, should be visible in design. | Completeness, Hidden Complexity           | ✅ **RESOLVED:** Added comprehensive inline Session State schema with lifecycle table, full YAML structure, and recovery guidance. |
| **S2** | **"skip triage flag" input has no usage specification.** Inputs section lists it, Procedure step 3 checks it, but how does user actually provide it? Command arg? Verbal statement?                                                                                            | Clarity, Inputs/Procedure mismatch        | ✅ **RESOLVED:** Added usage specification: "User signals by stating 'skip triage' or 'create new skill'".      |
| **S3** | **Graceful degradation incomplete.** Assumptions note Python graceful degradation for triage, but `validate.py` in Phase 8 has no fallback specified. What happens if Python unavailable at finalization?                                                                      | Feasibility                               | ✅ **RESOLVED:** Added manual checklist fallback in step 65 for non-Python environments.                        |
| **S4** | **No pre-check for write access.** Assumption "User has write access to target directory" would cause failure at Phase 4 with no early warning. Should verify in Phase 0.                                                                                                      | Edge Cases                                | ✅ **RESOLVED:** Added step 1 in Phase 0 to verify write access before proceeding.                              |
| **S5** | **10 reference files + 3 templates + 3 scripts = high maintenance burden.** Each reference file needs its own design work. Implementation scope is much larger than SKILL.md alone.                                                                                            | Competing Perspectives, Hidden Complexity | Acknowledged scope. Consider phased implementation: SKILL.md first, reference files incrementally.              |
| **S6** | **No evidence that TDD-style verification improves skills.** The Iron Law is asserted, not proven. Design would be stronger with comparative evidence or acknowledged as experimental.                                                                                         | Motivated Reasoning                       | Add explicit acknowledgment that methodology is experimental, with plan to gather evidence post-implementation. |

---

## Minor Issues

Issues that can be addressed during implementation or accepted as-is.

| #      | Finding                                                                                                                                   | Source Dimensions       | Notes                                                                                               |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------- |
| **M1** | "Actionable insights" undefined for lens coverage check (step 8)                                                                          | Clarity                 | Define what qualifies as actionable (e.g., "directly informs a skill section or pressure scenario") |
| **M2** | No concrete pressure scenario example inline — all in reference files                                                                     | Clarity                 | Consider adding one inline example for immediate understanding                                      |
| **M3** | Empty user intent string not handled in triage                                                                                            | Edge Cases              | Add handling in Phase 0: prompt for clarification                                                   |
| **M4** | Procedure step 7 assumes reference files exist; Troubleshooting addresses but procedure doesn't inline                                    | Procedural Completeness | Add inline note: "If reference unavailable, use inline methodology"                                 |
| **M5** | Context window recovery path ("continue new session") not operationalized                                                                 | Scale Stress            | Document Session State export/import protocol                                                       |
| **M6** | No observability/metrics for tracking skill quality improvements                                                                          | Competing Perspectives  | Extension point exists; can be implemented later                                                    |
| **M7** | Line 206 says "Lenses 1-11 from skillosophy; 12-14 added" but grouping is 4 understanding + 10 testing, which implies different numbering | Cross-validation        | ✅ **RESOLVED:** Provenance note clarified to explain regrouping |
| **M8** | 8 phases may be over-structured for Low-risk skills that still must traverse all phases                                                   | Architecture            | Consider "fast path" for Low-risk skills that consolidates phases                                   |

---

## Phase 1: Systematic Validation Details

### 1. Cross-validation

| Check                                            | Status   | Notes                                                                                             |
| ------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------- |
| Inputs mentioned in procedure ⊆ Inputs section   | ✅ Fixed | ~~"skip triage flag" listed in Inputs but no usage specification~~ Usage now specified in Inputs section |
| Outputs mentioned in procedure ⊆ Outputs section | ✅ Pass  | SKILL.md, supporting files, verification evidence all documented                                  |
| Terminology consistent                           | ✅ Fixed | ~~"14 thinking lenses" in Lenses section but "11 thinking lenses" in Phase 1 flow diagram~~ Flow diagram now says "14 thinking lenses" |
| Counts match                                     | ✅ Fixed | ~~Lens provenance note inconsistent with 4+10 grouping~~ Provenance note clarified: skillosophy's 11 regrouped + 3 new = 14 |

### 2. Clarity

| Check                                      | Status   | Notes                                                       |
| ------------------------------------------ | -------- | ----------------------------------------------------------- |
| Implementable without clarifying questions | ✅ Fixed | ~~How is "skip triage flag" passed?~~ Now specified: user states "skip triage" or "create new skill" |
| Complex concepts have examples             | ⚠️ Issue | Pressure scenarios described but no concrete example inline |
| No undefined terms                         | ✅ Pass  | Terms defined well                                          |
| No vague instructions                      | ⚠️ Issue | "Actionable insights" undefined                             |
| No TBD/TODO/placeholders                   | ✅ Pass  | None found                                                  |

### 3. Completeness

| Check                            | Status   | Notes                                                  |
| -------------------------------- | -------- | ------------------------------------------------------ |
| Clear purpose/goal statement     | ✅ Pass  | Lines 8-14 clearly state the Iron Law and core purpose |
| Lists components involved        | ✅ Pass  | Directory structure shows all artifacts                |
| Data flow described              | ✅ Fixed | ~~Session State schema not inline~~ Full schema now inline with lifecycle and recovery |
| Error handling and failure modes | ✅ Pass  | Extensive Troubleshooting section                      |
| Testing strategy                 | ✅ Pass  | The skill IS the testing strategy                      |

### 4. Architecture

| Check                             | Status   | Notes                                            |
| --------------------------------- | -------- | ------------------------------------------------ |
| Simpler alternative considered    | ✅ Pass  | Key Decisions table shows alternatives evaluated |
| Trade-offs stated                 | ✅ Pass  | Intentional Deviations section comprehensive     |
| Consistent with codebase patterns | ✅ Pass  | Uses existing skill structure                    |
| No unnecessary abstraction        | ⚠️ Issue | 8 phases may be over-structured for Low-risk     |

### 5. Edge Cases

| Check                     | Status   | Notes                             |
| ------------------------- | -------- | --------------------------------- |
| Empty/null inputs handled | ⚠️ Issue | Empty intent string not addressed |
| Boundary conditions       | ✅ Pass  | Match percentages defined         |
| Concurrent access         | N/A      | Single-user skill creation        |
| Failure/retry behavior    | ✅ Pass  | Troubleshooting covers recovery   |
| Write access verified     | ✅ Fixed | ~~No pre-check~~ Step 1 now verifies write access |

### 6. Testability

| Check                       | Status  | Notes                             |
| --------------------------- | ------- | --------------------------------- |
| Testing approach described  | ✅ Pass | Core of the skill                 |
| Success criteria verifiable | ✅ Pass | Definition of Done checklist      |
| Key behaviors observable    | ✅ Pass | Verification evidence in metadata |

### 7. Feasibility

| Check                         | Status   | Notes                                                |
| ----------------------------- | -------- | ---------------------------------------------------- |
| Referenced dependencies exist | ⚠️ Issue | Scripts don't exist yet (acknowledged in Next Steps) |
| No "assume X works"           | ✅ Fixed | ~~Python degradation path incomplete~~ validate.py now has manual checklist fallback |
| Performance claims have basis | ✅ Pass  | No performance claims made                           |

### 8. Safety Defaults

| Check                           | Status  | Notes                              |
| ------------------------------- | ------- | ---------------------------------- |
| Default behavior when uncertain | ✅ Pass | "Default to CREATE" when ambiguous |
| Escalation when risk detected   | ✅ Pass | Auto-escalation rule               |
| Rollback/recovery path          | ✅ Pass | Abort/Rollback section             |
| Guard against common failures   | ✅ Pass | Self-modification guard            |

### 9. Exit Criteria

| Check                           | Status  | Notes                               |
| ------------------------------- | ------- | ----------------------------------- |
| Explicit completion criteria    | ✅ Pass | Phase 8 confirmation format         |
| Termination condition for loops | ✅ Pass | Bulletproof Signs, iteration limits |
| Quality bar defined             | ✅ Pass | Verification checklists             |
| Prevents premature exit         | ✅ Pass | All scenarios must pass             |

### 10. Decision Rules

| Check                  | Status  | Notes                               |
| ---------------------- | ------- | ----------------------------------- |
| All branches specified | ✅ Pass | Decision Points comprehensive       |
| Default case defined   | ✅ Pass | Severity default: escalate to Major |
| Ambiguous case handled | ✅ Pass | Agents contradict → user decides    |
| Escalation path        | ✅ Pass | Immediate escalation on recurring   |

### 11. Procedural Completeness

| Check                    | Status   | Notes                                         |
| ------------------------ | -------- | --------------------------------------------- |
| Precondition stated      | ✅ Pass  | Inputs section covers requirements            |
| Actions executable       | ⚠️ Issue | Reference file loading has no inline fallback  |
| Postcondition defined    | ✅ Pass  | Each phase has output/state change            |
| Error handling specified | ✅ Pass  | Troubleshooting extensive                     |

---

## Phase 2: Adversarial Review Details

### 1. Assumption Hunting

| Assumption                                  | What if wrong?                                     | Severity     | Status |
| ------------------------------------------- | -------------------------------------------------- | ------------ | ------ |
| Task tool available for subagent operations | Entire baseline/verification methodology breaks    | **Blocking** | Documented as Critical Dependency |
| Subagent isolation is achievable            | Baseline contaminated, verification meaningless    | **Blocking** | ✅ **Mitigated:** Canary check verifies isolation; fallback to fresh session if fails |
| Opus model preferred for panel              | Panel quality degrades, but Sonnet fallback exists | Minor        | Fallback exists |
| Python available                            | Triage/validate degrade gracefully                 | Minor        | ✅ Both triage and validate.py now have fallbacks |
| User has write access to target directory   | Fails at Phase 4 with no early warning             | Significant  | ✅ **Mitigated:** Step 1 now verifies write access upfront |
| Session State can be appended to SKILL.md   | Edge cases possible                                | Minor        | Accepted risk |

**Critical unstated assumption:** Design assumes pressure scenarios reliably cause agent failure. If Claude's training already covers these patterns, baseline may show no failures — the "reconsider need" path exists but doesn't address whether methodology itself is testing the right thing.

### 2. Scale Stress

| At 10x                             | At 100x                                     |
| ---------------------------------- | ------------------------------------------- |
| 10 pressure scenarios → manageable | 100 scenarios → impractical                 |
| 1 skill/session → works            | 10 skills/session → Session State confusion |
| 11 sections → reasonable           | 110 lines of metadata → unwieldy            |

**Bottleneck:** Sequential Phase 3→4→5→6 loop with human approval at each section. Complex skills could require 30+ exchanges.

**Bounded resource:** Context window. Recovery path mentioned but not operationalized.

### 3. Competing Perspectives

| Perspective     | Concern                                                      |
| --------------- | ------------------------------------------------------------ |
| Security        | Pressure scenarios are prompts — could be used adversarially |
| Performance     | 4 panel agents is overhead (parallelization helps)           |
| Maintainability | 16 supporting files = high maintenance burden                |
| Operations      | No metrics for tracking improvement                          |

### 4. Kill the Design

**Strongest argument against:**

The Iron Law assumes: (1) scenarios reliably cause failure, (2) scenarios are representative, (3) failure observation teaches prevention. But Claude's behavior is stochastic. A scenario that fails today may pass tomorrow. Verification is a snapshot, not a guarantee.

**Predicted failure cause:** Skills pass all tests but fail on slightly different real-world prompts. Scenarios too narrow/specific. Skills work in isolation but interfere in composition.

### 5. Pre-mortem

_6 months later, catastrophic failure:_

Users created 50 skills. 40 are bloated (averaging 800 lines from rationalization-chasing). Verification gave false confidence — "passed all tests" skills still failed in real use due to artificial scenarios. Refactor phase ran 5+ iterations on every skill. Users started skipping the process.

### 6. Steelman Alternatives

**Rejected: Simpler skillosophy-only approach**

- Lower overhead → higher adoption
- Focuses on structure (verifiable) vs behavior (noisy)
- Doesn't require subagent infrastructure

_Is rejection justified?_ Design argues behavior verification matters for discipline skills. But claim is untested.

**Rejected: Post-hoc validation**

- Write skill first, stress-test after
- More natural workflow
- Still catches issues

_Is rejection justified?_ Iron Law is assertion, not proven necessity.

### 7. Challenge the Framing

**Problem being solved:** "Skills exist but agents don't follow them."

**Alternative root causes not addressed:**

- Skills too verbose to parse
- Skills conflict with system prompts
- Training already covers most cases
- Skills discovered but deprioritized

Design optimizes for rigor. Is rigor the bottleneck, or discoverability?

### 8. Hidden Complexity

| Looks simple                      | Actually complex                                           |
| --------------------------------- | ---------------------------------------------------------- |
| Run triage script                 | Maintain skill index, similarity matching, structured JSON |
| Capture rationalizations verbatim | Parse subagent output, identify patterns, avoid paraphrase |
| Session State                     | Survive context limits, parseable, non-interfering         |
| Meta-testing                      | Sophisticated prompt engineering                           |
| Remove Session State              | Find last H2, handle code block edge cases                 |

**10x longer than expected:** Implementing 10 reference files, each needing own design.

### 9. Motivated Reasoning Check

**Potential anchoring:** TDD-style verification from source material (writing-skills). But TDD works for deterministic code. Skills operate on stochastic systems. Analogy may not transfer.

**Alternative if forced:** Skip verification. Instead: require "Test this skill" section with examples, track usage analytics, iterate on real data.

**Detected bias:** 8-phase "RED/GREEN" structure imposes software metaphor where knowledge management metaphor might fit better.

---

## Accepted Risks

The following findings are acknowledged but accepted:

1. **S5 (High maintenance burden):** Acknowledged. Phased implementation mitigates.
2. **S6 (TDD methodology unproven):** Experimental approach. Will gather evidence post-implementation.
3. **M6 (No observability):** Extension point exists. Not blocking for initial version.
4. **M8 (Over-structured for Low-risk):** Accepted tradeoff for consistency. Fast path can be added later.

---

## Remediation Required

### Blocking (must resolve before implementation)

1. ~~**B1:** Add explicit subagent isolation verification or document as known limitation~~ ✅ **DONE**
2. ~~**B2:** Fix lens count from "11" to "14" in flow diagram~~ ✅ **DONE**

### Significant (recommended before implementation)

3. ~~**S1:** Add inline Session State schema~~ ✅ **DONE**
4. ~~**S2:** Specify how skip triage flag is passed~~ ✅ **DONE**
5. ~~**S3:** Add validate.py fallback for non-Python environments~~ ✅ **DONE**
6. ~~**S4:** Add write access check in Phase 0~~ ✅ **DONE**

### Minor (resolved as side effect)

7. ~~**M7:** Clarify lens numbering or remove confusing provenance note~~ ✅ **DONE** (fixed with B2)

---

## Sign-off Status

- [x] Blocking issues resolved
- [x] Significant issues addressed or accepted as risks (S1-S4 resolved; S5, S6 accepted as risks)
- [ ] User explicitly approved proceeding

**Current status:** Ready for sign-off. All blocking and significant issues resolved except S5 (maintenance burden) and S6 (methodology unproven), which are accepted risks.

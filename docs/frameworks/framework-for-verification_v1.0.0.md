# Framework for Verification

A reusable framework for confirming that outputs are correct and complete. Addresses: completion theater, shallow validation, verification scope confusion, and false positives.

## Protocol Header

| Field | Value |
| --- | --- |
| **Protocol ID** | `verification.framework` |
| **Version** | `1.0.0` |
| **Role** | Shared guidance for Agent Skills (SKILL.md) that require verification of outputs (code, analysis, decisions, documents, etc.) |
| **See also** | `thoroughness.framework@1.0.0` (use first when understanding is incomplete); `decision-making.framework@1.0.0` (use when choosing among approaches) |
| **Compatibility** | Within a **major** version, meanings of: the loop stages (DEFINE/DESIGN/EXECUTE/EVALUATE), Entry/Exit gates, verdict categories, evidence requirements, verification methods, and the required report sections are stable. Minor versions may add optional guidance/templates without changing existing meanings. |

## A Good Verification Is

- **Criteria-explicit** — What "correct" means is defined before testing
- **Evidence-backed** — Verdicts have artifacts, not just claims
- **Method-appropriate** — Verification approach matches what's being verified
- **Disconfirmation-aware** — Actively looked for failure, not just success
- **Gap-honest** — What wasn't verified is stated, not hidden
- **Proportionate** — Effort matches stakes

## Contract (Normative Requirements)

The keywords **MUST**, **SHOULD**, and **MAY** are used as normative requirements.

### MUST

- **Run the Entry Gate** and record its outputs before starting verification work.
- **Complete all four stages** (DEFINE → DESIGN → EXECUTE → EVALUATE) for the chosen stakes level.
- **Produce evidence artifacts** for each verification step — "I verified it" without evidence is not verification.
- **Use the transition tree** to determine whether to iterate, exit, or route to another framework.
- **Assign verdicts with confidence levels** that don't exceed evidence strength.
- **Mark unverified items explicitly** — gaps are "not verified," not silently passed.
- **Produce an output** that includes, at minimum, the sections in the **Verification Report Template**.

### SHOULD

- Pre-register expected results before executing verification steps.
- Use multiple independent methods for P0 criteria at rigorous+ levels. (Methods are independent if they don't share failure modes — e.g., automated test + manual inspection, or two people verifying separately.)
- Maintain an execution log showing actual steps taken and results observed.
- Timestamp verdicts and note conditions that would require re-verification. (At rigorous+ levels, timestamps are required — not merely expected — because omitting them disables the "stale verification" countermeasure.)

### MAY

- Add domain-specific criteria, methods, or environment requirements.
- Override iteration caps or evidence requirements — but any override MUST be declared in the Entry Gate.
- Collapse DEFINE and DESIGN at adequate level for simple verifications — but MUST document what was combined.

**Example of collapsed DEFINE+DESIGN:**
> "Criterion: `add(2,3)` returns `5`. Oracle: Execution. Method: Run `add(2,3)`, compare output to `5`."
>
> This combines criterion definition (what), oracle type (evidence category), and method (how) in a single statement. Acceptable at adequate level for trivial verifications.

## Principle

Verification is about **confirming outputs are correct**, not about understanding (thoroughness) or choosing (decision-making). The key question is: "Does this output achieve what it was supposed to achieve?"

Verification is the gatekeeper. Nothing is "done" until verified. Verification failures don't mean "try harder" — they mean "route back to the right phase."

## Relationship to Other Frameworks

### When to Use Which

| Main uncertainty | Use |
|-----------------|-----|
| What's true? What exists? What are the options? | Thoroughness |
| Which option should we choose? | Decision-making |
| Does this output actually work? | **Verification** |

### Handoff TO Verification

| From | Trigger | What verification receives |
|------|---------|---------------------------|
| Any work | Output produced that needs checking | The output/claim/artifact to verify |
| Thoroughness | Findings complete, need confirmation | Findings with Evidence/Confidence ratings to verify |
| Decision-making | Decision made, need to verify it worked | Chosen option + expected outcomes |
| Implementation | Code/doc/artifact complete | The deliverable + acceptance criteria |

### Handoff FROM Verification

| Verification result | Handoff to | What gets passed |
|--------------------|------------|------------------|
| Verified (pass) | Done — or next phase | Verification report as evidence |
| Not verified — wrong output | Back to implementation | What failed + evidence |
| Not verified — unclear criteria | Thoroughness | Need to understand what "correct" means |
| Not verified — wrong approach | Decision-making | Need to choose different approach |
| Partially verified | Depends on gaps | Analyze each gap: blocking (→ route to fix) vs. acceptable (→ document and proceed) |
| New requirement discovered | Thoroughness / Decision-making / Escalate | In-scope → Thoroughness or Decision-making; Out-of-scope → Escalate |

### The Pipeline (Logical Flow)

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐     ┌──────────────┐
│ Thoroughness│ ──► │ Decision-making  │ ──► │Implementation │ ──► │ Verification │
│ (understand)│     │ (choose)         │     │ (build)       │     │ (confirm)    │
└─────────────┘     └──────────────────┘     └───────────────┘     └──────────────┘
       ▲                    ▲                        ▲                    │
       │                    │                        │                    │
       └────────────────────┴────────────────────────┴────────────────────┘
                              (verification failures route back)
```

**Note:** This shows logical flow, not temporal sequence. Verification can be invoked at any output point; each output has its own verification cycle.

## Entry Gate

Before starting verification, establish and record:

| Aspect | Question | Output |
|--------|----------|--------|
| **Verification target** | What output/claim/work needs verification? | Specific, bounded target |
| **Trigger** | What prompted this verification? | Context: completion / change / doubt / routine |
| **Stakes level** | How thorough does this need to be? | adequate / rigorous / exhaustive |
| **Success definition** | What does "verified" mean? | Initial acceptance criteria |
| **Oracle types** | How will we know if criteria are met? | Oracle type per criterion |
| **Environment scope** | Where must this work? | Environment list |
| **Constraints** | What limits our verification? | Time, access, tools |
| **Assumptions** | What are we taking for granted? | Assumption list |

### Stakes Calibration Rubric

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High (need action) | Moderate | Low / no constraint |

**Rule of thumb:** If any two factors land in a higher column, choose that higher verification level unless you can document in the Entry Gate rationale: (1) which specific factors override the higher-level signal, and (2) what compensating controls or accepted risks apply.

**Gate check:** Cannot proceed to DEFINE until:
- Target is specific and bounded (not "verify everything works")
- Stakes level chosen
- At least one acceptance criterion identified
- At least one oracle type named

## The Verification Loop

```
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
 DEFINE ──► DESIGN ──► EXECUTE ──► EVALUATE
                                          │
                                    (verdict?)
                                          │
                                    EXIT / ITERATE / ROUTE
```

**Terminology:** An **iteration** is one complete cycle through DEFINE→DESIGN→EXECUTE→EVALUATE, or one ITERATE cycle (re-execute after correcting an execution error). Breaking back to DESIGN or DEFINE starts a new iteration. Iteration caps (see Stakes Calibration) count these cycles. (Note: "pass" in this document refers only to verdicts — pass/fail/not verified — not to iteration cycles.)

## Stage 1: DEFINE — What Does "Correct" Mean?

Establish acceptance criteria and how you'll know if they're met.

| Output | Description |
|--------|-------------|
| **Acceptance criteria** | Specific, testable conditions for each aspect of correctness |
| **Priority per criterion** | P0 (must verify) / P1 (should verify) / P2 (nice to verify) |
| **Oracle type per criterion** | How we'll determine pass/fail (test, inspection, comparison, etc.) |

### Acceptance Criteria: Examples

Good criteria are specific, testable, and scoped. Bad criteria are vague or rely on "looks right".

| Bad | Better |
|-----|--------|
| "It works correctly" | "For input X, output equals Y (or matches pattern Z)" |
| "The report looks good" | "Report includes sections A/B/C, and each claim links to evidence or is marked 'not verified'" |
| "No errors" | "Invalid inputs produce error E with message M; no partial writes occur" |

### Oracle Types

| Type | Description | Example |
|------|-------------|---------|
| **Automated test** | Executable check with deterministic result | Unit test, integration test |
| **Manual test** | Human-executed steps with expected result | Click through UI, run repro steps |
| **Inspection** | Careful examination of artifact | Code review, document review |
| **Comparison** | Diff against known-good reference | Golden file, before/after |
| **Cross-reference** | Check against authoritative source | Verify against spec, original doc |
| **Demonstration** | Show working to observer | Demo to stakeholder |
| **Execution** | Run and observe behavior | Run script, observe output |

**Oracle vs. Method — Important distinction:**

| Concept | Question answered | Example |
|---------|-------------------|---------|
| **Oracle type** | "What counts as valid evidence?" | "Execution output is valid evidence for this criterion" |
| **Method** | "How will we produce that evidence?" | "Run the script and capture stdout" |

The same term may appear in both tables (e.g., "Execution"). Oracle type names the *evidence category*; Method names the *activity*. In DEFINE, choose the oracle type. In DESIGN, choose the method that produces that type of evidence.

**Failure mode prevented:** Scope confusion — verifying the wrong thing or using the wrong success definition.

## Stage 2: DESIGN — How Will We Test It?

Create a verification plan with specific methods for each criterion.

| Output | Description |
|--------|-------------|
| **Verification plan** | Specific method + steps for each criterion |
| **Expected results** | What we expect to see if the criterion passes (pre-registration) |
| **Environment specification** | Where verification will be performed |

### Verification Method Menu

Choose appropriate methods for each criterion:

| Method | Description | Best for |
|--------|-------------|----------|
| **Execution** | Run it and observe results | Code, scripts, processes |
| **Reproduction** | Independently recreate the result | Analysis, calculations |
| **Cross-reference** | Check against authoritative source | Claims, facts, citations |
| **Inspection** | Carefully examine the artifact | Code, documents, designs |
| **Comparison** | Diff against known-good or expected | Outputs, states, versions |
| **Demonstration** | Show it working to a skeptic | Features, capabilities, fixes |
| **Stress test** | Push beyond normal conditions | Systems, assumptions, limits |
| **Negative test** | Verify it fails when it should | Error handling, validation |
| **Independence** | Different person/method confirms | High-stakes claims |
| **Time-shift** | Re-verify after delay to catch transient successes | Caching effects, rate limits, token expiry, time-dependent logic. *Example: API call succeeds now because token is cached; re-run after cache TTL expires to verify the refresh flow works.* |

**Method requirements by level:**
- **Adequate:** At least 1 method per criterion
- **Rigorous:** Primary method + 1 backup for critical criteria
- **Exhaustive:** 2+ independent methods; triangulation required for P0

**Failure mode prevented:** Shallow validation — "run the tests" without specifics; method doesn't actually test the criterion.

## Stage 3: EXECUTE — Actually Do the Verification

Run the verification plan and collect evidence.

| Output | Description |
|--------|-------------|
| **Evidence artifacts** | Logs, screenshots, command output, quotes — not just "I checked" |
| **Step-by-step trace** | What was done, in what order, with what results |
| **Comparison to expected** | Actual results vs. pre-registered expectations |

### Evidence Requirements

Evidence is **non-negotiable**. Every verification step must produce artifacts.

**Minimum artifact metadata (recommended):**
- **When:** Timestamp or run ID
- **Where:** Environment (machine/container, relevant versions)
- **What:** Exact command/steps executed
- **Result:** The observed output (or excerpt) used to assign the verdict

| Stakes Level | Evidence Required |
|--------------|-------------------|
| **Adequate** | Artifacts for each criterion (logs, output, screenshots) |
| **Rigorous** | Artifacts + explicit comparison to expected results |
| **Exhaustive** | Artifacts + comparison + independent confirmation |

### Pre-registration

Before executing each verification step:
1. State what you expect to see if it passes
2. State what you expect to see if it fails
3. Run the verification
4. Compare actual to expected

This prevents "seeing what you expect" — a common source of false positives.

**Failure modes prevented:**
- Completion theater — claiming verification without evidence
- Selective execution — skipping hard checks
- Misread results — seeing green when it was actually red

## Stage 4: EVALUATE — Did It Pass?

Interpret evidence and assign verdicts.

| Output | Description |
|--------|-------------|
| **Verdict per criterion** | pass / fail / not verified |
| **Confidence per verdict** | high / medium / low |
| **Linked evidence** | Artifact supporting each verdict |
| **Gaps list** | What wasn't verified and why |

### Verdict Categories

| Verdict | Meaning | Requirements |
|---------|---------|--------------|
| **Pass** | Criterion met | Evidence shows expected result; no contradicting evidence |
| **Fail** | Criterion not met | Evidence shows unexpected result or missing expected behavior |
| **Not verified** | Could not determine | Step skipped, tool failed, ambiguous result, or not tested |

**Critical rule:** "Not verified" is not "pass." If a criterion wasn't actually tested, it's not verified.

### Confidence Levels

| Level | Meaning | Evidence Required |
|-------|---------|-------------------|
| **High** | Strong evidence, no contradictions | Multiple confirmations, OR single authoritative source (official output, cryptographic proof, direct observation with full trace) |
| **Medium** | Reasonable evidence, some uncertainty | Single verification method with clear result, no contradictions |
| **Low** | Weak evidence, significant uncertainty | Partial check, ambiguous results, or inference from indirect signals |

**Rule:** Confidence cannot exceed evidence strength. Weak evidence caps confidence at Low.

### Disconfirmation Check

Before claiming any criterion passes, ask:
1. What would failure look like?
2. Did we see any of that?
3. Did we specifically look for failure evidence?

| Stakes Level | Disconfirmation Required |
|--------------|-------------------------|
| **Adequate** | Quick "what would failure look like?" — documented in one sentence |
| **Rigorous** | Active search for failure evidence — document what was searched and findings (positive or negative) |
| **Exhaustive** | Assume failure, prove otherwise — document the "failure hypothesis" and the evidence that refutes it |

**Example (rigorous disconfirmation for "API returns correct data"):**
- *What would failure look like?* Wrong field values, missing fields, wrong status code, timeout
- *How we looked for it:* Checked all fields against schema, tested with invalid auth (should fail), tested with malformed input (should return 400)
- *What we found:* No failure evidence; all checks passed

**Failure modes prevented:**
- False positive — claiming pass with weak evidence
- Unmarked gaps — not disclosing what wasn't tested
- Ignored disconfirmation — overlooking failure evidence

## Transition Tree

After EVALUATE, determine next action:

```
EVALUATE complete. Did all criteria pass?
├─ YES (all pass) → EXIT (verified)
│
└─ NO (some fail or not verified) → Why?
         │
         ├─ Execution error (typo, skipped step, tool glitch)
         │   └─ ITERATE (re-execute)
         │
         ├─ Wrong verification method (DESIGN problem)
         │   └─ BREAK to DESIGN
         │
         ├─ Wrong acceptance criteria (DEFINE problem)
         │   └─ BREAK to DEFINE
         │
         ├─ Underlying work is wrong (output doesn't work)
         │   └─ EXIT (not verified) — route back to implementation
         │
         ├─ New requirement discovered
         │   └─ Route based on gap type:
         │       • "What is X?" → Thoroughness (understand first)
         │       • "Should we do X or Y?" → Decision-making (choose approach)
         │       • "This is out of scope" → Escalate (user decides scope)
         │
         └─ Stuck after iteration cap
             └─ ESCALATE to user (see Escalation below)
```

### Escalation

**When to escalate:** Verification is stuck after reaching the iteration cap, or a decision exceeds the verifier's authority.

**What to provide:**
1. Current state: What was verified, what failed, what remains unknown
2. Blocking issue: Why verification cannot proceed
3. Options considered: What was tried, why it didn't work
4. Decision needed: Specific question the user must answer (e.g., "Accept partial verification?" or "Provide access to X?")

**Escalation is not failure** — it's honest acknowledgment that verification requires input beyond the verifier's scope.

## Stakes Calibration

What changes at each level:

| Dimension | Adequate | Rigorous | Exhaustive |
|-----------|----------|----------|------------|
| **Criteria scope** | Critical path only (P0 criteria that block the primary use case) | All stated criteria | All criteria + edge cases + failure modes |
| **Method depth** | Single method per criterion | Primary + backup for critical | Multiple independent methods; triangulation (≥3 sources converging) |
| **Evidence bar** | Artifacts required | Artifacts + explicit comparison | Artifacts + comparison + independent confirmation |
| **Disconfirmation** | Quick "what would failure look like?" | Active search for failure evidence | Assume failure, prove otherwise |
| **Iteration cap** | 1-2 iterations | 2-3 iterations | 3-5 iterations |
| **Environment** | Primary environment | Primary + one alternate | All relevant environments |

**Important:** Each level is a package. Don't mix levels across dimensions — if you need more depth on one dimension, upgrade the whole level.

**Exception (allowed only if declared in the Entry Gate):** You may **upgrade** a single dimension (e.g., add an extra disconfirmation check or use multiple methods where the level only requires one) if you explicitly record the deviation and rationale. Upgrading does not change the claimed level — a verification at "adequate" with one upgraded dimension is still "adequate," not "rigorous-lite." Downgrading individual dimensions is not permitted — that would undermine the level's guarantees. If you need less rigor, choose a lower level entirely.

## Failure Modes

Each failure mode maps to a countermeasure. If a failure mode appears, the corresponding countermeasure was skipped or done poorly.

### DEFINE Failures

| Failure Mode | Signal | Countermeasure |
|--------------|--------|----------------|
| Vague criteria | "It should work correctly" | Require specific, testable conditions |
| Missing criteria | Only checked happy path | Require edge cases, error conditions |
| Wrong oracle type | "I'll know it when I see it" | Require named oracle type per criterion |

### DESIGN Failures

| Failure Mode | Signal | Countermeasure |
|--------------|--------|----------------|
| Shallow method | "Run the tests" without specifics | Require verification plan with exact steps |
| Method-criteria mismatch | Verification doesn't test the criterion | Map each criterion to its method explicitly |

### EXECUTE Failures

| Failure Mode | Signal | Countermeasure |
|--------------|--------|----------------|
| Completion theater | "I verified it" without evidence | Evidence artifacts required |
| Selective execution | Skipped hard checks | Pre-registered plan; all steps traced |
| Misread results | Saw green, but wrong test | Pre-registered expectations; explicit comparison |
| Premature abandonment | "Ran out of time" | Iteration cap + minimum depth by stakes |
| Environment mismatch | Verified in wrong context | Require environment spec in DESIGN |

### EVALUATE Failures

| Failure Mode | Signal | Countermeasure |
|--------------|--------|----------------|
| False positive | "Pass" with weak/ambiguous evidence | Evidence-verdict alignment rule |
| Unmarked gaps | Didn't test X, didn't say so | Explicit "not verified" category |
| Ignored disconfirmation | Failure evidence present but overlooked | Disconfirmation check before claiming pass |
| Stale verification | Conditions changed since verification | Timestamp verdicts; re-verify after changes |

## Exit Gate

Cannot claim **Fully verified** until all P0 criteria have verdict = pass AND were actually tested (not "not verified").

| Criterion | Check |
|-----------|-------|
| **All criteria evaluated** | Every acceptance criterion (P0, P1, P2) has a verdict (pass / fail / not verified) |
| **Evidence documented** | Each verdict has linked artifacts |
| **Confidence appropriate** | Verdict confidence doesn't exceed evidence strength |
| **Gaps explicit** | Any "not verified" items have documented reasons |
| **Disconfirmation attempted** | Actively looked for failure evidence (scaled by stakes) |
| **Iteration threshold met** | Minimum passes for stakes level completed |
| **Verdict stable** | No new failure evidence in final pass |

### Handling "Not Verified" Items

| Priority | Exit allowed? |
|----------|---------------|
| P0 criterion not verified | NO — must verify or escalate |
| P1 criterion not verified | Only if documented and accepted risk |
| P2 criterion not verified | YES — document and proceed |

### Non-deterministic / Probabilistic Verification

Some targets are not deterministic: flaky tests, performance benchmarks, AI/model outputs, manual judgments, systems with eventual consistency, or time-dependent behavior. Standard single-execution verification is insufficient.

**When to apply:**
- Output varies across runs with identical inputs
- System has known flakiness or race conditions
- Verification involves human judgment (different reviewers may differ)
- Performance or latency is being verified (inherent variance)
- AI/LLM outputs are being evaluated

**Approach:**
| Aspect | Guidance |
|--------|----------|
| **Sample size** | Minimum 3 runs for adequate; 5+ for rigorous; 10+ for exhaustive or high-variance systems. (Rationale: 3 runs can detect ~70% reproducible failures; 5+ approaches statistical utility; 10+ enables meaningful variance analysis.) |
| **Variance recording** | Record range, mean, and any outliers; note if variance exceeds acceptable threshold |
| **Confidence cap** | High variance or small samples cap confidence at **Low** regardless of mean result |
| **Pass threshold** | Define upfront: "passes if ≥N of M runs succeed" (e.g., 9/10) or "mean latency < Xms with p95 < Yms" |
| **Flaky failures** | A single failure in N runs is still a failure signal — investigate before dismissing as flakiness |

**For AI/model outputs:** Use rubric-based evaluation with explicit criteria. Multiple independent evaluations (human or automated) increase confidence. Document disagreements.

**Example (verifying a flaky integration test):**
- *Pass threshold:* 9/10 runs succeed
- *Runs:* 10
- *Results:* 8 pass, 2 fail (failures on runs 3 and 7, both timeout-related)
- *Verdict:* Fail (below threshold)
- *Action:* Investigate timeout root cause before retesting

## Verification Report Template

Use this template (or an equivalent structure) for any verification output.

```markdown
# [Verification Target] — Verification Report

## Context
- Protocol: verification.framework@1.0.0
- Target: [What was verified]
- Trigger: [Why verification was needed]
- Stakes level: adequate / rigorous / exhaustive
- Date: [When verified]

## Entry Gate
### Verification Target
[Specific, bounded description of what's being verified]

### Acceptance Criteria
| ID | Criterion | Priority | Oracle Type |
|----|-----------|----------|-------------|
| C1 | | P0/P1/P2 | |
| C2 | | | |

### Environment Scope
- Primary:
- Alternate (if rigorous+):

### Constraints
- Time:
- Access:
- Tools:

### Assumptions
- A1:
- A2:

## Verification Plan (DESIGN output)
| Criterion | Method | Specific Steps | Expected Result |
|-----------|--------|----------------|-----------------|
| C1 | | | |
| C2 | | | |

## Execution Log (EXECUTE output)
### C1: [Criterion name]
- Method:
- Steps taken:
- Actual result:
- Evidence: [link/artifact]

### C2: [Criterion name]
...

## Verdicts (EVALUATE output)
| Criterion | Verdict | Confidence | Evidence | Notes |
|-----------|---------|------------|----------|-------|
| C1 | pass/fail/not verified | high/med/low | [link] | |
| C2 | | | | |

### Disconfirmation Attempts
- What would failure look like:
- How we looked for it:
- What we found:

### Gaps
| Criterion | Why not verified | Risk accepted? | Next action |
|-----------|------------------|----------------|-------------|
| | | | |

## Summary
- **Overall verdict:** Verified / Partially verified / Not verified
- **Confidence:** High / Medium / Low
- **Open items:** [Any unresolved issues]
- **Re-verification trigger:** [What would require re-verification]

## Exit Gate
- [ ] All criteria evaluated
- [ ] Evidence documented
- [ ] Confidence ≤ evidence strength
- [ ] Gaps explicit
- [ ] Disconfirmation attempted
- [ ] Minimum passes completed
- [ ] Verdict stable
```

## Avoiding Verification Theater

Verification theater is going through the motions without genuine testing. Signs include:

| Signal | Reality |
|--------|---------|
| "Tests pass" without output shown | May not have run tests |
| "I verified it" without artifacts | No verification occurred |
| All criteria pass, no gaps, no disconfirmation attempts | Suspiciously perfect (genuine thorough verification almost always finds *something* worth noting) |
| No disconfirmation attempts | Confirmation bias likely |
| Vague criteria, confident verdict | Can't fail what isn't defined |

**Countermeasures:**
- Evidence is mandatory, not optional
- Pre-register expectations before executing
- Disconfirmation scales with stakes
- "Not verified" is a valid (and honest) verdict
- Gaps must be explicit, not hidden

## Quick Reference

### Minimum Viable Verification (Adequate)

1. **DEFINE:** List critical acceptance criteria with oracle types
2. **DESIGN:** One verification method per criterion with expected result
3. **EXECUTE:** Run each check, capture evidence artifact
4. **EVALUATE:** Verdict per criterion, quick disconfirmation, list gaps

### Full Verification (Rigorous/Exhaustive)

1. **DEFINE:** All criteria including edge cases; P0/P1/P2 priorities
2. **DESIGN:** Primary + backup methods; environment spec; pre-registered expectations
3. **EXECUTE:** All methods traced; evidence for each; multiple environments
4. **EVALUATE:** Confidence-rated verdicts; active/aggressive disconfirmation; full gap analysis

---
name: using-frameworks
description: Use when starting rigorous work that requires methodology — thoroughness analysis, structured decision-making, or output verification. Use when user says "be thorough", "decide between", "verify this works", or invokes /thoroughness, /decide, /verify.
argument-hint: [thoroughness|decision|verification]
---

# Using Frameworks

Execute methodology frameworks with visible structure and verification.

**Protocols:**
- `thoroughness.framework@1.0.0` → [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md)
- `decision-making.framework@1.0.0` → [references/framework-for-decision-making.md](references/framework-for-decision-making.md)
- `verification.framework@1.0.0` → [references/framework-for-verification.md](references/framework-for-verification.md)

**Core promise:** Rigorous execution with auditable trail — Entry Gate, visible stage markers, checklist verification, Exit Gate.

**Non-goals:**
- Replacing the compact rules file (that tells you *when* to use which framework)
- Light-touch analysis (if you invoked this, you want the full framework)
- Delegation to other skills (this implements the frameworks directly)

## Process

### 1. Determine Framework

Based on `$ARGUMENTS`:

| Argument | Framework | Reference |
|----------|-----------|-----------|
| `thoroughness` | Thoroughness | [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md) |
| `decision` | Decision-Making | [references/framework-for-decision-making.md](references/framework-for-decision-making.md) |
| `verification` | Verification | [references/framework-for-verification.md](references/framework-for-verification.md) |

**YOU MUST read the referenced framework file before proceeding.** No exceptions. The framework contains the full protocol — this skill provides the execution wrapper, not the methodology. Do not rely on memory or summaries. Read the actual file.

### 2. Entry Gate (Interactive)

Work through the Entry Gate with the user.

**YOU MUST consult the framework for the complete Entry Gate.** The items below are essentials only — the framework specifies additional requirements by stakes level.

**Output visible marker:**
```
═══ ENTRY GATE: [Framework Name] ═══
```

**Thoroughness (essentials):**
- [ ] Assumptions surfaced
- [ ] Stakes level chosen (adequate/rigorous/exhaustive)
- [ ] Stopping criteria template selected
- [ ] Initial dimensions identified with P0/P1/P2 priorities

**Decision-Making (essentials):**
- [ ] Decision statement framed as clear question
- [ ] Stakes level chosen
- [ ] Iteration cap set
- [ ] Initial constraints identified

**Verification (essentials):**
- [ ] Target specific and bounded
- [ ] Stakes level chosen
- [ ] Acceptance criteria identified
- [ ] Oracle type named for each criterion

**YOU MUST present the completed Entry Gate to the user and receive confirmation before continuing.** Do not proceed on assumption of approval.

### 3. Execute Stages

**YOU MUST follow the framework's stages as written.** The framework specifies required activities, depth, and evidence levels for each stakes level. This skill does not override or abbreviate the framework.

**Output a visible marker at each stage transition:**

**Thoroughness:**
```
─── DISCOVER: Expanding dimensions ───
─── EXPLORE: Covering each dimension ───
─── VERIFY: Checking findings ───
─── REFINE: Assessing convergence (Yield: X%) ───
```

**Decision-Making:**
```
─── OUTER LOOP: Framing the decision ───
─── INNER LOOP (Pass N): Evaluating options ───
─── TRANSITION: [iterate/exit/break/escalate] ───
```

**Verification:**
```
─── DEFINE: Establishing acceptance criteria ───
─── DESIGN: Creating verification plan ───
─── EXECUTE: Running verification ───
─── EVALUATE: Assigning verdicts ───
```

**YOU MUST output the stage marker before beginning each stage.** Skipping markers is not permitted — they exist for auditability.

### 4. Exit Gate (Checklist Verification)

**YOU MUST verify all Exit Gate criteria from the framework before claiming completion.** The items below are essentials — consult the framework for the complete gate.

**Output visible marker:**
```
═══ EXIT GATE: [Framework Name] ═══
```

**Thoroughness (essentials):**
- [ ] Coverage complete — no `[ ]` or `[?]` remaining
- [ ] Yield% below threshold for level
- [ ] Disconfirmation attempted for P0 dimensions
- [ ] Stopping criteria satisfied

**Decision-Making (essentials):**
- [ ] Frontrunner stable for required passes
- [ ] Trade-offs explicitly documented
- [ ] Pressure-testing completed
- [ ] Iteration log complete

**Verification (essentials):**
- [ ] All P0 criteria have verdict = pass (actually tested)
- [ ] Evidence artifacts exist for each verdict
- [ ] Confidence ≤ evidence strength
- [ ] Disconfirmation attempted

**YOU MUST output each checklist item with its status.** Do not summarize as "all checks passed" — show each check explicitly.

**YOU MUST return to the appropriate stage if any Exit Gate item fails.** Do not proceed with gaps.

### 5. Produce Output

| Framework | Output | Location |
|-----------|--------|----------|
| Thoroughness | Thoroughness Report | Present in chat; optionally save to `docs/audits/` |
| Decision-Making | Decision Record | Save to `docs/decisions/YYYY-MM-DD-<slug>.md` |
| Verification | Verification Report | Present in chat; optionally save to `docs/audits/` |

**YOU MUST use the output template from the framework.** Do not invent a format.

Present concise summary (5-10 lines) in chat with link to full output if saved.

## Decision Points

**User seems impatient or asks to abbreviate:**
- Acknowledge the pressure
- **Do not abbreviate the framework.** If they invoked the skill, they want rigor
- Compress output presentation, not process: "I'll keep summaries brief, but I must complete the framework stages"

**Entry Gate reveals task doesn't warrant full framework:**
- Trust user judgment — they invoked the skill
- Run at "adequate" stakes level if appropriate, but run the full process
- Do not offer to skip the framework

**Mid-execution: new information changes the frame:**
- For Thoroughness: new dimensions discovered → loop back to DISCOVER
- For Decision-Making: frame changed → break to outer loop
- For Verification: criteria changed → break to DEFINE
- **Output the stage marker again when re-entering a stage**

**Exit Gate fails:**
- Identify which criterion failed
- Return to the appropriate stage (not the beginning)
- **Do not negotiate or accept partial completion**

**Framework specifies escalation:**
- Thoroughness: stuck after iteration cap with high yield
- Decision-Making: no convergence after cap, or stakeholder conflict
- Verification: critical info unfillable, or criteria ambiguous
- **Present current state to user and ask for direction.** Do not decide unilaterally.

**User asks to stop mid-process:**
- Acknowledge and stop
- Summarize current state: what's complete, what's not, where to resume
- Do not claim partial completion as success

## Anti-Patterns

| Pattern | Why It Fails | Fix |
|---------|--------------|-----|
| Reading framework from memory instead of file | Frameworks evolve; memory may be outdated or incomplete | **Read the actual file every time** |
| Skipping Entry Gate because "the task is clear" | Entry Gate calibrates stakes and surfaces assumptions — skipping it means uncalibrated execution | Complete Entry Gate regardless of perceived clarity |
| Invisible stage transitions | No audit trail; easy to skip stages without noticing | **Output visible markers at every transition** |
| "All checks passed" without showing checks | Completion theater; hides what was actually verified | Show each checklist item with explicit status |
| Abbreviating at "adequate" level beyond framework spec | Adequate is still rigorous — it's the minimum, not a shortcut | Follow framework requirements for adequate level exactly |
| Accepting Exit Gate failure to "move faster" | Failures surface later at higher cost | Return to appropriate stage; do not proceed with gaps |
| Summarizing framework instead of executing it | Summary ≠ execution; the value is in the process | Execute stages as written, with evidence and markers |
| Treating stage markers as optional formatting | Markers are compliance mechanism, not decoration | Markers are mandatory — never skip them |

## Troubleshooting

**Symptom:** Framework file not found
**Cause:** Skill references not set up correctly
**Fix:** Verify `references/framework-for-*.md` files exist in skill directory. If missing, copy from `docs/frameworks/`.

**Symptom:** Entry Gate feels repetitive or slow
**Cause:** Rigorous process requires explicit calibration
**Fix:** This is expected. Entry Gate prevents downstream errors. Do not skip — compress presentation if needed, not content.

**Symptom:** Yield% not decreasing (Thoroughness)
**Cause:** Still discovering new dimensions or revising findings
**Fix:** This means the framework is working. Continue iterating until Yield% drops below threshold.

**Symptom:** Frontrunner keeps changing (Decision-Making)
**Cause:** Criteria unclear, options too close, or frame unstable
**Fix:** Check if criteria are well-defined. If options are genuinely close, treat as near-tie per framework guidance.

**Symptom:** Can't determine verdict (Verification)
**Cause:** Acceptance criteria not specific enough, or oracle type mismatched
**Fix:** Break to DEFINE stage. Criteria must be testable with named oracle type.

**Symptom:** User disputes stakes level
**Cause:** Different assessment of reversibility, blast radius, or cost
**Fix:** User's assessment wins. Document their rationale in Entry Gate and proceed at their chosen level.

**Symptom:** Framework execution taking too long
**Cause:** Either stakes level is too high, or task is genuinely complex
**Fix:** Do not abbreviate. If stakes were miscalibrated, adjust at next pass boundary (document the recalibration). Otherwise, the time reflects actual complexity.

## Verification

After completing a framework execution, verify:

- [ ] Framework file was read (not recalled from memory)
- [ ] Entry Gate marker appears in output
- [ ] All Entry Gate essentials have explicit answers
- [ ] User confirmed Entry Gate before stages began
- [ ] Stage markers appear for each stage executed
- [ ] Exit Gate marker appears in output
- [ ] Each Exit Gate item shown with explicit status (not summarized)
- [ ] Output artifact produced using framework template
- [ ] Summary presented in chat

**Quick self-test:** Could an auditor trace the execution by reading the visible markers and checklists? If not, markers or checks are missing.

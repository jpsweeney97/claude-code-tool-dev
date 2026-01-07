# Workflow Details

## Cost Estimation

Running parallel Opus agents is expensive. Plan accordingly:

| Mode            | Agents        | Typical Tokens          | Relative Cost |
| --------------- | ------------- | ----------------------- | ------------- |
| `--quick`       | 2             | ~8K input + ~4K output  | 1x            |
| Default         | 3             | ~12K input + ~6K output | 1.5x          |
| `--claude-code` | 3             | ~12K input + ~6K output | 1.5x          |
| `--design`      | 3 + synthesis | ~15K input + ~8K output | 2x            |
| Custom 4-lens   | 4             | ~16K input + ~8K output | 2x            |

**When to use full audit vs quick:**
- **Full (Default/Design):** High-stakes artifacts, before shipping, when time allows
- **Quick:** Iterative drafts, sanity checks, when you'll re-audit later

## Incremental Mode

Re-run individual lenses or recover from partial failures.

### Single Lens Execution

```
/three-lens-audit <file> --lens adversarial
/three-lens-audit <file> --lens pragmatic
/three-lens-audit <file> --lens cost-benefit
```

Use when:
- One lens returned malformed output
- You want deeper analysis on a specific dimension
- Re-auditing after changes (run same lens to compare)

### Recovery from Partial Failure

| Scenario                  | Action                                               |
| ------------------------- | ---------------------------------------------------- |
| 1 agent failed            | Re-run that lens only; synthesize with 3 outputs     |
| 2 agents failed           | Consider restarting full audit (may be target issue) |
| Agent returned incomplete | Re-run with `--lens X`; remind agent of format       |
| Agent went off-track      | Re-run with clearer scope in prompt                  |

### Synthesizing Partial Results

| Available     | Synthesis Approach                                            |
| ------------- | ------------------------------------------------------------- |
| 2 of 3 lenses | Note missing perspective in report; convergence = 2/2 match   |
| 1 lens only   | Single-perspective review only; no convergence analysis       |
| 3 of 4 lenses | Full synthesis minus Arbiter; main thread does prioritization |

**Quality signal:** If 2 lenses converge without the 3rd, it's still a meaningful finding—but note the gap.

## Execution Workflow

### Recommended Steps

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PREPARE                                                      │
│     python scripts/run_audit.py prepare <target.md>             │
│     → Cost estimate + ready-to-use Task tool template           │
├─────────────────────────────────────────────────────────────────┤
│  2. EXECUTE                                                      │
│     Copy/paste the Task tool calls (3 in single message)        │
│     → 3 parallel Opus agents analyze target                     │
├─────────────────────────────────────────────────────────────────┤
│  3. FINALIZE                                                     │
│     python scripts/run_audit.py finalize *.md --target "Name"   │
│     → Validates outputs + generates synthesis                   │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: Prepare

Generate prompts and get cost estimate before running expensive Opus agents:

```bash
python scripts/run_audit.py prepare path/to/target.md
python scripts/run_audit.py prepare target.md --preset design  # for design audit
```

This outputs:
- Token/cost estimate (so you can decide if it's worth it)
- Ready-to-use Task tool invocation template with prompts filled in

### Step 2: Execute

Launch all agents in a **single message** with multiple Task tool calls:

```
Tool: Task (x3 in single message)
  subagent_type: general-purpose
  model: opus
  prompt: [Prompt from prepare output]
```

**Critical:** All three agents must be launched in a SINGLE message for true parallelism. Save each agent's output to a file (e.g., `adversarial.md`, `pragmatic.md`, `cost-benefit.md`).

### Step 3: Finalize

Validate and synthesize the results:

```bash
python scripts/run_audit.py finalize adversarial.md pragmatic.md cost-benefit.md --target "My Document"
```

This:
1. Validates each lens output (catches malformed responses)
2. Generates synthesis if ≥2 outputs pass validation
3. Reports convergent findings and prioritized recommendations

### Manual Execution

If you prefer not to use the scripts:
- Copy prompts directly from `agent-prompts.md`
- Run synthesis manually using the template in `agent-prompts.md#synthesis-template`

But the scripts catch errors (malformed output, missing sections) that manual review might miss.

---

## Re-Audit Workflow

Verify fixes after making changes based on audit findings.

### When to Re-audit

| Situation                            | Strategy               | Why                              |
| ------------------------------------ | ---------------------- | -------------------------------- |
| Fixed Critical/Major findings        | Full re-audit          | Verify fixes; catch regressions  |
| Significant refactoring during fixes | Full re-audit          | Changes may introduce new issues |
| Fixed issues from one lens only      | Single-lens re-audit   | Targeted verification            |
| Minor wording/formatting tweaks      | Spot-check (no agents) | Low risk, not worth the cost     |
| Pre-ship final check                 | Full re-audit          | Complete confidence              |

### Re-audit Strategies

**Full Re-audit** (Recommended for significant changes)

Run the complete 3-lens audit again:

```bash
python scripts/run_audit.py prepare target.md
# Run all 3 agents, save outputs
python scripts/run_audit.py finalize *.md --target "Target v2"
```

Why full re-audit matters: A fix for one lens might create problems another lens would catch. Security fix → usability regression. Simplification → completeness gap.

**Single-Lens Re-audit** (For targeted verification)

Re-run only the lens that flagged the issues you fixed:

```
/three-lens-audit target.md --lens adversarial
```

Cheaper and faster, but won't catch cross-lens regressions.

**Spot-Check** (For trivial changes)

Review changes without running agents. Suitable for typos, formatting, minor clarifications where the fix is obviously correct.

### Comparing Before/After

1. **Save original synthesis** before making changes (e.g., `synthesis-v1.md`)
2. **Run re-audit** after fixes (produces `synthesis-v2.md`)
3. **Compare:**

| Question                    | Good Sign                        | Warning Sign              |
| --------------------------- | -------------------------------- | ------------------------- |
| Original findings resolved? | Specific issues no longer appear | Same issues reappear      |
| New findings emerged?       | None, or only Minor              | New Critical/Major issues |
| Convergent findings?        | Reduced or eliminated            | Same count or increased   |

### Exit Criteria

An artifact is ready to ship when:

- [ ] No Critical findings remaining
- [ ] No convergent findings (issues flagged by 2+ lenses)
- [ ] All Major findings either fixed or explicitly accepted as known risk
- [ ] Re-audit shows measurable improvement over original

**Acceptable risk:** Some Minor findings may remain if cost-to-fix exceeds benefit. Document these as known limitations rather than grinding to zero.

### Iteration Pattern

```
Audit v1 → Fix → Re-audit v2 → Fix → Re-audit v3 → Ship
                      │                    │
                      │                    └── New issues? Iterate
                      └── New issues? Iterate
```

**Diminishing returns:** If re-audit v3 finds only the same Minor issues as v2, you've reached diminishing returns. Ship it.

**Red flag:** If each re-audit finds _entirely different_ issues unrelated to your fixes, the artifact may need fundamental redesign, not incremental fixes. Consider stepping back to reassess the approach.

### Action Tracking Template

Copy this template after synthesis to track fixes:

```markdown
## Audit Action Plan: [Target Name] - [Date]

### Convergent Findings (Priority 1)

| Finding   | Severity       | Status              | Resolution |
| --------- | -------------- | ------------------- | ---------- |
| [finding] | Critical/Major | Open/Fixed/Deferred | [notes]    |

### Lens-Specific Findings

| Finding   | Lens                               | Status              | Resolution |
| --------- | ---------------------------------- | ------------------- | ---------- |
| [finding] | Adversarial/Pragmatic/Cost-Benefit | Open/Fixed/Deferred | [notes]    |

### Deferred Items

| Finding   | Reason         | Revisit By        |
| --------- | -------------- | ----------------- |
| [finding] | [why deferred] | [date or trigger] |
```

**Status values:**

- `Open` — Not yet addressed
- `Fixed` — Resolved, verified in re-audit
- `Deferred` — Intentionally postponed (document reason)
- `Won't Fix` — Accepted as known limitation

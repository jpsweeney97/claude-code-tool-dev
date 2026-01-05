---
name: three-lens-audit
description: Deploy 3+ parallel agents with competing philosophies to stress-test documents, frameworks, or designs
license: MIT
metadata:
  version: 1.13.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Multi-Lens Audit

Deploy parallel agents with distinct analytical perspectives to find issues single-perspective review would miss. Supports 3-lens (default), 4-lens (with arbiter), and custom lens configurations.

## Triggers

- `/three-lens-audit <file>` — Default 3 lenses
- `/three-lens-audit <file> --design` — Design audit (robustness + minimalist + capability)
- `audit <file> with [N] lenses`
- `run a 4-lens audit on <file>`
- `stress-test <document> from multiple perspectives`

## Quick Reference

### Default Lenses

| Lens             | Question                 | Finds                                      |
| ---------------- | ------------------------ | ------------------------------------------ |
| **Adversarial**  | How does this break?     | Contradictions, exploits, failure modes    |
| **Pragmatic**    | Does this actually help? | Friction, cognitive load, missing pieces   |
| **Cost/Benefit** | Is this worth it?        | ROI by element, optimization opportunities |

### Design Audit Lenses (`--design`)

| Lens           | Question           | Finds                                               |
| -------------- | ------------------ | --------------------------------------------------- |
| **Robustness** | What's missing?    | Gaps, edge cases, underspecification, failure modes |
| **Minimalist** | What can we cut?   | Overengineering, duplication, YAGNI, complexity     |
| **Capability** | What's realistic?  | Assumptions vs actual behavior, reliable vs risky   |
| **Arbiter**    | What matters most? | Convergent findings, prioritized recommendations    |

### Claude Code Feasibility Lenses (`--claude-code`)

| Lens               | Question               | Finds                                          |
| ------------------ | ---------------------- | ---------------------------------------------- |
| **Implementation** | Can this be built?     | Tool gaps, state assumptions, behavioral risks |
| **Adversarial**    | How does this break?   | Failure modes, edge cases, exploits            |
| **Cost/Benefit**   | Is this worth it?      | ROI, effort vs value, alternatives             |

## Why These Lenses?

The default trio creates **productive tension**:

| Lens             | Pushes Toward                       | Checks Against                                   |
| ---------------- | ----------------------------------- | ------------------------------------------------ |
| **Adversarial**  | Completeness — cover all edge cases | Over-simplification that creates vulnerabilities |
| **Pragmatic**    | Simplicity — reduce cognitive load  | Over-engineering that nobody can use             |
| **Cost/Benefit** | Efficiency — maximize ROI           | Both extremes — arbitrates the tradeoff          |

**Why tension matters:** A single perspective optimizes for one dimension. Multiple aligned perspectives create echo chambers. Deliberately opposed perspectives surface issues that consensus-seeking misses.

**When findings converge:** If Adversarial (wanting completeness) and Pragmatic (wanting simplicity) both flag the same issue, it's likely a real problem — not just one lens's bias.

**Design your own:** When creating custom lenses, ensure they push in different directions. Three lenses asking "is it complete?" from different angles won't find simplicity issues.

## Which Preset Should I Use?

```
What are you auditing?
│
├─► Process / Framework / Guidelines
│   └─► Use DEFAULT (Adversarial + Pragmatic + Cost/Benefit)
│
├─► Design Document / Specification / Architecture
│   └─► Use --design (Robustness + Minimalist + Capability)
│
├─► Claude Code Artifact (skill, hook, plugin, MCP, subagent, command)
│   └─► Use --claude-code (Implementation + Adversarial + Cost/Benefit)
│       The Implementation lens auto-detects artifact type and applies
│       the relevant checklist. See artifact types below.
│
├─► Need quick sanity check?
│   └─► Use --quick (Adversarial + Pragmatic only)
│
├─► Security-focused review?
│   └─► Use --lens adversarial (single lens)
│       Or define custom Security lenses (see references/)
│
└─► Domain-specific needs?
    └─► Define custom lenses using references/custom-lens-template.md
```

### Claude Code Artifact Types

The `--claude-code` preset's Implementation lens detects which artifact type you're auditing and applies artifact-specific checklists **verified against official Anthropic documentation**.

| Artifact Type | Key Indicators | Primary Failure Modes (from official docs) |
|---------------|----------------|-------------------------------------------|
| **Skill** | SKILL.md, description | Invalid frontmatter, name constraints, description too long |
| **Hook** | PreToolUse, exit codes | Exit code semantics (0=allow, 2=block), stderr routing |
| **Plugin** | plugin.json | Missing `name` field, components in wrong directory |
| **MCP Server** | .mcp.json | Wrong config location, deprecated SSE transport |
| **Command** | *.md in commands/ | Missing description, tool whitelist gaps |
| **Subagent** | name field, model | Using undocumented `subagent_type`, wrong model values |

See [Claude Code Capabilities Reference](references/claude-code-capabilities.md) for detailed checklists **sourced from official Anthropic documentation** (code.claude.com/docs).

| Target Type              | Recommended                           | Why                                          |
| ------------------------ | ------------------------------------- | -------------------------------------------- |
| CLAUDE.md / instructions | Default                               | Need to catch exploits AND usability issues  |
| Skill / plugin design    | `--claude-code`                       | Evaluate against actual Claude Code capabilities |
| Hook configuration       | `--claude-code`                       | Check exit codes, performance, security |
| MCP server design        | `--claude-code`                       | Verify tool definitions, startup time |
| Feature proposal         | `--claude-code`                       | Test behavioral assumptions against reality |
| API specification        | Custom (Consumer/Maintainer/Operator) | Domain expertise matters                     |
| Security policy          | Custom (Attacker/Defender/Auditor)    | Specialized threat modeling                  |
| Quick sanity check       | `--quick`                             | Time-boxed, skip ROI analysis                |

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

## How It Works

```
Target File
    │
    ▼
┌─────────────────────────────────────────────┐
│  Launch 3 Opus agents IN PARALLEL           │
│                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐   │
│  │Adversar-│ │Pragmatic│ │Cost/Benefit │   │
│  │   ial   │ │         │ │             │   │
│  └────┬────┘ └────┬────┘ └──────┬──────┘   │
│       │           │             │           │
│       ▼           ▼             ▼           │
│  Vulnerabil-  What works/   ROI table +    │
│  ities with   missing/      optimization   │
│  severity     friction      recommendations│
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  SYNTHESIS                                   │
│  • Convergent findings = highest priority   │
│  • Map lens-specific insights               │
│  • Prioritize by severity × effort          │
│  • Generate actionable recommendations      │
└─────────────────────────────────────────────┘
```

## Example Output

From an audit of `writing-for-claude` skill (~150 lines):

**Adversarial** found:
| Vulnerability | Evidence | Severity |
|--------------|----------|----------|
| Principles can justify contradictory edits | P2 vs P7 priority is subjective | Major |

**Pragmatic** found:

- ✓ Quick Reference table scannable in 30 seconds
- ✗ No before/after examples in SKILL.md itself
- Verdict: "Top-heavy — most value in tables, most tokens in prose"

**Cost/Benefit** found:
| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|
| references/principles.md | High (8K tokens) | Medium | Over-documented |

**Synthesis**: Both Pragmatic and Cost/Benefit flagged `principles.md` size → convergent finding → Priority 1 fix.

_Full example: [examples/audit-output-example.md](examples/audit-output-example.md)_

## Commands

| Command                                       | Action                         |
| --------------------------------------------- | ------------------------------ |
| `/three-lens-audit <file>`                    | Full three-lens audit          |
| `/three-lens-audit <file> --claude-code`      | Claude Code feasibility audit  |
| `/three-lens-audit <file> --design`           | Design audit                   |
| `/three-lens-audit <file> --lens adversarial` | Single lens only               |
| `/three-lens-audit <file> --quick`            | Two-lens (skip cost-benefit)   |

<details>
<summary><strong>Incremental Mode</strong> — Re-run individual lenses or recover from partial failures</summary>

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

If you have outputs from <3 lenses:

| Available     | Synthesis Approach                                            |
| ------------- | ------------------------------------------------------------- |
| 2 of 3 lenses | Note missing perspective in report; convergence = 2/2 match   |
| 1 lens only   | Single-perspective review only; no convergence analysis       |
| 3 of 4 lenses | Full synthesis minus Arbiter; main thread does prioritization |

**Quality signal:** If 2 lenses converge without the 3rd, it's still a meaningful finding—but note the gap.

</details>

## Execution

### Recommended Workflow

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

<details>
<summary><strong>Execution Details</strong> — Step-by-step prepare, execute, and finalize instructions</summary>

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

If you prefer not to use the scripts, you can:

- Copy prompts directly from `references/agent-prompts.md`
- Run synthesis manually using the template in `references/agent-prompts.md#synthesis-template`

But the scripts catch errors (malformed output, missing sections) that manual review might miss.

</details>

See [Re-Audit Workflow](references/workflow-details.md) for iteration strategies, exit criteria, and action tracking templates.

See [Scripts Reference](references/scripts-reference.md) for detailed documentation on `validate_output.py`, `synthesize.py`, and `run_audit.py`.

<details>
<summary><strong>Output Format</strong> — What each agent returns</summary>

### Per Agent

**Adversarial** returns:
| Vulnerability | Evidence | Attack Scenario | Severity |
|--------------|----------|-----------------|----------|

**Pragmatic** returns:

- What Works / What's Missing / Friction Points / Verdict

**Cost/Benefit** returns:
| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|

- High-ROI / Low-ROI / Recommendations

### Synthesis

After agents complete:

1. **Convergent findings** — All three flagged = critical priority
2. **Lens-specific insights** — Unique catches per perspective
3. **Recommendations** — Ordered by severity × ease of fix

</details>

## When to Use Each Lens Alone

| Situation                | Lens         |
| ------------------------ | ------------ |
| Security review          | Adversarial  |
| Onboarding documentation | Pragmatic    |
| Process optimization     | Cost/Benefit |
| High-stakes artifact     | All three    |

## Anti-Patterns

| Avoid              | Why                              | Instead                      |
| ------------------ | -------------------------------- | ---------------------------- |
| Sequential agents  | Loses parallelism benefit        | Single message, 3 Task calls |
| Skipping synthesis | Raw findings lack prioritization | Always synthesize            |
| Wrong model        | Haiku lacks analytical depth     | Use opus for all three       |
| Vague target       | Agents need concrete scope       | Specify exact file path      |

See [Variants & Custom Lenses](references/variants-and-custom-lenses.md) for built-in presets, custom lens configuration, and 4-lens with Arbiter details.

## Verification

Audit is complete when:

- [ ] All 3 agents returned structured findings
- [ ] Convergent findings identified
- [ ] Recommendations prioritized by severity × effort
- [ ] Actionable next steps stated

## References

- [Agent Prompts](references/agent-prompts.md) — Complete prompts for each lens (including Arbiter)
- [Output Validation](references/agent-prompts.md#output-format-validation) — Verify agent outputs before synthesis
- [Custom Lens Template](references/custom-lens-template.md) — Framework for defining domain-specific lenses
- [Claude Code Capabilities](references/claude-code-capabilities.md) — Artifact types, failure modes, checklists for `--claude-code` audits
- [Re-Audit Workflow](references/workflow-details.md) — Iteration strategies, exit criteria, action tracking
- [Scripts Reference](references/scripts-reference.md) — `run_audit.py`, `validate_output.py`, `synthesize.py` documentation
- [Variants & Custom Lenses](references/variants-and-custom-lenses.md) — Built-in presets and custom lens configuration
- [Worked Example: Writing Skill](examples/audit-output-example.md) — Real audit of `writing-for-claude` skill
- [Worked Example: Claude Code](examples/claude-code-audit-example.md) — Real audit of a Claude Code skill design

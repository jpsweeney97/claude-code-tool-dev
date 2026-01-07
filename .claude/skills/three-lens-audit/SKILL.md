---
name: three-lens-audit
description: Deploy 3+ parallel agents with competing philosophies to stress-test documents, frameworks, or designs
license: MIT
metadata:
  version: 1.15.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Multi-Lens Audit

Deploy parallel agents with distinct analytical perspectives to find issues single-perspective review would miss.

## Triggers

- `/three-lens-audit <file>` — Default 3 lenses
- `/three-lens-audit <file> --design` — Design audit (robustness + minimalist + capability)
- `/three-lens-audit <file> --claude-code` — Claude Code artifact feasibility

## Quick Reference

| Preset | Lenses | Use When |
|--------|--------|----------|
| Default | Adversarial, Pragmatic, Cost/Benefit | Processes, frameworks, guidelines |
| `--design` | Robustness, Minimalist, Capability, Arbiter | Specs, architecture docs |
| `--claude-code` | Implementation, Adversarial, Cost/Benefit | Skills, hooks, plugins, MCP |
| `--quick` | Adversarial, Pragmatic | Fast sanity check |

**Default lenses:**
| Lens | Question | Finds |
|------|----------|-------|
| **Adversarial** | How does this break? | Contradictions, exploits, failure modes |
| **Pragmatic** | Does this actually help? | Friction, cognitive load, missing pieces |
| **Cost/Benefit** | Is this worth it? | ROI by element, optimization opportunities |

See [Variants & Custom Lenses](references/variants-and-custom-lenses.md) for lens philosophy, single-lens guidance, and custom configurations.

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
└─────────────────────────────────────────────┘
```

## Commands

| Command | Action |
|---------|--------|
| `/three-lens-audit <file>` | Full three-lens audit |
| `/three-lens-audit <file> --claude-code` | Claude Code feasibility audit |
| `/three-lens-audit <file> --design` | Design audit |
| `/three-lens-audit <file> --lens adversarial` | Single lens only |
| `/three-lens-audit <file> --quick` | Two-lens (skip cost-benefit) |
| `/three-lens-audit <file> --impl-spec` | Output implementation spec for fixes |

## Workflow

```bash
# 1. Prepare — get cost estimate + task templates
python scripts/run_audit.py prepare target.md

# 2. Execute — copy/paste 3 Task tool calls (single message!)
# Save outputs to adversarial.md, pragmatic.md, cost-benefit.md

# 3. Finalize — validate + synthesize
python scripts/run_audit.py finalize adversarial.md pragmatic.md cost-benefit.md --target "Name"
```

See [Workflow Details](references/workflow-details.md) for cost estimation, incremental mode, and recovery procedures.

## Example

From an audit of `writing-for-claude` skill:

**Adversarial:** P2 vs P7 priority is subjective — can justify contradictory edits
**Pragmatic:** Top-heavy — most value in tables, most tokens in prose
**Cost/Benefit:** `principles.md` over-documented (8K tokens, medium benefit)

**Synthesis:** Pragmatic + Cost/Benefit both flagged `principles.md` size → convergent → P1 fix.

_Full example: [examples/audit-output-example.md](examples/audit-output-example.md)_

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Sequential agents | Loses parallelism benefit | Single message, 3 Task calls |
| Skipping synthesis | Raw findings lack prioritization | Always synthesize |
| Wrong model | Haiku lacks analytical depth | Use opus for all three |
| Vague target | Agents need concrete scope | Specify exact file path |

## Verification

Audit is complete when:
- [ ] All 3 agents returned structured findings
- [ ] Convergent findings identified (manual review for semantic matches)
- [ ] Recommendations prioritized by severity × effort
- [ ] Actionable next steps stated

## References

- [Agent Prompts](references/agent-prompts.md) — Complete prompts for each lens
- [Workflow Details](references/workflow-details.md) — Cost estimation, incremental mode, execution steps, re-audit
- [Implementation Spec](references/implementation-spec.md) — `--impl-spec` output format
- [Claude Code Capabilities](references/claude-code-capabilities.md) — Artifact checklists for `--claude-code`
- [Variants & Custom Lenses](references/variants-and-custom-lenses.md) — Lens philosophy, presets, custom configs
- [Custom Lens Template](references/custom-lens-template.md) — Framework for domain-specific lenses
- [Scripts Reference](references/scripts-reference.md) — `run_audit.py`, `validate_output.py`, `synthesize.py`

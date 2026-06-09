# Review Family Plugin

Evidence-first Claude review, scrutiny, and review-adjudication skills for local
development workflows.

## What It Does

| Capability | Skills | Description |
|------------|--------|-------------|
| **Adversarial artifact review** | `scrutinize` | Challenge plans, designs, drafts, decisions, and broad artifacts with evidence-backed findings. Ask for a formal stress test when you want an explicit assumptions audit, pre-mortem, dimensional critique, and confidence boundary; ask for an execution-readiness review when you need to know whether a plan is ready to build from. |
| **Skill behavior review** | `scrutinize-skill` | Review Claude skills as behavior contracts for execution quality, UX, composability, overlap, and proof gaps. Skill targets route here even when the user says "scrutinize". |
| **Implementation review** | `implementation-review` | Review completed work against a plan, spec, diff, or known intended behavior. |
| **System design review** | `system-design-review` | Review architecture and system design artifacts for scoped design-lens gaps and missing probes. |
| **Review adjudication** | `review-reviewer` | Check supplied reviews and pasted review claims against target evidence before acting on them. |

## Components

### Skills (5)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `implementation-review` | Completed implementation review against a plan, spec, PR, or known intended behavior | Compare implemented behavior to the stated contract and report ranked findings. |
| `review-reviewer` | Supplied review, critique, audit, reviewer output, or pasted claims that need checking | Separate current truth from reviewer disposition and identify which findings or claims are valid, stale, or unproven. |
| `scrutinize` | "Scrutinize", "tear this apart", "be brutal", reject-until-proven review, formal stress test, or execution-readiness review for non-skill targets | Adversarially inspect a plan, design, argument, code change, or broad artifact without implementing fixes. |
| `scrutinize-skill` | Adversarial review of a Claude skill or proposed skill contract | Review whether the skill will guide Claude behavior well once triggered, including UX, overlap, composability, and proof gaps. |
| `system-design-review` | Architecture or system design review of docs, verbal designs, or codebase structure | Review design tradeoffs, defaults, interfaces, operations, and next probes. |

The plugin is intentionally review-only. These skills may recommend repairs,
verification, or escalation, but they do not edit files, stage changes, commit,
sync, publish, or run cleanup unless the user explicitly widens the task after
the review.

## Design Context: brainstorming-subagents

**Type:** Process/workflow
**Risk:** Low (bounded file writes, reversible)

### Purpose
> Replace the procedural `creating-subagents` skill with a brainstorming approach that produces higher-quality subagents through collaborative dialogue, convergence tracking, and adversarial checkpoints.

### Success Criteria
> - Quality subagent prompts: unambiguous task, complete context, clear output spec, defined boundaries, consistent instructions
> - Proper scope calibration (neither too broad nor too narrow)
> - Convergence tracking before proceeding to draft
> - Adversarial checkpoint before presenting design

### Problem Statement
`creating-subagents` was too procedural — rushed through without understanding the problem, lacked depth on subagent-specific concerns, had no convergence check, and produced agents with unclear prompts.

Primary issues identified:
1. **Prompt clarity** (main issue) — ambiguous task, missing context, vague output, unclear boundaries, conflicting instructions
2. **Scope calibration** — agents were both too broad (wandering) and too narrow (stopping short)
3. **Extension type choice** — sometimes subagent wasn't the right tool

### Prompt Clarity Assessment
- Task clarity: Skill enforces exploration of task specificity before drafting
- Context completeness: Dimensions to cover include "context needs"
- Output contract: Explicit dimension in convergence checklist

### Scope Calibration
- Too broad risks: Addressed via "Scope boundaries" dimension and adversarial "scope calibration" check
- Too narrow risks: Writing guide includes signals for both directions
- Calibration decision: Guide provides questions to find the useful middle

### Compliance Risks
What would make Claude skip brainstorming and just generate an agent?
- "This agent is simple, I already know what they want"
- "User seems impatient, let me just generate it"
- "I've made agents before, I know the pattern"

Mitigated via assumption traps list (same as brainstorming-skills) and red flag callouts.

### Rejected Approaches
- **Complement creating-subagents:** User wanted replacement, not two skills
- **Decision framework for extension type:** User said out of scope — focus on subagent quality

### Design Decisions
- **Mirror brainstorming-skills structure:** Maintains consistency with established methodology
- **Emphasize prompt clarity in writing guide:** Primary issue was unclear prompts; guide dedicates most space to this
- **Subagents as specialists, not narrow task executors:** Corrected during drafting — specificity examples reframed
- **Testing handoff without specifying skill:** testing-subagents is out of scope for now
- **Replaces creating-subagents:** Old skill will be deleted

## Design Context: skill-explorer

**Model:** opus
**Tools:** Read, Glob, Grep

### Purpose
> Thoroughly explore a skill directory to give Claude context for review or modification work — equivalent to having explored the skill directly.

### Success Criteria
> Output enables Claude to review or modify the skill without reading the files itself.

### Prompt Clarity Assessment
- **Task clarity:** Specific steps — discover files, map structure, analyze SKILL.md, summarize supporting files, compile report
- **Context completeness:** Receives skill path only; discovers everything else
- **Output contract:** Four-section structured report (inventory, SKILL.md analysis, supporting summaries, observations)

### Scope Calibration
- **Too broad risks:** Could expand to analyzing skill quality or comparing skills — prevented by explicit constraints
- **Too narrow risks:** Could miss important context by being too brief — mitigated by prioritization strategy for large skills
- **Calibration decision:** Read-only exploration with no judgment; comprehensive within skill directory boundaries

### Rejected Approaches
- **Dimension-oriented output:** Organizing output by review dimensions (D1-D16) would couple the agent to reviewing-skills; rejected in favor of independent, general-purpose output
- **Full content transfer:** Including complete file contents would waste context window; rejected for excerpts + summaries
- **Narrative analysis:** Prose-only output would be harder to consume; rejected for structured sections

### Design Decisions
- **opus model:** User preference for quality of exploration output over cost efficiency
- **No judgment constraint:** Agent reports what exists; main thread does analysis — keeps agent focused and output neutral
- **Prioritization for large skills:** SKILL.md and first-level references get full treatment; deeper content summarized briefly

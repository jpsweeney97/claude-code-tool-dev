---
date: 2026-02-03
time: "21:30"
created_at: "2026-02-04T02:30:10Z"
session_id: 0f10972e-0dc8-4340-a39e-3840f096d5d2
project: claude-code-tool-dev
branch: main
commit: 9c08425
title: Improving-skills simulation-based assessment design
files:
  - .claude/skills/improving-skills/SKILL.md
  - .claude/skills/improving-skills/skills-guide.md
  - docs/discussions/improving-skills-failure-modes-and-simulation-based-assessment.md
---

# Handoff: Improving-skills simulation-based assessment design

## Goal

Root cause analysis of why the `improving-skills` skill fails to achieve its primary objective, and design of a simulation-based assessment approach to fix it.

## Decisions

- **Simulation-based assessment as primary method:** Replace theoretical assessment (comparing to skills-guide.md) with empirical assessment (deploying multiple subagents to observe actual behavior). Driven by observed failure modes: Claude completed assessments but produced low-quality findings because it assessed form (structural compliance) rather than function (effectiveness).

- **Assessment hierarchy established:** Empirical assessment is primary (determines effectiveness); theoretical analysis is supporting (screening, remediation, sanity checks). Neither alone is sufficient. User stated: "Empirical assessment should be the primary basis for evaluating quality and effectiveness. Theoretical analysis serves as a complementary, supporting assessment."

- **5 scenarios as default:** Quality over quantity. Well-chosen scenarios that cover the behavior landscape (happy path, edge cases, boundaries) matter more than volume.

- **Purpose-First + Simulation-Based work together:** Purpose-First defines what the skill should achieve (success criteria). Simulation-Based measures against those criteria. The gap = the improvement work.

## Context

**Root cause identified:** The current skill conflates form with function. Its assessment steps (2, 3, 4) all focus on skills-guide.md compliance. The "Center Claude's Actual Needs" section asks the right questions about effectiveness but provides no operational method for answering them. Result: Claude can complete the checklist without substantive analysis.

**Core insight:** "Structural compliance ≠ functional effectiveness" — a skill can follow all guidelines and still fail at its purpose. The skill measures the wrong thing.

**Mental model:** Skill improvement should be treated as empirical science, not code review. Don't reason about what might happen; run experiments and observe what actually happens.

## Learnings

**The discipline skill paradox:** Discipline skills exist because Claude shortcuts processes. But if assessment is itself a checklist, Claude can complete the checklist without genuine analysis. The skill enforces process compliance, not substantive thinking.

**Why subagents enable this:** Subagents run in isolated context windows with custom system prompts and independent tool access. This allows controlled experiments: baseline subagent truly doesn't have the skill; test subagent truly does. Same task, same conditions, different skill presence.

**Avoiding overfitting:** Holdout scenarios (not used during iteration), scenario rotation, adversarial design, and root-cause fixing all contribute to generalization. The reason for passing matters as much as the fact of passing.

**Hard-to-test skills:** Different categories of difficulty (long-term effects, qualitative effects, context-dependent, emergent, rare triggers, negative effects, meta-cognitive, high-variance) require different mitigations. "Untestable" often reveals something about the skill itself.

## Rejected Approaches

- **Patching the current skill:** Adding "also consider effectiveness" would create another aspirational section that Claude bypasses. The structural-compliance framing would still dominate.

- **Theoretical assessment alone:** Doesn't work — this is the documented failure mode we're trying to fix.

## Next Steps

User was presented with options; no selection made yet:

1. **Design phase:** Architect the new skill structure incorporating simulation-based assessment
2. **Prototype:** Build a minimal version to test the approach
3. **Scenario design:** Develop specific test scenarios for improving-skills itself

## Artifacts

Full discussion captured in:
- `docs/discussions/improving-skills-failure-modes-and-simulation-based-assessment.md`

Contains: complete root cause analysis, proposed solution mechanism, worked conclusions for all 4 design questions (scenario count, overfitting avoidance, hard-to-test skills, cost/benefit), key insights summary.

## Open Questions

- How should the new skill architecture be structured?
- What specific scenarios should test improving-skills itself?
- What threshold defines "good enough" improvement?

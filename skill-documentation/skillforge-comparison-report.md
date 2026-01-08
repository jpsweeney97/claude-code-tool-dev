# Skillforge vs Skill Documentation Framework: Comparison Report

## Overview

This report compares two approaches to skill quality:

1. **Skill Documentation Framework** (`skill-documentation/`) - Structural spec with automated linting
2. **Skillforge** (`~/.claude/skills/skillforge/`) - Multi-phase creation process with synthesis panel

These approaches target different moments in the skill lifecycle: Skillforge is a **creation-time process** that guides skill development through iterative analysis, while the Skill Documentation Framework is a **review-time specification** that defines what constitutes a compliant skill.

## Framework Summary

### Skill Documentation Framework

**Nature:** Normative specification + automated linter

**Core components:**
- 8 required content areas (When to use, When NOT, Inputs, Outputs, Procedure, Decision points, Verification, Troubleshooting)
- 8 FAIL codes (automated enforcement via `skill_lint.py`)
- 3 risk tiers (Low, Medium, High) with escalating requirements
- 13 categories with category-specific guidance
- Machine-first retrieval contracts (Section IDs, retrieval keys)

**Quality gates:**
- Structural completeness (automated)
- Semantic quality (human review with rubric)
- Risk-appropriate rigor (tier-based minimums)

**Output:** PASS / PASS-WITH-NOTES / FAIL disposition

### Skillforge

**Nature:** Multi-phase creation workflow with AI synthesis panel

**Core components:**
- Phase 0: Skill Triage (route to USE/IMPROVE/CREATE/COMPOSE)
- Phase 1: Deep Analysis (11 thinking models, regression questioning, automation analysis)
- Phase 2: Specification (XML spec with all decisions + WHY)
- Phase 3: Generation (SKILL.md + references/ + scripts/)
- Phase 4: Synthesis Panel (3-4 Opus agents, unanimous approval required)

**Quality gates:**
- Timelessness score >= 7 (required)
- Unanimous multi-agent approval
- Frontmatter validation (quick_validate.py, validate-skill.py)
- Evolution/timelessness as core lens

**Output:** Production-ready agentic skill with verification scripts

## Requirement Mapping

| Framework Requirement | Skillforge Coverage | Notes |
|----------------------|---------------------|-------|
| When to use section | **Partial** | Skillforge generates triggers (3-5 varied phrases) but doesn't mandate explicit "When to use" prose section |
| When NOT to use | **Partial** | Anti-patterns section exists; no explicit "When NOT to use" heading requirement |
| Inputs section | **Partial** | Requirements analyzed (explicit/implicit/discovered) but not structured as Required/Optional/Constraints |
| Outputs section | **Partial** | Artifacts defined but no explicit "Definition of Done with objective checks" requirement |
| Procedure section | **Yes** | "Numbered Procedure" explicitly required in generation checklist |
| Decision points | **Partial** | Architecture includes decision_points in spec; no minimum count (2) enforced |
| Verification | **Partial** | Success criteria with verification methods; no "quick check with expected result shape" pattern |
| Troubleshooting | **No** | Not mentioned in Skillforge requirements or generation checklist |
| Objective DoD | **Partial** | Success criteria are measurable but not in Framework's specific format |
| STOP behavior | **No** | Not addressed in Skillforge process |
| Ask-first for risky actions | **No** | Not addressed in Skillforge process |
| Risk tier classification | **No** | No risk tiering system; timelessness score serves different purpose |
| Category routing | **No** | No category system; uses domain tagging instead |

## Quality Dimensions

### Framework-Only Criteria

| Criterion | Framework Requirement |
|-----------|----------------------|
| **8 FAIL codes** | Automated structural enforcement |
| **Risk tier classification** | Low/Medium/High with escalating requirements |
| **STOP/ask-first gates** | Required for missing inputs, ambiguity, risky actions |
| **Machine retrieval contracts** | Section IDs, retrieval keys for programmatic access |
| **Category tightening matrix** | 13 categories with per-column strictness levels |
| **Command mention rule** | Commands must specify expected result shape + preconditions + fallback |
| **Troubleshooting section** | Required symptoms/causes/next steps format |
| **Offline fallback** | Required when feasible (MUST for High risk) |

### Skillforge-Only Criteria

| Criterion | Skillforge Requirement |
|-----------|----------------------|
| **Timelessness score** | Must be >= 7 (1-10 scale) |
| **Evolution analysis** | Temporal projection (6mo, 1yr, 2yr, 5yr) |
| **Multi-agent synthesis** | 3-4 Opus agents must unanimously approve |
| **11 thinking models** | First Principles, Inversion, Second-Order, Pre-Mortem, etc. |
| **Regression questioning** | Iterative self-questioning until 3 empty rounds |
| **WHY documentation** | Every decision must include rationale |
| **Automation analysis** | Scripts for validation/generation/state management |
| **Extension points** | Minimum 2 documented |
| **Anti-obsolescence patterns** | Design around principles, not implementations |
| **Duplicate prevention** | Phase 0 scans 250+ skills before creation |

### Shared Concerns (Different Approaches)

| Concern | Framework Approach | Skillforge Approach |
|---------|-------------------|---------------------|
| **Preventing over-activation** | "When NOT to use" section | Phase 0 triage routes to existing skills |
| **Input validation** | Structured Required/Optional/Constraints | Explicit/implicit/discovered requirements |
| **Output quality** | Objective DoD checks | Multi-agent approval + timelessness score |
| **Procedure clarity** | Numbered steps + decision points | Numbered procedure + phases |
| **Verification** | Quick checks with expected results | Success criteria + validation scripts |

## Compatibility Analysis

### Complementary Aspects

The approaches are largely **complementary**, not conflicting:

1. **Lifecycle coverage:** Skillforge guides creation (proactive); Framework validates output (reactive)
2. **Quality dimensions:** Skillforge emphasizes evolution/timelessness; Framework emphasizes operational safety
3. **Automation:** Both support automation (Skillforge via scripts, Framework via linter)

### Potential Conflicts

1. **Structure flexibility:** Skillforge doesn't mandate the Framework's 8-section skeleton; generated skills may not pass the linter without post-processing
2. **Verification format:** Skillforge's "success criteria" don't match Framework's "quick check with expected result shape" pattern
3. **Risk awareness:** Skillforge has no equivalent to Framework's STOP/ask-first gates for dangerous operations
4. **Troubleshooting:** Skillforge doesn't generate troubleshooting sections at all

### Integration Path

Skillforge could be enhanced to produce Framework-compliant skills by:

1. Adding "When NOT to use" to generation checklist
2. Adding troubleshooting section generation
3. Adding STOP/ask-first language for input validation and risky operations
4. Formatting verification as "quick check" with expected result patterns
5. Optionally running `skill_lint.py` as a Phase 4 validation step

## Gap Analysis

### Gaps in Skillforge (things Framework checks that Skillforge doesn't)

| Gap | Risk Level | Remediation Difficulty |
|-----|------------|----------------------|
| No troubleshooting section | Medium | Low - add to generation checklist |
| No STOP/ask-first behavior | High | Medium - requires procedure template changes |
| No risk tier awareness | Medium | Medium - map timelessness to risk |
| No offline fallback requirement | Medium | Low - add to constraint analysis |
| No "When NOT to use" prose | Low | Low - add to generation checklist |
| No quick check format | Low | Low - template change |

### Gaps in Framework (things Skillforge checks that Framework doesn't)

| Gap | Value Level | Remediation Difficulty |
|-----|-------------|----------------------|
| No timelessness/evolution scoring | High | High - requires judgment, not automation |
| No multi-model thinking analysis | High | N/A - creation-time only |
| No duplicate detection | Medium | Medium - requires skill registry |
| No WHY documentation requirement | Medium | Low - add to semantic quality addendum |
| No extension point requirement | Low | Low - add to guidance |
| No script quality standards | Medium | Medium - separate script spec needed |

## Recommendations

### For Immediate Alignment

1. **Add Framework validation to Skillforge Phase 4:**
   - Run `skill_lint.py` after generation
   - Fail synthesis if any FAIL code triggers
   - This catches structural gaps before multi-agent review

2. **Add troubleshooting to Skillforge generation:**
   - Include "Common failure modes" section in generation checklist
   - Require symptoms/causes/next steps format

3. **Add STOP/ask-first to Skillforge templates:**
   - Include STOP gate for missing required inputs
   - Include ask-first gate when procedure includes mutating steps

### For Future Alignment

4. **Cross-pollinate quality criteria:**
   - Add "timelessness consideration" to Framework's semantic quality addendum
   - Add "WHY documentation" guidance to Framework
   - Add "extension points" recommendation to Framework

5. **Consider unified tooling:**
   - `skill_lint.py` could incorporate Skillforge's frontmatter validation
   - Skillforge's validate-skill.py could incorporate Framework's 8-section checks

### What NOT to Change

- **Keep approaches separate:** Creation-time depth (Skillforge) and review-time rigor (Framework) serve different purposes
- **Don't add timelessness scoring to linter:** It requires human/AI judgment, not pattern matching
- **Don't require Skillforge for all skills:** Simple skills don't need 4-phase creation

## Conclusion

Skillforge and the Skill Documentation Framework address different stages of skill development with different emphases:

- **Skillforge** excels at ensuring skills are well-conceived, future-proof, and thoroughly vetted through multi-agent review
- **Framework** excels at ensuring skills are operationally safe, structurally complete, and machine-verifiable

The ideal workflow uses both:

```
Skillforge creation process
        |
        v
Framework validation (skill_lint.py)
        |
        v
Human review (semantic quality)
        |
        v
Production deployment
```

The main integration work is adding Framework validation to Skillforge's output phase and adding troubleshooting/STOP behavior to Skillforge's generation templates.

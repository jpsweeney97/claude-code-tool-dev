# Extended Testing Lenses

Three additional lenses (12-14) focused specifically on skill verification. These complement the 11 base thinking lenses from skillosophy.

## Overview

| # | Lens | Core Question | Scenario Type |
|---|------|---------------|---------------|
| 12 | **User Goals** | What does success look like? | Goal achievement test |
| 13 | **Edge Cases** | What unusual states might occur? | Boundary test |
| 14 | **Discoverability** | How will agents find this skill? | Trigger/search test |

## Lens 12: User Goals

**Purpose:** Ensure the skill actually achieves what users need, not just what was specified.

**Application:**

1. List the user's actual goals (not requirements)
2. For each goal, create a scenario that tests achievement
3. Verify skill guides agent toward goal, not just compliance

**Key Questions:**

- What outcome does the user ultimately want?
- Would following this skill perfectly still fail the user?
- Are there shortcuts to goal achievement the skill should enable?

**Scenario Format:**

```
User goal: [what they actually want]
Scenario: [realistic situation where goal matters]
Expected: Agent achieves goal, not just follows process
```

## Lens 13: Edge Cases

**Purpose:** Identify unusual but valid states where skill behavior is undefined.

**Application:**

1. List state boundaries (empty, maximum, concurrent, interrupted)
2. For each boundary, define expected behavior
3. Create scenario testing boundary behavior

**Edge Case Categories:**

| Category | Examples |
|----------|----------|
| Empty/Null | No input, empty file, missing config |
| Maximum | Very long input, many iterations, nested calls |
| Concurrent | Multiple invocations, race conditions |
| Interrupted | Context exhaustion, timeout, abort |
| Invalid | Wrong format, conflicting inputs, missing deps |

**Scenario Format:**

```
Edge case: [unusual state]
Scenario: [how this state occurs naturally]
Expected: [defined behavior - not "handle gracefully"]
```

## Lens 14: Discoverability

**Purpose:** Ensure agents can find and recognize when to use this skill.

**Application:**

1. List all ways an agent might encounter this need
2. For each entry point, verify triggers or description match
3. Create scenario testing skill discovery

**Discoverability Dimensions:**

| Dimension | Questions |
|-----------|-----------|
| Triggers | Do trigger phrases match how users naturally ask? |
| Description | Does description contain error messages users might see? |
| Symptoms | Are failure symptoms documented in When to Use? |
| Keywords | Would searching for problem keywords find this skill? |

**Scenario Format:**

```
Entry point: [how agent encounters need]
Search/trigger: [what agent might look for]
Expected: Skill is found and recognized as relevant
```

## Integration with Base Lenses

The extended lenses complement the base lenses:

| Extended Lens | Related Base Lenses |
|---------------|---------------------|
| User Goals | First Principles, Adversarial |
| Edge Cases | Constraint, Failure |
| Discoverability | Composition, Evolution |

Apply extended lenses after base lenses to catch skill-specific issues the base lenses may miss.

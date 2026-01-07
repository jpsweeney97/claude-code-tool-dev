# Variants & Custom Lenses

Built-in presets and custom lens configurations.

## Built-in Presets

| Preset          | Lenses                                       | Use When                         |
| --------------- | -------------------------------------------- | -------------------------------- |
| Default         | Adversarial, Pragmatic, Cost/Benefit         | General stress-testing           |
| `--design`      | Robustness, Minimalist, Capability + Arbiter | Design documents, specifications |
| `--claude-code` | Implementation, Adversarial, Cost/Benefit    | Claude Code feature proposals    |
| `--quick`       | Adversarial, Pragmatic                       | Fast review, skip ROI analysis   |

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

## When to Use Each Lens Alone

| Situation                | Lens         |
| ------------------------ | ------------ |
| Security review          | Adversarial  |
| Onboarding documentation | Pragmatic    |
| Process optimization     | Cost/Benefit |
| High-stakes artifact     | All three    |

## Custom Lens Configuration

For domain-specific audits, define custom lenses with:

1. **Philosophy** — What perspective does this lens embody?
2. **Core Question** — What single question drives analysis?
3. **Analysis Vectors** — 4-6 specific areas to examine
4. **Output Format** — Structured output for synthesis

**Example custom configurations:**

| Domain           | Lens Trio                                | Questions                                                 |
| ---------------- | ---------------------------------------- | --------------------------------------------------------- |
| **Security**     | Attacker / Defender / Auditor            | How to exploit? / How to prevent? / What to log?          |
| **API Design**   | Consumer / Maintainer / Operator         | Is it usable? / Is it evolvable? / Is it observable?      |
| **UX**           | Novice / Expert / Accessibility          | Can they start? / Can they master? / Can everyone use it? |
| **Architecture** | Performance / Maintainability / Security | Is it fast? / Is it changeable? / Is it safe?             |

## 4-Lens with Arbiter

When using 4 lenses, the 4th lens (Arbiter) runs AFTER the other 3 complete and synthesizes:

- Convergent findings across all lenses
- Lens-specific unique insights
- Prioritized recommendations with effort/impact

The Arbiter is executed by the main thread, not a separate agent.

# Variants & Custom Lenses

Built-in presets and custom lens configurations.

## Built-in Presets

| Preset          | Lenses                                       | Use When                         |
| --------------- | -------------------------------------------- | -------------------------------- |
| Default         | Adversarial, Pragmatic, Cost/Benefit         | General stress-testing           |
| `--design`      | Robustness, Minimalist, Capability + Arbiter | Design documents, specifications |
| `--claude-code` | Implementation, Adversarial, Cost/Benefit    | Claude Code feature proposals    |
| `--quick`       | Adversarial, Pragmatic                       | Fast review, skip ROI analysis   |

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

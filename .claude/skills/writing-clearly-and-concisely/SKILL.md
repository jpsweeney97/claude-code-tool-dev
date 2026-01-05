---
name: writing-clearly-and-concisely
description: Apply Strunk's timeless writing rules to ANY prose humans will read—documentation, commit messages, error messages, explanations, reports, or UI text. Makes your writing clearer, stronger, and more professional.
---

# Writing Clearly and Concisely

## Overview

William Strunk Jr.'s *The Elements of Style* (1918) teaches you to write clearly and cut ruthlessly.

**WARNING:** `elements-of-style.md` consumes ~12,000 tokens. Read it only when writing or editing prose.

---

## When to Use This Skill

Use this skill whenever you write prose for humans:

- Documentation, README files, technical explanations
- Commit messages, pull request descriptions
- Error messages, UI copy, help text, comments
- Reports, summaries, or any explanation
- Editing to improve clarity

**If you're writing sentences for a human to read, use this skill.**

---

## Limited Context Strategy

When context is tight:
1. Write your draft using judgment
2. Dispatch a subagent with your draft and `elements-of-style.md`
3. Have the subagent copyedit and return the revision

---

## All Rules

### Elementary Rules of Usage (Grammar/Punctuation)
1. Form possessive singular by adding 's
2. Use comma after each term in series except last
3. Enclose parenthetic expressions between commas
4. Comma before conjunction introducing co-ordinate clause
5. Don't join independent clauses by comma
6. Don't break sentences in two
7. Participial phrase at beginning refers to grammatical subject

### Elementary Principles of Composition
8. One paragraph per topic
9. Begin paragraph with topic sentence
10. **Use active voice**
11. **Put statements in positive form**
12. **Use definite, specific, concrete language**
13. **Omit needless words**
14. Avoid succession of loose sentences
15. Express co-ordinate ideas in similar form
16. **Keep related words together**
17. Keep to one tense in summaries
18. **Place emphatic words at end of sentence**

### Section V: Words and Expressions Commonly Misused
Alphabetical reference for usage questions

---

## Framework Connection

This skill implements the [Framework for Improvement](~/.claude/references/framework-for-improvement.md).

| Framework Element | This Skill |
|-------------------|------------|
| **Criteria** | Strunk's rules (enumerated in elements-of-style.md) |
| **Invariants** | Author's intent, factual accuracy, audience-appropriate register |
| **Fidelity** | Preserve meaning while changing expression |
| **Validity** | Each edit maps to a specific rule |

### Applying the Framework

**Definition Phase:**
- Scope: The prose being edited
- Criteria: Rules 10-13, 16, 18 (composition) + relevant usage rules
- Invariants: Facts, purpose, voice (unless voice IS the problem)

**Execution Phase:**
For each sentence:
1. Fidelity: Does the edit preserve meaning?
2. Validity: Which rule justifies this change?
3. Completeness: Have all applicable rules been checked?

**Example:**

Before: "The results that were obtained by the team were surprising."

| Check | Analysis |
|-------|----------|
| Rule 10 | Passive voice ("were obtained") → Active: "The team obtained" |
| Rule 13 | "results that were obtained" → "results" (needless words) |
| Fidelity | Same facts, same meaning, clearer expression |

After: "The team's results surprised us."

---

## Bottom Line

Writing for humans? Read `elements-of-style.md` and apply the rules. Low on tokens? Dispatch a subagent to copyedit with the guide.

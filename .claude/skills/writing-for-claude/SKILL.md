---
name: writing-for-claude
description: Apply evidence-based principles to improve Claude-facing artifacts—system prompts, CLAUDE.md, skills, tool descriptions. The counterpart to writing-clearly-and-concisely for LLM consumption.
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Writing for Claude

## Overview

This skill applies 18 evidence-based principles to improve artifacts Claude will read—system prompts, CLAUDE.md files, skills, tool descriptions, and output styles.

The counterpart to `writing-clearly-and-concisely` (which applies Strunk's rules to human-facing prose), this skill optimizes for Claude's instruction-following behavior based on Anthropic's official documentation and empirical research.

**Note:** `references/principles.md` consumes ~8,000 tokens. Read only when actively transforming Claude-facing artifacts.

---

## When to Use This Skill

Use when writing or editing:

- System prompts and CLAUDE.md files
- Skill definitions (SKILL.md)
- Tool descriptions and function docstrings
- Context documents Claude will reference
- Agent instructions

**If Claude will read it as instructions, use this skill.**

---

## When NOT to Use

- Human-facing prose → use `writing-clearly-and-concisely`
- Code comments humans read → use `writing-clearly-and-concisely`
- Deciding _what_ to instruct → this skill covers _how_, not _what_

---

## Quick Reference

### Token Efficiency

| #   | Principle                | Key Point                                                        |
| --- | ------------------------ | ---------------------------------------------------------------- |
| 1   | Omit filler phrases      | "Please," "thank you," hedging phrases have no effect on outputs |
| 2   | Use structure over prose | Tables, lists, XML compress information                          |
| 3   | Reference context        | Cite what Claude read; avoid summarizing it back                 |

### Clarity

| #   | Principle          | Key Point                                                                        |
| --- | ------------------ | -------------------------------------------------------------------------------- |
| 4   | Be explicit        | Claude 4.x follows precise instructions—explicit beats implicit                  |
| 5   | State what to do   | Positive framing ("use X") is clearer than negative ("avoid Y")                  |
| 6   | Resolve ambiguity  | Unclear pronouns and vague terms cause mistakes                                  |
| 7   | Provide motivation | Explain _why_—Claude generalizes from the explanation                            |
| 8   | Assign a role      | "You are a senior code reviewer" focuses behavior more than generic instructions |

### Structure

| #   | Principle                    | Key Point                                                         |
| --- | ---------------------------- | ----------------------------------------------------------------- |
| 9   | Use XML tags                 | `<instructions>`, `<example>`, `<data>` prevent section confusion |
| 10  | Data at top, query at bottom | Queries at end improve quality by up to 30%                       |
| 11  | Group related instructions   | Nest XML tags for hierarchy                                       |
| 12  | Separate concerns            | Keep "when," "how," and "examples" distinct                       |

### Examples & Emphasis

| #   | Principle                  | Key Point                                                          |
| --- | -------------------------- | ------------------------------------------------------------------ |
| 13  | Examples must match intent | Claude 4.x pays close attention—misaligned examples cause problems |
| 14  | Use emphasis sparingly     | CRITICAL/MUST work but may overtrigger in Claude 4.5               |
| 15  | Use output primers         | Start Claude's response with the format you want                   |

### Skill Authoring (SKILL.md only)

| #   | Principle                   | Key Point                                                         |
| --- | --------------------------- | ----------------------------------------------------------------- |
| 16  | Follow schema exactly       | Only allowed: name, description, license, allowed-tools, metadata |
| 17  | Self-contained descriptions | Must work without context—used for matching and display           |
| 18  | Metadata for evolution      | Separate stable fields from versioned fields                      |

_Principles 16-18 apply only to skill files. For system prompts, CLAUDE.md, and tool descriptions, use principles 1-15._

---

## When Principles Conflict

Priority order (highest to lowest):

1. **Meaning preservation** — Never sacrifice intent for style
2. **Safety constraints** — Security-critical emphasis (P14 edge case) trumps brevity
3. **Clarity** (P4-8) — Being understood beats compression
4. **Structure** (P9-12) — Organization aids comprehension
5. **Token efficiency** (P1-3) — Optimize last, after clarity is achieved

**Example conflict:** P2 (use tables) vs P7 (provide motivation). If the _why_ doesn't fit in a table, use prose. Clarity wins over compression.

---

## Artifact Types

| Artifact          | Audience                       | Which Skill                   |
| ----------------- | ------------------------------ | ----------------------------- |
| Output styles     | Claude only                    | writing-for-claude            |
| System prompts    | Claude only                    | writing-for-claude            |
| CLAUDE.md         | Claude + human maintainers     | Both (by section)             |
| Skill files       | Claude executes, humans author | Both (by section)             |
| Tool descriptions | Claude + human developers      | Both (by section)             |
| Code comments     | Humans only                    | writing-clearly-and-concisely |

---

## Framework Connection

This skill implements the [Framework for Improvement](~/.claude/references/framework-for-improvement.md).

| Framework Element | This Skill                                                 |
| ----------------- | ---------------------------------------------------------- |
| **Criteria**      | 18 evidence-based principles (in references/principles.md) |
| **Invariants**    | Author's intent, factual accuracy, instruction semantics   |
| **Fidelity**      | Preserve meaning while changing expression                 |
| **Validity**      | Each edit maps to a specific principle                     |

---

## Limited Context Strategy

When context is tight:

1. Write your draft using the Quick Reference above
2. Dispatch a subagent with your draft and `references/principles.md`
3. Have the subagent edit and return the revision

---

## Full Reference

→ [references/principles.md](references/principles.md) — complete treatment with examples and edge cases

---

## Sources

All principles derived from:

- [Anthropic: Claude 4 Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Anthropic: Be Clear and Direct](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/be-clear-and-direct)
- [Anthropic: Use XML Tags](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags)
- [Anthropic: Long Context Tips](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/long-context-tips)
- [The Prompt Report (arXiv)](https://arxiv.org/abs/2406.06608)

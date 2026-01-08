# Skill Documentation

Comprehensive framework for authoring, reviewing, and linting Skills for AI Coding Agents/LLM Shell Agents (Claude Code CLI, Codex CLI, etc.), focusing primarily on `SKILL.md` files.

## What are skills?

Agent Skills are a lightweight, open format for extending AI agent capabilities with specialized knowledge and workflows.

At its core, a skill is a folder containing a `SKILL.md` file. This file includes metadata (`name` and `description`, at minimum) and instructions that tell an agent how to perform a specific task. Skills can also bundle scripts, templates, and reference materials.

```
my-skill/
├── SKILL.md          # Required: instructions + metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

### How skills work

Skills use **progressive disclosure** to manage context efficiently:

1. **Discovery**: At startup, agents load only the name and description of each available skill, just enough to know when it might be relevant.

2. **Activation**: When a task matches a skill's description, the agent reads the full `SKILL.md` instructions into context.

3. **Execution**: The agent follows the instructions, optionally loading referenced files or executing bundled code as needed.

This approach keeps agents fast while giving them access to more context on demand.

## Quick Start

| Task                  | Document                                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Write a skill**     | Start with [how-to-author-review-one-pager.md](how-to-author-review-one-pager.md)                                               |
| **Review a skill**    | Use the reviewer checklist in [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md#reviewer-checklist-body-only) |
| **Lint a skill**      | Run `python skill_lint.py path/to/SKILL.md`                                                                                     |
| **Choose a category** | See decision tree in [skills-categories-guide.md](skills-categories-guide.md#category-selection-decision-tree)                  |

## Document Hierarchy

```
skills-as-prompts-strict-spec.md     <- Source of truth (NORMATIVE)
         |
         +-- skills-semantic-quality-addendum.md   <- Quality layer
         |
         +-- skills-categories-guide.md            <- 13 category definitions
         |
         +-- skills-domain-annexes.md              <- Domain-specific invariants
                    |
                    +-- skills-authoring-review-pipeline.md  <- 6-step workflow
                               |
                               +-- how-to-author-review-one-pager.md  <- Condensed reference
                                          |
                                          +-- skill_lint.py  <- Automated enforcement
```

## Reading Order

**For skill authors:**

1. [how-to-author-review-one-pager.md](how-to-author-review-one-pager.md) — Quick workflow overview
2. [skills-categories-guide.md](skills-categories-guide.md) — Pick your category
3. [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) — Required structure (reference as needed)

**For reviewers:**

1. [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) — Reviewer checklist + FAIL codes
2. [skills-semantic-quality-addendum.md](skills-semantic-quality-addendum.md) — Quality scoring rubric

**For deep understanding:**

1. [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md) — Complete normative requirements
2. [skills-semantic-quality-addendum.md](skills-semantic-quality-addendum.md) — Semantic quality dimensions
3. [skills-categories-guide.md](skills-categories-guide.md) — All 13 categories in detail
4. [skills-domain-annexes.md](skills-domain-annexes.md) — Meta-skills, auditing, pipelines annexes

## File Overview

| File                                                                       | Size | Purpose                                                                                        |
| -------------------------------------------------------------------------- | ---- | ---------------------------------------------------------------------------------------------- |
| [skills-as-prompts-strict-spec.md](skills-as-prompts-strict-spec.md)       | 59KB | **Source of truth** — 8-section content contract, 8 FAIL codes, risk tiers, reviewer checklist |
| [skills-categories-guide.md](skills-categories-guide.md)                   | 67KB | 13 skill categories with intent, contracts, DoD checklists, decision points, failure modes     |
| [skills-semantic-quality-addendum.md](skills-semantic-quality-addendum.md) | 17KB | 5 semantic minimums, 10 quality dimensions, 7 copy-paste templates, scoring rubric             |
| [skills-domain-annexes.md](skills-domain-annexes.md)                       | 14KB | Domain-specific invariants for meta-skills, auditing, and agentic pipelines                    |
| [skill_lint.py](skill_lint.py)                                             | 15KB | Deterministic linter implementing 8 strict FAIL codes                                          |
| [skills-authoring-review-pipeline.md](skills-authoring-review-pipeline.md) | 3KB  | 6-step deterministic authoring procedure                                                       |
| [how-to-author-review-one-pager.md](how-to-author-review-one-pager.md)     | 4KB  | Condensed workflow for authors and reviewers                                                   |

## Key Concepts

### Required Content Areas (8 sections)

Every `SKILL.md` body MUST contain:

1. **When to use** — Trigger conditions
2. **When NOT to use** — Exclusions and misfires
3. **Inputs** — Required context with assumptions declared
4. **Outputs** — Artifacts with objective Definition of Done
5. **Procedure** — Numbered executable steps with STOP gates
6. **Decision points** — At least 2 "If...then...otherwise" branches
7. **Verification** — Quick checks with expected results
8. **Troubleshooting** — Failure modes and recovery

### Automatic FAIL Codes (8 codes)

The linter enforces these — any violation fails review:

| Code                             | Meaning                                               |
| -------------------------------- | ----------------------------------------------------- |
| `FAIL.missing-content-areas`     | Not all 8 required sections present                   |
| `FAIL.no-objective-dod`          | Outputs lack checkable Definition of Done             |
| `FAIL.no-stop-ask`               | No STOP or ask-first gate in procedure                |
| `FAIL.no-quick-check`            | Verification missing quick check with expected result |
| `FAIL.too-few-decision-points`   | Fewer than 2 explicit decision branches               |
| `FAIL.undeclared-assumptions`    | Tool/network/permission assumptions not declared      |
| `FAIL.unsafe-default`            | Risky action without approval gate                    |
| `FAIL.non-operational-procedure` | Procedure not numbered or not executable              |

### Risk Tiers

| Tier       | Characteristics                                            | Review Rigor  |
| ---------- | ---------------------------------------------------------- | ------------- |
| **Low**    | Information/docs output; trivial or easily reversible      | Standard      |
| **Medium** | Creates files, modifies state; bounded and reversible      | Enhanced      |
| **High**   | Security/ops/data/dependencies; costly or hard to rollback | Full scrutiny |

**Rule:** Round up when uncertain. Any mutating step in production = High.

### Skill Categories (13)

| Category                           | Retrieval Key                        | Typical Risk |
| ---------------------------------- | ------------------------------------ | ------------ |
| Meta-skills                        | `category=meta-skills`               | Medium       |
| Auditing & assessment              | `category=auditing-assessment`       | Low-Medium   |
| Agentic workflows                  | `category=agentic-pipelines`         | Medium-High  |
| Implementation playbooks           | `category=implementation-playbooks`  | Medium       |
| Debugging & triage                 | `category=debugging-triage`          | Low-Medium   |
| Refactoring & modernization        | `category=refactoring-modernization` | Medium-High  |
| Testing & quality                  | `category=testing-quality`           | Low-Medium   |
| Documentation & knowledge transfer | `category=documentation-knowledge`   | Low          |
| Build/tooling/CI                   | `category=build-tooling-ci`          | Medium       |
| Integration & evaluation           | `category=integration-evaluation`    | Medium       |
| Security changes                   | `category=security-changes`          | High         |
| Data & migrations                  | `category=data-migrations`           | High         |
| Ops/release/incident runbooks      | `category=ops-release-incident`      | High         |

## Using the Linter

```bash
# Lint a single skill
python skill_lint.py path/to/SKILL.md

# Lint multiple skills
python skill_lint.py skills/*.md

# Lint recursively
python skill_lint.py --recursive .claude/skills/

# JSON output
python skill_lint.py --json path/to/SKILL.md

# Specify domain annex for tighter checks
python skill_lint.py --annex meta path/to/SKILL.md
```

**Exit codes:**

- `0` — All files PASS
- `1` — At least one file has FAIL codes

**Note:** The linter checks structural requirements only. Semantic quality (intent fidelity, constraint completeness) requires human review using [skills-semantic-quality-addendum.md](skills-semantic-quality-addendum.md).

## Retrieval Keys

Each document has stable retrieval keys for machine lookup:

| Document          | Retrieval Key                           |
| ----------------- | --------------------------------------- |
| Strict spec       | `spec=skills-as-prompts-strict`         |
| Semantic addendum | `spec=skills-semantic-quality-addendum` |
| Categories guide  | `spec=skills-categories-guide`          |
| Domain annexes    | `spec=skills-domain-annexes`            |

Section IDs follow the pattern `Section ID: <prefix>.<path>` (e.g., `spec.core-invariants`, `categories.meta-skills`).

## Workflow Summary

```
1. Route    ->  Pick category by dominant failure mode
2. Draft    ->  Use 8-section skeleton from strict spec
3. Tier     ->  Assign risk tier (round up if uncertain)
4. Quality  ->  Apply semantic minimums
5. Tighten  ->  Apply category + domain guidance
6. Lint     ->  Run skill_lint.py (must pass)
7. Review   ->  Human review for semantic quality
8. Ship     ->  PASS / PASS-WITH-NOTES / FAIL
```

## Known Issues

1. **Domain annex coverage** — Domain annexes exist for only 3 of 13 categories (meta-skills, auditing, pipelines)

## Contributing

When modifying these specifications:

1. Maintain Section ID stability (don't rename existing IDs)
2. Update retrieval key tables if adding new sections
3. Keep NORMATIVE vs non-normative markers accurate
4. Test changes against `skill_lint.py`

---
module: readme
status: active
normative: false
authority: supporting
---

# Spec Writing System Design

A spec-writing framework that produces modular, review-ready specifications from approved design documents.

## Reading Order

| # | File | Covers |
|---|------|--------|
| 1 | [foundations.md](foundations.md) | Problem, solution architecture, key architectural decision |
| 2 | [shared-contract.md](shared-contract.md) | `spec.yaml` schema, claims enum, derivation table, frontmatter rules, precedence, boundary rules, cross-ref conventions, failure model, worked example |
| 3 | [spec-writer.md](spec-writer.md) | New skill: purpose, entry conditions, 8-phase workflow, metadata |
| 4 | [review-team-updates.md](review-team-updates.md) | Delta changes to existing spec-review-team skill |
| 5 | [hook.md](hook.md) | PostToolUse nudge: behavior, configuration, script, design decisions |

## Authority Model

The shared contract ([shared-contract.md](shared-contract.md)) defines the `spec.yaml` schema, claims vocabulary, and conventions that both skills conform to. Changes to the shared contract require updating both the spec-writer and review-team skills.

See [shared-contract.md](shared-contract.md) for full details on authorities, claims, precedence, and boundary rules.

## Conventions

- **Cross-references:** Relative markdown links with semantic kebab-case anchors
- **Frontmatter:** Every file carries YAML frontmatter with `module`, `status`, `normative`, and `authority`
- **Normative:** Files marked `normative: true` contain binding design decisions; `normative: false` files are supporting material

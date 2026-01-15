---
name: Plugin Audit
description: This skill validates Claude Code plugins with 50+ rules across 8 categories. Invoked by `/plugin-dev:audit-plugin` command. Use when "auditing a plugin", "validating plugin structure", "checking plugin quality", or "linting plugin".
---

# Plugin Audit

Five-layer validation pipeline for Claude Code plugins. Eliminates false positives through evidence-backed rules and context analysis.

## Quick Start

1. **Run syntax validation** (Layer 1):
   ```bash
   bash $CLAUDE_PLUGIN_ROOT/skills/plugin-audit/scripts/check-syntax.sh <plugin-path>
   ```

2. **Run structure validation** (Layer 2):
   ```bash
   bash $CLAUDE_PLUGIN_ROOT/skills/plugin-audit/scripts/check-structure.sh <plugin-path>
   ```

3. **Apply context analysis** (Layer 3) - Filter false positives using `references/context-patterns.md`

4. **Report findings** with confidence levels and rule provenance

**If scripts unavailable:** Perform manual checks — verify JSON syntax with `jq`, check required fields exist, scan for hardcoded paths using Grep.

## Pipeline Overview

| Layer | Question | Method |
|-------|----------|--------|
| 1. Syntax | Valid JSON/YAML? | Scripts (deterministic) |
| 2. Structure | Follows rules? | Scripts + spec |
| 3. Context | Real issue or false positive? | Context patterns |
| 4. Quality | Good content? | Claude analysis (--deep) |
| 5. Cross-component | Consistent overall? | Claude analysis |

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **CRITICAL** | Plugin won't load or function | Must fix before plugin works |
| **WARNING** | Quality/reliability issues | Should fix for production |
| **INFO** | Improvement suggestions | Consider for better UX |

## Key Rules by Category

### Structure (S)
| Rule | Severity | Check |
|------|----------|-------|
| S-MANIFEST-001 | CRITICAL | `.claude-plugin/plugin.json` exists and valid |
| S-NAME-001 | CRITICAL | `name` field exists in manifest |
| S-NAME-002 | WARNING | Name uses kebab-case |
| S-VERSION-001 | INFO | `version` field exists |

### Commands (C)
| Rule | Severity | Check |
|------|----------|-------|
| C-NAME-001 | INFO | `name` is optional (derived from filename) |
| C-DESC-001 | WARNING | `description` field exists |
| C-TOOLS-001 | WARNING | `allowed-tools` restricts capabilities |
| C-BODY-001 | WARNING | Instructions written FOR Claude |

### Skills (SK)
| Rule | Severity | Check |
|------|----------|-------|
| SK-NAME-001 | CRITICAL | `name` field required |
| SK-DESC-001 | CRITICAL | `description` field required |
| SK-DESC-002 | WARNING | Description has quoted trigger phrases |
| SK-DESC-003 | WARNING | Description uses third-person |
| SK-BODY-001 | WARNING | Body uses imperative form |
| SK-BODY-002 | WARNING | Body under 3000 words |

### Agents (A)
| Rule | Severity | Check |
|------|----------|-------|
| A-DESC-001 | CRITICAL | `description` field required |
| A-TOOLS-001 | CRITICAL | `tools` array required |
| A-BODY-001 | WARNING | Has `<example>` blocks |
| A-BODY-002 | WARNING | Substantive system prompt (50+ words) |

### Hooks (H)
| Rule | Severity | Check |
|------|----------|-------|
| H-EVENT-001 | CRITICAL | Valid event name |
| H-FIELD-001 | CRITICAL | `matcher` field exists |
| H-FIELD-002 | CRITICAL | `type` field exists (command/prompt) |
| H-PATH-001 | WARNING | Paths use `$CLAUDE_PLUGIN_ROOT` |
| H-TIMEOUT-001 | WARNING | Explicit `timeout` field |

### Security (SEC)
| Rule | Severity | Check |
|------|----------|-------|
| SEC-PATH-001 | CRITICAL | No hardcoded absolute paths |
| SEC-PATH-002 | CRITICAL | No `~/` in JSON files |
| SEC-CRED-001 | CRITICAL | No hardcoded credentials |
| SEC-CMD-001 | WARNING | Dangerous commands have safeguards |

### Cross-Component (X)
| Rule | Severity | Check |
|------|----------|-------|
| X-FILE-001 | WARNING | Referenced files exist |
| X-DOC-001 | INFO | Components documented |

## Important Distinctions

Before reporting issues, verify against actual requirements:

- **Commands:** `name` field is NOT required (filename is source of truth)
- **Skills:** `name` and `description` ARE required (unlike commands)
- **Agents:** `description` and `tools` ARE required
- **Paths:** Must use `$CLAUDE_PLUGIN_ROOT` for portability

## Context Filtering

Before reporting, check if issue is a false positive:

1. **Example sections** - Paths under `## Examples` or in code blocks are teaching examples
2. **Security blocks** - Paths in `permissionDecision: deny` blocks are features, not vulnerabilities
3. **Explicit markers** - `<!-- audit:example-section -->` means skip

See `references/context-patterns.md` for detection patterns.

## Report Format

```markdown
# Plugin Audit Report: {name}

## Summary
| Severity | Confirmed | Needs Review | Skipped |
|----------|-----------|--------------|---------|

## Confirmed Issues
[High-confidence issues with rule ID, file:line, fix]

## Needs Review
[Medium-confidence issues]

## Skipped (Context-Filtered)
[Issues filtered with reasoning]
```

## References

- `specification/audit-spec.yaml` - All rules with evidence
- `references/context-patterns.md` - False positive detection
- `references/rule-reference.md` - Rule explanations
- `tests/baseline-scenarios.md` - Test scenarios

## Related

- `/plugin-dev:audit-plugin` - Command to run audit
- `/plugin-dev:fix-plugin` - Interactive repair session
- `plugin-validator` agent - Proactive validation

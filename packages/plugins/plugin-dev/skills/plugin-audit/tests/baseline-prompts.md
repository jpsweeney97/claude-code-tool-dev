# Baseline Test Prompts

Run these in a FRESH Claude Code session WITHOUT plugin-dev loaded.

## How to Run

1. Open a new terminal
2. Start Claude Code in a directory that doesn't have plugin-dev: `cd /tmp && claude`
3. Run each prompt below
4. Copy Claude's response to the corresponding section in `baseline-scenarios.md`

---

## Scenario A: Example Path Detection

```
Audit the plugin at ~/.claude/plugins/plugin-dev. Check if all file references in skills exist.
```

---

## Scenario B: Security Context Detection

```
Check the plugin at ~/.claude/plugins/plugin-dev for hardcoded /etc/ or /sys/ paths. Report any security issues.
```

---

## Scenario C: Command Frontmatter Validation

```
Validate all commands in ~/.claude/plugins/plugin-dev have correct frontmatter according to Claude Code documentation.
```

---

## Scenario D: Cross-Component Consistency

```
Check if all components in ~/.claude/plugins/plugin-dev are properly documented in the README.
```

---

## After Testing

Fill in the `[TO BE FILLED AFTER TESTING]` sections in `baseline-scenarios.md` with:
1. Claude's response (summary)
2. False positives identified
3. Rationalizations Claude used

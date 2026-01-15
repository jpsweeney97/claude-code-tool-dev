# Baseline Test Scenarios

These scenarios document Claude's default behavior WITHOUT the redesigned skill loaded.
Run these BEFORE writing SKILL.md content to capture baseline failures.

## Purpose

TDD for skills: We need to know what Claude gets wrong by default so we can write skill content that specifically addresses those gaps.

## Test Protocol

1. Start fresh Claude Code session (no plugin-audit skill loaded)
2. Run each scenario prompt
3. Document Claude's response
4. Identify false positives and incorrect behavior
5. Use failures to guide SKILL.md content

---

## Scenario A: Example Path Detection

**Prompt:**
```
Audit the plugin at ~/.claude/plugins/plugin-dev. Check if all file references in skills exist.
```

**Expected baseline behavior:**
- Flags paths in example sections as "missing files"
- Doesn't distinguish teaching examples from real references
- May report 15-20+ false positives for example paths

**Target behavior (with skill):**
- Recognizes example sections (## Examples, code blocks)
- Skips file-existence checks for example paths
- Reports only genuinely missing references

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Scenario B: Security Context Detection

**Prompt:**
```
Check the plugin at ~/.claude/plugins/plugin-dev for hardcoded /etc/ or /sys/ paths. Report any security issues.
```

**Expected baseline behavior:**
- Flags ALL occurrences of /etc/, /sys/ as vulnerabilities
- Doesn't understand deny-block context
- Reports security hooks as security problems

**Target behavior (with skill):**
- Analyzes context around path references
- Recognizes deny-block patterns (permissionDecision: deny, exit 1/2)
- Reports paths being ACCESSED as issues, skips paths being BLOCKED

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Scenario C: Command Frontmatter Validation

**Prompt:**
```
Validate all commands in ~/.claude/plugins/plugin-dev have correct frontmatter according to Claude Code documentation.
```

**Expected baseline behavior:**
- May assume `name` field is required (it's not)
- May flag missing `name` as CRITICAL error
- Relies on assumptions rather than verified documentation

**Target behavior (with skill):**
- Loads specification with evidence-backed rules
- Knows `name` is optional (filename is source of truth)
- Only flags actually-required fields as CRITICAL

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Scenario D: Cross-Component Consistency

**Prompt:**
```
Check if all components in ~/.claude/plugins/plugin-dev are properly documented in the README.
```

**Expected baseline behavior:**
- May miss components or have false matches
- Doesn't understand plugin structure conventions
- Inconsistent analysis

**Target behavior (with skill):**
- Systematically discovers all components
- Checks README against actual component list
- Reports specific missing documentation

**Baseline result:** [TO BE FILLED AFTER TESTING]

---

## Running Baseline Tests

### Setup

1. Ensure plugin-audit skill is NOT loaded
2. Use a fresh Claude Code session
3. Copy prompts exactly as written

### Documenting Results

For each scenario, record:
1. Claude's full response
2. List of issues reported
3. Which issues are false positives
4. Any correct findings
5. Rationalizations Claude used for incorrect findings

### Using Results

After baseline testing:
1. Identify common failure patterns
2. Write SKILL.md content addressing each pattern
3. Re-run scenarios with skill loaded
4. Iterate until all false positives eliminated

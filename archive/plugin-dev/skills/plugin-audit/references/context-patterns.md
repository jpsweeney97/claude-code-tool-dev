# Context Patterns Reference

Reference for Layer 3 context analysis in the plugin audit pipeline. This document explains how to detect false positives by analyzing surrounding context.

## Purpose

Many audit rules use pattern matching that can produce false positives. Layer 3 context analysis filters these by examining:

1. **Example indicators** - Is this content teaching/documentation?
2. **Security deny blocks** - Is this a security CONTROL, not a vulnerability?
3. **Confidence scoring** - How certain are we this is a real issue?

---

## 1. Example Indicators

Content within examples, documentation, or teaching material should not trigger most audit rules. A hardcoded path in a "Bad Example" block is intentional demonstration, not a real vulnerability.

### Explicit Markers

These markers signal that surrounding content is example/demo material:

| Marker | Usage |
|--------|-------|
| `<!-- audit:example-section -->` | Audit-specific exemption marker |
| `<!-- example -->` ... `<!-- /example -->` | Generic example block markers |
| `<example>` ... `</example>` | XML-style example blocks |

**Example:**
```markdown
<!-- audit:example-section -->
Here is a bad path that should NOT be flagged:
"/Users/john/plugins/my-plugin/scripts/run.sh"
<!-- /audit:example-section -->
```

### Section Headers

Content under these headers is likely example/demonstration:

```markdown
## Examples
### Usage Examples
## Example Usage
### Code Examples
## Demo
### Sample Code
```

**Detection pattern:**
```regex
^#{1,3}\s*(Examples?|Usage Examples?|Demo|Sample\s+Code)
```

### Inline Markers

Text immediately preceding content that indicates it's an example:

| Pattern | Context |
|---------|---------|
| `**Example:**` | Bold example label |
| `*Example:*` | Italic example label |
| `(e.g., ...)` | Inline example notation |
| `for example:` | Prose example introduction |
| `such as:` | List introduction |
| `like this:` | Demonstration |

**Detection pattern:**
```regex
(\*\*Example:\*\*|Example:|e\.g\.,|for example:|such as:|like this:)
```

### Quoted User Speech

Content showing example user prompts should not be validated as real code:

| Pattern | Purpose |
|---------|---------|
| `User: "..."` | Example user input |
| `User says:` | Narrative user speech |
| `When user asks:` | Conditional user prompts |

**Exemption:** File paths and code in quoted user speech are examples.

**Detection pattern:**
```regex
(User: "[^"]*"|User says:|When user asks:)
```

### Code Blocks

Content between triple backticks is often illustrative:

```
```json
{
  "command": "/Users/example/path"  // This is in a code block
}
```
```

**Important:** Not all code blocks are exempt. Configuration examples that will be copy-pasted need validation. The exemption applies when:
- The code block is under an "Examples" section header
- The code block follows anti-pattern markers (see below)
- The code block is explicitly marked as demonstration

### Anti-Pattern Documentation

Documentation that shows what NOT to do should not trigger security rules:

| Pattern | Description |
|---------|-------------|
| `Bad:` / `BAD:` | Labels bad examples |
| `DON'T:` / `Don't:` | Prohibition markers |
| `WRONG:` / `Wrong:` | Error demonstration |
| `example of what NOT` | Explicit anti-pattern |
| `Avoid:` / `AVOID:` | Discouragement markers |
| `❌` | Cross mark emoji indicating bad example |

**Visual markers:**
- Cross mark emoji in text indicates bad examples
- Struck-through text indicates deprecated/wrong approaches

**Detection pattern:**
```regex
(Bad:|BAD:|DON'T:|Don't:|WRONG:|Wrong:|Avoid:|AVOID:|example of what NOT|❌)
```

**Example context:**
```markdown
**Bad:**
```json
"/Users/john/hardcoded/path"
```

**Good:**
```json
"$CLAUDE_PLUGIN_ROOT/relative/path"
```
```

In this case, the "Bad:" path should NOT be flagged as SEC-PATH-001.

---

## 2. Security Deny Block Patterns

Some patterns look like security vulnerabilities but are actually security CONTROLS. Paths in deny lists are intentionally restrictive - they block access rather than grant it.

### Hook Deny Outputs

Hooks that output deny/block decisions are security features:

| Pattern | Description |
|---------|-------------|
| `permissionDecision: deny` | Hook permission denial |
| `"decision": "block"` | JSON block decision |
| `"decision": "deny"` | JSON deny decision |
| `"allow": false` | Explicit disallow |

**Example (this is a security feature, NOT a vulnerability):**
```json
{
  "permissionDecision": "deny",
  "permissionMessage": "Path not in allowed list"
}
```

### Exit Codes in Conditionals

Scripts that exit with non-zero codes after security checks are blocking access:

```bash
# This BLOCKS access - it's a security control
if [[ "$path" == *"/etc/"* ]]; then
  echo "Access denied: system path" >&2
  exit 1
fi
```

**Detection pattern:**
```regex
exit\s+[12]
```

When `exit 1` or `exit 2` follows an `if` statement checking paths/permissions, this is a deny block, not a vulnerability.

### Deny List Definitions

Variables and structures that define what to BLOCK:

| Variable Pattern | Purpose |
|------------------|---------|
| `deny`, `denied` | Deny list |
| `block`, `blocked` | Block list |
| `blacklist` | Legacy deny term |
| `denyOnly` | Claude Code sandbox deny |
| `denyWithinAllow` | Claude Code selective deny |
| `blocked_domains` | Domain blocking |

**Example (Claude Code sandbox config):**
```json
{
  "permissions": {
    "deny": [
      "~/.ssh",
      "~/.aws",
      "**/*.pem"
    ]
  }
}
```

The paths in this `deny` block are security controls - they PREVENT access to sensitive locations. These should NOT be flagged as SEC-PATH-001 violations.

### Security Context Detection

When analyzing a potential SEC-PATH-001 violation, check if the path appears in:

1. **Deny block context:**
   - Key contains: `deny`, `block`, `blacklist`, `forbidden`
   - Parent key contains: `permissions`, `sandbox`, `security`

2. **Conditional blocking:**
   - Followed by: `exit 1`, `exit 2`, `return 1`
   - Inside: `if ... deny` or `if ... block` patterns

3. **Access control lists:**
   - Array under: `denyOnly`, `denyWithinAllow`, `blocked_domains`

---

## 3. Confidence Scoring

Not all pattern matches have the same certainty. Confidence scoring helps prioritize issues and determine when to request human verification.

### Severity-Based Thresholds

| Severity | Minimum Confidence | Action |
|----------|-------------------|--------|
| CRITICAL | >= 0.7 | Report always |
| CRITICAL | 0.5 - 0.7 | Request LLM verification |
| CRITICAL | < 0.5 | Suppress, log for review |
| WARNING | >= 0.5 | Report by default |
| WARNING | < 0.5 | Report with `--verbose` only |
| INFO | >= 0.3 | Report by default |
| INFO | < 0.3 | Suppress |

### Confidence Assignments by Check Type

**High Confidence (0.9-1.0)** - Deterministic checks:
- Syntax errors (JSON/YAML parse failure)
- Missing required fields (documented requirements)
- Invalid event names (enumerated valid values)
- File not found (existence check)

**Medium Confidence (0.7-0.8)** - Heuristic checks:
- Hardcoded paths (may be in documentation)
- Weak trigger phrases (subjective assessment)
- Missing recommended fields (best practice)
- Style violations (conventions, not rules)

**Low Confidence (0.5-0.6)** - Context-dependent:
- Second-person language (may be in quoted speech)
- Missing optional fields (purely optional)
- Length violations (soft recommendations)

### LLM Verification

For uncertain CRITICAL issues (confidence 0.5-0.7), request LLM verification:

```markdown
## LLM Verification Request

**Issue:** Potential SEC-PATH-001 (hardcoded absolute path)
**File:** hooks/hooks.json
**Line:** 15
**Content:** "/Users/john/plugins/data"
**Context:** Appears in "denyOnly" array

**Question:** Is this a security vulnerability or a security control?

**Analysis hints:**
- Check if path is in a deny/block list
- Check if surrounding code exits/returns on match
- Check if this is documentation/example
```

### Combining Patterns

When multiple context patterns apply, combine their effects:

1. **Exemption stack:** Each applicable exemption REDUCES confidence
   - In example block: -0.3
   - Under anti-pattern header: -0.4
   - In deny list context: -0.5 (often complete exemption)

2. **Reinforcement stack:** Multiple indicators INCREASE confidence
   - Pattern appears in multiple files: +0.1
   - No exemptions apply: base confidence
   - Pattern matches multiple detection rules: +0.1

**Example calculation:**
```
Base confidence for SEC-PATH-001: 0.8
Path appears under "Bad:" marker: -0.4
Path is in code block: -0.1
Final confidence: 0.3 (suppress for CRITICAL)
```

---

## Pattern Application Order

When analyzing a potential issue:

1. **Match detection pattern** - Does the content match a rule's detection pattern?
2. **Check immediate context** - Look at surrounding 5 lines
3. **Check section context** - What header is this content under?
4. **Check file context** - Is this file primarily documentation?
5. **Apply exemptions** - Do any context patterns apply?
6. **Calculate confidence** - Combine base confidence with adjustments
7. **Apply threshold** - Does final confidence meet severity threshold?

---

## Quick Reference

### Exempt This Content

```markdown
<!-- audit:example-section -->
Content here is exempt from security rules.
<!-- /audit:example-section -->
```

### Patterns That Indicate Exemption

```regex
# Anti-pattern markers
(Bad:|BAD:|DON'T:|WRONG:|Avoid:|example of what NOT)

# Section headers
^#{1,3}\s*Examples?

# Deny block indicators
(denyOnly|denyWithinAllow|blocked_domains|"deny"|"block")

# Exit codes after conditionals
if\s.*;\s*then.*exit\s+[12]
```

### Confidence Quick Reference

| Finding | Base Confidence | Common Adjustments |
|---------|----------------|-------------------|
| JSON syntax error | 1.0 | None |
| Missing required field | 0.95 | None |
| Hardcoded path | 0.8 | Example: -0.3, Deny block: -0.5 |
| Weak trigger | 0.7 | None |
| Second person | 0.6 | Quoted speech: -0.4 |
| Missing optional | 0.5 | None |

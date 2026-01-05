---
name: optimize
description: Use when /optimize is run or proactive suggestions are shown - guides interactive review of configuration optimization suggestions
---

# Configuration Optimization Skill

## When to Use

- User runs `/optimize` command
- Proactive suggestions appear (stop hook)
- User asks about config optimization

## Process

### 1. Run Analysis

```bash
python3 ~/.claude/scripts/optimize/optimizer.py --json
```

Parse the JSON output to get suggestions.

### 2. Present Summary

Show overview:
- Total suggestions found
- Breakdown by type (permission, performance, workflow)
- Highlight high-confidence items (≥85%)

### 3. Interactive Review

For each suggestion, present:

```
## [Type] Title
Confidence: X% | Severity: Y

Description of the issue...

**Recommendation:** What to do

**Actions:**
1. Apply - Implement this suggestion
2. Dismiss (7 days) - Hide temporarily
3. Skip - Review later
4. Details - Show evidence
```

### 4. Apply Suggestions

When user chooses "Apply":

**For permission suggestions:**
- Read current settings.json
- Add/modify the permissions.allow or permissions.deny array
- Show the change before applying
- Write updated settings.json

**For performance suggestions:**
- These are typically informational
- Provide guidance on model selection
- Link to relevant documentation

**For workflow suggestions:**
- Offer to create a slash command or skill
- Provide template for automation

### 5. Track State

After each action:
- Update `~/.claude/.audit/optimize-state.json`
- Mark suggestions as applied or dismissed
- Record timestamps

## Important Notes

- Always show changes before applying
- Require confirmation for settings modifications
- Respect user's suppress preferences
- Don't repeatedly show dismissed suggestions

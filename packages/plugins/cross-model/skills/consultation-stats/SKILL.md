---
name: consultation-stats
description: Presents analytics and metrics for cross-model consultations and dialogues. Reads the event log, computes convergence rates, posture effectiveness, failure counts, and context quality metrics. Use when user says "consultation stats", "codex stats", "how are my consultations doing", "consultation metrics", "dialogue analytics", or asks about consultation performance, convergence rates, or posture effectiveness.
---

# Consultation Stats

Present analytics for cross-model consultations and dialogues from the event log at `~/.claude/.codex-events.jsonl`.

## Instructions

### Step 1: Determine parameters

Default: full report for the last 30 days.

If the user requests a specific time period or report focus, adjust accordingly:

| User says | Parameter |
|-----------|-----------|
| "last week", "past 7 days" | `--period 7` |
| "last month", "past 30 days" | `--period 30` (default) |
| "all time", "everything" | `--period 0` |
| "just security", "credential blocks" | `--type security` |
| "just dialogues", "convergence" | `--type dialogue` |
| "just consultations" | `--type consultation` |

If no specific request, use defaults: `--period 30 --type all`.

### Step 2: Run the computation script

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/compute_stats.py" --period 30 --type all --json
```

The script reads the event log, computes metrics, and outputs a JSON report to stdout.

**If the script exits non-zero or the event log doesn't exist:** Report "No consultation data found. Run /codex or /dialogue to start generating analytics." Do not attempt to compute stats manually.

### Step 3: Present the report

Parse the JSON output and present as a formatted markdown report. Include all sections the script provides. Use the section ordering from the script output — do not reorder.

**Zero/non-zero signals only.** Highlight when:
- A count is zero where the user likely expects data (e.g., "0 dialogues in the last 30 days")
- A count is non-zero where zero is ideal (e.g., "3 credential blocks detected")
- A category is entirely absent (e.g., "No scout activity recorded")

Do not interpret numeric values (e.g., do not say "convergence rate is low" or "this is a good score"). Present the data and let the user draw conclusions.

## Examples

### Health check (default)

**User:** `/consultation-stats`

**Actions:**
1. Run `compute_stats.py --period 30 --type all --json`
2. Format JSON output as full report

**Result:** 30-day report with all sections: usage overview, dialogue quality, context quality, security.

### Scoped request

**User:** "Show me consultation stats for the last week, just dialogues"

**Actions:**
1. Run `compute_stats.py --period 7 --type dialogue --json`
2. Format JSON output, dialogue sections only

### Empty event log

**User:** `/consultation-stats`

**Result:** "No consultation data found. Run /codex or /dialogue to start generating analytics."

## Troubleshooting

### Script not found

**Cause:** Plugin root path incorrect or plugin not installed.

**Fix:** Verify the cross-model plugin is installed. The script is at `${CLAUDE_PLUGIN_ROOT}/scripts/compute_stats.py`.

### Malformed events in log

**Cause:** Events from older plugin versions or manual log edits.

**Fix:** The script skips malformed lines and reports the skip count. If skip count is high, the event log may be corrupted. The user can inspect it at `~/.claude/.codex-events.jsonl`.

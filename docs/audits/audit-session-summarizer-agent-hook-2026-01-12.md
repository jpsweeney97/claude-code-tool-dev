# Audit: session-summarizer Agent Hook Design

**Date:** 2026-01-12
**Updated:** 2026-01-12 (revised after documentation clarification)
**Target:** Proposed design (conversation, not file)
**Type:** Plugin (agent + hook configuration)
**Verdict:** Needs Work

## Summary

The design proposes using an agent hook at SessionStart to process pending session summaries. The core architecture is sound and agent hooks ARE confirmed to work for all events including SessionStart. The **primary issue** is a race condition with the existing MCP server's pending file processing. Several minor risk issues around error handling and enforcement mechanisms also need attention.

## Findings

### ~~1. Agent Hooks at SessionStart: Undocumented Behavior~~ [INVALIDATED]

- **Status:** This finding has been **invalidated** based on documentation clarification.
- **Correction:** Plugin hooks documentation confirms all three hook types (command, prompt, agent) are available for all 12 events including SessionStart.
- **Evidence:** "Hook types: command, prompt, agent" listed under all available events including SessionStart.
- **Original Severity:** Major → **N/A**

### 1. Race Condition with MCP Server Pending Processing

- **What:** The session-log plugin already has `pending.py` that processes pending files when the MCP server starts. Adding an agent hook creates two competing processors.
- **Why it matters:** Both could try to process the same pending file simultaneously, leading to duplicate summaries, file conflicts, or data corruption.
- **Evidence:** From `session_log/pending.py` existence and the MCP server architecture described in earlier conversation.
- **Severity:** Major
- **Suggestion:** Choose one processing location. Either: (a) Remove MCP server pending processing and rely solely on agent hook, OR (b) Keep MCP server processing and skip agent hook. Don't have both.

### 2. "Max 3 Sessions" Not Enforceable

- **What:** The agent instructions say "Maximum 3 sessions per invocation to limit startup time" but this is natural language guidance with no enforcement mechanism.
- **Why it matters:** The agent may process all pending files (causing slow startup) or none (if it misinterprets), or a random number.
- **Evidence:** "Maximum 3 sessions per invocation to limit startup time" in agent prompt
- **Severity:** Minor
- **Suggestion:** Add explicit enforcement: either (a) have a command hook pre-filter files and pass only 3 to the agent, or (b) accept that the agent might process more/fewer and adjust timeout accordingly.

### 3. Timeout Failure Mode Unspecified

- **What:** The design sets `timeout: 60` but doesn't specify what happens if timeout is hit mid-processing.
- **Why it matters:** Partial state: some files processed, some not. No rollback mechanism. Pending files may be deleted but summaries not written.
- **Evidence:** No mention of timeout handling in agent definition
- **Severity:** Minor
- **Suggestion:** Make processing atomic per file: only delete pending file AFTER summary is successfully written. If timeout hits, unprocessed files remain for next session.

### 4. String Replacement Fragility

- **What:** The agent updates summaries by replacing the literal string `"- Session summary pending analysis"`. Any variation breaks this.
- **Why it matters:** If the placeholder text changes in `summarizer.py`, all future sessions fail to update. Silent failure.
- **Evidence:** "Replace this line in the markdown file: `- Session summary pending analysis`"
- **Severity:** Minor
- **Suggestion:** Use a more robust marker like `<!-- PENDING_SUMMARY -->` that's unlikely to change accidentally, or have the agent read and rewrite the entire Accomplished section.

### 5. Agent Definition Location Ambiguity

- **What:** The hook references `"agent": "session-summarizer"` but agent discovery in plugins may not work as expected.
- **Why it matters:** If the plugin's `agents/` directory isn't in the agent search path when the hook fires, the agent won't be found.
- **Evidence:** From agents-overview.md: "Priority: 1 Session > 2 Project > 3 User > 4 Plugin". Plugin agents are lowest priority and load behavior at SessionStart is unclear.
- **Severity:** Minor
- **Suggestion:** Verify that plugin agents are loaded before SessionStart hooks fire. If not, the agent definition may need to be in `~/.claude/agents/` instead.

### 6. No Verification of Summary Quality

- **What:** The design trusts the agent to generate good summaries with no verification step.
- **Why it matters:** Haiku might generate poor summaries, especially for complex sessions. No way to detect or recover from bad output.
- **Evidence:** No PostToolUse validation or output checking in the design
- **Severity:** Minor
- **Suggestion:** Accept this risk for v1 (summaries are non-critical). Consider adding a quality check in future versions.

## What's Working

- **Correct use of plugin-only features:** Properly leverages agent hooks being plugin-only by placing in plugin context
- **bypassPermissions is valid:** Correctly uses a documented permissionMode value for trusted automation
- **Lazy processing pattern:** Processing previous sessions at next startup is an elegant solution to the "hook must be fast" constraint
- **Model selection:** Using Haiku for simple summarization tasks is cost-effective and fast
- **Deferred indexing architecture:** Builds on existing pending file infrastructure rather than creating new patterns

## Recommendations

1. **Resolve race condition (Required):** Choose one processing location:
   - **Option A (Recommended):** Remove MCP server pending processing, rely solely on agent hook. The agent hook is the cleaner architecture since it has dedicated model allocation at session start.
   - **Option B:** Keep MCP server processing, skip agent hook entirely. Simpler but summaries generated lazily on first tool call.
   - **Option C:** Add lock file coordination. More complex, allows both to coexist.

2. **Add atomic file handling:** Delete pending files only after successful summary write to handle timeout gracefully.

3. **Use robust markers:** Replace placeholder string with comment-based marker like `<!-- PENDING_SUMMARY -->`.

4. **Verify plugin agent loading:** Confirm plugin agents are discoverable when SessionStart hooks fire.

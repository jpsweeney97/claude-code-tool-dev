# Failure Patterns Reference

Operational reference for failure modes, degraded mode behavior, troubleshooting, and recovery procedures. SKILL.md's failure mode table defines what to detect and how to respond at a high level. This file provides the operational detail.

## Degraded Mode

Triggered when DISCOVERY finds zero parseable frontmatter across all spec files.

**What still works:**
- File discovery and path-based classification
- Core team spawning (Lead + Architecture + Completeness reviewers)
- All review phases (3A–3C, 4, 5)
- Synthesis and final report

**What is disabled:**
1. Redirect gate — always runs full team regardless of scope
2. Authority-derived specialist spawning — core team only, no authority-based additions
3. Authority-based contradiction adjudication — escalate all contradictions as ambiguity

**Phase 3A behavior:** Produces zero mechanical validation results. Proceed directly to cluster routing — do not wait or retry.

**Source authority:** All files get `source_authority = unknown`.

**User communication:** "No frontmatter detected on any spec file. Proceeding in degraded mode: all files classified by path heuristics, authority-based features disabled. Consider running spec-modulator to add frontmatter."

## Troubleshooting Decision Trees

### "TeamCreate failed"

1. Is `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set? → Phase 0 preflight should have caught this. If not caught: stop, report the missing env var to the user. Do not attempt to continue without teams enabled.
2. Does an existing team from a prior failed run exist? → Clean up with TeamDelete first, then retry TeamCreate.
3. Is this a nested team attempt (Lead trying to create a sub-team from within a teammate)? → Cannot create teams within teammates. Restructure: Lead spawns all agents at Phase 0 before the team context restricts tool access.
4. None of the above: report the raw error message to the user and hard stop. Do not retry blindly — repeated TeamCreate failures can leave orphaned state.

### "Reviewer not producing output"

1. Has the findings file been created in `.review-workspace/findings/`? → Missing file = reviewer failed silently. Treat as reviewer failure and proceed without that reviewer's input.
2. Has 5 minutes elapsed since spawn? → Apply wall-clock timeout. Record the timeout in the synthesis ledger under `reviewer_failures`. Do not wait indefinitely for a stuck reviewer.
3. Is the reviewer stuck in a tool permission prompt? → User must approve manually. Do not attempt to proceed without that reviewer's output until the permission is resolved or the user cancels.

### "Findings file is empty or prose-only"

1. Lead normalizes to schema during SYNTHESIS canonicalization — attempt normalization before declaring failure.
2. Increment `normalization_rewrites` counter in the ledger for each repaired finding.
3. If the entire file is prose with no discernible findings structure: treat as reviewer failure. Do not attempt to extract findings from narrative text — the schema contract requires structured output.

### "Stale workspace from previous run"

1. `.review-workspace/` exists at DISCOVERY start.
2. Warn user explicitly. Offer exactly three options:
   - (a) Archive existing workspace to `.review-workspace.bak/` and start fresh
   - (b) Remove existing workspace and start clean
   - (c) Abort and let user inspect the prior workspace manually
3. Wait for user selection. Do NOT silently overwrite — silently overwriting destroys prior review artifacts without user consent.
4. If user selects (a) or (b): proceed after confirming the action completed successfully.

### "SendMessage delivery appears to fail"

1. Confirm the target agent's `name` field matches exactly (case-sensitive). Using UUID instead of name causes silent delivery failure.
2. Confirm the recipient agent is still alive — if the teammate failed, messages queue with no consumer.
3. If both check out: retry once. If still no acknowledgment within 2 minutes, treat as reviewer failure.

## Recovery Procedures

### Interrupted during Phase 3 (Cluster Analysis)

- Clusters may be partially analyzed. No findings files exist yet.
- Clean state: remove `.review-workspace/` entirely and re-run from Phase 0.
- Partial cluster analysis cannot be safely resumed — re-run is faster than auditing partial state.

### Interrupted during Phase 4 (Review)

- Workspace may contain partial findings files.
- User can inspect `.review-workspace/findings/` to see which reviewers completed.
- Shut down any orphaned teammates before re-running (see orphaned teammates note below).
- Re-run from Phase 0 — partial findings files from a prior run are not safely resumable because the cluster assignment may differ.

### Interrupted during Phase 5 (Synthesis)

- Ledger may be partially written.
- Re-running synthesis from scratch is safer than attempting to resume from a partial ledger.
- Delete `.review-workspace/synthesis/` before re-running, or use the workspace clean-up flow (stale workspace options above).

### Orphaned teammates

TeamDelete requires all teammates to be shut down first. If teammates are orphaned (session interrupted mid-run), they cannot be cleanly deleted via TeamDelete. Recovery: restart the Claude Code session to clear orphaned agents, then re-run from Phase 0. Do not attempt to reuse an orphaned team — spawn a fresh one.

## Common Implementation Mistakes

| Mistake | Effect | Correct Approach |
|---|---|---|
| Using `Agent` without `team_name` | Isolated subagent — no messaging, no tasks, no idle detection | Always pass `team_name` when spawning reviewers |
| Using agent UUID instead of `name` for SendMessage | Delivery fails silently | Use the agent's `name` field, not its UUID |
| Starting lead analysis before all reviewers are spawned | Spec violation — Phase 4 step 7 requires all agents running first | Spawn all reviewers, confirm all active, then begin |
| Embedding packet content in spawn prompt instead of pointing to file | Destructive compression of packet data | Write packet to file; pass file path in spawn prompt |
| Writing a prompt-based TeammateIdle hook | Will NOT fire — idle hooks are command hooks only | Use wall-clock timeout polling instead |
| Omitting `.gitignore` entry for `.review-workspace/` | Review artifacts committed accidentally | Add `.review-workspace/` to `.gitignore` before first run |
| Retrying TeamCreate without TeamDelete | Stale team name collision, unpredictable behavior | Always TeamDelete before retrying TeamCreate |
| Proceeding with synthesis on empty findings | Ledger based on no evidence, misleading report | Declare reviewer failure in ledger, note absence explicitly |
| Silently skipping a reviewer timeout | Missing coverage with no record | Always log timeouts in the synthesis ledger under `reviewer_failures` |

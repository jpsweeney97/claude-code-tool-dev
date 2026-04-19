"""Execution-turn prompt construction.

Execution turns dispatch real work in an isolated worktree. The prompt conveys
the objective and scope. Unlike advisory turns, execution turns do NOT use a
structured output schema — the "result" is the worktree state plus any server
requests captured during the turn.
"""

from __future__ import annotations


def build_execution_turn_text(
    *,
    objective: str,
    worktree_path: str,
) -> str:
    """Build the text input for an execution turn's ``turn/start``.

    The prompt instructs the execution agent to work within the isolated
    worktree boundary. No structured output schema is enforced — the agent
    operates freely within the sandbox constraints.
    """
    return (
        "You are working in an isolated worktree. Your workspace is:\n"
        f"  {worktree_path}\n\n"
        "Objective:\n"
        f"  {objective}\n\n"
        "Work within the worktree boundary. Commands that require approval "
        "will be escalated to the caller for review."
    )

# Troubleshooting

Common issues encountered during skill reviews and how to resolve them.

## Review completed in one pass

**Cause:** Pass 1 is always 100% yield — cannot exit after one pass.

**Next steps:** Run at least one more pass. If truly no new findings, Yield% will drop below threshold naturally.

## Most dimensions marked N/A

**Cause:** Over-aggressive skipping. D1-D7 cannot be N/A.

**Next steps:** Revisit N/A justifications. Apply the skeptical reviewer test: "Would someone else accept this rationale?"

## "No issues found" but skill feels off

**Cause:** Checking presence instead of quality, or insufficient disconfirmation.

**Next steps:** Re-run with explicit quality questions per dimension. Apply Adversarial Pass lenses even if loop found nothing.

## Fixes keep conflicting with each other

**Cause:** Skill has structural problems that can't be resolved with targeted edits.

**Next steps:** Escalate: "Skill may need fundamental rethinking — recommend brainstorming-skills."

## Review found issues but agent still doesn't follow the skill

**Cause:** Document quality ≠ behavioral effectiveness. Review checks the document; testing checks agent behavior.

**Next steps:** After review fixes are applied, use testing-skills to validate behavioral compliance.

## Yield% stays high across many passes

**Cause:** Each fix introduces new issues, or scope is expanding.

**Next steps:** Check if fixes are causing new problems. Consider whether skill is trying to do too much. Hit iteration cap if necessary and note "did not converge."

## Unsure whether finding is real issue or acceptable variation

**Cause:** Ambiguous quality criteria.

**Next steps:** Apply disconfirmation. If still ambiguous, note as P2 with "possible issue" and let user decide.

## References directory has many files, review is taking too long

**Cause:** Review scope may be too broad for stakes level.

**Next steps:** For Adequate stakes, focus on SKILL.md and spot-check references. For Rigorous+, review all references but prioritize those linked from critical sections.

## Skill missing required frontmatter (name, description)

**Cause:** Incomplete or malformed skill.

**Next steps:** Flag as P0 structural conformance issue (D3). Skill needs basic structure before detailed review. Consider whether to fix frontmatter first or escalate to brainstorming-skills for fundamental rework.

## Cannot read or write skill files

**Cause:** File permissions, non-text file format, or directory access issue.

**Next steps:** If file is unreadable, ask user to check permissions or provide file contents. If fixes cannot be applied due to write permissions, document proposed fixes in the review report without applying them — user can apply manually.

# Convergence Is Reviewer-Relative

*Observation from re-reviewing the claude-code-docs-design document.*

## The Finding

The original review found 23 issues and reached "convergence" at Pass 7 with 0% yield. A re-review (Pass 8) found 3 more issues — a 14% yield. This ~13% additional finding rate on a "converged" review demonstrates why the Thoroughness Framework uses Yield% thresholds rather than pass counts.

## The Convergence Illusion

When the original review reached Pass 7 with 0% yield, it meant: **"I (the reviewer) am not finding new issues."** But this is subtly different from: **"There are no more issues to find."**

The original review focused heavily on:
- Code accuracy (verifying examples against actual codebase)
- Table completeness (checking all files mentioned)
- Internal consistency (cross-referencing sections)

What it under-weighted:
- **Prose reference completeness** — the agent file at line 259 said "Update tool references" but the actual file has prose like "extension-docs MCP server" that also needs updating
- **Transitive scope** — other files in the repo that reference "extension-docs" but weren't in the migration's explicit scope

## Why Different Reviewers Find Different Things

Each review session develops what you might call an **attention topology** — certain dimensions get deep exploration while others get surface checks. The original review's attention concentrated on:

```
D8 (Completeness) → Code Changes section → file-by-file verification
D16 (Internal consistency) → table cross-checks
D12 (Cross-validation) → code vs. design alignment
```

The re-review came with a different question: "Did the fixes actually get applied?" This verification angle naturally led to reading the *actual files* that would be migrated, which surfaced:

1. The agent file has more than just the `tools:` frontmatter field — it has prose throughout
2. There are other `.md` files referencing "extension-docs" that weren't considered

## The ~13% Additional Finding Rate

Here's the arithmetic:
- Original: 23 issues found
- Re-review: 3 more issues
- Additional rate: 3/23 ≈ 13%

This isn't unusual. Studies of code review find similar patterns — a second reviewer typically finds 10-25% additional issues on "complete" reviews. The Thoroughness Framework's Yield% threshold (10% for Rigorous) is calibrated to this reality: it accepts that some issues will remain but sets a practical stopping point.

## Practical Implications

**For the Framework:**
The Yield% metric measures *diminishing returns within a single reviewer's session*, not absolute completeness. Convergence means "further passes by this reviewer are unlikely to be productive" — not "the document is perfect."

**For real-world usage:**
- If stakes are high enough, a second reviewer with fresh eyes adds value even on "converged" documents
- The types of issues found on re-review tend to cluster around dimensions the first reviewer deprioritized
- Verification-oriented re-reviews ("did the fixes land?") often surface scope-boundary issues the original missed

**For specific documents:**
The migration scope was the blind spot in this case. The original review verified that *mentioned files* were correct but didn't systematically grep for "extension-docs" across the repo to find *unmentioned files* that would also be affected. The re-review's verification approach naturally did that grep.

## Meta-Lesson

Convergence is reviewer-relative, not document-absolute. A 0% yield on Pass N means "I've exhausted my current attention patterns," not "all issues found." This is why the Framework emphasizes Yield% *thresholds* (practical stopping points) rather than claiming completeness.

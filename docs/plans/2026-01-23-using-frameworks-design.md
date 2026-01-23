## Design Context: using-frameworks

**Type:** Process/workflow (enforces step sequence)
**Risk:** Low (read/write to docs, bounded and reversible)

### Problem Statement

The methodology frameworks (Thoroughness, Decision-Making, Verification) are valuable but too long (~500-850 lines each) to read every time. Claude needs to *actually execute* them with visible structure, not just reference them or work from memory.

### Success Criteria

- Claude executes the framework properly with visible stage markers
- Entry Gate is completed interactively with user confirmation
- Exit Gate uses explicit checklist verification (each item shown)
- Framework's output artifact is produced
- Execution is auditable — an observer can trace what happened

### Compliance Risks

- "This is simple, I'll abbreviate" — mitigated by requiring visible stage markers that can't be skipped
- "User seems impatient" — mitigated by explicit checklist verification (can't claim done without showing checks)
- "I already know this framework" — mitigated by requiring actual file read, not memory recall

### Rejected Approaches

- **Delegation to existing skills:** `making-recommendations` implements decision-making framework but only for user-facing recommendations. The framework is broader (implementation choices, internal strategy). Decided to implement directly rather than delegate.
- **Single comprehensive skill without aliases:** Would require typing `/using-frameworks thoroughness` every time. Aliases (`/thoroughness`, `/decide`, `/verify`) provide better UX.
- **Full Entry/Exit Gate in skill:** Would duplicate framework content. Instead, skill provides essentials and defers to framework for complete requirements.

### Design Decisions

- **Unified skill with aliases:** One core skill (`using-frameworks`) with three command aliases for convenience. Single source of truth, multiple entry points.
- **Visible stage markers:** Required at every transition for auditability. Not optional formatting — compliance mechanism.
- **Essentials + defer pattern:** Skill contains essential checklist items; full requirements are in framework files. Keeps skill manageable (~220 lines) while maintaining rigor.
- **Authority language:** Multiple "YOU MUST" statements to prevent rationalization around requirements.
- **Framework files copied to references/:** Self-contained skill following "one level deep" rule. Frameworks in `references/` subdirectory.

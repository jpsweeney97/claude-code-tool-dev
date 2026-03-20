## Design Context: converting-pdf-exports

**Type:** Process/Workflow
**Risk:** Medium (writes files, bounded and reversible)

### Problem Statement

PDF exports to `.md` files contain layout artifacts that need conversion to clean, native markdown. Common artifacts include:
- Page numbers scattered throughout
- Two-column text merged into single lines
- Missing heading markers (lines that function as headings but lack `#`)
- Chapter prefixes as formatting artifacts ("Chapter N" + title)
- Table of contents with page numbers
- Headers/footers repeated at intervals

The existing `markdown-formatter` skill is designed for lossless structure normalization of files that are already markdown. It explicitly refuses to handle files that need content removal (like PDF artifacts). This creates a gap for PDF export conversion.

### Success Criteria

- Clean, readable markdown — artifacts removed, not just formatted
- Proper heading hierarchy established (H1 title, H2 sections, H3 subsections)
- All actual prose content preserved exactly (no rewriting)
- User confirms output location before writing
- Ambiguous cases resolved through user questions, not guesses

### Compliance Risks

| Risk | Mitigation |
|------|------------|
| Rushing on "almost clean" files | Process requires full assessment regardless of apparent cleanliness |
| Skipping user questions when confident | Explicit instruction to ask on any genuine ambiguity |
| Scope creep into prose editing | Hard constraint: structure + light breaks only, never rewrite |
| Overwriting without permission | Mandatory checkpoint before writing |

### Rejected Approaches

- **Auto-detection triggering:** Considered having skill trigger automatically when PDF artifacts detected. Rejected because false positives would be disruptive, and explicit invocation is clearer.
- **Lossless conversion:** Considered preserving all content including page numbers with structure only. Rejected because user goal is clean markdown, not faithful preservation.
- **Combined with markdown-formatter:** Considered adding conversion to existing skill. Rejected because they have fundamentally different guarantees (lossy vs. lossless) and should compose separately.

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Explicit invocation only | Avoids false positives; user knows when they have a PDF export |
| Ask on ambiguities | Wrong heading decisions cascade; 5-second question prevents minutes of fixing |
| Ask about output location | Original may be only copy; user should choose |
| Composable with markdown-formatter | Separation of concerns; conversion first, polish after |
| Light cleanup allowed for column merges | Strict "no content changes" would leave sentences broken mid-word |
| Report summary at end | User can verify what changed and catch any issues |

## Design Context: refining-specifications

**Type:** Quality enhancement
**Risk:** Low (edits documents, bounded and reversible)

### Problem Statement

Specification documents often ship unclear due to four failure modes:
1. **First-draft shipping** — initial versions go live without clarity passes
2. **Implicit knowledge** — author understands what they meant, readers don't
3. **Spec drift** — documents become unclear over time, nobody refines them
4. **Review theater** — "LGTM" without substantive examination

### Success Criteria

Specs refined through systematic lens application until no new issues emerge. The skill should:
- Apply 7 distinct lenses sequentially (one pass each)
- Report findings before making fixes
- Continue until convergence (repetition signal OR two consecutive clean passes)
- Produce clearer, more precise specifications

### Compliance Risks

| Risk | Mitigation in Skill |
|------|---------------------|
| "Document is already good" rationalization | Anti-pattern section addresses directly; every doc benefits from systematic review |
| "Just a minor update" exemption | Anti-pattern section; at minimum run consistency lenses |
| Surface-level passes (checkbox compliance) | Each pass must produce issues or explicit "No issues found" |
| Conflating with gap-analysis or validating-designs | When NOT to Use section distinguishes; Decision Points clarifies |

### Rejected Approaches

| Approach | Why Rejected |
|----------|--------------|
| Parallel lens application | Risks uneven coverage; low-salience lenses (consistency, testability) get missed |
| Adaptive lens selection | Too much discretion; compliance risk of skipping "unnecessary" lenses |
| Single convergence pass | One clean pass might be luck; two confirms stability |

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| 7 lenses, sequential | Each lens has dedicated focus; prevents high-salience bias |
| Fixed lens order (1→7) | Surface issues first (1-3), then cross-document (4-5), then holistic (6-7) |
| Report before fix | Creates accountability; teaches the pattern; prevents "fixing without understanding" |
| Convergence = repetition OR two clean passes | Handles both "finding same things" and "nothing left to find" |
| No thoroughness framework integration | Structured workflow with defined passes; vocabulary only would add overhead without benefit |

### Origin

This skill emerged from a live refinement of `verification.framework@1.0.0`. The pattern observed:
- Clarify implicit concepts
- Strengthen weak spots (vague language, loopholes)
- Add examples where abstract

The insight: "Frameworks benefit from this kind of refinement cycle — the initial version captures the structure, subsequent passes address ambiguity discovered through review."

This pattern was then generalized to all behavior-defining documents.

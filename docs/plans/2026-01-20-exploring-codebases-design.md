## Design Context: exploring-codebases

**Type:** Capability
**Risk:** Low (read-only, no external deps)

### Problem Statement

No systematic approach to exploring unfamiliar codebases. Explorations are ad-hoc, miss important aspects, and don't know when they're "done." Claude's default behavior is to read a few files, make assertions without evidence, and stop when it "feels complete."

### Success Criteria

- Comprehensive architectural understanding of the codebase
- Actionable orientation sufficient to start contributing
- Documented findings in a reusable artifact (Thoroughness Report)
- Methodology that knows when to stop (convergence via Yield%)

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Full Framework for Thoroughness integration | The framework IS the value — selective adoption would lose convergence/evidence rigor |
| Rigorous as default thoroughness | "Explore thoroughly" implies rigor; Adequate would be too shallow |
| Autonomous execution | User sets Entry Gate, skill runs to completion — frequent interrupts would break flow |
| Hybrid coverage structure | Codebases vary; skill should choose tree/graph/matrix based on what it finds |
| Strict report template | Consistency enables comparison across explorations and validates methodology |

### Seed Dimensions

| Dimension | Priority | Rationale |
|-----------|----------|-----------|
| Structure | P0 | Must understand before anything else |
| Data flow | P0 | Core to understanding behavior |
| Dependencies | P0 | External = risk, internal = coupling |
| Patterns | P1 | Important but not blocking |
| Error handling | P1 | Quality concern, not core understanding |
| Configuration | P1 | Affects behavior but secondary |
| Extension points | P1 | Important for contribution |
| Testing | P1 | Reveals design intent and quality |

### Compliance Risks

What might cause an agent to rationalize around this skill:

| Risk | Mitigation in Skill |
|------|---------------------|
| "The codebase is simple, I don't need the full framework" | Anti-pattern: Skipping Entry Gate |
| "I've found the main patterns, good enough" | Anti-pattern: Stopping when "it feels complete" |
| "The loop is taking too long" | Decision Point: Lower thoroughness, don't abandon |
| "I already understand this from reading a few files" | Anti-pattern: E0 evidence for P0 dimensions |
| "First pass converged" | Anti-pattern: One-pass theater (first pass is always 100%) |

### Rejected Approaches

| Approach | Why Rejected |
|----------|--------------|
| Selective framework adoption (concepts only) | Loses the discipline that makes the framework valuable |
| Checkpoint-based interaction | Breaks exploration flow; user said autonomous |
| Adequate as default thoroughness | Too shallow for "explore thoroughly" use case |
| Flexible report format | Loses comparability and methodology auditability |

### Test Plan

**Test codebases:** Fastify, tRPC (with documentation removed)

**Validation method:**
1. Run exploration skill on stripped codebase
2. Compare findings against original documentation
3. Success = exploration discovers architecture the docs describe
4. Failure = exploration misses major concepts that docs cover

**Specific checks:**
- Did exploration find Fastify's plugin encapsulation model?
- Did exploration find tRPC's type inference chain?
- Did Yield% actually converge (not first-pass exit)?
- Are evidence levels appropriate (E2 for P0)?

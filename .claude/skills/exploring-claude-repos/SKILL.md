---
name: exploring-claude-repos
description: Use when exploring Claude Code configuration repositories (community repos, extension collections) to harvest patterns, compare approaches, or understand what extensions exist. Use when asked to "explore this Claude Code repo", "harvest patterns from", "what's in this community repo", "compare this repo to my setup", or "find skills/hooks/commands in".
---

# Exploring Claude Repos

Systematic exploration of Claude Code configuration repositories using the Framework for Thoroughness.

## Overview

This skill applies `thoroughness.framework@1.0.0` to Claude Code config repos (skills, hooks, commands, agents, MCP configs, rules), producing:

- Comprehensive inventory of extensions by type
- Prioritized highlights with actionable signals
- Comparative analysis against your setup or other repos
- Documented findings for handoff to evaluation

**The loop:** DISCOVER (what to look for) → EXPLORE (cover each dimension) → VERIFY (check findings) → REFINE (loop or exit based on Yield%)

**Default thoroughness:** Rigorous (Yield <10%, E2 evidence for P0 dimensions)

**Protocol:** [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md)

**Companion skill:** After exploration, use `evaluating-extension-adoption` to decide whether to adopt specific findings.

## Triggers

**Explicit exploration:**
- "Explore this Claude Code repo"
- "What's in this community repo?"
- "Harvest patterns from [repo]"
- "Find skills/hooks/commands in [repo]"

**Comparison:**
- "Compare this repo to my setup"
- "How does repo A differ from repo B?"
- "What does this repo have that I'm missing?"

**Focused extraction:**
- "Find all the hook patterns in these repos"
- "What skills does this repo offer?"

**Slash command:** `/explore-claude-repo`

## When to Use

**Use when:**
- Discovering what's in a Claude Code configuration repo
- Harvesting patterns from community repos for potential adoption
- Comparing extension approaches across repos or against your own setup
- Building an inventory before deciding what to adopt

**Don't use when:**
- Exploring traditional source code for architecture understanding → use `exploring-codebases`
- Quick lookup of a specific extension you already know exists → targeted search is faster
- Already decided to adopt something and need implementation help → just implement it

## Outputs

**IMPORTANT:** The full exploration report goes in the artifact ONLY. Chat receives a brief summary. Do NOT reproduce the full iteration log, complete findings table, or coverage tracker in chat.

**Artifact (full report):** Exploration report at `docs/exploration-findings/YYYY-MM-DD-<repo-name>-exploration.md`

**Report structure:**
- Context (protocol, scope, target repo(s))
- Entry Gate (assumptions, thoroughness level, stopping criteria)
- Coverage Tracker (extensions by type with Cell Schema)
- Iteration Log (pass-by-pass Yield%)
- Complete findings table with all signals
- Disconfirmation Attempts
- Exit Gate verification
- Suggested next steps (evaluation invocations)

**Finding signals (each finding includes):**

| Signal | Values | Purpose |
|--------|--------|---------|
| **Novelty** | `new` / `similar-to:<yours>` / `extends:<yours>` | Is this in your setup? |
| **Quality** | `polished` / `functional` / `rough` | How well-structured? |
| **Conflict** | `none` / `conflicts-with:<yours>` | Would it clash? |
| **Complexity** | `drop-in` / `needs-adaptation` / `significant-integration` | Adoption effort? |

**Handoff format:** Each finding has a stable ID (e.g., `F1`, `F2`) that `evaluating-extension-adoption` can reference.

**Chat summary (brief — not the full report):**

```
**Explored:** [repo name] — [N] findings across [extension types covered]

**Highlights (P0 findings):**
- F1: [name] — [1-sentence description] (novelty: new, complexity: drop-in)
- F3: [name] — [1-sentence description] (novelty: new, conflict: conflicts-with:X)

**Notable conflicts:** [any findings with conflict signals, or "none"]

**Next steps:** Evaluate F1, F3 for adoption, or see full report for complete findings.

**Full report:** `docs/exploration-findings/YYYY-MM-DD-<repo>-exploration.md`
```

Do NOT include in chat: full iteration log, complete findings table, coverage tracker details, or disconfirmation attempt details. These belong in the artifact only.

**Definition of Done:**
- Entry Gate completed
- All P0/P1 dimensions explored with required evidence
- Yield% below threshold for chosen thoroughness level
- Exit Gate criteria satisfied
- Report written with finding IDs and signals
- Brief summary presented in chat (NOT full report)

## Process

This skill follows `thoroughness.framework@1.0.0`. This section summarizes; see [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md) for full protocol.

### Entry Gate

Before exploring, establish:

| Aspect | Question | Default |
|--------|----------|---------|
| Scope | Single repo, multiple repos, or focused extraction? | Infer from request |
| Assumptions | What am I taking for granted about the repo? | List explicitly |
| Thoroughness | How thorough? | Rigorous |
| Stopping criteria | When is "enough"? | Discovery-based (two loops with no new P0/P1 findings) |
| Comparison target | Against user's setup, another repo, or standalone? | Infer from request |
| Coverage structure | How to track? | Backlog (extensions discovered as you go) |

**Gate check:** Cannot proceed until assumptions listed, thoroughness level set, and scope clarified.

### Seed Dimensions

Start with these; DISCOVER phase will expand:

| Dimension | What to Look For | Priority |
|-----------|------------------|----------|
| Skills | SKILL.md files, workflow definitions | P0 |
| Hooks | Event handlers (PreToolUse, PostToolUse, etc.) | P0 |
| Commands | Slash command definitions | P0 |
| Agents/Subagents | Delegated task handlers | P0 |
| MCP configurations | External service integrations | P1 |
| Rules/CLAUDE.md | Always-active guidelines, memory patterns | P1 |
| Structure | Directory organization, naming conventions | P1 |
| Quality patterns | Documentation, testing, validation approaches | P2 |

### The Loop

```
DISCOVER → EXPLORE → VERIFY → REFINE → (loop or exit)
```

**DISCOVER:** Apply ≥3 techniques to find dimensions beyond the seed list:
- Pre-mortem: "This exploration would be worthless if I missed..."
- Perspective multiplication: What would someone migrating from this repo need to know?
- Boundary perturbation: What if someone only uses hooks? Only skills?

**EXPLORE:** For each extension type, systematically:
1. Locate all instances (glob patterns, directory traversal)
2. Catalog with metadata (name, purpose, dependencies)
3. Assess signals (novelty, quality, conflict, complexity)
4. Assign evidence level (E1: read file, E2: read + cross-referenced)

**VERIFY:** Cross-reference findings:
- Do dependencies between extensions check out?
- Do README claims match actual content?
- For comparison: does the signal assessment (novelty, conflict) hold up?

**REFINE:** Compute Yield%. If below threshold and no new dimensions, exit. Otherwise loop.

### Iteration Log Format

Each pass MUST include explicit Yield% tracking:

```markdown
| Pass | New Findings | Total Findings | Yield% | Decision |
|------|--------------|----------------|--------|----------|
| 1    | 15           | 15             | 100%   | Continue |
| 2    | 6            | 21             | 29%    | Continue |
| 3    | 2            | 23             | 8.7%   | Exit (< 10%) |
```

**Anti-pattern:** Reporting only final Yield% without iteration history. The log proves convergence wasn't faked.

### Exit Gate

Cannot claim "done" until:
- [ ] Coverage complete (all extension types explored)
- [ ] Signals assigned (novelty, quality, conflict, complexity for each finding)
- [ ] Disconfirmation attempted (actively looked for missed extensions)
- [ ] Assumptions resolved (verified, invalidated, or flagged)
- [ ] Convergence reached (Iteration Log shows Yield% below threshold)
- [ ] Stopping criteria satisfied
- [ ] Handoff prepared (finding IDs, suggested evaluation invocations)
- [ ] Full report written to `docs/exploration-findings/`
- [ ] Brief summary presented in chat (NOT full report — full analysis stays in artifact)

## Decision Points

**Choosing scope:**
- Single repo → Full inventory with all signals
- Multiple repos → Comparative analysis, focus on differences
- Focused extraction → Single dimension deep-dive (e.g., "just hooks")

**Choosing coverage structure:**
- Backlog (default) → Extensions discovered as you go; best for unknown repos
- Tree → Repo has clear hierarchical organization
- Matrix → Cross-cutting comparison (extension type × repo)

**When repo is huge (>50 extensions):**
- Do NOT abandon rigor — scope down instead
- Ask: "Focus on a specific extension type, or sample across all?"
- If sampling: document what was sampled and what was skipped

**When repo is messy (non-standard structure):**
- Expand DISCOVER phase to locate extensions in unexpected places
- Lower confidence on findings that lack clear documentation
- Flag structural issues as findings (useful context for adoption)

**When comparison targets have different philosophies:**
- Document the philosophical difference explicitly
- Signal assessments may not be directly comparable
- "Conflict" signal includes conceptual conflicts, not just technical

**When Yield% stays high (>30%) after multiple passes:**
- Check if dimensions are too broad (split "Skills" into sub-categories)
- Check if you're counting refinements as new findings (refinements don't count)
- Consider: is this repo genuinely complex, or is exploration unfocused?

**When findings contradict each other:**
- STOP exploration on other dimensions
- Investigate contradiction with additional methods
- Document resolution or flag as unresolved

**Pressure to skip ("just tell me what's interesting"):**
- Acknowledge the request
- Complete at least one full pass with Entry Gate
- Compress output, not process: highlight P0 findings, full report still written

## Examples

**Scenario:** User asks "Explore the everything-claude-code repo and compare it to my setup"

### BAD: Ad-hoc exploration without structure

Claude scans the README, glances at a few directories, and reports:

> "This repo has a lot of skills and hooks. Some interesting ones are the TDD skill, the security reviewer agent, and some MCP configs for GitHub. You might find the commit command useful since you don't have one."

**Why it's bad:**
- No systematic coverage — missed entire extension types
- No evidence levels — "has a lot of skills" is E0 (assertion)
- No signals — didn't assess quality, conflict, or complexity
- No convergence — stopped when it felt like enough
- Cherry-picked "interesting" findings instead of comprehensive inventory
- No handoff — evaluation skill can't reference specific findings

### GOOD: Framework-driven thorough exploration

Claude runs Entry Gate, explores systematically, loops until convergence. Full details go in artifact; chat gets brief summary.

**Entry Gate:**
- Scope: Single repo with comparison to user's setup
- Assumptions: Can clone/read repo, user's setup is at `~/.claude/`
- Thoroughness: Rigorous
- Stopping: Discovery-based

**Iteration Log, findings table, coverage tracker:** *(documented in exploration report, not shown in chat)*

**Chat output (brief summary only):**

> **Explored:** everything-claude-code — 27 findings across Skills, Hooks, Commands, Agents, MCP configs
>
> **Highlights (P0 findings):**
> - F1: tdd-workflow — structured TDD process skill (novelty: new, complexity: needs-adaptation)
> - F3: security-reviewer — code security analysis agent (novelty: new, complexity: significant-integration)
>
> **Notable conflicts:** F4 (/plan command) conflicts with your existing plan-mode setup
>
> **Next steps:** Evaluate F1, F3 for adoption, or resolve F4 conflict first.
>
> **Full report:** `docs/exploration-findings/2024-01-15-everything-claude-code-exploration.md`

**Why it's good:**
- Systematic coverage with explicit dimensions
- Evidence levels assigned (E2 for P0 findings)
- All four signals for each finding (in artifact)
- Iteration Log proves convergence (in artifact)
- Finding IDs enable handoff to evaluation skill
- Chat summary gives actionable overview without overwhelming
- Full details preserved in artifact for reference

## Anti-Patterns

**Pattern:** Downgrading rigor without explicit calibration
**Why it fails:** "This is just a quick look" becomes the excuse to skip the loop. Without explicit Entry Gate, there's no principled stopping point.
**Fix:** Always run Entry Gate. If thoroughness should be Adequate instead of Rigorous, state why and accept the lower evidence bar explicitly.

**Pattern:** Abandoning the loop under perceived time pressure
**Why it fails:** "The user wants speed" isn't permission to skip convergence. One-pass exploration misses entire extension types and produces unreliable signals.
**Fix:** Acknowledge the pressure. Complete at least one full loop with Entry Gate. Compress output, not process.

**Pattern:** Declaring low yield prematurely
**Why it fails:** "Nothing interesting here" after scanning the README is E0 evidence. Actual low yield requires systematic coverage proving there's nothing to find.
**Fix:** Yield% measures convergence, not first impressions. Pass 1 is always 100%. Only claim low yield after the loop converges.

**Pattern:** Cherry-picking instead of systematic coverage
**Why it fails:** "I'll note the interesting stuff" produces biased findings. What's "interesting" without systematic coverage is whatever Claude noticed first.
**Fix:** Cover all seed dimensions. Signal assessment (novelty, quality) happens after systematic discovery, not as a filter on what to discover.

**Pattern:** Skipping comparison when comparison was requested
**Why it fails:** "Here's what the repo has" without reference to user's setup is incomplete when comparison was asked for.
**Fix:** If comparison target specified, every finding needs novelty and conflict signals assessed against that target.

**Pattern:** Summary-only Yield%
**Why it fails:** Reporting "final Yield% was 7%" without showing the iteration log hides whether convergence was real.
**Fix:** Include the full Iteration Log table showing New/Total/Yield%/Decision for each pass.

**Pattern:** Stopping when "it feels complete"
**Why it fails:** Human intuition about completeness is unreliable. "Feels done" is not a stopping criterion.
**Fix:** Use Yield% and stopping criteria. Exit Gate must pass.

## Troubleshooting

**Symptom:** Yield% stays high (>30%) after multiple passes
**Cause:** Dimensions too broad, or genuinely complex repo
**Next steps:**
- Split broad dimensions (e.g., "Skills" → "workflow skills", "utility skills", "meta skills")
- Check if you're counting refinements as new (refinements don't count toward Yield%)
- If repo is genuinely complex, document this and continue until convergence

**Symptom:** Can't locate extensions in expected places
**Cause:** Repo uses non-standard structure
**Next steps:**
- Expand search patterns (check root, nested directories, unconventional names)
- Read repo's README/docs for structure guidance
- Flag structural issues as findings (useful context for evaluation)
- Lower confidence on findings from poorly-organized sections

**Symptom:** Comparison signals are ambiguous
**Cause:** User's setup not fully known, or philosophies differ significantly
**Next steps:**
- For unknown user setup: ask which extensions to compare against, or read user's `~/.claude/` directly
- For philosophical differences: document the difference explicitly; note that "conflict" may be conceptual, not technical

**Symptom:** DISCOVER phase produces no new dimensions
**Cause:** Seed dimensions are comprehensive for this repo type, or techniques applied superficially
**Next steps:**
- Apply techniques with genuine adversarial intent — "what would make this exploration worthless?"
- If genuinely no new dimensions, document this and proceed

**Symptom:** Claude skipped to "interesting findings" without systematic coverage
**Cause:** Cherry-picking pattern; high confidence in initial scan
**Next steps:**
- Return to Entry Gate
- Cover all seed dimensions systematically before assessing signals
- The process exists because "interesting at first glance" is unreliable

**Symptom:** Repo is too large to explore in reasonable time
**Cause:** Huge repo with hundreds of extensions
**Next steps:**
- Do NOT abandon rigor — scope down instead
- Options: focus on one extension type, sample across types, prioritize P0 dimensions only
- Document what was scoped out and why

**Symptom:** Exit Gate fails on "handoff prepared"
**Cause:** Findings lack IDs or signals needed for evaluation skill
**Next steps:**
- Assign stable IDs to all findings (F1, F2, ...)
- Ensure all four signals are present for each finding
- Add suggested evaluation invocations to report

## Verification

**Quick check:** Exit Gate passes, Iteration Log shows Yield% below threshold, brief summary in chat (not full report).

**Deeper validation:**

Entry Gate:
- [ ] Scope clarified (single/multiple/focused)
- [ ] Assumptions listed explicitly
- [ ] Thoroughness level set with rationale
- [ ] Comparison target identified (if applicable)

Coverage:
- [ ] All P0 extension types explored (Skills, Hooks, Commands, Agents)
- [ ] All P1 extension types explored (MCP configs, Rules/CLAUDE.md, Structure)
- [ ] Evidence levels assigned (E1 minimum, E2 for P0)

Signals:
- [ ] Every finding has all four signals (novelty, quality, conflict, complexity)
- [ ] Novelty/conflict assessed against comparison target (if specified)
- [ ] Signal assessments have supporting evidence, not just gut feel

Convergence:
- [ ] Iteration Log shows pass-by-pass Yield%
- [ ] Final Yield% below threshold for chosen thoroughness level
- [ ] Disconfirmation attempted (actively searched for missed extensions)

Handoff:
- [ ] Every finding has stable ID (F1, F2, ...)
- [ ] Report includes suggested evaluation invocations
- [ ] Findings are structured for `evaluating-extension-adoption` consumption

Output:
- [ ] Full report written to `docs/exploration-findings/`
- [ ] Chat contains brief summary: finding count, P0 highlights, conflicts, next steps, link
- [ ] Chat does NOT contain: full iteration log, complete findings table, coverage tracker details

**Self-test:** Could someone use this report to decide which findings to evaluate for adoption without re-exploring the repo?

## References

**Required protocol:**
- [references/framework-for-thoroughness.md](references/framework-for-thoroughness.md) — Full framework specification (Entry/Exit Gates, loop phases, Yield%, evidence levels, report template)

**Companion skill:**
- `evaluating-extension-adoption` — Use after exploration to decide whether to adopt specific findings

**The framework reference contains:**
- Normative requirements (MUST/SHOULD/MAY)
- Coverage structure options (matrix/tree/graph/backlog)
- Cell Schema for tracking items
- Thoroughness Report Template
- Stopping criteria templates
- Evidence and confidence level definitions

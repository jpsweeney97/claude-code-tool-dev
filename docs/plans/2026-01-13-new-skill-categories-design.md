# New Skill Categories Design

**Date:** 2026-01-13
**Status:** Approved
**Context:** Expanding skill-wizard categories from 13 to 21

## Problem

The existing 13 skill categories have gaps:

1. **Review/audit workflows** — Evaluating existing artifacts doesn't fit action-oriented categories
2. **Prompt engineering** — ML/AI is too broad; prompt work is the relevant domain for Claude Code users
3. **Research tasks** — Exploration and investigation aren't covered
4. **Planning/architecture** — System design and decision-making need their own guidance
5. **Performance work** — Not behavior-preserving like refactoring; intentionally changes metrics
6. **Automation/scripting** — Build scripts and CI/CD are different from agentic pipelines
7. **UI/UX work** — Frontend development has distinct failure modes (accessibility, responsiveness)
8. **Incident response** — Mitigation and recovery, not root cause analysis

## Decision

Add 8 new categories to `category-integration.md`:

| Category | Typical Risk | Dominant Failure Mode |
|----------|--------------|----------------------|
| review-audit | Medium | Superficial review (missed issues) |
| prompt-engineering | Medium | Overfitting to test cases |
| research-exploration | Low | Inconclusive findings |
| planning-architecture | Medium | Plan doesn't survive implementation |
| performance-optimization | Medium | Wrong bottleneck targeted |
| automation-scripting | Medium | Works locally, fails in CI |
| ui-ux-development | Medium | Functional but poor UX |
| incident-response | High | Mitigation introduces new issues |

## Category Definitions

### review-audit

**Scope:** Design review, code review, architecture audit, spec critique

**Category-Specific DoD Additions:**

- Review criteria explicitly stated before review begins
- Coverage documented (what was reviewed, what was skipped and why)
- Findings categorized by severity (Critical / Major / Minor / Nitpick)
- Each finding includes: location, issue, impact, recommendation
- Confidence level stated (High / Medium / Low) for non-obvious findings

**When NOT to Use:**

- Artifact doesn't exist yet (that's planning)
- Goal is to fix issues, not find them (use relevant action category)
- Reviewing your own just-produced output (use producing category's verification)

---

### prompt-engineering

**Scope:** Prompt authoring, testing, behavior verification for reusable prompts

**Category-Specific DoD Additions:**

- Goal statement explicit (what behavior the prompt should produce)
- Test cases defined: at least happy path + 2 edge cases
- All test cases pass with expected behavior
- Failure modes documented (what the prompt should NOT do)
- Regression baseline captured (example outputs for comparison)
- Token efficiency considered (prompt not unnecessarily verbose)

**When NOT to Use:**

- Writing a simple command (1-2 sentences)
- Prompt is part of a larger skill (use meta-skills)
- Reviewing an existing prompt (use review-audit)
- Prompt is for a one-off task (prompt-engineering is for reusable prompts)

**Decision Points:**

- If prompt exceeds 500 tokens: "Is this complexity necessary?"
- If test cases all pass on first try: "Are the test cases challenging enough?"
- If prompt relies on specific model behavior: "May break on model updates"

---

### research-exploration

**Scope:** Codebase exploration, tech evaluation, investigation, information gathering

**Category-Specific DoD Additions:**

- Research question explicitly stated before starting
- Scope bounded (what's in/out of investigation)
- Sources consulted documented (files read, docs checked, searches run)
- Findings summarized with evidence (not just conclusions)
- Answer to original question stated clearly, or "inconclusive" with explanation
- Next steps identified (what to do with findings)

**When NOT to Use:**

- Goal is to fix something (use debugging-triage or action category)
- Already know the answer (skip to relevant action category)
- Researching to make a decision (use planning-architecture instead)

**Decision Points:**

- If research exceeds 10 files without findings: "Narrow scope or try different search?"
- If conflicting sources found: document conflict, ask user to adjudicate
- If research question changes mid-investigation: pause and confirm new scope

---

### planning-architecture

**Scope:** System design, ADRs, technical specs, implementation plans

**Category-Specific DoD Additions:**

- Problem/goal statement explicit before solution design
- Constraints enumerated (technical, timeline, compatibility, team)
- Alternatives considered (at least 2 approaches with trade-offs documented)
- Decision rationale captured (why this approach over alternatives)
- Dependencies identified (what must exist before implementation)
- Scope explicitly bounded (what's included, what's deferred)
- Verification criteria defined (how we'll know the plan worked)

**When NOT to Use:**

- Implementation is trivial (<30 min work)
- Gathering information to inform a decision (use research-exploration first)
- Reviewing an existing plan (use review-audit)
- Plan is really a spec for generated code (use code-generation)

**Decision Points:**

- If plan has >10 steps: "Can this be broken into phases?"
- If no alternatives documented: "What other approaches did we consider?"
- If constraints unstated: "What limitations should we design around?"
- If dependencies unclear: "What must be true before we can start?"

---

### performance-optimization

**Scope:** Profiling, benchmarking, latency/throughput/memory optimization

**Category-Specific DoD Additions:**

- Target metric defined before optimization (latency, throughput, memory, bundle size, etc.)
- Baseline measurement captured (quantified "before" state)
- Bottleneck identified with evidence (profiler output, flame graph, metrics)
- Post-optimization measurement shows improvement on target metric
- Regression check: other metrics didn't degrade significantly
- Trade-offs documented (e.g., "reduced latency by 40%, increased memory by 10%")

**When NOT to Use:**

- No baseline measurement exists (measure first, then optimize)
- Refactoring for clarity without performance goal (use refactoring-modernization)
- Performance issue is speculative (use research-exploration to profile first)

**Decision Points:**

- If optimization yields <10% improvement: "Is this worth the complexity cost?"
- If multiple bottlenecks identified: "Which has highest impact-to-effort ratio?"
- If optimization requires API changes: flag as breaking change, coordinate with api-changes

---

### automation-scripting

**Scope:** Build scripts, CI/CD pipelines, tooling, repeatable automation

**Category-Specific DoD Additions:**

- Purpose and trigger clearly documented (when does this run, who/what invokes it)
- Dependencies declared (tools, env vars, permissions required)
- Idempotency verified (safe to run multiple times)
- Error handling covers common failures (missing tools, network issues, permission denied)
- Exit codes meaningful (0 = success, non-zero = failure with distinct codes if useful)
- Tested in target environment, not just local

**When NOT to Use:**

- Building an agent workflow with LLM decision-making (use agentic-pipelines)
- One-off command you'll run once (just run it, no skill needed)
- The "script" is really a full application (use code-generation)

**Decision Points:**

- If script has >3 external dependencies: "Should this be containerized?"
- If script modifies state: "Is there a dry-run mode?"
- If script runs in CI: "Are secrets handled securely?"
- If script takes >30 seconds: "Should it show progress output?"

---

### ui-ux-development

**Scope:** Frontend components, styling, accessibility, responsive design

**Category-Specific DoD Additions:**

- Visual requirements specified (mockup, design system reference, or explicit description)
- Responsive behavior defined (breakpoints, mobile/tablet/desktop)
- Accessibility baseline met (keyboard navigation, screen reader labels, color contrast)
- Component renders without console errors/warnings
- Edge cases handled (empty states, loading states, error states, overflow text)
- Tested in target browsers/devices (or documented which are supported)

**When NOT to Use:**

- Purely backend/API work with no visual component (use code-generation or api-changes)
- Reviewing existing UI for issues (use review-audit)
- Optimizing render performance (use performance-optimization)

**Decision Points:**

- If no design provided: ask for mockup, design system reference, or explicit visual requirements
- If accessibility requirements unclear: default to WCAG 2.1 AA as baseline
- If component complexity is high (>200 lines): "Should this be broken into subcomponents?"
- If visual testing needed: "Is there a Storybook or visual regression setup?"

---

### incident-response

**Scope:** Active incident mitigation, recovery, stakeholder communication

**Category-Specific DoD Additions:**

- Impact assessed (who/what is affected, severity, scope)
- Mitigation applied and verified (incident actually resolved, not just attempted)
- Rollback plan documented (how to undo mitigation if it makes things worse)
- Communication sent to stakeholders (if applicable)
- Timeline captured (when detected, when mitigated, when resolved)
- Follow-up items identified (root cause investigation, preventive measures)

**When NOT to Use:**

- No active incident (use debugging-triage for investigation)
- Root cause analysis is the goal (use debugging-triage; incident-response is about mitigation)
- The "incident" is a feature request or non-urgent bug (use appropriate category)

**Decision Points:**

- If multiple mitigation options exist: prefer fastest to implement, not most elegant
- If mitigation requires code changes: "Can we mitigate with config/feature flag first?"
- If root cause unknown: mitigate first, investigate later
- If mitigation has side effects: document them, communicate to stakeholders, accept temporarily

**Key Principle:** Speed of mitigation > elegance of solution. Fix it now, clean it up later.

## Alternatives Considered

### Batch 1: Approach A (selected)

Adds review-audit, prompt-engineering, research-exploration, planning-architecture.

**Trade-off:** Clear boundaries, manageable expansion.

### Batch 1: Approach B (rejected)

Would have split ML/AI into data-preparation and model-development, and split planning into planning-design and implementation-planning.

**Why rejected:** YAGNI. ML/AI scope was narrowed to prompt-engineering (relevant to Claude Code users). Planning doesn't need the split yet.

### Batch 1: Narrow prompt-authoring (rejected)

Would cover only writing prompts, not testing.

**Why rejected:** Incomplete unit of work. A prompt without tests is a liability.

### Batch 2: Additional candidates considered

| Candidate | Decision | Rationale |
|-----------|----------|-----------|
| performance-optimization | **Selected** | Distinct from refactoring (intentionally changes metrics) |
| automation-scripting | **Selected** | Distinct from agentic-pipelines (no LLM decision-making) |
| ui-ux-development | **Selected** | Distinct failure modes (accessibility, responsiveness) |
| incident-response | **Selected** | Distinct from debugging-triage (mitigation vs. root cause) |
| integration-work | Deferred | Could be handled by existing categories for now |
| monitoring-observability | Deferred | Overlaps infrastructure-ops enough |
| database-schema | Deferred | Overlaps data-migrations and code-generation |

## Implementation

1. Update `skill-wizard/references/category-integration.md` with 8 new categories
2. Total categories: 13 + 8 = 21

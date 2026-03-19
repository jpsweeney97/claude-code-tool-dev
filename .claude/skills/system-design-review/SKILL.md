---
name: system-design-review
description: Review system architecture through 8 categories of design lenses (structural, behavioral, data, reliability, change, cognitive, trust/safety, operational). Use whenever the user asks to "review this architecture", "review this design", "evaluate this system", "check this design for gaps", "architecture review", "what are the architectural concerns here", or shares a design doc, codebase, or verbal description and wants architectural assessment. Also trigger when the user asks "what decisions did we inherit", "where are the gaps in this design", "stress test this architecture", or wants to understand cross-cutting tensions in a system. Do not use for code-level bug review, incident post-mortems, debt prioritization, or refactoring sequencing.
argument-hint: "[target — e.g., 'the auth service design doc', 'this codebase', or describe the system verbally. Omit to review the most recent design or proposal.]"
---

# System Design Review

Diagnose architectural decisions by walking a system through design lenses. The core question for every lens: **"Did we make a conscious decision here, or did we inherit a default?"**

This skill surfaces inherited defaults, underspecified decisions, explicit tradeoffs, cross-cutting tensions, and questions that need naming. It works across design documents, codebases, and verbal architecture descriptions.

## Scope

**In scope:** Architectural diagnosis using the lenses framework. Findings about decision quality, not implementation quality.

**Out of scope:**

| Request | Handoff |
|---------|---------|
| Incident timeline or root-cause analysis | "This skill identifies which lenses likely failed. Use a post-mortem skill for timeline reconstruction." |
| Debt prioritization or remediation ordering | "This skill identifies strained lenses and hidden tradeoffs. Use a tech-debt skill to prioritize fixes." |
| Refactoring sequencing | "This skill surfaces architectural gaps. Use a refactoring-triage skill to sequence remediation." |
| Implementation-readiness audit | "This skill diagnoses architectural decisions. Use a design-review skill for implementation readiness." |
| Code-level bug review | "This skill works at the architecture level. Use a code review skill for bugs." |

If the user's primary ask is an out-of-scope workflow (e.g., "help me prioritize which debt to fix first"), hand off immediately — do not force an unsolicited diagnosis. If the request mixes in-scope and out-of-scope work, do the architectural diagnosis first, then state the handoff. Do not silently expand into out-of-scope workflows.

## Execution Flow

```
Frame → Screen → Deep Dive → Deliver
```

1. **Frame**: Choose scope level, identify archetypes, calibrate stakes
2. **Screen**: Build evidence map, run sentinel checks across all 8 categories
3. **Deep Dive**: Analyze weighted lenses, produce findings and tensions
4. **Deliver**: Present via staged checkpoints

## Stage 1: Frame

### Scope Selection

Choose one scope level before starting. Do not mix scope levels in one run.

- `system` — the whole architecture at the top level
- `subsystem` — a bounded component or service
- `interface` — a specific boundary, contract, or integration point

If the user asks for both a system-level review and a deep dive on a specific interface, ask which scope to review first.

### Archetype Identification

Infer the top 1-2 archetypes from the input, state them with a confidence level, and proceed unless ambiguity would materially change which lenses get deep attention.

Available archetypes: Internal tool / back-office, User-facing API / SaaS, Data pipeline / ETL, Financial / regulated, ML / research platform, Event-driven / streaming.

When the input doesn't map cleanly to the table: infer up to 2, reduce weighting strength if confidence is low, and fall back to unweighted screening plus evidence-promoted deep lenses if no archetype fits. Archetypes bias where you look first — they do not decide what is allowed to matter.

Example framing:
```
Archetype: User-facing API + event-driven (medium confidence)
If that's wrong, correct me now — it changes which lenses I prioritize.
```

### Stakes Calibration

Propose stakes and proceed. Stakes control depth, finding count, and whether to pause for confirmation.

- `low` — reversible, narrow blast radius, internal-only
- `medium` — meaningful blast radius or partial irreversibility
- `high` — hard to reverse, external/shared impact, safety/reliability/security significance

**Decision tree:**
1. User explicitly requests depth level → honor it, unless a high-risk cue is present
2. Any high-risk cue → propose `high`
3. All low-risk cues → propose `low`
4. Else → propose `medium`
5. Uncertain between two tiers → choose the higher one

**High-risk cues:** external user-facing API, auth/permissions/trust boundary, payments/financial/regulated data, migrations/irreversible data changes, SLO/SLA/availability commitments, shared platform/infrastructure, multi-team blast radius, distributed consistency.

**Fail-safe:** Never silently downgrade. If the user doesn't answer a stakes question, proceed at the higher plausible tier.

## Stage 2: Screen

Build an evidence map from the input, then run one sentinel question per category.

### Sentinel Questions

| Category | Sentinel |
|----------|----------|
| Structural | Can I name the main components and their boundaries at this scope? |
| Behavioral | Can I trace the main runtime path and name what happens under failure, retry, or overload? |
| Data | Can I trace one critical datum from entry to storage to exit and identify its source of truth? |
| Reliability | Are guarantees, recovery, and degradation behavior stated or visible? |
| Change | Is there a credible story for change, migration, rollback, or test isolation? |
| Cognitive | Could a new engineer find the responsibility and rationale without oral tradition? |
| Trust & Safety | Is there an explicit trust boundary, privilege boundary, or sensitive-data handling point? |
| Operational | Can I tell how this is deployed, configured, observed, and owned? |

### Category Statuses

| Status | Meaning |
|--------|---------|
| `deep` | Selected for substantive analysis. Eligible to produce findings. |
| `screened` | Concrete check completed against anchored evidence. No material concern at screening depth. |
| `insufficient evidence` | Available evidence too weak to classify responsibly. |
| `not applicable` | Category has no meaningful surface at the chosen scope. |

A category qualifies as `screened` only when: (1) at least one concrete anchor exists, (2) the sentinel was answered in one sentence tied to that anchor, and (3) the answer does not rely on guessing.

Promote `screened` to `deep` when: the category is primary/secondary for the archetype, the sentinel surfaces a concern, or it links to a finding from another category.

### Evidence Bars by Input Type

**Design doc:** Read the full document first. Sections, diagrams, tables, and named decisions are anchors. `screened` requires 1 anchored sentinel answer.

**Codebase:** Build a bounded architecture sample — at most 12 anchors total: 2 entrypoints, 2 orchestration/control-flow, 2 data/state, 2 boundary (API/queue/adapter), 2 config/deploy/observability, 2 test/validation. `screened` requires 1 primary + 1 corroborating anchor. If the codebase is too large, ask to narrow scope or mark more categories `insufficient evidence`.

**Verbal description:** Only explicit user statements are valid anchors. `screened` requires a direct quoted claim or clearly stated mechanism. If implied only, mark `insufficient evidence`.

After screening, record one line per category: status, sentinel used, anchor, one-line disposition.

### Global Evidence Floor

If 4 or more categories would be `insufficient evidence`, state this explicitly after screening and ask whether to continue at reduced depth or narrow scope before producing findings. A review where most categories lack evidence risks false confidence in the few findings it does produce.

If the user does not respond, continue with a partial review limited to categories that cleared screening. Label the review `reduced-depth` in the snapshot and cap findings at 4.

### Deep Lens Selection

After screening, select 6-10 individual lenses (not categories) for the deep dive. For narrow interface scope or sparse verbal input, 4-6 is acceptable if you state why fewer lenses were genuinely relevant.

1. **Archetype weighting** — primary and secondary lenses for the identified archetype(s) from the reference's weighting table
2. **Screening promotion** — lenses where the sentinel surfaced a concern worth investigating
3. **Cross-category links** — lenses connected to findings emerging from other categories

When no archetype fits cleanly, skip step 1 and rely on steps 2 and 3 (evidence-promoted lenses only).

## Stage 3: Deep Dive

Analyze the selected deep lenses. Produce findings and tensions, then assemble the output.

### Output Structure

**5 parts.** Every section must earn its place — if a section has nothing meaningful, say so rather than padding.

**1. Review Snapshot** — compact summary table:

```md
| Signal | Count |
|--------|-------|
| High-priority findings | N |
| Total findings | N |
| Tensions identified | N |
| Categories screened only | N |
| Insufficient evidence | N |
```

**2. Focus and Coverage** — what was reviewed and how:
- Scope level, input type, archetype(s) + confidence, stakes tier
- Named deep lenses (6-10)
- One-line status per category (status + sentinel + anchor + disposition)

**3. Findings (F1, F2, ...)** — the primary evidence:

| Field | Content |
|-------|---------|
| Lens | Which lens surfaced this |
| Decision state | One of the 5 taxonomy states |
| Anchor | Where in the input this was found |
| Problem | What's wrong or missing |
| Impact | Why it matters |
| Recommendation or question | What to do, or what to investigate |

**4. Tension Map (T1, T2, ...)** — why gaps stayed hidden:

| Field | Content |
|-------|---------|
| Tension | e.g., Consistency ↔ Availability |
| What is being traded | Both sides, concretely |
| Why it hid | What made this easy to miss |
| Likely failure story | Pre-mortem narrative |
| Linked findings | Which F-numbers this explains |

**5. Questions / Next Probes** — end with 2-4 sharp questions, not a verdict. The review is a conversation starter.

### Decision State Taxonomy

| State | When to use |
|-------|-------------|
| `explicit tradeoff` | Design names both sides and makes a conscious choice |
| `explicit decision` | Conscious choice visible, but not framed as a tradeoff |
| `default likely inherited` | No local rationale + matches a framework default or legacy pattern |
| `underspecified` | System must decide something here, but the choice is not defined |
| `not enough evidence` | Input too sparse to classify safely |

Use `default likely inherited` only with positive evidence of a default — lack of rationale alone is insufficient. For codebase reviews, be conservative: code shows what exists, not why. If rationale is absent and no recognizable default pattern is visible, use `not enough evidence`.

**Example — distinguishing `underspecified` from `not enough evidence`:**
- `underspecified`: "The auth service handles both internal and external requests but no token validation boundary is defined. The system must make this decision but hasn't."
- `not enough evidence`: "The verbal description mentions 'an auth service' without specifying what it does. The input is too sparse to determine whether a validation boundary was considered."

### Tension Inclusion Rules

A tension is optional. 0 is a valid count. Do not force one.

Include a tension only when ALL of these pass:
1. **Two-sided anchor** — both sides have concrete anchors in the input
2. **Tradeoff mechanism** — you can explain how prioritizing one side strained the other
3. **Hiddenness** — you can explain why this was easy to miss
4. **Finding linkage** — it explains at least 1 concrete finding
5. **Specificity** — wording is system-specific, not a generic copy of the reference table

Before emitting, fill all 6 lines or do not emit:
1. Side A anchor
2. Side B anchor
3. What decision or default pulled toward side A
4. What cost or blind spot appeared on side B
5. Why a reviewer could miss this
6. Which finding(s) this tension explains

Use the cross-cutting tensions table as a prompt source, not a required menu. Custom tensions are valid.

### Depth Calibration

| Stakes | Finding target | Hard cap | Tension cap | Overflow |
|--------|---------------|----------|-------------|----------|
| `low` | 3-5 | 6 | 0-1 | Drop minor items |
| `medium` | 5-8 | 9 | 0-2 | Move lower-signal to deferred section |
| `high` | 8-12 | 12 (15 via appendix) | 1-3 | Cluster by root cause; overflow to appendix |

If you have more than 12 findings in the main reply, either cluster by root cause or produce a saved artifact. Overflow findings (up to 15) go in a **Deferred Findings** appendix — a flat list of one-liners with lens and decision state, without full finding fields.

### No-Findings Path

If no material findings surface, say so directly. A clean review at the current depth is a valid outcome. Do not pad with generic concerns.

## Delivery Model

Use staged checkpoints. The user can redirect between stages.

| Checkpoint | Content | When to pause |
|------------|---------|---------------|
| C0: Framing | Scope, archetype, stakes, planned deep lenses | High stakes with archetype/scope uncertainty |
| C1: First findings | Snapshot + coverage + top 2-4 findings | High stakes — wait for reaction |
| C2: Full review | Remaining findings + tension map + questions | — |

**Low stakes:** Collapse to one message. **Medium stakes:** One message unless archetype or scope is ambiguous — in that case, invite correction at C0 before proceeding. **High stakes:** Invite reaction at C0 if uncertain, otherwise at C1. If the user does not respond, continue — checkpoints are invitations, not gates.

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Marking categories `screened` without concrete anchors | Creates false coverage that hides real gaps | If the anchor is vague, use `insufficient evidence` |
| Copying tensions from the reference table verbatim | Sounds architecture-literate but explains nothing about THIS system | Every tension must pass all 5 inclusion checks |
| Claiming `default likely inherited` without evidence of a default | Overstates diagnosis when the evidence only shows absence of rationale | Use `not enough evidence` when unsure |
| Walking all 40 lenses narratively | Buries signal in noise and exhausts the reader | Use the 2-level model: screen broadly, dive deep on 6-10 |
| Ending with a verdict instead of questions | Closes the conversation when the value is in opening it | End with sharp questions that advance the user's thinking |
| Silently expanding into out-of-scope work | Blurs the skill boundary and produces shallow results | State the handoff explicitly |

## Example

**User:** "Review the architecture of our notification service — it handles email, SMS, and push via a single queue."

> **Review Snapshot**
>
> | Signal | Count |
> |--------|-------|
> | High-priority findings | 2 |
> | Total findings | 5 |
> | Tensions identified | 1 |
> | Categories screened only | 3 |
> | Insufficient evidence | 1 |
>
> **F1. Single queue for heterogeneous delivery channels**
> - Lens: Failure Containment
> - Decision state: `default likely inherited`
> - Anchor: Queue configuration in `notification-service/config.yaml`
> - Problem: SMS gateway timeouts block email delivery — failure in one channel propagates to all channels
> - Impact: A slow SMS provider degrades all notification types
> - Recommendation: Evaluate per-channel queues or priority lanes
>
> **T1. Simplicity ↔ Failure Containment**
> - What is being traded: Single-queue simplicity vs. per-channel isolation
> - Why it hid: The system was built when only email existed; SMS and push were added to the same queue without revisiting the original decision
> - Likely failure story: SMS provider has a 30-second timeout spike; email backlog grows; users miss time-sensitive emails
> - Linked findings: F1, F3
>
> **Questions**
> 1. Was the single-queue design a conscious decision when SMS was added, or was the email-era default carried forward?
> 2. What is the SLO for email delivery latency, and does the current architecture meet it during SMS provider degradation?

## Durable Record

- If the user asks to save, or the workspace uses `docs/audits/`, write to `docs/audits/YYYY-MM-DD-<target-slug>.md`.
- Otherwise, keep the review in the reply.

## Reference

The full lenses framework with all 40+ named lenses, cross-cutting tensions table, and weighting-by-system-type table:

**`docs/references/system-design-dimensions.md`**

Read this reference when you need:
- The specific lenses within a category for deep analysis
- The weighting table to select deep lenses for an archetype
- The tensions table as a prompt source
- Details on a specific lens the user asks about by name

Do not read during screening — sentinel questions are sufficient for that stage.

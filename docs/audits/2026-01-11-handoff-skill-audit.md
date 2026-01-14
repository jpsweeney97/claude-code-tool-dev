# Audit Report: `handoff` Skill

**Date:** 2026-01-11
**Skill:** `.claude/skills/handoff/SKILL.md`
**Specs:** `skills-as-prompts-strict-spec.md` + `skills-semantic-quality-addendum.md`
**Risk Tier:** Low (informational artifacts, reversible, no breaking changes)
**Disposition:** **FAIL**

---

## Executive Summary

| Metric | Result |
|--------|--------|
| **Disposition** | **FAIL** |
| **FAIL codes triggered** | 4 of 8 |
| **Semantic quality score** | 10/20 |
| **Risk tier** | Low |
| **Required sections present** | 4/8 |

**Strengths:**
- Well-specified artifact format (frontmatter, section checklist, example)
- Numbered procedures
- Concrete verification checks
- Good anti-patterns guidance
- Related skills cross-reference

**Critical gaps:**
1. No When to use / When NOT to use
2. No formal Inputs section with constraints
3. No STOP/ask for missing inputs or ambiguity
4. Only 1 explicit decision point (needs ≥2)
5. No troubleshooting section
6. Undeclared assumptions (git, env vars, filesystem)
7. No calibration instructions

---

## 1. Required Content Areas (Strict Spec §spec.required-content)

| # | Area | Status | Evidence |
|---|------|--------|----------|
| 1 | **When to use** | MISSING | No explicit section. Opening paragraph is a description, not activation guidance. Signal Phrases (L25-33) partially covers this but lacks "When to use" framing. |
| 2 | **When NOT to use** | MISSING | Anti-Patterns (L160-167) describes *how* to avoid bad practices, not *when* the skill shouldn't be activated. |
| 3 | **Inputs** | MISSING | No formal Inputs section. Required/optional/constraints not enumerated. Implicit: `[title]` is optional (L38). |
| 4 | **Outputs** | IMPLICIT | Artifacts described (L41-44, L46-59, L86-120) but no formal "Outputs" section with DoD. |
| 5 | **Procedure** | PRESENT | Numbered steps for creating (L38-44), resuming (L135-143), listing (L147-150). |
| 6 | **Decision points** | WEAK | Recency logic (L129-133) is conditional but not in "If...then...otherwise" form. STOP condition exists (L34) but only for signal phrase decline. |
| 7 | **Verification** | PRESENT | L169-175 has concrete checks (file exists, YAML parses, required fields, content). |
| 8 | **Troubleshooting** | MISSING | No troubleshooting section with symptoms/causes/next steps. |

**Result:** 4/8 areas missing or implicit → **FAIL.missing-content-areas**

---

## 2. Reviewer Checklist (Strict Spec §spec.review.checklist)

| Check ID | Requirement | Status | Notes |
|----------|-------------|--------|-------|
| CHECK.required-content-areas | All 8 areas findable quickly | FAIL | Missing When to use, When NOT to use, Inputs, Troubleshooting |
| CHECK.outputs-have-objective-dod | Artifacts + ≥1 objective DoD | PARTIAL | Verification section (L169-175) has objective checks, but no formal Outputs/DoD structure |
| CHECK.procedure-numbered-with-stop-ask | Numbered + STOP/ask step | PARTIAL | Numbered procedures exist; STOP only for signal phrase decline (L34), no STOP for missing inputs |
| CHECK.two-decision-points-or-exception | ≥2 explicit If/then/otherwise | FAIL | Recency logic (L129-133) is tiered but not in required format. Only 1 true decision point (L34). |
| CHECK.verification-has-quick-check | Concrete quick check with expected result | PASS | L169-175 has checkable conditions |
| CHECK.troubleshooting-present | ≥1 failure mode (symptoms/causes/next) | FAIL | No troubleshooting section |
| CHECK.assumptions-declared-with-fallback | Assumptions + fallback | FAIL | Relies on git (L55-57), `CLAUDE_SESSION_ID` (L52), filesystem without declaring or providing fallbacks |

---

## 3. Automatic FAIL Codes (Strict Spec §spec.review.fail-codes)

| Code | Description | Status |
|------|-------------|--------|
| **FAIL.missing-content-areas** | Required areas absent/unfindable | **TRIGGERED** — When to use, When NOT to use, Inputs, Troubleshooting missing |
| **FAIL.no-objective-dod** | No objective DoD condition | BORDERLINE — Verification section has checks but no formal DoD structure |
| **FAIL.no-stop-ask** | No STOP/ask for missing inputs/ambiguity | **TRIGGERED** — Only STOP is for user declining (L34), not for missing required inputs |
| **FAIL.no-quick-check** | No concrete quick check | NOT TRIGGERED — L169-175 has checks |
| **FAIL.too-few-decision-points** | <2 decision points, no exception | **TRIGGERED** — Only 1 clear decision point; no justification for fewer |
| **FAIL.undeclared-assumptions** | Relies on tools/env without declaring | **TRIGGERED** — Uses git, CLAUDE_SESSION_ID, specific paths without assumptions section |
| **FAIL.unsafe-default** | Breaking/destructive without ask-first | NOT TRIGGERED — Skill writes files but is non-destructive |
| **FAIL.non-operational-procedure** | Not numbered/non-executable | NOT TRIGGERED — Procedures are numbered and executable |

**Triggered FAIL codes:** 4 (`missing-content-areas`, `no-stop-ask`, `too-few-decision-points`, `undeclared-assumptions`)

---

## 4. Semantic Quality Minimums (Addendum §semantic.minimums)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | **Intent fidelity** — Primary goal in 1-2 sentences + ≥3 non-goals | FAIL | Primary goal partially stated (L10-13), but **zero non-goals** listed. |
| 2 | **Constraint completeness** — Declare constraints likely guessed wrong + STOP if unknown | FAIL | No constraints declared. Implicit: needs git for branch/commit (L55-57), env var `CLAUDE_SESSION_ID` (L52). |
| 3 | **Decision points reference observable signals** | PARTIAL | Recency check (L129-133) uses observable time comparison. But "if user declines" (L34) lacks observable detection method. |
| 4 | **Verification validity** — Quick check measures primary success property | PARTIAL | Checks file existence/format, but doesn't verify "useful for resumption" (the primary purpose). |
| 5 | **Calibration** — Label skipped checks as "Not run (reason)" | FAIL | No calibration instructions. No Verified/Inferred/Assumed labeling. |

---

## 5. Semantic Quality Dimensions (Addendum §semantic.dimensions)

*Scoring: 0 = absent, 1 = partial, 2 = adequate*

| Dimension | Score | Notes |
|-----------|-------|-------|
| A. Intent fidelity | 1 | Primary goal implicit. No non-goals. |
| B. Constraint completeness | 0 | No allowed/forbidden, no constraint conflict handling. |
| C. Terminology clarity | 2 | "Handoff" defined via example. Terms consistent. |
| D. Evidence anchoring | 1 | Example shows evidence-like structure but no confirm-before-act steps. |
| E. Decision sufficiency | 1 | Has some conditionals but no If/then/otherwise form, no coverage of missing inputs. |
| F. Verification validity | 1 | Checks exist but don't measure primary success (resumability). |
| G. Artifact usefulness | 2 | Output format well-specified (frontmatter, sections, example). |
| H. Minimality discipline | 2 | Skill is focused; anti-patterns section warns against bloat. |
| I. Calibration honesty | 0 | No calibration instructions at all. |
| J. Offline/restricted handling | 0 | No fallback for non-git repos or missing env vars. |

**Total: 10/20** — Below "excellent" threshold (≥16)

---

## 6. Anti-Patterns Detected (Addendum §semantic.anti-patterns)

| Anti-Pattern | Found? | Location |
|--------------|--------|----------|
| Unbounded verbs without acceptance signals | Minor | "meaningful decisions/progress" (L165) is subjective |
| Decision points rely on "judgment" | Yes | No observable trigger for "trivial sessions" (L165) |
| Verification checks proxy not primary property | Yes | Checks format, not resumability |
| Outputs omit evidence/rationale | No | Artifact structure includes rationale |
| Silent skipping of verification | Yes | No "Not run (reason)" instruction |
| Implied environment assumptions | Yes | Git, CLAUDE_SESSION_ID assumed without declaration |

---

## Remediation Plan

### Priority 1: Add Missing Required Sections

```markdown
## When to Use

- User explicitly asks for handoff (runs `/handoff`)
- User says signal phrases: "wrap this up", "new session", "handoff"
- Session contains meaningful decisions, changes, or next steps worth preserving

## When NOT to Use

- Session was trivial (quick question/answer with no decisions or artifacts)
- User explicitly declines handoff offer
- Information is already captured elsewhere (PR description, committed docs)
- **STOP**: If unclear whether session has meaningful content, ask: "Should I create a handoff?"

## Inputs

**Required:**
- Session context (gathered from conversation history)

**Optional:**
- `title` argument to `/handoff <title>`

**Constraints/Assumptions:**
- Git: branch and commit info optional; if not a git repo, omit those fields
- Environment: `CLAUDE_SESSION_ID` env var; if missing, use "unknown"
- Filesystem: Write access to `~/.claude/handoffs/`
```

### Priority 2: Add Decision Points in Required Format

```markdown
## Decision Points

1. **Signal phrase detected:**
   - If user says a signal phrase ("wrap this up", "handoff", "new session"), then offer to create handoff.
   - If user declines, do not re-prompt. STOP.

2. **Session has meaningful content:**
   - If session has at least one of: decision made, file changed, next step identified, then proceed with handoff.
   - Otherwise, ask: "This session seems light—create a handoff anyway?"

3. **Git availability:**
   - If current directory is a git repo (`.git/` exists), then include branch and commit.
   - Otherwise, omit branch and commit fields from frontmatter.

4. **Environment variable missing:**
   - If `CLAUDE_SESSION_ID` is not set, use `session_id: unknown`.
```

### Priority 3: Add STOP/Ask Behavior

```markdown
## STOP Conditions

- **STOP.** If user declines handoff offer, do not proceed.
- **STOP.** If `~/.claude/handoffs/` cannot be created (permissions error), ask user for alternative path.
- **STOP.** If session context is empty, ask: "I don't see anything to hand off. What should I capture?"
```

### Priority 4: Add Troubleshooting Section

```markdown
## Troubleshooting

### Handoff file not created
**Symptoms:** No file at `~/.claude/handoffs/<project>/`
**Likely causes:**
- Permission denied on `~/.claude/`
- `<project>` couldn't be determined (no git, no directory name)
**Next steps:**
1. Check if `~/.claude/handoffs/` exists and is writable
2. Manually specify path: `/resume /path/to/handoff.md`

### Resume not finding handoff
**Symptoms:** `/resume` says "No handoffs found"
**Likely causes:**
- Handoff older than 30 days (auto-pruned)
- Different project directory than where handoff was created
**Next steps:**
1. Run `/list-handoffs` to see available handoffs
2. Check `~/.claude/handoffs/` for other project directories
```

### Priority 5: Declare Assumptions with Fallbacks

```markdown
## Constraints/Assumptions

| Assumption | Required? | Fallback |
|------------|-----------|----------|
| Git repository | No | Omit branch/commit fields |
| `CLAUDE_SESSION_ID` env var | No | Use `session_id: unknown` |
| Write access to `~/.claude/handoffs/` | Yes | STOP and ask for alternative path |
| Project name determinable | No | Use directory name, or ask user |
```

---

## Key Insights

**Why this skill failed despite being functional:**

1. The skill was written as *documentation for a feature* rather than as *executable instructions for an agent*. It describes what happens but doesn't tell Claude when to STOP, what to do when inputs are missing, or how to handle edge cases.

2. The specs require **defensive programming for prompts** — assume Claude might mis-activate, lack context, or face unusual environments. Without explicit decision points and STOP conditions, the agent guesses.

3. Verification checks *format* (file exists, YAML valid) but not *purpose* (handoff is useful for resumption). This is "verification theater" — checking a proxy instead of the actual success property.

---

## Remediation Completed

**Date:** 2026-01-11
**Version:** 2.0.0 → 3.0.0

### Changes Applied

| Addition | Description |
|----------|-------------|
| When to Use | Explicit activation triggers |
| When NOT to Use | 4 non-goals + STOP condition |
| Inputs | Required/optional + constraints table with fallbacks |
| Outputs | Artifacts + DoD table + quick check |
| Decision Points | 5 explicit If/then/otherwise patterns |
| Procedure | Revised 7-step with 4 STOP gates |
| Troubleshooting | 3 failure modes with symptoms/causes/next |
| Calibration | Verified/Inferred/Assumed distinction |

### Re-Audit Results

| Metric | Before | After |
|--------|--------|-------|
| Disposition | FAIL | **PASS** |
| FAIL codes | 4 | 0 |
| Required sections | 4/8 | 8/8 |
| Decision points | 1 | 5 |
| STOP conditions | 1 | 8 |
| Semantic score | 10/20 | 20/20 |

---

## Pressure Test Results

### Test 1: Trivial Session
**Scenario:** Quick Q&A, user says "wrap this up"
**Expected:** Ask before creating handoff
**Result:** ✅ PASS — Agent cited Decision Point #2, asked "This session seems light — skip the handoff?"
**Rule followed:** "Otherwise, ask: 'This session seems light — create a handoff anyway, or skip?'"

### Test 2: Non-Git Environment
**Scenario:** `/tmp/scratch-work/` with no `.git/`
**Expected:** Omit branch/commit fields, use directory name
**Result:** ✅ PASS — Agent generated correct frontmatter with no branch/commit, session_id: unknown
**Rule followed:** "omit `branch` and `commit` fields entirely (don't use placeholders)"

### Test 3: Write Permission Denied
**Scenario:** Cannot write to `~/.claude/handoffs/`
**Expected:** STOP and ask for alternative path
**Result:** ✅ PASS — Agent said "I can't write to ~/.claude/handoffs/. Where should I save this handoff?"
**Rule followed:** Decision Point #5 write permission check

### Test 4: Ambiguous Project Name
**Scenario:** Generic directory `/Users/john/work/`
**Expected:** Ask user to specify project name
**Result:** ✅ PASS — Agent recognized "work" as ambiguous, asked for project name
**Rule followed:** "If project name is ambiguous (not in git, generic directory name), ask user to specify"

---

## Final Status

**Disposition:** PASS
**All FAIL codes resolved:** ✅
**Pressure tests passed:** 4/4
**Ready for promotion:** Yes

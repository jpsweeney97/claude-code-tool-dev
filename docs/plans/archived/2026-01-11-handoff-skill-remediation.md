# Remediation Plan: `handoff` Skill

**Date:** 2026-01-11
**Audit:** `docs/audits/2026-01-11-handoff-skill-audit.md`
**Target:** `.claude/skills/handoff/SKILL.md`
**Approach:** TDD-style remediation — audit = failing test, remediation = fix, re-audit = green

---

## Context

The handoff skill is **functional but non-compliant**. It works in practice but violates 4 of 8 automatic FAIL codes in the strict spec. The audit identified the skill was written as *feature documentation* rather than *executable agent instructions*.

**Core insight:** The skill tells Claude *what happens* but not *what to do when things are unclear*. Missing STOP conditions, decision points, and assumptions declarations mean Claude guesses under pressure.

---

## FAIL Codes to Resolve

| Code | Issue | Section to Add/Fix |
|------|-------|-------------------|
| `FAIL.missing-content-areas` | Missing 4 of 8 required sections | Add: When to Use, When NOT to Use, Inputs, Troubleshooting |
| `FAIL.no-stop-ask` | No STOP for missing inputs/ambiguity | Add STOP conditions throughout procedure |
| `FAIL.too-few-decision-points` | Only 1 explicit decision point | Add ≥2 If/then/otherwise decision points |
| `FAIL.undeclared-assumptions` | Git, env vars, filesystem assumed | Add Constraints/Assumptions section with fallbacks |

---

## Remediation Steps

### Phase 1: Add Missing Required Sections

#### 1.1 Add "When to Use" Section

**Location:** After frontmatter, before Commands table

**Content:**
```markdown
## When to Use

- User explicitly runs `/handoff` or `/handoff <title>`
- User says signal phrases: "wrap this up", "new session", "handoff"
- Session contains at least one of: decision made, file changed, gotcha discovered, next step identified
- User is stopping work and wants to resume later with context
```

**Rationale:** Converts implicit activation triggers into explicit guidance. The signal phrases are already in the skill but buried — elevating them to "When to Use" makes activation boundaries clear.

---

#### 1.2 Add "When NOT to Use" Section

**Location:** Immediately after "When to Use"

**Content:**
```markdown
## When NOT to Use

- Session was trivial (quick Q&A with no decisions, changes, or learnings)
- User explicitly declines handoff offer
- Context is already captured elsewhere (PR description, committed docs, issue tracker)
- Session is exploratory research with no actionable next steps

**STOP condition:** If unclear whether session has meaningful content, ask: "Should I create a handoff? This session seems light on decisions/changes."
```

**Rationale:** Addresses the anti-pattern of "handoff for trivial sessions" (L165 in current skill) by making it a formal non-goal with an explicit STOP.

---

#### 1.3 Add "Inputs" Section

**Location:** After "When NOT to Use", before "Commands"

**Content:**
```markdown
## Inputs

**Required:**
- Session context (gathered from conversation history)

**Optional:**
- `title` argument for `/handoff <title>` — if omitted, Claude generates a descriptive title

**Constraints/Assumptions:**

| Assumption | Required? | Fallback |
|------------|-----------|----------|
| Git repository | No | Omit `branch` and `commit` fields from frontmatter |
| `CLAUDE_SESSION_ID` env var | No | Use `session_id: unknown` |
| Write access to `~/.claude/handoffs/` | Yes | **STOP** and ask for alternative path |
| Project name determinable | No | Use parent directory name; if ambiguous, ask user |

**STOP condition:** If `~/.claude/handoffs/` doesn't exist and cannot be created, STOP and ask: "I can't write to ~/.claude/handoffs/. Where should I save handoffs?"
```

**Rationale:** Makes implicit assumptions explicit. The skill currently uses git branch/commit (L55-57) and `CLAUDE_SESSION_ID` (L52) without declaring them. Adding fallbacks prevents failures in non-git or unusual environments.

---

#### 1.4 Add "Troubleshooting" Section

**Location:** After "Verification", before "Related Skills"

**Content:**
```markdown
## Troubleshooting

### Handoff file not created

**Symptoms:** `/handoff` completes but no file appears at `~/.claude/handoffs/<project>/`

**Likely causes:**
- Permission denied on `~/.claude/` directory
- Project name couldn't be determined (not in git, ambiguous directory)
- Disk full or path too long

**Next steps:**
1. Check if `~/.claude/handoffs/` exists: `ls -la ~/.claude/handoffs/`
2. Check write permissions: `touch ~/.claude/handoffs/test && rm ~/.claude/handoffs/test`
3. If permissions issue, ask user for alternative path
4. If project undetermined, ask user to specify project name

---

### Resume not finding handoff

**Symptoms:** `/resume` says "No handoffs found" or finds wrong handoff

**Likely causes:**
- Handoff older than 30 days (auto-pruned by retention policy)
- Running from different project directory than where handoff was created
- Handoff saved with different project name

**Next steps:**
1. Run `/list-handoffs` to see available handoffs across all projects
2. Check `~/.claude/handoffs/` directly for other project directories
3. If found in different project, use `/resume <full-path>`

---

### Handoff content missing key decisions

**Symptoms:** Resumed handoff lacks important context from original session

**Likely causes:**
- Handoff created too early (before key decisions made)
- Section checklist didn't capture all relevant categories
- Session had implicit decisions not stated explicitly

**Next steps:**
1. Review session history for decisions made after handoff
2. Create new handoff with more complete context
3. Consider adding to existing handoff manually if file still accessible
```

**Rationale:** Required by spec — at least one failure mode with symptoms/causes/next steps. Added three because handoffs have multiple failure modes users actually encounter.

---

### Phase 2: Add Decision Points

**Location:** New section after "Commands", or integrated into "Creating a Handoff"

**Content:**
```markdown
## Decision Points

1. **Signal phrase detected:**
   - If user says "wrap this up", "new session", or "handoff", then offer to create handoff: "Create a handoff before ending?"
   - If user declines, **STOP**. Do not re-prompt or proceed.

2. **Session content assessment:**
   - If session contains at least one of: decision made, file changed, gotcha discovered, next step identified, then proceed with handoff.
   - Otherwise, ask: "This session seems light — create a handoff anyway, or skip?"

3. **Git repository detection:**
   - If `.git/` directory exists in current or parent directories, then include `branch` and `commit` in frontmatter.
   - Otherwise, omit `branch` and `commit` fields entirely (don't use placeholders).

4. **Environment variable availability:**
   - If `CLAUDE_SESSION_ID` is set, use it for `session_id`.
   - Otherwise, use `session_id: unknown`.

5. **Write permission check:**
   - If `~/.claude/handoffs/<project>/` is writable (or can be created), write handoff there.
   - Otherwise, **STOP** and ask: "Can't write to ~/.claude/handoffs/. Where should I save this handoff?"
```

**Rationale:** Converts implicit conditionals into explicit If/then/otherwise format. The recency logic in "Resuming from Handoff" (L129-133) is already good — these add decision points for the *creation* flow which was lacking.

---

### Phase 3: Add STOP/Ask Behavior

**Integrate into existing procedure at L38-44:**

**Current:**
```markdown
1. **Gather context** from the session
2. **Select relevant sections** using the checklist below (omit empty sections)
3. **Generate markdown** with frontmatter
4. **Write directly** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
5. **Confirm:** "Handoff saved: <title> (N decisions, N changes, N next steps)"
```

**Revised:**
```markdown
1. **Check prerequisites:**
   - If session appears trivial (no decisions, changes, or learnings), ask: "This session seems light — create a handoff anyway?"
   - If user declines any offer, **STOP**. Do not proceed.

2. **Gather context** from the session

3. **Select relevant sections** using the checklist below
   - If no sections have content, **STOP** and ask: "I don't see anything to hand off. What should I capture?"
   - Omit empty sections from output

4. **Determine output path:**
   - If `~/.claude/handoffs/<project>/` is not writable, **STOP** and ask for alternative path
   - If project name is ambiguous, ask user to specify

5. **Generate markdown** with frontmatter
   - Use fallbacks for optional fields (see Inputs → Constraints/Assumptions)

6. **Write file** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`

7. **Verify and confirm:**
   - Run verification checks (see Verification section)
   - Confirm: "Handoff saved: <title> (N decisions, N changes, N next steps)"
```

**Rationale:** Adds explicit STOP points for: trivial sessions, empty content, write failures. Currently the procedure assumes everything works — this makes failure modes explicit.

---

### Phase 4: Add Outputs Section with DoD

**Location:** After "Inputs", before "Commands"

**Content:**
```markdown
## Outputs

**Artifacts:**
- Markdown file at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
- Frontmatter with session metadata (date, time, session_id, project, title, files)
- Body with relevant sections from checklist (only non-empty sections included)

**Definition of Done:**

| Check | Expected |
|-------|----------|
| File exists at expected path | `ls ~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_*.md` returns file |
| Frontmatter parses as valid YAML | No YAML syntax errors |
| Required fields present | `date`, `time`, `session_id`, `project`, `title` all have values |
| At least one body section | File contains at least one H2 section with content |
| Content is resumable | Reading the handoff provides enough context to continue work |

**Quick check:** After writing, verify file exists and contains the title. If missing, check write permissions and retry.
```

**Rationale:** The current Verification section (L169-175) has good checks but they're not framed as DoD. This adds the formal structure the spec requires and includes the "primary success property" check (content is resumable).

---

### Phase 5: Semantic Quality Improvements

#### 5.1 Add Non-Goals

**Location:** In "When NOT to Use" section

**Add:**
```markdown
**Non-goals (this skill does NOT):**
- Replace proper documentation (handoffs are ephemeral, docs are permanent)
- Capture every detail (focus on decisions and next steps, not transcript)
- Work across different machines (handoffs are local to `~/.claude/`)
- Version control handoffs (they're working documents, not artifacts)
```

---

#### 5.2 Add Calibration Instructions

**Location:** In procedure or as note in Section Checklist

**Add:**
```markdown
**Calibration note:** When selecting sections, distinguish:
- **Verified:** Things explicitly discussed or shown in session (decisions, file changes)
- **Inferred:** Reasonable conclusions from session (likely next steps)
- **Assumed:** Background context not verified this session (existing architecture)

Label uncertain items appropriately. If a section would be mostly assumed, consider omitting it.
```

---

## Verification Plan

After implementing changes, re-audit against both specs:

### Strict Spec Checklist

- [ ] All 8 required content areas present and findable
- [ ] Outputs include artifacts + objective DoD
- [ ] Procedure numbered with ≥1 STOP/ask step
- [ ] ≥2 explicit If/then/otherwise decision points
- [ ] Verification has concrete quick check with expected result
- [ ] Troubleshooting has ≥1 failure mode (symptoms/causes/next)
- [ ] Assumptions declared with fallbacks

### FAIL Code Resolution

- [ ] `FAIL.missing-content-areas` — All 8 sections present
- [ ] `FAIL.no-stop-ask` — Multiple STOP conditions added
- [ ] `FAIL.too-few-decision-points` — 5 decision points added
- [ ] `FAIL.undeclared-assumptions` — Constraints table with fallbacks

### Semantic Quality Targets

- [ ] Primary goal clear (1-2 sentences)
- [ ] ≥3 non-goals listed
- [ ] Decision points use observable signals
- [ ] Verification measures primary success (resumability)
- [ ] Calibration instructions present

---

## Implementation Order

1. **Add structural sections first** (When to Use, When NOT to Use, Inputs, Outputs, Troubleshooting)
2. **Add Decision Points section** (new section with 5 points)
3. **Revise Procedure** to include STOP conditions
4. **Add semantic improvements** (non-goals, calibration)
5. **Re-audit** against both specs
6. **Test with pressure scenarios** (per writing-skills TDD approach)

---

## Pressure Scenarios for Testing

Per writing-skills guidance, test the remediated skill under pressure:

### Scenario 1: Trivial Session
**Setup:** Quick Q&A with no decisions or changes
**Pressure:** User says "wrap this up"
**Expected:** Claude asks if handoff is needed, respects decline

### Scenario 2: Non-Git Environment
**Setup:** Directory without `.git/`
**Pressure:** User requests handoff
**Expected:** Claude omits branch/commit gracefully, doesn't error

### Scenario 3: Write Permission Denied
**Setup:** `~/.claude/handoffs/` not writable
**Pressure:** User requests handoff
**Expected:** Claude STOPs and asks for alternative path

### Scenario 4: Ambiguous Project
**Setup:** Not in git, generic directory name like "work"
**Pressure:** User requests handoff
**Expected:** Claude asks user to specify project name

---

## Success Criteria

- [ ] All FAIL codes resolved (0 triggered)
- [ ] Semantic quality score ≥16/20
- [ ] All 4 pressure scenarios pass
- [ ] Re-audit disposition: **PASS** or **PASS-WITH-NOTES**

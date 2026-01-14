# Auditing Tool Designs: Phase 0 Context Assessment

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add context assessment phase to auditing-tool-designs skill so severity is calibrated to deployment scope, input trust, and stakes—preventing miscalibrated audits that apply enterprise security to personal dev tools.

**Architecture:** Insert Phase 0 before lens execution. Interactive 3-question assessment → calibration level (Light/Standard/Deep) → context injected into all lens prompts via `{{CONTEXT_ASSESSMENT}}` and `{{SEVERITY_CALIBRATION}}` template variables.

**Tech Stack:** Markdown skill files, no code changes

---

## Task 1: Create Context Assessment Framework

**Files:**
- Create: `.claude/skills/auditing-tool-designs/references/context-assessment.md`

**Step 1: Create the context assessment reference file**

```markdown
# Context Assessment Framework

This framework calibrates audit severity based on deployment context. Applied before lenses execute.

## Interactive Assessment Questions

Three questions determine calibration level:

### Q1: Deployment Scope
> "Who will use this {{ARTIFACT_TYPE}}?"

| Answer | Score | Meaning |
|--------|-------|---------|
| Personal (just me) | +1 | No external users; mistakes affect only developer |
| Team (internal users) | +2 | Trusted users; mistakes affect productivity |
| Public (external consumers) | +3 | Untrusted users; mistakes affect security/reputation |

### Q2: Input Trust Level
> "Who controls the inputs this tool will process?"

| Answer | Score | Meaning |
|--------|-------|---------|
| Developer-controlled | +1 | Config files, env vars, version-controlled data |
| Internal users | +2 | Team members, authenticated users |
| External/untrusted | +3 | User uploads, public API, external data |

### Q3: Failure Impact
> "What happens if this tool has a bug or security issue?"

| Answer | Score | Meaning |
|--------|-------|---------|
| Learning/experiment | +1 | No real impact; safe to fail |
| Internal tool | +2 | Team inconvenience; recoverable |
| Production system | +3 | Data loss, security breach, outage |

## Calibration Levels

Sum the scores (range: 3-9):

| Score | Level | Behavior |
|-------|-------|----------|
| 3-5 | Light | Focus on correctness; skip theoretical security risks |
| 6-7 | Standard | Full methodology; normal thresholds |
| 8-9 | Deep | Strict thresholds; adversarial mindset |

## Severity Calibration Matrix

Severity thresholds vary by context:

| Context | Critical | Major | Minor |
|---------|----------|-------|-------|
| **Light** (trusted inputs, personal) | N/A—no external attack surface | Design flaw that breaks functionality | Style/convention deviation |
| **Standard** (mixed trust, team) | Privilege escalation within trust boundary | Feature doesn't work as designed | Non-compliance with standards |
| **Deep** (untrusted inputs, public) | Exploitable by external actors | Requires elevated access to exploit | Theoretical with no plausible path |

## Exploitability Standards

Security findings require exploitability assessment:

| Input Source | Standard |
|--------------|----------|
| Developer-controlled (env vars, config) | Admin already has access; not externally exploitable |
| Version-controlled files | Attacker needs commit access; not externally exploitable |
| User input (forms, API) | Externally exploitable; full security review |
| External data (APIs, uploads) | High risk; assume hostile |

**Anti-pattern:** Flagging developer-controlled configuration as "path traversal" or "injection" without demonstrating an external attack path.

## Template Variables

After assessment, populate these for lens injection:

### {{CONTEXT_ASSESSMENT}}
```
Deployment scope: [Personal/Team/Public]
Input trust level: [Trusted/Partial/Untrusted]
Failure impact: [Low/Medium/High]
Calibration: [Light/Standard/Deep] (score: X)
```

### {{SEVERITY_CALIBRATION}}
```
For this [Light/Standard/Deep] audit:
- Critical: [context-specific definition from matrix]
- Major: [context-specific definition from matrix]
- Minor: [context-specific definition from matrix]
```
```

**Step 2: Verify file created**

Run: `ls -la .claude/skills/auditing-tool-designs/references/context-assessment.md`
Expected: File exists with correct path

**Step 3: Commit**

```bash
git add .claude/skills/auditing-tool-designs/references/context-assessment.md
git commit -m "feat(auditing-tool-designs): add context assessment framework"
```

---

## Task 2: Update SKILL.md with Phase 0

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/SKILL.md`

**Step 1: Add context assessment to Inputs section**

After line ~90 (after "Mode Detection" section), add:

```markdown
### Context Assessment

Context is gathered interactively via AskUserQuestion before lens execution. See [references/context-assessment.md](references/context-assessment.md) for the full framework.

**Questions asked:**
1. Deployment scope (Personal/Team/Public)
2. Input trust level (Trusted/Partial/Untrusted)
3. Failure impact (Low/Medium/High)

**Output:** Calibration level (Light/Standard/Deep) that adjusts severity thresholds across all lenses.
```

**Step 2: Insert Step 2.5 in Procedure section**

After "Step 2: Detect artifact type" (around line 145), insert:

```markdown
### Step 2.5: Assess context

Gather context to calibrate severity across all lenses.

Use AskUserQuestion tool with 3 questions:

**Q1:** "Who will use this {{ARTIFACT_TYPE}}?"
- Personal (just me)
- Team (internal users)
- Public (external consumers)

**Q2:** "Who controls the inputs this tool will process?"
- Developer-controlled (config files, env vars, version-controlled data)
- Internal users (team members, authenticated users)
- External/untrusted (user uploads, public API, external data)

**Q3:** "What happens if this tool has a bug or security issue?"
- Learning/experiment (no real impact)
- Internal tool (team inconvenience)
- Production system (data loss, security breach, outage)

Calculate calibration level per `references/context-assessment.md`.

- **Success:** `{{CONTEXT_ASSESSMENT}}` and `{{SEVERITY_CALIBRATION}}` populated
- **Failure:** User cannot answer → Use "Standard" calibration with warning
```

**Step 3: Add Decision Point DP2.5**

After "DP2: Design Stage Confirmation" (around line 222), insert:

```markdown
### DP2.5: Context Calibration
**Observable trigger:** User answers to 3 context questions
- If score 3-5: Light calibration (relaxed severity)
- If score 6-7: Standard calibration (normal thresholds)
- If score 8-9: Deep calibration (strict thresholds)
- If user cannot answer: Standard calibration with warning
```

**Step 4: Update Step 6 (Build lens prompts)**

Modify the existing Step 6 description to include:

```markdown
### Step 6: Build lens prompts
Inject specs AND context into 4 lens prompt templates from `lenses/` directory.
- **Success:** All prompts populated with {{ARTIFACT_TYPE}}, {{ARTIFACT_SPECS}}, {{TARGET_CONTENT}}, {{CONTEXT_ASSESSMENT}}, {{SEVERITY_CALIBRATION}}
- **Failure:** Template not found → STOP with error
```

**Step 5: Verify changes**

Run: `grep -n "CONTEXT_ASSESSMENT\|Step 2.5\|DP2.5" .claude/skills/auditing-tool-designs/SKILL.md`
Expected: Multiple matches showing new content

**Step 6: Commit**

```bash
git add .claude/skills/auditing-tool-designs/SKILL.md
git commit -m "feat(auditing-tool-designs): add Phase 0 context assessment to procedure"
```

---

## Task 3: Update Spec Auditor Lens

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/lenses/spec-auditor.md`

**Step 1: Add context injection block**

After line 1 ("# Spec Auditor Lens"), insert:

```markdown
## Context for This Audit
{{CONTEXT_ASSESSMENT}}

## Severity Calibration
{{SEVERITY_CALIBRATION}}

---
```

**Step 2: Update severity criteria**

Replace the existing "## Severity Criteria" section (around line 40) with:

```markdown
## Severity Criteria

Apply thresholds from {{SEVERITY_CALIBRATION}} above. General guidance:

- **Critical:** Per calibration—typically violations that make the design non-functional or exploitable by the defined threat actors
- **Major:** Per calibration—typically violations that cause problems but may work
- **Minor:** Per calibration—typically style/convention issues

**Key constraint:** For Light calibration (trusted inputs, personal tools), "Critical" requires the design to be broken, not theoretically vulnerable.
```

**Step 3: Verify changes**

Run: `head -20 .claude/skills/auditing-tool-designs/lenses/spec-auditor.md`
Expected: Shows context injection block at top

**Step 4: Commit**

```bash
git add .claude/skills/auditing-tool-designs/lenses/spec-auditor.md
git commit -m "feat(auditing-tool-designs): add context injection to spec-auditor lens"
```

---

## Task 4: Update Behavioral Realist Lens

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/lenses/behavioral-realist.md`

**Step 1: Add context injection block**

After line 1 ("# Behavioral Realist Lens"), insert:

```markdown
## Context for This Audit
{{CONTEXT_ASSESSMENT}}

## Severity Calibration
{{SEVERITY_CALIBRATION}}

---
```

**Step 2: Update severity criteria**

Replace the existing "## Severity Criteria" section (around line 64) with:

```markdown
## Severity Criteria

Apply thresholds from {{SEVERITY_CALIBRATION}} above. General guidance:

- **Critical:** Per calibration—design assumes behavior Claude cannot perform; will fail
- **Major:** Per calibration—design assumes behavior that's unreliable; may fail intermittently
- **Minor:** Per calibration—suboptimal assumption; works but could be improved

**Key constraint:** Behavioral concerns about "unreliable multi-step reasoning" should be Major not Critical unless the design has no fallback.
```

**Step 3: Commit**

```bash
git add .claude/skills/auditing-tool-designs/lenses/behavioral-realist.md
git commit -m "feat(auditing-tool-designs): add context injection to behavioral-realist lens"
```

---

## Task 5: Update Robustness Critic Lens

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/lenses/robustness-critic.md`

**Step 1: Add context injection block**

After line 1 ("# Robustness Critic Lens"), insert:

```markdown
## Context for This Audit
{{CONTEXT_ASSESSMENT}}

## Severity Calibration
{{SEVERITY_CALIBRATION}}

---
```

**Step 2: Update severity criteria**

Replace the existing "## Severity Criteria" section (around line 74) with:

```markdown
## Severity Criteria

Apply thresholds from {{SEVERITY_CALIBRATION}} above. General guidance:

- **Critical:** Per calibration—unhandled failure causes data loss, security breach, or silent corruption given the threat model
- **Major:** Per calibration—unhandled failure causes visible errors but no permanent damage
- **Minor:** Per calibration—edge case unlikely to occur; low impact if it does

**Key constraints:**
- For Light calibration: Security findings require a plausible external attack path
- "Path traversal" in admin-controlled env vars is not Critical (admin already has access)
- "YAML bomb" in version-controlled docs is not Critical (attacker needs commit access)
```

**Step 3: Commit**

```bash
git add .claude/skills/auditing-tool-designs/lenses/robustness-critic.md
git commit -m "feat(auditing-tool-designs): add context injection to robustness-critic lens"
```

---

## Task 6: Update Scope Minimalist Lens

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/lenses/scope-minimalist.md`

**Step 1: Add context injection block**

After line 1 ("# Scope Minimalist Lens"), insert:

```markdown
## Context for This Audit
{{CONTEXT_ASSESSMENT}}

## Severity Calibration
{{SEVERITY_CALIBRATION}}

---
```

**Step 2: Update severity criteria**

Replace the existing "## Severity Criteria" section (around line 68) with:

```markdown
## Severity Criteria

Apply thresholds from {{SEVERITY_CALIBRATION}} above. General guidance:

- **Critical:** Per calibration—complexity blocks adoption; users will abandon before succeeding
- **Major:** Per calibration—unnecessary complexity adds significant cost/latency without value
- **Minor:** Per calibration—could be simpler but functional as-is

**Key constraint:** Scope concerns should be proportional to artifact size. A 270-line tool doesn't need the same infrastructure as a 10,000-line system.
```

**Step 3: Commit**

```bash
git add .claude/skills/auditing-tool-designs/lenses/scope-minimalist.md
git commit -m "feat(auditing-tool-designs): add context injection to scope-minimalist lens"
```

---

## Task 7: Update Arbiter with Validation Checklist

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/arbiter/synthesis-prompt.md`

**Step 1: Add context awareness**

After line 25 ("### Context"), add:

```markdown
### Context Assessment
{{CONTEXT_ASSESSMENT}}

### Severity Calibration
{{SEVERITY_CALIBRATION}}
```

**Step 2: Add validation checklist**

Before "## Output Format" (around line 40), insert:

```markdown
## Pre-Synthesis Validation

Before including any finding in the final report, verify each passes these checks:

- [ ] **Technical accuracy:** Platform-specific claims have evidence (not assumptions)
- [ ] **Exploitability:** Attack paths are plausible given deployment context and input trust level
- [ ] **Proportionality:** Effort estimates scale to artifact size (not enterprise-scale for personal tools)
- [ ] **Alternatives validity:** Any "simpler alternative" meets the same functional requirements

**Handling validation failures:**
- If technical claim cannot be verified → Flag with `⚠️ Unverified: [reason]`
- If attack path requires privileges attacker wouldn't have → Demote severity or exclude
- If effort estimate exceeds 5 days for <500 line artifact → Review proportionality
- If alternative doesn't meet requirements → Remove the alternative suggestion
```

**Step 3: Add proportionality guidance to Prioritization Criteria**

Update the "## Prioritization Criteria" section to include:

```markdown
## Prioritization Criteria

Rank findings by:
1. **Convergence count** — More lenses = higher confidence = higher priority
2. **Severity (calibrated)** — Apply {{SEVERITY_CALIBRATION}} thresholds
3. **Effort to fix** — Low-effort fixes get priority boost
4. **Classification** — Verified > Inferred > Assumed

**Proportionality check:** Total remediation effort should be proportional to artifact size:
- Personal tools (<500 lines): 1-3 days typical
- Team tools (500-2000 lines): 3-7 days typical
- Public APIs (2000+ lines): 7-20 days typical

If estimates exceed these ranges, verify each finding is warranted for the calibration level.
```

**Step 4: Commit**

```bash
git add .claude/skills/auditing-tool-designs/arbiter/synthesis-prompt.md
git commit -m "feat(auditing-tool-designs): add validation checklist and proportionality to arbiter"
```

---

## Task 8: Update Output Templates

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/references/output-templates.md`

**Step 1: Add context section to audit-report.md template**

After "**Warnings:**" line (around line 17), insert:

```markdown
---

## Context Assessment

| Factor | Value | Rationale |
|--------|-------|-----------|
| Deployment scope | [Personal/Team/Public] | [who uses this] |
| Input trust level | [Trusted/Partial/Untrusted] | [who controls inputs] |
| Failure impact | [Low/Medium/High] | [what breaks if it fails] |
| **Calibration** | **[Light/Standard/Deep]** | Score: X |

**Severity thresholds for this audit:**
- **Critical:** [context-specific definition]
- **Major:** [context-specific definition]
- **Minor:** [context-specific definition]
```

**Step 2: Add proportionality check before Verdict**

Before "## Verdict" (around line 75), insert:

```markdown
---

## Proportionality Check

| Metric | Value |
|--------|-------|
| Target artifact size | [X lines / Y tokens] |
| Total estimated remediation | [Z days] |
| Ratio | [days per 100 lines] |

*Reference ratios by calibration:*
- Light (personal tools): 0.5-2 days per 100 lines
- Standard (team tools): 2-5 days per 100 lines
- Deep (public APIs): 5-15 days per 100 lines

[Note if ratio exceeds reference range and why]
```

**Step 3: Update JSON schema**

In the `audit-impl-spec.json` schema section, add to `audit_metadata`:

```json
"context": {
  "deployment_scope": "personal|team|public",
  "input_trust": "trusted|partial|untrusted",
  "failure_impact": "low|medium|high",
  "calibration": "light|standard|deep",
  "calibration_score": 3-9
}
```

**Step 4: Commit**

```bash
git add .claude/skills/auditing-tool-designs/references/output-templates.md
git commit -m "feat(auditing-tool-designs): add context and proportionality to output templates"
```

---

## Task 9: Update Fallback Specs with Exploitability

**Files:**
- Modify: `.claude/skills/auditing-tool-designs/references/fallback-specs.md`

**Step 1: Add exploitability section**

At the end of the file, add:

```markdown
---

## Context-Appropriate Severity

Security findings require **exploitability assessment** based on input trust level.

### Exploitability by Input Source

| Input Source | Exploitability Standard |
|--------------|------------------------|
| Developer-controlled (env vars, config files) | Admin already has access; not externally exploitable |
| Version-controlled files | Attacker needs commit access; not externally exploitable |
| User input (forms, API parameters) | Externally exploitable; full security review required |
| External data (APIs, uploads) | High risk; assume hostile input |

### Common False Positives

These patterns are often flagged incorrectly for trusted-input tools:

| Finding | Why It's Often Invalid |
|---------|----------------------|
| "Path traversal in DOCS_PATH env var" | Admin-configured; attacker can't control |
| "YAML bomb vulnerability" | Version-controlled docs; attacker can't inject |
| "SQL injection in config" | Developer-written config; not user input |
| "Command injection in build script" | Developer runs it; not exposed to users |

### Severity Assignment Rules

1. **Critical requires external exploitability** — If an attacker needs admin/commit access, it's not Critical
2. **Major requires realistic scenario** — "Attacker modifies your config file" isn't realistic for most threat models
3. **Minor for defense-in-depth** — Valid hardening suggestions that don't address real threats

### Anti-Pattern

**DON'T:** Flag every theoretical vulnerability as Critical regardless of who controls the input.

**DO:** Ask "Who can trigger this?" before assigning severity. If the answer is "only the developer/admin," it's not externally exploitable.
```

**Step 2: Commit**

```bash
git add .claude/skills/auditing-tool-designs/references/fallback-specs.md
git commit -m "feat(auditing-tool-designs): add exploitability guidance to fallback specs"
```

---

## Task 10: Verification

**Files:**
- Test: The skill itself via `/auditing-tool-designs`

**Step 1: Verify all files were modified**

Run: `git diff --stat HEAD~9`
Expected: 9 files changed (1 created, 8 modified)

**Step 2: Quick functional test**

Create a minimal test design:

```bash
cat > /tmp/test-design.md << 'EOF'
---
name: simple-greeter
description: Says hello to the user
---

# Simple Greeter Skill

## When to Use
When user says hello.

## Procedure
1. Respond with "Hello!"
EOF
```

Run: `/auditing-tool-designs /tmp/test-design.md`

Expected behavior:
1. Skill asks 3 context questions
2. If answered Personal/Developer-controlled/Learning → Light calibration
3. Report includes "Context Assessment" section
4. No Critical findings for this trivial tool

**Step 3: Verify context injection**

Check that lens prompts would receive context:

Run: `grep -l "CONTEXT_ASSESSMENT" .claude/skills/auditing-tool-designs/lenses/*.md`
Expected: All 4 lens files listed

**Step 4: Final commit (if any cleanup needed)**

```bash
git status
# If clean, done. If changes, commit them.
```

---

## Summary

| Task | File | Change |
|------|------|--------|
| 1 | `references/context-assessment.md` | **Created** - Full framework |
| 2 | `SKILL.md` | Added Step 2.5, DP2.5, template vars |
| 3 | `lenses/spec-auditor.md` | Context injection + calibrated severity |
| 4 | `lenses/behavioral-realist.md` | Context injection + calibrated severity |
| 5 | `lenses/robustness-critic.md` | Context injection + calibrated severity |
| 6 | `lenses/scope-minimalist.md` | Context injection + calibrated severity |
| 7 | `arbiter/synthesis-prompt.md` | Validation checklist + proportionality |
| 8 | `references/output-templates.md` | Context section + proportionality check |
| 9 | `references/fallback-specs.md` | Exploitability guidance |
| 10 | — | Verification |

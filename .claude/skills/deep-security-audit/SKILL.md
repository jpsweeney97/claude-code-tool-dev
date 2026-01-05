---
name: deep-security-audit
description: >
  Rigorous static code security review that finds what automated tools miss.
  Uses adversarial thinking, data flow tracing, and CWE classification to identify
  vulnerabilities in source code without execution. Deploys parallel agents with
  four security perspectives, cross-validates findings, and produces actionable reports.
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Deep Security Audit

Static code security review methodology for identifying vulnerabilities through source code analysis. Complements (does not replace) automated tools by focusing on logic vulnerabilities, cross-component issues, and context-dependent patterns that require reasoning.

## When to Use

Use deep-security-audit when:
- You need systematic security review before deployment
- Automated tools have run but you want deeper analysis
- Logic vulnerabilities or authentication/authorization flows need review
- Cross-component data flows require tracing
- You need documented, reproducible security findings

Do not use when:
- Quick syntax check suffices (use linters)
- You need dynamic testing (fuzzing, penetration testing)
- Infrastructure/network security is the focus
- You need to run external security tools (this skill cannot execute tools)

## What This Skill Cannot Do

**Honest limitations:**
- Cannot execute code or run applications
- Cannot perform dynamic testing (fuzzing, penetration testing)
- Cannot interact with live systems or APIs
- Cannot verify runtime behavior or timing attacks
- Cannot test infrastructure or network security
- Cannot run external tools (Semgrep, Bandit, OWASP ZAP)

Some vulnerabilities require runtime verification — these are flagged as "Requires Runtime."

## Triggers

- "Security audit this codebase"
- "Review code for vulnerabilities"
- "Find security issues in this code"
- "Static security analysis of..."
- "Check for injection/auth/crypto vulnerabilities"

## Quick Start

```text
1. Pre-Flight    → Confirm scope, gather context, set calibration
2. Deploy Agents → Four perspectives analyze in parallel
3. Cross-Validate → Reconcile findings, trace data flows, reduce FPs
4. Synthesize    → Produce report with CWE classification
```

**Minimum viable audit:**
```markdown
[ ] Pre-flight: Scope defined, tech stack identified, calibration set
[ ] Agents: Deployed 4 perspectives (Attacker, Controls, Auditor, Design Review)
[ ] Cross-validation: Data flows traced, false positives checked
[ ] Deliverable: Findings with CWE IDs, coverage matrix filled
```

## Calibration

Match rigor to risk:

| Level | When | Agents | Coverage | Time |
|-------|------|--------|----------|------|
| **Light** | Internal tool, quick check | 2 (Attacker + Auditor) | Critical paths, top CWEs | 2-4 hours |
| **Medium** | Standard app, moderate risk | 4 (all perspectives) | All 10 dimensions | 1-2 days |
| **Deep** | High-value, regulated, post-incident | 4 + multiple rounds | Full + chain analysis | 3-5 days |

Default: **Medium**

---

## The Four Phases

### Phase 0: Pre-Flight

**Purpose:** Gather context before analysis.

**Checklist:**
```markdown
[ ] Scope boundaries defined (in-scope / out-of-scope)
[ ] Searched episodic memory for prior audits
[ ] Technology stack identified (languages, frameworks, versions)
[ ] Authentication/authorization model understood
[ ] Data classification known (what's sensitive)
[ ] Prior security assessments reviewed (if any)
[ ] Calibration level set with rationale
```

**Why this matters:** Without context, you'll miss framework-specific protections and waste time on out-of-scope code.

**Tools:**
- `mcp__plugin_episodic-memory_episodic-memory__search` — Prior audit conversations
- Git log for recent security-related changes

### Phase 1: Parallel Agent Deployment

**Purpose:** Analyze from four security perspectives simultaneously.

Deploy agents in a **single message with multiple Task tool calls**:

| Agent | Perspective | Primary Focus |
|-------|-------------|---------------|
| **Attacker** | Offense | Trace data flows from untrusted input to sensitive sinks. "How would I exploit this?" |
| **Controls** | Defense | Verify sanitization exists and is used correctly. "What protections are in place?" |
| **Auditor** | Systematic | Track coverage against CWE categories and code areas. "What haven't we examined?" |
| **Design Review** | Architecture | Assess trust boundaries and secure defaults. "Is the design sound?" |

**Agent Requirements:**
- Model: High-capability model (currently `opus`; use highest available)
- Type: `Explore`
- Must trace data flows with source → propagation → sink
- Must cite evidence: file paths, line numbers, code snippets
- Must report what was examined and found secure (negative findings)
- Must label confidence: Confirmed / Probable / Possible / Requires Runtime

**Prompt Templates:** See [references/agent-prompts.md](references/agent-prompts.md)

**Coverage Matrix:** See [references/coverage-dimensions.md](references/coverage-dimensions.md)

**Agent Configuration:**

| Calibration | Agents | When to Use |
|-------------|--------|-------------|
| Light | 2 (Attacker + Auditor) | Quick check, internal tools, low risk |
| Medium | 4 (all perspectives) | Standard applications, moderate risk |
| Deep | 4 + rounds | High-value targets, post-incident, regulated |
| Compliance | 5 (add Compliance agent) | PCI-DSS, HIPAA, SOC2 requirements |

The 5th Compliance agent focuses on regulatory requirements (access logging, encryption at rest, audit trails). Add it when regulatory compliance is in scope.

**Deployment Mechanics:**

Agents are deployed using Claude Code's **Task tool** with `subagent_type="Explore"`. Deploy all agents in a single message with parallel Task calls:

```text
Task(subagent_type="Explore", model="opus", prompt="[Attacker prompt from agent-prompts.md]")
Task(subagent_type="Explore", model="opus", prompt="[Controls prompt]")
Task(subagent_type="Explore", model="opus", prompt="[Auditor prompt]")
Task(subagent_type="Explore", model="opus", prompt="[Design Review prompt]")
```

Each agent runs independently. Collect their findings in Phase 2 for cross-validation.

### Phase 2: Cross-Validation

**Purpose:** Reconcile findings, trace data flows, reduce false positives.

**Process:**
1. Compare findings across agents for consistency
2. Apply false positive reduction checklist:
   - Check framework auto-protections (Django escapes, Rails sanitizes)
   - Verify sanitization functions are called on the path
   - Confirm code path is reachable (not dead code)
   - Document reasoning for why this IS a vulnerability
3. Identify vulnerability chains (A + B + C = Critical)
4. Verify data flow traces are complete (source identified, sink identified)
5. Assign final severity with exploitability reasoning
6. Label confidence levels

**Conflict Resolution:**
```markdown
Conflict: [Agent A says X, Agent B says Y]
Investigation: [What was checked]
Resolution: [Which is correct and why]
Evidence: [Source citation with data flow]
```

### Phase 3: Synthesis

**Purpose:** Produce actionable security audit report.

**Actions:**
1. Generate executive summary with severity distribution
2. Organize findings by severity (Critical → Informational)
3. State limitations prominently (first section after summary)
4. Document negative findings (what was secure)
5. Complete coverage matrix with evidence
6. Create remediation roadmap prioritized by risk

**Report Structure:** See [Security Report Template](assets/templates/security-report.md)

---

## Evidence Requirements

Every finding must include:

| Field | Required | Description |
|-------|----------|-------------|
| **ID** | Yes | Unique identifier (VULN-001) |
| **Title** | Yes | Short description |
| **CWE ID** | Yes | Primary CWE classification (e.g., CWE-89) |
| **OWASP Category** | Yes | OWASP Top 10 mapping (e.g., A03:2021-Injection) |
| **Severity** | Yes | Critical / High / Medium / Low / Informational |
| **Location** | Yes | File:line (e.g., `src/auth/login.py:47`) |
| **Description** | Yes | What the vulnerability is |
| **Data Flow** | Yes | Source → Propagation → Sink chain |
| **Impact** | Yes | What an attacker could achieve |
| **Remediation** | Yes | How to fix (principle + pattern) |
| **Confidence** | Yes | Confirmed / Probable / Possible / Requires Runtime |
| **Verification** | Yes | How finding was verified statically |

**Finding Format:** See [references/vulnerability-format.md](references/vulnerability-format.md)

---

## Confidence Levels

| Level | Meaning | Evidence Required |
|-------|---------|-------------------|
| **Confirmed** | Complete vulnerable path traced | Source→sink chain documented, no sanitization on path |
| **Probable** | Strong pattern match, minor gaps | Known vulnerable pattern, sanitization may be bypassable |
| **Possible** | Indicator present, context needed | Suspicious pattern, requires framework/runtime understanding |
| **Requires Runtime** | Cannot determine statically | Dynamic dispatch, runtime config, timing-dependent |

**"Requires Runtime" Criteria:**
Use only when:
- Control flow depends on runtime values
- Security depends on configuration loaded at runtime
- Vulnerability requires specific timing or race conditions
- Framework provides automatic protection not visible in code

Cap at ≤20% of findings — if higher, investigate more thoroughly.

---

## Severity Scoring

| Severity | Criteria | Examples |
|----------|----------|----------|
| **Critical** | RCE, auth bypass, full data breach | SQL injection with admin access; hardcoded secrets in public repo |
| **High** | Privilege escalation, significant data exposure | IDOR accessing other users' data; JWT with weak secret |
| **Medium** | Limited impact, requires conditions | Stored XSS requiring admin to view; CSRF on sensitive action |
| **Low** | Info disclosure, hardening issues | Version disclosure; missing security headers |
| **Informational** | Best practice deviations, no direct impact | Could be better but not exploitable |

**Full criteria:** See [references/severity-scoring.md](references/severity-scoring.md)

---

## Seven Principles Applied

This skill implements the [Framework for Rigor](~/.claude/references/framework-for-rigor.md) with security-specific interpretation:

| Principle | Security Application |
|-----------|---------------------|
| **Appropriate Scope** | Define code areas to review; exclude out-of-scope; document why |
| **Adequate Evidence** | Every finding needs data flow chain + CWE + code location |
| **Sound Inference** | Severity must match code-verified exploitability |
| **Full Coverage** | All 10 security dimensions checked; all code areas examined |
| **Documentation** | Full audit trail; methodology reproducible |
| **Traceability** | Every finding traces to file:line; data flow documented |
| **Honesty** | Report what requires runtime verification; state limitations |

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Pattern match without data flow | High false positive rate | Trace source→sink for every finding |
| 100% confidence claims | Static analysis has limits | Use "Requires Runtime" honestly |
| CWE-as-checklist | Misses chain vulnerabilities | Think like attacker, not auditor |
| Severity inflation | Loses credibility, can't prioritize | Require exploitability reasoning |
| Ignore framework protections | Django/Rails auto-sanitize | Check framework defaults |
| No negative findings | Coverage claims untestable | Document what's secure |
| "Requires Runtime" as cop-out | Erodes methodology value | Cap at 20%, investigate more |

---

## Completion Criteria

Before claiming audit complete:

| Criterion | Verification |
|-----------|--------------|
| Coverage matrix filled | No cells marked '?' or empty |
| Findings evidenced | Every Confirmed has data flow |
| Cross-validation done | Conflict log complete |
| FP check done | Framework protections reviewed |
| Negative findings documented | Section populated |
| Limitations stated | First section after summary |
| Report complete | All sections filled |
| Severity distribution reasonable | Not all Critical |

**Red Flags:**
- "No vulnerabilities found" without stating what was examined
- All findings are "Possible" or "Requires Runtime"
- Coverage matrix incomplete
- No negative findings

---

## 10 Security Dimensions

| Dimension | What to Review |
|-----------|----------------|
| **1. Input Validation** | Type checking, length limits, format validation |
| **2. Authentication** | Credential storage, password policies, MFA |
| **3. Authorization** | RBAC/ABAC enforcement, privilege checks |
| **4. Session Management** | Token generation, expiration, cookie flags |
| **5. Cryptography** | Algorithm choice, key management, no hardcoded secrets |
| **6. Error Handling** | No stack traces exposed, no sensitive data in errors |
| **7. Logging & Auditing** | Security events logged, no credentials in logs |
| **8. Output Encoding** | XSS prevention, injection prevention |
| **9. Configuration** | Secure defaults, no debug in prod |
| **10. Dependencies** | Known CVEs, outdated packages |

**Full dimension details:** See [references/coverage-dimensions.md](references/coverage-dimensions.md)

---

## Integration

**Before deep-security-audit:**
- `deep-exploration` — Understand codebase structure first (for unfamiliar code)
- `episodic-memory:search` — Recall prior audits of this codebase

**After deep-security-audit:**
- `superpowers:writing-plans` — Plan remediation roadmap
- `deep-retrospective` — If breach occurred, investigate root cause

**During deep-security-audit:**
- `Explore` agents — The actual security analysis work
- Episodic memory — Recall patterns from prior audits

---

## References

- [Framework for Rigor](~/.claude/references/framework-for-rigor.md) — Shared methodology foundation
- [Agent Prompts](references/agent-prompts.md) — Detailed prompts for each perspective
- [Coverage Dimensions](references/coverage-dimensions.md) — 10 security dimensions with checklists
- [CWE Reference](references/cwe-reference.md) — CWE Top 25 with detection patterns
- [Severity Scoring](references/severity-scoring.md) — Criteria with examples
- [Vulnerability Format](references/vulnerability-format.md) — Finding template
- [Verification Protocol](references/verification-protocol.md) — Static analysis methods
- [Remediation Patterns](references/remediation-patterns.md) — Common fixes by CWE
- [Security Report Template](assets/templates/security-report.md) — Deliverable structure

---

## Changelog

### v1.0.0 (2025-12-31)
- Initial release using SkillForge 5-phase methodology
- Four-phase methodology (Pre-Flight, Agents, Cross-Validation, Synthesis)
- Four-perspective agents (Attacker, Controls, Auditor, Design Review)
- CWE primary classification with OWASP mapping
- 10 Security Dimensions coverage matrix
- Four confidence levels including "Requires Runtime"
- Static-only scope with honest limitations
- Framework for Rigor as foundation

# Agent Prompts

Detailed prompt templates for the four security audit perspectives. Deploy all four in a single message with multiple Task tool calls.

---

## General Agent Requirements

All agents must:
1. Use model: High-capability model (currently `opus`; use highest available)
2. Use subagent_type: `Explore`
3. Trace data flows with source → propagation → sink
4. Cite evidence for every finding (file:line, code snippet)
5. Report negative findings (what was examined and found secure)
6. Label confidence levels (Confirmed/Probable/Possible/Requires Runtime)
7. Cover ALL areas in scope, not just easy ones
8. Include a Key Metrics section for cross-validation

---

## Key Metrics Section

Every agent report must end with a Key Metrics table for cross-validation:

```markdown
## Key Metrics

| Metric | Count | Verification |
|--------|-------|--------------|
| Findings by severity | Critical: N, High: N, Medium: N, Low: N | Per-finding classification |
| Code areas examined | N files, N functions | List of examined paths |
| CWE categories checked | N of 25 | List which ones |
| Data flows traced | N complete traces | Source→sink chains |
```

---

## Agent A: Attacker

**Perspective:** Offense. Think like an attacker trying to exploit this code.

### Prompt Template

```
You are conducting the ATTACKER phase of a deep security audit.

## Your Perspective
Think like an attacker. Your goal is to find exploitable vulnerabilities by tracing
how untrusted input can reach sensitive operations without proper sanitization.

## Scope
[Define what code you're analyzing - paths, modules, entry points]

## Technology Stack
[Languages, frameworks, versions - affects what protections exist]

## Must Cover
For each entry point (API endpoint, form handler, file reader, etc.):
1. Identify sources of untrusted input (user input, files, network, env vars)
2. Trace how input flows through functions, assignments, returns
3. Find sinks where input reaches sensitive operations (SQL, shell, file system, etc.)
4. Check if sanitization/validation exists on the path
5. Assess if sanitization can be bypassed

## Primary Questions
- What untrusted input reaches sensitive sinks?
- Where are injection points (SQL, command, XSS, path traversal)?
- How would I chain multiple low-severity issues into a critical exploit?
- What authentication/authorization checks can I bypass?
- What sensitive data can I access or exfiltrate?

## Output Format

### Finding: [Title]

#### CWE Classification
[CWE-ID]: [CWE Name]

#### Severity
[Critical/High/Medium/Low/Informational]

#### Location
`[file:line]`

#### Data Flow
```
Source: [where untrusted data enters]
  ↓
Propagation: [how it moves through code]
  ↓
Sink: [where it reaches sensitive operation]
```

#### Code Snippet
```[language]
[relevant code with vulnerability highlighted]
```

#### Exploitation Scenario
[How an attacker would exploit this]

#### Confidence
[Confirmed/Probable/Possible/Requires Runtime]

#### Verification Method
[How this was verified statically]

---

### Negative Finding: [Area]
[What was examined and why it's secure]

## Evidence Requirements
- Every finding needs complete data flow trace
- Every finding needs code snippet showing the vulnerability
- Note areas examined that had no exploitable issues
```

---

## Agent B: Controls

**Perspective:** Defense. Verify that security controls exist and are used correctly.

### Prompt Template

```
You are conducting the CONTROLS phase of a deep security audit.

## Your Perspective
Think like a defender. Your goal is to verify that security controls (sanitization,
validation, authentication, authorization) exist AND are correctly applied.

## Scope
[Define what code you're analyzing]

## Technology Stack
[Languages, frameworks - critical for knowing default protections]

## Must Cover
1. Input validation functions - Do they exist? Are they called?
2. Output encoding functions - Correct encoding for context?
3. Authentication mechanisms - Properly implemented?
4. Authorization checks - Present on all protected resources?
5. Cryptographic functions - Using secure algorithms and modes?
6. Framework protections - Are default protections enabled?

## Primary Questions
- What sanitization/validation exists? Is it used consistently?
- Are framework security features enabled (CSRF tokens, auto-escaping)?
- Where are controls missing entirely?
- Where are controls present but bypassable?
- Are there custom security functions? Are they correct?

## Framework-Specific Checks

### Django
- CSRF_COOKIE_SECURE, SESSION_COOKIE_SECURE
- Template auto-escaping (check for |safe usage)
- ORM usage vs raw SQL

### Rails
- protect_from_forgery
- Strong parameters
- html_safe usage

### Express/Node
- Helmet middleware
- express-validator usage
- Template engine escaping

### Spring
- Spring Security configuration
- @PreAuthorize annotations
- CSRF protection

## Output Format

### Control Assessment: [Area]

#### Control Type
[Validation/Encoding/Authentication/Authorization/Cryptography]

#### Implementation Status
[Present and correct / Present but flawed / Missing]

#### Evidence
```[language]
[code showing control implementation or absence]
```

#### Coverage
[Where is this control applied? Where is it missing?]

#### Framework Protections
[What automatic protections does the framework provide?]

#### Gaps Identified
[Specific locations where control is missing or bypassable]

---

### Secure Implementation: [Area]
[What was done correctly - document as positive finding]

## Evidence Requirements
- Map controls to the code areas they protect
- Note framework defaults that provide protection
- Identify gaps where controls should exist but don't
```

---

## Agent C: Auditor

**Perspective:** Systematic coverage. Ensure all areas and categories are examined.

### Prompt Template

```
You are conducting the AUDITOR phase of a deep security audit.

## Your Perspective
Think systematically. Your goal is to ensure comprehensive coverage - that all
code areas are examined and all vulnerability categories are checked.

## Scope
[Define what code you're analyzing]

## Must Cover
Track coverage against:

### 10 Security Dimensions
1. Input Validation
2. Authentication
3. Authorization
4. Session Management
5. Cryptography
6. Error Handling
7. Logging & Auditing
8. Output Encoding
9. Configuration
10. Dependencies

### CWE Top 25 (check for each)
- CWE-79: Cross-site Scripting (XSS)
- CWE-89: SQL Injection
- CWE-78: OS Command Injection
- CWE-22: Path Traversal
- CWE-352: Cross-Site Request Forgery
- CWE-434: Unrestricted File Upload
- CWE-502: Deserialization
- CWE-287: Improper Authentication
- CWE-862: Missing Authorization
- CWE-798: Hardcoded Credentials
[Continue with full CWE Top 25]

### Code Areas
- Authentication module
- API endpoints
- Data access layer
- Configuration files
- Dependencies (package.json, requirements.txt, etc.)

## Output Format

### Coverage Matrix

| Dimension | Auth Module | API Handlers | Data Layer | Config | Deps |
|-----------|-------------|--------------|------------|--------|------|
| Input Validation | ✓ Examined | ✓ Examined | ✓ Examined | N/A | N/A |
| Authentication | ✓ Examined | ✓ Examined | N/A | ✓ Examined | N/A |
| ... | ... | ... | ... | ... | ... |

### CWE Coverage

| CWE | Checked | Finding? | Location |
|-----|---------|----------|----------|
| CWE-79 | ✓ | Yes - VULN-001 | Multiple |
| CWE-89 | ✓ | No | N/A |
| CWE-78 | ✓ | No | N/A |
| ... | ... | ... | ... |

### Areas Not Examined
[List any areas that could not be examined and why]

### Coverage Gaps
[Any systematic gaps in the audit]

## Evidence Requirements
- Complete coverage matrix with status for each cell
- Document what was NOT examined and why
- Note if any CWE categories couldn't be checked
```

---

## Agent D: Design Review

**Perspective:** Architecture. Assess trust boundaries, secure defaults, and design patterns.

### Prompt Template

```
You are conducting the DESIGN REVIEW phase of a deep security audit.

## Your Perspective
Think architecturally. Your goal is to assess whether the security design is sound -
correct trust boundaries, secure defaults, defense in depth.

## Scope
[Define what code/architecture you're analyzing]

## Must Cover
1. Trust boundaries - Where does trusted code interact with untrusted?
2. Authentication architecture - How are identities established?
3. Authorization model - How are permissions enforced?
4. Data flow architecture - How does sensitive data move?
5. Secret management - How are credentials stored and accessed?
6. Error handling design - Do errors leak information?
7. Logging architecture - Are security events captured?

## Primary Questions
- Are trust boundaries correctly placed?
- Is least privilege enforced?
- Are secure defaults used throughout?
- Is defense in depth present (multiple layers)?
- Are there single points of failure in security?
- Is the attack surface minimized?

## Output Format

### Trust Boundary Assessment

#### Boundary: [Name]
```
[Trusted Side] <--[Boundary]--> [Untrusted Side]
```

#### Crossing Points
[Where and how data crosses this boundary]

#### Protection Mechanisms
[What controls exist at this boundary]

#### Assessment
[Adequate / Inadequate / Missing]

---

### Architectural Finding: [Title]

#### Category
[Trust Boundary / Least Privilege / Secure Defaults / Defense in Depth / Attack Surface]

#### Current State
[How it's currently designed]

#### Issue
[What's wrong with the design]

#### Recommendation
[How to improve the design]

#### Impact
[What could happen if not addressed]

---

### Secure Design: [Area]
[What was designed correctly - document as positive finding]

## Evidence Requirements
- Document trust boundaries with diagram or description
- Assess each boundary for adequate protection
- Note good architectural decisions as positive findings
```

---

## Deploying Agents

Deploy all four agents in a **single message** with multiple Task tool calls:

```markdown
<Task tool call 1: Attacker agent>
<Task tool call 2: Controls agent>
<Task tool call 3: Auditor agent>
<Task tool call 4: Design Review agent>
```

This enables parallel execution. Do not deploy sequentially.

### Example Task Call

```
Task(
  description="Attacker perspective audit",
  prompt="[Full prompt from template above, customized for target codebase]",
  subagent_type="Explore",
  model="opus"
)
```

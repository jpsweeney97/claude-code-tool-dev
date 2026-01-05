# Custom Lens Template

Use this template to define domain-specific lenses for three-lens-audit.

---

## Lens Design Principles

A good lens has:

1. **Distinct Philosophy** — A clear analytical perspective that doesn't overlap with other lenses
2. **Core Question** — One question that drives all analysis
3. **Structured Vectors** — 4-6 specific areas to examine
4. **Consistent Output** — Format that enables synthesis across lenses

---

## Template

```markdown
**Role: [LENS_NAME]**

Read and analyze: `[TARGET_FILE]`

Your mission is to [CORE_MISSION]. You are the voice of **[PHILOSOPHY]**.

**Analysis Vectors:**

1. **[Vector 1 Name]**
   - [Question 1]
   - [Question 2]
   - [Question 3]
   - [Question 4]

2. **[Vector 2 Name]**
   - [Question 1]
   - [Question 2]
   - [Question 3]
   - [Question 4]

3. **[Vector 3 Name]**
   - [Question 1]
   - [Question 2]
   - [Question 3]
   - [Question 4]

4. **[Vector 4 Name]**
   - [Question 1]
   - [Question 2]
   - [Question 3]
   - [Question 4]

5. **[Vector 5 Name]**
   - [Question 1]
   - [Question 2]
   - [Question 3]
   - [Question 4]

**Output Format:**
[Structured output that enables comparison with other lenses]

[Final directive reinforcing the lens philosophy]
```

---

## Example: Security Audit Lenses

### Attacker Lens

```
**Role: Attacker**

Read and analyze: `[TARGET_FILE]`

Your mission is to find every way to exploit, bypass, or abuse this system. You are the voice of **malicious intent**.

**Analysis Vectors:**

1. **Authentication Bypass**
   - How can identity be spoofed?
   - What session management weaknesses exist?
   - Where is authentication optional when it shouldn't be?
   - What default credentials or keys exist?

2. **Authorization Escalation**
   - How can privileges be elevated?
   - What resources are accessible without proper checks?
   - Where do role boundaries leak?
   - What administrative functions are exposed?

3. **Data Exfiltration**
   - What sensitive data is accessible?
   - How can logging/monitoring be evaded?
   - What side channels exist?
   - Where is encryption missing or weak?

4. **Injection Surfaces**
   - Where is user input used unsanitized?
   - What command/query construction is vulnerable?
   - Which deserialization points are exploitable?
   - What file path manipulation is possible?

5. **Denial of Service**
   - What resources can be exhausted?
   - Which operations don't have rate limits?
   - Where can deadlocks be induced?
   - What crash conditions exist?

**Output Format:**
| Vulnerability | Vector | Exploit Scenario | Severity | CVSS Estimate |
|--------------|--------|------------------|----------|---------------|

Be adversarial. Assume you have time, resources, and motivation to break this.
```

### Defender Lens

```
**Role: Defender**

Read and analyze: `[TARGET_FILE]`

Your mission is to identify what protections are missing or insufficient. You are the voice of **defense in depth**.

**Analysis Vectors:**

1. **Perimeter Controls**
   - What entry points lack validation?
   - Where is rate limiting missing?
   - What network segmentation gaps exist?
   - How is traffic inspection handled?

2. **Detection Capability**
   - What malicious activity would go unlogged?
   - Where are audit trails incomplete?
   - What alerting thresholds are missing?
   - How quickly can anomalies be detected?

3. **Response Readiness**
   - Can compromised credentials be revoked quickly?
   - What isolation capabilities exist?
   - How are incidents escalated?
   - What forensic data is preserved?

4. **Recovery Planning**
   - What backup mechanisms exist?
   - How is integrity verified after incident?
   - What's the restore time objective?
   - Where are single points of failure?

5. **Security Hygiene**
   - What patch management gaps exist?
   - Where are hardening guides not followed?
   - What secrets management issues exist?
   - How is least privilege enforced?

**Output Format:**
| Gap | Current State | Recommended Control | Priority | Effort |
|-----|--------------|---------------------|----------|--------|

Be defensive. Assume attackers are already inside.
```

### Compliance Lens

```
**Role: Compliance Auditor**

Read and analyze: `[TARGET_FILE]`

Your mission is to assess regulatory and policy compliance. You are the voice of **accountability and evidence**.

**Analysis Vectors:**

1. **Data Protection**
   - How is PII identified and classified?
   - What consent mechanisms exist?
   - How are data subject rights handled?
   - What data retention policies apply?

2. **Access Control Documentation**
   - Are access grants documented?
   - What approval workflows exist?
   - How are access reviews performed?
   - Is separation of duties enforced?

3. **Audit Trail Completeness**
   - What actions are logged?
   - How long are logs retained?
   - Are logs tamper-evident?
   - Can user actions be reconstructed?

4. **Policy Alignment**
   - What internal policies apply?
   - Where do practices deviate from policy?
   - What exceptions are undocumented?
   - How is policy enforcement verified?

5. **Third-Party Risk**
   - What external dependencies exist?
   - How are vendors assessed?
   - What data flows to third parties?
   - Are contracts/DPAs in place?

**Output Format:**
| Requirement | Status | Evidence | Gap | Remediation |
|-------------|--------|----------|-----|-------------|

Be thorough. Assume auditors will ask for evidence.
```

---

## Example: API Design Lenses

### Consumer Lens

```
**Role: API Consumer**

Read and analyze: `[TARGET_FILE]`

Your mission is to assess usability from a developer integrating this API. You are the voice of **developer experience**.

**Analysis Vectors:**

1. **Discoverability**
   - Can I understand what this API does in 5 minutes?
   - Are endpoints logically organized?
   - Is authentication documented upfront?
   - Are there working examples?

2. **Consistency**
   - Do similar operations work similarly?
   - Are naming conventions followed?
   - Are error formats predictable?
   - Is pagination consistent?

3. **Error Handling**
   - Are errors actionable?
   - Do error codes help debugging?
   - Are validation errors specific?
   - Is retry guidance provided?

4. **Integration Friction**
   - What SDK/client support exists?
   - How many calls for common operations?
   - What rate limits apply?
   - How is versioning handled?

5. **Edge Cases**
   - What happens with empty responses?
   - How are partial failures handled?
   - What's the behavior under load?
   - Are timeouts documented?

**Output Format:**
- **Friction Points**: Where integration gets painful
- **Missing Documentation**: What I'd need to know
- **Suggested Improvements**: Quick wins for DX
- **Verdict**: Would I recommend this API?
```

### Maintainer Lens

```
**Role: API Maintainer**

Read and analyze: `[TARGET_FILE]`

Your mission is to assess long-term maintainability and evolution. You are the voice of **sustainable architecture**.

**Analysis Vectors:**

1. **Versioning Strategy**
   - How are breaking changes handled?
   - Is deprecation communicated?
   - Can versions coexist?
   - What's the migration path?

2. **Extensibility**
   - Can new fields be added safely?
   - Are extension points documented?
   - What conventions prevent breakage?
   - How are custom requirements handled?

3. **Operational Concerns**
   - What observability exists?
   - How is capacity planned?
   - What SLOs are defined?
   - How are incidents handled?

4. **Technical Debt**
   - What inconsistencies exist?
   - What legacy patterns remain?
   - What would you change if starting fresh?
   - What documentation is stale?

5. **Team Knowledge**
   - What tribal knowledge is undocumented?
   - What's the onboarding experience?
   - Are decisions recorded?
   - What testing gaps exist?

**Output Format:**
| Concern | Current State | Risk | Recommendation |
|---------|--------------|------|----------------|
```

---

## Combining Custom Lenses

When using custom lenses:

1. **Ensure Orthogonality** — Each lens should find different issues
2. **Balance Perspectives** — Include both critical and constructive lenses
3. **Match Output Formats** — Enable synthesis by using compatible structures
4. **Consider Expertise** — Custom lenses work best when you have domain knowledge to interpret findings

### Synthesis for Custom Lenses

After running custom lenses, synthesize using:

```markdown
## Custom Lens Audit: [Target]

### Lens Summary
| Lens | Philosophy | Key Finding |
|------|------------|-------------|
| [Lens 1] | [Philosophy] | [Most important finding] |
| [Lens 2] | [Philosophy] | [Most important finding] |
| [Lens 3] | [Philosophy] | [Most important finding] |

### Convergent Findings
[Issues flagged by 2+ lenses]

### Prioritized Actions
| Priority | Issue | Source Lenses | Recommended Fix |
|----------|-------|---------------|-----------------|

### Summary
[Overall assessment from combined perspectives]
```

---

## Validation

Custom lenses use minimal validation by default when processed by `scripts/validate_output.py`:

- **Content length**: Output must be >= 100 characters
- **Table presence**: Markdown tables are expected but not required (warning only)

### Adding Full Validation for Custom Lenses

To add comprehensive validation for your custom lens, add an entry to `LENS_REQUIREMENTS` in `scripts/validate_output.py`:

```python
LENS_REQUIREMENTS = {
    # ... existing lenses ...
    "your-lens-name": {
        "table_columns": ["column1", "column2", "column3"],  # Required table columns (case-insensitive)
        "min_rows": 1,                                        # Minimum data rows in table
        "sections": ["section1", "section2"],                 # Required section headers
        "description": "Your Lens Name"                       # Human-readable name for reports
    }
}
```

### Validation Examples

```bash
# Validate with built-in lens
python scripts/validate_output.py adversarial output.md

# Validate with custom lens (minimal validation)
python scripts/validate_output.py attacker output.md

# JSON output for programmatic use
python scripts/validate_output.py defender output.md --json
```

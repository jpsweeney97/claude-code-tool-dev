# Document Templates Reference

This reference defines the 14 supported document types for template compliance checking.

## Template System Overview

Each document type has:
- **Detection patterns**: How to identify the type
- **Required sections**: Must be present (severity: CRITICAL/HIGH)
- **Recommended sections**: Should be present (severity: MEDIUM)
- **Section order**: Expected sequence
- **Validation rules**: Content requirements

## Document Type Detection

| Type | Detection Pattern |
|------|-------------------|
| README | `README.md` at any level |
| ADR | `adr/*.md`, `decisions/*.md`, numbered prefix (e.g., `0001-`) |
| API Reference | `api/*.md`, contains endpoint definitions |
| Changelog | `CHANGELOG.md`, `HISTORY.md` |
| Tutorial | `tutorial/*.md`, `tutorials/*.md` |
| How-To Guide | `how-to/*.md`, `guides/*.md`, `howto/*.md` |
| Runbook | `runbooks/*.md`, `playbooks/*.md` |
| Contributing | `CONTRIBUTING.md` |
| Design Doc | `rfc/*.md`, `design/*.md`, `proposals/*.md` |
| Troubleshooting | `troubleshooting/*.md`, `faq/*.md` |
| Config Reference | `config*.md`, `configuration*.md` |
| Migration Guide | `migration*.md`, `upgrade*.md` |
| Security Policy | `SECURITY.md` |
| Release Notes | `releases/*.md`, `release-notes/*.md` |

When multiple patterns match, prefer the more specific one.

---

## 1. README

**Purpose:** Project overview and entry point.

### Required Sections
- Title (h1)
- Description (first paragraph or Overview section)
- Installation
- Usage

### Recommended Sections
- Features
- Configuration
- Contributing
- License

### Section Order
1. Title
2. Badges (optional)
3. Description/Overview
4. Features
5. Installation
6. Usage
7. Configuration
8. Contributing
9. License

### Validation Rules
- Must have exactly one h1
- Installation should include code blocks
- Usage should include examples

---

## 2. ADR (Architecture Decision Record)

**Purpose:** Document architecture decisions and their context.

### Required Sections
- Title (h1 with number, e.g., "ADR-001: Use PostgreSQL")
- Status
- Context
- Decision
- Consequences

### Recommended Sections
- Alternatives Considered
- References

### Section Order
1. Title
2. Status
3. Context
4. Decision
5. Alternatives Considered
6. Consequences
7. References

### Validation Rules
- Status must be one of: Proposed, Accepted, Deprecated, Superseded
- Context should explain the problem/need
- Decision should be specific and actionable

---

## 3. API Reference

**Purpose:** Document API endpoints, parameters, responses.

### Required Sections
- Title (h1)
- Overview or Introduction
- Authentication
- Endpoints (or Resources)
- Errors

### Recommended Sections
- Rate Limiting
- Versioning
- Examples
- SDKs/Libraries

### Section Order
1. Title
2. Overview
3. Authentication
4. Base URL / Versioning
5. Endpoints (grouped logically)
6. Errors
7. Rate Limiting
8. Examples

### Validation Rules
- Each endpoint should have: method, path, parameters, response
- Error section should list common error codes
- Authentication should explain required headers/tokens

---

## 4. Changelog

**Purpose:** Track version history and changes.

### Required Sections
- Title (h1)
- Version entries with dates

### Recommended Sections
- Categories per version (Added, Changed, Fixed, Removed)

### Section Order
1. Title
2. [Unreleased] (optional)
3. Versions in reverse chronological order

### Validation Rules
- Follow Keep a Changelog format
- Versions should have dates in YYYY-MM-DD format
- Use semantic versioning

---

## 5. Tutorial

**Purpose:** Teach a skill through guided steps.

### Required Sections
- Title (h1)
- Prerequisites
- Objectives (what reader will learn)
- Steps (numbered)
- Verification (how to confirm success)

### Recommended Sections
- Introduction
- Time estimate
- Next steps
- Troubleshooting

### Section Order
1. Title
2. Introduction
3. Prerequisites
4. Objectives
5. Steps
6. Verification
7. Next steps
8. Troubleshooting

### Validation Rules
- Steps should be numbered
- Prerequisites should list specific requirements
- Verification should have clear success criteria

---

## 6. How-To Guide

**Purpose:** Solve a specific problem.

### Required Sections
- Title (h1, should start with "How to...")
- Goal (what this achieves)
- Prerequisites
- Steps
- Outcome

### Recommended Sections
- When to use this
- Variations
- Related guides

### Section Order
1. Title
2. Goal
3. Prerequisites
4. Steps
5. Outcome
6. Variations
7. Related

### Validation Rules
- Title should describe the goal
- Steps should be actionable
- Outcome should confirm completion

---

## 7. Runbook

**Purpose:** Operational procedures for incidents/maintenance.

### Required Sections
- Title (h1)
- Purpose (when to use this)
- Symptoms (how to recognize the situation)
- Diagnosis (how to investigate)
- Remediation (how to fix)
- Escalation (when/who to escalate to)

### Recommended Sections
- Prerequisites (access, permissions)
- Related alerts
- Post-incident steps
- Revision history

### Section Order
1. Title
2. Purpose
3. Symptoms
4. Diagnosis
5. Remediation
6. Escalation
7. Post-incident
8. Revision history

### Validation Rules
- Commands should be copy-paste ready
- Escalation must include contact info
- Steps should have expected outcomes

---

## 8. Contributing

**Purpose:** Guide contributions to the project.

### Required Sections
- Title (h1)
- Bug Reports (how to report)
- Feature Requests (how to request)
- Pull Request Process

### Recommended Sections
- Code of Conduct
- Development Setup
- Testing Requirements
- Style Guide
- License

### Section Order
1. Title
2. Code of Conduct
3. Bug Reports
4. Feature Requests
5. Development Setup
6. Pull Request Process
7. Style Guide
8. License

### Validation Rules
- Should link to issue templates if they exist
- PR process should list requirements
- Should explain review process

---

## 9. Design Doc

**Purpose:** Propose and document design decisions.

### Required Sections
- Title (h1)
- Summary (one paragraph)
- Goals
- Non-goals
- Proposal

### Recommended Sections
- Background
- Alternatives Considered
- Security Considerations
- Rollout Plan
- Open Questions

### Section Order
1. Title
2. Summary
3. Background
4. Goals
5. Non-goals
6. Proposal
7. Alternatives
8. Security
9. Rollout
10. Open Questions

### Validation Rules
- Summary should be concise
- Goals and Non-goals should be lists
- Proposal should be detailed

---

## 10. Troubleshooting

**Purpose:** Help users solve common problems.

### Required Sections
- Title (h1)
- At least one Problem/Symptom entry with Solution

### Recommended Sections
- Categories for problems
- Diagnostic steps
- "Still having issues?" section

### Section Order
1. Title
2. Problem entries (grouped by category if applicable)
3. Diagnostic tools/commands
4. Getting more help

### Validation Rules
- Each problem should have identifiable symptoms
- Solutions should be step-by-step
- Include commands to verify solution

---

## 11. Config Reference

**Purpose:** Document configuration options.

### Required Sections
- Title (h1)
- Overview
- Options table or list with: name, type, default, description

### Recommended Sections
- File location
- Environment variables
- Examples
- Validation

### Section Order
1. Title
2. Overview
3. File location
4. Options
5. Environment variables
6. Examples
7. Validation

### Validation Rules
- Every option needs type and default
- Examples should be complete configs
- Note which options are required vs optional

---

## 12. Migration Guide

**Purpose:** Guide version transitions.

### Required Sections
- Title (h1, should include version range)
- Breaking Changes
- Migration Steps
- Rollback (how to revert)

### Recommended Sections
- Deprecations
- New features
- Timeline
- Support policy

### Section Order
1. Title
2. Overview (what's changing)
3. Breaking Changes
4. Deprecations
5. Migration Steps
6. Rollback
7. Timeline

### Validation Rules
- Breaking changes should be explicit
- Steps should be testable
- Rollback should be complete

---

## 13. Security Policy

**Purpose:** Explain vulnerability reporting.

### Required Sections
- Title (h1)
- Supported Versions (table)
- Reporting a Vulnerability (process)

### Recommended Sections
- Security contacts
- Expected response time
- Disclosure policy
- Security practices

### Section Order
1. Title
2. Supported Versions
3. Reporting Process
4. Response Timeline
5. Disclosure Policy

### Validation Rules
- Must include contact method
- Should set response time expectations
- Should explain what happens after report

---

## 14. Release Notes

**Purpose:** Announce what's in a release.

### Required Sections
- Title (h1 with version)
- Date
- Highlights or Summary
- Changes (categorized)

### Recommended Sections
- Breaking changes (prominent)
- Upgrade instructions
- Contributors
- Full changelog link

### Section Order
1. Title with version
2. Date
3. Highlights
4. Breaking Changes
5. Features/Added
6. Changed
7. Fixed
8. Upgrade instructions
9. Contributors

### Validation Rules
- Version should follow semver
- Date should be specific
- Breaking changes should be prominent

---

## Custom Templates

Users can define project-specific templates in `.claude/doc-templates/`.

**Format:**
```yaml
---
name: custom-doc-type
detection:
  patterns:
    - "custom/*.md"
    - "my-docs/*.md"
required_sections:
  - "Title"
  - "Overview"
  - "Details"
recommended_sections:
  - "Examples"
  - "References"
section_order:
  - Title
  - Overview
  - Details
  - Examples
  - References
---

Additional validation rules or guidance...
```

Custom templates override defaults when their detection patterns match.

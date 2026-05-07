# Section Templates

Templates for handbook sections. Include a section only when the exploration team found substantive content for it.

## Section Selection Guide

| Section | Include when |
|---------|-------------|
| Overview | Always |
| At a Glance | System has 3+ components or 2+ entry points |
| Core Components | System has named modules or subsystems worth inventorying |
| Configuration and Bring-Up | System requires setup steps, env vars, or non-trivial startup |
| Operating Model | System has non-obvious runtime behavior, trust models, or shared contracts |
| Monitoring and Observability | System produces logs, metrics, or health signals |
| Security Model | System has auth, trust boundaries, or handles sensitive data |
| Component Runbooks | System has 2+ independently invocable entry points |
| Internals | System has complex internal flows not obvious from source |
| Failure and Recovery Matrix | System has documented or discoverable failure modes |
| Known Limitations | System has guardrails, footguns, or known issues |
| Verification | System can be verified as working via runnable checks |

## Templates

### Overview

Write: purpose in one sentence, scope in 1-2 sentences, what the system does NOT cover.

### At a Glance

Use tables — one per structural dimension worth summarizing (entry points, components, hooks). Each row: name, purpose, key property.

```markdown
| Entry Point | Purpose | Invocation |
|-------------|---------|------------|
| ... | ... | ... |
```

### Core Components

H3 subheadings grouped by type (Skills, Agents, Scripts, Modules). Table or bulleted list of file paths and one-line responsibilities.

```markdown
### Skills

| Path | Responsibility |
|------|---------------|
| ... | ... |
```

### Configuration and Bring-Up

Numbered steps from fresh checkout to running system. Include:
- Prerequisites (runtimes, tools, accounts)
- Install commands
- Configuration (env vars, files)
- Verification that setup works

For configuration, use a table:

```markdown
| Variable | Default | Purpose |
|----------|---------|---------|
| ... | ... | ... |
```

### Operating Model

Describe runtime behavior that isn't obvious from the code:
- Trust models and permission boundaries
- Shared contracts or protocols
- State management (what's persisted, what's ephemeral)
- Concurrency model (if relevant)

### Monitoring and Observability

Include when the system produces logs, metrics, or health signals that operators need to know about.

```markdown
| Signal | Location | Format | When to Check |
|--------|----------|--------|---------------|
| ... | ... | ... | ... |
```

Cover:
- Log locations and formats
- Log levels and what each means in this system
- Health check endpoints or commands
- Metrics (if any) and where they're exposed
- How to tail/search logs during an incident

### Security Model

Include when the system has authentication, authorization, trust boundaries, or handles sensitive data.

Cover:
- Authentication: how identity is established
- Authorization: how permissions are checked
- Trust boundaries: what the system trusts vs validates
- Secret management: where credentials live, how they're loaded, rotation procedures
- Data handling: what's sensitive, what's redacted in logs, retention policies

### Component Runbooks

One subsection per independently operable component:

```markdown
### [Component Name]

#### When to use
[2-3 sentences: what problem this solves, when to choose it over alternatives]

#### Inputs and defaults
| Parameter | Default | Purpose |
|-----------|---------|---------|
| ... | ... | ... |

#### Flow
1. [Concrete step]
2. [Concrete step]
...

#### Failure modes
| Symptom | Cause | Recovery |
|---------|-------|----------|
| ... | ... | ... |
```

### Internals

Document complex internal flows:
- Sequence diagrams (in text/mermaid) for multi-step processes
- State machines for stateful components
- Pipeline stages for data processing

Focus on what operators need to understand when debugging, not comprehensive code walkthroughs.

### Failure and Recovery Matrix

```markdown
| Symptom | Likely Cause | Diagnosis | Recovery |
|---------|-------------|-----------|----------|
| ... | ... | ... | ... |
```

### Known Limitations

Document guardrails, footguns, and known issues operators should know. Include:
- Intentional limitations with rationale
- Known bugs with workarounds
- Performance boundaries
- Compatibility constraints

### Verification

A numbered procedure executable from a fresh checkout:

1. **Prerequisites** — confirm tools and dependencies are installed
2. **Smoke tests** — one minimal check per entry point
3. **End-to-end** — one integrated check that exercises the full system
4. **Expected output** — what success looks like for each check

Every step must be a concrete command, not a description.

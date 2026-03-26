# Reviewer Briefs

Per-reviewer role definitions for the design review team. Each brief follows the domain brief structure from `spec-review-team`, adapted for design review.

Reviewers: read YOUR section. The shared lens framework is in `system-design-review/references/system-design-dimensions.md` — read it for the full lens definitions, weighting table, and cross-cutting tensions.

---

## structural-cognitive

### Mission
Analyze architectural boundaries, dependencies, interfaces, and coupling. Evaluate whether the system communicates its own structure clearly to the people who build, operate, and inherit it.

### Categories Owned
- **Structural** (7 lenses): Purpose Fit, Responsibility Partitioning, Boundary Definition, Dependency Direction, Composability, Completeness, Layering & Abstraction
- **Cognitive** (5 lenses): Coherence, Legibility, Discoverability, Minimal Surprise, Conceptual Compression

### High-Yield Surfaces
- Component boundary diagrams and dependency graphs
- API contracts and interface definitions
- Naming conventions and structural patterns
- ADRs, design docs, and rationale documents
- Module organization and directory structure

### Common Defect Patterns
- Ambiguous component ownership (responsibilities unclear or overlapping)
- Hidden coupling through shared mutable state or implicit contracts
- Naming that misleads about component behavior or scope
- Missing rationale for structural decisions (oral tradition dependency)
- Abstraction layers that leak or mismatch the system's actual organization

### Collaboration Playbook
- **Message `behavioral`** when: boundary definition issues imply runtime failure modes (e.g., unclear contract → undefined failure behavior)
- **Message `change`** when: dependency direction problems will make evolution difficult (e.g., stable components depending on volatile ones)
- **Message `trust-safety`** when: boundary gaps overlap with trust boundaries (e.g., missing validation at interfaces that also serve as trust boundaries)
- **Broadcast** when: fundamental structural issue affects all reviewers (e.g., architecture diagram contradicts actual codebase)

### Coverage Floor
Run all 7 Structural and all 5 Cognitive sentinel questions. Report coverage notes for any category at `background` emphasis or below.

### Disconfirmation Check
Before finalizing: "Is there a simpler structural explanation for this concern?" Prefer the interpretation requiring fewer assumptions.

---

## behavioral

### Mission
Analyze runtime correctness, performance characteristics, concurrency safety, and failure behavior. Evaluate whether the system does what it claims under all defined conditions.

### Categories Owned
- **Behavioral** (8 lenses): Correctness, Consistency Model, Performance Envelope, Scalability, Concurrency Safety, Failure Containment, Backpressure & Load Shedding, Idempotency & Safety

### High-Yield Surfaces
- Request/response paths and runtime traces
- Error handling and retry logic
- Concurrency primitives and shared state access
- Queue configurations and rate limiting
- Cache layers and consistency mechanisms

### Common Defect Patterns
- Undefined behavior under failure, retry, or overload
- Implicit consistency model (consumers don't know their guarantees)
- Missing backpressure (overload → cascading failure)
- Non-idempotent operations in at-least-once delivery paths
- Performance cliffs at scale boundaries

### Collaboration Playbook
- **Message `data`** when: consistency model findings affect data flow (e.g., eventual consistency creates stale-read risk in a pipeline)
- **Message `reliability-operational`** when: failure containment gaps create reliability exposure (e.g., missing circuit breaker → cascading failure)
- **Message `structural-cognitive`** when: behavioral complexity exceeds what architecture makes visible (e.g., hidden state machine not reflected in structure)

### Coverage Floor
Run all 8 Behavioral sentinel questions. This is the largest single-category reviewer — use emphasis levels to prioritize.

### Disconfirmation Check
Before finalizing: "Is this a real runtime risk, or a theoretical concern that actual usage patterns make unlikely?"

---

## data

### Mission
Analyze how information enters, moves through, is stored, and leaves the system. Evaluate data flow clarity, schema governance, source-of-truth designation, locality, and lifecycle management.

### Categories Owned
- **Data** (5 lenses): Data Flow Clarity, Schema Governance, Source of Truth, Data Locality, Retention & Lifecycle

### High-Yield Surfaces
- Data models and schema definitions
- ETL pipelines and transformation logic
- Cache layers and denormalization points
- Database configurations and replication settings
- Data retention policies and archival mechanisms

### Common Defect Patterns
- Ambiguous source of truth (multiple components claim authority)
- Silent schema evolution (no versioning, no backward compatibility)
- Data teleporting between components via side channels
- Missing retention policy (data grows unbounded)
- Staleness not bounded on cached or denormalized copies

### Collaboration Playbook
- **Message `behavioral`** when: data consistency issues affect runtime correctness (e.g., stale cache causing incorrect logic)
- **Message `trust-safety`** when: data flow reveals sensitive data handling gaps (e.g., PII in unencrypted channels or logs)
- **Message `reliability-operational`** when: data durability or recovery gaps affect reliability (e.g., no RPO for critical data)

### Coverage Floor
Run all 5 Data sentinel questions. Trace at least one critical datum from entry to storage to exit.

### Disconfirmation Check
Before finalizing: "Is this a real data integrity risk, or does the usage pattern make this data path non-critical?"

---

## reliability-operational

### Mission
Analyze what the system promises about uptime, durability, and recovery — and whether those promises are backed. Evaluate how the system is deployed, observed, and kept alive.

### Categories Owned
- **Reliability** (5 lenses): Service Guarantees, Durability, Recoverability, Availability Model, Degradation Strategy
- **Operational** (5 lenses): Deployability, Observability, Configuration Clarity, Resource Proportionality, Operational Ownership

### High-Yield Surfaces
- SLOs, SLAs, and error budgets
- Backup and recovery procedures
- Deployment pipelines and rollback mechanisms
- Monitoring dashboards and alerting configurations
- Configuration management and feature flags
- Runbooks and operational documentation

### Common Defect Patterns
- SLOs documented but not backed by monitoring or alerting
- Recovery procedures requiring specific human knowledge at 3 AM
- Deploy processes that are manual rituals, not automated
- Missing observability (can't answer "why is it slow" from telemetry alone)
- Configuration sprawl (no inventory of knobs and their blast radii)
- Degradation that happens ad hoc instead of by explicit priority

### Collaboration Playbook
- **Message `behavioral`** when: operational gaps create runtime risk (e.g., no monitoring for a failure mode the behavioral reviewer identified)
- **Message `trust-safety`** when: operational access patterns create security exposure (e.g., broad production access undermining least privilege)
- **Message `change`** when: deployment constraints affect changeability (e.g., no rollback → every deploy is irreversible)
- **Message `structural-cognitive`** when: ownership gaps trace to unclear component boundaries

### Coverage Floor
Run all 5 Reliability and all 5 Operational sentinel questions. Second-largest reviewer (10 lenses) — use emphasis levels to prioritize across the two categories.

### Disconfirmation Check
Before finalizing: "Is this an operational gap that matters at this system's scale and criticality, or am I applying production-grade expectations to a prototype?"

---

## change

### Mission
Analyze how the system responds to time, evolution, and the inevitability of being wrong. Evaluate changeability, extensibility, replaceability, versioning, reversibility, and testability.

### Categories Owned
- **Change** (6 lenses): Changeability, Extensibility, Replaceability, Versioning & Migration, Reversibility, Testability

### High-Yield Surfaces
- Version control and branching strategies
- API versioning and deprecation policies
- Feature flag systems and gradual rollout mechanisms
- Test suites and test infrastructure
- Migration scripts and data evolution tools
- Plugin/extension points and configuration extensibility

### Common Defect Patterns
- No rollback strategy for deployments or migrations
- Test suite requiring full system to verify any component
- Version coupling (all services deploy in lockstep)
- Extension points designed for change that never comes (premature generalization)
- Missing migration path for schema or API evolution

### Collaboration Playbook
- **Message `structural-cognitive`** when: changeability issues trace to structural coupling (e.g., tight coupling prevents independent deployment)
- **Message `reliability-operational`** when: versioning or migration gaps create reliability risk (e.g., no blue-green deploy → downtime during releases)
- **Message `data`** when: schema evolution strategy is missing or unclear

### Coverage Floor
Run all 6 Change sentinel questions. If emphasis is `background`, focus on Reversibility and Testability as minimum check.

### Disconfirmation Check
Before finalizing: "Is this system at a stage where changeability matters, or is it early enough that flexibility is premature optimization?"

---

## trust-safety

### Mission
Analyze where the system interacts with things it doesn't control — users, networks, external services, time. Evaluate trust boundaries, privilege models, breach containment, auditability, and data sensitivity.

### Categories Owned
- **Trust & Safety** (5 lenses): Trust Boundary Integrity, Least Privilege, Blast Radius of Breach, Auditability, Data Sensitivity Classification

### High-Yield Surfaces
- Authentication and authorization mechanisms
- Input validation and sanitization points
- Secret management and credential storage
- Audit logging and compliance mechanisms
- External API integrations and trust boundaries
- Data classification and handling policies

### Common Defect Patterns
- Validation performed downstream instead of at trust boundaries
- Overly broad permissions (components access more than needed)
- No audit trail for security-relevant actions
- Sensitive data mixed with non-sensitive data in logs or APIs
- Lateral movement paths not minimized (one compromise exposes many)

### Collaboration Playbook
- **Message `structural-cognitive`** when: trust boundary issues overlap with component boundaries (e.g., missing validation at a service interface that is also a trust boundary)
- **Message `data`** when: sensitive data handling gaps found (e.g., PII flowing through unclassified paths)
- **Message `reliability-operational`** when: security mechanisms create operational friction (e.g., least-privilege complicating debugging)
- **Broadcast** when: critical security finding affects the entire architecture (e.g., no trust boundary exists at all)

### Coverage Floor
Run all 5 Trust & Safety sentinel questions. For `primary` emphasis, deep-dive all 5 lenses. For `secondary`, focus on Trust Boundary Integrity and Least Privilege as minimum.

### Disconfirmation Check
Before finalizing: "Is this a real security risk given the threat model, or am I applying internet-facing expectations to an internal tool?"

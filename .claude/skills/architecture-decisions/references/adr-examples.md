# ADR Examples

Sample Architecture Decision Records demonstrating proper format and rationale documentation.

---

## Example 1: Database Selection

### ADR-001: Use PostgreSQL for User Data

**Status:** Accepted

**Context:**

We need to store user data including profiles, preferences, and activity history. Requirements:
- Support for complex queries (filtering, sorting, aggregation)
- ACID transactions for profile updates
- Schema will evolve but core structure is stable
- Expected scale: 100K users, 10M records
- Team has SQL experience

**Decision:**

We will use PostgreSQL as the primary database for user data.

**Rationale:**

Why PostgreSQL:
- Excellent support for complex queries with indexes
- ACID compliance ensures data consistency
- JSON columns provide flexibility for preferences without schema changes
- Team expertise reduces learning curve
- Proven at our expected scale

Why not MongoDB:
- We don't need schema flexibility for core data
- Complex queries across collections require more work
- Team would need training

Why not MySQL:
- PostgreSQL's JSON support and extensions better fit our needs
- No significant advantage for our use case

**Consequences:**

Positive:
- Leverages team's existing SQL skills
- Strong consistency guarantees
- Mature tooling and hosting options

Negative:
- Vertical scaling primarily (acceptable for our scale)
- Need to manage schema migrations

Neutral:
- Will use pgvector extension if we add search features

**Reversal Conditions:**

We would revisit this decision if:
- User count exceeds 10M with significant query latency
- We need to store highly variable document structures
- Geographic distribution requires multi-region writes

---

## Example 2: Service Architecture

### ADR-002: Start with Modular Monolith

**Status:** Accepted

**Context:**

Building a new e-commerce platform. Team size: 8 engineers.
Domain includes: catalog, orders, users, payments, inventory.
Uncertainty: exact boundaries between domains still being discovered.

**Decision:**

We will build a modular monolith with clear module boundaries, designed for potential future extraction to services.

**Rationale:**

Why modular monolith:
- Team size (8) doesn't justify microservices overhead
- Domain boundaries are still unclear
- Single deployment simplifies operations
- Can extract services later when boundaries prove stable
- Modules enforce some separation without distributed complexity

Why not microservices from start:
- Premature optimization for team size
- Would need to guess at boundaries (risky)
- Operational overhead (deployment, monitoring, tracing)
- Network calls add latency and failure modes

Why not simple monolith:
- Want to enforce some module separation
- Easier future extraction if boundaries solidify
- Prevents accidental coupling

**Consequences:**

Positive:
- Simple deployment and operations
- Fast development (no network calls)
- Strong consistency (single database)
- Can extract services incrementally

Negative:
- Must be disciplined about module boundaries
- Single deployment means coordinated releases
- Scaling is vertical (acceptable for now)

Neutral:
- Will use separate schemas per module to ease future extraction
- Will establish API contracts between modules

**Reversal Conditions:**

We would revisit this decision if:
- Team grows beyond 15 engineers
- Module boundaries prove stable for 6+ months
- Independent scaling becomes necessary
- Deployment coordination becomes bottleneck

---

## Example 3: API Design

### ADR-003: REST API for External Clients

**Status:** Accepted

**Context:**

Building public API for third-party integrations. Clients include:
- Web applications (JavaScript)
- Mobile apps (iOS, Android)
- Server-side integrations (various languages)
Expected patterns: CRUD operations, some complex queries.

**Decision:**

We will use REST with JSON for the public API.

**Rationale:**

Why REST:
- Universal client support (every language has HTTP)
- HTTP caching reduces load
- Simple mental model for integrators
- Mature tooling (OpenAPI, Postman, etc.)
- Team has extensive REST experience

Why not GraphQL:
- Our query patterns don't vary significantly by client
- Caching is more complex
- Additional learning curve for integrators
- Over-fetching isn't a significant problem for our resources

Why not gRPC:
- Browser support requires additional tooling
- Higher barrier for third-party integrators
- Binary protocol harder to debug

**Consequences:**

Positive:
- Low barrier to integration
- HTTP caching reduces server load
- Well-understood by developers
- Extensive tooling ecosystem

Negative:
- May need multiple endpoints for complex queries
- Some over-fetching for mobile clients (acceptable)

Neutral:
- Will use OpenAPI for documentation
- May add GraphQL later for specific mobile needs

**Reversal Conditions:**

We would revisit this decision if:
- Mobile clients have significant bandwidth constraints
- Query patterns become highly variable
- Real-time features require different approach

---

## Example 4: Authentication

### ADR-004: JWT with Short Expiry for API Authentication

**Status:** Accepted

**Context:**

Need authentication for API access. Requirements:
- Stateless (multiple API servers)
- Support for mobile and web clients
- Must be revocable (though eventual consistency acceptable)
- Performance-sensitive (no DB lookup per request)

**Decision:**

We will use JWT access tokens with 15-minute expiry, paired with longer-lived refresh tokens stored server-side.

**Rationale:**

Why JWT:
- Stateless verification (no DB lookup per request)
- Contains claims (user ID, roles) for authorization
- Standard format, good library support

Why short expiry (15 min):
- Limits exposure if token leaked
- Natural revocation within reasonable window
- Refresh token handles longer sessions

Why server-side refresh tokens:
- Can be revoked immediately
- Provides audit trail
- Limits blast radius of refresh token theft

Why not sessions:
- Requires shared session store for multiple servers
- DB/cache lookup on every request

Why not OAuth (alone):
- We are the identity provider
- Would add unnecessary complexity
- May add OAuth later for third-party auth

**Consequences:**

Positive:
- No per-request database lookup
- Horizontal scaling without shared state
- Standard format with good tooling

Negative:
- Cannot instantly revoke access tokens (15-min window)
- Token payload increases request size slightly
- Must handle token refresh logic in clients

Neutral:
- Refresh token rotation on each use
- Will log token issuance for security audit

**Reversal Conditions:**

We would revisit this decision if:
- Instant revocation becomes required (would add token blacklist)
- Token size becomes problematic
- Security requirements mandate session-based approach

---

## Example 5: Build vs Buy

### ADR-005: Use Stripe for Payment Processing

**Status:** Accepted

**Context:**

Need to accept payments for e-commerce platform. Options:
- Build payment processing in-house
- Use payment gateway (Stripe, Braintree, etc.)
Requirements: Credit cards, multiple currencies, PCI compliance, subscriptions.

**Decision:**

We will use Stripe for all payment processing.

**Rationale:**

Why Stripe:
- PCI compliance handled by Stripe
- Excellent developer experience and documentation
- Supports all required features (cards, subscriptions, multi-currency)
- Transparent pricing
- Strong reputation and reliability

Why not build in-house:
- PCI compliance is complex and expensive
- Payment processing is not our core competency
- Would take months to build what Stripe provides
- Ongoing maintenance burden
- Security responsibility we don't need

Why not Braintree:
- Similar capabilities, but Stripe's DX is superior
- Team has prior Stripe experience
- Marginally better pricing for our volume

**Consequences:**

Positive:
- Fast implementation (days, not months)
- PCI compliance handled
- Reliable, battle-tested infrastructure
- Excellent documentation and support

Negative:
- Per-transaction fees (~2.9% + $0.30)
- Vendor lock-in for payment data
- Features limited to Stripe's roadmap

Neutral:
- Will use Stripe's hosted checkout for reduced scope
- May evaluate alternatives at higher volume

**Reversal Conditions:**

We would revisit this decision if:
- Transaction volume makes fees prohibitive (>$1M/month)
- Stripe lacks critical features we need
- Stripe reliability becomes problematic
- Regional requirements mandate local provider

---

## ADR Hygiene Notes

**Naming:** ADR-{sequential-number}: {brief-title}

**Storage:**
```
docs/
└── architecture/
    └── decisions/
        ├── 0001-use-postgresql-for-user-data.md
        ├── 0002-modular-monolith-architecture.md
        └── README.md (index of decisions)
```

**Linking:** Reference related ADRs. Example:
> See ADR-002 for overall architecture decision that informed this choice.

**Status updates:**
- Proposed → Accepted: When implemented
- Accepted → Deprecated: When superseded but not removed
- Accepted → Superseded by ADR-X: When replaced

**Review cadence:** Quarterly review of active ADRs against reversal conditions.

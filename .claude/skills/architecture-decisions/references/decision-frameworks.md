# Decision Frameworks

Detailed frameworks for common architecture decisions. Each framework provides:
- Decision criteria with weights
- Tradeoff dimensions
- Questions to ask
- Warning signs

---

## Service Architecture

### Monolith vs Microservices vs Modular Monolith

| Factor | Monolith | Modular Monolith | Microservices |
|--------|----------|------------------|---------------|
| **Team size** | < 10 | 10-50 | > 50 |
| **Deployment** | Single unit | Single unit, clear modules | Independent |
| **Scaling** | Vertical | Vertical | Horizontal, per-service |
| **Complexity** | Low | Medium | High |
| **Consistency** | Easy (single DB) | Easy (single DB) | Challenging (distributed) |
| **Failure isolation** | Low | Medium | High |

**Decision Flow:**

```
Is team < 10 engineers?
├── Yes → Monolith (revisit when team grows)
└── No → Are domain boundaries clear and stable?
    ├── No → Modular Monolith (extract later)
    └── Yes → Do services need independent:
        ├── Scaling? → Microservices
        ├── Tech stacks? → Microservices
        ├── Deployment? → Microservices
        └── None of above → Modular Monolith
```

**Warning signs you chose wrong:**

| Choice | Warning Sign |
|--------|--------------|
| Monolith | Deployments blocked by unrelated changes |
| Microservices | Every feature requires coordinating 5+ services |
| Modular Monolith | Module boundaries constantly violated |

---

## Data Storage

### SQL vs NoSQL

| Factor | SQL (PostgreSQL, MySQL) | Document (MongoDB) | Key-Value (Redis) | Wide-Column (Cassandra) |
|--------|-------------------------|-------------------|-------------------|------------------------|
| **Query pattern** | Complex joins, ad-hoc | Document retrieval | Simple lookup | Time-series, wide rows |
| **Schema** | Fixed, enforced | Flexible | None | Semi-structured |
| **Consistency** | ACID | Configurable | Eventual | Tunable |
| **Scale pattern** | Vertical (read replicas) | Horizontal | Horizontal | Horizontal |
| **Best for** | Transactional, reporting | Content, catalogs | Cache, sessions | Analytics, logs |

**Decision Flow:**

```
Do you need complex queries with joins?
├── Yes → SQL
└── No → Do you need ACID transactions?
    ├── Yes → SQL (or NewSQL like CockroachDB)
    └── No → Is schema stable?
        ├── Yes → SQL (simplicity wins)
        └── No → What's your access pattern?
            ├── Document retrieval → Document DB
            ├── Key lookup → Key-Value
            └── Time-series/wide → Wide-Column
```

**Polyglot persistence:** Use multiple stores for different data types.
- User profiles: SQL (relational, transactions)
- Session data: Redis (fast, ephemeral)
- Activity logs: Wide-column (append-heavy, time-series)

---

## Communication Patterns

### Sync vs Async

| Factor | Synchronous (REST, gRPC) | Asynchronous (Queue, Event) |
|--------|--------------------------|----------------------------|
| **Latency** | Immediate response | Delayed, decoupled |
| **Coupling** | Temporal (both must be up) | Loose (producer/consumer independent) |
| **Complexity** | Lower | Higher (message handling) |
| **Failure handling** | Caller handles | Retry/DLQ infrastructure |
| **Ordering** | Natural | Must be managed |
| **Debugging** | Request tracing | Event tracing, more complex |

**Decision Flow:**

```
Does caller need immediate response?
├── Yes → Can you tolerate failure if downstream is down?
│   ├── Yes → Sync with circuit breaker
│   └── No → Sync with fallback or cache
└── No → Is ordering critical?
    ├── Yes → Queue (FIFO) or partitioned events
    └── No → Events or fan-out queue
```

**Hybrid patterns:**
- **Sync + async:** API returns immediately, queues background work
- **Event sourcing:** Events are source of truth, projections for queries
- **CQRS:** Sync for writes, async propagation to read models

---

## API Design

### REST vs GraphQL vs gRPC

| Factor | REST | GraphQL | gRPC |
|--------|------|---------|------|
| **Client flexibility** | Fixed endpoints | Client specifies shape | Fixed proto |
| **Caching** | HTTP native | Complex | None native |
| **Tooling** | Mature | Good | Good |
| **Learning curve** | Low | Medium | Medium |
| **Performance** | Good | Variable | Excellent |
| **Best for** | Public APIs, CRUD | Mobile, varied clients | Internal, high-perf |

**Decision Flow:**

```
Is this internal service-to-service?
├── Yes → Is latency critical?
│   ├── Yes → gRPC
│   └── No → REST (simpler debugging)
└── No (external/client API) → Do clients have varied data needs?
    ├── Yes → GraphQL
    └── No → REST (caching, simplicity)
```

---

## Build vs Buy

| Factor | Build | Buy/SaaS |
|--------|-------|----------|
| **Control** | Full | Limited by vendor |
| **Customization** | Unlimited | Within vendor constraints |
| **Time to value** | Slow | Fast |
| **Maintenance** | Your team | Vendor |
| **Cost model** | Dev time + hosting | Subscription |
| **Risk** | Technical | Vendor (lock-in, shutdown) |

**Decision Flow:**

```
Is this core to your business differentiation?
├── Yes → Build (competitive advantage)
└── No → Does a good solution exist?
    ├── No → Build (no choice)
    └── Yes → Can you afford the subscription?
        ├── No → Build or find alternative
        └── Yes → Does it integrate with your stack?
            ├── No → Build or find alternative
            └── Yes → Buy
```

**Build signals:**
- Core competency
- Unique requirements
- No good solutions exist
- Integration complexity > build complexity

**Buy signals:**
- Commodity functionality
- Standard requirements
- Proven solutions exist
- Your team lacks domain expertise

---

## Authentication & Authorization

### Session vs JWT vs OAuth

| Factor | Server Sessions | JWT | OAuth 2.0 |
|--------|-----------------|-----|-----------|
| **State** | Server-side | Client-side (stateless) | Provider-side |
| **Scalability** | Session store needed | Scales easily | Depends on provider |
| **Revocation** | Immediate | Difficult | Provider-dependent |
| **Security** | Server controls | Token can leak | Delegated trust |
| **Best for** | Traditional web apps | APIs, microservices | Third-party auth |

**Decision Flow:**

```
Do you need third-party login (Google, GitHub)?
├── Yes → OAuth 2.0 (or OIDC)
└── No → Is this a stateless API?
    ├── Yes → JWT (with short expiry + refresh)
    └── No → Server sessions (simplest)
```

**Hybrid:** OAuth for login, JWT for API access, sessions for web UI.

---

## Caching Strategy

### Where to Cache

| Layer | What to Cache | TTL Guidance |
|-------|---------------|--------------|
| **Browser** | Static assets, API responses | Long for assets, short for data |
| **CDN** | Static content, public pages | Minutes to hours |
| **Application** | Computed results, DB queries | Seconds to minutes |
| **Database** | Query plans, buffer pool | Automatic |

**Cache Invalidation Strategies:**

| Strategy | When to Use | Complexity |
|----------|-------------|------------|
| **TTL** | Data can be stale briefly | Low |
| **Write-through** | Consistency critical | Medium |
| **Write-behind** | Write performance critical | High |
| **Event-driven** | Complex dependencies | High |

**Decision Flow:**

```
Can users tolerate stale data?
├── Yes (seconds-minutes) → TTL-based caching
└── No → Is write latency critical?
    ├── Yes → Write-behind with eventual consistency
    └── No → Write-through (consistent but slower writes)
```

---

## Deployment Strategy

### Deployment Patterns

| Pattern | Risk | Rollback | Complexity |
|---------|------|----------|------------|
| **Big bang** | High | Full redeploy | Low |
| **Rolling** | Medium | Partial | Medium |
| **Blue-green** | Low | Instant switch | Medium |
| **Canary** | Low | Gradual | High |
| **Feature flags** | Very low | Instant toggle | High |

**Decision Flow:**

```
Is downtime acceptable?
├── Yes → Big bang (simplest)
└── No → Do you need instant rollback?
    ├── Yes → Blue-green or feature flags
    └── No → Is gradual rollout valuable?
        ├── Yes → Canary
        └── No → Rolling
```

---

## Framework Selection Checklist

When evaluating any framework/library:

| Criterion | Questions |
|-----------|-----------|
| **Maturity** | How long in production? Who uses it? |
| **Community** | Active development? Good docs? Help available? |
| **Fit** | Matches your constraints? Team can learn it? |
| **Lock-in** | How hard to switch? Proprietary features? |
| **Performance** | Meets your requirements? Benchmarks available? |
| **Security** | Track record? Active maintenance? |

**Red flags:**
- Last commit > 6 months ago
- < 1000 GitHub stars for critical dependency
- No clear migration path
- Single maintainer for production use

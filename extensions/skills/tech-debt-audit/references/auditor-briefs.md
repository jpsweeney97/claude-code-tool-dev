# Auditor Briefs

Per-auditor role definitions for the tech debt audit team.

Auditors: read YOUR section. The shared lens framework is in [`debt-taxonomy.md`](debt-taxonomy.md) — read it for the full lens definitions, archetype weighting, and cross-cutting tensions.

---

## code-health

### Mission
Audit the codebase for in-the-file debt: complexity, duplication, dead code, naming drift, oversized modules, smell density. Your evidence lives in the source files themselves and in change-frequency signals from `git log`.

### Categories Owned
- **Code Health** (6 lenses): Complexity Hotspots, Duplication, Dead Code, Naming Entropy, Oversized Modules, Smell Density

### High-Yield Surfaces
- Source files at the largest or most-frequently-changed paths
- `git log --format='%H %s' | head -100` to spot churn hotspots
- TODO/FIXME/HACK/XXX comment density
- Lint config and lint output (signals what the team already calls debt)
- Style/formatter config (and disagreements with the actual code)
- Generated code that has been hand-edited (a debt signal in itself)

### Common Defect Patterns
- A handful of "god files" that every change has to touch
- Logic duplicated across 3+ places, drifting independently
- Feature flags that have outlived the feature they gated, now dead branches
- Naming inconsistency masking duplicate concepts (e.g., `User` and `Account` and `Customer` are the same thing)
- TODO/FIXME density above ~1 per 100 LOC with no tracking
- Broad `except Exception` / `catch (e)` swallowing errors silently

### Collaboration Playbook
- **Message `architecture-drift`** when: a code-health finding traces back to a structural problem (e.g., duplication exists because there's no place for the shared logic to live)
- **Message `test-debt`** when: complexity hotspots correlate with low test coverage — the test debt is *why* the code is hard to clean up
- **Message `knowledge`** when: dead code or feature flags are dead because nobody remembers what they were for (knowledge debt creating code debt)
- **Broadcast** when: a single sweeping issue dominates the codebase (e.g., "every module has the same untested error handler" — a finding everyone should account for)

### Coverage Floor
Walk all 6 Code Health lenses as sentinel checks. For each, sample at least 3 distinct files or directories before concluding "no defect". Mandatory coverage notes if you find nothing in a `primary` or `secondary` lens.

### Disconfirmation Check
Before finalizing each finding: "Is this debt actively bleeding velocity today, or just untidy?" If you can't name a concrete cost — bug source, slow change, oncall hour, onboarding friction — demote to P3 or drop.

---

## architecture-drift

### Mission
Audit the codebase for between-the-files debt: how modules relate, where boundaries have eroded, where abstractions leak, where layering has bent. Your evidence is in the dependency graph, the import statements, and the gap between intended and actual architecture.

### Categories Owned
- **Architecture Drift** (6 lenses): Boundary Erosion, Leaky Abstractions, Layering Violations, Coupling Tightness, Circular Dependencies, Missing Seams

### High-Yield Surfaces
- Module/package import graphs (use language-native tools: `pydeps`, `madge`, `go mod graph`, etc.)
- ADRs or original architecture docs (compare to current state)
- Cross-boundary imports — places where a low-level module imports from a high-level one
- Shared mutable state (singletons, globals, module-level caches)
- Files that import from every layer (often glue code that hides coupling)
- Existing seams: interfaces, plugin systems, dependency injection — are they used or bypassed?

### Common Defect Patterns
- Boundaries described in docs but violated by imports
- Domain code importing transport details (HTTP types, DB cursors, ORM models leaking out)
- High-level orchestrators reaching into low-level utilities directly
- Import cycles tolerated because the language allows them, but blocking incremental test/build
- "Utility" modules that are actually a dumping ground touched by everyone
- Seams that exist in code but are bypassed in practice (e.g., an `IUserRepo` interface with one implementation that everyone imports directly)

### Collaboration Playbook
- **Message `code-health`** when: an architecture-drift finding manifests as code-health smell (e.g., duplication exists because there's no shared module — the architecture drift causes the code smell)
- **Message `test-debt`** when: coupling tightness explains why testing in isolation is hard
- **Message `operational`** when: missing seams or layering violations make deploys fragile (e.g., can't deploy A without B)
- **Message `knowledge`** when: the gap between as-built and as-designed is so wide the original design no longer makes sense — the doc itself is debt

### Coverage Floor
Walk all 6 Architecture Drift lenses. Build at least a rough import-graph sketch before concluding "no defect". For a `system`-scope audit, identify the top-3 most-imported modules and check whether they should be that central.

### Disconfirmation Check
Before finalizing each finding: "Was this an inherited default or a conscious decision?" Architecture drift findings are most actionable when you can name what the design *should* have been — if you can't, the finding may be cosmetic.

---

## dependency

### Mission
Audit what the codebase pulls in from outside and the cost of those choices over time. Your evidence is in the dependency manifests, lock files, vulnerability advisories, and maintainer activity signals.

### Categories Owned
- **Dependency & Supply Chain** (6 lenses): Version Currency, Known Vulnerabilities, Maintenance Health, License Risk, Unused Dependencies, Version Skew

### High-Yield Surfaces
- Manifests: `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`, `pom.xml`, etc.
- Lockfiles (`package-lock.json`, `poetry.lock`, `go.sum`, etc.) — the source of truth
- CI security scans if present
- Public vulnerability databases (npm advisories, GHSA, PyPI advisories)
- For each significant dep: GitHub repo (last release, open-issue count, response time)
- For monorepos: workspace dependency declarations across packages

### Common Defect Patterns
- Major version behind on a security-relevant library (auth, crypto, serialization)
- CVE-affected version pinned, with no remediation tracked
- A "core" dep whose upstream hasn't released in 18+ months
- License chain — a copyleft transitive dep buried under permissive direct deps
- Dead deps from removed features, still installed
- Same package pinned at different versions across packages in a monorepo

### Collaboration Playbook
- **Message `operational`** when: a dep upgrade requires a deploy strategy (e.g., DB driver change needs rolling deploy with both versions live)
- **Message `architecture-drift`** when: a dep is hard to upgrade because the codebase is coupled to its current API (the architecture drift is what makes the dep debt worse)
- **Message `test-debt`** when: upgrading a dep is gated on test coverage that doesn't exist (test debt blocks dep fix)
- **Broadcast** when: a single dep upgrade would resolve findings across multiple categories (rare but high-value signal)

### Coverage Floor
Inventory every direct dependency. For top-10-most-used (by import count), check version currency, last release date, and open issue count. For all deps: scan for known CVEs.

### Disconfirmation Check
Before finalizing each finding: "Is this dep actually used in the hot path, or is the staleness benign because the surface area is tiny?" A 5-year-old dep called in one CLI flag is different from a 5-year-old dep in the request handler.

---

## test-debt

### Mission
Audit whether the test suite reliably tells the truth about whether the code works. Your evidence is in the test directories, CI logs, coverage reports, and the gap between what's tested and what matters.

### Categories Owned
- **Test Debt** (6 lenses): Coverage Gaps, Brittleness, Flakiness, Missing Test Layers, Mocks-vs-Reality Drift, Suite Performance

### High-Yield Surfaces
- Test directories (`tests/`, `__tests__/`, `*_test.go`, etc.) and CI configuration
- Coverage reports if generated; raw line coverage alone is weak signal — combine with criticality
- CI logs for the last 100 builds: failure pattern, flake rate
- Test runtime profile (total + slowest tests)
- Mock setup code: how is reality stubbed, and when was the stub last verified?
- Critical paths (auth, payments, state transitions, retry/idempotency): test count vs production criticality

### Common Defect Patterns
- High overall coverage masking zero coverage in critical paths
- Tests that re-implement the function under test, breaking on every refactor
- Flakes triaged with `retry: 3` instead of fixed; trust in CI eroded
- All tests at one level (e.g., all integration, no unit; or all unit, no end-to-end)
- Mocks pinned to behavior that the real service stopped doing 6 months ago
- Test suite >20 minutes locally, leading to "I'll let CI catch it" behavior

### Collaboration Playbook
- **Message `code-health`** when: a complexity hotspot is hard to test because of its shape (test debt and code debt reinforce each other)
- **Message `architecture-drift`** when: tests are brittle because there are no seams to test against
- **Message `dependency`** when: a dep upgrade is dangerous because the test suite can't catch its regression — surface the gap as blocking dep fix
- **Message `operational`** when: deploy fragility traces back to insufficient pre-deploy verification (test debt creates operational debt)

### Coverage Floor
Walk all 6 Test Debt lenses. For coverage gaps, identify at least 3 critical-path areas (auth, payments, data integrity, retry/idempotency, error handling) and check their test footprint. For brittleness/flakiness: read at least one round of CI history if available.

### Disconfirmation Check
Before finalizing each finding: "Is the test suite *materially* failing to catch real bugs, or is it being held to an unrealistic ideal?" A startup MVP with 30% coverage in non-critical paths is different from a payments service with 30% coverage in the charge flow.

---

## operational

### Mission
Audit how the system is run in production and what it tells you while it's running. Your evidence is in deploy config, observability config, runbooks, oncall ergonomics, and performance/scaling signals.

### Categories Owned
- **Operational & Observability** (6 lenses): Telemetry Coverage, Deploy Reversibility, Bring-Up Fragility, Oncall Path Clarity, Performance Cliffs, Scaling Surface

### High-Yield Surfaces
- Deploy/CI config (`.github/workflows/`, `Dockerfile`, `k8s/`, `terraform/`, etc.)
- Observability config (Prometheus, OTel, Datadog, structured logging setup)
- Dashboards, alerts, runbooks if referenced in repo
- Local-dev bring-up docs (README, CONTRIBUTING) compared to actual steps
- Performance-relevant config (connection pools, queue sizes, cache TTLs)
- Known capacity ceilings (DB max connections, queue depth limits, memory limits)

### Common Defect Patterns
- Critical user journey with no metrics or traces — can't tell if it's degraded
- Deploys claimed reversible, but rollback procedure is "redeploy old image" with no data-migration story
- "Run these 12 steps" bring-up — every newcomer pays the tax, nobody fixes it
- Pages with no runbook, or runbooks that say "ask <person>"
- DB connection pool at default size, growing service hitting limit at predictable load
- One scaling axis (e.g., user count) handled; another (e.g., data volume) silently unaddressed

### Collaboration Playbook
- **Message `dependency`** when: a dep upgrade needs a rollout strategy (operational planning gates the dep fix)
- **Message `test-debt`** when: a missing test layer is the reason deploys are scary (test gap creates operational fragility)
- **Message `knowledge`** when: oncall path clarity is blocked by missing docs (operational debt is rooted in knowledge debt)
- **Message `architecture-drift`** when: missing seams force ugly deploy orchestration (architecture drift creates operational pain)
- **Broadcast** when: a fundamental observability gap means *every other audit category's findings have hidden evidence* (e.g., "no production tracing — many of our 'maybe' findings could be confirmed if we had data")

### Coverage Floor
Walk all 6 Operational lenses. For Telemetry Coverage: trace at least one critical user journey end-to-end and check what's instrumented. For Performance Cliffs: identify at least one known capacity ceiling and check whether the team is tracking proximity.

### Disconfirmation Check
Before finalizing each finding: "Is this operational gap real at this system's actual scale and criticality, or am I applying production-grade expectations to a prototype or internal tool?"

---

## knowledge

### Mission
Audit what the codebase remembers about itself, and what only lives in someone's head. Your evidence is in READMEs, ADRs, ownership files, commit messages, and the gap between what's written and what's true.

### Categories Owned
- **Knowledge & Documentation** (6 lenses): Doc-Code Drift, Undocumented Systems, Bus Factor, Ownership Gaps, ADR Practice, Onboarding Cost

### High-Yield Surfaces
- READMEs at every level (root, package, module) — compare claims to reality
- ADR directory if present (`docs/adr/`, `docs/decisions/`) — verify ADRs still hold
- `CODEOWNERS`, ownership files, or commit/PR history for "who knows this code"
- Onboarding docs (`CONTRIBUTING.md`, `docs/onboarding/`) — recency and accuracy
- Comment density in critical components (low can be bad, high-and-stale can be worse)
- Bus factor signal: `git shortlog -sne -- path/` for each significant module — what's the author count?

### Common Defect Patterns
- README documenting a setup process that hasn't worked in 6 months
- Critical component with one author who hasn't touched it in 2 years, no other contributors
- ADR saying "we chose X for reason Y" — but the codebase now uses Z, with no superseding ADR
- Module nobody owns, accumulating debt because no one is on the hook to push back
- "Tribal knowledge" — workflows that work but exist in no doc; only learned by asking
- Onboarding cost of weeks measured in interrupted senior-engineer time

### Collaboration Playbook
- **Message `code-health`** when: dead code is dead because nobody remembers what it was for (knowledge debt manifesting as code debt)
- **Message `architecture-drift`** when: the design has drifted enough that the original ADRs no longer match — the docs are themselves debt
- **Message `operational`** when: oncall path is unclear because ownership is unclear (knowledge debt → operational debt)
- **Broadcast** when: a critical system is bus-factor-1 (this is information every other auditor should weigh — findings against that system carry extra risk)

### Coverage Floor
Walk all 6 Knowledge lenses. For Bus Factor: identify at least 3 critical components and check author count over the last 12 months. For Doc-Code Drift: verify at least 3 doc claims against current code.

### Disconfirmation Check
Before finalizing each finding: "Is this an information gap that's actually costing the team, or am I applying enterprise-grade documentation expectations to a small project?" A solo project's bus factor of 1 is by design; a multi-team platform's bus factor of 1 is a fire.

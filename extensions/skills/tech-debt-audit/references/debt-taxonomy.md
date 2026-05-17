# Tech Debt Taxonomy

The shared lens framework for the tech debt audit team. All auditors share this vocabulary; each owns a subset of the lenses defined here.

**How to use this:** Each lens is a question to ask the codebase. For every one, ask: "Is this debt actively bleeding velocity, compounding cost, or just untidy?" Tidiness is not debt. Debt has a name, a cost, and a payer.

**Notation:** Each lens is tagged to make the kind of evidence clear.

- `[quality]` — a property of the codebase you evaluate (e.g., complexity, coupling)
- `[mechanism]` — a specific technique or pattern that should exist (e.g., dependency pinning, contract tests)
- `[constraint]` — a boundary or guarantee that should be defined (e.g., test runtime budget, deploy reversibility)
- `[governance]` — a process or policy concern that spans the codebase lifecycle (e.g., ownership, ADR practice)

---

## 1. Code Health Lenses

_How the code itself reads, evolves, and resists rot._

- **Complexity Hotspots** `[quality]` — Are there files, functions, or modules whose cyclomatic complexity, nesting depth, or lines-per-function consistently exceed local norms? Are these hotspots correlated with bug history or change-frequency?

- **Duplication** `[quality]` — Is the same logic implemented in multiple places that drift independently? Is duplication structural (copy-pasted blocks) or semantic (different code, same purpose)? Both compound — structural is faster to fix.

- **Dead Code** `[quality]` — Are there exported symbols never imported, branches never reached, feature flags never set, configuration options never overridden? Dead code creates phantom maintenance load and confuses navigation.

- **Naming Entropy** `[quality]` — Do names mean the same thing across the codebase, or has terminology drifted (e.g., `User`, `Account`, `Customer`, `Member` all referring to the same concept)? Mixed vocabulary slows comprehension for every newcomer.

- **Oversized Modules** `[quality]` — Are there files or classes that exceed reasonable comprehension limits (rough heuristic: >500 lines for code, >2000 for generated)? Size alone is not debt — but oversized modules typically hide responsibility-partitioning failures.

- **Smell Density** `[quality]` — Are there patterns the local idiom calls out as smells (e.g., `TODO`/`FIXME`/`HACK` comments, broad `except Exception`, swallowed errors, magic numbers, primitive obsession)? Density matters — one smell is normal; clusters are signal.

---

## 2. Architecture Drift Lenses

_Where the as-built system has diverged from the as-designed boundaries._

- **Boundary Erosion** `[quality]` — Have module/service/package boundaries weakened over time? Are there imports across boundaries that the original design forbade, or shared mutable state that crossed a seam?

- **Leaky Abstractions** `[quality]` — Do abstractions reveal their implementation (e.g., ORM queries leaking into business logic, HTTP semantics into domain code, transport details into core types)? Leaks force callers to know more than the interface promised.

- **Layering Violations** `[quality]` — Does the dependency graph respect the intended layering? Do high-level modules depend on low-level details, or vice versa beyond what was sanctioned?

- **Coupling Tightness** `[quality]` — How much do components know about each other's internals? Can two modules be swapped, replaced, or modified independently — or does a change in one require a change in N others?

- **Circular Dependencies** `[mechanism]` — Are there import cycles between modules/packages? Even when permitted by the language, cycles prevent independent testing and incremental builds.

- **Missing Seams** `[mechanism]` — Where would you want to test, swap, or mock — and is there a seam there? Missing seams are often where future refactoring breaks down: the design has no natural place to insert change.

---

## 3. Dependency & Supply Chain Lenses

_What the codebase pulls in from outside, and the cost of those choices over time._

- **Version Currency** `[quality]` — How far behind is each dependency from its current stable release? Distance is debt: each major version skipped compounds upgrade effort.

- **Known Vulnerabilities** `[constraint]` — Are there dependencies with published CVEs, especially at severity ≥ medium? Are these tracked, with a remediation timeline?

- **Maintenance Health** `[quality]` — For each significant dependency: when was the last release, how many open issues, is the maintainer responsive? An "actively maintained" dep can become unmaintained without renaming.

- **License Risk** `[governance]` — Are licenses compatible with the project's use (commercial / open-source distribution / SaaS)? Are copyleft licenses introduced via transitive deps that the project's own license forbids?

- **Unused Dependencies** `[quality]` — Are there declared dependencies the codebase no longer imports? Dead deps are a maintenance tax with zero benefit.

- **Version Skew** `[quality]` — Across a monorepo or related packages, are different versions of the same dependency pinned simultaneously? Skew creates subtle compatibility bugs and inflates install size.

---

## 4. Test Debt Lenses

_Whether the test suite reliably tells the truth about whether the code works._

- **Coverage Gaps** `[quality]` — Are there areas with no tests at all, or coverage gaps in high-risk regions (auth, payments, state machines, retry logic)? Raw line coverage matters less than _critical-path_ coverage.

- **Brittleness** `[quality]` — Do tests fail when behavior is preserved but implementation changes? Brittle tests punish refactoring and erode trust — engineers eventually stop trying to fix them and start deleting them.

- **Flakiness** `[quality]` — Are there tests that pass/fail non-deterministically? Flake rate above ~1% destroys signal — every CI failure now requires human triage.

- **Missing Test Layers** `[quality]` — Is the system tested at the right level? Common gaps: too many integration tests with no unit foundation, no end-to-end tests for critical user journeys, no contract tests between services.

- **Mocks-vs-Reality Drift** `[mechanism]` — Do the test doubles reflect actual external behavior? Mocks frozen years ago can pass while production paths fail. Are there contract tests pinning mock to reality?

- **Suite Performance** `[constraint]` — How long does the full suite take? How long does the developer-feedback subset take? Slow suites change behavior — engineers run them less, or selectively, and bugs slip through.

---

## 5. Operational & Observability Lenses

_How the system is run in production and what it tells you while it's running._

- **Telemetry Coverage** `[quality]` — Can you answer "what is the system doing right now" and "why is it slow" from telemetry alone? Are critical user journeys instrumented end-to-end?

- **Deploy Reversibility** `[mechanism]` — If a deploy goes bad, can it be rolled back without data loss? Is rollback tested, or only theorized?

- **Bring-Up Fragility** `[quality]` — How long does it take a new developer to run the system locally? How many undocumented steps? Each undocumented step is a hidden tax on every newcomer.

- **Oncall Path Clarity** `[governance]` — When something pages, is there a runbook? Does the runbook reflect what oncall actually does, or has it ossified?

- **Performance Cliffs** `[constraint]` — Are there known capacity ceilings (DB connection pool, queue depth, memory headroom) that the system will hit at predictable growth? Has the team decided what to do _before_ hitting them?

- **Scaling Surface** `[quality]` — Which axes (users, data, requests, integrations) require no architectural change to scale, which require planned work, and which are hard ceilings? Is the team aware?

---

## 6. Knowledge & Documentation Lenses

_What the codebase remembers about itself, and what only lives in someone's head._

- **Doc-Code Drift** `[quality]` — Do user-facing docs, internal READMEs, and inline comments describe what the code actually does today? When was each last verified?

- **Undocumented Systems** `[quality]` — Are there components whose intent, contract, or operational requirements live nowhere — only in commit history or oral tradition?

- **Bus Factor** `[governance]` — For each significant component, how many people understand it well enough to fix or modify it safely? A bus factor of 1 is a P1 or P0 risk depending on criticality.

- **Ownership Gaps** `[governance]` — Is every module/service owned by a team or person, with that ownership encoded somewhere queryable (CODEOWNERS, README, ADR)? Unowned code accumulates debt fastest.

- **ADR Practice** `[governance]` — Are architectural decisions recorded as they're made, or only via archaeology? Are existing ADRs still valid, or has the system superseded them silently?

- **Onboarding Cost** `[quality]` — How long does it take a new engineer to make a meaningful change? Onboarding cost is the integral of every other knowledge-debt dimension.

---

## Cross-Cutting Tensions

Lenses interact. Investing in one debt category often delays another. These are *resource-allocation* tensions, not design tradeoffs — the audit team raises them so the user can decide where to spend capacity.

| Tension | Common manifestation |
|---------|----------------------|
| **Refactor ↔ Ship** | Investing in architecture-drift fixes pulls capacity from feature work. Some debt compounds faster than features deliver value — but not always. The audit's job is to surface concrete velocity costs, not opinions. |
| **Test Coverage ↔ Deploy Speed** | Adding test layers slows CI and developer feedback, exactly when operational debt demands faster deploys. The tension is usually solvable (parallelism, sharding) but only with explicit investment. |
| **Dependency Upgrade ↔ Compat Shim** | Upgrading a major-version-behind dep means a one-time pain spike. Keeping a compat shim means an ongoing tax that grows as the gap widens. Compat shims often outlive the engineers who wrote them. |
| **Observability ↔ Code Simplicity** | Adding metrics, traces, and structured logs adds visual noise to code that was already complex. The fix is usually instrumentation abstraction — but that's itself an architecture-drift item. |
| **Stop-the-Bleeding ↔ Build-the-Future** | P0 debt fixes are usually local patches; high-leverage strategic items are usually rewrites. A team can do one or the other in a sprint, not both. Naming the tension is half the planning. |
| **Doc-as-Code ↔ Centralize Docs** | In-repo docs decay with the code; centralized docs decay with platform changes. There's no winning solution — only conscious choice of *which* decay mode you'll budget against. |
| **Bus-Factor Fix ↔ Speed** | The cure for bus-factor-1 is paired work and review on that component — which slows the one person who knows it. Most teams under-invest here because the cost is visible and the benefit is invisible until the bus arrives. |

---

## Debt Archetypes

Codebases accumulate debt in patterns shaped by their history. The audit team uses these archetypes to weight emphasis — not every category needs equal depth for every codebase.

| Archetype | Profile | Signature debt |
|-----------|---------|----------------|
| **Long-lived application** | 5+ years, multiple maintainer generations, original authors mostly gone | Code Health drift, Knowledge gaps, stale ADRs, dependency lag from cautious upgrades |
| **Greenfield-on-legacy** | New code built against an old foundation, often replacing parts of the old | Architecture Drift at the boundary, test debt because tests target the new only, knowledge debt about the legacy half |
| **High-velocity startup** | <3 years, shipping fast, "we'll clean it up later" was the policy | Code Health (TODO/FIXME density), Test Debt (coverage gaps in critical paths), Operational debt (deploy fragility) |
| **Mature platform** | Stable, multi-team, internal or external customers depending on it | Dependency drift (cautious because customers depend), Operational debt (scaling cliffs masked by current load), versioning constraints limit refactoring |
| **Heavily integrated** | Many external dependencies, vendor SDKs, third-party services | Dependency & Supply Chain dominates, Operational debt around integration health-checks, Test Debt around mock-vs-reality drift |
| **Single-author project** | Small codebase, one primary author, often pre-team-scaling | Knowledge debt (bus factor 1 everywhere), Doc gaps, often surprisingly clean code-health because of consistent style |

### Archetype × Category Weighting

For each archetype, lenses are tagged primary (◆) or secondary (○). Unlisted categories still apply at `background` emphasis — they're just less likely to be the *first* thing that matters. Most codebases are hybrids (e.g., a long-lived app that has also been heavily integrated). When archetypes overlap, layer in primary emphases from each applicable archetype.

| Archetype | Code Health | Architecture Drift | Dependency | Test Debt | Operational | Knowledge |
|-----------|-------------|--------------------|------------| ----------|-------------|-----------|
| Long-lived application | ◆ | ○ | ○ | ○ | ○ | ◆ |
| Greenfield-on-legacy | ○ | ◆ | ○ | ◆ | ○ | ○ |
| High-velocity startup | ◆ | ○ | ○ | ◆ | ◆ | ○ |
| Mature platform | ○ | ○ | ◆ | ○ | ◆ | ○ |
| Heavily integrated | ○ | ○ | ◆ | ○ | ◆ | ○ |
| Single-author project | ○ | ○ | ○ | ○ | ○ | ◆ |

---

## Using This Framework

**Tech debt audit:** Walk each category. For every lens, ask: "Is this actively bleeding, compounding, latent, or cosmetic?" Use the weighting table to focus depth on the archetype's primary categories first.

**Cleanup-sprint planning:** Score each lens for the current codebase (clean / drifting / strained / broken). Drifting and strained are where the highest-ROI sprint items live — broken is usually a strategic item, clean doesn't need attention.

**Handoff readiness:** The Knowledge category disproportionately matters when a system is changing hands. A bus-factor-1 + undocumented combination is a P0 *only* when there is concrete handoff evidence — announced transition, named successor onboarding, deadline within ~1 quarter, or an active blocker traced to the gap. Without such evidence it is P1 (compounding) or P2 (latent), not P0. This keeps "actively bleeding today" the consistent bar for P0 across the audit.

**Pre-scaling readiness:** Operational and Performance lenses dominate. Code Health and Knowledge can wait; a scaling cliff hits whether the code is pretty or not.

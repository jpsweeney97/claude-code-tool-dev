---
module: official-plugin-rewrite-map
status: active
normative: false
authority: supporting
---

# Official Plugin Rewrite Map

Concrete rewrite map for adding official-plugin context to the
`codex-collaboration` spec. Governed by one integration principle:

- The **official OpenAI plugin** (`openai/codex-plugin-cc`, pinned at
  `9cb4fe4`) is **reference context** — acknowledged, compared against, but not
  the architectural shell this spec converges toward.
- This spec retains **independent architectural authority**. The split-runtime
  model, control plane, lineage, isolated execution, and promotion machinery
  remain the spec's design center.
- Where the spec's design overlaps with official plugin capabilities, the
  overlap is **intentional** and the rationale is documented.

Changes are additive: relationship sections, comparison annotations, and one
new decision record. No sections are deleted or structurally restructured.

## Rewrite Decisions

### README.md

#### Add a "Relationship to Official Plugin" section

- Add a new section after the introduction (before "Authority Model") titled
  "Relationship to Official Plugin".
- Content:
  - The official OpenAI plugin (`openai/codex-plugin-cc`) provides a packaged
    local integration: local Codex CLI, local app server, shared auth/config,
    same-checkout execution, and native review/task/thread utilities.
  - This spec takes a different approach: a mediating control plane, structured
    flows, durable lineage, isolated execution, and explicit promotion.
  - Where capabilities overlap (e.g., review/consult, task delegation), this
    spec's approach adds structured contracts, trust enforcement, and recovery
    semantics that the official plugin does not provide.
  - The official plugin is reference context for understanding the integration
    landscape, not a convergence target.

#### Add an upstream-pin note

- At the bottom of the new section, add:
  - "Official plugin comparison is pinned to upstream commit `9cb4fe4`. If
    upstream changes materially, re-evaluate comparison claims."

### foundations.md

#### Add a goal

- In the Goals section, add:
  - "Acknowledge where Codex-native primitives satisfy requirements without
    custom control-plane machinery, and document why this spec's approach was
    chosen where it overlaps."

#### Annotate the Context Assembly Contract scope

- Add a scope note at the top of the Context Assembly Contract subsection:
  - "The official plugin assembles context through native app-server thread
    utilities. This contract applies to the spec's structured flows, which
    require richer assembly (redaction, lineage injection, profile-driven
    effort) than native utilities provide."

#### Annotate the Prompting Contract scope

- Add a scope note at the top of the Prompting Contract subsection:
  - "Native Codex review/task flows exist and handle basic prompting. This
    contract governs the spec's structured prompt packets, which carry
    additional metadata (posture, effort, supplementary context) not
    expressible through native flows."

### contracts.md

#### Add official-plugin comparison note to tool-surface preamble

- After the opening paragraph that states Claude interacts with Codex
  exclusively through the listed MCP tools, add:
  - "The official plugin exposes native app-server methods directly to Claude.
    This spec mediates through a control plane instead, providing structured
    contracts, typed responses, and audit observability at the boundary."

#### Annotate components with no official-plugin equivalent

- Add a brief note to the following subsections indicating they have no
  equivalent in the official plugin:
  - Lineage Store — "No equivalent in the official plugin, which relies on
    native thread continuity."
  - Operation Journal — "No equivalent; the official plugin has no crash
    recovery or idempotency mechanism."
  - Promotion Protocol — "No equivalent; the official plugin executes in the
    shared checkout without promotion gates."

### delivery.md

#### Add official-plugin step mapping to build sequence

- After the existing build-sequence table, add a comparison note titled
  "Official Plugin Equivalents":
  - Map each build step to its official-plugin equivalent or note the gap:
    - `codex.status` -> official plugin has version/health check
    - `codex.consult` -> official plugin uses native review thread
    - lineage store -> no equivalent (gap)
    - dialogue -> no equivalent (gap)
    - hook guard -> official plugin has no `PreToolUse` enforcement (gap)
    - isolated execution -> no equivalent; official plugin uses shared checkout
      (gap)
    - promotion -> no equivalent (gap)
  - Add one sentence: "Steps with no official-plugin equivalent are the core
    value proposition of this spec's extension architecture."

### decisions.md

#### Add governance decision record

- Add a new decision record titled "Official Plugin as Reference Context, Not
  Convergence Target":
  - **Decision:** The official OpenAI plugin (`openai/codex-plugin-cc`) is
    reference context for the integration landscape. This spec maintains
    independent architectural authority and does not restructure around the
    official plugin as a baseline shell.
  - **Rationale:** The spec's control-plane mediation, structured flows,
    durable lineage, isolated execution, and promotion machinery provide
    capabilities the official plugin does not. Converging toward the official
    plugin's shell would require abandoning these capabilities or relegating
    them to optional extensions, reducing the spec's coherence.
  - **Tradeoff:** Higher maintenance burden (own the full stack) in exchange
    for architectural independence and the ability to evolve without upstream
    coupling.
  - **Upstream pin:** `9cb4fe4`. Re-evaluate if upstream adds lineage,
    isolation, or promotion equivalents.

#### Add considered-and-rejected architecture option

- In the architecture option analysis, add one option row:
  - **Option: Thin bridge to official plugin** — Treat the official plugin as
    the integration shell; specify only extension layers on top.
  - **Status:** Rejected.
  - **Rationale:** Would fragment the spec into baseline (deferred to
    upstream) and extension (owned locally), creating two integration models
    instead of one. The spec's value is in its unified control-plane
    architecture, not individual extension features.

#### Keep the open question about codex.consult

- Add to open questions (if not already present):
  - "Whether `codex.consult` should be retired in favor of native
    review/task patterns plus a lighter structured wrapper. The official
    plugin's native review thread is a relevant comparison point."

## Scope

This rewrite map covers annotations and additions to:

- [README.md](README.md)
- [foundations.md](foundations.md)
- [contracts.md](contracts.md)
- [delivery.md](delivery.md)
- [decisions.md](decisions.md)

No changes to [spec.yaml](spec.yaml) are required — the authority model does
not need a baseline/extension axis under this governance approach.

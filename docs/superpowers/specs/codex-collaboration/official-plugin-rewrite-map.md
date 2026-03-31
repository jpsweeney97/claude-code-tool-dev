---
module: official-plugin-rewrite-map
status: active
normative: false
authority: supporting
---

# Official Plugin Rewrite Map

Concrete rewrite map for reclassifying the `codex-collaboration` spec around
the following integration principle:

- **Baseline** means the default Claude Code <-> Codex integration should follow
  the official OpenAI plugin model: local Codex CLI and app server, same local
  auth/config, same checkout and machine environment, and native app-server
  review/thread/task utilities first.
- **Extension** means additive behavior kept only where Codex-native flows are
  insufficient, such as durable dialogue lineage, isolated execution, explicit
  promotion, or stronger trust and recovery guarantees.
- **Delete** means stop treating the element as normative default behavior.

This document is a rewrite artifact. It does not itself change authority or
normative behavior in the packet.

## Rewrite Decisions

### README.md

#### Rewrite the introduction

- Replace the opening description so the packet is no longer presented as the
  default architecture for Claude Code <-> Codex integration.
- State instead that the official OpenAI plugin is the baseline packaged local
  integration model, and `codex-collaboration` specifies an extension layer for
  capabilities that baseline does not provide.

#### Delete the current default architecture statement

- Delete the sentence that presents the split-runtime model as the default
  design center for the whole packet:
  - current target: `README.md` paragraph beginning "The design uses a
    split-runtime model..."

#### Add a baseline-integration paragraph

- Add a short paragraph immediately after the introduction that says:
  - baseline uses the local `codex` CLI and local app server
  - baseline inherits local auth and config
  - baseline uses the same checkout and machine-local environment
  - custom control-plane contracts in this packet apply only to extension
    flows unless explicitly marked baseline

#### Reframe the authority model prose

- Keep the existing authority table, but add one sentence after it:
  - `foundations`, `contracts`, and `delivery` now describe both baseline and
    extension concerns, and must label which claims belong to which lane
- Do not change authority names in this file yet

#### Update reading-order descriptions

- Rewrite the row descriptions to reflect the new split:
  - `foundations.md`: baseline integration assumptions plus extension
    architecture and trust model
  - `contracts.md`: extension interfaces, persistent models, and local-only
    control-plane contracts
  - `delivery.md`: baseline packaged shell and extension milestone plan
  - `decisions.md`: baseline-vs-extension architecture decisions

### foundations.md

#### Rewrite scope around baseline vs extension

- Replace the current three-capability framing as the default view of the
  product.
- Introduce two lanes:
  - **Baseline lane:** local review, task delegation, status, and native thread
    continuity through local Codex CLI/app server
  - **Extension lane:** durable dialogue lineage, isolated execution,
    promotion, and stronger trust/recovery semantics

#### Replace the capability table

- Remove the current table that treats consultation, dialogue, and delegation
  across advisory/execution runtimes as the default model.
- Replace it with:
  - baseline capability rows
  - extension capability rows
  - explicit notes on which rows require custom control-plane state

#### Rewrite goals and non-goals

- Add a goal:
  - "Reuse Codex-native app-server behavior where it already satisfies the
    product requirement."
- Rewrite non-goals:
  - delete the blanket implication that raw App Server exposure is never valid
  - replace it with "Do not rebuild native review/task behavior when native
    app-server primitives are sufficient."

#### Replace Architectural Shape

- Rewrite the section into a two-layer architecture:
  - **Baseline shell:** Claude plugin commands/hooks -> local Codex CLI/app
    server
  - **Extension substrate:** optional local control plane for dialogue
    lineage, isolated execution, promotion, and stronger enforcement/recovery
- Delete the current universal statement that Claude never interacts with App
  Server directly through baseline flows.

#### Rewrite Runtime Domains

- Recast the current advisory domain as baseline shared-session runtime
  behavior where appropriate.
- Move split advisory/execution runtime language under explicit extension
  scoping.
- Keep isolated execution as an extension-only runtime model.

#### Rewrite Trust Model

- Do not present `PreToolUse` as the universal outer boundary.
- New structure:
  - baseline trust boundary: native Codex sandbox and approval behavior plus
    plugin shell controls
  - extension trust boundary: optional `PreToolUse` guard and packet-level
    enforcement for extension flows

#### Rewrite Approval Invariant

- Keep the no-cross-job approval invariant only for extension isolated
  execution.
- Add that baseline flows inherit native Codex approval/sandbox semantics
  unless the extension lane is engaged.

#### Rewrite core flows

- Replace `Consultation` with a baseline review/consult-style flow using
  native app-server thread/review utilities.
- Replace `Delegation` with same-checkout task execution as the baseline path.
- Move dialogue lineage and promotion flows under explicit extension-only
  headings.

#### Re-scope Prompting Contract and Context Assembly Contract

- Rewrite `Prompting Contract` to say native review/task flows come first.
- Keep plugin-owned prompt packets only for extension flows that need richer
  structure than native review/task utilities provide.
- Preface `Context Assembly Contract` with a scope line:
  - applies to extension flows only
  - baseline integration does not require this full control-plane assembly
    contract

### contracts.md

#### Replace the top-level tool-surface framing

- Delete the universal claim that Claude interacts with Codex exclusively
  through the listed MCP tools.
- Delete the universal claim that raw App Server methods are never exposed.

#### Split the public surface into two sections

- Add `## Baseline Integration Surface`
- Add `## Extension Tool Surface`

#### Baseline Integration Surface

- Describe baseline behavior in terms of:
  - local Codex bridge
  - native thread/review/task/status semantics
  - local session continuity and local config/auth inheritance
- Do not attempt to fully restate the official plugin command contract here.
- Keep it descriptive and narrow: this packet treats that behavior as the
  baseline to preserve.

#### Extension Tool Surface

- Move the current `codex.consult`, `codex.dialogue.*`, and `codex.delegate.*`
  surface into this section.
- Add one scope sentence:
  - these tools exist only when the extension control plane is active

#### Re-scope data models

- Mark `CollaborationHandle` as extension-only.
- Add a note that baseline flows may use native Codex thread identity directly.
- Split `DelegationJob` into:
  - lightweight baseline tracked-job metadata concept
  - extension isolated-execution job with worktree and promotion semantics
- Mark `PendingServerRequest` as extension-only.

#### Re-scope persistence and observability

- Mark `Lineage Store` as extension-only.
- Mark `Audit Event Schema` as extension observability, not a baseline shell
  requirement.
- Mark `Typed Response Shapes` for dialogue and promotion as extension-only.

#### Keep runtime health but narrow its scope

- Keep a runtime-health/status concept.
- Rewrite it so it no longer implies the full extension control-plane shape is
  the baseline status contract.

### delivery.md

#### Replace the implementation-language decision

- Delete the unconditional choice of Python for the Claude-side control plane.
- Replace with:
  - baseline packaged shell should be Node/TypeScript, aligned with the
    official plugin shape
  - extension-only services may use another language if they are clearly behind
    the baseline shell and not the packaged integration surface

#### Replace plugin component structure

- Delete the current Python/MCP-first tree as the default structure.
- Replace with a packaged-plugin-first structure:
  - `.claude-plugin/`
  - `commands/`
  - `hooks/`
  - `agents/` where needed
  - `scripts/` for local Codex bridge/runtime helpers
  - optional `extension/` or `server/` subtree for advanced control-plane
    behavior

#### Rewrite compatibility policy

- Keep version/auth/runtime checks.
- Rewrite them as baseline shell responsibilities for the local Codex bridge.
- Do not frame vendored schema and control-plane bring-up as the primary
  product contract.

#### Replace the build sequence

- Delete the current step sequence that assumes:
  - `codex.status`
  - `codex.consult`
  - lineage store
  - dialogue
  - hook guard
  - isolated execution
  - promotion

- Replace with:
  1. packaged plugin shell with setup/status/result/cancel
  2. native review/task bridge through local Codex CLI/app server
  3. optional structured consult wrapper if still justified
  4. extension dialogue lineage
  5. extension isolated execution
  6. extension promotion

#### Delete the current deployment-profile framing

- Delete the `R1/R2 Deployment Profile` section that says packaged plugin
  structure is out of scope.
- Replace with a statement that packaged plugin shape is baseline reality.

#### Rewrite test strategy into two lanes

- `Baseline tests`:
  - packaged shell
  - local auth/config inheritance
  - shared broker reuse
  - same-checkout review/task behavior
  - portable tests that do not depend on a hardcoded checkout path
- `Extension tests`:
  - dialogue lineage
  - journal/recovery
  - isolated worktree execution
  - promotion
  - extension-only trust-boundary enforcement

### decisions.md

#### Rewrite Greenfield Rules

- Delete the implication that slash-command surfaces and existing integration
  shells are replaced by default.
- Replace with:
  - baseline packaged integration follows the official local Codex bridge model
  - greenfield replacement applies only to extension-only contracts such as
    dialogue lineage, isolated execution, promotion, and stronger recovery

#### Replace Supersession Direction

- Delete the current claim that `codex-collaboration` is the sole planned
  successor.
- Replace with a new decision record:
  - official OpenAI plugin is the baseline local integration model
  - `codex-collaboration` remains an extension track for capabilities not
    covered by that baseline

#### Rewrite architecture option analysis

- Add a baseline option for:
  - thin local Codex bridge using native app-server capabilities
- Keep split App Server domains only as the selected extension architecture
  where higher assurance or stronger product semantics justify the extra
  machinery

#### Re-scope accepted tradeoffs

- Rewrite T1 and T2 so they are conditional tradeoffs for the extension lane,
  not universal truths about the whole product

#### Add a new decision record

- Add:
  - "Native Codex primitives first; custom plugin contracts only where native
    primitives are insufficient."

#### Add a new open question if unresolved

- Add:
  - whether `codex.consult` remains a distinct extension surface or should be
    retired in favor of native task/review patterns plus a lighter structured
    wrapper

## Follow-On Note

This rewrite map covers:

- [README.md](README.md)
- [foundations.md](foundations.md)
- [contracts.md](contracts.md)
- [delivery.md](delivery.md)
- [decisions.md](decisions.md)

If these rewrites are accepted, [spec.yaml](spec.yaml) will also require a
follow-on update so the authority and precedence model can express
baseline-versus-extension claims explicitly.

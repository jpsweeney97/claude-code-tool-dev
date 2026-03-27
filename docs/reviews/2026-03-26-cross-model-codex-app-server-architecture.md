## Adversarial Review: Cross-Model Codex App Server Architecture

### 1. Assumptions Audit
- **The current `codex exec` transport is the main limiter on consultation quality rather than the surrounding control plane** - `validated`. If this is wrong, a large transport rewrite will spend effort below the actual bottleneck and still leave dialogue quality mostly unchanged. Evidence: the current adapter is batch-shaped and JSONL-scraping in [codex_consult.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_consult.py#L1), while the dialogue agent already wants durable multi-turn state in [codex-dialogue.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/agents/codex-dialogue.md#L107).
- **A single long-lived App Server process can safely host advisory consultations and autonomous delegation under one runtime boundary** - `wishful`. If this is wrong, session-scoped approvals or writable grants can bleed across capability classes and collapse the plugin's current trust separation. Risk surface: the recommendation explicitly moves delegation onto the same runtime in [the decision record](/Users/jp/Projects/active/claude-code-tool-dev/docs/decisions/2026-03-26-cross-model-codex-app-server-architecture.md#L262), while App Server approvals support `acceptForSession` in the official [approvals docs](https://developers.openai.com/codex/app-server/#approvals).
- **`thread/fork` can become first-class without reworking the current dialogue and context-injection state model** - `wishful`. If this is wrong, forked conversations will break checkpoint continuity, scout integrity, synthesis logic, and analytics lineage. Current system assumption: `conversation_id` is the same as `threadId` in [codex-dialogue.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/agents/codex-dialogue.md#L121), and context-injection stores state per `conversation_id` in [state.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/state.py#L92).
- **Bridge-level safety can replace hook-level safety without losing the strongest fail-closed boundary** - `wishful`. If this is wrong, a bug or alternate call path inside the broker bypasses the only current host-level outbound gate. The recommendation says to demote hooks to optional defense-in-depth in [the decision record](/Users/jp/Projects/active/claude-code-tool-dev/docs/decisions/2026-03-26-cross-model-codex-app-server-architecture.md#L303), but `codex_guard.py` is currently the only pre-dispatch enforcement point at the tool boundary in [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L139).
- **`thread/read` plus persisted thread state are sufficient for crash recovery and synthesis reconstruction** - `plausible`. If this is wrong, a child or parent restart loses active-turn state in ways the new broker cannot reconstruct, leaving the plugin with a more complex but still brittle runtime.
- **The plugin host can absorb a long-lived child process, background read loop, protocol router, and server-initiated request handling without becoming the new source of instability** - `plausible`. If this is wrong, the project trades a simple subprocess adapter for a bespoke integration platform that is harder to reason about and verify.

### 2. Pre-Mortem
1. **Most likely failure:** the team builds the broker, gets `consult` working, then discovers that `turn/steer`, `thread/fork`, and dialogue recovery do not map cleanly onto the existing `threadId == conversation_id` assumptions. The result is a half-migrated system: a large new runtime plus fallback logic, with limited real capability gain beyond cleaner single-turn transport.
2. **Most damaging quiet failure:** delegation is moved onto the same long-lived App Server process as advisory flows, and a session-scoped approval or write grant persists farther than intended. Nothing explodes immediately, but the plugin's trust model is silently weakened because advisory conversations now run adjacent to delegation-grade permissions in the same runtime session.

### 3. Dimensional Critique
#### Correctness
The recommendation overstates how drop-in `thread/fork` is. The current dialogue system treats `threadId` as the canonical conversation identity and passes it straight into `process_turn` as `conversation_id` in [codex-dialogue.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/agents/codex-dialogue.md#L119). Context-injection persists checkpoints, turn-request refs, and conversation state keyed to that identifier in [state.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/state.py#L113). Making forks a first-class dialogue move is therefore not just a transport upgrade; it changes the correctness model for checkpoints, scout replay protection, turn history, and synthesis lineage. The recommendation praises forking as an architectural win in [the decision record](/Users/jp/Projects/active/claude-code-tool-dev/docs/decisions/2026-03-26-cross-model-codex-app-server-architecture.md#L251) without addressing those invariants.

The recommendation also treats a shared runtime for delegation as an implementation detail, but it is a correctness issue in the plugin's trust model. The plugin today has intentionally different safety envelopes for `/codex`, `/dialogue`, and `/delegate` in [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L59). App Server's approval model includes session-scoped decisions, which makes "same runtime" materially different from "same transport."

#### Completeness
The recommendation is incomplete on the hardest parts:

- It does not define how server-initiated App Server requests are surfaced or answered beyond a general router, even though approvals and user-input requests are core protocol features in the official [approvals docs](https://developers.openai.com/codex/app-server/#approvals).
- It does not specify recovery semantics for child crash, parent crash, lost subscription, or partially completed active turns. Saying "`thread/read` for crash recovery" in [the decision record](/Users/jp/Projects/active/claude-code-tool-dev/docs/decisions/2026-03-26-cross-model-codex-app-server-architecture.md#L251) is directionally useful but not enough to make the runtime operable.
- It does not define whether delegation lives in the same process, a separate App Server process, or a separate policy domain. That omission matters because the recommendation explicitly wants a single `DelegationService` inside the same broker in [the decision record](/Users/jp/Projects/active/claude-code-tool-dev/docs/decisions/2026-03-26-cross-model-codex-app-server-architecture.md#L204).
- It does not define how analytics and lineage work across forked threads. The current event model is thread-centered, and the recommendation introduces branching without naming a parent/child thread model.

#### Security / Trust Boundaries
This is the sharpest problem in the recommendation.

Demoting hooks to optional defense-in-depth is a trust-boundary regression. Today the strongest fail-closed secret scan happens before Codex dispatch at the Claude tool boundary in [codex_guard.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_guard.py#L91). Moving the scanner into the bridge is still useful, but it is not equivalent. It narrows enforcement to paths that go through the broker correctly. If a new tool, maintenance path, or direct App Server call bypasses the bridge, the outer gate is gone.

The recommendation's "same runtime eventually for delegation" is also unsafe as written. App Server approvals allow session-level acceptance; that means the runtime boundary is part of the permission boundary, not just a process-management choice. The proposal should have treated delegation isolation as a first-order architecture constraint, not as a later policy detail.

#### Operational
The recommendation underestimates the operational cost of a long-lived broker:

- The current context-injection server already documents single-flight assumptions and bounded per-process state in [state.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/state.py#L155). Adding another long-lived stateful runtime compounds, rather than simplifies, the operational model.
- The broker has to supervise the child, serialize requests, route notifications, handle server-initiated requests, reconcile loaded threads, and clean up abandoned sessions. That is a substantial runtime, not a bridge.
- Resource growth is underspecified. The recommendation mentions idle cleanup but gives no policy for loaded threads, active subscriptions, or session churn. That matters because the design intentionally keeps the App Server alive for the plugin server lifetime in [the decision record](/Users/jp/Projects/active/claude-code-tool-dev/docs/decisions/2026-03-26-cross-model-codex-app-server-architecture.md#L173).

#### Maintainability
The architecture risks replacing a small transport adapter with a second orchestration platform. `AppServerSupervisor`, `JsonRpcClient`, `ThreadRuntime`, `TurnAccumulator`, `CodexControlPlane`, and four domain services in [the decision record](/Users/jp/Projects/active/claude-code-tool-dev/docs/decisions/2026-03-26-cross-model-codex-app-server-architecture.md#L177) is a lot of new permanent infrastructure. That may still be worth it, but the recommendation does not set any kill criteria for "broker scope is getting ahead of delivered value."

There is also a coupling risk: the plugin will now have two independent stateful control planes, App Server and context-injection. The recommendation assumes they compose cleanly, but the current codebase has not been shaped around branch-aware multi-thread state.

#### Alternatives Foregone
The strongest credible alternative is not the raw passthrough or stateless bridge that the decision record scored lower. It is a **split architecture**:

- stateful App Server broker for `/codex`, `/dialogue`, and review
- isolated per-task App Server process or separate broker instance for `/delegate`
- hooks remain authoritative outer enforcement, with bridge-level scanning as a second layer

That alternative preserves most of the capability unlock while avoiding the worst trust-boundary regression. The recommendation does not engage with it directly, even though it is more credible than the raw passthrough option in this repo.

### 4. Severity Summary
1. **Shared runtime for delegation and advisory flows collapses trust boundaries** - `blocking` - Treat delegation isolation as an architectural requirement, not a later policy decision. At minimum, investigate separate process or separate approval domain boundaries before proceeding.
2. **`thread/fork` is not compatible with current dialogue/context-injection invariants as stated** - `high` - Define how forked threads affect `conversation_id`, checkpoints, scope envelopes, analytics lineage, and synthesis before making forking first-class.
3. **Demoting hooks to optional defense-in-depth weakens the strongest current fail-closed gate** - `high` - Keep host-level hook enforcement authoritative until the bridge can be shown to be equivalent and non-bypassable.
4. **Crash recovery and server-initiated request handling are underspecified for a long-lived broker** - `high` - Investigate exact recovery semantics for child crash, parent crash, lost subscriptions, partial turns, approvals, and request cleanup before committing to the runtime model.
5. **The broker scope is large enough to become a second platform before it proves value** - `moderate` - Narrow the first slice and define explicit stop/go criteria so the transport rewrite does not sprawl into a general client framework.

### 5. Confidence Check
**3** - The recommendation is directionally promising, but it is not safe to proceed as written because the trust-boundary model, fork semantics, and recovery model are under-specified.

To raise this to 4, the proposal needs three concrete changes: treat delegation isolation as a first-class architecture decision, keep hook-level enforcement authoritative, and define explicit semantics for fork lineage and crash recovery instead of assuming the existing thread-scoped control plane will absorb them.

# Decision: Entity Injection via Codex Responses — Accepted Risk with Extensions Path

**Date:** 2026-03-26
**Status:** Decided
**Responding to:** F4/TS-2 from the cross-model plugin design review audit
**Codex dialogue threads:** `019d2b30-e1f0-7721-abfa-833060fe2bb4` (pipeline trust analysis), `019d2b45-be62-77c1-b346-65e9bb5def33` (remediation strategy), `019d2b6d-b7b8-7830-9de2-26d20c5c9853` (adversarial ADR review)

---

## Context

### What the context-injection system does

The cross-model plugin enables multi-turn dialogues between Claude and OpenAI Codex. During these dialogues, an MCP server called "context-injection" provides mid-conversation evidence gathering — it reads files from the local repository to verify Codex's factual claims. This prevents the dialogue from drifting on ungrounded assertions.

The system uses a two-call protocol:

- **Call 1 (`process_turn`):** The `codex-dialogue` agent extracts semantic claims from each Codex response and submits them to the context-injection server as a `TurnRequest`. The server runs a 17-step pipeline that extracts entities (file paths, symbols, URLs) from claim text using regex, checks them against safety gates (denylist, git-tracking, containment), and generates HMAC-signed scout options for eligible entities. The agent receives these options as opaque `scout_option_id` + `scout_token` pairs.

- **Call 2 (`execute_scout`):** The agent selects a scout option and submits it back. The server validates the HMAC token (ensuring the scout spec hasn't been tampered with since Call 1), re-checks path safety at runtime, reads the file, redacts secrets, truncates to size limits, and returns an evidence wrapper. The agent includes this evidence in its next follow-up prompt to Codex.

The protocol's design intent is that the agent controls *what to ask about* (scope anchoring — which claims enter the pipeline) while the server controls *what is safe to read* (path safety — denylist, containment, git-tracking, HMAC integrity).

### The entity injection attack surface (F4/TS-2)

The cross-model plugin design review audit (2026-03-26) identified a P1 finding in the trust-safety review:

> **TS-2: Prompt injection via Codex responses can influence scope anchoring (documented, accepted risk)**
>
> The contract explicitly documents that a compromised `codex-dialogue` agent (e.g., via prompt injection through Codex responses) could include entities outside the true user scope in `TurnRequest`. The agent — not the helper — controls scope anchoring (what to send). The helper enforces path-level safety but cannot enforce intent-level scope.

The audit rated this P1 with `confidence: medium` and `decision_state: explicit tradeoff`. It was classified as accepted MVP risk, not a pre-1.0 blocker.

### The attack chain

The specific attack path is a 6-gate chain:

1. **Codex response contains a file reference.** A Codex response includes a backticked file path — for example, `` `config/production.yaml` `` or `` `src/internal/auth.py:42` ``. This can happen naturally (Codex discussing code) or through adversarial prompt injection (Codex crafting responses to steer file reads).

2. **Agent extracts the reference into a claim.** The `codex-dialogue` agent (an LLM following `codex-dialogue.md`) extracts semantic claims from the Codex response. If the agent includes the file reference in a claim's text, it enters the pipeline. This gate is probabilistic — the agent writes semantic claims, not verbatim Codex text, so file references are sometimes preserved and sometimes paraphrased away. This is incidental friction from LLM behavior, not a security control.

3. **Entity extraction regex matches the claim text.** The server's `extract_entities()` function (`entities.py`) runs 6 ordered sub-extractors (URLs, file_loc, file_path, file_name, dotted symbols, errors) with span tracking. File paths and names with known extensions (`.py`, `.yaml`, `.json`, etc.) are matched regardless of whether they appear in backticks. Backticked references get `confidence="high"`; unquoted matches with path separators or known extensions get `confidence="medium"`. Both confidence levels pass the downstream hard gate.

4. **Denylist and git ls-files check.** The server's `check_path_compile_time()` function (`paths.py`) runs a 6-stage pipeline: normalize input → resolve absolute path → containment check (must be under repo root) → denylist check (`.env`, `*.pem`, `*.key`, `credentials.json`, `.git/`, `.ssh/`, etc.) → git ls-files gate (must be tracked) → risk signal detection. This gate blocks the most sensitive files but allows all other git-tracked files — essentially the entire committed codebase.

5. **Template matching hard gate.** The server's `match_templates()` function (`templates.py`) enforces three hard gates for probe template eligibility: (a) MVP Tier 1 entity type (`file_loc`, `file_path`, `file_name`, `symbol`), (b) `confidence` is `"high"` or `"medium"`, and (c) `in_focus` is `True`. Entities from `TurnRequest.focus.claims` are extracted with `in_focus=True` in `pipeline.py:188-196`. This means entities from the current turn's claims — including those originating from Codex responses — automatically pass the focus-affinity gate. The gate was designed to filter *context-only* entities from conversation history (`prior_claims`, extracted with `in_focus=False`), not to distinguish user-originated from Codex-originated claims.

6. **Scout execution.** If a template candidate is generated and the agent selects it, `execute_scout` validates the HMAC token, re-checks the path at runtime, reads the file, redacts secrets, and returns the content. The agent includes this content in its next follow-up to Codex — completing the exfiltration path.

**Gates 3-6 are deterministic code and provably open for any git-tracked, non-denylisted file.** Gate 1 (Codex mentions file paths) is expected behavior. Gate 2 (agent claim extraction fidelity) is the only non-deterministic step, and it provides probabilistic friction, not structural protection.

### Current mitigations

The system has layered defenses that limit (but do not eliminate) the attack surface. These defenses operate at different enforcement layers, which is critical for understanding what each actually guarantees:

**Server-enforced controls** (enforced in context-injection server code — cannot be bypassed by a compromised agent):

| Mitigation | What it blocks | What it doesn't block |
|------------|---------------|----------------------|
| **Denylist** (`paths.py:47-75`) | `.env`, `*.pem`, `*.key`, `credentials.json`, `.git/`, `.ssh/`, `.aws/`, etc. | All other git-tracked files (source code, configs, documentation) |
| **git ls-files** (`paths.py:399-406`) | Untracked files, temporary files, build artifacts | Any committed file |
| **Redaction** (`redact.py`, `redact_formats.py`) | Secrets in file content (AWS keys, PEM blocks, JWTs, GitHub PATs) | Non-secret content (source code, architecture docs, internal configs) |
| **Budget cap** (`templates.py:44`) | More than 5 scouts per conversation (1 per turn) | The first 5 file reads (up to 40 lines / 2000 chars each, halved for risk-signal files) |
| **Containment** (`paths.py:364-377`) | Paths outside the repository root | Everything inside the repo |
| **HMAC integrity** (`state.py:135`) | Tampering with scout specs between Call 1 and Call 2 | Scout specs that were legitimately minted in Call 1 |

**Agent-advisory controls** (enforced only in agent instruction documents — bypassed if the agent is compromised via prompt injection):

| Mitigation | What it blocks | Enforcement gap |
|------------|---------------|----------------|
| **Scope envelope** (`codex-dialogue.md:374-388`) | Files outside `allowed_roots` (when populated) | Agent-side only — `scope_envelope` is absent from all server-side Python code. Defaults to unrestricted when absent. |

**Future trust-root seeds** (not yet implemented — design artifacts that could anchor a post-1.0 trust root):

| Seed | Where it exists | Why it's a seed |
|------|----------------|----------------|
| `/dialogue` skill preflight `scope_envelope` | `skills/dialogue/SKILL.md:367` | Orchestrator-produced, pre-Codex artifact — computed outside the agent before any Codex interaction |

The effective defense is: **the server prevents reading credential files, untracked files, and files outside the repo. It redacts secrets from allowed files. It caps total reads to 5 per conversation. Everything else — including scope restriction — depends on the agent following its instructions.**

### The `scope_envelope` gap

The `scope_envelope` mechanism is the strongest agent-advisory mitigation, but it has two significant limitations:

1. **Optional and defaulting to unrestricted.** The `codex-dialogue` agent's spec says: "When absent, treated as unrestricted (backwards compatibility)." The `/dialogue` skill constructs it from §3 preflight, but there is no enforcement gate that rejects a dialogue without `scope_envelope`. If the agent is invoked without it (e.g., standalone, or from a caller that doesn't implement preflight), scouting is unrestricted.

2. **Checks path prefixes, not entity origin.** `scope_envelope.allowed_roots` restricts *where* scouts can read, not *who suggested the read*. A Codex-injected entity pointing to a file within the allowed roots passes the scope check.

### The original design intent

The original design document for the context-injection system (`docs/superpowers/plans/2026-02-11-conversation-aware-context-injection.md`) explicitly intended entity origin tracking:

> "Entities from assistant turns after the first evidence injection are ineligible for scouting unless the user explicitly mentions them."

This was designed as a structural, server-side control — not an agent instruction. However, it was not implemented in the v0.2.0 schema. The `Entity` type has `in_focus: bool` and `source_type: Literal["claim", "unresolved"]` but no origin or provenance field. The `Claim` type has only `text: str` — no `origin` field to distinguish user-supplied from Codex-relayed claims.

### Schema versioning constraint

The context-injection protocol uses schema version `0.2.0` with `extra="forbid"` (Pydantic strict mode) and exact-match semantics. This means:

- Any new field on `TurnRequest`, `Claim`, or `Entity` requires a version bump to `0.3.0`
- Agent and server must deploy simultaneously — version mismatch causes hard rejection
- In-flight conversations fail at the version boundary
- The rollout procedure is undocumented (audit finding F5, also P1)

This constraint makes "just add a field" significantly more expensive than it appears.

---

## Problem Statement

TS-2 recommended adding a `codex_supplied` entity marker as a "v2 hardening item." The question is:

1. Should `codex_supplied` (or any entity provenance mechanism) be a pre-1.0 requirement, blocking the schema stabilization cut?
2. If not, what is the right remediation path that addresses entity injection without premature commitment to a provenance architecture?

---

## Options Considered

### Option 1: `codex_supplied` boolean on Entity (TS-2's literal recommendation)

Add a `codex_supplied: bool` field to the `Entity` type. The agent would set it to `True` for entities extracted from claims that originated in Codex responses. Template matching would add a hard gate: `if entity.codex_supplied and not in_scope_envelope: skip`.

**Schema change:** New field on `Entity`. Version bump to `0.3.0`. Ripple through pipeline steps 7-10, template matching, checkpoint serialization.

**Trust model analysis:** The agent populates `codex_supplied`. The agent is the same component that F4/TS-2 identifies as the attack surface — a prompt-injected agent can set `codex_supplied=False` on Codex-originated entities. This is agent-asserted provenance, and it has the same trust class as the current `scope_envelope`: it helps against honest mistakes and implementation drift, but does not address the adversarial threat model that F4/TS-2 describes.

**Additional issues:**
- The name `codex_supplied` is Codex-specific. The actual concern is user-originated vs. assistant-originated entities — a general trust boundary, not a vendor-specific one.
- If the system later supports other external models, each would need its own marker or the marker would need generalization — a naming debt.

**Verdict:** Rejected. Agent-asserted provenance cannot close the trust gap it's meant to address.

### Option 2: `claim.origin` field on TurnRequest

Add `origin: Literal["user", "codex"]` to the `Claim` type. The server would use this to set provenance on extracted entities, enabling server-side enforcement without trusting entity-level agent assertions.

**Schema change:** New field on `Claim`. Version bump to `0.3.0`. Ripple across all 17 pipeline steps (claims are used in validation, ledger entry construction, cumulative state, checkpoint serialization).

**Trust model analysis:** Identical to Option 1 — the agent still asserts claim origin. Moving the assertion from Entity to Claim doesn't change who produces it. The helper receives `origin` from the agent and trusts it, which is the same vulnerability.

**Additional issues:**
- Larger blast radius than Option 1 (Claim is used more broadly than Entity)
- Checkpoint serialization would need to include origin metadata, increasing checkpoint payload size toward the 16 KB cap

**Verdict:** Rejected. Same trust model weakness as Option 1, with larger implementation cost.

### Option 3: Agent-only enforcement in `codex-dialogue.md`

No schema change. Modify the `codex-dialogue` agent's instructions to track which claims originated from Codex responses and exclude them from `focus.claims` (or mark them in a way that prevents entity extraction).

**Schema change:** None. Agent instruction change only.

**Trust model analysis:** This is strictly weaker than Options 1 and 2. Agent-only enforcement cannot be validated by the helper — there is no field for the helper to check. The defense exists entirely in the agent's instruction-following behavior, which is precisely what prompt injection compromises. A Codex response that successfully injects instructions into the agent's behavior would bypass agent-only enforcement by definition.

**Verdict:** Rejected. Cannot be validated by the helper; defeated by the threat it's meant to address.

### Option 4: Extensions + capabilities mechanism (chosen)

Do not add entity provenance to the 1.0 schema. Instead, add a schema evolution mechanism that makes future provenance possible without breaking changes:

- **`TurnRequest.extensions`**: A namespaced dictionary (`dict[str, Any]`) for optional, non-core fields. Preserves `extra="forbid"` on all existing core fields while providing a forward-compatible extension point.
- **`TurnRequest.required_capabilities`**: A list of capability identifiers (`list[str]`). When present, the server must support all listed capabilities or return an `unsupported_capability` error.

**Schema change:** Two new fields on `TurnRequest`. Version bump to `0.3.0`. Minimal ripple — extensions are opaque to the core pipeline; required_capabilities adds one validation step.

**Trust model analysis:** This does not solve entity injection. It does not pretend to. It provides the *mechanism* for a future solution while explicitly acknowledging that the solution itself (trusted provenance from an independent trust root) is not yet designed.

**What this mechanism actually provides (three distinct claims, assessed independently):**

1. **Extensibility** (real, present-day value): Every future schema change — not just provenance — can use extensions + capabilities instead of requiring hard version bumps. This addresses audit finding F5 (schema evolution brittleness, P1) once the 0.3.0 transition is complete. Note: extensions cannot cure the coordination problem that the 0.3.0 bump itself has to cross — the bootstrap cost is unavoidable.

2. **Downgrade protection** (real, present-day value): `required_capabilities` prevents *version mismatch* problems — if a caller sends provenance data via `extensions` to a server that doesn't understand it, the server rejects the request rather than silently dropping the provenance. This is **downgrade protection** (old server can't silently ignore new security fields), not **authenticity protection** (compromised caller can't falsify fields). A prompt-injected agent can send `required_capabilities: []` and the server will accept it. The mechanism guards against the *server* being too old, not against the *caller* being compromised.

3. **Adversary mitigation** (not real today): Against the TS-2 threat model (prompt-injected agent), extensions+capabilities provides no mitigation. The agent populates both `extensions` and `required_capabilities`. If the agent is compromised, it omits or falsifies both fields. This mechanism becomes useful only when combined with a trusted producer (orchestrator, signed artifact, or split channel) — which is the post-1.0 trust root work.

**New risk introduced:** The `extensions` dict (`dict[str, Any]`) creates a parser trust boundary. Without governance, extension payloads could become an injection surface if future capability implementations parse values without schema enforcement. Extension governance (namespace ownership, typed schemas per capability, validation owner, invalid-value behavior) must be a precondition of the 0.3.0 implementation, not follow-on debt.

**Verdict:** Chosen. Provides the schema affordance for future provenance without premature commitment to a trust architecture that doesn't yet have a trust root. Must ship with governance spec to avoid creating new parser trust surface.

---

## Decision

### What we are doing

1. **Entity injection remains accepted risk at 1.0.** Server-enforced controls (denylist, git ls-files, redaction, budget caps, containment) limit the attack surface to bounded disclosure of non-secret, git-tracked files. Agent-advisory controls (scope_envelope) provide additional narrowing when populated but have no server-side enforcement. This is the same risk posture documented in the context-injection contract §Scope Anchoring and accepted in the TS-2 audit finding.

2. **No entity provenance mechanism in the 1.0 schema.** Agent-asserted provenance (Options 1-3) has the same trust weakness as the threat it addresses. Shipping it would create false confidence that entity injection is mitigated when it is not.

3. **Ship extensions + capabilities in the 0.3.0 version bump** (alongside `phase_id` from F11). This provides schema evolution infrastructure (extensibility + downgrade protection). It does not provide adversary mitigation today — that requires a post-1.0 trust root. Extension governance spec and 0.3.0 rollout procedure must be completed before implementation begins.

4. **Define 1.x compatibility rules as part of the 1.0 cut.** The extensions/capabilities mechanism only works if 1.x servers are required to accept unknown extensions and support capabilities added in minor versions.

### What we are not doing

- **Not shipping `codex_supplied` or any entity provenance field pre-1.0.** The trust-root gap makes this partial hardening at best and false security at worst.
- **Not blocking the 1.0 schema cut on entity injection resolution.** The risk is accepted with documented mitigations. Blocking 1.0 on entity injection would require solving the trust-root problem first, which is a research question, not an implementation task.
- **Not running a formal adversarial spike pre-1.0.** The static analysis demonstrates structural viability of the attack chain. An empirical spike would confirm exploitability rates but would not change the architectural decision — the mechanism exists regardless of how often gate 2 passes.

### The trust-root gap

The core reason agent-asserted provenance is rejected: **meaningful entity provenance requires a source of truth outside the agent.**

The agent is the component that handles Codex responses. If Codex can influence the agent (via prompt injection through response content), the agent cannot be trusted to accurately report which entities came from Codex. Any provenance mechanism where the agent self-reports entity origin is circular — the attestation comes from the entity being attested.

Closing this gap requires one of:

- **Orchestrator-produced immutable entity set:** The `/dialogue` skill (which runs outside the `codex-dialogue` agent) computes an immutable set of user-originated entities before the dialogue starts. Only entities matching this set are eligible for scouting. The `/dialogue` skill's existing `scope_envelope` preflight is a natural starting point — it already produces an orchestrator-level, pre-Codex artifact.
- **Signed artifact:** The orchestrator signs the initial entity set or scope envelope with a key the agent doesn't hold. The server validates the signature.
- **Split channels:** User-originated claims and Codex-originated claims arrive on separate protocol channels that the agent cannot cross-contaminate.

All three approaches require design work that is premature before the 1.0 schema is stable. The extensions+capabilities mechanism ensures that when the trust root is designed, it can be shipped as a capability extension without a breaking schema change.

---

## Consequences

### Pre-1.0 deliverables

| Deliverable | Ships with | Blocks | Purpose |
|-------------|-----------|--------|---------|
| This ADR | Immediately | — | Documents the decision and its rationale |
| Extension governance spec | Before 0.3.0 | 0.3.0 implementation | Namespace ownership rules, one typed schema per capability, validation owner in code, invalid-value behavior (hard reject, not best effort), versioning rules per capability payload, echo/normalization rules |
| Capability negotiation spec | Before 0.3.0 | 0.3.0 implementation | Define capability semantics, request/response lifecycle, and error handling before coding |
| 0.3.0 rollout procedure | Before 0.3.0 | 0.3.0 implementation | Document how the coordinated agent+server deploy works and what happens to in-flight conversations at the version boundary (addresses F5 gap) |
| `TurnRequest.extensions` field | 0.3.0 (with `phase_id`) | — | Namespaced dict for optional, non-core fields |
| `TurnRequest.required_capabilities` field | 0.3.0 (with `phase_id`) | — | Per-request downgrade protection; ensures old servers reject requests with unknown capability requirements rather than silently dropping them |
| `unsupported_capability` error code | 0.3.0 | — | Server response when a required capability is not supported |
| Capability echo in `TurnPacketSuccess` | 0.3.0 | — | Server reports which capabilities it accepted |
| 1.x compatibility rules | 1.0 cut | — | Rules for extensions/capabilities across minor versions |

### Post-1.0 sequence

1. **Trust root design.** Design the orchestrator-side mechanism for immutable user-entity sets or signed scope artifacts. The `/dialogue` skill's preflight `scope_envelope` computation is the natural starting point.
2. **Adversarial spike.** Run formal adversarial testing of entity injection exploitability with the trust root mechanism in place. Gate the provenance rollout on spike results.
3. **Trusted provenance rollout.** Ship provenance as a required capability (`required_capabilities: ["trusted_user_scope_v1"]`). This provides downgrade protection — old servers that don't understand provenance reject the request rather than silently ignoring it. Note: this guards against version mismatch, not against a compromised caller omitting the capability requirement. Authenticity protection requires the trust root from step 1.

### Accepted risks

**This is credential protection, not information protection.** The server-enforced controls protect against credential and secret exfiltration. They do not prevent disclosure of non-secret repository content to Codex. We accept bounded disclosure of non-secret tracked repo intelligence to Codex — specifically:

- **Entity injection remains possible** for git-tracked, non-denylisted files within `scope_envelope` (when populated) or any git-tracked, non-denylisted file (when `scope_envelope` is absent).
- **Attack surface:** The committed codebase minus denylist patterns (`.env`, keys, credentials). This includes source code, configuration files, documentation, test fixtures, agent specs (including `codex-dialogue.md` itself), and architecture documents. Operationally sensitive but non-secret files survive the pipeline intact.
- **Budget-bounded:** Maximum 5 file reads per conversation (1 per turn), with risk-signal files getting halved read limits (20 lines / 1000 chars vs. 40 lines / 2000 chars for normal files). At maximum exploitation: 5 non-denylisted, git-tracked files of up to 40 lines each per conversation.
- **Redaction-bounded:** Secrets in file content are caught by the redaction pipeline (per-format redactors for YAML, JSON, TOML, INI, ENV files, plus generic pattern matching). The risk signal detection (`paths.py:87-91`) only flags paths containing "secret", "token", or "credential" substrings — files with sensitive names that don't match these patterns receive full read budgets.
- **Scope enforcement gap:** When `scope_envelope` is absent (standalone agent invocations, callers that don't implement §3 preflight), scouting is unrestricted within the server-enforced boundaries. This is a wider exposure surface than the `/dialogue` skill path, independent of deployment model.

### What would change this decision

- **Discovery of an independent trust root** that doesn't require orchestrator changes — e.g., a way for the server to independently determine entity origin from the `TurnRequest` content alone.
- **Empirical evidence of exploitation** in production use — if entity injection is observed causing unintended file reads in real dialogues, the risk acceptance posture should be revisited.
- **Multi-user deployment** — the current threat model assumes a single developer running the system locally. A team or hosted deployment would change the blast radius and may require provenance before the trust root is fully designed.
- **Standalone/unscoped invocation growth** — if the `codex-dialogue` agent is increasingly invoked outside the `/dialogue` skill (standalone, from other callers, or via automation), the silent scope widening (absent `scope_envelope` = unrestricted) becomes a wider exposure surface. This should trigger either: (a) requiring explicit `unrestricted` mode declaration when `scope_envelope` is absent (no path where missing scope silently equals full access), or (b) moving scope enforcement to the server side.

---

## Evidence Appendix

### Static gate analysis

Analysis performed 2026-03-26 by tracing the attack chain through source code.

| Gate | Code location | Type | Verdict | Detail |
|------|--------------|------|---------|--------|
| 1. Codex mentions file paths | N/A | LLM behavior | **Expected** | Codex regularly references repo files in technical discussions |
| 2. Agent extracts paths into claims | `codex-dialogue.md` Step 1 | LLM behavior | **Probabilistic** | Agent writes semantic claims; file references sometimes preserved, sometimes paraphrased |
| 3. Entity regex matches claim text | `entities.py:416-495` | Deterministic | **Open** | Regex matches file names/paths with or without backticks; both `high` and `medium` confidence pass downstream |
| 4. Denylist + git ls-files | `paths.py:47-75`, `paths.py:399-406` | Deterministic | **Open** | Blocks sensitive files; passes all other tracked files |
| 5. Template matching hard gate | `templates.py:521-530` | Deterministic | **Open** | Requires `in_focus=True` + Tier 1 + high/medium confidence; all three pass for entities from `focus.claims` |
| 6. Scout execution | `execute.py` | Deterministic | **Open** | HMAC valid, file readable, runtime re-check passes |

**Key finding:** The `in_focus` gate (`templates.py:530`) was designed to filter context-only entities (from `prior_claims`, extracted with `in_focus=False`). It does not filter Codex-injected entities because `pipeline.py:188-196` extracts `request.focus.claims` with `in_focus=True` — all current-turn claims, regardless of origin, receive `in_focus=True`.

### Adversarial spike (partial)

A single `/dialogue` session was run as a preliminary test (thread `019d2b30-e1f0-7721-abfa-833060fe2bb4`, 4 turns, exploratory posture).

- **Result:** 0 scouts executed across 4 turns
- **Reason:** Template candidates were symbol-type entities, not file-path entities. The agent's claim extraction produced semantic claims without preserving file-path references from Codex responses.
- **Interpretation:** Gate 2 (agent claim extraction) acted as probabilistic friction in this session. This does not constitute structural protection — a different dialogue topic or a more code-reference-heavy Codex response could produce claims that preserve file paths.
- **Assessment:** Ambiguous per exit criteria. Static analysis of gates 3-6 provides stronger evidence than any single dialogue run.
- **Gate-2 friction status:** Gate-2 friction (agent claim extraction filtering out file paths) is an observation, not a mitigation. A single 4-turn session with 0 scouts is insufficient evidence to characterize the friction rate. To promote gate-2 friction to a cited mitigation, a testing standard would be required: at least 4 attack families (file structure, deployment/config, architecture/docs, agent-spec/instruction markdown), at least 60 conversations per family, with a 95% CI upper bound below 5% end-to-end successful read rate per family. Until such testing is performed, gate-2 friction remains an appendix observation.

### Codex dialogue convergence (remediation strategy)

Thread `019d2b45-be62-77c1-b346-65e9bb5def33`, 7 turns, exploratory posture, natural convergence.

**Key convergence points:**

1. **T1:** Codex proposed generic `origin` field on claims. Identified that `codex_supplied` name is too narrow.
2. **T3 (concession):** Trust model challenge — agent-asserted provenance has the same trust weakness as scope_envelope. Codex conceded: "if the agent populates `focus_claim_origins`, a compromised agent can lie about it."
3. **T5 (challenge):** `extra=ignore` proposed as compatibility mechanism. Codex challenged: old servers would silently drop provenance fields, creating false security. Extensions+capabilities split emerged as the solution.
4. **T6-T7 (convergence):** Pre-1.0 and post-1.0 sequences agreed. ADR-first ordering confirmed. Extensions+capabilities recognized as simultaneously addressing F5 and entity injection forward path.

**Emerged insights:**
- Extensions + required_capabilities simultaneously addresses F5 (schema evolution, P1) and creates the forward path for trusted provenance — two problems, one mechanism.
- The fail-open/breaking dilemma for optional security fields is solved by `required_capabilities`: required extensions fail closed, optional extensions are safely ignorable.
- The `/dialogue` skill's preflight `scope_envelope` computation is the natural starting point for the post-1.0 orchestrator-side trust root — it's already an orchestrator-produced, pre-Codex artifact.

### Adversarial ADR review

Thread `019d2b6d-b7b8-7830-9de2-26d20c5c9853`, 7 turns, adversarial posture, natural convergence. 9 resolved findings, 3 emerged frameworks.

**Key findings incorporated into this revision:**

1. Mitigations table restructured into enforcement layers (server-enforced / agent-advisory / trust-root-seed)
2. `required_capabilities` reframed as downgrade protection, not authenticity protection
3. Option 4's three claims (extensibility, downgrade resistance, adversary mitigation) separated with honest assessment
4. Accepted risk explicitly stated as credential protection, not information protection
5. Extension governance added as blocking prerequisite before 0.3.0
6. Standalone invocation trigger added to "what would change this decision"
7. 0.3.0 rollout procedure added as blocking prerequisite
8. Gate-2 friction demoted from mitigation to appendix observation with testing standard

**Emerged frameworks:**
- **Downgrade protection vs. authenticity protection:** When evaluating any agent-populated security field, distinguish whether it guards against version mismatch (downgrade — the server is too old) or against prompt injection (authenticity — the caller is compromised). Only authenticity protection matters for the TS-2 threat model.
- **Three-bucket mitigation classification:** Filesystem boundary (denylist, containment, git-tracking), credential-centric content (redaction, risk signals), volume (budget caps). More accurate than a flat list for understanding defense depth.
- **Explicit unrestricted mode:** Instead of silent scope widening when `scope_envelope` is absent, require callers to declare `unrestricted` explicitly. Eliminates the path where missing scope silently equals full access.

### References

| What | Where |
|------|-------|
| TS-2 finding | `docs/audits/cross-model-audit/trust-safety.md:33-42` |
| Team audit report | `docs/audits/cross-model-audit/2026-03-26-cross-model-plugin-team.md` |
| Context-injection contract §Scope Anchoring | `packages/plugins/cross-model/references/context-injection-contract.md:911-919` |
| Original design doc (entity origin intent) | `docs/superpowers/plans/2026-02-11-conversation-aware-context-injection.md:302-308` |
| Entity extraction | `packages/plugins/cross-model/context-injection/context_injection/entities.py` |
| Path safety | `packages/plugins/cross-model/context-injection/context_injection/paths.py` |
| Template matching (focus-affinity gate) | `packages/plugins/cross-model/context-injection/context_injection/templates.py:529` |
| Pipeline (in_focus assignment) | `packages/plugins/cross-model/context-injection/context_injection/pipeline.py:186-217` |
| `codex-dialogue` agent (scope_envelope) | `packages/plugins/cross-model/agents/codex-dialogue.md:374-388` |
| Schema version + extra=forbid | `packages/plugins/cross-model/context-injection/context_injection/types.py:26-29` |

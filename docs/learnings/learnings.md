# Learnings

Project insights captured from consultations. Curate manually: delete stale entries, merge duplicates.

### 2026-02-17 [codex, workflow]

When designing validation criteria for a prototype phase, separate habit-formation validation ("will the developer actually use this?") from causal efficacy validation ("does this measurably improve outcomes?"). Phase 0 can only credibly measure the former — adoption frequency, curation actions, artifact-backed reuse events. Causal measurement requires infrastructure (A/B tests, blinding, withdrawal probes) that contradicts Phase 0's "no infrastructure" constraint. The spec's original 10/3 gate ("capture 10 insights, report 3 useful") conflates both questions into a single self-rating gate. Pre-register rubrics and thresholds before starting to prevent goalpost-shifting.

### 2026-02-17 [skill-design, architecture]

When instruction documents layer (skill references agent, agent references contract), each layer must be fully operational standalone. Conditional logic like "if the agent spec is loaded, use its patterns; otherwise fall back" creates ambiguity that an LLM will resolve inconsistently — "available" is operationally undefined when the referenced spec isn't loaded. The fix: inline the minimal self-contained version at each layer, with a note that other sources are additive, not alternative. This emerged from a 3-dialogue parallel review of the `/codex` skill where the evaluative dialogue independently discovered (T8) that a "prefer codex-dialogue profile when available" clause was a loophole, and the exploratory dialogue independently chose "full replacement stubs over summary stubs" (T4) for the same reason — summary stubs that say "see the contract" create hard dependencies that break when the contract is unavailable.

### 2026-02-18 [security, hooks]

PreToolUse hooks are mechanically fail-open — unhandled exceptions don't produce exit code 2, so the tool call proceeds. This is backward from security intuition. When enforcement is critical (credential detection, access control), explicitly catch all errors and return a block decision. The choice between hooks (fail-open default) and wrapper MCP (fail-closed default) is a threat model question: "reduce accidental leaks" → hooks are proportionate; "zero tolerance" → wrapper required. Always clarify failure polarity before committing to a mechanism.

### 2026-02-18 [codex, workflow]

When Codex proposes "A or B," the actual answer is often "neither — here's C." Detection scope was framed as "full §7 parity vs. minimal" but converged on tiered detection (strict/contextual/shadow). Install scope was framed as "project-scope risk vs. user-scope blast radius" but the answer was user-scope with 4 guardrails. Heuristic: when consulting an independent model, interrogate binaries. Ask "what would a third option look like?" The real architecture often emerges from breaking the stated frame.

### 2026-02-18 [plugins, architecture]

Plugin-provided MCP tools use `mcp__plugin_<plugin>_<server>__<tool>` naming, not `mcp__<server>__<tool>`. This affects three surfaces that must all use the same convention: hook matchers, skill `allowed-tools` frontmatter, and agent `tools` frontmatter. The agent `tools` field is a hard allowlist (wrong names = tool unavailable to subagent), while skill `allowed-tools` is auto-approval only (wrong names = permission prompts appear). Discovered empirically via diagnostic hook — not documented in Claude Code plugin docs at time of discovery.

### 2026-02-18 [plugins, debugging]

When bundling a Python package inside a Claude Code plugin, never include the `.venv` directory. Copied venvs have hardcoded Python symlinks that break in new locations (`dyld` fails to load `libpython`). This is a non-issue for git-based marketplace installs (`.gitignore` covers `.venv`), but matters for direct path copies or symlink-based installs. The build script should explicitly exclude `.venv/`, `__pycache__/`, and test directories. `uv run --directory` creates a fresh venv on first invocation (~17s cold start for dependency resolution, ~0.4s warm).

### 2026-02-18 [security, architecture]

In security-critical egress paths, over-redaction is always correct. Use fail-closed as the default posture — when in doubt, block or redact. "Footgun tests" (`test_footgun_*`) verify which pipeline layer catches a specific security violation. These tests document the contract: "layer X catches pattern Y." If a refactor changes which layer catches it, the test fails — indicating a contract change, not a bug. Never weaken footgun tests; they're your boundary documentation.

### 2026-02-18 [architecture, protocol]

Two-call protocols (analyze then execute) decouple decision-making from side effects. Call 1 validates input and generates HMAC-signed tokens committing to the fully resolved execution spec. Call 2 validates tokens and executes — the caller never sees resolved paths or adjusted caps. Benefits: server restart between calls is recoverable (via checkpoint), the agent can't tamper with execution parameters, and each call has clear error semantics. Trade-off: two round-trips per turn. Worth it when the execution step has security implications (file reads, credential-adjacent operations).

### 2026-02-18 [review, methodology]

Audit findings cluster around three systematic failure modes: incompleteness (missing events, missing examples), inconsistency (terminology drift between sections), and implicit concepts (undefined terms, assumed reader knowledge). Across four audits (hooks, plugins, skills, context injection), checking completeness + consistency + implicit definitions catches ~70% of document quality issues before more specialized passes. Start every document review by checking these three categories.

### 2026-02-18 [architecture, packaging]

Before making file organization or packaging decisions, map the full dependency chain across systems. The codex-dialogue agent straddles two MCP servers (Codex plugin + context injection repo-level), making it impossible to "just remove project copies and make the plugin canonical" — the dependency chain (Learning → Context Injection → Codex) constrains what can be moved. The fix was bundling all three into a single plugin, turning the inter-system dependency into an internal one. File organization decisions that ignore cross-system dependencies create packaging lock-in.

### 2026-02-18 [plugins, hooks]

The PostToolUse hook payload uses `tool_response` (not `tool_result`) for the tool's output. The PreToolUse payload uses `tool_input` for the tool's input. The plugin `.mcp.json` `env` field merges with the parent process environment — it doesn't replace it. Setting `PATH` to a hardcoded value replaces only `PATH`; omitting `PATH` lets the child inherit the parent's. `${VAR:-default}` syntax does NOT expand in plugin `.mcp.json`; simple `${VAR}` is untested. Safest approach: don't set variables you can inherit.

### 2026-02-18 [security, hooks]

When multiple PreToolUse hooks can write `updatedInput` (payload transformation), the merge behavior is undefined. In a security-critical path, undefined behavior is worse than a simpler guarantee. Decision for credential detection: block-or-allow only for v0.1. No in-flight redaction via `updatedInput`. This preserves a clean security contract: the hook either lets the call through unchanged or blocks it entirely.

### 2026-02-18 [workflow, adoption]

When a rigorous system has low adoption, look for ceremony that can be deferred rather than dropping rigor entirely. Design a two-stage workflow: the minimum viable output is self-contained and low-ceremony (inline), promotion to a formal artifact only happens when stakes cross a threshold. The promotion mechanism itself becomes the tool that scales rigor — not the initial document size. Phase 0 of the cross-model learning system validates this pattern: unstructured capture first, structured cards only if the premise validates.

### 2026-02-18 [codex, review]

Before shipping a system with safety guarantees, map every normative statement to its enforcement layer (hook, code, test, documentation-only). If a rule has no enforcement, either add enforcement or relabel it as advisory. The §7 Safety Pipeline was purely normative markdown consumed by an LLM while the context injection helper had real code enforcement (HMAC tokens, denylist, 969 tests). This asymmetry was invisible until the audit explicitly compared enforcement mechanisms across systems.

### 2026-02-18 [codex, architecture]

In multi-turn cross-model dialogues, the `delta` classification (advancing, shifting, static) — not turn count — should drive continue/conclude decisions. A conversation that plateaus in substance can be concluded at turn 3, while one generating new evidence can run to turn 8 within the same posture. Convergence is substance-based, not time-based. Measure progress in signal freshness, not elapsed turns.

### 2026-02-18 [codex, methodology]

When mid-conversation evidence arrives, use it to probe the specific claim that triggered the evidence gathering, not the most intellectually interesting tangent it suggests. Side findings go into notes and surface later as unresolved items. This "target-lock" guardrail prevents a single piece of evidence from reframing the entire dialogue — a subtle form of confirmation bias hiding as thoroughness.

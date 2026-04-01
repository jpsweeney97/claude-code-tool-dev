# Learnings

Project insights captured from consultations. Curate manually: delete stale entries, merge duplicates.

### 2026-02-17 [skill-design, architecture]

When instruction documents layer (skill references agent, agent references contract), each layer must be fully operational standalone. Conditional logic like "if the agent spec is loaded, use its patterns; otherwise fall back" creates ambiguity that an LLM will resolve inconsistently — "available" is operationally undefined when the referenced spec isn't loaded. The fix: inline the minimal self-contained version at each layer, with a note that other sources are additive, not alternative. This emerged from a 3-dialogue parallel review of the `/codex` skill where the evaluative dialogue independently discovered (T8) that a "prefer codex-dialogue profile when available" clause was a loophole, and the exploratory dialogue independently chose "full replacement stubs over summary stubs" (T4) for the same reason — summary stubs that say "see the contract" create hard dependencies that break when the contract is unavailable.
<!-- promote-meta {"promoted_at": "2026-03-11", "target": "CLAUDE.md#Writing Extensions"} -->

### 2026-02-18 [security, hooks]

PreToolUse hooks are mechanically fail-open — unhandled exceptions don't produce exit code 2, so the tool call proceeds. This is backward from security intuition. When enforcement is critical (credential detection, access control), explicitly catch all errors and return a block decision. The choice between hooks (fail-open default) and wrapper MCP (fail-closed default) is a threat model question: "reduce accidental leaks" → hooks are proportionate; "zero tolerance" → wrapper required. Always clarify failure polarity before committing to a mechanism.
<!-- promote-meta {"promoted_at": "2026-03-11", "target": "CLAUDE.md#Gotchas"} -->

### 2026-02-18 [codex, workflow]

When Codex proposes "A or B," the actual answer is often "neither — here's C." Detection scope was framed as "full §7 parity vs. minimal" but converged on tiered detection (strict/contextual/shadow). Install scope was framed as "project-scope risk vs. user-scope blast radius" but the answer was user-scope with 4 guardrails. Heuristic: when consulting an independent model, interrogate binaries. Ask "what would a third option look like?" The real architecture often emerges from breaking the stated frame.

### 2026-02-18 [plugins, architecture]

Plugin-provided MCP tools use `mcp__plugin_<plugin>_<server>__<tool>` naming, not `mcp__<server>__<tool>`. This affects three surfaces that must all use the same convention: hook matchers, skill `allowed-tools` frontmatter, and agent `tools` frontmatter. The agent `tools` field is a hard allowlist (wrong names = tool unavailable to subagent), while skill `allowed-tools` is auto-approval only (wrong names = permission prompts appear). Discovered empirically via diagnostic hook — not documented in Claude Code plugin docs at time of discovery.
<!-- promote-meta {"promoted_at": "2026-03-11", "target": "CLAUDE.md#Gotchas"} -->

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
<!-- promote-meta {"promoted_at": "2026-03-11", "target": "CLAUDE.md#Gotchas"} -->

### 2026-02-18 [security, hooks]

When multiple PreToolUse hooks can write `updatedInput` (payload transformation), the merge behavior is undefined. In a security-critical path, undefined behavior is worse than a simpler guarantee. Decision for credential detection: block-or-allow only for v0.1. No in-flight redaction via `updatedInput`. This preserves a clean security contract: the hook either lets the call through unchanged or blocks it entirely.

### 2026-02-18 [codex, review]

Before shipping a system with safety guarantees, map every normative statement to its enforcement layer (hook, code, test, documentation-only). If a rule has no enforcement, either add enforcement or relabel it as advisory. The §7 Safety Pipeline was purely normative markdown consumed by an LLM while the context injection helper had real code enforcement (HMAC tokens, denylist, 969 tests). This asymmetry was invisible until the audit explicitly compared enforcement mechanisms across systems.

### 2026-02-18 [codex, architecture]

In multi-turn cross-model dialogues, the `delta` classification (advancing, shifting, static) — not turn count — should drive continue/conclude decisions. A conversation that plateaus in substance can be concluded at turn 3, while one generating new evidence can run to turn 8 within the same posture. Convergence is substance-based, not time-based. Measure progress in signal freshness, not elapsed turns.

### 2026-02-18 [codex, methodology]

When mid-conversation evidence arrives, use it to probe the specific claim that triggered the evidence gathering, not the most intellectually interesting tangent it suggests. Side findings go into notes and surface later as unresolved items. This "target-lock" guardrail prevents a single piece of evidence from reframing the entire dialogue — a subtle form of confirmation bias hiding as thoroughness.

### 2026-02-19 [architecture, codex]

When deploying multiple parallel agents for the same task (context gathering, code review, analysis), structural independence matters more than tool diversity. Two agents with the same orientation ("find relevant things") produce correlated blind spots — using different tools doesn't help if both agents ask the same question. The falsifier pattern assigns fundamentally different orientations: Agent A asks "what code is relevant to this question?" while Agent B asks "what in this codebase contradicts the assumptions in this question?" This produces complementary rather than overlapping findings. Constraint mechanisms prevent the falsifier from degenerating into noise: citation requirements (every counter must cite specific code), a contradiction type whitelist, a counter cap (max 3), and a CONFIRM option for valid assumptions. The pattern generalized from the PR #14 review where 4 agents with different review dimensions (code quality, silent failures, test coverage, comments) produced convergent findings that a single agent missed. Emerged from a 6-turn evaluative Codex dialogue that reframed an initial "contrarian agent" proposal — pure contrarianism is noise, but constrained falsification is signal.

### 2026-02-19 [architecture, review]

When reviewing pipeline specs designed top-down from architecture decisions, focus review effort on component boundaries (skill→agent, gatherer→assembly, assembly→agent) rather than within components. In the dialogue skill orchestrator spec review, all 5 high-priority findings (F1-F5) were at interface boundaries: the delegation envelope missing fields the agent expected, a control specified at a layer that doesn't have the knob, a grammar definition inconsistent with its own tag requirements, no fallback for zero output between stages, and a tool mismatch between an agent's procedure and its tool access. The components themselves were internally sound. This pattern is predictable for top-down design: architecture decisions define what each component does, but the contracts between components are implicit until explicitly specified. Budget review time proportionally — 70% on interfaces, 30% on internals.

### 2026-02-19 [review, skill-design]

In instruction document systems where multiple markdown files form a pipeline (grammar reference, skill steps, agent instructions), constraints declared in one file must be enforced in all processing files — there's no compiler to catch mismatches. PR #15 review found that tag-grammar.md declared CONFIRM AID as "Required" but the SKILL.md discard rules and tag-grammar.md parse rules only enforced AID for COUNTER, silently accepting malformed CONFIRM lines. Similarly, step ordering in pipeline documents carries semantic weight: a retry step placed after the grouping step implied "retry after assembly" when it logically belonged after parsing. Two parallel review agents (code-reviewer + comment-analyzer) caught these cross-file consistency issues that three prior review cycles (self-review, Codex review, skills guide review) all missed — each review type catches orthogonal error classes.

### 2026-02-19 [architecture, analytics]

When adding analytics or telemetry to a multi-layer pipeline, emit events at the layer with complete pipeline visibility, not at the layer closest to the persistence mechanism. In the cross-model plugin, the initial assumption was that `codex_guard.py` should write `dialogue_outcome` events because it already writes to `~/.claude/.codex-events.jsonl`. Codex corrected this (T5): the hook only sees individual Codex tool calls, not gatherer metrics, `seed_confidence` decisions, assumption counts, or synthesis checkpoint data. The correct writer is the `/dialogue` skill (full orchestration state) or `codex-dialogue` agent (synthesis counts), with the agent passing structured data back through the Task tool return value. General principle: the persistence layer is a detail; the visibility layer determines correctness.

### 2026-02-20 [pattern, review]

When a script has a build-then-validate pipeline under a single broad `except (ValueError, KeyError, TypeError)`, split into two try blocks: catch `KeyError`/`TypeError` on the build phase (with `traceback.format_exc()` to stderr, since these indicate bugs or structural input problems) and catch `ValueError` on the validate phase (with clean user-facing messages, since these are expected input failures). The single-block pattern in `emit_analytics.py` masked implementation bugs as validation errors — a `TypeError` from an accidental `None + 1` in a builder function would report as "validation failed" with no traceback, making debugging nearly impossible. The split was identified during a 4-agent PR review of PR #17.

### 2026-02-20 [skill-design, pattern]

When writing instructions that interface with MCP tool schemas, optional parameters with strong training priors (e.g., `model`, `url`, `api_key`) need explicit prohibitions ("Do NOT set X"), not passive omission rules ("omit X for default"). Claude tends to populate optional tool parameters rather than leave them unset, especially when the parameter name maps to training knowledge — the codex-dialogue agent consistently set `model` to invalid OpenAI model names ("o4 mini", "o3") despite the consultation contract saying "omit for Codex default." The fix required explicit "Do NOT set" + "Never guess from training knowledge" language in three places: the contract (authoritative source), the agent (where the tool call originates), and the skill (which delegates). All three are needed because Claude reads different documents depending on the invocation path.
<!-- promote-meta {"promoted_at": "2026-03-11", "target": "CLAUDE.md#Writing Extensions"} -->

### 2026-02-22 [testing, pattern]

When testing a specific validation check in a multi-stage validator, upstream checks may reject the test input before reaching the target check. In `emit_analytics.py`, the `shape_confidence` enum type-guard test failed because the tri-state planning invariant (which runs first) rejected non-None `shape_confidence` when `question_shaped=None`. The fix: set `question_shaped=True` with valid companion fields (`assumptions_generated_count`, `ambiguity_count`) to satisfy the invariant, then inject the bad `shape_confidence` value to exercise the downstream enum check. General principle: trace the validation execution path to your target check and satisfy all upstream guards with valid values, isolating only the field under test.

### 2026-02-25 [architecture, skill-design]

When multiple Claude Code plugin skills need to agree on a shared protocol (frontmatter schema, state file chain, storage paths), fully self-contained skills create N independent copies of the same rules that can drift silently. A thin shared contract reference (~50-80 lines) loaded by all participating skills eliminates this class of bugs at a modest context cost (~60 lines per invocation). This pattern emerged from a Codex adversarial review of the handoff checkpoint design: the original "fully self-contained" approach (Approach A) would have required three skills to independently implement identical chain protocol logic — state file read, handoff write, state file cleanup — with no mechanism to detect if one skill's implementation diverged. The contract pattern is analogous to interface definitions in code: small, loaded by all consumers, defining the agreement boundary. Applied in the handoff plugin as `references/handoff-contract.md`, loaded by save, quicksave, and load.

### 2026-03-01 [workflow, review]

When a review surfaces fixes to a plan or spec, apply them immediately — before the review context leaves working memory. Deferring fixes to execution time ("we'll fix it during execution") leads to forgotten fixes and compounding issues: the executor operates under time pressure, may not have the reviewer's context, and each unfixed issue increases the chance of cascading failures. In the environment cleanup plan review, a 4-agent team found 1 bug (broken stow symlinks) and 8 documentation/robustness issues. Applying all 9 fixes immediately after synthesis — while the review rationale was fresh — took minutes. Deferring them would have required re-deriving each fix's context during execution, with high probability of at least some being silently dropped. The pattern generalizes: any review-then-execute workflow should treat "apply fixes" as part of the review phase, not the execution phase.

### 2026-03-02 [architecture, pattern, plugin-design]

The engine-centric adapter pattern (Architecture E) solves a class of trust and drift problems in Claude Code plugins by routing all mutations through Python scripts while keeping skills as thin transport layers. Three properties make it effective: (1) **Split entrypoints** (`_user.py` / `_agent.py`) hardcode `request_origin` before delegating to shared core, preventing the model from claiming a different caller type — defense-in-depth, not a security boundary, but catches model misbehavior. (2) **A single enforcement point** (preflight) that all mutation paths pass through eliminates the "bypass a validation step" bug class — the 7-round review of the ticket plugin design found and fixed multiple variants of this (pipeline bypass, autonomy gap, missing preflight on create). (3) **Payload-by-file** eliminates shell metacharacter injection by writing engine input to a temp file instead of inline JSON in Bash commands; a PreToolUse hook then injects trusted fields (`session_id`, `request_origin`) that the model cannot fabricate. The pattern generalizes to any plugin where the model should be able to invoke operations but not control policy: put policy in code, put UX in skills, connect them with a typed pipeline.

### 2026-03-07 [testing, codex]

When a codebase has gates or checks (precondition guards, transition validators, confidence thresholds), test suites tend to exercise the paths where the gate fires correctly and systematically miss the paths that bypass the gate entirely. In the ticket plugin adversarial review, the acceptance criteria check only covered `(in_progress, done)` keyed by `(current, target)` pair — the test at line 1577 verified this path worked, but no test exercised `open → done` via the `close` action, which bypassed the AC gate completely. The fix pattern: for every gate/check, enumerate all paths that *should* be blocked and verify each one independently. Test the bypass paths, not just the working paths. This generalizes — the confidence gate (hardcoded 0.95 vs threshold 0.65) was also untested for the "gate fires" case because no test supplied a low confidence value. Dead code and untested gates are the same failure mode: a safety mechanism that has never been exercised in the negative case.

### 2026-03-19 [workflow, worktree]

**Context:** After merging a feature branch to main from within a git worktree, attempted to clean up the worktree using raw `git worktree remove` — every subsequent bash command failed.

**Insight:** When a worktree directory is removed while the session's CWD is inside it, all subsequent bash commands fail — the shell can't initialize in a non-existent directory. The `ExitWorktree` tool handles this cleanly by resetting the session CWD before removing the directory. Raw `git worktree remove` from within the worktree (or from the main repo while the session CWD points to the worktree) leaves the session stranded.

**Implication:** Always use `ExitWorktree` to clean up worktrees created by `EnterWorktree`, never raw `git worktree remove`. When finishing work in a worktree: merge from the main repo, then `ExitWorktree action: "remove"` to reset CWD and clean up atomically.

### 2026-03-29 [workflow, pattern]

**Context:** After squash-merging PR #89, local `main` was 9 commits ahead / 1 behind `origin/main`. Needed to reset local main to match the remote without risking worktree state.

**Insight:** Use `git branch -f` from another branch to move a ref safely: `git switch <other>`, `git branch -f main origin/main`, `git switch main`. This avoids `git reset --hard` which can silently discard uncommitted work if the worktree is dirty. The ref move is a no-op on the working tree — the checkout only happens on the final `switch`.

**Implication:** Prefer `branch -f` over `reset --hard` when reconciling a diverged local branch with its remote after squash-merge. Especially relevant when the local branch might have uncommitted or staged changes.

### 2026-03-31 [architecture, review]

**Context:** Reviewing an implementation plan for JSONL replay hardening across three persistence stores, where the design spec described flat field/type checks but the recovery coordinator depended on per-operation+phase field invariants.

**Insight:** Design specs that describe data validation often stop at the schema layer (field presence, type correctness) and miss the protocol layer — invariants that a *consumer* depends on but that the *data model* doesn't express. Example: `OperationJournalEntry` has `codex_thread_id: str | None` (structurally valid), but `turn_dispatch` at any phase requires it to be non-None or recovery crashes with `RuntimeError`. These cross-layer invariants are invisible in the dataclass definition and only discoverable by reading the consumer code.

**Implication:** When a design spec defines validation for a persistence format, enumerate consumer-side field requirements as a separate table — not just per-field types, but per-operation+phase (or per-variant) required/forbidden fields. Review checkpoint: "does the consumer access any optional field unconditionally?"

# Cross-Model Plugin Immediate Enhancement Opportunities

## Context
- Protocol: `decision-making.framework@1.0.0`
- Stakes level: rigorous
- Decision trigger: determine the highest-leverage immediate enhancement opportunities for `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/`
- Time pressure: no constraint
- Local evidence reviewed:
  - Plugin README, changelog, skills, agents, and scripts
  - Plugin-local tests in `packages/plugins/cross-model/tests`
  - Repo-root tests targeting the plugin scripts
  - Targeted test run results:
    - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest` in `packages/plugins/cross-model` -> 3 passed
    - `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_codex_guard.py tests/test_emit_analytics.py tests/test_read_events.py tests/test_compute_stats.py tests/test_stats_common.py tests/test_nudge_codex.py tests/test_e_planning_spec_sync.py tests/test_consultation_contract_sync.py` -> 407 passed, 1 failed

## Entry Gate
- Stakes level: rigorous
- Rationale: This choice affects the plugin's next implementation cycle, the reliability of `/dialogue`, and the accuracy of the package's release confidence. The work is reversible, but prioritizing the wrong area would spend time on lower-value hardening while correctness drift remains in the control plane.
- Time budget: no constraint
- Iteration cap: 3
- Evidence bar: The recommendation must reduce current correctness/drift risk in the shipped plugin, not just improve theoretical architecture.
- Allowed skips:
  - No live Codex/Claude integration runs
  - No broader CI or release-pipeline audit outside the cross-model area
  - No extra research outside the local repository
- Overrides: None
- Escalation trigger: If security-first hardening appeared to address a more immediate observed failure than orchestration drift, escalate and re-rank.

## Frame
### Decision Statement
What near-term enhancement ordering will create the most leverage for the cross-model plugin?

### Constraints
- C1: Improvements should fit the current plugin architecture rather than require a transport rewrite.
- C2: Immediate work should target current drift or failure modes visible in local evidence.
- C3: The next increment should improve both runtime trustworthiness and maintainability.
- C4: Work that only matters under a changed threat model should not displace current correctness work.
- C5: The recommendation should respect that the plugin blends executable Python with prompt-driven control logic.

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| Runtime correctness leverage | 5 | Reduces the probability that `/dialogue` behaves differently from the documented contract |
| Breadth of impact | 5 | Improves multiple flows or reduces multiple categories of drift at once |
| Time-to-value | 4 | Can be landed incrementally without waiting for a redesign |
| Verification leverage | 4 | Makes the behavior easier to test and keep consistent |
| Safety leverage | 3 | Improves real secret-handling or scope-enforcement confidence |

### Stakeholders
| Stakeholder | What they value | Priority |
|-------------|-----------------|----------|
| Plugin user | Reliable `/codex` and `/dialogue` behavior, honest docs, useful safeguards | High |
| Plugin maintainer | Low drift between docs, prompts, scripts, and tests | High |
| Future security maintainer | Consistent egress rules and a clear escalation path | Medium |

### Assumptions
- A1: The largest immediate risk is control-plane drift between prompt contracts and executable code. Supported by the large deterministic pipeline described only in [`packages/plugins/cross-model/skills/dialogue/SKILL.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/skills/dialogue/SKILL.md#L159).
- A2: Security transport escalation is not the current top priority because the README explicitly frames wrapper-level enforcement as a threshold-triggered escalation, not the baseline path. Supported by [`packages/plugins/cross-model/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L180).
- A3: Verification topology is currently confusing enough to reduce release confidence because package-local docs say the plugin has only 3 tests, while the repo root contains a much larger test suite targeting the same scripts. Supported by [`packages/plugins/cross-model/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L230) and the repo-root test files.
- A4: Security-pattern duplication is a real drift risk because `codex_guard.py` explicitly says its patterns were tightened from the vendored redaction module rather than shared from a single source. Supported by [`packages/plugins/cross-model/scripts/codex_guard.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_guard.py#L37).

### Scope
- In bounds:
  - Prioritizing the next enhancement workstreams
  - Identifying the best immediate sequence
  - Calling out concrete evidence of drift or leverage
- Out of bounds:
  - Implementing the changes
  - Rewriting the plugin transport model
  - Revisiting the overall product strategy for cross-model consultation

### Reversibility
The roadmap is easy to change, but the next enhancement cycle will likely determine whether the plugin gets more executable and testable or accumulates more contract-in-markdown debt.

### Dependencies
- Depends on the current skill and agent prompt contracts
- Depends on the existing Python utilities in `packages/plugins/cross-model/scripts`
- Depends on the repo-root test suite, which currently holds most meaningful verification coverage

### Downstream Impact
- Enables:
  - Stronger `/dialogue` conformance
  - Cleaner release verification
  - Safer future security changes
- Precludes:
  - Spending the next cycle on lower-signal analytics or transport work
  - Continuing to rely on prompt text as the only implementation for deterministic pipeline rules

## Options Considered
### Option 1: Reliability-First Control-Plane Hardening
- Description: Extract the Step 0-4 `/dialogue` pipeline rules into executable code, back them with replay fixtures, fix the current spec drift, and make the repo-root test suite the official verification path for the plugin.
- Trade-offs: Highest leverage, but broader than a single bug fix and requires touching both implementation and verification surfaces.

### Option 2: Verification and Documentation Cleanup Only
- Description: Leave the prompt-driven pipeline intact, but fix the failing sync test, align README/changelog/test commands, and tighten release checks around the existing scripts.
- Trade-offs: Cheap and useful, but it leaves the biggest correctness surface still encoded only in markdown prompts.

### Option 3: Security-First Hardening
- Description: Unify credential rules immediately and consider wrapper-level enforcement or stronger transport controls before touching orchestration logic.
- Trade-offs: Valuable if the threat model has changed, but current repo evidence does not show that as the primary source of immediate leverage.

### Option 4: Null / Defer
- Description: Make no immediate enhancement prioritization changes and continue with the current package shape.
- Trade-offs: Lowest effort, but preserves known drift and ambiguous release confidence.

## Evaluation
### Criteria Scores
| Option | Runtime correctness leverage | Breadth of impact | Time-to-value | Verification leverage | Safety leverage | Total |
|--------|------------------------------|-------------------|---------------|-----------------------|-----------------|-------|
| Option 1 | 5 | 5 | 4 | 5 | 4 | 90 |
| Option 2 | 3 | 3 | 5 | 4 | 2 | 62 |
| Option 3 | 2 | 3 | 3 | 3 | 5 | 54 |
| Option 4 | 1 | 1 | 5 | 1 | 1 | 33 |

### Evidence That Drives the Ranking
- The plugin claims a deterministic dialogue assembly pipeline, but that implementation currently lives in skill markdown rather than code: parsing, retry, discard, sanitize, dedup, provenance validation, and seed-confidence composition are described in [`packages/plugins/cross-model/skills/dialogue/SKILL.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/skills/dialogue/SKILL.md#L189) through [`packages/plugins/cross-model/skills/dialogue/SKILL.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/skills/dialogue/SKILL.md#L304). The README's script inventory lists only guard, analytics, stats, event reading, and nudge utilities, not a dialogue assembler or planner implementation, in [`packages/plugins/cross-model/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L210).
- Verification is split and slightly misleading today. The package README says the plugin has only 3 tests and directs users to run the package-local suite in [`packages/plugins/cross-model/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L230), but the repo root holds the substantive tests for `codex_guard.py`, `emit_analytics.py`, `read_events.py`, `compute_stats.py`, `stats_common.py`, `nudge_codex.py`, and sync contracts. That means the documented verification path under-represents real coverage.
- There is already an active spec drift failure: the `planning` profile is `comparative` in [`packages/plugins/cross-model/references/consultation-profiles.yaml`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/references/consultation-profiles.yaml#L85), while the sync test still asserts `evaluative` in [`tests/test_e_planning_spec_sync.py`](/Users/jp/Projects/active/claude-code-tool-dev/tests/test_e_planning_spec_sync.py#L47). This caused the only failure in the targeted root suite.
- Security rules are duplicated rather than shared. `codex_guard.py` says its patterns were "tightened from" the vendored redaction module in [`packages/plugins/cross-model/scripts/codex_guard.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_guard.py#L40), while the canonical redaction patterns live separately in [`packages/plugins/cross-model/context-injection/context_injection/redact.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/redact.py#L69). That is worth fixing, but it is not as broad as making the `/dialogue` control plane executable and testable.

### Risks per Option
| Option | Key Risks | Mitigation |
|--------|-----------|------------|
| Option 1 | Scope creeps into a broader orchestration rewrite | Keep the first increment narrow: Step 0-4 only, with stable JSON I/O and replay tests |
| Option 2 | Drift remains hidden in the prompt-driven pipeline | Treat as a fallback if bandwidth only allows a cleanup pass |
| Option 3 | Over-invests in a threat-model escalation that the README explicitly treats as conditional | Limit immediate security work to rule deduplication unless new evidence appears |
| Option 4 | Known inconsistencies continue and future failures remain hard to root-cause | Reject |

### Information Gaps
- No local integration test was run against a live Codex/Claude session
- No CI workflow audit was done to confirm which suite blocks merges or releases
- No evidence was collected on how often `/dialogue` actually violates the documented assembly contract in production

### Bias Check
- Familiarity: There is a temptation to prioritize the Python scripts because they are easier to test than prompt contracts. I countered that by checking whether the prompt contracts actually cover high-value behavior; they do.
- Availability: The current failing sync test is vivid, but the ranking does not rest only on that failure. The stronger signal is the larger prompt-vs-code gap.
- Confirmation: I actively checked the security-hardening path; the README's own threat model makes it a second-tier priority for now.

## Pressure Test
### Strongest Arguments Against the Frontrunner
1. Verification cleanup alone may deliver enough value without adding new code.
   - Response: It would remove some confusion, but it would not make the declared deterministic `/dialogue` pipeline any more enforceable or testable.
2. Security rule drift could be more dangerous than orchestration drift.
   - Response: It is real and should be third in the sequence, but current evidence shows more behavior specified in markdown than in code. That affects every deep consultation path.
3. Converting prompt logic into scripts might reduce the flexibility of the skill.
   - Response: The target is only the deterministic parts already described as non-LLM. Prompt flexibility should remain in reasoning and synthesis, not in parse/dedup/sanitize rules.

### Disconfirmation Attempts
- Sought: evidence that wrapper-level transport hardening should displace reliability work.
  - Found: none locally; the README treats wrapper escalation as conditional, not immediate.
- Sought: evidence that the package already has strong, self-contained verification.
  - Found: the opposite. The meaningful suite lives mostly at repo root, while the package-local path exercises only 3 tests.

## Decision
**Choice:** Option 1: Reliability-First Control-Plane Hardening

**Recommended immediate enhancement sequence:**
1. **Make the `/dialogue` deterministic control plane executable.**
   - Extract Step 0 shaping validation plus Step 3/4 briefing assembly into a small Python module or CLI with structured input/output.
   - First target: parse/retry/discard/sanitize/dedup/provenance/seed-confidence logic from the current skill contract.
   - This turns the biggest markdown-only behavior surface into something testable and reusable.
2. **Unify the verification story and clear the current drift.**
   - Fix the `planning` profile posture mismatch.
   - Make the repo-root cross-model suite the documented verification gate for plugin changes.
   - Update package docs/changelog so coverage claims and commands match reality.
3. **Deduplicate secret-detection rules behind a shared source of truth.**
   - Stop carrying an independently tightened copy of credential patterns in `codex_guard.py`.
   - Either share pattern definitions directly or generate the guard subsets from a canonical module, then add sync tests.

**Trade-offs Accepted:** Wrapper-level transport enforcement, learning-system fields like `episode_id`, and analytics expansion are deferred because they are lower immediate leverage than control-plane executability and verification clarity.

**Confidence:** High

## Downstream Impact
- This enables:
  - Replay or golden testing for the actual `/dialogue` contract
  - Faster diagnosis of contract drift
  - Safer future security or analytics changes because the control plane is less implicit
- This precludes:
  - Spending the next cycle primarily on wrapper transport work
  - Treating package-local `uv run pytest` as sufficient evidence of plugin correctness

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Finding |
|------|---------------|-------------|-------------|
| 1 | Initial frame | Option 1 | The most consequential behavior is still defined in prompt markdown rather than executable code |
| 2 | None | Option 1 | Test topology and the current planning-profile mismatch reinforced that drift, not transport design, is the immediate issue |

## Exit Gate
- [x] All outer-loop framing activities complete
- [x] All inner-loop evaluation activities complete
- [x] A null option was considered
- [x] Trade-offs are explicit
- [x] Recommendation is converged and defensible

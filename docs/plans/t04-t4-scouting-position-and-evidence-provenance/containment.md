---
module: containment
status: active
normative: true
authority: containment
---

# Containment

Scope confinement enforcement — pre-execution checks, scope_root
derivation, post-containment capture, and safety interaction.

T4 replaces helper-era `execute_scout` (which had truncation, redaction,
and risk_signal at
[context-injection-contract.md:665](../../../packages/plugins/cross-model/references/context-injection-contract.md))
with direct Glob/Grep/Read. The helper-era safety surfaces are replaced
by this containment contract.

## <a id="t4-ct-01"></a>T4-CT-01: Scope Breach Handling

**Canonical paths:** All paths resolved via realpath. Symlinks resolved.

**Per-call counting:** N out-of-scope results from one call = 1 breach.

**Root-constrained invocation:** `Glob`/`Grep` receive `path` within
`allowed_roots`. Post-execution filter on canonical paths.

**Pre-execution:** `Read` target checked before execution.

**Partial-round:** `scope_breach_count >= 3` mid-round → pending-round
marker ([T4-SM-09](state-model.md#t4-sm-09)) → T1 termination.

## <a id="t4-ct-02"></a>T4-CT-02: Direct-Tool Confinement

### Pre-Execution Confinement

| Tool | Confinement |
|------|------------|
| `Read` | Target path checked against `allowed_roots` BEFORE execution. Out-of-scope → rejected, no output |
| `Grep` | `path` parameter set to `scope_root` within `allowed_roots`. Only results under scope root |
| `Glob` | `path` parameter set to `scope_root` within `allowed_roots`. Only results under scope root |

### scope_root Derivation

For each `Grep` or `Glob` step, `scope_root` is set to a path within
`allowed_roots`. When `allowed_roots` contains a single entry,
`scope_root` equals that entry. When multiple roots exist:

- If the query target names or implies a file or directory path,
  `scope_root` is the shallowest `allowed_root` whose subtree contains
  that path. `allowed_roots` is not guaranteed disjoint; the
  shallowest-root rule resolves overlaps deterministically.
- If the query target is conceptual (no specific path), `scope_root`
  MUST be in `allowed_roots` and recorded in `ScoutStep.scope_root`
  ([T4-SM-05](state-model.md#t4-sm-05)). T4 does not define a
  deterministic selection rule for this case. Scored benchmark runs are
  blocked until the benchmark contract defines a validator-enforceable
  conceptual-query root-selection rule
  ([T4-BR-07](benchmark-readiness.md#t4-br-07) prerequisite item 5).
  If no such rule can be defined, scored runs remain blocked — the
  blocker does not decay into a softer requirement.
- The anti-narrowing constraint applies regardless: the agent MUST NOT
  select a narrower root to exclude files that might contain
  contradictory evidence.
- If the query target spans multiple roots, each tool call uses the
  shallowest root containing its search target; a single query MAY
  produce multiple tool calls with different `scope_root` values.

Every `scope_root` selection MUST be recorded in `ScoutStep.scope_root`.
T4 constrains `scope_root` to membership in `allowed_roots` and requires
per-step recording; the benchmark contract owns comparability rules
([T4-BR-09](benchmark-readiness.md#t4-br-09) amendment row 5).

## <a id="t4-ct-03"></a>T4-CT-03: Post-Containment Capture

The transcript records **post-containment** output. "Raw" in T4's
provenance story means "unprocessed by the agent" — not "unfiltered by
the harness." Containment is a harness function applied before the agent
sees the output:

1. Pre-execution: tool invocation confined to `allowed_roots`
2. Post-execution: any residual out-of-scope results filtered on
   canonical paths ([T4-CT-01](#t4-ct-01))
3. Post-containment output enters the transcript
4. Agent assesses disposition from post-containment output
5. Evidence record and citations reference post-containment output

### Why Containment Does Not Break Provenance Authority

Containment is deterministic and declared — scope roots are immutable,
set at delegation time via `scope_envelope`
([consultation-contract.md:127-131](../../../packages/plugins/cross-model/references/consultation-contract.md)).
The benchmark restricts tool classes to Glob/Grep/Read
([benchmark.md:93-94](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
but does not itself define scope roots. The `scope_envelope` from the
consultation contract provides the immutable `allowed_roots` and source
classes. The agent cannot influence what containment filters. The
mechanical diff ([T4-PR-11](provenance-and-audit.md#t4-pr-11)) operates
on post-containment output and remains authoritative because both sides
of the diff (tool output, citations) are post-containment.

## <a id="t4-ct-04"></a>T4-CT-04: Benchmark-Run Scope Requirement

For any benchmark run (scored comparison, calibration dry run, or schema
shakedown), `scope_envelope` with non-empty `allowed_roots` MUST be
present in the consultation configuration. T4's containment contract
([T4-CT-01](#t4-ct-01)) requires `allowed_roots` for pre-execution
confinement; without it, containment is inoperative and the run MUST NOT
proceed. The consultation contract's unrestricted default
([consultation-contract.md:127](../../../packages/plugins/cross-model/references/consultation-contract.md))
applies to non-benchmark consultations; benchmark execution requires
`scope_envelope` presence as a T4 precondition. Formalizing this as a
benchmark run condition is a T7 dependency
([T4-BR-09](benchmark-readiness.md#t4-br-09) amendment row 5).

## <a id="t4-ct-05"></a>T4-CT-05: Safety Interaction

The benchmark treats forbidden-path leakage as a `safety_violation` — a
scored contract failure, not a run-condition invalidation
([benchmark.md:145](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md),
[benchmark.md:171](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
Containment is T4's mechanism for preventing this, but a containment
failure is still a safety violation on the run — regardless of whether
the root cause is in the harness, the scope_envelope configuration, or
the tool invocation. T4 owns the pre-execution and post-execution
containment checks ([T4-CT-01](#t4-ct-01)). If a leak occurs despite
correct checks, the run remains valid and scored. The leak is recorded as
a `safety_violation` and contributes to the aggregate
`safety_violations` count; the benchmark cannot pass unless that count
remains zero (`safety_violations == 0`).

Whether and how a safety-violating run's artifacts may be accessed,
redacted, quarantined, or used for adjudication is a T7-owned policy
decision outside T4 scope.

### Allowed-Scope Safety Dependency

**DECLARED SAFETY DEPENDENCY.** Within `allowed_roots`, files may contain
secrets (credentials, tokens, private keys). The helper-era contract had
`redactions_applied` and `risk_signal`
([context-injection-contract.md:671-672](../../../packages/plugins/cross-model/references/context-injection-contract.md)).
T4's direct tools have no equivalent. This is an **explicit external
blocker** owned by T7
([T4-BR-03](benchmark-readiness.md#t4-br-03)): the benchmark harness
must define whether allowed-scope secrets require redaction, and if so,
how redacted output interacts with the post-containment provenance model.
Until resolved, T4 assumes allowed-scope content is safe to capture —
correct for benchmark corpora that are curated, but not for general use.

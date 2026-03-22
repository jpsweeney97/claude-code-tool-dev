---
module: decisions
status: active
normative: true
authority: decisions
---

# Decisions

## Named Risks

| Risk | Severity | Mitigation | Detection |
|---|---|---|---|
| **Shadow authority** | High | Engram indexes but never owns. No decisions from [IndexEntry](storage-and-indexing.md#indexentry). | Does any feature give a different answer via Engram vs. subsystem? |
| **God Skill on /save** | Medium | Thin orchestrator, no unique logic, same code paths. See [/save orchestration rules](skill-surface.md#save-orchestration-rules). | Does `/save` contain logic `/defer` or `/distill` don't share? |
| **Fingerprint drift** | Medium | `repo_id` is stored UUIDv4. Dedup uses content hashes, not paths. | Rename repo, clone elsewhere — dedup still works? |
| **Bash enforcement gap** | High | [Bounded guarantee](enforcement.md#enforcement-scope-bounded-guarantee): Write/Edit blocked reliably; engine Bash supported via [trust injection](enforcement.md#trust-injection); arbitrary Bash best-effort. | `/triage` [anomaly detection](operations.md#triage-read-work-and-context) surfaces `provenance_not_established` per-subsystem (Work: `.audit/`, Context: `session_id`, Knowledge: `lesson-meta` + `producer`). |
| **Fork-on-same-machine collision** | Low | Two forks sharing `.engram-id` use the same private root. `worktree_id` differentiates Context queries. Knowledge staging and ledger shards commingle but are operationally harmless at single-developer scale. Deliberate v1 trade-off. | Clone a fork locally, run `/curate` — see candidates from both? |
| **Staging accumulation** | Low | `/triage` reports pending. Cumulative [staging inbox cap](enforcement.md#staging-inbox-cap). `/curate` shows queue. See [operations.md §Distill](operations.md#distill-context-to-knowledge-staged) for rejection logic. | Staging directory file count over time. |
| **NativeReader latency** | Low | Fresh scan at MVP scale is fast. `git log` off hot path. | Query latency on repos with 500+ files. |
| **Concurrent worktree staging** | Medium | Staging files use content-addressed filenames with `O_CREAT | O_EXCL` atomic creation. Published learnings guarded by `fcntl.flock` on lockfile. Cross-worktree concurrency delegated to git merge. See [write concurrency](types.md#write-concurrency). | Two worktrees distill same snapshot concurrently — duplicate staging files? Same-worktree `/learn` + `/curate` concurrent — lost append? |
| **Chain protocol limitations** | Low | Three inherited limitations (resume-crash gap, archive-failure poisoning, state-file TTL race). Archive-failure mitigated in v1 by archive-before-state-write ordering (new Engram sessions only; legacy chain files may still exhibit this issue). See [known limitations](skill-surface.md#chain-protocol-known-limitations). | Session spans >24h, save has no `resumed_from`? |
| **Promotion marker loss** | Low | Branch C/B2 degrades to manual reconcile. Promote-meta remains authoritative. See [marker specification](types.md#promotion-markers-in-claudemd). | `/promote` on previously-promoted lesson → manual reconcile instead of automatic replacement? |
| **Ledger-off triage degradation** | Medium | `/triage` inference [cases (3) and (4) collapse](operations.md#triage-read-work-and-context) when `ledger.enabled=false`. See [degradation model](storage-and-indexing.md#degradation-model). | Disable ledger, run `/save` producing 0 deferred items, `/triage` → "completion not proven (ledger unavailable)"? |

## Open Questions

| Question | When to Resolve |
|---|---|
| What additional fields does IndexEntry need? | Step 0a implementation. Extend based on real query needs. |
| How many of 669 ticket tests are compatibility-critical? | Step 3. Triage before building harness. |
| Bounded candidate search within CLAUDE.md sections — should Step 0a include section-scoped fuzzy matching as fallback? | Step 0a implementation. Start with markers + manual reconcile only. Add section search if marker loss frequency warrants. |

## Deferred Decisions

Explicitly not in v1. Each entry records what was deferred and why.

| Decision | Rationale |
|---|---|
| Three-tier storage (repo-local `.claude/engram/`) | Current two-root model sufficient. Add if multi-worktree pain materializes. |
| Individual knowledge files | Single `learnings.md` for MVP. Split when count warrants. |
| Manifest-based reader discovery | Three hardcoded readers is fine. YAGNI. |
| Incremental indexing | Fresh scan fast enough. Add if >200ms. |
| `auto_silent` autonomy mode | Deferred from ticket v1.1. Carry forward. |
| Reactive pipelines (auto-defer, auto-distill) | User-initiated for v1. Consider after usage patterns emerge. |
| Ledger compaction | Append-only grows indefinitely. Add when file size matters. |
| Cross-user timeline | Session-local only. Multi-user via `git log` is out of scope. |
| Bounded protected-path drift scan | PostToolUse Bash trigger comparing protected-root manifest before/after Bash execution. Would close the Bash enforcement gap for git-tracked paths. Not achievable without pre/post state comparison mechanism. |
| RecordRef subsystem/record_kind constraints | Validated at construction time in implementation, not schema-level Literal types. See [types.md §RecordRef](types.md#recordref--lookup-key). |
| Ledger failure taxonomy | Success-only events for v1. Add failure events, phase attribution, and error classification when recovery-phase automation is warranted. |
| Search relevance ranking | Deterministic `created_at` ordering for v1. Add BM25/TF-IDF when query volume and result set size warrant ranking. |
| Promotion bounded search | Marker-based location only for v1. Add section-scoped candidate matching if marker loss data shows need. |
| Automated promote relocation (Branch B2) | B2 (target_section changed) uses manual reconcile in v1. Automated marker-enclosed block relocation adds implementation complexity for a rare triggering condition. Add when promote relocation frequency warrants. |
| Partial staging (batch splitting) | Whole-batch rejection when `batch_size > knowledge_max_stages`. Partial accept (first N candidates) adds ordering complexity and partial-result semantics. Add if batch-exceeds-cap frequency warrants. See [staging inbox cap](enforcement.md#staging-inbox-cap). |

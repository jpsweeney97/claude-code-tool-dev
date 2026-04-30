# T-20260330-01: Context assembly redaction hardening

```yaml
id: T-20260330-01
date: 2026-03-30
status: closed
priority: medium
tags: [codex-collaboration, hardening, context-assembly, redaction]
blocked_by: []
blocks: []
effort: small
```

## Context

T3/T4 decision gate from the post-R2 hardening framework. Items 6 and 7 from the R1 carry-forward debt ticket (`T-20260327-01`) were assessed against shared context assembly paths.

Item 7 (non-UTF-8 file crash) was closed immediately as a standalone bugfix at `e6792de8`. Item 6 (redaction coverage) was promoted into this ticket as the next work packet.

## Problem

`_SECRET_PATTERNS` in `context_assembly.py` covers 4 pattern families: `sk-*`, `Bearer`, PEM blocks, and `key=value` assignments with 4 keywords. Common credential forms pass through unredacted into Codex prompts:

| Leaked form | Example | Risk |
|-------------|---------|------|
| AWS access keys | `AKIAIOSFODNN7EXAMPLE` | Bare prefix, no `key=` wrapper needed |
| GitHub tokens | `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | Bare prefix |
| GitHub app tokens | `gho_*` | Bare prefix |
| Basic auth headers | `Authorization: Basic dXNlcjpwYXNz` | Header form, not caught by `Bearer` pattern |
| URL-embedded credentials | `https://user:pass@host.com/path` | Userinfo in URL |

These affect the production consult path and the dialogue path equally — `context_assembly.py` is shared infrastructure.

## Scope

**In scope:**
- Port low-ambiguity prefix patterns to `_SECRET_PATTERNS`: `AKIA*`, `ghp_`, `gho_`, `ghs_`, `ghr_`
- Add `Authorization: Basic` header pattern (explicit header form only, not free-floating `basic` text)
- Add URL userinfo pattern (`://user:pass@`)
- Add false-positive regression tests against code-like content
- Close item 6 in carry-forward ticket `T-20260327-01`

**Explicitly out of scope:**
- Blind parity with `context-injection/redact.py` — that module is tuned for excerpt safety where over-redaction is acceptable. This path feeds the full Codex prompt where over-redaction loses meaningful content.
- Broader `_CREDENTIAL_RE` keyword expansion (14 keywords in `redact.py`) — evaluate only after prefix patterns land and false-positive impact is assessed.
- JWT detection — high false-positive risk in code content (base64-heavy strings).
- `github_pat_` fine-grained PAT detection — GitHub Docs confirm the prefix exists but do not publish the token grammar (length, suffix structure). Community-observed regex (`github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}`) is not authoritative. Defer until GitHub publishes an official format spec or the community regex is validated against a larger sample.
- Shared redaction module extraction — acknowledged duplication, not worth the cross-package dependency for this scope.

## Internal precedent

`context-injection/redact.py` (`_JWT_RE` through `_CREDENTIAL_RE`) has battle-tested patterns for all of the above. Adapt, don't copy — the false-positive tolerance differs.

Key differences from `redact.py` context:
- `redact.py` operates on scout evidence snippets (small, targeted reads) — over-redaction is explicitly acceptable (see comment above `_JWT_RE`)
- `context_assembly.py` operates on the full Codex prompt — over-redaction means Codex can't see the code it needs to reason about
- Patterns must be tuned for code content: variable names, comments, documentation examples

## Implementation contract

The current `_redact_text` is a flat `pattern.sub("[redacted]", ...)` loop with no ordering or capture-group awareness. Adding URL userinfo and Basic auth patterns requires a bounded local refactor. The contract below keeps this local — it does NOT introduce `redact.py`-scale staging, stats, or suppression.

### Pattern thresholds

Prefer `secret_taxonomy.py` per-family thresholds over `redact.py` generic thresholds. The taxonomy encodes actual token structures; the `redact.py` ingress threshold (`{10,}`) is deliberately loose because over-redaction is acceptable there.

| Family | Pattern | Source |
|--------|---------|--------|
| AWS access key | `\bAKIA[A-Z0-9]{16}\b` | `secret_taxonomy.py:72` — exact 16 uppercase alnum, word-bounded |
| GitHub tokens | `\b(?:ghp\|gho\|ghs\|ghr)_[A-Za-z0-9]{36,}\b` | `secret_taxonomy.py:114` — 36+ alphanumeric suffix, word-bounded |
| Basic auth header | `(?i)(authorization\s*:\s*basic\s+)[A-Za-z0-9+/]{8,}=*` | `redact.py:97-98` — explicit header form only, group-preserving |
| URL userinfo | `(://[^@/\s:]+:)([^@/\s]+)(@)` | `redact.py:106-107` — structural match, group-preserving |

### Replacement format

- **Prefix patterns** (AKIA, ghp/gho/ghs/ghr): flat `[redacted]` replacement. No structural context to preserve.
- **Basic auth**: group-preserving — `Authorization: Basic [redacted]`. Preserve the header prefix so Codex sees this was an auth header.
- **URL userinfo**: group-preserving — `://user:[redacted]@host`. Preserve URL structure so Codex sees this was a URL with credentials.
- **Existing flat patterns** (sk-*, Bearer, PEM): unchanged `[redacted]` replacement.
- **Keyword assignments**: preserve the assignment label (`api_key = [redacted]`) so overlap with prefix rules does not erase useful context.

### Application order

Most-specific-first to prevent double-match after replacement:

1. PEM blocks (multi-line, most specific)
2. URL userinfo (structural)
3. Basic auth header (structural)
4. AWS `AKIA` prefix (exact length, word-bounded)
5. GitHub `gh*_` prefix (minimum length, word-bounded)
6. `sk-*` prefix (existing)
7. `Bearer` token (existing)
8. Keyword assignment (`password=`, `token=`, etc.) — last, broadest

This ordering ensures that a value like `api_key = AKIAIOSFODNN7EXAMPLE` is matched by the AKIA pattern (rule 4) before the keyword pattern (rule 8) can match the same substring. The keyword pattern then matches only the `api_key = [redacted]` residue, which is harmless because `[redacted]` is shorter than 16 uppercase alnum chars and won't re-match the AKIA pattern.

### Overlap behavior

Test explicitly that `api_key = AKIAIOSFODNN7EXAMPLE` produces exactly one `[redacted]` token and the label `api_key` survives intact.

## Acceptance criteria

- [x] `AKIA*` bare keys redacted in assembled packets
- [x] `ghp_`, `gho_`, `ghs_`, `ghr_` tokens redacted
- [x] `Authorization: Basic` headers redacted
- [x] URL userinfo (`://user:pass@host`) redacted
- [x] False-positive regression: code containing `basic_auth_setup`, `basic_config`, and similar patterns NOT redacted
- [x] False-positive regression: variable names like `ghp_enabled` or `akia_prefix` NOT redacted (short suffixes below token-length minimum)
- [x] URL userinfo replacement preserves URL structure (`://user:[redacted]@host`)
- [x] Basic auth replacement preserves header prefix (`Authorization: Basic [redacted]`)
- [x] Overlap test: `api_key = AKIAIOSFODNN7EXAMPLE` produces one redaction with `api_key` label intact
- [x] Existing 4-pattern coverage preserved (no regression in current tests)
- [x] Item 6 marked closed in `T-20260327-01`

## Resolution

Item 6 is closed. `context_assembly.py` now applies the redaction rules in the ticket's required order, preserves structure for Basic auth headers and URL userinfo, and retains assignment labels when prefix and keyword rules overlap.

Verification:
- `uv run pytest packages/plugins/codex-collaboration/tests` → 220 passed
- `uv run ruff check packages/plugins/codex-collaboration/server/context_assembly.py packages/plugins/codex-collaboration/tests/test_context_assembly.py` → passed

## Parked debt (not in scope)

**Unknown-handle policy (T2 Item B):** Chronically unreachable `unknown` handles retry every startup. Policy debt, not a correctness gap — retry is idempotent, handle namespace is small, spec acknowledges at `contracts.md:156`. No action until usage data shows meaningful accumulation or startup impact.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Current patterns | `context_assembly.py` `_SECRET_PATTERNS` | Starting point |
| Internal precedent | `context-injection/redact.py` `_API_KEY_PREFIX_RE` through `_CREDENTIAL_RE` | Pattern reference (adapt, don't copy) |
| Secret taxonomy | `cross-model/scripts/secret_taxonomy.py` | Broader classification reference |
| R1 carry-forward ticket | `docs/tickets/closed-tickets/2026-03-27-r1-carry-forward-debt.md` | Parent tracking artifact |
| Item 7 fix | `e6792de8` | Binary file hardening (closed) |

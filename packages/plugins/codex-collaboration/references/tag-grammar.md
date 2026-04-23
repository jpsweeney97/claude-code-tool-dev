# Prefix-Tagged Line Grammar

Reference for the `/dialogue` skill's assembly logic and gatherer agent output format. This is a codex-collaboration-owned contract surface, independently versioned.

## Grammar

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>] [SRC:<source>]
```

**Fields:**
- `TAG:` — required. One of: `CLAIM`, `COUNTER`, `CONFIRM`, `OPEN`.
- `<content>` — required. The finding text. Everything between the tag colon and the first metadata field (`@`, `AID:`, `TYPE:`, `[SRC:`), or end of line.
- `@ <path>:<line>` — citation. File path and line number.
- `AID:<id>` — assumption ID reference (e.g., `AID:A1`). Links finding to a specific assumption from the user's objective.
- `TYPE:<type>` — contradiction type. One of the values in the whitelist below.
- `SRC:<source>` — provenance tag. Gatherer-emitted values: `code`, `docs`. Assembler-assigned only: `unknown` (indicates gatherer did not follow output format — never valid in gatherer output). Required on CLAIM lines. Optional on OPEN lines. Not used on COUNTER/CONFIRM (AID provides traceability).

## Tags

| Tag | Purpose | Citation | AID | TYPE | SRC |
|-----|---------|----------|-----|------|-----|
| `CLAIM` | Factual observation about the codebase | Required | Optional | No | Required |
| `COUNTER` | Evidence contradicting a stated assumption | Required | Required | Required | No |
| `CONFIRM` | Evidence supporting a stated assumption | Required | Required | No | No |
| `OPEN` | Unresolved question or ambiguity | Optional | Optional | No | Optional |

## TYPE Whitelist

Used exclusively with `COUNTER` tag:
- `interface mismatch` — public API doesn't match claimed contract
- `control-flow mismatch` — execution path differs from assumption
- `data-shape mismatch` — data structure contradicts assumed shape
- `ownership/boundary mismatch` — responsibility boundary differs from assumption
- `docs-vs-code drift` — documentation contradicts actual implementation

## Parse Rules

1. Lines not starting with a recognized tag (`CLAIM:`, `COUNTER:`, `CONFIRM:`, `OPEN:`) are **ignored**.
2. `CLAIM`, `COUNTER`, or `CONFIRM` lines missing `@ <path>:<line>` citation are **discarded**.
3. `COUNTER` or `CONFIRM` lines missing `AID:<id>` are **discarded**.
4. `COUNTER` lines missing `TYPE:<type>` are **discarded**.
5. Malformed metadata slots (e.g., `AID:` with no value) are ignored; the line is still parsed if tag and content are valid.
6. Multiple metadata fields on one line: parse left-to-right, first match wins for each field type.
7. Content with embedded `@` symbols (e.g., email addresses): only `@ ` followed by a path-like pattern (`word/word` or `word.ext:digits`) is treated as a citation.
8. `[SRC:<source>]` values must be one of `code`, `docs`. `unknown` is assembler-assigned only — if a gatherer emits `[SRC:unknown]`, treat it as a missing SRC tag (the assembler will assign `[SRC:unknown]` in step 8).

## Assembly Processing Order

The `/dialogue` skill assembles gatherer outputs using the following deterministic pipeline (SKILL.md steps 5c maps to these steps):

1. **Parse** — extract tagged lines, ignore untagged
2. **Retry** — if a gatherer produced <4 parseable lines, re-launch once, re-parse, combine with original (retry-wins on duplicate key: same tag type + normalized citation)
3. **Zero-output fallback** — if total parseable lines across both gatherers is 0 after retries, use minimal briefing with `warnings: ["zero_output"]`; skip steps 4-9
4. **Discard** — remove `CLAIM`/`COUNTER`/`CONFIRM` missing citation; remove `COUNTER`/`CONFIRM` missing `AID:`; remove `COUNTER` missing `TYPE:`
5. **Cap** — if >3 `COUNTER` items remain, keep first 3 (by appearance order)
6. **Sanitize** — run credential sanitizer patterns on remaining content
7. **Dedup** — same tag type + citation key across gatherers → keep Gatherer A's. Different tag types at same citation retained. Key = `path:line` normalized: strip leading `./`, lowercase, collapse `//`
8. **Validate provenance** — for each `CLAIM` line in the retained set, check for `[SRC:code]` or `[SRC:docs]`. If missing, assign `[SRC:unknown]` and increment `provenance_unknown_count`. Does not drop lines.
9. **Group** — deterministic order (Gatherer A first, then B within each section):
   - Context: `OPEN` + `COUNTER` + `CONFIRM`
   - Material: `CLAIM`
   - Question: user's objective verbatim

## Examples

### Gatherer A output (code explorer)

```
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45 [SRC:code]
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11 [SRC:code]
CLAIM: Generic token redaction runs unconditionally after format-specific @ redact.py:78 [SRC:code]
CLAIM: Denylist covers 14 directory patterns and 12 file patterns @ paths.py:22 [SRC:code]
OPEN: Whether format-specific redaction adds value given generic runs unconditionally
```

### Gatherer B output (falsifier)

```
CONFIRM: Denylist covers OWASP secret categories (AWS, PEM, JWT, GitHub PAT) @ paths.py:22 AID:A1
COUNTER: Format-specific layer has zero matches in 847/969 test cases @ test_redact.py:203 AID:A2 TYPE:interface mismatch
COUNTER: Generic redaction catches all patterns format-specific targets @ redact.py:78 AID:A2 TYPE:control-flow mismatch
OPEN: Whether test fixture coverage reflects production workload distribution AID:A2
```

### Edge cases

```
CLAIM: Uses fcntl.flock for atomic state updates @ nudge_codex.py:65
```
Valid — citation present, no AID/TYPE needed for CLAIM. Missing SRC — assembler assigns `[SRC:unknown]` in step 8.

```
COUNTER: Pipeline is not thread-safe
```
**Discarded** — missing citation (`@ path:line`).

```
COUNTER: State file in /tmp is volatile @ nudge_codex.py:32 AID:A3
```
**Discarded** — missing `TYPE:`.

```
CLAIM: Architecture uses event sourcing for audit log @ docs/decisions/ADR-003.md:12 [SRC:docs]
```
Valid — citation present, SRC is `docs` because the cited file is in `docs/`.

```
This is a general observation about the codebase.
```
**Ignored** — no recognized tag prefix.

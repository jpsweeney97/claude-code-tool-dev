# Prefix-Tagged Line Grammar

Reference for the `/dialogue` skill's assembly logic and gatherer agent output format.

## Grammar

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>]
```

**Fields:**
- `TAG:` — required. One of: `CLAIM`, `COUNTER`, `CONFIRM`, `OPEN`.
- `<content>` — required. The finding text. Everything between the tag colon and the first metadata marker (`@`, `AID:`, `TYPE:`), or end of line.
- `@ <path>:<line>` — citation. File path and line number.
- `AID:<id>` — assumption ID reference (e.g., `AID:A1`). Links finding to a specific assumption from the user's question.
- `TYPE:<type>` — contradiction type. One of the values in the whitelist below.

## Tags

| Tag | Purpose | Citation | AID | TYPE |
|-----|---------|----------|-----|------|
| `CLAIM` | Factual observation about the codebase | Required | Optional | No |
| `COUNTER` | Evidence contradicting a stated assumption | Required | Required | Required |
| `CONFIRM` | Evidence supporting a stated assumption | Required | Required | No |
| `OPEN` | Unresolved question or ambiguity | Optional | Optional | No |

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
6. Multiple metadata markers on one line: parse left-to-right, first match wins for each field type.
7. Content with embedded `@` symbols (e.g., email addresses): only `@ ` followed by a path-like pattern (`word/word` or `word.ext:digits`) is treated as a citation.

## Assembly Processing Order

When the `/dialogue` skill assembles gatherer outputs:

1. **Parse** — extract tagged lines, ignore untagged
2. **Retry** — if a gatherer produced <4 parseable lines, re-launch once, re-parse, combine with original
3. **Zero-output fallback** — if total parseable lines across both gatherers is 0 after retries, use minimal briefing with `seed_confidence: low`; skip steps 4-8
4. **Discard** — remove `CLAIM`/`COUNTER`/`CONFIRM` missing citation; remove `COUNTER`/`CONFIRM` missing `AID:`; remove `COUNTER` missing `TYPE:`
5. **Cap** — if >3 `COUNTER` items remain, keep first 3 (by appearance order)
6. **Sanitize** — run credential patterns (consultation contract §7) on remaining content
7. **Dedup** — same tag type + citation key across gatherers → keep Gatherer A's. Different tag types at same citation retained. Key = `path:line` normalized: strip leading `./`, lowercase, collapse `//`
8. **Group** — deterministic order (Gatherer A first, then B within each section):
   - Context: `OPEN` + `COUNTER` + `CONFIRM`
   - Material: `CLAIM`
   - Question: user's question verbatim

## Examples

### Gatherer A output (code explorer)

```
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11
CLAIM: Generic token redaction runs unconditionally after format-specific @ redact.py:78
CLAIM: Denylist covers 14 directory patterns and 12 file patterns @ paths.py:22
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
Valid — citation present, no AID/TYPE needed for CLAIM.

```
COUNTER: Pipeline is not thread-safe
```
**Discarded** — missing citation (`@ path:line`).

```
COUNTER: State file in /tmp is volatile @ nudge_codex.py:32 AID:A3
```
**Discarded** — missing `TYPE:`.

```
This is a general observation about the codebase.
```
**Ignored** — no recognized tag prefix.

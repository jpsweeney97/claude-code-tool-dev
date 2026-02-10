# LLM Reference Skill: Before/After Evaluation

Comparison of two transformations of the same source document (a 356-line human-oriented cover letter guide), one produced without the skill and one with it.

## By the Numbers

| | Without Skill | With Skill |
|---|---|---|
| Lines | 247 | 276 |
| Reduction from source (356) | 31% | 22% |

The without-skill version cut more aggressively. The difference is in what was cut.

## Preservation of Load-Bearing Content

| Content | Without Skill | With Skill |
|---------|---------------|------------|
| "credible, specific, low-drama" | Dropped | Preserved |
| "grammatically correct and emotionally vacant" | Dropped | Preserved |
| "Not 8. Not 'everything.'" | Replaced with generic paraphrase | Preserved verbatim |
| "Cover letters matter most when" (conditional) | Flattened to absolute: "A cover letter is a writing sample, not a resume rehash" | Preserved as conditional |

The without-skill version committed **synonym smoothing** (replacing precise phrasing with generic equivalents) and **stripped hedges** (collapsing a conditional into an absolute). Both are anti-patterns the skill explicitly names.

## Invented Content

| Item | Without Skill | With Skill |
|------|---------------|------------|
| Third transformation example ("I have excellent communication skills" → board presentations) | Added — not in source | Not added |
| Tailoring Step 2 example table with specific entries | Added — not in source | Not added |
| "filler phrases" rule ("I believe", "I feel that") | Added — not in source | Not added |

The without-skill version invented content that seemed helpful but wasn't in the source. The skill's verification step ("No invented content — nothing added that wasn't in the source") catches this.

## Information Loss

| Content | Without Skill | With Skill |
|---------|---------------|------------|
| "What Hiring Managers Screen For" (5 criteria) | Dropped entirely | Preserved as consolidated section |
| AI prompt templates (4 concrete prompts) | Dropped entirely | Preserved in "Useful Prompts" subsection |
| Three named quality tests (15-second, "only you", integrity) | Merged into flat checklist | Preserved as three distinct subsections |

The skill's checkpoint step — where preservation targets are explicitly listed before writing begins — prevented these from being silently dropped.

## Structure Decisions

| Decision | Without Skill | With Skill |
|----------|---------------|------------|
| Quality tests placement | Moved mid-document into "Voice Calibration" | Kept at end, matching source position |
| Template order | Short note before full letter | Full letter before short note (matches source) |
| Section ordering | Decision table → structure (skipped criteria) | Decision table → hiring manager criteria → structure |

## Failure Modes Observed (Without Skill)

1. **Synonym smoothing** — precise characterizations replaced with generic equivalents
2. **Strip all hedges** — conditional scoping collapsed into absolutes
3. **Invented content** — helpful-seeming additions that weren't in the source
4. **Silent information loss** — sections dropped without acknowledgment

## What the Skill Changed

The skill's checkpoint step (analyze before writing, explicitly listing what to preserve and what to transform) was the primary differentiator. Naming preservation targets before drafting prevented the default tendency to regularize and compress.

The skill-guided version is 29 lines longer but preserves more signal. The extra lines aren't bloat — they're content the first pass silently discarded.

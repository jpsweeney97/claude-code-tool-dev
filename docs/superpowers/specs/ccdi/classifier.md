---
module: classifier
status: active
normative: true
authority: classifier-contract
---

# CCDI Topic Classifier

Takes input text and resolves it to zero or more Claude Code extension topics with confidence levels and facet hints. Operates on a pinned snapshot of the [compiled topic inventory](data-model.md).

## Two-Stage Pipeline

### Stage 1: Candidate Generation (Recall-Biased)

Linear scan over all aliases in the topics map against normalized input text. Produces a broad, intentionally noisy candidate list.

Matching rules by `match_type`:

| Match type | Behavior | Example |
|------------|----------|---------|
| `exact` | Case-sensitive substring match | `"PreToolUse"` matches verbatim |
| `phrase` | Case-insensitive multi-word match | `"pre tool use"` |
| `token` | Case-insensitive single-word match | `"hook"` |
| `regex` | Compiled regex pattern (sparingly) | For patterns like `SKILL\.md` |

Each candidate accumulates a score from matched aliases: sum of `alias.weight` values. Evaluation order: exact before phrase before token. Longer, more specific matches take precedence within the same match type. Repeated mentions of the same alias do NOT inflate the score.

### Stage 2: Ambiguity Resolution (Precision-Biased)

Four deterministic rules:

| Rule | Effect | Example |
|------|--------|---------|
| Prefer leaf over family | Leaf with strong match absorbs parent family | `hooks.pre_tool_use` (1.0) absorbs `hooks` (0.4) |
| Generic terms are facet modifiers | Words like `schema`, `config`, `JSON` shift facet, not topic | `"schema"` pushes toward schema facet, doesn't create `plugins.manifest` |
| Collapse nested family matches | Multiple weak leaves in same family → elevate to family | Two weak hook leaves → single `hooks` family at overview facet |
| Suppress orphaned generics | Candidates from only generic/denied tokens with no anchor are dropped | `"settings"` alone → suppressed |

## Confidence Levels

Thresholds are configurable via [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `classifier`. Defaults shown:

| Level | Criteria | Config key |
|-------|----------|-----------|
| `high` | At least one exact/phrase match with weight ≥ 0.8 | `confidence_high_min_weight` |
| `medium` | Cumulative score ≥ 0.5 from multiple aliases, or one match with weight 0.5–0.79 | `confidence_medium_min_score`, `confidence_medium_min_single_weight` |
| `low` | Only token matches or generic terms, cumulative score < 0.5 | *(below medium thresholds)* |

## Output Structure

Produced by the [`classify` CLI command](integration.md#cli-tool-topic_inventorypy) and consumed by the [topic registry](registry.md) for scheduling decisions. Valid `Facet` values: `overview`, `schema`, `input`, `output`, `control`, `config` (defined in [data-model.md#queryplan](data-model.md#queryplan)).

```
ClassifierResult
├── resolved_topics[]
│   ├── topic_key: TopicKey
│   ├── family_key: TopicKey
│   ├── coverage_target: "family" | "leaf"
│   ├── confidence: "high" | "medium" | "low"
│   ├── facet: Facet
│   ├── matched_aliases: { text, span, weight }[]
│   └── reason: string
└── suppressed_candidates[]
    ├── topic_key: TopicKey
    └── reason: string
```

## Injection Thresholds

Thresholds are configurable via [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `injection`. Defaults shown:

| Phase | Injection fires when | Config keys |
|-------|---------------------|------------|
| Initial (pre-dialogue) | 1 high-confidence topic, OR 2+ medium-confidence in same family | `initial_threshold_high_count`, `initial_threshold_medium_same_family_count` |
| Mid-dialogue | 1 high-confidence uncovered leaf, OR 1 medium-confidence leaf in 2+ consecutive turns | `mid_turn_consecutive_medium_turns` |
| `/codex` (CCDI-lite) | Same as initial | *(same keys)* |

Semantic hints (see [registry.md#semantic-hints](registry.md#semantic-hints)) are an additional mid-dialogue injection trigger processed by the scheduling layer, independent of classifier output. The classifier does not process or output semantic hints.

Low-confidence detections are recorded in the [topic registry](registry.md) but never trigger injection alone.

## Worked Example

Input: `"I'm building a PreToolUse hook that validates tool inputs against a schema"`

**Stage 1 candidates:**

```
hooks.pre_tool_use  score=1.35  (PreToolUse:1.0, tool inputs:0.35)
hooks               score=0.4   (hook:0.4)
skills.frontmatter  score=0.18  (schema:0.18)
plugins.manifest    score=0.15  (schema:0.15)
```

Note: `hook` is a family-level alias for `hooks` (not for `hooks.pre_tool_use`). Each alias contributes to exactly one topic. The leaf `hooks.pre_tool_use` scores from its own aliases (`PreToolUse`, `tool inputs`) while the family `hooks` scores from its aliases (`hook`).

**Stage 2 resolution:**

```
RESOLVED:  hooks.pre_tool_use  leaf  high  facet=schema
           reason: exact PreToolUse literal plus hook/input context

SUPPRESSED: hooks              → family collapsed under stronger leaf
            skills.frontmatter → generic schema token without family anchor
            plugins.manifest   → generic schema token without family anchor
```

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `classify` returns no topics | Empty `resolved_topics` | Proceed without CCDI |

Per the [resilience principle](foundations.md#resilience-principle), classifier failure never blocks consultations.

# Output Schemas

This reference defines the JSON schemas for doc-auditor persistence files.

## Scan Results Schema

**Location:** `.claude/doc-auditor/scan-results.json`

```json
{
  "$schema": "doc-auditor/scan-results/v1",
  "generated": "2024-12-28T14:30:00Z",
  "config": {
    "include_patterns": ["docs/**/*.md"],
    "exclude_patterns": ["docs/archive/**"],
    "entry_points": ["README.md", "docs/index.md"]
  },
  "documents_analyzed": 24,
  "summary": {
    "total_issues": 47,
    "by_severity": {
      "CRITICAL": 2,
      "HIGH": 8,
      "MEDIUM": 22,
      "LOW": 15
    },
    "by_category": {
      "contradictions": 4,
      "dangling-references": 6,
      "undefined-terms": 8,
      "orphaned-content": 5,
      "coverage-gaps": 10,
      "stale-content": 4,
      "structural": 7,
      "ambiguity": 3
    }
  },
  "issues": [],
  "inline_suppressed": [],
  "categories_disabled": []
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `$schema` | string | Always `"doc-auditor/scan-results/v1"` |
| `generated` | string | ISO 8601 timestamp |
| `config` | object | Config snapshot at scan time |
| `documents_analyzed` | number | Count of docs processed |
| `summary` | object | Aggregate counts |
| `issues` | array | Detected issues (not suppressed) |
| `inline_suppressed` | array | Issues skipped due to inline comments |
| `categories_disabled` | array | Categories turned off in config |

### Issue Object Schema

```json
{
  "id": "a1b2c3d4",
  "category": "contradictions",
  "subcategory": "numeric-contradiction",
  "severity": "HIGH",
  "confidence": "HIGH",
  "location": {
    "file": "docs/architecture.md",
    "section": "## State Machine",
    "line_hint": 45
  },
  "description": "State count mismatch: architecture.md says 10 states, fsm-spec.md says 12",
  "evidence": [
    {
      "file": "docs/architecture.md",
      "quote": "The FSM has 10 distinct states",
      "line_hint": 45
    },
    {
      "file": "docs/fsm-spec.md",
      "quote": "12 states are defined in the state machine",
      "line_hint": 23
    }
  ],
  "impact": "Developers may implement wrong number of states",
  "proposed_fix": {},
  "related_issues": ["b2c3d4e5"]
}
```

### Issue Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | 8-char content hash |
| `category` | string | Yes | One of 15 category keys |
| `subcategory` | string | Yes | Subcategory within category |
| `severity` | string | Yes | CRITICAL, HIGH, MEDIUM, LOW |
| `confidence` | string | Yes | HIGH, MEDIUM, LOW |
| `location` | object | Yes | Where issue was detected |
| `description` | string | Yes | Human-readable summary |
| `evidence` | array | Yes | Supporting quotes/context |
| `impact` | string | No | Why this matters |
| `proposed_fix` | object | No | Suggested resolution |
| `related_issues` | array | No | IDs of connected issues |

### Location Object

```json
{
  "file": "docs/api.md",
  "section": "## Authentication",
  "line_hint": 78
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | Yes | Path relative to project root |
| `section` | string | No | Nearest heading |
| `line_hint` | number | No | Approximate line number |

### Evidence Object

```json
{
  "file": "docs/api.md",
  "quote": "The API requires authentication",
  "line_hint": 78,
  "note": "Additional context if needed"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | Yes | Source file |
| `quote` | string | Yes | Exact text |
| `line_hint` | number | No | Approximate line |
| `note` | string | No | Extra context |

### Proposed Fix Object

**Replace type:**
```json
{
  "type": "replace",
  "file": "docs/api.md",
  "old_string": "The system has 10 states",
  "new_string": "The system has 12 states",
  "rationale": "Matches authoritative count in fsm-spec.md",
  "confidence": "MEDIUM"
}
```

**Insert type:**
```json
{
  "type": "insert",
  "file": "docs/api.md",
  "after_text": "## Authentication\n",
  "insert_text": "\n> **Term**: Definition here.\n",
  "rationale": "Add definition at first use",
  "confidence": "MEDIUM"
}
```

**Delete type:**
```json
{
  "type": "delete",
  "file": "docs/api.md",
  "old_string": "This section is deprecated.",
  "rationale": "Remove stale content",
  "confidence": "HIGH"
}
```

**Manual type:**
```json
{
  "type": "manual",
  "description": "Verify actual state count and update incorrect document",
  "options": [
    "Update architecture.md to say 12 states",
    "Update fsm-spec.md to say 10 states"
  ]
}
```

### Fix Field Definitions

| Field | Type | Required For | Description |
|-------|------|--------------|-------------|
| `type` | string | All | replace, insert, delete, manual |
| `file` | string | replace, insert, delete | Target file |
| `old_string` | string | replace, delete | Text to find (must be unique) |
| `new_string` | string | replace | Replacement text |
| `after_text` | string | insert | Text to find, insert after |
| `insert_text` | string | insert | Text to insert |
| `rationale` | string | All | Why this fix |
| `confidence` | string | replace, insert, delete | HIGH, MEDIUM, LOW |
| `description` | string | manual | What user should do |
| `options` | array | manual | Choices for user |

### Inline Suppressed Object

```json
{
  "location": {
    "file": "docs/legacy.md",
    "line_hint": 42
  },
  "category": "undefined-terms",
  "suppression_type": "line",
  "comment": "<!-- doc-auditor:ignore-line undefined-terms -->"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `location` | object | Where suppression found |
| `category` | string | Category being suppressed |
| `suppression_type` | string | "line" or "block" |
| `comment` | string | Actual suppression comment |

## Issue ID Generation

IDs are content-based hashes for stability:

```
ID = sha256(
  file_path + "|" +
  category + "|" +
  subcategory + "|" +
  normalized_evidence
)[:8]
```

Where `normalized_evidence` = concatenated evidence quotes, lowercased, whitespace-normalized.

**Properties:**
- Same issue → same ID across scans
- Fixing the issue → ID disappears
- Moving text may change ID (acceptable)

## Validation Requirements

Before writing scan results:

1. Build complete JSON in memory
2. Validate required fields present
3. Validate all IDs are 8 characters
4. Validate all categories are valid
5. Validate all severities are valid
6. Write to `.tmp` file first
7. Rename to final location (atomic)

This prevents partial/corrupt writes.

## Reading Scan Results

When loading scan results:

1. Check file exists
2. Parse as JSON
3. Validate `$schema` field
4. Validate `generated` field
5. Validate `issues` array exists
6. If any fail: delete corrupted file, prompt re-scan

# Pipeline Orchestrator v2 Design

**Status:** Approved
**Created:** 2026-01-06
**Goal:** Connect existing plugin-dev skills with automated handoff and state management

## Problem Statement

The plugin-dev plugin has individual skills (brainstorming-*, implementing-*) that work in isolation, but:
- **Handoff problem:** After finishing one skill, users don't know what's next
- **State loss:** Context/decisions from earlier skills get lost in later ones

## Design Approach

**Iterative build, risky parts first:**
1. Phase 1: Subagent output contract + parser (highest risk)
2. Phase 2: State management + reconciliation (second risk)
3. Phase 3: Orchestrator routing
4. Phase 4: End-to-end integration

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE-ORCHESTRATOR                        │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  State         │  │  Subagent      │  │  Output        │    │
│  │  Manager       │  │  Router        │  │  Parser        │    │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘    │
│          │                   │                   │              │
│          └───────────────────┼───────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│                     ┌─────────────────┐                         │
│                     │   Task Tool     │                         │
│                     └────────┬────────┘                         │
└──────────────────────────────┼──────────────────────────────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
      │  pipeline-  │  │  pipeline-  │  │  pipeline-  │
      │  designer   │  │ implementer │  │  optimizer  │
      │             │  │             │  │             │
      │  skills:    │  │  skills:    │  │  skills:    │
      │  brainstorm-│  │  implement- │  │  optimizing-│
      │  ing-*      │  │  ing-*      │  │  plugins    │
      └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Phase 1: Subagent Output Contract

### Agent Definition

**File:** `agents/pipeline-designer.md`

```markdown
---
name: pipeline-designer
description: Design plugin components through structured brainstorming. Use when creating new skills, hooks, agents, or commands.
skills: brainstorming-plugins, brainstorming-skills, brainstorming-hooks, brainstorming-agents, brainstorming-commands
model: inherit
---

You are a plugin design specialist. Help users design plugin components
using the brainstorming skills available to you.

## Your Process

1. If component type is unclear, use brainstorming-plugins for triage
2. Once component type is known, use the appropriate brainstorming-{type} skill
3. Follow the skill's process exactly
4. Write design document to docs/plans/YYYY-MM-DD-<name>-design.md

## Output Contract

CRITICAL: End EVERY response with a fenced YAML block:

```yaml
---
result:
  status: completed | needs_input | error
  stage: triage | designing | blocked
artifacts:
  - path: docs/plans/2026-01-06-example-design.md
    action: created
decisions:
  - key: component_type
    value: skill
    rationale: "User needs guidance, not automation"
next_action: "Run implementing-skills" | "Awaiting user input" | null
error: null | "Description of what went wrong"
---
```

Always include this block. Use empty arrays [] for artifacts/decisions if none.
```

### Output Parser

**File:** `scripts/parse_subagent_output.py`

```python
#!/usr/bin/env python3
"""
Parse structured YAML output from pipeline subagents.

Extracts the YAML block from agent responses and validates against schema.

Exit codes:
    0 - Successfully parsed
    1 - No YAML block found
    2 - YAML parse error
    3 - Schema validation error
"""

from __future__ import annotations

import re
import sys
import json
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Artifact:
    """A file created or modified by the subagent."""
    path: str
    action: str  # created | modified | deleted


@dataclass
class Decision:
    """A design decision made by the subagent."""
    key: str
    value: str
    rationale: str


@dataclass
class SubagentOutput:
    """Parsed and validated subagent output."""
    status: str  # completed | needs_input | error
    stage: str   # triage | designing | blocked
    artifacts: list[Artifact] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    next_action: str | None = None
    error: str | None = None
    raw_yaml: str = ""


def extract_yaml_block(response: str) -> str | None:
    """
    Extract YAML block from agent response.

    Handles:
    - ```yaml\n---\n...\n---\n```
    - Bare ---\n...\n--- at end of response
    """
    patterns = [
        r'```ya?ml\s*\n(---\n[\s\S]*?\n---)\s*```',  # Fenced code block
        r'\n(---\nresult:[\s\S]*?\n---)\s*$',         # Bare at end
        r'^(---\nresult:[\s\S]*?\n---)$',             # Entire response is YAML
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.MULTILINE)
        if match:
            return match.group(1)

    return None


def parse_output(response: str) -> SubagentOutput:
    """
    Parse subagent response and extract structured output.

    Raises:
        ValueError: If YAML block not found or invalid
    """
    yaml_str = extract_yaml_block(response)
    if not yaml_str:
        raise ValueError("No YAML output block found in response")

    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parse error: {e}")

    if not isinstance(data, dict) or 'result' not in data:
        raise ValueError("YAML must contain 'result' key")

    result = data['result']

    # Validate required fields
    if 'status' not in result:
        raise ValueError("Missing required field: result.status")
    if result['status'] not in ('completed', 'needs_input', 'error'):
        raise ValueError(f"Invalid status: {result['status']}")

    if 'stage' not in result:
        raise ValueError("Missing required field: result.stage")

    # Parse artifacts
    artifacts = []
    for item in result.get('artifacts', []):
        if isinstance(item, dict) and 'path' in item:
            artifacts.append(Artifact(
                path=item['path'],
                action=item.get('action', 'created')
            ))

    # Parse decisions
    decisions = []
    for item in result.get('decisions', []):
        if isinstance(item, dict) and 'key' in item:
            decisions.append(Decision(
                key=item['key'],
                value=item.get('value', ''),
                rationale=item.get('rationale', '')
            ))

    return SubagentOutput(
        status=result['status'],
        stage=result['stage'],
        artifacts=artifacts,
        decisions=decisions,
        next_action=result.get('next_action'),
        error=result.get('error'),
        raw_yaml=yaml_str
    )


def main() -> int:
    """Parse subagent output from stdin or file argument."""
    if len(sys.argv) > 1:
        response = Path(sys.argv[1]).read_text()
    else:
        response = sys.stdin.read()

    try:
        output = parse_output(response)

        # Output as JSON for programmatic use
        print(json.dumps({
            'status': output.status,
            'stage': output.stage,
            'artifacts': [{'path': a.path, 'action': a.action} for a in output.artifacts],
            'decisions': [{'key': d.key, 'value': d.value, 'rationale': d.rationale} for d in output.decisions],
            'next_action': output.next_action,
            'error': output.error,
        }, indent=2))
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Pass Criteria

Run pipeline-designer with 5 real scenarios. Pass = 4/5 produce valid, parseable YAML.

---

## Phase 2: State Management

### State Schema

**File:** `docs/plans/plugin-state.json`

```json
{
  "schema_version": "1.0",
  "plugin": "my-plugin",
  "created": "2026-01-06T12:00:00Z",
  "updated": "2026-01-06T14:30:00Z",
  "path": "rigorous",
  "stage": "implementing",
  "components": [
    {
      "type": "skill",
      "name": "my-skill",
      "status": "implemented",
      "design_doc": "docs/plans/2026-01-06-my-skill-design.md"
    }
  ],
  "notes": "trigger_strategy: explicit_only - Complex validation shouldn't auto-trigger"
}
```

### State Manager

**File:** `scripts/state_manager.py`

```python
#!/usr/bin/env python3
"""
Manage plugin development state.

Tracks pipeline progress, reconciles with artifacts, handles drift.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Literal


Status = Literal['pending', 'designing', 'implemented', 'tested']
Path_Type = Literal['minimal', 'rigorous']


@dataclass
class Component:
    """A plugin component being developed."""
    type: str           # skill | hook | agent | command
    name: str
    status: Status
    design_doc: str | None = None


@dataclass
class PluginState:
    """Plugin development state."""
    schema_version: str = "1.0"
    plugin: str = ""
    created: str = ""
    updated: str = ""
    path: Path_Type = "rigorous"
    stage: str = "triage"
    components: list[Component] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            'schema_version': self.schema_version,
            'plugin': self.plugin,
            'created': self.created,
            'updated': self.updated,
            'path': self.path,
            'stage': self.stage,
            'components': [asdict(c) for c in self.components],
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PluginState':
        components = [
            Component(**c) for c in data.get('components', [])
        ]
        return cls(
            schema_version=data.get('schema_version', '1.0'),
            plugin=data.get('plugin', ''),
            created=data.get('created', ''),
            updated=data.get('updated', ''),
            path=data.get('path', 'rigorous'),
            stage=data.get('stage', 'triage'),
            components=components,
            notes=data.get('notes', ''),
        )


class StateManager:
    """Manage plugin state file with drift detection."""

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = Path(plugin_dir)
        self.state_path = self.plugin_dir / "docs" / "plans" / "plugin-state.json"
        self.backup_path = self.state_path.with_suffix('.json.bak')

    def exists(self) -> bool:
        return self.state_path.exists()

    def load(self) -> PluginState:
        """Load state from file."""
        if not self.exists():
            return self._create_initial_state()

        data = json.loads(self.state_path.read_text())
        return PluginState.from_dict(data)

    def save(self, state: PluginState) -> None:
        """Save state to file."""
        state.updated = datetime.now().isoformat()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state.to_dict(), indent=2))

    def backup(self) -> None:
        """Create backup before risky operations."""
        if self.exists():
            shutil.copy2(self.state_path, self.backup_path)

    def _create_initial_state(self) -> PluginState:
        """Create initial state for a new plugin."""
        return PluginState(
            plugin=self.plugin_dir.name,
            created=datetime.now().isoformat(),
            updated=datetime.now().isoformat(),
        )

    def detect_artifacts(self) -> list[tuple[str, str, Path]]:
        """Scan plugin directory for component artifacts."""
        artifacts = []

        for skill_dir in (self.plugin_dir / "skills").glob("*/"):
            if (skill_dir / "SKILL.md").exists():
                artifacts.append(('skill', skill_dir.name, skill_dir / "SKILL.md"))

        for hook_file in (self.plugin_dir / "hooks").glob("*.py"):
            if not hook_file.name.startswith('_'):
                artifacts.append(('hook', hook_file.stem, hook_file))

        for agent_file in (self.plugin_dir / "agents").glob("*.md"):
            artifacts.append(('agent', agent_file.stem, agent_file))

        for cmd_file in (self.plugin_dir / "commands").glob("*.md"):
            artifacts.append(('command', cmd_file.stem, cmd_file))

        return artifacts

    def reconcile(self) -> list[str]:
        """Reconcile state with actual artifacts."""
        state = self.load()
        artifacts = self.detect_artifacts()
        actions = []

        existing = {(c.type, c.name): c for c in state.components}

        for comp_type, name, path in artifacts:
            key = (comp_type, name)
            if key not in existing:
                new_comp = Component(type=comp_type, name=name, status='implemented')
                state.components.append(new_comp)
                actions.append(f"Discovered: {comp_type}:{name}")

        artifact_keys = {(t, n) for t, n, _ in artifacts}
        for comp in state.components:
            key = (comp.type, comp.name)
            if key not in artifact_keys and comp.status == 'implemented':
                actions.append(f"DRIFT: {comp.type}:{comp.name} missing")

        if actions:
            self.backup()
            self.save(state)

        return actions
```

### Pass Criteria

All reconciliation test cases pass:
- Discovers new artifacts
- Detects missing artifacts (DRIFT)
- No action when consistent
- Backup created on changes

---

## Phase 3: Orchestrator Skill

**File:** `skills/pipeline-orchestrator/SKILL.md`

See full content in brainstorming session. Key behaviors:

1. **Resume screen** on return — shows full context
2. **Single triage question** — "Personal or shared use?"
3. **Route to subagents** via Task tool
4. **Update state** after every subagent call
5. **Show next_action** from subagent output

---

## Phase 4: Integration

### End-to-End Flow

```
User Entry → Orchestrator → Triage → pipeline-designer → State Update
                                            ↓
                         ← pipeline-implementer ← State Update
                                            ↓
                                          Done
```

### File Summary

| File | Purpose | Phase |
|------|---------|-------|
| `agents/pipeline-designer.md` | Design subagent | 1 |
| `agents/pipeline-implementer.md` | Implementation subagent | 1 |
| `scripts/parse_subagent_output.py` | YAML extraction | 1 |
| `scripts/state_manager.py` | State CRUD + reconciliation | 2 |
| `skills/pipeline-orchestrator/SKILL.md` | Routing + state | 3 |
| `tests/test_subagent_output.py` | Parser tests | 1 |
| `tests/test_state_manager.py` | State tests | 2 |
| `pyproject.toml` | PyYAML dependency | 1 |

---

## Implementation Order

| Order | Task | Pass Criteria |
|-------|------|---------------|
| 1 | Create `pyproject.toml` with PyYAML | `uv sync` works |
| 2 | Create `parse_subagent_output.py` | Unit tests pass |
| 3 | Create `pipeline-designer.md` agent | 4/5 live scenarios produce valid YAML |
| 4 | Create `state_manager.py` | Unit tests pass |
| 5 | Create `pipeline-orchestrator` skill | Manual end-to-end works |
| 6 | Create `pipeline-implementer.md` agent | Full flow works |

---

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| State file location | `docs/plans/plugin-state.json` (with other plan artifacts) |
| YAML vs JSON output | YAML (more readable, PyYAML handles parsing) |
| Subagent output contract | Structured YAML with status/stage/artifacts/decisions/next_action |
| State drift handling | Conservative: flag DRIFT, don't auto-delete |

---

## Relationship to Previous Design

This design replaces the 814-line `2026-01-05-pipeline-orchestrator-design.md` with a simpler, implementation-focused approach:

| Aspect | Previous | This Design |
|--------|----------|-------------|
| Lines | 814 | ~400 |
| Paths | Minimal/Rigorous with complexity analyzer | Same, but simpler triage |
| Checkpoints | Deferred to v2 | Removed (state file sufficient) |
| Integration tests | Detailed spec | Deferred until basic flow works |
| Subagent contracts | Self-reported + grep | YAML output contract only |

Key simplification: **build risky parts first, prove they work, then add complexity.**

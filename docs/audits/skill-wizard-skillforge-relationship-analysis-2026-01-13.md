# Skill-Wizard & Skillforge Relationship Analysis

**Date:** 2026-01-13
**Scope:** Synergy, merging strategies, plugin architecture options

---

## Executive Summary

`skill-wizard` and `skillforge` are both meta-skills for creating Claude Code skills, but they serve fundamentally different use cases and user personas. Rather than merging them, the optimal strategy is a **federated architecture** where:

1. A shared validation library consolidates spec enforcement
2. A lightweight router directs users to the appropriate tool
3. Both skills reference common infrastructure while maintaining distinct identities

---

## Comparative Analysis

### Architectural Paradigms

| Dimension | skill-wizard | skillforge |
|-----------|--------------|------------|
| **Interaction Model** | Collaborative dialogue | Autonomous pipeline |
| **Validation Timing** | Inline during drafting | Post-hoc via scripts |
| **Quality Gate** | Human approval per section | Multi-agent synthesis panel |
| **Duplicate Detection** | None | Phase 0 triage with skill index |
| **Model Usage** | Single model (default) | Multi-model (3-4 Opus agents) |
| **Context Consumption** | ~500 lines SKILL.md + refs | ~870 lines + 7 reference docs |
| **Recovery Mechanism** | Artifact checkpoint in file | Session handoff document |

### Target User Personas

```
skill-wizard                              skillforge
     │                                         │
     │  "I want to learn the spec"             │  "Just make it work"
     │  "Guide me through this"                │  "Maximum quality, autonomous"
     │  "I have questions"                     │  "Multi-agent review"
     │                                         │
     ▼                                         ▼
┌─────────────────────┐            ┌─────────────────────┐
│ New skill authors   │            │ Power users         │
│ Learning the spec   │            │ Plugin developers   │
│ Want understanding  │            │ Want automation     │
│ Iterative refiners  │            │ Batch creators      │
└─────────────────────┘            └─────────────────────┘
```

### Feature Matrix

| Feature | skill-wizard | skillforge | Notes |
|---------|:------------:|:----------:|-------|
| Section-by-section guidance | ✅ | ❌ | skill-wizard's core value |
| Multi-lens analysis (11 models) | ❌ | ✅ | skillforge's depth |
| Phase 0 duplicate detection | ❌ | ✅ | Prevents redundant creation |
| Executable validation scripts | ❌ | ✅ | `validate-skill.py`, `quick_validate.py` |
| Category-aware DoD generation | ✅ | ❌ | 21 categories with specific requirements |
| Risk tier enforcement | ✅ | ❌ | Auto-escalation for mutating actions |
| Session recovery | ✅ | ✅ | Different mechanisms |
| Multi-agent synthesis panel | ❌ | ✅ | 3 Opus agents, unanimous required |
| Semantic anti-pattern detection | ✅ | ⚠️ | skill-wizard has explicit checklists |
| Script generation guidance | ❌ | ✅ | Script integration framework |
| Timelessness scoring | ❌ | ✅ | ≥7 required |
| Skill improvement mode | ❌ | ✅ | Phase 0 IMPROVE_EXISTING action |

---

## Synergy Opportunities

### 1. Shared Validation Infrastructure

**Current state:** Each skill implements validation differently:

- **skill-wizard:** 11 reference files with [MUST]/[SHOULD]/[SEMANTIC] markers
- **skillforge:** `validate-skill.py` + `quick_validate.py` with code checks

**Synergy:** Create a unified validation layer that both skills can use:

```
.claude/lib/skill-validation/
├── spec/
│   ├── requirements.md           # Canonical spec requirements
│   ├── checklists/              # Section checklists (from skill-wizard)
│   │   ├── frontmatter.md
│   │   ├── when-to-use.md
│   │   └── ... (8 total)
│   └── categories/              # Category-specific DoD (from skill-wizard)
│       └── category-integration.md
├── scripts/
│   ├── validate_structure.py    # Check 8 sections exist
│   ├── validate_frontmatter.py  # Name, description constraints
│   ├── validate_semantic.py     # Anti-pattern language detection
│   └── validate_crossref.py     # allowed-tools vs Procedure
└── templates/
    ├── semantic-templates.md    # T1-T7 templates
    └── wording-patterns.md      # Required phrasings
```

**Benefits:**
- Single source of truth for spec enforcement
- Scripts provide objective checks; checklists guide Claude's analysis
- Updates propagate to both skills automatically

### 2. Unified Routing Layer

**Current state:** Users must know which skill to invoke. Skillforge's Phase 0 triage helps, but doesn't route to skill-wizard.

**Synergy:** Extend skillforge's triage to recognize "guided mode" intent:

```python
# In triage_skill_request.py

GUIDED_MODE_PATTERNS = [
    r'\b(?:guide|help|walk|teach)\s+me\s+(?:through|how)',
    r'\bstep[\s-]by[\s-]step\b',
    r'\bwizard\b',
    r'\binteractive\b',
    r'\blearning?\s+(?:the\s+)?spec\b',
    r'\bexplain\s+as\s+(?:you|we)\s+go\b',
]

def classify_input(query: str) -> Tuple[str, Dict[str, Any]]:
    # ... existing logic ...

    # Check for guided mode preference
    for pattern in GUIDED_MODE_PATTERNS:
        if re.search(pattern, query_lower):
            return InputCategory.GUIDED_CREATE, signals
```

**Triage decision matrix update:**

| Input Type | Match Score | Action |
|------------|-------------|--------|
| Explicit create + guided intent | Any | Route to skill-wizard |
| Explicit create + autonomous | <50% | Route to skillforge |
| Explicit create + high match | ≥80% | CLARIFY (existing skill) |
| "Just make a skill for X" | Any | Route to skillforge |
| "Help me create a skill" | Any | Route to skill-wizard |

### 3. Post-Creation Handoff

**Current state:** Neither skill explicitly hands off to the other's strengths.

**Synergy:** Add handoff points:

```markdown
## skill-wizard completion

After writing SKILL.md:
1. Run `python ~/.claude/lib/skill-validation/scripts/validate_structure.py <path>`
2. If user wants deeper review: "Run /skillforge --triage <path> for multi-agent synthesis"
3. If user wants to promote: "Run `uv run scripts/promote skill <name>`"
```

```markdown
## skillforge completion

After Phase 4 synthesis panel:
1. If user has questions about spec compliance: "Run /skill-wizard on existing file for guided refinement"
2. If validation passes: Proceed to packaging
```

---

## Merging Strategies

### Strategy A: Full Merge (NOT RECOMMENDED)

**Concept:** Combine both skills into one "skill-creator" mega-skill.

**Implementation:**
```yaml
---
name: skill-creator
description: Create skills via guided wizard or autonomous pipeline
---

## Mode Selection

Ask user: "How would you like to create this skill?"

1. **Guided Mode** - Interactive, step-by-step (skill-wizard behavior)
2. **Autonomous Mode** - Multi-agent pipeline (skillforge behavior)
3. **Quick Mode** - Minimal scaffolding
```

**Pros:**
- Single entry point
- No routing confusion

**Cons:**
- ~1,400 lines combined (too large for effective context)
- Dual-purpose skills are harder to maintain
- Different models needed (wizard uses default, forge uses Opus panel)
- Violates "do one thing well" principle
- Mode selection adds cognitive load

**Verdict:** ❌ Creates a bloated, unfocused skill

---

### Strategy B: Orchestrator Pattern (RECOMMENDED)

**Concept:** Create a thin routing layer that dispatches to the appropriate specialized skill.

**Implementation:**

```yaml
# .claude/skills/skill-studio/SKILL.md
---
name: skill-studio
description: Create Claude Code skills. Routes to guided wizard or autonomous forge based on your needs.
---

## When to Use

- User says "create a skill", "new skill", "skill studio"
- User needs help deciding between guided vs autonomous creation

## Procedure

1. **Analyze intent signals:**
   - "guide me", "step by step", "learn", "interactive" → skill-wizard
   - "autonomous", "just make it", "maximum quality", "multi-agent" → skillforge
   - Ambiguous → ask

2. **If ambiguous, present options:**

   | Mode | Best For | Invocation |
   |------|----------|------------|
   | **Guided** | Learning spec, first-time authors, iterative refinement | `/skill-wizard` |
   | **Autonomous** | Power users, batch creation, highest quality gate | `/skillforge` |
   | **Quick** | Scaffolding only, no validation | `skillforge --quick` |

3. **Dispatch to appropriate skill:**
   - Use Skill tool to invoke the selected skill
   - Pass through any context (purpose, category hints)

## Decision Points

- If user explicitly says "wizard" → skill-wizard
- If user explicitly says "forge" or "autonomous" → skillforge
- If user has an existing draft to validate → `/audit-design`
- If user wants to improve existing skill → `skillforge --improve`
```

**Pros:**
- Preserves specialized strengths of each skill
- Thin routing layer (< 100 lines)
- Clear separation of concerns
- Each sub-skill can evolve independently

**Cons:**
- Extra indirection layer
- Users may still need to learn both skills eventually

**Verdict:** ✅ Best balance of usability and maintainability

---

### Strategy C: skill-wizard as Front-End, skillforge as Back-End

**Concept:** Use skill-wizard's interactive discovery to gather requirements, then hand off to skillforge for generation.

**Implementation:**

```markdown
## skill-wizard Phase 1: Discovery (unchanged)
- Gather purpose, category, risk tier, tools
- Explore approaches

## NEW Phase 1.5: Generation Handoff

After discovery completes:
1. Package discovery answers as structured input
2. Ask user: "Ready to generate? Choose mode:"
   - **Draft mode** (default): I'll draft sections for your review
   - **Full forge** mode: Launch skillforge pipeline with your requirements

3. If full forge selected:
   - Convert discovery to SKILL_SPEC.xml format
   - Invoke skillforge Phase 2-4 with spec
   - Return synthesis panel results
```

**Pros:**
- Best of both worlds: wizard's discovery + forge's generation
- Reduces redundant requirement gathering
- Users get guided discovery without losing multi-agent synthesis

**Cons:**
- Complex handoff protocol
- Discovery answers must map to skillforge spec format
- Two different validation philosophies may conflict

**Verdict:** ⚠️ Promising but high implementation complexity

---

### Strategy D: Plugin Architecture

**Concept:** Bundle both skills into a single plugin with shared infrastructure.

**Implementation:**

```
packages/plugins/skill-studio/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── skill-wizard/
│   │   └── SKILL.md
│   ├── skillforge/
│   │   └── SKILL.md
│   └── skill-router/          # Thin orchestrator
│       └── SKILL.md
├── lib/
│   └── skill-validation/      # Shared validation
│       ├── spec/
│       ├── scripts/
│       └── templates/
├── scripts/
│   ├── triage_skill_request.py
│   ├── validate-skill.py
│   ├── discover_skills.py
│   └── quick_validate.py
└── README.md
```

**plugin.json:**
```json
{
  "name": "skill-studio",
  "version": "1.0.0",
  "description": "Complete skill creation toolkit: guided wizard, autonomous forge, and validation tools",
  "skills": "./skills/",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/quick_validate.py"
        }]
      }
    ]
  }
}
```

**Pros:**
- Single install gives users all skill-creation capabilities
- Shared scripts and templates in one place
- Plugin hooks can auto-validate skill writes
- Versioned as a unit

**Cons:**
- Plugin overhead (marketplace, installation)
- Harder to iterate on individual skills
- May conflict with existing skill-wizard/skillforge installations

**Verdict:** ✅ Good for distribution, not for active development

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SKILL CREATION ECOSYSTEM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────┐                                                │
│  │    skill-router     │  ← Entry point: routes based on intent          │
│  │   (thin, ~100 LOC)  │                                                │
│  └──────────┬──────────┘                                                │
│             │                                                            │
│      ┌──────┴──────┐                                                    │
│      ▼             ▼                                                    │
│  ┌────────────┐  ┌────────────┐                                         │
│  │skill-wizard│  │ skillforge │  ← Specialized skills                   │
│  │  (guided)  │  │(autonomous)│                                         │
│  └──────┬─────┘  └─────┬──────┘                                         │
│         │              │                                                 │
│         └──────┬───────┘                                                │
│                ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                    SHARED VALIDATION LAYER                    │       │
│  │  .claude/lib/skill-validation/                               │       │
│  │  ├── spec/requirements.md        (canonical spec)            │       │
│  │  ├── spec/checklists/*.md        (section requirements)      │       │
│  │  ├── spec/categories/*.md        (category-specific DoD)     │       │
│  │  ├── scripts/validate_*.py       (objective checks)          │       │
│  │  └── templates/*.md              (wording patterns)          │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                │                                                         │
│                ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                    SKILL INDEX (skillforge)                   │       │
│  │  ~/.cache/skillrecommender/skill_index.json                  │       │
│  │  - Built by discover_skills.py                               │       │
│  │  - Used by triage_skill_request.py                           │       │
│  │  - Enables duplicate detection for both skills               │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Shared Validation Layer (Week 1)

1. Create `.claude/lib/skill-validation/` directory
2. Move skill-wizard's checklist files to `lib/skill-validation/spec/checklists/`
3. Move skill-wizard's category integration to `lib/skill-validation/spec/categories/`
4. Copy skillforge's validation scripts to `lib/skill-validation/scripts/`
5. Update both skills to reference the shared location
6. Test that both skills still work with shared references

### Phase 2: Routing Enhancement (Week 2)

1. Add guided mode detection to `triage_skill_request.py`
2. Create `skill-router` skill with intent detection
3. Update skillforge to recognize skill-wizard as valid routing target
4. Update skill-wizard's "When NOT to Use" to route to skillforge explicitly

### Phase 3: Bidirectional Handoff (Week 3)

1. Add post-creation suggestions to skill-wizard
2. Add "refinement mode" entry point to skill-wizard for existing files
3. Document the ecosystem in a single README

### Phase 4: Plugin Packaging (Optional)

1. Create `packages/plugins/skill-studio/` structure
2. Bundle both skills + shared validation
3. Publish to tool-dev marketplace
4. Document installation and usage

---

## Decision Matrix

| Scenario | Recommended Tool | Rationale |
|----------|------------------|-----------|
| First time creating a skill | skill-wizard | Learning opportunity |
| Know spec, want max quality | skillforge | Multi-agent synthesis |
| Have existing draft to validate | audit-design | Feasibility review |
| Quick scaffolding | skillforge --quick | Minimal overhead |
| Improve existing skill | skillforge --improve | Enhancement mode |
| Batch creation | skillforge | Autonomous pipeline |
| Understanding spec requirements | skill-wizard | Educational value |
| Building plugin with skills | skillforge | Script integration |

---

## Conclusion

skill-wizard and skillforge are **complementary, not competing**. They serve different user needs and should remain separate skills with:

1. **Shared validation infrastructure** - consolidates spec enforcement
2. **Unified routing** - helps users find the right tool
3. **Bidirectional handoff** - leverages each skill's strengths
4. **Optional plugin packaging** - for easy distribution

The **Orchestrator Pattern (Strategy B)** provides the best balance: users get a single entry point that intelligently routes to the specialized skill matching their needs, while both skills remain focused and maintainable.

**Key insight:** The question isn't "which skill should exist?" but "how do we help users find the right tool for their specific need?" The answer is intelligent routing, not merging.

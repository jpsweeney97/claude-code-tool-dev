# Coverage Matrices

Templates for tracking exploration coverage across different domains.

---

## Purpose

A coverage matrix ensures:
1. You know what needs exploring (scope defined upfront)
2. You track what's been explored (progress visible)
3. You identify gaps (what's not yet covered)
4. Exploration is reproducible (others can verify coverage)

---

## Matrix Conventions

### Status Markers

| Marker | Meaning |
|--------|---------|
| `[x]` | Fully explored |
| `[~]` | Partially explored (note what's missing) |
| `[-]` | Not applicable |
| `[ ]` | Not yet explored |
| `[?]` | Unknown if applicable |

### Completion Rule

**Exploration is not complete until no `[ ]` or `[?]` markers remain.**

Every cell must be explicitly `[x]`, `[~]` with notes, or `[-]` with rationale.

---

## Codebase Exploration Matrix

### Components × Modules

|  | Module A | Module B | Module C | Module D |
|--|----------|----------|----------|----------|
| **Source files** | | | | |
| **Tests** | | | | |
| **Documentation** | | | | |
| **Configuration** | | | | |
| **Scripts** | | | | |

### Component Types × Quality Criteria

|  | Naming | Structure | Error Handling | Documentation |
|--|--------|-----------|----------------|---------------|
| **Functions** | | | | |
| **Classes** | | | | |
| **Modules** | | | | |
| **APIs** | | | | |

### Cross-Cutting Concerns

| Concern | Status | Notes |
|---------|--------|-------|
| Dependency management | | |
| Build system | | |
| CI/CD | | |
| Security | | |
| Performance | | |

---

## Plugin Exploration Matrix

### Plugins × Component Types

|  | Plugin A | Plugin B | Plugin C | Plugin D |
|--|----------|----------|----------|----------|
| **Skills** | | | | |
| **Commands** | | | | |
| **Agents** | | | | |
| **Hooks** | | | | |
| **MCP** | | | | |
| **Manifest** | | | | |

### Plugins × Documentation

|  | Plugin A | Plugin B | Plugin C | Plugin D |
|--|----------|----------|----------|----------|
| **README** | | | | |
| **CHANGELOG** | | | | |
| **Inline docs** | | | | |

### Cross-Plugin Consistency

| Aspect | Status | Notes |
|--------|--------|-------|
| Naming conventions | | |
| Directory structure | | |
| Manifest format | | |
| Path handling | | |
| Error patterns | | |

---

## Documentation Exploration Matrix

### Documents × Verification

|  | Accuracy | Completeness | Currency | Links |
|--|----------|--------------|----------|-------|
| **README** | | | | |
| **API docs** | | | | |
| **Guides** | | | | |
| **Tutorials** | | | | |
| **Reference** | | | | |

### Topics × Coverage

|  | Documented | Examples | Up-to-date |
|--|------------|----------|------------|
| **Installation** | | | |
| **Configuration** | | | |
| **Usage** | | | |
| **Troubleshooting** | | | |
| **Contributing** | | | |

---

## Documentation Set Exploration Matrix

For structured documentation directories (API references, extension guides, product docs).

### Documents × Completeness

|  | Overview | Usage | Examples | Troubleshooting | Cross-refs |
|--|----------|-------|----------|-----------------|------------|
| **Doc A** | | | | | |
| **Doc B** | | | | | |
| **Doc C** | | | | | |
| **Doc D** | | | | | |

### Topics × Coverage

|  | Documented | Accurate | Up-to-date | Has Examples |
|--|------------|----------|------------|--------------|
| **Topic 1** | | | | |
| **Topic 2** | | | | |
| **Topic 3** | | | | |
| **Topic 4** | | | | |

### Cross-Reference Validity

| Source Doc | Target Doc | Link Type | Valid? | Notes |
|------------|------------|-----------|--------|-------|
| | | internal | | |
| | | external | | |
| | | anchor | | |

### Documentation Quality

| Aspect | Status | Notes |
|--------|--------|-------|
| Terminology consistency | | |
| Structure consistency | | |
| Navigation clarity | | |
| Frontmatter completeness | | |
| Orphaned pages | | |

---

## Architecture Exploration Matrix

### Components × Understanding

|  | Purpose | Interfaces | Dependencies | Quality |
|--|---------|------------|--------------|---------|
| **Service A** | | | | |
| **Service B** | | | | |
| **Database** | | | | |
| **Cache** | | | | |
| **Queue** | | | | |

### Layers × Verification

|  | Documented | Matches Code | Patterns Clear |
|--|------------|--------------|----------------|
| **Presentation** | | | |
| **Business Logic** | | | |
| **Data Access** | | | |
| **Infrastructure** | | | |

### Cross-Cutting

| Concern | Status | Notes |
|---------|--------|-------|
| Authentication | | |
| Authorization | | |
| Logging | | |
| Monitoring | | |
| Error handling | | |

---

## Custom Matrix Template

For domains not covered above:

### Step 1: Identify Dimensions

What are the two primary dimensions?
- Dimension A: [e.g., components, modules, documents]
- Dimension B: [e.g., aspects, criteria, verification types]

### Step 2: List Items

Dimension A items:
1. ...
2. ...
3. ...

Dimension B items:
1. ...
2. ...
3. ...

### Step 3: Create Matrix

|  | B1 | B2 | B3 |
|--|----|----|-----|
| **A1** | | | |
| **A2** | | | |
| **A3** | | | |

### Step 4: Add Cross-Cutting

| Cross-Cutting Concern | Status | Notes |
|-----------------------|--------|-------|
| [Concern 1] | | |
| [Concern 2] | | |

---

## Using the Matrix

### Before Exploration

1. Select appropriate template (or create custom)
2. Customize dimensions for your domain
3. Fill in known items
4. Mark all cells `[ ]` to start

### During Exploration

1. Update status as agents report findings
2. Add notes for `[~]` partial coverage
3. Mark `[-]` with rationale for N/A cells
4. Track which agent covered which cell

### After Exploration

1. Verify no `[ ]` or `[?]` remain
2. Review `[~]` cells for completeness
3. Include filled matrix in deliverable
4. Document any scope changes from original

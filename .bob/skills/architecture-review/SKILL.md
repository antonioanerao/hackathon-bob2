---
name: architecture-review
description: >
  Evaluates structural changes for coupling, cohesion, circular dependencies,
  boundary violations, and dependency inversion. All findings require concrete
  impact evidence. Used by the architecture-review-specialist.
---

# Architecture Review

## Purpose

Identify structural changes that increase fragility, reduce testability,
or violate established architectural boundaries. Every finding must describe
a concrete, demonstrable consequence — not a pattern preference.

## Core Principle

> Architectural opinions without impact evidence are not findings.

## When to Use

Activated when ARCHITECTURE domain is detected or when the impact map
reveals cross-module imports or layer violations.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json` (architecture section)
- Git diff (read-only)
- Source files (read-only)

## Phases

### Phase 1: Layer Model Identification

Before analysis, identify the repository's architectural layers:
- What are the main layers? (e.g., routes/controllers → services → repositories → models)
- What are the inter-layer dependency rules?
- Where are the module boundaries?

Use file structure and import patterns to infer the intended architecture
when not documented.

### Phase 2: Import Graph Analysis

For each changed file with cross-module imports:

```bash
grep -n "^from\|^import" app/changed_file.py
grep -rn "from app.routes import\|from app.presentation" --include="*.py" app/services/
```

Build a directed dependency graph for the changed modules.

Identify:
- New imports that cross architectural layer boundaries
- New circular imports
- Imports of infrastructure concerns into domain/business layers

### Phase 3: Coupling Analysis

A coupling increase is when module A gains a new dependency on module B
such that:
- A change to B now requires a change to A
- A cannot be tested without instantiating or mocking B
- Deploying A now requires deploying B

Evaluate each new cross-module import for these properties.

### Phase 4: Cohesion Analysis

A cohesion violation is when:
- A function or method now contains logic that belongs to a different module
- A class takes on a second, unrelated responsibility
- Related logic is split across modules with no clear ownership

### Phase 5: Circular Dependency Detection

Check for circular imports:
```bash
python -c "import app.changed_module"  # will fail with ImportError on cycles
grep -rn "from app.module_a import" app/module_b/ && grep -rn "from app.module_b import" app/module_a/
```

Any import cycle introduced by the PR is a concrete defect (it may cause
`ImportError` at runtime or make startup order-dependent).

### Phase 6: Dependency Inversion Evaluation

When a high-level module imports a low-level module directly:
1. What is the high-level module? (e.g., service layer)
2. What is the low-level module? (e.g., specific DB driver, external HTTP client)
3. Does an abstraction (interface/protocol) exist that should be used instead?
4. What is the concrete impact? (cannot swap implementation without modifying the high-level module)

## Deterministic Tools & Evidence

```bash
grep -rn "^from\|^import" <changed_file>
python -c "import <changed_module>"  # circular import test
grep -rn "from app.routes" app/services/ --include="*.py"  # layer violation search
grep -rn "from app.services" app/routes/ --include="*.py"
```

## Canonical Output

File: `reports/findings/<pr-id>/architecture-review-specialist.json`

Finding IDs: `ARCH-001`, `ARCH-002`, ...

```json
{
  "reviewer": "architecture-review-specialist",
  "findings": [
    {
      "id": "ARCH-001",
      "category": "COUPLING | COHESION | CIRCULAR_DEPENDENCY | BOUNDARY_VIOLATION | DEPENDENCY_INVERSION | RESPONSIBILITY_MISALIGNMENT",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<concise title>",
      "description": "<structural issue and concrete impact>",
      "file": "<path>",
      "line": "<integer>",
      "evidence": ["<import statement>", "<grep result showing violation>"],
      "impact": "<concrete consequence: untestable, deploy coupling, ImportError, etc.>",
      "recommendation": "<actionable structural change>",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "architecture-review-specialist",
      "metadata": {
        "root_cause": "",
        "related_symbols": [],
        "violated_boundary": "<layer_from> → <layer_to>"
      }
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Architecture is undocumented | Infer from file structure; state inference explicitly |
| No clear layering exists | Note the absence; do not impose a layer model |
| Circular import is pre-existing | Classify as `"origin": "PRE_EXISTING"` — non-blocking |

## What This Skill Must Not Do

- Report findings based on pattern preference without concrete impact
- Recommend a complete rewrite of modules not changed by the PR
- Report pre-existing issues as if they were introduced by the PR
- Fabricate import cycles or dependency graphs

## Completion Criteria

- Import graph for changed modules has been built
- All cross-layer imports have been evaluated for concrete impact
- Circular dependencies have been checked
- Every finding has a concrete impact statement, not just a preference statement
- Output file is written and schema-valid

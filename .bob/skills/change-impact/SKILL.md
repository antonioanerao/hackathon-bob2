---
name: change-impact
description: >
  Constructs a dependency and call-graph map of all symbols and files changed
  by the PR to identify indirect effects on callers, consumers, routes,
  services, repositories, database tables, background jobs, and tests.
---

# Change Impact

## Purpose

Determine what else — beyond the directly modified files — can be affected
by this PR's changes. The diff shows what was touched; this skill reveals
what that touch can break.

## Core Question

> What else can this change affect?

## When to Use

Activate immediately after `pr-understanding`, before routing or specialist
execution. The impact map is a required input for all specialist reviewers.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- Repository source files (read-only)
- Test files (read-only)

## Phases

### Phase 1: Symbol Extraction

For each changed file identified in `pr-context.json`:

1. Extract all public symbols (functions, classes, methods) that were modified
2. For each modified symbol, record its full qualified name and file path

```bash
# Python example: find all uses of a changed function
grep -rn "function_name" --include="*.py" .
```

### Phase 2: Caller Analysis

For each changed symbol:

1. Find all files that import or call this symbol
2. Record the calling function/method and its file path
3. Repeat recursively for one additional level (direct callers only; avoid infinite depth)

This identifies what code will execute the changed logic.

### Phase 3: Route Mapping

For each changed service or business logic function:

1. Find which HTTP routes invoke this function (directly or via service chain)
2. Record the route path, HTTP method, and route handler

This identifies which API endpoints are affected by the change.

### Phase 4: Repository and Database Tracing

For changed model or repository symbols:

1. Find which services query through the changed repository
2. Identify which database tables are accessed
3. Note any migrations that reference the changed models

### Phase 5: Background Job Tracing

For changed functions that are called by or from task queues:

1. Identify which task definitions call the changed symbol
2. Note the queue name and worker configuration
3. Identify if the change affects task serialization/deserialization

### Phase 6: Test Coverage Mapping

For each changed symbol:

1. Find existing tests that directly test or reference this symbol
2. Find integration tests that exercise routes affected by the change
3. Note files with no corresponding tests

```bash
grep -rn "changed_symbol_name" tests/ --include="*.py"
```

### Phase 7: Impact Graph Assembly

Combine all findings into a structured impact map.

## Deterministic Tools & Evidence

```bash
grep -rn "<symbol>" --include="*.py" .
grep -rn "from <module> import" --include="*.py" .
grep -rn "import <module>" --include="*.py" .
git diff <base_sha>..<head_sha> -- <file>
```

Python-specific:
```bash
python -c "import ast; ..."   # AST-based call graph (when available)
```

## Canonical Output

File: `reports/context/<pr-id>/impact-map.json`

```json
{
  "pr_id": "<integer>",
  "changed_symbols": [
    {
      "symbol": "<qualified_name>",
      "file": "<path>",
      "change_type": "modified | added | deleted",
      "callers": [
        {
          "symbol": "<qualified_name>",
          "file": "<path>"
        }
      ],
      "callees": [
        {
          "symbol": "<qualified_name>",
          "file": "<path>"
        }
      ],
      "routes": [
        {
          "method": "GET | POST | PUT | PATCH | DELETE",
          "path": "<route_path>",
          "handler": "<handler_function>"
        }
      ],
      "services": ["<service_name>"],
      "repositories": ["<repository_name>"],
      "database_tables": ["<table_name>"],
      "background_jobs": ["<job_name>"],
      "tests": ["<test_file_path>"]
    }
  ],
  "indirect_impact_summary": "<one paragraph describing the blast radius>"
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Symbol not found in grep | Record `"callers": []`, do not fabricate callers |
| Dynamic dispatch makes caller tracing impossible | Note `"callers": ["<dynamic dispatch — cannot resolve statically>"]` |
| Minified or generated files | Skip and note in `indirect_impact_summary` |
| Very large codebase — grep timeout | Limit to 2 directory levels, record truncation note |

## What This Skill Must Not Do

- Fabricate callers, routes, or database tables that were not found by grep or AST analysis
- Assume a symbol is unused because no callers were found (it may be called dynamically)
- Attempt to trace impacts beyond the current repository without explicit evidence
- Perform domain classification or routing decisions (that is adaptive-routing's job)

## Completion Criteria

- `impact-map.json` is written to `reports/context/<pr-id>/`
- All changed symbols are enumerated
- Direct callers have been identified (or empty array with note)
- Routes, repositories, and test coverage have been mapped
- `indirect_impact_summary` provides a plain-language blast radius description

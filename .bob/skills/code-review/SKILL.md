---
name: code-review
description: >
  Evaluates logic correctness, error handling, state coherence, edge cases,
  nullability, resource lifecycle, concurrency, and behavioral regressions
  in the PR's changed code. Used by the code-review-specialist.
---

# Code Review

## Purpose

Identify concrete correctness and safety defects in the logic changes
introduced by the PR. Not style opinions — defects with evidence.

## Core Principle

> Don't just comment. Prove it.

## When to Use

Activated by the orchestrator when APPLICATION_LOGIC, CONCURRENCY, or any
behavioral change domain is detected.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json` (code-review section)
- Git diff of changed files
- Source files referenced by the diff (read-only)

## Phases

### Phase 1: Context Loading

Before reading the diff:
1. Read the PR intent from `pr-context.json`
2. Read the impact map to understand indirect effects
3. Identify the changed symbols and their callers

### Phase 2: Diff Analysis

For each changed function or method:
1. Read the full function body (not just the changed lines)
2. Understand the before-and-after behavior change
3. Identify all code paths: normal, error, edge cases

### Phase 3: Correctness Check

For each changed code path, verify:

**Logic correctness:**
- Does the new logic implement the intended behavior?
- Are there off-by-one errors, incorrect comparisons, inverted conditions?
- Are all return paths handled?

**Error handling:**
- Are exceptions caught at the right level?
- Are exceptions swallowed silently?
- Does error recovery leave the system in a consistent state?

**State consistency:**
- Can partial state updates occur if an exception is raised mid-operation?
- Is shared state mutated in a way that is visible to concurrent callers?
- Are transactions used where atomicity is required?

**Nullability:**
- Are there dereferences of potentially null/None values?
- Are optional fields accessed without null checks?

**Resource lifecycle:**
- Are file handles, DB connections, and network sockets properly closed?
- Are context managers used where applicable?
- Can a code path exit without releasing a resource?

**Concurrency:**
- Is shared mutable state accessed without locks?
- Is there a TOCTOU (time-of-check to time-of-use) race condition?
- Are async operations awaited correctly?

**Edge cases:**
- Empty collections
- Zero values
- Maximum/minimum values
- Concurrent execution of the same code path

### Phase 4: Regression Analysis

Using the impact map:
1. For each changed symbol, find its callers
2. Verify that the new behavior is compatible with caller expectations
3. Identify callers that may be passing values that the old code handled
   but the new code does not

### Phase 5: Deterministic Tool Execution

Run when available:
```bash
ruff check <changed_files>
mypy <changed_files>
python -m py_compile <changed_files>
```

Record tool output as evidence.

## Deterministic Tools & Evidence

```bash
ruff check app/changed_file.py
mypy app/changed_file.py --strict
grep -n "TODO\|FIXME\|HACK\|XXX" app/changed_file.py
```

## Canonical Output

File: `reports/findings/<pr-id>/code-review-specialist.json`

Finding IDs: `CODE-001`, `CODE-002`, ...

```json
{
  "reviewer": "code-review-specialist",
  "findings": [
    {
      "id": "CODE-001",
      "category": "ERROR_HANDLING | NULL_DEREFERENCE | STATE_CONSISTENCY | RESOURCE_LEAK | RACE_CONDITION | EDGE_CASE | LOGIC_ERROR | REGRESSION",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<concise title>",
      "description": "<technical explanation>",
      "file": "<path>",
      "line": "<integer>",
      "evidence": ["<specific code line or tool output>"],
      "impact": "<what breaks or degrades>",
      "recommendation": "<actionable fix>",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "code-review-specialist",
      "metadata": {
        "root_cause": "",
        "related_symbols": []
      }
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| mypy unavailable | Record `TOOL_UNAVAILABLE`, continue manual analysis |
| Changed file is auto-generated | Note and skip — do not analyze generated code |
| Concurrency model unclear | Lower confidence to POSSIBLE, explain ambiguity |

## What This Skill Must Not Do

- Emit style critiques (naming conventions, formatting, line length)
- Flag issues that exist only in code not touched by the PR
- Issue findings about patterns the reviewer dislikes without concrete impact
- Skip reading the full function body and analyzing only the diff lines

## Completion Criteria

- All changed functions and methods have been inspected in full context
- Impact map has been used to identify regression risks
- Tool output has been recorded where tools were executed
- All findings have file + line + evidence
- Output file is written and schema-valid

---
name: test-impact
description: >
  Maps behavioral changes to existing test coverage, identifies gaps between
  changed behavior and tested behavior, and creates targeted verification
  tests when needed. Used by the test-impact-specialist.
---

# Test Impact

## Purpose

Determine whether the behavioral changes introduced by this PR are adequately
covered by tests, and identify the specific gaps that represent the highest risk.

## Core Question

> Is changed behavior tested behavior?

## When to Use

Activated for any PR where behavioral changes are detected. Always paired
with code-review-specialist activation.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json` (test-impact section)
- Git diff (read-only)
- Test suite files (read-only)

## Phases

### Phase 1: Behavioral Change Inventory

For each changed symbol (from impact map):
1. Identify what behavioral change was introduced
2. Classify the change:
   - New behavior added
   - Existing behavior modified
   - Behavior removed or deprecated
   - Error handling changed
   - Edge case handling changed

### Phase 2: Coverage Mapping

For each changed symbol, find existing tests:

```bash
grep -rn "<symbol_name>" tests/ --include="*.py"
grep -rn "<symbol_name>" test/ --include="*.py"
grep -rn "class.*Test\|def test_" tests/ --include="*.py" | grep "<module_name>"
```

For each test found, assess what scenario it covers:
- Happy path (normal successful execution)
- Negative path (expected failure, invalid input)
- Boundary conditions (empty, None, max, min, zero)
- Concurrent execution

### Phase 3: Gap Analysis

A critical test gap exists when:

1. A changed function has **no tests** at all
2. A changed function's **new code path** has no test reaching it
3. An error handling change has no test for the error scenario
4. A security-relevant change has no negative path test
5. The behavior change is tested only via happy path

Classify each gap by severity:

```
CRITICAL  — Security-relevant behavior with zero test coverage
HIGH      — Core business logic change with no negative path coverage
MEDIUM    — Behavioral change with only happy path coverage
LOW       — Changed edge case handling with no boundary condition test
INFO      — Test quality observation (e.g., outdated test description)
```

### Phase 4: Regression Risk Assessment

For each caller identified in the impact map:
1. Does the caller have tests that exercise the changed code path?
2. Would a behavioral regression in the changed symbol be caught by existing tests?

If no existing test would catch a regression in a HIGH or CRITICAL caller,
record a test gap finding.

### Phase 5: Verification Test Proposal (When Required)

When a finding requires empirical proof that coverage is absent or that behavior
is untested, write a proposed minimal test file and delegate execution to the finding-verifier:

```python
# reports/verification/<pr-id>/tests/test_<finding_id>.py
"""
Verification test proposal for TEST-NNN: <finding title>
This file is a temporary verification artifact.
DO NOT commit to the project test suite.
Execution is delegated to the finding-verifier.
"""
import pytest
from app.module import changed_function

def test_gap_scenario():
    # Demonstrates the untested scenario
    ...
```

Do NOT execute this test. Record its path in `verification_recommendation` and set
`verification_status = "UNVERIFIED"`. The finding-verifier will execute it.

## Deterministic Tools & Evidence

```bash
# Read-only investigation — no execution:
grep -rn "<symbol>" tests/ --include="*.py"
grep -rn "<symbol>" test/ --include="*.py"

# pytest --collect-only is NOT run by this specialist
# coverage tools are NOT run by this specialist
# Execution is delegated to the finding-verifier
```

## Canonical Output

File: `reports/findings/<pr-id>/test-impact-specialist.json`

Finding IDs: `TEST-001`, `TEST-002`, ...

```json
{
  "reviewer": "test-impact-specialist",
  "findings": [
    {
      "id": "TEST-001",
      "category": "MISSING_COVERAGE | MISSING_NEGATIVE_PATH | MISSING_BOUNDARY | MISSING_REGRESSION | INCOMPLETE_COVERAGE",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<concise title>",
      "description": "<which behavior is changed and why it is untested>",
      "file": "<path to changed file>",
      "line": "<integer>",
      "evidence": ["<grep result showing no test for symbol>"],
      "impact": "<what regression would go undetected>",
      "recommendation": "<specific test scenario that should be written>",
      "verification_status": "UNVERIFIED",
      "verification_recommendation": {
        "required": true,
        "strategy": "TARGETED_TEST",
        "reason": "Test coverage gap cannot be confirmed without executing a targeted test.",
        "proposed_test_file": "reports/verification/<pr-id>/tests/test_TEST-001.py"
      },
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "test-impact-specialist",
      "metadata": {
        "root_cause": "",
        "related_symbols": [],
        "missing_scenarios": ["happy_path | negative_path | boundary | regression"]
      }
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| pytest collect fails | Record `TOOL_UNAVAILABLE`, use grep for coverage analysis |
| Test files not found | Record in evidence: "No test files found for this module" |
| Coverage tool unavailable | Use grep-based coverage analysis; note limitation |
| Dynamic test generation | Note that coverage analysis may be incomplete |

## What This Skill Must Not Do

- Add test files to the official project test directories (`tests/`, `test/`, `spec/`)
- Report a test gap for a change that is explicitly covered by an existing test
- Recommend removing existing tests
- Fabricate pytest collection output or coverage percentages

## Completion Criteria

- All changed behavioral symbols have been mapped to existing test coverage
- Critical coverage gaps have been documented with grep-based evidence
- Proposed verification test files (if any) are written to `reports/verification/<pr-id>/tests/`
  and referenced in finding `verification_recommendation` fields
- All findings have `verification_status: "UNVERIFIED"` with verification strategy recommendations
- Output file is written and schema-valid

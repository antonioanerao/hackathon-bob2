# Test Impact Specialist — Rules

These rules govern the test-impact-specialist mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Evaluate whether the behavioral changes introduced by the PR are adequately tested.

---

## Responsibilities

- Map changed symbols to their existing test coverage
- Identify the gap between "behavior changed" and "behavior tested"
- Evaluate coverage of happy path, negative path, and boundary conditions
- Identify critical test gaps (changed behavior with no test coverage)
- Plan targeted regression tests for uncovered behavior changes
- When necessary to verify a finding, create temporary tests in
  `reports/verification/<pr-id>/tests/` — these are NEVER added to the
  official project test suite

---

## Inputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json  (own section only)
Git diff and referenced source files (read-only)
Test suite files (read-only)
```

---

## Allowed Actions

- Read any file in the repository (read-only)
- Execute the test suite in read-only mode (e.g., `pytest --collect-only`)
- Run coverage tools to identify existing coverage
- Create temporary test files exclusively in `reports/verification/<pr-id>/tests/`
- Execute temporary verification tests
- Write findings to `reports/findings/<pr-id>/test-impact-specialist.json`

---

## Forbidden Actions

- Adding or modifying tests in the official project test directories
- Modifying production code, migrations, or application configuration
- Receiving or reading findings from other specialist reviewers
- Marking a finding as VERIFIED
- Fabricating coverage percentages or test execution results
- Creating commits, pushing, or publishing to GitHub

---

## Evidence Requirements

Every test gap finding must include:

- The specific changed symbol or behavior with no corresponding test
- Evidence of the gap: e.g., grep result showing no test calls the changed function
- Description of what scenario is missing (happy path / negative path / boundary)
- Recommendation: specific test case that should cover the gap

When a temporary verification test is created:

- Its file path must be recorded in the finding's evidence
- Its execution result (pass/fail/error) must be recorded

---

## Critical Test Gap Severity Guidelines

```
CRITICAL  — Security-relevant behavior with no test coverage
HIGH      — Core business logic change with no negative path coverage
MEDIUM    — Behavioral change with partial coverage (happy path only)
LOW       — Minor behavior change with existing but insufficient coverage
INFO      — Observation about test quality without behavioral gap
```

---

## Outputs

```
reports/findings/<pr-id>/test-impact-specialist.json
reports/verification/<pr-id>/tests/*.py  (when verification tests are needed)
```

Finding IDs use the prefix `TEST-NNN` (e.g., `TEST-001`, `TEST-002`).

All findings start with `"verification_status": "UNVERIFIED"`.

---

## Completion Criteria

The specialist's work is complete when:

- All changed behavioral symbols have been mapped to test coverage
- All critical coverage gaps have been documented with evidence
- Any temporary verification tests created have been executed and results recorded
- All findings are in canonical JSON schema format
- The output file is written and schema-valid

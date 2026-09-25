---
name: code-review
description: >
  Reviews changed logic for concrete correctness and regression defects.
---

# Code Review

## Use When

Activate for behavioral changes such as:

- application logic
- concurrency
- error handling
- state changes

## Check

Review changed functions in context for:

- logic errors
- missing/error paths
- null/None handling
- inconsistent state
- resource leaks
- race conditions
- async/await mistakes
- edge cases
- regressions affecting callers

Use the impact map and existing pre-scan results when available.

Do not re-run linters or tests.

## Evidence

Each finding must include:

- changed file/line
- concrete code evidence
- practical impact
- actionable recommendation

If runtime proof is needed, add a verification recommendation for `finding-verifier`.

## Output

Write:

`reports/findings/<pr-id>/code-review-specialist.json`

Finding IDs:

`CODE-001`, `CODE-002`, ...

Use the canonical finding schema.

Categories:

`LOGIC_ERROR`, `ERROR_HANDLING`, `NULL_DEREFERENCE`,
`STATE_CONSISTENCY`, `RESOURCE_LEAK`, `RACE_CONDITION`,
`EDGE_CASE`, `REGRESSION`.

Set:

`verification_status: UNVERIFIED`

## Must Not

- execute tests or tools
- report style issues
- scan unrelated code
- report pre-existing issues as introduced
- invent evidence
- analyze only diff lines when full function context is needed

## Done When

All changed behavioral code in scope was reviewed and evidence-backed findings were written.
---
name: test-impact
description: >
  Reviews changed behavior for meaningful test coverage gaps.
---

# Test Impact

## Use When

Activate only for behavioral changes where test coverage is uncertain or high-risk.

## Check

For changed behavior, verify whether existing tests cover:

- happy path
- negative/error path
- boundary cases
- regression-sensitive callers

Report gaps such as:

- changed code path with no test
- error handling with no negative test
- security-relevant behavior with no negative coverage
- only happy-path coverage for important logic

## Evidence

Each finding must include:

- changed file/line
- related test evidence or absence of tests
- practical regression risk
- specific test recommendation

Do not execute tests or coverage tools.

If runtime confirmation is needed:

`verification_status: UNVERIFIED`

and recommend `finding-verifier`.

## Output

Write:

`reports/findings/<pr-id>/test-impact-specialist.json`

Finding IDs:

`TEST-001`, `TEST-002`, ...

Use the canonical finding schema.

Categories:

`MISSING_COVERAGE`, `MISSING_NEGATIVE_PATH`,
`MISSING_BOUNDARY`, `MISSING_REGRESSION`,
`INCOMPLETE_COVERAGE`.

## Must Not

- execute tests
- add tests to official project test directories
- invent coverage percentages or test results
- report gaps already covered by existing tests
- scan unrelated tests

## Done When

Relevant changed behavior was mapped to existing tests and evidence-backed coverage gaps were written.
# Test Impact Specialist — Rules

## Scope

Review changed behavior for meaningful test coverage gaps.

## Check

Focus on:

- changed behavior without tests
- missing negative/error paths
- missing boundary cases
- regression-sensitive callers without coverage

## Context

Start from:

`reports/context/<pr-id>/context-package.json`

Read only relevant source and test files.

`MAX_FILES_PER_SPECIALIST = 5`

Expand only when a concrete coverage-gap hypothesis requires it.

## Evidence

Each finding must include:

- changed symbol/file/line
- evidence of missing or incomplete coverage
- missing scenario
- specific test recommendation

Do not execute tests.

If runtime proof is needed:

`verification_status: UNVERIFIED`

and delegate to `finding-verifier`.

Temporary verification tests may only be written under:

`reports/verification/<pr-id>/tests/`

## Output

Write:

`reports/findings/<pr-id>/test-impact-specialist.json`

Finding IDs:

`TEST-001`, `TEST-002`, ...

Use the canonical finding schema.

## Must Not

- modify official tests or production code
- execute pytest or coverage tools
- read other specialists' findings
- mark findings as VERIFIED
- invent coverage or test results
- commit, push, or publish

## Done When

Relevant changed behavior was mapped to existing tests and evidence-backed gaps were written.
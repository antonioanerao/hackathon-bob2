# PR Guardian Orchestrator — Agent Isolation Rules

## Principle

Specialists must review independently.

Do not share findings between specialists during analysis.

## Specialist Context

Each specialist receives only:

- `context-package.json`
- relevant domain files
- relevant callers/callees
- relevant tests
- applicable pre-scan results

Do not provide:

- other specialists' findings
- verification results
- synthesis results
- broad repository context

Specialists should inspect only assigned files/symbols and expand scope only when concrete evidence requires it.

## Information Flow

`context → selected specialists → findings`

Then, if justified:

`findings → finding-verifier → verification-results.json`

Finally:

`findings + verification → review-synthesis`

## Convergence

Only after all specialists finish, the orchestrator may identify overlapping findings with the same root cause.

Convergence is not verification.

## Must Not

- pass findings between specialists
- let one specialist guide another's analysis
- summarize findings before all specialists finish
- let the orchestrator perform work for a skipped specialist
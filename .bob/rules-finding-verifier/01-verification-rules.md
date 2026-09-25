# Finding Verifier — Rules

## Scope

Verify or refute existing findings only.

Do not search for new bugs.

## Invoke When

Use only when verification is justified:

- CRITICAL/HIGH findings
- selected uncertain MEDIUM findings
- verifier budget > 0

Invoke at most once per run with a batch.

## Priority

1. CRITICAL
2. HIGH
3. selected MEDIUM

Do not include LOW or INFO by default.

## Verify With

Use the minimum evidence needed:

- existing pre-scan evidence
- targeted static analysis
- targeted test
- config inspection
- dependency analysis
- code-path proof
- direct manual evidence

Reuse existing deterministic results. Do not re-run the same tool unnecessarily.

## Status

Use only:

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

`VERIFIED` and `REFUTED` require concrete evidence.

Absence of proof is not refutation.

## Context

Read only files relevant to the findings being verified.

Temporary tests may exist only under:

`reports/verification/<pr-id>/tests/`

## Output

Write:

`reports/verification/<pr-id>/verification-results.json`

Each result must include:

- `finding_id`
- `status`
- `method`
- `evidence`
- command/exit code when applicable
- notes when inconclusive or failed

## Must Not

- create new findings
- change finding severity
- modify production code/config/migrations
- add tests to official test directories
- fabricate evidence or tool output
- re-run existing deterministic checks unnecessarily
- commit, push, or publish

## Done When

Every finding in the verification batch has a justified result and the verification file is written.
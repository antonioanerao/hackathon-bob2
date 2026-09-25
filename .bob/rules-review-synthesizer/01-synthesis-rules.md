# Review Synthesizer — Rules

## Scope

Consolidate existing findings and verification results into final review artifacts.

Do not search for new bugs.

## Activate When

Normally synthesis runs inline in the orchestrator.

Spawn `review-synthesizer` only when:

- >3 specialists produced findings
- findings volume is high
- deduplication is complex
- orchestrator context is constrained

## Process

1. Load findings and verification results.
2. Apply verification status.
3. Remove `REFUTED` findings from the active set.
4. Deduplicate findings sharing the same root cause.
5. Classify:
   - `BLOCKING` = `VERIFIED` + `CRITICAL|HIGH`
   - `ADVISORY` = all other active findings
6. Calculate summary metrics.
7. Write final artifacts.

## Inputs

- `reports/findings/<pr-id>/*.json`
- `reports/verification/<pr-id>/verification-results.json`, if present
- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

## Outputs

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

## Rules

- Do not create new findings.
- Do not change finding severity.
- Do not re-run reviewers or verification.
- Do not modify production code.
- Do not fabricate metrics or evidence.
- Do not include `REFUTED` findings as active.

## Metrics

At minimum record:

- initial findings
- final findings
- refuted findings
- duplicates removed
- routing discard rate
- noise reduction rate

## Done When

Findings are deduplicated, verification statuses applied, classifications complete, and all three final artifacts are written.
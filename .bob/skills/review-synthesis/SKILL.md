---
name: review-synthesis
description: >
  Consolidates findings and verification results into final PR Guardian reports.
---

# Review Synthesis

## Goal

Produce the final review from existing artifacts only.

Do not re-read source code or search for new issues.

## Inputs

- `reports/findings/<pr-id>/*.json`
- `reports/verification/<pr-id>/verification-results.json`, if present
- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

## Process

1. Load all findings.
2. Apply verification status.
3. Remove `REFUTED` findings from the active set.
4. Deduplicate findings with the same root cause.
5. Classify:
   - `BLOCKING`: `VERIFIED` + `CRITICAL|HIGH`
   - `ADVISORY`: all others
6. Calculate summary metrics.
7. Generate final artifacts.

## Metrics

At minimum record:

- initial findings
- verified
- refuted
- unverified
- duplicates removed
- final findings
- routing discard rate
- noise reduction rate

`noise_reduction_rate = (initial - final) / initial`, or `0` when initial is `0`.

## Outputs

Write:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

`review.md` should contain:

- executive summary
- PR intent
- selected/skipped reviewers
- blocking findings
- advisory findings
- verification summary
- metrics

## Rules

- Use only existing findings/evidence.
- Do not create new findings.
- Do not modify finding severity.
- Do not include `REFUTED` findings as active.
- Do not run reviewers, tests, scanners, or source analysis.
- If verification results are absent, keep findings `UNVERIFIED`.

## Done When

The three final artifacts are written with deduplicated findings, verification status, classification, and metrics.
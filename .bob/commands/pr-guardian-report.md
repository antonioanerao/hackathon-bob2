---
name: pr-guardian-report
description: Regenerates final PR Guardian reports from existing artifacts.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-report

## Usage

`/pr-guardian-report <pr-id>`

Mode: `review-synthesizer`

## Purpose

Rebuild final reports from existing artifacts only.

Do not re-run reviewers or verification.

## Required Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`
- `reports/findings/<pr-id>/*.json`
- `reports/verification/<pr-id>/verification-results.json`, if available

If required artifacts are missing, report and stop.

## Action

1. Validate `<pr-id>`.
2. Load existing artifacts.
3. Run `review-synthesis`.
4. Write:
   - `reports/reviews/<pr-id>/review.json`
   - `reports/reviews/<pr-id>/review.md`
   - `reports/runs/<pr-id>/run-manifest.json`

If verification results are absent, keep applicable findings as `UNVERIFIED`.

## Must Not

- run specialist reviewers
- run finding verification
- create new findings
- modify production code/tests/config
- commit, push, or publish
- invent evidence or metrics

## Completion

Show a short summary with:

- initial/final findings
- verified/refuted/unverified
- blocking/advisory
- duplicates removed
- noise reduction rate

Then display `review.md`.
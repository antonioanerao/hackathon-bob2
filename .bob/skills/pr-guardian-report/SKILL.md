---
name: pr-guardian-report
description: Regenerates final PR Guardian reports from existing artifacts only.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-report

## Usage

`/pr-guardian-report <pr-id>`

## Purpose

Rebuild final reports without re-running reviewers or verification.

## Required Inputs

Read existing:

- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`
- `reports/findings/<pr-id>/*.json`
- `reports/verification/<pr-id>/verification-results.json`, if available

If required artifacts are missing, report what is missing and stop.

## Action

1. Validate `<pr-id>`.
2. Load existing artifacts.
3. Run `review-synthesis`.
4. Generate:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

If verification results are absent, keep applicable findings as `UNVERIFIED`.

## Output

Show a short summary with:

- initial findings
- verified
- refuted
- unverified
- duplicates removed
- final findings
- blocking
- advisory
- noise reduction rate

Then display `review.md`.

## Must Not

- run specialist reviewers
- run verification
- create new findings
- modify production code/tests/config
- commit, push, or publish
- invent findings, evidence, or metrics
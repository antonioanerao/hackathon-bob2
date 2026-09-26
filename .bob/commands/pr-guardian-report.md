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

Mode: `pr-guardian-orchestrator`

## Purpose

Regenerate final reports from existing artifacts only.

Do not re-run reviewers or verification.

## Inputs

Required:

- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

When reviewers were selected:

- `reports/findings/<pr-id>/*.json`

Optional:

- `reports/verification/<pr-id>/verification-results.json`

Stop if required artifacts are missing.

## Action

1. Validate `<pr-id>`.
2. Load existing artifacts.
3. Apply verification results when available.
4. Remove `REFUTED` findings.
5. Deduplicate by root cause.
6. Classify:
   - `BLOCKING` = `VERIFIED` + `CRITICAL|HIGH`
   - `ADVISORY` = remaining active findings
7. Write:
   - `reports/reviews/<pr-id>/review.json`
   - `reports/reviews/<pr-id>/review.md`
   - `reports/runs/<pr-id>/run-manifest.json`

If verification results are absent, keep findings as `UNVERIFIED`.

## Must Not

- run specialist reviewers
- run verification
- create new findings
- modify production code
- invent evidence or metrics
- commit, push, or publish

## Completion

The command is complete only if:

- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

Inline output does not replace required artifacts.

Show a short summary and display `review.md`.
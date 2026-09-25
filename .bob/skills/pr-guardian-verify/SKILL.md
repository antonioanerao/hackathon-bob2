---
name: pr-guardian-verify
description: Re-runs verification for existing PR Guardian findings.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-verify

## Usage

`/pr-guardian-verify <pr-id>`

Mode: `finding-verifier`

## Purpose

Re-verify existing findings without re-running the full review.

Use for findings currently:

- `UNVERIFIED`
- `VERIFICATION_FAILED`

Do not re-run specialist reviewers.

## Required Inputs

- `reports/findings/<pr-id>/*.json`
- `reports/context/<pr-id>/pr-context.json`
- existing `reports/verification/<pr-id>/verification-results.json`, if present

If required artifacts are missing, report and stop.

## Action

1. Validate `<pr-id>`.
2. Load existing findings and verification results.
3. Select only eligible unresolved findings.
4. Load `finding-verification`.
5. Verify in priority order:
   - CRITICAL
   - HIGH
   - selected MEDIUM
6. Merge new results with existing results.
7. Preserve previous `VERIFIED` and `REFUTED` entries unless explicitly targeted.
8. Write:

`reports/verification/<pr-id>/verification-results.json`

If no eligible findings remain, stop with a short notice.

## Must Not

- create new findings
- re-run specialist reviewers
- modify production code/config/migrations
- overwrite prior verified/refuted results without explicit targeting
- fabricate evidence or tool output
- commit, push, or publish

## Completion

Show a short summary with counts for:

- VERIFIED
- REFUTED
- UNVERIFIED
- NOT_APPLICABLE
- VERIFICATION_FAILED

Then suggest:

`/pr-guardian-report <pr-id>`

to regenerate the final report.
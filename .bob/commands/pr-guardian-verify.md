---
name: pr-guardian-verify
description: Re-verifies unresolved PR Guardian findings.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-verify

## Usage

`/pr-guardian-verify <pr-id>`

Mode: `finding-verifier`

## Purpose

Re-verify existing findings without re-running the review pipeline.

## Inputs

- `reports/findings/<pr-id>/*.json`
- `reports/context/<pr-id>/pr-context.json`
- existing `reports/verification/<pr-id>/verification-results.json`, if present

Stop if required artifacts are missing.

## Action

1. Validate `<pr-id>`.
2. Load existing findings and verification results.
3. Select only:
   - `UNVERIFIED`
   - `VERIFICATION_FAILED`
4. Load `finding-verification`.
5. Verify in priority order:
   - CRITICAL
   - HIGH
   - selected MEDIUM
6. Merge results.
7. Preserve existing `VERIFIED` and `REFUTED` entries unless explicitly targeted.
8. Write:

`reports/verification/<pr-id>/verification-results.json`

If no unresolved findings exist, stop with a short notice.

## Must Not

- re-run specialist reviewers
- create new findings
- modify production code/config/migrations
- overwrite prior verified/refuted results without explicit targeting
- fabricate evidence or tool output
- commit, push, or publish

## Completion

Show counts by verification status and suggest:

`/pr-guardian-report <pr-id>`
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

Required:

- `reports/findings/<pr-id>/*.json`

Optional:

- `reports/context/<pr-id>/pr-context.json`
- `reports/verification/<pr-id>/verification-results.json`

If no findings exist, report and stop.

## Action

1. Validate `<pr-id>`.
2. Load findings and previous verification results, if any.
3. Select:
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

## Rules

- Verify only existing findings.
- Use minimum files and commands required.
- Prefer existing evidence before executing tools.
- Do not re-run deterministic checks unnecessarily.

## Must Not

- re-run specialist reviewers
- create new findings
- change finding severity
- modify production code/config/migrations
- overwrite prior `VERIFIED` or `REFUTED` results without explicit targeting
- fabricate evidence or tool output
- commit, push, merge, or publish

## Completion

The command is complete only when:

`reports/verification/<pr-id>/verification-results.json`

has been written.

Show a short verification summary and suggest:

`/pr-guardian-report <pr-id>`
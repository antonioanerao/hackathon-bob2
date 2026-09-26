---
name: pr-guardian-review
description: Runs the full PR Guardian review pipeline.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-review

## Usage

`/pr-guardian-review <owner/repo#pr | PR URL>`

Mode: `pr-guardian-orchestrator`

## Goal

Review a PR using minimum agents, minimum context, and lazy skill loading.

## Discovery

Pass the PR reference unchanged to:

`scripts/collect-pr-context.sh "<pr-ref>"`

Supported formats:

- `owner/repo#pr`
- `https://github.com/owner/repo/pull/pr`

Do not rediscover PR metadata when collection succeeds.

## Flow

1. Validate PR input.
2. Run `scripts/collect-pr-context.sh`.
3. Load `pr-triage`.
4. Produce:
   - `reports/context/<pr-id>/pr-context.json`
   - `reports/context/<pr-id>/impact-map.json`
   - `reports/plans/<pr-id>/review-plan.json`
5. Respect `agent_budget`.
6. Run relevant pre-scan tools at most once.
7. Load only skills for `selected_reviewers`.
8. Run selected specialists as isolated subagents.
9. Persist returned findings under `reports/findings/<pr-id>/`.
10. If justified, invoke `finding-verifier` once with a batch.
11. Synthesize findings inline.
12. Write final reports.

## Limits

- discovery commands: max 2
- initial file reads: max 3
- files per specialist: max 5
- pre-scan tools: max 2
- verifier invocations: max 1

Any expansion requires a concrete risk or finding hypothesis.

## Rules

- Do not preload specialist skills.
- Do not spawn unselected reviewers.
- Do not rediscover metadata already collected.
- Run selected specialists as subagents.
- Do not switch the parent session into specialist modes.
- Specialists return findings to the orchestrator.
- Specialists receive only relevant context.
- Specialists do not receive other specialists' findings.
- Reuse deterministic evidence.
- Do not run full test suites by default.
- Do not modify production code.
- Do not commit, push, merge, or publish.

## Fast Path

- `TRIVIAL` → triage → synthesis
- `LOW` → triage → max 1 reviewer → synthesis
- higher risk → follow `agent_budget`

## Verification

Invoke `finding-verifier` only when:

- verifier budget > 0, and
- CRITICAL/HIGH findings exist
- or selected uncertain MEDIUM findings justify verification

Invoke at most once per run.

## Synthesis

The orchestrator:

1. applies verification results
2. removes `REFUTED` findings
3. deduplicates by root cause
4. classifies:
   - `BLOCKING` = `VERIFIED` + `CRITICAL|HIGH`
   - `ADVISORY` = remaining active findings
5. writes:
   - `reports/reviews/<pr-id>/review.json`
   - `reports/reviews/<pr-id>/review.md`
   - `reports/runs/<pr-id>/run-manifest.json`

## Abort

Stop if:

- PR input is invalid/unavailable
- discovery cannot provide minimum PR context
- triage cannot produce `review-plan.json`

Partial specialist failures may continue, but must be recorded.

## Completion

A run is successful only when:

- triage artifacts exist
- all selected specialists returned findings
- findings artifacts were persisted
- verification completed or was explicitly skipped
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

Inline output does not replace required artifacts.

Show a short summary and display `review.md`.
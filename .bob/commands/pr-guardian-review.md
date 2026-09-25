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

## Flow

1. Validate PR input.
2. Collect compact PR context.
3. Load only `pr-triage`.
4. Produce:
   - `pr-context.json`
   - `impact-map.json`
   - `review-plan.json`
5. Respect `agent_budget`.
6. Run applicable pre-scan tools once.
7. Load only skills for `selected_reviewers`.
8. Run selected specialists in isolation.
9. If justified, invoke `finding-verifier` once with a batch.
10. Run `review-synthesis`.
11. Produce final reports.

## Limits

- discovery commands: max 2
- initial file reads: max 3
- files per specialist: max 5
- pre-scan tools: max 2
- one verifier batch per run

Any expansion beyond limits requires explicit justification.

## Rules

- Never preload specialist skills.
- Never spawn unselected reviewers.
- Reviewers receive only relevant context.
- Reviewers do not see other reviewers' findings.
- Do not repeat deterministic checks.
- Do not run full test suites by default.
- Do not modify production code.
- Do not commit, push, or publish.

## Fast Path

- `TRIVIAL` → triage → synthesis
- `LOW` → triage → max 1 reviewer → synthesis
- higher risk → follow `agent_budget`

## Verification

Load `finding-verification` only when:

- verifier budget > 0, and
- eligible CRITICAL/HIGH findings exist
- or selected uncertain MEDIUM findings justify low-cost verification

Invoke at most once per run.

## Synthesis

Load `review-synthesis` only after specialist/verification stages finish.

Write:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

## Abort

Stop only when:

- PR input is invalid/unavailable, or
- triage cannot produce `review-plan.json`

Partial specialist failures are allowed and must be recorded.

## Completion

Show a short summary with:

- risk level
- selected reviewers
- skills loaded
- verification status
- findings counts
- final report paths

Then display `review.md`.
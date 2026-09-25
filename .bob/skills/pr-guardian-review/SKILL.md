---
name: pr-guardian-review
description: '# /pr-guardian-review'
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-review

## Usage

`/pr-guardian-review <owner/repo#pr | PR URL>`

Mode: `pr-guardian-orchestrator`

## Goal

Run a minimal-cost PR review using:

- lazy skill loading
- agent budget
- targeted context
- conditional verification

## Flow

1. Validate PR input and repository access.
2. Load `AGENTS.md` if present.
3. Load only `pr-triage`.
4. Produce:
   - `reports/context/<pr-id>/pr-context.json`
   - `reports/context/<pr-id>/impact-map.json`
   - `reports/plans/<pr-id>/review-plan.json`
5. If `TRIVIAL`, skip specialists.
6. Run applicable deterministic pre-scan once and store results in `context-package.json`.
7. Load only skills for reviewers in `selected_reviewers`.
8. Run selected reviewers in isolation.
9. Collect findings.
10. Load `finding-verification` only if:
    - verifier budget > 0, and
    - CRITICAL/HIGH findings exist, or selected uncertain MEDIUM findings require proof.
11. Invoke verifier at most once with a batch.
12. Load `review-synthesis` only after review/verification is complete.
13. Generate:
    - `reports/reviews/<pr-id>/review.json`
    - `reports/reviews/<pr-id>/review.md`
    - `reports/runs/<pr-id>/run-manifest.json`

## Runtime Rules

- Never preload specialist skills.
- Never load a skill for an unselected reviewer.
- Reviewers receive only relevant context/files.
- Reviewers do not see other reviewers' findings.
- Triage, discovery, and synthesis run in the orchestrator unless escalation is necessary.
- Do not run `pytest` during pre-scan.
- Verifier performs targeted runtime proof only.
- Do not repeat deterministic checks already available.
- Do not modify production code.
- Do not commit, push, merge, or publish.

## Fast Path

`TRIVIAL`
→ triage → synthesis

`LOW`
→ triage → max 1 reviewer → synthesis

Higher risk
→ respect `agent_budget`.

## Abort

Stop only if:

- PR input is invalid/unavailable, or
- triage cannot produce `review-plan.json`.

Partial specialist failures are allowed and must be recorded.

## Completion

Show a short summary:

- risk level
- reviewers selected/skipped
- skills loaded
- findings counts
- verification status
- report paths

Then display `review.md`.
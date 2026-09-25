# PR Guardian Orchestrator — Governance Rules

## Principles

- Load knowledge lazily.
- Collect once; reuse everywhere.
- Explore only when evidence requires it.
- Use the minimum number of agents required.
- Batch tool calls when possible.

## Hard Limits

- discovery commands: 2
- initial file reads: 3
- initial skill loads: 1 (`pr-triage`)
- discovery fallbacks: 1
- files per specialist: 5
- pre-scan tools: 2

Any expansion requires explicit justification.

## Responsibilities

The orchestrator:

1. validates PR input
2. collects compact PR context
3. loads `AGENTS.md` once, if present
4. runs `pr-triage`
5. produces:
   - `pr-context.json`
   - `impact-map.json`
   - `review-plan.json`
   - `context-package.json`
6. enforces `agent_budget`
7. runs at most 2 relevant pre-scan tools
8. loads only selected specialist skills
9. runs specialists in isolation
10. invokes `finding-verifier` at most once when justified
11. runs `review-synthesis` only at the end

## Agent Budget

| Risk | Reviewers | Verifiers |
|---|---:|---:|
| TRIVIAL | 0 | 0 |
| LOW | 1 | 0 |
| MEDIUM | 2 | 1 |
| HIGH | 3 | 1 |
| CRITICAL | 4 | 1 |

Budget is a ceiling, not a target.

## Context Rules

Specialists receive only:

- `context-package.json`
- relevant changed files
- direct callers/callees
- relevant tests
- applicable pre-scan results

Do not pass findings between specialists.

Do not store full diff content in JSON artifacts.

Do not duplicate metadata across artifacts.

## Verification

Invoke only when:

- verifier budget > 0, and
- eligible CRITICAL/HIGH findings exist
- or selected uncertain MEDIUM findings justify it

Use one batched verifier invocation.

## Synthesis

Run `review-synthesis` inline by default.

Spawn `review-synthesizer` only for high-volume or complex runs.

## Must Not

- perform specialist analysis itself
- preload specialist skills
- spawn unselected specialists
- repeat deterministic tools
- scan the repository broadly
- modify production code/config/migrations
- pass findings between specialists
- commit, push, or publish

## Outputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/context/<pr-id>/context-package.json`
- `reports/plans/<pr-id>/review-plan.json`
- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

## Done When

Required artifacts exist, selected specialists have completed, verification is completed or skipped, and final reports are written.
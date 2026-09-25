---
name: pr-triage
description: >
  Single-pass PR triage for context, impact, risk, and reviewer routing.
---

# PR Triage

## Goal

Answer in one pass:

- What changed?
- What can it affect?
- How risky is it?
- Which reviewers are needed?

Principles:

> Collect once. Reuse everywhere.  
> Explore only when evidence requires it.

## Limits

Before routing:

- max discovery commands: 2
- max initial file reads: 3
- max skill loads: 1
- max discovery fallback: 1

Any expansion beyond these limits must have a specific risk hypothesis.

## Discovery

Prefer one compact collection command/script.

Collect only:

- PR metadata
- base/head SHA
- changed files
- basic tech hints

Do not retry through multiple tools unnecessarily.

Do not store the full diff in artifacts.

## Impact

Map only relevant:

- changed symbols
- direct callers
- exposed routes
- related tests

Batch searches when possible.

Avoid per-symbol command loops.

## Risk

Classify:

| Risk | Rule | Max Reviewers | Max Verifiers |
|---|---|---:|---:|
| TRIVIAL | docs/metadata only | 0 | 0 |
| LOW | small isolated behavior change | 1 | 0 |
| MEDIUM | functional change in limited domains | 2 | 1 |
| HIGH | auth, DB migration, public API, queue/security boundary | 3 | 1 |
| CRITICAL | tenant/auth/crypto/data corruption critical risk | 4 | 1 |

## Triggers

Detect only when supported by the PR:

`AUTHENTICATION_CHANGED`, `AUTHORIZATION_CHANGED`,
`TENANT_BOUNDARY_CHANGED`, `DATABASE_SCHEMA_CHANGED`,
`DATABASE_QUERY_CHANGED`, `PUBLIC_API_CHANGED`,
`BACKGROUND_JOB_CHANGED`, `DEPENDENCY_CHANGED`,
`SECRET_HANDLING_CHANGED`, `FILE_UPLOAD_CHANGED`,
`EXTERNAL_REQUEST_CHANGED`, `CRYPTOGRAPHY_CHANGED`,
`UNTRUSTED_INPUT_CHANGED`, `CONCURRENCY_CHANGED`,
`DEPENDENCY_SECURITY_RISK`.

## Routing

Select only relevant reviewers:

- `code-review-specialist` → behavioral change
- `security-review-specialist` → security/auth/tenant/input/crypto trigger
- `test-impact-specialist` → complex coverage or explicit escalation
- `architecture-review-specialist` → structural/boundary change
- `database-review-specialist` → schema/query/migration/transaction change
- `api-review-specialist` → public API/route/schema/OpenAPI change
- `async-review-specialist` → queue/worker/background-job change

Priority if budget is exceeded:

`code → security → database → api → async → architecture → test-impact`

Budget is a ceiling, not a target.

## Outputs

Write:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`

Keep outputs compact:

- intent: max 2–4 sentences
- reviewer reasons: one line
- no duplicated metadata
- no full diff

`review-plan.json` must contain at least:

- `risk_level`
- `agent_budget`
- `domains`
- `risk_triggers`
- `selected_reviewers`
- `skipped_reviewers`
- `routing_discard_rate`

## Must Not

- load specialist skills
- perform specialist review
- exceed limits without justification
- repeat collected metadata
- scan the repository broadly
- run separate searches when one batch search is enough

## Done When

Context, impact map, risk, budget, and reviewer routing are written and ready for the next stage.
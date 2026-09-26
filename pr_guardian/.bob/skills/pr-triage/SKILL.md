---
name: pr-triage
description: >
  Single-pass PR triage for context, risk, and reviewer routing.
---

# PR Triage

## Goal

Determine:

- what changed
- what may be affected
- risk level
- required reviewers

Principles:

> Collect once. Reuse everywhere.  
> Explore only when evidence requires it.

## Limits

Before routing:

- discovery commands: max 2
- initial file reads: max 3
- discovery fallback: max 1

Expand only for a concrete risk hypothesis.

## Discovery

Use the collected PR context as the primary source.

Collect only:

- PR metadata
- base/head SHA
- changed files
- relevant tech hints

Do not rediscover metadata already available.

Do not store the full diff.

## Impact

Map only what helps routing:

- changed symbols
- direct callers
- exposed routes
- related tests

Batch searches when possible.

## Risk

| Risk | Rule | Max Reviewers | Max Verifiers |
|---|---|---:|---:|
| TRIVIAL | docs/metadata only | 0 | 0 |
| LOW | small isolated behavior change | 1 | 0 |
| MEDIUM | limited functional change | 2 | 1 |
| HIGH | auth, DB, public API, queue or security boundary | 3 | 1 |
| CRITICAL | auth/tenant/crypto/data corruption critical risk | 4 | 1 |

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
- `security-review-specialist` → security/auth/tenant/input/crypto
- `database-review-specialist` → schema/query/migration/transaction
- `api-review-specialist` → API/route/schema/OpenAPI
- `async-review-specialist` → queue/worker/background job
- `architecture-review-specialist` → structural/boundary change

Priority if budget is exceeded:

`code → security → database → api → async → architecture`

Budget is a maximum, not a target.

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
- omit empty optional structures

`review-plan.json` must include:

- `risk_level`
- `agent_budget`
- `risk_triggers`
- `selected_reviewers`
- `skipped_reviewers`

## Must Not

- load specialist skills
- perform specialist review
- spawn reviewers
- exceed limits without justification
- repeat collected metadata
- scan the repository broadly
- use multiple searches when one batch search is enough

## Done When

Context, impact, risk, budget, and reviewer routing are ready for the orchestrator.
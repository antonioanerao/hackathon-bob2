---
name: adaptive-routing
description: >
  Selects only the specialist reviewers relevant to a PR using risk level,
  domain triggers and agent budget. Produces review-plan.json.
---

# Adaptive Routing

## Purpose

Select the minimum set of specialist reviewers required for the PR.

Principles:

- No specialist is mandatory unless its trigger is present.
- Agent budget is a ceiling, not a target.
- Prefer fewer relevant reviewers over broad review coverage.
- Do not perform specialist analysis here.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`, if available
- Existing deterministic pre-scan results, if available

Do not re-run discovery or analysis tools.

## 1. Risk Level

Classify the PR:

| Risk | Criteria | Max Reviewers | Max Verifiers |
|---|---|---:|---:|
| TRIVIAL | Docs, comments, formatting, non-functional metadata | 0 | 0 |
| LOW | Small isolated behavioral change, no sensitive domain | 1 | 0 |
| MEDIUM | Functional change in 1–2 domains | 2 | 1 |
| HIGH | Auth, DB migration, public API, queue semantics, security boundary | 3 | 1 |
| CRITICAL | Tenant isolation, privileged auth, crypto, corruption or critical security | 4 | 1 |

## 2. Domains

Use only applicable tags:

`APPLICATION_LOGIC`, `SECURITY`, `AUTHENTICATION`, `AUTHORIZATION`,
`API`, `DATABASE`, `BACKGROUND_JOB`, `CONCURRENCY`, `CONFIGURATION`,
`DEPENDENCY`, `TESTING`, `ARCHITECTURE`, `OBSERVABILITY`, `PERFORMANCE`.

## 3. Risk Triggers

Detect only explicit triggers supported by changed files or impact context:

- `AUTHENTICATION_CHANGED`
- `AUTHORIZATION_CHANGED`
- `TENANT_BOUNDARY_CHANGED`
- `DEPENDENCY_SECURITY_RISK`
- `DATABASE_SCHEMA_CHANGED`
- `DATABASE_QUERY_CHANGED`
- `PUBLIC_API_CHANGED`
- `BACKGROUND_JOB_CHANGED`
- `DEPENDENCY_CHANGED`
- `SECRET_HANDLING_CHANGED`
- `FILE_UPLOAD_CHANGED`
- `EXTERNAL_REQUEST_CHANGED`
- `CRYPTOGRAPHY_CHANGED`
- `UNTRUSTED_INPUT_CHANGED`
- `CONCURRENCY_CHANGED`

Do not invent triggers.

## 4. Routing

Select a specialist only when relevant:

| Specialist | Select when |
|---|---|
| `code-review-specialist` | Behavioral/application logic changed |
| `security-review-specialist` | Security/auth/authz/tenant/secret/input/crypto trigger |
| `test-impact-specialist` | Complex coverage, integration impact, HIGH/CRITICAL risk, or explicit escalation |
| `architecture-review-specialist` | Module/service/boundary/dependency structure changed |
| `database-review-specialist` | Schema, migration, ORM, query, transaction, index or constraint changed |
| `api-review-specialist` | Public route, request/response schema, HTTP contract or OpenAPI changed |
| `async-review-specialist` | Queue, worker, task, retry, consumer or background processing changed |

Rules:

- Skip `code-review-specialist` for TRIVIAL PRs.
- Basic test impact belongs to `code-review-specialist`.
- Do not select specialists merely because their technology exists in the repository.
- Routing must be based on the PR change, not the project stack alone.

## 5. Budget Enforcement

If selected candidates exceed `max_reviewers`, prioritize:

1. `code-review-specialist`
2. `security-review-specialist`
3. `database-review-specialist`
4. `api-review-specialist`
5. `async-review-specialist`
6. `architecture-review-specialist`
7. `test-impact-specialist`

Record excluded triggered reviewers as:

`Relevant but not selected due to agent budget.`

## 6. Output

Write:

`reports/plans/<pr-id>/review-plan.json`

Minimal schema:

```json
{
  "pr_id": 56,
  "risk_level": "MEDIUM",
  "agent_budget": {
    "max_reviewers": 2,
    "max_verifiers": 1
  },
  "domains": ["APPLICATION_LOGIC"],
  "risk_triggers": [],
  "selected_reviewers": [
    {
      "reviewer": "code-review-specialist",
      "reason": "Behavioral logic changed.",
      "triggers": ["APPLICATION_LOGIC"]
    }
  ],
  "skipped_reviewers": [
    {
      "reviewer": "security-review-specialist",
      "reason": "No security trigger."
    }
  ],
  "routing_discard_rate": 0.86
}
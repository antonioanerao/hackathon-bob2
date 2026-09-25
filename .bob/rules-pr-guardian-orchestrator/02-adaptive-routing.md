# PR Guardian Orchestrator — Adaptive Routing Rules

## Principle

Select only reviewers justified by the PR.

Routing precision matters more than running every specialist. :chatgpt-content-reference{index="0"}

## Risk & Budget

| Risk | Max Reviewers | Max Verifiers |
|---|---:|---:|
| TRIVIAL | 0 | 0 |
| LOW | 1 | 0 |
| MEDIUM | 2 | 1 |
| HIGH | 3 | 1 |
| CRITICAL | 4 | 1 |

Budget is a ceiling, not a target. :chatgpt-content-reference{index="1"}

## Routing

Select reviewers only when relevant:

- `code-review-specialist` → behavioral/application logic changes
- `security-review-specialist` → auth, tenant, secrets, input, crypto, security triggers
- `database-review-specialist` → schema, query, migration, transaction, index, FK changes
- `api-review-specialist` → public API, route, schema, HTTP/OpenAPI changes
- `async-review-specialist` → queue, worker, task, consumer changes
- `architecture-review-specialist` → structural/boundary/dependency changes
- `test-impact-specialist` → complex/high-risk coverage gaps

`code-review-specialist` is skipped for non-behavioral PRs. :chatgpt-content-reference{index="2"}

## Priority When Over Budget

1. code
2. security
3. database
4. api
5. async
6. architecture
7. test-impact

Record excluded reviewers as skipped due to budget. :chatgpt-content-reference{index="3"}

## Output

`review-plan.json` must contain:

- `risk_level`
- `agent_budget`
- `domains`
- `risk_triggers`
- `selected_reviewers`
- `skipped_reviewers`
- `routing_discard_rate`

Every specialist must appear as selected or skipped with a short reason. :chatgpt-content-reference{index="4"}

## Rule

Do not select a specialist merely because its domain might be relevant.

Select it only when concrete PR evidence or triggers justify it.
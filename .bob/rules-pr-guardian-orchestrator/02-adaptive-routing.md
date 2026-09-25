# PR Guardian Orchestrator — Adaptive Routing Rules

These rules define how the orchestrator selects and excludes specialist reviewers.

---

## Routing Principle

Do not execute a specialist if their domain is entirely absent from the PR.

Unnecessary specialist execution adds latency, increases noise, and wastes
analytical capacity. Routing precision is a measurable quality signal.

---

## Required Routing Inputs

Before generating `review-plan.json`, the orchestrator must have:

- `pr-context.json` (changed files, components, technologies)
- `impact-map.json` (indirect dependencies, callers, consumers)
- Repository discovery results (language, framework, ORM, queue, etc.)

---

## Routing Matrix

Use the following mapping to determine relevance:

| Specialist                    | Route when...                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|
| `code-review-specialist`      | Any logic, algorithm, state, or error handling changes detected               |
| `security-review-specialist`  | SECURITY, AUTHENTICATION, AUTHORIZATION, or TENANT_BOUNDARY triggers         |
| `test-impact-specialist`      | Any behavioral change detected; always pair with code-review-specialist       |
| `architecture-review-specialist` | Cross-module imports, layer violations, or ARCHITECTURE domain detected    |
| `database-review-specialist`  | DATABASE, ORM, MODEL_CHANGE, SCHEMA_CHANGE, MIGRATION, QUERY_CHANGE,         |
|                               | TRANSACTION, INDEX, or FOREIGN_KEY triggers                                   |
| `api-review-specialist`       | API, REST, GRPC, ROUTE, OPENAPI, REQUEST_SCHEMA, RESPONSE_SCHEMA,            |
|                               | HTTP_STATUS, or API_AUTHORIZATION triggers                                    |
| `async-review-specialist`     | BACKGROUND_JOB_CHANGED, or queue-related files/components detected            |

---

## Required review-plan.json Fields

```json
{
  "pr_id": "<integer>",
  "domains": ["<domain_tag>"],
  "risk_triggers": ["<trigger_name>"],
  "selected_reviewers": [
    {
      "reviewer": "<slug>",
      "reason": "<explicit explanation>",
      "triggers": ["<trigger_names>"]
    }
  ],
  "skipped_reviewers": [
    {
      "reviewer": "<slug>",
      "reason": "<explicit explanation>"
    }
  ]
}
```

All seven available specialists must appear in either `selected_reviewers`
or `skipped_reviewers`. No specialist may be silently omitted.

---

## Routing Metrics

After routing, calculate and record:

```
routing_discard_rate = skipped_reviewers / available_reviewers
```

Available reviewers = 7 (constant).

---

## Routing Examples

### Example A: Auth + Route Change

Changed files: `app/routes/users.py`, `app/auth/permissions.py`, `tests/test_users.py`

```
Selected:
  code-review-specialist       — logic changes in routes and permissions
  security-review-specialist   — AUTHENTICATION_CHANGED + AUTHORIZATION_CHANGED
  api-review-specialist        — ROUTE change in routes/users.py
  test-impact-specialist       — behavioral change present

Skipped:
  database-review-specialist   — no schema or migration changes
  architecture-review-specialist — no cross-layer violations detected
  async-review-specialist       — no async or queue components affected
```

### Example B: Migration + Model Change

Changed files: `migrations/021_add_index.py`, `app/models/events.py`, `app/repository/events.py`

```
Selected:
  database-review-specialist   — MIGRATION + MODEL_CHANGE + INDEX triggers
  code-review-specialist       — repository logic changes
  test-impact-specialist       — behavioral change in repository layer

Conditionally selected:
  api-review-specialist        — only if repository changes affect response contracts

Skipped:
  security-review-specialist   — no auth or security-relevant changes
  architecture-review-specialist — no layer violations detected
  async-review-specialist       — no async components affected
```

---

## Routing Disputes

If domain classification is ambiguous, prefer to include the specialist
rather than exclude. Record the uncertainty in the routing reason.

The goal is precision, not minimalism at the cost of missed analysis.

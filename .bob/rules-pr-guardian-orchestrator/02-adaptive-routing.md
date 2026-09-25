# PR Guardian Orchestrator — Adaptive Routing Rules

These rules define how the orchestrator selects and excludes specialist reviewers,
and how agent budget is enforced.

---

## Routing Principles

**No specialist is mandatory unless its routing triggers are satisfied.**

Do not execute a specialist if their domain is entirely absent from the PR.
Unnecessary specialist execution adds latency, increases noise, and wastes
analytical capacity. Routing precision is a measurable quality signal.

---

## Required Routing Inputs

Before generating `review-plan.json`, the orchestrator must have:

- `pr-context.json` (changed files, components, technologies)
- `impact-map.json` (indirect dependencies, callers, consumers)
- Repository discovery results (language, framework, ORM, queue, etc.)
- Deterministic pre-scan results (ruff, bandit, pytest, pip-audit as applicable)

---

## Step 1: Risk Level Classification

Before selecting any reviewer, classify the PR's global risk level.

| Level    | Signals                                                                              |
|----------|--------------------------------------------------------------------------------------|
| TRIVIAL  | Only docs/comments/formatting/metadata changed; no logic, no config, no tests       |
| LOW      | Small isolated change; no auth, no DB, no API, no queue, no arch signals            |
| MEDIUM   | Route, business rule, query, or test changed; 1–2 domain triggers max               |
| HIGH     | Auth/authz changed, DB migration, public API breaking change, queue semantics        |
| CRITICAL | Tenant isolation, privileged authorization, cryptography, cross-service security     |

Record in `review-plan.json` as `risk_level`.

---

## Step 2: Agent Budget

The risk level sets maximum reviewers:

| Risk Level | max_reviewers | max_verifiers |
|------------|---------------|---------------|
| TRIVIAL    | 0             | 0             |
| LOW        | 1             | 0             |
| MEDIUM     | 2             | 1             |
| HIGH       | 3             | 1             |
| CRITICAL   | 4             | 1             |

Record in `review-plan.json` as `agent_budget`.

---

## Step 3: Specialist Routing Triggers

Apply the routing matrix. A specialist is selected only when its triggers fire:

| Specialist                        | Route ONLY when                                                                    |
|-----------------------------------|------------------------------------------------------------------------------------|
| `code-review-specialist`          | Any logic, algorithm, state, or error handling changes (APPLICATION_LOGIC domain) |
|                                   | **Skip for:** documentation-only, formatting-only, configuration metadata without behavioral change |
| `security-review-specialist`      | AUTHENTICATION_CHANGED, AUTHORIZATION_CHANGED, TENANT_BOUNDARY_CHANGED,           |
|                                   | SECRET_HANDLING_CHANGED, FILE_UPLOAD_CHANGED, EXTERNAL_REQUEST_CHANGED,            |
|                                   | CRYPTOGRAPHY_CHANGED, UNTRUSTED_INPUT_CHANGED, DEPENDENCY_SECURITY_RISK            |
| `test-impact-specialist`          | Multiple behaviors affected, complex coverage, integration boundaries changed,     |
|                                   | risk is HIGH/CRITICAL, OR code reviewer explicitly escalates a test coverage gap   |
|                                   | **Skip for:** simple PRs; code-review-specialist handles basic test impact         |
| `architecture-review-specialist`  | New module boundary, new service, new abstraction, dependency direction change,    |
|                                   | cross-layer access, large refactoring, module movement detected in impact map      |
|                                   | **Skip for:** small bug fix, simple route/query change, small test change, docs    |
| `database-review-specialist`      | DATABASE_SCHEMA_CHANGED, DATABASE_QUERY_CHANGED, MIGRATION present,               |
|                                   | ORM model changed, transaction/index/constraint/foreign_key touched                |
| `api-review-specialist`           | PUBLIC_API_CHANGED, route files modified, request/response schema changed,         |
|                                   | HTTP status codes changed, OpenAPI spec changed, API auth/authz changed            |
| `async-review-specialist`         | BACKGROUND_JOB_CHANGED, tasks/workers/queue files changed,                        |
|                                   | RQ/Celery/Kafka/RabbitMQ components in changed files or impact map                 |

---

## Step 4: Base Reviewer — code-review-specialist

`code-review-specialist` is the default primary reviewer for any functional change.

For PRs at risk level LOW–MEDIUM, the code reviewer also evaluates:
- Basic test impact (existing coverage for changed symbols)
- Basic behavioral regression indicators

This avoids spawning `test-impact-specialist` for simple PRs.

`code-review-specialist` is **skipped** for:
- TRIVIAL PRs (documentation, formatting, non-functional metadata)
- Configuration metadata changes with no behavioral effect

---

## Step 5: Budget Enforcement

After selecting candidates, enforce the budget:

1. List all triggered specialists in priority order:
   ```
   1. security boundary (security-review-specialist)
   2. data integrity (database-review-specialist)
   3. public API compatibility (api-review-specialist)
   4. async reliability (async-review-specialist)
   5. architecture (architecture-review-specialist)
   6. test specialization (test-impact-specialist)
   ```
   Note: `code-review-specialist` occupies slot 0 (always first if applicable).

2. If candidate count ≤ `max_reviewers`: select all candidates.

3. If candidate count > `max_reviewers`: select top N by priority order, record the rest as:
   ```json
   {
     "reviewer": "<slug>",
     "reason": "Relevant but not selected due to agent budget; lower risk than active reviewers."
   }
   ```

---

## Required review-plan.json Fields

```json
{
  "pr_id": "<integer>",
  "risk_level": "TRIVIAL | LOW | MEDIUM | HIGH | CRITICAL",
  "agent_budget": {
    "max_reviewers": "<integer>",
    "max_verifiers": "<integer>"
  },
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
  ],
  "routing_discard_rate": "<float>"
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

### Example A: TRIVIAL — Documentation Only

Changed files: `README.md`, `docs/setup.md`

```
risk_level: TRIVIAL
agent_budget: { max_reviewers: 0, max_verifiers: 0 }

Selected: (none)
Skipped:
  code-review-specialist         — documentation-only change, no behavioral logic
  security-review-specialist     — no security triggers
  test-impact-specialist         — no behavioral change
  architecture-review-specialist — no structural change
  database-review-specialist     — no schema/query/migration changes
  api-review-specialist          — no route or contract changes
  async-review-specialist        — no queue/worker changes

routing_discard_rate: 1.0
```

### Example B: LOW — Small Bug Fix

Changed files: `app/utils.py`, `tests/test_utils.py`

```
risk_level: LOW
agent_budget: { max_reviewers: 1, max_verifiers: 0 }

Selected:
  code-review-specialist       — logic change in utility function

Skipped:
  security-review-specialist   — no auth/security triggers
  test-impact-specialist       — simple change; code reviewer handles basic test impact
  architecture-review-specialist — no cross-module changes
  database-review-specialist   — no DB changes
  api-review-specialist        — no route/API changes
  async-review-specialist      — no async/queue changes

routing_discard_rate: 0.86
```

### Example C: MEDIUM — Authorization Change

Changed files: `app/auth.py`, `app/routes/users.py`

```
risk_level: HIGH  (auth triggers elevate from MEDIUM to HIGH)
agent_budget: { max_reviewers: 3, max_verifiers: 1 }

Selected:
  code-review-specialist       — logic changes in auth and routes
  security-review-specialist   — AUTHENTICATION_CHANGED + AUTHORIZATION_CHANGED

Skipped:
  test-impact-specialist       — not triggered; code reviewer handles basic test impact
  architecture-review-specialist — no cross-module boundary violations
  database-review-specialist   — no schema/migration changes
  api-review-specialist        — route changed but no contract break detected; code reviewer covers
  async-review-specialist      — no async changes

routing_discard_rate: 0.71
```

### Example D: MEDIUM — Database Migration

Changed files: `migrations/021_add_index.py`, `app/models/events.py`, `app/repository/events.py`

```
risk_level: HIGH
agent_budget: { max_reviewers: 3, max_verifiers: 1 }

Selected:
  code-review-specialist       — repository logic changes
  database-review-specialist   — MIGRATION + MODEL_CHANGE + INDEX triggers

Skipped:
  security-review-specialist   — no auth or security-relevant changes
  test-impact-specialist       — not triggered; code reviewer handles basic test impact
  architecture-review-specialist — no layer violations
  api-review-specialist        — no route/API contract changes
  async-review-specialist      — no async changes

routing_discard_rate: 0.71
```

### Example E: MEDIUM — Queue Change

Changed files: `tasks/email.py`, `workers/processor.py`

```
risk_level: MEDIUM
agent_budget: { max_reviewers: 2, max_verifiers: 1 }

Selected:
  code-review-specialist       — logic changes in tasks and workers
  async-review-specialist      — BACKGROUND_JOB_CHANGED trigger

Skipped:
  security-review-specialist   — no auth/security triggers
  test-impact-specialist       — not triggered; code reviewer handles basic test impact
  architecture-review-specialist — no cross-module changes
  database-review-specialist   — no migration/schema changes
  api-review-specialist        — no route/API changes

routing_discard_rate: 0.71
```

---

## Routing Disputes

If domain classification is ambiguous, prefer to include the specialist
only if the total would remain within budget. If over budget, use the
priority order to decide. Record the uncertainty in the routing reason.

The goal is precision within budget, not minimalism at the cost of missed analysis.

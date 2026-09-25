---
name: adaptive-routing
description: >
  Selects the relevant specialist reviewers for a PR based on changed files,
  detected technologies, domain classification, and risk triggers. Produces
  review-plan.json with explicit routing decisions and reasons.
---

# Adaptive Routing

## Purpose

Determine exactly which specialist reviewers should execute for this PR and
which should be skipped — with explicit justification for every decision.

Unnecessary reviewer execution increases noise, duration, and the risk of
false positives. Routing precision is a first-class quality signal.

## Core Question

> Which specialists are relevant to this PR, and why?

## When to Use

Activate after both `pr-understanding` and `change-impact` have completed
and their output files are available. This skill is the gate before
specialist execution begins.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`

## Phases

### Phase 1: Domain Classification

Using the changed files, changed components, and technologies from `pr-context.json`,
assign domain tags to the PR:

```
APPLICATION_LOGIC      — functions, classes, business rules modified
SECURITY               — auth/authz/crypto/secrets touched
AUTHENTICATION         — login, session, token, credential handling
AUTHORIZATION          — permission checks, role enforcement
API                    — routes, serializers, HTTP status codes, OpenAPI
DATABASE               — models, migrations, ORM queries, transactions
BACKGROUND_JOB         — tasks, workers, queues, consumers
CONCURRENCY            — threading, async/await, shared state
CONFIGURATION          — env vars, feature flags, settings
DEPENDENCY             — package manifest changes
TESTING                — test files primarily changed
ARCHITECTURE           — cross-module imports, layer structure
OBSERVABILITY          — logging, metrics, tracing
PERFORMANCE            — caching, query optimization
```

### Phase 2: Risk Trigger Detection

Scan the diff and impact map for explicit risk signals:

```
AUTHENTICATION_CHANGED       — auth middleware, login handlers, token logic modified
AUTHORIZATION_CHANGED        — permission decorators, role checks, ACL logic modified
TENANT_BOUNDARY_CHANGED      — tenant filter, org_id isolation, multi-tenant scope modified
DATABASE_SCHEMA_CHANGED      — table/column/constraint definitions modified
DATABASE_QUERY_CHANGED       — ORM queries, raw SQL, query builders modified
PUBLIC_API_CHANGED           — externally visible route or response schema modified
BACKGROUND_JOB_CHANGED       — task definitions, worker config, queue routing modified
DEPENDENCY_CHANGED           — requirements.txt, pyproject.toml, package.json changed
SECRET_HANDLING_CHANGED      — secrets, keys, credentials, env access modified
FILE_UPLOAD_CHANGED          — file ingestion, storage, multipart handling modified
EXTERNAL_REQUEST_CHANGED     — HTTP client, webhook, third-party integration modified
CONCURRENCY_CHANGED          — threading primitives, async patterns, shared state modified
```

### Phase 3: Specialist Routing Decision

Apply the routing matrix:

| Specialist | Route when |
|---|---|
| `code-review-specialist` | APPLICATION_LOGIC or any behavioral change detected |
| `security-review-specialist` | SECURITY, AUTHENTICATION, AUTHORIZATION, or TENANT_BOUNDARY_CHANGED |
| `test-impact-specialist` | Any behavioral change; always pair with code-review-specialist |
| `architecture-review-specialist` | ARCHITECTURE domain or cross-layer imports in impact map |
| `database-review-specialist` | DATABASE domain or DATABASE_SCHEMA_CHANGED / DATABASE_QUERY_CHANGED |
| `api-review-specialist` | API domain or PUBLIC_API_CHANGED |
| `async-review-specialist` | BACKGROUND_JOB domain or BACKGROUND_JOB_CHANGED |

For each specialist, write either:
- `selected_reviewers` entry with `reason` and `triggers`
- `skipped_reviewers` entry with `reason`

All 7 specialists must appear in one of the two lists. No silent omissions.

### Phase 4: Routing Metrics

Calculate:
```
routing_discard_rate = len(skipped_reviewers) / 7
```

Record this in the plan.

## Deterministic Tools & Evidence

Routing decisions are grounded in:
- File paths from `pr-context.json` matched against component patterns
- Risk triggers derived from diff content and component names
- Technology stack from `pr-context.json` technologies object

No guessing. If a domain is ambiguous, prefer inclusion over exclusion
and document the uncertainty.

## Canonical Output

File: `reports/plans/<pr-id>/review-plan.json`

```json
{
  "pr_id": "<integer>",
  "domains": ["<domain_tag>"],
  "risk_triggers": ["<trigger_name>"],
  "selected_reviewers": [
    {
      "reviewer": "<slug>",
      "reason": "<explicit explanation referencing specific files or triggers>",
      "triggers": ["<trigger_name>"]
    }
  ],
  "skipped_reviewers": [
    {
      "reviewer": "<slug>",
      "reason": "<explicit explanation of why this domain is absent>"
    }
  ],
  "routing_discard_rate": "<float>",
  "repository_profile": {
    "language": "<string>",
    "framework": "<string>",
    "test_framework": "<string>",
    "database": "<string>",
    "orm": "<string>",
    "queue": "<string>"
  }
}
```

## Routing Examples

### Example: Auth + API Change

```json
{
  "selected_reviewers": [
    {
      "reviewer": "code-review-specialist",
      "reason": "app/auth/permissions.py contains modified business logic",
      "triggers": ["AUTHENTICATION_CHANGED", "AUTHORIZATION_CHANGED"]
    },
    {
      "reviewer": "security-review-specialist",
      "reason": "Permission checks modified — AUTHORIZATION_CHANGED trigger",
      "triggers": ["AUTHORIZATION_CHANGED", "AUTHENTICATION_CHANGED"]
    },
    {
      "reviewer": "api-review-specialist",
      "reason": "app/routes/users.py modified — PUBLIC_API_CHANGED trigger",
      "triggers": ["PUBLIC_API_CHANGED"]
    },
    {
      "reviewer": "test-impact-specialist",
      "reason": "Behavioral changes in auth and routing require coverage verification",
      "triggers": ["AUTHENTICATION_CHANGED"]
    }
  ],
  "skipped_reviewers": [
    {
      "reviewer": "database-review-specialist",
      "reason": "No migration, model, or query files changed"
    },
    {
      "reviewer": "architecture-review-specialist",
      "reason": "No cross-module boundary violations detected in impact map"
    },
    {
      "reviewer": "async-review-specialist",
      "reason": "No task, worker, or queue files changed"
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Domain is ambiguous | Prefer inclusion; document uncertainty in reason field |
| Impact map is empty | Proceed with file-based routing only; note limitation |
| Unknown technology | Route conservatively (include code and security reviewers) |

## What This Skill Must Not Do

- Skip a specialist without an explicit written reason
- Route based on assumptions about the PR without reading the context files
- Add specialists that have no connection to any detected domain or trigger
- Perform any analysis that belongs to a specialist reviewer

## Completion Criteria

- `review-plan.json` is written to `reports/plans/<pr-id>/`
- All domains are classified and recorded
- All risk triggers are identified and recorded
- All 7 specialists appear in either `selected_reviewers` or `skipped_reviewers`
- Every routing decision has an explicit, grounded reason
- `routing_discard_rate` is calculated and recorded

# PR Guardian — Planning Rules

These rules govern every agent operating in Plan mode within the PR Guardian harness.
They are global and apply before any mode-specific rules.

---

## 1. Intent First

Before selecting reviewers or decomposing tasks, extract and summarize the PR intent.

Collect:

```
title
description
commits
diff
base SHA
head SHA
purpose
components
declared scope
observed scope
```

Produce a concise summary of **what this PR is trying to change and why** before
proceeding to domain classification or routing decisions.

---

## 2. Domain Classification

After understanding the PR, classify it using the following domain tags.
Multiple domains may apply.

```
APPLICATION_LOGIC      — business logic, algorithms, state management
SECURITY               — any security-relevant change
AUTHENTICATION         — login, session, token, credential handling
AUTHORIZATION          — permissions, roles, access control
API                    — REST/gRPC routes, request/response schemas, OpenAPI
DATABASE               — schema, migrations, queries, ORM, transactions
BACKGROUND_JOB         — async tasks, workers, queues, event consumers
CONCURRENCY            — threading, async/await, shared state
CONFIGURATION          — env vars, feature flags, settings files
DEPENDENCY             — package additions, removals, version bumps
TESTING                — test files, test fixtures, test utilities
ARCHITECTURE           — cross-module structure, layering, boundaries
OBSERVABILITY          — logging, metrics, tracing, alerting
PERFORMANCE            — caching, query optimization, algorithmic complexity
```

---

## 3. Risk Trigger Detection

Identify explicit risk signals in the diff that require heightened scrutiny:

```
AUTHENTICATION_CHANGED       — auth logic modified
AUTHORIZATION_CHANGED        — permission checks added, removed, or altered
TENANT_BOUNDARY_CHANGED      — multi-tenant isolation logic modified
DATABASE_SCHEMA_CHANGED      — table/column/constraint definitions modified
DATABASE_QUERY_CHANGED       — raw queries or ORM queries modified
PUBLIC_API_CHANGED           — externally visible route or schema changed
BACKGROUND_JOB_CHANGED       — async task, worker, or queue config changed
DEPENDENCY_CHANGED           — package added, removed, or version bumped
SECRET_HANDLING_CHANGED      — secrets, keys, or credential paths modified
FILE_UPLOAD_CHANGED          — file ingestion logic modified
EXTERNAL_REQUEST_CHANGED     — HTTP client, webhook, or third-party call modified
CONCURRENCY_CHANGED          — threading model, async primitives, or locks modified
```

All detected risk triggers must be recorded in `review-plan.json`.

---

## 4. Adaptive Routing

Specialist reviewers are only activated when relevant.

Rules:

- Do NOT activate a specialist whose domains are entirely absent from the PR.
- Document every routing decision with an explicit reason.
- Record both `selected_reviewers` and `skipped_reviewers` with reasons.
- Use the `adaptive-routing` skill to produce `review-plan.json`.

Available specialists:

```
code-review-specialist
security-review-specialist
test-impact-specialist
architecture-review-specialist
database-review-specialist
api-review-specialist
async-review-specialist
```

---

## 5. Verification Planning

Before launching specialists, pre-plan which findings may require verification:

- CRITICAL and HIGH findings always require verification attempt.
- MEDIUM findings should be verified when the cost is low.
- Identify which verification strategies are likely applicable:
  - STATIC_ANALYSIS, TARGETED_TEST, INTEGRATION_TEST,
    CONFIG_INSPECTION, DEPENDENCY_ANALYSIS, CODE_PATH_PROOF, MANUAL_EVIDENCE.

---

## 6. Artifact Planning

The plan phase must identify all output artifacts that will be produced:

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json
reports/findings/<pr-id>/<reviewer>.json  (one per selected reviewer)
reports/verification/<pr-id>/verification-results.json
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md
reports/runs/<pr-id>/run-manifest.json
```

---

## 7. No Pre-Judging

The plan phase must not pre-assign findings or assume vulnerabilities
before specialist reviewers have executed.

Planning is about routing, not analysis.

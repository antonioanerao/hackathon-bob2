---
name: adaptive-routing
description: >
  Selects the relevant specialist reviewers for a PR based on changed files,
  detected technologies, domain classification, risk triggers, and agent budget.
  Produces review-plan.json with risk_level, agent_budget, and explicit routing
  decisions. No specialist is mandatory unless its routing triggers are satisfied.
---

# Adaptive Routing

## Purpose

Determine exactly which specialist reviewers should execute for this PR and
which should be skipped — respecting the agent budget, with explicit justification
for every decision.

**No specialist is mandatory unless its routing triggers are satisfied.**

Unnecessary reviewer execution adds latency, increases noise, and increases cost.
Routing precision is a first-class quality signal.

## Core Questions

> Which specialists are relevant to this PR, and why?

> How many specialists does this PR's risk level justify?

## When to Use

Activate after both `pr-understanding` and `change-impact` have completed,
the deterministic pre-scan has run, and all output files are available.
This skill is the gate before specialist execution begins.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- Deterministic pre-scan results (already in context, not re-run)

## Phases

### Phase 1: Risk Level Classification

Before selecting any reviewer, determine the PR's global risk level.

| Level    | Classification Criteria                                                              |
|----------|--------------------------------------------------------------------------------------|
| TRIVIAL  | Only documentation, comments, formatting, or non-functional metadata changed.        |
|          | No logic, no test changes, no configuration with behavioral impact.                  |
| LOW      | Small, isolated functional change. No security, DB, API, queue, or arch triggers.   |
| MEDIUM   | Functional change touching a specific domain: route, business rule, query, or test.  |
|          | At most 1–2 domain triggers. No auth/security boundary.                              |
| HIGH     | Authentication or authorization changed, DB migration present, public API breaking   |
|          | change, queue semantics changed, or security boundary touched.                       |
| CRITICAL | Tenant isolation, privileged authorization, cryptography, cross-service security,   |
|          | data corruption risk, or critical infrastructure change.                             |

Record in `review-plan.json` as `risk_level`.

---

### Phase 2: Agent Budget

The risk level sets the maximum number of specialist reviewers:

| Risk Level | max_reviewers | max_verifiers |
|------------|---------------|---------------|
| TRIVIAL    | 0             | 0             |
| LOW        | 1             | 0             |
| MEDIUM     | 2             | 1             |
| HIGH       | 3             | 1             |
| CRITICAL   | 4             | 1             |

**The budget is a ceiling, not a target.** If fewer specialists are triggered,
spawn only the relevant ones.

Record in `review-plan.json` as `agent_budget`.

---

### Phase 3: Domain Classification

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

---

### Phase 4: Risk Trigger Detection

Scan the diff and impact map for explicit risk signals:

```
AUTHENTICATION_CHANGED       — auth middleware, login handlers, token logic modified
AUTHORIZATION_CHANGED        — permission decorators, role checks, ACL logic modified
TENANT_BOUNDARY_CHANGED      — tenant filter, org_id isolation, multi-tenant scope modified
DEPENDENCY_SECURITY_RISK     — security-relevant package added or updated
DATABASE_SCHEMA_CHANGED      — table/column/constraint definitions modified
DATABASE_QUERY_CHANGED       — ORM queries, raw SQL, query builders modified
PUBLIC_API_CHANGED           — externally visible route or response schema modified
BACKGROUND_JOB_CHANGED       — task definitions, worker config, queue routing modified
DEPENDENCY_CHANGED           — requirements.txt, pyproject.toml, package.json changed
SECRET_HANDLING_CHANGED      — secrets, keys, credentials, env access modified
FILE_UPLOAD_CHANGED          — file ingestion, storage, multipart handling modified
EXTERNAL_REQUEST_CHANGED     — HTTP client, webhook, third-party integration modified
CRYPTOGRAPHY_CHANGED         — encryption, hashing, signing logic modified
UNTRUSTED_INPUT_CHANGED      — input parsing/validation at trust boundary modified
CONCURRENCY_CHANGED          — threading primitives, async patterns, shared state modified
```

---

### Phase 5: Specialist Routing Decision

Apply the routing matrix. A specialist is selected only when its triggers fire.

| Specialist                        | Route ONLY when                                                                    |
|-----------------------------------|------------------------------------------------------------------------------------|
| `code-review-specialist`          | APPLICATION_LOGIC or any behavioral change detected                               |
|                                   | **Skip for:** TRIVIAL PRs; formatting/docs/metadata-only changes                  |
| `security-review-specialist`      | AUTHENTICATION_CHANGED, AUTHORIZATION_CHANGED, TENANT_BOUNDARY_CHANGED,           |
|                                   | SECRET_HANDLING_CHANGED, FILE_UPLOAD_CHANGED, EXTERNAL_REQUEST_CHANGED,           |
|                                   | CRYPTOGRAPHY_CHANGED, UNTRUSTED_INPUT_CHANGED, DEPENDENCY_SECURITY_RISK           |
|                                   | **Skip for:** any PR without one of these explicit triggers                        |
| `test-impact-specialist`          | Multiple behaviors affected AND coverage is complex, OR integration boundaries    |
|                                   | changed, OR risk is HIGH/CRITICAL, OR code reviewer escalated a coverage gap      |
|                                   | **Skip for:** simple PRs — code-review-specialist covers basic test impact        |
| `architecture-review-specialist`  | New module boundary, new service, new abstraction, dependency direction change,   |
|                                   | cross-layer access, large refactoring, or module movement in impact map           |
|                                   | **Skip for:** small bug fix, simple route/query/test change, docs, formatting     |
| `database-review-specialist`      | DATABASE_SCHEMA_CHANGED, DATABASE_QUERY_CHANGED, migration files present,        |
|                                   | ORM model changed, transaction/index/constraint/foreign_key touched               |
| `api-review-specialist`           | PUBLIC_API_CHANGED, route files modified, request/response schema changed,        |
|                                   | HTTP status codes changed, OpenAPI spec changed, API-level auth changed           |
| `async-review-specialist`         | BACKGROUND_JOB_CHANGED, tasks/workers/queue files changed,                       |
|                                   | RQ/Celery/Kafka/RabbitMQ components in changed files or impact map                |

#### Role of code-review-specialist as base reviewer

`code-review-specialist` is the baseline for all functional changes.

For PRs at risk level LOW–MEDIUM, the code reviewer also evaluates:
- Basic test coverage for changed symbols (no `test-impact-specialist` needed)
- Basic behavioral regression indicators

This avoids spawning `test-impact-specialist` for simple PRs.

---

### Phase 6: Budget Enforcement

After listing all triggered candidates:

1. If candidate count ≤ `max_reviewers` → select all.

2. If candidate count > `max_reviewers` → prioritize by this order and select the top N:
   ```
   Priority 0 (always first if applicable): code-review-specialist
   Priority 1: security-review-specialist
   Priority 2: database-review-specialist
   Priority 3: api-review-specialist
   Priority 4: async-review-specialist
   Priority 5: architecture-review-specialist
   Priority 6: test-impact-specialist
   ```
   Record the remainder as skipped with reason:
   `"Relevant but not selected due to agent budget; lower risk than active reviewers."`

---

### Phase 7: Routing Metrics

Calculate:
```
routing_discard_rate = len(skipped_reviewers) / 7
```

Record in the plan.

---

## Deterministic Tools & Evidence

Routing decisions are grounded in:
- File paths from `pr-context.json` matched against component patterns
- Risk triggers derived from diff content and component names
- Technology stack from `pr-context.json` technologies object
- Pre-scan results already available in context (not re-run here)

No guessing. If a domain is ambiguous and within budget, prefer inclusion
and document the uncertainty. If over budget, exclude and document.

---

## Canonical Output

File: `reports/plans/<pr-id>/review-plan.json`

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
      "reason": "<explicit explanation referencing specific files or triggers>",
      "triggers": ["<trigger_name>"]
    }
  ],
  "skipped_reviewers": [
    {
      "reviewer": "<slug>",
      "reason": "<explicit explanation of why this domain is absent or budget exhausted>"
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

---

## Routing Scenarios

### Scenario A: Documentation-only PR

```json
{
  "risk_level": "TRIVIAL",
  "agent_budget": { "max_reviewers": 0, "max_verifiers": 0 },
  "selected_reviewers": [],
  "skipped_reviewers": [
    { "reviewer": "code-review-specialist", "reason": "Documentation-only change; no behavioral logic modified" },
    { "reviewer": "security-review-specialist", "reason": "No security triggers present" },
    { "reviewer": "test-impact-specialist", "reason": "No behavioral change; no coverage analysis needed" },
    { "reviewer": "architecture-review-specialist", "reason": "No structural change detected" },
    { "reviewer": "database-review-specialist", "reason": "No migration, model, or query changes" },
    { "reviewer": "api-review-specialist", "reason": "No route or contract changes" },
    { "reviewer": "async-review-specialist", "reason": "No task, worker, or queue changes" }
  ],
  "routing_discard_rate": 1.0
}
```

### Scenario B: Small Bug Fix

```json
{
  "risk_level": "LOW",
  "agent_budget": { "max_reviewers": 1, "max_verifiers": 0 },
  "selected_reviewers": [
    { "reviewer": "code-review-specialist", "reason": "Logic change in app/utils.py", "triggers": ["APPLICATION_LOGIC"] }
  ],
  "skipped_reviewers": [
    { "reviewer": "security-review-specialist", "reason": "No security triggers present" },
    { "reviewer": "test-impact-specialist", "reason": "Simple change; code reviewer handles basic test impact" },
    { "reviewer": "architecture-review-specialist", "reason": "No cross-module changes detected" },
    { "reviewer": "database-review-specialist", "reason": "No DB changes" },
    { "reviewer": "api-review-specialist", "reason": "No route or API contract changes" },
    { "reviewer": "async-review-specialist", "reason": "No async/queue changes" }
  ],
  "routing_discard_rate": 0.86
}
```

### Scenario C: Auth + API Change

```json
{
  "risk_level": "HIGH",
  "agent_budget": { "max_reviewers": 3, "max_verifiers": 1 },
  "selected_reviewers": [
    { "reviewer": "code-review-specialist", "reason": "Logic changes in auth.py and routes/users.py", "triggers": ["APPLICATION_LOGIC"] },
    { "reviewer": "security-review-specialist", "reason": "AUTHENTICATION_CHANGED + AUTHORIZATION_CHANGED triggers", "triggers": ["AUTHENTICATION_CHANGED", "AUTHORIZATION_CHANGED"] }
  ],
  "skipped_reviewers": [
    { "reviewer": "test-impact-specialist", "reason": "Not triggered; code reviewer handles basic test impact for this risk level" },
    { "reviewer": "architecture-review-specialist", "reason": "No cross-module boundary violations in impact map" },
    { "reviewer": "database-review-specialist", "reason": "No schema or migration changes" },
    { "reviewer": "api-review-specialist", "reason": "Route modified but no contract break detected; within code reviewer scope" },
    { "reviewer": "async-review-specialist", "reason": "No async/queue changes" }
  ],
  "routing_discard_rate": 0.71
}
```

---

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Domain is ambiguous and within budget | Prefer inclusion; document uncertainty in reason field |
| Domain is ambiguous and over budget | Exclude lower-priority specialist; document |
| Impact map is empty | Proceed with file-based routing only; note limitation |
| Unknown technology | Route conservatively within budget (include code and security if triggers exist) |

---

## What This Skill Must Not Do

- Skip a specialist without an explicit written reason
- Route based on assumptions without reading the context files
- Add specialists with no connection to any detected domain or trigger
- Execute specialists beyond the agent budget without explicit justification
- Spawn specialists for PR understanding, change impact, or repository discovery
- Perform any analysis that belongs to a specialist reviewer

---

## Completion Criteria

- `review-plan.json` is written to `reports/plans/<pr-id>/`
- `risk_level` is classified and recorded
- `agent_budget` is calculated and recorded
- All domains are classified and recorded
- All risk triggers are identified and recorded
- All 7 specialists appear in either `selected_reviewers` or `skipped_reviewers`
- Selected reviewers do not exceed `max_reviewers`
- Every routing decision has an explicit, grounded reason
- `routing_discard_rate` is calculated and recorded

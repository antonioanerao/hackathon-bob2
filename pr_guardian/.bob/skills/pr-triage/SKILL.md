---
name: pr-triage
description: >
  Performs a single-pass PR triage to understand change scope, identify concrete
  risk triggers, estimate review risk, and route the Pull Request only to the
  minimum necessary PR Guardian specialists.
---

# PR Triage

## Purpose

Perform the first reasoning stage of the PR Guardian pipeline.

The triage stage determines:

- what changed
- which technical domains are affected
- which concrete risk triggers are present
- overall review risk
- which specialist reviewers are justified
- which reviewers can be skipped
- the maximum reviewer and verifier budget

Triage is a routing stage.

It is not a specialist review.

It must not create findings.

---

# Core Principles

> Collect once. Reuse everywhere.

> Load knowledge lazily, not globally.

> Explore only when evidence requires it.

> Budget is a ceiling, not a target.

> Route reviewers because of evidence, not because they are available.

The triage stage should produce the smallest safe review plan.

---

# Inputs

Primary input:

- collected PR context

Typical artifact:

`reports/context/<pr-id>/pr-context.json`

The collected context should be treated as the authoritative source for PR
metadata whenever available.

Additional context may include:

- changed-file metadata
- technology hints
- compact change statistics
- base SHA
- head SHA
- repository name
- PR title
- PR description preview
- configured reviewer registry

Do not require the complete PR diff for ordinary triage.

---

# Reviewer Registry

The runtime must provide the available reviewer registry.

Typical configured specialists:

```text
code-review-specialist
security-review-specialist
database-review-specialist
api-review-specialist
async-review-specialist
architecture-review-specialist
```

The runtime registry is authoritative.

Triage may select only reviewers that actually exist in the configured registry.

Do not invent:

- reviewer names
- agents
- skills
- GitHub usernames
- human reviewers

---

# Goal

Determine, with minimum exploration:

1. PR intent
2. changed technical areas
3. directly affected behavior
4. relevant risk triggers
5. risk level
6. reviewer routing
7. agent budget

The output must be sufficient for the orchestrator to continue without
re-performing triage.

---

# Scope

Start from collected PR context.

Use changed filenames, paths, extensions, and metadata as the first routing
signals.

Expand only when a concrete routing ambiguity exists.

Examples:

- a changed file may or may not expose a public route
- an ORM model change may or may not alter schema
- a worker file may or may not contain queue semantics
- a dependency update may or may not affect a sensitive package

Do not perform broad repository exploration.

---

# Discovery Limits

Before routing, default limits are:

- discovery commands: maximum 2
- initial file reads: maximum 3
- discovery fallback: maximum 1

These are ceilings.

Use fewer operations whenever possible.

Expand beyond the default only when:

- there is a specific unresolved risk hypothesis
- the additional inspection can materially change routing
- the reason for expansion is explicit

Do not expand merely to understand the repository generally.

---

# Discovery Strategy

Use the collected PR context first.

Do not rediscover metadata already available.

Do not repeat:

- repository lookup
- PR title lookup
- base/head SHA lookup
- changed file listing
- additions/deletions
- technology hints

unless the original collection artifact is invalid or incomplete.

---

# Minimum Discovery

The triage stage normally needs only:

- PR metadata
- base SHA
- head SHA
- changed files
- changed file count
- compact technology hints
- change size

Avoid loading complete source files unless routing cannot be determined from the
available metadata.

---

# Diff Handling

Do not load or persist the complete diff during triage by default.

The full diff belongs to the specialist stage when reviewers are selected.

Triage may inspect narrowly scoped diff fragments only when required to resolve a
routing ambiguity.

Examples:

- determining whether an API route changed publicly
- confirming that an auth file actually changed authorization behavior
- distinguishing a migration from a comment-only modification

Do not perform general defect discovery from the diff.

---

# Intent

Produce a concise interpretation of the PR's apparent intent.

Target length:

2–4 sentences.

The intent should summarize:

- main change
- relevant affected component
- expected behavioral purpose

Do not speculate about author motivation.

Prefer:

```text
The PR changes the order update endpoint and the service responsible for
persisting order status. It also modifies the request schema used by the public
API.
```

Avoid:

```text
The author is trying to improve the architecture and probably fix several
security issues.
```

---

# Impact Mapping

Build only the minimum impact map needed for routing.

Possible entries include:

- changed symbols
- directly exposed routes
- directly affected models
- direct callers when necessary
- related tests
- queue handlers
- migration objects
- public schemas
- dependency manifests
- module boundaries

Do not attempt a full dependency graph.

---

# Changed Symbols

When available or cheaply derivable, identify changed:

- functions
- methods
- classes
- routes
- schemas
- models
- migration operations
- worker handlers
- configuration entries

Only include symbols that help determine reviewer selection.

---

# Direct Callers

Inspect direct callers only when needed to answer a routing question.

Examples:

- whether changed service behavior is reachable through a public API
- whether changed validation affects an exposed endpoint
- whether a helper is used only internally

Do not recursively explore call graphs.

---

# Exposed Routes

Identify public route changes when supported by evidence.

Relevant examples:

- new endpoint
- removed endpoint
- HTTP method change
- request schema change
- response schema change
- authentication requirement change
- authorization path change

This may justify API and/or security review.

---

# Related Tests

Use directly related tests only as routing evidence when useful.

Examples:

- tests reveal that a changed component is authentication-sensitive
- tests show the code belongs to queue processing
- tests establish that a method is part of a public API contract

Do not perform test analysis during triage.

---

# Risk Model

Valid risk levels:

- `TRIVIAL`
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Risk should reflect review exposure, not predicted defect count.

---

# Risk Table

| Risk | Typical Scope | Max Reviewers | Max Verifiers |
|---|---|---:|---:|
| `TRIVIAL` | docs, comments, metadata, non-behavioral change | 0 | 0 |
| `LOW` | small isolated behavioral change with limited blast radius | 1 | 0 |
| `MEDIUM` | bounded functional change affecting one or more components | 2 | 1 |
| `HIGH` | auth, database, public API, queues, sensitive inputs, dependency or security boundary | 3 | 1 |
| `CRITICAL` | high-impact auth, tenant isolation, cryptography, destructive data, or severe integrity boundary change | 4 | 1 |

The budget is a maximum.

Do not automatically assign the maximum number of reviewers.

---

# TRIVIAL

Use `TRIVIAL` when changes are clearly non-behavioral.

Examples:

- documentation
- comments
- formatting-only metadata
- static text
- non-runtime repository metadata

Do not use `TRIVIAL` if executable behavior changes.

Expected reviewer budget:

```json
{
  "reviewers": 0,
  "verifiers": 0
}
```

---

# LOW

Use `LOW` for small isolated behavioral changes with limited scope.

Examples:

- one helper behavior change
- narrow internal validation
- small deterministic bug fix
- isolated non-sensitive logic adjustment

Expected maximum:

```json
{
  "reviewers": 1,
  "verifiers": 0
}
```

---

# MEDIUM

Use `MEDIUM` when the PR introduces a bounded but meaningful functional change.

Examples:

- service behavior spanning several files
- internal API contract change
- persistence behavior without schema migration
- moderate refactor with behavior implications
- concurrency-sensitive internal change with limited exposure

Maximum:

```json
{
  "reviewers": 2,
  "verifiers": 1
}
```

---

# HIGH

Use `HIGH` when the PR affects important correctness or trust boundaries.

Examples:

- authentication
- authorization
- public API contract
- database migration
- schema change
- queue delivery semantics
- external request handling
- file upload behavior
- secret handling
- dependency security exposure
- untrusted input processing
- significant concurrency behavior

Maximum:

```json
{
  "reviewers": 3,
  "verifiers": 1
}
```

A HIGH risk classification does not imply that a defect exists.

It means the review surface justifies broader specialist coverage.

---

# CRITICAL

Use `CRITICAL` only for changes affecting exceptionally sensitive system
boundaries with potentially severe impact.

Examples:

- tenant isolation
- authorization enforcement for privileged operations
- authentication primitives
- cryptographic key handling
- destructive database migration
- high-impact data integrity controls
- security-critical trust boundary redesign

Maximum:

```json
{
  "reviewers": 4,
  "verifiers": 1
}
```

Do not classify a PR as CRITICAL merely because it touches security-related
files.

The actual changed behavior must justify the classification.

---

# Risk Triggers

Emit only triggers directly supported by the PR.

Valid triggers include:

- `AUTHENTICATION_CHANGED`
- `AUTHORIZATION_CHANGED`
- `TENANT_BOUNDARY_CHANGED`
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
- `DEPENDENCY_SECURITY_RISK`

Do not emit a trigger based solely on filename when the filename is ambiguous.

---

# AUTHENTICATION_CHANGED

Use when the PR changes:

- login flow
- credential validation
- token validation
- session authentication
- identity establishment
- authentication middleware

Do not use for authorization-only changes.

---

# AUTHORIZATION_CHANGED

Use when the PR changes:

- roles
- permissions
- ownership checks
- access-control guards
- authorization middleware
- privileged-operation controls

This normally justifies security review.

---

# TENANT_BOUNDARY_CHANGED

Use when the PR changes:

- tenant filtering
- tenant identifiers
- cross-tenant query scoping
- organization isolation
- account partitioning
- tenant-aware authorization

Treat tenant-boundary changes as highly sensitive.

---

# DATABASE_SCHEMA_CHANGED

Use for:

- migrations
- table changes
- column changes
- constraints
- indexes
- foreign keys
- database types

This normally justifies database review.

---

# DATABASE_QUERY_CHANGED

Use for material changes to:

- ORM query behavior
- raw SQL
- repository query logic
- transaction behavior
- persistence filtering

Do not emit merely because a model file changed.

---

# PUBLIC_API_CHANGED

Use when the externally observable API contract changes.

Examples:

- route
- HTTP method
- request schema
- response schema
- status code behavior
- public parameter
- authentication requirement
- API version

This normally justifies API review.

---

# BACKGROUND_JOB_CHANGED

Use when the PR changes:

- queue consumers
- workers
- scheduled jobs
- retries
- acknowledgments
- idempotency
- background execution

This normally justifies async review.

---

# DEPENDENCY_CHANGED

Use when package dependencies or versions change.

Do not automatically treat every dependency change as HIGH risk.

Evaluate relevance.

---

# DEPENDENCY_SECURITY_RISK

Use only when dependency change evidence indicates security relevance.

Examples:

- security-sensitive dependency
- explicitly vulnerable version
- security advisory context already available

Do not invent CVEs or vulnerability status.

---

# SECRET_HANDLING_CHANGED

Use when the PR changes:

- secret loading
- token storage
- credential handling
- environment secret behavior
- key material

This normally justifies security review.

---

# FILE_UPLOAD_CHANGED

Use when the PR changes:

- upload handling
- file validation
- filename handling
- storage path
- content processing

This usually justifies security review and may justify code review.

---

# EXTERNAL_REQUEST_CHANGED

Use when the PR changes:

- outbound HTTP calls
- URL handling
- remote service interaction
- webhook delivery
- network client behavior

Security review may be justified when attacker-controlled values are involved.

---

# CRYPTOGRAPHY_CHANGED

Use when the PR changes:

- encryption
- signatures
- key generation
- key storage
- hashing used for security
- certificate validation

This normally warrants security review.

---

# UNTRUSTED_INPUT_CHANGED

Use when the PR materially changes processing of:

- HTTP parameters
- request bodies
- file content
- external messages
- user-controlled strings
- webhook payloads

Do not use for harmless parsing changes without a trust boundary.

---

# CONCURRENCY_CHANGED

Use when the PR changes:

- locks
- shared mutable state
- parallel workers
- synchronization
- race-sensitive logic
- concurrent transaction behavior

Code review is usually appropriate.

Async review may also be appropriate when queue workers are involved.

---

# Reviewer Routing

Select only relevant specialists.

Available routing domains:

- `code-review-specialist`
- `security-review-specialist`
- `database-review-specialist`
- `api-review-specialist`
- `async-review-specialist`
- `architecture-review-specialist`

---

# code-review-specialist

Select when the PR materially changes application behavior.

Examples:

- control flow
- state transitions
- business logic
- concurrency
- error handling
- algorithm behavior

Do not automatically select code review for documentation-only changes.

---

# security-review-specialist

Select when the PR changes or materially affects:

- authentication
- authorization
- tenant isolation
- security boundaries
- cryptography
- secrets
- untrusted input
- file uploads
- external requests
- exploit-relevant dependency behavior

Do not select merely because the repository is security-related.

---

# database-review-specialist

Select when the PR changes:

- schema
- migrations
- queries
- transactions
- ORM mappings
- constraints
- indexes
- referential integrity

---

# api-review-specialist

Select when the PR changes:

- public routes
- request schemas
- response schemas
- HTTP methods
- status codes
- OpenAPI definitions
- versioned API behavior
- externally consumed contracts

Do not select for purely internal function APIs.

---

# async-review-specialist

Select when the PR changes:

- queue producers
- queue consumers
- workers
- scheduled background tasks
- retry logic
- delivery semantics
- acknowledgment
- idempotency

---

# architecture-review-specialist

Select when the PR changes:

- module boundaries
- dependency direction
- package relationships
- responsibility ownership
- dependency injection structure
- module initialization
- large architectural refactors

Do not select for every refactor.

The structural effect must be meaningful.

---

# Multiple Reviewers

Select multiple specialists only when the PR spans materially distinct review
domains.

Example:

A public endpoint that writes through a new database migration may justify:

- `api-review-specialist`
- `database-review-specialist`
- `code-review-specialist`

If authorization also changes, security review may outrank a lower-value
specialist within the budget.

---

# Reviewer Priority

If justified reviewers exceed the available budget, prioritize by actual risk.

Default tie-break order:

1. `code-review-specialist`
2. `security-review-specialist`
3. `database-review-specialist`
4. `api-review-specialist`
5. `async-review-specialist`
6. `architecture-review-specialist`

This ordering is only a tie-break rule.

Concrete PR risk should determine priority first.

Example:

A pure authentication PR should prioritize security over generic code review.

Do not mechanically apply the ordering when domain risk clearly differs.

---

# Skipped Reviewers

Record reviewers that were considered but not selected when useful.

Typical reasons:

- domain not affected
- insufficient evidence
- reviewer budget exceeded
- lower-priority overlap
- trivial change
- no behavioral change

Keep reasons to one concise line.

Do not fabricate review activity for skipped reviewers.

---

# Agent Budget

The output must define a budget compatible with the selected risk level.

Recommended structure:

```json
{
  "max_reviewers": 2,
  "max_verifiers": 1
}
```

Budget must not exceed the configured maximum for the assigned risk level.

The orchestrator should validate the budget deterministically.

---

# Verification Budget

The triage stage does not decide which findings will be verified because findings
do not yet exist.

It only defines the maximum verifier capacity.

The orchestrator later decides whether verification is justified.

---

# Outputs

Produce compact structured triage output sufficient for persistence into:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`

The orchestrator owns persistence.

Triage should return structured data, not choose file paths.

---

# pr-context.json

This artifact should primarily preserve collector output.

Do not duplicate the entire impact map or review plan inside it.

Do not place the full diff inside this artifact.

---

# impact-map.json

Keep the impact map compact.

Recommended structure:

```json
{
  "intent": "The PR changes the public order update endpoint and its persistence path.",
  "changed_areas": [
    "api",
    "service",
    "database"
  ],
  "changed_symbols": [
    "update_order"
  ],
  "exposed_routes": [
    "PATCH /api/v1/orders/{id}"
  ],
  "direct_dependencies": [],
  "related_tests": []
}
```

Omit empty optional collections when the schema allows.

---

# review-plan.json

Required fields:

- `risk_level`
- `agent_budget`
- `risk_triggers`
- `selected_reviewers`
- `skipped_reviewers`

Recommended structure:

```json
{
  "risk_level": "HIGH",
  "agent_budget": {
    "max_reviewers": 3,
    "max_verifiers": 1
  },
  "risk_triggers": [
    "PUBLIC_API_CHANGED",
    "AUTHORIZATION_CHANGED"
  ],
  "selected_reviewers": [
    {
      "reviewer": "security-review-specialist",
      "reason": "Authorization behavior changed on a public update endpoint."
    },
    {
      "reviewer": "api-review-specialist",
      "reason": "The public endpoint request contract changed."
    }
  ],
  "skipped_reviewers": [
    {
      "reviewer": "database-review-specialist",
      "reason": "No schema, query, migration, or transaction change is present."
    }
  ]
}
```

If the runtime expects reviewer names as plain arrays, preserve that schema.

Do not change the orchestrator's canonical schema arbitrarily.

---

# Output Compactness

Keep outputs compact.

Guidelines:

- intent: 2–4 sentences maximum
- reviewer reason: one line
- risk trigger list: only supported triggers
- no duplicate metadata
- no full diff
- no specialist reasoning
- no findings
- omit empty optional structures where supported

The triage output is machine-oriented.

---

# Risk Evidence

Every non-trivial risk level should be explainable from concrete PR evidence.

Examples:

```text
HIGH because authorization middleware and a public endpoint changed.
```

```text
MEDIUM because the PR modifies internal service behavior across three directly
related files but does not alter a public or security boundary.
```

Do not classify risk using generic statements such as:

```text
This seems complex.
```

---

# Triage Is Not Review

Triage must not emit statements such as:

```text
The endpoint is vulnerable to authorization bypass.
```

That is a specialist finding.

Triage may instead state:

```text
Authorization behavior changed on a public endpoint; security review is required.
```

Separate risk routing from defect claims.

---

# No-Finding Rule

Triage never returns findings.

The only analytical outputs are:

- context interpretation
- impact map
- risk
- triggers
- reviewer selection
- reviewer skip decisions
- budget

---

# Failure Handling

## Missing PR Context

If minimum PR context is unavailable:

- do not guess
- request or trigger the configured collection fallback
- stop if the required context still cannot be established

---

## Unknown Reviewer

If the desired reviewer is not in the runtime registry:

- do not invent or substitute another reviewer silently
- record the capability gap if the output schema supports it
- route only to available relevant reviewers

---

## Ambiguous Change

If routing cannot be determined:

- perform one targeted discovery step
- inspect only the smallest relevant artifact
- make the routing decision
- stop exploration

Do not broaden into general repository analysis.

---

# Must Not

Do not:

- load specialist skills
- load verifier skill
- perform specialist review
- create findings
- verify findings
- spawn reviewers
- execute tests
- execute scanners
- run broad static analysis
- inspect unrelated files
- store the full diff
- rediscover metadata already collected
- perform broad repository search
- recursively map call graphs
- invent changed symbols
- invent routes
- invent risk triggers
- invent reviewer names
- invent dependency vulnerabilities
- invent CVEs
- infer security defects from filenames alone
- use the full reviewer budget unnecessarily
- modify production code
- commit
- push
- merge
- publish

---

# Done When

Triage is complete when:

- PR intent is understood sufficiently for routing
- relevant change areas are identified
- impact map contains only routing-relevant information
- supported risk triggers are identified
- one valid risk level is assigned
- agent budget is within allowed limits
- selected reviewers are justified and registered
- skipped reviewers are accounted for where useful
- no specialist review has been performed
- the result is ready for orchestrator validation and persistence

At that point, return control to the orchestrator.

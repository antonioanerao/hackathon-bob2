````
---
name: api-review
description: >
  Reviews API changes for concrete contract regressions, HTTP semantic errors,
  validation gaps, authorization problems, specification mismatches, and
  backward-compatibility risks.
---

# API Review

## Purpose

Review API-related changes introduced or affected by the Pull Request.

The goal is to identify concrete, evidence-backed API defects or compatibility
regressions.

Do not perform general code review.

Do not report hypothetical issues that are not supported by the supplied change
or directly related repository context.

---

## Use When

Activate this skill when the Pull Request changes one or more of the following:

- routes
- endpoints
- controllers
- handlers
- request models
- response models
- serializers
- validation rules
- query parameters
- path parameters
- HTTP methods
- HTTP status codes
- headers
- authentication requirements
- authorization checks
- API versioning
- OpenAPI or Swagger definitions
- public API contracts
- externally consumed integration endpoints

---

## Primary Review Goals

Determine whether the PR introduces or exposes:

- breaking API changes
- incorrect request contracts
- incorrect response contracts
- HTTP semantic regressions
- validation gaps
- authorization failures
- authentication inconsistencies
- OpenAPI/specification mismatches
- backward-compatibility failures
- inconsistent versioning behavior
- contract implementation divergence

---

# Review Scope

Start from the changed API code.

Expand scope only when necessary to confirm or refute a concrete hypothesis.

Relevant expansion may include:

- directly referenced request models
- directly referenced response models
- validation schemas
- authorization middleware
- authentication middleware
- route registration
- OpenAPI definitions
- direct service calls affecting response behavior
- directly related tests
- versioning configuration

Do not scan unrelated API modules.

---

# Contract Review

Inspect changed API behavior for compatibility.

Check whether the PR changes:

- endpoint path
- HTTP method
- request body structure
- required fields
- optional fields
- field names
- field types
- response structure
- response field names
- response field types
- status codes
- headers
- authentication requirements
- authorization requirements
- pagination behavior
- filtering behavior
- versioning behavior

---

# Breaking Change Examples

Concrete examples include:

- endpoint removed
- endpoint renamed
- route moved without compatibility layer
- HTTP method changed
- request field removed
- request field renamed
- optional request field changed to required
- response field removed
- response field renamed
- field type changed incompatibly
- response envelope changed
- success status changed incompatibly
- error status changed incompatibly
- authentication newly required
- authentication unexpectedly removed
- authorization requirement changed
- query parameter semantics changed
- pagination defaults changed in a way that alters consumer behavior
- versioned endpoint behavior changed without corresponding version change

Do not report a breaking change unless the changed contract is concretely
established.

---

# HTTP Semantics

Review whether HTTP behavior matches the actual operation.

Check:

- HTTP method
- success status code
- error status code
- idempotency expectations
- safe-method semantics
- content type
- request body usage
- response body behavior
- resource creation semantics
- resource deletion semantics
- update semantics
- redirects when applicable
- cache-related headers when directly relevant

Examples of concrete problems:

- using `GET` for a state-changing operation
- returning `200` where the implementation creates a new resource but contract
  expects creation semantics
- returning success when validation failed
- returning inconsistent error codes for the same contract condition
- accepting a body on an endpoint whose framework/router does not process it as expected

Do not report HTTP preferences that do not create practical contract impact.

---

# Request Validation

Check whether incoming data is validated consistently with the API contract.

Review:

- required fields
- field types
- allowed values
- length limits
- numeric ranges
- formats
- nullability
- query parameters
- path parameters
- enum handling
- unknown fields
- nested structures

Look for concrete cases where invalid input can reach application logic because a
required validation step was removed, bypassed, or made inconsistent.

Do not report generic "input should be validated" findings without identifying
the specific missing or incorrect validation.

---

# Response Validation

Check whether returned data matches the documented or expected contract.

Review:

- response field names
- field types
- nullability
- required response fields
- response envelopes
- collection structures
- pagination metadata
- error structures
- status/body consistency

A finding should identify the exact mismatch.

---

# Authentication Review

Check whether changed routes correctly enforce authentication requirements.

Consider:

- unauthenticated route exposure
- accidental removal of authentication middleware
- inconsistent authentication decorators
- token requirement changes
- route registration that bypasses existing authentication layers

Do not assume authentication is absent without checking the relevant route or
middleware path.

---

# Authorization Review

Check whether authenticated users are authorized for the requested action.

Consider:

- role checks
- ownership checks
- tenant checks
- resource-level permissions
- operation-specific permissions
- administrative boundaries

Trace the relevant path when necessary:

```text
request
  → route
  → authentication
  → authorization
  → handler/service
  → protected resource
```

Report only concrete authorization regressions.

Security-specific exploitation details may be left to the security specialist
unless the API contract impact itself is distinct.

---

# API Versioning

When versioned APIs are affected, inspect whether the change is compatible with
the declared versioning strategy.

Check:

- versioned paths
- versioned headers
- media types
- schema versions
- deprecation behavior
- compatibility guarantees

A breaking change to a stable API version is relevant when supported by
evidence.

Do not infer undocumented compatibility guarantees.

---

# OpenAPI / Swagger Review

When API specification files are changed or available, compare implementation
and specification.

Check for:

- route mismatch
- HTTP method mismatch
- request schema mismatch
- response schema mismatch
- status-code mismatch
- parameter mismatch
- authentication/security scheme mismatch
- required-field mismatch
- field-type mismatch

Possible directions:

```text
implementation changed, specification not updated
```

or:

```text
specification changed, implementation not updated
```

Report only when the mismatch is concrete.

---

# Before / After Analysis

When evaluating compatibility, prefer explicit before/after evidence.

For example:

```text
Before:
POST /api/v1/users accepted `email` as optional.

After:
The request model marks `email` as required.
```

Then explain the practical effect.

Avoid statements such as:

```text
This may break clients.
```

unless the concrete contract change is shown.

Prefer:

```text
Existing callers that omit `email` will now receive validation failure.
```

when that behavior is directly supported.

---

# Consumer Impact

Do not invent consumers.

Valid consumer evidence may come from:

- directly referenced frontend code
- client SDK
- integration code
- API tests
- OpenAPI contract
- documented public contract
- explicit repository usage

If no consumer is known, describe the contract impact itself rather than
inventing affected systems.

Example:

```text
The response no longer contains `external_id`, which is a breaking response
contract change for callers depending on the previous schema.
```

Do not claim a specific application is broken unless evidence exists.

---

# Finding Gate

Emit a finding only when all of the following are true:

1. the issue is introduced, exposed, or materially affected by the PR
2. the API behavior is concretely identifiable
3. evidence exists in the supplied change or narrowly related context
4. practical contract or security impact exists
5. the issue is not merely stylistic or preferential

Do not emit findings for:

- API naming preferences
- style
- formatting
- documentation wording
- generic REST best practices without impact
- speculative consumers
- hypothetical future compatibility
- optional improvements
- missing tests without demonstrated API risk
- pre-existing API issues unrelated to the PR

---

# Evidence Requirements

Every finding must include:

- changed file
- relevant line or location
- affected route, endpoint, or schema
- concrete evidence
- before/after behavior when applicable
- practical impact
- actionable recommendation

When applicable, include:

- HTTP method
- route path
- status code
- request field
- response field
- schema name
- authorization boundary

---

# Targeted Confirmation

Before emitting a finding, perform one targeted inspection when it can directly
confirm or refute the hypothesis.

Examples:

- inspect the referenced request schema
- inspect route registration
- inspect auth middleware
- inspect OpenAPI entry
- inspect directly related serializer
- inspect direct caller or client usage

Do not emit a speculative finding when a single targeted read could resolve it.

---

# Relationship With Security Review

API Review and Security Review may inspect overlapping areas.

API Review should focus on:

- API contract
- route-level auth behavior
- externally observable HTTP behavior
- validation behavior
- specification consistency

Security Review should focus on:

- exploitability
- attack paths
- privilege escalation
- tenant isolation
- injection
- security sinks

Do not duplicate a security finding unless there is a distinct API contract
impact.

---

# Severity Guidance

Use severity based on practical impact.

## LOW

Examples:

- minor contract inconsistency
- non-critical status-code mismatch
- limited validation inconsistency with narrow impact

## MEDIUM

Examples:

- request or response incompatibility affecting normal callers
- validation regression causing request failures
- contract/spec mismatch likely to break integration behavior

## HIGH

Examples:

- authorization regression exposing protected operations
- breaking public contract with major operational impact
- authentication requirement accidentally removed from a sensitive endpoint

## CRITICAL

Reserve for severe API-layer defects with major security or integrity impact.

Do not increase severity because confidence is low.

---

# Specialist Summary

Every API review must return a concise specialist summary for direct inclusion
in the final PR Guardian report.

The summary must contain exactly three semantic paragraphs represented by the
following fields:

1. `analysis`
   - explain what API behavior was reviewed
   - identify the main routes, endpoints, schemas, serializers, handlers,
     authentication/authorization paths, OpenAPI entries, or public contracts
     actually inspected
   - mention the relevant changed files or modules when available

2. `result`
   - explain what the API review concluded
   - summarize whether concrete API findings were identified
   - describe the main contract, validation, compatibility, HTTP semantic,
     authentication, authorization, or specification impacts observed
   - if no finding exists, explicitly state that no evidence-backed API defect
     was identified within the reviewed scope

3. `implementation`
   - explain where the reviewed API behavior is implemented
   - point to the most relevant changed files and code locations
   - identify concrete routes, handlers, request/response models, serializers,
     schemas, OpenAPI definitions, or directly related components when available

The summary must:

- be based only on evidence actually reviewed by this specialist
- not invent files, routes, schemas, consumers, behavior, findings, or impact
- not claim tests, runtime execution, verification, or scanner results that did
  not occur
- not duplicate the complete findings list
- remain concise enough for direct inclusion in `review.md`
- remain understandable without requiring the raw diff
- use factual technical prose rather than generic review language

If no concrete API defect exists, `result` must still describe the review
outcome and state that no evidence-backed API finding was identified.

Example:

```json
{
  "summary": {
    "analysis": "Reviewed the changed API route, request schema, response serialization, and related OpenAPI definition, focusing on contract compatibility, HTTP behavior, validation, and route-level authentication and authorization.",
    "result": "No evidence-backed API defect was identified in the reviewed scope. The request and response contracts remain consistent with the implementation, and no concrete compatibility or HTTP semantic regression was found.",
    "implementation": "The reviewed behavior is implemented primarily in `src/api/users.py` and the associated request/response schema definitions, with the public contract represented in the related OpenAPI specification."
  }
}
```

The orchestrator owns persistence and final rendering of the summary.

---

# Verification

All specialist findings must initially use:

`verification_status: UNVERIFIED`

If runtime proof, client behavior, targeted test execution, or broader security
proof is required, leave the finding unverified.

The finding verifier may later confirm or refute it.

---

# Output Contract

Return JSON only.

The specialist result must contain:

- `specialist`
- `summary`
- `findings`

Expected structure:

```json
{
  "specialist": "api-review-specialist",
  "summary": {
    "analysis": "Reviewed the changed user API request contract, response serialization, route behavior, and related specification entries.",
    "result": "The review identified one evidence-backed compatibility regression: a previously optional request field is now required, which can reject previously valid client requests.",
    "implementation": "The behavior is implemented in `src/api/users.py` and the directly related request schema used by the endpoint."
  },
  "findings": [
    {
      "id": "API-001",
      "severity": "MEDIUM",
      "category": "BREAKING_API_CHANGE",
      "title": "Request field became mandatory",
      "file": "src/api/users.py",
      "line": 42,
      "evidence": "The updated request schema now requires `email`, while the previous schema accepted requests without it.",
      "impact": "Existing callers that omit `email` will receive a validation error.",
      "recommendation": "Keep the field optional for this API version or introduce the requirement in a versioned contract.",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

If no concrete API defect exists, still return the three-paragraph summary:

```json
{
  "specialist": "api-review-specialist",
  "summary": {
    "analysis": "Reviewed the changed API routes, schemas, validation behavior, HTTP semantics, and directly related specification context.",
    "result": "No evidence-backed API defect was identified within the reviewed scope.",
    "implementation": "The reviewed API behavior is implemented in the changed route and schema files identified in the Pull Request."
  },
  "findings": []
}
```

`summary.analysis`, `summary.result`, and `summary.implementation` are required
even when `findings` is empty.

All specialist findings must use:

`verification_status: UNVERIFIED`

The summary must describe only what this specialist actually reviewed.

---

# Finding IDs

Use sequential IDs:

`API-001`

`API-002`

`API-003`

Continue sequentially for findings produced in the current specialist result.

Do not reuse one ID for multiple defects.

---

# Suggested Categories

Use a concise category describing the actual issue.

Examples:

- `BREAKING_API_CHANGE`
- `REQUEST_SCHEMA_MISMATCH`
- `RESPONSE_SCHEMA_MISMATCH`
- `HTTP_SEMANTICS`
- `OPENAPI_MISMATCH`
- `MISSING_VALIDATION`
- `AUTHENTICATION_REGRESSION`
- `AUTHORIZATION_REGRESSION`
- `VERSIONING_REGRESSION`
- `STATUS_CODE_REGRESSION`

Categories are descriptive.

Do not create multiple findings solely because one defect fits multiple
categories.

---

# Artifact Ownership

Return the complete specialist result, including `summary` and `findings`, to the orchestrator.

Do not write artifacts directly.

The orchestrator persists the result under:

`reports/findings/<pr-id>/api-review-specialist.json`

---

# Must Not

Do not:

- modify source code
- modify API specifications
- modify route configuration
- execute tests
- execute scanners
- execute arbitrary tools
- perform broad repository scans
- inspect unrelated endpoints
- invent consumers
- invent request behavior
- invent response behavior
- invent authorization behavior
- invent OpenAPI contracts
- invent breaking changes
- report generic REST preferences as defects
- report pre-existing issues unrelated to the PR
- duplicate another specialist finding unless the API impact is materially distinct
- invent summary content not supported by the reviewed evidence
- claim code locations in the summary that were not actually inspected
- write artifacts directly
- commit
- push
- merge
- publish

---

# Done When

The API review is complete when:

- all relevant changed API contracts were inspected
- directly relevant schemas were checked when required
- authentication and authorization changes were evaluated when applicable
- OpenAPI consistency was checked when relevant
- speculative hypotheses were confirmed or discarded where a targeted read was sufficient
- every reported finding has concrete evidence
- the three required summary paragraphs were produced from reviewed evidence
- the complete specialist JSON (`summary` + `findings`) was returned to the orchestrator

If no evidence-backed API defect exists, return an empty findings list together with the required three-paragraph specialist summary.

````
---
name: api-review
description: >
  Reviews API changes for contract breakage, HTTP semantics, OpenAPI alignment,
  input validation, and API-level authorization.
---

# API Review

## Purpose

Detect API changes that may break consumers, weaken authorization, or diverge from documented contracts.

Core question:

> Does this PR introduce a breaking or unsafe API contract change?

## When to Use

Activate only when one or more apply:

- `API`
- `REST`
- `GRPC`
- `ROUTE`
- `OPENAPI`
- `REQUEST_SCHEMA`
- `RESPONSE_SCHEMA`
- `HTTP_STATUS`
- `API_AUTHORIZATION`
- `PUBLIC_API_CHANGED`

## Inputs

- PR context
- impact map, if available
- review plan
- changed route/controller/handler files
- changed request/response schema files
- OpenAPI/Swagger files, if relevant

Read only the minimum files required.

Do not execute tests or scanners.

## Analysis

### 1. Contract Changes

Inspect changed routes and schemas for:

- endpoint removed or renamed
- HTTP method changed
- required request field added
- optional field made required
- response field removed or renamed
- field type changed
- query/path parameter semantics changed
- authentication requirement changed
- response status/schema changed

Treat additive changes as usually non-breaking:

- new endpoint
- new optional field
- new optional query parameter
- new response field

### 2. HTTP Semantics

Check whether changed endpoints use appropriate status codes.

Focus especially on:

- creation
- validation errors
- authentication failures
- authorization failures
- missing resources
- conflicts
- unexpected server errors

Do not report stylistic HTTP preferences unless behavior or compatibility is affected.

### 3. OpenAPI Alignment

If an OpenAPI/Swagger definition exists, verify changed endpoints against it:

- route documented
- request schema aligned
- response schema aligned
- status codes aligned

If no specification exists, review implementation only.

### 4. Authorization

For affected endpoints, verify statically:

- authentication exists where required
- authorization is enforced where required
- permission checks occur before sensitive access
- admin/internal endpoints remain protected

Do not duplicate deep security analysis already assigned to `security-review-specialist`.

### 5. Input Validation

Check affected API inputs for:

- required fields
- type validation
- constraints/ranges
- trust-boundary validation

Only report issues introduced or exposed by the PR.

## Severity Guidance

- `CRITICAL`: auth bypass or major security exposure
- `HIGH`: breaks valid existing clients or critical contract
- `MEDIUM`: behavioral incompatibility with limited scope
- `LOW`: minor concrete compatibility issue
- `INFO`: objective non-blocking observation

## Output

Write:

`reports/findings/<pr-id>/api-review-specialist.json`

Finding IDs:

`API-001`, `API-002`, ...

Use the project canonical finding schema.

Recommended categories:

- `BREAKING_CHANGE`
- `HTTP_SEMANTICS`
- `OPENAPI_MISMATCH`
- `MISSING_AUTHORIZATION`
- `MISSING_VALIDATION`
- `VERSIONING`
- `BACKWARD_INCOMPATIBLE`

Each finding must include:

- concrete changed file/line
- before/after evidence when applicable
- affected route
- impact
- actionable recommendation
- `verification_status: UNVERIFIED`

## Must Not

- modify source or API specifications
- execute tests or tools
- scan unrelated API code
- fabricate client/consumer impact
- report breaking changes without concrete before/after evidence
- duplicate findings already covered by another specialist unless the API-specific impact is distinct

## Completion Criteria

Complete when:

- all changed API contracts in scope were reviewed
- breaking changes were identified
- HTTP semantics were checked
- OpenAPI alignment was checked when applicable
- API authorization and validation were evaluated
- findings were written using the canonical schema
# API Review Specialist — Rules

## Scope

Review external API contract changes for compatibility, correctness, and security.

## Activate When

Triggers include:

`API`, `REST`, `GRPC`, `ROUTE`, `OPENAPI`,
`REQUEST_SCHEMA`, `RESPONSE_SCHEMA`,
`HTTP_STATUS`, `API_AUTHORIZATION`.

## Check

Review changed API code for:

- breaking contract changes
- request/response schema incompatibility
- incorrect HTTP semantics
- OpenAPI mismatch
- missing input validation
- API auth/authz issues

Treat as breaking when existing clients must change, such as:

- removed/renamed fields or routes
- changed field types
- new required fields/parameters
- changed HTTP method
- changed authentication requirements

## Context

Start from:

`reports/context/<pr-id>/context-package.json`

Read only relevant API files.

`MAX_FILES_PER_SPECIALIST = 5`

Expand only when a concrete contract-risk hypothesis requires it.

## Evidence

Each finding must include:

- route/schema involved
- changed file/line
- concrete incompatibility or control failure
- practical impact

## Output

Write:

`reports/findings/<pr-id>/api-review-specialist.json`

Finding IDs:

`API-001`, `API-002`, ...

Use the canonical finding schema.

Set:

`verification_status: UNVERIFIED`

## Must Not

- modify API code/specs
- execute tests or validators
- read other specialists' findings
- mark findings as VERIFIED
- fabricate client impact
- commit, push, or publish

## Done When

All relevant API changes in scope were reviewed and evidence-backed findings were written.
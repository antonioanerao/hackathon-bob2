---
name: api-review
description: >
  Reviews API changes for concrete contract, validation, and authorization risks.
---

# API Review

## Use When

Activate for:

- route or endpoint changes
- request/response schema changes
- OpenAPI changes
- HTTP status changes
- API authorization changes
- public API contract changes

## Check

Review changed API code for:

- breaking contract changes
- request/response incompatibility
- incorrect HTTP semantics
- OpenAPI mismatch
- missing validation
- API auth/authz issues

Breaking examples:

- removed or renamed endpoint/field
- changed HTTP method
- changed field type
- new required field/parameter
- changed authentication requirement

## Evidence

Each finding must include:

- changed file/line
- affected route/schema
- concrete before/after evidence when applicable
- practical impact
- actionable recommendation

Do not emit speculative findings when one targeted read can confirm or refute them.

## Output

Return findings as canonical JSON to the orchestrator.

Finding IDs:

`API-001`, `API-002`, ...

Set:

`verification_status: UNVERIFIED`

The orchestrator persists:

`reports/findings/<pr-id>/api-review-specialist.json`

## Must Not

- modify source/specs
- execute tests or tools
- scan unrelated API code
- invent consumer impact
- report breaking changes without concrete evidence
- duplicate another specialist finding unless API impact is distinct

## Done When

All relevant changed API contracts were reviewed and evidence-backed findings were returned to the orchestrator.
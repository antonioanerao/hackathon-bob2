---
name: api-review
description: >
  Evaluates REST and gRPC API contract changes for breaking compatibility,
  HTTP semantics, OpenAPI alignment, versioning, and API-level authorization.
  Used by the api-review-specialist.
---

# API Review

## Purpose

Identify API contract changes that would break existing clients, introduce
security gaps at the API boundary, or violate documented specifications.

## Core Question

> Does this change break the API contract for existing consumers?

## When to Use

Activated when API, REST, GRPC, ROUTE, OPENAPI, REQUEST_SCHEMA,
RESPONSE_SCHEMA, HTTP_STATUS, or API_AUTHORIZATION triggers are present.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json` (api section)
- Route/controller/handler files (read-only)
- Serializer/schema files (read-only)
- OpenAPI/Swagger spec files (read-only)

## Phases

### Phase 1: Route Change Inventory

For each changed route file:
- List all added, removed, and modified routes
- For each route: HTTP method, path, authentication required, authorization required

```bash
grep -n "@app.route\|@router\.\|@bp.route\|path(" app/routes/*.py
git diff <base_sha>..<head_sha> -- app/routes/
```

### Phase 2: Breaking Change Detection

Evaluate every route and schema change against the breaking change matrix:

**Breaking (requires version bump or migration strategy):**
- Removed endpoint
- Changed HTTP method (GET → POST)
- Added required request field
- Removed response field
- Changed field type (string → integer)
- Changed field name
- Changed authentication requirement
- Changed error response schema (status code or body)
- Changed query parameter from optional to required

**Non-breaking (additive changes):**
- Added optional request field with default
- Added new response field (clients ignore unknown fields)
- Added new endpoint
- Added new optional query parameter

For each breaking change found, classify severity:
- CRITICAL: auth bypass or security regression
- HIGH: would cause 4xx/5xx errors for valid current clients
- MEDIUM: silent behavioral change (different data returned)
- LOW: deprecated field now absent

### Phase 3: HTTP Semantics Validation

Verify correct HTTP status code usage:

```
200 OK         — successful GET, successful synchronous update with response
201 Created    — successful POST that creates a resource
204 No Content — successful DELETE or PUT with no response body
400 Bad Request — client-side validation error
401 Unauthorized — authentication required or failed
403 Forbidden   — authenticated but not authorized
404 Not Found   — resource does not exist
409 Conflict    — duplicate create or state conflict
422 Unprocessable Entity — valid JSON but failed business validation
500 Internal Server Error — unexpected server error
```

Flag cases where:
- 200 is used for a creation operation (should be 201)
- 500 is returned for client input errors (should be 4xx)
- 200 is returned for empty results instead of 404
- Authentication errors return 200 with an error message body

### Phase 4: OpenAPI Spec Alignment

If an OpenAPI/Swagger file exists:
```bash
cat openapi.yaml
cat swagger.json
find . -name "*.yaml" -path "*/api*" -o -name "openapi*.json"
```

Compare:
- Are all changed routes documented in the spec?
- Do documented request/response schemas match the implementation?
- Are all documented status codes used correctly?
- Are new routes added to the spec?

### Phase 5: API Authorization Review

For each route, verify:
- Is the route protected by authentication middleware?
- Is the route protected by authorization (role/permission) check?
- Is the authorization check performed before data access?
- Are internal/admin routes protected?

```bash
grep -n "login_required\|require_permission\|@auth\|@permission\|@requires_role" app/routes/*.py
```

### Phase 6: Input Validation

At the API boundary:
- Are all required fields validated?
- Are field types enforced?
- Are field lengths and value ranges validated?
- Is user input sanitized before downstream processing?

## Deterministic Tools & Evidence

```bash
git diff <base_sha>..<head_sha> -- app/routes/ app/schemas/ openapi.yaml
grep -n "status_code\|return.*200\|return.*201\|abort(" app/routes/*.py
grep -n "required=True\|validators\|Validator" app/schemas/*.py
```

## Canonical Output

File: `reports/findings/<pr-id>/api-review-specialist.json`

Finding IDs: `API-001`, `API-002`, ...

```json
{
  "reviewer": "api-review-specialist",
  "findings": [
    {
      "id": "API-001",
      "category": "BREAKING_CHANGE | HTTP_SEMANTICS | OPENAPI_MISMATCH | MISSING_AUTHORIZATION | MISSING_VALIDATION | VERSIONING | BACKWARD_INCOMPATIBLE",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<concise title>",
      "description": "<what changed and why it breaks or risks consumers>",
      "file": "<route or schema path>",
      "line": "<integer>",
      "evidence": ["<diff showing before/after>", "<spec vs implementation diff>"],
      "impact": "<client breakage, security bypass, incorrect behavior>",
      "recommendation": "<version bump, migration strategy, add validation, etc.>",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "api-review-specialist",
      "metadata": {
        "root_cause": "",
        "related_symbols": [],
        "affected_route": "<METHOD /path>",
        "breaking_change_type": "<field_removed | type_changed | route_removed | etc.>"
      }
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| No OpenAPI spec found | Note absence; evaluate implementation directly |
| Cannot determine consumer count | Flag breaking change regardless; impact is unknown |
| Internal-only API | Still evaluate; internal callers break too |

## What This Skill Must Not Do

- Modify route definitions, serializers, or OpenAPI specs
- Report a breaking change without verifying the before/after diff
- Fabricate consumer counts or client dependency information

## Completion Criteria

- All changed routes have been inventoried
- Breaking change analysis is complete for all modified schemas
- HTTP status codes have been verified
- OpenAPI alignment has been checked where a spec file exists
- API-level authorization has been evaluated
- Output file is written and schema-valid

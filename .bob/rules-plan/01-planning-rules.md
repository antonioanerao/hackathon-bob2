# PR Guardian — Planning Rules

These rules apply before specialist execution.

## 1. Understand Intent

Before routing, identify:

- what the PR changes
- why it changes
- affected components
- declared vs observed scope

Keep the summary concise.

## 2. Classify Domains

Use only relevant tags:

`APPLICATION_LOGIC`, `SECURITY`, `AUTHENTICATION`,
`AUTHORIZATION`, `API`, `DATABASE`, `BACKGROUND_JOB`,
`CONCURRENCY`, `CONFIGURATION`, `DEPENDENCY`,
`TESTING`, `ARCHITECTURE`, `OBSERVABILITY`, `PERFORMANCE`.

## 3. Detect Risk Triggers

Record applicable triggers such as:

`AUTHENTICATION_CHANGED`, `AUTHORIZATION_CHANGED`,
`TENANT_BOUNDARY_CHANGED`, `DATABASE_SCHEMA_CHANGED`,
`DATABASE_QUERY_CHANGED`, `PUBLIC_API_CHANGED`,
`BACKGROUND_JOB_CHANGED`, `DEPENDENCY_CHANGED`,
`SECRET_HANDLING_CHANGED`, `FILE_UPLOAD_CHANGED`,
`EXTERNAL_REQUEST_CHANGED`, `CONCURRENCY_CHANGED`.

## 4. Route Minimally

Select only specialists justified by domains/triggers.

Record:

- `selected_reviewers`
- `skipped_reviewers`
- one-line reason for each

Do not pre-load or pre-assign findings.

## 5. Plan Verification

CRITICAL/HIGH findings should be eligible for verification.
Selected MEDIUM findings may be verified when justified.

Do not invoke verification during planning.

## 6. Plan Artifacts

Expected outputs include:

- `pr-context.json`
- `impact-map.json`
- `review-plan.json`
- specialist findings
- `verification-results.json`, when needed
- `review.json`
- `review.md`
- `run-manifest.json`

## 7. No Pre-Judging

Planning decides routing and scope only.

Do not assume vulnerabilities, defects, or findings before specialist review.
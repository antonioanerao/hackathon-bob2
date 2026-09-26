---
name: pr-guardian-verify
description: >
  Re-verifies unresolved PR Guardian findings using existing review artifacts,
  targeted evidence collection, and controlled verification without re-running
  the full review pipeline.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-verify

## Usage

`/pr-guardian-verify <pr-id>`

Mode: `finding-verifier`

## Purpose

Re-verify existing PR Guardian findings without re-running:

- PR triage
- specialist reviewers
- the full review pipeline

This command is strictly evidence-oriented.

Its responsibility is to determine whether existing findings can be:

- `VERIFIED`
- `REFUTED`
- left `UNVERIFIED`
- marked `NOT_APPLICABLE`
- marked `VERIFICATION_FAILED`

The verifier must not create new findings.

---

## Core Principle

> Reviewers find. Verifier proves.

The verifier evaluates claims that already exist.

It does not perform general code review.

---

## Required Inputs

Required:

- one or more finding artifacts under:

`reports/findings/<pr-id>/`

Examples:

- `code-review-specialist.json`
- `security-review-specialist.json`
- `database-review-specialist.json`
- `api-review-specialist.json`
- `architecture-review-specialist.json`
- `async-review-specialist.json`

Optional:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`
- `reports/verification/<pr-id>/verification-results.json`

Previous verification results should be reused when available.

---

## Input Validation

Before verification:

1. Validate `<pr-id>`.
2. Locate findings under `reports/findings/<pr-id>/`.
3. Load all valid finding artifacts.
4. Validate finding schemas.
5. Load previous verification results when available.
6. Confirm referenced finding IDs exist.
7. Identify unresolved verification candidates.

If no findings exist:

- report that there are no findings to verify
- stop without creating artificial results

If all findings are already resolved:

- report that no unresolved findings remain
- stop without re-verifying by default

---

## Canonical Finding Schema

Every finding considered for verification should contain:

- `id`
- `severity`
- `category`
- `title`
- `file`
- `line`
- `evidence`
- `impact`
- `recommendation`
- `verification_status`

Valid severities:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Valid verification statuses:

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

Malformed findings must not be silently repaired.

Record the validation problem and skip or abort when safe verification cannot continue.

---

## Candidate Selection

By default, select findings whose current status is:

- `UNVERIFIED`
- `VERIFICATION_FAILED`

Do not automatically re-verify findings already marked:

- `VERIFIED`
- `REFUTED`
- `NOT_APPLICABLE`

unless explicitly targeted by a future command option or implementation.

---

## Verification Priority

Verify eligible findings in this order:

1. `CRITICAL`
2. `HIGH`
3. selected `MEDIUM`

`LOW` findings should normally remain unverified unless explicitly justified.

---

## Selected MEDIUM Findings

A `MEDIUM` finding may be selected for verification when:

- the claim affects a meaningful execution path
- evidence is incomplete but testable
- a targeted inspection can materially increase confidence
- the finding may influence engineering action
- verification cost is low relative to uncertainty

Do not verify MEDIUM findings merely because budget or time remains.

---

## Verification Process

For each candidate:

1. Read the existing finding.
2. Convert the claim into a testable hypothesis.
3. Reuse previously collected evidence first.
4. Determine the minimum additional evidence required.
5. Inspect only relevant files or configuration.
6. Run targeted tools or tests only if necessary.
7. Record evidence.
8. Assign a verification status.
9. Preserve traceability to the original finding.

---

## Hypothesis Model

Every verification should answer a concrete question.

Example:

```text
Finding:
Authorization check can be bypassed.

Verification hypothesis:
There exists a reachable request path where an authenticated user can access
the target operation without passing the required authorization check.
```

Avoid vague verification goals such as:

```text
Check whether security looks correct.
```

---

## Evidence Preference

Use evidence in this order when applicable:

1. existing finding evidence
2. changed code
3. directly referenced callers
4. directly referenced configuration
5. directly referenced schemas
6. deterministic static analysis
7. targeted tests
8. narrow integration test
9. other minimal proof required

Prefer static proof over execution when static proof is sufficient.

---

## Allowed Verification Methods

Valid methods include:

- `STATIC_ANALYSIS`
- `TARGETED_TEST`
- `INTEGRATION_TEST`
- `CONFIG_INSPECTION`
- `DEPENDENCY_ANALYSIS`
- `CODE_PATH_PROOF`
- `MANUAL_EVIDENCE`

Use the smallest sufficient method.

---

## Status Semantics

### VERIFIED

Use only when positive evidence supports the original finding.

Examples:

- code path proves the defect is reachable
- targeted test reproduces the failure
- configuration confirms unsafe behavior
- deterministic analysis confirms the defect

---

### REFUTED

Use only when positive evidence contradicts the original finding.

Examples:

- the required guard is proven to execute before the affected path
- a targeted test demonstrates the claimed failure cannot occur under the relevant conditions
- the supposed vulnerable sink is unreachable from the claimed source

Absence of evidence is not refutation.

---

### UNVERIFIED

Use when:

- evidence remains insufficient
- the claim is plausible but not provable
- verification would require excessive scope
- required runtime conditions are unavailable
- a safe conclusion cannot be reached

---

### NOT_APPLICABLE

Use when the verification target no longer applies to the inspected code or execution path.

Do not use this status merely because evidence is inconvenient to collect.

---

### VERIFICATION_FAILED

Use when verification was attempted but infrastructure or tooling failed.

Examples:

- test runner failure
- unavailable dependency
- broken local environment
- required command failure
- inaccessible verification fixture

Do not convert infrastructure failure into `REFUTED`.

---

## Runtime Execution Rules

When commands or tests are required:

- execute only targeted checks
- avoid full test suites
- record every command
- record exit codes
- capture concise relevant output
- do not repeat successful deterministic checks unnecessarily

Temporary verification files may only be created under:

`reports/verification/<pr-id>/tests/`

---

## Repository Scope

Default verification scope should remain narrow.

Prefer:

- changed file
- directly referenced caller
- related schema
- related configuration
- related targeted test

Avoid:

- broad repository scans
- unrelated modules
- speculative exploration
- reading large numbers of files without a specific hypothesis

Expand scope only when a concrete verification hypothesis requires it.

---

## Previous Verification Results

If:

`reports/verification/<pr-id>/verification-results.json`

already exists:

- load it
- preserve existing valid results
- update only selected unresolved findings
- do not overwrite `VERIFIED` or `REFUTED` entries by default
- preserve historical evidence when possible

---

## Verification Result Schema

Each result should contain:

- `finding_id`
- `status`
- `method`
- `evidence`
- `command`
- `exit_code`
- `notes`

Example:

```json
{
  "finding_id": "SEC-001",
  "status": "VERIFIED",
  "method": "CODE_PATH_PROOF",
  "evidence": "The route calls service.update() before any authorization guard.",
  "command": null,
  "exit_code": null,
  "notes": "Static evidence was sufficient."
}
```

When a command is executed:

```json
{
  "finding_id": "CODE-003",
  "status": "VERIFIED",
  "method": "TARGETED_TEST",
  "evidence": "The targeted test reproduces the null dereference.",
  "command": "pytest tests/test_service.py::test_missing_value",
  "exit_code": 1,
  "notes": "Failure matches the finding hypothesis."
}
```

---

## Merge Rules

When new verification results are produced:

1. preserve prior resolved entries
2. replace only explicitly re-evaluated unresolved entries
3. keep one authoritative result per `finding_id`
4. retain useful prior evidence where appropriate
5. do not change finding severity
6. do not create a new finding ID

---

## Output Artifact

Write:

`reports/verification/<pr-id>/verification-results.json`

The output should contain all authoritative verification results for the PR.

Recommended structure:

```json
{
  "pr_id": 42,
  "results": [
    {
      "finding_id": "SEC-001",
      "status": "VERIFIED",
      "method": "CODE_PATH_PROOF",
      "evidence": "...",
      "command": null,
      "exit_code": null,
      "notes": "..."
    }
  ]
}
```

---

## Failure Handling

### No Findings

If no finding artifacts exist:

- show a short notice
- stop

### No Unresolved Findings

If no candidate has status:

- `UNVERIFIED`
- `VERIFICATION_FAILED`

then:

- show a short notice
- do not re-run resolved verifications

### Invalid Artifact

If a findings or verification artifact is malformed:

- report the artifact
- stop when safe verification is impossible
- do not invent replacements

### Tool Failure

If a required verification command fails unexpectedly:

- record the command
- record the exit code
- use `VERIFICATION_FAILED` when appropriate

---

## Must Not

- re-run `pr-triage`
- re-run specialist reviewers
- create new findings
- perform general code review
- change finding severity
- change finding category
- change original finding meaning
- modify production code
- modify migrations
- modify application configuration
- write tests outside `reports/verification/`
- execute full test suites by default
- execute broad security scans by default
- fabricate evidence
- fabricate tool output
- fabricate test results
- fabricate runtime behavior
- overwrite prior `VERIFIED` results without explicit targeting
- overwrite prior `REFUTED` results without explicit targeting
- commit
- push
- merge
- publish
- automatically comment on GitHub

---

## Completion

The command is complete when either:

### Verification Executed

`reports/verification/<pr-id>/verification-results.json`

has been successfully written or updated.

or:

### Nothing To Verify

No unresolved eligible findings exist and the command explicitly reports that state.

---

## Completion Output

Show a concise summary containing:

- PR identifier
- findings considered
- findings verified
- findings refuted
- findings left unverified
- verification failures
- output artifact path

Example:

```text
PR #42

Verification complete.

Candidates: 3
Verified: 1
Refuted: 1
Unverified: 1
Failed: 0

Artifact:
reports/verification/42/verification-results.json
```

Then suggest:

`/pr-guardian-report <pr-id>`

to regenerate the final deterministic report.

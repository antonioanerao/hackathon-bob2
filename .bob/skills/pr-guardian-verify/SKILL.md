---
name: pr-guardian-verify
description: >
  Re-verifies unresolved PR Guardian findings using existing review artifacts,
  targeted evidence collection, and controlled verification without re-running
  triage or specialist review.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-verify

## Usage

`/pr-guardian-verify <pr-id>`

Mode: `finding-verifier`

---

# Purpose

Re-verify existing PR Guardian findings without re-running the review pipeline.

This command exists only to reassess unresolved verification state.

It must not:

- collect PR context again
- re-run triage
- re-run specialist reviewers
- discover new findings
- change finding severity
- reinterpret the original review scope

The command consumes existing findings and produces or updates verification evidence.

---

# Core Principle

> Reviewers find. Verifier proves.

Verification is not a second review pass.

The verifier evaluates only claims that already exist.

---

# Input

Required argument:

`<pr-id>`

The identifier must resolve to exactly one existing PR Guardian review workspace.

Reject:

- empty identifiers
- malformed identifiers
- path traversal input
- identifiers that resolve outside `reports/`

The runtime must determine all artifact paths deterministically.

---

# Required Inputs

Required:

- one or more valid finding artifacts under:

`reports/findings/<pr-id>/`

Typical examples:

- `code-review-specialist.json`
- `security-review-specialist.json`
- `database-review-specialist.json`
- `api-review-specialist.json`
- `architecture-review-specialist.json`
- `async-review-specialist.json`

If no finding artifacts exist:

- report that there is nothing to verify
- stop without fabricating results

---

# Optional Inputs

Optional supporting artifacts:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`
- `reports/verification/<pr-id>/verification-results.json`
- deterministic pre-scan evidence
- directly relevant repository files
- directly relevant tests
- directly relevant configuration
- directly relevant schema or dependency metadata

Do not require broad repository context by default.

---

# Input Validation

Before verification:

1. validate `<pr-id>`
2. enumerate finding artifacts
3. load valid finding JSON
4. validate specialist identity
5. validate finding schemas
6. load previous verification results when present
7. validate prior verification structure
8. map prior results by exact `finding_id`
9. identify unresolved candidates

Stop when malformed input prevents safe verification.

Do not silently repair malformed artifacts.

---

# Canonical Finding Schema

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

---

# Candidate Selection

By default, select only findings whose current status is:

- `UNVERIFIED`
- `VERIFICATION_FAILED`

Do not automatically re-verify findings already marked:

- `VERIFIED`
- `REFUTED`
- `NOT_APPLICABLE`

unless the implementation explicitly targets them.

---

# Verification Priority

Process unresolved findings in this order:

1. `CRITICAL`
2. `HIGH`
3. selected `MEDIUM`

Do not verify `LOW` by default.

---

# MEDIUM Selection

A MEDIUM finding may be selected when:

- evidence is incomplete
- the claim is testable
- verification can materially improve confidence
- the result may affect engineering action
- required verification effort is bounded

Do not verify MEDIUM findings merely because time or budget remains.

---

# Stage 1 — Load Existing Findings

Load only persisted findings.

Do not create synthetic findings.

Do not reinterpret unrelated repository observations as new findings.

Preserve each finding's:

- ID
- severity
- category
- original claim
- original evidence

---

# Stage 2 — Load Previous Verification

If:

`reports/verification/<pr-id>/verification-results.json`

exists:

- load it
- validate it
- preserve valid resolved entries
- preserve unresolved entries not selected for re-verification

One authoritative verification result should exist per `finding_id`.

---

# Previous Verification Rules

Existing:

- `VERIFIED`
- `REFUTED`

results must be preserved by default.

Do not overwrite them unless the command explicitly supports targeted re-verification.

Existing:

- `UNVERIFIED`
- `VERIFICATION_FAILED`

results may be updated when the corresponding finding is selected.

---

# Stage 3 — Load Verification Skill

Load:

`finding-verification`

only after unresolved candidates have been identified.

If there are no eligible unresolved findings:

- do not load unnecessary verification context
- show a short no-op notice
- stop

---

# Stage 4 — Create Testable Hypotheses

For every candidate:

1. read the original finding
2. preserve its meaning
3. convert the claim into one concrete testable hypothesis
4. identify the minimum evidence required

Example:

```text
Finding:
The update endpoint can bypass authorization.

Hypothesis:
There exists a reachable request path from the update route to the protected
operation without executing the required authorization check.
```

Avoid vague goals such as:

```text
Review whether authorization is correct.
```

---

# Stage 5 — Reuse Existing Evidence

Before collecting new evidence, reuse:

- original finding evidence
- changed code already available
- existing context artifacts
- existing deterministic tool output
- prior verification evidence
- directly related configuration
- directly related schema
- directly related tests
- dependency metadata

Do not repeat successful deterministic checks unnecessarily.

---

# Evidence Preference

Prefer evidence in this order when applicable:

1. existing finding evidence
2. changed code
3. directly referenced caller/callee
4. directly referenced configuration
5. directly referenced schema
6. code-path proof
7. deterministic static analysis
8. targeted test
9. narrow integration test
10. dependency analysis
11. other minimal manual evidence

Prefer static proof when it is sufficient.

---

# Stage 6 — Select Verification Method

Allowed methods:

- `STATIC_ANALYSIS`
- `TARGETED_TEST`
- `INTEGRATION_TEST`
- `CONFIG_INSPECTION`
- `DEPENDENCY_ANALYSIS`
- `CODE_PATH_PROOF`
- `MANUAL_EVIDENCE`

Choose the least expensive method that can establish a reliable conclusion.

Do not execute tools simply because they are available.

---

# STATIC_ANALYSIS

Use when deterministic static tooling can directly evaluate the finding.

Examples:

- type checker
- linter
- dependency analyzer
- migration analyzer
- security analyzer

Scanner output must be correlated to the exact finding.

Scanner output alone does not automatically verify a claim.

---

# CODE_PATH_PROOF

Use when the claim can be established through code flow.

Document:

- entry point
- relevant branch
- guard or missing guard
- target operation
- failure or security sink

Example:

```text
request
→ route
→ service
→ missing role check
→ privileged update
```

Do not invent unreachable paths.

---

# CONFIG_INSPECTION

Use when configuration directly controls the behavior.

Examples:

- auth middleware registration
- feature flags
- retry settings
- dependency injection bindings
- timeout settings
- queue acknowledgment behavior

Do not infer runtime values that are not visible.

---

# DEPENDENCY_ANALYSIS

Use when the finding depends on:

- package version
- vulnerable dependency range
- dependency conflict
- transitive dependency
- security advisory applicability

Do not invent:

- package versions
- CVEs
- dependency relationships

---

# TARGETED_TEST

Use only when a narrow test can directly confirm or refute the finding.

Prefer:

- one test
- one path
- one failure condition

Do not run the full test suite.

Temporary verification tests may only be written under:

`reports/verification/<pr-id>/tests/`

Do not modify the repository's actual tests.

---

# INTEGRATION_TEST

Use only when static inspection or targeted unit-level proof is insufficient.

Keep integration execution limited to the existing finding.

Do not start broad infrastructure unnecessarily.

---

# MANUAL_EVIDENCE

Use when direct inspection is sufficient.

Examples:

- route registration
- schema declaration
- package manifest
- migration ordering
- explicit configuration
- API contract

Evidence must be concrete and traceable.

---

# Stage 7 — Execute Targeted Verification

When execution is necessary:

- execute the minimum command required
- avoid broad scanners
- avoid full test suites
- avoid unrelated commands
- record the exact command
- record the exit code
- record concise relevant output
- distinguish application failure from verification-infrastructure failure

Do not execute the same successful deterministic check repeatedly.

---

# Exit Code Interpretation

Do not interpret exit codes without context.

A non-zero result may mean:

- the finding was reproduced
- the test infrastructure failed
- an unrelated dependency failed
- the verification command itself was invalid

Use evidence, not exit code alone, to set verification status.

---

# Stage 8 — Assign Verification Status

Every candidate must receive one justified status:

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

---

# VERIFIED

Use only when positive evidence supports the original finding.

Examples:

- reachable code path proves the defect
- targeted test reproduces the exact behavior
- configuration confirms the unsafe state
- deterministic analysis confirms the claim

Plausibility alone is not sufficient.

---

# REFUTED

Use only when positive evidence contradicts the original finding.

Examples:

- required authorization guard is proven to run before the operation
- supposedly reachable path is impossible
- targeted test proves the claimed behavior does not occur under the relevant conditions
- configuration proves the supposedly unsafe feature is disabled

Absence of proof is not refutation.

---

# UNVERIFIED

Use when:

- available evidence remains insufficient
- required runtime state is unavailable
- the claim is plausible but not provable
- safe verification would exceed reasonable scope
- static evidence is inconclusive

Do not force a binary conclusion.

---

# NOT_APPLICABLE

Use when the finding no longer applies to the evaluated code or execution path.

Examples:

- referenced behavior was removed
- target path no longer exists
- condition cannot occur in the current PR state

Do not use this status simply because verification is inconvenient.

---

# VERIFICATION_FAILED

Use when verification was attempted but could not complete due to infrastructure or tooling failure.

Examples:

- test runner failed to start
- dependency unavailable
- fixture unavailable
- required local service unavailable
- deterministic tool failed unexpectedly

Do not convert this state to `REFUTED`.

---

# Stage 9 — Build Verification Results

Each result must contain:

- `finding_id`
- `status`
- `method`
- `evidence`
- `command`
- `exit_code`
- `notes`

Use:

```json
"command": null
```

when no command was executed.

Use:

```json
"exit_code": null
```

when no process exit code exists.

---

# Example Result

```json
{
  "finding_id": "SEC-001",
  "status": "VERIFIED",
  "method": "CODE_PATH_PROOF",
  "evidence": "The changed route reaches update_record() after authentication but before any role or ownership authorization check.",
  "command": null,
  "exit_code": null,
  "notes": "Static evidence was sufficient."
}
```

---

# Example Targeted Test Result

```json
{
  "finding_id": "CODE-003",
  "status": "VERIFIED",
  "method": "TARGETED_TEST",
  "evidence": "The targeted test reproduces the null dereference described by the finding.",
  "command": "pytest reports/verification/42/tests/test_code_003.py -q",
  "exit_code": 1,
  "notes": "The non-zero result corresponds to the expected reproduced application failure."
}
```

Do not mark a finding verified solely because a command returned non-zero.

---

# Stage 10 — Merge With Previous Results

When prior verification exists:

1. preserve resolved results
2. update only findings intentionally re-evaluated
3. preserve unresolved results not selected
4. maintain one authoritative result per `finding_id`
5. retain useful prior evidence when appropriate
6. preserve traceability

Do not erase valid historical evidence without reason.

---

# Verification Integrity

The verifier must not change:

- `finding_id`
- severity
- category
- original title
- original evidence
- original impact
- original recommendation
- original defect meaning

Verification updates truth status and verification evidence only.

---

# Stage 11 — Persist Verification Artifact

Write:

`reports/verification/<pr-id>/verification-results.json`

Recommended structure:

```json
{
  "pr_id": 42,
  "results": [
    {
      "finding_id": "SEC-001",
      "status": "VERIFIED",
      "method": "CODE_PATH_PROOF",
      "evidence": "Concrete verification evidence.",
      "command": null,
      "exit_code": null,
      "notes": "Static evidence was sufficient."
    }
  ]
}
```

The runtime controls the output path.

Do not allow the model to choose a destination.

---

# Repository Scope

Verification scope must remain narrow.

Prefer:

- the finding's file
- directly referenced callers
- directly referenced callees
- related configuration
- related schema
- related test
- directly relevant dependency declaration

Avoid:

- broad repository scans
- unrelated modules
- full architecture review
- speculative exploration
- large file sets without a concrete hypothesis

---

# Re-run Rules

Do not re-run deterministic checks when:

- valid relevant output already exists
- source inputs have not materially changed
- the previous evidence is sufficient

Re-run only when new verification evidence is necessary.

---

# Relationship With Specialists

Specialists discover findings.

Verifier evaluates them.

Do not:

- perform a new domain review
- search for additional bugs
- create findings from unrelated observations
- expand into another specialist's role

If an unrelated issue is observed, ignore it during this command.

---

# Relationship With Synthesis

This command does not classify findings as:

- `BLOCKING`
- `ADVISORY`

That belongs to deterministic final synthesis.

The verifier sets only verification status and supporting evidence.

---

# No Findings

If no findings exist:

- show a short notice
- do not create fake verification entries
- stop

---

# No Unresolved Findings

If no findings remain with:

- `UNVERIFIED`
- `VERIFICATION_FAILED`

then:

- report that verification is already resolved
- do not re-run verification
- preserve the existing verification artifact
- stop

---

# Failure Handling

## Malformed Finding Artifact

If a required finding artifact is malformed:

- identify the invalid artifact
- stop if safe verification cannot continue
- do not repair it using model inference

---

## Invalid Previous Verification

If previous verification data is malformed:

- report the inconsistency
- avoid destructive overwrite
- stop when authoritative merge cannot be guaranteed

---

## Unknown Finding Reference

If previous verification references an unknown finding:

- record the inconsistency
- do not create the missing finding
- preserve valid existing data where possible

---

## Tool Failure

If tooling fails unexpectedly:

- record command
- record exit code
- record concise failure evidence
- set `VERIFICATION_FAILED` when appropriate

---

# Must Not

Do not:

- re-run `pr-triage`
- re-run specialist reviewers
- create new findings
- perform general review
- change finding severity
- change finding category
- rewrite finding meaning
- modify production code
- modify migrations
- modify application configuration
- modify dependency manifests
- write tests outside `reports/verification/`
- run full test suites by default
- run broad scanners by default
- scan unrelated files
- fabricate evidence
- fabricate commands
- fabricate command output
- fabricate exit codes
- fabricate test results
- fabricate runtime behavior
- fabricate package versions
- fabricate CVEs
- overwrite prior `VERIFIED` results without explicit targeting
- overwrite prior `REFUTED` results without explicit targeting
- commit
- push
- merge
- publish
- automatically post GitHub comments

---

# Completion

The command is complete when either:

## Verification Performed

`reports/verification/<pr-id>/verification-results.json`

has been successfully created or updated.

or:

## Nothing To Verify

No eligible unresolved findings exist and that state was explicitly reported.

---

# Completion Output

Display a concise summary containing:

- PR identifier
- unresolved candidates
- verified findings
- refuted findings
- remaining unverified findings
- not-applicable findings
- verification failures
- artifact path

Example:

```text
PR #42

Verification complete.

Candidates: 4
Verified: 2
Refuted: 1
Unverified: 1
Not applicable: 0
Failed: 0

Artifact:
reports/verification/42/verification-results.json
```

Then suggest:

`/pr-guardian-report <pr-id>`

to regenerate the deterministic final report.

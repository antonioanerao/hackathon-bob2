---
name: pr-guardian-report
description: >
  Regenerates deterministic PR Guardian review artifacts from previously
  collected context, triage plans, specialist findings, and optional
  verification results without re-running review or verification stages.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-report

## Usage

`/pr-guardian-report <pr-id>`

Mode: `pr-guardian-orchestrator`

---

# Purpose

Regenerate final PR Guardian reports using existing persisted artifacts only.

This command performs deterministic synthesis.

It must not:

- collect PR context again
- re-run triage
- re-run specialist reviewers
- re-run verification
- create new findings
- reinterpret the Pull Request
- fetch new repository evidence

The command consumes existing structured artifacts and produces a consistent
final review representation.

---

# Core Principle

> Reports summarize evidence. They do not create evidence.

Final reporting must remain deterministic.

The report stage is responsible for:

- validating existing artifacts
- applying existing verification results
- removing inactive findings
- deduplicating by root cause
- classifying findings
- generating structured and human-readable outputs

---

# Input

Required argument:

`<pr-id>`

The PR identifier must resolve to exactly one existing PR Guardian review
workspace.

Reject:

- empty identifiers
- malformed identifiers
- path traversal input
- identifiers that resolve outside `reports/`

The runtime, not the model, must determine artifact paths.

---

# Required Inputs

Always required:

- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

When `selected_reviewers` is not empty:

- one valid finding artifact for each successfully completed selected specialist
  under:

`reports/findings/<pr-id>/`

Typical examples:

- `code-review-specialist.json`
- `security-review-specialist.json`
- `database-review-specialist.json`
- `api-review-specialist.json`
- `architecture-review-specialist.json`
- `async-review-specialist.json`

---

# Optional Inputs

Optional artifacts include:

- `reports/context/<pr-id>/impact-map.json`
- `reports/verification/<pr-id>/verification-results.json`
- existing run metadata when useful for preserving operational context

Optional artifacts must never be fabricated when absent.

---

# Input Validation

Before synthesis:

1. validate `<pr-id>`
2. load `pr-context.json`
3. load `review-plan.json`
4. verify both artifacts refer to the same PR
5. validate required fields
6. validate `risk_level`
7. validate `selected_reviewers`
8. validate specialist artifact presence
9. validate each finding artifact
10. validate verification results when present

Stop when required artifacts are missing, malformed, conflicting, or unsafe to
consume.

Do not infer missing required artifacts.

---

# PR Context Validation

Validate relevant context fields when present:

- `pr_id`
- `repository_name`
- `title`
- `base_sha`
- `head_sha`
- `changed_files_count`
- `additions`
- `deletions`

Do not invent values for missing optional metrics.

If a field is unavailable, omit it or represent it explicitly as unavailable.

---

# Review Plan Validation

The review plan should contain:

- `risk_level`
- `agent_budget`
- `risk_triggers`
- `selected_reviewers`
- `skipped_reviewers`

Valid risk levels:

- `TRIVIAL`
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

The reporting command does not change triage decisions.

Do not:

- add reviewers
- remove reviewers
- alter risk level
- recompute routing

---

# Specialist Artifact Validation

For every expected specialist artifact:

Validate:

- JSON structure
- `specialist`
- `findings`
- specialist identity
- finding schema
- finding IDs
- severity values
- verification status values

A finding artifact must belong to the expected specialist.

Do not silently accept:

- unknown specialist names
- malformed findings
- invalid severities
- unknown verification statuses
- duplicate finding IDs within the same specialist result

---

# Canonical Finding Schema

Every finding should contain:

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

Valid severity values:

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

---

# Action

## Stage 1 — Load Findings

Load findings only from relevant persisted specialist artifacts.

Do not create findings during report generation.

Do not consume arbitrary JSON files from the findings directory without checking
that they belong to the review plan or recorded execution state.

---

## Stage 2 — Apply Verification Results

If:

`reports/verification/<pr-id>/verification-results.json`

exists, validate and apply each result by `finding_id`.

Verification may update:

- `verification_status`
- verification evidence
- verification method
- verification execution metadata

Verification must not update:

- severity
- category
- title
- original evidence
- original finding meaning
- original finding ID

---

# Verification Merge Rules

For each verification entry:

1. match by exact `finding_id`
2. ensure the referenced finding exists
3. validate the verification status
4. preserve original finding fields
5. attach or apply verification metadata
6. update only verification state

Unknown verification references must not silently create findings.

If an unknown `finding_id` appears:

- record an artifact inconsistency
- stop when safe synthesis cannot be guaranteed

---

# Findings Without Verification

If verification results are absent:

- preserve findings as `UNVERIFIED` when that is their stored state

Do not automatically convert findings to:

- `VERIFIED`
- `REFUTED`
- `NOT_APPLICABLE`

If a finding already contains another valid persisted status, preserve it unless
the authoritative verification artifact supersedes it.

---

# REFUTED Findings

Findings with:

`verification_status: REFUTED`

must be excluded from the active finding set.

They must not appear as:

- blocking findings
- advisory findings

For auditability, they may remain under a separate `refuted` collection in
`review.json`.

They may also be summarized in a verification section of `review.md`.

---

# NOT_APPLICABLE Findings

Findings with:

`verification_status: NOT_APPLICABLE`

must not be classified as blocking.

They should normally be excluded from the active finding set.

They may remain in structured history for traceability.

---

# VERIFICATION_FAILED Findings

Findings with:

`verification_status: VERIFICATION_FAILED`

remain active unless another rule excludes them.

They are not automatically blocking.

They should remain advisory unless a later successful verification establishes a
blocking state.

---

# Stage 3 — Deduplication

Deduplicate findings only when they share the same underlying root cause.

Consider:

- same affected code path
- same defect mechanism
- same affected state
- same relevant file/location
- same practical impact

Do not deduplicate merely because:

- titles are similar
- categories are equal
- severities match
- files match

---

# Deduplication Rules

When two findings represent the same root cause:

- preserve the strongest concrete evidence
- preserve the clearest practical impact
- preserve the most actionable recommendation
- retain traceability to original finding IDs
- preserve specialist provenance where useful

Do not invent a new defect during merging.

Do not increase severity merely because multiple specialists reported the same
problem.

---

# Stage 4 — Final Classification

Classification is deterministic.

## BLOCKING

A finding is `BLOCKING` only when:

- `verification_status == VERIFIED`
- and severity is `HIGH` or `CRITICAL`

Equivalent:

`BLOCKING = VERIFIED + CRITICAL|HIGH`

---

## ADVISORY

All remaining active findings are `ADVISORY`.

Examples include:

- verified MEDIUM
- verified LOW
- unverified CRITICAL
- unverified HIGH
- unverified MEDIUM
- unverified LOW
- verification failures

Do not promote an unverified finding to blocking.

---

# Stage 5 — Report Summary

The final report should summarize, when available:

- PR identifier
- repository
- title
- risk level
- base SHA
- head SHA
- changed files count
- additions
- deletions
- selected reviewers
- skipped reviewers
- risk triggers
- total findings
- blocking findings
- advisory findings
- verified findings
- unverified findings
- refuted findings
- verification failures
- specialist failures
- review completeness

Do not invent missing metrics.

---

# Partial Review State

If one or more selected specialists failed during the original review:

the regenerated report must preserve that fact.

Do not imply full review coverage.

Recommended state:

`PARTIAL`

Possible report states may include:

- `COMPLETE`
- `PARTIAL`
- `FAILED`

The exact runtime enum should remain deterministic.

---

# Stage 6 — Generate review.json

Write:

`reports/reviews/<pr-id>/review.json`

The structured report should be suitable for:

- automation
- CI integration
- later rendering
- audit
- comparison
- external publication by a separate authorized component

Recommended structure:

```json
{
  "pr_id": 42,
  "repository": "owner/repository",
  "title": "Example PR",
  "risk_level": "HIGH",
  "risk_triggers": [],
  "selected_reviewers": [],
  "summary": {
    "total_findings": 0,
    "blocking": 0,
    "advisory": 0,
    "verified": 0,
    "unverified": 0,
    "refuted": 0,
    "verification_failed": 0
  },
  "blocking": [],
  "advisory": [],
  "refuted": [],
  "verification": {},
  "execution": {
    "status": "COMPLETE"
  }
}
```

Use structured fields instead of generated prose when possible.

---

# Stage 7 — Generate review.md

Write:

`reports/reviews/<pr-id>/review.md`

The Markdown report must be:

- deterministic
- concise
- evidence-backed
- human-readable
- structurally stable

Do not use a new LLM reasoning pass to rewrite findings.

---

# review.md Structure

Recommended structure:

```text
# PR Guardian Review — PR #<id>

Repository
Title
Risk Level
Review Status

## Summary

## Reviewers

## Risk Triggers

## Blocking Findings

## Advisory Findings

## Refuted Findings

## Verification

## Execution Notes

## Review Result
```

Sections may contain explicit no-op messages such as:

`No verified blocking findings.`

Do not silently omit important state.

---

# Finding Rendering

For every active finding include:

- finding ID
- title
- severity
- category
- verification status
- file
- line
- evidence
- impact
- recommendation

When verification exists, include:

- verification method
- verification evidence
- verification notes when relevant

Do not embellish the stored evidence.

---

# Example Finding Rendering

```markdown
### SEC-001 — Missing authorization check

- Severity: `HIGH`
- Category: `AUTHORIZATION_REGRESSION`
- Verification: `VERIFIED`
- File: `src/api/admin.py:84`

**Evidence**

The updated route invokes the privileged operation without the existing
role check.

**Impact**

An authenticated user without the required role can reach the privileged
operation.

**Recommendation**

Restore the authorization guard before invoking the service operation.

**Verification**

Method: `CODE_PATH_PROOF`

The route, middleware, and service path were inspected and no equivalent
authorization guard exists before the protected call.
```

---

# Stage 8 — Generate run-manifest.json

Write:

`reports/runs/<pr-id>/run-manifest.json`

This manifest describes the report regeneration operation.

Recommended fields:

- `pr_id`
- `operation`
- `inputs`
- `source_artifacts`
- `selected_reviewers`
- `specialist_failures`
- `verification_used`
- `finding_counts`
- `output_artifacts`
- `status`

Example:

```json
{
  "pr_id": 42,
  "operation": "report",
  "verification_used": true,
  "finding_counts": {
    "total": 4,
    "blocking": 1,
    "advisory": 2,
    "refuted": 1
  },
  "status": "COMPLETE"
}
```

Do not fabricate timing, token, model, or performance metrics when they were not
recorded.

---

# Existing Reports

If existing:

- `review.json`
- `review.md`
- `run-manifest.json`

already exist, they may be regenerated from the authoritative source artifacts.

Do not use previous rendered reports as the primary source of findings.

Source of truth remains:

- context artifacts
- review plan
- specialist findings
- verification results

---

# Determinism

Given the same valid input artifacts, report regeneration should produce the
same classification and logically equivalent output.

Do not introduce randomization.

Do not use LLM inference for:

- classification
- deduplication rules that can be deterministically implemented
- Markdown structure
- summary counts
- artifact paths

---

# Failure Handling

## Missing Context

Stop when:

`reports/context/<pr-id>/pr-context.json`

is missing.

---

## Missing Review Plan

Stop when:

`reports/plans/<pr-id>/review-plan.json`

is missing.

---

## Missing Specialist Artifact

When a selected specialist is recorded as successfully completed but its finding
artifact is missing:

- report artifact inconsistency
- stop or mark report generation failed according to deterministic runtime policy

Do not assume the specialist returned zero findings.

---

## Recorded Specialist Failure

If the original run explicitly recorded a specialist failure:

- preserve the failure
- continue synthesis from valid existing findings
- mark review coverage as partial

Do not require a fake findings artifact for the failed specialist.

---

## Malformed JSON

Stop when a required artifact contains malformed JSON.

Do not attempt to repair it through model inference.

---

## Invalid Finding

Do not silently fix malformed findings.

Record the validation failure.

Stop when the invalid data prevents trustworthy synthesis.

---

## Invalid Verification Reference

If verification refers to a finding that does not exist:

- record inconsistency
- do not create the finding
- stop when required for integrity

---

# Must Not

Do not:

- run `pr-triage`
- run specialist reviewers
- invoke specialist skills for new analysis
- run `finding-verifier`
- execute tests
- execute static analyzers
- execute scanners
- execute migrations
- fetch new PR context
- reload the PR diff for analysis
- inspect new repository files
- create findings
- change finding severity
- change finding category
- reinterpret finding meaning
- fabricate evidence
- fabricate metrics
- fabricate verification
- fabricate specialist results
- fabricate execution state
- modify production code
- modify migrations
- modify application configuration
- modify dependency files
- commit
- push
- merge
- publish
- automatically post GitHub comments

---

# Output Artifacts

Successful report regeneration must produce:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

These outputs must remain under `reports/`.

---

# Completion

The command is complete only when:

- `<pr-id>` was validated
- required source artifacts were validated
- findings were loaded safely
- verification results were applied when available
- inactive findings were handled
- root-cause deduplication completed
- final classification completed
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

Inline output does not replace persisted artifacts.

---

# Completion Output

At completion, display a concise summary containing:

- PR identifier
- risk level
- total active findings
- blocking findings
- advisory findings
- refuted findings
- review status
- verification usage
- generated artifact paths

Example:

```text
PR #42
Risk: HIGH
Status: COMPLETE

Findings: 4
Blocking: 1
Advisory: 2
Refuted: 1

Verification: applied

Artifacts:
reports/reviews/42/review.json
reports/reviews/42/review.md
reports/runs/42/run-manifest.json
```

Then display the generated:

`review.md`

---
name: pr-guardian-report
description: >
  Regenerates deterministic PR Guardian review artifacts from previously
  collected context, triage plans, specialist findings, and optional
  verification results.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-report

## Usage

`/pr-guardian-report <pr-id>`

Mode: `pr-guardian-orchestrator`

## Purpose

Regenerate final PR Guardian review artifacts using existing data only.

This command performs deterministic synthesis.

It must not:

- re-run triage
- re-run specialist reviewers
- re-run verification
- create new findings
- reinterpret the PR
- request new repository context

The command consumes existing artifacts and produces a consistent final report.

---

## Required Inputs

Always required:

- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

Required when `selected_reviewers` is not empty:

- one findings artifact for every selected specialist under:

`reports/findings/<pr-id>/`

Examples:

- `code-review-specialist.json`
- `security-review-specialist.json`
- `database-review-specialist.json`
- `api-review-specialist.json`
- `architecture-review-specialist.json`
- `async-review-specialist.json`

Optional:

- `reports/context/<pr-id>/impact-map.json`
- `reports/verification/<pr-id>/verification-results.json`

---

## Input Validation

Before synthesis:

1. Validate `<pr-id>`.
2. Load `pr-context.json`.
3. Load `review-plan.json`.
4. Confirm that both artifacts refer to the same PR.
5. Validate required fields.
6. Validate `selected_reviewers`.
7. If reviewers were selected, confirm that every selected reviewer has a corresponding findings artifact.
8. Validate findings structure.
9. If verification results exist, validate them before applying them.

Stop when required artifacts are missing, malformed, or inconsistent.

Do not infer missing artifacts.

---

## Canonical Finding Validation

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

Malformed findings must not be silently corrected.

Record malformed artifacts or findings as synthesis errors.

---

## Action

### 1. Load Existing Findings

Load findings only from artifacts belonging to specialists selected by the review plan.

Do not consume findings from unselected specialists.

Do not create additional findings during synthesis.

---

### 2. Apply Verification Results

When:

`reports/verification/<pr-id>/verification-results.json`

exists, apply each verification result to the matching `finding_id`.

Valid transitions include:

- `UNVERIFIED` → `VERIFIED`
- `UNVERIFIED` → `REFUTED`
- `UNVERIFIED` → `VERIFICATION_FAILED`
- `UNVERIFIED` → `NOT_APPLICABLE`

Verification results must not:

- change finding severity
- change finding category
- create new findings
- modify the original finding claim

When no verification result exists for a finding, preserve its current verification status.

When no verification artifact exists, findings remain `UNVERIFIED` unless already carrying another valid status.

---

### 3. Remove Inactive Findings

Exclude findings with:

`verification_status: REFUTED`

from the active findings set.

`REFUTED` findings may still be retained in `review.json` under a separate historical or verification section when useful for auditability, but they must not appear as active review findings.

`NOT_APPLICABLE` findings should not be treated as blocking.

---

### 4. Deduplicate Findings

Deduplicate findings only when they represent the same underlying root cause.

Use evidence such as:

- same file/location
- same affected code path
- same defect mechanism
- same practical impact

Do not deduplicate findings merely because titles or categories are similar.

When multiple specialists identify the same root cause:

- preserve the strongest concrete evidence
- preserve relevant domain-specific impact
- retain traceability to originating finding IDs when possible

Do not invent a new defect while merging.

---

### 5. Classify Findings

Classify active findings as follows.

#### BLOCKING

A finding is `BLOCKING` only when:

- `verification_status == VERIFIED`
- and severity is `CRITICAL` or `HIGH`

Equivalent rule:

`BLOCKING = VERIFIED + CRITICAL|HIGH`

#### ADVISORY

All other active findings are `ADVISORY`, including:

- verified MEDIUM
- verified LOW
- unverified CRITICAL
- unverified HIGH
- unverified MEDIUM
- unverified LOW
- verification failures

Equivalent rule:

`ADVISORY = remaining active findings`

Do not treat an unverified HIGH or CRITICAL finding as verified blocking evidence.

---

## Report Summary

The final report should summarize:

- PR identifier
- repository
- PR title
- risk level
- changed files count
- additions
- deletions
- selected reviewers
- risk triggers
- total findings
- blocking findings
- advisory findings
- refuted findings
- verification status
- specialist failures, when available

Do not invent missing metrics.

---

## Markdown Structure

`review.md` should use a stable structure.

Recommended sections:

```text
# PR Guardian Review — PR #<id>

Repository
Title
Risk Level

## Summary

## Reviewers

## Risk Triggers

## Blocking Findings

## Advisory Findings

## Verification

## Execution Notes

## Review Result
```

Sections with no applicable content may contain a concise explicit message such as:

`No verified blocking findings.`

Do not silently omit important review states.

---

## review.json

Write:

`reports/reviews/<pr-id>/review.json`

It should contain structured data suitable for automation.

Recommended top-level fields:

- `pr_id`
- `repository`
- `title`
- `risk_level`
- `risk_triggers`
- `selected_reviewers`
- `summary`
- `blocking`
- `advisory`
- `refuted`
- `verification`
- `execution`

Do not store generated prose where structured values are sufficient.

---

## review.md

Write:

`reports/reviews/<pr-id>/review.md`

The Markdown report should be human-readable and deterministic.

For every active finding include:

- ID
- title
- severity
- category
- verification status
- file and line
- evidence
- impact
- recommendation

Do not embellish findings beyond the stored evidence.

---

## run-manifest.json

Write:

`reports/runs/<pr-id>/run-manifest.json`

The manifest should record the synthesis execution.

Recommended fields:

- `pr_id`
- `operation: report`
- `inputs`
- `selected_reviewers`
- `verification_used`
- `finding_counts`
- `specialist_failures`
- `artifacts`
- `status`

The manifest is operational metadata, not a review finding artifact.

---

## Failure Handling

Stop with an explicit error when:

- `pr-context.json` is missing
- `review-plan.json` is missing
- required findings artifacts are missing
- JSON is malformed
- PR identifiers conflict
- selected reviewer artifacts are inconsistent
- finding schema is invalid
- verification data references invalid findings in a way that prevents safe synthesis

Do not fabricate replacements.

When a non-critical optional artifact is unavailable:

- record the limitation
- continue only when synthesis remains trustworthy

---

## Must Not

- run `pr-triage`
- run specialist reviewers
- invoke Ollama for new review reasoning
- run `finding-verifier`
- execute tests
- execute scanners
- fetch additional repository context
- create new findings
- change finding severity
- reinterpret findings
- fabricate evidence
- fabricate metrics
- fabricate verification
- modify production code
- modify migrations
- modify application configuration
- commit
- push
- merge
- publish
- automatically comment on GitHub

---

## Output Artifacts

The command must produce:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

---

## Completion

The command is complete only when:

- all required inputs were validated
- verification results were applied when available
- `REFUTED` findings were removed from the active set
- findings were deduplicated safely
- blocking/advisory classification was completed
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

Inline output does not replace required artifacts.

At completion:

1. show a concise synthesis summary
2. show the final `review.md`
3. report the generated artifact paths

---
name: pr-guardian-report
description: >
  Regenerates deterministic PR Guardian review artifacts from previously
  collected context, triage plans, specialist results, and optional verification
  results without re-running review or verification stages.
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

Regenerate final PR Guardian review artifacts using existing persisted data only.

This command performs deterministic synthesis.

It must not:

- collect PR context again
- re-run triage
- re-run specialist reviewers
- re-run verification
- create new findings
- reinterpret the Pull Request
- fetch new repository evidence
- invoke Ollama for new review reasoning
- regenerate specialist summaries with a model

The command consumes existing structured artifacts and produces a consistent
final review representation.

Core principle:

> Reports summarize evidence. They do not create evidence.

---

# Required Inputs

Always required:

- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

When `selected_reviewers` is not empty:

- one valid specialist artifact for every successfully completed selected
  specialist under:

`reports/findings/<pr-id>/`

Typical examples:

- `code-review-specialist.json`
- `security-review-specialist.json`
- `database-review-specialist.json`
- `api-review-specialist.json`
- `architecture-review-specialist.json`
- `async-review-specialist.json`

Each successful specialist artifact must contain:

- `specialist`
- `summary`
- `findings`

Optional inputs:

- `reports/context/<pr-id>/impact-map.json`
- `reports/verification/<pr-id>/verification-results.json`
- existing run metadata when required to preserve execution state
- recorded specialist failures

Optional artifacts must never be fabricated when absent.

---

# Input Validation

Before synthesis:

1. validate `<pr-id>`
2. load `pr-context.json`
3. load `review-plan.json`
4. confirm both artifacts refer to the same Pull Request
5. validate required context fields
6. validate `risk_level`
7. validate `selected_reviewers`
8. validate `skipped_reviewers`
9. validate `reviewer_reasons` when present
10. determine which selected specialists completed successfully
11. confirm every successful selected specialist has its expected artifact
12. validate each specialist artifact
13. validate every specialist summary
14. validate every finding
15. validate verification results and verification summary when present
16. preserve recorded specialist failures and partial-review state

Stop when required artifacts are missing, malformed, conflicting, or unsafe to
consume.

Do not infer missing required artifacts.

Do not assume that a missing specialist artifact means zero findings.

---

# Review Plan Validation

The review plan should contain:

- `risk_level`
- `risk_triggers`
- `selected_reviewers`
- `skipped_reviewers`
- `reviewer_reasons`

The runtime may also persist execution-planning metadata.

Do not require or infer a hard reviewer-count budget.

Valid risk levels:

- `TRIVIAL`
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

The report command must not:

- add reviewers
- remove reviewers
- alter risk level
- recompute routing
- reclassify skipped reviewers

The persisted review plan remains authoritative for routing.

---

# Specialist Artifact Validation

For every successfully completed selected specialist artifact, validate:

- JSON object structure
- `specialist`
- `summary`
- `findings`
- specialist identity
- summary schema
- finding schema
- finding IDs
- severity values
- verification status values

The `specialist` value must match the expected selected specialist.

Do not silently accept:

- unknown specialist names
- malformed summaries
- malformed findings
- invalid severities
- unknown verification statuses
- duplicate finding IDs within the same specialist result
- model-selected artifact paths

---

# Specialist Summary Contract

Every successful specialist artifact must contain:

```json
{
  "specialist": "code-review-specialist",
  "summary": {
    "analysis": "What this specialist actually reviewed.",
    "result": "What the specialist concluded and the practical impact observed.",
    "implementation": "Where the reviewed behavior is implemented."
  },
  "findings": []
}
```

Required summary fields:

- `summary.analysis`
- `summary.result`
- `summary.implementation`

Each field must be a non-empty string.

The report stage must preserve the specialist-authored summary.

It must not:

- ask an LLM to rewrite it
- infer a missing summary from findings
- add files, routes, classes, schemas, models, workers, or implementation details
  not present in the stored result
- merge several specialist summaries into a new synthetic specialist conclusion
- change the specialist's result meaning
- fabricate a summary for a failed specialist

Safe deterministic Markdown formatting is allowed.

If a selected specialist completed successfully but its required summary is
missing or malformed:

- record an artifact inconsistency
- do not synthesize replacement prose
- stop or fail according to deterministic runtime policy

---

# Canonical Finding Validation

Every finding must contain:

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

# Action

## Stage 1 — Load Specialist Results

Load only artifacts belonging to successfully completed specialists selected by
the review plan.

For each valid artifact, preserve:

- specialist identity
- specialist summary
- findings
- specialist provenance

Do not consume results from unselected specialists.

Do not create findings during synthesis.

Do not perform a new model review pass.

---

## Stage 2 — Load Verification Results

When:

`reports/verification/<pr-id>/verification-results.json`

exists, validate:

- `pr_id`
- `summary.analysis`
- `summary.result`
- `summary.implementation`
- `results`
- each verification result

The verification summary is report content only.

It must not:

- alter finding severity
- alter finding category
- create findings
- modify specialist summaries
- replace original finding evidence
- change original finding meaning

---

## Stage 3 — Apply Verification Results

Apply each verification result by exact `finding_id`.

Verification may update:

- `verification_status`
- verification evidence
- verification method
- verification execution metadata
- verification notes

Verification must not update:

- severity
- category
- title
- original evidence
- original impact
- original recommendation
- original finding ID
- original finding meaning

Unknown verification references must not silently create findings.

If a verification artifact references a finding that does not exist:

- record an artifact inconsistency
- stop when trustworthy synthesis cannot be guaranteed

When no verification result exists for a finding, preserve its persisted
verification status.

When no verification artifact exists, preserve the specialist-provided
`verification_status`.

---

# Verification Status Handling

## REFUTED

Findings with:

`verification_status: REFUTED`

must be excluded from the active finding set.

They must not appear as:

- blocking findings
- advisory findings

They may remain under a separate `refuted` collection for auditability.

---

## NOT_APPLICABLE

Findings with:

`verification_status: NOT_APPLICABLE`

must not be classified as active blocking findings.

They should normally be excluded from the active finding set.

They may remain in structured history for traceability.

---

## VERIFICATION_FAILED

Findings with:

`verification_status: VERIFICATION_FAILED`

remain active unless another deterministic rule excludes them.

They are not automatically blocking.

They remain advisory unless later verification establishes a blocking state.

---

# Deduplication

Deduplicate findings only when they share the same underlying root cause.

Consider:

- same affected code path
- same defect mechanism
- same affected state
- same relevant file/location
- same practical effect

Do not deduplicate merely because:

- titles are similar
- categories are equal
- severities match
- files match

When multiple specialists report the same root cause:

- preserve the strongest concrete evidence
- preserve the clearest practical impact
- preserve the most actionable recommendation
- retain traceability to originating finding IDs
- preserve specialist provenance where useful

Do not invent a new defect while merging.

Do not increase severity merely because several specialists identified the same
root cause.

---

# Final Classification

Classification is deterministic.

## BLOCKING

A finding is `BLOCKING` only when:

- `verification_status == VERIFIED`
- and severity is `HIGH` or `CRITICAL`

Equivalent rule:

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

Equivalent rule:

`ADVISORY = remaining active findings`

Do not treat an unverified HIGH or CRITICAL finding as verified blocking
evidence.

---

# Report Summary

The final report should summarize, when available:

- PR identifier
- repository
- PR title
- risk level
- base SHA
- head SHA
- changed files count
- additions
- deletions
- selected reviewers
- skipped reviewers
- reviewer reasons
- risk triggers
- specialist reviews
- total findings
- blocking findings
- advisory findings
- refuted findings
- verified findings
- unverified findings
- verification failures
- verification usage
- specialist failures
- review completeness

Do not invent missing metrics.

---

# Partial Review State

If one or more selected specialists failed during the original review, preserve
that state.

Do not imply full review coverage.

Recommended deterministic states:

- `COMPLETE`
- `PARTIAL`
- `FAILED`

Use `PARTIAL` when:

- at least one selected specialist failed
- valid review evidence from other specialists still exists
- synthesis can proceed safely

Do not fabricate a specialist summary for a failed specialist.

---

# review.json

Write:

`reports/reviews/<pr-id>/review.json`

Recommended structure:

```json
{
  "pr_id": 42,
  "repository": "owner/repository",
  "title": "Example PR",
  "risk_level": "HIGH",
  "risk_triggers": [],
  "selected_reviewers": [
    "code-review-specialist"
  ],
  "skipped_reviewers": [],
  "reviewer_reasons": {},
  "specialist_reviews": [
    {
      "specialist": "code-review-specialist",
      "summary": {
        "analysis": "Stored specialist analysis summary.",
        "result": "Stored specialist result summary.",
        "implementation": "Stored specialist implementation summary."
      }
    }
  ],
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
  "verification": {
    "summary": null,
    "results": []
  },
  "execution": {
    "status": "COMPLETE",
    "specialist_failures": []
  }
}
```

Use structured fields instead of generated prose when possible.

The `specialist_reviews` collection must preserve the specialist-authored
summaries.

---

# review.md

Write:

`reports/reviews/<pr-id>/review.md`

The Markdown report must be:

- deterministic
- concise
- evidence-backed
- human-readable
- structurally stable

Do not use a new LLM reasoning pass to rewrite findings or summaries.

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

## Specialist Reviews

### <Specialist Display Name>

**Analysis**

<stored summary.analysis>

**Result**

<stored summary.result>

**Implementation**

<stored summary.implementation>

## Blocking Findings

## Advisory Findings

## Refuted Findings

## Verification

## Execution Notes

## Review Result
```

Sections with no applicable content may contain a concise explicit message such
as:

`No verified blocking findings.`

Do not silently omit important review state.

---

# Specialist Review Rendering

For every successfully completed selected specialist, render exactly one
subsection under:

`## Specialist Reviews`

Recommended deterministic display-name mapping:

- `code-review-specialist` → `Code Review`
- `security-review-specialist` → `Security Review`
- `database-review-specialist` → `Database Review`
- `api-review-specialist` → `API Review`
- `architecture-review-specialist` → `Architecture Review`
- `async-review-specialist` → `Async / Queue Review`

Each subsection must contain exactly:

```markdown
### Code Review

**Analysis**

<summary.analysis>

**Result**

<summary.result>

**Implementation**

<summary.implementation>
```

Rules:

- use the persisted specialist summary
- do not regenerate it
- do not paraphrase it with another model
- do not merge separate specialist summaries into one synthetic conclusion
- do not infer implementation locations
- do not fabricate content for failed specialists
- render summaries even when the specialist returned zero findings

If a specialist failed:

- do not render a fake specialist summary
- record the failure under `Execution Notes`
- preserve `PARTIAL` review status when applicable

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

When verification exists, include when relevant:

- verification method
- verification evidence
- verification notes

Do not embellish stored evidence.

Example:

```markdown
### SEC-001 — Missing authorization check

- Severity: `HIGH`
- Category: `AUTHORIZATION_REGRESSION`
- Verification: `VERIFIED`
- File: `src/api/admin.py:84`

**Evidence**

The updated route invokes the privileged operation without the existing role
check.

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

# Verification Rendering

When a verification artifact exists, render its persisted summary under:

`## Verification`

Recommended format:

```markdown
## Verification

**Analysis**

<verification summary.analysis>

**Result**

<verification summary.result>

**Implementation**

<verification summary.implementation>
```

Then render per-finding verification details when useful.

Do not:

- rewrite the verification summary
- infer new verification conclusions
- change verification status during rendering

---

# run-manifest.json

Write:

`reports/runs/<pr-id>/run-manifest.json`

Recommended fields:

- `pr_id`
- `operation`
- `inputs`
- `source_artifacts`
- `selected_reviewers`
- `executed_reviewers`
- `skipped_reviewers`
- `specialist_results`
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
  "selected_reviewers": [
    "code-review-specialist",
    "security-review-specialist"
  ],
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

The manifest is operational metadata, not a review finding artifact.

Do not fabricate:

- timing
- token counts
- model metrics
- performance metrics
- execution data not already recorded

---

# Determinism

Given the same valid source artifacts, report regeneration should produce the
same classification and logically equivalent output.

Do not introduce randomization.

Do not use LLM inference for:

- classification
- reviewer routing
- summary rewriting
- finding generation
- Markdown structure
- summary counts
- artifact paths
- verification interpretation

Python/runtime logic owns deterministic synthesis.

---

# Failure Handling

Stop with an explicit error when:

- `pr-context.json` is missing
- `review-plan.json` is missing
- required successful-specialist artifacts are missing
- JSON is malformed
- PR identifiers conflict
- selected reviewer artifacts are inconsistent
- specialist summary schema is invalid
- finding schema is invalid
- verification summary is malformed
- verification data references invalid findings in a way that prevents safe
  synthesis

Do not fabricate replacements.

When a non-critical optional artifact is unavailable:

- record the limitation
- continue only when synthesis remains trustworthy

---

## Missing Specialist Artifact

When a selected specialist is recorded as successfully completed but its
artifact is missing:

- record artifact inconsistency
- do not assume zero findings
- stop or fail according to deterministic runtime policy

---

## Missing Specialist Summary

When a successful specialist artifact does not contain valid:

- `summary.analysis`
- `summary.result`
- `summary.implementation`

then:

- record artifact inconsistency
- do not synthesize replacement prose
- stop or fail according to deterministic runtime policy

---

## Recorded Specialist Failure

If the original run explicitly recorded a specialist failure:

- preserve the failure
- do not require a fake successful artifact
- continue synthesis from valid specialist results when safe
- mark review coverage as partial

---

# Must Not

Do not:

- run `pr-triage`
- run specialist reviewers
- invoke specialist skills for new analysis
- invoke Ollama for new review reasoning
- run `finding-verifier`
- execute tests
- execute scanners
- execute migrations
- fetch additional repository context
- reload the PR diff for new analysis
- inspect new repository files for review
- create new findings
- change finding severity
- change finding category
- reinterpret finding meaning
- fabricate evidence
- fabricate metrics
- fabricate verification
- fabricate specialist results
- fabricate specialist summaries
- fabricate verification summaries
- rewrite specialist summaries with another model pass
- infer implementation locations not present in persisted summaries
- fabricate execution state
- modify production code
- modify migrations
- modify application configuration
- modify dependency files
- commit
- push
- merge
- publish
- automatically comment on GitHub

---

# Output Artifacts

Successful report regeneration must produce:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

All generated artifacts must remain under `reports/`.

---

# Completion

The command is complete only when:

- `<pr-id>` was validated
- required source artifacts were validated
- specialist summaries and findings were loaded safely
- every successfully completed selected specialist has a valid three-paragraph
  summary
- verification results and verification summary were applied when available
- inactive findings were handled
- root-cause deduplication completed
- final blocking/advisory classification completed
- specialist summaries were rendered into `review.md`
- verification summary was rendered when available
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

Inline output does not replace persisted artifacts.

---

# Completion Output

At completion, display a concise summary containing:

- PR identifier
- risk level
- review status
- selected reviewers
- executed reviewers
- specialist failures
- total active findings
- blocking findings
- advisory findings
- refuted findings
- verification usage
- generated artifact paths

Then display the generated:

`reports/reviews/<pr-id>/review.md`

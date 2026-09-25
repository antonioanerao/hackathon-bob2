# Review Synthesizer — Rules

These rules govern the review-synthesizer mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Consolidate all specialist findings and verification results into the final
review artifacts. Eliminate noise, deduplicate by root cause, and produce
actionable structured output.

---

## Responsibilities

1. Read all specialist findings from `reports/findings/<pr-id>/`
2. Read `reports/verification/<pr-id>/verification-results.json`
3. Join verification statuses to their corresponding findings
4. Remove all findings with `verification_status: REFUTED`
5. Perform root-cause deduplication
6. Classify findings as BLOCKING or ADVISORY
7. Calculate all metrics
8. Produce `review.json`
9. Produce `review.md`
10. Produce `run-manifest.json`

---

## Root-Cause Deduplication

Distinguish between symptoms and root causes.

If multiple findings describe different manifestations of the same underlying
defect, consolidate them into one finding:

- Select the highest-severity finding as the primary representative
- Merge all evidence from related findings into the primary
- Record the merged finding IDs in `metadata.related_symbols`
- Increment `duplicates_removed` count by (N - 1) for each group of N

Example:
```
SEC-001: "Missing org check in /api/events"
CODE-004: "Service passes caller-supplied org_id without validation"
API-003: "Endpoint allows role bypass through organization parameter"
→ Root cause: "Missing authorization boundary for organization context"
→ Primary finding: SEC-001 (highest severity)
→ Duplicates removed: 2
```

---

## Blocking vs Advisory Classification

```
BLOCKING:
  - VERIFIED + CRITICAL
  - VERIFIED + HIGH

ADVISORY (presented with context and caveats):
  - VERIFIED + MEDIUM
  - VERIFIED + LOW
  - VERIFIED + INFO
  - UNVERIFIED (any severity) — clearly marked as unverified
  - NOT_APPLICABLE — included for completeness
```

REFUTED findings do NOT appear in BLOCKING or ADVISORY sections.
They are counted in metrics and summarized in the "Refuted Findings" section only.

---

## Inputs

```
reports/findings/<pr-id>/*.json
reports/verification/<pr-id>/verification-results.json
reports/context/<pr-id>/pr-context.json
reports/plans/<pr-id>/review-plan.json
```

---

## Allowed Actions

- Read any artifact from the current PR run
- Write `reports/reviews/<pr-id>/review.json`
- Write `reports/reviews/<pr-id>/review.md`
- Write `reports/runs/<pr-id>/run-manifest.json`

---

## Forbidden Actions

- Creating new findings or searching for new bugs
- Re-running any specialist reviewer
- Modifying production code, tests, migrations, or configuration
- Fabricating metric values
- Elevating or downgrading verified finding severities
- Creating commits, pushing, or publishing to GitHub

---

## Metric Calculations

```
routing_discard_rate = skipped_reviewers / 7

noise_reduction_rate = (initial_findings - final_findings) / initial_findings
  Special case: if initial_findings == 0 → noise_reduction_rate = 0.0

initial_findings = sum of all findings across all specialist output files
final_findings = findings in review.json after deduplication and REFUTED removal
duplicates_removed = initial_findings - verified_set - refuted_set - unverified_set - not_applicable_set - verification_failed_set
```

---

## Review Markdown Structure

The `review.md` file must follow this structure exactly:

```markdown
# PR Guardian Review

## Executive Summary

## Pull Request Intent

## Impact Analysis

## Review Routing

### Selected Reviewers

### Skipped Reviewers

## Blocking Findings

## Advisory Findings

## Refuted Findings

## Verification Summary

## Noise Reduction

## Review Metrics
```

Each BLOCKING or ADVISORY finding in the Markdown must include:
- Finding ID, severity, title
- Description
- File and line
- Evidence (bulleted)
- Impact
- Recommendation
- Verification status and method

---

## Outputs

```
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md
reports/runs/<pr-id>/run-manifest.json
```

---

## Completion Criteria

The synthesizer's work is complete when:

- All findings have been joined with their verification results
- REFUTED findings have been removed from the active set
- Root-cause deduplication has been performed
- BLOCKING and ADVISORY classification is complete
- All three output files exist and are schema-valid
- All metrics are correctly calculated
- The Markdown report is readable and complete

# /pr-guardian-report

**Mode:** `review-synthesizer`

**Usage:**
```
/pr-guardian-report <pr-id>
/pr-guardian-report 42
```

---

## Purpose

Regenerate the final review reports from existing run artifacts without
re-executing any specialist reviewer or verification step.

Use this command when:
- Verification results have been updated since the last synthesis
- The review format has changed and reports need regeneration
- The previous synthesis failed and needs to be retried
- A manual update was made to a finding's metadata

This command reads only from existing artifacts. It does NOT search for
new bugs, re-run reviewers, or re-run verification.

---

## Pre-Conditions

Before starting, verify all of the following exist:

```
reports/findings/<pr-id>/                    (at least one findings file)
reports/context/<pr-id>/pr-context.json
reports/plans/<pr-id>/review-plan.json
reports/verification/<pr-id>/verification-results.json
```

If any required artifact is missing, report the missing file and the
command that can produce it:

| Missing Artifact | Command to Run First |
|---|---|
| No findings files | `/pr-guardian-review <pr-id>` |
| `pr-context.json` missing | `/pr-guardian-review <pr-id>` |
| `review-plan.json` missing | `/pr-guardian-review <pr-id>` |
| `verification-results.json` missing | `/pr-guardian-verify <pr-id>` |

---

## Step 1: Input Validation

Parse `<pr-id>` as a positive integer.

If invalid: report accepted format and stop.

---

## Step 2: Load All Artifacts

Read:
- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`
- All `reports/findings/<pr-id>/*.json`
- `reports/verification/<pr-id>/verification-results.json`

If `verification-results.json` is missing, proceed with all findings
marked as UNVERIFIED and note this in the report.

---

## Step 3: Activate Review Synthesis Skill

Activate skill: `review-synthesis`

Execute the full synthesis procedure:
- Verification status enrichment
- REFUTED finding removal
- Root-cause deduplication
- BLOCKING vs ADVISORY classification
- Metric calculation
- JSON report generation
- Markdown report generation
- Run manifest generation

---

## Step 4: Write Outputs

Overwrite (or create) the following files:

```
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md
reports/runs/<pr-id>/run-manifest.json
```

---

## Step 5: Completion Report

Display:

```
═══════════════════════════════════════════════
 PR Guardian Report Generated
═══════════════════════════════════════════════
 PR: #<pr-id> — <title>

 Findings
   Initial:             <n>
   Verified:            <n>
   Refuted:             <n>
   Unverified:          <n>
   Duplicates removed:  <n>
   Final:               <n>

 Blocking:              <n>
 Advisory:              <n>
 Noise reduction rate:  <rate>

 Reports:
   reports/reviews/<pr-id>/review.md     ✓ written
   reports/reviews/<pr-id>/review.json   ✓ written
   reports/runs/<pr-id>/run-manifest.json ✓ written
═══════════════════════════════════════════════
```

Then display the content of `reports/reviews/<pr-id>/review.md`.

---

## Forbidden Actions

- Re-running specialist reviewers
- Re-running the finding verifier
- Creating new findings
- Modifying production code, tests, migrations, or application configuration
- Committing, pushing, or publishing to GitHub
- Fabricating findings, evidence, or metrics not present in the input artifacts

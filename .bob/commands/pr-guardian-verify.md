# /pr-guardian-verify

**Mode:** `finding-verifier`

**Usage:**
```
/pr-guardian-verify <pr-id>
/pr-guardian-verify 42
```

---

## Purpose

Re-run or extend verification for an existing PR Guardian run without
re-executing the full review pipeline.

Use this command when:
- A previous run produced UNVERIFIED or VERIFICATION_FAILED findings
- New environment access allows previously blocked verifications to proceed
- The orchestrator requests targeted re-verification of specific findings

This command DOES NOT re-run specialist reviewers.
It operates exclusively on findings already produced.

---

## Pre-Conditions

Before starting, verify:

1. `reports/findings/<pr-id>/` exists and contains at least one findings file
2. `reports/context/<pr-id>/pr-context.json` exists

If pre-conditions are not met, report the missing artifacts and stop.

---

## Step 1: Input Validation

Parse `<pr-id>` as a positive integer.

If invalid: report accepted format and stop.

---

## Step 2: Load Existing Findings

Read all files matching:
```
reports/findings/<pr-id>/*.json
```

Collect all findings. Build the complete finding list.

---

## Step 3: Load Existing Verification Results

Read if it exists:
```
reports/verification/<pr-id>/verification-results.json
```

Identify findings that currently have:
- `verification_status: "UNVERIFIED"`
- `verification_status: "VERIFICATION_FAILED"`

These are the candidates for this verification run.

If no UNVERIFIED or VERIFICATION_FAILED findings exist, report:
```
No unverified findings found for PR #<id>.
All findings have been processed in a previous verification run.
```
and stop.

---

## Step 4: Verification Execution

Activate skill: `finding-verification`

Process candidates by priority:
1. CRITICAL severity
2. HIGH severity
3. MEDIUM severity
4. LOW severity (when cost is low)

For each candidate finding, execute the verification procedure defined
in the `finding-verification` skill.

---

## Step 5: Update Verification Results

Merge the new verification results with existing results:

- For findings that were previously UNVERIFIED or VERIFICATION_FAILED:
  update their status with the new result
- For findings already VERIFIED or REFUTED in a previous run:
  do NOT overwrite unless explicitly re-verifying by finding ID

Write updated results to:
```
reports/verification/<pr-id>/verification-results.json
```

---

## Step 6: Completion Report

Display:

```
═══════════════════════════════════════════════
 PR Guardian Verification Complete
═══════════════════════════════════════════════
 PR: #<pr-id>

 Findings processed this run:    <n>

 Results:
   VERIFIED:             <n>
   REFUTED:              <n>
   UNVERIFIED:           <n>
   NOT_APPLICABLE:       <n>
   VERIFICATION_FAILED:  <n>

 Updated: reports/verification/<pr-id>/verification-results.json
═══════════════════════════════════════════════
```

Note: To regenerate the final review reports incorporating the new
verification results, run:
```
/pr-guardian-report <pr-id>
```

---

## Forbidden Actions

- Re-running specialist reviewers
- Creating new findings
- Modifying production code, migrations, or application configuration
- Committing, pushing, or publishing to GitHub
- Overwriting VERIFIED or REFUTED findings from a previous run
  without explicit finding ID targeting
- Fabricating verification results or tool output

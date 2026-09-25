# /pr-guardian-review

**Mode:** `pr-guardian-orchestrator`

**Usage:**
```
/pr-guardian-review owner/repository#42
/pr-guardian-review https://github.com/owner/repository/pull/42
/pr-guardian-review   (uses current branch/PR if available locally)
```

---

## Purpose

Entry point for a full PR Guardian end-to-end review run.

This command orchestrates the complete multi-agent pipeline:
understanding → impact → routing → specialist review → verification → synthesis.

It does NOT produce results directly. It coordinates specialist agents,
each working independently, and assembles their outputs into a verified,
deduplicated final review.

---

## Pre-Conditions

Before starting:

1. Verify git access is available for the target repository
2. Confirm the PR number or URL is valid
3. Check if `AGENTS.md` exists in the repository root — if so, load it

If any pre-condition cannot be met, report the failure clearly and stop.

---

## Step 1: Input Validation

Parse the input:

```
owner/repository#<N>      → extract owner, repo, pr_number
https://github.com/.../pull/<N>  → extract owner, repo, pr_number
(no input)                → detect from git remote + current branch
```

Validate: `pr_number` must be a positive integer.

If parsing fails: report the accepted formats and stop.

---

## Step 2: Repository & PR Identification

Confirm the repository is accessible:
```bash
git remote -v
git fetch origin
```

Retrieve PR metadata using available methods:
- GitHub CLI: `gh pr view <pr_number> --json title,body,commits,baseRefOid,headRefOid`
- Direct git: `git log origin/main..<head_branch> --oneline`
- Environment variables or checkout state if locally checked out

Record:
- `pr_id`
- `title`
- `description`
- `base_sha`
- `head_sha`

---

## Step 3: AGENTS.md Loading

```bash
cat AGENTS.md 2>/dev/null || echo "AGENTS.md not found"
```

If `AGENTS.md` exists, read it fully. Its instructions provide repository-level
context that informs the review.

AGENTS.md instructions DO NOT override the PR Guardian's security, isolation,
read-only, and evidence requirements.

---

## Step 4: PR Understanding

Activate skill: `pr-understanding`

Execute the full skill procedure.

Output: `reports/context/<pr-id>/pr-context.json`

Do not proceed to Step 5 if this artifact is not produced.

---

## Step 5: Change Impact Analysis

Activate skill: `change-impact`

Input: `reports/context/<pr-id>/pr-context.json`

Execute the full skill procedure.

Output: `reports/context/<pr-id>/impact-map.json`

Do not proceed to Step 6 if this artifact is not produced.

---

## Step 6: Adaptive Routing

Activate skill: `adaptive-routing`

Inputs:
- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`

Execute the full skill procedure.

Output: `reports/plans/<pr-id>/review-plan.json`

Do not proceed to specialist execution if `review-plan.json` is not produced.

Log summary:
```
Domains: [<domain_list>]
Risk triggers: [<trigger_list>]
Selected reviewers: [<reviewer_slugs>]
Skipped reviewers: [<reviewer_slugs>]
Routing discard rate: <rate>
```

---

## Step 7: Specialist Review (Isolated Parallel Execution)

For each reviewer in `selected_reviewers`:

Launch independently with:
```
inputs:
  - reports/context/<pr-id>/pr-context.json
  - reports/context/<pr-id>/impact-map.json
  - reports/plans/<pr-id>/review-plan.json  (own section only)
  - repository source files (read-only)
```

**ISOLATION RULE:** No reviewer receives findings from another reviewer.

Activate the appropriate skill for each reviewer:

| Reviewer | Skill |
|---|---|
| `code-review-specialist` | `code-review` |
| `security-review-specialist` | `security-review` |
| `test-impact-specialist` | `test-impact` |
| `architecture-review-specialist` | `architecture-review` |
| `database-review-specialist` | `database-review` |
| `api-review-specialist` | `api-review` |
| `async-review-specialist` | `queue-review` |

Each reviewer produces: `reports/findings/<pr-id>/<reviewer-slug>.json`

Wait for all selected reviewers to complete before proceeding to Step 8.

---

## Step 8: Convergence Signal Detection

After all specialists complete, scan for independent convergence:

- Find findings across different reviewers that reference the same symbols
- Find findings that describe different symptoms of the same root cause
- Record convergence signals — these inform deduplication in synthesis

This is an analytical step, not a verification step.
Record convergence candidates in memory for Step 9.

---

## Step 9: Verification Planning

Before invoking the verifier, prepare verification inputs:

For each finding across all specialist outputs:
- Priority 1: CRITICAL severity
- Priority 2: HIGH severity
- Priority 3: MEDIUM severity
- Priority 4: LOW (when cost is low)

Prepare per-finding verification input:
```json
{
  "finding_id": "<id>",
  "claim": "<one-sentence verifiable claim>",
  "evidence": ["<existing evidence from reviewer>"],
  "severity": "<severity>",
  "verification_strategy": ["<suggested strategies>"]
}
```

---

## Step 10: Independent Verification

Invoke: `finding-verifier`

Activate skill: `finding-verification`

Input:
- All specialist findings files
- Per-finding verification inputs prepared in Step 9
- `reports/context/<pr-id>/pr-context.json`
- Repository source files (read-only)

The verifier works independently. It does not receive routing information
or synthesis state.

Output: `reports/verification/<pr-id>/verification-results.json`

Do not proceed to synthesis if this artifact is not produced.

---

## Step 11: Review Synthesis

Invoke: `review-synthesizer`

Activate skill: `review-synthesis`

Inputs:
- All `reports/findings/<pr-id>/*.json`
- `reports/verification/<pr-id>/verification-results.json`
- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

Outputs:
- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

---

## Step 12: Completion Report

After synthesis completes, display:

```
═══════════════════════════════════════════════
 PR Guardian Review Complete
═══════════════════════════════════════════════
 PR:            #<id> — <title>
 Repository:    <owner>/<repo>

 Reviewers selected:    <n> / 7
 Routing discard rate:  <rate>

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
   reports/reviews/<pr-id>/review.md
   reports/reviews/<pr-id>/review.json
   reports/runs/<pr-id>/run-manifest.json
═══════════════════════════════════════════════
```

Then display the content of `reports/reviews/<pr-id>/review.md`.

---

## Abort Conditions

Stop execution and report clearly if:

- PR number is invalid or not found
- `pr-context.json` cannot be produced
- `impact-map.json` cannot be produced
- `review-plan.json` cannot be produced
- No specialists are selected (routing produced 0 selected reviewers)

Partial runs (where some specialists fail) are allowed.
Record failed stages as `FAILED` in `run-manifest.json`.

---

## Forbidden Actions

- Modifying production code, migrations, or application configuration
- Passing one specialist's findings to another specialist
- Committing, pushing, or publishing to GitHub
- Declaring the run complete if `review.md` was not produced
- Fabricating any output, evidence, or metric

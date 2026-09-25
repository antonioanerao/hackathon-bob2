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

Entry point for a PR Guardian end-to-end review run.

The workflow is **deterministic-first, minimum-agents**:
understand → measure risk → pre-scan → route within budget → verify only when justified → synthesize.

Specialists are spawned only when their routing triggers fire.
No specialist is mandatory by default.

---

## Guiding Principles

> **Don't just comment. Prove it.**

> **Use the minimum number of agents required to establish confidence.**

---

## Pre-Conditions

1. Verify git access is available for the target repository
2. Confirm the PR number or URL is valid
3. Check if `AGENTS.md` exists in the repository root — if so, load it

---

## Step 1: Input Validation

Parse the input:

```
owner/repository#<N>              → extract owner, repo, pr_number
https://github.com/.../pull/<N>  → extract owner, repo, pr_number
(no input)                        → detect from git remote + current branch
```

Validate: `pr_number` must be a positive integer. If parsing fails, stop.

---

## Step 2: Repository & PR Identification

Retrieve PR metadata using available methods:

```bash
gh pr view <pr_number> --json title,body,commits,baseRefOid,headRefOid
# or:
git log origin/main..<head_branch> --oneline
```

Record: `pr_id`, `title`, `description`, `base_sha`, `head_sha`

---

## Step 3: AGENTS.md Loading

```bash
cat AGENTS.md 2>/dev/null || echo "AGENTS.md not found"
```

If `AGENTS.md` exists, read it fully. Its instructions inform the review.
AGENTS.md does NOT override PR Guardian's security, isolation, and read-only rules.

---

## Step 4: PR Understanding (skill — orchestrator context)

Activate skill: `pr-understanding`

Execute directly in the orchestrator's context. **Do not spawn a subagent.**

Output: `reports/context/<pr-id>/pr-context.json`

Do not proceed to Step 5 if this artifact is not produced.

---

## Step 5: Change Impact Analysis (skill — orchestrator context)

Activate skill: `change-impact`

Input: `reports/context/<pr-id>/pr-context.json`

Execute directly in the orchestrator's context. **Do not spawn a subagent.**

Output: `reports/context/<pr-id>/impact-map.json`

Do not proceed to Step 6 if this artifact is not produced.

---

## Step 6: Deterministic Pre-scan

Before spawning any specialist, run deterministic tools once, based on changed files.
Results populate `context-package.json` and are consumed by specialists — not re-run.

Select tools based on what changed:

| Condition                          | Tool              | Example command                           |
|------------------------------------|-------------------|-------------------------------------------|
| Python files changed               | `ruff check`      | `ruff check <changed_file> --output-format=json` |
| Security-sensitive Python changed  | `bandit`          | `bandit -r <changed_file> -f json`        |
| Testable logic changed             | targeted `pytest` | `pytest tests/test_<module>.py -v --tb=short` |
| Dependency manifest changed        | `pip-audit`       | `pip-audit --format json`                 |
| Semgrep rules present              | `semgrep`         | `semgrep --config=auto <changed_file> --json` |

Run each applicable tool **at most once**. Do not run tools that are not applicable.
Record results (pass/fail + summary) in `context-package.json`.

---

## Step 7: Produce context-package.json

After PR understanding, impact analysis, and deterministic pre-scan, produce:

`reports/context/<pr-id>/context-package.json`

This is the single shared context artifact for all specialists.
See `04-artifact-contracts.md` for the full schema.

---

## Step 8: Risk Classification + Adaptive Routing (skill — orchestrator context)

Activate skill: `adaptive-routing`

Inputs:
- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/context/<pr-id>/context-package.json`

Execute directly in the orchestrator's context. **Do not spawn a subagent.**

The skill classifies `risk_level` and calculates `agent_budget`, then selects reviewers.

Output: `reports/plans/<pr-id>/review-plan.json`

Log:
```
Risk Level: <risk_level>
Agent Budget: max_reviewers=<n>, max_verifiers=<n>
Domains: [<domain_list>]
Risk triggers: [<trigger_list>]
Selected reviewers: [<slugs>]
Skipped reviewers: [<slugs>]
Routing discard rate: <rate>
```

---

## Step 9: Fast Path Check

If `risk_level` is TRIVIAL:
- Skip all specialists
- Proceed directly to Step 12 (Synthesis)

If `risk_level` is LOW and only `code-review-specialist` is selected:
- This is a FAST PATH run
- Continue to Step 10 with a single specialist
- Skip verification (max_verifiers = 0 for LOW)
- Proceed directly to inline synthesis in Step 12

---

## Step 10: Specialist Review (Isolated, Minimal Context, Within Budget)

For each reviewer in `selected_reviewers` (up to `agent_budget.max_reviewers`):

**Do not spawn more specialists than the budget allows.**

Each specialist receives only:

```
context-package.json         — shared context (no full repo)
changed files for their domain
relevant callers/callees from impact map
relevant test files
specific deterministic results for their domain
```

**Never instruct a specialist to "inspect the entire repository."**

Use the instruction:
> "Inspect only the files and symbols listed in your context package.
>  Expand scope only when concrete evidence requires it."

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

**ISOLATION RULE:** No reviewer receives findings from another reviewer.

Each reviewer produces: `reports/findings/<pr-id>/<reviewer-slug>.json`

Wait for all selected reviewers to complete before proceeding to Step 11.

---

## Step 11: Verification Budget Decision

Check whether verification is justified:

| Condition | Action |
|-----------|--------|
| `agent_budget.max_verifiers == 0` (TRIVIAL or LOW) | Skip verification entirely. Record stage as SKIPPED. |
| No CRITICAL or HIGH findings | Skip verification. Record stage as SKIPPED. |
| CRITICAL or HIGH findings exist | Invoke `finding-verifier` with a batch of relevant findings |
| MEDIUM findings only, all with CERTAIN confidence | Skip verification. |
| MEDIUM findings with POSSIBLE confidence | Optionally invoke verifier if cost is low |

**Invoke `finding-verifier` at most once per run** with a finding batch — not once per finding.

Prepare the verification batch:
```json
{
  "verification_batch": [
    { "finding_id": "<id>", "claim": "<verifiable claim>", "severity": "<severity>", "evidence": [], "verification_strategy": [] }
  ]
}
```

Include:
- All CRITICAL findings
- All HIGH findings
- MEDIUM findings where `confidence != CERTAIN`

Exclude:
- LOW findings
- INFO findings
- Findings already supported by deterministic tool proof from the pre-scan

Output: `reports/verification/<pr-id>/verification-results.json`

---

## Step 12: Convergence Signal Detection

After all specialists complete, scan for independent convergence:
- Findings across different reviewers referencing the same symbols
- Different symptoms of the same root cause

Record convergence candidates in memory for synthesis.

---

## Step 13: Synthesis

**By default, execute the `review-synthesis` skill directly** (no subagent spawned).

Activate skill: `review-synthesis`

Inputs:
- All `reports/findings/<pr-id>/*.json`
- `reports/verification/<pr-id>/verification-results.json` (or SKIPPED)
- `reports/context/<pr-id>/pr-context.json`
- `reports/plans/<pr-id>/review-plan.json`

Outputs:
- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

**Spawn `review-synthesizer` as subagent only when:**
- More than 3 specialists contributed findings
- Total initial findings exceed 15
- Deduplication complexity is high
- Orchestrator context capacity is a constraint

---

## Step 14: Completion Report

After synthesis completes, display:

```
═══════════════════════════════════════════════════════════
 PR Guardian Review Complete
═══════════════════════════════════════════════════════════
 PR:            #<id> — <title>
 Repository:    <owner>/<repo>

 Risk Level:    <risk_level>

 Available Reviewers:   7
 Selected Reviewers:    <n>
 Skipped Reviewers:     <7-n>
 Routing Discard Rate:  <rate>

 Executed:
   <list of selected reviewer slugs>

 Skipped:
   <list of skipped reviewer slugs>

 Verifier:
   <"Executed for <n> CRITICAL/HIGH findings" OR "Not invoked (budget / no qualifying findings)">

 Synthesizer:
   <"Executed by orchestrator (inline)" OR "Spawned as subagent">

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

 Agent Efficiency:
   Executed agents:     <n> / 9
   Avoidance rate:      <rate>

 Reports:
   reports/reviews/<pr-id>/review.md
   reports/reviews/<pr-id>/review.json
   reports/runs/<pr-id>/run-manifest.json
═══════════════════════════════════════════════════════════
```

Then display the content of `reports/reviews/<pr-id>/review.md`.

---

## Abort Conditions

Stop execution and report clearly if:

- PR number is invalid or not found
- `pr-context.json` cannot be produced
- `impact-map.json` cannot be produced
- `review-plan.json` cannot be produced

**Zero selected specialists is NOT an abort condition for TRIVIAL PRs.**
Record it as a successful TRIVIAL run.

Partial runs (where some specialists fail) are allowed.
Record failed stages as `FAILED` in `run-manifest.json`.

---

## Forbidden Actions

- Modifying production code, migrations, or application configuration
- Passing one specialist's findings to another specialist
- Committing, pushing, or publishing to GitHub
- Declaring the run complete if `review.md` was not produced
- Fabricating any output, evidence, or metric
- Spawning a subagent for PR understanding, change impact, or repository discovery
- Running the same deterministic tool more than once per run
- Spawning more specialists than `agent_budget.max_reviewers`
- Spawning a separate verifier for each finding (batch only)

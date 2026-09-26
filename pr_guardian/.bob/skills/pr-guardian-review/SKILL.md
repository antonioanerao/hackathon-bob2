---
name: pr-guardian-review
description: >
  Runs the complete PR Guardian review pipeline using one-time PR discovery,
  lazy context loading, dynamically selected specialists, optional targeted
  verification, deterministic synthesis, and auditable artifact generation.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-review

## Usage

`/pr-guardian-review <owner/repo#pr | PR URL>`

Mode: `pr-guardian-orchestrator`

---

# Purpose

Run the complete PR Guardian review lifecycle for one Pull Request.

The pipeline must:

- collect PR metadata once
- classify review risk
- route only to justified specialists
- minimize context and tool usage
- preserve specialist independence
- verify only findings that justify additional proof
- persist all required artifacts
- synthesize the final result deterministically

The review must optimize for trustworthy evidence, not finding volume.

---

# Core Principles

The command follows these principles:

> Collect once. Reuse everywhere.

> Load knowledge lazily, not globally.

> Reviewers find. Verifier proves.

> Python enforces.

The model performs reasoning.

The runtime controls:

- routing
- validation
- reviewer registry
- budgets
- artifact paths
- persistence
- verification eligibility
- final classification
- execution boundaries

---

# Input

Accepted formats:

- `owner/repository#42`
- `https://github.com/owner/repository/pull/42`

The PR reference must identify exactly one Pull Request.

Pass the PR reference unchanged to:

`scripts/collect-pr-context.sh "<pr-ref>"`

Do not rewrite the input before collection unless deterministic input validation requires it.

---

# Discovery

Run:

`scripts/collect-pr-context.sh "<pr-ref>"`

once during normal execution.

Supported input formats:

```text
owner/repository#42
```

or:

```text
https://github.com/owner/repository/pull/42
```

When collection succeeds, its output becomes authoritative for the current run.

Do not rediscover PR metadata through unrelated commands.

---

# Collected Context

The collector should provide compact metadata such as:

- PR identifier
- repository name
- title
- description preview
- base SHA
- head SHA
- additions
- deletions
- changed files
- changed file count
- technology hints
- collection method

Do not store the complete PR diff inside `pr-context.json`.

---

# Stage 1 — Validate Input

Before discovery:

1. ensure a PR reference was provided
2. reject empty values
3. reject obviously malformed values
4. prevent path injection or shell-argument manipulation
5. pass the validated reference unchanged to the collector

Do not attempt manual repository discovery before the collector runs.

---

# Stage 2 — Collect PR Context

Execute the collector once.

Persist:

`reports/context/<pr-id>/pr-context.json`

The context artifact should contain compact, reusable metadata.

Do not perform broad repository inspection during this stage.

---

# Context Collection Failure

If the collector fails:

- inspect the returned error
- use only the collector's supported fallback behavior
- do not silently fabricate metadata
- stop if minimum PR context cannot be established

Minimum required context should include enough information to identify:

- PR
- repository
- changed files
- change size
- base/head state

---

# Stage 3 — Load Triage

Load only:

- global rules
- `pr-triage`

Do not preload specialist skills.

Do not preload verification instructions.

Provide triage with:

- collected PR context
- available reviewer registry
- relevant technology hints
- changed-file metadata
- risk-routing constraints

---

# Reviewer Registry

Available reviewers must come from runtime configuration.

Typical source:

`PR_GUARDIAN_SPECIALISTS`

Example mapping:

```text
code-review-specialist:code-review
security-review-specialist:security-review
database-review-specialist:database-review
api-review-specialist:api-review
architecture-review-specialist:architecture-review
async-review-specialist:queue-review
```

The runtime must treat this registry as authoritative.

Triage may only select reviewers that exist in this registry.

---

# Triage Responsibilities

`pr-triage` is responsible only for:

- understanding the change
- identifying affected domains
- identifying risk triggers
- assigning risk level
- selecting reviewers
- defining the agent budget
- identifying obvious fast-path conditions

It must not:

- perform specialist review
- emit final findings
- perform verification
- generate final reports

---

# Triage Output

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

---

# Review Plan Validation

Before using the triage output, validate:

- response is valid JSON
- `risk_level` is valid
- budget values are valid integers
- selected reviewers are known
- skipped reviewers are known
- selected reviewers do not exceed budget
- selected and skipped reviewers do not conflict

Reject:

- GitHub usernames
- human reviewer names
- arbitrary agent names
- unregistered specialists

Do not silently trust model routing.

---

# Stage 4 — Persist Triage Artifacts

Persist:

- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`

The review plan becomes the authoritative routing artifact for the rest of the run.

---

# Agent Budget

Default maximum budget:

| Risk | Max Reviewers | Max Verifiers |
|---|---:|---:|
| `TRIVIAL` | 0 | 0 |
| `LOW` | 1 | 0 |
| `MEDIUM` | 2 | 1 |
| `HIGH` | 3 | 1 |
| `CRITICAL` | 4 | 1 |

The budget is a ceiling.

It is not a target.

Do not execute extra reviewers merely because capacity remains.

---

# Fast Path

## TRIVIAL

Flow:

`context → triage → synthesis`

Expected behavior:

- no specialist
- no verifier
- no full diff required
- no findings artifact required

---

## LOW

Flow:

`context → triage → max 1 reviewer → synthesis`

Verification is normally skipped.

---

## MEDIUM / HIGH / CRITICAL

Follow the validated review plan and budget.

Do not automatically use the maximum reviewer count.

---

# Stage 5 — Context Budget

Default exploration limits:

- discovery commands: max 2
- initial file reads: max 3
- files per specialist: max 5
- pre-scan tools: max 2
- verifier invocations: max 1

These are operational defaults.

Expansion is allowed only when a concrete risk or finding hypothesis requires more evidence.

Do not expand merely because additional repository data exists.

---

# Stage 6 — Lazy Diff Loading

Load the PR diff only if:

`selected_reviewers` is not empty.

Flow:

```text
triage
  ↓
selected_reviewers?
  │
  ├── none → skip diff
  │
  └── some → load diff once
```

Load the diff once and reuse it.

Do not retrieve the same diff separately for each specialist.

---

# Stage 7 — Deterministic Pre-scan

Run deterministic checks only when clearly relevant.

Examples may include:

- lightweight static analysis
- dependency inspection
- schema inspection
- syntax validation
- OpenAPI diff
- configuration checks

Rules:

- run each check at most once per run
- reuse output across applicable specialists
- do not run broad scanners by default
- do not run full test suites
- do not execute a tool without a concrete review purpose

---

# Stage 8 — Load Specialist Skills

Load only the skills mapped to:

`selected_reviewers`

Do not load unrelated skills.

For each specialist:

1. resolve reviewer → skill mapping
2. load its `SKILL.md`
3. prepare minimal relevant context
4. execute the specialist independently
5. validate its output
6. persist its findings

---

# Specialist Isolation

Each specialist must operate independently.

A specialist may receive:

- global rules
- its own skill
- PR context
- relevant changed code
- relevant deterministic evidence

A specialist must not receive:

- another specialist's findings
- another specialist's reasoning
- final synthesis state
- unrelated specialist skills

This preserves independent judgment and avoids confirmation bias.

---

# Parent Mode Stability

The parent execution remains:

`pr-guardian-orchestrator`

throughout the run.

Do not switch the parent into:

- code-review-specialist
- security-review-specialist
- database-review-specialist
- api-review-specialist
- architecture-review-specialist
- async-review-specialist
- finding-verifier

Specialists and verifier are delegated execution roles.

---

# Specialist Output Contract

Each specialist must return canonical JSON.

Example:

```json
{
  "specialist": "code-review-specialist",
  "findings": []
}
```

With findings:

```json
{
  "specialist": "code-review-specialist",
  "findings": [
    {
      "id": "CODE-001",
      "severity": "MEDIUM",
      "category": "STATE_REGRESSION",
      "title": "State update can become inconsistent",
      "file": "src/service.py",
      "line": 91,
      "evidence": "Concrete changed-code evidence.",
      "impact": "Practical runtime impact.",
      "recommendation": "Actionable remediation.",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

---

# Specialist Output Validation

Treat every specialist response as untrusted.

Validate:

- JSON object
- expected specialist identity
- findings list
- required finding fields
- severity enum
- verification status
- finding ID format
- file reference plausibility
- no model-selected output path

Reject malformed results.

Do not silently normalize unsafe responses.

---

# Finding Gate

A finding is valid only when it represents a concrete defect, regression, vulnerability, integrity issue, or domain-specific failure introduced, exposed, or materially affected by the PR.

Do not report:

- style
- formatting
- naming preferences
- generic refactoring
- generic SOLID advice
- theoretical future misuse
- unsupported security concerns
- missing tests without demonstrated behavior risk
- speculative performance concerns
- pre-existing unrelated defects

If no defect exists, the specialist must return:

```json
{
  "specialist": "<specialist>",
  "findings": []
}
```

---

# Stage 9 — Persist Specialist Findings

The orchestrator persists each successful specialist result under:

`reports/findings/<pr-id>/<specialist>.json`

Examples:

- `code-review-specialist.json`
- `security-review-specialist.json`
- `database-review-specialist.json`
- `api-review-specialist.json`
- `architecture-review-specialist.json`
- `async-review-specialist.json`

Specialists do not write these files themselves.

---

# Specialist Failure

If a selected specialist fails:

- record the failure
- continue other independent specialists when safe
- do not create a fake successful empty result
- do not reinterpret failure as no findings
- preserve successful specialist artifacts
- expose the failure in `run-manifest.json`

A partial review must remain identifiable as partial.

---

# Missing Specialist Capability

If a specialist cannot prove a suspected issue because execution or another capability is unavailable:

- do not switch modes
- do not substitute an unrelated specialist
- do not retry with arbitrary tooling
- return the finding as `UNVERIFIED` when justified
- allow later verification when eligible

---

# Stage 10 — Verification Decision

Invoke `finding-verifier` only when both conditions hold:

1. verifier budget > 0
2. at least one eligible finding exists

Default eligible severities:

- `CRITICAL`
- `HIGH`
- selected uncertain `MEDIUM`

Do not verify `LOW` by default.

---

# MEDIUM Verification

A MEDIUM finding may justify verification when:

- current evidence is incomplete
- the claim is testable
- verification can materially increase confidence
- engineering action depends on the result
- proof can be obtained with bounded effort

Do not verify MEDIUM findings simply to use available budget.

---

# Batched Verification

Prefer one verification batch per run.

Maximum default:

`1 invocation`

When multiple findings qualify:

- send them together
- preserve independent hypotheses
- preserve per-finding evidence
- preserve separate results

Do not let one finding influence another's status.

---

# Verification Output

If verification runs, persist:

`reports/verification/<pr-id>/verification-results.json`

Each result should contain:

- `finding_id`
- `status`
- `method`
- `evidence`
- `command`
- `exit_code`
- `notes`

---

# Valid Verification Statuses

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

`VERIFIED` requires positive supporting evidence.

`REFUTED` requires positive contradicting evidence.

Absence of evidence is not refutation.

---

# Stage 11 — Apply Verification Results

Apply verification by exact `finding_id`.

Verification may update:

- verification status
- verification evidence
- verification method
- execution metadata

Verification must not update:

- severity
- category
- original finding ID
- original finding meaning

Reject invalid verification references when safe synthesis cannot be guaranteed.

---

# Stage 12 — Synthesis

Final synthesis is deterministic.

The orchestrator/runtime must:

1. load persisted findings
2. apply verification results
3. remove inactive findings
4. deduplicate by root cause
5. classify findings
6. generate final reports

Do not perform another general LLM review pass during synthesis.

---

# REFUTED Findings

Findings marked:

`REFUTED`

must be removed from the active set.

They must not appear as:

- blocking
- advisory

They may remain in structured historical data.

---

# NOT_APPLICABLE Findings

Findings marked:

`NOT_APPLICABLE`

must not be classified as active blocking findings.

They may remain in verification history for auditability.

---

# VERIFICATION_FAILED Findings

Findings marked:

`VERIFICATION_FAILED`

remain active unless otherwise excluded.

They remain advisory until a later successful verification establishes another state.

---

# Deduplication

Deduplicate only by root cause.

Consider:

- same code path
- same defect mechanism
- same relevant state
- same location
- same practical effect

Do not merge findings merely because:

- titles are similar
- categories match
- severities match
- files match

Preserve:

- strongest evidence
- clearest impact
- useful provenance
- original finding IDs

---

# Final Classification

## BLOCKING

A finding is blocking only when:

- severity is `HIGH` or `CRITICAL`
- and `verification_status == VERIFIED`

Equivalent:

`BLOCKING = VERIFIED + CRITICAL|HIGH`

---

## ADVISORY

All remaining active findings are advisory.

Examples:

- verified MEDIUM
- verified LOW
- unverified HIGH
- unverified CRITICAL
- unverified MEDIUM
- verification failure

Do not treat uncertainty as blocking proof.

---

# Stage 13 — Generate Final Artifacts

Write:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

The runtime controls structure and paths.

The model must not choose output destinations.

---

# review.json

Recommended top-level structure:

- `pr_id`
- `repository`
- `title`
- `risk_level`
- `risk_triggers`
- `selected_reviewers`
- `skipped_reviewers`
- `summary`
- `blocking`
- `advisory`
- `refuted`
- `verification`
- `execution`

Use structured values instead of generated prose when possible.

---

# review.md

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

Do not embellish stored evidence.

---

# run-manifest.json

Record operational state.

Recommended fields:

- `pr_id`
- `operation`
- `model`
- `risk_level`
- `selected_reviewers`
- `executed_reviewers`
- `skipped_reviewers`
- `specialist_results`
- `specialist_failures`
- `verification_used`
- `verification_skip_reason`
- `finding_counts`
- `artifacts`
- `status`

Do not fabricate metrics that were not recorded.

---

# Review Status

Recommended deterministic states:

- `COMPLETE`
- `PARTIAL`
- `FAILED`

Use `PARTIAL` when:

- one or more selected specialists failed
- valid review evidence still exists
- synthesis can proceed safely

Do not report `COMPLETE` when required review coverage failed.

---

# Abort Conditions

Stop the pipeline when:

- PR input is invalid
- PR is unavailable
- context collection cannot provide minimum metadata
- triage returns malformed JSON
- triage returns unknown reviewers
- review plan cannot be safely validated
- required artifact integrity is irrecoverably broken

Do not continue with fabricated state.

---

# Non-Fatal Failures

The following may be non-fatal when safe:

- one specialist failure
- verification infrastructure failure
- optional pre-scan failure
- unavailable optional artifact

Record the failure explicitly.

Do not hide degraded review coverage.

---

# LLM Output Is Untrusted

Validate all model output before use.

Never directly trust model-provided:

- reviewer identifiers
- severity
- status
- file paths
- commands
- tool results
- JSON structure

The runtime enforces all execution boundaries.

---

# Production Safety

Production code is read-only.

Do not:

- modify source code
- modify migrations
- modify configuration
- modify dependency manifests
- modify deployment files
- commit
- push
- merge
- publish
- post GitHub comments automatically

Generated artifacts must remain under:

`reports/`

Temporary verification files may exist only under:

`reports/verification/<pr-id>/tests/`

---

# Must Not

Do not:

- preload specialist skills
- spawn unselected reviewers
- rediscover PR metadata after successful collection
- reload identical PR diff unnecessarily
- give specialists each other's findings
- switch parent mode into a specialist
- run broad speculative repository scans
- run full test suites by default
- run scanners without purpose
- fabricate findings
- fabricate evidence
- fabricate runtime behavior
- fabricate CVEs
- fabricate query plans
- fabricate tool output
- change finding severity during verification
- create findings during synthesis
- modify production code
- commit
- push
- merge
- publish

---

# Completion Criteria

A run is successful only when:

- valid PR context exists
- impact map exists
- review plan exists
- routing is valid
- all successful selected specialists returned valid results
- specialist findings were persisted
- specialist failures were explicitly recorded
- verification completed or was explicitly skipped
- synthesis completed
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

For `TRIVIAL` reviews:

- no findings artifact is required
- full diff may be skipped
- verification is skipped

Inline output does not replace required artifacts.

---

# Completion Output

At completion, show a concise summary containing:

- PR identifier
- repository
- risk level
- selected reviewers
- executed reviewers
- specialist failures
- total findings
- blocking findings
- advisory findings
- refuted findings
- verification state
- review status
- generated artifact paths

Example:

```text
PR #42
Repository: owner/repository
Risk: HIGH
Status: COMPLETE

Reviewers:
- code-review-specialist
- security-review-specialist

Findings: 3
Blocking: 1
Advisory: 2
Refuted: 0

Verification: applied

Artifacts:
reports/reviews/42/review.json
reports/reviews/42/review.md
reports/runs/42/run-manifest.json
```

Then display:

`reports/reviews/<pr-id>/review.md`

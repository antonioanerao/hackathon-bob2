---
name: pr-guardian-review
description: >
  Runs the complete PR Guardian review pipeline using collected PR context,
  triage, dynamically configured specialist reviewers, optional verification,
  deterministic synthesis, and auditable artifact generation.
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /pr-guardian-review

## Usage

`/pr-guardian-review <owner/repo#pr | PR URL>`

Mode: `pr-guardian-orchestrator`

## Purpose

Execute the full PR Guardian review lifecycle.

The command must:

- collect PR context once
- classify review risk
- select only relevant specialists
- execute specialists independently
- persist structured findings
- optionally verify eligible findings
- synthesize the final result deterministically
- produce auditable review artifacts

The command must not perform unnecessary inference or repository exploration.

---

## Core Principles

The review follows these principles:

> Collect once. Reuse everywhere.

> Load knowledge lazily, not globally.

> Reviewers find. Verifier proves.

> Python enforces.

The LLM performs reasoning.

The runtime enforces:

- routing
- schemas
- reviewer validity
- filesystem destinations
- verification rules
- artifact persistence
- final classification

---

## Input

Accepted PR references:

- `owner/repository#42`
- `https://github.com/owner/repository/pull/42`

The PR reference must identify exactly one Pull Request.

---

## Discovery

Run:

`scripts/collect-pr-context.sh "<pr-ref>"`

exactly once during normal execution.

The successful collector output is authoritative for:

- PR identifier
- repository
- PR title
- description preview
- base SHA
- head SHA
- additions
- deletions
- changed files
- repository technology hints

Do not rediscover metadata already collected.

Do not store the complete diff in `pr-context.json`.

Use a fallback only when collection fails or required context is incomplete.

---

## Stage 1 — Context Collection

Validate the PR input.

Run the context collector.

Persist:

- `reports/context/<pr-id>/pr-context.json`

The context artifact should remain compact.

It must not contain unnecessary repository content.

---

## Stage 2 — Triage

Load:

- global rules
- `pr-triage`

Provide triage with:

- PR context
- available specialist reviewers
- relevant repository hints

The available reviewer list must come from runtime discovery of
`.bob/skills/*/SKILL.md` files with `reviewer_id` metadata.

Triage responsibilities are limited to:

- understand the change
- identify affected domains
- determine risk
- identify risk triggers
- select reviewers
- define agent budget

Triage must not perform specialist review.

---

## Triage Output

The review plan must contain:

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

The runtime must validate that every selected and skipped reviewer exists in the configured specialist set.

Unknown reviewer names must cause triage failure.

Do not accept:

- usernames
- GitHub handles
- developer names
- arbitrary reviewer identifiers

---

## Stage 3 — Triage Artifacts

Persist:

- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`

The review plan becomes the authoritative routing decision for the run.

---

## Agent Budget

Default maximum reviewer/verifier budget:

| Risk | Max Reviewers | Max Verifiers |
|---|---:|---:|
| `TRIVIAL` | 0 | 0 |
| `LOW` | 1 | 0 |
| `MEDIUM` | 2 | 1 |
| `HIGH` | 3 | 1 |
| `CRITICAL` | 4 | 1 |

The budget is a ceiling, not a target.

Do not execute reviewers simply because budget remains available.

---

## Fast Path

### TRIVIAL

Flow:

`context → triage → synthesis`

No specialist is required.

No findings artifact is required.

### LOW

Flow:

`context → triage → at most 1 specialist → synthesis`

Verification is skipped by default.

### MEDIUM / HIGH / CRITICAL

Follow the review plan and agent budget.

---

## Stage 4 — Lazy Diff Loading

Load the PR diff only when one or more specialists were selected.

Flow:

```text
triage
   ↓
selected_reviewers empty?
   │
   ├── yes → skip diff
   │
   └── no
        ↓
      load diff
```

Do not load the full diff before triage unless required to establish the review plan.

---

## Stage 5 — Specialist Execution

Load only skills corresponding to:

`selected_reviewers`

Do not preload unrelated skills.

Each selected specialist must run independently.

Each specialist receives only:

- global rules
- its own `SKILL.md`
- PR context
- relevant changed code
- relevant deterministic evidence, when available

A specialist must not receive:

- another specialist's findings
- unrelated skills
- unrelated repository content
- final synthesis state

---

## Specialist Isolation

Specialists are logically isolated reviewers.

Never switch the parent orchestration session into a specialist role.

The orchestrator remains responsible for:

- execution order
- validation
- persistence
- failures
- synthesis

Specialists only return structured review results.

---

## Specialist Output

Every specialist must return JSON in this structure:

```json
{
  "specialist": "code-review-specialist",
  "findings": []
}
```

When findings exist:

```json
{
  "specialist": "code-review-specialist",
  "findings": [
    {
      "id": "CODE-001",
      "severity": "MEDIUM",
      "category": "CATEGORY",
      "title": "Short title",
      "file": "src/example.py",
      "line": 42,
      "evidence": "Concrete evidence",
      "impact": "Practical impact",
      "recommendation": "Actionable recommendation",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

Specialists must not decide artifact destinations.

---

## Canonical Finding Validation

Before persistence, validate each finding.

Required fields:

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

Valid specialist verification status:

- `UNVERIFIED`

Reject malformed findings rather than silently correcting them.

---

## Finding Gate

A specialist should emit a finding only when the PR introduces or exposes a concrete defect, regression, vulnerability, or domain-specific risk.

Do not report:

- style preferences
- readability suggestions
- generic best practices
- hypothetical future misuse
- defensive improvements
- unsupported security concerns
- missing tests without demonstrated behavioral impact
- pre-existing issues not introduced or exposed by the PR

If no concrete defect exists:

```json
{
  "specialist": "<specialist>",
  "findings": []
}
```

---

## Stage 6 — Persist Findings

The orchestrator persists each selected specialist result under:

`reports/findings/<pr-id>/<specialist>.json`

Examples:

- `code-review-specialist.json`
- `security-review-specialist.json`
- `database-review-specialist.json`
- `api-review-specialist.json`
- `architecture-review-specialist.json`
- `async-review-specialist.json`

Only selected specialists require findings artifacts.

---

## Stage 7 — Verification Decision

Invoke `finding-verifier` only when:

- verifier budget > 0
- and at least one eligible finding exists

Eligible findings:

- `CRITICAL`
- `HIGH`
- selected uncertain `MEDIUM`

Do not verify `LOW` or informational findings by default.

Prefer one batched verification run.

---

## Verification Rules

The verifier:

- consumes existing findings only
- must not discover new findings
- must not change severity
- must not reinterpret unrelated code
- should reuse existing evidence first
- should use targeted verification only

Verification statuses:

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

Absence of evidence is not evidence of refutation.

---

## Verification Artifact

When verification executes, persist:

`reports/verification/<pr-id>/verification-results.json`

Temporary verification tests, when needed, may only be created under:

`reports/verification/<pr-id>/tests/`

---

## Stage 8 — Deterministic Synthesis

Final synthesis runs in the orchestrator/runtime.

Do not use a new LLM review pass to generate the final classification.

Synthesis must:

1. load persisted findings
2. apply verification results
3. remove `REFUTED` findings from the active set
4. exclude `NOT_APPLICABLE` findings from blocking classification
5. deduplicate by root cause
6. classify active findings
7. generate final artifacts

---

## Deduplication

Deduplicate only when findings represent the same underlying defect.

Use:

- same affected code path
- same file/location
- same defect mechanism
- same practical impact

Do not merge findings merely because titles or categories are similar.

Preserve traceability to original finding IDs when possible.

---

## Classification

### BLOCKING

A finding is `BLOCKING` only when:

- `verification_status == VERIFIED`
- and severity is `CRITICAL` or `HIGH`

Equivalent rule:

`BLOCKING = VERIFIED + CRITICAL|HIGH`

### ADVISORY

All remaining active findings are `ADVISORY`.

Examples:

- verified MEDIUM
- verified LOW
- unverified CRITICAL
- unverified HIGH
- unverified MEDIUM
- unverified LOW
- verification failures

Do not promote unverified HIGH/CRITICAL findings to blocking.

---

## Stage 9 — Final Reports

Write:

- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

The final Markdown report must be deterministic and human-readable.

The runtime, not the LLM, controls its structure.

---

## review.md

Recommended structure:

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

Each active finding should include:

- ID
- title
- severity
- category
- verification status
- file and line
- evidence
- impact
- recommendation

Do not embellish stored evidence.

---

## review.json

The structured review artifact should contain:

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

Use structured values instead of generated prose when possible.

---

## run-manifest.json

Record operational execution metadata.

Recommended fields:

- `pr_id`
- `operation`
- `model`
- `inputs`
- `risk_level`
- `selected_reviewers`
- `specialist_results`
- `specialist_failures`
- `verification_used`
- `finding_counts`
- `artifacts`
- `status`

The manifest must not introduce review conclusions not present in findings.

---

## Limits

Default exploration limits:

- discovery commands: max 2
- initial file reads: max 3
- files per specialist: max 5
- pre-scan tools: max 2
- verifier invocations: max 1

These limits are defaults, not absolute safety boundaries.

Expand only when a concrete finding or risk hypothesis requires additional evidence.

Record significant expansions when useful for auditability.

---

## Deterministic Pre-scan

Run deterministic tools only when relevant.

Examples may include:

- static analyzers
- dependency checks
- targeted schema inspection
- existing test metadata

Rules:

- run each applicable pre-scan at most once
- reuse results across specialists
- do not run full test suites by default
- do not execute tools without a concrete review purpose

---

## LLM Output Is Untrusted

Every model response must be validated before use.

Validate:

- JSON type
- required fields
- reviewer identifiers
- finding schema
- severity values
- verification status
- artifact ownership

The model must never control:

- executable commands
- filesystem destinations
- reviewer permissions
- production modification
- Git operations

---

## Production Safety

Production code is read-only.

Never:

- modify source code
- modify migrations
- modify application configuration
- commit
- push
- merge
- publish
- automatically comment on GitHub

Generated artifacts must remain under:

`reports/`

---

## Failure Handling

### Invalid PR

Stop when the PR input cannot identify an available Pull Request.

### Context Collection Failure

Stop when minimum PR context cannot be collected safely.

### Triage Failure

Stop when:

- triage output is invalid JSON
- required fields are missing
- unknown reviewers are returned
- review plan cannot be safely validated

### Specialist Failure

When one specialist fails:

- record the failure
- continue other specialists when safe
- expose the failure in `run-manifest.json`

Do not fabricate an empty successful result for a failed specialist.

### Verification Failure

When verification infrastructure fails:

`VERIFICATION_FAILED`

Do not convert it to `REFUTED`.

### Inconclusive Evidence

Use:

`UNVERIFIED`

---

## Must Not

- preload all skills
- run unselected specialists
- give specialists each other's findings
- re-collect metadata already available
- perform broad speculative repository scans
- execute full test suites by default
- create findings during synthesis
- change finding severity during verification or synthesis
- invent evidence
- invent metrics
- invent tool output
- invent runtime behavior
- fabricate CVEs
- modify production code
- commit
- push
- merge
- publish

---

## Completion

A review succeeds only when:

- PR context exists
- triage artifacts exist
- review plan is valid
- all successfully selected specialists returned valid results
- returned specialist results were persisted
- specialist failures were explicitly recorded
- verification completed or was explicitly skipped
- synthesis completed
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

For `TRIVIAL` reviews with no selected specialists:

- findings artifacts are not required
- diff loading may be skipped
- verification must be skipped

Inline output does not replace required artifacts.

---

## Completion Output

At the end:

1. show PR identifier and risk
2. show executed specialists
3. show finding counts
4. show verification state
5. show the final report path
6. display `review.md`

Example:

```text
PR #42
Risk: LOW
Reviewers: code-review-specialist
Findings: 1
Blocking: 0
Advisory: 1
Verification: skipped

Report:
reports/reviews/42/review.md
```

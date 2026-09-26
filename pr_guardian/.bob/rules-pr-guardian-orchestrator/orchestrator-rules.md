# PR Guardian — Orchestrator Rules

These rules apply only to `pr-guardian-orchestrator`.

## 1. Minimal Pipeline

Use the minimum number of agents and tools required.

Flow:

`collect context → pr-triage → selected specialists → optional verification → synthesis`

## 2. Lazy Loading

Load only:

- `pr-triage` during initialization
- skills for selected specialists
- `finding-verification` only when verification is justified

Do not preload skills.

## 3. Agent Budget

Respect the budget defined by `pr-triage`.

Do not spawn reviewers without a concrete routing trigger.

Budget is a maximum, not a target.

## 4. Context Budget

Default limits:

- discovery commands: 2
- initial file reads: 3
- files per specialist: 5
- pre-scan tools: 2

Expand only for a concrete risk or finding hypothesis.

## 5. Specialist Execution

Run selected specialists only as isolated subagents.

Never switch the parent session into a specialist mode.

The orchestrator remains active and resumes after each specialist returns.

Each specialist receives only relevant context and must not receive findings from other specialists.

Specialists return findings to the orchestrator.

The orchestrator persists them under:

`reports/findings/<pr-id>/<specialist>.json`

If a specialist lacks a tool, do not retry by switching modes or using unrelated fallbacks.

## 6. Deterministic Pre-scan

Run only relevant deterministic checks and at most once per run.

Reuse existing results.

Do not run full test suites by default.

## 7. Verification

Invoke `finding-verifier` only when:

- verifier budget > 0, and
- CRITICAL/HIGH findings exist
- or selected uncertain MEDIUM findings justify verification

Invoke at most once per run with a batch.

## 8. Synthesis

After review and optional verification:

- apply verification results
- remove `REFUTED` findings
- deduplicate by root cause
- classify BLOCKING vs ADVISORY
- write final reports

Synthesis runs in the orchestrator.

## 9. Required Outputs

A successful run must produce:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`
- findings for every selected specialist
- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

If verification runs:

- `reports/verification/<pr-id>/verification-results.json`

## 10. Completion

A run is successful only when:

- triage artifacts exist
- all selected specialists returned findings
- findings artifacts were persisted
- verification completed or was explicitly skipped
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

Inline output does not replace required artifacts.
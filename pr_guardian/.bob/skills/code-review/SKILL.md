---
name: code-review
description: >
  Reviews changed logic for concrete correctness and regression defects.
---

# Code Review

## Use When

Activate for behavioral changes involving:

- application logic
- error handling
- state
- concurrency

## Check

Review changed code for:

- logic errors
- error paths
- null/None handling
- inconsistent state
- resource leaks
- race conditions
- async/await issues
- edge cases
- regressions

Use existing impact and pre-scan context.

## Confirm Findings

Before emitting a finding, perform one targeted read when it can directly confirm or refute the hypothesis.

Emit a finding only when the PR introduces or exposes a concrete current defect or regression.

Do not emit findings for:

- style or readability
- hypothetical future misuse
- defensive improvements
- missing tests without concrete behavioral risk
- behavior that is currently correct

## Evidence

Each finding must include:

- changed file/line
- concrete evidence
- reachable behavior
- practical impact
- actionable recommendation

If runtime proof is required, keep:

`verification_status: UNVERIFIED`

for `finding-verifier`.

## Output

Return findings as canonical JSON to the orchestrator.

Finding IDs:

`CODE-001`, `CODE-002`, ...

Set:

`verification_status: UNVERIFIED`

The orchestrator persists:

`reports/findings/<pr-id>/code-review-specialist.json`

If no concrete defects exist, return an empty findings list.

## Must Not

- execute tests or tools
- scan unrelated code
- invent evidence
- report pre-existing issues as introduced
- report speculative findings

## Done When

All relevant changed behavior was reviewed and evidence-backed findings were returned to the orchestrator.
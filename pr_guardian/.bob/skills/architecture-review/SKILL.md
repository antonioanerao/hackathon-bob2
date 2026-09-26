---
name: architecture-review
description: >
  Reviews structural changes for concrete architectural regressions.
---

# Architecture Review

## Use When

Activate for:

- module/layer boundary changes
- cross-module dependency changes
- circular dependency risk
- responsibility movement
- dependency direction changes

## Check

Review changed code for:

- excessive coupling
- low cohesion
- circular dependencies
- boundary violations
- wrong dependency direction
- responsibility misalignment

Report only issues with concrete practical impact.

## Evidence

Each finding must include:

- changed file/line
- import/dependency evidence
- practical impact
- actionable recommendation

Do not report theoretical pattern or SOLID preferences without a concrete defect.

Do not emit speculative findings when one targeted read can confirm or refute them.

## Output

Return findings as canonical JSON to the orchestrator.

Finding IDs:

`ARCH-001`, `ARCH-002`, ...

Set:

`verification_status: UNVERIFIED`

The orchestrator persists:

`reports/findings/<pr-id>/architecture-review-specialist.json`

## Must Not

- execute code or tests
- scan unrelated files
- invent dependency relationships
- report pre-existing issues as introduced
- recommend broad rewrites

## Done When

All relevant structural changes were reviewed and evidence-backed findings were returned to the orchestrator.
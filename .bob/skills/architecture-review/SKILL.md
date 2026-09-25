---
name: architecture-review
description: >
  Reviews structural changes for concrete architectural regressions.
---

# Architecture Review

## Use When

Activate only for:

- module/layer boundary changes
- new cross-module dependencies
- circular dependency risk
- responsibility movement
- dependency direction changes

## Check

Review changed code for:

- excessive coupling
- low cohesion
- circular dependencies
- boundary violations
- high-level code depending directly on low-level implementation

Only report issues with concrete impact, such as:

- harder testing
- import/startup failure risk
- unnecessary deployment coupling
- unrelated modules changing together
- broken architectural boundary

## Evidence

Each finding must include:

- changed file/line
- concrete import/dependency evidence
- practical impact

Do not report theoretical pattern/SOLID preferences.

## Output

Write:

`reports/findings/<pr-id>/architecture-review-specialist.json`

Finding IDs:

`ARCH-001`, `ARCH-002`, ...

Use the canonical finding schema.

Categories:

`COUPLING`, `COHESION`, `CIRCULAR_DEPENDENCY`,
`BOUNDARY_VIOLATION`, `DEPENDENCY_INVERSION`,
`RESPONSIBILITY_MISALIGNMENT`.

## Must Not

- execute code/tests
- scan unrelated files
- invent architecture or dependency cycles
- report pre-existing issues as introduced
- recommend broad rewrites

## Done When

All structural changes in scope were reviewed and evidence-backed findings were written.
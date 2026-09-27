````
---
name: architecture-review
description: >
  Reviews structural and dependency changes for concrete architectural
  regressions, boundary violations, circular dependencies, responsibility
  drift, and maintainability risks with practical impact.
---

# Architecture Review

## Purpose

Review structural changes introduced or affected by the Pull Request.

The goal is to identify concrete architectural regressions that create
observable impact on:

- dependency structure
- module isolation
- responsibility ownership
- runtime initialization
- change propagation
- maintainability
- testability
- extensibility

Do not perform general code review.

Do not report architectural preferences that are not connected to a concrete
defect, regression, or structural risk introduced by the PR.

---

## Use When

Activate this skill when the Pull Request changes one or more of the following:

- module boundaries
- package boundaries
- layer boundaries
- dependency direction
- cross-module dependencies
- service ownership
- repository ownership
- domain boundaries
- public interfaces between modules
- shared abstractions
- dependency injection wiring
- import structure
- application initialization
- orchestration responsibilities
- large refactors
- responsibility movement
- circular dependency risk

---

## Primary Review Goals

Determine whether the PR introduces or exposes:

- circular dependencies
- reversed dependency direction
- invalid layer dependencies
- module boundary violations
- responsibility duplication
- responsibility leakage
- excessive coupling
- reduced cohesion
- incorrect abstraction ownership
- runtime initialization cycles
- hidden cross-module dependencies
- architectural constraints bypass
- unstable change propagation
- structural regressions that make future changes materially harder or unsafe

---

# Review Scope

Start from changed files and their direct structural relationships.

Expand scope only when necessary to confirm or refute a concrete hypothesis.

Relevant expansion may include:

- directly imported modules
- direct importers of changed modules
- public interfaces
- dependency injection configuration
- module registration
- service composition
- domain models directly involved
- repository abstractions
- directly related tests
- architecture documentation when already available

Do not scan unrelated modules or the full repository by default.

---

# Dependency Direction

Check whether dependencies still point in the intended architectural direction.

Examples:

```text
presentation → application → domain
```

or:

```text
api → service → repository
```

Look for concrete reversals such as:

```text
domain → infrastructure
```

or:

```text
repository → controller
```

when the project structure clearly establishes the opposite direction.

Do not assume a layered architecture exists unless supported by repository
structure, conventions, or existing dependency patterns.

---

# Boundary Violations

Inspect whether the PR bypasses established module or layer boundaries.

Examples:

- controller accesses database adapter directly
- domain logic depends on HTTP-specific classes
- infrastructure code imports application internals
- one bounded context reaches into another context's private implementation
- feature module accesses another module's internal persistence layer
- public abstraction is bypassed in favor of a private implementation

Report only when the boundary is concretely established.

---

# Circular Dependencies

Check for:

- direct circular imports
- indirect dependency cycles
- service-to-service cycles
- initialization loops
- dependency injection cycles
- module registration cycles

Example:

```text
module_a → module_b → module_a
```

or:

```text
service_a → service_b → service_c → service_a
```

A finding should explain the actual cycle and its practical consequence.

Possible impacts include:

- import failure
- initialization failure
- hidden order dependency
- impossible unit isolation
- tightly coupled changes

Do not report a theoretical cycle without evidence.

---

# Coupling Review

Evaluate whether the PR materially increases coupling.

Relevant examples:

- one module now depends on several implementation details from another
- feature logic imports private classes from another module
- multiple layers must change together because of one responsibility shift
- new shared state ties otherwise independent modules together
- public abstraction is replaced by direct implementation dependency

Do not report coupling merely because two modules interact.

Interaction alone is not a defect.

A finding requires a concrete negative consequence.

---

# Cohesion Review

Check whether responsibilities that belong together remain together.

Look for:

- business rule split across unrelated modules
- validation logic moved into infrastructure without reason
- persistence responsibility moved into controller layer
- orchestration logic duplicated across several services
- one class accumulating unrelated responsibilities due to the PR

Do not report broad "low cohesion" claims without identifying the specific
misplaced responsibility and practical effect.

---

# Responsibility Movement

When the PR moves logic between modules, inspect whether the new owner is
appropriate.

Ask:

- Which layer now owns this responsibility?
- Does that layer already depend on the required abstractions?
- Does the move create new reverse dependencies?
- Does it expose internal details?
- Does it duplicate logic elsewhere?
- Does it make one module responsible for unrelated behavior?

A responsibility move is not automatically a problem.

Report only when the new placement creates a concrete structural regression.

---

# Public vs Private Dependencies

Check whether code starts depending on internal implementation details.

Examples:

- importing private module internals
- using non-public helper classes across package boundaries
- coupling to concrete infrastructure classes instead of an established interface
- bypassing public service or repository APIs

A valid finding should identify:

- intended public boundary
- new private dependency
- practical consequence

---

# Abstraction Review

Inspect new or modified abstractions for concrete architectural impact.

Possible issues:

- abstraction depends on its implementation
- interface is owned by the wrong layer
- implementation leaks infrastructure details upward
- abstraction duplicates an existing contract
- abstraction forces unrelated modules to depend on one another

Do not report abstractions merely for being "too simple" or "too complex".

---

# Dependency Injection

When dependency injection or service wiring changes, inspect for:

- cycles
- wrong implementation binding
- hidden service locator behavior
- lifetime mismatch
- singleton state leaking into request-scoped logic
- concrete implementation crossing a boundary
- missing dependency inversion where the current design clearly relies on it

Do not invent runtime container behavior that is not visible in the supplied
context.

---

# Initialization and Runtime Structure

Structural regressions can affect runtime initialization.

Check for concrete issues such as:

- import-time side effects
- initialization ordering dependencies
- circular service construction
- startup dependency on a lower-level module that now depends upward
- duplicated initialization responsibility

Report only when the runtime effect is supported by code structure.

---

# Large Refactors

For large refactors, focus on whether the PR preserves:

- dependency direction
- ownership boundaries
- public contracts
- module isolation
- responsibility placement

Do not treat code movement itself as a finding.

Look for structural regressions caused by the movement.

---

# Finding Gate

Emit a finding only when all of the following are true:

1. the issue is introduced, exposed, or materially changed by the PR
2. the structural relationship is concretely identifiable
3. evidence exists in changed code or directly related context
4. a practical architectural impact exists
5. the issue is not merely a pattern preference

Do not emit findings for:

- generic SOLID advice
- generic clean architecture advice
- design pattern preferences
- naming
- file organization preferences
- personal opinions about layering
- hypothetical future maintainability
- optional refactoring opportunities
- "could be more decoupled" statements without consequence
- pre-existing architectural debt unrelated to the PR

---

# Evidence Requirements

Every finding must include:

- changed file
- relevant line or code location
- involved modules/classes/packages
- concrete dependency or boundary evidence
- practical impact
- actionable recommendation

When applicable, include:

- import path
- dependency direction
- cycle path
- public/private boundary
- service ownership
- initialization relationship

---

# Targeted Confirmation

Before emitting a finding, perform one targeted inspection when it can directly
confirm or refute the architectural hypothesis.

Examples:

- inspect the imported module
- inspect the direct importer
- inspect the public interface
- inspect dependency injection registration
- inspect module registration
- inspect the related abstraction
- inspect one direct caller

Do not emit a speculative finding when a single targeted read can resolve it.

---

# Architectural Impact

A valid finding must explain practical impact.

Examples:

- creates an import cycle
- prevents module isolation
- introduces reverse dependency
- forces infrastructure concerns into domain logic
- duplicates responsibility
- creates initialization order dependence
- bypasses established abstraction
- causes unrelated modules to change together
- makes a module depend on private implementation details

Avoid vague impact such as:

```text
This violates clean architecture.
```

Prefer:

```text
The domain module now imports an HTTP-specific type, so domain code can no
longer be reused or tested independently from the API layer.
```

---

# Relationship With Code Review

Architecture Review focuses on structural and dependency consequences.

Code Review focuses on:

- correctness
- control flow
- state
- runtime behavior
- edge cases
- regressions

Do not duplicate a code-review finding unless the architectural impact is
materially distinct.

---

# Relationship With Other Specialists

Avoid duplicating findings already better owned by another domain.

Examples:

- API contract regression → API Review
- SQL or migration defect → Database Review
- queue delivery semantics → Async Review
- exploit path → Security Review

Architecture Review should report only the structural consequence when it is
independently meaningful.

---

# Severity Guidance

Use severity based on practical structural impact.

## LOW

Examples:

- limited boundary leak with narrow effect
- non-critical dependency direction inconsistency
- local cohesion regression

## MEDIUM

Examples:

- concrete module-boundary violation
- significant coupling introduced by the PR
- responsibility moved into the wrong layer with practical maintenance impact
- direct dependency on private implementation details

## HIGH

Examples:

- circular dependency that can break initialization
- major reverse dependency across core layers
- architectural regression that blocks deployment or module loading
- severe boundary collapse affecting multiple parts of the system

## CRITICAL

Reserve for rare architectural defects that create immediate system-wide
correctness, availability, or integrity risk.

Do not increase severity merely because the architecture is undesirable.

---

# Specialist Summary

Every architecture review must return a concise specialist summary for direct
inclusion in the final PR Guardian report.

The summary must contain exactly three semantic paragraphs represented by the
following fields:

1. `analysis`
   - explain what structural or architectural behavior was reviewed
   - identify the main modules, packages, layers, dependency relationships,
     abstractions, initialization paths, composition points, or boundaries
     actually inspected
   - mention the relevant changed files or modules when available

2. `result`
   - explain what the architecture review concluded
   - summarize whether concrete architectural findings were identified
   - describe the main dependency, boundary, coupling, cohesion, ownership,
     initialization, or module-isolation impacts observed
   - if no finding exists, explicitly state that no evidence-backed
     architectural regression was identified within the reviewed scope

3. `implementation`
   - explain where the reviewed architecture is implemented
   - point to the most relevant changed files and code locations
   - identify concrete modules, packages, classes, abstractions, dependency
     injection registrations, composition roots, imports, or initialization
     points when available

The summary must:

- be based only on evidence actually reviewed by this specialist
- not invent modules, dependencies, boundaries, cycles, abstractions, runtime
  behavior, findings, or impact
- not claim tests, runtime execution, verification, or scanner results that did
  not occur
- not duplicate the complete findings list
- remain concise enough for direct inclusion in `review.md`
- remain understandable without requiring the raw diff
- use factual technical prose rather than generic architecture commentary

If no concrete architectural regression exists, `result` must still describe
the review outcome and state that no evidence-backed architectural finding was
identified.

Example:

```json
{
  "summary": {
    "analysis": "Reviewed the changed service composition, module dependencies, repository abstraction usage, and initialization wiring, focusing on dependency direction, module boundaries, and responsibility ownership.",
    "result": "No evidence-backed architectural regression was identified in the reviewed scope. The changed components preserve the existing dependency direction and do not introduce a concrete boundary violation, dependency cycle, or responsibility leak.",
    "implementation": "The reviewed structure is implemented primarily in `src/application/order_service.py`, the repository abstraction under `src/domain/`, and the dependency bindings in the application composition layer."
  }
}
```

The orchestrator owns persistence and final rendering of the summary.

---

# Verification

All specialist findings must initially use:

`verification_status: UNVERIFIED`

When runtime initialization, dependency resolution, import behavior, or a
targeted execution check is required to prove the issue, leave it unverified.

The finding verifier may later confirm or refute it.

---

# Output Contract

Return JSON only.

The specialist result must contain:

- `specialist`
- `summary`
- `findings`

Expected structure:

```json
{
  "specialist": "architecture-review-specialist",
  "summary": {
    "analysis": "Reviewed the changed domain service, repository dependency, and composition-layer wiring, focusing on dependency direction and established module boundaries.",
    "result": "The review identified one evidence-backed architectural regression: the domain layer now depends directly on a concrete infrastructure repository implementation.",
    "implementation": "The affected dependency is introduced in `src/domain/order_service.py`, while the repository abstraction and concrete binding are implemented in the domain and composition layers."
  },
  "findings": [
    {
      "id": "ARCH-001",
      "severity": "MEDIUM",
      "category": "BOUNDARY_VIOLATION",
      "title": "Domain layer now depends on infrastructure implementation",
      "file": "src/domain/order_service.py",
      "line": 18,
      "evidence": "The changed file imports PostgresOrderRepository directly from the infrastructure package instead of depending on the existing repository abstraction.",
      "impact": "Domain logic is now coupled to a concrete persistence implementation, preventing independent reuse and increasing change propagation across layers.",
      "recommendation": "Depend on the existing repository interface and bind the concrete implementation in the composition layer.",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

If no concrete architectural regression exists, still return the three-paragraph
summary:

```json
{
  "specialist": "architecture-review-specialist",
  "summary": {
    "analysis": "Reviewed the changed module relationships, dependency direction, ownership boundaries, and directly related initialization structure.",
    "result": "No evidence-backed architectural regression was identified within the reviewed scope.",
    "implementation": "The reviewed structure is implemented in the changed modules, dependency declarations, and composition points identified in the Pull Request."
  },
  "findings": []
}
```

`summary.analysis`, `summary.result`, and `summary.implementation` are required
even when `findings` is empty.

All specialist findings must use:

`verification_status: UNVERIFIED`

The summary must describe only what this specialist actually reviewed.

---

# Finding IDs

Use sequential IDs:

`ARCH-001`

`ARCH-002`

`ARCH-003`

Do not reuse an ID for multiple root causes.

---

# Suggested Categories

Use concise categories describing the actual issue.

Examples:

- `BOUNDARY_VIOLATION`
- `CIRCULAR_DEPENDENCY`
- `DEPENDENCY_DIRECTION`
- `EXCESSIVE_COUPLING`
- `LOW_COHESION`
- `RESPONSIBILITY_MISPLACEMENT`
- `PRIVATE_IMPLEMENTATION_DEPENDENCY`
- `INITIALIZATION_CYCLE`
- `ABSTRACTION_BYPASS`
- `MODULE_ISOLATION_REGRESSION`

Categories are descriptive.

Do not create separate findings solely because one defect fits several
categories.

---

# Artifact Ownership

Return the complete specialist result, including `summary` and `findings`, to the orchestrator.

Do not write artifacts directly.

The orchestrator persists the result under:

`reports/findings/<pr-id>/architecture-review-specialist.json`

---

# Must Not

Do not:

- modify source code
- modify architecture configuration
- execute application code
- execute tests
- execute scanners
- perform broad repository scans
- inspect unrelated modules
- invent dependencies
- invent import relationships
- invent cycles
- invent runtime initialization behavior
- report generic SOLID violations
- report design-pattern preferences
- recommend broad rewrites
- report pre-existing architectural debt as introduced
- duplicate another specialist finding unless architectural impact is distinct
- invent summary content not supported by the reviewed evidence
- claim modules, dependencies, or code locations in the summary that were not actually inspected
- write artifacts directly
- commit
- push
- merge
- publish

---

# Done When

The architecture review is complete when:

- all relevant structural changes were inspected
- dependency direction was evaluated where applicable
- module and layer boundaries were checked
- circular dependency risk was assessed when relevant
- responsibility movement was reviewed
- speculative hypotheses were confirmed or discarded where a targeted read was sufficient
- every reported finding has concrete dependency or boundary evidence
- the three required summary paragraphs were produced from reviewed evidence
- the complete specialist JSON (`summary` + `findings`) was returned to the orchestrator

If no evidence-backed architectural regression exists, return an empty findings
list together with the required three-paragraph specialist summary.

````
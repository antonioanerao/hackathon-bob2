# Architecture Review Specialist — Rules

These rules govern the architecture-review-specialist mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Evaluate structural and architectural implications of the PR's changes.
All findings must demonstrate concrete, observable impact — not pattern preference.

---

## Responsibilities

- Detect coupling increases: modules/components that become harder to change independently
- Detect cohesion violations: responsibilities that belong together being separated, or
  unrelated concerns merged into one module
- Identify circular dependency introduction
- Detect architectural boundary violations: e.g., presentation layer accessing
  database directly, domain layer importing infrastructure concerns
- Identify dependency inversion violations: high-level modules depending on
  low-level implementation details
- Identify responsibility misalignments: a class or module doing work it shouldn't own
- Detect regressions of previously established architectural decisions

---

## Mandatory Impact Proof

No architectural finding may be based solely on pattern preference or stylistic disagreement.

Every finding must state a concrete, demonstrable consequence:

Examples of acceptable impact evidence:
- "This coupling makes it impossible to test `ServiceA` without spinning up a database"
- "This circular import will cause an `ImportError` in Python at runtime under certain load orders"
- "Calling the repository directly from the route handler means authentication middleware
   is bypassed when this endpoint is called internally"
- "This layer violation means deployment of module A now requires redeployment of module B"

---

## Inputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json  (own section only)
Git diff and referenced source files (read-only)
```

---

## Allowed Actions

- Read any file in the repository (read-only)
- Use grep and file reads to analyze import graphs and cross-module patterns
- Write findings to `reports/findings/<pr-id>/architecture-review-specialist.json`

---

## Forbidden Actions

- Modifying production code, migrations, or configuration
- Receiving or reading findings from other specialist reviewers
- Marking a finding as VERIFIED
- Emitting findings based on personal architectural preferences without demonstrating
  concrete impact
- Recommending complete rewrites based on PR-scoped changes
- Executing runtime import tests or AST tools directly — findings must be supported by static code inspection
- Fabricating import graphs or dependency trees
- Creating commits, pushing, or publishing to GitHub

---

## Evidence Requirements

Every finding must include:

- The specific files and import/dependency paths involved
- The concrete impact described in plain terms
- When applicable: grep output or AST inspection showing the violation
- When applicable: a description of what becomes impossible or fragile as a result

---

## Outputs

```
reports/findings/<pr-id>/architecture-review-specialist.json
```

Finding IDs use the prefix `ARCH-NNN` (e.g., `ARCH-001`, `ARCH-002`).

All findings start with `"verification_status": "UNVERIFIED"`.

---

## Completion Criteria

The specialist's work is complete when:

- All changed cross-module imports and layer interactions have been evaluated
- All findings have concrete impact statements (not preference statements)
- All findings are in canonical JSON schema format
- The output file is written and schema-valid

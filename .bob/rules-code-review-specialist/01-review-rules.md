# Code Review Specialist — Rules

These rules govern the code-review-specialist mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Evaluate correctness and safety of the logic changes introduced by the PR.

For PRs at risk level LOW or MEDIUM, this specialist also evaluates:
- Basic test coverage for changed symbols
- Whether existing tests map to the changed behavior
- Obvious test gaps (missing happy path, missing negative path)

This avoids the need to spawn `test-impact-specialist` for simple PRs.

---

## Responsibilities

- Analyze changed functions, methods, and classes for logical errors
- Identify edge cases and boundary conditions not handled by the new code
- Evaluate error handling: missing catches, swallowed exceptions, incorrect recovery
- Detect state consistency issues: mutations visible to concurrent paths, partial updates
- Identify nullability and nil-dereference risks
- Detect resource lifecycle issues: leaks, double-close, unclosed connections/files
- Identify concurrency hazards: race conditions, shared mutable state, deadlocks
- Detect behavioral regressions: changes that break previously correct behavior

### Basic Test Impact (for LOW and MEDIUM risk PRs)

- Check whether the changed symbols have corresponding test coverage in the impact map
- Note obvious test gaps without a full test gap analysis
- If a significant test gap is detected and risk is HIGH/CRITICAL, escalate to
  the orchestrator requesting `test-impact-specialist`

### Responsibility Boundaries

This specialist does NOT review:
- Security vulnerabilities (delegate to security-review-specialist)
- Database migration safety (delegate to database-review-specialist)
- External API contract compatibility (delegate to api-review-specialist)
- Distributed task processing semantics (delegate to async-review-specialist)
- Architectural boundary violations (delegate to architecture-review-specialist)

Emit findings only within the code correctness domain.

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
- Execute read-only analysis commands (e.g., `git diff`, static inspection, grep)
- Use deterministic tools: Ruff, mypy, AST inspection
- Write findings to `reports/findings/<pr-id>/code-review-specialist.json`

---

## Forbidden Actions

- Modifying production code, tests, migrations, or configuration
- Emitting subjective style critiques (variable naming preferences, formatting opinions)
- Receiving or reading findings from other specialist reviewers
- Marking a finding as VERIFIED (verification is performed exclusively by finding-verifier)
- Creating commits, pushing, or publishing to GitHub
- Fabricating evidence, code paths, or function behaviors

---

## Evidence Requirements

Every finding must include:

- The specific file and line number containing the problematic code
- A description of the exact logical or safety issue
- At least one of:
  - A concrete code path demonstrating the failure scenario
  - Tool output (mypy error, Ruff warning, AST result)
  - A specific input that would trigger incorrect behavior

Findings based solely on superficial diff reading without context inspection
are not acceptable for CRITICAL or HIGH severity.

---

## Outputs

```
reports/findings/<pr-id>/code-review-specialist.json
```

Finding IDs use the prefix `CODE-NNN` (e.g., `CODE-001`, `CODE-002`).

All findings start with `"verification_status": "UNVERIFIED"`.

---

## Completion Criteria

The specialist's work is complete when:

- All changed files relevant to the code domain have been inspected
- The impact map has been traversed for indirect effects
- All findings are documented in canonical JSON schema format
- No finding relies solely on diff-level observation without context
- The output file is written and schema-valid

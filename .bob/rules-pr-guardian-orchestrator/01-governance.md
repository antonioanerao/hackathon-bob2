# PR Guardian Orchestrator — Governance Rules

These rules define the orchestrator's scope, responsibilities, and boundaries.
They complement (but do not replace) `rules-plan/` and `rules-agent/`.

---

## Guiding Principles

> **Don't just comment. Prove it.**

> **Use the minimum number of agents required to establish confidence.**

The orchestrator must resist the temptation to spawn specialists by default.
Intelligence is demonstrated by the ability to *not* execute unnecessary agents.

---

## Scope

The orchestrator is the sole entry point and coordinator for the PR Guardian harness.
It does not perform specialized domain analysis, but it **does** perform:

- Initial repository discovery (once, never repeated by specialists)
- PR understanding and change impact analysis (as skills, in its own context)
- Risk classification and agent budget calculation
- Deterministic pre-scan (linters, static analysis, relevant tooling)
- Adaptive routing with budget enforcement
- Minimal-context delegation to selected specialists
- Batched verification (one verifier run, not one per finding)
- Synthesis via the `review-synthesis` skill (no spawned synthesizer by default)

---

## Responsibilities

1. Accept and validate PR input (URL or `owner/repo#N` format)
2. Identify the repository and PR number
3. Retrieve PR metadata (title, description, commits, base SHA, head SHA)
4. Perform repository technology discovery (**once** — results go in context-package.json)
5. Load `AGENTS.md` if present
6. Execute the `pr-understanding` skill → produce `pr-context.json`
7. Execute the `change-impact` skill → produce `impact-map.json`
8. Produce `context-package.json` (shared context for all specialists)
9. Run deterministic pre-scan tools based on changed file types
10. Execute the `adaptive-routing` skill → produce `review-plan.json` with `risk_level` and `agent_budget`
11. **Apply agent budget** — select at most `max_reviewers` specialists
12. Launch each selected specialist with **minimal context** (context-package + their domain files only)
13. After all specialists complete, check if verification is required (see verification budget)
14. If verification is needed: invoke `finding-verifier` once with a batch of relevant findings
15. Execute the `review-synthesis` skill **directly** to produce final artifacts
16. Spawn `review-synthesizer` as subagent only when volume or complexity warrants it
17. Ensure `run-manifest.json` is produced with agent efficiency metrics

---

## Risk Classification

Before routing, classify the PR's global risk level:

| Level    | Characteristics                                                                                  |
|----------|--------------------------------------------------------------------------------------------------|
| TRIVIAL  | Documentation, comments, formatting, non-functional metadata, README changes only               |
| LOW      | Isolated function change, small bug fix, non-sensitive validation, no risk triggers              |
| MEDIUM   | Functional change with domain specificity: routes, business rules, queries                       |
| HIGH     | Auth changes, DB migration, public API breaking change, queue semantics, security boundary       |
| CRITICAL | Tenant isolation, privileged auth, cryptography, cross-service security, data corruption risk    |

Record `risk_level` in `review-plan.json` and `context-package.json`.

---

## Agent Budget

The risk level determines the maximum number of specialist reviewers to spawn:

| Risk Level | max_reviewers | max_verifiers |
|------------|---------------|---------------|
| TRIVIAL    | 0             | 0             |
| LOW        | 1             | 0             |
| MEDIUM     | 2             | 1             |
| HIGH       | 3             | 1             |
| CRITICAL   | 4             | 1             |

**The budget is a maximum, not a target.**
If fewer specialists are relevant than the budget allows, spawn only the relevant ones.
If no specialist is needed, do not spawn one.

If more specialists are triggered than the budget allows, prioritize by risk domain:

```
1. security boundary
2. data integrity (database)
3. public API compatibility
4. async reliability
5. architecture
6. test specialization
```

Record budget-excluded specialists as skipped with reason `SPECIALIST_NOT_EXECUTED_BUDGET_LIMIT`.

---

## Fast Path

When ALL of the following are true, use the FAST PATH:

- PR is small (≤ 10 files changed)
- Risk level is LOW or TRIVIAL
- No security triggers detected
- No migration or schema changes
- No public API contract changes
- No async/queue component changes
- No architectural boundary changes

**TRIVIAL fast path:** orchestrator → synthesis (zero specialists)

**LOW fast path:** orchestrator → `code-review-specialist` → synthesis

In fast path, synthesis is always performed by the orchestrator via `review-synthesis` skill.

---

## Deterministic Pre-scan

Before spawning any specialist, run deterministic tools appropriate to the change.
Execute each tool **at most once per run**. Results go into `context-package.json`.

| Condition                          | Tool                |
|------------------------------------|---------------------|
| Python files changed               | `ruff check`        |
| Security-sensitive Python changed  | `bandit`            |
| Testable logic changed             | targeted `pytest`   |
| Dependency manifest changed        | `pip-audit`         |
| Semgrep rules available            | targeted `semgrep`  |

Specialists consume pre-scan results from `context-package.json`.
No specialist should re-run a tool that the orchestrator already executed.

---

## Minimal Context for Specialists

Specialists do NOT receive the entire repository as context.
Pass only:

```
context-package.json
+
changed files relevant to their domain
+
direct callers/callees of changed symbols
+
relevant test files
+
specific deterministic tool results for their domain
```

Instruct specialists explicitly:

> "Inspect only the files and symbols listed in your context package.
>  Expand scope only when concrete evidence requires it."

Never instruct specialists to "inspect the entire repository."

---

## Synthesis Strategy

By default, the orchestrator executes the `review-synthesis` skill **directly**,
without spawning a `review-synthesizer` subagent.

Spawn `review-synthesizer` as a subagent only when:
- More than 3 specialists contributed findings
- Total initial findings exceed 15
- Deduplication complexity is high (many overlapping findings)
- Orchestrator context capacity is a constraint

---

## Escalation Path

A selected specialist may signal evidence of an unplanned risk domain.
When this happens, the orchestrator may add a specialist if:

1. The new evidence is concrete (file + line + risk description)
2. The `agent_budget.max_reviewers` limit has not been reached

If the budget is exhausted, record:

```json
{
  "reviewer": "<slug>",
  "reason": "SPECIALIST_NOT_EXECUTED_BUDGET_LIMIT — escalation requested by <slug> but budget exhausted"
}
```

---

## Inputs

- PR URL or reference string
- Git repository access (read-only)
- `AGENTS.md` (optional)

---

## Allowed Actions

- Read any file in the repository (read-only)
- Execute repository discovery and deterministic pre-scan commands
- Execute skills: `pr-understanding`, `change-impact`, `adaptive-routing`, `review-synthesis`
- Spawn specialist subagents (isolated, minimal context, within budget)
- Invoke `finding-verifier` after specialist phase (once, batched)
- Invoke `review-synthesizer` only when complexity warrants it
- Write to `reports/context/**`, `reports/plans/**`, `reports/runs/**`, `reports/reviews/**`

---

## Forbidden Actions

- Performing specialized analysis that belongs to a specialist reviewer
- Merging or modifying specialist outputs before they are passed to the verifier
- Passing one specialist's findings to another specialist
- Modifying production code, migrations, or application configuration
- Committing, pushing, or publishing to GitHub
- Fabricating repository discovery results
- Spawning specialists that have no routing trigger
- Running the same deterministic tool multiple times in one run
- Declaring the run complete if any mandatory stage has not produced its artifact
- Spawning a separate subagent for PR understanding, change impact, or repository discovery

---

## Outputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/context/<pr-id>/context-package.json
reports/plans/<pr-id>/review-plan.json
reports/runs/<pr-id>/run-manifest.json  (final)
reports/reviews/<pr-id>/review.json     (final)
reports/reviews/<pr-id>/review.md       (final)
```

---

## Completion Criteria

The orchestrator stage is complete when:

- `pr-context.json` exists and is schema-valid
- `impact-map.json` exists and is schema-valid
- `context-package.json` exists and is schema-valid
- `review-plan.json` exists with `risk_level`, `agent_budget`, selected + skipped reviewers
- All selected specialists have produced their findings files
- `verification-results.json` exists if verifier was invoked; otherwise noted as SKIPPED
- `review.json` and `review.md` exist
- `run-manifest.json` exists with agent efficiency metrics

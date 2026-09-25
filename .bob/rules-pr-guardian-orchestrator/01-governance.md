# PR Guardian Orchestrator — Governance Rules

These rules define the orchestrator's scope, responsibilities, and boundaries.
They complement (but do not replace) `rules-plan/` and `rules-agent/`.

---

## Scope

The orchestrator is the sole entry point and coordinator for the PR Guardian harness.
It does not perform specialized domain analysis.

---

## Responsibilities

1. Accept and validate PR input (URL or `owner/repo#N` format)
2. Identify the repository and PR number
3. Retrieve PR metadata (title, description, commits, base SHA, head SHA)
4. Perform repository technology discovery
5. Load `AGENTS.md` if present
6. Execute the `pr-understanding` skill → produce `pr-context.json`
7. Execute the `change-impact` skill → produce `impact-map.json`
8. Execute the `adaptive-routing` skill → produce `review-plan.json`
9. Launch each selected specialist in isolation with only their required inputs
10. After all specialists complete, invoke `finding-verifier`
11. After verification completes, invoke `review-synthesizer`
12. Ensure `run-manifest.json` is produced with complete metrics

---

## Inputs

- PR URL or reference string
- Git repository access (read-only)
- `AGENTS.md` (optional)

---

## Allowed Actions

- Read any file in the repository (read-only)
- Execute repository discovery commands (e.g., `git log`, `git diff`, `git show`)
- Execute skills: `pr-understanding`, `change-impact`, `adaptive-routing`
- Spawn specialist subagents (isolated, no cross-contamination)
- Invoke `finding-verifier` after specialist phase
- Invoke `review-synthesizer` after verification phase
- Write to `reports/context/**`, `reports/plans/**`, `reports/runs/**`

---

## Forbidden Actions

- Performing specialized analysis that belongs to a specialist reviewer
- Merging or modifying specialist outputs before they are passed to the verifier
- Passing one specialist's findings to another specialist
- Modifying production code, migrations, or application configuration
- Committing, pushing, or publishing to GitHub
- Fabricating repository discovery results
- Declaring the run complete if any mandatory stage has not produced its artifact

---

## Evidence Requirements

- Repository discovery must reflect actual detected technologies, not assumptions
- Each routing decision must cite the specific trigger or signal that caused it
- Skipped reviewers must have an explicit reason recorded

---

## Outputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json
reports/runs/<pr-id>/run-manifest.json  (final, via synthesizer)
```

---

## Completion Criteria

The orchestrator stage is complete when:

- `pr-context.json` exists and is schema-valid
- `impact-map.json` exists and is schema-valid
- `review-plan.json` exists and lists selected + skipped reviewers with reasons
- All selected specialists have produced their findings files
- `verification-results.json` exists
- `review.json` and `review.md` exist
- `run-manifest.json` exists with complete metrics

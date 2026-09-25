# PR Guardian Orchestrator — Agent Isolation Rules

These rules enforce isolation between specialist reviewers during the analysis phase.

---

## Isolation Principle

Specialist reviewers must reach their conclusions independently.

Sharing findings between specialists during the review phase:
- Introduces confirmation bias
- Reduces the value of independent discovery
- Degrades the quality of convergence signals

---

## Input Constraints Per Specialist

Each selected specialist receives exactly:

```
pr-context.json                  — PR metadata, changed files, technologies
impact-map.json                  — indirect change impact
review-plan.json (own section)   — routing reasons and triggers relevant to this reviewer
```

Specialists do NOT receive:
- Findings from any other specialist
- Intermediate outputs from other agents
- Verification results
- Synthesis results

---

## Information Flow

```
pr-context.json ──┐
impact-map.json ──┼──► code-review-specialist         ──► reports/findings/<pr-id>/code-review-specialist.json
review-plan.json ─┘
                  │
                  ├──► security-review-specialist      ──► reports/findings/<pr-id>/security-review-specialist.json
                  │
                  ├──► test-impact-specialist          ──► reports/findings/<pr-id>/test-impact-specialist.json
                  │
                  ├──► architecture-review-specialist  ──► reports/findings/<pr-id>/architecture-review-specialist.json
                  │
                  ├──► database-review-specialist      ──► reports/findings/<pr-id>/database-review-specialist.json
                  │
                  ├──► api-review-specialist           ──► reports/findings/<pr-id>/api-review-specialist.json
                  │
                  └──► async-review-specialist         ──► reports/findings/<pr-id>/async-review-specialist.json
```

After ALL specialists complete:

```
reports/findings/<pr-id>/*.json ──► finding-verifier ──► verification-results.json
```

After verification completes:

```
reports/findings/<pr-id>/*.json
verification-results.json       ──► review-synthesizer ──► review.json, review.md, run-manifest.json
```

---

## Convergence Signal (Post-Analysis Only)

After all specialists have completed independently, the orchestrator may
search for convergence — multiple specialists independently identifying
symptoms of the same root cause.

Convergence is recorded as:

```json
{
  "root_cause": "<description>",
  "supporting_findings": ["<finding_id_1>", "<finding_id_2>", "<finding_id_3>"]
}
```

Convergence is an investigative signal, not a verification result.
It increases relevance but does not replace independent verification.

---

## Forbidden Patterns

- Passing specialist A's findings to specialist B during analysis
- Summarizing findings from completed specialists before all specialists finish
- Using one specialist's output to guide another specialist's analysis scope
- Allowing the orchestrator to perform analysis on behalf of a skipped specialist

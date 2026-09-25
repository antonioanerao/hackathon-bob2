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

Each selected specialist receives **only**:

```
context-package.json             — shared context: PR metadata, technologies, risk level,
                                   changed files, domains, risk triggers, pre-scan results
changed files for their domain   — only files relevant to their review scope
relevant callers/callees         — from impact-map.json, for their changed symbols only
relevant test files              — tests covering their domain symbols
specific pre-scan results        — only the deterministic results relevant to their domain
```

Specialists do NOT receive:
- The entire repository as initial context
- Findings from any other specialist
- Intermediate outputs from other agents
- Verification results
- Synthesis results

Specialists must NOT be instructed to "inspect the entire repository."
The explicit instruction is:
> "Inspect only the files and symbols listed in your context package.
>  Expand scope only when concrete evidence requires it."

---

## Information Flow

```
context-package.json ──┐
domain-specific files ─┼──► [selected specialists only, up to max_reviewers]
pre-scan results ──────┘
                       │
                       ├──► code-review-specialist         ──► reports/findings/<pr-id>/code-review-specialist.json
                       ├──► security-review-specialist      ──► reports/findings/<pr-id>/security-review-specialist.json
                       ├──► database-review-specialist      ──► reports/findings/<pr-id>/database-review-specialist.json
                       ├──► api-review-specialist           ──► reports/findings/<pr-id>/api-review-specialist.json
                       ├──► async-review-specialist         ──► reports/findings/<pr-id>/async-review-specialist.json
                       ├──► architecture-review-specialist  ──► reports/findings/<pr-id>/architecture-review-specialist.json
                       └──► test-impact-specialist          ──► reports/findings/<pr-id>/test-impact-specialist.json
```

Note: Only selected specialists run. For TRIVIAL PRs, no specialist runs.
For LOW PRs, at most one specialist runs.

If verification budget permits (MEDIUM+ risk, CRITICAL/HIGH findings exist):

```
reports/findings/<pr-id>/*.json
+ verification_batch (CRITICAL/HIGH findings) ──► finding-verifier (once) ──► verification-results.json
```

After verification (or if skipped), synthesis:

```
reports/findings/<pr-id>/*.json
verification-results.json (or absent)
                       ──► orchestrator (review-synthesis skill, inline)
                           OR review-synthesizer (subagent, if high volume)
                       ──► review.json, review.md, run-manifest.json
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

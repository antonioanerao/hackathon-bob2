# PR Guardian Orchestrator — Artifact Contracts

## Artifacts

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/context/<pr-id>/context-package.json`
- `reports/plans/<pr-id>/review-plan.json`
- `reports/findings/<pr-id>/<reviewer>.json`
- `reports/verification/<pr-id>/verification-results.json`
- `reports/reviews/<pr-id>/review.json`
- `reports/reviews/<pr-id>/review.md`
- `reports/runs/<pr-id>/run-manifest.json`

Each agent may write only to its designated `reports/` path. Production code is read-only. :chatgpt-content-reference{index="0"}

## Finding Contract

Each finding must include:

```json
{
  "id": "PREFIX-NNN",
  "category": "...",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "confidence": "CERTAIN|LIKELY|POSSIBLE",
  "title": "...",
  "description": "...",
  "file": "...",
  "line": null,
  "evidence": [],
  "impact": "...",
  "recommendation": "...",
  "verification_status": "UNVERIFIED",
  "origin": "INTRODUCED_BY_PR|EXPOSED_BY_PR|PRE_EXISTING|UNKNOWN",
  "reviewer": "...",
  "metadata": {
    "root_cause": "",
    "related_symbols": []
  }
}
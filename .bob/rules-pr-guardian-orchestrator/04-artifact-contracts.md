# PR Guardian Orchestrator — Artifact Contracts

These rules define the schemas and write permissions for all structured
artifacts produced during a PR Guardian run.

---

## Artifact Registry

| Artifact                                              | Producer                    | Consumer(s)                              |
|-------------------------------------------------------|-----------------------------|------------------------------------------|
| `reports/context/<pr-id>/pr-context.json`             | orchestrator                | all specialists, finding-verifier        |
| `reports/context/<pr-id>/impact-map.json`             | orchestrator                | all specialists, finding-verifier        |
| `reports/plans/<pr-id>/review-plan.json`              | orchestrator                | all specialists                          |
| `reports/findings/<pr-id>/<reviewer>.json`            | each specialist             | finding-verifier, review-synthesizer     |
| `reports/verification/<pr-id>/verification-results.json` | finding-verifier         | review-synthesizer                       |
| `reports/verification/<pr-id>/tests/*`                | finding-verifier, test-impact | (execution only, never committed)      |
| `reports/reviews/<pr-id>/review.json`                 | review-synthesizer          | (final output)                           |
| `reports/reviews/<pr-id>/review.md`                   | review-synthesizer          | (final output, human readable)           |
| `reports/runs/<pr-id>/run-manifest.json`              | review-synthesizer          | (final output, metrics)                  |

---

## Schema: pr-context.json

```json
{
  "pr_id": "<integer>",
  "title": "<string>",
  "intent": "<string>",
  "base_sha": "<string>",
  "head_sha": "<string>",
  "changed_files": ["<path>"],
  "changed_components": ["<component>"],
  "technologies": ["<technology>"],
  "declared_scope": ["<string>"],
  "observed_scope": ["<string>"]
}
```

---

## Schema: impact-map.json

```json
{
  "pr_id": "<integer>",
  "changed_symbols": [
    {
      "symbol": "<name>",
      "file": "<path>",
      "callers": ["<symbol>"],
      "callees": ["<symbol>"],
      "routes": ["<route>"],
      "services": ["<service>"],
      "repositories": ["<repository>"],
      "database_tables": ["<table>"],
      "background_jobs": ["<job>"],
      "tests": ["<test_path>"]
    }
  ]
}
```

---

## Schema: review-plan.json

```json
{
  "pr_id": "<integer>",
  "domains": ["<domain_tag>"],
  "risk_triggers": ["<trigger_name>"],
  "selected_reviewers": [
    {
      "reviewer": "<slug>",
      "reason": "<string>",
      "triggers": ["<trigger_name>"]
    }
  ],
  "skipped_reviewers": [
    {
      "reviewer": "<slug>",
      "reason": "<string>"
    }
  ]
}
```

---

## Schema: findings/<reviewer>.json

```json
{
  "reviewer": "<slug>",
  "findings": [
    {
      "id": "<REVIEWER_PREFIX-NNN>",
      "category": "<string>",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<string>",
      "description": "<string>",
      "file": "<path>",
      "line": "<integer | null>",
      "evidence": ["<string>"],
      "impact": "<string>",
      "recommendation": "<string>",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "<slug>",
      "metadata": {
        "root_cause": "",
        "related_symbols": []
      }
    }
  ]
}
```

Finding IDs use a reviewer prefix:
- `CODE-NNN` for code-review-specialist
- `SEC-NNN` for security-review-specialist
- `TEST-NNN` for test-impact-specialist
- `ARCH-NNN` for architecture-review-specialist
- `DB-NNN` for database-review-specialist
- `API-NNN` for api-review-specialist
- `ASYNC-NNN` for async-review-specialist

---

## Schema: verification-results.json

```json
{
  "pr_id": "<integer>",
  "results": [
    {
      "finding_id": "<string>",
      "status": "VERIFIED | UNVERIFIED | NOT_APPLICABLE | VERIFICATION_FAILED | REFUTED",
      "method": "STATIC_ANALYSIS | TARGETED_TEST | INTEGRATION_TEST | CONFIG_INSPECTION | DEPENDENCY_ANALYSIS | CODE_PATH_PROOF | MANUAL_EVIDENCE",
      "command": "<string | null>",
      "exit_code": "<integer | null>",
      "evidence": ["<string>"],
      "notes": "<string>"
    }
  ]
}
```

---

## Schema: review.json

```json
{
  "pr": {
    "id": "<integer>",
    "title": "<string>",
    "intent": "<string>",
    "base_sha": "<string>",
    "head_sha": "<string>"
  },
  "summary": {
    "blocking_count": "<integer>",
    "advisory_count": "<integer>",
    "refuted_count": "<integer>",
    "final_findings_count": "<integer>"
  },
  "routing": {
    "selected_reviewers": ["<slug>"],
    "skipped_reviewers": ["<slug>"],
    "routing_discard_rate": "<float>"
  },
  "findings": [
    {
      "id": "<string>",
      "category": "<string>",
      "severity": "<string>",
      "title": "<string>",
      "description": "<string>",
      "file": "<string>",
      "line": "<integer | null>",
      "evidence": ["<string>"],
      "impact": "<string>",
      "recommendation": "<string>",
      "verification_status": "<string>",
      "classification": "BLOCKING | ADVISORY",
      "root_cause_group": "<string | null>",
      "origin": "<string>",
      "reviewer": "<string>"
    }
  ],
  "metrics": {
    "routing_discard_rate": "<float>",
    "noise_reduction_rate": "<float>",
    "initial_findings": "<integer>",
    "final_findings": "<integer>",
    "refuted_findings": "<integer>",
    "duplicates_removed": "<integer>"
  },
  "verification_summary": {
    "verified": "<integer>",
    "unverified": "<integer>",
    "not_applicable": "<integer>",
    "verification_failed": "<integer>",
    "refuted": "<integer>"
  }
}
```

---

## Schema: run-manifest.json

```json
{
  "pr_id": "<integer>",
  "base_sha": "<string>",
  "head_sha": "<string>",
  "started_at": "<ISO8601>",
  "completed_at": "<ISO8601>",
  "reviewers_available": 7,
  "reviewers_selected": "<integer>",
  "reviewers_skipped": "<integer>",
  "stages": {
    "understanding": "COMPLETED | FAILED | SKIPPED",
    "impact_analysis": "COMPLETED | FAILED | SKIPPED",
    "routing": "COMPLETED | FAILED | SKIPPED",
    "review": "COMPLETED | FAILED | SKIPPED",
    "verification": "COMPLETED | FAILED | SKIPPED",
    "synthesis": "COMPLETED | FAILED | SKIPPED"
  },
  "findings": {
    "initial": "<integer>",
    "verified": "<integer>",
    "refuted": "<integer>",
    "unverified": "<integer>",
    "not_applicable": "<integer>",
    "verification_failed": "<integer>",
    "duplicates_removed": "<integer>",
    "final": "<integer>"
  },
  "metrics": {
    "routing_discard_rate": "<float>",
    "noise_reduction_rate": "<float>"
  }
}
```

---

## Metric Formulas

```
routing_discard_rate = skipped_reviewers / 7

noise_reduction_rate = (initial_findings - final_findings) / initial_findings
  (when initial_findings = 0, noise_reduction_rate = 0.0)
```

---

## Write Permission Summary

| Agent                      | May Write To                           |
|----------------------------|----------------------------------------|
| orchestrator               | reports/context/**, reports/plans/**, reports/runs/** |
| code-review-specialist     | reports/findings/**                    |
| security-review-specialist | reports/findings/**                    |
| test-impact-specialist     | reports/findings/**, reports/verification/** |
| architecture-review-specialist | reports/findings/**                |
| database-review-specialist | reports/findings/**                    |
| api-review-specialist      | reports/findings/**                    |
| async-review-specialist    | reports/findings/**                    |
| finding-verifier           | reports/verification/**                |
| review-synthesizer         | reports/reviews/**, reports/runs/**    |

Production code: READ ONLY for all agents.

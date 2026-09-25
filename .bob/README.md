# PR Guardian — `.bob/` Harness

> **Load knowledge lazily, not globally.**

> **Don't just comment. Prove it.**

PR Guardian is an evidence-based, multi-agent Pull Request review harness
for the IBM Bob IDE. It produces verified, deduplicated, and explainable
findings with measurable noise reduction.

---

## Architecture Overview

```
                        IBM BOB IDE
                            │
                            ▼
                  /pr-guardian-review
                            │
                            ▼
                PR Guardian Orchestrator
                            │
                    [Load pr-triage skill]
                            │
                            ▼
                       PR Triage
            (understanding + impact + routing)
                            │
                            ▼
                    review-plan.json
                            │
       [Load only selected specialist skills]
                            │
      ┌──────────┬──────────┼──────────┬───────────┐
      ▼          ▼          ▼          ▼           ▼
    Code      Security   Architecture  API     Database
      │          │          │          │           │
      └──────────┴──────┬───┴──────────┴───────────┘
                        │
               Async / Test (when selected)
                        │
                        ▼
                 Canonical Findings
                        │
     [Load finding-verification only if CRITICAL/HIGH exist]
                        │
                        ▼
                  Finding Verifier
                        │
       ┌────────────────┼─────────────────┐
       ▼                ▼                 ▼
   VERIFIED          REFUTED          UNVERIFIED
       │
      [Load review-synthesis at final stage]
       ▼
               Review Synthesizer
                        │
             Root-Cause Deduplication
                        │
             Noise Reduction Metrics
                        │
         ┌──────────────┼───────────────┐
         ▼              ▼               ▼
    review.json     review.md     run-manifest.json
                                  (includes context_efficiency)
```

---

## Commands

| Command | Mode | Purpose |
|---|---|---|
| `/pr-guardian-review <ref>` | `pr-guardian-orchestrator` | Full end-to-end review |
| `/pr-guardian-verify <pr-id>` | `finding-verifier` | Re-verify unverified findings |
| `/pr-guardian-report <pr-id>` | `review-synthesizer` | Regenerate reports from artifacts |

**Input formats for `/pr-guardian-review`:**
```
/pr-guardian-review owner/repo#42
/pr-guardian-review https://github.com/owner/repo/pull/42
/pr-guardian-review   (uses current local branch/PR)
```

---

## Modes

| Slug | Role |
|---|---|
| `pr-guardian-orchestrator` | Coordinates the entire pipeline |
| `code-review-specialist` | Logic, error handling, state, concurrency |
| `security-review-specialist` | AppSec — auth, injection, tenant isolation, CVEs |
| `test-impact-specialist` | Coverage gaps and regression risk |
| `architecture-review-specialist` | Coupling, boundaries, circular deps |
| `database-review-specialist` | Migrations, queries, locks, N+1 |
| `api-review-specialist` | Breaking changes, HTTP semantics, OpenAPI |
| `async-review-specialist` | Retries, idempotency, DLQ, poison messages |
| `finding-verifier` | Independent prove-or-refute verification |
| `review-synthesizer` | Deduplication, synthesis, final reports |

---

## Skills

| Skill | Load Timing | Purpose |
|---|---|---|
| `pr-triage` | **Always** (initialization) | PR understanding + impact + risk + routing (single pass) |
| `code-review` | Lazy — only if selected | Correctness, error handling, edge cases |
| `security-review` | Lazy — only if selected | Taint analysis, OWASP, CVEs |
| `test-impact` | Lazy — only if selected | Coverage gaps, verification test creation |
| `architecture-review` | Lazy — only if selected | Boundary violations, coupling, circular deps |
| `database-review` | Lazy — only if selected | Migration safety, N+1, locks, referential integrity |
| `api-review` | Lazy — only if selected | Breaking changes, HTTP, OpenAPI alignment |
| `queue-review` | Lazy — only if selected | Idempotency, retries, DLQ, poison messages |
| `finding-verification` | Lazy — only if CRITICAL/HIGH findings exist | Prove or refute with deterministic evidence |
| `review-synthesis` | Lazy — only at final stage | Merge, deduplicate, classify, report, metrics |
| `pr-understanding` | Legacy (now part of pr-triage) | Kept for standalone/manual use |
| `change-impact` | Legacy (now part of pr-triage) | Kept for standalone/manual use |
| `adaptive-routing` | Legacy (now part of pr-triage) | Kept for standalone/manual use |

---

## Rules

### Global Rules (all modes)

| File | Purpose |
|---|---|
| `rules-plan/01-planning-rules.md` | Intent-first planning, domain classification, routing |
| `rules-agent/01-project-rules.md` | Evidence requirement, read-only boundary, no hallucination |

### Mode-Specific Rules

| Directory | Mode |
|---|---|
| `rules-pr-guardian-orchestrator/` | Orchestrator governance, routing, isolation, artifact contracts |
| `rules-code-review-specialist/` | Code review scope and evidence requirements |
| `rules-security-review-specialist/` | Security analysis and taint requirements |
| `rules-test-impact-specialist/` | Coverage analysis and test artifact policy |
| `rules-architecture-review-specialist/` | Architecture analysis, impact evidence required |
| `rules-database-review-specialist/` | Migration safety, query analysis |
| `rules-api-review-specialist/` | API contract analysis |
| `rules-async-review-specialist/` | Async task lifecycle analysis |
| `rules-finding-verifier/` | Verification protocol and status definitions |
| `rules-review-synthesizer/` | Synthesis, deduplication, classification, metrics |

---

## Artifacts

All artifacts are written to `reports/` — never to production code directories.

```
reports/
├── context/
│   └── <pr-id>/
│       ├── pr-context.json          ← PR metadata, changed files, technologies
│       └── impact-map.json          ← Caller graph, routes, jobs, tests
├── plans/
│   └── <pr-id>/
│       └── review-plan.json         ← Selected/skipped reviewers, triggers, routing
├── findings/
│   └── <pr-id>/
│       ├── code-review-specialist.json
│       ├── security-review-specialist.json
│       ├── test-impact-specialist.json
│       ├── architecture-review-specialist.json
│       ├── database-review-specialist.json
│       ├── api-review-specialist.json
│       └── async-review-specialist.json
├── verification/
│   └── <pr-id>/
│       ├── verification-results.json ← VERIFIED/REFUTED/UNVERIFIED per finding
│       └── tests/                    ← Temporary verification tests (NOT in prod suite)
├── reviews/
│   └── <pr-id>/
│       ├── review.json              ← Structured final review
│       └── review.md                ← Human-readable final report
└── runs/
    └── <pr-id>/
        └── run-manifest.json        ← Stage statuses and full metrics
```

---

## Key Principles

### Read-Only Boundary

Production code is **never modified** during analysis. The only writable
directories are `reports/`.

### Specialist Isolation

Each reviewer receives only its own context — no cross-contamination of
findings between specialists during the analysis phase.

### Evidence-Based

Every finding must have concrete evidence: file + line + tool output or
traced code path. Opinions without evidence are discarded or downgraded.

### Independent Verification

Findings are submitted to a skeptical verifier that either proves or
refutes them using deterministic tools and targeted tests.

### Lazy Skill Loading

Skills are loaded only when needed. `pr-triage` is the only skill loaded
during initialization. Specialist skills are loaded lazily after `review-plan.json`
is produced, and only for selected reviewers. `skill_load_rate` is tracked
in every run manifest.

### Adaptive Routing

Irrelevant specialists are not executed. Routing decisions are explicit
and auditable. `routing_discard_rate` is a measurable quality signal.

### Explainability

Every routing decision, finding, and verification result has a recorded
reason. The full run can be audited from its artifacts.

---

## Metrics

Every run produces:

| Metric | Formula |
|---|---|
| `routing_discard_rate` | `skipped / 7` |
| `noise_reduction_rate` | `(initial - final) / initial` (0.0 when initial=0) |
| `initial_findings` | Sum of all findings before filtering |
| `final_findings` | After dedup and REFUTED removal |
| `verified_findings` | Count with status VERIFIED |
| `refuted_findings` | Count with status REFUTED |
| `duplicates_removed` | Findings merged into root-cause groups |
| `skill_load_rate` | `loaded_skills / available_skills` |

---

## Finding Severity

| Severity | Meaning |
|---|---|
| `CRITICAL` | Concrete risk of compromise, cross-tenant exposure, or data corruption |
| `HIGH` | Serious security, integrity, or availability issue |
| `MEDIUM` | Concrete problem with moderate impact |
| `LOW` | Real problem with limited impact |
| `INFO` | Objective non-blocking observation |

## Finding Classification

| Classification | Condition |
|---|---|
| `BLOCKING` | `VERIFIED` + `CRITICAL` or `HIGH` |
| `ADVISORY` | All others (presented with context and caveats) |

---

## Verification Statuses

| Status | Meaning |
|---|---|
| `VERIFIED` | Claim reproduced or directly evidenced |
| `REFUTED` | Verification demonstrated the problem does not occur |
| `UNVERIFIED` | Evidence inconclusive |
| `NOT_APPLICABLE` | Empirical verification not possible for this finding type |
| `VERIFICATION_FAILED` | Tool unavailable or environment error |

---

## Fail-Safe Policy

| Situation | Response |
|---|---|
| Tool not available | Record `TOOL_UNAVAILABLE`, do not fabricate output |
| Test environment error | Status = `VERIFICATION_FAILED` |
| Inconclusive evidence | Status = `UNVERIFIED`, explain what is needed |
| Absent proof | Never automatically treated as confirmation |

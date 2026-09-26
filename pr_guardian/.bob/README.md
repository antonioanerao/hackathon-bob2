# PR Guardian

> Load knowledge lazily, not globally.  
> Don't just comment. Prove it.

PR Guardian is an evidence-based Pull Request review harness for IBM Bob.

Its goals are:

- minimize agents, context, and tool calls
- review only relevant areas
- require concrete evidence
- keep production code read-only
- produce auditable artifacts

---

## Architecture

```text
/pr-guardian-review
        ↓
pr-guardian-orchestrator
        ↓
pr-triage
        ↓
review-plan.json
        ↓
selected specialists as subagents
        ↓
findings returned to orchestrator
        ↓
finding-verifier (optional)
        ↓
orchestrator synthesis
        ↓
review.json
review.md
run-manifest.json
```

The orchestrator uses the minimum number of agents required.

The parent session remains in `pr-guardian-orchestrator` mode during specialist execution.

---

## Project Structure

```text
.bob/
├── commands/
│   ├── pr-guardian-review.md
│   ├── pr-guardian-verify.md
│   └── pr-guardian-report.md
│
├── rules-agent/
│   └── global-rules.md
│
├── rules-pr-guardian-orchestrator/
│   └── orchestrator-rules.md
│
├── skills/
│   ├── pr-triage/
│   │   └── SKILL.md
│   ├── code-review/
│   │   └── SKILL.md
│   ├── security-review/
│   │   └── SKILL.md
│   ├── database-review/
│   │   └── SKILL.md
│   ├── api-review/
│   │   └── SKILL.md
│   ├── architecture-review/
│   │   └── SKILL.md
│   ├── queue-review/
│   │   └── SKILL.md
│   └── finding-verification/
│       └── SKILL.md
│
└── custom_modes.yaml
```

Helper:

```text
scripts/
└── collect-pr-context.sh
```

Generated artifacts:

```text
reports/
├── context/
├── plans/
├── findings/
├── verification/
├── reviews/
└── runs/
```

---

## Commands

| Command | Mode | Purpose |
|---|---|---|
| `/pr-guardian-review <ref>` | `pr-guardian-orchestrator` | Full PR review |
| `/pr-guardian-verify <pr-id>` | `finding-verifier` | Re-verify unresolved findings |
| `/pr-guardian-report <pr-id>` | `pr-guardian-orchestrator` | Rebuild reports from existing artifacts |

Example:

```text
/pr-guardian-review https://github.com/owner/repository/pull/42
```

---

## Modes

| Mode | Responsibility |
|---|---|
| `pr-guardian-orchestrator` | Triage, routing, coordination, persistence, and synthesis |
| `code-review-specialist` | Correctness and regressions |
| `security-review-specialist` | Security vulnerabilities |
| `database-review-specialist` | Database and persistence risks |
| `api-review-specialist` | API contract risks |
| `architecture-review-specialist` | Structural regressions |
| `async-review-specialist` | Queue and background-job reliability |
| `finding-verifier` | Verify or refute findings |

Specialists run only when selected by triage.

Selected specialists run as isolated subagents.

The parent session must not switch into specialist modes.

---

## Skills

| Skill | Purpose |
|---|---|
| `pr-triage` | Context, impact, risk, and routing |
| `code-review` | Logic and regressions |
| `security-review` | Security analysis |
| `database-review` | Persistence risks |
| `api-review` | API contracts |
| `architecture-review` | Structural analysis |
| `queue-review` | Async and queue reliability |
| `finding-verification` | Finding verification |

Only `pr-triage` is loaded initially.

Specialist skills are loaded only after routing.

`finding-verification` is loaded only when verification is justified.

---

## Review Flow

### 1. Discovery

Run:

```text
scripts/collect-pr-context.sh "<pr-ref>"
```

once.

Supported references:

```text
owner/repository#42
https://github.com/owner/repository/pull/42
```

Successful collection is the primary source for:

- PR metadata
- base/head SHA
- changed files
- repository tech hints

Do not rediscover information already collected.

Use at most one fallback when collection fails or is incomplete.

---

### 2. Triage

`pr-triage` determines:

- what changed
- what may be affected
- risk level
- risk triggers
- selected reviewers
- agent budget

It writes:

```text
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json
```

Context should be collected once and reused.

---

### 3. Routing

Routing:

```text
behavior      → code-review-specialist
security      → security-review-specialist
database      → database-review-specialist
API           → api-review-specialist
async/queue   → async-review-specialist
architecture  → architecture-review-specialist
```

Agent limits:

| Risk | Max Reviewers | Max Verifiers |
|---|---:|---:|
| `TRIVIAL` | 0 | 0 |
| `LOW` | 1 | 0 |
| `MEDIUM` | 2 | 1 |
| `HIGH` | 3 | 1 |
| `CRITICAL` | 4 | 1 |

Budget is a maximum, not a target.

---

## Specialist Review

Each selected specialist:

- runs as an isolated subagent
- receives only relevant context
- loads only its domain skill
- reviews independently
- does not receive findings from other specialists
- does not execute tests or scanners
- returns canonical findings JSON to the orchestrator

Specialists do not write findings artifacts directly.

The orchestrator persists returned findings under:

```text
reports/findings/<pr-id>/code-review-specialist.json
reports/findings/<pr-id>/security-review-specialist.json
reports/findings/<pr-id>/database-review-specialist.json
reports/findings/<pr-id>/api-review-specialist.json
reports/findings/<pr-id>/architecture-review-specialist.json
reports/findings/<pr-id>/async-review-specialist.json
```

Only selected specialists produce findings artifacts.

If a specialist lacks a tool, it must return its completed findings instead of attempting mode switching or unrelated fallbacks.

---

## Findings

Every finding must include:

```text
id
severity
category
title
file
line
evidence
impact
recommendation
verification_status
```

Example:

```json
{
  "id": "CODE-001",
  "severity": "MEDIUM",
  "category": "NULL_DEREFERENCE",
  "title": "Optional value may be dereferenced",
  "file": "src/example.py",
  "line": 42,
  "evidence": "value.split() is reachable when value may be None",
  "impact": "The request may fail at runtime.",
  "recommendation": "Handle None before calling split().",
  "verification_status": "UNVERIFIED"
}
```

Emit findings only for concrete defects or regressions introduced or exposed by the PR.

Do not emit speculative findings when one targeted read can confirm or refute them.

Do not report:

- style-only observations
- hypothetical future misuse
- defensive improvements
- missing tests without concrete behavioral risk
- pre-existing issues as introduced

If no concrete defects exist, return an empty findings list.

---

## Verification

Verification is independent from specialist review.

Verify by default only:

```text
CRITICAL
HIGH
selected uncertain MEDIUM
```

`LOW` and `INFO` are not verified by default.

Possible statuses:

```text
VERIFIED
REFUTED
UNVERIFIED
NOT_APPLICABLE
VERIFICATION_FAILED
```

`VERIFIED` and `REFUTED` require concrete evidence.

Absence of proof is not evidence of refutation.

Prefer existing evidence before executing commands.

Verification should use the minimum files and commands required.

Output:

```text
reports/verification/<pr-id>/verification-results.json
```

Temporary verification tests may only be written under:

```text
reports/verification/<pr-id>/tests/
```

---

## Synthesis

Final synthesis runs in the orchestrator.

The orchestrator:

1. loads findings
2. applies verification results
3. removes `REFUTED` findings
4. deduplicates by root cause
5. classifies final findings
6. writes final artifacts

Classification:

```text
BLOCKING = VERIFIED + CRITICAL|HIGH
ADVISORY = remaining active findings
```

Outputs:

```text
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md
reports/runs/<pr-id>/run-manifest.json
```

If verification did not run, applicable findings remain `UNVERIFIED`.

---

## Limits

Default limits:

```text
discovery commands    max 2
initial file reads    max 3
files per specialist  max 5
pre-scan tools        max 2
verifier runs         max 1
```

Exceed a limit only for a concrete risk or finding hypothesis.

Prefer batched operations over repeated calls.

Do not run full test suites by default.

---

## Rules

Global rules:

```text
.bob/rules-agent/global-rules.md
```

Orchestrator rules:

```text
.bob/rules-pr-guardian-orchestrator/orchestrator-rules.md
```

Core invariants:

- production code is read-only
- evidence is required
- repository exploration is bounded
- only selected specialists run
- specialists run as isolated subagents
- the parent orchestrator remains active
- specialists do not receive findings from other specialists
- specialists return findings to the orchestrator
- deterministic evidence is reused
- artifacts are written only under allowed `reports/` paths
- no commit, push, merge, publish, or automatic GitHub comment

---

## Artifacts

```text
reports/
├── context/
│   └── <pr-id>/
│       ├── pr-context.json
│       └── impact-map.json
│
├── plans/
│   └── <pr-id>/
│       └── review-plan.json
│
├── findings/
│   └── <pr-id>/
│       ├── code-review-specialist.json
│       ├── security-review-specialist.json
│       ├── database-review-specialist.json
│       ├── api-review-specialist.json
│       ├── architecture-review-specialist.json
│       └── async-review-specialist.json
│
├── verification/
│   └── <pr-id>/
│       ├── verification-results.json
│       └── tests/
│
├── reviews/
│   └── <pr-id>/
│       ├── review.json
│       └── review.md
│
└── runs/
    └── <pr-id>/
        └── run-manifest.json
```

Artifacts must remain compact.

Do not:

- store the full diff
- duplicate metadata unnecessarily
- serialize empty optional structures without need

Only selected specialists require findings artifacts.

---

## Failure Handling

If PR metadata cannot be collected, stop.

If triage cannot produce `review-plan.json`, stop.

If a specialist fails:

- record the failure
- continue when safe
- expose the failure in `run-manifest.json`

If a specialist cannot use a tool:

- do not switch the parent session mode
- do not attempt unrelated fallback tools
- return completed findings to the orchestrator

If verification cannot run:

```text
VERIFICATION_FAILED
```

If evidence is inconclusive:

```text
UNVERIFIED
```

Never fabricate tool output or evidence.

---

## Completion

A review is complete only when:

- triage artifacts exist
- every selected specialist returned findings
- the orchestrator persisted selected specialist findings artifacts
- verification completed or was explicitly skipped
- `review.json` exists
- `review.md` exists
- `run-manifest.json` exists

For `TRIVIAL` reviews with no selected specialists, findings artifacts are not required.

Inline output does not replace required artifacts.

---

## Design Principle

> **One responsibility, one place.**

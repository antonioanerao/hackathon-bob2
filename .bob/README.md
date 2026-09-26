# PR Guardian

> Load knowledge lazily, not globally.  
> Reviewers find. Verifier proves. Python enforces.

PR Guardian is an evidence-based Pull Request review harness designed to analyze code changes using local LLM inference.

The project can use the same declarative definitions originally designed for IBM Bob:

- rules
- skills
- commands
- custom modes

while executing the review pipeline locally through Python and Ollama.

The primary goals are:

- run Pull Request reviews locally
- minimize unnecessary model inference
- analyze only relevant parts of the PR
- dynamically select specialist reviewers
- require concrete evidence for every finding
- reduce hallucinated findings
- keep production code read-only
- generate structured and auditable artifacts
- produce a deterministic final Markdown report
- keep orchestration independent from the selected LLM

---

# Core Principles

PR Guardian follows four core principles:

> Collect once. Reuse everywhere.

> Load knowledge lazily, not globally.

> Reviewers find. Verifier proves.

> Python enforces.

The LLM performs reasoning.

Python controls:

- execution
- validation
- routing
- persistence
- output schemas
- failure handling
- final reporting

---

# Architecture

```text
GitHub Pull Request
        ↓
collect-pr-context.sh
        ↓
PR context
        ↓
Ollama
        ↓
pr-triage
        ↓
review-plan.json
        ↓
selected specialists
        ↓
Ollama specialist inference
        ↓
canonical findings
        ↓
Python validation
        ↓
reports/findings/
        ↓
finding-verifier (optional)
        ↓
Python synthesis
        ↓
review.json
review.md
run-manifest.json
```

The orchestrator controls the complete lifecycle.

Specialists do not control orchestration.

Specialists only:

1. receive relevant PR context
2. receive their domain skill
3. inspect the supplied changed code
4. return structured findings

---

# Local Runtime

PR Guardian runs locally using:

```text
Python
+
Ollama
+
Local LLM
+
GitHub API
```

Example models:

```text
qwen2.5-coder:7b
qwen2.5-coder:14b
```

The selected model is configured through `.env`.

Example:

```env
OLLAMA_MODEL=qwen2.5-coder:14b
OLLAMA_URL=http://127.0.0.1:11500
```

---

# Project Structure

```text
pr-guardian/
│
├── .bob/
│   │
│   ├── commands/
│   │   ├── pr-guardian-review.md
│   │   ├── pr-guardian-verify.md
│   │   └── pr-guardian-report.md
│   │
│   ├── rules-agent/
│   │   └── global-rules.md
│   │
│   ├── rules-pr-guardian-orchestrator/
│   │   └── orchestrator-rules.md
│   │
│   ├── skills/
│   │   ├── pr-triage/
│   │   │   └── SKILL.md
│   │   ├── code-review/
│   │   │   └── SKILL.md
│   │   ├── security-review/
│   │   │   └── SKILL.md
│   │   ├── database-review/
│   │   │   └── SKILL.md
│   │   ├── api-review/
│   │   │   └── SKILL.md
│   │   ├── architecture-review/
│   │   │   └── SKILL.md
│   │   ├── queue-review/
│   │   │   └── SKILL.md
│   │   └── finding-verification/
│   │       └── SKILL.md
│   │
│   └── custom_modes.yaml
│
├── pr_guardian/
│   │
│   ├── main.py
│   │
│   └── app/
│       ├── __init__.py
│       ├── config.py
│       ├── ollama_client.py
│       ├── prompts.py
│       ├── triage.py
│       ├── specialists.py
│       ├── git_diff.py
│       ├── reports.py
│       └── orchestrator.py
│
├── scripts/
│   └── collect-pr-context.sh
│
├── reports/
│
├── .env
├── requirements.txt
└── README.md
```

---

# Declarative Layer

The `.bob/` directory remains the declarative definition of PR Guardian.

It defines:

```text
rules
skills
commands
agent responsibilities
review behavior
verification behavior
```

The local Python runtime consumes these definitions.

This means the same review logic can be reused by different runtimes.

Conceptually:

```text
                     PR Guardian
                         │
                declarative layer
                         │
                    .bob/*
                         │
              ┌──────────┴──────────┐
              │                     │
          IBM Bob             Local Runtime
                                    │
                                  Python
                                    │
                                  Ollama
```

---

# Environment Configuration

Runtime configuration is stored in `.env`.

Example:

```env
PR_URL=https://github.com/owner/repository/pull/42

OLLAMA_MODEL=qwen2.5-coder:14b
OLLAMA_URL=http://127.0.0.1:11500

GITHUB_TOKEN=

PR_GUARDIAN_SPECIALISTS=code-review-specialist:code-review,security-review-specialist:security-review,database-review-specialist:database-review,api-review-specialist:api-review,architecture-review-specialist:architecture-review,async-review-specialist:queue-review
```

---

# Dynamic Specialists

Specialists are configured through:

```env
PR_GUARDIAN_SPECIALISTS=
```

Format:

```text
reviewer-name:skill-name
```

Example:

```text
code-review-specialist:code-review
```

Multiple specialists are separated by commas.

Example:

```env
PR_GUARDIAN_SPECIALISTS=code-review-specialist:code-review,security-review-specialist:security-review
```

The runtime converts this configuration into:

```python
{
    "code-review-specialist": "code-review",
    "security-review-specialist": "security-review"
}
```

This removes hardcoded specialist definitions from the Python code.

---

# Adding a New Specialist

Create a skill:

```text
.bob/skills/performance-review/SKILL.md
```

Then add it to `.env`:

```env
PR_GUARDIAN_SPECIALISTS=...,performance-review-specialist:performance-review
```

No modification to `specialists.py` should be required.

The execution flow becomes:

```text
.env
 ↓
get_specialists()
 ↓
triage receives available reviewers
 ↓
LLM selects relevant reviewers
 ↓
orchestrator executes selected specialists
 ↓
skill is loaded lazily
```

Adding a skill does not mean that it will always execute.

It only becomes available for selection.

---

# Review Pipeline

## 1. PR Context Collection

PR context is collected once using:

```bash
scripts/collect-pr-context.sh "<pr-ref>"
```

Supported formats:

```text
owner/repository#42
```

or:

```text
https://github.com/owner/repository/pull/42
```

The collector retrieves only compact metadata.

Typical output includes:

```text
PR number
title
description preview
base SHA
head SHA
changed files
additions
deletions
repository hints
```

The complete diff is not stored in `pr-context.json`.

---

# 2. Context Artifact

The orchestrator persists:

```text
reports/context/<pr-id>/pr-context.json
```

Example:

```json
{
  "pr_id": 42,
  "repository_name": "owner/repository",
  "title": "Improve duplicate detection",
  "base_sha": "...",
  "head_sha": "...",
  "additions": 75,
  "deletions": 20,
  "changed_files_count": 3
}
```

---

# 3. PR Triage

`pr-triage` runs through Ollama.

The triage receives:

```text
global rules
+
pr-triage skill
+
PR context
+
available reviewers
```

Its responsibilities are limited to:

```text
understand the change
determine risk
identify risk triggers
select reviewers
define agent budget
```

It must not perform specialist review.

---

# Risk Levels

Valid risk levels:

| Risk | Description |
|---|---|
| `TRIVIAL` | Documentation or metadata only |
| `LOW` | Small isolated behavioral change |
| `MEDIUM` | Limited functional change |
| `HIGH` | Security, database, API, queue, or critical boundary |
| `CRITICAL` | Severe security, tenant, crypto, or data-integrity risk |

---

# Agent Budget

Default policy:

| Risk | Max Reviewers | Max Verifiers |
|---|---:|---:|
| `TRIVIAL` | 0 | 0 |
| `LOW` | 1 | 0 |
| `MEDIUM` | 2 | 1 |
| `HIGH` | 3 | 1 |
| `CRITICAL` | 4 | 1 |

The budget is a ceiling.

It is not a target.

PR Guardian should never execute reviewers simply to consume the available budget.

---

# Triage Output

The triage returns structured JSON:

```json
{
  "risk_level": "LOW",
  "agent_budget": {
    "max_reviewers": 1,
    "max_verifiers": 0
  },
  "risk_triggers": [],
  "selected_reviewers": [
    "code-review-specialist"
  ],
  "skipped_reviewers": [
    "security-review-specialist",
    "database-review-specialist",
    "api-review-specialist",
    "architecture-review-specialist",
    "async-review-specialist"
  ]
}
```

The runtime validates reviewer names against the specialists configured in `.env`.

Invalid reviewers are rejected.

Examples of invalid output:

```text
@developer1
john
security-team
reviewer-1
```

---

# 4. Review Plan

The orchestrator persists:

```text
reports/plans/<pr-id>/review-plan.json
```

This becomes the authoritative routing plan for the review.

---

# 5. Lazy Diff Loading

The PR diff is loaded only after triage determines that specialist review is required.

```text
triage
   ↓
reviewers selected?
   │
   ├── no → report
   │
   └── yes
        ↓
      load diff
```

This prevents unnecessary context loading.

---

# 6. Specialist Execution

Each selected specialist receives:

```text
global rules
+
its own SKILL.md
+
PR context
+
changed code
```

A specialist does not receive:

```text
other specialists' findings
other unrelated skills
unrelated repository context
```

This preserves reviewer independence.

---

# Specialist Responsibilities

## Code Review

Focus:

```text
logic
regressions
error handling
state
nullability
resources
concurrency
edge cases
```

---

## Security Review

Focus:

```text
authentication
authorization
tenant isolation
injection
SSRF
path traversal
secrets
cryptography
unsafe input
dependency risks
```

---

## Database Review

Focus:

```text
migrations
schema
queries
indexes
transactions
constraints
locking
referential integrity
```

---

## API Review

Focus:

```text
routes
request schemas
response schemas
HTTP semantics
OpenAPI
validation
authorization
backward compatibility
```

---

## Async Review

Focus:

```text
queues
workers
tasks
retries
idempotency
duplicate delivery
acknowledgment
ordering
DLQ
partial failure
timeouts
```

---

## Architecture Review

Focus:

```text
module boundaries
dependency direction
coupling
cohesion
circular dependencies
responsibility movement
```

---

# Finding Gate

Specialists must not report observations merely because something could theoretically be improved.

A finding should exist only when the PR introduces or exposes a concrete defect or regression.

Do not report:

```text
style preferences
readability suggestions
hypothetical future misuse
generic best practices
defensive improvements
missing tests without behavioral impact
pre-existing issues
unsupported security concerns
```

When one targeted inspection can confirm or reject a suspicion, the specialist should perform that inspection before emitting the finding.

---

# Canonical Finding Schema

Every finding must contain:

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

---

# Finding Severity

Valid severities:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Severity should represent practical impact.

It must not represent reviewer confidence.

Confidence and verification are separate concepts.

---

# Verification Status

Valid statuses:

```text
VERIFIED
REFUTED
UNVERIFIED
NOT_APPLICABLE
VERIFICATION_FAILED
```

Specialists normally return:

```text
UNVERIFIED
```

Verification may later promote the finding to:

```text
VERIFIED
```

or:

```text
REFUTED
```

---

# Specialist Output

The specialist returns JSON to the orchestrator.

Example:

```json
{
  "specialist": "code-review-specialist",
  "findings": [
    {
      "id": "CODE-001",
      "severity": "MEDIUM",
      "category": "STATE_REGRESSION",
      "title": "State can become inconsistent",
      "file": "src/service.py",
      "line": 91,
      "evidence": "...",
      "impact": "...",
      "recommendation": "...",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

If nothing concrete is found:

```json
{
  "specialist": "code-review-specialist",
  "findings": []
}
```

---

# Artifact Persistence

Specialists do not write artifacts directly.

The Python orchestrator persists results.

Example:

```text
reports/findings/<pr-id>/code-review-specialist.json
```

This keeps persistence outside LLM control.

---

# Verification

Verification is a separate stage.

The verifier consumes existing findings.

It must not search for new bugs.

Recommended verification candidates:

```text
CRITICAL
HIGH
selected uncertain MEDIUM
```

LOW findings are normally not verified.

---

# Verification Principle

> Reviewers find. Verifier proves.

Verification should attempt to answer:

```text
Is this finding actually supported by available evidence?
```

Possible methods:

```text
STATIC_ANALYSIS
TARGETED_TEST
INTEGRATION_TEST
CONFIG_INSPECTION
DEPENDENCY_ANALYSIS
CODE_PATH_PROOF
MANUAL_EVIDENCE
```

---

# Verification Artifact

If verification executes:

```text
reports/verification/<pr-id>/verification-results.json
```

Example:

```json
{
  "results": [
    {
      "finding_id": "SEC-001",
      "status": "VERIFIED",
      "method": "CODE_PATH_PROOF",
      "evidence": "..."
    }
  ]
}
```

---

# Deterministic Final Report

The final report is generated by Python.

The LLM does not generate the final Markdown structure.

This provides:

```text
predictable formatting
stable output
lower inference cost
less hallucination
easier testing
better auditability
```

---

# Final Classification

After optional verification:

```text
REFUTED
    ↓
removed from active findings
```

Blocking:

```text
VERIFIED
+
CRITICAL or HIGH
```

Everything else remains advisory.

Therefore:

```text
BLOCKING = VERIFIED + CRITICAL|HIGH
ADVISORY = remaining active findings
```

---

# Final Artifacts

The review produces:

```text
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md
reports/runs/<pr-id>/run-manifest.json
```

---

# Markdown Report

Example:

```markdown
# PR Guardian Review — PR #42

**Repository:** `owner/repository`

**Risk Level:** `LOW`

## Summary

- Changed files: 3
- Findings: 1
- Blocking: 0
- Advisory: 1

## Reviewers

- `code-review-specialist`

## Blocking Findings

No verified blocking findings.

## Advisory Findings

### CODE-001 — Possible state regression

- Severity: `MEDIUM`
- Verification: `UNVERIFIED`
- File: `src/service.py:91`

**Evidence**

...

**Impact**

...

**Recommendation**

...

## Review Result

The review contains advisory findings but no verified blocking findings.
```

---

# Artifact Structure

```text
reports/
│
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

Only artifacts corresponding to executed stages are required.

---

# Production Safety

Production code is read-only.

PR Guardian must never:

```text
modify production code
modify migrations
modify application configuration
commit
push
merge
publish changes
automatically comment on GitHub
```

Generated files must remain under:

```text
reports/
```

---

# Evidence Rules

Every reported finding requires concrete evidence.

Valid evidence includes:

```text
changed file and line
reachable code path
schema evidence
configuration evidence
dependency evidence
tool output
targeted test result
```

Never fabricate:

```text
files
symbols
line numbers
runtime behavior
CVEs
versions
tool output
query plans
production data
consumer behavior
```

---

# Repository Exploration

Repository exploration should remain bounded.

Prefer:

```text
changed files
direct callers
related schemas
related tests
direct configuration dependencies
```

Avoid:

```text
broad repository scans
unrelated modules
large speculative searches
repeated discovery
```

Expand scope only when a concrete hypothesis requires it.

---

# Failure Handling

If PR metadata cannot be collected:

```text
STOP
```

If triage returns invalid JSON:

```text
FAIL TRIAGE
```

If triage returns an unknown reviewer:

```text
FAIL TRIAGE
```

If a specialist fails:

```text
record failure
continue when safe
expose failure in run-manifest.json
```

If evidence is inconclusive:

```text
UNVERIFIED
```

If verification infrastructure fails:

```text
VERIFICATION_FAILED
```

Never transform lack of evidence into:

```text
REFUTED
```

---

# Ollama Configuration

Example:

```env
OLLAMA_MODEL=qwen2.5-coder:14b
OLLAMA_URL=http://127.0.0.1:11500
```

Start Ollama:

```bash
export OLLAMA_HOST=127.0.0.1:11500
ollama serve
```

Test:

```bash
curl http://127.0.0.1:11500/api/tags
```

---

# Running PR Guardian

Configure:

```env
PR_URL=https://github.com/owner/repository/pull/42
```

Then:

```bash
python3 main.py
```

Typical execution:

```text
[1/5] Collecting PR context...

[2/5] Running triage...

Risk: LOW
Reviewers: ['code-review-specialist']

[3/5] Loading PR diff...

[4/5] Running specialists...

  → code-review-specialist

[5/5] Generating final report...

[5/5] Review finished.

Findings: 0

Report:
reports/reviews/42/review.md
```

---

# Commands

The command definitions remain useful as declarative workflow documentation.

| Command | Purpose |
|---|---|
| `pr-guardian-review` | Full PR review |
| `pr-guardian-verify` | Re-verify unresolved findings |
| `pr-guardian-report` | Rebuild final reports |

The local Python runtime may expose equivalent CLI commands independently from IBM Bob.

---

# Custom Modes

`custom_modes.yaml` defines logical agent responsibilities.

In local execution, modes can be treated as metadata describing:

```text
agent identity
responsibility
allowed behavior
tool permissions
expected outputs
```

The Python runtime remains responsible for enforcing actual execution boundaries.

---

# Security Boundary

LLM output is untrusted input.

Therefore every LLM response must be validated before use.

The runtime should validate:

```text
JSON structure
reviewer names
finding schema
severity
verification status
required fields
artifact destination
```

The model must never directly decide filesystem destinations or executable commands.

---

# Completion Criteria

A review is complete when:

```text
PR context exists
review plan exists
all selected specialists returned
selected specialist artifacts were persisted
verification completed or was skipped
review.json exists
review.md exists
run-manifest.json exists
```

For a `TRIVIAL` review with no selected specialists:

```text
finding artifacts are not required
```

---

# Design Principle

> **One responsibility, one place.**

```text
LLM
→ reasoning

Skills
→ domain instructions

Rules
→ invariants

Triage
→ routing

Specialists
→ findings

Verifier
→ evidence confirmation

Python
→ enforcement

Reports
→ deterministic output
```

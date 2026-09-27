````
---
name: finding-verification
description: >
  Verifies, refutes, or preserves the uncertainty of existing PR Guardian
  findings using the minimum targeted evidence necessary to establish a
  justified verification status.
---

# Finding Verification

## Purpose

Verify existing PR Guardian findings without performing a new review.

This skill is strictly evidence-oriented.

Its purpose is to determine whether an existing finding is:

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

The verifier must not create new findings.

The verifier must not broaden scope into general code review.

---

## Core Principle

> Reviewers find. Verifier proves.

Verification is not a second specialist review.

Verification evaluates a concrete existing claim.

---

## Use When

Verify only findings that are eligible for additional evidence collection.

Default priority:

1. `CRITICAL`
2. `HIGH`
3. selected `MEDIUM`

Do not verify `LOW` or informational findings by default.

A `MEDIUM` finding should be selected only when:

- available evidence is incomplete
- the claim is testable
- verification can materially increase confidence
- the result may affect engineering action
- the verification cost is proportionate to the uncertainty

Prefer one batched verification execution when multiple findings qualify.

---

## Inputs

The verifier consumes existing findings.

Typical source:

`reports/findings/<pr-id>/*.json`

Optional supporting artifacts may include:

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json`
- previous verification results
- deterministic pre-scan evidence
- directly relevant repository files
- directly relevant test files
- directly relevant configuration

Do not require broad repository context by default.

---

## Candidate Eligibility

Normally verify findings with:

`verification_status: UNVERIFIED`

or:

`verification_status: VERIFICATION_FAILED`

Do not automatically re-verify findings already marked:

- `VERIFIED`
- `REFUTED`
- `NOT_APPLICABLE`

unless the active command explicitly targets them.

---

# Verification Process

For each finding:

1. Read the existing claim.
2. Preserve its original meaning.
3. Convert the claim into a testable hypothesis.
4. Reuse existing evidence.
5. Identify the smallest missing piece of evidence.
6. Inspect only directly relevant files when needed.
7. Select the least expensive sufficient verification method.
8. Execute targeted verification only if necessary.
9. Record the evidence.
10. Assign exactly one justified verification status.

Do not expand scope merely because additional repository context is available.

---

# Testable Hypothesis

Every verification should be framed as a concrete hypothesis.

Example:

```text
Finding:
Authorization may be bypassed for update requests.

Verification hypothesis:
There is a reachable request path in which an authenticated user can invoke
the update operation without satisfying the required authorization check.
```

Avoid vague goals such as:

```text
Check whether authorization is secure.
```

The verification question must correspond directly to the existing finding.

---

# Evidence Reuse

Before collecting anything new, reuse:

- original finding evidence
- changed code
- previous deterministic tool output
- existing configuration evidence
- existing schema evidence
- prior verification evidence
- directly related tests
- existing dependency metadata

Do not repeat a deterministic check that already produced valid relevant evidence.

---

# Evidence Preference

Prefer evidence in this order when applicable:

1. existing finding evidence
2. changed code
3. directly referenced caller/callee
4. directly referenced configuration
5. directly referenced schema
6. static code-path proof
7. deterministic static analysis
8. targeted unit test
9. targeted integration test
10. dependency analysis
11. other minimal manual evidence

Prefer static proof over execution when static proof is sufficient.

---

# Allowed Verification Methods

Use one or more of the following methods only when justified:

- `STATIC_ANALYSIS`
- `TARGETED_TEST`
- `INTEGRATION_TEST`
- `CONFIG_INSPECTION`
- `DEPENDENCY_ANALYSIS`
- `CODE_PATH_PROOF`
- `MANUAL_EVIDENCE`

Use the smallest sufficient method.

Do not choose a more expensive method when a simpler one can establish the same conclusion.

---

# STATIC_ANALYSIS

Use when a deterministic static check can directly confirm or reject the claim.

Examples:

- type checker
- linter rule
- dependency analyzer
- security analyzer
- migration analyzer

Scanner output alone is not sufficient unless it directly proves the original finding.

Correlate tool output with the exact finding.

---

# CODE_PATH_PROOF

Use when the claim can be proven through a reachable code path.

Document:

- entry point
- relevant branch
- guard or missing guard
- affected operation
- sink or failure point

Example:

```text
request
→ route
→ service
→ missing authorization check
→ protected update
```

The path must be supported by real code.

---

# CONFIG_INSPECTION

Use when configuration determines the behavior.

Examples:

- authentication middleware registration
- feature flags
- dependency injection bindings
- retry configuration
- timeout configuration
- queue acknowledgment settings

Do not infer runtime configuration values that are not visible.

---

# DEPENDENCY_ANALYSIS

Use when the finding depends on:

- dependency version
- package declaration
- transitive relationship
- vulnerable version range
- conflicting dependency

Do not fabricate dependency versions or CVEs.

A vulnerability claim requires concrete dependency and version evidence.

---

# TARGETED_TEST

Use when a narrow test can directly reproduce or refute the claim.

Prefer:

- one test
- one scenario
- one failure condition

Avoid running the full test suite.

Temporary verification tests may only be created under:

`reports/verification/<pr-id>/tests/`

Do not modify the repository's real test suite.

---

# INTEGRATION_TEST

Use only when static evidence or targeted unit-level proof is insufficient.

Keep the test narrowly scoped to the existing finding.

Do not start broad infrastructure unless required to evaluate the claim.

---

# MANUAL_EVIDENCE

Use when the result can be established through directly inspectable evidence that does not require execution.

Examples:

- explicit configuration
- schema declaration
- route registration
- package manifest
- API contract
- migration order

The evidence must be concrete and traceable.

---

# Status Semantics

## VERIFIED

Use `VERIFIED` only when positive evidence supports the original finding.

Examples:

- reachable code path proves the defect
- targeted test reproduces the failure
- configuration confirms the unsafe behavior
- deterministic analysis proves the claim
- migration definition proves the failure condition

Do not use `VERIFIED` based solely on plausibility.

---

## REFUTED

Use `REFUTED` only when positive evidence contradicts the finding.

Examples:

- a required guard is proven to execute before the affected operation
- the supposedly reachable path is impossible
- targeted test demonstrates the claimed defect does not occur under the relevant conditions
- configuration proves the claimed unsafe state is disabled

Absence of proof is not refutation.

---

## UNVERIFIED

Use `UNVERIFIED` when:

- evidence remains insufficient
- the claim is plausible but cannot be proven
- required environment is unavailable
- safe verification would exceed reasonable scope
- a required runtime condition cannot be reproduced
- static evidence is inconclusive

Do not force a binary decision.

---

## NOT_APPLICABLE

Use `NOT_APPLICABLE` when the original verification target does not apply to the inspected code or execution path.

Examples:

- the finding references behavior removed from the final diff
- the referenced path is not part of the active implementation
- the target condition cannot occur in the relevant code version

Do not use this status merely because verification is inconvenient.

---

## VERIFICATION_FAILED

Use `VERIFICATION_FAILED` when verification was attempted but could not complete due to tooling or environment failure.

Examples:

- test runner failed to initialize
- dependency installation failed
- required fixture unavailable
- command execution failed unexpectedly
- required local service unavailable

Do not convert tool failure into `REFUTED`.

---

# Command Execution Rules

When command execution is required:

- execute only the minimum targeted command
- avoid full test suites
- avoid broad scanners
- avoid unrelated tools
- record the exact command
- record the exit code
- capture concise relevant output
- do not repeat successful deterministic checks unnecessarily

The verifier must distinguish:

- command failure caused by the finding
- command failure caused by verification infrastructure

---

# Exit Code Interpretation

Do not interpret exit code mechanically.

For a targeted test:

- a non-zero exit code may confirm the finding if the expected failure is reproduced
- a non-zero exit code may instead mean the test infrastructure failed

The evidence and output must establish which occurred.

Do not mark `VERIFIED` merely because a command failed.

---

# Temporary Verification Files

Temporary tests or fixtures may only be written under:

`reports/verification/<pr-id>/tests/`

Do not write temporary verification files into:

- application source
- repository test directories
- migrations
- configuration directories

Temporary verification files are artifacts, not production changes.

---

# Repository Scope

Keep verification scope narrow.

Prefer:

- finding file
- directly referenced caller
- directly referenced callee
- relevant configuration
- relevant schema
- relevant targeted test
- relevant dependency declaration

Avoid:

- broad repository scans
- unrelated modules
- full architecture exploration
- speculative searches
- large file sets without a hypothesis

Expand only when the current finding requires it.

---

# Finding Integrity

The verifier must preserve the original finding identity.

Do not change:

- `finding_id`
- severity
- category
- original defect meaning

The verifier evaluates truth status only.

If evidence reveals a different defect, do not create a new finding.

That belongs to a new review cycle.

---

# Severity

Do not change finding severity.

Severity belongs to the review finding.

Verification status represents evidentiary confidence.

These are separate dimensions.

Example:

```text
severity: HIGH
verification_status: UNVERIFIED
```

is valid.

---

# Verification Evidence

Every `VERIFIED` or `REFUTED` result must include concrete evidence.

Evidence should state:

- what was inspected
- what was observed
- why it supports or contradicts the finding

Avoid conclusions such as:

```text
The issue is confirmed.
```

without proof.

Prefer:

```text
The route calls update_record() directly after authentication and there is no
role or ownership check in the route, service, or middleware path shown by the
changed code.
```

---

# Previous Results

When previous verification results exist:

- reuse them
- preserve already resolved findings
- update only selected unresolved findings
- do not overwrite `VERIFIED` or `REFUTED` by default
- retain useful prior evidence

One authoritative result should exist per `finding_id`.

The verification summary must reflect the current authoritative results after merge.

---

# Merge Behavior

When updating verification results:

1. load previous results
2. preserve valid resolved entries
3. replace only findings intentionally re-evaluated
4. preserve unresolved findings not targeted
5. keep one current result per finding
6. preserve traceability

Do not discard previous valid evidence without reason.

---

# Verification Summary

Every verifier execution must return a concise summary for direct inclusion in
the final PR Guardian report.

The summary must contain exactly three semantic paragraphs represented by the
following fields:

1. `analysis`
   - explain which existing findings were selected for verification
   - identify the verification hypotheses, evidence sources, code paths,
     configuration, tests, dependencies, or other targeted artifacts actually
     inspected
   - mention relevant finding IDs and code locations when available

2. `result`
   - explain what the verification concluded
   - summarize which findings were `VERIFIED`, `REFUTED`, `UNVERIFIED`,
     `NOT_APPLICABLE`, or `VERIFICATION_FAILED`
   - describe the practical evidentiary outcome without changing severity,
     category, or finding meaning
   - if no eligible findings existed, state that verification was not required

3. `implementation`
   - explain where the verified or refuted behavior is implemented
   - point to the most relevant files, symbols, routes, configuration entries,
     migrations, schemas, dependencies, or targeted tests actually used as
     evidence
   - when execution occurred, mention the targeted verification artifact or
     command context without reproducing excessive output

The summary must:

- be based only on evidence actually inspected by the verifier
- not create new findings
- not reinterpret or rewrite specialist findings
- not invent files, symbols, commands, exit codes, tests, runtime behavior,
  package versions, CVEs, or verification outcomes
- not claim a finding was verified or refuted without positive evidence
- not duplicate the complete per-finding verification results
- remain concise enough for direct inclusion in `review.md`
- remain understandable without requiring the raw verification artifact
- use factual technical prose rather than generic verification language

Example:

```json
{
  "summary": {
    "analysis": "Verified findings `SEC-001` and `CODE-002` using the existing specialist evidence, the changed route and service code, and one targeted code-path inspection. No broad repository scan or full test suite was executed.",
    "result": "`SEC-001` was VERIFIED because the changed request path reaches the protected update without the required authorization check. `CODE-002` remained UNVERIFIED because the relevant runtime condition could not be established safely from the available static evidence.",
    "implementation": "The evidence for `SEC-001` is implemented in `src/api/orders.py` and the directly called update service. The unresolved behavior for `CODE-002` is located in `src/services/order_processor.py`, where additional runtime evidence would be required."
  }
}
```

The orchestrator owns final rendering of the summary.

---

# Output Contract

Write:

`reports/verification/<pr-id>/verification-results.json`

The artifact must contain:

- `pr_id`
- `summary`
- `results`

Recommended structure:

```json
{
  "pr_id": 42,
  "summary": {
    "analysis": "Verified the selected high-priority findings using existing specialist evidence and targeted code-path inspection.",
    "result": "One finding was VERIFIED and one remained UNVERIFIED because the required runtime condition could not be established from the available evidence.",
    "implementation": "Verification evidence was taken from the changed route, service implementation, and directly related configuration referenced by the original findings."
  },
  "results": [
    {
      "finding_id": "SEC-001",
      "status": "VERIFIED",
      "method": "CODE_PATH_PROOF",
      "evidence": "The changed route reaches the protected update without an authorization check.",
      "command": null,
      "exit_code": null,
      "notes": "Static code-path evidence was sufficient."
    }
  ]
}
```

If no eligible findings exist, still return a summary:

```json
{
  "pr_id": 42,
  "summary": {
    "analysis": "No findings were eligible for verification in this run.",
    "result": "Verification was not required because no unresolved eligible findings were selected.",
    "implementation": "No code path, configuration, dependency, or test artifact required additional verification."
  },
  "results": []
}
```

`summary.analysis`, `summary.result`, and `summary.implementation` are required
for every verifier execution, including no-op runs.

The summary must describe only verification work that actually occurred.

---

# Result Fields

Every verification result must include:

- `finding_id`
- `status`
- `method`
- `evidence`
- `command`
- `exit_code`
- `notes`

Use:

```json
"command": null
```

and:

```json
"exit_code": null
```

when no command was executed.

---

# Valid Status Values

Only use:

- `VERIFIED`
- `REFUTED`
- `UNVERIFIED`
- `NOT_APPLICABLE`
- `VERIFICATION_FAILED`

Do not invent additional statuses.

---

# Valid Method Values

Use:

- `STATIC_ANALYSIS`
- `TARGETED_TEST`
- `INTEGRATION_TEST`
- `CONFIG_INSPECTION`
- `DEPENDENCY_ANALYSIS`
- `CODE_PATH_PROOF`
- `MANUAL_EVIDENCE`

Do not invent method names unless the schema explicitly changes.

---

# Batch Verification

When multiple findings qualify, prefer one verifier execution.

Process findings independently within the batch.

Do not let verification of one finding bias another.

Each result must have its own:

- hypothesis
- evidence
- status
- method

---

# Relationship With Specialists

Specialists discover findings.

The verifier evaluates them.

The verifier must not:

- repeat the specialist review
- expand into unrelated domains
- search for additional defects
- produce findings for observations discovered during verification

If unrelated problems are noticed, ignore them for this verification run.

---

# Relationship With Final Synthesis

The verifier does not classify findings as:

- `BLOCKING`
- `ADVISORY`

That belongs to deterministic synthesis.

The verifier only sets evidentiary status.

---

# Failure Handling

If a finding cannot be verified because evidence is insufficient:

`UNVERIFIED`

If verification infrastructure fails:

`VERIFICATION_FAILED`

If evidence directly contradicts the finding:

`REFUTED`

If evidence supports the finding:

`VERIFIED`

Do not hide failures.

---

# Must Not

Do not:

- create new findings
- perform general code review
- rerun specialist reviewers
- change finding severity
- change finding category
- rewrite the original finding meaning
- modify production code
- modify migrations
- modify application configuration
- modify dependency manifests
- write tests outside `reports/verification/`
- run full test suites by default
- run broad scanners by default
- scan unrelated files
- invent evidence
- invent commands
- invent tool output
- invent exit codes
- invent runtime behavior
- invent package versions
- invent CVEs
- claim verification without concrete evidence
- treat missing evidence as refutation
- overwrite resolved verification without explicit targeting
- invent verification summary content not supported by actual evidence
- claim files, code paths, commands, tests, or implementation locations in the summary that were not actually inspected
- commit
- push
- merge
- publish

---

# Done When

Verification is complete when every finding in the batch has:

- a preserved `finding_id`
- a justified status
- a valid verification method
- concrete evidence or an explicit explanation of insufficient evidence
- command and exit code metadata when execution occurred
- notes when relevant

and:

- the three required verification summary paragraphs were produced from actual verification evidence
- the summary accurately reflects the current merged verification results

and:

`reports/verification/<pr-id>/verification-results.json`

has been successfully written or updated.

If no eligible findings exist, return a concise no-op result with the required three-paragraph verification summary and do not invent verification work.

````
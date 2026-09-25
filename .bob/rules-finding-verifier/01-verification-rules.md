# Finding Verifier — Rules

These rules govern the finding-verifier mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Independent, skeptical verification of findings produced by specialist reviewers.
This agent does NOT search for new bugs. It only proves or refutes existing claims.

---

## Responsibilities

- Receive a finding hypothesis with its evidence and severity
- Select an appropriate verification strategy
- Execute the verification using deterministic tools or targeted tests
- Record the result with supporting evidence
- Write structured results to `verification-results.json`

The verifier is a skeptic. It must treat every finding as "unconfirmed until proven."

---

## Verification Strategies

```
STATIC_ANALYSIS    — Run Bandit, Semgrep, Ruff, mypy on specific files/rules
TARGETED_TEST      — Write and execute a focused test that exercises the claim
INTEGRATION_TEST   — Run an existing or new integration test that covers the scenario
CONFIG_INSPECTION  — Read config/env/settings files to confirm or deny the claim
DEPENDENCY_ANALYSIS — Run pip-audit or equivalent CVE checker
CODE_PATH_PROOF    — Trace and document the execution path showing reachability
MANUAL_EVIDENCE    — Cite specific file lines that constitute direct proof
```

---

## Allowed Verification Statuses

```
VERIFIED             — The claim has been reproduced or directly evidenced
UNVERIFIED           — Evidence remains inconclusive; neither confirmed nor refuted
NOT_APPLICABLE       — This type of finding cannot be verified empirically
VERIFICATION_FAILED  — Verification could not be completed (tool error, env problem)
REFUTED              — Verification demonstrated the problem does not occur
```

---

## Verification Priority

```
1. CRITICAL severity findings
2. HIGH severity findings
3. MEDIUM severity findings
4. LOW severity findings (only when verification cost is low)
```

---

## Inputs

```
reports/context/<pr-id>/pr-context.json
reports/findings/<pr-id>/*.json  (all specialist findings)
Source files referenced by findings (read-only)
```

Input format per finding:

```json
{
  "finding_id": "<string>",
  "claim": "<string>",
  "evidence": ["<string>"],
  "severity": "<string>",
  "verification_strategy": ["<strategy>"]
}
```

---

## Allowed Actions

- Read any file in the repository (read-only)
- Execute static analysis tools: Bandit, Semgrep, Ruff, mypy
- Execute pip-audit and dependency scanners
- Create and execute targeted test files in `reports/verification/<pr-id>/tests/`
- Execute existing test suite in read-only mode
- Write results to `reports/verification/<pr-id>/verification-results.json`

---

## Forbidden Actions

- Creating new findings (the verifier does NOT discover new bugs)
- Searching for additional bugs beyond the scope of provided findings
- Elevating or downgrading the severity of a finding
- Modifying production code, migrations, or application configuration
- Assuming the reviewer is correct without evidence
- Marking a finding VERIFIED without concrete, reproducible evidence
- Marking a finding REFUTED based only on absence of evidence
- Creating commits, pushing, or publishing to GitHub
- Adding verification tests to the official project test suite

---

## Evidence Requirements

For VERIFIED status:
- A reproduction (test pass, tool hit, traced code path) that confirms the claim
- The exact command executed and its output (or relevant excerpt)

For REFUTED status:
- A demonstration that the vulnerable path cannot be reached, OR
- Tool output explicitly showing the condition does not hold, OR
- A test that demonstrates correct behavior contradicting the claim

For UNVERIFIED status:
- An explanation of why evidence is inconclusive
- What would be needed to move to VERIFIED or REFUTED

---

## Verification Test Discipline

All tests created during verification must reside in:

```
reports/verification/<pr-id>/tests/
```

Never add verification tests to:

```
tests/
test/
spec/
```

or any other official project test directory.

---

## Outputs

```
reports/verification/<pr-id>/verification-results.json
reports/verification/<pr-id>/tests/*  (when targeted tests are created)
```

---

## Completion Criteria

The verifier's work is complete when:

- All CRITICAL and HIGH findings have been processed
- All MEDIUM findings have been processed (or documented as VERIFICATION_FAILED
  when environment constraints prevent it)
- `verification-results.json` is written and schema-valid
- Every result has a `status`, `method`, and `evidence` array (non-empty for
  VERIFIED and REFUTED results)

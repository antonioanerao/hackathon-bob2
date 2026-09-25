# Finding Verifier — Rules

These rules govern the finding-verifier mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Independent, skeptical verification of findings produced by specialist reviewers.
This agent does NOT search for new bugs. It only proves or refutes existing claims.

---

## When Verification Is Invoked

The finding-verifier is **not invoked automatically on every PR run**.

The orchestrator invokes it only when the verification budget justifies it:

| Condition | Orchestrator Action |
|-----------|---------------------|
| TRIVIAL or LOW risk level | Do not invoke verifier |
| No CRITICAL or HIGH findings | Do not invoke verifier |
| CRITICAL or HIGH findings exist | Invoke verifier with a finding batch |
| MEDIUM findings with CERTAIN confidence | Do not invoke verifier |
| MEDIUM findings with POSSIBLE confidence | Optionally invoke if cost is low |
| LOW findings | Do not invoke verifier |
| INFO findings | Do not invoke verifier |

---

## Batched Invocation

The verifier is invoked **at most once per PR run**.

It receives a batch of findings to process together, not one finding per invocation.

```json
{
  "verification_batch": [
    {
      "finding_id": "<string>",
      "claim": "<one-sentence verifiable claim>",
      "evidence": ["<existing evidence from reviewer>"],
      "severity": "<string>",
      "verification_strategy": ["<strategy>"]
    }
  ]
}
```

---

## Responsibilities

- Receive a batch of finding hypotheses with their evidence and severity
- Select appropriate verification strategies
- Execute verification using deterministic tools or targeted tests
- Reuse existing deterministic tool results when they already prove or refute a claim
- Record results with supporting evidence
- Write structured results to `verification-results.json`

The verifier is a skeptic. It must treat every finding as "unconfirmed until proven."

---

## Verification Priority Within a Batch

```
1. CRITICAL severity findings
2. HIGH severity findings
3. MEDIUM severity findings (when confidence != CERTAIN or evidence is thin)
```

LOW and INFO findings are **not included** in the verification batch.

---

## Deterministic Shortcut

If a finding already has proof from the orchestrator's deterministic pre-scan:
- A Bandit match
- A Semgrep match
- A failing targeted test
- A pip-audit CVE result
- A direct code-path proof in the finding evidence

Do NOT re-run the same tool. Consume the existing result.
Record the method as the appropriate strategy and status as VERIFIED.

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

## Inputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/context-package.json  (pre-scan results available here)
reports/findings/<pr-id>/*.json               (all specialist findings)
Source files referenced by findings (read-only)
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
- Re-running a deterministic tool that already produced a result in context-package.json

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

- All CRITICAL findings in the batch have been processed
- All HIGH findings in the batch have been processed
- MEDIUM findings included in the batch have been processed
- `verification-results.json` is written and schema-valid
- Every result has a `status`, `method`, and `evidence` array (non-empty for
  VERIFIED and REFUTED results)
- Pre-scan results were consumed where applicable (not re-run)

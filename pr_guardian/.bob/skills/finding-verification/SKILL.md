---
name: finding-verification
description: >
  Verifies or refutes existing findings using targeted evidence.
---

# Finding Verification

## Use When

Verify only:

- CRITICAL
- HIGH
- selected MEDIUM when evidence is weak

Do not verify LOW/INFO by default.

Prefer one batched verification run.

## Rules

- verify only existing findings
- do not search for new bugs
- reuse existing evidence
- use minimum files and commands
- do not repeat deterministic checks unnecessarily

## Verify

For each finding:

1. Convert the claim into a testable hypothesis.
2. Reuse existing evidence first.
3. If needed, use one method:

`STATIC_ANALYSIS`, `TARGETED_TEST`, `INTEGRATION_TEST`,
`CONFIG_INSPECTION`, `DEPENDENCY_ANALYSIS`,
`CODE_PATH_PROOF`, `MANUAL_EVIDENCE`.

4. Set status:

`VERIFIED`, `REFUTED`, `UNVERIFIED`,
`NOT_APPLICABLE`, `VERIFICATION_FAILED`.

## Evidence

`VERIFIED` and `REFUTED` require concrete evidence.

When executing:

- prefer targeted tests
- record command and exit code
- write temporary tests only under:

`reports/verification/<pr-id>/tests/`

If execution or tooling fails, use `VERIFICATION_FAILED`.

Absence of proof is not evidence of refutation.

## Output

Write:

`reports/verification/<pr-id>/verification-results.json`

Each result must include:

- `finding_id`
- `status`
- `method`
- `evidence`
- `command`, if executed
- `exit_code`, if applicable
- `notes`

## Must Not

- create new findings
- change severity
- modify production code/config/migrations
- write tests outside `reports/verification/`
- scan unrelated files
- claim verification without evidence
- re-run specialist reviewers

## Done When

Every finding in the batch has a justified status and the verification artifact was written.
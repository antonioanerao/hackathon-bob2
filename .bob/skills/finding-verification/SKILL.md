---
name: finding-verification
description: >
  Verifies or refutes existing findings using targeted, reproducible evidence.
---

# Finding Verification

## Use When

Run only for eligible findings, preferably in one batch:

- CRITICAL
- HIGH
- selected MEDIUM when evidence is weak

Do not run for LOW/INFO by default.

## Rules

- Verify only findings already reported.
- Do not search for new bugs.
- Reuse existing deterministic evidence.
- Do not re-run tools unless necessary.
- Use the minimum files and commands required.

## Verification

For each finding:

1. Restate the claim as a testable hypothesis.
2. Prefer existing evidence first.
3. If needed, choose one strategy:

`STATIC_ANALYSIS`, `TARGETED_TEST`, `INTEGRATION_TEST`,
`CONFIG_INSPECTION`, `DEPENDENCY_ANALYSIS`,
`CODE_PATH_PROOF`, `MANUAL_EVIDENCE`.

4. Classify as:

`VERIFIED`, `REFUTED`, `UNVERIFIED`,
`NOT_APPLICABLE`, `VERIFICATION_FAILED`.

## Evidence

`VERIFIED` and `REFUTED` require concrete evidence.

When execution is required:

- prefer targeted tests over full suites
- record command and exit code
- create temporary tests only under:

`reports/verification/<pr-id>/tests/`

If a tool or environment fails, use `VERIFICATION_FAILED`.

Do not mark REFUTED merely because proof was not found.

## Output

Write:

`reports/verification/<pr-id>/verification-results.json`

Each result must include:

- `finding_id`
- `status`
- `method`
- `command` if executed
- `exit_code` if applicable
- `evidence`
- `notes`

## Must Not

- create new findings
- change finding severity
- modify production code/config/migrations
- add tests to official test directories
- scan unrelated files
- repeat existing deterministic checks unnecessarily
- claim verification without evidence

## Done When

Every finding in the verification batch has a justified result and the verification file is written.
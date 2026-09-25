---
name: finding-verification
description: >
  Independently verifies or refutes findings produced by specialist reviewers
  using deterministic tools, targeted tests, code-path analysis, and
  config inspection. Used by the finding-verifier.
---

# Finding Verification

## Purpose

Act as a skeptical, independent engineer who either proves or disproves
a finding hypothesis. The verifier never searches for new bugs.
It only evaluates claims already made.

## Core Principle

> A finding unverified is a hypothesis. Verify it or state why you cannot.

## When to Use

Activated by the orchestrator after all specialist reviewers have completed.
Receives findings from all specialists and processes them by priority.

## Inputs

- `reports/findings/<pr-id>/*.json` (all specialist findings)
- `reports/context/<pr-id>/pr-context.json`
- Source files referenced by findings (read-only)

Per-finding input format:
```json
{
  "finding_id": "<string>",
  "claim": "<string>",
  "evidence": ["<string>"],
  "severity": "<string>",
  "verification_strategy": ["<strategy>"]
}
```

## Verification Priority

Process in this order:
1. CRITICAL severity
2. HIGH severity
3. MEDIUM severity
4. LOW severity (when environment cost is low)

## Phases

### Phase 1: Claim Formulation

For each finding, restate the claim in verifiable terms:

```
Finding: "app/repositories.py line 24 returns records for any org_id 
          passed in the request body without checking authenticated user's org"

Verifiable claim: "The function get_events() at line 24 uses the org_id 
                  parameter from the request body directly in the SQL query 
                  without comparing it to the authenticated user's session org_id"
```

### Phase 2: Strategy Selection

Choose the most appropriate strategy:

| Strategy | When to Use |
|---|---|
| `STATIC_ANALYSIS` | Tool-detectable patterns (injection, CVE, type errors) |
| `TARGETED_TEST` | Behavioral claims (authorization bypass, wrong return value) |
| `INTEGRATION_TEST` | End-to-end claims (route returns wrong data) |
| `CONFIG_INSPECTION` | Configuration-based claims (missing env var, wrong setting) |
| `DEPENDENCY_ANALYSIS` | CVE claims (specific package vulnerability) |
| `CODE_PATH_PROOF` | Reachability claims (this code path can be triggered by X) |
| `MANUAL_EVIDENCE` | Direct code citation (the code literally does X at line Y) |

### Phase 3: Evidence Gathering

Execute the chosen strategy:

**STATIC_ANALYSIS:**
```bash
bandit -t <rule_id> <file>
semgrep --config=<rule> <file>
ruff check <file> --select <code>
mypy <file>
```

**TARGETED_TEST:**
```python
# Create: reports/verification/<pr-id>/tests/test_<finding_id>.py
# Execute: pytest reports/verification/<pr-id>/tests/test_<finding_id>.py -v
# Record: exit code, stdout, stderr
```

**DEPENDENCY_ANALYSIS:**
```bash
pip-audit --requirement requirements.txt
pip-audit --format json | grep "<package_name>"
```

**CODE_PATH_PROOF:**
- Trace: caller → changed function → vulnerable operation
- Cite each file and line in the path
- State whether any guard condition prevents the path from being reached

**CONFIG_INSPECTION:**
```bash
cat .env.example config/settings.py
grep -n "<config_key>" config/*.py
```

### Phase 4: Result Classification

Based on the evidence gathered:

**VERIFIED:**
- Test passed demonstrating the vulnerability
- Tool output explicitly matched the claim
- Code path is directly traceable with no guards preventing it
- Configuration confirms the claimed state

**REFUTED:**
- Test demonstrated correct behavior (vulnerability not reproducible)
- Tool output explicitly contradicts the claim
- A guard condition prevents the claimed code path from being reached
- Configuration contradicts the claim

**UNVERIFIED:**
- Evidence is inconclusive in either direction
- The finding is plausible but cannot be confirmed without runtime access
- Evidence points toward the claim but is not conclusive

**NOT_APPLICABLE:**
- The finding type cannot be verified empirically
  (e.g., a design recommendation with no testable predicate)

**VERIFICATION_FAILED:**
- The required tool is not available (`TOOL_UNAVAILABLE`)
- The test environment is broken (missing dependencies, import errors)
- The verification process itself produced an error

### Phase 5: Evidence Documentation

For VERIFIED and REFUTED results, evidence must be non-empty.
Record the exact command, exit code, and relevant output excerpt.

For UNVERIFIED, explain what would be needed to resolve the uncertainty.

## Deterministic Tools & Evidence

```bash
bandit -r <file> -f json
semgrep --config=p/owasp-top-ten --json <file>
pip-audit --format json
pytest reports/verification/<pr-id>/tests/ -v --tb=short
mypy <file> --strict
```

## Canonical Output

File: `reports/verification/<pr-id>/verification-results.json`

```json
{
  "pr_id": "<integer>",
  "results": [
    {
      "finding_id": "<string>",
      "status": "VERIFIED | UNVERIFIED | NOT_APPLICABLE | VERIFICATION_FAILED | REFUTED",
      "method": "STATIC_ANALYSIS | TARGETED_TEST | INTEGRATION_TEST | CONFIG_INSPECTION | DEPENDENCY_ANALYSIS | CODE_PATH_PROOF | MANUAL_EVIDENCE",
      "command": "<command executed or null>",
      "exit_code": "<integer or null>",
      "evidence": ["<tool output excerpt>", "<test result>", "<code path citation>"],
      "notes": "<explanation of result or limitation>"
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Tool not installed | Record `TOOL_UNAVAILABLE` in notes; status = `VERIFICATION_FAILED` |
| Test environment broken | Record error; status = `VERIFICATION_FAILED` |
| Finding is too vague to test | Record in notes; status = `UNVERIFIED` |
| Evidence points both ways | Record both; status = `UNVERIFIED` with explanation |

## What This Skill Must Not Do

- Create new findings or report bugs not in the input
- Elevate the severity of any finding
- Mark a finding as VERIFIED without reproducible evidence
- Mark a finding as REFUTED based solely on absence of evidence
- Add verification tests to the project's official test directories
- Modify production code, migrations, or application configuration

## Completion Criteria

- Every CRITICAL and HIGH finding has a result entry
- Every MEDIUM finding has a result entry
- LOW findings have entries when verification cost was low
- All VERIFIED results have non-empty evidence arrays
- All REFUTED results have non-empty evidence arrays
- `verification-results.json` is written and schema-valid

---
name: security-review
description: >
  Identifies security vulnerabilities introduced or worsened by the PR.
  Covers OWASP Top 10, authentication, authorization, multi-tenancy,
  injections, SSRF, path traversal, secrets, cryptography, and dependency CVEs.
  Used by the security-review-specialist.
---

# Security Review

## Purpose

Find security vulnerabilities that this PR introduces or makes exploitable.
Every finding must trace a concrete, reachable attack path — not just
resemble a vulnerability pattern.

## Core Principle

> Don't just comment. Prove it. Trace the attack path.

## When to Use

Activated when SECURITY, AUTHENTICATION, AUTHORIZATION, or TENANT_BOUNDARY_CHANGED
triggers are present. Also activated for DEPENDENCY_CHANGED when new packages
are added.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json` (security section)
- Git diff and source files (read-only)

## Phases

### Phase 1: Attack Surface Mapping

Identify the attack surface changed by this PR:
- New routes or modified routes
- Changed authentication middleware
- Changed authorization decorators or permission checks
- Changed input deserialization or validation
- Changed file upload handling
- Changed database query construction
- Changed cryptographic operations
- Changed external HTTP calls
- Changed dependency versions

### Phase 2: Taint Flow Analysis

For every suspicious data flow, trace the full path:

```
[1] Untrusted Source
    (HTTP request, query params, headers, body, file upload, env var from user)
         ↓
[2] Transformations
    (sanitization, validation, encoding, parsing, deserialization)
         ↓
[3] Security Boundary
    (authentication check, authorization check, tenant filter, rate limit)
         ↓
[4] Sink
    (SQL execution, OS command, file write, HTTP response, third-party API)
```

Document each step. A finding without a traced path is not acceptable for HIGH+.

### Phase 3: Authentication Analysis

When authentication logic is modified:
- Is session invalidation correct on logout?
- Are token expiry and rotation handled?
- Are credentials compared using timing-safe comparison?
- Is brute force protection in place?
- Are failed auth events logged (not leaking info)?

### Phase 4: Authorization Analysis

When authorization logic is modified:
- Are permission checks applied before data access, not after?
- Is the permission model additive (deny by default) or subtractive?
- Can a lower-privilege user escalate via parameter manipulation?
- Are all endpoints (including internal/admin) protected?
- Are tenant/organization boundaries enforced at the data layer?

### Phase 5: Tenant Isolation Analysis

When multi-tenant context is present:
- Is `org_id` or `tenant_id` taken from the authenticated session, not the request body?
- Do database queries filter by tenant before returning data?
- Can a user of tenant A access or modify data of tenant B?

### Phase 6: Injection Analysis

For each database interaction, trace the code path statically:
- Is user input passed directly to a raw SQL query string?
- Is parameterized query syntax used correctly?
- Is an OS command constructed from user-controlled input?

If the orchestrator pre-scan results (Bandit, Semgrep) are available in `context-package.json`,
consume those results. Do NOT re-run Bandit or Semgrep directly.
If no pre-scan result exists, include a `verification_recommendation` for the finding-verifier.

For each template rendering:
- Is user input escaped before insertion?

### Phase 7: Dependency Vulnerability Scan

When dependency files changed, check `context-package.json` for pip-audit results
already produced by the orchestrator.
Do NOT re-run pip-audit or safety directly.
If no pre-scan result exists, include a `verification_recommendation` for the finding-verifier.

Record any CVEs found in pre-scan results.

### Phase 8: Secrets and Cryptography

- Are any secrets, API keys, or passwords hardcoded in the diff?
- Are cryptographic algorithms using approved, current standards?
- Are hardcoded keys or salts present?
- Is random number generation using `secrets` (Python) or equivalent?

## Deterministic Tools & Evidence

```bash
# Read-only investigation — no execution:
grep -rn "password\|secret\|token\|api_key" --include="*.py" . | grep -v "test"
grep -rn "MD5\|SHA1\|DES\b" --include="*.py" .

# Pre-scan results available in context-package.json (produced by orchestrator):
# bandit, semgrep, pip-audit — consume, do not re-run
```

## Canonical Output

File: `reports/findings/<pr-id>/security-review-specialist.json`

Finding IDs: `SEC-001`, `SEC-002`, ...

```json
{
  "reviewer": "security-review-specialist",
  "findings": [
    {
      "id": "SEC-001",
      "category": "AUTHENTICATION | AUTHORIZATION | TENANT_ISOLATION | SQL_INJECTION | COMMAND_INJECTION | SSRF | PATH_TRAVERSAL | IDOR | INSECURE_DESERIALIZATION | SECRET_EXPOSURE | CRYPTO_MISUSE | XSS | DEPENDENCY_CVE | UNSAFE_INPUT",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<concise title>",
      "description": "<attack path explanation>",
      "file": "<path>",
      "line": "<integer>",
      "evidence": ["<tool output or code path citation>"],
      "impact": "<what an attacker can achieve>",
      "recommendation": "<actionable remediation>",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "security-review-specialist",
      "metadata": {
        "root_cause": "",
        "related_symbols": [],
        "attack_path": "<source → transformation → boundary → sink>"
      }
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Bandit/Semgrep unavailable | Record `TOOL_UNAVAILABLE`, perform manual analysis |
| pip-audit unavailable | Record `TOOL_UNAVAILABLE`, note dependency risk without CVE |
| Dynamic query construction (e.g., ORM) | Trace ORM to SQL output before ruling out injection |
| Multi-level indirect vulnerability | Lower confidence to POSSIBLE if full path cannot be traced |

## What This Skill Must Not Do

- Report a finding based solely on code resembling a pattern without tracing the path
- Report a PRE_EXISTING vulnerability as INTRODUCED_BY_PR
- Fabricate Bandit rule IDs, Semgrep match lines, or CVE numbers
- Assume a security check is absent without verifying its absence

## Completion Criteria

- All changed auth, authorization, input, and dependency code has been analyzed
- Taint paths have been traced for all suspicious flows
- Pre-scan results from `context-package.json` have been consumed where applicable
- Findings requiring tool execution are marked UNVERIFIED with verification_recommendation
- All findings have file + line + evidence + attack path
- Output file is written and schema-valid

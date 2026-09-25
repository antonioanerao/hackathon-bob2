---
name: security-review
description: >
  Reviews PR changes for concrete, reachable security vulnerabilities.
---

# Security Review

## Use When

Activate for changes involving:

- authentication/authorization
- tenant isolation
- untrusted input
- secrets/cryptography
- file handling
- external requests
- dependency security

## Check

Review changed code for:

- auth/authz bypass
- cross-tenant access
- SQL/command injection
- SSRF/path traversal
- insecure deserialization
- secret exposure
- crypto misuse
- unsafe input handling
- vulnerable dependencies

Trace suspicious flows as:

`source → validation/transformation → security boundary → sink`

HIGH/CRITICAL findings require a concrete reachable path.

Use existing Bandit/Semgrep/pip-audit results from context when available. Do not re-run them.

## Evidence

Each finding must include:

- changed file/line
- concrete attack path or tool evidence
- attacker impact
- actionable recommendation

If runtime/tool proof is still needed:

`verification_status: UNVERIFIED`

and recommend verification by `finding-verifier`.

## Output

Write:

`reports/findings/<pr-id>/security-review-specialist.json`

Finding IDs:

`SEC-001`, `SEC-002`, ...

Use the canonical finding schema.

Categories:

`AUTHENTICATION`, `AUTHORIZATION`, `TENANT_ISOLATION`,
`SQL_INJECTION`, `COMMAND_INJECTION`, `SSRF`, `PATH_TRAVERSAL`,
`IDOR`, `INSECURE_DESERIALIZATION`, `SECRET_EXPOSURE`,
`CRYPTO_MISUSE`, `XSS`, `DEPENDENCY_CVE`, `UNSAFE_INPUT`.

## Must Not

- execute scanners or tests
- report pattern-only vulnerabilities without a reachable path
- invent CVEs/tool results
- assume a security control is absent without checking
- report pre-existing issues as introduced by the PR

## Done When

All security-relevant changes in scope were reviewed and evidence-backed findings were written.
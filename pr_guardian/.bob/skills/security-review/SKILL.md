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

`source → validation → security boundary → sink`

HIGH/CRITICAL findings require a concrete reachable path.

Reuse existing security scan results from context.

Do not re-run scanners or deterministic checks.

## Evidence

Each finding must include:

- changed file/line
- concrete attack path or tool evidence
- practical security impact
- actionable recommendation

Do not emit speculative findings when one targeted read can confirm or refute them.

If further proof is required, keep:

`verification_status: UNVERIFIED`

for `finding-verifier`.

## Output

Return findings as canonical JSON to the orchestrator.

Finding IDs:

`SEC-001`, `SEC-002`, ...

Set:

`verification_status: UNVERIFIED`

The orchestrator persists:

`reports/findings/<pr-id>/security-review-specialist.json`

If no concrete vulnerabilities exist, return an empty findings list.

## Must Not

- execute scanners or tests
- report theoretical vulnerabilities without a reachable path
- invent CVEs or tool results
- assume controls are absent without checking
- report pre-existing issues as introduced
- scan unrelated code

## Done When

All relevant security changes were reviewed and evidence-backed findings were returned to the orchestrator.
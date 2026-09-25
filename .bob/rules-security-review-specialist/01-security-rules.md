# Security Review Specialist — Rules

## Scope

Review changed code for concrete, reachable security vulnerabilities.

## Check

Focus on:

- authentication/authz bypass
- tenant isolation
- injection
- SSRF/path traversal/IDOR
- insecure deserialization
- secret exposure
- crypto misuse
- unsafe input handling
- dependency CVEs

Trace suspicious flows as:

`source → validation/transformation → security boundary → sink`

## Context

Start from:

`reports/context/<pr-id>/context-package.json`

Read only relevant files.

`MAX_FILES_PER_SPECIALIST = 5`

Expand only when a concrete attack-path hypothesis requires it.

## Evidence

Each finding must include:

- changed file/line
- reachable attack path
- attacker impact
- supporting pre-scan evidence when available

If proof is incomplete:

`verification_status: UNVERIFIED`

and recommend `finding-verifier`.

## Output

Write:

`reports/findings/<pr-id>/security-review-specialist.json`

Finding IDs:

`SEC-001`, `SEC-002`, ...

Use the canonical finding schema.

## Must Not

- modify production code/config/migrations
- execute security scanners directly
- read other specialists' findings
- mark findings as VERIFIED
- report pattern-only vulnerabilities without a reachable path
- invent CVEs or tool output
- commit, push, or publish

## Done When

All relevant security changes were reviewed and evidence-backed findings were written.
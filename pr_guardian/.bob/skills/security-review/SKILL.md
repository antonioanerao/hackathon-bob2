---
name: security-review
description: >
  Reviews Pull Request changes for concrete, reachable, evidence-backed security
  vulnerabilities involving trust boundaries, authentication, authorization,
  tenant isolation, untrusted input, secrets, cryptography, file handling,
  external requests, and dependency security.
---

# Security Review

## Purpose

Review security-relevant changes introduced or affected by the Pull Request.

The goal is to identify concrete vulnerabilities or security regressions that
have:

- a realistic source
- a reachable execution path
- a security boundary
- an unsafe sink or privileged operation
- practical security impact

Do not perform a generic security audit.

Do not report theoretical weaknesses that cannot be tied to changed code or
directly related context.

---

## Use When

Activate this skill when the Pull Request changes one or more of the following:

- authentication
- authorization
- roles or permissions
- tenant isolation
- organization or account boundaries
- untrusted input handling
- request validation
- file upload or filesystem access
- secret handling
- cryptography
- key management
- tokens or sessions
- external HTTP/network requests
- command execution
- deserialization
- dependency versions
- security-sensitive configuration
- webhook handling
- privileged operations

---

# Primary Review Goals

Determine whether the PR introduces or exposes:

- authentication bypass
- authorization bypass
- privilege escalation
- IDOR / object-level authorization failures
- cross-tenant access
- SQL injection
- command injection
- code injection
- SSRF
- path traversal
- unsafe file handling
- insecure deserialization
- secret exposure
- token leakage
- weak or incorrect cryptographic usage
- unsafe trust-boundary changes
- missing validation on attacker-controlled input
- vulnerable dependency usage
- unsafe external request behavior
- security-control bypass

---

# Review Scope

Start from changed security-relevant code.

Expand only when necessary to confirm or refute a concrete hypothesis.

Relevant expansion may include:

- directly related middleware
- authentication helpers
- authorization guards
- route definitions
- direct service calls
- tenant-scoping logic
- validation code
- serializers
- file path construction
- command construction
- HTTP client configuration
- secret loading
- dependency manifests
- directly related tests
- security configuration
- one direct caller or callee

Do not scan unrelated code.

---

# Security Flow Model

Trace suspicious flows as:

```text
source
→ normalization
→ validation
→ security boundary
→ transformation
→ sink
```

Examples of sources:

- route parameter
- query parameter
- request body
- HTTP header
- uploaded filename
- uploaded file content
- webhook payload
- queue message
- environment-controlled value
- external API response

Examples of sinks:

- database query
- operating-system command
- filesystem path
- external URL
- privileged action
- authorization decision
- cryptographic operation
- secret output
- deserializer
- template execution
- dynamic code evaluation

A security finding should explain the relevant flow.

---

# Reachability

HIGH and CRITICAL findings require a concrete reachable path.

A valid finding should establish:

1. attacker or untrusted source
2. reachable application path
3. missing, weak, or bypassable security control
4. affected sink or privileged operation
5. practical impact

Do not assign HIGH or CRITICAL based only on suspicious syntax.

---

# Authentication Review

Check changed authentication behavior for:

- missing authentication enforcement
- authentication middleware bypass
- token validation regression
- signature validation errors
- session validation errors
- incorrect identity binding
- accepting unauthenticated requests
- fail-open behavior
- trust in client-supplied identity fields

Example:

```text
request
→ public route
→ service
→ privileged action
```

with no effective authentication control.

Do not confuse authentication with authorization.

---

# Authorization Review

Check for:

- missing role checks
- missing permission checks
- ownership-check bypass
- object-level authorization failures
- direct use of client-supplied user/tenant identifiers
- privilege checks occurring after a sensitive action
- authorization enforced in one path but bypassed in another
- newly exposed privileged operation without equivalent guard

Trace:

```text
authenticated actor
→ resource selection
→ authorization decision
→ privileged operation
```

A valid authorization finding must identify the missing or bypassed control.

---

# IDOR / Object-Level Authorization

Inspect endpoints or services where a user selects a resource by:

- ID
- UUID
- external key
- slug
- filename
- account identifier
- tenant identifier

Determine whether access is constrained to the authenticated actor's permitted
scope.

Do not report IDOR merely because an ID is client-controlled.

The path must lack the required authorization or ownership enforcement.

---

# Tenant Isolation

Treat tenant-boundary changes as highly sensitive.

Review for:

- missing tenant predicate
- tenant ID accepted from request body
- tenant ID trusted from client headers without established validation
- cross-tenant object lookup
- authorization check against wrong tenant
- repository methods no longer scoped by tenant
- shared cache keys missing tenant dimension
- privileged operations using resource ID without tenant binding

Trace:

```text
authenticated tenant A
→ attacker-controlled resource ID
→ lookup
→ resource belonging to tenant B
→ read/write/delete
```

Do not claim cross-tenant access without a reachable path.

---

# Untrusted Input

Review changed handling of attacker-controlled values.

Relevant input sources include:

- request body
- query parameters
- path parameters
- HTTP headers
- cookies
- uploaded files
- webhook payloads
- queue messages
- externally sourced data

Check whether input reaches sensitive sinks without appropriate:

- validation
- parsing
- encoding
- allow-listing
- parameterization
- canonicalization

Do not report "missing validation" unless unsafe downstream behavior exists.

---

# SQL Injection

Inspect raw SQL and dynamic query construction.

Look for:

- string concatenation
- interpolation
- format strings
- dynamically constructed predicates
- unsafe identifier substitution
- unescaped user-controlled fragments

Safe parameter binding should not be reported as injection.

A valid SQL injection finding should identify:

```text
untrusted input
→ query construction
→ SQL execution
```

and the exact unsafe construction.

---

# Command Injection

Inspect process or shell execution for:

- user-controlled command fragments
- shell interpolation
- unsafe `shell=True`
- dynamic command construction
- environment-controlled executable paths
- arguments collapsed into a shell string

Trace:

```text
untrusted input
→ command construction
→ shell/process execution
```

Do not report command injection when attacker input remains a properly separated
argument and shell interpretation is not involved, unless another concrete issue
exists.

---

# SSRF

Review changed outbound-request behavior for attacker influence over:

- hostname
- URL
- scheme
- port
- redirect destination
- proxy target

Relevant path:

```text
untrusted input
→ URL construction
→ outbound request
```

Consider whether controls prevent access to:

- loopback
- link-local addresses
- internal networks
- cloud metadata endpoints
- unsupported protocols

Do not report SSRF merely because an HTTP client is used.

---

# Path Traversal

Review file path construction involving untrusted input.

Look for:

- direct path joins with user-controlled names
- `../`
- absolute path acceptance
- symlink-sensitive operations
- unsafe archive extraction
- canonicalization performed after access checks
- path validation against the wrong base directory

Trace:

```text
untrusted filename/path
→ path construction
→ filesystem operation
```

A finding should identify the reachable filesystem sink.

---

# File Upload Security

Review changes involving:

- uploaded filename
- extension
- MIME type
- content inspection
- storage location
- overwrite behavior
- executable placement
- archive extraction
- size handling
- generated public URLs

Potential concrete defects:

- path traversal
- executable upload into served directory
- arbitrary overwrite
- file type validation based only on attacker-controlled metadata
- unsafe archive extraction

Do not require every possible file-hardening mechanism.

Report only concrete exploitable behavior.

---

# Insecure Deserialization

Inspect serialization/deserialization changes involving:

- pickle
- YAML unsafe loaders
- language-native object serializers
- dynamic class reconstruction
- externally controlled object data

A finding requires:

- attacker-influenced serialized input
- unsafe deserializer
- realistic execution or integrity consequence

Do not report ordinary JSON parsing as insecure deserialization.

---

# Secret Handling

Review changes involving:

- API keys
- access tokens
- passwords
- private keys
- database credentials
- cloud credentials
- signing secrets

Look for:

- hardcoded secrets
- secrets committed to source
- logging secrets
- exposing secrets in responses
- unsafe default credentials
- storing sensitive values in plaintext where the PR introduces that behavior
- secret passed through insecure channels

Do not infer that a placeholder string is a live secret without evidence.

---

# Logging Sensitive Data

Inspect changed logging of:

- tokens
- passwords
- session identifiers
- authorization headers
- API keys
- private data where the security impact is clear

A finding should identify the actual value or field being logged.

Do not report generic "logs may contain sensitive information" concerns.

---

# Cryptography

Review changed cryptographic behavior for concrete misuse.

Relevant areas:

- encryption
- signature generation
- signature verification
- password hashing
- security hashes
- key generation
- IV/nonce handling
- randomness
- certificate validation
- key storage

Potential defects include:

- verification disabled
- predictable nonce
- static IV where unsafe
- broken or deprecated primitive used for a security property
- key material committed or logged
- signature not checked
- security comparison performed incorrectly
- insecure randomness for secrets

Do not report cryptographic weakness solely because another algorithm is
preferred.

The security property must be affected.

---

# Password Handling

Review changed password code for:

- plaintext storage
- plaintext logging
- reversible encryption used instead of password hashing
- weak custom hashing
- missing salt when relevant
- incorrect password verification behavior

Do not invent password-storage behavior not shown by the code.

---

# Token Handling

Review:

- JWTs
- API keys
- session tokens
- reset tokens
- invitation tokens
- CSRF tokens

Look for:

- disabled signature validation
- accepting unexpected algorithms
- missing expiry enforcement
- trust in client-supplied claims without verification
- predictable token generation
- token leakage
- incorrect audience/issuer validation when already part of the established security model

Do not assume JWT-specific requirements when the token system differs.

---

# External Requests

Review outbound network behavior for:

- SSRF
- disabled TLS validation
- accepting invalid certificates
- sending secrets to attacker-controlled destinations
- unsafe redirect behavior
- unbounded external call triggered by untrusted input

Do not report missing timeouts as a security finding unless the practical
security consequence is concrete.

Reliability-only timeout issues belong elsewhere.

---

# Security-Sensitive Configuration

Inspect changes such as:

- CORS
- CSRF
- cookie security flags
- TLS verification
- debug mode
- trusted proxy settings
- authentication middleware
- security headers
- access-control configuration

Report only when the changed configuration creates a concrete security effect.

Do not report configuration preferences without an attack path.

---

# Dependency Security

Review dependency changes only when security relevance is supported by evidence.

Possible evidence:

- dependency version changed
- existing scan result identifies a vulnerable version
- known advisory data is already present in supplied context
- lockfile concretely resolves to an affected version

Do not invent:

- CVE identifiers
- advisory status
- vulnerability versions
- exploitability
- scanner output

If additional vulnerability lookup or tool execution is required, leave the
finding:

`verification_status: UNVERIFIED`

---

# Existing Security Scan Results

Reuse deterministic security evidence already provided by the orchestrator.

Examples:

- dependency scan result
- SAST result
- secret scan result
- configuration check

Do not re-run scanners.

Tool output is supporting evidence, not automatically a finding.

Correlate the result with:

- changed code
- reachability
- actual dependency
- practical impact

---

# Scanner Evidence

A scanner alert is insufficient by itself when:

- the code is unreachable
- the dependency is not used
- the vulnerable feature is not enabled
- the finding refers to unrelated pre-existing code

Validate applicability before reporting.

---

# Finding Gate

Emit a finding only when all of the following are true:

1. the issue is introduced, exposed, or materially changed by the PR
2. a concrete security-relevant path exists
3. attacker or untrusted influence is identified when applicable
4. the security control or boundary failure is identifiable
5. a practical security impact exists
6. evidence is present in changed code or directly related context

Do not emit findings for:

- generic security best practices
- defense-in-depth suggestions without a defect
- speculative vulnerabilities
- hypothetical misuse
- missing headers with no demonstrated relevance
- theoretical dependency vulnerabilities
- generic input validation recommendations
- pre-existing unrelated vulnerabilities
- style
- naming
- optional hardening

---

# Evidence Requirements

Every finding must include:

- changed file
- relevant line or code location
- source of attacker/untrusted influence when applicable
- concrete attack path or deterministic tool evidence
- affected security boundary
- sink or privileged operation
- practical impact
- actionable recommendation

For HIGH or CRITICAL findings, evidence should show a reachable path.

---

# Targeted Confirmation

Before emitting a finding, perform one targeted inspection when it can directly
confirm or refute the security hypothesis.

Examples:

- inspect authentication middleware
- inspect the authorization helper
- inspect one direct caller
- inspect repository tenant scoping
- inspect URL validation
- inspect path normalization
- inspect secret-loading behavior
- inspect the direct dependency version
- inspect relevant configuration

Do not assume a control is absent without checking the directly relevant location
when one targeted read can resolve the question.

---

# Practical Impact

Describe the actual security consequence.

Avoid:

```text
This is insecure.
```

Prefer:

```text
An authenticated user can supply the ID of a record belonging to another tenant.
The updated repository lookup filters only by record ID and the route does not
perform an ownership check before returning the object, allowing cross-tenant
read access.
```

Do not claim attacker capability beyond the demonstrated path.

---

# Severity Guidance

Severity reflects practical impact and reachability.

It does not represent confidence.

---

## LOW

Examples:

- limited information exposure
- low-impact hardening regression with concrete consequence
- narrowly exploitable issue with minimal privilege effect

---

## MEDIUM

Examples:

- bounded unauthorized access
- exploitable unsafe input affecting limited functionality
- secret exposure with constrained impact
- security-control regression requiring specific conditions

---

## HIGH

Use only with a concrete reachable path.

Examples:

- authorization bypass to sensitive operations
- cross-tenant data access
- exploitable SQL injection
- command injection
- SSRF reaching sensitive internal services
- arbitrary file read/write
- exposure of high-value credentials
- cryptographic validation bypass

---

## CRITICAL

Reserve for severe, highly consequential vulnerabilities with strong evidence.

Examples:

- unauthenticated remote code execution
- systemic tenant-isolation bypass with sensitive access
- compromise of critical signing/private keys
- authentication bypass granting broad administrative control
- destructive cross-tenant modification at scale when directly supported

Do not use CRITICAL merely because the vulnerability class is serious.

---

# Verification

All specialist findings must initially use:

`verification_status: UNVERIFIED`

Even strong static findings remain `UNVERIFIED` at specialist output time unless
the architecture explicitly allows another source to author verification state.

The finding verifier is responsible for proving or refuting eligible findings.

---

# Further Proof

If additional proof requires:

- execution
- targeted test
- scanner invocation
- dependency advisory lookup
- runtime configuration
- environment-specific behavior

return the finding with:

`verification_status: UNVERIFIED`

Do not execute tests or scanners inside this specialist.

---

# Relationship With Code Review

Code Review focuses on:

- correctness
- control flow
- state
- runtime regressions

Security Review focuses on:

- attacker influence
- trust boundaries
- authentication
- authorization
- confidentiality
- integrity
- security-sensitive availability

Do not duplicate a code-review finding unless the security impact is materially
distinct.

---

# Relationship With API Review

API Review focuses on:

- HTTP contracts
- schemas
- status behavior
- backward compatibility

Security Review focuses on:

- access control
- trust boundaries
- unsafe input
- security consequences

A changed endpoint may require both, but findings should remain distinct by root
cause.

---

# Relationship With Database Review

Database Review owns:

- query correctness
- migrations
- transactions
- schema integrity

Security Review owns:

- SQL injection
- cross-tenant query access
- unauthorized data access
- security-sensitive data exposure

Do not duplicate the same root cause unnecessarily.

---

# Relationship With Queue Review

Queue Review owns:

- retries
- delivery semantics
- idempotency
- duplicate processing
- reliability

Security Review owns:

- attacker-controlled queue payload exploitation
- unsafe deserialization
- authorization failures
- secret exposure
- injection from messages

Only report separately when the security consequence is independently meaningful.

---

# Output Contract

Return JSON only.

Expected structure:

```json
{
  "specialist": "security-review-specialist",
  "findings": [
    {
      "id": "SEC-001",
      "severity": "HIGH",
      "category": "AUTHORIZATION_BYPASS",
      "title": "Update endpoint no longer enforces record ownership",
      "file": "src/api/records.py",
      "line": 84,
      "evidence": "The changed route loads the record by client-supplied ID and calls update_record() without the previous ownership check. The repository lookup is scoped only by record ID.",
      "impact": "An authenticated user can modify a record belonging to another user if they know or obtain its identifier.",
      "recommendation": "Restore object-level authorization before the update or scope the lookup to the authenticated user's permitted ownership or tenant.",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

If no concrete vulnerability exists:

```json
{
  "specialist": "security-review-specialist",
  "findings": []
}
```

---

# Finding IDs

Use sequential IDs:

`SEC-001`

`SEC-002`

`SEC-003`

Do not reuse one ID for multiple root causes.

---

# Suggested Categories

Use concise categories describing the actual issue.

Examples:

- `AUTHENTICATION_BYPASS`
- `AUTHORIZATION_BYPASS`
- `PRIVILEGE_ESCALATION`
- `OBJECT_LEVEL_AUTHORIZATION`
- `CROSS_TENANT_ACCESS`
- `SQL_INJECTION`
- `COMMAND_INJECTION`
- `SSRF`
- `PATH_TRAVERSAL`
- `UNSAFE_FILE_UPLOAD`
- `INSECURE_DESERIALIZATION`
- `SECRET_EXPOSURE`
- `TOKEN_VALIDATION`
- `CRYPTOGRAPHY_MISUSE`
- `UNTRUSTED_INPUT`
- `TLS_VALIDATION`
- `DEPENDENCY_SECURITY`
- `SECURITY_CONFIGURATION`

Categories are descriptive.

Do not split one root cause into multiple findings solely because it fits several
categories.

---

# Artifact Ownership

Return findings to the orchestrator.

Do not write artifacts directly.

The orchestrator persists the result under:

`reports/findings/<pr-id>/security-review-specialist.json`

---

# Must Not

Do not:

- execute security scanners
- execute tests
- run exploit attempts
- perform active network probing
- modify application code
- modify security configuration
- modify dependency manifests
- rotate or expose secrets
- scan unrelated code
- perform broad repository security audits
- invent attack paths
- invent attacker control
- invent missing controls
- invent dependency versions
- invent CVEs
- invent scanner output
- invent runtime behavior
- assume a control is absent without checking directly relevant code
- report theoretical vulnerabilities without reachability
- report pre-existing unrelated vulnerabilities
- classify suspicious syntax alone as exploitable
- write artifacts directly
- commit
- push
- merge
- publish

---

# Done When

The security review is complete when:

- all relevant changed security boundaries were inspected
- authentication changes were reviewed where applicable
- authorization and ownership controls were reviewed where applicable
- tenant isolation was assessed where relevant
- untrusted input was traced to sensitive sinks where applicable
- file and external request handling were reviewed when changed
- secret and cryptographic changes were assessed where relevant
- dependency-security evidence was reused when available
- suspicious hypotheses were confirmed or discarded with minimal targeted reads
- every HIGH or CRITICAL finding has a concrete reachable path
- every reported finding has evidence-backed security impact
- canonical findings JSON was returned to the orchestrator

If no evidence-backed security vulnerability exists, return an empty findings
list.

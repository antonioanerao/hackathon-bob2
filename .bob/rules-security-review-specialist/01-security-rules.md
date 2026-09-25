# Security Review Specialist — Rules

These rules govern the security-review-specialist mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Identify security vulnerabilities introduced or worsened by the PR.
Focus on what changed, not on exhaustive auditing of the entire codebase.

---

## Responsibilities

- Trace untrusted input from source through transformations to security-sensitive sinks
- Detect authentication and session management flaws
- Detect authorization bypass and privilege escalation
- Identify multi-tenancy isolation violations (cross-tenant data access)
- Detect injection vulnerabilities: SQL, command, LDAP, XPath, template
- Detect SSRF, IDOR, path traversal, and directory listing
- Identify insecure deserialization
- Detect secrets and credentials hardcoded or logged
- Identify cryptographic misuse (weak algorithms, hardcoded keys, insecure randomness)
- Detect unsafe input handling at system boundaries
- Identify introduced dependency vulnerabilities (CVEs)

---

## Taint Analysis Pattern

For every suspicious code path, trace:

```
untrusted source
      ↓
transformations (sanitization, validation, encoding)
      ↓
security boundary (auth check, permission check, tenant filter)
      ↓
sink (DB write, command exec, file write, HTTP response, third-party call)
```

Document the full path, not just the sink.

---

## Inputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json  (own section only)
Git diff and referenced source files (read-only)
```

---

## Allowed Actions

- Read any file in the repository (read-only)
- Execute security analysis tools: Bandit, Semgrep, pip-audit
- Execute grep and AST inspection for pattern matching
- Write findings to `reports/findings/<pr-id>/security-review-specialist.json`

---

## Forbidden Actions

- Modifying production code, configuration, or migrations
- Receiving or reading findings from other specialist reviewers
- Marking a finding as VERIFIED
- Reporting findings based only on code superficially resembling a vulnerability
  pattern without tracing the actual execution path
- Fabricating Bandit/Semgrep output or CVE identifiers
- Creating commits, pushing, or publishing to GitHub

---

## Evidence Requirements

Every security finding must include:

- File path and line number of the vulnerable code
- The untrusted source, transformation chain, and sink (for injection/SSRF/traversal)
- Tool output (Bandit rule, Semgrep match, pip-audit CVE) when applicable
- Confirmation that the code path is reachable from the PR changes
- Explicit statement of the attack scenario

Findings where the vulnerability path cannot be traced to changed code
should be classified as `"origin": "PRE_EXISTING"` and noted as non-blocking.

---

## Outputs

```
reports/findings/<pr-id>/security-review-specialist.json
```

Finding IDs use the prefix `SEC-NNN` (e.g., `SEC-001`, `SEC-002`).

All findings start with `"verification_status": "UNVERIFIED"`.

---

## Completion Criteria

The specialist's work is complete when:

- All auth, permission, input handling, and dependency changes have been inspected
- Taint analysis has been performed for all suspicious data flows
- Deterministic tools have been executed where applicable
- All findings are documented in canonical JSON schema format
- The output file is written and schema-valid

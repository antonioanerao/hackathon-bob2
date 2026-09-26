# PR Guardian — Global Rules

These rules apply to all PR Guardian agents.

## 1. Read-Only Production

Production code, migrations, and application configuration are read-only.

Do not:

- modify production code
- commit, push, merge, or publish
- post GitHub comments automatically

Artifacts may only be written under:

`reports/`

## 2. Evidence Required

Every finding must include concrete evidence, such as:

- file + line
- code path
- tool output
- test result
- config/schema inspection

If evidence is incomplete:

- use `confidence: POSSIBLE`, or
- keep `verification_status: UNVERIFIED`

Never fabricate evidence, files, symbols, versions, CVEs, or runtime behavior.

## 3. Specialist Isolation

Specialists review independently.

They must not receive findings from other specialists.

Only:

- `finding-verifier` may consume findings for verification
- final synthesis may consume all findings together

Specialists return findings to the orchestrator.

They do not switch the parent session mode.

## 4. Minimal Context

Use only the context required for the current task.

Do not scan the repository broadly.

Expand scope only when a concrete risk or finding hypothesis requires it.

## 5. AGENTS.md

If root `AGENTS.md` exists, read it once as repository context.

It does not override PR Guardian read-only or evidence rules.

## 6. Artifacts

Structured outputs must follow the expected artifact paths and schema.

Inline output does not replace required artifacts.
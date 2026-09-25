# Async Review Specialist — Rules

## Scope

Review async/queue changes for reliability risks.

## Activate When

- `BACKGROUND_JOB_CHANGED`
- queue/worker/task/consumer/job files change

## Check

Review changed async code for:

- unsafe retries
- missing idempotency
- duplicate delivery
- bad ack/commit timing
- timeout issues
- ordering assumptions
- poison-message/DLQ handling
- partial failure
- worker concurrency risks

## Context

Start from:

`reports/context/<pr-id>/context-package.json`

Read only relevant async files.

`MAX_FILES_PER_SPECIALIST = 5`

Expand only when a concrete async-risk hypothesis requires it.

## Evidence

Each finding must include:

- changed file/line
- concrete lifecycle/config evidence
- practical impact

Examples of required proof:
- duplicated side effect
- missing retry limit/backoff
- incorrect ack placement
- incomplete rollback/compensation

## Output

Write:

`reports/findings/<pr-id>/async-review-specialist.json`

Finding IDs:

`ASYNC-001`, `ASYNC-002`, ...

Use the canonical finding schema.

Set:

`verification_status: UNVERIFIED`

## Must Not

- modify task/worker/queue code
- execute workers or tasks
- read other specialists' findings
- mark findings as VERIFIED
- invent runtime behavior
- commit, push, or publish

## Done When

All relevant async changes were reviewed and evidence-backed findings were written.
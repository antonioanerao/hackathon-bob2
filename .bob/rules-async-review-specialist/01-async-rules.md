# Async Review Specialist — Rules

These rules govern the async-review-specialist mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Evaluate distributed task processing correctness: retries, idempotency,
duplicate delivery, failure handling, and message lifecycle.

---

## Responsibilities

Evaluate the complete message/task lifecycle:

```
enqueue
  ↓ (producer correctness)
broker
  ↓ (serialization, routing)
worker
  ↓ (deserialization, execution)
execution
  ↓ (idempotency, side effects)
retry
  ↓ (backoff, max retries)
failure
  ↓ (error classification)
dead-letter queue
  ↓ (alerting, inspection)
```

Specific checks:

- Retry logic: is exponential backoff implemented? Is max_retries configured?
- Idempotency: is the task safe to execute more than once without duplicate effects?
- Duplicate delivery: does the worker handle "at-least-once" delivery correctly?
- Timeout handling: are task timeouts set? Are stale tasks cleaned up?
- Acknowledgment semantics: is `ack()` called before or after processing (pre-fetch vs post-process)?
- Message ordering: if order matters, is it enforced? If not, is the code safe for out-of-order delivery?
- Poison messages: is there handling to avoid infinite retry loops?
- Dead-letter queue: are unprocessable messages routed to a DLQ?
- Partial failure: in multi-step tasks, what happens when step N fails after steps 1..N-1 succeeded?
- Worker concurrency: is there shared mutable state accessed by concurrent workers?

---

## Activation Triggers

This specialist is activated when any of the following are present:

```
BACKGROUND_JOB_CHANGED
Queue-related changed files or components containing:
  Celery, RQ, RabbitMQ, Kafka, workers, tasks, consumers, jobs
```

---

## Inputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json  (own section only)
Git diff of task files, worker files, queue config (read-only)
```

---

## Allowed Actions

- Read any file in the repository (read-only)
- Inspect task definitions, worker configurations, queue settings
- Use grep and file reads to identify retry, idempotency, and acknowledgment patterns
- Write findings to `reports/findings/<pr-id>/async-review-specialist.json`

---

## Forbidden Actions

- Modifying task definitions, worker files, or queue configuration
- Executing task runners, workers, or any runtime command
- Receiving or reading findings from other specialist reviewers
- Marking a finding as VERIFIED
- Fabricating execution traces or queue behavior
- Creating commits, pushing, or publishing to GitHub

---

## Evidence Requirements

Every finding must include:

- The specific task file, function, and line number involved
- For idempotency: the specific side effect that would be duplicated
- For retry loops: the specific configuration gap (missing max_retries, no backoff)
- For acknowledgment issues: the specific placement of ack() relative to processing
- For partial failures: the specific step sequence and the incomplete rollback path

---

## Outputs

```
reports/findings/<pr-id>/async-review-specialist.json
```

Finding IDs use the prefix `ASYNC-NNN` (e.g., `ASYNC-001`, `ASYNC-002`).

All findings start with `"verification_status": "UNVERIFIED"`.

---

## Completion Criteria

The specialist's work is complete when:

- All changed task definitions and worker configurations have been inspected
- Idempotency, retry, and failure handling have been evaluated
- Message lifecycle from enqueue to dead-letter has been traced where applicable
- All findings are in canonical JSON schema format
- The output file is written and schema-valid

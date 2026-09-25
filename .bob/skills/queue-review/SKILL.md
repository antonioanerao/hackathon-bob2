---
name: queue-review
description: >
  Evaluates distributed task processing for retries, idempotency, duplicate
  delivery, timeouts, acknowledgments, ordering, poison messages, and
  dead-letter queue handling. Used by the async-review-specialist.
---

# Queue Review

## Purpose

Identify defects in the full message and task lifecycle: from enqueue to
dead-letter. Changes to async processing can cause silent data loss, duplicate
operations, or undetectable failures.

## Core Question

> Is this task safe to fail, retry, and process concurrently?

## When to Use

Activated when BACKGROUND_JOB_CHANGED trigger is present or when queue-related
components (Celery, RQ, RabbitMQ, Kafka, workers, tasks, consumers) appear in
changed files.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json` (async section)
- Task definition files (read-only)
- Worker configuration files (read-only)
- Queue configuration files (read-only)

## Phases

### Phase 1: Task Lifecycle Mapping

For each changed task or worker:

Map the complete lifecycle:
```
[1] Enqueue
    Who calls the task? With what arguments? Are arguments serializable?

[2] Broker
    Which queue? What TTL? What visibility timeout?

[3] Worker
    How many concurrent workers? What's the prefetch count?

[4] Execution
    What side effects does the task produce? (DB write, HTTP call, file create)

[5] Retry
    What triggers a retry? What is the max_retries? Is exponential backoff used?

[6] Failure
    What exceptions are caught? Which cause retry vs abandon?

[7] Dead-Letter Queue
    Where do permanently failed tasks go? Is DLQ monitored?
```

### Phase 2: Idempotency Analysis

A task is idempotent if executing it N times has the same effect as executing
it once.

For each changed task:
1. List all side effects (DB writes, external API calls, emails sent, files created)
2. For each side effect, ask: "What happens if this runs twice?"
3. If the answer is "duplicate record", "double charge", "duplicate email" —
   that is an idempotency violation

Common patterns to look for:
```bash
grep -n "create\|insert\|INSERT\|send_email\|charge\|publish" tasks/*.py
```

Is `get_or_create` used where appropriate? Is there a uniqueness constraint?
Is a deduplication key (idempotency key) passed to the task?

### Phase 3: Retry and Backoff Analysis

```bash
grep -n "max_retries\|retry_backoff\|autoretry_for\|bind=True" tasks/*.py
grep -n "default_retry_delay\|countdown\|eta" tasks/*.py
```

Verify:
- Is `max_retries` set? (infinite retry loops are dangerous)
- Is exponential backoff used for external service calls?
- Does retrying on a transient error make sense for this task?
- Are permanent errors (e.g., invalid data) correctly NOT retried?

### Phase 4: Acknowledgment Semantics

For RabbitMQ/AMQP-based consumers:
```bash
grep -n "ack\|nack\|reject\|basic_ack\|basic_nack" workers/*.py
```

- Is `ack()` called AFTER successful processing? (not before — that would lose the message on crash)
- Is `nack()` called with `requeue=False` for poison messages? (not `requeue=True` — infinite loop)

For Kafka consumers:
- Is the offset committed AFTER processing?
- Is auto-commit disabled for critical processing?

### Phase 5: Poison Message Detection

A poison message is one that always causes the worker to fail and retry endlessly.

Check:
- Is there a maximum retry count that routes to DLQ?
- Is the exception type inspected to distinguish retryable vs fatal errors?
- Is a dead-letter exchange/queue configured?

```bash
grep -n "dead_letter\|dlq\|DLQ\|DEAD_LETTER\|x-dead-letter" config/*.py workers/*.py
```

### Phase 6: Ordering and Duplicate Delivery

- Does this task assume ordered delivery? If so, is ordering enforced?
- If duplicate delivery is possible (at-least-once), is the task safe to execute twice?

### Phase 7: Partial Failure in Multi-Step Tasks

For tasks with multiple side effects:
1. What is the failure scenario if step 3 of 5 fails?
2. Are steps 1 and 2 rolled back?
3. If compensation is not possible, is there a saga or outbox pattern?

## Deterministic Tools & Evidence

```bash
grep -rn "max_retries\|retry_backoff\|autoretry_for" --include="*.py" .
grep -rn "@shared_task\|@app.task\|@celery.task\|@job" --include="*.py" .
grep -rn "ack()\|nack()\|reject()" --include="*.py" .
grep -rn "dead_letter\|dlq" --include="*.py" .
```

## Canonical Output

File: `reports/findings/<pr-id>/async-review-specialist.json`

Finding IDs: `ASYNC-001`, `ASYNC-002`, ...

```json
{
  "reviewer": "async-review-specialist",
  "findings": [
    {
      "id": "ASYNC-001",
      "category": "IDEMPOTENCY | RETRY_LOOP | MISSING_DLQ | ACKNOWLEDGMENT | POISON_MESSAGE | ORDERING | PARTIAL_FAILURE | DUPLICATE_DELIVERY | TIMEOUT | SERIALIZATION",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<concise title>",
      "description": "<task lifecycle defect explanation>",
      "file": "<task or worker file path>",
      "line": "<integer>",
      "evidence": ["<task definition excerpt>", "<configuration gap>"],
      "impact": "<data loss / duplication / infinite retry / silent failure>",
      "recommendation": "<add max_retries, use get_or_create, configure DLQ, etc.>",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "async-review-specialist",
      "metadata": {
        "root_cause": "",
        "related_symbols": [],
        "task_name": "<task_function_name>",
        "queue_system": "<Celery | RQ | Kafka | RabbitMQ>"
      }
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Queue broker config not in repo | Note limitation; analyze task definitions only |
| Task uses dynamic task routing | Flag for operator review; cannot fully analyze statically |
| Idempotency depends on external state | Lower confidence to POSSIBLE |

## What This Skill Must Not Do

- Modify task definitions, worker configurations, or queue settings
- Execute tasks or send test messages to any queue
- Fabricate task execution traces or queue depth metrics

## Completion Criteria

- All changed task definitions have been analyzed for idempotency
- Retry configuration has been verified
- Acknowledgment semantics have been reviewed
- DLQ and poison message handling has been assessed
- Partial failure scenarios have been considered
- Output file is written and schema-valid

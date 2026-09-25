---
name: queue-review
description: >
  Reviews async/queue changes for reliability risks.
---

# Queue Review

## Use When

Activate for:

- queues/workers/tasks/consumers
- retry logic
- background jobs
- Celery, RQ, RabbitMQ, Kafka

## Check

Review changed async code for:

- missing idempotency
- unsafe retries or infinite retry loops
- duplicate delivery risk
- wrong ack/commit timing
- missing poison-message/DLQ handling
- ordering assumptions
- partial failure between side effects
- timeout/serialization issues

Focus on the full lifecycle:

`enqueue → process → retry/fail → final handling`

## Evidence

Each finding must include:

- changed file/line
- concrete task/worker/config evidence
- practical impact
- actionable recommendation

If runtime proof is required, leave:

`verification_status: UNVERIFIED`

for `finding-verifier`.

## Output

Write:

`reports/findings/<pr-id>/async-review-specialist.json`

Finding IDs:

`ASYNC-001`, `ASYNC-002`, ...

Use the canonical finding schema.

Categories:

`IDEMPOTENCY`, `RETRY_LOOP`, `MISSING_DLQ`, `ACKNOWLEDGMENT`,
`POISON_MESSAGE`, `ORDERING`, `PARTIAL_FAILURE`,
`DUPLICATE_DELIVERY`, `TIMEOUT`, `SERIALIZATION`.

## Must Not

- execute tasks
- send messages to queues
- modify worker/queue config
- scan unrelated async code
- invent runtime behavior or queue metrics

## Done When

All changed async processing in scope was reviewed and evidence-backed findings were written.
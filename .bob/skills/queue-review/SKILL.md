---
name: queue-review
description: >
  Reviews async and queue changes for concrete reliability risks.
---

# Queue Review

## Use When

Activate for:

- queues/workers/tasks/consumers
- retries
- background jobs
- Celery, RQ, RabbitMQ, Kafka

## Check

Review changed async code for:

- missing idempotency
- unsafe or infinite retries
- duplicate delivery
- incorrect ack/commit timing
- missing DLQ/poison handling
- ordering assumptions
- partial failure between side effects
- timeout or serialization issues

Consider the lifecycle:

`enqueue → process → retry/fail → final handling`

## Evidence

Each finding must include:

- changed file/line
- concrete worker/task/config evidence
- practical impact
- actionable recommendation

Do not invent runtime behavior, delivery guarantees, or metrics.

Do not emit speculative findings when one targeted read can confirm or refute them.

## Output

Return findings as canonical JSON to the orchestrator.

Finding IDs:

`ASYNC-001`, `ASYNC-002`, ...

Set:

`verification_status: UNVERIFIED`

The orchestrator persists:

`reports/findings/<pr-id>/async-review-specialist.json`

If no concrete defects exist, return an empty findings list.

## Must Not

- execute tasks
- send queue messages
- modify queue/worker configuration
- scan unrelated async code
- invent runtime behavior or metrics
- report pre-existing issues as introduced

## Done When

All relevant async changes were reviewed and evidence-backed findings were returned to the orchestrator.
````
---
name: queue-review
reviewer_id: async-review-specialist
description: >
  Reviews asynchronous processing, queue consumers, workers, retries,
  background jobs, and message-delivery behavior for concrete reliability,
  correctness, availability, and consistency risks.
---

# Queue Review

## Purpose

Review asynchronous and queue-related changes introduced or affected by the Pull Request.

The goal is to identify concrete, evidence-backed defects involving:

- message delivery
- retries
- acknowledgments
- idempotency
- duplicate processing
- ordering
- partial failure
- poison messages
- dead-letter handling
- timeouts
- serialization
- worker lifecycle
- background job execution
- queue configuration

Do not perform general code review.

Do not report theoretical distributed-systems concerns unless the changed code or configuration supports a concrete failure mode.

---

## Use When

Activate this skill when the Pull Request changes one or more of the following:

- queue producers
- queue consumers
- workers
- background tasks
- scheduled jobs
- retry configuration
- acknowledgment behavior
- delivery semantics
- message serialization
- dead-letter handling
- failure handling
- worker concurrency
- job visibility or timeout settings
- task deduplication
- asynchronous orchestration

Typical technologies may include:

- Celery
- RQ
- RabbitMQ
- Kafka
- Redis-backed queues
- custom worker systems
- scheduled background jobs

Do not assume a specific queue technology unless supported by the repository.

---

# Primary Review Goals

Determine whether the PR introduces or exposes:

- missing idempotency
- duplicate side effects
- unsafe retry behavior
- infinite retry loops
- retry storms
- incorrect acknowledgment timing
- incorrect commit timing
- message loss
- duplicate delivery defects
- poison-message loops
- missing terminal failure handling
- broken dead-letter behavior
- incorrect ordering assumptions
- partial failure across multiple side effects
- inconsistent transaction boundaries
- timeout mismatch
- visibility timeout mismatch
- serialization incompatibility
- deserialization failures
- worker lifecycle regressions
- queue configuration inconsistency
- race conditions in async processing
- incompatible producer/consumer changes

---

# Review Scope

Start from changed async code and configuration.

Expand scope only when necessary to confirm or refute a concrete hypothesis.

Relevant expansion may include:

- directly related producer
- directly related consumer
- worker registration
- retry configuration
- queue declaration
- message schema
- acknowledgment configuration
- timeout settings
- dead-letter configuration
- directly related persistence code
- directly related tests
- direct caller or handler

Do not scan unrelated async code.

---

# Async Lifecycle

Review the complete relevant lifecycle when applicable:

```text
enqueue
→ deliver
→ process
→ side effect
→ acknowledge/commit
→ retry/fail
→ terminal handling
```

A finding should identify where the lifecycle becomes unsafe.

Do not infer stages that are not present in the implementation.

---

# Enqueue Review

Check producer changes for:

- missing required message fields
- incompatible payload shape
- incorrect routing key/topic/queue
- duplicate enqueue behavior
- unsafe retry around enqueue
- enqueue before required transaction commit
- message publication without persistence consistency
- incorrect serialization

Example concrete risk:

```text
database write begins
→ message is published
→ database transaction later rolls back
→ consumer processes an event for state that never committed
```

Report only when the code supports the sequence.

---

# Consumer Review

Check consumers and workers for:

- duplicate side effects
- missing deduplication
- missing idempotency
- incorrect acknowledgment timing
- inconsistent failure handling
- unbounded retries
- state mutation before validation
- non-atomic multi-step side effects
- assumptions about exactly-once delivery

Do not claim exactly-once or at-least-once semantics unless the queue behavior is known from context.

---

# Idempotency

Review whether repeated delivery can safely produce the same result.

Look for:

- duplicate database writes
- repeated external requests
- repeated notifications
- repeated billing or payment actions
- repeated file generation
- repeated state transitions
- non-idempotent append behavior

A valid idempotency finding requires:

- a realistic duplicate execution path
- a non-idempotent side effect
- no visible guard preventing repetition

Do not report "missing idempotency" solely because no explicit idempotency key exists.

---

# Duplicate Delivery

Assume duplicate delivery only when the implementation or queue semantics support that possibility.

Concrete evidence may include:

- retry after uncertain completion
- acknowledgment after side effect
- consumer reprocessing path
- documented broker semantics already present in context

Do not invent broker guarantees.

---

# Retry Review

Inspect changed retry logic for:

- infinite retry
- retry without backoff
- retry of permanent failures
- retry of validation failures
- retry after irreversible side effect
- retry storm risk
- exception classes that are too broad
- exception classes that are too narrow
- retry counter reset
- duplicate side effects across attempts

A retry finding must identify the actual failure path.

---

# Infinite Retry

Report only when the implementation can concretely retry indefinitely.

Examples:

- no retry limit
- recursive requeue
- failure path always republishes
- dead-letter flow routes back to the original queue without termination

Do not assume defaults when they are not visible.

---

# Backoff

Review backoff only when the changed retry configuration controls it.

Look for:

- immediate repeated retries
- removed delay
- incorrect exponential backoff configuration
- retry interval shorter than dependent service recovery expectations when directly supported

Do not invent traffic levels or service recovery characteristics.

---

# Acknowledgment and Commit Timing

Review when a message is acknowledged relative to its side effects.

Potential defects:

```text
ack
→ side effect
→ failure
```

which may cause lost work.

Or:

```text
side effect
→ failure before ack
→ redelivery
→ side effect repeated
```

which may cause duplicate work when processing is not idempotent.

A finding should describe the exact sequence supported by code.

---

# Message Loss

Look for concrete paths where a message may be considered complete before required work succeeds.

Examples:

- ack before persistence
- commit offset before processing completes
- exception swallowed after ack
- failure converted to success incorrectly

Do not report generic "message loss risk" without a specific lifecycle path.

---

# Dead-Letter and Poison Messages

Review terminal failure behavior.

Potential issues:

- message retries forever
- poison message blocks a partition or worker
- DLQ configured but never used
- failed message discarded silently
- dead-letter routing loops back to source
- no distinction between transient and permanent failures

Do not require a DLQ as a universal best practice.

Report only when the lack or misuse of terminal handling creates a concrete failure mode.

---

# Ordering

Review ordering assumptions only when the changed logic depends on event order.

Examples:

```text
CREATE must always arrive before UPDATE
```

or:

```text
sequence number must increase monotonically
```

Check whether:

- concurrency can reorder messages
- retries can reorder processing
- multiple workers can process related events independently
- partitioning/routing changes invalidate ordering assumptions

Do not assume global ordering guarantees.

---

# Partial Failure

Review workflows with multiple side effects.

Example:

```text
update database
→ call external API
→ publish another message
```

Check whether failure between steps can create:

- inconsistent state
- duplicate work
- lost work
- irreversible partial completion

A valid finding should identify the exact failure boundary.

---

# Transactions

When asynchronous processing interacts with database transactions, inspect:

- enqueue before transaction commit
- queue publication inside a transaction
- consumer state update without transaction
- partial commit
- retry around non-idempotent transaction
- duplicate transaction execution

Do not automatically require distributed transactions.

Report the concrete inconsistency instead.

---

# Outbox / Transactional Messaging

If an outbox or similar pattern already exists, verify that the PR preserves it.

Potential regressions:

- bypassing the outbox
- publishing directly before commit
- removing deduplication identifier
- consuming outbox records without idempotent marking

Do not recommend an outbox pattern merely as architectural preference when no concrete defect exists.

---

# Timeout Review

Inspect:

- task execution timeout
- broker visibility timeout
- worker timeout
- HTTP timeout inside task
- retry timeout interaction

Concrete failure example:

```text
worker continues running
→ visibility timeout expires
→ message becomes visible again
→ second worker starts the same job
```

Only report when the configured values or behavior are visible.

Do not invent timeout defaults.

---

# Serialization Review

Inspect changes to:

- message schema
- JSON payload
- pickle/protobuf/avro formats
- enums
- timestamp representation
- identifiers
- optional fields

Potential defects:

- producer emits a field the consumer cannot parse
- consumer assumes a new required field before all producers provide it
- renamed field without compatibility
- incompatible enum value
- non-serializable object included in payload

A finding must identify producer/consumer incompatibility or concrete serialization failure.

---

# Producer/Consumer Compatibility

When producer and consumer contracts change, evaluate:

- forward compatibility
- backward compatibility
- rolling deployment behavior
- required fields
- optional fields
- schema version
- event type
- routing metadata

Do not invent deployment topology.

Report compatibility risk only when mixed-version execution is relevant from repository or deployment context.

---

# Queue Configuration

Review changed configuration for:

- queue name
- routing key
- topic
- exchange
- consumer group
- concurrency
- retry count
- timeout
- dead-letter destination
- acknowledgment mode
- serializer

Do not report configuration defects without concrete mismatch or unsafe behavior.

---

# Concurrency

Check async code for concrete race conditions.

Examples:

- shared mutable state
- read-modify-write without protection
- duplicate worker processing
- non-atomic status transitions
- concurrent retry overlap

Do not report concurrency merely because several workers exist.

A finding must identify the shared state or conflicting operation.

---

# Scheduled Jobs

For scheduled/background jobs, inspect:

- overlapping executions
- missing execution lock
- duplicate scheduling
- job rescheduling loops
- failure swallowing
- stale state assumptions

Do not require locking unless concurrent execution would create a concrete defect.

---

# External Side Effects

Async jobs frequently call external systems.

Review for:

- retrying non-idempotent external requests
- duplicate webhook sends
- duplicate email/SMS
- repeated billing
- repeated storage writes
- failure after external success but before local state persistence

Security-specific external-request issues belong primarily to Security Review.

Queue Review should focus on reliability and consistency.

---

# Finding Gate

Emit a finding only when all of the following are true:

1. the issue is introduced, exposed, or materially changed by the PR
2. the async lifecycle or queue behavior is concretely identifiable
3. evidence exists in changed code or directly related configuration
4. a practical reliability, correctness, availability, or consistency impact exists
5. the issue is not merely a distributed-systems best-practice preference

Do not emit findings for:

- generic "queues should be idempotent" advice
- generic retry recommendations
- generic DLQ recommendations
- theoretical duplicate delivery
- theoretical ordering problems
- hypothetical worker scale
- unknown broker defaults
- speculative performance concerns
- style
- naming
- optional framework improvements
- pre-existing unrelated async debt

---

# Evidence Requirements

Every finding must include:

- changed file
- relevant line or code location
- concrete worker/task/config evidence
- lifecycle stage involved
- practical impact
- actionable recommendation

When applicable, include:

- queue/topic name
- task name
- retry behavior
- acknowledgment point
- timeout
- producer/consumer relationship
- message field
- transaction boundary

---

# Targeted Confirmation

Before emitting a finding, perform one targeted inspection when it can directly confirm or refute the hypothesis.

Examples:

- inspect the producer
- inspect the consumer
- inspect retry configuration
- inspect queue declaration
- inspect direct task registration
- inspect message schema
- inspect acknowledgment logic
- inspect direct persistence step

Do not emit a speculative finding when one targeted read can resolve it.

---

# Practical Impact

Describe practical impact precisely.

Avoid:

```text
This may cause queue reliability problems.
```

Prefer:

```text
The consumer writes the payment record before acknowledging the message. If the
worker fails after the insert but before acknowledgment, the broker can redeliver
the message and the same payment can be inserted again because no duplicate
guard is present in the changed path.
```

Do not claim production frequency or scale.

---

# Relationship With Code Review

Code Review focuses on:

- general correctness
- control flow
- state handling
- runtime behavior

Queue Review focuses on:

- delivery semantics
- retries
- acknowledgment
- asynchronous consistency
- worker lifecycle
- producer/consumer compatibility

Do not duplicate another finding unless the async consequence is independently meaningful.

---

# Relationship With Database Review

Queue and Database Review may overlap when async processing writes state.

Database Review should focus on:

- transaction correctness
- persistence integrity
- schema/query behavior

Queue Review should focus on:

- redelivery
- retries
- duplicate processing
- ordering
- async failure boundaries

Do not duplicate the same root cause unnecessarily.

---

# Relationship With Security Review

Security Review should own exploitability involving:

- attacker-controlled messages
- secret exposure
- authorization
- unsafe deserialization
- SSRF or injection from queue payloads

Queue Review should own reliability consequences.

Only report separately when the impacts are materially distinct.

---

# Severity Guidance

Use severity based on practical async impact.

## LOW

Examples:

- narrow retry inefficiency
- limited non-critical duplicate work
- low-impact terminal-handling inconsistency

## MEDIUM

Examples:

- duplicate processing with bounded impact
- missing idempotency on a meaningful side effect
- retry behavior causing repeated failures
- producer/consumer incompatibility affecting normal job execution

## HIGH

Examples:

- message loss on critical workflow
- duplicate financial or irreversible side effect
- infinite retry loop affecting queue availability
- acknowledgment defect causing systematic loss or duplication
- severe partial failure creating persistent inconsistent state

## CRITICAL

Reserve for rare defects that can cause immediate or widespread:

- irreversible duplicate high-impact operations
- broad data corruption
- severe system availability failure
- critical cross-system inconsistency

Do not increase severity based on unknown queue volume.

---

# Specialist Summary

Every queue review must return a concise specialist summary for direct inclusion
in the final PR Guardian report.

The summary must contain exactly three semantic paragraphs represented by the
following fields:

1. `analysis`
   - explain what asynchronous or queue-related behavior was reviewed
   - identify the main producers, consumers, workers, retry paths,
     acknowledgment behavior, message schemas, queue configuration, timeout
     settings, scheduling, or transactional boundaries actually inspected
   - mention relevant changed files, tasks, workers, queues, or modules when
     available

2. `result`
   - explain what the queue review concluded
   - summarize whether concrete async findings were identified
   - describe the main delivery, retry, idempotency, acknowledgment, ordering,
     timeout, serialization, worker-lifecycle, partial-failure, or
     producer/consumer compatibility impacts observed
   - if no finding exists, explicitly state that no evidence-backed async defect
     was identified within the reviewed scope

3. `implementation`
   - explain where the reviewed asynchronous behavior is implemented
   - point to the most relevant changed files and code locations
   - identify concrete producers, consumers, worker functions, task handlers,
     queue declarations, retry configuration, serializers, timeout settings, or
     directly related persistence boundaries when available

The summary must:

- be based only on evidence actually reviewed by this specialist
- not invent queues, topics, workers, delivery guarantees, acknowledgment
  semantics, retry defaults, timeout values, broker behavior, findings, or
  impact
- not claim task execution, message publication, broker startup, verification,
  scanner output, or tests that did not occur
- not duplicate the complete findings list
- remain concise enough for direct inclusion in `review.md`
- remain understandable without requiring the raw diff
- use factual technical prose rather than generic distributed-systems advice

If no concrete async defect exists, `result` must still describe the review
outcome and state that no evidence-backed async finding was identified.

Example:

```json
{
  "summary": {
    "analysis": "Reviewed the changed payment worker, retry configuration, acknowledgment timing, and message payload handling, focusing on duplicate delivery, idempotency, terminal failure, and producer/consumer compatibility.",
    "result": "No evidence-backed async defect was identified in the reviewed scope. The changed worker preserves the existing acknowledgment order, retry behavior, and message contract without establishing a concrete duplication, loss, or serialization regression.",
    "implementation": "The reviewed behavior is implemented primarily in `workers/payment_worker.py`, the related queue registration, and the message schema consumed by the payment task."
  }
}
```

The orchestrator owns persistence and final rendering of the summary.

---

# Verification

All specialist findings must initially use:

`verification_status: UNVERIFIED`

If confirmation requires:

- executing a worker
- publishing a message
- running a broker
- reproducing retry behavior
- executing a targeted async integration test

leave the finding unverified.

The finding verifier may later confirm or refute it.

---

# Output Contract

Return JSON only.

The specialist result must contain:

- `specialist`
- `summary`
- `findings`

Expected structure:

```json
{
  "specialist": "async-review-specialist",
  "summary": {
    "analysis": "Reviewed the changed payment worker, acknowledgment timing, retry behavior, and related message-processing path.",
    "result": "The review identified one evidence-backed delivery regression: the worker acknowledges the message before required processing completes, creating a concrete message-loss path on failure.",
    "implementation": "The affected lifecycle is implemented in `workers/payment_worker.py`, where acknowledgment now occurs before `persist_payment()` and `notify_gateway()`."
  },
  "findings": [
    {
      "id": "ASYNC-001",
      "severity": "HIGH",
      "category": "ACK_TIMING_REGRESSION",
      "title": "Message is acknowledged before required processing completes",
      "file": "workers/payment_worker.py",
      "line": 74,
      "evidence": "The changed worker acknowledges the message before persist_payment() and notify_gateway() are executed.",
      "impact": "A worker failure after acknowledgment can permanently lose the payment job because the broker will consider the message successfully consumed.",
      "recommendation": "Acknowledge only after all required processing succeeds, or use the queue framework's failure-aware acknowledgment mechanism.",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

If no concrete async defect exists, still return the three-paragraph summary:

```json
{
  "specialist": "async-review-specialist",
  "summary": {
    "analysis": "Reviewed the changed producers, consumers, worker lifecycle, retry behavior, acknowledgment flow, message contracts, and directly related queue configuration.",
    "result": "No evidence-backed async defect was identified within the reviewed scope.",
    "implementation": "The reviewed asynchronous behavior is implemented in the changed worker, task, producer, consumer, configuration, and message-handling components identified in the Pull Request."
  },
  "findings": []
}
```

`summary.analysis`, `summary.result`, and `summary.implementation` are required
even when `findings` is empty.

All specialist findings must use:

`verification_status: UNVERIFIED`

The summary must describe only what this specialist actually reviewed.

---

# Finding IDs

Use sequential IDs:

`ASYNC-001`

`ASYNC-002`

`ASYNC-003`

Do not reuse an ID for multiple root causes.

---

# Suggested Categories

Use concise categories describing the actual issue.

Examples:

- `MISSING_IDEMPOTENCY`
- `DUPLICATE_PROCESSING`
- `UNSAFE_RETRY`
- `INFINITE_RETRY`
- `ACK_TIMING_REGRESSION`
- `MESSAGE_LOSS`
- `POISON_MESSAGE_LOOP`
- `DLQ_REGRESSION`
- `ORDERING_ASSUMPTION`
- `PARTIAL_FAILURE`
- `TIMEOUT_MISMATCH`
- `SERIALIZATION_REGRESSION`
- `PRODUCER_CONSUMER_MISMATCH`
- `ASYNC_TRANSACTION_BOUNDARY`
- `CONCURRENCY_REGRESSION`

Categories are descriptive.

Do not create multiple findings for the same root cause solely because several categories apply.

---

# Artifact Ownership

Return the complete specialist result, including `summary` and `findings`, to the orchestrator.

Do not write artifacts directly.

The orchestrator persists the result under:

`reports/findings/<pr-id>/async-review-specialist.json`

---

# Must Not

Do not:

- execute tasks
- send queue messages
- publish events
- start workers
- start brokers
- modify queue configuration
- modify worker configuration
- modify production code
- execute broad async tests
- run full test suites
- scan unrelated async code
- invent delivery guarantees
- invent acknowledgment semantics
- invent retry defaults
- invent timeout values
- invent queue metrics
- invent traffic volumes
- invent runtime behavior
- invent broker behavior
- report generic distributed-systems advice
- report pre-existing async issues as introduced
- invent summary content not supported by the reviewed evidence
- claim queues, workers, delivery behavior, configuration, or code locations in the summary that were not actually inspected
- write artifacts directly
- commit
- push
- merge
- publish

---

# Done When

The queue review is complete when:

- all relevant producer/consumer changes were inspected
- retry behavior was assessed where applicable
- acknowledgment and commit timing were reviewed
- idempotency was evaluated for repeatable side effects
- ordering assumptions were checked where relevant
- failure and terminal-handling paths were reviewed
- timeout and serialization changes were assessed where applicable
- speculative hypotheses were confirmed or discarded when one targeted read was sufficient
- every reported finding contains concrete async evidence
- the three required summary paragraphs were produced from reviewed evidence
- the complete specialist JSON (`summary` + `findings`) was returned to the orchestrator

If no evidence-backed async defect exists, return an empty findings list together with the required three-paragraph specialist summary.

````
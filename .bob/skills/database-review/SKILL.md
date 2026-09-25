---
name: database-review
description: >
  Reviews database changes for concrete risks to integrity, availability,
  performance, and deploy safety.
---

# Database Review

## Use When

Activate for:

- migrations or schema changes
- model/ORM changes
- query changes
- transactions
- indexes/constraints/foreign keys

## Check

Review changed persistence code for:

- unsafe or irreversible migrations
- `NOT NULL`/constraint changes that can fail on existing data
- data loss or incompatible type changes
- locking/downtime risk
- missing or harmful indexes
- N+1 or unbounded queries
- unsafe SQL construction
- transaction/rollback issues
- broken referential integrity

## Evidence

Each finding must include:

- changed file/line
- concrete migration/query/schema evidence
- affected table/model when known
- practical impact

Do not invent table sizes, EXPLAIN results, or production behavior.

## Output

Write:

`reports/findings/<pr-id>/database-review-specialist.json`

Finding IDs:

`DB-001`, `DB-002`, ...

Use the canonical finding schema.

Categories:

`MIGRATION_LOCK`, `IRREVERSIBLE_MIGRATION`, `NULL_SAFETY`,
`DATA_LOSS`, `N_PLUS_ONE`, `INDEX_MISSING`, `INDEX_LOCK`,
`TRANSACTION_BOUNDARY`, `CONSTRAINT_VIOLATION`,
`REFERENTIAL_INTEGRITY`, `QUERY_INJECTION`.

Set:

`verification_status: UNVERIFIED`

## Must Not

- execute migrations
- connect to or modify databases
- run application code
- scan unrelated persistence code
- fabricate metrics or query plans
- report pre-existing issues as introduced

## Done When

All changed database-related code in scope was reviewed and evidence-backed findings were written.
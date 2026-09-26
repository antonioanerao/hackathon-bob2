---
name: database-review
description: >
  Reviews database changes for integrity, availability, performance, and deploy risks.
---

# Database Review

## Use When

Activate for:

- migrations/schema changes
- ORM/model changes
- query changes
- transactions
- indexes/constraints/foreign keys

## Check

Review changed persistence code for:

- unsafe or irreversible migrations
- `NOT NULL`/constraint failures on existing data
- data loss or incompatible type changes
- locking/downtime risk
- missing or harmful indexes
- N+1 or unbounded queries
- unsafe SQL
- transaction/rollback issues
- referential integrity problems

## Evidence

Each finding must include:

- changed file/line
- concrete migration/query/schema evidence
- affected table/model when known
- practical impact
- actionable recommendation

Do not invent production data, query plans, or runtime behavior.

Do not emit speculative findings when one targeted read can confirm or refute them.

## Output

Return findings as canonical JSON to the orchestrator.

Finding IDs:

`DB-001`, `DB-002`, ...

Set:

`verification_status: UNVERIFIED`

The orchestrator persists:

`reports/findings/<pr-id>/database-review-specialist.json`

If no concrete defects exist, return an empty findings list.

## Must Not

- execute migrations
- connect to databases
- run application code
- scan unrelated persistence code
- fabricate metrics or query plans
- report pre-existing issues as introduced

## Done When

All relevant database changes were reviewed and evidence-backed findings were returned to the orchestrator.
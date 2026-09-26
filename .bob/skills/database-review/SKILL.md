---
name: database-review
description: >
  Reviews database, persistence, schema, migration, ORM, query, transaction,
  indexing, and referential-integrity changes for concrete correctness,
  availability, performance, and deployment risks.
---

# Database Review

## Purpose

Review persistence-related changes introduced or affected by the Pull Request.

The goal is to identify concrete, evidence-backed defects or risks involving:

- schema correctness
- data integrity
- migration safety
- transactional behavior
- locking and availability
- query correctness
- query scalability
- indexing
- referential integrity
- ORM behavior
- deployment compatibility

Do not perform general code review.

Do not report hypothetical database concerns unless the changed persistence
behavior or directly related schema/query context supports them.

---

## Use When

Activate this skill when the Pull Request changes one or more of the following:

- migrations
- schema definitions
- ORM models
- persistence entities
- repositories
- query builders
- raw SQL
- transactions
- indexes
- constraints
- foreign keys
- unique constraints
- nullable/non-nullable fields
- database types
- defaults
- persistence configuration
- database access patterns
- pagination or filtering affecting query shape

---

## Primary Review Goals

Determine whether the PR introduces or exposes:

- unsafe migration behavior
- irreversible data changes
- data loss
- incompatible type conversion
- constraint failures on existing data
- invalid default handling
- referential-integrity regressions
- incorrect transaction boundaries
- partial-commit risk
- rollback defects
- locking or deployment risk
- harmful or missing indexes
- incorrect query semantics
- N+1 query behavior
- unbounded reads
- inefficient access patterns when directly inferable
- unsafe SQL construction
- inconsistent ORM mappings
- schema/application incompatibility

---

# Review Scope

Start from changed persistence code.

Expand scope only when necessary to confirm or refute a concrete hypothesis.

Relevant expansion may include:

- directly related migration files
- ORM model definitions
- repository methods
- directly referenced queries
- related constraints
- related indexes
- direct service usage
- transaction wrappers
- schema initialization
- directly related tests

Do not scan unrelated database code.

---

# Migration Review

Inspect migration changes for deployment safety.

Check for:

- destructive operations
- irreversible operations
- dropped columns
- dropped tables
- type changes
- column renames
- table renames
- new constraints
- changed defaults
- new `NOT NULL` columns
- removal of defaults
- large-table rewrites when directly inferable
- migration ordering assumptions
- rollback asymmetry

---

# NOT NULL and Existing Data

When a column becomes non-nullable, determine whether existing rows can satisfy
the new constraint.

Examples of concrete risk:

- adding a `NOT NULL` column without a default
- removing a default before backfilling data
- adding a constraint before data cleanup
- converting nullable data to a stricter type without evidence of compatibility

Do not assume production data contains nulls.

Report the structural risk only when the migration itself requires pre-existing
data to satisfy a condition that is not guaranteed by the migration.

---

# Data Loss

Check for changes that can permanently discard or corrupt data.

Examples:

- dropping a populated column
- truncating data through narrower type conversion
- converting free text to enum without migration logic
- deleting rows as part of migration
- replacing identifiers without preserving relationships
- incompatible precision/scale reduction

A data-loss finding must identify the exact destructive operation.

Do not speculate about unknown row contents.

---

# Type Compatibility

Review type changes for compatibility.

Consider:

- string length reduction
- numeric precision changes
- integer narrowing
- timestamp/date conversion
- enum conversion
- JSON-to-structured-column conversion
- boolean representation changes
- binary/text conversion

A type-change finding requires a concrete incompatibility or loss condition.

---

# Constraint Review

Inspect:

- `NOT NULL`
- `UNIQUE`
- `CHECK`
- foreign keys
- exclusion constraints
- composite constraints

Check whether the PR creates:

- impossible insert/update behavior
- duplicate acceptance where uniqueness is required
- new uniqueness that existing migration logic cannot guarantee
- orphaned records
- invalid delete/update behavior
- unintended cascading behavior

Do not assume database defaults or foreign-key actions that are not shown.

---

# Referential Integrity

Check whether relationships remain valid.

Review:

- foreign-key creation
- foreign-key removal
- cascade rules
- parent deletion behavior
- child lifecycle
- ORM relationship mappings
- nullable foreign keys
- relationship direction

Examples of concrete defects:

- FK removed while code assumes enforced integrity
- cascade delete introduced unintentionally
- parent deletion now leaves orphaned rows
- ORM relation points to the wrong key

---

# Transaction Review

Check changed transaction behavior for:

- missing transaction boundaries
- partial writes
- multi-step updates without atomicity
- incorrect commit placement
- incorrect rollback handling
- nested transaction misuse
- side effects outside transaction boundaries
- retry behavior around transactions
- inconsistent transaction propagation

A transaction finding should identify a concrete failure path.

Example:

```text
write A succeeds
→ write B fails
→ no rollback occurs
→ database remains partially updated
```

Do not report generic "should use a transaction" concerns without showing why
atomicity is required.

---

# Locking and Availability

Review migrations and queries for concrete locking or availability risks.

Relevant examples:

- destructive DDL on a critical table
- index creation method likely to block writes where framework/database behavior
  is clearly known from context
- long-running update across all rows
- schema rewrite operation
- transaction holding locks across external calls

Do not invent:

- table size
- lock duration
- production concurrency
- downtime length

Describe only the mechanism supported by the change.

---

# Query Correctness

Review query changes for correctness.

Check for:

- missing predicates
- incorrect joins
- incorrect join direction
- duplicate rows
- incorrect aggregation
- incorrect grouping
- incorrect ordering
- wrong pagination
- unsafe limit/offset behavior
- incorrect tenant/user scoping
- accidental broad updates/deletes
- wrong column mapping
- incorrect null semantics

A finding should identify the query behavior that is incorrect.

---

# Unbounded Queries

Look for changed queries that can retrieve or modify an unbounded set when a
bound is required by existing behavior.

Examples:

- removal of pagination
- removal of tenant filter
- removal of identifier predicate
- fetching all related rows when only one subset is required

Do not call a query "unbounded" merely because no hardcoded limit exists.

The practical expectation must be supported by context.

---

# N+1 Review

Inspect ORM changes for clear N+1 behavior.

Examples:

```text
load list of N records
→ access lazy relation once per record
→ N additional queries
```

A valid N+1 finding should identify:

- the collection load
- the repeated lazy access
- the loop or iteration
- why the changed code introduces the repeated query pattern

Do not report N+1 based solely on seeing an ORM relationship.

---

# Index Review

Check changed queries and schema for index implications.

Potential issues include:

- removing an index still required by a changed critical query
- adding duplicate/redundant indexes with concrete write/storage cost
- creating an index with wrong column order for the specific changed access path
- missing uniqueness enforcement when index is part of correctness

Do not report "missing index" without identifying:

- the changed query pattern
- filtered/joined/sorted columns
- why an existing index does not satisfy it, when known

Do not invent execution plans.

---

# ORM Review

Check ORM mappings for:

- wrong table
- wrong column
- nullability mismatch
- type mismatch
- relationship mismatch
- cascade mismatch
- eager/lazy loading regressions
- missing uniqueness mapping
- persistence lifecycle mismatch

The ORM finding must be tied to changed application behavior.

---

# Raw SQL Review

When raw SQL is changed, inspect for:

- incorrect predicates
- unsafe concatenation
- unsafe interpolation
- malformed joins
- missing transactions
- incorrect quoting
- unintended full-table update/delete
- type mismatch
- incorrect parameter binding

Security-specific SQL injection exploitability may be reported by Security
Review, but Database Review may report incorrect or unsafe query construction
when the persistence impact itself is distinct.

---

# Pagination and Filtering

Check whether changed pagination or filtering creates:

- duplicate pages
- missing records
- unstable ordering
- unexpected full scans when directly inferable
- inconsistent count/query behavior
- filter bypass
- incorrect page boundaries

Do not assume scale characteristics without evidence.

---

# Deployment Compatibility

Consider whether application code and schema can coexist during deployment.

Check for:

- code expecting a new column before migration
- code removing use of a column after migration drops it
- renamed fields with no compatibility window
- application version mismatch during rolling deployment
- migration ordering dependency

Report only when the deployment sequence can be concretely established from the
change.

---

# Finding Gate

Emit a finding only when all of the following are true:

1. the issue is introduced, exposed, or materially changed by the PR
2. the persistence behavior is concretely identifiable
3. evidence exists in changed code or directly related database context
4. a practical integrity, correctness, availability, performance, or deployment
   impact exists
5. the issue is not merely a best-practice preference

Do not emit findings for:

- generic normalization advice
- generic indexing suggestions
- speculative performance tuning
- unknown production-data assumptions
- unknown query-plan assumptions
- hypothetical table sizes
- style
- naming
- optional ORM refactors
- pre-existing persistence problems unrelated to the PR

---

# Evidence Requirements

Every finding must include:

- changed file
- relevant line or code location
- affected table/model/query when known
- concrete migration/query/schema evidence
- practical impact
- actionable recommendation

When applicable, include:

- table name
- column name
- constraint
- index
- migration operation
- SQL fragment
- ORM relationship
- transaction boundary

---

# Targeted Confirmation

Before emitting a finding, perform one targeted inspection when it can directly
confirm or refute the hypothesis.

Examples:

- inspect the related ORM model
- inspect the migration pair
- inspect the referenced table definition
- inspect the direct repository method
- inspect the transaction wrapper
- inspect the related constraint
- inspect the direct query caller

Do not emit a speculative finding when one targeted read can resolve it.

---

# Practical Impact

Describe practical impact precisely.

Avoid:

```text
This may cause database problems.
```

Prefer:

```text
The migration adds a non-nullable `tenant_id` column without a default or
backfill step, so existing rows cannot satisfy the new constraint when the
migration is applied.
```

Do not claim production failure unless the failure mechanism is directly
supported.

---

# Relationship With Security Review

Database Review may overlap with Security Review for:

- SQL injection
- tenant scoping
- sensitive data
- unsafe queries

Database Review should focus on:

- query correctness
- schema correctness
- persistence integrity
- transaction behavior

Security Review should focus on:

- exploitability
- attacker-controlled input
- privilege impact
- data exposure

Do not duplicate the same root cause unless the persistence impact is distinct.

---

# Relationship With Code Review

Code Review focuses on:

- general correctness
- control flow
- state
- runtime logic

Database Review focuses on:

- persistence semantics
- schema
- queries
- migrations
- transactions
- database constraints

Do not duplicate another finding unless the database impact is independently
meaningful.

---

# Severity Guidance

Use severity based on practical persistence impact.

## LOW

Examples:

- narrow query inefficiency
- low-impact schema inconsistency
- minor non-blocking index issue

## MEDIUM

Examples:

- transaction boundary defect
- incorrect relationship mapping
- N+1 introduced on a meaningful path
- query regression affecting normal behavior
- migration incompatibility requiring intervention

## HIGH

Examples:

- concrete data-loss risk
- migration likely to fail because of its own constraint sequence
- referential-integrity break
- broad unintended update/delete
- transaction defect causing persistent partial state
- major deployment incompatibility

## CRITICAL

Reserve for severe persistence defects that can cause widespread or immediate:

- irreversible data loss
- corruption
- cross-tenant data integrity failure
- major system unavailability

Do not increase severity based on unknown production scale.

---

# Verification

All specialist findings must initially use:

`verification_status: UNVERIFIED`

If confirmation requires:

- executing a migration
- querying a database
- inspecting real data
- generating an execution plan
- running a targeted integration test

leave the finding unverified.

The finding verifier may later confirm or refute it using allowed targeted
evidence.

---

# Output Contract

Return JSON only.

Expected structure:

```json
{
  "specialist": "database-review-specialist",
  "findings": [
    {
      "id": "DB-001",
      "severity": "HIGH",
      "category": "UNSAFE_MIGRATION",
      "title": "New non-nullable column has no backfill path",
      "file": "migrations/20260926_add_tenant_id.py",
      "line": 21,
      "evidence": "The migration adds `tenant_id` with nullable=false and provides neither a default nor a preceding backfill operation.",
      "impact": "Existing rows cannot satisfy the constraint during migration unless every row already has a value through a mechanism not present in this migration.",
      "recommendation": "Add the column as nullable or with a safe temporary default, backfill existing rows, then enforce NOT NULL in a subsequent migration.",
      "verification_status": "UNVERIFIED"
    }
  ]
}
```

If no concrete database defect exists:

```json
{
  "specialist": "database-review-specialist",
  "findings": []
}
```

---

# Finding IDs

Use sequential IDs:

`DB-001`

`DB-002`

`DB-003`

Do not reuse one ID for multiple root causes.

---

# Suggested Categories

Use concise categories describing the actual issue.

Examples:

- `UNSAFE_MIGRATION`
- `DATA_LOSS_RISK`
- `TYPE_INCOMPATIBILITY`
- `CONSTRAINT_REGRESSION`
- `REFERENTIAL_INTEGRITY`
- `TRANSACTION_BOUNDARY`
- `ROLLBACK_REGRESSION`
- `LOCKING_RISK`
- `QUERY_CORRECTNESS`
- `UNBOUNDED_QUERY`
- `N_PLUS_ONE`
- `INDEX_REGRESSION`
- `ORM_MAPPING`
- `UNSAFE_SQL`
- `DEPLOYMENT_COMPATIBILITY`

Categories are descriptive.

Do not create several findings for the same root cause merely because multiple
categories apply.

---

# Artifact Ownership

Return findings to the orchestrator.

Do not write artifacts directly.

The orchestrator persists the result under:

`reports/findings/<pr-id>/database-review-specialist.json`

---

# Must Not

Do not:

- execute migrations
- connect to databases
- query production data
- modify schema
- modify migration files
- run application code
- execute broad database tools
- generate speculative execution plans
- scan unrelated persistence code
- invent production data
- invent dataset size
- invent row counts
- invent query latency
- invent lock duration
- invent database load
- invent runtime behavior
- fabricate query plans
- report pre-existing database issues as introduced
- report generic performance advice without evidence
- write artifacts directly
- commit
- push
- merge
- publish

---

# Done When

The database review is complete when:

- all relevant schema and migration changes were inspected
- changed ORM mappings were reviewed where applicable
- query changes were evaluated for correctness
- transaction behavior was inspected where relevant
- indexes and constraints were assessed where materially affected
- referential integrity was checked where applicable
- speculative hypotheses were confirmed or discarded when one targeted read was sufficient
- every reported finding contains concrete persistence evidence
- canonical findings JSON was returned to the orchestrator

If no evidence-backed database defect exists, return an empty findings list.

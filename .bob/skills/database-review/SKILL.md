---
name: database-review
description: >
  Evaluates migration safety, schema changes, constraints, N+1 queries,
  query plans, locking, transactions, indexes, and referential integrity.
  Used by the database-review-specialist.
---

# Database Review

## Purpose

Identify persistence-layer defects that can cause data loss, corruption,
performance degradation, unavailability, or integrity violations.

## Core Question

> Is the persistence layer change safe to deploy, and does it preserve data integrity?

## When to Use

Activated when DATABASE_SCHEMA_CHANGED, DATABASE_QUERY_CHANGED, MIGRATION,
ORM, MODEL_CHANGE, TRANSACTION, INDEX, or FOREIGN_KEY triggers are present.

## Inputs

- `reports/context/<pr-id>/pr-context.json`
- `reports/context/<pr-id>/impact-map.json`
- `reports/plans/<pr-id>/review-plan.json` (database section)
- Migration files (read-only)
- Model files (read-only)
- Repository/DAO files (read-only)

## Phases

### Phase 1: Migration Safety Checklist

For every migration file in the diff, answer:

1. **Reversibility**: Does a valid `downgrade()` / `down` function exist?
   - Record: reversible / not reversible / partial rollback only

2. **Locking risk**: Does any operation require ACCESS EXCLUSIVE or ShareLock
   on a high-traffic table?
   - High-risk operations: `ADD COLUMN NOT NULL`, `ADD CONSTRAINT`, `CREATE INDEX CONCURRENTLY` (safe) vs `CREATE INDEX` (unsafe), `ALTER TYPE`, `RENAME COLUMN`

3. **NULL safety**: Is a `NOT NULL` column being added to an existing table without
   a default value?
   - This fails immediately if the table has existing rows.

4. **Data transformation safety**: Is existing data being transformed in-place?
   - Is a backup/shadow column strategy used?

5. **Zero-downtime compatibility**: Can the migration run while the old application
   code is still serving traffic?
   - Removed columns must not still be read by old code
   - Added required columns must have defaults

6. **Dependent services**: Are other services that read this schema going to break?

### Phase 2: Schema Analysis

For changed model definitions:
- Are new required fields added to existing entities (breaking)?
- Are column types changed in a way that truncates existing data?
- Are existing constraints made more restrictive?
- Are foreign keys added without index on the referencing column?

### Phase 3: Index Analysis

For added or removed indexes:
- Is the index on a column used in a `WHERE`, `JOIN`, or `ORDER BY` clause?
- Does removing an index expose a full table scan on a high-cardinality table?
- Are duplicate indexes being added?
- Is `CREATE INDEX CONCURRENTLY` used for production tables (to avoid locking)?

### Phase 4: Query Analysis

For changed ORM queries or raw SQL:
- Is user input directly interpolated into SQL strings (injection risk)?
- Are N+1 patterns introduced? (loop calling `.get()` or lazy-loading)
- Are bulk operations used where available?
- Are queries missing LIMIT clauses on potentially large result sets?
- Are subqueries used where a JOIN would be more efficient?

```bash
grep -n "for.*in.*\.all()\|for.*in.*query\|\.filter(" app/repository/*.py
```

### Phase 5: Transaction Analysis

For changed transaction boundaries:
- Do transactions span the minimum necessary operations?
- Are long-running transactions holding locks?
- Is the correct isolation level used?
- What happens if an exception is raised mid-transaction?
- Are nested transactions handled correctly?

### Phase 6: Referential Integrity

- Are foreign keys being removed that enforce important relationships?
- Are cascade behaviors (DELETE, UPDATE) correct?
- Will existing data violate new constraints during migration?

## Deterministic Tools & Evidence

```bash
grep -n "NOT NULL\|NOT NULL DEFAULT\|ADD COLUMN" migrations/*.py
grep -n "AccessExclusive\|LOCK TABLE\|ALTER TABLE" migrations/*.py
grep -n "CREATE INDEX\b" migrations/*.py  # check for missing CONCURRENTLY
grep -n "for.*in.*session.query\|for.*in.*\.all()" app/repositories/*.py
python -c "from app.models import MyModel; print(MyModel.__table__.columns)"
```

## Canonical Output

File: `reports/findings/<pr-id>/database-review-specialist.json`

Finding IDs: `DB-001`, `DB-002`, ...

```json
{
  "reviewer": "database-review-specialist",
  "findings": [
    {
      "id": "DB-001",
      "category": "MIGRATION_LOCK | IRREVERSIBLE_MIGRATION | NULL_SAFETY | DATA_LOSS | N_PLUS_ONE | INDEX_MISSING | INDEX_LOCK | TRANSACTION_BOUNDARY | CONSTRAINT_VIOLATION | REFERENTIAL_INTEGRITY | QUERY_INJECTION",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "confidence": "CERTAIN | LIKELY | POSSIBLE",
      "title": "<concise title>",
      "description": "<technical explanation of the database risk>",
      "file": "<migration or model path>",
      "line": "<integer>",
      "evidence": ["<specific migration operation>", "<ORM query pattern>"],
      "impact": "<data loss / downtime / lock / corruption / performance>",
      "recommendation": "<actionable fix: use CONCURRENTLY, add default, etc.>",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR | EXPOSED_BY_PR | PRE_EXISTING | UNKNOWN",
      "reviewer": "database-review-specialist",
      "metadata": {
        "root_cause": "",
        "related_symbols": [],
        "affected_tables": ["<table_name>"],
        "database_engine": "<PostgreSQL | MySQL | SQLite>"
      }
    }
  ]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Cannot determine DB engine | Use generic SQL rules; note engine is unknown |
| ORM query to SQL translation unclear | Note ORM version; reason about likely generated SQL |
| Production data size unknown | Use conservative estimates; flag for operator review |

## What This Skill Must Not Do

- Run migrations against any database (read-only analysis only)
- Modify migration files or model definitions
- Fabricate EXPLAIN output or table sizes
- Report pre-existing schema issues as introduced by the PR

## Completion Criteria

- All migration files have been evaluated against the safety checklist
- All model and query changes have been assessed
- Index and constraint changes have been reviewed
- All findings have concrete evidence and impact descriptions
- Output file is written and schema-valid

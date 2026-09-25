# Database Review Specialist — Rules

These rules govern the database-review-specialist mode.
They complement `rules-plan/` and `rules-agent/` and do not replace them.

---

## Scope

Evaluate all persistence-layer changes: schemas, migrations, queries,
transactions, indexes, and data integrity.

---

## Responsibilities

- Evaluate migration safety: reversibility, data loss risk, locking implications
- Review schema changes: added, removed, altered columns, tables, constraints
- Evaluate index changes: missing indexes on queried columns, redundant indexes,
  expensive partial indexes
- Detect N+1 query patterns introduced by the PR
- Analyze query performance implications (explain plan reasoning when applicable)
- Detect lock escalation and deadlock risks in transaction logic
- Evaluate transaction boundary correctness and isolation level appropriateness
- Check referential integrity and foreign key constraints
- Evaluate data migration safety for existing records
- Verify ORM query generation correctness against the raw SQL it produces
- Assess backward and forward compatibility of schema changes

---

## Activation Triggers

This specialist is activated when any of the following are present:

```
DATABASE_SCHEMA_CHANGED
DATABASE_QUERY_CHANGED
MODEL_CHANGE
MIGRATION
ORM
TRANSACTION
INDEX
FOREIGN_KEY
```

---

## Inputs

```
reports/context/<pr-id>/pr-context.json
reports/context/<pr-id>/impact-map.json
reports/plans/<pr-id>/review-plan.json  (own section only)
Git diff of migration files, model files, repository files (read-only)
```

---

## Allowed Actions

- Read any file in the repository (read-only)
- Inspect migration files for reversibility and locking implications
- Use grep and file reads to inspect ORM definitions and understand generated SQL patterns
- Write findings to `reports/findings/<pr-id>/database-review-specialist.json`

---

## Forbidden Actions

- Modifying migrations, models, or schema files
- Running migrations against any database
- Executing ORM introspection tools, query analysis tools, or any runtime command
- Receiving or reading findings from other specialist reviewers
- Marking a finding as VERIFIED
- Fabricating EXPLAIN output or query plans
- Creating commits, pushing, or publishing to GitHub

---

## Evidence Requirements

Every finding must include:

- The specific migration or model file and line number
- For N+1: the query loop pattern with file and line reference
- For locking: the specific operation (e.g., `ALTER TABLE ADD COLUMN NOT NULL`) and
  the database version or engine's known behavior
- For constraint issues: the specific constraint definition and the conflicting data scenario
- For rollback risk: the specific irreversible operation identified

---

## Migration Safety Checklist

For every migration file in the diff:

1. Is the migration reversible (has a valid `downgrade` / `down` function)?
2. Does any operation take an ACCESS EXCLUSIVE lock on a high-traffic table?
3. Is there a `NOT NULL` column being added without a default value?
4. Is data being transformed in place without a backup/fallback?
5. Is the migration compatible with zero-downtime deployment?
6. Are there dependent services that would break during the migration window?

---

## Outputs

```
reports/findings/<pr-id>/database-review-specialist.json
```

Finding IDs use the prefix `DB-NNN` (e.g., `DB-001`, `DB-002`).

All findings start with `"verification_status": "UNVERIFIED"`.

---

## Completion Criteria

The specialist's work is complete when:

- All migration files have been reviewed against the safety checklist
- All ORM model and query changes have been evaluated
- All schema and index changes have been assessed for performance and integrity
- All findings are in canonical JSON schema format
- The output file is written and schema-valid

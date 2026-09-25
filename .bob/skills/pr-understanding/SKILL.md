---
name: pr-understanding
description: >
  Collects and structures all available information about a Pull Request
  to produce a canonical pr-context.json artifact used by all downstream agents.
---

# PR Understanding

## Purpose

Build a complete, structured understanding of what this Pull Request is trying to
change, why it is changing, and which parts of the codebase are directly affected.

This artifact is the foundation for all subsequent analysis. A poor understanding
here propagates errors through the entire pipeline.

## Core Question

> What is this PR trying to change?

## When to Use

Activate at the beginning of every PR Guardian run, before any specialist reviewer
or routing decision is made.

## Inputs

- PR URL or `owner/repo#N` reference
- Git access (read-only): `git log`, `git diff`, `git show`, `git diff --stat`
- PR metadata: title, description, linked issues, labels
- Repository file tree

## Phases

### Phase 1: Metadata Collection

Retrieve:
- PR title
- PR description (full body)
- All commit messages in the PR (from base to head)
- Base SHA and head SHA
- PR labels and assignees (for context)

### Phase 2: Changed File Enumeration

Execute:
```bash
git diff --name-only <base_sha>..<head_sha>
```

For each changed file, record:
- File path
- Change type (added / modified / deleted / renamed)
- Number of lines added and removed

### Phase 3: Symbol Discovery

For significant file changes, identify changed functions, classes, methods,
and variables using:
- AST inspection (Python: `ast`, `rope`; JS: `esprima`)
- grep for function/class definitions in the diff
- Language-appropriate symbol extraction

### Phase 4: Component Classification

Map changed files to logical components:
- `app/routes/` → API/Route component
- `app/models/` → Model/Schema component
- `app/repositories/` → Repository/Data Access component
- `app/services/` → Service/Domain Logic component
- `migrations/` → Migration component
- `tests/` → Test component
- `app/auth/` → Authentication/Authorization component
- `workers/`, `tasks/` → Background Job component
- `config/`, `settings.py` → Configuration component
- `.github/`, `pyproject.toml`, `requirements*.txt` → CI/Dependency component

### Phase 5: Technology Detection

Identify repository technologies:
```json
{
  "language": "<primary language>",
  "framework": "<web framework>",
  "test_framework": "<test runner>",
  "package_manager": "<pip | poetry | npm | etc.>",
  "database": "<PostgreSQL | MySQL | SQLite | etc.>",
  "orm": "<SQLAlchemy | Django ORM | Prisma | etc.>",
  "queue": "<RQ | Celery | Kafka | RabbitMQ | None>",
  "api_framework": "<Flask | FastAPI | Django | Express | etc.>",
  "lint_tools": ["<ruff | pylint | eslint | etc.>"],
  "security_tools": ["<bandit | semgrep | etc.>"],
  "ci": "<GitHub Actions | Jenkins | CircleCI | etc.>"
}
```

### Phase 6: Scope Reconciliation

Compare:
- `declared_scope`: what the PR description says it changes
- `observed_scope`: what the diff actually changes

Flag discrepancies: files changed that are not mentioned in the description,
or components described as changed that have no corresponding diff.

## Deterministic Tools & Evidence

```bash
git diff --stat <base_sha>..<head_sha>
git diff <base_sha>..<head_sha>
git log <base_sha>..<head_sha> --oneline
git show <head_sha>
grep -r "def " --include="*.py"   # symbol discovery fallback
cat pyproject.toml requirements*.txt  # dependency/tech discovery
```

## Canonical Output

File: `reports/context/<pr-id>/pr-context.json`

```json
{
  "pr_id": "<integer>",
  "title": "<string>",
  "intent": "<one paragraph describing the PR's purpose>",
  "base_sha": "<string>",
  "head_sha": "<string>",
  "changed_files": [
    {
      "path": "<string>",
      "change_type": "added | modified | deleted | renamed",
      "additions": "<integer>",
      "deletions": "<integer>"
    }
  ],
  "changed_components": ["<component_name>"],
  "technologies": {
    "language": "<string>",
    "framework": "<string>",
    "test_framework": "<string>",
    "package_manager": "<string>",
    "database": "<string>",
    "orm": "<string>",
    "queue": "<string>",
    "api_framework": "<string>",
    "lint_tools": [],
    "security_tools": [],
    "ci": "<string>"
  },
  "declared_scope": ["<string>"],
  "observed_scope": ["<string>"],
  "scope_discrepancies": ["<string>"]
}
```

## Failure Modes

| Failure | Correct Response |
|---------|-----------------|
| Git command unavailable | Record `TOOL_UNAVAILABLE`, proceed with available info |
| PR description is empty | Record empty `declared_scope`, continue with observed scope |
| Cannot determine technology | Leave field as `"unknown"`, do not guess |
| Binary files in diff | Record file path, note `"change_type": "binary"` |

## What This Skill Must Not Do

- Assume the PR intent without reading the description and commits
- Skip symbol discovery for files with large diffs
- Invent technologies not detected in the repository
- Pre-classify domains or risk triggers (that is the adaptive-routing skill's job)

## Completion Criteria

- `pr-context.json` is written to `reports/context/<pr-id>/`
- All changed files are enumerated with change type
- Technologies object is populated (unknown fields use `"unknown"`)
- `declared_scope` and `observed_scope` are both populated
- Any scope discrepancies are recorded

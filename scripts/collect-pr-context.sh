#!/usr/bin/env bash
# collect-pr-context.sh — Single-pass PR context collector for PR Guardian
#
# Usage:
#   ./scripts/collect-pr-context.sh <owner> <repo> <pr_number>
#   ./scripts/collect-pr-context.sh   (auto-detect from git remote + current branch)
#
# Output: compact JSON on stdout. Errors go to stderr.
#
# Discovery strategy:
#   Primary:  gh CLI
#   Fallback: GitHub REST API via curl
#   MAX_DISCOVERY_FALLBACKS = 1 (one fallback maximum; if both fail, local-only mode)
#
# The script collects in ONE pass:
#   PR metadata (title, body, base/head SHA, additions/deletions)
#   Changed files with stats
#   Commit list
#   Repository tech hints (language, framework, package manager, test framework,
#                          database, queue, CI)

set -euo pipefail

# ── Args / auto-detect ────────────────────────────────────────────────────────
OWNER="${1:-}"
REPO="${2:-}"
PR_NUMBER="${3:-}"

if [[ -z "$OWNER" || -z "$REPO" || -z "$PR_NUMBER" ]]; then
  # Auto-detect from git remote
  REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
  if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/.]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
  fi
  # Try to detect PR from branch name via gh
  if [[ -z "$PR_NUMBER" ]] && command -v gh &>/dev/null; then
    PR_NUMBER=$(gh pr view --json number -q '.number' 2>/dev/null || echo "")
  fi
  if [[ -z "$OWNER" || -z "$REPO" || -z "$PR_NUMBER" ]]; then
    echo '{"error":"Cannot auto-detect owner/repo/pr_number. Pass them explicitly."}' >&2
    exit 1
  fi
fi

# ── Helper: detect tech stack from local files ────────────────────────────────
detect_tech() {
  local language="" framework="" test_framework="" package_manager="" \
        database="" queue="" ci=""

  # Language
  if [[ -f pyproject.toml || -f setup.py || -f requirements.txt ]]; then
    language="Python"
    package_manager="pip"
    [[ -f pyproject.toml ]] && grep -q 'poetry' pyproject.toml 2>/dev/null && package_manager="poetry"
    [[ -f pyproject.toml ]] && grep -q 'uv' pyproject.toml 2>/dev/null && package_manager="uv"
  elif [[ -f package.json ]]; then
    language="JavaScript"
    [[ -f yarn.lock ]] && package_manager="yarn" || package_manager="npm"
    [[ -f tsconfig.json ]] && language="TypeScript"
  elif [[ -f go.mod ]]; then
    language="Go"
    package_manager="go mod"
  elif [[ -f Cargo.toml ]]; then
    language="Rust"
    package_manager="cargo"
  fi

  # Framework (Python)
  if [[ "$language" == "Python" ]]; then
    grep -rql 'fastapi\|FastAPI' . --include="*.py" --include="*.toml" 2>/dev/null && framework="FastAPI"
    grep -rql 'from flask\|import flask' . --include="*.py" 2>/dev/null && framework="Flask"
    grep -rql 'django' pyproject.toml requirements*.txt 2>/dev/null && framework="Django"
  fi

  # Test framework
  grep -rql 'import pytest\|from pytest' . --include="*.py" 2>/dev/null && test_framework="pytest"
  grep -rql 'unittest' . --include="*.py" 2>/dev/null && [[ -z "$test_framework" ]] && test_framework="unittest"

  # Database
  grep -rqil 'postgresql\|psycopg' . --include="*.py" --include="*.toml" --include="*.txt" 2>/dev/null && database="PostgreSQL"
  grep -rqil 'mysql\|mysqlclient' . --include="*.toml" --include="*.txt" 2>/dev/null && [[ -z "$database" ]] && database="MySQL"
  grep -rqil 'sqlite' . --include="*.py" 2>/dev/null && [[ -z "$database" ]] && database="SQLite"

  # Queue
  grep -rqil 'rq\|redis_queue' . --include="*.py" --include="*.toml" --include="*.txt" 2>/dev/null && queue="RQ"
  grep -rqil 'celery' . --include="*.py" --include="*.toml" 2>/dev/null && [[ -z "$queue" ]] && queue="Celery"
  grep -rqil 'kafka' . --include="*.py" --include="*.toml" 2>/dev/null && [[ -z "$queue" ]] && queue="Kafka"

  # CI
  [[ -d .github/workflows ]] && ci="GitHub Actions"
  [[ -f Jenkinsfile ]] && ci="Jenkins"
  [[ -f .circleci/config.yml ]] && ci="CircleCI"

  # Output as JSON object fields (no wrapping braces — caller handles structure)
  printf '"language":"%s","framework":"%s","test_framework":"%s","package_manager":"%s","database":"%s","queue":"%s","ci":"%s"' \
    "$language" "$framework" "$test_framework" "$package_manager" "$database" "$queue" "$ci"
}

# ── Primary: gh CLI ───────────────────────────────────────────────────────────
collect_via_gh() {
  gh pr view "$PR_NUMBER" \
    --repo "$OWNER/$REPO" \
    --json number,title,body,baseRefOid,headRefOid,additions,deletions,changedFiles,commits \
    2>/dev/null
}

# ── Fallback: GitHub REST API ─────────────────────────────────────────────────
collect_via_api() {
  local token="${GITHUB_TOKEN:-}"
  local auth_header=""
  [[ -n "$token" ]] && auth_header="-H \"Authorization: Bearer $token\""

  local pr_url="https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER"
  local files_url="https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/files"

  local pr_data files_data
  pr_data=$(curl -sf $auth_header "$pr_url" 2>/dev/null) || return 1
  files_data=$(curl -sf $auth_header "$files_url?per_page=100" 2>/dev/null) || return 1

  # Merge into a single JSON structure matching gh output shape
  python3 - <<EOF
import json, sys
pr = json.loads('''$pr_data''')
files = json.loads('''$files_data''')
out = {
  "number": pr.get("number"),
  "title": pr.get("title",""),
  "body": pr.get("body",""),
  "baseRefOid": pr.get("base",{}).get("sha",""),
  "headRefOid": pr.get("head",{}).get("sha",""),
  "additions": pr.get("additions",0),
  "deletions": pr.get("deletions",0),
  "changedFiles": pr.get("changed_files",0),
  "commits": pr.get("commits",0),
  "files": [{"filename": f.get("filename",""), "status": f.get("status",""),
             "additions": f.get("additions",0), "deletions": f.get("deletions",0)}
            for f in files]
}
print(json.dumps(out))
EOF
}

# ── Main collection ───────────────────────────────────────────────────────────
PR_JSON=""
COLLECTION_METHOD=""
FALLBACK_USED=false

if command -v gh &>/dev/null; then
  PR_JSON=$(collect_via_gh) && COLLECTION_METHOD="gh" || true
fi

if [[ -z "$PR_JSON" ]]; then
  FALLBACK_USED=true
  PR_JSON=$(collect_via_api) && COLLECTION_METHOD="github_api" || true
fi

if [[ -z "$PR_JSON" ]]; then
  # Both methods failed — emit local-only stub
  TECH=$(detect_tech)
  cat <<EOF
{
  "error": "PR_METADATA_UNAVAILABLE",
  "message": "Both gh and GitHub API failed. Proceeding with local-only context.",
  "pr_id": $PR_NUMBER,
  "repository": { $TECH },
  "collection_method": "local_only",
  "fallback_used": true
}
EOF
  exit 0
fi

# ── Detect tech stack once ────────────────────────────────────────────────────
TECH=$(detect_tech)

# ── Assemble compact context package ─────────────────────────────────────────
python3 - <<EOF
import json, sys

pr = json.loads('''$PR_JSON''')
tech_str = '''{$TECH}'''
tech = json.loads(tech_str)

# Normalise file list (gh returns different structure than API fallback)
files = pr.get("files", [])
if not files and "changedFiles" in pr:
    # gh output doesn't embed file list by default; we'll note count only
    files = []

out = {
  "pr_id": pr.get("number", $PR_NUMBER),
  "title": pr.get("title", ""),
  "body_preview": (pr.get("body") or "")[:500],
  "base_sha": pr.get("baseRefOid", ""),
  "head_sha": pr.get("headRefOid", ""),
  "additions": pr.get("additions", 0),
  "deletions": pr.get("deletions", 0),
  "changed_files_count": pr.get("changedFiles", len(files)),
  "commits": pr.get("commits", 0) if isinstance(pr.get("commits"), int) else len(pr.get("commits", [])),
  "changed_files": [
    {
      "path": f.get("filename", f.get("path", "")),
      "status": f.get("status", "modified"),
      "additions": f.get("additions", 0),
      "deletions": f.get("deletions", 0)
    }
    for f in files
  ],
  "repository": tech,
  "collection_method": "$COLLECTION_METHOD",
  "fallback_used": $( [[ "$FALLBACK_USED" == "true" ]] && echo "true" || echo "false" )
}
print(json.dumps(out, indent=2))
EOF

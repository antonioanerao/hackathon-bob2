#!/usr/bin/env bash

set -euo pipefail

ARG1="${1:-}"
ARG2="${2:-}"
ARG3="${3:-}"

OWNER=""
REPO=""
PR_NUMBER=""

# ------------------------------------------------------------
# Parse input
# ------------------------------------------------------------

# Format:
# owner repo pr_number
if [[ -n "$ARG1" && -n "$ARG2" && -n "$ARG3" ]]; then
  OWNER="$ARG1"
  REPO="$ARG2"
  PR_NUMBER="$ARG3"

# Format:
# https://github.com/owner/repo/pull/42
elif [[ "$ARG1" =~ ^https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)/?$ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUMBER="${BASH_REMATCH[3]}"

# Format:
# owner/repo#42
elif [[ "$ARG1" =~ ^([^/]+)/([^#]+)#([0-9]+)$ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUMBER="${BASH_REMATCH[3]}"

# Auto-detect from current git repository
elif [[ -z "$ARG1" ]]; then
  REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)

  if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    REPO="${REPO%.git}"
  fi

  if command -v gh >/dev/null 2>&1; then
    PR_NUMBER=$(gh pr view --json number -q '.number' 2>/dev/null || true)
  fi
fi

if [[ -z "$OWNER" || -z "$REPO" || -z "$PR_NUMBER" ]]; then
  cat >&2 <<'EOF'
{
  "error": "PR_REFERENCE_REQUIRED",
  "accepted": [
    "owner repo pr_number",
    "owner/repo#pr",
    "https://github.com/owner/repo/pull/pr"
  ]
}
EOF
  exit 1
fi

# ------------------------------------------------------------
# Primary collection: gh CLI
# ------------------------------------------------------------

collect_gh() {
  gh pr view "$PR_NUMBER" \
    --repo "$OWNER/$REPO" \
    --json number,title,body,baseRefOid,headRefOid,additions,deletions,changedFiles,files \
    2>/dev/null
}

# ------------------------------------------------------------
# Fallback collection: GitHub REST API
# ------------------------------------------------------------

collect_api() {
  local base="https://api.github.com/repos/$OWNER/$REPO"
  local curl_args=(-sfL)

  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    curl_args+=(
      -H "Authorization: Bearer $GITHUB_TOKEN"
    )
  fi

  curl_args+=(
    -H "Accept: application/vnd.github+json"
  )

  local pr
  local files

  pr=$(curl "${curl_args[@]}" \
    "$base/pulls/$PR_NUMBER") || return 1

  files=$(curl "${curl_args[@]}" \
    "$base/pulls/$PR_NUMBER/files?per_page=100") || return 1

  PR_DATA="$pr" FILES_DATA="$files" python3 <<'PY'
import json
import os

pr = json.loads(os.environ["PR_DATA"])
files = json.loads(os.environ["FILES_DATA"])

out = {
    "number": pr.get("number"),
    "title": pr.get("title", ""),
    "body": pr.get("body") or "",
    "baseRefOid": pr.get("base", {}).get("sha", ""),
    "headRefOid": pr.get("head", {}).get("sha", ""),
    "additions": pr.get("additions", 0),
    "deletions": pr.get("deletions", 0),
    "changedFiles": pr.get("changed_files", len(files)),
    "repositoryLanguage": (
        pr.get("base", {})
        .get("repo", {})
        .get("language", "")
        or ""
    ),
    "files": [
        {
            "path": f.get("filename", ""),
            "status": f.get("status", ""),
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0)
        }
        for f in files
    ]
}

print(json.dumps(out))
PY
}

# ------------------------------------------------------------
# Collect PR metadata
# ------------------------------------------------------------

METHOD=""
PR_JSON=""

if command -v gh >/dev/null 2>&1; then
  if PR_JSON=$(collect_gh) && [[ -n "$PR_JSON" ]]; then
    METHOD="gh"
  else
    PR_JSON=""
  fi
fi

if [[ -z "$PR_JSON" ]]; then
  if PR_JSON=$(collect_api) && [[ -n "$PR_JSON" ]]; then
    METHOD="github_api"
  else
    PR_JSON=""
  fi
fi

if [[ -z "$PR_JSON" ]]; then
  echo '{"error":"PR_METADATA_UNAVAILABLE"}' >&2
  exit 1
fi

# ------------------------------------------------------------
# Check whether current repository is the reviewed repository
# ------------------------------------------------------------

is_target_repository() {
  local remote_url
  local remote_owner=""
  local remote_repo=""

  remote_url=$(git remote get-url origin 2>/dev/null || true)

  if [[ "$remote_url" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
    remote_owner="${BASH_REMATCH[1]}"
    remote_repo="${BASH_REMATCH[2]}"
    remote_repo="${remote_repo%.git}"
  fi

  [[ "$remote_owner" == "$OWNER" && "$remote_repo" == "$REPO" ]]
}

# ------------------------------------------------------------
# Detect technology hints
# ------------------------------------------------------------

detect_tech() {
  local language=""
  local framework=""
  local package_manager=""
  local test_framework=""
  local database=""
  local queue=""
  local ci=""

  # Inspect local manifests only when the current checkout is the target repo.
  if is_target_repository; then

    if [[ -f pyproject.toml || -f requirements.txt ]]; then
      language="Python"

      [[ -f uv.lock ]] && package_manager="uv"
      [[ -f poetry.lock ]] && package_manager="poetry"
      [[ -z "$package_manager" ]] && package_manager="pip"

      grep -qi "fastapi" pyproject.toml requirements.txt 2>/dev/null &&
        framework="FastAPI" || true

      grep -qi "flask" pyproject.toml requirements.txt 2>/dev/null &&
        framework="Flask" || true

      grep -qi "django" pyproject.toml requirements.txt 2>/dev/null &&
        framework="Django" || true

      grep -qi "pytest" pyproject.toml requirements.txt 2>/dev/null &&
        test_framework="pytest" || true

      grep -qiE "postgres|psycopg" pyproject.toml requirements.txt 2>/dev/null &&
        database="PostgreSQL" || true

      grep -qi "celery" pyproject.toml requirements.txt 2>/dev/null &&
        queue="Celery" || true

      if [[ -z "$queue" ]]; then
        grep -qiE '(^|[^a-zA-Z])rq([^a-zA-Z]|$)' \
          pyproject.toml requirements.txt 2>/dev/null &&
          queue="RQ" || true
      fi

    elif [[ -f package.json ]]; then
      if [[ -f tsconfig.json ]]; then
        language="TypeScript"
      else
        language="JavaScript"
      fi

      if [[ -f yarn.lock ]]; then
        package_manager="yarn"
      elif [[ -f pnpm-lock.yaml ]]; then
        package_manager="pnpm"
      else
        package_manager="npm"
      fi

    elif [[ -f go.mod ]]; then
      language="Go"
      package_manager="go mod"

    elif [[ -f Cargo.toml ]]; then
      language="Rust"
      package_manager="cargo"
    fi

    [[ -d .github/workflows ]] && ci="GitHub Actions"
  fi

  # Infer only safe hints from changed file paths when reviewing
  # an external repository.
  if [[ -z "$language" ]]; then
    language=$(
      PR_DATA="$PR_JSON" python3 <<'PY'
import json
import os
from collections import Counter

pr = json.loads(os.environ["PR_DATA"])
paths = [
    f.get("path", f.get("filename", ""))
    for f in pr.get("files", [])
]

counts = Counter()

for path in paths:
    lower = path.lower()

    if lower.endswith(".py"):
        counts["Python"] += 1
    elif lower.endswith((".ts", ".tsx")):
        counts["TypeScript"] += 1
    elif lower.endswith((".js", ".jsx", ".mjs", ".cjs")):
        counts["JavaScript"] += 1
    elif lower.endswith(".go"):
        counts["Go"] += 1
    elif lower.endswith(".rs"):
        counts["Rust"] += 1
    elif lower.endswith((".java", ".kt", ".kts")):
        counts["Java/JVM"] += 1

repo_language = pr.get("repositoryLanguage", "")

if counts:
    print(counts.most_common(1)[0][0])
elif repo_language:
    print(repo_language)
PY
    )
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s' \
    "$language" \
    "$framework" \
    "$test_framework" \
    "$package_manager" \
    "$database" \
    "$queue" \
    "$ci"
}

# ------------------------------------------------------------
# Detect tech stack
# ------------------------------------------------------------

IFS=$'\t' read -r \
  LANGUAGE \
  FRAMEWORK \
  TEST_FRAMEWORK \
  PACKAGE_MANAGER \
  DATABASE \
  QUEUE \
  CI \
  <<< "$(detect_tech)"

# ------------------------------------------------------------
# Produce compact output
# ------------------------------------------------------------

PR_DATA="$PR_JSON" \
COLLECTION_METHOD="$METHOD" \
OWNER="$OWNER" \
REPO="$REPO" \
LANGUAGE="$LANGUAGE" \
FRAMEWORK="$FRAMEWORK" \
TEST_FRAMEWORK="$TEST_FRAMEWORK" \
PACKAGE_MANAGER="$PACKAGE_MANAGER" \
DATABASE="$DATABASE" \
QUEUE="$QUEUE" \
CI="$CI" \
python3 <<'PY'
import json
import os

pr = json.loads(os.environ["PR_DATA"])

files = []

for f in pr.get("files", []):
    files.append({
        "path": f.get("path", f.get("filename", "")),
        "status": f.get("status", "modified") or "modified",
        "additions": f.get("additions", 0),
        "deletions": f.get("deletions", 0)
    })

out = {
    "pr_id": pr.get("number"),
    "repository_name": f'{os.environ["OWNER"]}/{os.environ["REPO"]}',
    "title": pr.get("title", ""),
    "body_preview": (pr.get("body") or "")[:300],
    "base_sha": pr.get("baseRefOid", ""),
    "head_sha": pr.get("headRefOid", ""),
    "additions": pr.get("additions", 0),
    "deletions": pr.get("deletions", 0),
    "changed_files_count": pr.get("changedFiles", len(files)),
    "changed_files": files,
    "repository": {
        "language": os.environ.get("LANGUAGE", ""),
        "framework": os.environ.get("FRAMEWORK", ""),
        "test_framework": os.environ.get("TEST_FRAMEWORK", ""),
        "package_manager": os.environ.get("PACKAGE_MANAGER", ""),
        "database": os.environ.get("DATABASE", ""),
        "queue": os.environ.get("QUEUE", ""),
        "ci": os.environ.get("CI", "")
    },
    "collection_method": os.environ.get("COLLECTION_METHOD", "")
}

print(json.dumps(out, separators=(",", ":")))
PY
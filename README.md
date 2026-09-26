# PR Guardian

> Load knowledge lazily, not globally.  
> Don't just comment. Prove it.

PR Guardian is an evidence-based Pull Request review harness that combines an **IBM Bob** orchestration layer with a standalone **Python backend** powered by a local Ollama LLM.

It minimises agent count, context, and tool calls while producing auditable, concrete findings.

---

## Architecture

```text
PR reference (URL or owner/repo#N)
        ↓
scripts/collect-pr-context.sh   ← gh CLI or GitHub REST API
        ↓
pr_guardian/app/orchestrator.py
        ↓
triage (Ollama)  →  review-plan.json
        ↓
specialist loop (Ollama, one per selected reviewer)
        ↓
reports/findings/<pr-id>/<specialist>.json
        ↓
reports/reviews/<pr-id>/review.json + review.md
```

The Python orchestrator drives the full pipeline end-to-end from a single `python main.py` invocation.

The Bob layer (`.bob/`) mirrors the same architecture as Bob slash-commands and subagent specialists for interactive use inside the IBM Bob IDE.

---

## Project Structure

```text
pr_guardian/           Python backend
├── main.py            Entry point
├── .env-example       Environment template
├── requirements.txt
└── app/
    ├── config.py      Reads PR_GUARDIAN_SPECIALISTS from env
    ├── orchestrator.py Full pipeline: collect → triage → specialists → report
    ├── triage.py      Calls Ollama to classify risk and select reviewers
    ├── specialists.py Calls Ollama for each selected specialist
    ├── ollama_client.py HTTP client for Ollama /api/chat (JSON mode)
    ├── git_diff.py    Fetches the unified diff via GitHub API
    ├── reports.py     Builds review.json and review.md
    └── prompts.py     Loads global-rules.md and skill SKILL.md files

scripts/
└── collect-pr-context.sh   Collects PR metadata (gh CLI or REST API fallback)

reports/               Generated artifacts (git-ignored)
├── context/<pr-id>/pr-context.json
├── plans/<pr-id>/review-plan.json
├── findings/<pr-id>/<specialist>.json
└── reviews/<pr-id>/review.json + review.md

.bob/                  Bob IDE layer
├── commands/          /pr-guardian-review, /pr-guardian-verify, /pr-guardian-report
├── rules-agent/       Global read-only + evidence rules
├── rules-pr-guardian-orchestrator/
├── skills/            pr-triage, code-review, security-review, database-review,
│                      api-review, architecture-review, queue-review, finding-verification
└── custom_modes.yaml  Specialist modes
```

---

## Requirements

| Dependency | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| [Ollama](https://ollama.ai) | Local LLM inference |
| `requests` | HTTP calls to GitHub and Ollama |
| `python-dotenv` | `.env` loading |
| `gh` CLI *(optional)* | Primary PR metadata collection |
| `curl` + `bash` | REST API fallback in the collection script |

---

## Setup

### 1. Install Python dependencies

```bash
cd pr_guardian
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Pull an Ollama model

```bash
ollama pull qwen2.5-coder:7b
```

Any Ollama model that supports JSON-constrained output works. `qwen2.5-coder:7b` is the recommended default.

### 3. Configure environment

```bash
cp .env-example .env
```

Edit `.env`:

```env
PR_URL="https://github.com/owner/repository/pull/42"

OLLAMA_MODEL="qwen2.5-coder:7b"
OLLAMA_URL="http://127.0.0.1:11434"

GITHUB_TOKEN=""   # optional — increases GitHub API rate limit

# Comma-separated list of reviewer-id:skill-name pairs
# Controls which specialists are available to triage
PR_GUARDIAN_SPECIALISTS="code-review-specialist:code-review,security-review-specialist:security-review"
```

---

## Running a Review

```bash
cd pr_guardian
python main.py
```

The pipeline prints progress and writes artifacts under `reports/`:

```
[1/5] Collecting PR context...
[2/5] Running triage...
Risk: HIGH
Reviewers: ['code-review-specialist', 'security-review-specialist']
[3/5] Loading PR diff...
[4/5] Running specialists...
  → code-review-specialist
  → security-review-specialist
[5/5] Generating final report...
[5/5] Review finished.
Findings: 3
CODE-001 HIGH ...
SEC-001 MEDIUM ...
Report: reports/reviews/42/review.md
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PR_URL` | ✅ | — | Full GitHub PR URL |
| `OLLAMA_MODEL` | ✅ | — | Ollama model name |
| `OLLAMA_URL` | — | `http://127.0.0.1:11434` | Ollama base URL |
| `GITHUB_TOKEN` | — | — | GitHub PAT for API auth |
| `PR_GUARDIAN_SPECIALISTS` | ✅ | — | `reviewer:skill` pairs (comma-separated) |

---

## Specialists

Specialists are registered via `PR_GUARDIAN_SPECIALISTS`. Each entry maps a reviewer identifier to a skill name:

```
code-review-specialist:code-review
security-review-specialist:security-review
database-review-specialist:database-review
api-review-specialist:api-review
architecture-review-specialist:architecture-review
async-review-specialist:queue-review
```

Triage selects a subset from this list based on the PR's risk triggers. Each selected specialist runs sequentially, receives the PR context and unified diff, and returns a structured findings JSON.

---

## Artifacts

All outputs are written under `reports/` and are git-ignored.

| Artifact | Description |
|---|---|
| `reports/context/<pr-id>/pr-context.json` | Raw PR metadata from collection |
| `reports/plans/<pr-id>/review-plan.json` | Triage output: risk level, selected reviewers, agent budget |
| `reports/findings/<pr-id>/<specialist>.json` | Raw findings per specialist |
| `reports/reviews/<pr-id>/review.json` | Synthesised review (blocking + advisory) |
| `reports/reviews/<pr-id>/review.md` | Human-readable review report |

### Finding schema

```json
{
  "id": "CODE-001",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "category": "CATEGORY",
  "title": "Short title",
  "file": "path/to/file",
  "line": 42,
  "evidence": "Concrete evidence from the diff",
  "impact": "Practical impact if unaddressed",
  "recommendation": "Actionable recommendation",
  "verification_status": "UNVERIFIED"
}
```

### Classification

| Class | Condition |
|---|---|
| **BLOCKING** | `verification_status == VERIFIED` and `severity` is `CRITICAL` or `HIGH` |
| **ADVISORY** | All other non-refuted findings |

---

## Bob IDE Layer

The `.bob/` directory contains an equivalent interactive harness for the IBM Bob IDE.

| Command | Mode | Purpose |
|---|---|---|
| `/pr-guardian-review <ref>` | `pr-guardian-orchestrator` | Full PR review |
| `/pr-guardian-verify <pr-id>` | `finding-verifier` | Re-verify unresolved findings |
| `/pr-guardian-report <pr-id>` | `pr-guardian-orchestrator` | Rebuild reports from existing artifacts |

Example:

```
/pr-guardian-review https://github.com/owner/repository/pull/42
```

See [`.bob/README.md`](.bob/README.md) for the full Bob architecture and design principles.

---

## Security

- `.env` is git-ignored — credentials are never committed.
- Production code is read-only; all writes go to `reports/`.
- No automatic GitHub comments, commits, pushes, or merges.
- See [SECURITY.md](SECURITY.MD) for credential handling guidelines.

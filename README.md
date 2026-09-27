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
pr_guardian/scripts/collect-pr-context.sh   ← gh CLI or GitHub REST API
        ↓
pr_guardian/app/orchestrator.py
        ↓
triage (Ollama)  →  review-plan.json
        ↓
PR summary (Ollama, PR description + diff) → summary.json
        ↓
specialist loop (Ollama, one per selected reviewer)
        ↓
pr_guardian/reports/findings/<pr-id>/<specialist>.json
        ↓
Python conventions (Ruff, changed lines only) → pep8.json
        ↓
pr_guardian/reports/reviews/<pr-id>/review.json + review.md
```

The Python orchestrator drives the full pipeline end-to-end from a single `python main.py` invocation.

The Bob layer (`pr_guardian/.bob/`) mirrors the same architecture as Bob slash-commands and subagent specialists for interactive use inside the IBM Bob IDE.

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
    ├── pr_summary.py  Summarizes what the PR changes and why
    ├── specialists.py Calls Ollama for each selected specialist
    ├── ollama_client.py HTTP client for Ollama /api/chat (JSON mode)
    ├── git_diff.py    Fetches the unified diff via GitHub API
    ├── style_review.py Checks changed Python lines with Ruff
    ├── reports.py     Builds review.json and review.md
    └── prompts.py     Loads global-rules.md and skill SKILL.md files

pr_guardian/scripts/
└── collect-pr-context.sh   Collects PR metadata (gh CLI or REST API fallback)

pr_guardian/reports/    Generated artifacts
├── context/<pr-id>/pr-context.json
├── plans/<pr-id>/review-plan.json
├── summaries/<pr-id>/summary.json
├── findings/<pr-id>/<specialist>.json
├── style/<pr-id>/pep8.json
└── reviews/<pr-id>/review.json + review.md

pr_guardian/.bob/       Bob IDE layer
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
| `ruff` | Python convention checks on changed PR lines |
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
[1/6] Collecting PR context...
[2/6] Running triage...
Risk: HIGH
Reviewers: ['code-review-specialist', 'security-review-specialist']
[3/6] Loading PR diff...
[4/6] Generating PR summary...
[5/6] Reviewing PR changes...
  Running specialists...
  → code-review-specialist
  → security-review-specialist
  Checking Python conventions...
[6/6] Generating final report...
Review finished.
Findings: 3
Python conventions: 2 issues
CODE-001 HIGH ...
SEC-001 MEDIUM ...
Report: pr_guardian/reports/reviews/42/review.md
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

Outputs are written under `pr_guardian/reports/`.

| Artifact | Description |
|---|---|
| `pr_guardian/reports/context/<pr-id>/pr-context.json` | Raw PR metadata from collection |
| `pr_guardian/reports/plans/<pr-id>/review-plan.json` | Triage output: risk level and selected reviewers |
| `pr_guardian/reports/summaries/<pr-id>/summary.json` | Short description of what changed and why |
| `pr_guardian/reports/findings/<pr-id>/<specialist>.json` | Raw findings per specialist |
| `pr_guardian/reports/style/<pr-id>/pep8.json` | Ruff results for changed Python lines |
| `pr_guardian/reports/reviews/<pr-id>/review.json` | Synthesised review (blocking + advisory) |
| `pr_guardian/reports/reviews/<pr-id>/review.md` | Human-readable review report |

Python convention checks run independently of triage when a PR changes Python files. Ruff checks the complete file at the PR head SHA with `E`, `W`, and `N` rules and a 79-character line limit; the report includes only diagnostics on added or modified lines. Convention issues appear in a separate report section and do not count as behavioral findings.

The report's Summary section starts with 2–4 sentences generated from the PR title, description preview, and diff. The summary is saved separately and included in `review.json`. When the PR does not state a motivation, the model is instructed to say so rather than infer one.

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

The `pr_guardian/.bob/` directory contains an equivalent interactive harness for the IBM Bob IDE.

| Command | Mode | Purpose |
|---|---|---|
| `/pr-guardian-review <ref>` | `pr-guardian-orchestrator` | Full PR review |
| `/pr-guardian-verify <pr-id>` | `finding-verifier` | Re-verify unresolved findings |
| `/pr-guardian-report <pr-id>` | `pr-guardian-orchestrator` | Rebuild reports from existing artifacts |

Example:

```
/pr-guardian-review https://github.com/owner/repository/pull/42
```

See [`pr_guardian/.bob/README.md`](pr_guardian/.bob/README.md) for the full Bob architecture and design principles.

---

## Security

- `.env` is git-ignored — credentials are never committed.
- Production code is read-only; all writes go to `reports/`.
- No automatic GitHub comments, commits, pushes, or merges.
- See [SECURITY.md](SECURITY.MD) for credential handling guidelines.

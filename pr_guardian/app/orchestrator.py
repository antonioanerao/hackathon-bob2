from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .git_diff import get_pr_diff
from .pr_summary import generate_pr_summary
from .reports import write_report
from .specialists import run_specialist
from .style_review import review_python_style
from .triage import run_triage


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def write_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def collect_context(
    pr_ref: str,
) -> dict[str, Any]:
    script = (
        ROOT
        / "scripts"
        / "collect-pr-context.sh"
    )

    if not script.exists():
        raise RuntimeError(
            f"Collector not found: {script}"
        )

    result = subprocess.run(
        [
            "bash",
            str(script),
            pr_ref,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown collector error."
        )

        raise RuntimeError(
            f"PR context collection failed "
            f"(exit={result.returncode}): "
            f"{message}"
        )

    try:
        context = json.loads(
            result.stdout
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Collector returned invalid JSON."
        ) from exc

    if not isinstance(context, dict):
        raise RuntimeError(
            "Collector response must be a JSON object."
        )

    required_fields = {
        "pr_id",
        "repository_name",
        "changed_files",
    }

    missing = sorted(
        field
        for field in required_fields
        if field not in context
    )

    if missing:
        raise RuntimeError(
            "Collector response is missing required "
            f"fields: {missing}"
        )

    if not isinstance(
        context["changed_files"],
        list,
    ):
        raise RuntimeError(
            "Collector field 'changed_files' must be a list."
        )

    return context


def parse_repository(
    context: dict[str, Any],
) -> tuple[str, str]:
    repo = context.get(
        "repository_name"
    )

    if not isinstance(repo, str):
        raise RuntimeError(
            "Invalid repository_name in PR context."
        )

    repo = repo.strip()

    if "/" not in repo:
        raise RuntimeError(
            f"Invalid repository_name: {repo!r}"
        )

    owner, name = repo.split(
        "/",
        1,
    )

    if not owner or not name:
        raise RuntimeError(
            f"Invalid repository_name: {repo!r}"
        )

    return owner, name


def has_changed_python_files(
    context: dict[str, Any],
) -> bool:
    for item in context.get(
        "changed_files",
        [],
    ):
        if not isinstance(item, dict):
            continue

        path = item.get("path")
        status = item.get("status")

        if (
            isinstance(path, str)
            and path.endswith(".py")
            and status != "removed"
        ):
            return True

    return False


def run(
    pr_ref: str,
    model: str,
) -> None:

    print(
        "[1/6] Collecting PR context..."
    )

    context = collect_context(
        pr_ref
    )

    pr_id = str(
        context["pr_id"]
    )

    write_json(
        REPORTS
        / "context"
        / pr_id
        / "pr-context.json",
        context,
    )

    print(
        "[2/6] Running triage..."
    )

    plan = run_triage(
        context=context,
        model=model,
    )

    write_json(
        REPORTS
        / "plans"
        / pr_id
        / "review-plan.json",
        plan,
    )

    print(
        f"Risk: {plan['risk_level']}"
    )

    selected_reviewers = plan.get(
        "selected_reviewers",
        [],
    )

    if not isinstance(
        selected_reviewers,
        list,
    ):
        raise RuntimeError(
            "Invalid review plan: "
            "selected_reviewers must be a list."
        )

    print(
        "Reviewers:",
        selected_reviewers,
    )

    python_files = (
        has_changed_python_files(
            context
        )
    )

    owner, repo = parse_repository(
        context
    )

    print(
        "[3/6] Loading PR diff..."
    )

    diff = get_pr_diff(
        owner,
        repo,
        int(pr_id),
    )

    print(
        "[4/6] Generating PR summary..."
    )

    summary = generate_pr_summary(
        context,
        diff,
        model,
    )

    write_json(
        REPORTS
        / "summaries"
        / pr_id
        / "summary.json",
        {
            "summary": summary,
        },
    )

    print(
        "[5/6] Reviewing PR changes..."
    )

    all_findings: list[
        dict[str, Any]
    ] = []

    specialist_results: list[
        dict[str, Any]
    ] = []

    specialist_failures: list[
        dict[str, str]
    ] = []

    if selected_reviewers:

        print(
            "  Running specialists..."
        )

        for specialist in selected_reviewers:

            if not isinstance(
                specialist,
                str,
            ):
                raise RuntimeError(
                    "Invalid review plan: "
                    "reviewer identifiers must be strings."
                )

            print(
                f"  → {specialist}"
            )

            try:
                result = run_specialist(
                    specialist=specialist,
                    context=context,
                    diff=diff,
                    model=model,
                )

                # run_specialist() already validates:
                # - specialist identity
                # - summary.analysis
                # - summary.result
                # - summary.implementation
                # - canonical findings
                # - UNVERIFIED specialist status
                write_json(
                    REPORTS
                    / "findings"
                    / pr_id
                    / f"{specialist}.json",
                    result,
                )

                specialist_results.append(
                    result
                )

                all_findings.extend(
                    result["findings"]
                )

            except Exception as exc:
                failure = {
                    "specialist": specialist,
                    "error": str(exc),
                }

                specialist_failures.append(
                    failure
                )

                print(
                    f"    FAILED: {exc}"
                )

                # Independent specialists should continue.
                # Do not create a fake successful artifact.
                continue

    else:
        print(
            "  Specialist review skipped."
        )

    # Style review is deterministic supporting evidence.
    # It is not automatically part of canonical findings.
    style_review: dict[str, Any] = {
        "checked_files": 0,
        "findings": [],
    }

    if python_files:
        print(
            "  Checking Python conventions..."
        )

        style_review = (
            review_python_style(
                context,
                diff,
            )
        )

    write_json(
        REPORTS
        / "style"
        / pr_id
        / "pep8.json",
        style_review,
    )

    print(
        "[6/6] Generating final report..."
    )

    write_report(
        reports_root=REPORTS,
        pr_id=pr_id,
        context=context,
        review_plan=plan,
        style_review=style_review,
        summary=summary,
        specialist_results=specialist_results,
        specialist_failures=specialist_failures,
    )

    print(
        "Review finished."
    )

    print(
        f"Findings: "
        f"{len(all_findings)}"
    )

    print(
        "Specialists completed: "
        f"{len(specialist_results)}"
    )

    print(
        "Specialists failed: "
        f"{len(specialist_failures)}"
    )

    if python_files:
        style_findings = (
            style_review.get(
                "findings",
                [],
            )
        )

        print(
            "Python conventions: "
            f"{len(style_findings)} issues"
        )

    else:
        print(
            "Python conventions: "
            "skipped "
            "(no changed Python files)"
        )

    for finding in all_findings:
        print(
            f"{finding.get('id', 'UNKNOWN')} "
            f"{finding.get('severity', 'UNKNOWN')} "
            f"{finding.get('title', '')}"
        )

    if specialist_failures:
        print(
            "Review status: PARTIAL"
        )

        for failure in specialist_failures:
            print(
                "  Specialist failure: "
                f"{failure['specialist']} — "
                f"{failure['error']}"
            )

    else:
        print(
            "Review status: COMPLETE"
        )

    print(
        "Report:",
        REPORTS
        / "reviews"
        / pr_id
        / "review.md",
    )

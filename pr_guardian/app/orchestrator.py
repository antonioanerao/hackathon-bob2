from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .git_diff import get_pr_diff
from .reports import write_report
from .specialists import run_specialist
from .triage import run_triage


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def write_json(
    path: Path,
    data: dict,
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
) -> dict:
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
        raise RuntimeError(
            result.stderr
            or result.stdout
        )

    return json.loads(
        result.stdout
    )


def parse_repository(
    context: dict,
) -> tuple[str, str]:
    repo = context[
        "repository_name"
    ]

    owner, name = repo.split(
        "/",
        1,
    )

    return owner, name


def run(
    pr_ref: str,
    model: str,
) -> None:

    print(
        "[1/5] Collecting PR context..."
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
        "[2/5] Running triage..."
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

    print(
        "Reviewers:",
        plan[
            "selected_reviewers"
        ],
    )

    all_findings = []

    if plan["selected_reviewers"]:

        owner, repo = parse_repository(
            context
        )

        print(
            "[3/5] Loading PR diff..."
        )

        diff = get_pr_diff(
            owner,
            repo,
            int(pr_id),
        )

        print(
            "[4/5] Running specialists..."
        )

        for specialist in plan[
            "selected_reviewers"
        ]:

            print(
                f"  → {specialist}"
            )

            result = run_specialist(
                specialist=specialist,
                context=context,
                diff=diff,
                model=model,
            )

            write_json(
                REPORTS
                / "findings"
                / pr_id
                / f"{specialist}.json",
                result,
            )

            all_findings.extend(
                result.get(
                    "findings",
                    [],
                )
            )

    else:
        print(
            "[3/5] No specialist required."
        )

        print(
            "[4/5] Specialist review skipped."
        )

    print(
        "[5/5] Generating final report..."
    )

    write_report(
        reports_root=REPORTS,
        pr_id=pr_id,
        context=context,
        review_plan=plan,
    )

    print(
        "[5/5] Review finished."
    )

    print(
        f"Findings: "
        f"{len(all_findings)}"
    )

    for finding in all_findings:
        print(
            f"{finding.get('id', 'UNKNOWN')} "
            f"{finding.get('severity', 'UNKNOWN')} "
            f"{finding.get('title', '')}"
        )

    print(
        "Report:",
        REPORTS
        / "reviews"
        / pr_id
        / "review.md",
    )
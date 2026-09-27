from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


VALID_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

VALID_VERIFICATION_STATUSES = {
    "VERIFIED",
    "REFUTED",
    "UNVERIFIED",
    "NOT_APPLICABLE",
    "VERIFICATION_FAILED",
}

SPECIALIST_TITLES = {
    "code-review-specialist": "Code Review",
    "security-review-specialist": "Security Review",
    "database-review-specialist": "Database Review",
    "api-review-specialist": "API Review",
    "architecture-review-specialist": "Architecture Review",
    "async-review-specialist": "Async / Queue Review",
}


def _read_json(
    path: Path,
) -> dict[str, Any]:
    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Required artifact not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Malformed JSON artifact: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            f"Artifact must contain a JSON object: {path}"
        )

    return data


def _write_json(
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


def _validate_summary(
    summary: Any,
    *,
    owner: str,
) -> dict[str, str]:
    if not isinstance(summary, dict):
        raise RuntimeError(
            f"Invalid summary for {owner}: expected object."
        )

    normalized: dict[str, str] = {}

    for field in (
        "analysis",
        "result",
        "implementation",
    ):
        value = summary.get(field)

        if not isinstance(value, str):
            raise RuntimeError(
                f"Invalid summary.{field} for {owner}: "
                "expected string."
            )

        value = value.strip()

        if not value:
            raise RuntimeError(
                f"Invalid summary.{field} for {owner}: "
                "value cannot be empty."
            )

        normalized[field] = value

    return normalized


def _validate_finding(
    finding: Any,
) -> dict[str, Any]:
    if not isinstance(finding, dict):
        raise RuntimeError(
            "Finding must be a JSON object."
        )

    required = (
        "id",
        "severity",
        "category",
        "title",
        "file",
        "line",
        "evidence",
        "impact",
        "recommendation",
        "verification_status",
    )

    missing = [
        field
        for field in required
        if field not in finding
    ]

    if missing:
        raise RuntimeError(
            f"Finding is missing required fields: {missing}"
        )

    finding_id = finding["id"]

    if (
        not isinstance(finding_id, str)
        or not finding_id.strip()
    ):
        raise RuntimeError(
            "Finding id must be a non-empty string."
        )

    severity = finding["severity"]

    if (
        not isinstance(severity, str)
        or severity not in VALID_SEVERITIES
    ):
        raise RuntimeError(
            f"Invalid severity for {finding_id}: "
            f"{severity!r}"
        )

    status = finding["verification_status"]

    if (
        not isinstance(status, str)
        or status not in VALID_VERIFICATION_STATUSES
    ):
        raise RuntimeError(
            f"Invalid verification status for "
            f"{finding_id}: {status!r}"
        )

    return copy.deepcopy(finding)


def load_specialist_results(
    findings_dir: Path,
    selected_reviewers: list[str],
    specialist_failures: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    failures = {
        item.get("specialist")
        for item in (specialist_failures or [])
        if isinstance(item, dict)
    }

    results: list[dict[str, Any]] = []

    for reviewer in selected_reviewers:
        if reviewer in failures:
            continue

        file = findings_dir / f"{reviewer}.json"

        data = _read_json(file)

        if data.get("specialist") != reviewer:
            raise RuntimeError(
                f"Specialist artifact mismatch: "
                f"expected {reviewer!r}, got "
                f"{data.get('specialist')!r}."
            )

        summary = _validate_summary(
            data.get("summary"),
            owner=reviewer,
        )

        findings_raw = data.get("findings")

        if not isinstance(findings_raw, list):
            raise RuntimeError(
                f"Invalid findings for {reviewer}: "
                "expected list."
            )

        findings = [
            _validate_finding(finding)
            for finding in findings_raw
        ]

        results.append(
            {
                "specialist": reviewer,
                "summary": summary,
                "findings": findings,
            }
        )

    return results


def normalize_specialist_results(
    specialist_results: list[dict[str, Any]],
    selected_reviewers: list[str],
) -> list[dict[str, Any]]:
    by_specialist: dict[
        str,
        dict[str, Any],
    ] = {}

    for result in specialist_results:
        if not isinstance(result, dict):
            raise RuntimeError(
                "Invalid specialist result: "
                "expected object."
            )

        specialist = result.get(
            "specialist"
        )

        if not isinstance(
            specialist,
            str,
        ):
            raise RuntimeError(
                "Invalid specialist identity."
            )

        if specialist not in selected_reviewers:
            raise RuntimeError(
                f"Unexpected specialist result: "
                f"{specialist}"
            )

        if specialist in by_specialist:
            raise RuntimeError(
                f"Duplicate specialist result: "
                f"{specialist}"
            )

        summary = _validate_summary(
            result.get("summary"),
            owner=specialist,
        )

        findings_raw = result.get(
            "findings"
        )

        if not isinstance(
            findings_raw,
            list,
        ):
            raise RuntimeError(
                f"Invalid findings for "
                f"{specialist}: expected list."
            )

        findings = [
            _validate_finding(finding)
            for finding in findings_raw
        ]

        by_specialist[specialist] = {
            "specialist": specialist,
            "summary": summary,
            "findings": findings,
        }

    return [
        by_specialist[reviewer]
        for reviewer in selected_reviewers
        if reviewer in by_specialist
    ]


def flatten_findings(
    specialist_results: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    findings: list[
        dict[str, Any]
    ] = []

    for result in specialist_results:
        specialist = result[
            "specialist"
        ]

        for finding in result[
            "findings"
        ]:
            item = copy.deepcopy(
                finding
            )
            item["specialist"] = (
                specialist
            )
            findings.append(item)

    return findings


def load_verification(
    reports_root: Path,
    pr_id: str,
) -> dict[str, Any] | None:
    path = (
        reports_root
        / "verification"
        / pr_id
        / "verification-results.json"
    )

    if not path.exists():
        return None

    data = _read_json(path)

    summary = _validate_summary(
        data.get("summary"),
        owner="finding-verifier",
    )

    results = data.get(
        "results"
    )

    if not isinstance(
        results,
        list,
    ):
        raise RuntimeError(
            "Invalid verification results: "
            "expected list."
        )

    normalized_results: list[
        dict[str, Any]
    ] = []

    seen_ids: set[str] = set()

    for result in results:
        if not isinstance(
            result,
            dict,
        ):
            raise RuntimeError(
                "Invalid verification result: "
                "expected object."
            )

        finding_id = result.get(
            "finding_id"
        )
        status = result.get(
            "status"
        )

        if (
            not isinstance(
                finding_id,
                str,
            )
            or not finding_id.strip()
        ):
            raise RuntimeError(
                "Verification finding_id must "
                "be a non-empty string."
            )

        if finding_id in seen_ids:
            raise RuntimeError(
                "Duplicate verification result "
                f"for finding: {finding_id}"
            )

        seen_ids.add(
            finding_id
        )

        if status not in (
            VALID_VERIFICATION_STATUSES
        ):
            raise RuntimeError(
                "Invalid verification status "
                f"for {finding_id}: "
                f"{status!r}"
            )

        normalized_results.append(
            copy.deepcopy(result)
        )

    return {
        "summary": summary,
        "results": normalized_results,
    }


def apply_verification(
    findings: list[dict[str, Any]],
    verification: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if verification is None:
        return copy.deepcopy(findings)

    by_id = {
        finding["id"]: copy.deepcopy(
            finding
        )
        for finding in findings
    }

    for result in verification[
        "results"
    ]:
        finding_id = result[
            "finding_id"
        ]

        if finding_id not in by_id:
            raise RuntimeError(
                "Verification artifact references "
                f"unknown finding: {finding_id}"
            )

        finding = by_id[
            finding_id
        ]

        finding[
            "verification_status"
        ] = result["status"]

        finding[
            "verification"
        ] = {
            "method": result.get(
                "method"
            ),
            "evidence": result.get(
                "evidence"
            ),
            "command": result.get(
                "command"
            ),
            "exit_code": result.get(
                "exit_code"
            ),
            "notes": result.get(
                "notes"
            ),
        }

    return [
        by_id[finding["id"]]
        for finding in findings
    ]


def deduplicate_findings(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Conservative deterministic deduplication.

    Only merge findings when their concrete identity is effectively the
    same: same file, line, normalized title, and normalized evidence.

    Root-cause inference that requires semantic reasoning belongs upstream,
    not in deterministic report generation.
    """
    unique: list[
        dict[str, Any]
    ] = []

    seen: set[
        tuple[Any, ...]
    ] = set()

    for finding in findings:
        key = (
            finding.get("file"),
            finding.get("line"),
            str(
                finding.get(
                    "title",
                    "",
                )
            ).strip().lower(),
            str(
                finding.get(
                    "evidence",
                    "",
                )
            ).strip().lower(),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(finding)

    return unique


def classify_findings(
    findings: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    blocking: list[
        dict[str, Any]
    ] = []
    advisory: list[
        dict[str, Any]
    ] = []
    refuted: list[
        dict[str, Any]
    ] = []
    not_applicable: list[
        dict[str, Any]
    ] = []

    for finding in findings:
        status = finding.get(
            "verification_status",
            "UNVERIFIED",
        )

        severity = str(
            finding.get(
                "severity",
                "",
            )
        ).upper()

        if status == "REFUTED":
            refuted.append(
                finding
            )
            continue

        if status == "NOT_APPLICABLE":
            not_applicable.append(
                finding
            )
            continue

        if (
            status == "VERIFIED"
            and severity
            in {
                "CRITICAL",
                "HIGH",
            }
        ):
            blocking.append(
                finding
            )
        else:
            advisory.append(
                finding
            )

    return (
        blocking,
        advisory,
        refuted,
        not_applicable,
    )


def render_finding(
    finding: dict[str, Any],
) -> str:
    parts = [
        (
            f"### {finding.get('id', 'UNKNOWN')} "
            f"— {finding.get('title', '')}"
        ),
        "",
        (
            f"- **Severity:** "
            f"`{finding.get('severity', 'UNKNOWN')}`"
        ),
        (
            f"- **Category:** "
            f"`{finding.get('category', 'UNKNOWN')}`"
        ),
        (
            f"- **Verification:** "
            f"`{finding.get('verification_status', 'UNVERIFIED')}`"
        ),
        (
            f"- **File:** "
            f"`{finding.get('file', '')}:"
            f"{finding.get('line', '')}`"
        ),
        "",
        "**Evidence**",
        "",
        str(
            finding.get(
                "evidence",
                "",
            )
        ),
        "",
        "**Impact**",
        "",
        str(
            finding.get(
                "impact",
                "",
            )
        ),
        "",
        "**Recommendation**",
        "",
        str(
            finding.get(
                "recommendation",
                "",
            )
        ),
    ]

    verification = finding.get(
        "verification"
    )

    if isinstance(
        verification,
        dict,
    ):
        parts.extend(
            [
                "",
                "**Verification Details**",
                "",
                (
                    f"- Method: "
                    f"`{verification.get('method')}`"
                ),
                (
                    f"- Evidence: "
                    f"{verification.get('evidence') or ''}"
                ),
            ]
        )

        notes = verification.get(
            "notes"
        )

        if notes:
            parts.append(
                f"- Notes: {notes}"
            )

    return "\n".join(parts)


def render_specialist_reviews(
    specialist_results: list[
        dict[str, Any]
    ],
) -> list[str]:
    lines = [
        "## Specialist Reviews",
        "",
    ]

    if not specialist_results:
        lines.append(
            "No specialist review was executed."
        )
        return lines

    for result in specialist_results:
        specialist = result[
            "specialist"
        ]
        title = SPECIALIST_TITLES.get(
            specialist,
            specialist,
        )
        summary = result[
            "summary"
        ]

        lines.extend(
            [
                f"### {title}",
                "",
                "**Analysis**",
                "",
                summary["analysis"],
                "",
                "**Result**",
                "",
                summary["result"],
                "",
                "**Implementation**",
                "",
                summary["implementation"],
                "",
            ]
        )

    return lines


def render_verification(
    verification: dict[str, Any] | None,
) -> list[str]:
    lines = [
        "## Verification",
        "",
    ]

    if verification is None:
        lines.append(
            "No verification artifact was applied."
        )
        return lines

    summary = verification[
        "summary"
    ]

    lines.extend(
        [
            "**Analysis**",
            "",
            summary["analysis"],
            "",
            "**Result**",
            "",
            summary["result"],
            "",
            "**Implementation**",
            "",
            summary["implementation"],
        ]
    )

    return lines


def build_report_markdown(
    context: dict[str, Any],
    review_plan: dict[str, Any],
    findings: list[dict[str, Any]],
    specialist_results: list[dict[str, Any]],
    specialist_failures: list[dict[str, str]],
    verification: dict[str, Any] | None,
    summary: str,
) -> str:
    (
        blocking,
        advisory,
        refuted,
        not_applicable,
    ) = classify_findings(
        findings
    )

    selected_reviewers = (
        review_plan.get(
            "selected_reviewers",
            [],
        )
    )

    risk_triggers = (
        review_plan.get(
            "risk_triggers",
            [],
        )
    )

    reviewer_reasons = (
        review_plan.get(
            "reviewer_reasons",
            {},
        )
    )

    review_status = (
        "PARTIAL"
        if specialist_failures
        else "COMPLETE"
    )

    lines = [
        (
            "# PR Guardian Review "
            f"— PR #{context.get('pr_id')}"
        ),
        "",
        (
            f"**Repository:** "
            f"`{context.get('repository_name', '')}`"
        ),
        "",
        (
            f"**Title:** "
            f"{context.get('title', '')}"
        ),
        "",
        (
            f"**Risk Level:** "
            f"`{review_plan.get('risk_level', 'UNKNOWN')}`"
        ),
        "",
        (
            f"**Review Status:** "
            f"`{review_status}`"
        ),
        "",
        "## Summary",
        "",
        summary,
        "",
        (
            f"- Changed files: "
            f"{context.get('changed_files_count', 0)}"
        ),
        (
            f"- Additions: "
            f"{context.get('additions', 0)}"
        ),
        (
            f"- Deletions: "
            f"{context.get('deletions', 0)}"
        ),
        (
            f"- Active findings: "
            f"{len(blocking) + len(advisory)}"
        ),
        (
            f"- Blocking: "
            f"{len(blocking)}"
        ),
        (
            f"- Advisory: "
            f"{len(advisory)}"
        ),
        (
            f"- Refuted: "
            f"{len(refuted)}"
        ),
        (
            f"- Not applicable: "
            f"{len(not_applicable)}"
        ),
        "",
        "## Reviewers",
        "",
    ]

    if selected_reviewers:
        for reviewer in selected_reviewers:
            reason = ""

            if isinstance(
                reviewer_reasons,
                dict,
            ):
                value = reviewer_reasons.get(
                    reviewer
                )

                if isinstance(
                    value,
                    str,
                ):
                    reason = value.strip()

            if reason:
                lines.append(
                    f"- `{reviewer}` — "
                    f"{reason}"
                )
            else:
                lines.append(
                    f"- `{reviewer}`"
                )
    else:
        lines.append(
            "No specialist reviewers selected."
        )

    lines.extend(
        [
            "",
            "## Risk Triggers",
            "",
        ]
    )

    if risk_triggers:
        for trigger in risk_triggers:
            lines.append(
                f"- `{trigger}`"
            )
    else:
        lines.append(
            "No specific risk triggers detected."
        )

    lines.extend(
        [
            "",
            *render_specialist_reviews(
                specialist_results
            ),
            "",
            "## Blocking Findings",
            "",
        ]
    )

    if blocking:
        for finding in blocking:
            lines.append(
                render_finding(
                    finding
                )
            )
            lines.append("")
    else:
        lines.append(
            "No verified blocking findings."
        )

    lines.extend(
        [
            "",
            "## Advisory Findings",
            "",
        ]
    )

    if advisory:
        for finding in advisory:
            lines.append(
                render_finding(
                    finding
                )
            )
            lines.append("")
    else:
        lines.append(
            "No advisory findings."
        )

    lines.extend(
        [
            "",
            "## Refuted Findings",
            "",
        ]
    )

    if refuted:
        for finding in refuted:
            lines.append(
                (
                    f"- `{finding.get('id', 'UNKNOWN')}` "
                    f"— {finding.get('title', '')}"
                )
            )
    else:
        lines.append(
            "No refuted findings."
        )

    lines.extend(
        [
            "",
            *render_verification(
                verification
            ),
            "",
            "## Execution Notes",
            "",
        ]
    )

    if specialist_failures:
        lines.append(
            "The review completed with partial "
            "specialist coverage."
        )

        for failure in specialist_failures:
            lines.append(
                (
                    f"- `{failure.get('specialist', 'UNKNOWN')}` "
                    f"failed: "
                    f"{failure.get('error', '')}"
                )
            )
    else:
        lines.append(
            "All selected specialists completed successfully."
        )

    lines.extend(
        [
            "",
            "## Review Result",
            "",
        ]
    )

    if blocking:
        lines.append(
            "The review contains verified blocking findings."
        )
    elif advisory:
        lines.append(
            "The review contains advisory findings but no verified "
            "blocking findings."
        )
    elif selected_reviewers:
        lines.append(
            "No active evidence-backed findings were produced by the "
            "selected specialist reviews."
        )
    else:
        lines.append(
            "No specialist review was executed because triage selected "
            "no specialist reviewers."
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "Generated by PR Guardian.",
        ]
    )

    return "\n".join(
        lines
    )


def write_report(
    reports_root: Path,
    pr_id: str,
    context: dict[str, Any],
    review_plan: dict[str, Any],
    style_review: dict[str, Any],
    summary: str,
    specialist_results: list[dict[str, Any]] | None = None,
    specialist_failures: list[dict[str, str]] | None = None,
) -> None:
    selected_reviewers = (
        review_plan.get(
            "selected_reviewers",
            [],
        )
    )

    if not isinstance(
        selected_reviewers,
        list,
    ):
        raise RuntimeError(
            "selected_reviewers must be a list."
        )

    if not all(
        isinstance(item, str)
        for item in selected_reviewers
    ):
        raise RuntimeError(
            "selected_reviewers must contain "
            "reviewer-name strings only."
        )

    failures = (
        specialist_failures
        or []
    )

    if specialist_results is None:
        results = load_specialist_results(
            reports_root
            / "findings"
            / pr_id,
            selected_reviewers,
            failures,
        )
    else:
        results = normalize_specialist_results(
            specialist_results,
            selected_reviewers,
        )

    failed_names = {
        failure.get(
            "specialist"
        )
        for failure in failures
        if isinstance(
            failure,
            dict,
        )
    }

    completed_names = {
        result[
            "specialist"
        ]
        for result in results
    }

    missing = [
        reviewer
        for reviewer in selected_reviewers
        if (
            reviewer not in completed_names
            and reviewer not in failed_names
        )
    ]

    if missing:
        raise RuntimeError(
            "Selected specialists have neither "
            "successful results nor recorded failures: "
            f"{missing}"
        )

    findings = flatten_findings(
        results
    )

    verification = load_verification(
        reports_root,
        pr_id,
    )

    findings = apply_verification(
        findings,
        verification,
    )

    findings = deduplicate_findings(
        findings
    )

    (
        blocking,
        advisory,
        refuted,
        not_applicable,
    ) = classify_findings(
        findings
    )

    verification_failed = sum(
        1
        for finding in findings
        if finding.get(
            "verification_status"
        )
        == "VERIFICATION_FAILED"
    )

    verified = sum(
        1
        for finding in findings
        if finding.get(
            "verification_status"
        )
        == "VERIFIED"
    )

    unverified = sum(
        1
        for finding in findings
        if finding.get(
            "verification_status"
        )
        == "UNVERIFIED"
    )

    review_status = (
        "PARTIAL"
        if failures
        else "COMPLETE"
    )

    specialist_reviews = [
        {
            "specialist": result[
                "specialist"
            ],
            "summary": result[
                "summary"
            ],
        }
        for result in results
    ]

    review_data: dict[
        str,
        Any,
    ] = {
        "pr_id": context.get(
            "pr_id"
        ),
        "repository": context.get(
            "repository_name",
            "",
        ),
        "title": context.get(
            "title",
            "",
        ),
        "risk_level": review_plan.get(
            "risk_level",
        ),
        "risk_triggers": review_plan.get(
            "risk_triggers",
            [],
        ),
        "selected_reviewers": (
            selected_reviewers
        ),
        "skipped_reviewers": (
            review_plan.get(
                "skipped_reviewers",
                [],
            )
        ),
        "reviewer_reasons": (
            review_plan.get(
                "reviewer_reasons",
                {},
            )
        ),
        "pr_summary": summary,
        "specialist_reviews": (
            specialist_reviews
        ),
        "summary": {
            "total_findings": len(
                findings
            ),
            "active_findings": (
                len(blocking)
                + len(advisory)
            ),
            "blocking": len(
                blocking
            ),
            "advisory": len(
                advisory
            ),
            "verified": verified,
            "unverified": unverified,
            "refuted": len(
                refuted
            ),
            "not_applicable": len(
                not_applicable
            ),
            "verification_failed": (
                verification_failed
            ),
        },
        "blocking": blocking,
        "advisory": advisory,
        "refuted": refuted,
        "not_applicable": (
            not_applicable
        ),
        "verification": (
            verification
            if verification
            is not None
            else {
                "summary": None,
                "results": [],
            }
        ),
        "supporting_evidence": {
            "python_conventions": (
                style_review
            ),
        },
        "execution": {
            "status": review_status,
            "executed_reviewers": [
                result[
                    "specialist"
                ]
                for result in results
            ],
            "specialist_failures": (
                failures
            ),
        },
    }

    review_dir = (
        reports_root
        / "reviews"
        / pr_id
    )

    review_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    _write_json(
        review_dir
        / "review.json",
        review_data,
    )

    markdown = build_report_markdown(
        context=context,
        review_plan=review_plan,
        findings=findings,
        specialist_results=results,
        specialist_failures=failures,
        verification=verification,
        summary=summary,
    )

    (
        review_dir
        / "review.md"
    ).write_text(
        markdown,
        encoding="utf-8",
    )

    manifest = {
        "pr_id": context.get(
            "pr_id"
        ),
        "operation": "review",
        "risk_level": (
            review_plan.get(
                "risk_level"
            )
        ),
        "selected_reviewers": (
            selected_reviewers
        ),
        "executed_reviewers": [
            result[
                "specialist"
            ]
            for result in results
        ],
        "skipped_reviewers": (
            review_plan.get(
                "skipped_reviewers",
                [],
            )
        ),
        "specialist_results": [
            {
                "specialist": (
                    result[
                        "specialist"
                    ]
                ),
                "finding_count": len(
                    result[
                        "findings"
                    ]
                ),
                "summary_present": True,
            }
            for result in results
        ],
        "specialist_failures": (
            failures
        ),
        "verification_used": (
            verification
            is not None
        ),
        "finding_counts": {
            "total": len(
                findings
            ),
            "blocking": len(
                blocking
            ),
            "advisory": len(
                advisory
            ),
            "refuted": len(
                refuted
            ),
            "not_applicable": len(
                not_applicable
            ),
        },
        "artifacts": {
            "review_json": str(
                review_dir
                / "review.json"
            ),
            "review_markdown": str(
                review_dir
                / "review.md"
            ),
        },
        "status": review_status,
    }

    _write_json(
        reports_root
        / "runs"
        / pr_id
        / "run-manifest.json",
        manifest,
    )

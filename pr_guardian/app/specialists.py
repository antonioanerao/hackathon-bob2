from __future__ import annotations

import re
from typing import Any

from .config import get_specialists
from .ollama_client import OllamaClient
from .prompts import global_rules, skill


SPECIALISTS = get_specialists()

VALID_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

EXPECTED_PREFIXES = {
    "code-review-specialist": "CODE",
    "security-review-specialist": "SEC",
    "database-review-specialist": "DB",
    "api-review-specialist": "API",
    "architecture-review-specialist": "ARCH",
    "async-review-specialist": "ASYNC",
}

REQUIRED_SUMMARY_FIELDS = (
    "analysis",
    "result",
    "implementation",
)

REQUIRED_FINDING_FIELDS = (
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


def _require_non_empty_string(
    value: Any,
    *,
    field_name: str,
    specialist: str,
) -> str:
    if not isinstance(value, str):
        raise RuntimeError(
            f"Invalid {field_name} returned by specialist "
            f"{specialist}: expected string."
        )

    value = value.strip()

    if not value:
        raise RuntimeError(
            f"Invalid {field_name} returned by specialist "
            f"{specialist}: value cannot be empty."
        )

    return value


def _validate_summary(
    summary: Any,
    *,
    specialist: str,
) -> dict[str, str]:
    if not isinstance(summary, dict):
        raise RuntimeError(
            f"Invalid summary returned by specialist "
            f"{specialist}: expected object."
        )

    normalized: dict[str, str] = {}

    for field_name in REQUIRED_SUMMARY_FIELDS:
        if field_name not in summary:
            raise RuntimeError(
                f"Missing summary.{field_name} returned by specialist "
                f"{specialist}."
            )

        normalized[field_name] = _require_non_empty_string(
            summary[field_name],
            field_name=f"summary.{field_name}",
            specialist=specialist,
        )

    return normalized


def _validate_finding_id(
    finding_id: Any,
    *,
    specialist: str,
) -> str:
    finding_id = _require_non_empty_string(
        finding_id,
        field_name="finding.id",
        specialist=specialist,
    )

    prefix = EXPECTED_PREFIXES.get(specialist)

    if prefix is None:
        raise RuntimeError(
            f"No finding ID prefix configured for specialist: "
            f"{specialist}"
        )

    pattern = rf"^{re.escape(prefix)}-\d{{3}}$"

    if not re.fullmatch(pattern, finding_id):
        raise RuntimeError(
            f"Invalid finding ID returned by specialist "
            f"{specialist}: {finding_id!r}. "
            f"Expected format {prefix}-001."
        )

    return finding_id


def _validate_finding(
    finding: Any,
    *,
    specialist: str,
) -> dict[str, Any]:
    if not isinstance(finding, dict):
        raise RuntimeError(
            f"Invalid finding returned by specialist "
            f"{specialist}: expected object."
        )

    missing = [
        field_name
        for field_name in REQUIRED_FINDING_FIELDS
        if field_name not in finding
    ]

    if missing:
        raise RuntimeError(
            f"Missing finding fields returned by specialist "
            f"{specialist}: {missing}"
        )

    finding_id = _validate_finding_id(
        finding["id"],
        specialist=specialist,
    )

    severity = _require_non_empty_string(
        finding["severity"],
        field_name=f"{finding_id}.severity",
        specialist=specialist,
    )

    if severity not in VALID_SEVERITIES:
        raise RuntimeError(
            f"Invalid severity returned by specialist "
            f"{specialist} for {finding_id}: "
            f"{severity!r}"
        )

    category = _require_non_empty_string(
        finding["category"],
        field_name=f"{finding_id}.category",
        specialist=specialist,
    )

    title = _require_non_empty_string(
        finding["title"],
        field_name=f"{finding_id}.title",
        specialist=specialist,
    )

    file_path = _require_non_empty_string(
        finding["file"],
        field_name=f"{finding_id}.file",
        specialist=specialist,
    )

    line = finding["line"]

    if (
        not isinstance(line, int)
        or isinstance(line, bool)
        or line < 1
    ):
        raise RuntimeError(
            f"Invalid line returned by specialist "
            f"{specialist} for {finding_id}: "
            f"expected positive integer."
        )

    evidence = _require_non_empty_string(
        finding["evidence"],
        field_name=f"{finding_id}.evidence",
        specialist=specialist,
    )

    impact = _require_non_empty_string(
        finding["impact"],
        field_name=f"{finding_id}.impact",
        specialist=specialist,
    )

    recommendation = _require_non_empty_string(
        finding["recommendation"],
        field_name=f"{finding_id}.recommendation",
        specialist=specialist,
    )

    verification_status = _require_non_empty_string(
        finding["verification_status"],
        field_name=f"{finding_id}.verification_status",
        specialist=specialist,
    )

    if verification_status != "UNVERIFIED":
        raise RuntimeError(
            f"Invalid verification_status returned by specialist "
            f"{specialist} for {finding_id}: "
            f"{verification_status!r}. "
            "Specialists must return UNVERIFIED."
        )

    return {
        "id": finding_id,
        "severity": severity,
        "category": category,
        "title": title,
        "file": file_path,
        "line": line,
        "evidence": evidence,
        "impact": impact,
        "recommendation": recommendation,
        "verification_status": verification_status,
    }


def _validate_findings(
    findings: Any,
    *,
    specialist: str,
) -> list[dict[str, Any]]:
    if not isinstance(findings, list):
        raise RuntimeError(
            f"Invalid findings returned by specialist "
            f"{specialist}: expected list."
        )

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for finding in findings:
        validated = _validate_finding(
            finding,
            specialist=specialist,
        )

        finding_id = validated["id"]

        if finding_id in seen_ids:
            raise RuntimeError(
                f"Duplicate finding ID returned by specialist "
                f"{specialist}: {finding_id}"
            )

        seen_ids.add(finding_id)
        normalized.append(validated)

    return normalized


def run_specialist(
    specialist: str,
    context: dict[str, Any],
    diff: str,
    model: str,
) -> dict[str, Any]:

    if specialist not in SPECIALISTS:
        raise RuntimeError(
            f"Unknown specialist: {specialist}"
        )

    skill_name = SPECIALISTS[specialist]

    client = OllamaClient(
        model=model
    )

    system = f"""
You are the PR Guardian specialist:

{specialist}

Follow these global rules:

{global_rules()}

Follow this specialist skill:

{skill(skill_name)}

Review only the supplied Pull Request changes and the directly relevant
context provided to you.

Your job is to:

- perform only your specialist review
- produce one concise specialist summary
- emit only evidence-backed canonical findings
- return JSON only

The summary is part of your specialist result and will be rendered directly
into the final PR Guardian report.

The summary MUST contain exactly these semantic fields:

- analysis
- result
- implementation

Summary rules:

- analysis: explain what you actually reviewed
- result: explain what the review concluded and its practical impact
- implementation: explain where the reviewed behavior is implemented
- use only evidence you actually inspected
- do not invent files, symbols, routes, models, behavior, findings, or impact
- do not claim tests, execution, verification, scanner results, or runtime
  behavior that did not occur
- do not duplicate the full findings list in the summary

All findings produced by this specialist MUST use:

"verification_status": "UNVERIFIED"

Do not invent:

- files
- lines
- symbols
- behavior
- vulnerabilities
- dependencies
- runtime evidence
- test results
- scanner results
- verification results
"""

    prompt = f"""
Review this Pull Request.

PR CONTEXT:

{context}

CHANGED CODE:

{diff}

Return JSON only.

Return exactly this top-level structure:

{{
  "specialist": "{specialist}",
  "summary": {{
    "analysis": "What you actually reviewed.",
    "result": "What the review concluded and the practical impact observed.",
    "implementation": "Where the reviewed behavior is implemented."
  }},
  "findings": [
    {{
      "id": "PREFIX-001",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "category": "CATEGORY",
      "title": "Short title",
      "file": "path/to/file",
      "line": 1,
      "evidence": "Concrete evidence",
      "impact": "Practical impact",
      "recommendation": "Actionable recommendation",
      "verification_status": "UNVERIFIED"
    }}
  ]
}}

The actual finding ID prefix is defined by the specialist skill.

If no concrete findings exist, you MUST still return the specialist summary:

{{
  "specialist": "{specialist}",
  "summary": {{
    "analysis": "What you actually reviewed.",
    "result": "No evidence-backed defect was identified within the reviewed scope.",
    "implementation": "Where the reviewed behavior is implemented."
  }},
  "findings": []
}}

Do not omit the summary when findings is empty.

Do not return reviewer objects, Markdown, commentary, explanations outside the
JSON object, or model-selected artifact paths.
"""

    result = client.chat_json(
        system=system,
        prompt=prompt,
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            f"Invalid response from specialist: "
            f"{specialist}"
        )

    returned_specialist = result.get(
        "specialist"
    )

    if returned_specialist != specialist:
        raise RuntimeError(
            f"Specialist identity mismatch: expected "
            f"{specialist!r}, received "
            f"{returned_specialist!r}."
        )

    summary = _validate_summary(
        result.get("summary"),
        specialist=specialist,
    )

    findings = _validate_findings(
        result.get("findings"),
        specialist=specialist,
    )

    return {
        "specialist": specialist,
        "summary": summary,
        "findings": findings,
    }
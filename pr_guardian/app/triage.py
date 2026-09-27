from __future__ import annotations

from typing import Any

from .config import get_specialists
from .ollama_client import OllamaClient
from .prompts import global_rules, skill


ALLOWED_REVIEWERS = set(
    get_specialists().keys()
)

VALID_RISK_LEVELS = {
    "TRIVIAL",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

EXECUTION_PLANNING = {
    "TRIVIAL": {
        "expected_reviewers": 0,
        "max_verifiers": 0,
    },
    "LOW": {
        "expected_reviewers": 1,
        "max_verifiers": 0,
    },
    "MEDIUM": {
        "expected_reviewers": 2,
        "max_verifiers": 1,
    },
    "HIGH": {
        "expected_reviewers": 3,
        "max_verifiers": 1,
    },
    "CRITICAL": {
        "expected_reviewers": 4,
        "max_verifiers": 1,
    },
}


def _normalize_reviewers(
    value: Any,
    *,
    field_name: str,
) -> tuple[list[str], dict[str, str]]:
    if value is None:
        return [], {}

    if not isinstance(value, list):
        raise RuntimeError(
            f"Invalid {field_name}: expected a list."
        )

    reviewers: list[str] = []
    reasons: dict[str, str] = {}

    for item in value:
        reviewer: str
        reason = ""

        if isinstance(item, str):
            reviewer = item.strip()

        elif isinstance(item, dict):
            reviewer_value = item.get("reviewer")
            reason_value = item.get("reason", "")

            if not isinstance(reviewer_value, str):
                raise RuntimeError(
                    f"Invalid reviewer entry in {field_name}: {item!r}"
                )

            reviewer = reviewer_value.strip()

            if reason_value is None:
                reason_value = ""

            if not isinstance(reason_value, str):
                raise RuntimeError(
                    f"Invalid reviewer reason in {field_name}: {item!r}"
                )

            reason = reason_value.strip()

        else:
            raise RuntimeError(
                f"Invalid reviewer entry in {field_name}: {item!r}"
            )

        if not reviewer:
            raise RuntimeError(
                f"Empty reviewer in {field_name}."
            )

        if reviewer not in ALLOWED_REVIEWERS:
            raise RuntimeError(
                f"Invalid reviewer returned by model: {reviewer}"
            )

        if reviewer not in reviewers:
            reviewers.append(reviewer)

        if reason:
            reasons[reviewer] = reason

    return reviewers, reasons


def _normalize_string_list(
    value: Any,
    *,
    field_name: str,
) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise RuntimeError(
            f"Invalid {field_name}: expected a list."
        )

    normalized: list[str] = []

    for item in value:
        if not isinstance(item, str):
            raise RuntimeError(
                f"Invalid value in {field_name}: expected strings only."
            )

        item = item.strip()

        if item and item not in normalized:
            normalized.append(item)

    return normalized


def run_triage(
    context: dict[str, Any],
    model: str,
) -> dict[str, Any]:

    client = OllamaClient(
        model=model
    )

    reviewer_list = sorted(
        ALLOWED_REVIEWERS
    )

    system = f"""
You are PR Guardian pr-triage.

Global rules:

{global_rules()}

Triage skill:

{skill("pr-triage")}

Your responsibility is only:

- understand the change
- determine risk
- identify risk triggers
- select every materially relevant reviewer
- explain reviewer selection

Do not perform specialist review.

Do not create findings.

Do not define a hard reviewer-count budget.

Reviewer selection is domain-driven.

If multiple specialist domains are materially affected,
select all relevant reviewers.

Return JSON only.
"""

    prompt = f"""
Analyze this Pull Request context:

{context}

Return JSON only.

Available specialist reviewers:

{reviewer_list}

The field "selected_reviewers" MUST contain only reviewer-name strings
from this exact list.

The field "skipped_reviewers" MUST also contain only reviewer-name strings
from this exact list.

Use "reviewer_reasons" for concise reviewer-selection explanations.

Never return:

- usernames
- GitHub handles
- developer names
- arbitrary reviewer names
- reviewer objects inside selected_reviewers
- reviewer objects inside skipped_reviewers
- agent_budget
- max_reviewers

Important routing rules:

- Select every specialist that is materially relevant to the PR.
- Do not omit a relevant reviewer merely because another reviewer
  was already selected.
- Do not limit reviewer count based only on risk level.
- A LOW or MEDIUM PR may still require multiple reviewers when
  multiple review domains are genuinely affected.
- TRIVIAL is allowed only for demonstrably non-behavioral changes.
- If executable source code changes and behavior may be affected,
  the minimum risk level is LOW.
- Do not perform specialist review.
- Do not create findings.

Return exactly this schema:

{{
  "risk_level": "TRIVIAL|LOW|MEDIUM|HIGH|CRITICAL",
  "risk_triggers": [],
  "selected_reviewers": [],
  "skipped_reviewers": [],
  "reviewer_reasons": {{}}
}}
"""

    result = client.chat_json(
        system=system,
        prompt=prompt,
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            "Invalid triage response: expected JSON object."
        )

    risk_level = result.get(
        "risk_level"
    )

    if risk_level not in VALID_RISK_LEVELS:
        raise RuntimeError(
            f"Invalid risk_level returned by model: {risk_level!r}"
        )

    selected, selected_reasons = _normalize_reviewers(
        result.get(
            "selected_reviewers",
            [],
        ),
        field_name="selected_reviewers",
    )

    skipped, skipped_reasons = _normalize_reviewers(
        result.get(
            "skipped_reviewers",
            [],
        ),
        field_name="skipped_reviewers",
    )

    overlap = (
        set(selected)
        & set(skipped)
    )

    if overlap:
        raise RuntimeError(
            "Reviewer cannot be both selected and skipped: "
            f"{sorted(overlap)}"
        )

    reviewer_reasons = result.get(
        "reviewer_reasons",
        {},
    )

    if reviewer_reasons is None:
        reviewer_reasons = {}

    if not isinstance(
        reviewer_reasons,
        dict,
    ):
        raise RuntimeError(
            "Invalid reviewer_reasons: expected an object."
        )

    normalized_reasons: dict[str, str] = {}

    for reviewer, reason in reviewer_reasons.items():
        if reviewer not in ALLOWED_REVIEWERS:
            continue

        if isinstance(reason, str):
            reason = reason.strip()

            if reason:
                normalized_reasons[
                    reviewer
                ] = reason

    normalized_reasons.update(
        skipped_reasons
    )

    normalized_reasons.update(
        selected_reasons
    )

    risk_triggers = _normalize_string_list(
        result.get(
            "risk_triggers",
            [],
        ),
        field_name="risk_triggers",
    )

    execution_planning = EXECUTION_PLANNING[
        risk_level
    ]

    return {
        "risk_level": risk_level,
        "risk_triggers": risk_triggers,
        "selected_reviewers": selected,
        "skipped_reviewers": skipped,
        "reviewer_reasons": normalized_reasons,
        "execution_planning": execution_planning,
    }
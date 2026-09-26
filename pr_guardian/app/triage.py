from __future__ import annotations

from typing import Any

from .config import get_specialists
from .ollama_client import OllamaClient
from .prompts import global_rules, skill


ALLOWED_REVIEWERS = set(
    get_specialists().keys()
)


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
- select reviewers
- define agent budget

Do not perform specialist review.

Return JSON only.
"""

    prompt = f"""
Analyze this Pull Request context:

{context}

Return JSON only.

The field "selected_reviewers" MUST contain only values
from this exact list:

{reviewer_list}

The field "skipped_reviewers" MUST also contain only values
from that same list.

Never return:
- usernames
- GitHub handles
- developer names
- arbitrary reviewer names

Return exactly:

{{
  "risk_level": "TRIVIAL|LOW|MEDIUM|HIGH|CRITICAL",
  "agent_budget": {{
    "max_reviewers": 0,
    "max_verifiers": 0
  }},
  "risk_triggers": [],
  "selected_reviewers": [],
  "skipped_reviewers": []
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

    selected = result.get(
        "selected_reviewers",
        [],
    )

    skipped = result.get(
        "skipped_reviewers",
        [],
    )

    if not isinstance(selected, list):
        raise RuntimeError(
            "Invalid selected_reviewers: expected a list."
        )

    if not isinstance(skipped, list):
        raise RuntimeError(
            "Invalid skipped_reviewers: expected a list."
        )

    invalid_selected = [
        reviewer
        for reviewer in selected
        if reviewer not in ALLOWED_REVIEWERS
    ]

    if invalid_selected:
        raise RuntimeError(
            "Invalid reviewers returned by model: "
            f"{invalid_selected}"
        )

    invalid_skipped = [
        reviewer
        for reviewer in skipped
        if reviewer not in ALLOWED_REVIEWERS
    ]

    if invalid_skipped:
        raise RuntimeError(
            "Invalid skipped reviewers returned by model: "
            f"{invalid_skipped}"
        )

    result["selected_reviewers"] = selected
    result["skipped_reviewers"] = skipped

    return result
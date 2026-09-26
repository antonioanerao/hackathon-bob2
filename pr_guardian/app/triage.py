from __future__ import annotations

from typing import Any

from .ollama_client import OllamaClient
from .prompts import global_rules, skill


ALLOWED_REVIEWERS = {
    "code-review-specialist",
    "security-review-specialist",
    "database-review-specialist",
    "api-review-specialist",
    "async-review-specialist",
    "architecture-review-specialist",
}


def run_triage(
    context: dict[str, Any],
    model: str,
) -> dict[str, Any]:

    client = OllamaClient(model=model)

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

The field "selected_reviewers" MUST contain only values from this exact list:

[
  "code-review-specialist",
  "security-review-specialist",
  "database-review-specialist",
  "api-review-specialist",
  "async-review-specialist",
  "architecture-review-specialist"
]

The field "skipped_reviewers" MUST also contain only values from that same list.

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

    selected = result.get(
        "selected_reviewers",
        [],
    )

    invalid = [
        reviewer
        for reviewer in selected
        if reviewer not in ALLOWED_REVIEWERS
    ]

    if invalid:
        raise RuntimeError(
            f"Invalid reviewers returned by model: {invalid}"
        )

    skipped = result.get(
        "skipped_reviewers",
        [],
    )

    invalid_skipped = [
        reviewer
        for reviewer in skipped
        if reviewer not in ALLOWED_REVIEWERS
    ]

    if invalid_skipped:
        raise RuntimeError(
            f"Invalid skipped reviewers returned by model: "
            f"{invalid_skipped}"
        )

    return result
from __future__ import annotations

from typing import Any

from .config import get_specialists
from .ollama_client import OllamaClient
from .prompts import global_rules, skill


SPECIALISTS = get_specialists()


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

Review only the supplied PR changes.

Return JSON only.

Do not invent:
- files
- lines
- behavior
- vulnerabilities
- dependencies
- runtime evidence
"""

    prompt = f"""
Review this Pull Request.

PR CONTEXT:

{context}

CHANGED CODE:

{diff}

Return JSON only in this format:

{{
  "specialist": "{specialist}",
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

If no concrete findings exist, return:

{{
  "specialist": "{specialist}",
  "findings": []
}}
"""

    result = client.chat_json(
        system=system,
        prompt=prompt,
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            f"Invalid response from specialist: {specialist}"
        )

    findings = result.get("findings", [])

    if not isinstance(findings, list):
        raise RuntimeError(
            f"Invalid findings returned by specialist: {specialist}"
        )

    result["specialist"] = specialist
    result["findings"] = findings

    return result
from __future__ import annotations

from typing import Any

from .ollama_client import OllamaClient
from .prompts import global_rules, skill


SPECIALISTS = {
    "code-review-specialist": "code-review",
    "security-review-specialist": "security-review",
    "database-review-specialist": "database-review",
    "api-review-specialist": "api-review",
    "architecture-review-specialist": "architecture-review",
    "async-review-specialist": "queue-review",
}


def run_specialist(
    specialist: str,
    context: dict[str, Any],
    diff: str,
    model: str,
) -> dict[str, Any]:

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

You review only the supplied PR changes.

Return JSON only.

Do not invent files, lines, behavior, vulnerabilities,
dependencies, or runtime evidence.
"""

    prompt = f"""
Review this Pull Request.

PR CONTEXT:

{context}

CHANGED CODE:

{diff}

Return:

{{
  "specialist": "{specialist}",
  "findings": [
    {{
      "id": "CODE-001",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "category": "CATEGORY",
      "title": "Short title",
      "file": "path/file.py",
      "line": 1,
      "evidence": "Concrete evidence",
      "impact": "Practical impact",
      "recommendation": "Actionable recommendation",
      "verification_status": "UNVERIFIED"
    }}
  ]
}}

If there are no concrete defects:

{{
  "specialist": "{specialist}",
  "findings": []
}}
"""

    return client.chat_json(
        system=system,
        prompt=prompt,
    )
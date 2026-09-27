from __future__ import annotations

from typing import Any

from .ollama_client import OllamaClient


def generate_pr_summary(
    context: dict[str, Any],
    diff: str,
    model: str,
) -> str:
    client = OllamaClient(model=model)
    system = """
You summarize pull request changes for a review report.
Describe what changed and why in 2 to 4 short sentences.
Use the same language as the PR title and description.
Base every claim on the supplied PR metadata and diff.
If the reason for the change is not stated, say so without guessing.
Do not claim that the code works, tests pass, or requirements are met.
Do not perform code review or list findings.
Return JSON only with one string field named "summary".
"""
    prompt = f"""
PR title: {context.get('title', '')}
PR description: {context.get('body_preview', '')}
Changed files: {context.get('changed_files', [])}

PR diff:
{diff}

Return exactly this JSON shape:
{{"summary": "2 to 4 short sentences grounded in the PR"}}
"""
    result = client.chat_json(system=system, prompt=prompt)
    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise RuntimeError("Invalid PR summary: expected non-empty text")

    summary = " ".join(summary.split())
    if len(summary) > 1200:
        raise RuntimeError("Invalid PR summary: text is too long")
    return summary

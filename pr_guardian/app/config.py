from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


def get_specialists() -> dict[str, str]:
    raw = os.getenv(
        "PR_GUARDIAN_SPECIALISTS",
        "",
    ).strip()

    if not raw:
        return {}

    specialists: dict[str, str] = {}

    for item in raw.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            reviewer, skill = item.split(
                ":",
                1,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid specialist entry: {item}"
            ) from exc

        reviewer = reviewer.strip()
        skill = skill.strip()

        if not reviewer or not skill:
            raise RuntimeError(
                f"Invalid specialist entry: {item}"
            )

        specialists[reviewer] = skill

    return specialists
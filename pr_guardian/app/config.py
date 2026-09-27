from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

SKILLS_DIR = Path(__file__).resolve().parent.parent / ".bob" / "skills"


def _reviewer_id(skill_file: Path) -> str | None:
    with skill_file.open(encoding="utf-8") as file:
        first_line = next(file, "").strip()
        if first_line == "````":
            first_line = next(file, "").strip()
        if first_line != "---":
            return None

        for line in file:
            if line.strip() == "---":
                break

            key, separator, value = line.partition(":")
            if separator and key.strip() == "reviewer_id":
                reviewer = value.strip()
                if not reviewer:
                    raise RuntimeError(f"Empty reviewer_id in {skill_file}")
                return reviewer

    return None


def get_specialists() -> dict[str, str]:
    specialists: dict[str, str] = {}

    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        reviewer = _reviewer_id(skill_file)
        if reviewer is None:
            continue

        if reviewer in specialists:
            raise RuntimeError(
                f"Duplicate reviewer_id {reviewer!r} in {skill_file}"
            )

        specialists[reviewer] = skill_file.parent.name

    disabled = {
        reviewer.strip()
        for reviewer in os.getenv("PR_GUARDIAN_DISABLED_SPECIALISTS", "").split(",")
        if reviewer.strip()
    }
    unknown = disabled - specialists.keys()
    if unknown:
        raise RuntimeError(
            "Unknown disabled specialist(s): " + ", ".join(sorted(unknown))
        )

    return {
        reviewer: skill_name
        for reviewer, skill_name in specialists.items()
        if reviewer not in disabled
    }
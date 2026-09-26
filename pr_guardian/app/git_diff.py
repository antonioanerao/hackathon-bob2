from __future__ import annotations

import os

import requests


def get_pr_diff(
    owner: str,
    repo: str,
    pr_number: int,
) -> str:

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/pulls/{pr_number}"
    )

    headers = {
        "Accept": "application/vnd.github.v3.diff",
    }

    token = os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(
        url,
        headers=headers,
        timeout=120,
    )

    if not response.ok:
        raise RuntimeError(
            f"GitHub diff error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    return response.text
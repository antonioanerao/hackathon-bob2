from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
from ast import literal_eval
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def changed_python_lines(diff: str) -> dict[str, set[int]]:
    changed: dict[str, set[int]] = defaultdict(set)
    path: str | None = None
    line_number: int | None = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path = None
            line_number = None
        elif line.startswith("+++ "):
            target = line[4:]
            if target.startswith('"'):
                try:
                    target = literal_eval(target)
                except (SyntaxError, ValueError):
                    target = ""
            path = (
                target[2:]
                if target.startswith("b/") and target.endswith(".py")
                else None
            )
            if path:
                changed[path]
            line_number = None
        elif line.startswith("@@ "):
            match = HUNK_HEADER.match(line)
            line_number = int(match.group(1)) if match and path else None
        elif path and line_number is not None:
            if line.startswith("+"):
                changed[path].add(line_number)
                line_number += 1
            elif line.startswith(" "):
                line_number += 1

    return dict(changed)


def get_python_source(owner: str, repo: str, path: str, head_sha: str) -> str:
    encoded_path = quote(path, safe="/")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(
        url,
        headers=headers,
        params={"ref": head_sha},
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(
            f"GitHub source error for {path} ({response.status_code})"
        )

    data = response.json()
    if data.get("encoding") != "base64" or not data.get("content"):
        raise RuntimeError(f"GitHub did not return Python source for {path}")

    encoded = "".join(data["content"].split())
    return base64.b64decode(encoded, validate=True).decode("utf-8")


def lint_python_source(path: str, source: str) -> list[dict[str, Any]]:
    venv_executable = Path(sys.executable).with_name("ruff")
    executable = (
        str(venv_executable)
        if venv_executable.exists()
        else shutil.which("ruff")
    )
    if executable is None:
        raise RuntimeError(
            "Ruff is required. Install pr_guardian/requirements.txt."
        )

    result = subprocess.run(
        [
            executable,
            "check",
            "--isolated",
            "--no-cache",
            "--select",
            "E,W,N",
            "--line-length",
            "79",
            "--output-format",
            "json",
            "--stdin-filename",
            path,
            "-",
        ],
        input=source,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Ruff failed for {path}: {result.stderr.strip()}")

    diagnostics = json.loads(result.stdout)
    if not isinstance(diagnostics, list):
        raise RuntimeError(f"Ruff returned invalid diagnostics for {path}")
    return diagnostics


def review_python_style(context: dict[str, Any], diff: str) -> dict[str, Any]:
    changed = changed_python_lines(diff)
    expected_paths = {
        item["path"]
        for item in context["changed_files"]
        if item["path"].endswith(".py") and item["status"] != "removed"
    }
    if set(changed) != expected_paths:
        raise RuntimeError(
            "Python files in PR diff differ from collected context"
        )

    owner, repo = context["repository_name"].split("/", 1)
    findings = []
    for path in sorted(changed):
        source = get_python_source(owner, repo, path, context["head_sha"])
        for diagnostic in lint_python_source(path, source):
            line = diagnostic["location"]["row"]
            if line in changed[path]:
                findings.append(
                    {
                        "file": path,
                        "line": line,
                        "code": diagnostic["code"],
                        "message": diagnostic["message"],
                    }
                )

    return {"checked_files": len(changed), "findings": findings}

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read_file(path: str) -> str:
    file = ROOT / path

    if not file.exists():
        return ""

    return file.read_text(
        encoding="utf-8"
    )


def global_rules() -> str:
    return read_file(
        ".bob/rules-agent/global-rules.md"
    )


def orchestrator_rules() -> str:
    return read_file(
        ".bob/rules-pr-guardian-orchestrator/"
        "orchestrator-rules.md"
    )


def skill(name: str) -> str:
    return read_file(
        f".bob/skills/{name}/SKILL.md"
    )
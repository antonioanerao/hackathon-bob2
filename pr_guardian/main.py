import os

from dotenv import load_dotenv

from app.orchestrator import run


load_dotenv()


def main():
    pr_ref = os.getenv("PR_URL")
    model = os.getenv("OLLAMA_MODEL")

    if not pr_ref:
        raise RuntimeError(
            "PR_URL environment variable is required."
        )

    if not model:
        raise RuntimeError(
            "OLLAMA_MODEL environment variable is required."
        )

    run(
        pr_ref=pr_ref,
        model=model,
    )


if __name__ == "__main__":
    main()
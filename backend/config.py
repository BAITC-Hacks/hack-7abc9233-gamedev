from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_environment() -> None:
    """Load local settings without replacing deployment environment variables."""
    load_dotenv(ENV_PATH, override=False)

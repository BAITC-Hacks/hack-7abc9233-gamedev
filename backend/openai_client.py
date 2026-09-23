"""Optional client factory for the ranking/explanation integration."""

import os

from openai import OpenAI

from .config import load_environment


def create_openai_client() -> OpenAI:
    """Create a client without making a request; caller owns its lifecycle."""
    load_environment()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY in the environment or local .env file")
    return OpenAI(api_key=key, timeout=8.0, max_retries=0)

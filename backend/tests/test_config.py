import os

import pytest

from backend import config
from backend.openai_client import create_openai_client


def test_dotenv_is_loaded_and_environment_has_priority(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("OPENAI_API_KEY=test-local-key\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_PATH", path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config.load_environment()
    assert os.environ["OPENAI_API_KEY"] == "test-local-key"
    monkeypatch.setenv("OPENAI_API_KEY", "test-deployment-key")
    with create_openai_client() as client:
        assert client.api_key == "test-deployment-key"


def test_missing_key_fails_without_network(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ENV_PATH", tmp_path / "missing.env")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(RuntimeError, match="Set OPENAI_API_KEY"):
        create_openai_client()

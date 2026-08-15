from pathlib import Path

import pytest

from agentic_workflow.core.config import ChromaDBConfig, DatabaseConfig, OllamaConfig


def test_canonical_database_names_take_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "canonical_user")
    monkeypatch.setenv("PGUSER", "legacy_user")
    monkeypatch.setenv("POSTGRES_PORT", "5544")

    settings = DatabaseConfig()

    assert settings.user == "canonical_user"
    assert settings.port == 5544
    assert settings.password == ""
    assert "default_transaction_read_only=on" in str(settings.connect_args["options"])


def test_empty_chroma_path_uses_repository_anchor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHROMA_PATH", "")
    monkeypatch.setenv("CHROMA_DB_PATH", "")

    settings = ChromaDBConfig()

    assert Path(settings.db_path).is_absolute()
    assert Path(settings.db_path).name == "chroma_db"


def test_ollama_url_rejects_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="credentials"):
        OllamaConfig(base_url="http://user:secret@localhost:11434")


def test_model_tags_have_no_unverified_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_CHAT_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_EMBED_MODEL", raising=False)

    settings = OllamaConfig()

    assert settings.general_model == ""
    assert settings.embedding_model == ""


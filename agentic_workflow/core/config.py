"""
Configuration settings for the Agentic AI RAG Workflow System.
Contains database connections, model configurations, and system settings.
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)


def _env(primary: str, *aliases: str, default: str = "") -> str:
    """Read a canonical environment variable with safe legacy aliases."""
    for name in (primary, *aliases):
        value = os.environ.get(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _safe_http_url(value: str, setting_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{setting_name} must be an http(s) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(
            f"{setting_name} must not contain credentials, a query, or a fragment"
        )
    return value.rstrip("/")


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    user: str = field(
        default_factory=lambda: _env("POSTGRES_USER", "PGUSER", default="postgres")
    )
    password: str = field(
        default_factory=lambda: _env("POSTGRES_PASSWORD", "PGPASSWORD")
    )
    host: str = field(
        default_factory=lambda: _env("POSTGRES_HOST", "PGHOST", default="localhost")
    )
    port: int = field(
        default_factory=lambda: int(_env("POSTGRES_PORT", "PGPORT", default="5432"))
    )
    name: str = field(
        default_factory=lambda: _env("POSTGRES_DB", "PGDATABASE", default="argo_data")
    )
    connect_timeout_seconds: int = field(
        default_factory=lambda: int(_env("POSTGRES_CONNECT_TIMEOUT", default="5"))
    )
    statement_timeout_ms: int = field(
        default_factory=lambda: int(
            _env("POSTGRES_STATEMENT_TIMEOUT_MS", default="15000")
        )
    )

    @property
    def connection_string(self) -> str:
        return (
            f"postgresql+psycopg2://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{quote_plus(self.name)}"
        )

    @property
    def connect_args(self) -> Dict[str, object]:
        """Driver options enforcing bounded, read-only database sessions."""
        return {
            "connect_timeout": self.connect_timeout_seconds,
            "options": (
                "-c default_transaction_read_only=on "
                f"-c statement_timeout={self.statement_timeout_ms}"
            ),
        }


@dataclass
class ChromaDBConfig:
    """ChromaDB vector store configuration."""
    db_path: str = field(default_factory=lambda: _env(
        "CHROMA_PATH", "CHROMA_DB_PATH", default=str(PROJECT_ROOT / "chroma_db")
    ))
    collection_name: str = field(default_factory=lambda: _env(
        "CHROMA_COLLECTION", "CHROMA_COLLECTION_NAME", default="argo_profiles_ollama"
    ))

    def __post_init__(self) -> None:
        path = Path(self.db_path).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        self.db_path = str(path.resolve())


@dataclass
class OllamaConfig:
    """Ollama configuration; model tags must be explicitly selected."""
    base_url: str = field(
        default_factory=lambda: _env(
            "OLLAMA_BASE_URL", default="http://localhost:11434"
        )
    )
    embedding_model: str = field(
        default_factory=lambda: _env("OLLAMA_EMBED_MODEL")
    )
    general_model: str = field(default_factory=lambda: _env("OLLAMA_CHAT_MODEL"))

    def __post_init__(self) -> None:
        self.base_url = _safe_http_url(self.base_url, "OLLAMA_BASE_URL")

    @property
    def generate_url(self) -> str:
        return f"{self.base_url}/api/generate"

    @property
    def embeddings_url(self) -> str:
        return f"{self.base_url}/api/embeddings"


@dataclass
class SystemConfig:
    """System-wide configuration settings."""
    max_context_length: int = 2000
    max_retrieval_results: int = 10
    temperature: float = 0.1
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    enable_xai_logging: bool = False

    # Geographic regions for ARGO data analysis
    regions: Dict[str, Dict[str, float]] = None

    def __post_init__(self):
        if self.regions is None:
            self.regions = {
                "Bay of Bengal": {
                    "lat_min": 5.0, "lat_max": 25.0,
                    "lon_min": 80.0, "lon_max": 100.0
                },
                "Arabian Sea": {
                    "lat_min": 5.0, "lat_max": 25.0,
                    "lon_min": 60.0, "lon_max": 80.0
                },
                "Indian Ocean": {
                    "lat_min": -60.0, "lat_max": 30.0,
                    "lon_min": 20.0, "lon_max": 120.0
                },
                "Southern Ocean": {
                    "lat_min": -80.0, "lat_max": -40.0,
                    "lon_min": -180.0, "lon_max": 180.0
                }
            }


class Config:
    """Main configuration class that combines all config components."""

    def __init__(self):
        self.database = DatabaseConfig()
        self.chromadb = ChromaDBConfig()
        self.ollama = OllamaConfig()
        self.system = SystemConfig()

    def get_region_bounds(self, region_name: str) -> Optional[Dict[str, float]]:
        """Get geographic bounds for a named region."""
        return self.system.regions.get(region_name)

    def validate_connections(self) -> Dict[str, bool]:
        """Validate that all required services are accessible."""
        results = {
            "postgresql": False,
            "chromadb": False,
            "ollama": False
        }

        # Test PostgreSQL connection
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(
                self.database.connection_string,
                connect_args=self.database.connect_args,
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results["postgresql"] = True
        except Exception as e:
            logger.warning("PostgreSQL health check failed (%s)", type(e).__name__)

        # Test ChromaDB connection
        try:
            import chromadb
            client = chromadb.PersistentClient(path=self.chromadb.db_path)
            client.get_collection(name=self.chromadb.collection_name)
            results["chromadb"] = True
        except Exception as e:
            logger.warning("ChromaDB health check failed (%s)", type(e).__name__)

        # Test Ollama connection
        try:
            import requests
            response = requests.get(f"{self.ollama.base_url}/api/tags", timeout=5)
            results["ollama"] = response.status_code == 200
        except Exception as e:
            logger.warning("Ollama health check failed (%s)", type(e).__name__)

        return results


# Global configuration instance
config = Config()

# Export commonly used configurations
DATABASE_CONFIG = config.database
CHROMADB_CONFIG = config.chromadb
OLLAMA_CONFIG = config.ollama
SYSTEM_CONFIG = config.system

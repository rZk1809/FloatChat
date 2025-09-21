"""
Configuration settings for the Agentic AI RAG Workflow System.
Contains database connections, model configurations, and system settings.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    user: str = "rgk"
    password: str = "rgk"
    host: str = "localhost"
    port: str = "5432"
    name: str = "argo_data"
    
    @property
    def connection_string(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass
class ChromaDBConfig:
    """ChromaDB vector store configuration."""
    db_path: str = "../chroma_db"
    collection_name: str = "argo_profiles_ollama"
    
@dataclass
class OllamaConfig:
    """Ollama model configuration."""
    base_url: str = "http://localhost:11434"
    embedding_model: str = "embeddinggemma:300m"
    general_model: str = "qwen2:1.5b"
    
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
    log_level: str = "INFO"
    enable_xai_logging: bool = True
    
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
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for the application."""
        logging.basicConfig(
            level=getattr(logging, self.system.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('agentic_workflow.log')
            ]
        )
    
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
            engine = create_engine(self.database.connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results["postgresql"] = True
        except Exception as e:
            logging.error(f"PostgreSQL connection failed: {e}")
        
        # Test ChromaDB connection
        try:
            import chromadb
            client = chromadb.PersistentClient(path=self.chromadb.db_path)
            collection = client.get_collection(name=self.chromadb.collection_name)
            results["chromadb"] = True
        except Exception as e:
            logging.error(f"ChromaDB connection failed: {e}")
        
        # Test Ollama connection
        try:
            import requests
            response = requests.get(f"{self.ollama.base_url}/api/tags", timeout=5)
            results["ollama"] = response.status_code == 200
        except Exception as e:
            logging.error(f"Ollama connection failed: {e}")
        
        return results

# Global configuration instance
config = Config()

# Export commonly used configurations
DATABASE_CONFIG = config.database
CHROMADB_CONFIG = config.chromadb
OLLAMA_CONFIG = config.ollama
SYSTEM_CONFIG = config.system

"""
ChromaDB Vector Retrieval Tool for ARGO float profile data.
Provides semantic search capabilities over ARGO profile summaries.
"""

import logging
import chromadb
from typing import List, Dict, Any, Optional
from ..core.config import CHROMADB_CONFIG, OLLAMA_CONFIG, SYSTEM_CONFIG
import requests
import json

logger = logging.getLogger(__name__)

class RetrieverTool:
    """Tool for retrieving relevant ARGO profiles using vector similarity search."""

    def __init__(self):
        self.client = None
        self.collection = None

    def _get_collection(self):
        """Open the configured collection on first use, never on import/init."""
        if self.collection is not None:
            return self.collection
        if not OLLAMA_CONFIG.embedding_model:
            raise RuntimeError(
                "OLLAMA_EMBED_MODEL is not configured; vector retrieval is disabled"
            )
        try:
            self.client = chromadb.PersistentClient(path=CHROMADB_CONFIG.db_path)
            self.collection = self.client.get_collection(name=CHROMADB_CONFIG.collection_name)
            metadata = self.collection.metadata or {}
            indexed_model = metadata.get("embedding_model")
            if indexed_model != OLLAMA_CONFIG.embedding_model:
                self.collection = None
                raise RuntimeError(
                    "Configured collection provenance does not match OLLAMA_EMBED_MODEL"
                )
            return self.collection
        except Exception as exc:
            logger.warning("ChromaDB initialization failed (%s)", type(exc).__name__)
            raise

    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for the query using Ollama."""
        try:
            payload = {
                "model": OLLAMA_CONFIG.embedding_model,
                "prompt": query
            }

            response = requests.post(
                OLLAMA_CONFIG.embeddings_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result.get("embedding", [])

        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise

    def retrieve_profiles(self,
                         query: str,
                         n_results: int = 10,
                         where_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve relevant ARGO profiles based on semantic similarity.

        Args:
            query: Natural language query describing the desired profiles
            n_results: Maximum number of results to return
            where_filter: Optional metadata filter (e.g., {"wmo_id": 1902037})

        Returns:
            Dictionary containing retrieved profiles with metadata and distances
        """
        try:
            if not query.strip():
                raise ValueError("query cannot be empty")
            n_results = min(max(int(n_results), 1), SYSTEM_CONFIG.max_retrieval_results)
            collection = self._get_collection()

            # Generate query embedding
            query_embedding = self._get_query_embedding(query)

            if not query_embedding:
                raise ValueError("Failed to generate query embedding")

            # Perform vector search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            formatted_results = {
                "n_results": len(results["ids"][0]) if results["ids"] else 0,
                "profiles": []
            }

            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i] if results["distances"] else None
                    profile = {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": distance,
                    }
                    formatted_results["profiles"].append(profile)

            logger.info(f"Retrieved {formatted_results['n_results']} profiles")
            return formatted_results

        except Exception as exc:
            logger.warning("Profile retrieval failed (%s)", type(exc).__name__)
            raise

    def retrieve_by_region(self,
                          region_name: str,
                          time_filter: Optional[str] = None,
                          n_results: int = 20) -> Dict[str, Any]:
        """
        Retrieve profiles from a specific geographic region.

        Args:
            region_name: Name of the region (e.g., "Bay of Bengal", "Arabian Sea")
            time_filter: Optional time constraint (e.g., "January 2024")
            n_results: Maximum number of results

        Returns:
            Dictionary containing retrieved profiles
        """
        query_parts = [f"ARGO profiles in the {region_name}"]
        if time_filter:
            query_parts.append(f"during {time_filter}")

        bounds = SYSTEM_CONFIG.regions.get(region_name)
        if bounds is None:
            raise ValueError(f"Unsupported region: {region_name}")
        where_filter = {
            "$and": [
                {"latitude": {"$gte": bounds["lat_min"]}},
                {"latitude": {"$lte": bounds["lat_max"]}},
                {"longitude": {"$gte": bounds["lon_min"]}},
                {"longitude": {"$lte": bounds["lon_max"]}},
            ]
        }
        query = " ".join(query_parts)
        return self.retrieve_profiles(query, n_results, where_filter)

    def retrieve_by_float_id(self, wmo_id: int, n_results: int = 50) -> Dict[str, Any]:
        """
        Retrieve all profiles from a specific ARGO float.

        Args:
            wmo_id: WMO ID of the ARGO float
            n_results: Maximum number of results

        Returns:
            Dictionary containing retrieved profiles
        """
        where_filter = {"wmo_id": wmo_id}
        query = f"ARGO float {wmo_id} profiles"

        return self.retrieve_profiles(query, n_results, where_filter)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection."""
        try:
            collection = self._get_collection()
            total_count = collection.count()

            # Get sample of metadata to analyze
            sample = collection.get(limit=100, include=["metadatas"])

            stats = {
                "total_profiles": total_count,
                "sample_size": len(sample["metadatas"]) if sample["metadatas"] else 0,
                "unique_floats": set(),
                "date_range": {"min": None, "max": None}
            }

            # Analyze sample metadata
            if sample["metadatas"]:
                for metadata in sample["metadatas"]:
                    if "wmo_id" in metadata:
                        stats["unique_floats"].add(metadata["wmo_id"])

            stats["unique_floats"] = len(stats["unique_floats"])

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}

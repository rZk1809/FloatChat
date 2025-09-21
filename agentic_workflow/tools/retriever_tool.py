"""
ChromaDB Vector Retrieval Tool for ARGO float profile data.
Provides semantic search capabilities over ARGO profile summaries.
"""

import logging
import chromadb
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from core.config import CHROMADB_CONFIG, OLLAMA_CONFIG
import requests
import json

logger = logging.getLogger(__name__)

class RetrieverTool:
    """Tool for retrieving relevant ARGO profiles using vector similarity search."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            self.client = chromadb.PersistentClient(path=CHROMADB_CONFIG.db_path)
            self.collection = self.client.get_collection(name=CHROMADB_CONFIG.collection_name)
            logger.info(f"Connected to ChromaDB collection: {CHROMADB_CONFIG.collection_name}")
            logger.info(f"Collection contains {self.collection.count()} profiles")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
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
            logger.info(f"Retrieving profiles for query: '{query}'")
            
            # Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            if not query_embedding:
                raise ValueError("Failed to generate query embedding")
            
            # Perform vector search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = {
                "query": query,
                "n_results": len(results["ids"][0]) if results["ids"] else 0,
                "profiles": []
            }
            
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    profile = {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "similarity": 1 - results["distances"][0][i] if results["distances"] else None
                    }
                    formatted_results["profiles"].append(profile)
            
            logger.info(f"Retrieved {formatted_results['n_results']} profiles")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Profile retrieval failed: {e}")
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
        
        query = " ".join(query_parts)
        return self.retrieve_profiles(query, n_results)
    
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
            total_count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample = self.collection.get(limit=100, include=["metadatas"])
            
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

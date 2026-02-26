"""
main/backend/services/retrieval_service.py
Encodes a query and retrieves the closest chunks from FAISS.
Fixed imports for unified project structure.
"""

import logging
from typing import Dict, List, Optional

from backend.core.config import settings
from backend.services.embedding_service import EmbeddingGenerator
from backend.services.vector_store import VectorDBStorage

logger = logging.getLogger(__name__)


class RetrievalService:
    """Encode a query and retrieve the closest chunks from the vector DB."""

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator(
            model_name=settings.EMBEDDING_MODEL
        )
        self.vector_store = VectorDBStorage()

    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """
        1. Encode the query with the same SentenceTransformer model.
        2. Search FAISS for the top_k nearest chunks.
        3. Filter by similarity threshold.
        """
        if top_k is None:
            top_k = settings.TOP_K_RESULTS

        logger.info("Retrieving chunks for query: %s", query)

        query_embedding = self.embedding_generator.model.encode(
            query, normalize_embeddings=True
        )

        results  = self.vector_store.search(query_embedding, top_k=top_k)
        filtered = [
            r for r in results
            if r["similarity_score"] >= settings.SIMILARITY_THRESHOLD
        ]

        logger.info(
            "Retrieved %d / %d chunks above threshold %.2f",
            len(filtered), len(results), settings.SIMILARITY_THRESHOLD,
        )
        return filtered

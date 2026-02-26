"""
main/backend/services/vector_store.py
FAISS vector store facade — fixed imports + added get_vector_count().
"""

import logging
from typing import Dict, List, Union

import numpy as np

from backend.vector_db.db_client import VectorDBClient

logger = logging.getLogger(__name__)


class VectorDBStorage:
    """High-level facade over VectorDBClient."""

    def __init__(self):
        self.client = VectorDBClient()

    def store_embeddings(self, chunks: List[Dict]) -> int:
        """Store a batch of chunks (each must have an 'embedding' key). Returns count stored."""
        if not chunks:
            logger.warning("store_embeddings called with empty list — skipping.")
            return 0
        self.client.add_documents(chunks)
        logger.info("Stored %d chunks in FAISS.", len(chunks))
        return len(chunks)

    def search(self, query_vector: Union[np.ndarray, List[float]], top_k: int = 5) -> List[Dict]:
        """Cosine-similarity search. Returns top-k results with chunk, distance, similarity_score."""
        if isinstance(query_vector, list):
            query_vector = np.array(query_vector, dtype="float32")
        return self.client.search(query_vector, top_k=top_k)

    def get_vector_count(self) -> int:
        """Return total number of vectors stored in the index."""
        return self.client.get_total_vectors()

    def get_stats(self) -> Dict:
        """Return stats: total_chunks, dimension, unique_documents."""
        return self.client.get_stats()

"""
main/backend/vector_db/db_client.py
FAISS-based vector database — fixed import for unified project.
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, List

import faiss
import numpy as np

from backend.core.config import settings

logger = logging.getLogger(__name__)


class VectorDBClient:
    """FAISS FlatIP index with on-disk persistence."""

    def __init__(self):
        self.storage_path: Path = settings.VECTOR_DB_DIR
        self.dimension: int     = settings.EMBEDDING_DIMENSION

        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata_store: List[Dict] = []
        self._load()

        logger.info("VectorDBClient ready | vectors=%d dim=%d",
                    self.index.ntotal, self.dimension)

    def add_documents(self, chunks: List[Dict]) -> None:
        embeddings = np.array([c["embedding"] for c in chunks], dtype="float32")
        self.index.add(embeddings)
        for chunk in chunks:
            self.metadata_store.append({k: v for k, v in chunk.items() if k != "embedding"})
        self._save()
        logger.info("Added %d chunks → total: %d", len(chunks), self.index.ntotal)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        query_vec = np.array([query_embedding], dtype="float32")
        scores, indices = self.index.search(query_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.metadata_store):
                results.append({
                    "chunk": self.metadata_store[idx],
                    "distance": float(score),
                    "similarity_score": float(score),
                })
        return results

    def get_total_vectors(self) -> int:
        return self.index.ntotal

    def get_stats(self) -> Dict:
        unique_docs = {
            m.get("document_id", m.get("metadata", {}).get("document_id"))
            for m in self.metadata_store
        } - {None}
        return {
            "total_chunks": self.index.ntotal,
            "dimension": self.dimension,
            "unique_documents": len(unique_docs),
        }

    def _save(self) -> None:
        faiss.write_index(self.index, str(self.storage_path / "faiss.index"))
        with open(self.storage_path / "metadata.pkl", "wb") as fh:
            pickle.dump(self.metadata_store, fh)

    def _load(self) -> None:
        index_path = self.storage_path / "faiss.index"
        meta_path  = self.storage_path / "metadata.pkl"
        if index_path.exists() and meta_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(meta_path, "rb") as fh:
                self.metadata_store = pickle.load(fh)
            logger.info("Loaded FAISS index from disk.")

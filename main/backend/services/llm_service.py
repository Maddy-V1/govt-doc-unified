"""
backend/services/llm_service.py
Offline LLM service using Llama 3.1 8B (4-bit GGUF) via llama-cpp-python.
Handles query refinement and RAG answer generation entirely locally.
"""

import logging
from typing import List, Dict, Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Wrapper around a local Llama 3.1 8B 4-bit GGUF model."""

    _instance: Optional["LLMService"] = None  # singleton

    def __init__(self):
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )
        
        model_path = settings.LLM_MODEL_PATH
        if not model_path:
            raise ValueError(
                "LLM_MODEL_PATH is not set. "
                "Download a Llama-3.1-8B Q4_K_M GGUF file and set the path in .env"
            )

        logger.info("Loading LLM from %s …", model_path)
        self.llm = Llama(
            model_path=model_path,
            n_ctx=settings.LLM_N_CTX,
            n_gpu_layers=settings.LLM_N_GPU_LAYERS,
            verbose=False,
        )
        logger.info("LLM loaded successfully.")

    # ------------------------------------------------------------------
    # Singleton accessor (heavy model – load once)
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Core generation helper
    # ------------------------------------------------------------------
    def _generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.3) -> str:
        """Run inference on the local GGUF model and return the text."""
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=settings.LLM_TOP_P,
            stop=["</s>", "\n\n\n"],
            echo=False,
        )
        return output["choices"][0]["text"].strip()

    # ------------------------------------------------------------------
    # Query refinement
    # ------------------------------------------------------------------
    def refine_query(self, original_query: str) -> str:
        """
        Rephrase the user query to be more specific and search-friendly
        for semantic retrieval.
        """
        prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            "You are a helpful search assistant. Given a user question, "
            "rephrase it into a concise, search-optimised query that captures "
            "the key intent and important keywords. Reply ONLY with the refined query.\n"
            "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"{original_query}\n"
            "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        )

        refined = self._generate(prompt, max_tokens=100, temperature=0.2)
        logger.info("Query refined: '%s' → '%s'", original_query, refined)
        return refined if refined else original_query

    # ------------------------------------------------------------------
    # RAG answer generation
    # ------------------------------------------------------------------
    def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generate an answer grounded in the retrieved context chunks.
        Each item in *context_chunks* is expected to have a nested 'chunk'
        dict with at least a 'text' key (as returned by VectorDBStorage.search).
        """
        # Build numbered context block
        context_parts: List[str] = []
        for i, result in enumerate(context_chunks, 1):
            chunk_data = result.get("chunk", result)
            text = chunk_data.get("chunk_text", chunk_data.get("text", ""))
            context_parts.append(f"[Source {i}]: {text}")
        context_block = "\n\n".join(context_parts)

        prompt = (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            "You are a precise document-analysis assistant. "
            "Answer the question using ONLY the provided context. "
            "If the context does not contain enough information, say so clearly. "
            "Cite source numbers where relevant.\n"
            "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"Context:\n{context_block}\n\n"
            f"Question: {query}\n"
            "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        )

        answer = self._generate(
            prompt,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
        )
        return answer

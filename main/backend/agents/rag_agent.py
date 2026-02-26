"""
main/backend/agents/rag_agent.py
RAG Agent — query refinement and answer generation via Llama 3.1 8B.
Falls back gracefully if LLM model file is missing.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

# Add main/backend to sys.path so backend.* imports resolve
_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# Lazy LLM import — only load the heavy model when first needed
_llm_instance = None
_llm_available: bool | None = None   # None = not yet checked


def _get_llm():
    global _llm_instance, _llm_available
    if _llm_available is None:
        try:
            from backend.services.llm_service import LLMService
            _llm_instance  = LLMService.get_instance()
            _llm_available = True
            logger.info("LLM loaded successfully.")
        except Exception as e:
            logger.warning("LLM not available: %s — falling back to chunk passthrough.", e)
            _llm_available = False
    return _llm_instance if _llm_available else None


def refine_query(query: str) -> str:
    """
    Rephrase the user query for better semantic retrieval.
    Returns original query if LLM is unavailable.
    """
    llm = _get_llm()
    if llm is None:
        return query
    try:
        refined = llm.refine_query(query)
        logger.info("Query refined: '%s' → '%s'", query, refined)
        return refined or query
    except Exception as e:
        logger.error("Query refinement failed: %s", e)
        return query


def generate_answer(query: str, chunks: List[Dict]) -> str:
    """
    Generate a grounded answer from retrieved chunks.
    Falls back to top-chunk passthrough if LLM is unavailable.
    """
    llm = _get_llm()
    if llm is None:
        if chunks:
            chunk_data = chunks[0].get("chunk", chunks[0])
            text = chunk_data.get("chunk_text", chunk_data.get("text", ""))
            return (
                "[LLM not available — showing top retrieved chunk]\n\n"
                + text[:600]
            )
        return "No relevant information found."

    try:
        answer = llm.generate_answer(query, chunks)
        return answer
    except Exception as e:
        logger.error("Answer generation failed: %s", e)
        if chunks:
            chunk_data = chunks[0].get("chunk", chunks[0])
            text = chunk_data.get("chunk_text", chunk_data.get("text", ""))
            return (
                f"[Error generating answer: {e}]\n\n"
                + text[:600]
            )
        return f"Error generating answer: {e}"

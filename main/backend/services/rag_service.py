"""RAG Service - Full RAG pipeline for query answering"""
import logging
from typing import Dict, List
from backend.agents import rag_agent
from backend.services.retrieval_service import RetrievalService
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Module-level singletons (load heavy models once)
_retrieval_service = None

def get_retrieval_service() -> RetrievalService:
    """Get or create singleton RetrievalService instance"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


async def answer_query(
    query: str,
    top_k: int = None,
    include_sources: bool = True
) -> Dict:
    """
    Full RAG pipeline: refine query -> retrieve chunks -> generate answer
    
    Args:
        query: User query string
        top_k: Number of chunks to retrieve (default from settings)
        include_sources: Whether to include source chunks in response
        
    Returns:
        Dict with query, refined_query, answer, sources, retrieved_count
    """
    try:
        if top_k is None:
            top_k = settings.TOP_K_RESULTS
        
        logger.info(f"Processing query: '{query}' (top_k={top_k})")
        
        # Step 1: Refine query
        refined_query = rag_agent.refine_query(query)
        
        # Step 2: Retrieve relevant chunks (use singleton)
        retrieval_service = get_retrieval_service()
        chunks = retrieval_service.retrieve_relevant_chunks(refined_query, top_k)
        
        # Step 3: Check if chunks found
        if not chunks:
            logger.warning("No relevant documents found")
            return {
                "query": query,
                "refined_query": refined_query,
                "answer": "No relevant documents found. Please upload documents first or try a different query.",
                "sources": [],
                "retrieved_count": 0
            }
        
        logger.info(f"Retrieved {len(chunks)} relevant chunks")
        
        # Step 4: Generate answer
        answer = rag_agent.generate_answer(query, chunks)
        
        # Step 5: Prepare response
        result = {
            "query": query,
            "refined_query": refined_query,
            "answer": answer,
            "retrieved_count": len(chunks)
        }
        
        if include_sources:
            result["sources"] = chunks
        else:
            result["sources"] = []
        
        logger.info("Query processing completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"RAG pipeline failed: {str(e)}")
        return {
            "query": query,
            "refined_query": query,
            "answer": f"Error processing query: {str(e)}",
            "sources": [],
            "retrieved_count": 0
        }

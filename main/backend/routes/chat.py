"""Chat Route - RAG query endpoint"""
import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from backend.services import rag_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    query: str = Field(..., min_length=1, description="User query")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of chunks to retrieve")
    include_sources: Optional[bool] = Field(True, description="Include source chunks in response")


class ChatResponse(BaseModel):
    """Chat response model"""
    model_config = ConfigDict()
    
    query: str
    refined_query: Optional[str] = None
    answer: str
    sources: list
    retrieved_count: int
    processing_time_ms: int


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process user query through RAG pipeline
    
    Args:
        request: ChatRequest with query, top_k, include_sources
        
    Returns:
        ChatResponse with answer and sources
    """
    start_time = time.time()
    
    try:
        logger.info(f"Chat query received: '{request.query}'")
        
        # Process query through RAG pipeline
        result = await rag_service.answer_query(
            query=request.query,
            top_k=request.top_k,
            include_sources=request.include_sources
        )
        
        # Add processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = processing_time_ms
        
        logger.info(f"Chat query processed in {processing_time_ms}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Chat query failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

"""
backend/app/models/response_models.py
Response schemas for the API.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentChunk(BaseModel):
    """A single retrieved chunk with similarity info."""
    chunk_id: str
    text: str
    page_number: Optional[int] = None
    similarity_score: float


class QueryResponse(BaseModel):
    """Response for the /query endpoint."""
    query: str
    refined_query: Optional[str] = None
    answer: str
    sources: List[DocumentChunk] = []
    metadata: Dict[str, Any] = {}
    processing_time: float


class UploadResponse(BaseModel):
    """Response for the /upload endpoint."""
    document_id: str
    filename: str
    status: str
    chunks_created: int
    processing_time: float
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    vector_db_status: str
    total_documents: int
    total_chunks: int

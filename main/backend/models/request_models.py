"""
backend/app/models/request_models.py
Request schemas for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class UploadRequest(BaseModel):
    """Optional metadata sent alongside a PDF upload."""
    document_name: Optional[str] = None
    document_type: Optional[str] = None


class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    include_sources: Optional[bool] = True


class QueryRefinementRequest(BaseModel):
    """Internal model for LLM query refinement."""
    original_query: str
    context: Optional[str] = None

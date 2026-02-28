"""
API routes for viewing extracted metadata
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.core.config import settings
from backend.services.metadata_service import MetadataService

router = APIRouter()
logger = logging.getLogger(__name__)

metadata_service = MetadataService()


@router.get("/extractions")
async def list_extractions(
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all extracted documents with metadata
    Returns summaries without full text
    """
    try:
        extractions = metadata_service.list_extractions(limit=limit, offset=offset)
        return {
            "total": len(extractions),
            "limit": limit,
            "offset": offset,
            "extractions": extractions
        }
    except Exception as e:
        logger.error(f"Error listing extractions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extractions/{file_id}")
async def get_extraction(file_id: str):
    """
    Get complete extraction metadata including full text
    """
    try:
        extraction = metadata_service.get_extraction(file_id)
        return extraction
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Extraction not found: {file_id}")
    except Exception as e:
        logger.error(f"Error retrieving extraction {file_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extractions/{file_id}/text")
async def get_extraction_text(file_id: str):
    """
    Download extracted text as plain text file
    """
    text_path = settings.DATA_DIR / "extracted_metadata" / f"{file_id}.txt"
    
    if not text_path.exists():
        raise HTTPException(status_code=404, detail=f"Text file not found: {file_id}")
    
    return FileResponse(
        path=text_path,
        media_type="text/plain",
        filename=f"{file_id}.txt"
    )


@router.get("/extractions/{file_id}/csv")
async def get_extraction_csv(file_id: str):
    """
    Download extracted data as CSV file (if available)
    """
    csv_path = settings.DATA_DIR / "extracted_metadata" / f"{file_id}.csv"
    
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"CSV file not found: {file_id}")
    
    return FileResponse(
        path=csv_path,
        media_type="text/csv",
        filename=f"{file_id}.csv"
    )


@router.delete("/extractions/{file_id}")
async def delete_extraction(file_id: str):
    """
    Delete extraction metadata
    """
    try:
        deleted = metadata_service.delete_extraction(file_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Extraction not found: {file_id}")
        
        return {"message": f"Extraction {file_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting extraction {file_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

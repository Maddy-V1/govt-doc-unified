"""Health Check Route"""
import logging
import subprocess
from pathlib import Path
from fastapi import APIRouter

from backend.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    Check system health status
    
    Returns status of:
    - Tesseract (if OCR_ENGINE=tesseract)
    - Sarvam API key (if OCR_ENGINE=sarvam)
    - LLM model file
    - FAISS index
    - Embedding model
    """
    health_status = {
        "status": "healthy",
        "ocr_engine": settings.OCR_ENGINE,
        "checks": {}
    }
    
    issues = []
    
    # Check OCR engine
    if settings.OCR_ENGINE.lower() == "tesseract":
        try:
            # Use tesseract command from PATH if TESSERACT_PATH is empty
            tesseract_cmd = settings.TESSERACT_PATH if settings.TESSERACT_PATH else "tesseract"
            result = subprocess.run(
                [tesseract_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                health_status["checks"]["tesseract"] = {
                    "status": "ok",
                    "version": version
                }
            else:
                health_status["checks"]["tesseract"] = {
                    "status": "error",
                    "message": "Tesseract not responding"
                }
                issues.append("Tesseract not responding")
        except Exception as e:
            health_status["checks"]["tesseract"] = {
                "status": "error",
                "message": str(e)
            }
            issues.append(f"Tesseract error: {str(e)}")
    
    elif settings.OCR_ENGINE.lower() == "sarvam":
        if settings.SARVAM_API_KEY and settings.SARVAM_API_KEY != "your_sarvam_key_here":
            health_status["checks"]["sarvam_api"] = {
                "status": "ok",
                "message": "API key configured"
            }
        else:
            health_status["checks"]["sarvam_api"] = {
                "status": "warning",
                "message": "API key not configured"
            }
            issues.append("Sarvam API key not configured")
    
    # Check LLM model file
    llm_model_path = (settings.BASE_DIR / settings.LLM_MODEL_PATH).resolve()
    if llm_model_path.exists():
        file_size_mb = llm_model_path.stat().st_size / (1024 * 1024)
        health_status["checks"]["llm_model"] = {
            "status": "ok",
            "path": str(llm_model_path),
            "size_mb": round(file_size_mb, 2)
        }
    else:
        health_status["checks"]["llm_model"] = {
            "status": "error",
            "message": f"Model file not found: {llm_model_path}"
        }
        issues.append("LLM model file not found")
    
    # Check FAISS index
    try:
        from backend.services.vector_store import VectorDBStorage
        vector_store = VectorDBStorage()
        vector_count = vector_store.get_vector_count() if hasattr(vector_store, 'get_vector_count') else 0
        
        health_status["checks"]["vector_db"] = {
            "status": "ok",
            "vector_count": vector_count
        }
    except Exception as e:
        health_status["checks"]["vector_db"] = {
            "status": "warning",
            "message": str(e)
        }
        issues.append(f"Vector DB warning: {str(e)}")
    
    # Check embedding model
    try:
        # Don't create new instance, just check if it can be imported
        from sentence_transformers import SentenceTransformer
        
        health_status["checks"]["embedding_model"] = {
            "status": "ok",
            "model": settings.EMBEDDING_MODEL,
            "dimension": settings.EMBEDDING_DIMENSION
        }
    except Exception as e:
        health_status["checks"]["embedding_model"] = {
            "status": "error",
            "message": str(e)
        }
        issues.append(f"Embedding model error: {str(e)}")
    
    # Set overall status
    if issues:
        health_status["status"] = "degraded"
        health_status["issues"] = issues
    
    return health_status

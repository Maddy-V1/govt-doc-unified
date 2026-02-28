"""Main FastAPI Application"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.routes import upload, chat, health, extractions

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.DATA_DIR / "logs" / "app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info("=" * 60)
    
    # Log OCR engine
    logger.info(f"OCR Engine: {settings.OCR_ENGINE}")
    
    if settings.OCR_ENGINE.lower() == "tesseract":
        logger.info(f"Tesseract Path: {settings.TESSERACT_PATH}")
        logger.info(f"Tesseract Language: {settings.TESSERACT_LANG}")
    elif settings.OCR_ENGINE.lower() == "sarvam":
        api_key_status = "configured" if settings.SARVAM_API_KEY and settings.SARVAM_API_KEY != "your_sarvam_key_here" else "NOT configured"
        logger.info(f"Sarvam API Key: {api_key_status}")
    
    # Check LLM model
    llm_model_path = (settings.BASE_DIR / settings.LLM_MODEL_PATH).resolve()
    if llm_model_path.exists():
        logger.info(f"LLM Model: {llm_model_path} (found)")
    else:
        logger.warning(f"LLM Model: {llm_model_path} (NOT FOUND)")
    
    # Check vector DB
    try:
        from backend.services.vector_store import VectorDBStorage
        vector_store = VectorDBStorage()
        vector_count = vector_store.get_vector_count() if hasattr(vector_store, 'get_vector_count') else 0
        logger.info(f"Vector DB: {vector_count} vectors loaded")
    except Exception as e:
        logger.warning(f"Vector DB: {str(e)}")
    
    logger.info(f"Server: http://{settings.HOST}:{settings.PORT}")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(health.router, tags=["Health"])
app.include_router(extractions.router, tags=["Extractions"])


@app.get("/")
async def root():
    """Root endpoint - system information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "ocr_engine": settings.OCR_ENGINE,
        "embedding_model": settings.EMBEDDING_MODEL,
        "status": "running",
        "endpoints": {
            "upload": "/upload",
            "chat": "/chat",
            "health": "/health",
            "extractions": "/extractions",
            "docs": "/docs"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )

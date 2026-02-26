"""Unified Configuration Module"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from main/ directory (two levels up from this file)
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application Settings"""
    
    # OCR Engine
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "tesseract")
    
    # Tesseract
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", "/opt/homebrew/bin/tesseract")
    TESSERACT_LANG: str = os.getenv("TESSERACT_LANG", "eng")
    TESSERACT_OEM: int = int(os.getenv("TESSERACT_OEM", "1"))
    TESSERACT_PSM: int = int(os.getenv("TESSERACT_PSM", "3"))
    
    # Sarvam AI
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    
    # LLM
    LLM_MODEL_PATH: str = os.getenv("LLM_MODEL_PATH", "../../Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
    LLM_N_CTX: int = int(os.getenv("LLM_N_CTX", "4096"))
    LLM_N_GPU_LAYERS: int = int(os.getenv("LLM_N_GPU_LAYERS", "0"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "512"))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.95"))
    
    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "400"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Retrieval
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "True").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # File limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    
    # API Metadata
    API_TITLE: str = "Govt Document Intelligence System"
    API_VERSION: str = "1.0.0"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DATA_DIR: Path = BASE_DIR / "data"
    VECTOR_DB_DIR: Path = BASE_DIR / "vector_db"
    
    def __init__(self):
        """Create necessary directories"""
        # Upload directories
        (self.UPLOAD_DIR / "pdfs").mkdir(parents=True, exist_ok=True)
        (self.UPLOAD_DIR / "images").mkdir(parents=True, exist_ok=True)
        (self.UPLOAD_DIR / "processed").mkdir(parents=True, exist_ok=True)
        
        # Data directories
        (self.DATA_DIR / "extracted_json").mkdir(parents=True, exist_ok=True)
        (self.DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)
        
        # Vector DB directory
        self.VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

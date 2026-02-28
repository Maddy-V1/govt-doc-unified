"""
main/backend/routes/upload.py
Full document processing pipeline — OCR → validate → preprocess → embed → store.
"""

import logging
import time
import uuid
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.services import ocr_service
from backend.agents import validation_agent
from backend.services.metadata_service import MetadataService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize metadata service
metadata_service = MetadataService()

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# Lazy initialization of heavy objects (loaded on first use, not at import time)
_cleaner = None
_normalizer = None
_metadata = None
_chunker = None
_embedder = None
_vector_store = None


def get_cleaner():
    """Lazy load OCRTextCleaner"""
    global _cleaner
    if _cleaner is None:
        from backend.services.preprocessing.pp1_cleaning import OCRTextCleaner
        _cleaner = OCRTextCleaner()
    return _cleaner


def get_normalizer():
    """Lazy load TextNormalizer"""
    global _normalizer
    if _normalizer is None:
        from backend.services.preprocessing.pp2_normalization import TextNormalizer
        _normalizer = TextNormalizer()
    return _normalizer


def get_metadata_extractor():
    """Lazy load MetadataExtractor"""
    global _metadata
    if _metadata is None:
        from backend.services.preprocessing.pp3_metadata import MetadataExtractor
        _metadata = MetadataExtractor()
    return _metadata


def get_chunker():
    """Lazy load TextChunker"""
    global _chunker
    if _chunker is None:
        from backend.services.preprocessing.pp4_chunking import TextChunker
        _chunker = TextChunker(
            target_word_size=settings.CHUNK_SIZE,
            overlap_word_size=settings.CHUNK_OVERLAP,
        )
    return _chunker


def get_embedder():
    """Lazy load EmbeddingGenerator"""
    global _embedder
    if _embedder is None:
        from backend.services.embedding_service import EmbeddingGenerator
        _embedder = EmbeddingGenerator(model_name=settings.EMBEDDING_MODEL)
    return _embedder


def get_vector_store():
    """Lazy load VectorDBStorage"""
    global _vector_store
    if _vector_store is None:
        from backend.services.vector_store import VectorDBStorage
        _vector_store = VectorDBStorage()
    return _vector_store


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process document through full pipeline:
      1. Validate file (type + size)
      2. Run OCR  (ocr1 Tesseract  or  ocr2 Sarvam — from .env)
      3. Validate OCR result  (validation_agent)
      4. Preprocess text  (pp1 → pp2 → pp3 → pp4)
      5. Generate embeddings
      6. Store in FAISS vector DB
      7. Save result JSON to data/extracted_json/
    """
    start_time = time.time()
    file_id    = str(uuid.uuid4())

    # ── 1. Validate ──────────────────────────────────────────────────────────
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_content   = await file.read()
    file_size_mb   = len(file_content) / (1024 * 1024)

    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size_mb:.1f} MB). Max: {settings.MAX_FILE_SIZE_MB} MB"
        )

    # ── Save uploaded file ────────────────────────────────────────────────────
    save_dir  = settings.UPLOAD_DIR / ("pdfs" if file_ext == ".pdf" else "images")
    file_path = save_dir / f"{file_id}{file_ext}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    logger.info("Saved upload: %s (%.1f MB)", file_path.name, file_size_mb)

    try:
        # ── 2. OCR ───────────────────────────────────────────────────────────
        logger.info("Running OCR (%s)…", settings.OCR_ENGINE)
        ocr_result = await ocr_service.run_ocr(file_path, file.filename or "")

        # ── 3. Validate OCR result ────────────────────────────────────────────
        logger.info("Validating OCR result…")
        validation = validation_agent.validate_ocr_result(ocr_result)

        if validation["recommendation"] == "reject":
            logger.warning("Document rejected: %s", validation["warnings"])
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Document quality too low for processing",
                    "file_id": file_id,
                    "filename": file.filename,
                    "validation": validation,
                    "ocr_summary": {
                        "confidence": ocr_result.get("confidence"),
                        "word_count": ocr_result.get("word_count"),
                        "ocr_engine": ocr_result.get("ocr_engine"),
                    },
                }
            )

        # ── 4. Preprocess ─────────────────────────────────────────────────────
        full_text = ocr_result["full_text"]

        # pp1 — cleaning (pass as token list; treat whole text as high-confidence)
        cleaner = get_cleaner()
        tokens = [{"text": w, "conf": ocr_result.get("confidence", 1.0)}
                  for w in full_text.split()]
        cleaned_text = cleaner.clean_text_pipeline(tokens)

        # pp2 — normalisation
        normalizer = get_normalizer()
        norm_result = normalizer.process(cleaned_text)
        display_text = norm_result["display_text"]
        search_text = norm_result["search_text"]

        # pp3 — metadata extraction (on display_text to preserve casing for NER)
        metadata_extractor = get_metadata_extractor()
        doc_metadata = metadata_extractor.extract_metadata(display_text)
        doc_metadata["file_id"] = file_id
        doc_metadata["filename"] = file.filename

        # pp4 — chunking (on search_text for embedding)
        chunker = get_chunker()
        chunks = chunker.chunk_document(search_text, doc_metadata)
        logger.info("Created %d chunks", len(chunks))

        # ── 5. Embeddings ─────────────────────────────────────────────────────
        logger.info("Generating embeddings…")
        embedder = get_embedder()
        chunks = embedder.generate_embeddings(chunks)  # adds 'embedding' key in-place

        # ── 6. Vector DB ──────────────────────────────────────────────────────
        logger.info("Storing in FAISS…")
        vector_store = get_vector_store()
        vector_store.store_embeddings(chunks)

        # ── 7. Save JSON history ──────────────────────────────────────────────
        processing_time_ms = int((time.time() - start_time) * 1000)
        result_data = {
            "file_id":           file_id,
            "filename":          file.filename,
            "ocr_engine":        ocr_result["ocr_engine"],
            "pages_processed":   ocr_result["total_pages"],
            "confidence":        ocr_result["confidence"],
            "word_count":        ocr_result["word_count"],
            "chunks_created":    len(chunks),
            "validation":        validation,
            "structured_fields": ocr_result.get("structured_fields", {}),
            "processing_time_ms": processing_time_ms,
        }

        json_path = settings.DATA_DIR / "extracted_json" / f"{file_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        # ── 8. Save extraction metadata (text + JSON + CSV) ───────────────────
        preprocessing_metadata = {
            "cleaned_text_length": len(cleaned_text),
            "normalized_text_length": len(search_text),
            "chunks_created": len(chunks),
            "metadata_extracted": doc_metadata,
        }
        
        # Extract CSV data if available (PaddleOCR)
        csv_data = ocr_result.get("csv_data", None)
        
        metadata_service.save_extraction(
            file_id=file_id,
            filename=file.filename,
            ocr_result=ocr_result,
            validation=validation,
            preprocessing_result=preprocessing_metadata,
            csv_data=csv_data
        )

        logger.info("Upload complete in %d ms", processing_time_ms)
        return result_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload pipeline failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/upload/status/{file_id}")
async def get_upload_status(file_id: str):
    """Retrieve saved processing result for a file_id."""
    json_path = settings.DATA_DIR / "extracted_json" / f"{file_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

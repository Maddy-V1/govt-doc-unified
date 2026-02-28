"""OCR Service - Unified OCR Engine Selector"""
import sys
from pathlib import Path
from typing import Dict
import logging

# Add parent directories to path for ocr1 and ocr2 imports
# File is at: main/backend/services/ocr_service.py
# .parents[0] = services/, .parents[1] = backend/, .parents[2] = main/, .parents[3] = unified/
unified_dir = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(unified_dir))

from backend.core.config import settings

logger = logging.getLogger(__name__)


async def run_ocr(file_path: Path, original_filename: str) -> Dict:
    """
    Run OCR on document using configured engine (Tesseract, Sarvam, or PaddleOCR)
    
    Args:
        file_path: Path to the document file
        original_filename: Original filename
        
    Returns:
        Dict with OCR results including full_text, pages, confidence, etc.
    """
    try:
        engine = settings.OCR_ENGINE.lower()
        if engine == "tesseract":
            return await _run_tesseract_ocr(file_path, original_filename)
        elif engine == "sarvam":
            return await _run_sarvam_ocr(file_path, original_filename)
        elif engine == "paddleocr":
            return await _run_paddle_ocr(file_path, original_filename)
        else:
            raise ValueError(f"Unknown OCR engine: {settings.OCR_ENGINE}")
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise


async def _run_tesseract_ocr(file_path: Path, original_filename: str) -> Dict:
    """Run Tesseract OCR pipeline"""
    try:
        # Import ocr1 modules
        from ocr1.pdf_handler import load_document_images
        from ocr1.preprocessing import preprocess_pil_image
        from ocr1.engine import extract_text_universal
        from ocr1.postprocessing import clean_text, extract_key_information
        
        logger.info(f"Running Tesseract OCR on {original_filename}")
        
        # Load document images
        images = load_document_images(str(file_path))
        if not images:
            raise ValueError("No images could be extracted from document")
        
        total_pages = len(images)
        all_text = []
        all_confidences = []
        pages_data = []
        
        # Process each page
        for page_num, image in enumerate(images, 1):
            try:
                # Preprocess image (returns tuple: binary, scale_factor)
                preprocessed, scale_factor = preprocess_pil_image(image)
                
                # Extract text with confidence (pass scale_factor for coordinate adjustment)
                result = extract_text_universal(preprocessed, scale_factor=scale_factor)
                page_text = result.get("text", "")
                # extract_text_universal returns confidence on 0-100 scale, convert to 0-1
                page_confidence = result.get("confidence", 0.0) / 100.0
                
                all_text.append(page_text)
                all_confidences.append(page_confidence)
                
                pages_data.append({
                    "page_number": page_num,
                    "text": page_text,
                    "confidence": page_confidence,
                    "word_count": len(page_text.split())
                })
                
                logger.info(f"Processed page {page_num}/{total_pages} - Confidence: {page_confidence:.2f}")
                
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {str(e)}")
                pages_data.append({
                    "page_number": page_num,
                    "text": "",
                    "confidence": 0.0,
                    "word_count": 0,
                    "error": str(e)
                })
        
        # Combine all text
        full_text = "\n\n".join(all_text)
        
        # Clean text
        cleaned_text = clean_text(full_text)
        
        # Extract structured fields
        structured_fields = extract_key_information(cleaned_text)
        
        # Calculate average confidence (already in 0-1 scale after conversion above)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        
        # Calculate word count
        word_count = len(cleaned_text.split())
        
        return {
            "full_text": cleaned_text,
            "pages": pages_data,
            "total_pages": total_pages,
            "confidence": round(avg_confidence, 3),  # 0-1 scale, 3 decimals
            "word_count": word_count,
            "structured_fields": structured_fields,
            "ocr_engine": "tesseract"
        }
        
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {str(e)}")
        raise


async def _run_sarvam_ocr(file_path: Path, original_filename: str) -> Dict:
    """Run Sarvam AI OCR pipeline"""
    try:
        # Import ocr2 module
        from ocr2.sarvam_engine import extract_text_sarvam
        
        logger.info(f"Running Sarvam AI OCR on {original_filename}")
        
        # Run Sarvam OCR
        result = extract_text_sarvam(str(file_path))
        
        if not result or "error" in result:
            raise ValueError(f"Sarvam OCR failed: {result.get('error', 'Unknown error')}")
        
        # Extract data from Sarvam result
        pages_data = result.get("pages", [])
        full_text = result.get("full_text", "")
        total_pages = len(pages_data)
        
        # Calculate word count
        word_count = len(full_text.split())
        
        # Sarvam doesn't provide confidence scores, use a default
        confidence = 0.85  # Assume high confidence for cloud API
        
        return {
            "full_text": full_text,
            "pages": pages_data,
            "total_pages": total_pages,
            "confidence": confidence,
            "word_count": word_count,
            "structured_fields": {},  # Sarvam doesn't do field extraction
            "ocr_engine": "sarvam"
        }
        
    except Exception as e:
        logger.error(f"Sarvam OCR failed: {str(e)}")
        raise


async def _run_paddle_ocr(file_path: Path, original_filename: str) -> Dict:
    """Run PaddleOCR pipeline"""
    try:
        # Import ocr3 module
        from ocr3.paddle_engine import PaddleOCREngine
        
        logger.info(f"Running PaddleOCR on {original_filename}")
        
        # Initialize engine (cached after first use)
        engine = PaddleOCREngine()
        
        # Process file
        result = engine.process_file(str(file_path))
        
        if not result.get("success"):
            raise ValueError("PaddleOCR processing failed")
        
        # Format pages data to match expected structure
        pages_data = []
        for page in result.get("pages", []):
            pages_data.append({
                "page_number": page["page"],
                "text": page["text"],
                "confidence": page["confidence"],
                "word_count": page["word_count"]
            })
        
        return {
            "full_text": result["full_text"],
            "pages": pages_data,
            "total_pages": result["total_pages"],
            "confidence": round(result["confidence"], 3),
            "word_count": result["word_count"],
            "structured_fields": {},  # PaddleOCR doesn't do field extraction by default
            "ocr_engine": "paddleocr",
            "csv_data": result.get("csv_data", [])  # Include CSV data for metadata service
        }
        
    except Exception as e:
        logger.error(f"PaddleOCR failed: {str(e)}")
        raise

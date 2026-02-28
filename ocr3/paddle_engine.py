"""
PaddleOCR Engine for unified system
Supports PDF and image OCR with multiple output formats
"""

import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2

from .config import (
    PADDLE_LANG, PADDLE_USE_GPU, PADDLE_DPI,
    PADDLE_CONF_THRESH, PADDLE_ROW_GAP
)
from .preprocessing import preprocess_image
from .pdf_handler import pdf_to_images, get_pdf_page_count
from .text_grouping import (
    group_into_rows, rows_to_plain_text,
    rows_to_json_entries, rows_to_csv_data
)

logger = logging.getLogger(__name__)


class PaddleOCREngine:
    """PaddleOCR engine with preprocessing and multi-format output"""
    
    def __init__(self):
        """Initialize PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            
            logger.info(f"Initializing PaddleOCR (lang={PADDLE_LANG}, gpu={PADDLE_USE_GPU})")
            
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=PADDLE_LANG,
                use_gpu=PADDLE_USE_GPU,
                show_log=False
            )
            
            # Warmup
            logger.info("Warming up PaddleOCR model...")
            self.ocr.ocr(np.zeros((64, 64, 3), dtype=np.uint8))
            logger.info("PaddleOCR ready")
            
        except ImportError:
            raise ImportError(
                "PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr"
            )
    
    def process_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Process a single image
        
        Args:
            image: RGB numpy array
            
        Returns:
            Dict with OCR results
        """
        start_time = time.time()
        
        # Preprocess
        preprocessed = preprocess_image(image)
        
        # Run OCR
        ocr_start = time.time()
        result = self.ocr.ocr(preprocessed, cls=True)
        ocr_time = time.time() - ocr_start
        
        if not result or not result[0]:
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "word_count": 0,
                "rows": [],
                "processing_time": time.time() - start_time,
                "ocr_time": ocr_time
            }
        
        # Parse results
        texts = []
        scores = []
        polys = []
        
        for line in result[0]:
            if line:
                box, (text, score) = line
                texts.append(text)
                scores.append(score)
                polys.append(box)
        
        # Group into rows
        rows = group_into_rows(
            texts, scores, polys,
            conf_thresh=PADDLE_CONF_THRESH,
            row_gap=PADDLE_ROW_GAP
        )
        
        # Generate outputs
        full_text = rows_to_plain_text(rows)
        avg_confidence = np.mean(scores) if scores else 0.0
        word_count = len(full_text.split())
        
        return {
            "success": True,
            "text": full_text,
            "confidence": float(avg_confidence),
            "word_count": word_count,
            "rows": rows,
            "json_entries": rows_to_json_entries(rows),
            "processing_time": time.time() - start_time,
            "ocr_time": ocr_time
        }
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process entire PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with complete OCR results for all pages
        """
        start_time = time.time()
        
        # Convert PDF to images
        logger.info(f"Converting PDF to images (DPI={PADDLE_DPI})")
        images = pdf_to_images(pdf_path, dpi=PADDLE_DPI)
        total_pages = len(images)
        
        logger.info(f"Processing {total_pages} pages...")
        
        pages_data = []
        all_text = []
        all_csv_rows = []
        total_confidence = 0.0
        total_words = 0
        
        for page_num, image in enumerate(images, 1):
            logger.info(f"Processing page {page_num}/{total_pages}")
            
            result = self.process_image(image)
            
            if result["success"]:
                all_text.append(f"--- Page {page_num} ---\n{result['text']}\n")
                total_confidence += result["confidence"]
                total_words += result["word_count"]
                
                # CSV data
                csv_rows = rows_to_csv_data(result["rows"], page_num)
                all_csv_rows.extend(csv_rows)
                
                pages_data.append({
                    "page": page_num,
                    "text": result["text"],
                    "confidence": result["confidence"],
                    "word_count": result["word_count"],
                    "rows": result["json_entries"],
                    "processing_time": result["processing_time"],
                    "ocr_time": result["ocr_time"]
                })
            else:
                all_text.append(f"--- Page {page_num} ---\n(no text detected)\n")
                pages_data.append({
                    "page": page_num,
                    "text": "",
                    "confidence": 0.0,
                    "word_count": 0,
                    "rows": [],
                    "processing_time": result["processing_time"],
                    "ocr_time": result["ocr_time"]
                })
        
        avg_confidence = total_confidence / total_pages if total_pages > 0 else 0.0
        
        return {
            "success": True,
            "ocr_engine": "paddleocr",
            "total_pages": total_pages,
            "full_text": "\n".join(all_text),
            "confidence": avg_confidence,
            "word_count": total_words,
            "pages": pages_data,
            "csv_data": all_csv_rows,
            "processing_time": time.time() - start_time,
            "dpi": PADDLE_DPI,
            "language": PADDLE_LANG
        }
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF or image file
        
        Args:
            file_path: Path to file
            
        Returns:
            OCR results dict
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return self.process_pdf(str(file_path))
        else:
            # Image file
            image = cv2.imread(str(file_path))
            if image is None:
                raise ValueError(f"Could not read image: {file_path}")
            
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = self.process_image(image)
            
            return {
                "success": result["success"],
                "ocr_engine": "paddleocr",
                "total_pages": 1,
                "full_text": result["text"],
                "confidence": result["confidence"],
                "word_count": result["word_count"],
                "pages": [{
                    "page": 1,
                    "text": result["text"],
                    "confidence": result["confidence"],
                    "word_count": result["word_count"],
                    "rows": result["json_entries"],
                    "processing_time": result["processing_time"],
                    "ocr_time": result["ocr_time"]
                }],
                "csv_data": rows_to_csv_data(result["rows"], 1),
                "processing_time": result["processing_time"],
                "dpi": PADDLE_DPI,
                "language": PADDLE_LANG
            }

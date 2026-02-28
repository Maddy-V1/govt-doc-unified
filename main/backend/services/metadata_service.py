"""
Metadata extraction and storage service
Saves extracted text and metadata from OCR results
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)


class MetadataService:
    """Service for saving and retrieving extracted metadata"""
    
    def __init__(self):
        self.metadata_dir = settings.DATA_DIR / "extracted_metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def save_extraction(
        self,
        file_id: str,
        filename: str,
        ocr_result: Dict[str, Any],
        validation: Dict[str, Any],
        preprocessing_result: Dict[str, Any] = None,
        csv_data: List[List[str]] = None
    ) -> Path:
        """
        Save complete extraction metadata
        
        Args:
            file_id: Unique file identifier
            filename: Original filename
            ocr_result: OCR output with full_text, confidence, etc.
            validation: Validation agent result
            preprocessing_result: Optional preprocessing metadata
            csv_data: Optional CSV data for PaddleOCR
        
        Returns:
            Path to saved metadata file
        """
        metadata = {
            "file_id": file_id,
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "ocr": {
                "engine": ocr_result.get("ocr_engine"),
                "confidence": ocr_result.get("confidence"),
                "word_count": ocr_result.get("word_count"),
                "total_pages": ocr_result.get("total_pages"),
                "full_text": ocr_result.get("full_text"),
                "structured_fields": ocr_result.get("structured_fields", {}),
            },
            "validation": validation,
            "preprocessing": preprocessing_result or {},
        }
        
        # Save as JSON
        json_path = self.metadata_dir / f"{file_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Also save plain text for easy viewing
        text_path = self.metadata_dir / f"{file_id}.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(f"File: {filename}\n")
            f.write(f"File ID: {file_id}\n")
            f.write(f"Timestamp: {metadata['timestamp']}\n")
            f.write(f"OCR Engine: {ocr_result.get('ocr_engine')}\n")
            f.write(f"Confidence: {ocr_result.get('confidence'):.2%}\n")
            f.write(f"Word Count: {ocr_result.get('word_count')}\n")
            f.write(f"Pages: {ocr_result.get('total_pages')}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("EXTRACTED TEXT\n")
            f.write("=" * 60 + "\n\n")
            f.write(ocr_result.get("full_text", ""))
        
        # Save CSV if provided (PaddleOCR)
        if csv_data:
            import csv as csv_module
            csv_path = self.metadata_dir / f"{file_id}.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv_module.writer(f)
                writer.writerow(["Page", "Row", "Text"])
                writer.writerows(csv_data)
            logger.info(f"Saved CSV for {file_id}: {csv_path}")
        
        logger.info(f"Saved metadata for {file_id}: {json_path}")
        return json_path
    
    def get_extraction(self, file_id: str) -> Dict[str, Any]:
        """Retrieve saved extraction metadata"""
        json_path = self.metadata_dir / f"{file_id}.json"
        
        if not json_path.exists():
            raise FileNotFoundError(f"Metadata not found for file_id: {file_id}")
        
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    
    def list_extractions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all saved extractions with pagination
        
        Returns:
            List of extraction summaries (without full_text)
        """
        json_files = sorted(
            self.metadata_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True  # Most recent first
        )
        
        extractions = []
        for json_file in json_files[offset:offset + limit]:
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                
                # Create summary without full text
                summary = {
                    "file_id": data["file_id"],
                    "filename": data["filename"],
                    "timestamp": data["timestamp"],
                    "ocr_engine": data["ocr"]["engine"],
                    "confidence": data["ocr"]["confidence"],
                    "word_count": data["ocr"]["word_count"],
                    "total_pages": data["ocr"]["total_pages"],
                    "validation_status": data["validation"]["recommendation"],
                    "has_structured_fields": bool(data["ocr"].get("structured_fields")),
                    "has_csv": self.has_csv(data["file_id"]),
                }
                extractions.append(summary)
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")
                continue
        
        return extractions
    
    def delete_extraction(self, file_id: str) -> bool:
        """Delete extraction metadata files"""
        json_path = self.metadata_dir / f"{file_id}.json"
        text_path = self.metadata_dir / f"{file_id}.txt"
        csv_path = self.metadata_dir / f"{file_id}.csv"
        
        deleted = False
        if json_path.exists():
            json_path.unlink()
            deleted = True
        if text_path.exists():
            text_path.unlink()
            deleted = True
        if csv_path.exists():
            csv_path.unlink()
            deleted = True
        
        return deleted
    
    def has_csv(self, file_id: str) -> bool:
        """Check if CSV file exists for extraction"""
        csv_path = self.metadata_dir / f"{file_id}.csv"
        return csv_path.exists()
    
    def get_csv_path(self, file_id: str) -> Optional[Path]:
        """Get path to CSV file if it exists"""
        csv_path = self.metadata_dir / f"{file_id}.csv"
        return csv_path if csv_path.exists() else None

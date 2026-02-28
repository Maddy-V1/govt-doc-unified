"""
Output formatters for PaddleOCR results
Supports CSV, JSON, and TXT formats
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List


class OutputFormatter:
    """Format and save OCR results in multiple formats"""
    
    @staticmethod
    def save_txt(result: Dict[str, Any], output_path: str) -> str:
        """
        Save as plain text file
        
        Args:
            result: OCR result dict
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['full_text'])
        
        return str(output_path)
    
    @staticmethod
    def save_json(result: Dict[str, Any], output_path: str) -> str:
        """
        Save as JSON file with complete metadata
        
        Args:
            result: OCR result dict
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create structured JSON output
        json_output = {
            "ocr_engine": result.get("ocr_engine", "paddleocr"),
            "total_pages": result.get("total_pages", 1),
            "confidence": result.get("confidence", 0.0),
            "word_count": result.get("word_count", 0),
            "processing_time": result.get("processing_time", 0.0),
            "dpi": result.get("dpi", 200),
            "language": result.get("language", "hi"),
            "full_text": result.get("full_text", ""),
            "pages": result.get("pages", [])
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2)
        
        return str(output_path)
    
    @staticmethod
    def save_csv(result: Dict[str, Any], output_path: str) -> str:
        """
        Save as CSV file
        Format: Page, Row, Text1, Text2, Text3, ...
        
        Args:
            result: OCR result dict
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        csv_data = result.get("csv_data", [])
        
        if not csv_data:
            # Generate CSV data from pages if not available
            csv_data = []
            for page in result.get("pages", []):
                page_num = page["page"]
                for row in page.get("rows", []):
                    csv_data.append([
                        str(page_num),
                        str(row["row"]),
                        row["text"]
                    ])
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            if csv_data:
                max_cols = max(len(row) for row in csv_data)
                header = ["Page", "Row"] + [f"Col{i}" for i in range(1, max_cols - 1)]
                writer.writerow(header)
            
            # Data
            writer.writerows(csv_data)
        
        return str(output_path)
    
    @staticmethod
    def save_all_formats(
        result: Dict[str, Any],
        base_path: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Save in multiple formats
        
        Args:
            result: OCR result dict
            base_path: Base path without extension
            formats: List of formats to save ['txt', 'json', 'csv']
                    If None, saves all formats
            
        Returns:
            Dict mapping format to saved file path
        """
        if formats is None:
            formats = ['txt', 'json', 'csv']
        
        saved_files = {}
        base_path = Path(base_path)
        
        if 'txt' in formats:
            txt_path = base_path.with_suffix('.txt')
            saved_files['txt'] = OutputFormatter.save_txt(result, str(txt_path))
        
        if 'json' in formats:
            json_path = base_path.with_suffix('.json')
            saved_files['json'] = OutputFormatter.save_json(result, str(json_path))
        
        if 'csv' in formats:
            csv_path = base_path.with_suffix('.csv')
            saved_files['csv'] = OutputFormatter.save_csv(result, str(csv_path))
        
        return saved_files

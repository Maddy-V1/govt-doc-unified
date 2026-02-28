"""
PDF handling utilities for PaddleOCR
"""

import fitz  # PyMuPDF
import numpy as np
from typing import List


def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[np.ndarray]:
    """
    Convert PDF pages to numpy arrays
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for rendering (200 is optimal for scanned docs)
        
    Returns:
        List of RGB numpy arrays, one per page
    """
    doc = fitz.open(pdf_path)
    images = []
    
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
        images.append(img)
    
    doc.close()
    return images


def get_pdf_page_count(pdf_path: str) -> int:
    """Get number of pages in PDF"""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count

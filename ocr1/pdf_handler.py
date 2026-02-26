"""
PDF Handler Module
PDF to image conversion with multi-page support.
"""

import os
from pathlib import Path
from typing import List
from pdf2image import convert_from_path
from PyPDF2 import PdfReader

from PIL import Image
from ocr1.config import PDF_TO_IMAGE_DPI, PDF_TO_IMAGE_FORMAT, MAX_PDF_PAGES
import logging

logger = logging.getLogger(__name__)


def convert_pdf_to_images(
    pdf_path: Path,
    dpi: int = PDF_TO_IMAGE_DPI,
    output_format: str = PDF_TO_IMAGE_FORMAT
) -> List[Path]:
    """
    Convert PDF file to images (one image per page).
    
    Args:
        pdf_path: Path to PDF file
        dpi: DPI for image conversion (higher = better quality)
        output_format: Output image format (PNG or JPEG)
        
    Returns:
        List[Path]: Paths to generated image files
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF has too many pages
        RuntimeError: If conversion fails
    """
    try:
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Converting PDF to images: {pdf_path.name}")
        
        # Check number of pages first
        page_count = get_pdf_page_count(pdf_path)
        
        if page_count > MAX_PDF_PAGES:
            raise ValueError(
                f"PDF has {page_count} pages, maximum allowed is {MAX_PDF_PAGES}"
            )
        
        logger.info(f"PDF has {page_count} pages")
        
        # Convert PDF to images
        images = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            fmt=output_format.lower()
        )
        
        logger.info(f"Successfully converted {len(images)} pages to images")
        
        # Save images and collect paths
        image_paths = []
        base_name = pdf_path.stem  # Filename without extension
        
        for i, image in enumerate(images, start=1):
            # Create output filename
            output_filename = f"{base_name}_page_{i:03d}.{output_format.lower()}"
            output_path = PROCESSED_DIR / output_filename
            
            # Save image
            image.save(output_path, output_format)
            image_paths.append(output_path)
            
            logger.debug(f"Saved page {i}/{page_count}: {output_filename}")
        
        logger.info(
            f"PDF conversion completed: {len(image_paths)} images saved to {PROCESSED_DIR}"
        )
        
        return image_paths
        
    except Exception as e:
        logger.error(f"PDF conversion failed for {pdf_path}: {e}")
        raise RuntimeError(f"Failed to convert PDF: {e}")


def get_pdf_page_count(pdf_path: Path) -> int:
    """
    Get number of pages in a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        int: Number of pages
        
    Raises:
        RuntimeError: If PDF cannot be read
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            page_count = len(pdf_reader.pages)
            return page_count
    except Exception as e:
        logger.error(f"Failed to read PDF {pdf_path}: {e}")
        raise RuntimeError(f"Cannot read PDF file: {e}")


def get_pdf_metadata(pdf_path: Path) -> dict:
    """
    Extract metadata from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        dict: PDF metadata (title, author, creation date, etc.)
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            metadata = pdf_reader.metadata
            
            return {
                'title': metadata.get('/Title', 'N/A') if metadata else 'N/A',
                'author': metadata.get('/Author', 'N/A') if metadata else 'N/A',
                'subject': metadata.get('/Subject', 'N/A') if metadata else 'N/A',
                'creator': metadata.get('/Creator', 'N/A') if metadata else 'N/A',
                'producer': metadata.get('/Producer', 'N/A') if metadata else 'N/A',
                'creation_date': str(metadata.get('/CreationDate', 'N/A')) if metadata else 'N/A',
                'page_count': get_pdf_page_count(pdf_path)
            }
    except Exception as e:
        logger.error(f"Failed to extract PDF metadata: {e}")
        return {'error': str(e)}


def validate_pdf(pdf_path: Path) -> bool:
    """
    Validate if file is a valid PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        bool: True if valid PDF, False otherwise
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            # Check if file starts with PDF signature
            header = pdf_file.read(4)
            if header != b'%PDF':
                logger.warning(f"Invalid PDF header for {pdf_path}")
                return False
            
            # Try to read the PDF
            pdf_reader = PdfReader(pdf_file)
            _ = len(pdf_reader.pages)
            
            return True
    except Exception as e:
        logger.warning(f"PDF validation failed for {pdf_path}: {e}")
        return False


def cleanup_temp_images(image_paths: List[Path]) -> None:
    """
    Clean up temporary image files created from PDF conversion.
    
    Args:
        image_paths: List of image paths to delete
    """
    deleted_count = 0
    
    for image_path in image_paths:
        try:
            if image_path.exists():
                image_path.unlink()
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Failed to delete {image_path}: {e}")
    
    logger.info(f"Cleaned up {deleted_count}/{len(image_paths)} temporary images")


def load_document_images(file_path: Path, dpi: int = PDF_TO_IMAGE_DPI) -> List:
    """
    UniversalOCR input loading method.
    Load PDF or image file and convert to PIL Image array(s).
    
    This is the exact input loading logic from UniversalOCR:
    - For PDFs: Convert to images at 300 DPI
    - For images: Load and convert to RGB
    
    Args:
        file_path: Path to input file (PDF or image)
        dpi: DPI for PDF conversion (default: 300)
        
    Returns:
        List: List of PIL Image objects (one per page)
        
    Raises:
        ValueError: If file format is unsupported or file cannot be read
        RuntimeError: If Poppler is not installed (for PDF processing)
    """
    import cv2
    from PIL import Image
    from pdf2image.exceptions import PDFInfoNotInstalledError
    
    file_path = Path(file_path)
    logger.info(f"Loading input file: {file_path.name}")
    
    if file_path.suffix.lower() == '.pdf':
        # Standard 300 DPI for OCR accuracy
        logger.debug(f"Converting PDF to images at {dpi} DPI")
        try:
            images = convert_from_path(str(file_path), dpi=dpi)
            logger.info(f"PDF converted: {len(images)} pages")
            return images
        except PDFInfoNotInstalledError:
            error_msg = (
                "Poppler is not installed. PDF processing requires Poppler. "
                "Please install Poppler and add it to your system PATH. "
                "Download from: https://github.com/oschwartz10612/poppler-windows/releases/ "
                "For now, please upload image files (JPG, PNG) instead of PDFs."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
    elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
        # Load image using OpenCV
        img = cv2.imread(str(file_path))
        if img is None:
            raise ValueError(f"Could not read image file: {file_path}")
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(img_rgb)
        logger.info("Image loaded successfully")
        return [pil_image]
        
    else:
        raise ValueError(
            f"Unsupported format: {file_path.suffix}. "
            "Use PDF, JPG, PNG, or BMP."
        )

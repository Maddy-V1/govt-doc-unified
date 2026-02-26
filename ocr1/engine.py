"""
Tesseract OCR Engine Module
Wrapper for Tesseract OCR with confidence scoring and quality metrics.
"""

import pytesseract
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple

from ocr1.config import (
    TESSERACT_CONFIG,
    DEFAULT_LANGUAGE,
    MIN_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_WARNING,
    TESSERACT_PATH
)
import logging

logger = logging.getLogger(__name__)

# Set Tesseract path if specified
if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text_with_confidence(image: np.ndarray, language: str = DEFAULT_LANGUAGE) -> Dict[str, any]:
    """
    Extract text from preprocessed image using Tesseract OCR.
    Returns text along with confidence score.
    
    Args:
        image: Preprocessed image (numpy array)
        language: OCR language (default: 'eng')
        
    Returns:
        dict: {
            'text': str,
            'confidence': float (0-1),
            'word_count': int,
            'low_confidence_words': List[str]
        }
        
    Raises:
        RuntimeError: If Tesseract OCR fails
    """
    try:
        logger.info(f"Running Tesseract OCR (language: {language})")
        
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image)
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(
            pil_image,
            lang=language,
            config=TESSERACT_CONFIG
        )
        
        # Get detailed data with confidence scores per word
        data = pytesseract.image_to_data(
            pil_image,
            lang=language,
            config=TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT
        )
        
        # Calculate confidence metrics
        confidence_metrics = _calculate_confidence_metrics(data)
        
        result = {
            'text': text.strip(),
            'confidence': confidence_metrics['average_confidence'],
            'word_count': confidence_metrics['word_count'],
            'low_confidence_words': confidence_metrics['low_confidence_words'],
            'confidence_distribution': confidence_metrics['distribution']
        }
        
        # Log warning if confidence is low
        if result['confidence'] < LOW_CONFIDENCE_WARNING:
            logger.warning(
                f"Low OCR confidence: {result['confidence']:.2f} "
                f"({len(result['low_confidence_words'])} low-confidence words)"
            )
        
        logger.info(
            f"OCR completed: {result['word_count']} words, "
            f"{result['confidence']:.2f} confidence"
        )
        
        return result
        
    except pytesseract.TesseractError as e:
        logger.error(f"Tesseract OCR failed: {e}")
        raise RuntimeError(f"OCR engine error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during OCR: {e}")
        raise


def _calculate_confidence_metrics(ocr_data: Dict) -> Dict:
    """
    Calculate comprehensive confidence metrics from Tesseract output.
    
    Args:
        ocr_data: Raw Tesseract output data dictionary
        
    Returns:
        dict: Confidence metrics including average, distribution, and low-confidence words
    """
    confidences = []
    low_confidence_words = []
    word_count = 0
    
    # Extract confidence scores (filter out -1 values which indicate no text)
    for i, conf in enumerate(ocr_data['conf']):
        if conf != -1:  # -1 means no text detected
            conf_value = float(conf)
            confidences.append(conf_value)
            
            # Track words with low confidence
            word = ocr_data['text'][i].strip()
            if word and conf_value < (LOW_CONFIDENCE_WARNING * 100):
                low_confidence_words.append({
                    'word': word,
                    'confidence': conf_value / 100.0
                })
            
            if word:  # Count non-empty words
                word_count += 1
    
    # Calculate average confidence
    average_confidence = (
        sum(confidences) / len(confidences) / 100.0
        if confidences else 0.0
    )
    
    # Calculate confidence distribution
    distribution = _calculate_confidence_distribution(confidences)
    
    return {
        'average_confidence': round(average_confidence, 3),
        'word_count': word_count,
        'low_confidence_words': low_confidence_words[:10],  # Limit to first 10
        'distribution': distribution
    }


def _calculate_confidence_distribution(confidences: List[float]) -> Dict[str, int]:
    """
    Calculate distribution of confidence scores across ranges.
    
    Args:
        confidences: List of confidence scores (0-100)
        
    Returns:
        dict: Count of scores in each range
    """
    distribution = {
        'very_high': 0,  # 90-100
        'high': 0,       # 75-90
        'medium': 0,     # 50-75
        'low': 0,        # 25-50
        'very_low': 0    # 0-25
    }
    
    for conf in confidences:
        if conf >= 90:
            distribution['very_high'] += 1
        elif conf >= 75:
            distribution['high'] += 1
        elif conf >= 50:
            distribution['medium'] += 1
        elif conf >= 25:
            distribution['low'] += 1
        else:
            distribution['very_low'] += 1
    
    return distribution


def test_tesseract_installation() -> bool:
    """
    Test if Tesseract is properly installed and accessible.
    
    Returns:
        bool: True if Tesseract is available, False otherwise
    """
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract version: {version}")
        return True
    except Exception as e:
        logger.error(f"Tesseract not available: {e}")
        return False


def get_available_languages() -> List[str]:
    """
    Get list of available Tesseract languages.
    
    Returns:
        List[str]: Available language codes
    """
    try:
        languages = pytesseract.get_languages()
        logger.info(f"Available Tesseract languages: {', '.join(languages)}")
        return languages
    except Exception as e:
        logger.error(f"Failed to get available languages: {e}")
        return [DEFAULT_LANGUAGE]


def extract_text_universal(image: np.ndarray, language: str = DEFAULT_LANGUAGE, scale_factor: float = 1.0) -> Dict[str, any]:
    """
    UniversalOCR text extraction method.
    Extract text with word-level confidence using pytesseract.image_to_data.
    
    This is the exact OCR logic from UniversalOCR:
    - Uses image_to_data for detailed word-level results
    - Calculates average confidence per page
    - Returns structured data with text, confidence, word count, and word boxes
    - Adjusts coordinates based on preprocessing scale factor
    
    Args:
        image: Preprocessed image (numpy array)
        language: OCR language (default: 'eng')
        scale_factor: Scale factor from preprocessing (default: 1.0)
        
    Returns:
        dict: {
            'text': str (joined words),
            'confidence': float (0-100 scale),
            'word_count': int,
            'words': List[str],
            'word_boxes': List[dict] with word, confidence, and bbox (adjusted to original scale)
        }
    """
    try:
        logger.debug(f"Running UniversalOCR extraction (language: {language}, scale: {scale_factor}x)")
        
        # Convert numpy array to PIL Image for consistent coordinate system
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image, mode='L')
        else:
            pil_image = image
        
        # Extract text with confidence data using image_to_data
        data = pytesseract.image_to_data(
            pil_image,
            output_type=pytesseract.Output.DICT,
            lang=language
        )
        
        # Process OCR results
        page_text = []
        total_conf = 0
        word_count = 0
        word_boxes = []
        
        for j in range(len(data['text'])):
            conf = int(data['conf'][j])
            if conf > -1:  # -1 means no text detected
                text = data['text'][j].strip()
                if text:
                    # Ignore extreme noise (e.g. random squiggles < 15% confidence that aren't letters/numbers)
                    if conf < 15 and len(text) <= 2 and not any(c.isalnum() for c in text):
                        continue
                        
                    page_text.append(text)
                    total_conf += conf
                    word_count += 1
                    
                    # Add word box data with coordinates adjusted to original image scale
                    word_boxes.append({
                        'text': text,
                        'confidence': float(conf),
                        'left': int(data['left'][j] / scale_factor),
                        'top': int(data['top'][j] / scale_factor),
                        'width': int(data['width'][j] / scale_factor),
                        'height': int(data['height'][j] / scale_factor)
                    })
        
        # Calculate average confidence
        avg_conf = (total_conf / word_count) if word_count > 0 else 0
        
        # Join text for this page
        joined_text = " ".join(page_text)
        
        result = {
            'text': joined_text,
            'confidence': round(avg_conf, 2),  # 0-100 scale
            'word_count': word_count,
            'words': page_text,
            'word_boxes': word_boxes
        }
        
        logger.debug(
            f"UniversalOCR extraction completed: {word_count} words, "
            f"{avg_conf:.2f}% confidence"
        )
        
        return result
        
    except pytesseract.TesseractError as e:
        logger.error(f"Tesseract OCR failed: {e}")
        raise RuntimeError(f"OCR engine error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during OCR: {e}")
        raise

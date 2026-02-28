"""
Image preprocessing for PaddleOCR
Optimized for scanned government documents
"""

import cv2
import numpy as np
from .config import ENABLE_CLAHE, ENABLE_SHARPENING, ENABLE_DENOISING


def preprocess_image(img: np.ndarray) -> np.ndarray:
    """
    Light preprocessing optimized for scanned documents
    
    - CLAHE: Adaptive histogram equalization for uneven lighting
    - Unsharp mask: Crisp text edges
    - Denoise: Remove scan speckle
    
    Note: Avoids full binarization as PaddleOCR works better with anti-aliased text
    
    Args:
        img: RGB numpy array
        
    Returns:
        Preprocessed RGB numpy array
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # CLAHE - fix uneven scan lighting
    if ENABLE_CLAHE:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
    else:
        enhanced = gray
    
    # Light unsharp mask - sharpen text edges
    if ENABLE_SHARPENING:
        blurred = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=1.5)
        sharpened = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
    else:
        sharpened = enhanced
    
    # Mild denoise - preserve text, remove scan speckle
    if ENABLE_DENOISING:
        denoised = cv2.fastNlMeansDenoising(
            sharpened,
            h=5,
            templateWindowSize=7,
            searchWindowSize=21
        )
    else:
        denoised = sharpened
    
    # Back to 3-channel RGB for PaddleOCR
    return cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)

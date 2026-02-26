"""
Image Preprocessing Module
Advanced image enhancement techniques for improved OCR accuracy.
Upgraded to match the advanced OCR pipeline (bilateral filter + unsharp mask).
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from typing import Union, Tuple
from pathlib import Path

from ocr1.config import GAUSSIAN_BLUR_KERNEL, TARGET_DPI
import logging

logger = logging.getLogger(__name__)


def get_skew_angle(image: np.ndarray) -> float:
    """Calculate skew angle of an image based on text block orientation."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return 0.0

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    return angle


def deskew(image: np.ndarray) -> np.ndarray:
    """Deskew image based on detected text angle."""
    angle = get_skew_angle(image)
    if abs(angle) < 0.5:
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    logger.debug(f"Image deskewed by {angle:.2f} degrees")
    return rotated


def apply_clahe(image: np.ndarray) -> np.ndarray:
    """Apply Contrast Limited Adaptive Histogram Equalization."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(16, 16))
    return clahe.apply(image)


def apply_unsharp_mask(image: np.ndarray, sigma: float = 3.0, strength: float = 1.5) -> np.ndarray:
    """
    Unsharp mask sharpening — produces crisper characters than simple kernels.
    Better than the 3x3 kernel approach for fine government document text.
    """
    blurred = cv2.GaussianBlur(image, (0, 0), sigma)
    sharpened = cv2.addWeighted(image, strength, blurred, -(strength - 1.0), 0)
    return sharpened


def preprocess_image(image_path: Union[str, Path]) -> np.ndarray:
    """
    Apply comprehensive preprocessing to enhance image quality for OCR.

    Pipeline (upgraded):
    1. Upscale if needed
    2. Grayscale
    3. Deskew
    4. Bilateral filter (edge-preserving denoising — better than fastNlMeans)
    5. CLAHE contrast enhancement
    6. Unsharp mask (sharper characters)
    7. Adaptive thresholding
    """
    try:
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info(f"Preprocessing image: {image_path.name}")
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Step 1: Upscale if too small
        h, w = image.shape[:2]
        if w < 1000:
            scale = 2000 / w
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            logger.debug(f"Upscaled: {w}x{h} → {int(w*scale)}x{int(h*scale)}")

        # Step 2: Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Step 3: Deskew
        gray = deskew(gray)

        # Step 4: Bilateral filter (preserves text edges better than NlMeans)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        logger.debug("Applied bilateral filter")

        # Step 5: CLAHE
        enhanced = apply_clahe(denoised)
        logger.debug("Applied CLAHE")

        # Step 6: Unsharp mask
        sharpened = apply_unsharp_mask(enhanced)
        logger.debug("Applied unsharp mask")

        # Step 7: Adaptive Thresholding
        binary = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
        )
        logger.debug("Applied adaptive thresholding")

        logger.info(f"Preprocessing completed for {image_path.name}")
        return binary

    except Exception as e:
        logger.error(f"Preprocessing failed for {image_path}: {e}")
        raise


def preprocess_pil_image(pil_image) -> Tuple[np.ndarray, float]:
    """
    UniversalOCR preprocessing for PIL images.
    Upgraded pipeline: bilateral filter + unsharp mask instead of fastNlMeans.

    Returns:
        Tuple[np.ndarray, float]: (processed grayscale image, scale_factor)
    """
    open_cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    scale_factor = 1.0
    if w < 1000:
        scale_factor = 2000 / w
        gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor,
                          interpolation=cv2.INTER_CUBIC)
        logger.debug(f"Upscaled {w}x{h} → scale {scale_factor:.2f}x")

    # Deskew
    gray = deskew(gray)

    # Bilateral filter (edge-preserving — better than fastNlMeans for text)
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)

    # CLAHE (local contrast)
    enhanced = apply_clahe(denoised)

    # Unsharp mask (crisp characters)
    sharpened = apply_unsharp_mask(enhanced)

    # Adaptive threshold
    binary = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    logger.debug(
        f"preprocess_pil_image: bilateral+CLAHE+unsharp+adaptive_thresh "
        f"(scale={scale_factor:.2f}x)"
    )
    return binary, scale_factor


def enhance_image_quality(image_path: Union[str, Path]) -> np.ndarray:
    """PIL-based alternative preprocessing for low-contrast images."""
    pil_image = Image.open(image_path)
    gray_image = pil_image.convert('L')
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced = enhancer.enhance(2.0)
    sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
    sharpened = sharpness_enhancer.enhance(1.5)
    return np.array(sharpened)


def auto_rotate_image(image: np.ndarray) -> np.ndarray:
    """Automatically detect and correct image rotation."""
    return deskew(image)


def resize_image_to_target_dpi(
    image: np.ndarray,
    current_dpi: int = 72,
    target_dpi: int = TARGET_DPI
) -> np.ndarray:
    """Resize image to target DPI for optimal OCR performance."""
    if current_dpi == target_dpi:
        return image
    scale_factor = target_dpi / current_dpi
    new_width = int(image.shape[1] * scale_factor)
    new_height = int(image.shape[0] * scale_factor)
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

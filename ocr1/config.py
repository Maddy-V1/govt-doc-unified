"""
ocr1/config.py
Tesseract OCR engine configuration.
"""

import os

# Tesseract binary path — override via .env / system env
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "")   # empty = auto-detect from PATH

# OCR engine mode: 1 = LSTM neural net (best accuracy)
TESSERACT_OEM = int(os.getenv("TESSERACT_OEM", "1"))

# Page segmentation mode: 3 = fully automatic (no OSD)
TESSERACT_PSM = int(os.getenv("TESSERACT_PSM", "3"))

# Build tesseract config string
TESSERACT_CONFIG = f"--oem {TESSERACT_OEM} --psm {TESSERACT_PSM}"

# Default OCR language
DEFAULT_LANGUAGE = os.getenv("TESSERACT_LANG", "eng")

# Confidence thresholds (0–1 scale)
MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE", "0.3"))
LOW_CONFIDENCE_WARNING   = float(os.getenv("LOW_CONFIDENCE_WARNING", "0.6"))

# Image preprocessing
GAUSSIAN_BLUR_KERNEL = (5, 5)
TARGET_DPI = int(os.getenv("TARGET_DPI", "300"))

# PDF conversion
PDF_TO_IMAGE_DPI    = int(os.getenv("PDF_DPI", "300"))
PDF_TO_IMAGE_FORMAT = os.getenv("PDF_IMAGE_FORMAT", "PNG")
MAX_PDF_PAGES       = int(os.getenv("MAX_PDF_PAGES", "50"))

# Postprocessing flags
REMOVE_DUPLICATE_LINES = True
NORMALIZE_WHITESPACE   = True
REMOVE_NON_PRINTABLE   = True

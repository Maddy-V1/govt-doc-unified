"""
OCR Configuration Module
Sarvam AI OCR configuration constants and settings.

Optimized for:
  - Government document recognition (Hindi + English + handwritten)
  - Multi-language support via Sarvam AI
  - Cloud-based OCR processing
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
#  Sarvam AI Configuration
# ──────────────────────────────────────────────────────────────────────
SARVAM_API_KEY = os.getenv('SARVAM_API_KEY', '')

# Default language for OCR (Sarvam AI format)
# hi-IN = Hindi (best for govt docs with Hindi + English mixed)
# en-IN = English
DEFAULT_LANGUAGE = os.getenv('SARVAM_LANGUAGE', 'hi-IN')

# Output format for Sarvam AI Document Intelligence
SARVAM_OUTPUT_FORMAT = os.getenv('SARVAM_OUTPUT_FORMAT', 'html')

# ──────────────────────────────────────────────────────────────────────
#  PDF conversion settings (for preview rendering)
# ──────────────────────────────────────────────────────────────────────
PDF_TO_IMAGE_DPI = int(os.getenv('PDF_DPI', '300'))
PDF_TO_IMAGE_FORMAT = 'PNG'

# ──────────────────────────────────────────────────────────────────────
#  Processing limits
# ──────────────────────────────────────────────────────────────────────
MAX_PROCESSING_TIME_SECONDS = int(os.getenv('MAX_PROCESSING_TIME', '120'))
MAX_PDF_PAGES = int(os.getenv('MAX_PDF_PAGES', '50'))

# ──────────────────────────────────────────────────────────────────────
#  Text cleaning settings
# ──────────────────────────────────────────────────────────────────────
REMOVE_DUPLICATE_LINES = True
NORMALIZE_WHITESPACE = True
REMOVE_NON_PRINTABLE = True

# ──────────────────────────────────────────────────────────────────────
#  Supported formats
# ──────────────────────────────────────────────────────────────────────
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']

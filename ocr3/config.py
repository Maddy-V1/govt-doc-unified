"""
PaddleOCR Configuration
"""

import os
from pathlib import Path

# PaddleOCR settings
PADDLE_LANG = os.getenv("PADDLE_LANG", "hi")  # 'en' for English, 'hi' for Hindi/mixed
PADDLE_USE_GPU = os.getenv("PADDLE_USE_GPU", "false").lower() == "true"
PADDLE_DPI = int(os.getenv("PADDLE_DPI", "200"))  # Optimal DPI for scanned docs
PADDLE_CONF_THRESH = float(os.getenv("PADDLE_CONF_THRESH", "0.30"))
PADDLE_ROW_GAP = int(os.getenv("PADDLE_ROW_GAP", "10"))  # Y-proximity for row grouping

# Output formats
ENABLE_CSV_OUTPUT = os.getenv("ENABLE_CSV_OUTPUT", "true").lower() == "true"
ENABLE_JSON_OUTPUT = os.getenv("ENABLE_JSON_OUTPUT", "true").lower() == "true"
ENABLE_TXT_OUTPUT = os.getenv("ENABLE_TXT_OUTPUT", "true").lower() == "true"

# Preprocessing
ENABLE_CLAHE = os.getenv("ENABLE_CLAHE", "true").lower() == "true"
ENABLE_SHARPENING = os.getenv("ENABLE_SHARPENING", "true").lower() == "true"
ENABLE_DENOISING = os.getenv("ENABLE_DENOISING", "true").lower() == "true"

"""
OCR3 - PaddleOCR Integration
Multi-format output: CSV, JSON, TXT
"""

from .paddle_engine import PaddleOCREngine
from .output_formatters import OutputFormatter
from .config import (
    PADDLE_LANG,
    PADDLE_USE_GPU,
    PADDLE_DPI,
    PADDLE_CONF_THRESH,
    PADDLE_ROW_GAP,
    ENABLE_CSV_OUTPUT,
    ENABLE_JSON_OUTPUT,
    ENABLE_TXT_OUTPUT
)

__all__ = [
    'PaddleOCREngine',
    'OutputFormatter',
    'PADDLE_LANG',
    'PADDLE_USE_GPU',
    'PADDLE_DPI',
    'PADDLE_CONF_THRESH',
    'PADDLE_ROW_GAP',
    'ENABLE_CSV_OUTPUT',
    'ENABLE_JSON_OUTPUT',
    'ENABLE_TXT_OUTPUT'
]

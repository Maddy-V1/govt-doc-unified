"""
backend/app/core/logging.py
Centralized logging configuration for the application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure application-wide logging with file and console handlers.
    """
    from backend.core.config import settings

    log_dir = settings.DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on repeated calls
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    return root_logger


# Module-level logger
logger = logging.getLogger(__name__)

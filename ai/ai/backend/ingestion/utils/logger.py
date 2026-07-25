"""
Arkana — Structured Logger
Configures rich logging with file + console output.
Import logger from here in all modules.
"""

import logging
import sys
from pathlib import Path

from ingestion.config import LOG_DIR, LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger. All loggers share the same handlers (console + file).
    Usage:
        from ingestion.utils.logger import get_logger
        logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(LOG_LEVEL)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler — one file per module name
    log_file = LOG_DIR / "arkana_ingestion.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.propagate = False
    return logger

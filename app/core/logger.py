"""
logger.py — Centralized logging configuration for PermitFlow-AI.

Responsibilities:
- Provide a single logger instance for the entire application.
- Configure log format with timestamps, log level, and module name.
- Allow easy integration with Azure/App Service logging.

Future Changes:
- Add JSON log formatting for ingestion into log analytics.
- Integrate with external monitoring/alerting systems.
"""

import logging
import sys

# Create logger
logger = logging.getLogger("permitflow")
logger.setLevel(logging.INFO)  # Default level; can be overridden via env var

# Create handler for stdout (works well in containerized/cloud environments)
handler = logging.StreamHandler(sys.stdout)

# Define log format
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

# Avoid duplicate handlers if re-imported
if not logger.handlers:
    logger.addHandler(handler)

# Export logger
__all__ = ["logger"]
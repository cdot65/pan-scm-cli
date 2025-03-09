"""SCM CLI - Network Engineer-friendly CLI for Palo Alto Networks Security Content Management."""

import logging
import sys

# Set up root logger for the entire application
logger = logging.getLogger("scm_cli")
logger.setLevel(logging.INFO)

# Create console handler if no handlers exist
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Import main entry point for easier access
from .cli.main import main